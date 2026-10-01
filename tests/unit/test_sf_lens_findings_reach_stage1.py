"""Phase 22 addendum (2026-10-01) — what a lens learned must reach its hypothesis.

Three outcomes are possible for a lens probe, and ALL THREE have to arrive at
Stage 1:

  1. the warehouse answered its data_query   -> measured rows in the prompt
  2. the principal answered its question     -> the answer in the prompt
  3. nobody answered                         -> proceed, but record the gap as an
                                                ungrounded assumption

Before this, only (2) travelled. A lens's own answered query was returned to the
UI and then DROPPED before Stage 1 -- which makes the whole thing a
data-retrieval feature rather than a differentiation mechanism, since the
hypothesis never saw the evidence.

(3) is the owner's decision, 2026-10-01: an unknowable or slow-to-research
question must not block the analysis.
"""
import re
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.models.solution_finder_models import SolutionFinderRequest, TradeOffCriterion
from src.agents.new.a9_solution_finder_agent import A9_Solution_Finder_Agent, _format_lens_finding

LENS_COUNCIL = ["commercial", "operational", "structural"]
# Must match the agent's own section layout -- the lens block is deliberately
# inside "## PROBLEM" (single newlines), not a separate section.
_PROBLEM_SECTION = re.compile(r"## PROBLEM\n(.*?)\n\n", re.DOTALL)

FINDING = {
    "persona_id": "commercial", "kpi": "Cost of Goods Sold", "dimension": "Product Line",
    "timeframe": "year_to_date", "why": "separates input-cost inflation from mix migration",
    "rows": [{"product_line": "Engine Oils", "cogs_2026": 39359562.24, "yoy_pct": 12.3},
             {"product_line": "Coolants & Antifreeze", "cogs_2026": 9201637.75, "yoy_pct": 0.8}],
    "sql": "SELECT product_line, ... FROM `agent9-465818...`",
}


def _kpi(kpi_id, client_id, name="Gross Margin %"):
    return SimpleNamespace(id=kpi_id, client_id=client_id, name=name)


def _patched_provider():
    provider = MagicMock()
    provider.get_all.return_value = [_kpi("gross_margin_pct", "lubricants")]
    factory = MagicMock()
    factory.get_provider.return_value = provider
    return patch("src.registry.factory.RegistryFactory", return_value=factory)


class _CapturingOrchestrator:
    def __init__(self):
        self.sections: dict[str, str] = {}
        self.full: dict[str, str] = {}

    async def get_agent(self, name, *a, **k):
        return None

    async def execute_agent_method(self, agent_name, method_name, params):
        req = params.get("request")
        req_id = getattr(req, "request_id", "")
        content = getattr(req, "content", "") or ""
        m = re.search(r"_s1_(.+)$", req_id)
        pid = m.group(1) if m else "?"
        sec = _PROBLEM_SECTION.search(content)
        self.sections[pid] = sec.group(1) if sec else ""
        self.full[pid] = content
        return SimpleNamespace(
            status="success", request_id=req_id, model_used="mock", usage={}, confidence=0.9,
            analysis={
                "persona_id": pid, "framework": "MECE", "hypothesis": "h",
                "key_evidence": ["e1", "e2", "e3"], "recommended_focus": "Engine Oils",
                "conviction": "High",
                "proposed_option": {
                    "title": "t", "mechanism": "m", "description": "d",
                    "time_horizon": "0-90 days",
                    "impact_estimate": {"metric": "Gross Margin", "unit": "%",
                                        "recovery_range": {"low": 1.0, "high": 2.0}, "basis": "b"},
                    "cost_signal": "Medium", "risk_signal": "Low",
                },
            })


async def _build_sf(monkeypatch, stub):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    sf = await A9_Solution_Finder_Agent.create({
        "enable_llm_debate": True, "enable_hybrid_council": True,
        "enable_causal_grounding": False,
    })
    await sf.connect()
    sf.orchestrator = stub
    sf.llm_service_agent = None
    return sf


def _request(**prefs_extra):
    prefs = {"debate_stage": "stage1_only", "consulting_personas": LENS_COUNCIL}
    prefs.update(prefs_extra)
    return SolutionFinderRequest(
        request_id=str(uuid.uuid4()), principal_id="cfo_001",
        problem_statement="Gross margin declined vs prior year",
        deep_analysis_output={"plan": {"kpi_name": "Gross Margin %", "client_id": "lubricants"}},
        client_id="lubricants", preferences=prefs,
        evaluation_criteria=[TradeOffCriterion(name="impact", weight=0.5),
                             TradeOffCriterion(name="cost", weight=0.3),
                             TradeOffCriterion(name="risk", weight=0.2)],
    )


async def _run(sf, request):
    with _patched_provider(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_causal_neighbourhood = AsyncMock(return_value=[])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[])
        return await sf.recommend_actions(request)


class TestFindingsReachStage1:
    @pytest.mark.asyncio
    async def test_measured_rows_reach_the_asking_persona(self, monkeypatch):
        stub = _CapturingOrchestrator()
        sf = await _build_sf(monkeypatch, stub)
        await _run(sf, _request(lens_findings={"commercial": FINDING}))

        sec = stub.sections["commercial"]
        assert "Engine Oils" in sec, "the measured rows must reach the hypothesis prompt"
        assert "12.3" in sec
        assert "MEASURED RESULT" in sec, "must be labelled as measured, not blended into context"

    @pytest.mark.asyncio
    async def test_a_finding_goes_only_to_the_lens_that_asked(self, monkeypatch):
        """Evidence is per-lens. Broadcasting one lens's query result to all
        three would manufacture the agreement the council exists to avoid."""
        stub = _CapturingOrchestrator()
        sf = await _build_sf(monkeypatch, stub)
        await _run(sf, _request(lens_findings={"commercial": FINDING}))
        assert "Engine Oils" in stub.sections["commercial"]
        for other in ("operational", "structural"):
            assert "Engine Oils" not in stub.sections[other]

    @pytest.mark.asyncio
    async def test_unanswered_question_becomes_an_explicit_assumption_instruction(self, monkeypatch):
        """Owner decision: proceed rather than block -- but the hypothesis must
        KNOW it is resting on something unverified."""
        stub = _CapturingOrchestrator()
        sf = await _build_sf(monkeypatch, stub)
        await _run(sf, _request(
            lens_open_questions={"structural": "Did finance change costing allocation in Q3?"},
            lens_refinement={},  # nobody answered
        ))
        sec = stub.sections["structural"]
        assert "UNANSWERED" in sec
        assert "costing allocation" in sec
        assert "grounded=false" in sec, "must be recorded as an ungrounded assumption"
        assert "human_confirmation" in sec

    @pytest.mark.asyncio
    async def test_an_answered_question_is_not_marked_unanswered(self, monkeypatch):
        stub = _CapturingOrchestrator()
        sf = await _build_sf(monkeypatch, stub)
        await _run(sf, _request(
            lens_open_questions={"structural": "Did finance change costing allocation in Q3?"},
            lens_refinement={"structural": "No, methodology was unchanged all year."},
        ))
        sec = stub.sections["structural"]
        assert "methodology was unchanged" in sec
        assert "UNANSWERED" not in sec

    @pytest.mark.asyncio
    async def test_no_probe_data_leaves_the_prompt_untouched(self, monkeypatch):
        stub = _CapturingOrchestrator()
        sf = await _build_sf(monkeypatch, stub)
        await _run(sf, _request())
        for pid in LENS_COUNCIL:
            assert stub.sections[pid].strip() == "Gross margin declined vs prior year"


class TestFindingFormatter:
    def test_empty_rows_are_not_dressed_up_as_evidence(self):
        out = _format_lens_finding("Commercial Lens", {"kpi": "COGS", "rows": []})
        assert "absence of evidence, not evidence of absence" in out

    def test_rows_are_capped_and_the_omission_disclosed(self):
        out = _format_lens_finding("X", {"kpi": "K", "rows": [{"i": i} for i in range(40)]}, max_rows=5)
        assert "further rows omitted" in out, "a silent truncation would misrepresent the result"

    def test_non_dict_is_survivable(self):
        assert _format_lens_finding("X", None) == ""
