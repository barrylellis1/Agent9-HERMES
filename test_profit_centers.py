# test_profit_centers.py
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from src.services.a9_data_product_mcp_service import A9_Data_Product_MCP_Service

def find_valid_profit_centers():
    """Initializes the MCP service and queries for valid profit centers."""
    print("Initializing MCP Service to load data...")
    mcp_service = A9_Data_Product_MCP_Service()
    print("Service initialized.")

    query = """
        SELECT DISTINCT "Profit Center Name"
        FROM FI_Star_View
        WHERE "Account Hierarchy Desc" = 'Gross Revenue'
    """

    print(f"Executing diagnostic query:\n{query}")
    result_df = mcp_service.execute_query(query)

    if not result_df.empty:
        print("\n--- Found Valid Profit Centers with Gross Revenue ---")
        print(result_df)
    else:
        print("\n--- No Profit Centers found with Gross Revenue data. ---")

if __name__ == "__main__":
    find_valid_profit_centers()
