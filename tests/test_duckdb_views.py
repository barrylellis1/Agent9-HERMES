import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import agent
from src.agents.a9_data_product_mcp_service_agent import A9_Data_Product_MCP_Service_Agent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("duckdb_view_test")

async def test_view_creation():
    """Test function to directly validate view creation from YAML contract"""
    
    logger.info("Starting view creation test")
    
    # Create agent config
    agent_config = {
        "sap_data_path": "C:/Users/barry/Documents/Agent 9/SAP DataSphere Data/datasphere-content-1.7/datasphere-content-1.7/SAP_Sample_Content/CSV/FI",
        "registry_path": "src/registry_references",
        "data_product_registry": "data_product_registry/data_product_registry.csv",
        "allow_custom_sql": True,
        "validate_sql": True
    }
    
    # Create agent instance
    logger.info("Creating agent instance")
    agent = await A9_Data_Product_MCP_Service_Agent.create_from_registry(agent_config, logger)
    
    # Register CSV files and views
    logger.info("Registering CSV files and views")
    test_tx_id = "test-view-creation-123"
    success = await agent._register_csv_files(transaction_id=test_tx_id)
    
    logger.info(f"View registration success: {success}")
    
    # Test querying the views
    required_views = [
        'fi_star_view',
        'fi_sales_by_customer_type_view',
        'fi_financial_transactions_view',
        'fi_customer_transactions_view'
    ]
    
    logger.info("Checking if views can be queried:")
    for view in required_views:
        try:
            # Try to execute a simple query against the view
            result = agent.duckdb_conn.execute(f"SELECT * FROM {view} LIMIT 1").fetchdf()
            row_count = len(result)
            logger.info(f"✅ View {view} exists and returned {row_count} row(s)")
            logger.info(f"   Columns: {result.columns.tolist()}")
        except Exception as e:
            logger.error(f"❌ View {view} failed: {str(e)}")
    
    logger.info("View test complete")

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_view_creation())
