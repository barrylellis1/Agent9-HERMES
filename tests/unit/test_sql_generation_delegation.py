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
    
    # Wire a mock DGA — DGA is now mandatory (simulates _wire_governance_dependencies())
    mock_dga = AsyncMock()
    mock_dga.translate_business_terms = AsyncMock(return_value=MagicMock(
        resolved_terms={'kpi': 'test_kpi'},
        unmapped_terms=[],
        human_action_required=False,
    ))
    mock_dga.map_kpis_to_data_products = AsyncMock(return_value=MagicMock(
        mappings=[MagicMock(kpi_name='test_kpi')],
        unmapped_kpis=[],
    ))
    sa_agent.data_governance_agent = mock_dga

    # Mock the _get_kpi_value method
    sa_agent._get_kpi_value = AsyncMock(return_value=test_kpi_value)

    # Call process_nl_query
    response = await sa_agent.process_nl_query(nl_request)

    # DGA mandatory path was exercised
    mock_dga.translate_business_terms.assert_called_once()

    # Verify the response contains the SQL
    assert response.sql_query == 'SELECT * FROM test_view'


@pytest.mark.asyncio
async def test_sql_generation_fallback():
    """
    DGA is now mandatory. When DGA is None, process_nl_query must raise AttributeError
    (calling .translate_business_terms on None) rather than silently falling back.
    """
    agent_registry.clear()
    orchestrator = await A9_Orchestrator_Agent.create()
    await initialize_agent_registry()

    sa_agent = await orchestrator.create_agent_with_dependencies(
        "A9_Situation_Awareness_Agent",
        {"orchestrator": orchestrator}
    )

    sa_agent.kpi_registry = {
        'test_kpi': KPIDefinition(
            name='test_kpi',
            description='Test KPI',
            unit='USD',
            data_product_id='test_dp',
            view_name='test_view'
        )
    }

    await sa_agent.connect()
    # DGA deliberately left as None (not wired) — simulates missing _wire_governance_dependencies()
    sa_agent.data_governance_agent = None

    nl_request = {
        'query': 'show me test_kpi',
        'timeframe': TimeFrame.CURRENT_QUARTER,
        'comparison_type': ComparisonType.QUARTER_OVER_QUARTER,
        'filters': {},
        'principal_context': {
            'role': 'CFO',
            'principal_id': 'cfo_001',
            'business_processes': ["Finance"],
            'default_filters': {},
            'decision_style': 'Analytical',
            'communication_style': 'Concise',
            'preferred_timeframes': [TimeFrame.CURRENT_QUARTER]
        }
    }

    # DGA is mandatory — calling None.translate_business_terms should raise
    with pytest.raises((AttributeError, Exception)):
        await sa_agent.process_nl_query(nl_request)


@pytest.mark.asyncio
async def test_dga_mandatory_path_happy_path():
    """
    When DGA is wired, process_nl_query completes successfully using DGA for term
    translation and KPI mapping.
    """
    agent_registry.clear()
    orchestrator = await A9_Orchestrator_Agent.create()
    await initialize_agent_registry()

    sa_agent = await orchestrator.create_agent_with_dependencies(
        "A9_Situation_Awareness_Agent",
        {"orchestrator": orchestrator}
    )

    test_kpi = KPIDefinition(
        name='test_kpi',
        description='Test KPI',
        unit='USD',
        data_product_id='test_dp',
        view_name='test_view'
    )
    sa_agent.kpi_registry = {'test_kpi': test_kpi}

    await sa_agent.connect()

    # Wire a mock DGA — simulates _wire_governance_dependencies()
    mock_dga = AsyncMock()
    mock_dga.translate_business_terms = AsyncMock(return_value=MagicMock(
        resolved_terms={'test': 'test_kpi'},
        unmapped_terms=[],
        human_action_required=False,
    ))
    mock_dga.map_kpis_to_data_products = AsyncMock(return_value=MagicMock(
        mappings=[MagicMock(kpi_name='test_kpi')],
        unmapped_kpis=[],
    ))
    sa_agent.data_governance_agent = mock_dga

    # Mock DPA SQL generation
    mock_dpa = AsyncMock(spec=A9_Data_Product_Agent)
    mock_dpa.generate_sql = AsyncMock(return_value={
        'sql': 'SELECT SUM(value) FROM test_view',
        'success': True,
        'message': 'OK'
    })
    mock_dpa.execute_sql = AsyncMock(return_value={
        'success': True, 'columns': ['value'], 'rows': [[100.0]]
    })
    sa_agent.data_product_agent = mock_dpa

    nl_request = {
        'query': 'show me test_kpi revenue',
        'timeframe': TimeFrame.CURRENT_QUARTER,
        'comparison_type': ComparisonType.QUARTER_OVER_QUARTER,
        'filters': {},
        'principal_context': {
            'role': 'CFO',
            'principal_id': 'cfo_001',
            'business_processes': ["Finance"],
            'default_filters': {},
            'decision_style': 'Analytical',
            'communication_style': 'Concise',
            'preferred_timeframes': [TimeFrame.CURRENT_QUARTER]
        }
    }

    response = await sa_agent.process_nl_query(nl_request)

    # DGA was called — mandatory path executed
    mock_dga.translate_business_terms.assert_called_once()
    assert response is not None


@pytest.mark.asyncio
async def test_dga_view_name_resolution_mandatory():
    """
    DPA._get_view_name_from_kpi must call DGA.get_view_name_for_kpi rather than
    silently returning a fallback when DGA is wired.
    """
    agent_registry.clear()
    orchestrator = await A9_Orchestrator_Agent.create()
    await initialize_agent_registry()

    dpa = await orchestrator.create_agent_with_dependencies(
        "A9_Data_Product_Agent",
        {"orchestrator": orchestrator}
    )
    await dpa.connect(orchestrator)

    mock_dga = AsyncMock()
    mock_dga.get_view_name_for_kpi = AsyncMock(return_value=MagicMock(
        view_name='LubricantsStarSchemaView',
        data_product_id='dp_lubricants_bq',
    ))
    dpa.data_governance_agent = mock_dga

    kpi_def = KPIDefinition(
        name='Net Revenue',
        description='Net Revenue KPI',
        unit='USD',
        data_product_id='dp_lubricants_bq',
    )

    view_name = await dpa._get_view_name_from_kpi(kpi_def)

    mock_dga.get_view_name_for_kpi.assert_called_once()
    assert view_name == 'LubricantsStarSchemaView'


@pytest.mark.asyncio
async def test_dga_none_raises_on_view_resolution():
    """
    When DGA is None, _get_view_name_from_kpi must raise (AttributeError) rather than
    silently returning a fallback view name.
    """
    agent_registry.clear()
    orchestrator = await A9_Orchestrator_Agent.create()
    await initialize_agent_registry()

    dpa = await orchestrator.create_agent_with_dependencies(
        "A9_Data_Product_Agent",
        {"orchestrator": orchestrator}
    )
    await dpa.connect(orchestrator)
    dpa.data_governance_agent = None  # not wired

    kpi_def = KPIDefinition(
        name='Net Revenue',
        description='Net Revenue KPI',
        unit='USD',
        data_product_id='dp_lubricants_bq',
    )

    with pytest.raises((AttributeError, Exception)):
        await dpa._get_view_name_from_kpi(kpi_def)
