"""
Test script for the fixed Situation Awareness Agent.
This script tests the initialization and connection of the agent with the fixes applied.
"""

import asyncio
import logging
import sys
import os
import pytest

pytestmark = pytest.mark.asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the agent
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.new.a9_orchestrator_agent import initialize_agent_registry

async def test_situation_awareness_agent():
    """Test the initialization and connection of the Situation Awareness Agent."""
    try:
        # Initialize the agent registry
        await initialize_agent_registry()
        
        # Create the agent
        logging.info("Creating Situation Awareness Agent...")
        agent = await A9_Situation_Awareness_Agent.create({})
        
        # Check if the agent was created successfully
        if agent:
            logging.info("Situation Awareness Agent created successfully")
            
            # Check if the agent has the required attributes
            logging.info("Checking agent attributes...")
            attributes = [
                "principal_profiles",
                "data_product_agent",
                "data_governance_agent",
                "principal_context_agent",
                "kpi_registry"
            ]
            
            for attr in attributes:
                if hasattr(agent, attr):
                    value = getattr(agent, attr)
                    if value is None:
                        logging.warning(f"Agent attribute '{attr}' is None")
                    elif isinstance(value, dict) and not value:
                        logging.warning(f"Agent attribute '{attr}' is an empty dictionary")
                    else:
                        logging.info(f"Agent attribute '{attr}' is present and initialized")
                else:
                    logging.error(f"Agent attribute '{attr}' is missing")
            
            # Test disconnection
            await agent.disconnect()
            logging.info("Agent disconnected successfully")
            
            return True
        else:
            logging.error("Failed to create Situation Awareness Agent")
            return False
    except Exception as e:
        logging.error(f"Error testing Situation Awareness Agent: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting Situation Awareness Agent test...")
    asyncio.run(test_situation_awareness_agent())
    logging.info("Test completed")
