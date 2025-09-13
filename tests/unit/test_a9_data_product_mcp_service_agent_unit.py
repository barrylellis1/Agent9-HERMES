import os
import tempfile
import asyncio
import unittest

from src.agents.a9_data_product_mcp_service_agent import (
    A9_Data_Product_MCP_Service_Agent,
    SQLExecutionRequest,
)


class TestA9MCPServiceAgentUnit(unittest.TestCase):
    """Focused unit tests for A9_Data_Product_MCP_Service_Agent.execute_sql.

    These tests use an isolated temporary DuckDB file and create a minimal
    FI_Star_View so we can verify SELECT aggregation works through the agent.
    """

    @classmethod
    def setUpClass(cls):
        # Create a temporary directory and choose a DB path that does NOT exist yet
        # so DuckDB can create it itself.
        cls.tmp_dir = tempfile.TemporaryDirectory()
        cls.tmp_db_path = os.path.join(cls.tmp_dir.name, "unit_test.duckdb")

        # Build minimal config; A9_Data_Product_MCP_Service_Config allows extra fields
        cls.config = {
            "database_type": "duckdb",
            "database_path": cls.tmp_db_path,
            # Defaults for registry paths are fine for this unit test
            "registry_path": "src/registry_references",
            "data_product_registry": "data_product_registry/data_product_registry.csv",
            # Validation on; only SELECT allowed
            "validate_sql": True,
            "allow_custom_sql": True,
        }

        # Create agent instance (async factory)
        cls.agent = asyncio.run(A9_Data_Product_MCP_Service_Agent.create(cls.config))

        # Create minimal table and view inside the same DB the agent uses
        conn = cls.agent.db_manager.duckdb_conn
        conn.execute("CREATE TABLE IF NOT EXISTS FinancialTransactions(\n            \"Transaction Value Amount\" DECIMAL(18,2)\n        )")
        # Insert a few rows
        conn.execute("INSERT INTO FinancialTransactions VALUES (100.00), (250.50), (149.50)")
        # Create the canonical view used by the KPI queries
        conn.execute("CREATE OR REPLACE VIEW FI_Star_View AS SELECT * FROM FinancialTransactions")

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

    def test_execute_sql_sum_from_fi_star_view(self):
        """Happy path: SUM over FI_Star_View returns one row with correct value."""
        req = SQLExecutionRequest(
            request_id="unit-1",
            principal_id="unit-principal",
            sql='SELECT SUM("Transaction Value Amount") AS total_value FROM "FI_Star_View"',
        )
        resp = asyncio.run(asyncio.wait_for(self.agent.execute_sql(req), timeout=10))
        resp_d = resp.model_dump() if hasattr(resp, 'model_dump') else (resp if isinstance(resp, dict) else {})
        self.assertEqual(resp_d.get("status"), "success")
        self.assertTrue(len(resp_d.get("columns", [])) > 0)
        self.assertEqual(resp_d.get("row_count"), 1)
        # SUM(100.00 + 250.50 + 149.50) = 500.00
        rows = resp_d.get("rows", [])
        total = rows[0][0] if rows else None
        # Allow either float/Decimal
        self.assertAlmostEqual(float(total), 500.00, places=2)

    def test_invalid_sql_rejected(self):
        """Security: non-SELECT statements must be rejected."""
        req = SQLExecutionRequest(
            request_id="unit-2",
            principal_id="unit-principal",
            sql='DELETE FROM "FI_Star_View"',
        )
        resp = asyncio.run(asyncio.wait_for(self.agent.execute_sql(req), timeout=10))
        resp_d = resp.model_dump() if hasattr(resp, 'model_dump') else (resp if isinstance(resp, dict) else {})
        self.assertEqual(resp_d.get("status"), "error")
        # Error message should mention only SELECT statements are allowed
        em = (resp_d.get("error_message") or resp_d.get("error") or resp_d.get("message") or "").lower()
        self.assertIn("only select statements", em)


if __name__ == "__main__":
    unittest.main()
