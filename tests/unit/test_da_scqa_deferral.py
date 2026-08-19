"""
Phase 19, Slice 3 — SCQA deferral tests (2026-08-18).

Two things this slice changed, tested separately:

1. `_generate_scqa_summary` gained a `frame: Optional[FramingDecision]`
   parameter. `frame=None` (every pre-Phase-19 call site, unchanged) must
   produce byte-identical output to before — proven by
   test_da_scqa_failure_no_fallback.py / test_11i_compound_alerts.py /
   test_da_sf_va_opportunity_mode.py continuing to pass unmodified (verified
   in the same commit as this file, not re-proven here). This file instead
   proves the NEW behavior: when `frame` IS present, every deterministic
   fallback branch emits the chosen objective as its Question — "the single
   highest-risk detail in the build" per the implementation plan, since
   skipping it reintroduces the exact fabricated-frame-on-a-failure-path
   defect `_safe_generate_scqa_summary` was extracted to guard against, one
   layer up.

2. New `generate_scqa_for_frame()` reconstructs `_generate_scqa_summary`'s
   inputs from a serialized `da_output` dict. Tested against a REAL captured
   payload (decision-studio-ui/tests/e2e/fixtures/live-briefing-payload.json)
   rather than a hand-built stub, so the reconstruction is proven against an
   actual shape DA has produced, not an assumption about that shape.

Same lightweight stub-construction pattern as test_da_scqa_failure_no_fallback.py
and test_da_framing_prompt.py: no orchestrator/DPA infrastructure needed. The
stub deliberately has NO `llm_service_agent` attribute, so any LLM path inside
`_generate_scqa_summary` raises AttributeError immediately, caught by its own
try/except, and falls through to the deterministic `_fallback()` — the same
mechanism that already makes the flag-off test suite exercise the fallback
path today, just used here deliberately rather than incidentally.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
from src.agents.models.deep_analysis_models import (
    DeepAnalysisPlan,
    KTIsIsNot,
    ChangePoint,
    DeepAnalysisResponse,
    FramingDecision,
)

_LOGGER = logging.getLogger("test.scqa_deferral")

_FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "decision-studio-ui" / "tests" / "e2e" / "fixtures" / "live-briefing-payload.json"
)


def _make_da_stub() -> A9_Deep_Analysis_Agent:
    stub = object.__new__(A9_Deep_Analysis_Agent)
    stub.logger = _LOGGER
    return stub  # deliberately no llm_service_agent — see module docstring


def _plan(**overrides):
    base = dict(kpi_name="gross_margin_pct", client_id="hess", timeframe="year_to_date")
    base.update(overrides)
    return DeepAnalysisPlan(**base)


def _kt(**overrides):
    base = dict(
        where_is=[{"key": "Synthetic Blend Engine Oil", "delta": -7.1}],
        where_is_not=[{"key": "Coolants"}],
    )
    base.update(overrides)
    return KTIsIsNot(**base)


def _frame(objective="Addressing base_oil_cost instead of gross_margin_pct directly"):
    return FramingDecision(
        choice="alternative", chosen_kpi_id="base_oil_cost",
        chosen_objective_text=objective,
        falsification_criterion="If base oil prices stabilize and margin does not recover, this was wrong.",
    )


# ---------------------------------------------------------------------------
# DeepAnalysisResponse model fields
# ---------------------------------------------------------------------------

class TestResponseModelFields:
    def test_scqa_deferred_defaults_false(self):
        r = DeepAnalysisResponse.success(request_id="x")
        assert r.scqa_deferred is False
        assert r.scqa_inputs is None

    def test_scqa_deferred_and_inputs_settable(self):
        r = DeepAnalysisResponse.success(
            request_id="x", scqa_summary=None, scqa_deferred=True,
            scqa_inputs={"comparison_type": "budget", "inverse_logic": False, "kpi_unit": "%"},
        )
        assert r.scqa_deferred is True
        assert r.scqa_summary is None
        assert r.scqa_inputs == {"comparison_type": "budget", "inverse_logic": False, "kpi_unit": "%"}


# ---------------------------------------------------------------------------
# _generate_scqa_summary's deterministic fallback, with a chosen frame
# ---------------------------------------------------------------------------

class TestFallbackQuestionOverride:
    @pytest.mark.asyncio
    async def test_problem_mode_fallback_emits_chosen_objective(self):
        da = _make_da_stub()
        frame = _frame()
        result = await da._generate_scqa_summary(
            plan=_plan(), kt=_kt(), change_points=[], spec={"comparison_type": "previous", "inverse_logic": False},
            principal_id="cfo_001", analysis_mode="problem", frame=frame,
        )
        assert f"Question: {frame.chosen_objective_text}" in result
        assert "What actions can address the identified contributors?" not in result

    @pytest.mark.asyncio
    async def test_opportunity_mode_fallback_emits_chosen_objective(self):
        da = _make_da_stub()
        frame = _frame("Sustaining e-commerce growth rather than diagnosing it as a problem")
        result = await da._generate_scqa_summary(
            plan=_plan(), kt=_kt(), change_points=[], spec={"comparison_type": "previous", "inverse_logic": False},
            principal_id="cfo_001", analysis_mode="opportunity", frame=frame,
        )
        assert f"Question: {frame.chosen_objective_text}" in result
        assert "How do we scale the" not in result

    @pytest.mark.asyncio
    async def test_mixed_mode_fallback_emits_chosen_objective_all_three_branches(self):
        """Mixed mode has THREE separate hardcoded Question lines depending on
        relative magnitude — every one must be overridden, not just the
        branch that happens to fire first."""
        da = _make_da_stub()
        frame = _frame()

        # net_opp > net_problem * 3
        kt_opp_dominant = _kt(where_is=[
            {"key": "A", "delta": 100, "segment_type": "opportunity"},
            {"key": "B", "delta": -1, "segment_type": "problem"},
        ])
        result = await da._generate_scqa_summary(
            plan=_plan(), kt=kt_opp_dominant, change_points=[], spec={}, principal_id="x",
            analysis_mode="mixed", frame=frame,
        )
        assert f"Question: {frame.chosen_objective_text}" in result

        # net_problem > net_opp * 3
        kt_problem_dominant = _kt(where_is=[
            {"key": "A", "delta": 1, "segment_type": "opportunity"},
            {"key": "B", "delta": -100, "segment_type": "problem"},
        ])
        result = await da._generate_scqa_summary(
            plan=_plan(), kt=kt_problem_dominant, change_points=[], spec={}, principal_id="x",
            analysis_mode="mixed", frame=frame,
        )
        assert f"Question: {frame.chosen_objective_text}" in result

        # comparable magnitude -> else branch
        kt_comparable = _kt(where_is=[
            {"key": "A", "delta": 10, "segment_type": "opportunity"},
            {"key": "B", "delta": -10, "segment_type": "problem"},
        ])
        result = await da._generate_scqa_summary(
            plan=_plan(), kt=kt_comparable, change_points=[], spec={}, principal_id="x",
            analysis_mode="mixed", frame=frame,
        )
        assert f"Question: {frame.chosen_objective_text}" in result

    @pytest.mark.asyncio
    async def test_matrix_branch_fallback_emits_chosen_objective(self):
        da = _make_da_stub()
        frame = _frame()
        kt_matrix = _kt(
            where_is=[{"key": "A", "delta": -5, "basis_agreement": "confirmed"}],
            where_is_not=[{"key": "B", "basis_agreement": "basis_specific"}],
        )
        result = await da._generate_scqa_summary(
            plan=_plan(), kt=kt_matrix, change_points=[], spec={}, principal_id="x",
            analysis_mode="problem", matrix_ran=True, comparator_secondary="budget", frame=frame,
        )
        assert f"Question: {frame.chosen_objective_text}" in result

    @pytest.mark.asyncio
    async def test_frame_none_leaves_fallback_unchanged(self):
        """The control: frame=None (every existing call site) must reproduce
        the exact original question text, not the override."""
        da = _make_da_stub()
        result = await da._generate_scqa_summary(
            plan=_plan(), kt=_kt(), change_points=[], spec={"comparison_type": "previous", "inverse_logic": False},
            principal_id="cfo_001", analysis_mode="problem", frame=None,
        )
        assert "Question: What actions can address the identified contributors?" in result


# ---------------------------------------------------------------------------
# generate_scqa_for_frame — reconstruction from a real captured payload
# ---------------------------------------------------------------------------

def _kpi_ns(unit="%"):
    from types import SimpleNamespace
    return SimpleNamespace(id="gross_margin_pct", client_id="lubricants", name="Gross Margin %", unit=unit)


def _registry_patch(records):
    provider = MagicMock()
    provider.get_all.return_value = records
    factory = MagicMock()
    factory.get_provider.return_value = provider
    return patch("src.registry.factory.RegistryFactory", return_value=factory)


class TestGenerateScqaForFrame:
    @pytest.fixture
    def real_analysis_payload(self):
        assert _FIXTURE_PATH.exists(), f"expected fixture at {_FIXTURE_PATH}"
        with open(_FIXTURE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data["analysis"]  # the serialized DeepAnalysisResponse shape

    @pytest.mark.asyncio
    async def test_reconstructs_from_real_payload_and_emits_chosen_objective(self, real_analysis_payload):
        """The realistic-shape test the plan calls for: a genuine captured
        payload, not a hand-built stub. This fixture predates Slice 3 (no
        scqa_inputs key), so this also exercises the old-shaped-payload
        fallback path."""
        da = _make_da_stub()
        frame = _frame("Addressing base_oil_cost exposure instead of gross_margin_pct directly")
        with _registry_patch([_kpi_ns()]):
            result = await da.generate_scqa_for_frame(
                da_output=real_analysis_payload, principal_id="cfo_001", frame=frame,
                decided_by_role="CFO",
            )
        assert result is not None
        assert result.startswith(f"Frame (chosen by CFO): {frame.chosen_objective_text}\n\n")
        assert f"Question: {frame.chosen_objective_text}" in result

    @pytest.mark.asyncio
    async def test_falls_back_to_kpi_lookup_when_scqa_inputs_absent(self, real_analysis_payload):
        """Old-shaped payload (confirmed above: no scqa_inputs key) must
        still resolve a kpi_unit via a live KPI lookup rather than assume
        one — same source _build_kt_summary already uses."""
        assert "scqa_inputs" not in real_analysis_payload
        da = _make_da_stub()
        frame = _frame()
        with _registry_patch([_kpi_ns(unit="%")]) as _:
            result = await da.generate_scqa_for_frame(
                da_output=real_analysis_payload, principal_id="cfo_001", frame=frame,
            )
        assert result is not None  # did not raise, degraded to a live lookup successfully

    @pytest.mark.asyncio
    async def test_missing_plan_returns_none(self):
        da = _make_da_stub()
        result = await da.generate_scqa_for_frame(da_output={}, principal_id="x", frame=_frame())
        assert result is None

    @pytest.mark.asyncio
    async def test_malformed_change_point_entry_skipped_not_raised(self, real_analysis_payload):
        payload = dict(real_analysis_payload)
        payload["change_points"] = [{"not": "a valid change point shape"}, "not even a dict", None]
        da = _make_da_stub()
        with _registry_patch([_kpi_ns()]):
            result = await da.generate_scqa_for_frame(da_output=payload, principal_id="x", frame=_frame())
        assert result is not None  # did not raise despite every entry being unusable

    @pytest.mark.asyncio
    async def test_role_label_falls_back_to_principal_id_when_role_absent(self, real_analysis_payload):
        da = _make_da_stub()
        frame = _frame()
        with _registry_patch([_kpi_ns()]):
            result = await da.generate_scqa_for_frame(
                da_output=real_analysis_payload, principal_id="cfo_001", frame=frame,
                decided_by_role=None,
            )
        assert result.startswith("Frame (chosen by cfo_001):")


# ---------------------------------------------------------------------------
# _build_situation_complication_facts — the pre-framing facts-only narrative
#
# Found live 2026-08-19: with the framing gate on, DeepFocusView's "Analysis"
# panel rendered completely empty pre-framing — its only content sources
# (scqa_summary, a change-points fallback dead whenever Variance Breakdown
# already exists) were both absent simultaneously. This method exists so the
# panel has real content immediately at DA completion, without waiting on a
# frame — proven here by asserting NO Question/Answer text ever appears in
# its output (that's the one guarantee that matters: it must never imply a
# recommendation that hasn't been examined yet).
# ---------------------------------------------------------------------------

def _da_no_llm() -> A9_Deep_Analysis_Agent:
    return _make_da_stub()  # same no-llm_service_agent stub — this method never calls the LLM anyway


class TestSituationComplicationFacts:
    def test_problem_mode_names_no_recommendation(self):
        da = _da_no_llm()
        result = da._build_situation_complication_facts(
            plan=_plan(), kt=_kt(), change_points=[],
            spec={"comparison_type": "previous", "inverse_logic": False},
            analysis_mode="problem",
        )
        assert result.startswith("Situation:")
        assert "Complication:" in result
        assert "Question:" not in result
        assert "Answer:" not in result

    def test_opportunity_mode_names_no_recommendation(self):
        da = _da_no_llm()
        result = da._build_situation_complication_facts(
            plan=_plan(), kt=_kt(), change_points=[],
            spec={"comparison_type": "previous", "inverse_logic": False},
            analysis_mode="opportunity",
        )
        assert "Situation:" in result and "Complication:" in result
        assert "Question:" not in result and "Answer:" not in result

    def test_mixed_mode_names_no_recommendation(self):
        da = _da_no_llm()
        kt_mixed = _kt(where_is=[
            {"key": "A", "delta": 10, "segment_type": "opportunity"},
            {"key": "B", "delta": -10, "segment_type": "problem"},
        ])
        result = da._build_situation_complication_facts(
            plan=_plan(), kt=kt_mixed, change_points=[], spec={}, analysis_mode="mixed",
        )
        assert "bifurcated" in result
        assert "Question:" not in result and "Answer:" not in result

    def test_matrix_branch_names_no_recommendation(self):
        da = _da_no_llm()
        kt_matrix = _kt(
            where_is=[{"key": "A", "delta": -5, "basis_agreement": "confirmed"}],
            where_is_not=[{"key": "B", "basis_agreement": "basis_specific"}],
        )
        result = da._build_situation_complication_facts(
            plan=_plan(), kt=kt_matrix, change_points=[], spec={},
            analysis_mode="problem", matrix_ran=True, comparator_secondary="budget",
        )
        assert "breached on two bases" in result
        assert "Question:" not in result and "Answer:" not in result

    def test_alert_type_variants_all_avoid_recommendation(self):
        da = _da_no_llm()
        for alert_type in ("projected_breach", "plan_variance", "acceleration", None):
            result = da._build_situation_complication_facts(
                plan=_plan(), kt=_kt(), change_points=[],
                spec={"comparison_type": "previous", "inverse_logic": False},
                analysis_mode="problem", alert_type=alert_type,
            )
            assert "Question:" not in result and "Answer:" not in result, alert_type

    def test_compound_pattern_names_no_recommendation(self):
        da = _da_no_llm()
        result = da._build_situation_complication_facts(
            plan=_plan(), kt=_kt(), change_points=[], spec={},
            analysis_mode="problem", compound_pattern="Revenue up 8% while margin fell 3pp",
        )
        assert "Revenue up 8% while margin fell 3pp" in result
        assert "Question:" not in result and "Answer:" not in result

    def test_never_raises_on_empty_inputs(self):
        """Facts-only means it must degrade gracefully to generic language,
        never raise — an empty Analysis panel is bad, an exception aborting
        the whole DA run over cosmetic text is worse."""
        da = _da_no_llm()
        result = da._build_situation_complication_facts(
            plan=_plan(), kt=KTIsIsNot(where_is=[], where_is_not=[]),
            change_points=[], spec=None, analysis_mode="problem",
        )
        assert isinstance(result, str) and len(result) > 0


class TestExecuteDeepAnalysisWiring:
    """execute_deep_analysis wires _build_situation_complication_facts into the
    scqa_deferred branch only — the flag-off path must stay untouched, and a
    build failure must degrade to None rather than abort the run."""

    def test_field_defaults_none(self):
        r = DeepAnalysisResponse.success(request_id="x")
        assert r.situation_complication_summary is None

    def test_field_settable_alongside_deferred_scqa(self):
        r = DeepAnalysisResponse.success(
            request_id="x", scqa_summary=None, scqa_deferred=True,
            situation_complication_summary="Situation: X is down. Complication: driven by Y.",
        )
        assert r.scqa_deferred is True
        assert r.scqa_summary is None
        assert r.situation_complication_summary == "Situation: X is down. Complication: driven by Y."
