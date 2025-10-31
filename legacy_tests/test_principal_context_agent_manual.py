#!/usr/bin/env python
"""
Manual test script for the Principal Context Agent with the updated registry structure.
This script tests the agent's ability to load principal profiles from the registry,
fetch profiles by role, and get principal context.
"""

import asyncio
import os
import sys
import uuid
import logging
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('principal_context_agent_test.log')
    ]
)
logger = logging.getLogger("principal_context_agent_test")

# Also log to console directly for visibility
def log_info(msg):
    print(f"INFO: {msg}")
    logger.info(msg)
    
def log_error(msg, exc_info=False):
    print(f"ERROR: {msg}")
    logger.error(msg, exc_info=exc_info)

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
from src.registry.factory import RegistryFactory

async def test_load_principal_profiles():
    """Test loading principal profiles from the registry."""
    log_info("=== Testing loading principal profiles ===")
    
    try:
        # Create agent
        log_info("Creating Principal Context Agent")
        agent = A9_Principal_Context_Agent()
        
        # Initialize agent
        log_info("Connecting agent")
        await agent.connect()
        
        # Check if profiles were loaded
        if not hasattr(agent, 'principal_profiles'):
            log_error("Agent does not have principal_profiles attribute")
            # Check if _load_principal_profiles method exists
            if hasattr(agent, '_load_principal_profiles'):
                log_info("Agent has _load_principal_profiles method, trying to call it directly")
                try:
                    await agent._load_principal_profiles()
                    log_info("Called _load_principal_profiles directly")
                except Exception as e:
                    log_error(f"Error calling _load_principal_profiles directly: {str(e)}", exc_info=True)
            return None
            
        # Check principal_profiles
        profile_count = len(agent.principal_profiles)
        log_info(f"Loaded {profile_count} principal profiles in principal_profiles dictionary")
        
        # Check principal_profiles_by_id
        if hasattr(agent, 'principal_profiles_by_id'):
            by_id_count = len(agent.principal_profiles_by_id)
            log_info(f"Loaded {by_id_count} principal profiles in principal_profiles_by_id dictionary")
            if by_id_count > 0:
                log_info(f"Keys in principal_profiles_by_id: {list(agent.principal_profiles_by_id.keys())}")
        else:
            log_info("Agent does not have principal_profiles_by_id attribute")
        
        # Print the roles that were loaded
        roles = list(agent.principal_profiles.keys())
        log_info(f"Available roles in principal_profiles: {roles}")
        
        # Print a sample profile
        if roles:
            sample_role = roles[0]
            sample_profile = agent.principal_profiles[sample_role]
            log_info(f"Sample profile for {sample_role}:")
            if isinstance(sample_profile, dict):
                for key, value in sample_profile.items():
                    log_info(f"  {key}: {value}")
            else:
                log_info(f"  Profile type: {type(sample_profile)}")
                if hasattr(sample_profile, 'model_dump'):
                    log_info(f"  Profile data: {sample_profile.model_dump()}")
                elif hasattr(sample_profile, 'dict'):
                    log_info(f"  Profile data: {sample_profile.dict()}")
                else:
                    log_info(f"  Profile attributes: {dir(sample_profile)}")
        
        # Check if _load_principal_profiles method exists and inspect its code
        if hasattr(agent, '_load_principal_profiles'):
            import inspect
            log_info("Inspecting _load_principal_profiles method")
            try:
                method_code = inspect.getsource(agent._load_principal_profiles)
                log_info(f"_load_principal_profiles method code:\n{method_code}")
            except Exception as e:
                log_error(f"Could not get source code for _load_principal_profiles: {str(e)}")
        
        return agent
    except Exception as e:
        log_error(f"Error loading principal profiles: {str(e)}", exc_info=True)
        return None

async def test_fetch_principal_profile(agent: A9_Principal_Context_Agent, role: str):
    """Test fetching a principal profile by role."""
    log_info(f"=== Testing fetch_principal_profile for role: {role} ===")
    
    try:
        # Try to access the profile directly from principal_profiles_by_id first
        if hasattr(agent, 'principal_profiles_by_id'):
            log_info(f"Checking if '{role}' exists in principal_profiles_by_id")
            if role in agent.principal_profiles_by_id:
                log_info(f"Found '{role}' directly in principal_profiles_by_id")
                direct_profile = agent.principal_profiles_by_id[role]
                log_info(f"Direct profile type: {type(direct_profile)}")
                if hasattr(direct_profile, 'model_dump'):
                    log_info(f"Direct profile data: {direct_profile.model_dump()}")
        
        # Now try the fetch_principal_profile method
        log_info(f"Calling fetch_principal_profile for '{role}'")
        profile = await agent.fetch_principal_profile(role)
        
        if profile:
            log_info(f"Successfully fetched profile for {role}:")
            log_info(f"  Profile type: {type(profile)}")
            
            # Handle different return types
            if isinstance(profile, dict):
                log_info(f"  Name: {profile.get('name')}")
                log_info(f"  Title: {profile.get('title')}")
                log_info(f"  Business Processes: {profile.get('business_processes')}")
                log_info(f"  Default Filters: {profile.get('default_filters')}")
                log_info(f"  Decision Style: {profile.get('decision_style')}")
                log_info(f"  Communication Style: {profile.get('communication_style')}")
                log_info(f"  Timeframes: {profile.get('timeframes')}")
            else:
                # For Pydantic models or other objects
                log_info(f"  Profile attributes: {dir(profile)}")
                if hasattr(profile, 'model_dump'):
                    profile_data = profile.model_dump()
                    log_info(f"  Profile data: {profile_data}")
                    for key, value in profile_data.items():
                        log_info(f"  {key}: {value}")
                elif hasattr(profile, 'dict'):
                    profile_data = profile.dict()
                    log_info(f"  Profile data: {profile_data}")
                    for key, value in profile_data.items():
                        log_info(f"  {key}: {value}")
        else:
            log_error(f"Failed to fetch profile for {role}")
            
            # Debug the fetch_principal_profile method
            if hasattr(agent, 'fetch_principal_profile'):
                import inspect
                log_info("Inspecting fetch_principal_profile method")
                try:
                    method_code = inspect.getsource(agent.fetch_principal_profile)
                    log_info(f"fetch_principal_profile method code:\n{method_code}")
                except Exception as e:
                    log_error(f"Could not get source code for fetch_principal_profile: {str(e)}")
        
        return profile
    except Exception as e:
        log_error(f"Error in test_fetch_principal_profile: {str(e)}", exc_info=True)
        return None

async def test_get_principal_context(agent: A9_Principal_Context_Agent, role: str):
    log_info(f"=== Testing get_principal_context for role: {role} ===")
    log_info(f"Calling get_principal_context with role: {role}")
    try:
        context = await agent.get_principal_context(role)
        log_info(f"Successfully got context for {role}:")
        log_info(f"Context: {context}")
        return context
    except Exception as e:
        log_error(f"Error testing get_principal_context: {str(e)}")
        return None

async def test_case_insensitive_lookup(agent: A9_Principal_Context_Agent):
    log_info("=== Testing case-insensitive profile lookup ===")
    
    # Test different formats of the same role
    role_formats = [
        "CFO",           # Original enum value
        "cfo",           # lowercase
        "Cfo",           # Title case
        "FINANCE_MANAGER", # UPPERCASE_WITH_UNDERSCORES
        "Finance Manager", # Original enum value
        "finance manager", # lowercase with space
    ]
    
    for role_format in role_formats:
        log_info(f"Testing lookup with role format: '{role_format}'")
        try:
            context = await agent.get_principal_context(role_format)
            if context:
                log_info(f"✓ Successfully found profile for '{role_format}'")
                log_info(f"  Mapped to role: {context.get('role', 'unknown')}")
                log_info(f"  Principal ID: {context.get('principal_id', 'unknown')}")
            else:
                log_error(f"✗ Failed to find profile for '{role_format}'")
        except Exception as e:
            log_error(f"✗ Error looking up '{role_format}': {str(e)}")
    
    # Test non-existent role
    try:
        log_info("Testing lookup with non-existent role: 'INVALID_ROLE'")
        context = await agent.get_principal_context("INVALID_ROLE")
        if context:
            log_info(f"Got fallback context for non-existent role: {context.get('role', 'unknown')}")
        else:
            log_error("Failed to get fallback context for non-existent role")
    except Exception as e:
        log_error(f"Error testing non-existent role: {str(e)}")

async def test_extract_filters(agent: A9_Principal_Context_Agent):
    """Test extracting filters from a job description."""
    logger.info("=== Testing extract_filters ===")
    
    job_description = """
    Analyze the Q2 financial performance for the North America region, 
    focusing on the Retail division's revenue growth compared to last year.
    """
    
    request = ExtractFiltersRequest(
        job_description=job_description,
        description=job_description,  # Keep for backward compatibility
        request_id=str(uuid.uuid4())
    )
    
    response = await agent.extract_filters(request)
    
    logger.info(f"Response status: {response.status}")
    logger.info(f"Response message: {response.message}")
    
    if response.status == "success":
        logger.info(f"Extracted filters: {response.filters}")
        logger.info(f"Extracted filter objects: {[f.model_dump() for f in response.extracted_filters]}")
    
    return response

async def test_set_principal_context(agent: A9_Principal_Context_Agent, role: str):
    """Test setting principal context."""
    logger.info(f"=== Testing set_principal_context for role: {role} ===")
    
    request = SetPrincipalContextRequest(
        principal_id=role,
        context_data={
            "filters": {"region": "North America", "division": "Retail"},
            "timeframe": "QUARTERLY"
        },
        request_id=str(uuid.uuid4())
    )
    
    response = await agent.set_principal_context(request)
    
    logger.info(f"Response status: {response.status}")
    logger.info(f"Response message: {response.message}")
    
    if response.status == "success":
        logger.info(f"Updated profile: {response.profile}")
        logger.info(f"Updated filters: {response.filters}")
    
    return response

async def test_registry_structure():
    """Test the registry structure directly."""
    log_info("=== Testing registry structure ===")
    
    try:
        # Initialize registry bootstrap first
        from src.registry.bootstrap import RegistryBootstrap
        base_path = os.path.abspath(os.path.dirname(__file__))
        config = {
            "base_path": base_path,
            "registry_path": os.path.join(base_path, "src", "registry")
        }
        log_info("Initializing registry bootstrap")
        success = await RegistryBootstrap.initialize(config)
        if not success:
            log_error("Failed to initialize registry bootstrap")
            return None
        log_info("Registry bootstrap initialized successfully")
        
        # Now get the factory from the bootstrap class
        factory = RegistryBootstrap._factory
        if not factory:
            log_error("Failed to get registry factory from bootstrap")
            return None
        log_info("Got RegistryFactory from bootstrap")
        
        # Check what providers are available
        provider_status = factory.provider_status()
        log_info(f"Provider status: {provider_status}")
        
        # Check if principal_profile provider is registered
        if 'principal_profile' not in provider_status:
            log_error("principal_profile provider not found in registry factory")
            log_info("Available providers: " + ", ".join(provider_status.keys()))
        else:
            log_info(f"principal_profile provider status: {provider_status.get('principal_profile')}")
        
        principal_provider = factory.get_provider("principal_profile")
        log_info(f"Got principal provider: {principal_provider}")
        
        if not principal_provider:
            log_error("Failed to get principal provider")
            return None
        
        # Check provider methods
        log_info(f"Provider methods: {dir(principal_provider)}")
        
        # Check the registry file directly
        registry_path = os.path.join(base_path, "src", "registry", "principal", "principal_registry.yaml")
        if os.path.exists(registry_path):
            log_info(f"Principal registry file exists at: {registry_path}")
            with open(registry_path, 'r') as f:
                file_content = f.read()
                log_info(f"Registry file content length: {len(file_content)} bytes")
                log_info(f"Registry file first 100 chars: {file_content[:100]}...")
        else:
            log_error(f"Principal registry file not found at: {registry_path}")
        
        registry_data = principal_provider.get_all()
        log_info(f"Got registry data type: {type(registry_data)}")
        
        if not registry_data:
            log_error("Failed to get registry data")
            return None
        
        # Handle list return value from get_all()
        if isinstance(registry_data, list):
            principals = registry_data
            log_info(f"Found {len(principals)} principals in registry")
            
            # Print all principal details for debugging
            for i, principal in enumerate(principals):
                log_info(f"Principal {i+1} details:")
                log_info(f"  ID: {principal.id if hasattr(principal, 'id') else 'N/A'}")
                log_info(f"  Name: {principal.name if hasattr(principal, 'name') else 'N/A'}")
                log_info(f"  Role: {principal.role if hasattr(principal, 'role') else 'N/A'}")
                log_info(f"  Title: {principal.title if hasattr(principal, 'title') else 'N/A'}")
                log_info(f"  Business Processes: {principal.business_processes if hasattr(principal, 'business_processes') else []}")
                
                # Print all attributes for debugging
                log_info(f"  All attributes: {dir(principal)}")
                
                # Try to convert to dict if possible
                if hasattr(principal, 'dict'):
                    log_info(f"  Dict representation: {principal.dict()}")
                elif hasattr(principal, 'model_dump'):
                    log_info(f"  Dict representation: {principal.model_dump()}")
                else:
                    log_info(f"  No dict or model_dump method available")
                    
                # Print raw __dict__ if available
                if hasattr(principal, '__dict__'):
                    log_info(f"  __dict__ representation: {principal.__dict__}")
                else:
                    log_info(f"  No __dict__ attribute available")
        else:
            log_error(f"Unexpected registry data type: {type(registry_data)}")
            log_info(f"Registry data structure: {registry_data}")
        
        return registry_data
    except Exception as e:
        log_error(f"Error testing registry structure: {str(e)}", exc_info=True)
        return None

async def main():
    # Logging is already configured at the top of the file
    log_info("Starting Principal Context Agent tests")
    
    try:
        # Test registry structure
        log_info("Step 1: Testing registry structure")
        await test_registry_structure()
        
        # Test agent initialization and profile loading
        log_info("\nStep 2: Testing Agent Initialization")
        agent = await test_load_principal_profiles()
        if not agent:
            log_error("Failed to initialize agent")
            return
            
        if not hasattr(agent, 'principal_profiles') or not agent.principal_profiles:
            log_error("Agent's principal_profiles dictionary is empty")
            # Check principal_profiles_by_id as well
            if hasattr(agent, 'principal_profiles_by_id'):
                log_info(f"principal_profiles_by_id has {len(agent.principal_profiles_by_id)} entries")
                if agent.principal_profiles_by_id:
                    log_info(f"Keys in principal_profiles_by_id: {list(agent.principal_profiles_by_id.keys())}")
            return
        
        # Get available roles from agent
        available_roles = list(agent.principal_profiles.keys())
        log_info(f"Available roles from agent: {available_roles}")
        
        # Test with roles that exist in the agent's profiles
        test_roles = available_roles[:3] if len(available_roles) >= 3 else available_roles
        if not test_roles:
            # Try to get roles from principal_profiles_by_id if available
            if hasattr(agent, 'principal_profiles_by_id') and agent.principal_profiles_by_id:
                # Try to use the role attribute from profiles in principal_profiles_by_id
                test_roles = []
                for profile_id, profile in agent.principal_profiles_by_id.items():
                    if hasattr(profile, 'role') and profile.role:
                        test_roles.append(profile.role)
                    else:
                        # If no role attribute, use the ID as fallback
                        test_roles.append(profile_id)
                test_roles = test_roles[:3] if test_roles else ["cfo", "ceo", "coo"]
            else:
                test_roles = ["cfo", "ceo", "coo"]  # Fallback to default roles
        
        log_info(f"Testing with roles: {test_roles}")
        
        for role in test_roles:
            log_info(f"\nTesting with role: {role}")
            
            # Test fetching principal profile
            log_info("Step 3: Testing fetch_principal_profile")
            profile = await test_fetch_principal_profile(agent, role)
            if not profile:
                log_info(f"Could not fetch profile for {role}, continuing with next tests")
            
            # Test getting principal context
            log_info("Step 4: Testing get_principal_context")
            context = await test_get_principal_context(agent, role)
            if not context:
                log_info(f"Could not get context for {role}, continuing with next tests")
        
        # Test case-insensitive profile lookup
        log_info("\nStep 5: Testing case-insensitive profile lookup")
        await test_case_insensitive_lookup(agent)
        
        # Test extracting filters
        log_info("\nStep 6: Testing extract_filters")
        filter_response = await test_extract_filters(agent)
        
        log_info("All tests completed successfully")
    
    except Exception as e:
        log_error(f"Test failed with error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
