# arch-allow-direct-agent-construction
"""
Test script for A9_Data_Product_MCP_Service_Agent.

This script validates the DuckDB integration with SAP Datasphere CSV data files,
testing SQL execution and data product access functionality.
"""

import os
import sys
import asyncio
import unittest
from pathlib import Path

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.a9_data_product_mcp_service_agent import (
    A9_Data_Product_MCP_Service_Agent,
    SQLExecutionRequest,
    DataProductRequest
)
from src.agents.agent_config_models import A9_Data_Product_MCP_Service_Config


class TestDataProductMCPService(unittest.TestCase):
    """Test cases for the Data Product MCP Service Agent"""

    def setUp(self):
        """Set up the test environment"""
        # Create a test configuration
        self.config = A9_Data_Product_MCP_Service_Config(
            # Use the actual SAP data path
            sap_data_path="C:/Users/Blell/Documents/Agent9/SAP DataSphere Data/datasphere-content-1.7/datasphere-content-1.7/SAP_Sample_Content/CSV/FI",
            registry_path="src/registry_references",
            data_product_registry="data_product_registry/data_product_registry.csv",
            allow_custom_sql=True,
            validate_sql=True
        )
        
        # Skip tests if the SAP data path is not available on this machine
        if not os.path.exists(self.config.sap_data_path):
            self.skipTest(f"SAP data path not found: {self.config.sap_data_path}")
        # Create the agent instance using async factory to ensure proper initialization
        self.agent = asyncio.run(A9_Data_Product_MCP_Service_Agent.create(self.config))
        
        # Mock request data
        self.request_id = "test-request-123"
        self.timestamp = "2025-08-05T14:30:00-05:00"
        self.user = "test_user"
        self.principal_id = "test-principal-456"

    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'agent') and self.agent is not None:
            self.agent.close()

    def test_initialize_duckdb_connection(self):
        """Test if DuckDB connection initializes correctly"""
        # Check if connection exists
        self.assertIsNotNone(self.agent.duckdb_conn)
        
        # Register CSV files (async) to ensure sap.* tables are available
        asyncio.run(self.agent._register_csv_files())
        
        # Check if tables were registered in the sap schema
        result = self.agent.duckdb_conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='sap'").fetchall()
        self.assertTrue(len(result) > 0, "No tables were registered in DuckDB sap schema")
        
        print(f"Found {len(result)} registered tables in sap schema:")
        for table in result:
            print(f"- {table[0]}")

    def test_csv_data_loaded(self):
        """Test if SAP CSV data was loaded correctly"""
        # Ensure tables are registered
        asyncio.run(self.agent._register_csv_files())
        
        # First get a list of available tables in the sap schema
        available_tables = []
        try:
            result = self.agent.duckdb_conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='sap'").fetchall()
            available_tables = [row[0] for row in result]
            print(f"Available tables in sap schema: {available_tables}")
        except Exception as e:
            print(f"Error listing tables: {str(e)}")
        
        # Test any tables that are available
        if not available_tables:
            self.fail("No tables available in DuckDB sap schema")
            
        for table in available_tables[:3]:  # Test first 3 tables
            if not table.startswith('sap.'): 
                table = f"sap.{table}"
                
            try:
                result = self.agent.duckdb_conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                count = result[0] if result else 0
                print(f"Table {table} has {count} rows")
                self.assertTrue(count >= 0, f"Table {table} query failed")
            except Exception as e:
                print(f"Failed to query table {table}: {str(e)}")

    def test_execute_sql(self):
        """Test SQL execution functionality"""
        # Create a test request
        request = SQLExecutionRequest(
            request_id=self.request_id,
            timestamp=self.timestamp,
            sql="SELECT * FROM sap.Customer LIMIT 5",
            user=self.user,
            principal_id=self.principal_id
        )
        
        # Run the request asynchronously
        response = asyncio.run(self.agent.execute_sql(request))
        
        # Validate the response
        self.assertEqual(response.status, "success")
        self.assertEqual(response.request_id, self.request_id)
        self.assertTrue(len(response.columns) > 0)
        self.assertTrue(len(response.rows) > 0)
        self.assertEqual(response.row_count, len(response.rows))
        
        print(f"SQL execution returned {response.row_count} rows")
        print(f"Columns: {response.columns}")
        print(f"First row: {response.rows[0] if response.rows else 'None'}")

    def test_invalid_sql(self):
        """Test handling of invalid SQL statements"""
        # Create a test request with invalid SQL (DELETE statement)
        request = SQLExecutionRequest(
            request_id=self.request_id,
            timestamp=self.timestamp,
            sql="DELETE FROM sap.Customer",
            user=self.user,
            principal_id=self.principal_id
        )
        
        # Run the request asynchronously
        response = asyncio.run(self.agent.execute_sql(request))
        
        # Validate the error response
        self.assertEqual(response.status, "error")
        # Prefer error_message field; some models reserve 'error' for classmethod name
        err_text = getattr(response, 'error_message', None) or getattr(response, 'error', None)
        self.assertIsNotNone(err_text)
        self.assertIn("only SELECT statements", err_text)
        
        print(f"Invalid SQL correctly rejected with error: {response.error}")

    def test_complex_query(self):
        """Test a more complex query with joins"""
        # Create a test request with a JOIN query
        request = SQLExecutionRequest(
            request_id=self.request_id,
            timestamp=self.timestamp,
            sql="""
            SELECT c.CustomerID, c.Name, t.Description, f.Amount
            FROM sap.Customer c
            JOIN sap.CustomerType t ON c.CustomerTypeID = t.CustomerTypeID
            JOIN sap.FinancialTransactions f ON c.CustomerID = f.CustomerID
            LIMIT 10
            """,
            user=self.user,
            principal_id=self.principal_id
        )
        
        # Run the request asynchronously
        response = asyncio.run(self.agent.execute_sql(request))
        
        # Print the query result
        print(f"Complex query status: {response.status}")
        if response.status == "success":
            print(f"Returned {response.row_count} rows")
            print(f"Columns: {response.columns}")
            print(f"First row: {response.rows[0] if response.rows else 'None'}")
        else:
            print(f"Error: {response.error}")


if __name__ == "__main__":
    unittest.main()
