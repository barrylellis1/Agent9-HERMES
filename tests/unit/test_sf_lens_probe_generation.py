"""
Phase 22 Stage B — lens-probe question generation (debate_stage="lens_probe").

One framework-anchored question per persona, generated in parallel via
asyncio.gather -- the exact concurrency pattern _run_stage1 already uses for
its own three per-persona calls, one stage earlier. Sits before Stage 1's own
(heavier) setup: needs only the refined problem + dataset recap, not the
Stage-1-specific da_compact_s1/bc_compact_s1 blobs assembled further down.

These tests capture the ACTUAL prompt sent per persona (request_id is
`{req_id}_lensprobe_{persona_id}`) and assert:
- all three personas get a question, generated concurrently (not serially)
- each persona's own real methodology.frameworks reached its own prompt
- a persona whose LLM call fails degrades to no question for that persona,
  not a broken response for the other two or a failed run overall
- the early return skips Stage 1 and synthesis entirely -- no options,
  no LLM calls beyond the three probe calls
"""
from __future__ import annotations

import asyncio
import re
import time
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


class _CapturingLensProbeOrchestrator:
    """Answers ONLY lens-probe calls (request_id contains "_lensprobe_"); any
    other call is a test-design error -- the early return must never reach
    Stage 1 or synthesis. `delay` simulates real latency so a serial-vs-
    parallel timing assertion is meaningful rather than trivially true."""

    def __init__(self, *, fail_persona: str | None = None, delay: float = 0.05):
        self.captured: dict[str, str] = {}
        self.call_count = 0
        self._fail_persona = fail_persona
        self._delay = delay

    async def execute_agent_method(self, agent_name: str, method_name: str, params):
        assert agent_name == "A9_LLM_Service_Agent" and method_name == "analyze"
        req = params.get("request")
        req_id = getattr(req, "request_id", "")
        assert "_lensprobe_" in req_id, f"unexpected call reached Stage 1/synthesis: {req_id}"
        self.call_count += 1

        await asyncio.sleep(self._delay)

        persona_id = req_id.rsplit("_lensprobe_", 1)[-1]
        self.captured[persona_id] = getattr(req, "content", "") or ""

        if self._fail_persona and persona_id == self._fail_persona:
            return SimpleNamespace(status="error", request_id=req_id, analysis=None,
                                   model_used="mock-llm", usage={})

        return SimpleNamespace(
            status="success", request_id=req_id,
            analysis={"question": f"What does {persona_id} need to know first?"},
            model_used="mock-llm", usage={},
        )


async def _build_sf(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    sf = await A9_Solution_Finder_Agent.create({
        "enable_llm_debate": True,
        "enable_hybrid_council": True,
        "enable_causal_grounding": False,
    })
    await sf.connect()
    return sf


def _sf_request(*, personas: list[str]) -> SolutionFinderRequest:
    return SolutionFinderRequest(
        request_id=str(uuid.uuid4()), principal_id="cfo_001",
        problem_statement="Gross margin declined vs prior year",
        deep_analysis_output={"plan": {"kpi_name": "Gross Margin %", "client_id": "lubricants"}},
        client_id="lubricants",
        preferences={"debate_stage": "lens_probe", "consulting_personas": personas},
        evaluation_criteria=[TradeOffCriterion(name="impact", weight=0.5),
                             TradeOffCriterion(name="cost", weight=0.3),
                             TradeOffCriterion(name="risk", weight=0.2)],
    )


async def _run(sf, request):
    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_causal_neighbourhood = AsyncMock(return_value=[])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[])
        return await sf.recommend_actions(request)


LENS_COUNCIL = ["commercial", "operational", "structural"]


@pytest.mark.asyncio
async def test_generates_one_question_per_persona(monkeypatch):
    sf = await _build_sf(monkeypatch)
    stub = _CapturingLensProbeOrchestrator()
    sf.orchestrator = stub
    sf.llm_service_agent = None

    resp = await _run(sf, _sf_request(personas=LENS_COUNCIL))

    assert resp.status == "success"
    assert set(resp.lens_probe_questions) == set(LENS_COUNCIL)
    for pid in LENS_COUNCIL:
        assert resp.lens_probe_questions[pid]  # non-empty


@pytest.mark.asyncio
async def test_each_personas_own_real_frameworks_reach_its_own_prompt(monkeypatch):
    """Not invented for the probe: the SAME methodology.frameworks Stage 1
    already receives via to_prompt_context(), reaching the model one stage
    earlier where it can shape what gets asked."""
    sf = await _build_sf(monkeypatch)
    stub = _CapturingLensProbeOrchestrator()
    sf.orchestrator = stub
    sf.llm_service_agent = None

    await _run(sf, _sf_request(personas=LENS_COUNCIL))

    # Each lens's own real, distinct methodology anchor (consulting_personas_
    # registry.yaml) shows up in its OWN prompt, not a sibling's.
    assert "Price-Volume-Mix Decomposition" in stub.captured["commercial"]
    assert "Cost-to-Serve Analysis" in stub.captured["operational"]
    assert "Reallocation / Exit Economics" in stub.captured["structural"]
    assert "Price-Volume-Mix Decomposition" not in stub.captured["operational"]
    assert "Reallocation / Exit Economics" not in stub.captured["commercial"]


@pytest.mark.asyncio
async def test_probes_run_concurrently_not_serially(monkeypatch):
    """asyncio.gather, mirroring _run_stage1's own pattern -- 3 calls at
    ~50ms each must complete in ~1 call's worth of wall time, not 3."""
    sf = await _build_sf(monkeypatch)
    stub = _CapturingLensProbeOrchestrator(delay=0.05)
    sf.orchestrator = stub
    sf.llm_service_agent = None

    t0 = time.perf_counter()
    await _run(sf, _sf_request(personas=LENS_COUNCIL))
    elapsed = time.perf_counter() - t0

    assert stub.call_count == 3
    assert elapsed < 0.12, f"took {elapsed:.3f}s -- looks serial (3x0.05s), not gathered"


@pytest.mark.asyncio
async def test_one_persona_failing_does_not_break_the_others(monkeypatch):
    """Non-fatal by design, same discipline as the critic pass: one bad call
    must not block the other two personas or fail the whole request."""
    sf = await _build_sf(monkeypatch)
    stub = _CapturingLensProbeOrchestrator(fail_persona="operational")
    sf.orchestrator = stub
    sf.llm_service_agent = None

    resp = await _run(sf, _sf_request(personas=LENS_COUNCIL))

    assert resp.status == "success"
    assert set(resp.lens_probe_questions) == {"commercial", "structural"}
    assert "operational" not in resp.lens_probe_questions


@pytest.mark.asyncio
async def test_early_return_never_reaches_stage1_or_synthesis(monkeypatch):
    """The orchestrator stub asserts this on every call already (any non-
    lens-probe call raises); a clean run with exactly 3 calls is the
    positive half of that guarantee."""
    sf = await _build_sf(monkeypatch)
    stub = _CapturingLensProbeOrchestrator()
    sf.orchestrator = stub
    sf.llm_service_agent = None

    resp = await _run(sf, _sf_request(personas=LENS_COUNCIL))

    assert stub.call_count == 3  # exactly the 3 probes, nothing more
    assert resp.options_ranked == []
    assert resp.analysis_degraded is False


class _TwoStageOrchestrator:
    """Answers BOTH a lens_probe call and the stage1_only calls that follow
    it -- the actual two-dispatch sequence Stage C's UI will drive. Proves
    the round trip end to end: generated questions -> (fake) answers fed back
    as lens_refinement -> genuinely different Stage 1 prompts per persona."""

    def __init__(self):
        self.stage1_sections: dict[str, str] = {}

    async def execute_agent_method(self, agent_name: str, method_name: str, params):
        assert agent_name == "A9_LLM_Service_Agent" and method_name == "analyze"
        req = params.get("request")
        req_id = getattr(req, "request_id", "")
        content = getattr(req, "content", "") or ""

        if "_lensprobe_" in req_id:
            persona_id = req_id.rsplit("_lensprobe_", 1)[-1]
            return SimpleNamespace(
                status="success", request_id=req_id,
                analysis={"question": f"[{persona_id}] what should I know first?"},
                model_used="mock-llm", usage={},
            )

        assert "_s1_" in req_id, f"unexpected call: {req_id}"
        persona_id = req_id.rsplit("_s1_", 1)[-1]
        m = re.search(r"## PROBLEM\n(.*?)\n\n", content, re.DOTALL)
        self.stage1_sections[persona_id] = m.group(1) if m else ""
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
                               model_used="mock-llm", usage={})


@pytest.mark.asyncio
async def test_full_round_trip_questions_to_answers_to_differentiated_stage1(monkeypatch):
    """The actual two-dispatch sequence: generate questions, feed answers back
    as lens_refinement, confirm Stage 1 genuinely differentiates -- the whole
    point of Phase 22 Stage B, proven end to end rather than piecewise."""
    sf = await _build_sf(monkeypatch)
    stub = _TwoStageOrchestrator()
    sf.orchestrator = stub
    sf.llm_service_agent = None

    probe_resp = await _run(sf, _sf_request(personas=LENS_COUNCIL))
    assert set(probe_resp.lens_probe_questions) == set(LENS_COUNCIL)

    # Stage C's UI would collect real answers here; this test's stand-in
    # answers are deliberately keyed by persona so the round trip is provable.
    fake_answers = {
        pid: f"My answer to: {probe_resp.lens_probe_questions[pid]}"
        for pid in LENS_COUNCIL
    }

    stage1_req = _sf_request(personas=LENS_COUNCIL)
    stage1_req.preferences["debate_stage"] = "stage1_only"
    stage1_req.preferences["lens_refinement"] = fake_answers

    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_causal_neighbourhood = AsyncMock(return_value=[])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[])
        stage1_resp = await sf.recommend_actions(stage1_req)

    assert stage1_resp.status == "success"
    sections = stub.stage1_sections
    assert set(sections) == set(LENS_COUNCIL)
    for pid in LENS_COUNCIL:
        assert fake_answers[pid] in sections[pid]
    assert sections["commercial"] != sections["operational"] != sections["structural"]
