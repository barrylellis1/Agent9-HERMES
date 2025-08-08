import pytest
import asyncio

from src.agents.agent_registry import registry
from src.agents.a9_principal_context_agent import A9_Principal_Context_Agent
from src.agents.utils.a9_exceptions import ValidationError



@pytest.mark.asyncio
async def test_create_and_register_agent():
    """Tests that the agent can be created and registers itself."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    assert isinstance(agent, A9_Principal_Context_Agent)
    assert agent.name == "A9_Principal_Context_Agent"

@pytest.mark.asyncio
async def test_fetch_principal_profile_success():
    """Tests that fetching a profile returns the expected mock data."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    profile = await agent.fetch_principal_profile("ceo")
    
    assert "profile" in profile
    assert "responsibilities" in profile["profile"]
    assert "default_filters" in profile["profile"]
    assert isinstance(profile["profile"]["responsibilities"], list)

@pytest.mark.asyncio
async def test_fetch_principal_profile_validation_error():
    """Tests that a validation error is raised for a missing principal_id."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    with pytest.raises(ValidationError):
        await agent.fetch_principal_profile("")
