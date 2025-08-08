import pytest
import asyncio
import uuid
from unittest.mock import AsyncMock
from datetime import datetime, timezone

from src.agents.agent_registry import registry
from src.agents.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
from src.agents.models.a9_core_models import SituationReport, AnalysisResult
from src.models.llm_models import LLMProvider, LLMResponse
from src.agents.a9_llm_service_agent import A9_LLM_Service_Agent

@pytest.fixture
def mock_situation_report() -> SituationReport:
    """Provides a mock SituationReport for tests."""
    return SituationReport(
        situation_id="sit_123",
        principal_id="ceo",
        kpi_name="Revenue",
        business_process="Finance: Revenue Growth Analysis",
        current_value=950000,
        expected_value=1000000,
        delta=-50000,
        status="new",
        timestamp=datetime.now(timezone.utc).isoformat(),
        start_date="2024-01-01",
        end_date="2024-01-31",
        filters_applied={"Region": "North America"}
    )

@pytest.mark.asyncio
async def test_create_and_register_agent():
    """Tests that the agent can be created and registers itself."""
    agent = await registry.get_agent("A9_Deep_Analysis_Agent")
    assert isinstance(agent, A9_Deep_Analysis_Agent)
    assert agent.name == "A9_Deep_Analysis_Agent"

@pytest.mark.asyncio
async def test_perform_deep_analysis_success(mocker, mock_situation_report):
    """Tests the successful execution of a deep analysis by mocking the LLM call."""
    from unittest.mock import AsyncMock
    from src.agents.agent_config_models import A9DeepAnalysisAgentConfig

    # 1. Instantiate the agent under test
    agent = A9_Deep_Analysis_Agent(config=A9DeepAnalysisAgentConfig(analysis_model_endpoint="http://mock.endpoint/api"))

    # 2. Mock the final LLMResponse that the agent will produce
    mock_llm_output = LLMResponse(
        response='{"root_cause_hypotheses": ["Hypothesis 1"], "summary": "A summary", "confidence": 0.9}',
        timestamp=datetime.now(timezone.utc).isoformat(),
        source="llm",
        model_used="mock_model"
    )

    # 3. Mock the internal methods to isolate the final construction logic
    mocker.patch.object(agent, '_generate_kt_table', new_callable=AsyncMock, return_value={"key": "value"})
    mocker.patch.object(agent, '_get_llm_analysis', new_callable=AsyncMock, return_value=mock_llm_output)

    # 4. Perform the analysis
    analysis_result = await agent.perform_deep_analysis(mock_situation_report)

    # 5. Assert the result is constructed correctly
    assert isinstance(analysis_result, AnalysisResult)
    assert analysis_result.situation_id == mock_situation_report.situation_id
    assert analysis_result.confidence_score == 0.9
    assert "Hypothesis 1" in analysis_result.root_cause_hypotheses
    assert analysis_result.summary == "A summary"
