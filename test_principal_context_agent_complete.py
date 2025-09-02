#!/usr/bin/env python
"""
Comprehensive test script for the Principal Context Agent.
This script tests all major functionality of the agent with the updated registry structure.
"""

import asyncio
import logging
import os
import sys
import uuid
import yaml
import traceback
from pprint import pformat
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('principal_context_agent_test.log')
    ]
)
logger = logging.getLogger("principal_context_test")

# Test registry structure directly
def test_registry_structure():
    """Test the registry structure directly."""
    logger.info("=== Testing Registry Structure ===")
    
    try:
        # Path to the registry file
        registry_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                    "src", "registry", "principal", "principal_registry.yaml")
        
        logger.info(f"Registry path: {registry_path}")
        
        if not os.path.exists(registry_path):
            logger.error(f"Registry file not found at: {registry_path}")
            return None
        
        with open(registry_path, 'r') as f:
            registry_data = yaml.safe_load(f)
        
        logger.info(f"Registry top-level keys: {list(registry_data.keys())}")
        
        # Check for principals
        if "principals" in registry_data:
            principals = registry_data["principals"]
            logger.info(f"Found {len(principals)} principals in registry")
            
            # Print details of the first principal
            principal = principals[0]
            logger.info(f"First principal:")
            logger.info(f"  ID: {principal.get('id')}")
            logger.info(f"  Name: {principal.get('name')}")
            logger.info(f"  Role: {principal.get('role')}")
            logger.info(f"  Keys: {list(principal.keys())}")
            
            return registry_data
        else:
            logger.warning("No 'principals' key found in registry data")
            return None
    
    except Exception as e:
        logger.error(f"Error testing registry structure: {str(e)}")
        traceback.print_exc()
        return None

async def test_agent_initialization():
    """Test the agent initialization."""
    logger.info("=== Testing Agent Initialization ===")
    
    try:
        # Import the agent
        from src.agents.a9_principal_context_agent import A9_Principal_Context_Agent
        
        # Create and initialize the agent
        logger.info("Creating agent instance")
        agent = A9_Principal_Context_Agent()
        
        logger.info("Connecting agent")
        await agent.connect()
        
        logger.info("Agent connected successfully")
        
        # Check if principal_profiles were loaded
        if hasattr(agent, 'principal_profiles'):
            logger.info(f"Loaded {len(agent.principal_profiles)} principal profiles")
            logger.info(f"Available roles: {list(agent.principal_profiles.keys())}")
            
            # Print the first profile
            if agent.principal_profiles:
                first_role = list(agent.principal_profiles.keys())[0]
                logger.info(f"First profile ({first_role}):")
                logger.info(pformat(agent.principal_profiles[first_role]))
        else:
            logger.error("No principal_profiles attribute found on agent")
        
        return agent
    
    except Exception as e:
        logger.error(f"Error testing agent initialization: {str(e)}")
        traceback.print_exc()
        return None

async def test_fetch_principal_profile(agent, role="cfo"):
    """Test the fetch_principal_profile method."""
    logger.info(f"=== Testing fetch_principal_profile for role: {role} ===")
    
    try:
        if not agent:
            logger.error("Agent is None, cannot test fetch_principal_profile")
            return None
        
        # Call the method
        logger.info(f"Calling fetch_principal_profile with role: {role}")
        profile = await agent.fetch_principal_profile(role)
        
        # Log the result
        if profile:
            logger.info(f"Successfully fetched profile for {role}")
            logger.info(f"Profile content:")
            logger.info(pformat(profile))
        else:
            logger.error(f"Failed to fetch profile for {role}")
        
        return profile
    
    except Exception as e:
        logger.error(f"Error testing fetch_principal_profile: {str(e)}")
        traceback.print_exc()
        return None

async def test_get_principal_context(agent, role="cfo"):
    """Test the get_principal_context method."""
    logger.info(f"=== Testing get_principal_context for role: {role} ===")
    
    try:
        if not agent:
            logger.error("Agent is None, cannot test get_principal_context")
            return None
        
        # Call the method
        logger.info(f"Calling get_principal_context with role: {role}")
        response = await agent.get_principal_context(role)
        
        # Log the result
        logger.info(f"Response status: {response.status}")
        logger.info(f"Response message: {response.message}")
        
        if hasattr(response, 'context'):
            context = response.context
            logger.info(f"Context role: {context.role}")
            logger.info(f"Context business processes: {[str(bp) for bp in context.business_processes]}")
            logger.info(f"Context default filters: {context.default_filters}")
            logger.info(f"Context decision style: {context.decision_style}")
            logger.info(f"Context communication style: {context.communication_style}")
            logger.info(f"Context preferred timeframes: {[str(tf) for tf in context.preferred_timeframes]}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error testing get_principal_context: {str(e)}")
        traceback.print_exc()
        return None

async def test_extract_filters(agent):
    """Test the extract_filters method."""
    logger.info("=== Testing extract_filters ===")
    
    try:
        if not agent:
            logger.error("Agent is None, cannot test extract_filters")
            return None
        
        # Test job description
        job_description = """
        As a CFO, I need to analyze the monthly financial performance of our European operations,
        focusing on the Sales and Marketing departments. I need to compare current quarter results
        with the previous quarter and year-to-date performance.
        """
        
        # Call the method
        logger.info(f"Calling extract_filters with job description")
        response = await agent.extract_filters(job_description)
        
        # Log the result
        logger.info(f"Response status: {response.status}")
        logger.info(f"Response message: {response.message}")
        logger.info(f"Extracted filters: {response.filters}")
        
        if hasattr(response, 'extracted_filters'):
            for filter_item in response.extracted_filters:
                logger.info(f"  {filter_item.dimension}: {filter_item.value} (confidence: {filter_item.confidence})")
        
        return response
    
    except Exception as e:
        logger.error(f"Error testing extract_filters: {str(e)}")
        traceback.print_exc()
        return None

async def main():
    """Main test function."""
    try:
        logger.info("Starting Principal Context Agent tests")
        
        # Test registry structure
        registry_data = test_registry_structure()
        
        # Test agent initialization
        agent = await test_agent_initialization()
        if not agent:
            logger.error("Failed to initialize agent, cannot continue with agent tests")
            return
        
        # Test with known roles
        roles = ["cfo", "ceo", "coo"]
        for role in roles:
            # Test fetch_principal_profile
            await test_fetch_principal_profile(agent, role)
            
            # Test get_principal_context
            await test_get_principal_context(agent, role)
        
        # Test extract_filters
        await test_extract_filters(agent)
        
        logger.info("All tests completed successfully")
    
    except Exception as e:
        logger.error(f"Tests failed with error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
