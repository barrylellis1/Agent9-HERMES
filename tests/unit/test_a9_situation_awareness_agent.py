# arch-allow-direct-agent-construction
import pytest
pytest.skip("Skipped: legacy/non-MVP test (temporarily disabled during MVP migration)", allow_module_level=True)
import asyncio
import pandas as pd
from unittest.mock import patch, MagicMock, AsyncMock, call

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

@pytest.mark.asyncio
async def test_kpi_mapping_delegation(mocker):
    """Tests that the Situation Awareness Agent delegates KPI mapping to Data Governance Agent."""
    # Mock the Data Governance Agent
    mock_data_governance_agent = AsyncMock()
    
    # Set up mock response for map_kpis_to_data_products
    from src.agents.models.data_governance_models import KPIDataProductMappingResponse, KPIDataProductMapping
    mock_mapping_response = KPIDataProductMappingResponse(
        mappings=[
            KPIDataProductMapping(
                kpi_name="Revenue",
                data_product_id="dp_001",
                technical_name="view_revenue",
                metadata={"description": "Total revenue", "thresholds": {"critical": 1000000}}
            )
        ],
        unmapped_kpis=["Unknown KPI"],
        human_action_required=False
    )
    mock_data_governance_agent.map_kpis_to_data_products.return_value = mock_mapping_response
    
    # Set up mock response for get_view_name_for_kpi
    from src.agents.models.data_governance_models import KPIViewNameResponse
    mock_view_name_response = KPIViewNameResponse(
        kpi_name="Revenue",
        asset_path="view_revenue",
        data_product_id="dp_001"
    )
    mock_data_governance_agent.get_view_name_for_kpi.return_value = mock_view_name_response
    
    # Mock the Data Product Agent
    mock_data_product_agent = AsyncMock()
    
    # Set up mock response for generate_sql_for_kpi
    mock_data_product_agent.generate_sql_for_kpi.return_value = {
        "success": True,
        "sql": "SELECT SUM(amount) FROM view_revenue"
    }
    
    # Set up mock response for execute_sql
    from src.agents.a9_data_product_mcp_service_agent import SQLExecutionResponse
    mock_sql_response = SQLExecutionResponse(
        request_id="test_request",
        status="success",
        results=[{"value": 1500000}],
        error_message=None
    )
    mock_data_product_agent.execute_sql.return_value = mock_sql_response
    
    # Mock the Orchestrator Agent
    mock_orchestrator = AsyncMock()
    
    async def side_effect_get_agent(agent_name, *args, **kwargs):
        if agent_name == "A9_Data_Product_MCP_Service_Agent":
            return mock_data_product_agent
        if agent_name == "A9_Data_Governance_Agent":
            return mock_data_governance_agent
        return mock_orchestrator
    
    mock_orchestrator.get_agent.side_effect = side_effect_get_agent
    
    # Create the Situation Awareness Agent with mocked dependencies
    from src.agents.agent_config_models import A9SituationAwarenessAgentConfig
    mock_config = A9SituationAwarenessAgentConfig()
    
    # Patch the orchestrator creation
    with patch('src.agents.new.a9_orchestrator_agent.A9_Orchestrator_Agent.create', return_value=mock_orchestrator):
        # Use the new implementation from src/agents/new
        from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
        agent = A9_Situation_Awareness_Agent(config=mock_config)
        
        # Connect to services
        await agent.connect()
        
        # Create a KPI values request
        from src.agents.models.situation_awareness_models import KPIValuesRequest, TimeFrame, ComparisonType
        request = KPIValuesRequest(
            principal_id="CFO_001",
            kpi_names=["Revenue", "Unknown KPI"],
            timeframe=TimeFrame.CURRENT_QUARTER,
            comparison_type=ComparisonType.QUARTER_OVER_QUARTER,
            filters={}
        )
        
        # Call the method that should delegate to Data Governance Agent
        response = await agent.get_kpi_values(request)
        
        # Verify that the Data Governance Agent was called for KPI mapping
        mock_data_governance_agent.map_kpis_to_data_products.assert_called_once()
        
        # Verify that the Data Governance Agent was called for view name resolution
        mock_data_governance_agent.get_view_name_for_kpi.assert_called_once_with("Revenue")
        
        # Verify the response
        assert response.status == "success"
        assert len(response.kpi_values) == 1
        assert response.kpi_values[0].kpi_name == "Revenue"
        assert response.kpi_values[0].value == 1500000
        assert "Unknown KPI" in response.unmapped_kpis
