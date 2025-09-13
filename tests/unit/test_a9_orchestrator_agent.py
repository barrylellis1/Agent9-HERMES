# arch-allow-direct-agent-construction
import pytest
pytest.skip("Skipped: legacy/non-MVP test (temporarily disabled during MVP migration)", allow_module_level=True)
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.agents.agent_registry import registry
from src.agents.a9_orchestrator_agent import A9_Orchestrator_Agent
from src.agents.models.a9_core_models import SolutionSet
from src.agents.agent_config_models import A9OrchestratorAgentConfig
from src.agents.a9_llm_service_agent import A9_LLM_Service_Agent
from src.models.llm_models import LLMRequest, LLMResponse, LLMProvider



@pytest.mark.asyncio
async def test_create_and_register_agent():
    """Tests that the agent can be created and registers itself."""
    agent = await registry.get_agent("A9_Orchestrator_Agent")
    assert isinstance(agent, A9_Orchestrator_Agent)
    assert agent.name == "A9_Orchestrator_Agent"

@pytest.mark.asyncio
async def test_run_workflow_success(mocker):
    """Tests the full, successful end-to-end workflow with mocks."""
    # Mock all dependent agents
    mock_principal_agent = await registry.get_agent("A9_Principal_Context_Agent")
    mock_sit_aware_agent = await registry.get_agent("A9_Situation_Awareness_Agent")
    mock_deep_analysis_agent = await registry.get_agent("A9_Deep_Analysis_Agent")
    mock_solution_finder_agent = await registry.get_agent("A9_Solution_Finder_Agent")

    # 1. Mock Principal Context response
    mock_profile = {
        "profile": {
            "user_id": "ceo",
            "first_name": "Test",
            "last_name": "User",
            "role": "CEO",
            "department": "Executive",
            "business_processes": ["Finance: Gross Revenue Analysis"]
        }
    }
    mocker.patch.object(mock_principal_agent, 'fetch_principal_profile', new_callable=AsyncMock, return_value=mock_profile)

    # 2. Mock Situation Awareness response
    mock_situation_report = mocker.MagicMock()
    mock_situation_report.kpi_name = "Gross Revenue"
    mocker.patch.object(mock_sit_aware_agent, 'get_situational_picture', new_callable=AsyncMock, return_value=[mock_situation_report])

    # 3. Mock Deep Analysis response
    mock_analysis_result = mocker.MagicMock()
    mocker.patch.object(mock_deep_analysis_agent, 'perform_deep_analysis', new_callable=AsyncMock, return_value=mock_analysis_result)

    # 4. Mock Solution Finder response
    mock_solution_set = SolutionSet(solution_set_id="set_123", analysis_id="analysis_abc", options=[], human_action_required=False)
    mocker.patch.object(mock_solution_finder_agent, 'find_solutions', new_callable=AsyncMock, return_value=mock_solution_set)

    # Run the workflow
    orchestrator = await registry.get_agent("A9_Orchestrator_Agent")
    final_result = await orchestrator.run_workflow(principal_id="ceo", hitl_choice=1)

    # Assertions
    assert final_result is not None
    assert isinstance(final_result, SolutionSet)
    assert final_result.solution_set_id == "set_123"

@pytest.mark.asyncio
async def test_run_workflow_no_situation_found(mocker):
    """Tests that the workflow handles cases where no situation is detected."""
    # Mock the situation awareness agent to return no reports
    mock_sit_aware_agent = await registry.get_agent("A9_Situation_Awareness_Agent")
    mocker.patch.object(mock_sit_aware_agent, 'get_situational_picture', return_value=[])

    orchestrator = await registry.get_agent("A9_Orchestrator_Agent")
    # Use a valid principal that exists, like 'ceo'
    result = await orchestrator.run_workflow("ceo")

    assert result is None

@pytest.mark.asyncio
async def test_get_llm_analysis_success(mocker):
    """Tests that the orchestrator can successfully route a request to the LLM service."""
    # 1. Define the mock response
    mock_llm_response = LLMResponse(
        response='{"analysis": "This is a test analysis."}',
        timestamp=datetime.now().isoformat(),
        source="llm",
        model_used="mock_model"
    )

    # 2. Patch the handle_request method directly on the LLM service agent class
    mock_handle_request = mocker.patch(
        'src.agents.a9_llm_service_agent.A9_LLM_Service_Agent.handle_request',
        new_callable=AsyncMock,
        return_value=mock_llm_response
    )

    # 3. Instantiate the orchestrator. It will get the real LLM agent, but its method is patched.
    mock_config = A9OrchestratorAgentConfig()
    orchestrator = A9_Orchestrator_Agent(config=mock_config)
    llm_request = LLMRequest(
        user_id="test_user",
        prompt="test prompt",
        provider=LLMProvider.OPENAI,
        model_name="gpt-4"
    )

    # 4. Run the method
    result = await orchestrator.get_llm_analysis(llm_request)

    # 5. Assert the result and that the mock was called
    assert result == mock_llm_response
    mock_handle_request.assert_awaited_once_with(llm_request)
