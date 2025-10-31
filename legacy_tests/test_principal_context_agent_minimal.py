#!/usr/bin/env python
"""
Minimal test script for the Principal Context Agent.
This script tests only the basic functionality to verify the agent works with the registry.
"""

import asyncio
import logging
import traceback
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("minimal_test")

async def test_principal_context_agent():
    """Test the Principal Context Agent with minimal functionality."""
    try:
        # First check if we can access the registry directly
        logger.info("Checking registry file directly")
        registry_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "src", "registry", "principal", "principal_registry.yaml")
        
        if os.path.exists(registry_path):
            logger.info(f"Registry file exists at: {registry_path}")
            import yaml
            with open(registry_path, 'r') as f:
                registry_data = yaml.safe_load(f)
                logger.info(f"Registry keys: {list(registry_data.keys())}")
                if 'principals' in registry_data:
                    logger.info(f"Found {len(registry_data['principals'])} principals in registry")
        else:
            logger.error(f"Registry file not found at: {registry_path}")
        
        logger.info("Importing A9_Principal_Context_Agent")
        from src.agents.a9_principal_context_agent import A9_Principal_Context_Agent
        
        logger.info("Creating agent instance")
        agent = A9_Principal_Context_Agent()
        
        logger.info("Connecting agent")
        await agent.connect()
        
        logger.info("Agent connected successfully")
        
        # Check if principal_profiles were loaded
        if hasattr(agent, 'principal_profiles'):
            logger.info(f"Loaded {len(agent.principal_profiles)} principal profiles")
            logger.info(f"Available roles: {list(agent.principal_profiles.keys())}")
        else:
            logger.error("No principal_profiles attribute found on agent")
        
        # Test fetch_principal_profile with a known role
        role = "cfo"
        logger.info(f"Testing fetch_principal_profile with role: {role}")
        profile = await agent.fetch_principal_profile(role)
        
        if profile:
            logger.info(f"Successfully fetched profile for {role}")
            logger.info(f"Profile name: {profile.get('name')}")
            logger.info(f"Profile business processes: {profile.get('business_processes')}")
        else:
            logger.error(f"Failed to fetch profile for {role}")
        
        logger.info("Test completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_principal_context_agent())
    sys.exit(0 if success else 1)
