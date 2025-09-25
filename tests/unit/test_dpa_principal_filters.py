import pytest
from types import SimpleNamespace
import os
import sys

# Ensure project root is on sys.path for 'src' imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.agents.new.a9_orchestrator_agent import (
    A9_Orchestrator_Agent,
    initialize_agent_registry,
)
from src.registry.factory import RegistryFactory


async def _get_dp_agent():
    orchestrator = await A9_Orchestrator_Agent.create({})
    # Register factories so the orchestrator can create agents
    await initialize_agent_registry()
    # Minimal registry factory for agent config (no providers required for these tests)
    rf = RegistryFactory()
    dp_agent = await orchestrator.create_agent_with_dependencies(
        "A9_Data_Product_Agent",
        {"orchestrator": orchestrator, "registry_factory": rf}
    )
    return dp_agent


@pytest.mark.asyncio
async def test_get_kpi_data_merges_principal_defaults(monkeypatch):
    agent = await _get_dp_agent()

    captured = {}

    async def mock_generate_sql_for_kpi(kpi_definition, timeframe=None, filters=None):
        captured['filters'] = filters or {}
        return {"success": True, "sql": "SELECT 1 AS v"}

    async def mock_execute_sql(sql, principal_context=None):
        return {
            "success": True,
            "columns": ["v"],
            "rows": [[123.0]],
            "execution_time": 0.001,
        }

    monkeypatch.setattr(agent, "generate_sql_for_kpi", mock_generate_sql_for_kpi)
    monkeypatch.setattr(agent, "execute_sql", mock_execute_sql)

    principal_context = SimpleNamespace(
        default_filters={
            'profit_center_hierarchyid': ['Best Run U'],
            'customer_hierarchyid': ['Total'],
        }
    )

    kpi_def = SimpleNamespace(name="Gross Revenue", data_product_id='FI_Star_Schema')

    resp = await agent.get_kpi_data(
        kpi_definition=kpi_def,
        timeframe=None,
        filters={
            'Version': 'Budget',
            'customer_hierarchyid': ['17100001'],  # should override principal default
        },
        principal_context=principal_context,
    )

    assert resp["status"] == "success"
    assert 'filters' in captured
    merged = captured['filters']

    # Principal default preserved when not overridden
    assert merged.get('profit_center_hierarchyid') == ['Best Run U']

    # Explicit filters override principal defaults
    assert merged.get('customer_hierarchyid') == ['17100001']

    # Explicit filters preserved
    assert merged.get('Version') == 'Budget'


@pytest.mark.asyncio
async def test_generate_sql_ignores_all_tokens_in_filters():
    agent = await _get_dp_agent()

    kpi_def = SimpleNamespace(name="Gross Revenue", data_product_id='FI_Star_Schema')

    filters = {
        'profit_center_hierarchyid': ['Total', 'Best Run U'],  # 'Total' should be ignored
        'customer_hierarchyid': '#',                           # '#' should be ignored entirely
        'Version': 'Actual',
    }

    sql = await agent._generate_sql_for_kpi(kpi_def, timeframe=None, filters=filters)

    assert isinstance(sql, str)
    assert sql.strip().lower().startswith('select')

    # Ensure sentinel tokens are not present in the SQL
    assert 'Total' not in sql
    assert "'#'" not in sql
    assert "='#'" not in sql

    # Ensure valid remaining filters are present
    # Profit Center should include only 'Best Run U' in the IN clause
    assert '"Profit Center Hierarchyid"' in sql
    assert "'Best Run U'" in sql

    # Version filter should be applied
    assert '"Version" = ' in sql or '"Version"=' in sql


@pytest.mark.asyncio
async def test_get_kpi_comparison_data_merges_principal_defaults(monkeypatch):
    agent = await _get_dp_agent()

    captured = {}

    async def mock_generate_sql_for_kpi_comparison(kpi_definition, timeframe=None, comparison_type="previous_period", filters=None):
        captured['filters'] = filters or {}
        return {"success": True, "sql": "SELECT 1 AS v"}

    async def mock_execute_sql(sql, principal_context=None):
        return {
            "success": True,
            "columns": ["v"],
            "rows": [{"v": 200.0}],
            "execution_time": 0.001,
        }

    monkeypatch.setattr(agent, "generate_sql_for_kpi_comparison", mock_generate_sql_for_kpi_comparison)
    monkeypatch.setattr(agent, "execute_sql", mock_execute_sql)

    principal_context = SimpleNamespace(
        default_filters={
            'profit_center_hierarchyid': ['Finance'],
            'customer_hierarchyid': ['Total'],
        }
    )

    kpi_def = SimpleNamespace(name="Gross Revenue", data_product_id='FI_Star_Schema')

    resp = await agent.get_kpi_comparison_data(
        kpi_definition=kpi_def,
        timeframe=None,
        comparison_type="previous_period",
        filters={
            'customer_hierarchyid': ['17100001'],  # Override default
        },
        principal_context=principal_context,
    )

    assert resp["status"] == "success"
    merged = captured.get('filters', {})
    assert merged.get('profit_center_hierarchyid') == ['Finance']
    assert merged.get('customer_hierarchyid') == ['17100001']
