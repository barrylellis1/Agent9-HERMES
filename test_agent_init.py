"""
Test script for agent initialization and connection
This script isolates the agent initialization process to diagnose issues.
"""

import asyncio
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add src directory to path if needed
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.registry.factory import RegistryFactory
from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent
from src.agents.new.a9_principal_context_agent import A9_Principal_Context_Agent
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.new.a9_data_governance_agent import A9_Data_Governance_Agent
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent

async def test_agent_initialization():
    """Test agent initialization and connection in isolation."""
    logger = logging.getLogger("test_agent_init")
    logger.info("Starting agent initialization test")
    
    try:
        # Create registry factory and initialize it first
        logger.info("Creating and initializing registry factory")
        registry_factory = RegistryFactory()
        await registry_factory.initialize()
        
        # Create and connect the orchestrator
        logger.info("Creating orchestrator agent")
        orchestrator_config = {}
        orchestrator = await A9_Orchestrator_Agent.create(orchestrator_config)
        logger.info("Connecting orchestrator agent")
        await orchestrator.connect()
        
        # Create Principal Context Agent
        logger.info("Creating Principal Context Agent")
        pc_agent_config = {
            "orchestrator": orchestrator,
            "registry_factory": registry_factory
        }
        pc_agent = await A9_Principal_Context_Agent.create(pc_agent_config)
        logger.info("Registering Principal Context Agent with orchestrator")
        await orchestrator.register_agent("A9_Principal_Context_Agent", pc_agent)
        
        # Create Data Governance Agent
        logger.info("Creating Data Governance Agent")
        dg_agent_config = {
            "orchestrator": orchestrator,
            "registry_factory": registry_factory
        }
        dg_agent = await A9_Data_Governance_Agent.create(dg_agent_config)
        logger.info("Registering Data Governance Agent with orchestrator")
        await orchestrator.register_agent("A9_Data_Governance_Agent", dg_agent)
        
        # Create Data Product Agent
        logger.info("Creating Data Product Agent")
        dp_agent_config = {
            "contract_path": "src/contracts/fi_star_schema.yaml",
            "db_type": "duckdb",
            "db_path": "data/agent9-hermes.duckdb",
            "registry_path": "src/registry/data_product",
            "orchestrator": orchestrator,
            "registry_factory": registry_factory
        }
        dp_agent = await A9_Data_Product_Agent.create(dp_agent_config)
        logger.info("Registering Data Product Agent with orchestrator")
        await orchestrator.register_agent("A9_Data_Product_Agent", dp_agent)
        
        # Create Situation Awareness Agent
        logger.info("Creating Situation Awareness Agent")
        sa_agent_config = {
            "contract_path": "src/contracts/fi_star_schema.yaml",
            "target_domains": ["Finance"],
            "orchestrator": orchestrator,
            "registry_factory": registry_factory
        }
        sa_agent = await A9_Situation_Awareness_Agent.create(sa_agent_config)
        logger.info("Registering Situation Awareness Agent with orchestrator")
        await orchestrator.register_agent("A9_Situation_Awareness_Agent", sa_agent)
        
        # Connect all agents with explicit orchestrator parameter
        logger.info("Connecting Principal Context Agent")
        try:
            await pc_agent.connect(orchestrator)
        except TypeError as e:
            logger.error(f"Error connecting Principal Context Agent: {str(e)}")
            logger.info("Trying without orchestrator parameter")
            await pc_agent.connect()
        
        logger.info("Connecting Data Governance Agent")
        try:
            await dg_agent.connect(orchestrator)
        except TypeError as e:
            logger.error(f"Error connecting Data Governance Agent: {str(e)}")
            logger.info("Trying without orchestrator parameter")
            await dg_agent.connect()
        
        logger.info("Connecting Data Product Agent")
        try:
            await dp_agent.connect(orchestrator)
        except TypeError as e:
            logger.error(f"Error connecting Data Product Agent: {str(e)}")
            logger.info("Trying without orchestrator parameter")
            await dp_agent.connect()
        
        logger.info("Connecting Situation Awareness Agent")
        try:
            await sa_agent.connect(orchestrator)
        except TypeError as e:
            logger.error(f"Error connecting Situation Awareness Agent: {str(e)}")
            logger.info("Trying without orchestrator parameter")
            await sa_agent.connect()
        
        # Test getting agents from orchestrator
        logger.info("\nTesting agent retrieval from orchestrator:")
        pc_agent_from_orchestrator = await orchestrator.get_agent("A9_Principal_Context_Agent")
        logger.info(f"Retrieved Principal Context Agent: {pc_agent_from_orchestrator is not None}")
        
        dg_agent_from_orchestrator = await orchestrator.get_agent("A9_Data_Governance_Agent")
        logger.info(f"Retrieved Data Governance Agent: {dg_agent_from_orchestrator is not None}")
        
        dp_agent_from_orchestrator = await orchestrator.get_agent("A9_Data_Product_Agent")
        logger.info(f"Retrieved Data Product Agent: {dp_agent_from_orchestrator is not None}")
        
        sa_agent_from_orchestrator = await orchestrator.get_agent("A9_Situation_Awareness_Agent")
        logger.info(f"Retrieved Situation Awareness Agent: {sa_agent_from_orchestrator is not None}")
        
    except Exception as e:
        logger.error(f"Error during agent initialization: {str(e)}", exc_info=True)
    
    logger.info("Agent initialization test complete")

if __name__ == "__main__":
    asyncio.run(test_agent_initialization())
