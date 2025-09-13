"""
Integration test for Situation Awareness Agent and Data Product Agent.

This test focuses on the interaction between the Situation Awareness Agent
and the Data Product Agent, specifically for SQL delegation.
"""

import os
import sys
import asyncio
import logging
import pytest
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the mock agents
from tests.mocks.mock_agents import (
    MockAgentFactory,
    MockRegistryFactory,
    MockOrchestratorAgent,
    patch_registry_factory
)

# Import situation awareness models
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

# Import the agents
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent

# Define request/response classes if needed
class SituationDetectionRequest(BaseRequest):
    """Request for situation detection."""
    principal_context: Dict[str, Any]
    business_processes: List[str]
    timeframe: Dict[str, Any]
    comparison_type: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None

class SituationDetectionResponse(BaseResponse):
    """Response with detected situations."""
    situations: List[Dict[str, Any]]

@pytest.mark.asyncio
async def test_sql_delegation():
    """Test SQL delegation from Situation Awareness Agent to Data Product Agent."""
    logger.info("Starting SQL delegation integration test")
    
    # Patch the registry factory
    registry_factory = patch_registry_factory()
    
    try:
        # Create mock orchestrator
        orchestrator = await MockOrchestratorAgent.create({})
        
        # Create a Data Product Agent
        dp_agent_config = {
            "contract_path": "src/contracts/fi_star_schema.yaml",
            "db_type": "duckdb",
            "db_path": "data/agent9-hermes.duckdb",
            "orchestrator": orchestrator
        }
        dp_agent = await A9_Data_Product_Agent.create(dp_agent_config)
        
        # Register the Data Product Agent with the orchestrator
        orchestrator.register_agent("A9_Data_Product_Agent", dp_agent)
        
        # Create the Situation Awareness Agent using the orchestrator
        sa_agent_config = {
            "contract_path": "src/contracts/fi_star_schema.yaml",
            "target_domains": ["Finance"],
            "orchestrator": orchestrator
        }
        
        logger.info("Creating Situation Awareness Agent...")
        sa_agent = await A9_Situation_Awareness_Agent.create(sa_agent_config)
        
        # Verify KPI registry is loaded
        logger.info(f"KPI Registry loaded: {len(sa_agent.kpi_registry)} KPIs")
        
        # Test SQL delegation for a specific KPI
        test_kpi_id = "fin_revenue"
        if test_kpi_id in sa_agent.kpi_registry:
            kpi_def = sa_agent.kpi_registry[test_kpi_id]
            logger.info(f"Testing SQL delegation for KPI: {test_kpi_id}")
            
            # Define test parameters
            filters = {"region": "North America"}
            timeframe = {"start_date": "2025-01-01", "end_date": "2025-03-31", "period": "quarterly"}
            
            # Call the method that delegates to Data Product Agent
            sql = await sa_agent._get_sql_for_kpi(test_kpi_id, filters, timeframe)
            
            logger.info(f"Generated SQL: {sql}")
            
            # Verify SQL was generated
            if sql:
                logger.info("SQL delegation successful")
                return True
            else:
                logger.error("SQL delegation failed")
                return False
        else:
            logger.error(f"Test KPI {test_kpi_id} not found in registry")
            return False
            
    except Exception as e:
        logger.error(f"Error in SQL delegation test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if 'dp_agent' in locals():
            await dp_agent.disconnect()
        if 'sa_agent' in locals():
            await sa_agent.disconnect()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_sql_delegation())
