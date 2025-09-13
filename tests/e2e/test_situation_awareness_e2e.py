"""
End-to-end test for Situation Awareness Agent.

This test focuses on testing the full workflow of the Situation Awareness Agent
with minimal mocking, including KPI loading, situation detection, and SQL delegation.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the orchestrator agent
from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent

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

# Define request/response classes
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

async def test_e2e_workflow():
    """Test end-to-end workflow of the Situation Awareness Agent."""
    logger.info("Starting end-to-end test for Situation Awareness Agent")
    
    # Create the orchestrator agent
    orchestrator_config = {}
    orchestrator = await A9_Orchestrator_Agent.create(orchestrator_config)
    
    try:
        # Create all required agents through the orchestrator
        logger.info("Creating Data Product Agent...")
        data_product_agent = await orchestrator.create_agent(
            "A9_Data_Product_Agent", 
            {
                "contract_path": "src/contracts/fi_star_schema.yaml"
            }
        )
        
        logger.info("Creating Principal Context Agent...")
        principal_context_agent = await orchestrator.create_agent(
            "A9_Principal_Context_Agent", 
            {}
        )
        
        logger.info("Creating Data Governance Agent...")
        data_governance_agent = await orchestrator.create_agent(
            "A9_Data_Governance_Agent", 
            {}
        )
        
        logger.info("Creating Situation Awareness Agent...")
        situation_awareness_agent = await orchestrator.create_agent(
            "A9_Situation_Awareness_Agent", 
            {
                "contract_path": "src/contracts/fi_star_schema.yaml",
                "target_domains": ["Finance"]
            }
        )
        
        # Connect all agents
        logger.info("Connecting all agents...")
        await orchestrator.connect_agents()
        
        # Verify KPI registry is loaded
        logger.info("Verifying KPI registry...")
        kpi_registry = situation_awareness_agent.kpi_registry
        logger.info(f"KPI Registry loaded: {len(kpi_registry)} KPIs")
        
        if len(kpi_registry) == 0:
            logger.error("KPI registry is empty")
            return False
        
        # Test situation detection
        logger.info("Testing situation detection...")
        
        # Create a situation detection request
        request = SituationDetectionRequest(
            principal_context={
                "role": "Finance Manager",
                "business_processes": ["Financial Reporting"],
                "domains": ["Finance"]
            },
            business_processes=["Financial Reporting"],
            timeframe={
                "start_date": "2025-01-01",
                "end_date": "2025-03-31",
                "period": "quarterly"
            },
            comparison_type="year_over_year",
            filters={
                "region": "North America"
            }
        )
        
        # Call the situation detection method
        logger.info("Calling detect_situations...")
        response = await situation_awareness_agent.detect_situations(request)
        
        # Verify response
        if response and hasattr(response, 'situations'):
            logger.info(f"Detected {len(response.situations)} situations")
            
            # Log the detected situations
            for situation in response.situations:
                logger.info(f"Situation: {situation.get('name', 'Unnamed')} - {situation.get('severity', 'Unknown')}")
            
            return True
        else:
            logger.error("No situations detected or invalid response")
            return False
            
    except Exception as e:
        logger.error(f"Error in end-to-end test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Disconnect all agents
        logger.info("Disconnecting all agents...")
        await orchestrator.disconnect_agents()

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_e2e_workflow())
