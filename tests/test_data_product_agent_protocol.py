 # arch-allow-direct-agent-construction
"""
Test script for Data Product Agent protocol implementation.
This script verifies that the Data Product Agent correctly implements the DataProductProtocol.
"""

import asyncio
import os
import sys
import logging
import traceback
from typing import Dict, Any, List

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Data Product Agent
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.agent_config_models import A9_Data_Product_Agent_Config

# Configure logging
log_file = "data_product_agent_test.log"
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add file handler
file_handler = logging.FileHandler(log_file, mode='w')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Get logger and add file handler
logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

async def test_data_product_agent():
    """Test the Data Product Agent protocol implementation."""
    logger.info("Starting Data Product Agent protocol test")
    
    try:
        # Check if data directory exists
        if not os.path.exists("data"):
            logger.error("Data directory does not exist. Creating it.")
            os.makedirs("data", exist_ok=True)
            
        # Check if database file exists
        db_path = "data/agent9-hermes.duckdb"
        if not os.path.exists(db_path):
            logger.warning(f"Database file {db_path} does not exist. It will be created automatically.")
            
        # Check if contracts directory exists
        if not os.path.exists("src/contracts"):
            logger.error("Contracts directory does not exist")
            return False
            
        # Check if data product registry file exists
        registry_file = "src/contracts/dp_fi_20250516_001_prejoined.yaml"
        if not os.path.exists(registry_file):
            logger.error(f"Data product registry file {registry_file} does not exist")
            return False
    
        # Create configuration for the agent
        logger.info("Creating agent configuration")
        config = A9_Data_Product_Agent_Config(
            data_directory="data",
            database={"type": "duckdb", "path": db_path},
            registry_path="src/contracts",
            data_product_registry="dp_fi_20250516_001_prejoined.yaml",
            allow_custom_sql=True,
            validate_sql=True,
            log_queries=True,
            log_level="INFO"
        )
        
        # Log configuration details
        logger.info(f"Configuration: data_directory={config.data_directory}")
        logger.info(f"Configuration: database={config.database}")
        logger.info(f"Configuration: registry_path={config.registry_path}")
        logger.info(f"Configuration: data_product_registry={config.data_product_registry}")
        
        # Create the agent
        logger.info("Creating Data Product Agent")
        try:
            agent = await A9_Data_Product_Agent.create(config)
            logger.info("Agent created successfully")
        except Exception as e:
            logger.error(f"Failed to create Data Product Agent: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    except Exception as e:
        logger.error(f"Error during test setup: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    
    try:
        # Test list_data_products
        logger.info("Testing list_data_products method")
        data_products = await agent.list_data_products()
        logger.info(f"Found {len(data_products)} data products")
        assert isinstance(data_products, list), "list_data_products should return a list"
        
        # Test get_data_product if any products exist
        if len(data_products) > 0:
            product_id = data_products[0].get('id')
            if product_id:
                logger.info(f"Testing get_data_product method with ID: {product_id}")
                product_result = await agent.get_data_product(product_id)
                logger.info(f"Retrieved data product: {product_result.get('name', 'Unknown')}")
                assert 'data_product' in product_result, "Missing data_product in response"
                assert 'transaction_id' in product_result, "Missing transaction_id in response"
                assert 'success' in product_result, "Missing success in response"
        
        # Test generate_sql
        logger.info("Testing generate_sql method")
        sql_result = await agent.generate_sql("Show me all financial data for Q1 2025")
        logger.info(f"Generated SQL: {sql_result.get('sql', 'No SQL generated')}")
        assert 'sql' in sql_result, "Missing sql in response"
        assert 'transaction_id' in sql_result, "Missing transaction_id in response"
        assert 'success' in sql_result, "Missing success in response"
        
        # Test execute_sql with the generated SQL if available
        if sql_result.get('sql'):
            logger.info("Testing execute_sql method")
            sql_to_execute = sql_result['sql']
            execute_result = await agent.execute_sql(sql_to_execute)
            logger.info(f"SQL execution result has {len(execute_result.get('data', []))} rows")
            assert 'data' in execute_result, "Missing data in response"
            assert 'columns' in execute_result, "Missing columns in response"
            assert 'transaction_id' in execute_result, "Missing transaction_id in response"
            assert 'success' in execute_result, "Missing success in response"
            
            # Test create_view with the generated SQL
            logger.info("Testing create_view method")
            view_result = await agent.create_view(
                "test_view_" + sql_result['transaction_id'][:8],
                sql_to_execute,
                {"description": "Test view created by protocol test"}
            )
            logger.info(f"View creation result: {view_result.get('message', 'No message')}")
            assert 'view_name' in view_result, "Missing view_name in response"
            assert 'transaction_id' in view_result, "Missing transaction_id in response"
            assert 'success' in view_result, "Missing success in response"
        
        logger.info("All protocol methods tested successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error testing Data Product Agent: {str(e)}", exc_info=True)
        return False
    finally:
        # Clean up
        await agent.disconnect()
        logger.info("Data Product Agent disconnected")

if __name__ == "__main__":
    try:
        result = asyncio.run(test_data_product_agent())
        if result:
            logger.info("✅ Data Product Agent protocol test completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Data Product Agent protocol test failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unhandled exception in test: {str(e)}")
        logger.error(traceback.format_exc())
        sys.exit(1)
