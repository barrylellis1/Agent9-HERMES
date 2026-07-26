"""
Phase 15 Stage C — context contract tests (llm_prompt_redesign_da_sf.md §3.2).

Follows the same stub-orchestrator pattern as
tests/integration/test_solution_finder_llm_debate.py, but captures every
prompt sent to A9_LLM_Service_Agent.analyze() so the actual PROMPT TEXT can
be asserted on, rather than just the parsed response shape.

Covers:
- decision_maker block + paired instruction reaches BOTH Stage 1 persona
  prompts and the synthesis prompt (previously: zero at Stage 1, unconsumed
  data at synthesis)
- principal.time_frame is actually wired into the prompt (previously framed
  but never extracted anywhere in the runtime)
- Cat 4 principal-adaptive framing branches correctly on role, and the M1
  invariant ("never change the conclusion") is stated explicitly
- strict tenancy: a missing business-context record produces the explicit
  disclaimer, never the old generic hardcoded business_terms/profit_center text
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent, initialize_agent_registry
from src.agents.models.solution_finder_models import SolutionFinderRequest, TradeOffCriterion


class _CapturingOrchestrator:
    """Stub orchestrator that returns canned synthesis output for every
    analyze() call while recording every prompt sent, so both Stage 1
    (per-persona) and synthesis prompts can be inspected afterward."""

    def __init__(self):
        self.captured_prompts: list[str] = []

    async def execute_agent_method(self, agent_name: str, method_name: str, params):
        if agent_name == "A9_LLM_Service_Agent" and method_name == "analyze":
            req = params.get("request")
            self.captured_prompts.append(getattr(req, "content", "") or "")
            # Stage 1 calls (request_id contains "_s1_") get a persona hypothesis shape;
            # the synthesis call gets the full options shape.
            req_id = getattr(req, "request_id", "")
            if "_s1_" in req_id:
                analysis = {
                    "persona_id": "mckinsey",
                    "framework": "MECE root-cause",
                    "hypothesis": "Cost driver concentrated in one segment",
                    "key_evidence": ["e1", "e2", "e3"],
                    "recommended_focus": "North Region",
                    "conviction": "High",
                    "proposed_option": {
                        "title": "Renegotiate supplier contracts",
                        "description": "Reduce COGS via supplier renegotiation",
                        "mechanism": "Direct cost reduction",
                        "time_horizon": "0-90 days",
                        "impact_estimate": {"metric": "Gross Margin", "unit": "%", "recovery_range": {"low": 1.0, "high": 2.0}, "basis": "..."},
                        "cost_signal": "Medium",
                        "risk_signal": "Low",
                    },
                }
            else:
                analysis = {
                    "problem_reframe": {"situation": "s", "complication": "c", "question": "q", "key_assumptions": []},
                    "options": [
                        {"id": "opt_1", "title": "Renegotiate supplier contracts", "expected_impact": 0.7, "cost": 0.3, "risk": 0.2},
                        {"id": "opt_2", "title": "Shift product mix", "expected_impact": 0.5, "cost": 0.4, "risk": 0.3},
                        {"id": "opt_3", "title": "Pricing realignment", "expected_impact": 0.6, "cost": 0.5, "risk": 0.4},
                    ],
                    "recommendation": {"id": "opt_1", "title": "Renegotiate supplier contracts"},
                    "recommendation_rationale": "Because margin pressure is concentrated in one supplier relationship.",
                    "unresolved_tensions": [],
                    "blind_spots": [],
                    "next_steps": [],
                    "cross_review": {},
                }
            return SimpleNamespace(
                status="success",
                request_id=req_id,
                analysis=analysis,
                model_used="mock-llm",
                usage={},
                confidence=0.9,
            )
        raise AssertionError(f"Unexpected call: {agent_name}.{method_name}")


async def _run_sf_with_principal_context(monkeypatch, principal_context: dict) -> _CapturingOrchestrator:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    orch = await A9_Orchestrator_Agent.create()
    await initialize_agent_registry()

    sf = await orch.create_agent_with_dependencies(
        "A9_Solution_Finder_Agent",
        # enable_hybrid_council is required for the Stage 1 parallel-persona path
        # (consulting_personas stays empty, and Stage 1 never runs, without it —
        # see the "using_hybrid_council" gate in recommend_actions).
        {"enable_llm_debate": True, "enable_hybrid_council": True},
    )
    await sf.connect(orch)

    stub = _CapturingOrchestrator()
    sf.orchestrator = stub

    req = SolutionFinderRequest(
        request_id=str(uuid.uuid4()),
        principal_id="cfo_001",
        problem_statement="Gross margin declined in North region vs plan",
        deep_analysis_output={"where": [{"dimension": "Region", "key": "North"}]},
        principal_context=principal_context,
        evaluation_criteria=[
            TradeOffCriterion(name="impact", weight=0.5),
            TradeOffCriterion(name="cost", weight=0.3),
            TradeOffCriterion(name="risk", weight=0.2),
        ],
    )
    resp = await sf.recommend_actions(req)
    assert getattr(resp, "status", "error") == "success", getattr(resp, "error_message", None)
    return stub


@pytest.mark.asyncio
async def test_decision_maker_reaches_synthesis_prompt_with_paired_instruction(monkeypatch):
    stub = await _run_sf_with_principal_context(monkeypatch, {
        "role": "CFO",
        "decision_style": "analytical",
        "current_focus": ["Gross margin recovery"],
        "time_frame": {"default_period": "QTD"},
    })

    synthesis_prompts = [p for p in stub.captured_prompts if "## INPUT DATA" in p]
    assert synthesis_prompts, "no synthesis-shaped prompt was captured"
    synth = synthesis_prompts[0]

    # The instruction, not just the data — this was the bug (finding #3 in the design doc)
    assert "DECISION MAKER" in synth
    assert "CFO" in synth
    assert "time_frame" in synth.lower() or "QTD" in synth  # previously-unwired field now present
    assert "prerequisites" in synth  # escalation-flagging instruction references the real field name


@pytest.mark.asyncio
async def test_decision_maker_reaches_stage1_persona_prompts(monkeypatch):
    stub = await _run_sf_with_principal_context(monkeypatch, {
        "role": "CFO",
        "decision_style": "analytical",
        "current_focus": ["Gross margin recovery"],
    })

    stage1_prompts = [p for p in stub.captured_prompts if "## DECISION MAKER\n" in p]
    assert stage1_prompts, "decision_maker block never reached a Stage 1 persona prompt"
    assert "advising the CFO directly" in stage1_prompts[0]


@pytest.mark.asyncio
async def test_low_detail_preference_gets_decision_first_framing(monkeypatch):
    # communication_style is sourced from the registry's real communication.detail_level
    # field (see A9_Principal_Context_Agent) — not a role-title keyword guess. A "CEO"
    # role string alone must NOT drive this branch; only the real preference should.
    stub = await _run_sf_with_principal_context(monkeypatch, {
        "role": "CEO", "decision_style": "visionary", "communication_style": "low",
    })
    synth = next(p for p in stub.captured_prompts if "## INPUT DATA" in p)
    assert "5-8 bullets" in synth
    # M1 invariant must be stated explicitly, not just implied
    assert "ENTRY POINT AND DEPTH ONLY" in synth
    assert "never let role adaptation" in synth


@pytest.mark.asyncio
async def test_high_detail_preference_gets_diagnostic_depth_framing(monkeypatch):
    stub = await _run_sf_with_principal_context(monkeypatch, {
        "role": "Regional Sales Director", "decision_style": "pragmatic", "communication_style": "high",
    })
    synth = next(p for p in stub.captured_prompts if "## INPUT DATA" in p)
    assert "diagnostic depth and implementation-level detail" in synth
    assert "5-8 bullets" not in synth


@pytest.mark.asyncio
async def test_role_string_alone_no_longer_drives_framing(monkeypatch):
    # Regression guard for the fix itself: a "CFO"/"CEO"-shaped role with NO
    # communication_style present must NOT get the decision-first branch just
    # because the title matches a hardcoded keyword — it must fall through to
    # the medium/default balanced framing.
    stub = await _run_sf_with_principal_context(monkeypatch, {"role": "CFO", "decision_style": "analytical"})
    synth = next(p for p in stub.captured_prompts if "## INPUT DATA" in p)
    assert "Balance decision-first framing" in synth
    assert "5-8 bullets" not in synth


@pytest.mark.asyncio
async def test_medium_detail_preference_gets_balanced_framing(monkeypatch):
    stub = await _run_sf_with_principal_context(monkeypatch, {"role": "CFO", "communication_style": "medium"})
    synth = next(p for p in stub.captured_prompts if "## INPUT DATA" in p)
    assert "Balance decision-first framing" in synth


@pytest.mark.asyncio
async def test_missing_business_context_gets_explicit_disclaimer_not_generic_fallback(monkeypatch):
    # No client_id resolvable anywhere -> Supabase lookup skipped -> old code path
    # used to silently inject fabricated "profit_center"/"customer_type" text.
    stub = await _run_sf_with_principal_context(monkeypatch, {"role": "CFO"})
    synth = next(p for p in stub.captured_prompts if "## INPUT DATA" in p)

    assert "No business context available" in synth
    # The old fabricated generic content must never appear again
    assert "Operational unit responsible for generating revenue" not in synth
    assert "Segment classification (Enterprise, SMB, Gov)" not in synth


@pytest.mark.asyncio
async def test_no_principal_context_does_not_crash_and_omits_decision_maker_section(monkeypatch):
    stub = await _run_sf_with_principal_context(monkeypatch, {})
    synth = next(p for p in stub.captured_prompts if "## INPUT DATA" in p)
    # No fabricated decision-maker guidance when nothing is known about the principal
    assert "DECISION MAKER — CONSUMPTION INSTRUCTIONS" not in synth
