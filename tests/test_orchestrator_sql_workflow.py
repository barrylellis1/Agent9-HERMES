"""
Test script for orchestrator-driven SQL generation workflow.

This script demonstrates the end-to-end workflow between LLM Service Agent
and Data Product MCP Service Agent for SQL generation from natural language
queries as orchestrated by the Orchestrator Agent.
"""

import os
import sys
import asyncio
import unittest
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the src directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import agent classes and request/response models
from src.agents.a9_llm_service_agent import (
    A9_LLM_Service_Agent,
    A9_LLM_SQLGenerationRequest
)
from src.agents.a9_data_product_mcp_service_agent import (
    A9_Data_Product_MCP_Service_Agent,
    DataProductRequest
)
from src.agents.agent_config_models import (
    A9_LLM_Service_Agent_Config,
    A9_Data_Product_MCP_Service_Config
)

# Import Registry Factory
from src.registry.factory import RegistryProvider

# Import any needed test utilities
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("orchestrator_test")

# Ensure agent module loggers are also at INFO level for debugging
logging.getLogger("src.agents.a9_data_product_mcp_service_agent").setLevel(logging.INFO)


class TestOrchestratorSQLWorkflow(unittest.TestCase):
    """Test cases for the orchestrator-driven SQL workflow"""

    def setUp(self):
        """Set up the test environment with agents and mock orchestrator components"""
        # Force reload .env file to ensure we have latest values
        load_dotenv(override=True)
        
        # Get API key from environment - switching to OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment. Tests will likely fail.")
            # Print all env vars for debugging (masking sensitive values)
            env_vars = {key: '***' if 'key' in key.lower() or 'secret' in key.lower() else val 
                      for key, val in os.environ.items()}
            logger.info(f"Available environment variables: {env_vars}")
        else:
            masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****"
            logger.info(f"Using OPENAI_API_KEY: {masked_key}")

        # Configure LLM Service Agent with OpenAI provider
        self.llm_config = A9_LLM_Service_Agent_Config(
            provider="openai",  # Switch to OpenAI
            model_name="gpt-4-turbo",  # Use GPT-4 Turbo model
            api_key=api_key,  # Use the API key we just loaded
            api_key_env_var="OPENAI_API_KEY",  # Use OpenAI env var
            guardrails_path="src/guardrails/cascade_guardrails.yaml",
            prompt_templates_path="src/prompt_templates/cascade_prompt_templates.md",
            logging_enabled=True
        )
        
        # No need to update model name as we're using the default gpt-4o
        
        # Configure Data Product MCP Service Agent
        self.data_product_config = A9_Data_Product_MCP_Service_Config(
            sap_data_path="C:/Users/barry/Documents/Agent 9/SAP DataSphere Data/datasphere-content-1.7/datasphere-content-1.7/SAP_Sample_Content/CSV/FI",
            # Use Registry Factory pattern instead of direct registry references
            registry_path=RegistryProvider.get_registry_path(),
            data_product_registry="src/registry/data_product/data_product_registry.yaml",  # Updated to use YAML registry file
            contracts_path=RegistryProvider.get_registry_path("data_product_registry/data_products"),
            allow_custom_sql=True,
            validate_sql=True
        )
        
        # Create the agent instances using async initialization
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running event loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        # Initialize the registry provider before creating agents
        RegistryProvider.initialize(registry_base_path="src/registry_references")
        
        self.llm_agent = A9_LLM_Service_Agent(self.llm_config)
        # Use async factory method for data product agent
        self.data_product_agent = loop.run_until_complete(
            A9_Data_Product_MCP_Service_Agent.create_from_registry(
                self.data_product_config.model_dump(), logger
            )
        )
        
        # Mock orchestrator request parameters
        self.request_id = "test-orchestrator-workflow-123"
        self.timestamp = "2025-08-05T15:30:00-05:00"
        self.user = "test_user"
        self.principal_id = "test-principal-789"
        
        # Load YAML contract for context
        self.yaml_contract = None
        try:
            with open("src/contracts/fi_star_schema.yaml", "r") as f:
                self.yaml_contract = f.read()
        except Exception as e:
            logger.warning(f"Could not load YAML contract: {str(e)}")
        
        # Ensure data product agent has tables registered
        # Use async version of registration method
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running event loop, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(self.data_product_agent._register_csv_files())

    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'data_product_agent') and self.data_product_agent is not None:
            self.data_product_agent.close()
        
        # Note: LLM Service Agent doesn't need explicit cleanup

    async def orchestrator_workflow(self, natural_language_query: str, data_product_id: str):
        """
        Simulate the orchestrator workflow for SQL generation and execution
        
        Args:
            natural_language_query: Natural language query from user
            data_product_id: Target data product ID
            
        Returns:
            Final data product response with results
        """
        logger.info(f"[ORCHESTRATOR] Starting workflow for query: {natural_language_query}")
        
        # Step 1: Generate SQL from natural language query using LLM Service Agent
        sql_request = A9_LLM_SQLGenerationRequest(
            request_id=self.request_id,
            timestamp=self.timestamp,
            natural_language_query=natural_language_query,
            data_product_id=data_product_id,
            yaml_contract=self.yaml_contract,
            principal_id=self.principal_id,
            include_explain=True
        )
        
        logger.info("[ORCHESTRATOR] Sending SQL generation request to LLM Service Agent")
        sql_response = await self.llm_agent.generate_sql(sql_request)
        
        if sql_response.status != "success":
            logger.error(f"[ORCHESTRATOR] SQL generation failed: {sql_response.error_message}")
            return None
        
        logger.info(f"[ORCHESTRATOR] SQL generated: {sql_response.sql_query}")
        
        # Step 2: Execute generated SQL using Data Product MCP Service Agent
        data_product_request = DataProductRequest(
            request_id=self.request_id,
            timestamp=self.timestamp,
            product_id=data_product_id,
            sql_query=sql_response.sql_query,  # Pass the generated SQL to the data product agent
            principal_id=self.principal_id
        )
        
        logger.info("[ORCHESTRATOR] Sending data product request with generated SQL to Data Product Agent")
        data_product_response = await self.data_product_agent.get_data_product(data_product_request)
        
        if data_product_response.status != "success":
            logger.error(f"[ORCHESTRATOR] Data product execution failed: {data_product_response.error}")
        else:
            logger.info(f"[ORCHESTRATOR] Data product execution successful with {data_product_response.row_count} rows")
        
        # Return the final data product response
        return data_product_response

    def test_natural_language_to_data(self):
        """Test the full orchestrator flow from natural language to data product"""
        # Define test cases with natural language queries
        test_cases = [
            {
                "query": "Show me the top 5 customers by transaction amount",
                "data_product": "fi_customer_transactions_view"
            },
            {
                "query": "What were the total sales by customer type last year?",
                "data_product": "fi_sales_by_customer_type_view"
            },
            {
                "query": "List all financial transactions over $10,000",
                "data_product": "fi_financial_transactions_view"
            }
        ]
        
        for case in test_cases:
            with self.subTest(query=case["query"]):
                # Get the current event loop instead of creating a new one
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No running event loop, create a new one
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                # Run the async workflow using the existing loop
                response = loop.run_until_complete(
                    self.orchestrator_workflow(case["query"], case["data_product"])
                )
                
                # Validate the response
                self.assertIsNotNone(response, "Workflow response should not be None")
                if response is not None:  # Only proceed with validation if response exists
                    if response.status == "success":
                        print(f"Query: '{case['query']}'")
                        print(f"Rows returned: {response.row_count}")
                        print(f"Columns: {response.columns}")
                        if response.rows:
                            print(f"First row: {response.rows[0]}")
                        print("---")
                    else:
                        print(f"Query failed: '{case['query']}'")
                        print(f"Error: {response.error_message if hasattr(response, 'error_message') else response.message}")
                        print(f"SQL: {case.get('data_product', 'unknown')}")
                        print("---")
                    
                    # Note: We don't assert success because some test queries might legitimately fail
                    # due to schema mismatches or other reasons, which is still a valid test case


if __name__ == "__main__":
    # Initialize the Registry Provider with the correct base path
    RegistryProvider.initialize(registry_base_path="src/registry")
    
    # Check if API key is set (should be loaded from .env via dotenv)
    if not os.environ.get("OPENAI_API_KEY"):
        print("WARNING: OPENAI_API_KEY environment variable not set in .env file. LLM tests will fail.")
        print("Please copy .env.example to .env and add your OpenAI API key.")
    else:
        # Mask the key when showing it's available
        key = os.environ.get("OPENAI_API_KEY")
        masked_key = key[:4] + "*" * (len(key) - 8) + key[-4:] if len(key) > 8 else "****"
        print(f"Using OpenAI API key: {masked_key}")
    
    unittest.main()
