import os
import tempfile
import asyncio
import unittest

from src.agents.a9_data_product_mcp_service_agent import (
    A9_Data_Product_MCP_Service_Agent,
    SQLExecutionRequest,
)


class TestMCPServiceAgentUnitPytest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.tmp_db_path = os.path.join(cls.tmp_dir.name, "unit_test.duckdb")

        cls.config = {
            "database_type": "duckdb",
            "database_path": cls.tmp_db_path,
            "registry_path": "src/registry_references",
            "data_product_registry": "data_product_registry/data_product_registry.csv",
            "validate_sql": True,
            "allow_custom_sql": True,
        }

        cls.agent = asyncio.run(A9_Data_Product_MCP_Service_Agent.create(cls.config))

        conn = cls.agent.db_manager.duckdb_conn
        conn.execute(
            "CREATE TABLE IF NOT EXISTS FinancialTransactions(\n            \"Transaction Value Amount\" DECIMAL(18,2)\n        )"
        )
        conn.execute(
            "INSERT INTO FinancialTransactions VALUES (100.00), (250.50), (149.50)"
        )
        conn.execute(
            "CREATE OR REPLACE VIEW FI_Star_View AS SELECT * FROM FinancialTransactions"
        )

    @classmethod
    def tearDownClass(cls):
        try:
            if getattr(cls, "agent", None):
                cls.agent.close()
        finally:
            try:
                if getattr(cls, "tmp_dir", None):
                    cls.tmp_dir.cleanup()
            except Exception:
                pass

    def test_happy_path_sum(self):
        req = SQLExecutionRequest(
            request_id="unit-1",
            principal_id="unit-principal",
            sql='SELECT SUM("Transaction Value Amount") AS total_value FROM "FI_Star_View"',
        )
        resp = asyncio.run(asyncio.wait_for(self.agent.execute_sql(req), timeout=10))
        resp_d = resp.model_dump() if hasattr(resp, 'model_dump') else (resp if isinstance(resp, dict) else {})
        assert resp_d.get("status") == "success"
        assert len(resp_d.get("columns", [])) > 0
        assert resp_d.get("row_count") == 1
        rows = resp_d.get("rows", [])
        total = rows[0][0] if rows else None
        assert abs(float(total) - 500.00) < 1e-6

    def test_invalid_sql(self):
        req = SQLExecutionRequest(
            request_id="unit-2",
            principal_id="unit-principal",
            sql='DELETE FROM "FI_Star_View"',
        )
        resp = asyncio.run(asyncio.wait_for(self.agent.execute_sql(req), timeout=10))
        resp_d = resp.model_dump() if hasattr(resp, 'model_dump') else (resp if isinstance(resp, dict) else {})
        assert resp_d.get("status") == "error"
        em = (resp_d.get("error_message") or resp_d.get("error") or resp_d.get("message") or "").lower()
        assert "only select statements" in em
