"""
Test script to verify KPI view name resolution delegation from Situation Awareness Agent to Data Governance Agent.
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("kpi_mapping_test.log")
    ]
)
logger = logging.getLogger("kpi_view_resolution_test")

# Import required modules
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.models.situation_awareness_models import (
    KPIDefinition, TimeFrame, ComparisonType
)

async def test_kpi_view_resolution():
    """Test KPI view name resolution with delegation to Data Governance Agent."""
    logger.info("Starting KPI view name resolution test")
    
    # Initialize the Situation Awareness Agent with minimal config
    agent = A9_Situation_Awareness_Agent({
        "contract_path": "src/contracts/dp_fi_20250516_001_prejoined.yaml"
    })
    
    # Connect to dependent services (including Data Governance Agent)
    logger.info("Connecting to dependent services...")
    connected = await agent.connect()
    if not connected:
        logger.error("Failed to connect to dependent services")
        return
    
    logger.info("Connected to dependent services")
    
    # Create a test KPI definition
    test_kpi = KPIDefinition(
        name="Revenue",
        description="Total revenue for the company",
        data_product_id="dp_fi_20250516_001",
        calculation=None,
        business_processes=["Finance: Revenue Growth Analysis"]
    )
    
    # Test the _get_kpi_value method which should use Data Governance Agent for view name resolution
    logger.info(f"Testing _get_kpi_value for KPI: {test_kpi.name}")
    try:
        kpi_value = await agent._get_kpi_value(
            test_kpi,
            TimeFrame.CURRENT_QUARTER,
            ComparisonType.QUARTER_OVER_QUARTER,
            filters={}
        )
        
        logger.info(f"KPI Value result: {kpi_value}")
        logger.info(f"KPI Value: {kpi_value.value if kpi_value else 'None'}")
        
    except Exception as e:
        logger.error(f"Error getting KPI value: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(test_kpi_view_resolution())
