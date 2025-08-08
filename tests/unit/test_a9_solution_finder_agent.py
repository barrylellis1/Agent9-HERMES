import pytest
import asyncio
import uuid

from src.agents.agent_registry import registry
from src.agents.a9_solution_finder_agent import A9_Solution_Finder_Agent
from src.agents.models.a9_core_models import AnalysisResult, SolutionSet, SolutionOption


@pytest.fixture
def mock_analysis_result() -> AnalysisResult:
    """Provides a mock AnalysisResult for tests."""
    return AnalysisResult(
        analysis_id=str(uuid.uuid4()),
        situation_id=str(uuid.uuid4()),
        root_cause_hypotheses=["Unexpected marketing campaign"],
        kepner_tregoe_table={"what_is": "A revenue shortfall"},
        confidence_score=0.85,
        summary="A summary of the analysis."
    )

@pytest.mark.asyncio
async def test_create_and_register_agent():
    """Tests that the agent can be created and registers itself."""
    agent = await registry.get_agent("A9_Solution_Finder_Agent")
    assert isinstance(agent, A9_Solution_Finder_Agent)
    assert agent.name == "A9_Solution_Finder_Agent"

@pytest.mark.asyncio
async def test_find_solutions_success(mock_analysis_result):
    """Tests that finding solutions returns a valid SolutionSet."""
    agent = await registry.get_agent("A9_Solution_Finder_Agent")
    solution_set = await agent.find_solutions(mock_analysis_result)
    
    assert isinstance(solution_set, SolutionSet)
    assert solution_set.analysis_id == mock_analysis_result.analysis_id
    assert isinstance(solution_set.options, list)
    assert len(solution_set.options) > 0
    assert isinstance(solution_set.options[0], SolutionOption)
    assert solution_set.human_action_required is True
