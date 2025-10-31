# arch-allow-direct-agent-construction
import asyncio
from types import SimpleNamespace
import os
import sys
import pytest

# Ensure project root is on sys.path for 'src' imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent


@pytest.mark.asyncio
async def test_get_kpi_data_happy_path(monkeypatch):
    agent = A9_Data_Product_Agent(config={})

    # Mock SQL generation
    async def mock_generate_sql_for_kpi(kpi_definition, timeframe=None, filters=None):
        return {"success": True, "sql": "SELECT 42 AS value"}

    # Mock SQL execution returning a dict row
    async def mock_execute_sql(sql, principal_context=None):
        return {
            "success": True,
            "columns": ["value"],
            "rows": [{"value": 123.45}],
            "execution_time": 0.01,
        }

    monkeypatch.setattr(agent, "generate_sql_for_kpi", mock_generate_sql_for_kpi)
    monkeypatch.setattr(agent, "execute_sql", mock_execute_sql)

    kpi_def = SimpleNamespace(name="Gross Revenue")
    resp = await agent.get_kpi_data(kpi_definition=kpi_def, timeframe=None, filters={})

    assert resp["status"] == "success"
    assert isinstance(resp["kpi_value"], (int, float))
    assert resp["kpi_value"] == 123.45


@pytest.mark.asyncio
async def test_get_kpi_comparison_data_happy_path(monkeypatch):
    agent = A9_Data_Product_Agent(config={})

    async def mock_generate_sql_for_kpi_comparison(kpi_definition, timeframe=None, comparison_type="previous_period", filters=None):
        return {"success": True, "sql": "SELECT 84 AS value"}

    async def mock_execute_sql(sql, principal_context=None):
        return {
            "success": True,
            "columns": ["value"],
            "rows": [[456.78]],
            "execution_time": 0.02,
        }

    monkeypatch.setattr(agent, "generate_sql_for_kpi_comparison", mock_generate_sql_for_kpi_comparison)
    monkeypatch.setattr(agent, "execute_sql", mock_execute_sql)

    kpi_def = SimpleNamespace(name="Gross Revenue")
    resp = await agent.get_kpi_comparison_data(kpi_definition=kpi_def, timeframe=None, comparison_type="previous_period", filters={})

    assert resp["status"] == "success"
    assert resp["comparison_value"] == 456.78
