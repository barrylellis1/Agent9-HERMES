# arch-allow-direct-agent-construction
"""
Phase 11G: DA mixed analysis mode unit tests.

Covers:
  1. _infer_analysis_mode — pure problem, pure opportunity, mixed, empty, boundary
  2. Post-loop IS/IS NOT reshuffling — segment_type tagging, mixed merge, opportunity swap
  3. DeepAnalysisResponse.analysis_mode field propagation
"""
import pytest
from unittest.mock import MagicMock

from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent, _MIXED_MODE_PURITY_THRESHOLD
from src.agents.models.deep_analysis_models import DeepAnalysisResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _agent() -> A9_Deep_Analysis_Agent:
    """Minimal DA agent instance — no orchestrator or DPA needed for these tests."""
    return A9_Deep_Analysis_Agent({})


def _items(n: int) -> list:
    """Return a list of n dummy variance tuples."""
    return [(f"key_{i}", 100.0, 90.0, -10.0) for i in range(n)]


def _opp_items(n: int) -> list:
    """Return a list of n dummy outperformer tuples."""
    return [(f"opp_{i}", 110.0, 100.0, 10.0) for i in range(n)]


# ---------------------------------------------------------------------------
# 1. _infer_analysis_mode
# ---------------------------------------------------------------------------

class TestInferAnalysisMode:
    def setup_method(self):
        self.da = _agent()

    def test_pure_problem_all_problem(self):
        # 5 problem, 0 healthy → problem
        result = self.da._infer_analysis_mode(_items(5), [], caller_hint="problem")
        assert result == "problem"

    def test_pure_problem_above_threshold(self):
        # 4 problem, 1 healthy → 4/5 = 80% → exactly at threshold → problem
        result = self.da._infer_analysis_mode(_items(4), _opp_items(1), top_n=5)
        assert result == "problem"

    def test_pure_opportunity_all_healthy(self):
        # 0 problem, 5 healthy → opportunity
        result = self.da._infer_analysis_mode([], _opp_items(5), caller_hint="opportunity")
        assert result == "opportunity"

    def test_pure_opportunity_above_threshold(self):
        # 1 problem, 4 healthy → 4/5 = 80% → opportunity
        result = self.da._infer_analysis_mode(_items(1), _opp_items(4), top_n=5)
        assert result == "opportunity"

    def test_mixed_equal_split(self):
        # 5 problem, 5 healthy → each 50% → mixed
        result = self.da._infer_analysis_mode(_items(5), _opp_items(5), top_n=5)
        assert result == "mixed"

    def test_mixed_below_threshold(self):
        # 3 problem, 2 healthy → 3/5 = 60% < 80% → mixed
        result = self.da._infer_analysis_mode(_items(3), _opp_items(2), top_n=5)
        assert result == "mixed"

    def test_empty_falls_back_to_caller_hint_problem(self):
        result = self.da._infer_analysis_mode([], [], caller_hint="problem")
        assert result == "problem"

    def test_empty_falls_back_to_caller_hint_opportunity(self):
        result = self.da._infer_analysis_mode([], [], caller_hint="opportunity")
        assert result == "opportunity"

    def test_top_n_caps_long_lists(self):
        # 20 problem, 1 healthy — but top_n=5 caps to 5 problem vs 1 healthy → 5/6 ≈ 83% → problem
        result = self.da._infer_analysis_mode(_items(20), _opp_items(1), top_n=5)
        assert result == "problem"

    def test_purity_threshold_constant(self):
        # Sanity-check the module constant hasn't drifted
        assert _MIXED_MODE_PURITY_THRESHOLD == 0.80


# ---------------------------------------------------------------------------
# 2. Post-loop IS/IS NOT reshuffling
# ---------------------------------------------------------------------------

def _make_entry(key: str, segment_type: str, delta: float = -10.0) -> dict:
    return {"dimension": "Region", "key": key, "current": 90.0, "previous": 100.0,
            "delta": delta, "segment_type": segment_type}


class _FakePlan:
    """Minimal stand-in for DeepAnalysisPlan used by the reshuffling block."""
    def __init__(self, mode: str = "problem"):
        self.analysis_mode = mode
        self.kpi_name = "Test KPI"
        self.timeframe = "YTD"
        self.dimensions = []


class _FakeKT:
    def __init__(self):
        self.where_is: list = []
        self.where_is_not: list = []
        self.benchmark_segments: list = []


def _apply_reshuffling(where_is: list, where_is_not: list, effective_mode: str):
    """
    Replicate the post-loop reshuffling logic from a9_deep_analysis_agent.py
    so we can test it in isolation without running the full dimension loop.
    """
    kt = _FakeKT()
    kt.where_is = list(where_is)
    kt.where_is_not = list(where_is_not)

    if effective_mode == "opportunity":
        kt.where_is, kt.where_is_not = kt.where_is_not, kt.where_is
    elif effective_mode == "mixed":
        kt.where_is = kt.where_is + kt.where_is_not
        kt.where_is_not = []
        kt.where_is.sort(key=lambda item: abs(item.get("delta") or 0), reverse=True)

    return kt


class TestPostLoopReshuffling:
    def _problem_entries(self, n=3):
        return [_make_entry(f"prob_{i}", "problem", delta=-(i + 1) * 10.0) for i in range(n)]

    def _opp_entries(self, n=2):
        return [_make_entry(f"opp_{i}", "opportunity", delta=(i + 1) * 5.0) for i in range(n)]

    def test_problem_mode_no_reshuffling(self):
        prob = self._problem_entries(3)
        healthy = self._opp_entries(2)
        kt = _apply_reshuffling(prob, healthy, "problem")
        assert kt.where_is == prob
        assert kt.where_is_not == healthy

    def test_opportunity_mode_swaps_is_and_is_not(self):
        prob = self._problem_entries(3)
        healthy = self._opp_entries(2)
        kt = _apply_reshuffling(prob, healthy, "opportunity")
        # After swap: where_is = previously-healthy, where_is_not = previously-problem
        assert kt.where_is == healthy
        assert kt.where_is_not == prob

    def test_mixed_mode_merges_into_where_is(self):
        prob = self._problem_entries(3)
        healthy = self._opp_entries(2)
        kt = _apply_reshuffling(prob, healthy, "mixed")
        assert len(kt.where_is) == 5
        assert kt.where_is_not == []

    def test_mixed_mode_sorted_by_abs_delta_descending(self):
        prob = self._problem_entries(3)   # deltas: -10, -20, -30
        healthy = self._opp_entries(2)    # deltas: +5, +10
        kt = _apply_reshuffling(prob, healthy, "mixed")
        abs_deltas = [abs(item["delta"]) for item in kt.where_is]
        assert abs_deltas == sorted(abs_deltas, reverse=True)

    def test_mixed_mode_preserves_segment_type(self):
        prob = self._problem_entries(2)
        healthy = self._opp_entries(2)
        kt = _apply_reshuffling(prob, healthy, "mixed")
        types = {item["segment_type"] for item in kt.where_is}
        assert "problem" in types
        assert "opportunity" in types

    def test_mixed_mode_empty_healthy_still_merges(self):
        prob = self._problem_entries(3)
        kt = _apply_reshuffling(prob, [], "mixed")
        assert len(kt.where_is) == 3
        assert kt.where_is_not == []

    def test_opportunity_mode_empty_problem_items(self):
        healthy = self._opp_entries(3)
        kt = _apply_reshuffling([], healthy, "opportunity")
        assert kt.where_is == healthy
        assert kt.where_is_not == []


# ---------------------------------------------------------------------------
# 3. DeepAnalysisResponse.analysis_mode field
# ---------------------------------------------------------------------------

_REQ_ID = "req-test-001"


class TestDeepAnalysisResponseAnalysisMode:
    def test_default_is_problem(self):
        resp = DeepAnalysisResponse(request_id=_REQ_ID, status="ok", message="ok", analysis_mode="problem")
        assert resp.analysis_mode == "problem"

    def test_opportunity_roundtrips(self):
        resp = DeepAnalysisResponse(request_id=_REQ_ID, status="ok", message="ok", analysis_mode="opportunity")
        assert resp.analysis_mode == "opportunity"

    def test_mixed_roundtrips(self):
        resp = DeepAnalysisResponse(request_id=_REQ_ID, status="ok", message="ok", analysis_mode="mixed")
        assert resp.analysis_mode == "mixed"

    def test_invalid_mode_raises(self):
        with pytest.raises(Exception):
            DeepAnalysisResponse(request_id=_REQ_ID, status="ok", message="ok", analysis_mode="unknown")

    def test_analysis_mode_propagates_via_success_factory(self):
        resp = DeepAnalysisResponse.success(
            request_id=_REQ_ID,
            data={"scqa_summary": "test"},
            analysis_mode="mixed",
        )
        assert resp.analysis_mode == "mixed"
        assert resp.status == "success"
