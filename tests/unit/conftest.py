import pytest
import asyncio

# arch-allow-direct-agent-construction

LEGACY_STACK_AVAILABLE = True
try:
    from src.agents.agent_registry import registry
    from src.agents.a9_orchestrator_agent import A9_Orchestrator_Agent
    from src.agents.a9_principal_context_agent import A9_Principal_Context_Agent
    from src.agents.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
    from src.agents.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
    from src.agents.a9_solution_finder_agent import A9_Solution_Finder_Agent
    from src.agents.a9_data_governance_agent import A9_Data_Governance_Agent
    from src.agents.a9_data_product_agent import A9_Data_Product_Agent
    from src.agents.a9_nlp_interface_agent_v2 import A9_NLP_Interface_Agent_V2
    from pytest_asyncio import fixture as async_fixture
    from unittest.mock import patch, AsyncMock
except Exception:
    LEGACY_STACK_AVAILABLE = False
    # Provide stand-ins to keep pytest collection working
    from pytest_asyncio import fixture as async_fixture

@async_fixture
async def nlp_agent():
    """Creates and returns an isolated NLP agent instance for testing."""
    if not LEGACY_STACK_AVAILABLE:
        # No-op to keep tests that don't need legacy stack running
        yield None
        return
    else:
        with patch('src.agents.a9_nlp_interface_agent_v2.A9_NLP_Interface_Agent_V2.register_with_registry', new_callable=AsyncMock):
            agent = await A9_NLP_Interface_Agent_V2.create_from_registry()
            yield agent

@pytest.fixture(scope="function")
def event_loop():
    """Create an instance of the default event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@async_fixture(scope="function", autouse=True)
async def setup_agents(request, event_loop):
    if 'no_agent_setup' in request.keywords or not LEGACY_STACK_AVAILABLE:
        # Skip heavy legacy setup for tests that don't need it or when legacy stack is unavailable
        yield
        return
    """Fixture to set up all agents in the correct order for the test session."""
    # Clear the registry to ensure a clean state for each test run
    registry._agents = {}
    registry._agent_classes = {}

    # Instantiate agents in dependency order
    # Level 0: No dependencies
    principal_context_agent = await A9_Principal_Context_Agent.create_from_registry()
    data_governance_agent = await A9_Data_Governance_Agent.create_from_registry()
    data_product_agent = await A9_Data_Product_Agent.create_from_registry()
    nlp_interface_agent = await A9_NLP_Interface_Agent_V2.create_from_registry()
    situation_awareness_agent = await A9_Situation_Awareness_Agent.create_from_registry()
    
    # Level 1: Depends on other agents (Orchestrator)
    orchestrator = await A9_Orchestrator_Agent.create_from_registry()

    # Level 2: Depends on Orchestrator
    deep_analysis_agent = await A9_Deep_Analysis_Agent.create_from_registry()
    deep_analysis_agent.orchestrator = orchestrator
    solution_finder_agent = await A9_Solution_Finder_Agent.create_from_registry()

    # Yield control to the tests
    yield

    # Teardown: clear the registry after the session
    registry._agents = {}
    registry._agent_classes = {}
