#!/usr/bin/env python
"""
Test script for SQL execution using the Data Product MCP Service Agent.
This demonstrates how to use the agent to execute SQL queries against the registry.
"""

import pytest
pytestmark = pytest.mark.skip(reason="Legacy root-level test not aligned with HERMES test layout; run tests under tests/ instead")

import asyncio
import logging
import os
import sys
import yaml
from typing import Dict, Any, List

# Add project root to path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import agent components
from src.agents.a9_data_product_mcp_service_agent import (
    A9_Data_Product_MCP_Service_Agent,
    SQLExecutionRequest,
    SQLExecutionResponse
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SQL_Test")

async def main():
    """Main function to test SQL execution"""
    try:
        # Create agent configuration
        config = {
            "name": "Data_Product_MCP_Service_Agent",
            "version": "1.0",
            "description": "Test SQL execution against registry data products",
            "data_directory": "src/data",
            "data_product_registry": "src/registry/data_product/data_product_registry.yaml",
            "backend": "duckdb",
            "contracts_path": "src/contracts",
            "principal": "CFO"  # Set principal context
        }
        
        logger.info("Creating Data Product MCP Service Agent...")
        agent = await A9_Data_Product_MCP_Service_Agent.create(config, logger)
        logger.info(f"Agent created successfully. Registry status: has_data_products={agent.registry.get('has_data_products', False)}")
        
        # Log available data products
        data_products = agent.registry.get('data_products', [])
        logger.info(f"Available data products: {len(data_products)}")
        for product in data_products:
            logger.info(f"  - {product.product_id}: {product.name}")
        
        # Test queries
        test_queries = [
            # Simple SELECT from registry data products
            "SELECT * FROM data_products LIMIT 5",
            
            # Query for financial transactions
            "SELECT * FROM fi_financial_transactions_view LIMIT 5",
            
            # Query for sales by customer type
            "SELECT * FROM fi_sales_by_customer_type_view LIMIT 5",
            
            # Example of a more complex query
            """
            SELECT 
                customer_type, 
                COUNT(*) as transaction_count, 
                SUM(amount) as total_amount
            FROM fi_customer_transactions_view
            GROUP BY customer_type
            """
        ]
        
        # Execute each query
        for i, sql in enumerate(test_queries):
            logger.info(f"Executing query {i+1}:\n{sql}")
            
            # Create request
            request = SQLExecutionRequest(
                request_id=f"test-query-{i+1}",
                sql=sql,
                context={"test": True},
                principal_id="CFO"  # Required field
            )
            
            # Execute query
            response = await agent.execute_sql(request)
            
            # Log results
            logger.info(f"Query {i+1} status: {response.status}")
            if response.status == "success":
                logger.info(f"Columns: {response.columns}")
                logger.info(f"Row count: {response.row_count}")
                
                # Log first few rows
                for j, row in enumerate(response.rows[:3]):
                    logger.info(f"  Row {j+1}: {row}")
                if response.row_count > 3:
                    logger.info(f"  ... and {response.row_count - 3} more rows")
            else:
                logger.error(f"Error: {response.error_message}")
            
            logger.info("-" * 50)
        
        # Clean up
        agent.close()
        logger.info("Test completed successfully")
        
    except Exception as e:
        logger.exception(f"Error executing test: {str(e)}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
