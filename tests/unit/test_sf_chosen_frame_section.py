"""
Phase 19, Slice 7 — Solution Finder expresses the reframe (2026-08-18).

Without this, a recorded framing decision is displayed but never acted on —
the whole point of the feature would be hollow. `_build_chosen_frame_section`
reuses the SHAPE of the existing `stage1_allow_frame_challenge` branch (see
test_sf_frame_challenge_flag.py) — that branch phrases an alternative frame
as *permission*, already tested and found insufficient; this is the same
underlying idea driven by a *recorded decision* instead, which has never
been tested.

No separate config flag gates this (unlike stage1_allow_frame_challenge) —
the natural gate is data presence: `preferences.refinement_result.framing_decision`
can only be non-None once a principal has actually submitted the mandatory
gate, so testing "absent -> empty section -> byte-identical" IS the
flag-off-equivalent guard here.

Two tiers, same split as test_sf_stage_d_causal_grounding.py:
1. `_build_chosen_frame_section` as a pure function.
2. End-to-end: the section actually reaches BOTH the Stage 1 and synthesis
   prompts SF sends to the LLM service, via the same stub-orchestrator
   pattern (_CapturingOrchestrator) that file already established.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.agents.new.a9_solution_finder_agent import _build_chosen_frame_section
from src.agents.models.solution_finder_models import SolutionFinderRequest, TradeOffCriterion


# ---------------------------------------------------------------------------
# Tier 1 — _build_chosen_frame_section as a pure function
# ---------------------------------------------------------------------------

def _decision(**overrides):
    base = dict(
        choice="alternative", chosen_kpi_id="cogs",
        chosen_objective_text="Addressing base_oil_cost instead of gross_margin_pct directly",
        falsification_criterion="x",
    )
    base.update(overrides)
    return base


def test_none_produces_empty_section():
    assert _build_chosen_frame_section(None) == ""


def test_non_dict_produces_empty_section():
    assert _build_chosen_frame_section("not a dict") == ""
    assert _build_chosen_frame_section(["also", "not", "a", "dict"]) == ""


def test_missing_objective_text_produces_empty_section():
    d = _decision()
    del d["chosen_objective_text"]
    assert _build_chosen_frame_section(d) == ""


def test_blank_objective_text_produces_empty_section():
    assert _build_chosen_frame_section(_decision(chosen_objective_text="   ")) == ""


def test_confirm_stated_section_present_and_labeled_correctly():
    section = _build_chosen_frame_section(_decision(
        choice="confirm_stated", chosen_objective_text="Recovering Gross Margin %",
    ))
    assert "CHOSEN FRAME" in section
    assert "Recovering Gross Margin %" in section
    assert "confirmed this objective is correct" in section
    assert "MUST serve this objective" in section


def test_alternative_section_present_and_labeled_correctly():
    section = _build_chosen_frame_section(_decision(
        choice="alternative", chosen_objective_text="Addressing base_oil_cost exposure",
    ))
    assert "CHOSEN FRAME" in section
    assert "Addressing base_oil_cost exposure" in section
    assert "chose this objective instead of the KPI's own raw recovery" in section
    assert "MUST serve this objective" in section


def test_other_choice_gets_the_alternative_style_note():
    section = _build_chosen_frame_section(_decision(choice="other", chosen_objective_text="Something else entirely"))
    assert "chose this objective instead of the KPI's own raw recovery" in section


# ---------------------------------------------------------------------------
# Tier 2 — end to end: the section actually reaches both LLM prompts
# ---------------------------------------------------------------------------

class _CapturingOrchestrator:
    def __init__(self):
        self.captured_prompts: list[str] = []

    async def execute_agent_method(self, agent_name: str, method_name: str, params):
        if agent_name == "A9_LLM_Service_Agent" and method_name == "analyze":
            req = params.get("request")
            self.captured_prompts.append(getattr(req, "content", "") or "")
            return SimpleNamespace(
                status="success", request_id=getattr(req, "request_id", "test"),
                analysis={
                    "options": [{"id": "opt_1", "title": "Renegotiate supplier contracts",
                                 "expected_impact": 0.7, "cost": 0.3, "risk": 0.2}],
                    "recommendation": {"id": "opt_1", "title": "Renegotiate supplier contracts"},
                    "recommendation_rationale": "Because margin pressure is concentrated in one relationship.",
                    "problem_reframe": {"situation": "s", "complication": "c", "question": "q", "key_assumptions": []},
                    "unresolved_tensions": [], "blind_spots": [], "next_steps": [], "cross_review": {},
                },
                model_used="mock-llm", usage={}, confidence=0.9,
            )
        raise AssertionError(f"Unexpected call: {agent_name}.{method_name}")


async def _build_sf(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    from src.agents.new.a9_solution_finder_agent import A9_Solution_Finder_Agent
    sf = await A9_Solution_Finder_Agent.create({
        "enable_llm_debate": True,
        "enable_hybrid_council": True,  # required for Stage 1 to run at all
    })
    await sf.connect()
    stub = _CapturingOrchestrator()
    sf.orchestrator = stub
    return sf, stub


def _sf_request(*, framing_decision=None, client_id: str = "hess") -> SolutionFinderRequest:
    prefs = {}
    if framing_decision is not None:
        prefs["refinement_result"] = {"framing_decision": framing_decision}
    return SolutionFinderRequest(
        request_id=str(uuid.uuid4()), principal_id="cfo_001",
        problem_statement="Gross margin declined vs plan",
        deep_analysis_output={"plan": {"kpi_name": "Gross Margin %", "client_id": client_id}},
        client_id=client_id,
        preferences=prefs or None,
        evaluation_criteria=[TradeOffCriterion(name="impact", weight=0.5),
                              TradeOffCriterion(name="cost", weight=0.3),
                              TradeOffCriterion(name="risk", weight=0.2)],
    )


def _synthesis_prompt(stub) -> str:
    return next(p for p in stub.captured_prompts if "## INPUT DATA" in p)


def _stage1_prompts(stub) -> list[str]:
    return [p for p in stub.captured_prompts if "## PERSONA\n" in p]


@pytest.mark.asyncio
async def test_no_framing_decision_produces_byte_identical_prompts():
    """The control: absent framing_decision must never inject the section —
    matches how every pre-Phase-19 test in this file already ran."""
    monkeypatch = pytest.MonkeyPatch()
    try:
        sf, stub = await _build_sf(monkeypatch)
        resp = await sf.recommend_actions(_sf_request(framing_decision=None))
        assert resp.status == "success", getattr(resp, "error_message", None)
        assert "CHOSEN FRAME" not in _synthesis_prompt(stub)
        for p in _stage1_prompts(stub):
            assert "CHOSEN FRAME" not in p
    finally:
        monkeypatch.undo()


@pytest.mark.asyncio
async def test_framing_decision_reaches_synthesis_prompt():
    monkeypatch = pytest.MonkeyPatch()
    try:
        sf, stub = await _build_sf(monkeypatch)
        decision = _decision(chosen_objective_text="Addressing base_oil_cost exposure instead of gross_margin_pct directly")
        resp = await sf.recommend_actions(_sf_request(framing_decision=decision))
        assert resp.status == "success", getattr(resp, "error_message", None)

        synth = _synthesis_prompt(stub)
        assert "CHOSEN FRAME" in synth
        assert "Addressing base_oil_cost exposure instead of gross_margin_pct directly" in synth
        assert "MUST serve this objective" in synth
    finally:
        monkeypatch.undo()


@pytest.mark.asyncio
async def test_framing_decision_reaches_every_stage1_persona_prompt():
    """The actual point of this slice: each persona forms its hypothesis
    already knowing the chosen objective, not just synthesis reconciling
    after the fact."""
    monkeypatch = pytest.MonkeyPatch()
    try:
        sf, stub = await _build_sf(monkeypatch)
        decision = _decision(choice="confirm_stated", chosen_objective_text="Recovering Gross Margin %")
        resp = await sf.recommend_actions(_sf_request(framing_decision=decision))
        assert resp.status == "success", getattr(resp, "error_message", None)

        stage1_prompts = _stage1_prompts(stub)
        assert stage1_prompts, "Stage 1 never ran — enable_hybrid_council gate not satisfied"
        for p in stage1_prompts:
            assert "CHOSEN FRAME" in p
            assert "Recovering Gross Margin %" in p
    finally:
        monkeypatch.undo()
