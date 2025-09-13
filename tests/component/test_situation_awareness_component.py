"""
Component test for Situation Awareness Agent.

This test focuses on testing the Situation Awareness Agent in isolation,
with mocked dependencies.
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pytest
pytestmark = pytest.mark.asyncio

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the mock agents
from tests.mocks.mock_agents import (
    MockAgentFactory,
    MockDataProductAgent,
    MockPrincipalContextAgent,
    MockOrchestratorAgent,
    patch_registry_factory
)

# Import situation awareness models
from src.agents.models.situation_awareness_models import (
    SituationSeverity,
    Situation,
    KPIDefinition,
    KPIValue,
    TimeFrame,
    ComparisonType,
    BusinessProcess,
    PrincipalRole
)

# Import the agent
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent

@pytest.mark.asyncio
async def test_kpi_loading():
    """Test KPI loading in the Situation Awareness Agent."""
    logger.info("Starting KPI loading component test")
    
    # Patch the registry factory
    registry_factory = patch_registry_factory()
    
    try:
        # Create mock orchestrator
        orchestrator = await MockOrchestratorAgent.create({})
        
        # Register mock dependencies with the orchestrator
        data_product_agent = await MockDataProductAgent.create({})
        principal_context_agent = await MockPrincipalContextAgent.create({})
        
        # Register agents with the orchestrator
        orchestrator.register_agent("A9_Data_Product_Agent", data_product_agent)
        orchestrator.register_agent("A9_Principal_Context_Agent", principal_context_agent)
        
        # Create the Situation Awareness Agent with orchestrator
        agent_config = {
            "contract_path": "src/contracts/fi_star_schema.yaml",
            "target_domains": ["Finance"],
            "orchestrator": orchestrator
        }
        
        logger.info("Creating Situation Awareness Agent...")
        agent = await A9_Situation_Awareness_Agent.create(agent_config)
        
        # Verify KPI registry is loaded
        logger.info(f"KPI Registry loaded: {len(agent.kpi_registry)} KPIs")
        
        # Print the KPIs for verification
        for kpi_name, kpi_def in agent.kpi_registry.items():
            logger.info(f"KPI: {kpi_name}")
        
        # Test KPI filtering by domain
        finance_kpis = [kpi for kpi_name, kpi in agent.kpi_registry.items() 
                       if hasattr(kpi, 'domain') and kpi.domain == "Finance"]
        logger.info(f"Finance KPIs: {len(finance_kpis)}")
        
        return len(agent.kpi_registry) > 0
            
    except Exception as e:
        logger.error(f"Error in KPI loading test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if 'agent' in locals():
            await agent.disconnect()

@pytest.mark.asyncio
async def test_principal_profile_loading():
    """Test principal profile loading in the Situation Awareness Agent."""
    logger.info("Starting principal profile loading component test")
    
    # Patch the registry factory
    registry_factory = patch_registry_factory()
    
    try:
        # Create mock orchestrator
        orchestrator = await MockOrchestratorAgent.create({})
        
        # Register mock dependencies with the orchestrator
        data_product_agent = await MockDataProductAgent.create({})
        principal_context_agent = await MockPrincipalContextAgent.create({})
        
        # Register agents with the orchestrator
        orchestrator.register_agent("A9_Data_Product_Agent", data_product_agent)
        orchestrator.register_agent("A9_Principal_Context_Agent", principal_context_agent)
        
        # Create the Situation Awareness Agent with orchestrator
        agent_config = {
            "contract_path": "src/contracts/fi_star_schema.yaml",
            "target_domains": ["Finance"],
            "orchestrator": orchestrator
        }
        
        logger.info("Creating Situation Awareness Agent...")
        agent = await A9_Situation_Awareness_Agent.create(agent_config)
        
        # Load principal profiles
        await agent._load_principal_profiles()
        
        # Verify principal profiles are loaded
        logger.info(f"Principal profiles loaded: {len(agent.principal_profiles)}")
        
        # Print the profiles for verification
        for principal_id, profile in agent.principal_profiles.items():
            logger.info(f"Profile: {principal_id} - {profile.get('role', 'Unknown role')}")
        
        return len(agent.principal_profiles) > 0
            
    except Exception as e:
        logger.error(f"Error in principal profile loading test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        if 'agent' in locals():
            await agent.disconnect()

async def run_all_tests():
    """Run all component tests."""
    logger.info("Running all Situation Awareness Agent component tests")
    
    kpi_loading_result = await test_kpi_loading()
    logger.info(f"KPI loading test: {'PASSED' if kpi_loading_result else 'FAILED'}")
    
    profile_loading_result = await test_principal_profile_loading()
    logger.info(f"Principal profile loading test: {'PASSED' if profile_loading_result else 'FAILED'}")
    
    return kpi_loading_result and profile_loading_result

if __name__ == "__main__":
    # Run all tests
    asyncio.run(run_all_tests())
