"""Phase 22 addendum (2026-10-01) — bounded lens follow-up rounds.

This is where a lookup becomes an investigation: the valuable question is
usually the one the FIRST answer makes askable — "3 of 5 compressed, 2 held;
what is different about the 2?" — and it cannot be asked up front.

The risk being managed is the inverse of the convergence problem that started
Phase 22. A lens with a framework asks questions its framework favours; iterate
and it compounds, arriving more confident rather than more correct. So the cap
is a hard integer the model cannot argue with, and "done" is offered as the
expected answer rather than a failure.
"""
import re
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.models.solution_finder_models import SolutionFinderRequest, TradeOffCriterion
from src.agents.new.a9_solution_finder_agent import A9_Solution_Finder_Agent, _format_lens_finding

LENS_COUNCIL = ["commercial"]
DATA_Q = {"kind": "data_query", "kpi": "Gross Margin %", "dimension": "Product Line",
          "timeframe": "year_to_date", "why": "first look"}
FOLLOW_Q = {"kind": "data_query", "kpi": "Gross Margin %", "dimension": "Channel",
            "timeframe": "year_to_date", "why": "what is different about the two that held"}
DONE = {"kind": "done", "why": "the cost story is sufficient"}


def _kpi(kpi_id="gross_margin_pct", client_id="lubricants", name="Gross Margin %"):
    return SimpleNamespace(id=kpi_id, client_id=client_id, name=name, data_product_id="dp_x")


def _patched_provider():
    provider = MagicMock()
    provider.get_all.return_value = [_kpi()]
    factory = MagicMock()
    factory.get_provider.return_value = provider
    return patch("src.registry.factory.RegistryFactory", return_value=factory)


def _dpa():
    d = MagicMock()
    d.get_kpi_definition = AsyncMock(return_value=_kpi())
    d.generate_sql_for_kpi = AsyncMock(return_value={"success": True, "sql": "SELECT 1"})
    d.execute_sql = AsyncMock(return_value={"success": True, "rows": [{"v": 1}]})
    return d


class _Orch:
    """Replies by request_id: the probe gets `first`, each follow-up round gets
    the next scripted verdict (last one repeats)."""

    def __init__(self, first, followups, dpa):
        self.first = first
        self.followups = followups
        self.dpa = dpa
        self.followup_calls = 0

    async def get_agent(self, name, *a, **k):
        return self.dpa if name == "A9_Data_Product_Agent" else None

    async def execute_agent_method(self, agent_name, method_name, params):
        req = params.get("request")
        rid = getattr(req, "request_id", "")
        if "_lensfollowup" in rid:
            idx = int(re.search(r"_lensfollowup(\d+)_", rid).group(1))
            self.followup_calls += 1
            verdict = self.followups[min(idx, len(self.followups) - 1)] if self.followups else DONE
        else:
            verdict = self.first
        return SimpleNamespace(status="success", request_id=rid, analysis=verdict,
                               model_used="mock", usage={})


async def _build_sf(monkeypatch, orch, *, max_followups=1):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    sf = await A9_Solution_Finder_Agent.create({
        "enable_llm_debate": True, "enable_hybrid_council": True,
        "enable_causal_grounding": False, "lens_probe_max_followups": max_followups,
    })
    await sf.connect()
    sf.orchestrator = orch
    sf.llm_service_agent = None
    return sf


def _request():
    return SolutionFinderRequest(
        request_id=str(uuid.uuid4()), principal_id="cfo_001",
        problem_statement="Gross margin declined vs prior year",
        deep_analysis_output={"plan": {"kpi_name": "Gross Margin %", "client_id": "lubricants"}},
        client_id="lubricants",
        preferences={"debate_stage": "lens_probe", "consulting_personas": LENS_COUNCIL},
        evaluation_criteria=[TradeOffCriterion(name="impact", weight=0.5),
                             TradeOffCriterion(name="cost", weight=0.3),
                             TradeOffCriterion(name="risk", weight=0.2)],
    )


async def _run(sf):
    with _patched_provider(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_causal_neighbourhood = AsyncMock(return_value=[])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[])
        return await sf.recommend_actions(_request())


def _finding(resp):
    return (getattr(resp, "lens_probe_findings", None) or {}).get("commercial") or {}


class TestFollowUps:
    @pytest.mark.asyncio
    async def test_a_lens_can_ask_again_after_seeing_its_answer(self, monkeypatch):
        orch = _Orch(DATA_Q, [FOLLOW_Q], _dpa())
        sf = await _build_sf(monkeypatch, orch, max_followups=1)
        fu = _finding(await _run(sf)).get("follow_ups") or []
        assert len(fu) == 1
        assert "two that held" in fu[0]["why"]

    @pytest.mark.asyncio
    async def test_done_is_honoured_and_costs_nothing_further(self, monkeypatch):
        """The expected outcome. A lens saying 'no' must not be retried."""
        orch = _Orch(DATA_Q, [DONE], _dpa())
        sf = await _build_sf(monkeypatch, orch, max_followups=3)
        assert (_finding(await _run(sf)).get("follow_ups") or []) == []
        assert orch.followup_calls == 1, "must stop asking after the first 'done'"

    @pytest.mark.asyncio
    async def test_cap_binds_even_when_the_lens_never_stops(self, monkeypatch):
        """The guard that matters. A lens that always wants one more must be
        stopped by the cap, not by its own judgement."""
        orch = _Orch(DATA_Q, [FOLLOW_Q], _dpa())  # always asks again
        sf = await _build_sf(monkeypatch, orch, max_followups=2)
        fu = _finding(await _run(sf)).get("follow_ups") or []
        assert len(fu) == 2, "exactly the cap, never more"
        assert orch.followup_calls == 2

    @pytest.mark.asyncio
    async def test_zero_disables_follow_up_entirely(self, monkeypatch):
        orch = _Orch(DATA_Q, [FOLLOW_Q], _dpa())
        sf = await _build_sf(monkeypatch, orch, max_followups=0)
        assert (_finding(await _run(sf)).get("follow_ups") or []) == []
        assert orch.followup_calls == 0, "no LLM spend when disabled"

    @pytest.mark.asyncio
    async def test_a_failed_followup_keeps_the_first_finding(self, monkeypatch):
        """Non-fatal: a broken follow-up must not discard what round 1 learned."""
        dpa = _dpa()
        dpa.execute_sql = AsyncMock(side_effect=[
            {"success": True, "rows": [{"v": 1}]},   # first query succeeds
            Exception("warehouse blew up"),           # follow-up fails
        ])
        orch = _Orch(DATA_Q, [FOLLOW_Q], dpa)
        sf = await _build_sf(monkeypatch, orch, max_followups=1)
        f = _finding(await _run(sf))
        assert f.get("rows"), "the original finding must survive"
        assert (f.get("follow_ups") or []) == []


class TestFollowUpRendering:
    def test_followups_are_labelled_not_flattened(self):
        """A lens that asked again did a different thing from one that asked
        once; the hypothesis should be able to tell."""
        out = _format_lens_finding("Commercial Lens", {
            "kpi": "Gross Margin %", "rows": [{"a": 1}],
            "follow_ups": [{"kpi": "Gross Margin %", "dimension": "Channel",
                            "why": "which held", "rows": [{"b": 2}]}],
        })
        assert "Follow-up 1" in out
        assert "which held" in out
        assert "'b': 2" in out or '"b": 2' in out

    def test_no_followups_renders_unchanged(self):
        out = _format_lens_finding("X", {"kpi": "K", "rows": [{"a": 1}]})
        assert "Follow-up" not in out

    def test_empty_followup_rows_are_not_dressed_up(self):
        out = _format_lens_finding("X", {"kpi": "K", "rows": [{"a": 1}],
                                         "follow_ups": [{"kpi": "K", "rows": []}]})
        assert "absence of evidence" in out
