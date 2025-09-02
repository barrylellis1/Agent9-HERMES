"""
Simple test script for the Situation Awareness Agent.
"""

import asyncio
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Import the agent
from src.agents.a9_situation_awareness_agent import A9_Situation_Awareness_Agent

async def test_agent_initialization():
    """Test basic agent initialization."""
    try:
        print("Creating Situation Awareness Agent...")
        agent = A9_Situation_Awareness_Agent({})
        print("Agent instance created successfully!")
        
        print("Connecting agent...")
        await agent.connect()
        print("Agent connected successfully!")
        
        return True
    except Exception as e:
        print(f"Error testing agent: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Situation Awareness Agent simple test...")
    result = asyncio.run(test_agent_initialization())
    print(f"Test {'passed' if result else 'failed'}")
