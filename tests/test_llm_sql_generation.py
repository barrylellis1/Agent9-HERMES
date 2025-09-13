# arch-allow-direct-agent-construction
"""
Test SQL generation functionality of the LLM Service Agent.
This tests the orchestrator-driven workflow for generating SQL from natural language queries.
"""

import os
import sys
import asyncio
import logging
import yaml
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the agents and models
from src.agents.a9_llm_service_agent import (
    A9_LLM_Service_Agent,
    A9_LLM_SQLGenerationRequest,
    A9_LLM_SQLGenerationResponse
)
from src.agents.a9_data_product_mcp_service_agent import (
    A9_Data_Product_MCP_Service_Agent,
    SQLExecutionRequest,
    DataProductResponse
)

# Import configuration models
from src.agents.agent_config_models import (
    A9_LLM_Service_Agent_Config,
    A9_Data_Product_MCP_Service_Config
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def load_yaml_contract():
    """Load the YAML contract for testing"""
    try:
        contract_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'contracts', 'fi_star_schema.yaml'))
        with open(contract_path, 'r') as f:
            yaml_contract = f.read()
        return yaml_contract
    except Exception as e:
        logger.error(f"Error loading YAML contract: {str(e)}")
        return None


async def test_sql_generation():
    """Test SQL generation from natural language query"""
    logger.info("Starting SQL generation test")

    # Create LLM Service Agent instance (orchestrator-driven)
    llm_agent = A9_LLM_Service_Agent({
        "provider": "anthropic",
        "model_name": "claude-3-sonnet-20240229",
        "api_key_env_var": "ANTHROPIC_API_KEY"
    })

    # Load the YAML contract
    yaml_contract = await load_yaml_contract()
    if not yaml_contract:
        logger.error("Failed to load YAML contract, aborting test")
        return

    # Define a test natural language query
    nlq = "Show me the top 5 vendors by spend in Q1 2025"

    # Create the request
    request = A9_LLM_SQLGenerationRequest(
        request_id=f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        timestamp=datetime.now().isoformat(),
        principal_id="test_user",
        natural_language_query=nlq,
        data_product_id="fi_star_schema",
        yaml_contract=yaml_contract,
        include_explain=True
    )

    # Generate SQL
    logger.info(f"Generating SQL for query: {nlq}")
    sql_response = await llm_agent.generate_sql(request)

    # Log the response
    logger.info(f"SQL Generation Status: {sql_response.status}")
    logger.info(f"Generated SQL: {sql_response.sql_query}")
    logger.info(f"Confidence: {sql_response.confidence}")
    
    if sql_response.warnings:
        logger.warning(f"Warnings: {', '.join(sql_response.warnings)}")
    
    if sql_response.explanation:
        logger.info(f"Explanation: {sql_response.explanation}")

    if sql_response.status == "error":
        logger.error(f"Error generating SQL: {sql_response.error_message}")
        return

    # Now test execution of the generated SQL with the Data Product MCP Service Agent
    logger.info("Testing execution of the generated SQL")
    
    # Create Data Product MCP Service Agent instance (orchestrator-driven)
    dp_agent = await A9_Data_Product_MCP_Service_Agent.create_from_registry({
        "sap_data_path": "C:/Users/barry/Documents/Agent 9/SAP DataSphere Data/datasphere-content-1.7/datasphere-content-1.7/SAP_Sample_Content/CSV/FI",
        "log_queries": True
    })

    # Create SQL execution request
    sql_exec_request = SQLExecutionRequest(
        request_id=f"test_exec_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        timestamp=datetime.now().isoformat(),
        principal_id="test_user",
        sql_query=sql_response.sql_query
    )

    # Execute the SQL
    logger.info("Executing the generated SQL query")
    sql_exec_response = await dp_agent.execute_sql(sql_exec_request)

    # Log the result
    logger.info(f"SQL Execution Status: {sql_exec_response.status}")
    if sql_exec_response.status == "success":
        logger.info(f"Row Count: {sql_exec_response.row_count}")
        logger.info(f"Results sample: {json.dumps(sql_exec_response.results[:3], indent=2) if sql_exec_response.results else 'No results'}")
    else:
        logger.error(f"Error executing SQL: {sql_exec_response.error_message}")

    return {
        "generation": sql_response,
        "execution": sql_exec_response
    }


async def test_data_product_generation():
    """Test SQL generation and data product retrieval in an orchestrator-driven workflow"""
    logger.info("Starting integrated data product test")

    # Create agent instances (orchestrator-driven)
    llm_agent = A9_LLM_Service_Agent({
        "provider": "anthropic",
        "model_name": "claude-3-sonnet-20240229",
        "api_key_env_var": "ANTHROPIC_API_KEY"
    })
    
    dp_agent = await A9_Data_Product_MCP_Service_Agent.create_from_registry({
        "sap_data_path": "C:/Users/barry/Documents/Agent 9/SAP DataSphere Data/datasphere-content-1.7/datasphere-content-1.7/SAP_Sample_Content/CSV/FI",
        "log_queries": True
    })

    # Load the YAML contract
    yaml_contract = await load_yaml_contract()
    if not yaml_contract:
        logger.error("Failed to load YAML contract, aborting test")
        return

    # Define a test natural language query
    nlq = "Show me total AR by region for the latest quarter"

    # Step 1: NLP interface would understand the query and identify data_product_id
    # Simulated result of NLP interface processing
    data_product_id = "fi_star_schema"
    
    # Step 2: Generate SQL based on the query
    sql_gen_request = A9_LLM_SQLGenerationRequest(
        request_id=f"test_dp_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        timestamp=datetime.now().isoformat(),
        principal_id="test_user",
        natural_language_query=nlq,
        data_product_id=data_product_id,
        yaml_contract=yaml_contract,
        include_explain=True
    )
    
    # Generate SQL
    logger.info(f"Generating SQL for data product query: {nlq}")
    sql_response = await llm_agent.generate_sql(sql_gen_request)
    
    if sql_response.status == "error":
        logger.error(f"Error generating SQL: {sql_response.error_message}")
        return
        
    logger.info(f"Generated SQL: {sql_response.sql_query}")
    
    # Step 3: Use generated SQL to get data product
    dp_request = SQLExecutionRequest(
        request_id=f"test_dp_exec_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        timestamp=datetime.now().isoformat(),
        principal_id="test_user",
        sql_query=sql_response.sql_query
    )
    
    # Execute and get data product
    logger.info("Retrieving data product using generated SQL")
    dp_response = await dp_agent.execute_sql(dp_request)
    
    # Log the result
    logger.info(f"Data Product Status: {dp_response.status}")
    if dp_response.status == "success":
        logger.info(f"Row Count: {dp_response.row_count}")
        logger.info(f"Results sample: {json.dumps(dp_response.results[:3], indent=2) if dp_response.results else 'No results'}")
    else:
        logger.error(f"Error retrieving data product: {dp_response.error_message}")
        
    return {
        "nlq": nlq,
        "sql_generation": sql_response,
        "data_product": dp_response
    }


async def main():
    """Run the tests"""
    logger.info("Running SQL generation tests")
    
    # Test basic SQL generation
    result1 = await test_sql_generation()
    
    # Test integrated data product workflow
    result2 = await test_data_product_generation()
    
    logger.info("Tests completed")
    return {
        "sql_generation_test": result1,
        "data_product_test": result2
    }


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
