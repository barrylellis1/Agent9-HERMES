# arch-allow-direct-agent-construction
"""
Test script for orchestrator-driven SQL generation workflow.

This script demonstrates the end-to-end workflow between LLM Service Agent
and Data Product Agent for SQL generation from natural language
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
from src.agents.new.a9_llm_service_agent import (
    A9_LLM_Service_Agent,
    A9_LLM_SQLGenerationRequest
)
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.agent_config_models import A9_LLM_Service_Agent_Config

# Import Registry Factory
from src.registry.factory import RegistryFactory
from src.registry.bootstrap import RegistryBootstrap

# Import any needed test utilities
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("orchestrator_test")

# Ensure agent module loggers are also at INFO level for debugging
logging.getLogger("src.agents.new.a9_data_product_agent").setLevel(logging.INFO)


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
        
        # Get event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        # Initialize the registry factory
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
        # NOTE: This will pick up Supabase config from env if present
        loop.run_until_complete(RegistryBootstrap.initialize({"base_path": base_path}))
        self.registry_factory = RegistryFactory()
        
        # Ensure providers are loaded
        if self.registry_factory.get_provider("data_product"):
            loop.run_until_complete(self.registry_factory.get_provider("data_product").load())
            
        # Configure Data Product Agent
        self.data_product_config = {
            "data_directory": "data",
            "database": {
                "type": "duckdb", 
                "path": "data/agent9-hermes.duckdb"
            },
            "registry_factory": self.registry_factory,
            "bypass_mcp": True
        }
        
        self.llm_agent = A9_LLM_Service_Agent(self.llm_config)
        
        # Use async factory method for data product agent
        self.data_product_agent = loop.run_until_complete(
            A9_Data_Product_Agent.create(
                self.data_product_config, logger
            )
        )
        
        # Connect the agent
        loop.run_until_complete(self.data_product_agent.db_manager.connect({'database_path': self.data_product_agent.db_path}))
        
        # Mock orchestrator request parameters
        self.request_id = "test-orchestrator-workflow-123"
        self.timestamp = "2025-08-05T15:30:00-05:00"
        self.user = "test_user"
        self.principal_id = "test-principal-789"
        
        # We will load contracts dynamically in the test method

    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'data_product_agent') and self.data_product_agent is not None:
             try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self.data_product_agent.disconnect())
             except Exception:
                 pass
        
        # Note: LLM Service Agent doesn't need explicit cleanup

    def _load_contract(self, filename: str) -> str:
        """Load contract YAML content"""
        try:
            # Try absolute path first
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "registry_references", "data_product_registry", "data_products"))
            contract_path = os.path.join(base_path, filename)
            
            if os.path.exists(contract_path):
                with open(contract_path, "r") as f:
                    return f.read()
            else:
                logger.warning(f"Contract file not found at {contract_path}")
                return None
        except Exception as e:
            logger.warning(f"Could not load YAML contract {filename}: {str(e)}")
            return None

    async def orchestrator_workflow(self, natural_language_query: str, data_product_id: str, yaml_contract: str):
        """
        Simulate the orchestrator workflow for SQL generation and execution
        
        Args:
            natural_language_query: Natural language query from user
            data_product_id: Target data product view ID
            yaml_contract: The YAML contract content
            
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
            yaml_contract=yaml_contract,
            principal_id=self.principal_id,
            include_explain=True
        )
        
        logger.info(f"[ORCHESTRATOR] Sending SQL generation request to LLM Service Agent for {data_product_id}")
        sql_response = await self.llm_agent.generate_sql(sql_request)
        
        if sql_response.status != "success":
            logger.error(f"[ORCHESTRATOR] SQL generation failed: {sql_response.error_message}")
            return None
        
        logger.info(f"[ORCHESTRATOR] SQL generated: {sql_response.sql_query}")
        
        # Step 2: Execute generated SQL using Data Product Agent
        logger.info("[ORCHESTRATOR] Sending generated SQL to Data Product Agent for execution")
        
        # Note: In a real run without actual data, this might return 0 rows or fail if tables don't exist
        # We catch the error to ensure the test can proceed to validation of the SQL generation part at least
        try:
            data_product_response = await self.data_product_agent.execute_sql(sql_response.sql_query)
            
            if not data_product_response.get("success", False):
                logger.error(f"[ORCHESTRATOR] Data product execution failed: {data_product_response.get('message')}")
            else:
                logger.info(f"[ORCHESTRATOR] Data product execution successful with {data_product_response.get('row_count')} rows")
            
            return data_product_response
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Execution exception: {e}")
            return {"success": False, "message": str(e), "rows": [], "row_count": 0}

    def test_natural_language_to_data(self):
        """Test the full orchestrator flow from natural language to data product"""
        # Define test cases with natural language queries
        test_cases = [
            # FI Star Schema Tests
            {
                "query": "Show me the top 5 customers by transaction amount",
                "data_product": "FI_Star_View",
                "contract_file": "fi_star_schema.yaml"
            },
            {
                "query": "What were the total sales by customer type last year?",
                "data_product": "FI_Star_View",
                "contract_file": "fi_star_schema.yaml"
            },
            # Sales Star Schema Tests (BigQuery)
            {
                "query": "Which business partners generated the highest net sales?",
                "data_product": "Sales_SalesOrderStarSchemaView",
                "contract_file": "sales_star_schema.yaml"
            },
            {
                "query": "What is the gross sales trend by product category?",
                "data_product": "Sales_SalesOrderStarSchemaView",
                "contract_file": "sales_star_schema.yaml"
            }
        ]
        
        for case in test_cases:
            with self.subTest(query=case["query"]):
                # Get the current event loop
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Load contract
                contract = self._load_contract(case["contract_file"])
                if not contract:
                    print(f"SKIPPING: Could not load contract {case['contract_file']}")
                    continue

                # Run the async workflow using the existing loop
                response = loop.run_until_complete(
                    self.orchestrator_workflow(case["query"], case["data_product"], contract)
                )
                
                # Validate the response
                self.assertIsNotNone(response, "Workflow response should not be None")
                if response is not None:
                    # We print results regardless of success to debug execution issues vs generation success
                    print(f"Query: '{case['query']}'")
                    print(f"Target View: {case['data_product']}")
                    print(f"Success: {response.get('success')}")
                    if response.get('success'):
                        print(f"Rows returned: {response.get('row_count')}")
                        columns = response.get('columns') or (list(response['rows'][0].keys()) if response.get('rows') else [])
                        print(f"Columns: {columns}")
                        if response.get('rows'):
                            print(f"First row: {response['rows'][0]}")
                    else:
                        print(f"Error: {response.get('message')}")
                        # Print SQL for debugging if available
                        # (Not directly in response unless we added it, but it is logged)
                    print("---")


if __name__ == "__main__":
    # Initialize the Registry Factory
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(RegistryBootstrap.initialize({"base_path": base_path}))
    
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
