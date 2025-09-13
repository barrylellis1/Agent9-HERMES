"""
Integration test for Situation Awareness Agent and Data Product Agent with detailed debugging.

This test focuses on the interaction between the Situation Awareness Agent
and the Data Product Agent, specifically for SQL delegation.
"""

import os
import sys
import asyncio
import logging
import traceback
import pytest
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the mock agents
try:
    from tests.mocks.mock_agents import (
        MockAgentFactory,
        MockRegistryFactory,
        MockOrchestratorAgent,
        patch_registry_factory
    )
    logger.info("Successfully imported mock agents")
except ImportError as e:
    logger.error(f"Failed to import mock agents: {str(e)}")
    traceback.print_exc()
    pytest.skip(f"Skipping test due to import error: {e}", allow_module_level=True)

# Import situation awareness models
try:
    from src.agents.models.situation_awareness_models import (
        SituationSeverity,
        Situation,
        KPIDefinition,
        KPIValue,
        TimeFrame,
        ComparisonType,
        BusinessProcess,
        PrincipalRole,
        BaseRequest,
        BaseResponse
    )
    logger.info("Successfully imported situation awareness models")
except ImportError as e:
    logger.error(f"Failed to import situation awareness models: {str(e)}")
    traceback.print_exc()
    pytest.skip(f"Skipping test due to import error: {e}", allow_module_level=True)

# Import the agents
try:
    from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
    from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
    logger.info("Successfully imported agent implementations")
except ImportError as e:
    logger.error(f"Failed to import agent implementations: {str(e)}")
    traceback.print_exc()
    pytest.skip(f"Skipping test due to import error: {e}", allow_module_level=True)

@pytest.mark.asyncio
async def test_sql_delegation():
    """Test SQL delegation from Situation Awareness Agent to Data Product Agent."""
    logger.info("Starting SQL delegation integration test")
    
    # Patch the registry factory
    try:
        registry_factory = patch_registry_factory()
        logger.info("Successfully patched registry factory")
    except Exception as e:
        logger.error(f"Failed to patch registry factory: {str(e)}")
        traceback.print_exc()
        return False
    
    try:
        # Create mock orchestrator
        logger.info("Creating Mock Orchestrator Agent...")
        orchestrator = await MockOrchestratorAgent.create({})
        logger.info("Mock Orchestrator Agent created successfully")
        
        # Create a Data Product Agent
        dp_agent_config = {
            "contract_path": "src/contracts/fi_star_schema.yaml",
            "db_type": "duckdb",
            "db_path": "data/agent9-hermes.duckdb",
            "orchestrator": orchestrator
        }
        logger.info("Creating Data Product Agent...")
        dp_agent = await A9_Data_Product_Agent.create(dp_agent_config)
        logger.info("Data Product Agent created successfully")
        
        # Register the Data Product Agent with the orchestrator
        orchestrator.register_agent("A9_Data_Product_Agent", dp_agent)
        logger.info("Data Product Agent registered with orchestrator")
        
        # Create the Situation Awareness Agent using the orchestrator
        sa_agent_config = {
            "contract_path": "src/contracts/fi_star_schema.yaml",
            "target_domains": ["Finance"],
            "orchestrator": orchestrator
        }
        
        logger.info("Creating Situation Awareness Agent...")
        sa_agent = await A9_Situation_Awareness_Agent.create(sa_agent_config)
        logger.info("Situation Awareness Agent created successfully")
        
        # Verify KPI registry is loaded
        logger.info(f"KPI Registry loaded: {len(sa_agent.kpi_registry)} KPIs")
        
        # List all KPIs in registry for debugging
        for kpi_id, kpi_def in sa_agent.kpi_registry.items():
            logger.info(f"KPI in registry: {kpi_id}")
        
        # Test SQL delegation for a specific KPI
        test_kpi_id = "fin_revenue"
        if test_kpi_id in sa_agent.kpi_registry:
            kpi_def = sa_agent.kpi_registry[test_kpi_id]
            logger.info(f"Testing SQL delegation for KPI: {test_kpi_id}")
            logger.info(f"KPI definition: {kpi_def}")
            
            # Define test parameters
            filters = {"region": "North America"}
            timeframe = {"start_date": "2025-01-01", "end_date": "2025-03-31", "period": "quarterly"}
            
            # Check if the method exists
            if hasattr(sa_agent, '_get_sql_for_kpi'):
                logger.info("_get_sql_for_kpi method exists")
            else:
                logger.error("_get_sql_for_kpi method does not exist")
                # Try alternative methods
                methods = [m for m in dir(sa_agent) if m.startswith('_') and 'sql' in m.lower()]
                logger.info(f"Available SQL-related methods: {methods}")
                return False
            
            # Call the method that delegates to Data Product Agent
            try:
                logger.info("Calling _get_sql_for_kpi method...")
                sql = await sa_agent._get_sql_for_kpi(test_kpi_id, filters, timeframe)
                logger.info(f"Generated SQL: {sql}")
                
                # Verify SQL was generated
                if sql:
                    logger.info("SQL delegation successful")
                    return True
                else:
                    logger.error("SQL delegation failed - empty SQL returned")
                    return False
            except Exception as e:
                logger.error(f"Error calling _get_sql_for_kpi: {str(e)}")
                traceback.print_exc()
                return False
        else:
            logger.error(f"Test KPI {test_kpi_id} not found in registry")
            logger.info(f"Available KPIs: {list(sa_agent.kpi_registry.keys())}")
            return False
            
    except Exception as e:
        logger.error(f"Error in SQL delegation test: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if 'orchestrator' in locals():
            try:
                # The orchestrator will handle disconnecting all registered agents
                await orchestrator.disconnect()
                logger.info("Orchestrator and all registered agents disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting orchestrator: {str(e)}")
                # Try to disconnect individual agents as fallback
                if 'dp_agent' in locals():
                    try:
                        await dp_agent.disconnect()
                        logger.info("Data Product Agent disconnected")
                    except Exception as e:
                        logger.error(f"Error disconnecting Data Product Agent: {str(e)}")
                if 'sa_agent' in locals():
                    try:
                        await sa_agent.disconnect()
                        logger.info("Situation Awareness Agent disconnected")
                    except Exception as e:
                        logger.error(f"Error disconnecting Situation Awareness Agent: {str(e)}")

if __name__ == "__main__":
    # Run the test
    try:
        result = asyncio.run(test_sql_delegation())
        logger.info(f"Test result: {'PASSED' if result else 'FAILED'}")
        sys.exit(0 if result else 1)
    except Exception as e:
        logger.error(f"Unhandled exception in test: {str(e)}")
        traceback.print_exc()
        sys.exit(1)
