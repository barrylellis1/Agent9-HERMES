"""Regression tests for the modern Data Product Agent SQL execution flow."""

import asyncio
import os
import sys
import tempfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest

from src.agents.models.sql_models import SQLExecutionRequest
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent


class _StubProvider:
    """Minimal provider implementing get/get_all required by agent."""

    def __init__(self, provider_type: str):
        self._provider_type = provider_type

    def get_provider_type(self) -> str:
        return self._provider_type

    def get(self, _identifier):
        return None

    def get_all(self):
        return []


class _TestRegistryFactory:
    """Provides stub registry providers to satisfy agent dependencies."""

    def __init__(self):
        self._providers = {
            "data_product": _StubProvider("data_product"),
            "kpi": _StubProvider("kpi"),
        }

    def get_provider(self, name: str):
        return self._providers.get(name)


def _build_agent_config(database_path: str) -> dict:
    return {
        "data_directory": os.path.dirname(database_path),
        "database": {"type": "duckdb", "path": database_path},
        "registry_factory": _TestRegistryFactory(),
        "bypass_mcp": True,
    }


@pytest.fixture(scope="module")
def data_product_agent():
    tmp_dir = tempfile.TemporaryDirectory()
    tmp_db_path = os.path.join(tmp_dir.name, "unit_test.duckdb")

    agent = asyncio.run(A9_Data_Product_Agent.create(_build_agent_config(tmp_db_path)))

    asyncio.run(agent.db_manager.connect({"database_path": tmp_db_path}))
    conn = agent.db_manager.duckdb_conn
    conn.execute(
        "CREATE TABLE IF NOT EXISTS FinancialTransactions(\n            \"Transaction Value Amount\" DECIMAL(18,2)\n        )"
    )
    conn.execute(
        "INSERT INTO FinancialTransactions VALUES (100.00), (250.50), (149.50)"
    )
    conn.execute(
        "CREATE OR REPLACE VIEW FI_Star_View AS SELECT * FROM FinancialTransactions"
    )

    yield agent

    asyncio.run(agent.disconnect())
    tmp_dir.cleanup()


@pytest.mark.asyncio
async def test_execute_sql_sum_from_fi_star_view(data_product_agent):
    request = SQLExecutionRequest(
        request_id="unit-1",
        principal_id="unit-principal",
        sql='SELECT SUM("Transaction Value Amount") AS total_value FROM FI_Star_View',
    )

    response = await data_product_agent.execute_sql(request)

    assert response.get("success") is True
    assert response.get("row_count") == 1
    rows = response.get("rows", [])
    assert rows and abs(float(rows[0]["total_value"])) == pytest.approx(500.0, rel=1e-6)


@pytest.mark.asyncio
async def test_invalid_sql_rejected(data_product_agent):
    request = SQLExecutionRequest(
        request_id="unit-2",
        principal_id="unit-principal",
        sql='DELETE FROM FI_Star_View',
    )

    response = await data_product_agent.execute_sql(request)

    assert response.get("success") is False
    message = response.get("message", "").lower()
    assert "only select" in message or "invalid sql" in message
