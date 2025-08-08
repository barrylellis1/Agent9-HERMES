import pytest
import asyncio
import pandas as pd
from unittest.mock import patch, MagicMock, AsyncMock

from src.agents.agent_registry import registry
from src.agents.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.models.a9_core_models import SituationReport, A9PrincipalContextProfile
from src.agents.agent_config_models import A9SituationAwarenessAgentConfig

@pytest.mark.asyncio
async def test_create_and_register_agent():
    """Tests that the agent can be created and registers itself."""
    agent = await registry.get_agent("A9_Situation_Awareness_Agent")
    assert isinstance(agent, A9_Situation_Awareness_Agent)
    assert agent.name == "A9_Situation_Awareness_Agent"

@pytest.mark.asyncio
async def test_run_situation_check_success(mocker):
    """Tests that running a situation check returns a valid report."""
    # Mock the orchestrator that the situation agent will call
    mock_orchestrator = AsyncMock()
    mock_nlp_response = {
        "sql_query": "SELECT 1 AS current_value, 0 AS previous_value",
        "start_date": "2023-01-01",
        "end_date": "2023-01-31"
    }
    mock_orchestrator.route_request.return_value = mock_nlp_response

    # Mock the MCP service to return a predictable DataFrame
    mock_mcp_service = MagicMock()
    mock_df = pd.DataFrame([{'current_value': 1.0, 'previous_value': 0.5}]) # Example data
    mock_mcp_service.execute_query.return_value = mock_df

    mock_gov_agent = MagicMock()
    future = asyncio.Future()
    future.set_result(["Gross Revenue"])
    mock_gov_agent.get_kpis_for_business_processes = AsyncMock(return_value=future.result())

    async def side_effect_get_agent(agent_name, *args, **kwargs):
        if agent_name == "A9_MCP_Service_Agent":
            return mock_mcp_service
        if agent_name == "A9_Data_Governance_Agent":
            return mock_gov_agent
        if agent_name == "A9_Orchestrator_Agent":
            return mock_orchestrator
        # Fallback to the real agent for the subject under test
        return await A9_Situation_Awareness_Agent.create_from_registry()

    mocker.patch('src.agents.a9_situation_awareness_agent.registry.get_agent', side_effect=side_effect_get_agent)
    principal_profile_dict = {
        "user_id": "ceo",
        "first_name": "Test",
        "last_name": "User",
        "role": "CEO",
        "department": "Executive",
        "business_processes": ["Finance: Revenue Growth Analysis"],
        "default_filters": {"CompanyCode": "1000"}
    }
    principal_profile = A9PrincipalContextProfile(**principal_profile_dict)
    mock_config = A9SituationAwarenessAgentConfig()
    agent = A9_Situation_Awareness_Agent(config=mock_config)
    situation_reports = await agent.get_situational_picture(principal_id="ceo", principal_profile=principal_profile)

    assert situation_reports
    assert isinstance(situation_reports, list)
    assert len(situation_reports) == 1

    report = situation_reports[0]
    assert isinstance(report, SituationReport)
    assert report.kpi_name == "Gross Revenue"
    assert report.status == "Opportunity"  # 100% change is positive
    assert report.principal_id == "ceo"
    assert report.business_process == "Finance: Revenue Growth Analysis"
    assert "CompanyCode" in report.filters_applied
