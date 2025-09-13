"""
Simple test script for verifying KPI registry integration with Situation Awareness Agent.
This script focuses specifically on testing the KPI loading and situation detection
with the canonical KPI model.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import unittest.mock as mock
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import situation awareness models
from src.agents.models.situation_awareness_models import (
    SituationSeverity,
    Situation,
    KPIDefinition,
    KPIValue,
    TimeFrame,
    ComparisonType,
    BusinessProcess,
    PrincipalRole,
    BaseRequest,
    BaseResponse
)

# Define request/response classes for situation detection
class SituationDetectionRequest(BaseRequest):
    """Request for situation detection."""
    principal_context: 'PrincipalContext'
    business_processes: List[BusinessProcess]
    timeframe: TimeFrame
    comparison_type: Optional[ComparisonType] = None
    filters: Optional[Dict[str, Any]] = None

class SituationDetectionResponse(BaseResponse):
    """Response with detected situations."""
    situations: List[Situation]

class PrincipalContext(BaseModel):
    """Principal context for personalization."""
    role: PrincipalRole
    principal_id: str
    business_processes: List[BusinessProcess]
    default_filters: Dict[str, Any]
    decision_style: str
    communication_style: str
    preferred_timeframes: List[TimeFrame]

# Import registry models
from src.registry.models.kpi import KPI

# Import agent orchestration
from src.agents.agent_registry import AgentRegistry
from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent

# Import the agents
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent

# Mock Data Product Agent for testing
class MockDataProductAgent:
    def __init__(self):
        self.config = mock.MagicMock()
        # Add required attributes that are accessed during testing
        self.config.contracts_path = "src/contracts"
        self.data_products = {
            "financial_transactions": {"tables": ["gl_line_items", "ap_items", "ar_items"]},
            "general_ledger": {"tables": ["accounts", "cost_centers", "profit_centers"]}
        }
        # Mock KPIs with technical names that match business terms
        self.kpi_registry = {
            "revenue": {
                "name": "revenue",
                "description": "Total revenue",
                "unit": "USD",
                "business_process_ids": ["Finance: Revenue Growth Analysis"]
            },
            "profit_margin": {
                "name": "profit_margin",
                "description": "Profit margin percentage",
                "unit": "%",
                "business_process_ids": ["Finance: Profitability Analysis"]
            }
        }
    
    async def connect(self):
        logger.info("Mock Data Product Agent connected")
        return True
    
    async def disconnect(self):
        logger.info("Mock Data Product Agent disconnected")
        return True
    
    async def generate_sql(self, query: str, context: Dict[str, Any] = None) -> str:
        """Mock SQL generation for KPIs"""
        logger.info(f"Generating SQL for query: {query}")
        return "SELECT SUM(amount) FROM gl_line_items WHERE account_type = 'revenue'"
    
    async def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """Mock SQL execution returning sample data"""
        logger.info(f"Executing SQL: {sql}")
        if "revenue" in sql.lower():
            return [{"value": 1000000.0}]
        elif "profit" in sql.lower():
            return [{"value": 250000.0}]
        else:
            return [{"value": 0.0}]

# Mock Principal Context Agent for testing
class MockPrincipalContextAgent:
    def __init__(self):
        self.config = mock.MagicMock()
        # Sample principal profiles for testing
        self.principal_profiles = {
            "CFO": {
                "id": "CFO",
                "name": "Chief Financial Officer",
                "role": "CFO",
                "business_processes": ["Finance: Profitability Analysis", "Finance: Revenue Growth Analysis"],
                "default_filters": {},
                "decision_style": "analytical",
                "communication_style": "direct",
                "preferred_timeframes": ["current_month", "current_quarter", "year_to_date"]
            },
            "Finance_Manager": {
                "id": "Finance_Manager",
                "name": "Finance Manager",
                "role": "Finance Manager",
                "business_processes": ["Finance: Expense Management", "Finance: Budget vs. Actuals"],
                "default_filters": {},
                "decision_style": "collaborative",
                "communication_style": "detailed",
                "preferred_timeframes": ["month_to_date", "quarter_to_date"]
            }
        }
    
    async def connect(self):
        logger.info("Mock Principal Context Agent connected")
        return True
    
    async def disconnect(self):
        logger.info("Mock Principal Context Agent disconnected")
        return True
    
    async def get_all_principal_profiles(self):
        """Return all principal profiles"""
        logger.info("Getting all principal profiles")
        return self.principal_profiles
    
    async def get_principal_profile(self, principal_id: str):
        """Return a specific principal profile"""
        logger.info(f"Getting principal profile for {principal_id}")
        return self.principal_profiles.get(principal_id)

# Create a factory function for the Situation Awareness Agent
async def create_situation_awareness_agent(config):
    """Create a new instance of the Situation Awareness Agent"""
    return await A9_Situation_Awareness_Agent.create(config)

async def test_kpi_registry_integration():
    """Test KPI registry integration with Situation Awareness Agent"""
    logger.info("Starting KPI registry integration test")
    
    # Create an orchestrator
    orchestrator = await A9_Orchestrator_Agent.create({})
    
    # Define an async factory for the Data Product Agent
    async def async_data_product_agent_factory(config):
        if config.get("mock", False):
            return MockDataProductAgent()
        else:
            # Import the Data Product Agent
            from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
            # Await the async create method
            return await A9_Data_Product_Agent.create({
                "contracts_path": "src/contracts",
                "data_directory": "data",
                "registry_path": "src/registry/data_product/data_product_registry.yaml"
            })
    
    # Define an async factory for the Principal Context Agent
    async def async_principal_context_agent_factory(config):
        if config.get("mock", False):
            return MockPrincipalContextAgent()
        else:
            # Import the Principal Context Agent
            from src.agents.new.a9_principal_context_agent import A9_Principal_Context_Agent
            # Await the async create method
            return await A9_Principal_Context_Agent.create({
                "registry_path": "src/registry/principal/principal_registry.yaml"
            })
    
    # Register the agent factories with the registry
    AgentRegistry.register_agent_factory(
        "A9_Data_Product_Agent",
        async_data_product_agent_factory
    )
    
    AgentRegistry.register_agent_factory(
        "A9_Principal_Context_Agent",
        async_principal_context_agent_factory
    )
    
    # Register the agent factories with the orchestrator
    await orchestrator.register_agent("A9_Data_Product_Agent", {"mock": True})
    await orchestrator.register_agent("A9_Principal_Context_Agent", {"mock": True})
    
    try:
        # Create the Situation Awareness Agent with the orchestrator
        agent_config = {
            "contract_path": "src/contracts/fi_star_schema.yaml",
            "orchestrator": orchestrator,
            "mock": True  # Use mock agents for testing
        }
        
        logger.info("Creating Situation Awareness Agent...")
        agent = await create_situation_awareness_agent(agent_config)
        
        # Connect to dependencies through the orchestrator
        logger.info("Connecting to dependencies via orchestrator...")
        await agent.connect()
        
        # Verify KPI registry is loaded
        logger.info(f"KPI Registry loaded: {len(agent.kpi_registry)} KPIs")
        for kpi_name, kpi_def in agent.kpi_registry.items():
            logger.info(f"KPI: {kpi_name} - {kpi_def.get('description', 'No description')}")
        
        # Verify principal profiles are loaded
        logger.info(f"Principal Profiles loaded: {len(agent.principal_profiles)} profiles")
        for profile_id, profile in agent.principal_profiles.items():
            logger.info(f"Profile: {profile_id} - {profile.get('name', 'No name')}")
        
        # Create a sample situation detection request
        principal_context = PrincipalContext(
            role=PrincipalRole.CFO,
            principal_id="CFO",
            business_processes=[BusinessProcess.PROFITABILITY_ANALYSIS, BusinessProcess.REVENUE_GROWTH],
            default_filters={},
            decision_style="analytical",
            communication_style="direct",
            preferred_timeframes=[TimeFrame.CURRENT_MONTH, TimeFrame.CURRENT_QUARTER]
        )
        
        request = SituationDetectionRequest(
            request_id="test-request-001",
            timestamp=datetime.now(),
            principal_context=principal_context,
            business_processes=[BusinessProcess.PROFITABILITY_ANALYSIS, BusinessProcess.REVENUE_GROWTH],
            timeframe=TimeFrame.CURRENT_MONTH,
            comparison_type=ComparisonType.MONTH_OVER_MONTH
        )
        
        # Detect situations
        logger.info("Detecting situations...")
        response = await agent.detect_situations(request)
        
        # Verify response
        logger.info(f"Detected {len(response.situations)} situations")
        for situation in response.situations:
            logger.info(f"Situation: {situation.kpi_name} - {situation.severity} - {situation.description}")
        
        # Disconnect from dependencies
        logger.info("Disconnecting from dependencies...")
        await agent.disconnect()
        
        logger.info("KPI registry integration test completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error in KPI registry integration test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_kpi_registry_integration())
