#!/usr/bin/env python
"""
Debug script for the Principal Context Agent with the updated registry structure.
This script provides detailed debugging information at each step.
"""

import asyncio
import os
import sys
import uuid
import logging
import traceback
from pprint import pformat
from typing import Dict, List, Any, Optional

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Use DEBUG level for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('principal_context_agent_debug.log')  # Also log to file
    ]
)
logger = logging.getLogger("principal_context_debug")

# Import agent and models
try:
    logger.info("Importing required modules")
    from src.agents.a9_principal_context_agent import A9_Principal_Context_Agent
    from src.agents.models.principal_context_models import (
        PrincipalProfileRequest, PrincipalProfileResponse,
        SetPrincipalContextRequest, SetPrincipalContextResponse,
        ExtractFiltersRequest, ExtractFiltersResponse, ExtractedFilter
    )
    from src.agents.models.situation_awareness_models import (
        PrincipalRole, BusinessProcess, TimeFrame, PrincipalContext
    )
    from src.registry.registry_factory import RegistryFactory
    logger.info("Successfully imported all required modules")
except Exception as e:
    logger.error(f"Error importing modules: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

async def debug_registry_factory():
    """Debug the RegistryFactory."""
    logger.info("=== Debugging RegistryFactory ===")
    
    try:
        factory = RegistryFactory()
        logger.info("Created RegistryFactory instance")
        
        # Check available providers
        providers = factory.get_available_providers()
        logger.info(f"Available providers: {providers}")
        
        # Try to get the principal provider
        principal_provider = factory.get_provider("principal")
        logger.info(f"Principal provider: {principal_provider}")
        
        if principal_provider:
            # Check provider methods
            methods = [method for method in dir(principal_provider) if not method.startswith('_')]
            logger.info(f"Provider methods: {methods}")
            
            # Try to get all data
            try:
                registry_data = principal_provider.get_all()
                logger.info(f"Registry data type: {type(registry_data)}")
                
                if registry_data:
                    if isinstance(registry_data, dict):
                        logger.info(f"Registry keys: {list(registry_data.keys())}")
                    else:
                        logger.info(f"Registry data is not a dictionary, it's a {type(registry_data)}")
                else:
                    logger.warning("Registry data is None or empty")
            except Exception as e:
                logger.error(f"Error getting registry data: {str(e)}")
                traceback.print_exc()
        else:
            logger.error("Failed to get principal provider")
        
        return principal_provider
    except Exception as e:
        logger.error(f"Error in debug_registry_factory: {str(e)}")
        traceback.print_exc()
        return None

async def debug_agent_initialization():
    """Debug the agent initialization process."""
    logger.info("=== Debugging Agent Initialization ===")
    
    try:
        # Create agent
        logger.info("Creating Principal Context Agent")
        agent = A9_Principal_Context_Agent()
        logger.info(f"Agent created: {agent}")
        
        # Check agent attributes before initialization
        logger.info("Agent attributes before initialization:")
        for attr in dir(agent):
            if not attr.startswith('_') and not callable(getattr(agent, attr)):
                logger.info(f"  {attr}: {getattr(agent, attr)}")
        
        # Initialize agent
        logger.info("Connecting agent")
        await agent.connect()
        logger.info("Agent connected")
        
        # Check agent attributes after initialization
        logger.info("Agent attributes after initialization:")
        for attr in dir(agent):
            if not attr.startswith('_') and not callable(getattr(agent, attr)):
                value = getattr(agent, attr)
                if attr == 'principal_profiles':
                    logger.info(f"  {attr}: {list(value.keys()) if value else None}")
                else:
                    logger.info(f"  {attr}: {value}")
        
        return agent
    except Exception as e:
        logger.error(f"Error in debug_agent_initialization: {str(e)}")
        traceback.print_exc()
        return None

async def debug_fetch_principal_profile(agent, role):
    """Debug the fetch_principal_profile method."""
    logger.info(f"=== Debugging fetch_principal_profile for role: {role} ===")
    
    try:
        # Check if the role exists in principal_profiles
        if hasattr(agent, 'principal_profiles'):
            if role.lower() in agent.principal_profiles:
                logger.info(f"Role '{role}' found in agent.principal_profiles")
                logger.info(f"Profile data: {agent.principal_profiles[role.lower()]}")
            else:
                logger.warning(f"Role '{role}' not found in agent.principal_profiles")
                logger.info(f"Available roles: {list(agent.principal_profiles.keys())}")
        
        # Call the method
        logger.info(f"Calling fetch_principal_profile with role: {role}")
        profile = await agent.fetch_principal_profile(role)
        
        # Log the result
        logger.info(f"fetch_principal_profile result type: {type(profile)}")
        if profile:
            logger.info(f"Profile content: {pformat(profile)}")
        else:
            logger.warning("Profile is None or empty")
        
        return profile
    except Exception as e:
        logger.error(f"Error in debug_fetch_principal_profile: {str(e)}")
        traceback.print_exc()
        return None

async def debug_get_principal_context(agent, role):
    """Debug the get_principal_context method."""
    logger.info(f"=== Debugging get_principal_context for role: {role} ===")
    
    try:
        # Call the method
        logger.info(f"Calling get_principal_context with role: {role}")
        response = await agent.get_principal_context(role)
        
        # Log the result
        logger.info(f"get_principal_context result type: {type(response)}")
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
        logger.error(f"Error in debug_get_principal_context: {str(e)}")
        traceback.print_exc()
        return None

async def main():
    """Main debug function."""
    try:
        logger.info("Starting Principal Context Agent debugging")
        
        # Debug RegistryFactory
        await debug_registry_factory()
        
        # Debug agent initialization
        agent = await debug_agent_initialization()
        if not agent:
            logger.error("Failed to initialize agent, cannot continue")
            return
        
        # Debug with a known role (CFO)
        role = "cfo"
        
        # Debug fetch_principal_profile
        await debug_fetch_principal_profile(agent, role)
        
        # Debug get_principal_context
        await debug_get_principal_context(agent, role)
        
        logger.info("Debugging completed successfully")
    
    except Exception as e:
        logger.error(f"Debug failed with error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
