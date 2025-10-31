"""
Test script to verify principal context lookup by ID and role.
"""

import asyncio
import logging
from src.agents.new.a9_principal_context_agent import A9_Principal_Context_Agent
from src.agents.models.situation_awareness_models import PrincipalRole

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_principal_context_lookup():
    """Test principal context lookup by ID and role."""
    # Create Principal Context Agent
    agent = A9_Principal_Context_Agent()
    await agent.connect()
    
    # Test lookup by role enum
    logger.info("Testing lookup by role enum (CFO)...")
    context_by_role_enum = await agent.get_principal_context(PrincipalRole.CFO)
    logger.info(f"Context by role enum: {context_by_role_enum}")
    
    # Test lookup by role string
    logger.info("Testing lookup by role string ('CFO')...")
    context_by_role_str = await agent.get_principal_context("CFO")
    logger.info(f"Context by role string: {context_by_role_str}")
    
    # Test lookup by ID
    logger.info("Testing lookup by ID ('cfo_001')...")
    context_by_id = await agent.get_principal_context_by_id("cfo_001")
    logger.info(f"Context by ID: {context_by_id}")
    
    # Test lookup by non-existent ID
    logger.info("Testing lookup by non-existent ID ('nonexistent_id')...")
    context_by_nonexistent_id = await agent.get_principal_context_by_id("nonexistent_id")
    logger.info(f"Context by non-existent ID: {context_by_nonexistent_id}")
    
    # Disconnect agent
    await agent.disconnect()

if __name__ == "__main__":
    asyncio.run(test_principal_context_lookup())
