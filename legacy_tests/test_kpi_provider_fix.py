"""
Test script to verify KPI provider initialization and KPI definition handling.
"""

import asyncio
import logging
import sys
import traceback
from pprint import pformat

from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.models.situation_awareness_models import KPIDefinition

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def test_kpi_provider_initialization():
    """Test KPI provider initialization in Situation Awareness Agent."""
    logger.info("Testing KPI provider initialization...")
    
    agent = None
    try:
        # Create Situation Awareness Agent
        logger.info("Creating Situation Awareness Agent...")
        agent = await A9_Situation_Awareness_Agent.create()
        logger.info("Agent created successfully")
        
        # Check if KPI registry was loaded
        if hasattr(agent, '_kpi_registry') and agent._kpi_registry:
            logger.info(f"KPI registry loaded successfully with {len(agent._kpi_registry)} KPIs")
            
            # Print KPI registry keys
            logger.info(f"KPI registry keys: {list(agent._kpi_registry.keys())}")
            
            # Print first KPI to verify structure
            if agent._kpi_registry:
                try:
                    first_kpi_key = list(agent._kpi_registry.keys())[0]
                    first_kpi = agent._kpi_registry[first_kpi_key]
                    logger.info(f"First KPI ({first_kpi_key}): {pformat(first_kpi.__dict__)}")
                    
                    # Check if kpi_id field exists
                    if hasattr(first_kpi, 'kpi_id'):
                        logger.info(f"KPI ID field exists: {first_kpi.kpi_id}")
                    else:
                        logger.warning("KPI ID field does not exist on KPI definition")
                        
                    # Check other fields
                    logger.info(f"KPI name: {first_kpi.name}")
                    logger.info(f"KPI description: {first_kpi.description}")
                    logger.info(f"KPI data_product_id: {first_kpi.data_product_id}")
                    
                    # Test creating a new KPIDefinition with kpi_id
                    test_kpi = KPIDefinition(
                        name="Test KPI",
                        description="Test KPI Description",
                        data_product_id="test_dp_001",
                        kpi_id="test_kpi_001"
                    )
                    logger.info(f"Created test KPI with kpi_id: {test_kpi.kpi_id}")
                except Exception as e:
                    logger.error(f"Error examining first KPI: {str(e)}")
                    traceback.print_exc()
        else:
            logger.warning("KPI registry not loaded or empty")
            if hasattr(agent, '_kpi_registry'):
                logger.info(f"KPI registry exists but is empty: {agent._kpi_registry}")
            else:
                logger.info("KPI registry attribute does not exist on agent")
        
        # Test the _load_kpi_registry method directly
        logger.info("Testing _load_kpi_registry method directly...")
        try:
            await agent._load_kpi_registry()
            logger.info("_load_kpi_registry method completed successfully")
        except Exception as e:
            logger.error(f"Error in _load_kpi_registry: {str(e)}")
            traceback.print_exc()
    
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        traceback.print_exc()
    finally:
        # Clean up
        if agent:
            try:
                await agent.disconnect()
                logger.info("Agent disconnected successfully")
            except Exception as e:
                logger.error(f"Error disconnecting agent: {str(e)}")
    
    return True

if __name__ == "__main__":
    logger.info("Starting KPI provider fix test")
    asyncio.run(test_kpi_provider_initialization())
    logger.info("Test completed")
