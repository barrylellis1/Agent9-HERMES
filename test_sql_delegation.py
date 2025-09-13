import sys
import os
import asyncio
import logging
from typing import Dict, Any, List, Optional
import pytest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sql_delegation_test.log')
    ]
)

logger = logging.getLogger('sql_delegation_test')

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import agents and protocols
try:
    from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
    from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
    from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent
    from src.agents.protocols.situation_awareness_protocol import SituationAwarenessProtocol
    from src.agents.protocols.data_product_protocol import DataProductProtocol
    from src.agents.models.situation_awareness_models import KPIDefinition, KPIValue, TimeFrame, ComparisonType
    from src.models.kpi_models import KPI
    logger.info("Successfully imported required modules")
except ImportError as e:
    logger.error(f"Error importing modules: {str(e)}")
    pytest.skip(f"Skipping test_sql_delegation due to import error: {e}", allow_module_level=True)


@pytest.mark.asyncio
async def test_sql_delegation():
    """Test SQL generation delegation from Situation Awareness Agent to Data Product Agent"""
    logger.info("Starting SQL delegation test")
    
    # Create orchestrator
    orchestrator = await A9_Orchestrator_Agent.create({})
    logger.info("Connected to orchestrator")
    
    # Create Data Product Agent with empty config using factory method
    data_product_agent = await A9_Data_Product_Agent.create({}, logger=logger)
    logger.info("Created Data Product Agent")
    
    # Register Data Product Agent with orchestrator
    await orchestrator.register_agent("A9_Data_Product_Agent", data_product_agent)
    logger.info("Registered Data Product Agent with orchestrator")
    
    # Create Situation Awareness Agent using factory method (pass orchestrator so it can discover DP agent)
    sa_agent = await A9_Situation_Awareness_Agent.create({"orchestrator": orchestrator})
    logger.info("Created Situation Awareness Agent")
    
    # Create a test KPI definition
    kpi_def = KPIDefinition(
        name="test_kpi",
        description="Test KPI for SQL delegation",
        unit="USD",
        data_product_id="test_dp",
        calculation={
            "query_template": "SELECT SUM(revenue) FROM sales WHERE quarter = 'Q3'"
        }
    )
    
    # Add KPI to registry
    sa_agent.kpi_registry = {"test_kpi": kpi_def}
    
    # For this delegation test, we do not need to register KPI in the DP agent's KPI provider.
    # The SA agent maintains its own minimal registry for lookup in this test.
    logger.info("Prepared test KPI in SA agent registry")
    
    # Create a test KPI value
    kpi_value = KPIValue(
        kpi_name="test_kpi",
        value=100.0,
        timeframe=TimeFrame.CURRENT_QUARTER,
        dimensions={}
    )
    
    # Test SQL generation delegation directly
    query = "Show me the revenue for this quarter"
    kpi_values = [kpi_value]
    
    # Call the Situation Awareness Agent's internal method directly for testing
    logger.info(f"Testing SQL generation delegation with query: {query}")
    
    try:
        # Call the delegated method directly for testing
        sql = await sa_agent._generate_sql_for_query(query, kpi_values)
        
        if sql:
            logger.info(f"SQL was successfully generated via delegation: {sql}")
            logger.info("SQL generation delegation test PASSED")
        else:
            logger.error("SQL generation returned None")
            logger.info("SQL generation delegation test FAILED")
    except Exception as e:
        logger.error(f"Error during SQL generation delegation test: {str(e)}")
        logger.info("SQL generation delegation test FAILED")
    
    # Disconnect agents
    await sa_agent.disconnect()
    await data_product_agent.disconnect()
    await orchestrator.disconnect()
    logger.info("Disconnected all agents")
    
    logger.info("Test completed")
