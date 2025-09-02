import pytest
import asyncio
import uuid
from unittest.mock import patch, MagicMock

from src.agents.agent_registry import registry
from src.agents.a9_principal_context_agent import A9_Principal_Context_Agent
from src.agents.utils.a9_exceptions import ValidationError
from src.agents.models.principal_context_models import (
    PrincipalProfileRequest,
    PrincipalProfileResponse,
    SetPrincipalContextRequest,
    SetPrincipalContextResponse,
    ExtractFiltersRequest,
    ExtractFiltersResponse,
    ExtractedFilter
)
from src.agents.models.situation_awareness_models import PrincipalContext, TimeFrame, BusinessProcess


@pytest.mark.asyncio
async def test_create_and_register_agent():
    """Tests that the agent can be created and registers itself."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    assert isinstance(agent, A9_Principal_Context_Agent)
    assert agent.name == "A9_Principal_Context_Agent"

@pytest.mark.asyncio
async def test_fetch_principal_profile_success():
    """Tests that fetching a profile returns the expected data."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    profile = await agent.fetch_principal_profile("ceo")
    
    assert profile is not None
    assert "name" in profile
    assert "business_processes" in profile
    assert "default_filters" in profile
    assert "decision_style" in profile
    assert "communication_style" in profile
    assert isinstance(profile["business_processes"], list)

@pytest.mark.asyncio
async def test_fetch_principal_profile_validation_error():
    """Tests that a validation error is raised for a missing principal_id."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    with pytest.raises(ValidationError):
        await agent.fetch_principal_profile("")

@pytest.mark.asyncio
async def test_get_principal_context_with_string():
    """Tests get_principal_context with a string input."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    response = await agent.get_principal_context("cfo")
    
    assert isinstance(response, PrincipalProfileResponse)
    assert response.status == "success"
    assert response.context.role.lower() == "cfo"
    assert len(response.context.business_processes) > 0
    assert isinstance(response.context.default_filters, dict)
    assert "profit_center_hierarchyid" in response.context.default_filters
    assert len(response.context.preferred_timeframes) > 0

@pytest.mark.asyncio
async def test_get_principal_context_with_dict():
    """Tests get_principal_context with a dictionary input."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    request_dict = {"principal_role": "ceo", "request_id": str(uuid.uuid4())}
    response = await agent.get_principal_context(request_dict)
    
    assert isinstance(response, PrincipalProfileResponse)
    assert response.status == "success"
    assert response.context.role.lower() == "ceo"
    assert response.request_id == request_dict["request_id"]

@pytest.mark.asyncio
async def test_get_principal_context_with_model():
    """Tests get_principal_context with a Pydantic model input."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    request = PrincipalProfileRequest(principal_role="coo", request_id=str(uuid.uuid4()))
    response = await agent.get_principal_context(request)
    
    assert isinstance(response, PrincipalProfileResponse)
    assert response.status == "success"
    assert response.context.role.lower() == "coo"
    assert response.request_id == request.request_id

@pytest.mark.asyncio
async def test_get_principal_context_unknown_role():
    """Tests get_principal_context with an unknown role."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    response = await agent.get_principal_context("unknown_role")
    
    assert isinstance(response, PrincipalProfileResponse)
    assert response.status == "error"
    assert "unknown_role" in response.message.lower()

@pytest.mark.asyncio
async def test_extract_filters_from_job_description():
    """Tests extracting filters from a job description."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    job_description = """
    Analyze the Q2 financial performance for the North America region, 
    focusing on the Retail division's revenue growth compared to last year.
    """
    
    request = ExtractFiltersRequest(
        description=job_description,  # Note: field name is 'description' not 'job_description'
        request_id=str(uuid.uuid4())
    )
    
    response = await agent.extract_filters(request)
    
    assert isinstance(response, ExtractFiltersResponse)
    assert response.status == "success"
    assert len(response.filters) > 0
    
    # Check for expected filters
    assert "region" in response.filters
    assert "North America" in response.filters["region"]
    
    # Check extracted_filters list
    assert len(response.extracted_filters) > 0
    filter_dimensions = [f.dimension for f in response.extracted_filters]
    assert "region" in filter_dimensions
    assert "time_period" in filter_dimensions

@pytest.mark.asyncio
async def test_extract_filters_empty_description():
    """Tests extracting filters from an empty job description."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    request = ExtractFiltersRequest(
        description="",  # Note: field name is 'description' not 'job_description'
        request_id=str(uuid.uuid4())
    )
    
    response = await agent.extract_filters(request)
    
    assert isinstance(response, ExtractFiltersResponse)
    # Empty description should still return success but with no filters
    assert response.status == "success"
    assert len(response.filters) == 0
    assert len(response.extracted_filters) == 0

@pytest.mark.asyncio
async def test_set_principal_context():
    """Tests setting principal context."""
    agent = await registry.get_agent("A9_Principal_Context_Agent")
    
    # Create a request with principal_id and context_data
    request = SetPrincipalContextRequest(
        principal_id="cfo",  # Use a role that exists in the registry
        context_data={
            "filters": {"region": "North America", "division": "Retail"},
            "timeframe": "QUARTERLY"
        },
        request_id=str(uuid.uuid4())
    )
    
    response = await agent.set_principal_context(request)
    
    assert isinstance(response, SetPrincipalContextResponse)
    assert response.status == "success"
    assert "cfo" in response.message.lower()
    assert isinstance(response.profile, dict)
    assert isinstance(response.filters, dict)

@pytest.mark.asyncio
async def test_with_mocked_registry_provider():
    """Tests the agent with a mocked registry provider."""
    # Create a mock registry data with principals array
    mock_registry_data = {
        "principals": [
            {
                "id": "mock_cfo_001",
                "name": "Mock CFO",
                "title": "Chief Financial Officer",
                "role": "MOCK_CFO",
                "department": "Finance",
                "responsibilities": ["Financial reporting", "Budget management"],
                "business_processes": ["Finance: Reporting", "Finance: Budget Planning"],
                "default_filters": {"region": "Global", "division": "All"},
                "typical_timeframes": ["Quarterly", "Annual"],
                "principal_groups": ["executive_team"],
                "persona_profile": {
                    "decision_style": "analytical",
                    "risk_tolerance": "moderate",
                    "communication_style": "direct",
                    "values": ["accuracy", "efficiency"]
                },
                "preferences": {
                    "channel": "email",
                    "ui": "finance_dashboard"
                },
                "permissions": ["finance_read", "finance_write"]
            }
        ],
        "roles": [
            {
                "id": "mock_cfo_001",
                "name": "MOCK_CFO",
                "description": "Mock Chief Financial Officer",
                "permissions": ["finance_read", "finance_write"]
            }
        ]
    }
    
    # Create a mock provider class
    mock_provider = MagicMock()
    mock_provider.get_all.return_value = mock_registry_data
    
    # Patch the registry factory to return our mock provider
    with patch('src.agents.a9_principal_context_agent.RegistryFactory') as mock_factory:
        mock_factory_instance = MagicMock()
        mock_factory_instance.get_provider.return_value = mock_provider
        mock_factory.return_value = mock_factory_instance
        
        # Create the agent with the mocked dependencies
        agent = A9_Principal_Context_Agent()
        await agent.connect()
        
        # Test with the mocked provider
        response = await agent.get_principal_context("mock_cfo")
        
        # Verify the response contains our mock data
        assert isinstance(response, PrincipalProfileResponse)
        assert response.status == "success"
        assert response.context.role.lower() == "mock_cfo"
        assert len(response.context.business_processes) > 0
        assert isinstance(response.context.default_filters, dict)
        assert "region" in response.context.default_filters
        assert response.context.default_filters["region"] == "Global"
        assert len(response.context.preferred_timeframes) > 0
