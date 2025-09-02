"""
Test script for the Situation Awareness Agent.
This script tests the basic initialization and connection of the agent.
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
from src.agents.models.situation_awareness_models import PrincipalRole, PrincipalContext

async def test_agent_initialization():
    """Test basic agent initialization and connection."""
    try:
        # Create the agent
        print("Creating Situation Awareness Agent...")
        agent = await A9_Situation_Awareness_Agent.create({})
        
        print("Agent created successfully!")
        
        # Test getting principal context
        print("Testing get_principal_context...")
        context = await agent.get_principal_context(PrincipalRole.CFO)
        print(f"Got principal context for {context.role}: {context.business_processes}")
        
        # Test getting diagnostic questions
        print("Testing get_diagnostic_questions...")
        questions = await agent.get_diagnostic_questions(context)
        print(f"Got {len(questions)} diagnostic questions")
        
        # Test getting recommended questions
        print("Testing get_recommended_questions...")
        recommended = await agent.get_recommended_questions(context)
        print(f"Got {len(recommended)} recommended questions")
        
        # Disconnect the agent
        await agent.disconnect()
        print("Agent disconnected successfully!")
        
        return True
    except Exception as e:
        print(f"Error testing agent: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Situation Awareness Agent test...")
    result = asyncio.run(test_agent_initialization())
    print(f"Test {'passed' if result else 'failed'}")
