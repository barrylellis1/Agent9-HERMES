import asyncio
import pytest

pytestmark = pytest.mark.asyncio

from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent, initialize_agent_registry
from src.agents.models.deep_analysis_models import DeepAnalysisRequest
from src.agents.models.solution_finder_models import SolutionFinderRequest, TradeOffCriterion


@pytest.mark.asyncio
async def test_deep_analysis_agent_basic():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    # Create agent via orchestrator factory
    agent = await orchestrator.create_agent_with_dependencies("A9_Deep_Analysis_Agent", {"orchestrator": orchestrator})
    assert agent is not None

    # Enumerate
    req = DeepAnalysisRequest(
        request_id="req-da-1",
        principal_id="test_principal",
        kpi_name="Revenue",
        timeframe="current_quarter",
        filters={"Version": "Actual"},
        target_count=5,
        enable_percent_growth=False,
    )
    resp = await agent.enumerate_dimensions(req)
    assert resp.status == "success"
    assert resp.plan is not None

    # Plan
    plan_resp = await agent.plan_deep_analysis(req)
    assert plan_resp.status == "success"
    assert plan_resp.plan is not None

    # Execute
    exec_resp = await agent.execute_deep_analysis(plan_resp.plan)
    assert exec_resp.status == "success"
    assert exec_resp.scqa_summary is not None


@pytest.mark.asyncio
async def test_solution_finder_agent_basic():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    # Create agent via orchestrator factory
    agent = await orchestrator.create_agent_with_dependencies("A9_Solution_Finder_Agent", {"orchestrator": orchestrator})
    assert agent is not None

    req = SolutionFinderRequest(
        request_id="req-sf-1",
        principal_id="test_principal",
        problem_statement="Margin compression detected in Q3",
        evaluation_criteria=[
            TradeOffCriterion(name="impact", weight=0.5),
            TradeOffCriterion(name="cost", weight=0.25),
            TradeOffCriterion(name="risk", weight=0.25),
        ],
    )

    resp = await agent.recommend_actions(req)
    assert resp.status == "success"
    assert len(resp.options_ranked) >= 1
    assert resp.human_action_required is True
