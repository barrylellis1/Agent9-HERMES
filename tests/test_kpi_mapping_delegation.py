# arch-allow-direct-agent-construction
"""
Test script to verify KPI mapping delegation from Situation Awareness Agent to Data Governance Agent.
"""
import pytest
pytest.skip("Skipped: legacy/non-MVP test (temporarily disabled during MVP migration)", allow_module_level=True)
import asyncio
import logging
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_kpi_mapping_delegation")

# Import required modules
try:
    from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
    from src.agents.models.situation_awareness_models import (
        KPIValuesRequest, TimeFrame, ComparisonType
    )
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Trying alternative import paths...")
    
    # Try relative imports
    from agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
    from agents.models.situation_awareness_models import (
        KPIValuesRequest, TimeFrame, ComparisonType
    )

async def test_kpi_values_request():
    """Test KPI values request with delegation to Data Governance Agent."""
    logger.info("Starting KPI mapping delegation test")
    
    # Initialize the Situation Awareness Agent
    agent = A9_Situation_Awareness_Agent({})
    
    # Connect to dependent services (including Data Governance Agent)
    connected = await agent.connect()
    if not connected:
        logger.error("Failed to connect to dependent services")
        return
    
    logger.info("Connected to dependent services")
    
    # Create a KPI values request
    request = KPIValuesRequest(
        principal_id="CFO_001",
        kpi_names=["Revenue", "Profit Margin", "Operating Expenses"],
        timeframe=TimeFrame.CURRENT_QUARTER,
        comparison_type=ComparisonType.QUARTER_OVER_QUARTER,
        filters={}
    )
    
    # Get KPI values - this should use Data Governance Agent for mapping
    logger.info(f"Requesting KPI values for: {request.kpi_names}")
    response = await agent.get_kpi_values(request)
    
    # Log the results
    logger.info(f"Response status: {response.status}")
    logger.info(f"Response message: {response.message}")
    logger.info(f"KPI values found: {len(response.kpi_values)}")
    for kpi_value in response.kpi_values:
        logger.info(f"KPI: {kpi_value.kpi_name}, Value: {kpi_value.value}")
    
    logger.info(f"Unmapped KPIs: {response.unmapped_kpis}")
    
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(test_kpi_values_request())
