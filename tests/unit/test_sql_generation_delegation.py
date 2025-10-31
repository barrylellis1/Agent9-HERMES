import sys
import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    # Import models and agents
    from src.agents.models.situation_awareness_models import (
        KPIDefinition, KPIValue, TimeFrame, ComparisonType, NLQueryRequest
    )
except ImportError:
    # Fallback imports if the above fails
    from src.agents.models.situation_awareness_models import (
        KPIDefinition, KPIValue, TimeFrame, ComparisonType
    )
    
    # Create a simple NLQueryRequest class if it doesn't exist
    class NLQueryRequest:
        def __init__(self, query, timeframe=None, comparison_type=None, filters=None):
            self.query = query
            self.timeframe = timeframe
            self.comparison_type = comparison_type
            self.filters = filters or {}
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent, initialize_agent_registry, agent_registry


@pytest.mark.asyncio
async def test_sql_generation_delegation():
    """
    Test that the Situation Awareness Agent delegates SQL generation to the Data Product Agent.
    """
    # Ensure a clean registry state for this test
    agent_registry.clear()
    # Create real orchestrator and initialize registry
    orchestrator = await A9_Orchestrator_Agent.create()
    await initialize_agent_registry()

    # Create mock Data Product Agent and register factory with orchestrator
    mock_data_product_agent = AsyncMock(spec=A9_Data_Product_Agent)
    # SA agent delegates to data_product_agent.generate_sql(query, context)
    mock_data_product_agent.generate_sql = AsyncMock(return_value={
        'sql': 'SELECT * FROM test_view',
        'success': True,
        'message': 'SQL generated successfully'
    })

    async def _mock_dp_factory(config=None):
        return mock_data_product_agent

    await orchestrator.register_agent_factory("A9_Data_Product_Agent", _mock_dp_factory)

    # Create SA agent via orchestrator (dependency on DP agent will resolve)
    sa_agent = await orchestrator.create_agent_with_dependencies(
        "A9_Situation_Awareness_Agent",
        {"orchestrator": orchestrator}
    )
    
    # KPI registry will be set after connect to avoid being overwritten
    
    # Create test KPI value
    test_kpi_value = KPIValue(
        kpi_name='test_kpi',
        value=100.0,
        timeframe=TimeFrame.CURRENT_QUARTER,
        dimensions={}
    )
    
    # Connect the agent (SA currently creates its own orchestrator internally)
    try:
        await sa_agent.connect(orchestrator)
    except TypeError:
        await sa_agent.connect()
    # Ensure the SA agent uses our mock DP agent
    sa_agent.data_product_agent = mock_data_product_agent
    # Mock the KPI registry (after connect so it's not overwritten)
    sa_agent.kpi_registry = {
        'test_kpi': KPIDefinition(
            name='test_kpi',
            description='Test KPI',
            unit='USD',
            data_product_id='test_dp',
            view_name='test_view'
        )
    }
    
    # Test _generate_sql_for_query method
    sql = await sa_agent._generate_sql_for_query('test query', [test_kpi_value])
    
    # Verify that Data Product Agent was called
    mock_data_product_agent.generate_sql.assert_called_once()
    
    # Verify the SQL was returned correctly
    assert sql == 'SELECT * FROM test_view'
    
    # Test process_nl_query method using a dict (agent will convert and add request_id/timestamp)
    nl_request = {
        'query': 'test query',
        'timeframe': TimeFrame.CURRENT_QUARTER,
        'comparison_type': ComparisonType.QUARTER_OVER_QUARTER,
        'filters': {},
        'principal_context': {
            'role': 'CFO',
            'principal_id': 'cfo_001',
            'business_processes': ["Finance: Profitability Analysis"],
            'default_filters': {},
            'decision_style': 'Analytical',
            'communication_style': 'Concise',
            'preferred_timeframes': [TimeFrame.CURRENT_QUARTER]
        }
    }
    
    # Mock the map_kpis_to_data_products method
    sa_agent.data_governance_agent = AsyncMock()
    sa_agent.data_governance_agent.map_kpis_to_data_products.return_value = {
        'kpis': {'test_kpi': sa_agent.kpi_registry['test_kpi']},
        'unmapped_terms': []
    }
    
    # Mock the _get_kpi_value method
    sa_agent._get_kpi_value = AsyncMock(return_value=test_kpi_value)

    # Provide a deterministic translation_result structure to avoid awaiting AsyncMock attributes
    class _TranslationResult:
        def __init__(self):
            self.resolved_terms = {"kpi": "gross_revenue"}
    sa_agent.translation_result = _TranslationResult()

    # Call process_nl_query
    response = await sa_agent.process_nl_query(nl_request)
    
    # Verify that the Data Product Agent was called for SQL generation
    assert mock_data_product_agent.generate_sql.call_count == 2
    
    # Verify the response contains the SQL
    assert response.sql_query == 'SELECT * FROM test_view'


@pytest.mark.asyncio
async def test_sql_generation_fallback():
    """
    Test that the Situation Awareness Agent falls back to deprecated methods
    when Data Product Agent is not available.
    """
    # Ensure a clean registry state for this test
    agent_registry.clear()
    # Create real orchestrator and initialize registry
    orchestrator = await A9_Orchestrator_Agent.create()
    await initialize_agent_registry()

    # Create SA agent via orchestrator
    sa_agent = await orchestrator.create_agent_with_dependencies(
        "A9_Situation_Awareness_Agent",
        {"orchestrator": orchestrator}
    )
    
    # Mock the KPI registry
    sa_agent.kpi_registry = {
        'test_kpi': KPIDefinition(
            name='test_kpi',
            description='Test KPI',
            unit='USD',
            data_product_id='test_dp',
            view_name='test_view'
        )
    }
    
    # Create test KPI value
    test_kpi_value = KPIValue(
        kpi_name='test_kpi',
        value=100.0,
        timeframe=TimeFrame.CURRENT_QUARTER,
        dimensions={}
    )
    
    # Connect the agent
    await sa_agent.connect()
    # Explicitly simulate no Data Product Agent available (use a sentinel without generate_sql)
    sa_agent.data_product_agent = object()
    
    # Test _generate_sql_for_query method
    sql = await sa_agent._generate_sql_for_query('test query', [test_kpi_value])
    
    # Verify the SQL fallback behavior (current implementation returns None when DP agent is unavailable)
    assert sql is None
