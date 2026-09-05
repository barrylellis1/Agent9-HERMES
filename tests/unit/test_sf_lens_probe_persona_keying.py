"""
Phase 22 Stage B — the load-bearing fix: ps_s1 stops being persona-invariant.

Before this, `ps_s1` (the "## PROBLEM" section every Stage 1 persona call
receives) was computed exactly ONCE, closed over by all three `_run_stage1(p)`
calls — the code's own prior comment named it "computed ONCE here
(persona-invariant text)". Refinement's diagnostic groundwork was locked in
identically for commercial/operational/structural (or mckinsey/bcg/bain)
before any lens or framework existed to shape it — the root cause behind
Stage 1 hypotheses that named three different frameworks but converged on
generic, near-identical reasoning (confirmed against
frontier_bakeoff_2026-09-04/astra/run_01).

These tests capture the ACTUAL prompt text sent to each persona's Stage 1
call (request_id is `{req_id}_s1_{persona_id}`, so the persona is identifiable
without trusting the model's own self-identification) and assert:

- with different `preferences.lens_refinement` answers per persona, the three
  captured "## PROBLEM" sections are genuinely different strings — the thing
  that was structurally impossible before this fix
- with NO lens_refinement supplied (today's production shape, until Stage C
  ships), all three stay identical — this fix must not silently change
  behavior for callers that haven't adopted lens probing yet
- a persona absent from lens_refinement falls back to the shared base text,
  not an empty/broken prompt — partial adoption must degrade gracefully
"""
from __future__ import annotations

import re
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.models.solution_finder_models import SolutionFinderRequest, TradeOffCriterion
from src.agents.new.a9_solution_finder_agent import A9_Solution_Finder_Agent


def _kpi(kpi_id, client_id, name="Gross Margin %"):
    return SimpleNamespace(id=kpi_id, client_id=client_id, name=name)


def _patched_provider_for_e2e():
    provider = MagicMock()
    provider.get_all.return_value = [_kpi("gross_margin_pct", "lubricants")]
    factory = MagicMock()
    factory.get_provider.return_value = provider
    return patch("src.registry.factory.RegistryFactory", return_value=factory)


_PROBLEM_SECTION = re.compile(r"## PROBLEM\n(.*?)\n\n", re.DOTALL)


class _CapturingOrchestrator:
    """Stage 1 only — returns a minimal valid hypothesis for any persona,
    keyed by the persona id embedded in request_id (`{req_id}_s1_{persona_id}`,
    a9_solution_finder_agent.py) rather than trusting the model's own
    self-identification, same discipline the agent's own attribution
    handling already follows."""

    def __init__(self):
        self.problem_sections_by_persona: dict[str, str] = {}

    async def execute_agent_method(self, agent_name: str, method_name: str, params):
        assert agent_name == "A9_LLM_Service_Agent" and method_name == "analyze"
        req = params.get("request")
        req_id = getattr(req, "request_id", "")
        content = getattr(req, "content", "") or ""

        m = re.search(r"_s1_(.+)$", req_id)
        persona_id = m.group(1) if m else "?"
        section = _PROBLEM_SECTION.search(content)
        self.problem_sections_by_persona[persona_id] = section.group(1) if section else ""

        analysis = {
            "persona_id": persona_id, "framework": "MECE", "hypothesis": "h",
            "key_evidence": ["e1", "e2", "e3"], "recommended_focus": "Chain A",
            "conviction": "High",
            "proposed_option": {
                "title": "Reprice anchor accounts", "mechanism": "Margin recovery",
                "description": "d", "time_horizon": "0-90 days",
                "impact_estimate": {"metric": "Gross Margin", "unit": "%",
                                    "recovery_range": {"low": 1.0, "high": 2.0}, "basis": "..."},
                "cost_signal": "Medium", "risk_signal": "Low",
            },
        }
        return SimpleNamespace(status="success", request_id=req_id, analysis=analysis,
                               model_used="mock-llm", usage={}, confidence=0.9)


async def _build_sf(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    sf = await A9_Solution_Finder_Agent.create({
        "enable_llm_debate": True,
        "enable_hybrid_council": True,
        "enable_causal_grounding": False,
    })
    await sf.connect()
    return sf


def _sf_request(*, personas: list[str], lens_refinement: dict | None) -> SolutionFinderRequest:
    # stage1_only stops after Stage 1 (_skip_synthesis_llm=True) -- exactly the
    # production first dispatch. "hypothesis" would proceed to a synthesis call
    # this stub doesn't handle.
    prefs = {"debate_stage": "stage1_only", "consulting_personas": personas}
    if lens_refinement is not None:
        prefs["lens_refinement"] = lens_refinement
    return SolutionFinderRequest(
        request_id=str(uuid.uuid4()), principal_id="cfo_001",
        problem_statement="Gross margin declined vs prior year",
        deep_analysis_output={"plan": {"kpi_name": "Gross Margin %", "client_id": "lubricants"}},
        client_id="lubricants",
        preferences=prefs,
        evaluation_criteria=[TradeOffCriterion(name="impact", weight=0.5),
                             TradeOffCriterion(name="cost", weight=0.3),
                             TradeOffCriterion(name="risk", weight=0.2)],
    )


async def _run(sf, stub, request):
    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_causal_neighbourhood = AsyncMock(return_value=[])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[])
        return await sf.recommend_actions(request)


LENS_COUNCIL = ["commercial", "operational", "structural"]


@pytest.mark.asyncio
async def test_different_lens_answers_produce_different_stage1_prompts(monkeypatch):
    """The fix, proven directly: three personas, three different lens-probe
    answers, three genuinely different ## PROBLEM sections. Before this stage
    ps_s1 was one string shared by all three _run_stage1(p) closures — this
    was structurally impossible to produce."""
    sf = await _build_sf(monkeypatch)
    stub = _CapturingOrchestrator()
    sf.orchestrator = stub
    sf.llm_service_agent = None

    lens_refinement = {
        "commercial": "The decline is concentrated in anchor accounts under price-lock.",
        "operational": "Base oil cost inflation has not yet been hedged for Q3.",
        "structural": "Value-tier grades may be structurally declining, not cyclically dipping.",
    }
    resp = await _run(sf, stub, _sf_request(personas=LENS_COUNCIL, lens_refinement=lens_refinement))

    assert resp.status == "success"
    sections = stub.problem_sections_by_persona
    assert set(sections) == set(LENS_COUNCIL)

    # Every persona's answer text reached its OWN section...
    for persona_id, answer in lens_refinement.items():
        assert answer in sections[persona_id], (
            f"{persona_id}'s lens-probe answer never reached its own Stage 1 prompt"
        )
    # ...and NOT any other persona's — this is the actual differentiation, not
    # just "the field is present somewhere."
    assert sections["commercial"] != sections["operational"] != sections["structural"]
    assert lens_refinement["commercial"] not in sections["operational"]
    assert lens_refinement["operational"] not in sections["structural"]
    assert lens_refinement["structural"] not in sections["commercial"]


@pytest.mark.asyncio
async def test_no_lens_refinement_keeps_todays_shared_behavior(monkeypatch):
    """Callers that haven't adopted lens probing yet (today's production shape,
    until Stage C ships) must see NO behavior change: all three personas still
    get the identical shared refined-problem text."""
    sf = await _build_sf(monkeypatch)
    stub = _CapturingOrchestrator()
    sf.orchestrator = stub
    sf.llm_service_agent = None

    resp = await _run(sf, stub, _sf_request(personas=LENS_COUNCIL, lens_refinement=None))

    assert resp.status == "success"
    sections = stub.problem_sections_by_persona
    assert set(sections) == set(LENS_COUNCIL)
    values = list(sections.values())
    assert values[0] == values[1] == values[2], (
        "with no lens_refinement supplied, all three personas must still "
        "receive identical text -- this fix must not change default behavior"
    )


@pytest.mark.asyncio
async def test_partial_lens_refinement_falls_back_gracefully_per_persona(monkeypatch):
    """A persona absent from lens_refinement (partial answer, or Stage C not
    yet driving all three) falls back to the shared base text -- not an
    empty or broken prompt. Skip support proper is Phase 23; this is the
    degrade-gracefully floor Stage B already provides for free."""
    sf = await _build_sf(monkeypatch)
    stub = _CapturingOrchestrator()
    sf.orchestrator = stub
    sf.llm_service_agent = None

    lens_refinement = {"commercial": "Anchor accounts are under price-lock."}
    resp = await _run(sf, stub, _sf_request(personas=LENS_COUNCIL, lens_refinement=lens_refinement))

    assert resp.status == "success"
    sections = stub.problem_sections_by_persona
    assert "Anchor accounts are under price-lock." in sections["commercial"]
    # operational/structural got no lens answer -> fall back to the SAME
    # shared base text as each other (not broken, not empty).
    assert sections["operational"] == sections["structural"]
    assert sections["operational"]  # non-empty
    assert "Anchor accounts are under price-lock." not in sections["operational"]
