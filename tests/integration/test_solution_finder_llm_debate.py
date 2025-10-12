import asyncio
import uuid
from types import SimpleNamespace

import pytest

from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent, initialize_agent_registry
from src.agents.models.solution_finder_models import SolutionFinderRequest, TradeOffCriterion


@pytest.mark.asyncio
async def test_solution_finder_llm_debate_path(monkeypatch):
    # Ensure LLM service can initialize
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    # Orchestrator and registry init
    orch = await A9_Orchestrator_Agent.create()
    await initialize_agent_registry()

    # Create Solution Finder with LLM debate enabled
    sf = await orch.create_agent_with_dependencies(
        "A9_Solution_Finder_Agent",
        {"enable_llm_debate": True}
    )
    # Ensure agent connected with orchestrator reference
    await sf.connect(orch)

    # Stub orchestrator on the agent instance to deterministically exercise LLM path
    class _StubOrchestrator:
        async def execute_agent_method(self, agent_name: str, method_name: str, params):
            if agent_name == "A9_LLM_Service_Agent" and method_name == "analyze":
                req = params.get("request")
                return SimpleNamespace(
                    status="success",
                    request_id=getattr(req, "request_id", "test"),
                    analysis={
                        "options": [
                            {"id": "optA", "title": "QA fast-track", "expected_impact": 0.8, "cost": 0.3, "risk": 0.4},
                            {"id": "optB", "title": "Shift capacity", "expected_impact": 0.7, "cost": 0.2, "risk": 0.3},
                        ],
                        "consensus_rationale": "Consensus to fast-track QA fixes",
                        "transcript": [{"persona": "QA Lead", "opinion": "Prioritize torque test bypass under controls."}],
                        "transcript_detailed": [],
                    },
                    model_used="mock-llm",
                    usage={},
                    confidence=0.95,
                )
            raise AssertionError(f"Unexpected call: {agent_name}.{method_name}")

    sf.orchestrator = _StubOrchestrator()

    # Build request with minimal problem framing
    req = SolutionFinderRequest(
        request_id=str(uuid.uuid4()),
        principal_id="cfo_001",
        problem_statement="COGS variance concentrated in US10_PCC3S Jan–Apr vs Budget; stabilize after May",
        deep_analysis_output={"where": [{"dimension": "Profit Center Name", "key": "US10_PCC3S"}]},
        evaluation_criteria=[
            TradeOffCriterion(name="impact", weight=0.5),
            TradeOffCriterion(name="cost", weight=0.3),
            TradeOffCriterion(name="risk", weight=0.2),
        ],
    )

    resp = await sf.recommend_actions(req)

    assert getattr(resp, "status", "error") == "success"
    assert resp.recommendation is not None
    assert len(resp.options_ranked) >= 2
    assert isinstance(resp.recommendation_rationale, str) and len(resp.recommendation_rationale) > 0
    # Confirm LLM path indicators: either audit marker present OR consensus rationale surfaced
    llm_audit = any(ev.get("event") == "llm_debate_completed" for ev in (resp.audit_log or []))
    assert llm_audit or (resp.recommendation_rationale or "").startswith("Consensus")
