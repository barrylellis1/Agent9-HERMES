import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch, mock_open, AsyncMock
import json
import os

from src.agents.new.a9_kpi_assistant_agent import (
    A9_KPI_Assistant_Agent,
    KPISuggestionRequest,
    SchemaMetadata,
    KPIChatRequest,
    KPIValidationRequest,
    KPIFinalizeRequest
)
from src.agents.agent_config_models import A9_KPI_Assistant_Agent_Config
from src.agents.new.a9_llm_service_agent import A9_LLM_Response

# Mock Data
SAMPLE_SCHEMA = SchemaMetadata(
    data_product_id="dp_sales_analytics",
    domain="Sales",
    source_system="BigQuery",
    tables=["sales_orders"],
    measures=[
        {"name": "total_amount", "data_type": "FLOAT"},
        {"name": "quantity", "data_type": "INTEGER"}
    ],
    dimensions=[
        {"name": "customer_segment", "data_type": "STRING"},
        {"name": "region", "data_type": "STRING"}
    ],
    time_columns=[
        {"name": "order_date", "data_type": "TIMESTAMP"}
    ],
    request_id="req_schema_123",
    principal_id="user_123"
)

SAMPLE_KPI_JSON = """
[
  {
    "id": "gross_revenue",
    "name": "Gross Revenue",
    "domain": "Sales",
    "description": "Total sales revenue before deductions",
    "unit": "USD",
    "data_product_id": "dp_sales_analytics",
    "sql_query": "SELECT SUM(total_amount) FROM `project.dataset.sales_orders`",
    "dimensions": [{"name": "Region", "field": "region", "description": "Sales region", "values": ["all"]}],
    "thresholds": [{"comparison_type": "target", "green_threshold": 100000, "yellow_threshold": 50000, "red_threshold": 10000, "inverse_logic": false}],
    "metadata": {
      "line": "top_line",
      "altitude": "strategic",
      "profit_driver_type": "revenue",
      "lens_affinity": "bcg",
      "refresh_frequency": "daily",
      "data_latency": "1 hour",
      "calculation_complexity": "simple"
    },
    "business_process_ids": ["sales_process"],
    "tags": ["revenue"],
    "owner_role": "CSO",
    "stakeholder_roles": ["CEO"]
  }
]
"""

@pytest.fixture
def mock_llm_agent():
    llm = MagicMock()
    # Async mock for generate
    async def mock_generate(*args, **kwargs):
        return A9_LLM_Response(
            status="success",
            request_id="mock_req_123",
            operation="generate",
            content=SAMPLE_KPI_JSON,
            usage={"total_tokens": 100}
        )
    llm.generate = mock_generate
    return llm

@pytest_asyncio.fixture
async def kpi_agent(mock_llm_agent):
    config = A9_KPI_Assistant_Agent_Config(
        llm_provider="openai",
        llm_model="gpt-4",
        temperature=0.0
    )
    agent = A9_KPI_Assistant_Agent(config)
    # Inject mock LLM agent directly
    agent.llm_agent = mock_llm_agent
    return agent

@pytest.mark.asyncio
async def test_connect(mock_llm_agent):
    """Test connection initializes LLM agent"""
    # We need to mock A9_LLM_Service_Agent.create since connect calls it
    with patch('src.agents.new.a9_kpi_assistant_agent.A9_LLM_Service_Agent.create', new_callable=MagicMock) as mock_create:
        async def async_create(*args, **kwargs):
            return mock_llm_agent
        mock_create.side_effect = async_create
        
        agent = A9_KPI_Assistant_Agent()
        success = await agent.connect()
        
        assert success is True
        assert agent.llm_agent is not None
        mock_create.assert_called_once()

@pytest.mark.asyncio
async def test_suggest_kpis(kpi_agent, mock_llm_agent):
    """Test KPI suggestion generation and parsing"""
    request = KPISuggestionRequest(
        schema_metadata=SAMPLE_SCHEMA,
        num_suggestions=3,
        request_id="req_suggest_123",
        principal_id="user_123"
    )
    
    response = await kpi_agent.suggest_kpis(request)
    
    assert response.status == "success"
    assert len(response.suggested_kpis) == 1
    assert response.suggested_kpis[0]["id"] == "gross_revenue"
    assert response.conversation_id.startswith("kpi_conv_")
    
    # Verify conversation history was initialized
    assert response.conversation_id in kpi_agent.conversation_history
    history = kpi_agent.conversation_history[response.conversation_id]
    assert len(history) == 3  # system, user, assistant

@pytest.mark.asyncio
async def test_chat_refinement(kpi_agent):
    """Test chat interaction"""
    # Setup initial conversation
    conv_id = "test_conv_123"
    kpi_agent.conversation_history[conv_id] = [{"role": "system", "content": "Start"}]
    
    request = KPIChatRequest(
        conversation_id=conv_id,
        message="Change the threshold to 200000",
        current_kpis=[],
        request_id="req_chat_123",
        principal_id="user_123"
    )
    
    # Mock LLM response with updated KPI
    updated_kpi_json = SAMPLE_KPI_JSON.replace("100000", "200000")
    async def mock_chat_response(*args, **kwargs):
        return A9_LLM_Response(
            status="success",
            request_id="mock_chat_123",
            operation="chat",
            content=f"Sure, updated.\n```json\n{updated_kpi_json}\n```",
            usage={"total_tokens": 50}
        )
    kpi_agent.llm_agent.generate = mock_chat_response
    
    response = await kpi_agent.chat(request)
    
    assert response.status == "success"
    assert response.updated_kpis is not None
    assert response.updated_kpis[0]["thresholds"][0]["green_threshold"] == 200000
    
    # Verify history updated
    history = kpi_agent.conversation_history[conv_id]
    assert history[-2]["role"] == "user"
    assert history[-2]["content"] == "Change the threshold to 200000"
    assert history[-1]["role"] == "assistant"

@pytest.mark.asyncio
async def test_validate_kpi_valid(kpi_agent):
    """Test validation of a valid KPI"""
    valid_kpi = json.loads(SAMPLE_KPI_JSON)[0]
    
    request = KPIValidationRequest(
        kpi_definition=valid_kpi,
        schema_metadata=SAMPLE_SCHEMA,
        request_id="req_val_123",
        principal_id="user_123"
    )
    
    response = await kpi_agent.validate_kpi(request)
    
    assert response.status == "success"
    assert response.valid is True
    assert len(response.errors) == 0

@pytest.mark.asyncio
async def test_validate_kpi_invalid_metadata(kpi_agent):
    """Test validation with invalid strategic metadata"""
    invalid_kpi = json.loads(SAMPLE_KPI_JSON)[0]
    # Invalid combinations
    invalid_kpi["metadata"]["line"] = "top_line"
    invalid_kpi["metadata"]["profit_driver_type"] = "expense" # Should be revenue
    
    request = KPIValidationRequest(
        kpi_definition=invalid_kpi,
        schema_metadata=SAMPLE_SCHEMA,
        request_id="req_val_inv_123",
        principal_id="user_123"
    )
    
    response = await kpi_agent.validate_kpi(request)
    
    assert response.status == "success"
    # It might still be valid but have warnings
    assert "Inconsistent: top_line with expense driver" in str(response.warnings)

@pytest.mark.asyncio
async def test_validate_kpi_missing_fields(kpi_agent):
    """Test validation with missing required fields"""
    incomplete_kpi = {"id": "test_id"} # Missing name, domain, etc.
    
    request = KPIValidationRequest(
        kpi_definition=incomplete_kpi,
        schema_metadata=SAMPLE_SCHEMA,
        request_id="req_val_miss_123",
        principal_id="user_123"
    )
    
    response = await kpi_agent.validate_kpi(request)
    
    assert response.status == "success"
    assert response.valid is False
    assert any("Missing required field: name" in err for err in response.errors)

@pytest.mark.asyncio
async def test_finalize_kpis_extend_with_registry(kpi_agent):
    """Test finalizing KPIs in extend mode (merging) with registry update"""
    new_kpis = json.loads(SAMPLE_KPI_JSON)
    existing_yaml = """
data_product_id: dp_sales_analytics
kpis:
  - id: existing_kpi
    name: Existing KPI
"""
    
    request = KPIFinalizeRequest(
        data_product_id="dp_sales_analytics",
        kpis=new_kpis,
        extend_mode=True,
        request_id="req_fin_123",
        principal_id="user_123"
    )
    
    # Mock Registry components
    mock_provider = AsyncMock()
    mock_provider.register = AsyncMock(return_value=True)
    
    mock_factory = MagicMock()
    mock_factory.is_initialized = True
    mock_factory.get_kpi_provider.return_value = mock_provider

    # Mock file operations and RegistryFactory
    with patch("src.agents.new.a9_kpi_assistant_agent.os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=existing_yaml)), \
         patch.object(kpi_agent, "_save_contract_yaml") as mock_save, \
         patch.object(kpi_agent, "_load_contract_yaml", return_value=existing_yaml), \
         patch("src.registry.factory.RegistryFactory", return_value=mock_factory):
            
        response = await kpi_agent.finalize_kpis(request)
        
        assert response.status == "success"
        
        # Verify the updated yaml content in the save call
        mock_save.assert_called_once()
        saved_yaml = mock_save.call_args[0][1]
        
        # Should contain both existing and new KPI
        assert "id: existing_kpi" in saved_yaml
        assert "id: gross_revenue" in saved_yaml
        
        # Verify registry update was triggered
        mock_provider.register.assert_called()
        assert response.registry_updates["success"] == ["gross_revenue"]

@pytest.mark.asyncio
async def test_finalize_kpis_replace(kpi_agent):
    """Test finalizing KPIs in replace mode"""
    new_kpis = json.loads(SAMPLE_KPI_JSON)
    existing_yaml = """
data_product_id: dp_sales_analytics
kpis:
  - id: existing_kpi
    name: Existing KPI
"""
    
    request = KPIFinalizeRequest(
        data_product_id="dp_sales_analytics",
        kpis=new_kpis,
        extend_mode=False, # Replace mode
        request_id="req_fin_rep_123",
        principal_id="user_123"
    )
    
    # Mock Registry components
    mock_provider = AsyncMock()
    mock_provider.register = AsyncMock(return_value=True)
    
    mock_factory = MagicMock()
    mock_factory.is_initialized = True
    mock_factory.get_kpi_provider.return_value = mock_provider

    with patch("src.agents.new.a9_kpi_assistant_agent.os.path.exists", return_value=True), \
         patch.object(kpi_agent, "_save_contract_yaml") as mock_save, \
         patch.object(kpi_agent, "_load_contract_yaml", return_value=existing_yaml), \
         patch("src.registry.factory.RegistryFactory", return_value=mock_factory):
            
        response = await kpi_agent.finalize_kpis(request)
        
        assert response.status == "success"
        
        saved_yaml = mock_save.call_args[0][1]
        
        # Should contain ONLY new KPI
        assert "id: existing_kpi" not in saved_yaml
        assert "id: gross_revenue" in saved_yaml
