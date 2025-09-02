# test_view_data.py
import pytest
pytestmark = pytest.mark.skip(reason="Legacy root-level test not aligned with HERMES test layout; run tests under tests/ instead")

import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.services.a9_data_product_mcp_service import A9_Data_Product_MCP_Service

def inspect_view_data():
    """Initializes the MCP service and queries for distinct filter values."""
    print("Initializing MCP Service to load data...")
    mcp_service = A9_Data_Product_MCP_Service()
    print("Service initialized.")

    queries = {
        "Account Hierarchy Desc": "SELECT DISTINCT \"Account Hierarchy Desc\" FROM FI_Star_View LIMIT 10",
        "Profit Center Hierarchyid": "SELECT DISTINCT \"Profit Center Hierarchyid\" FROM FI_Star_View LIMIT 10",
        "Customer Hierarchyid": "SELECT DISTINCT \"Customer Hierarchyid\" FROM FI_Star_View LIMIT 10"
    }

    for name, query in queries.items():
        print(f"\n--- Querying for distinct values in: {name} ---")
        print(f"Executing: {query}")
        result_df = mcp_service.execute_query(query)

        if not result_df.empty:
            print(result_df)
        else:
            print("No distinct values found.")

if __name__ == "__main__":
    inspect_view_data()
