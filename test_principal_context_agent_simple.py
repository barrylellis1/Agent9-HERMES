#!/usr/bin/env python
"""
Simple test script for the Principal Context Agent with the updated registry structure.
This script tests the agent's ability to load principal profiles from the registry,
fetch profiles by role, and get principal context.
"""

import asyncio
import os
import sys
import uuid
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("principal_context_agent_test")

# Import agent and models
from src.agents.a9_principal_context_agent import A9_Principal_Context_Agent
from src.agents.models.principal_context_models import (
    PrincipalProfileRequest, PrincipalProfileResponse, 
    ExtractFiltersRequest, ExtractFiltersResponse,
    SetPrincipalContextRequest, SetPrincipalContextResponse
)
from src.agents.models.situation_awareness_models import (
    PrincipalContext, TimeFrame, BusinessProcess
)

async def test_agent():
    """Test the Principal Context Agent with the updated registry structure."""
    try:
        logger.info("Creating and initializing Principal Context Agent")
        agent = A9_Principal_Context_Agent()
        await agent.connect()
        
        # Check if profiles were loaded
        if not hasattr(agent, 'principal_profiles') or not agent.principal_profiles:
            logger.error("Agent did not load principal profiles")
            return
        
        logger.info(f"Loaded {len(agent.principal_profiles)} principal profiles")
        logger.info(f"Available roles: {list(agent.principal_profiles.keys())}")
        
        # Test with a known role (CFO)
        role = "cfo"
        logger.info(f"\nTesting with role: {role}")
        
        # Test fetch_principal_profile
        logger.info("Testing fetch_principal_profile")
        profile = await agent.fetch_principal_profile(role)
        if profile:
            logger.info(f"Successfully fetched profile for {role}:")
            logger.info(f"  Name: {profile.get('name')}")
            logger.info(f"  Business Processes: {profile.get('business_processes')}")
            logger.info(f"  Default Filters: {profile.get('default_filters')}")
        else:
            logger.error(f"Failed to fetch profile for {role}")
        
        # Test get_principal_context
        logger.info("\nTesting get_principal_context")
        response = await agent.get_principal_context(role)
        logger.info(f"Response status: {response.status}")
        logger.info(f"Response message: {response.message}")
        
        if response.status == "success":
            context = response.context
            logger.info(f"Principal Context:")
            logger.info(f"  Role: {context.role}")
            logger.info(f"  Business Processes: {[str(bp) for bp in context.business_processes]}")
            logger.info(f"  Default Filters: {context.default_filters}")
            logger.info(f"  Decision Style: {context.decision_style}")
            logger.info(f"  Communication Style: {context.communication_style}")
            logger.info(f"  Preferred Timeframes: {[str(tf) for tf in context.preferred_timeframes]}")
        
        logger.info("\nTest completed successfully")
    
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_agent())
