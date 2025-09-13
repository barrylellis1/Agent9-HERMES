"""
Mock agent implementations for testing.

This module provides standardized mock implementations of Agent9 agents
that can be used across different test scenarios.
"""

import logging
import unittest.mock as mock
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import protocols
try:
    from src.agents.protocols.data_product_protocol import DataProductProtocol
    from src.agents.protocols.principal_context_protocol import PrincipalContextProtocol
    from src.agents.protocols.situation_awareness_protocol import SituationAwarenessProtocol
    from src.agents.protocols.orchestrator_protocol import OrchestratorProtocol
    PROTOCOLS_AVAILABLE = True
except ImportError:
    logger.warning("Agent protocols not available, using base classes instead")
    PROTOCOLS_AVAILABLE = False
    # Define placeholder base classes if protocols are not available
    class DataProductProtocol: pass
    class PrincipalContextProtocol: pass
    class SituationAwarenessProtocol: pass
    class OrchestratorProtocol: pass

# Standard test data
TEST_KPIS = [
    {
        "id": "fin_revenue",
        "name": "Revenue",
        "description": "Total revenue across all business units",
        "unit": "USD",
        "domain": "Finance",
        "calculation": "SUM(revenue)",
        "source_table": "financial_data",
        "business_processes": ["Sales", "Marketing"],
        "thresholds": {
            "critical": {"value": 1000000, "comparison": "lt"},
            "warning": {"value": 1500000, "comparison": "lt"}
        }
    },
    {
        "id": "fin_profit_margin",
        "name": "Profit Margin",
        "description": "Profit margin percentage",
        "unit": "%",
        "domain": "Finance",
        "calculation": "(SUM(revenue) - SUM(costs)) / SUM(revenue) * 100",
        "source_table": "financial_data",
        "business_processes": ["Finance", "Operations"],
        "thresholds": {
            "critical": {"value": 10, "comparison": "lt"},
            "warning": {"value": 15, "comparison": "lt"}
        }
    },
    {
        "id": "fin_cash_flow",
        "name": "Cash Flow",
        "description": "Net cash flow",
        "unit": "USD",
        "domain": "Finance",
        "calculation": "SUM(cash_in) - SUM(cash_out)",
        "source_table": "cash_flow_data",
        "business_processes": ["Finance", "Treasury"],
        "thresholds": {
            "critical": {"value": 0, "comparison": "lt"},
            "warning": {"value": 100000, "comparison": "lt"}
        }
    }
]

TEST_PRINCIPAL_PROFILES = [
    {
        "principal_id": "cfo_001",
        "role": "CFO",
        "name": "Jane Smith",
        "business_processes": ["Finance", "Treasury", "Accounting"],
        "default_filters": {"region": "Global", "time_period": "Monthly"},
        "decision_style": "analytical",
        "communication_style": "direct",
        "preferred_timeframes": ["Monthly", "Quarterly", "Annual"]
    },
    {
        "principal_id": "ceo_001",
        "role": "CEO",
        "name": "John Doe",
        "business_processes": ["Executive", "Strategy", "Operations"],
        "default_filters": {"region": "Global", "time_period": "Quarterly"},
        "decision_style": "strategic",
        "communication_style": "visionary",
        "preferred_timeframes": ["Quarterly", "Annual"]
    }
]

class MockKPIProvider:
    """Mock KPI provider for testing."""
    
    def __init__(self, kpis=None):
        """Initialize with optional custom KPIs."""
        self.kpis = kpis or TEST_KPIS
    
    def get_all(self):
        """Get all KPIs."""
        return self.kpis
    
    def get_by_id(self, kpi_id):
        """Get a KPI by ID."""
        for kpi in self.kpis:
            if kpi["id"] == kpi_id:
                return kpi
        return None
    
    def get_by_domain(self, domain):
        """Get KPIs by domain."""
        return [kpi for kpi in self.kpis if kpi.get("domain") == domain]

class MockPrincipalProfileProvider:
    """Mock principal profile provider for testing."""
    
    def __init__(self, profiles=None):
        """Initialize with optional custom profiles."""
        self.profiles = profiles or TEST_PRINCIPAL_PROFILES
    
    def get_all(self):
        """Get all principal profiles."""
        return self.profiles
    
    def get_by_id(self, principal_id):
        """Get a principal profile by ID."""
        for profile in self.profiles:
            if profile["principal_id"] == principal_id:
                return profile
        return None
    
    def get_by_role(self, role):
        """Get principal profiles by role."""
        return [profile for profile in self.profiles if profile.get("role") == role]

class MockRegistryFactory:
    """Mock registry factory for testing."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MockRegistryFactory, cls).__new__(cls)
            cls._instance.providers = {
                "kpi": MockKPIProvider(),
                "principal_profile": MockPrincipalProfileProvider()
            }
        return cls._instance
    
    def get_kpi_provider(self):
        """Get the KPI provider."""
        return self.providers.get("kpi")
    
    def get_principal_profile_provider(self):
        """Get the principal profile provider."""
        return self.providers.get("principal_profile")
    
    def get_provider(self, provider_type):
        """Get a provider by type."""
        return self.providers.get(provider_type)

class MockDataProductAgent(DataProductProtocol):
    """Mock Data Product Agent for testing."""
    
    def __init__(self, config=None):
        """Initialize with optional config."""
        self.config = config or {}
        self.contract_path = self.config.get("contract_path", "src/contracts/fi_star_schema.yaml")
        
    async def connect(self):
        """Connect to the agent."""
        logger.info("Mock Data Product Agent connected")
        return True
    
    async def disconnect(self):
        """Disconnect from the agent."""
        logger.info("Mock Data Product Agent disconnected")
        return True
    
    async def generate_sql(self, kpi_id, filters=None, timeframe=None):
        """Generate SQL for a KPI."""
        logger.info(f"Mock Data Product Agent generating SQL for KPI: {kpi_id}")
        # Return a simple mock SQL query
        return f"SELECT * FROM financial_data WHERE kpi_id = '{kpi_id}'"
    
    async def execute_sql(self, sql_query):
        """Execute a SQL query."""
        logger.info(f"Mock Data Product Agent executing SQL: {sql_query}")
        # Return mock data based on the query
        if "revenue" in sql_query.lower():
            return [{"date": "2025-01-01", "value": 2000000}]
        elif "profit" in sql_query.lower():
            return [{"date": "2025-01-01", "value": 20}]
        elif "cash" in sql_query.lower():
            return [{"date": "2025-01-01", "value": 500000}]
        else:
            return [{"date": "2025-01-01", "value": 0}]
    
    @classmethod
    async def create(cls, config):
        """Create a new instance."""
        instance = cls(config)
        await instance.connect()
        return instance

class MockPrincipalContextAgent(PrincipalContextProtocol):
    """Mock Principal Context Agent for testing."""
    
    def __init__(self, config=None):
        """Initialize with optional config."""
        self.config = config or {}
        self.profiles = TEST_PRINCIPAL_PROFILES
        
    async def connect(self):
        """Connect to the agent."""
        logger.info("Mock Principal Context Agent connected")
        return True
    
    async def disconnect(self):
        """Disconnect from the agent."""
        logger.info("Mock Principal Context Agent disconnected")
        return True
    
    async def get_principal_profile(self, principal_id):
        """Get a principal profile by ID."""
        logger.info(f"Mock Principal Context Agent getting profile for: {principal_id}")
        for profile in self.profiles:
            if profile["principal_id"] == principal_id:
                return profile
        return None
    
    async def get_all_principal_profiles(self):
        """Get all principal profiles."""
        logger.info("Mock Principal Context Agent getting all profiles")
        return self.profiles
    
    @classmethod
    async def create(cls, config):
        """Create a new instance."""
        instance = cls(config)
        await instance.connect()
        return instance

class MockOrchestratorAgent(OrchestratorProtocol):
    """Mock Orchestrator Agent for testing."""
    
    def __init__(self, config=None):
        """Initialize with optional config."""
        self.config = config or {}
        self.registered_agents = {}
        self.agent_factories = {
            "A9_Data_Product_Agent": MockAgentFactory.create_data_product_agent,
            "A9_Principal_Context_Agent": MockAgentFactory.create_principal_context_agent
        }
        
    async def connect(self):
        """Connect to the agent."""
        logger.info("Mock Orchestrator Agent connected")
        return True
    
    async def disconnect(self):
        """Disconnect from the agent."""
        logger.info("Mock Orchestrator Agent disconnected")
        return True
    
    def register_agent(self, agent_name, agent_instance):
        """Register an agent instance."""
        logger.info(f"Registering agent: {agent_name}")
        self.registered_agents[agent_name] = agent_instance
        return True
    
    def register_agent_factory(self, agent_name, factory_function):
        """Register an agent factory function."""
        logger.info(f"Registering agent factory: {agent_name}")
        self.agent_factories[agent_name] = factory_function
        return True
    
    async def get_agent(self, agent_name):
        """Get an agent by name."""
        logger.info(f"Getting agent: {agent_name}")
        if agent_name in self.registered_agents:
            return self.registered_agents[agent_name]
        elif agent_name in self.agent_factories:
            # Create the agent using the factory
            agent = await self.agent_factories[agent_name]({})
            self.registered_agents[agent_name] = agent
            return agent
        else:
            logger.warning(f"Agent not found: {agent_name}")
            return None
    
    @classmethod
    async def create(cls, config):
        """Create a new instance."""
        instance = cls(config)
        await instance.connect()
        return instance

# Factory for creating mock agents
class MockAgentFactory:
    """Factory for creating standardized mock agents."""
    
    @staticmethod
    async def create_data_product_agent(config=None):
        """Create a mock Data Product Agent."""
        return await MockDataProductAgent.create(config or {})
    
    @staticmethod
    async def create_principal_context_agent(config=None):
        """Create a mock Principal Context Agent."""
        return await MockPrincipalContextAgent.create(config or {})
    
    @staticmethod
    async def create_orchestrator_agent(config=None):
        """Create a mock Orchestrator Agent."""
        return await MockOrchestratorAgent.create(config or {})
    
    @staticmethod
    def register_mock_agents(agent_registry):
        """Register mock agents with the agent registry."""
        agent_registry.register_agent_factory(
            "A9_Data_Product_Agent",
            MockAgentFactory.create_data_product_agent
        )
        agent_registry.register_agent_factory(
            "A9_Principal_Context_Agent",
            MockAgentFactory.create_principal_context_agent
        )

# Helper function to patch registry factory
def patch_registry_factory():
    """Patch the registry factory import."""
    import sys
    sys.modules['src.registry.registry_factory'] = type(
        'MockRegistryFactoryModule', 
        (), 
        {'RegistryFactory': MockRegistryFactory}
    )
    return MockRegistryFactory()
