"""
API routes for KPI Assistant during data product onboarding.

Provides endpoints for:
- KPI suggestion based on schema analysis
- Interactive chat for KPI refinement
- KPI validation
- KPI finalization and contract updates
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import logging

from src.agents.new.a9_kpi_assistant_agent import (
    A9_KPI_Assistant_Agent,
    KPISuggestionRequest,
    KPISuggestionResponse,
    KPIChatRequest,
    KPIChatResponse,
    KPIValidationRequest,
    KPIValidationResponse,
    KPIFinalizeRequest,
    KPIFinalizeResponse,
    SchemaMetadata,
    create_kpi_assistant_agent
)
from src.agents.agent_config_models import A9_KPI_Assistant_Agent_Config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/data-product-onboarding/kpi-assistant", tags=["kpi-assistant"])

# Global agent instance (will be initialized on startup)
_kpi_assistant_agent: Optional[A9_KPI_Assistant_Agent] = None


async def get_kpi_assistant_agent() -> A9_KPI_Assistant_Agent:
    """Dependency to get KPI Assistant Agent instance"""
    global _kpi_assistant_agent
    if _kpi_assistant_agent is None:
        config = A9_KPI_Assistant_Agent_Config()
        _kpi_assistant_agent = create_kpi_assistant_agent(config)
        await _kpi_assistant_agent.connect()
    return _kpi_assistant_agent


# Request/Response models for API
class SuggestKPIsAPIRequest(BaseModel):
    """API request for KPI suggestions"""
    data_product_id: str
    domain: str = "Unknown"
    source_system: str
    tables: List[str] = Field(default_factory=list, description="Table/view names in the data product")
    database: Optional[str] = Field(None, description="Database/project name")
    schema: Optional[str] = Field(None, description="Schema/dataset name")
    measures: List[Dict[str, Any]] = Field(default_factory=list)
    dimensions: List[Dict[str, Any]] = Field(default_factory=list)
    time_columns: List[Dict[str, Any]] = Field(default_factory=list)
    identifiers: List[Dict[str, Any]] = Field(default_factory=list)
    user_context: Optional[Dict[str, Any]] = None
    num_suggestions: int = 5


class SuggestKPIsAPIResponse(BaseModel):
    """API response for KPI suggestions"""
    status: str
    suggested_kpis: List[Dict[str, Any]]
    conversation_id: str
    rationale: str
    error: Optional[str] = None


class ChatAPIRequest(BaseModel):
    """API request for KPI chat"""
    conversation_id: str
    message: str
    current_kpis: List[Dict[str, Any]] = Field(default_factory=list)


class ChatAPIResponse(BaseModel):
    """API response for KPI chat"""
    status: str
    response: str
    updated_kpis: Optional[List[Dict[str, Any]]] = None
    actions: Optional[List[Dict[str, str]]] = None
    error: Optional[str] = None


class ValidateKPIAPIRequest(BaseModel):
    """API request for KPI validation"""
    kpi_definition: Dict[str, Any]
    data_product_id: str
    domain: str
    source_system: str
    measures: List[Dict[str, Any]] = Field(default_factory=list)
    dimensions: List[Dict[str, Any]] = Field(default_factory=list)
    time_columns: List[Dict[str, Any]] = Field(default_factory=list)
    identifiers: List[Dict[str, Any]] = Field(default_factory=list)


class ValidateKPIAPIResponse(BaseModel):
    """API response for KPI validation"""
    status: str
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class FinalizeKPIsAPIRequest(BaseModel):
    """API request for KPI finalization"""
    data_product_id: str
    kpis: List[Dict[str, Any]]
    extend_mode: bool = Field(default=False, description="If True, merge new KPIs with existing ones; if False, replace all KPIs")


class FinalizeKPIsAPIResponse(BaseModel):
    """API response for KPI finalization"""
    status: str
    updated_contract_yaml: str
    registry_updates: Dict[str, Any]
    error: Optional[str] = None


@router.post("/suggest", response_model=SuggestKPIsAPIResponse)
async def suggest_kpis(
    request: SuggestKPIsAPIRequest,
    agent: A9_KPI_Assistant_Agent = Depends(get_kpi_assistant_agent)
) -> SuggestKPIsAPIResponse:
    """
    Generate KPI suggestions based on schema analysis.
    
    Analyzes the inspected schema (measures, dimensions, time columns) and suggests
    3-7 business KPIs with complete attribute sets including strategic metadata.
    """
    try:
        logger.info(f"Generating KPI suggestions for {request.data_product_id}")
        
        # Build schema metadata
        schema_metadata = SchemaMetadata(
            data_product_id=request.data_product_id,
            domain=request.domain,
            source_system=request.source_system,
            tables=request.tables,
            database=request.database,
            schema=request.schema,
            measures=request.measures,
            dimensions=request.dimensions,
            time_columns=request.time_columns,
            identifiers=request.identifiers
        )
        
        # Create agent request
        agent_request = KPISuggestionRequest(
            schema_metadata=schema_metadata,
            user_context=request.user_context,
            num_suggestions=request.num_suggestions
        )
        
        # Call agent
        response = await agent.suggest_kpis(agent_request)
        
        return SuggestKPIsAPIResponse(
            status=response.status,
            suggested_kpis=response.suggested_kpis,
            conversation_id=response.conversation_id,
            rationale=response.rationale,
            error=response.error_message if response.status == "error" else None
        )
        
    except Exception as e:
        logger.error(f"Error in suggest_kpis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatAPIResponse)
async def chat(
    request: ChatAPIRequest,
    agent: A9_KPI_Assistant_Agent = Depends(get_kpi_assistant_agent)
) -> ChatAPIResponse:
    """
    Handle conversational KPI refinement.
    
    Accepts natural language requests to customize KPIs, clarify thresholds,
    adjust dimensions, or modify governance mappings.
    """
    try:
        logger.info(f"Processing chat message for conversation {request.conversation_id}")
        
        # Create agent request
        agent_request = KPIChatRequest(
            conversation_id=request.conversation_id,
            message=request.message,
            current_kpis=request.current_kpis
        )
        
        # Call agent
        response = await agent.chat(agent_request)
        
        return ChatAPIResponse(
            status=response.status,
            response=response.response,
            updated_kpis=response.updated_kpis,
            actions=response.actions,
            error=response.error if hasattr(response, 'error') else None
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate", response_model=ValidateKPIAPIResponse)
async def validate_kpi(
    request: ValidateKPIAPIRequest,
    agent: A9_KPI_Assistant_Agent = Depends(get_kpi_assistant_agent)
) -> ValidateKPIAPIResponse:
    """
    Validate a KPI definition against schema and governance rules.
    
    Checks:
    - All required attributes present
    - SQL query valid against schema
    - Strategic metadata tags consistent
    - Dimensions exist in schema
    """
    try:
        logger.info("Validating KPI definition")
        
        # Build schema metadata
        schema_metadata = SchemaMetadata(
            data_product_id=request.data_product_id,
            domain=request.domain,
            source_system=request.source_system,
            measures=request.measures,
            dimensions=request.dimensions,
            time_columns=request.time_columns,
            identifiers=request.identifiers
        )
        
        # Create agent request
        agent_request = KPIValidationRequest(
            kpi_definition=request.kpi_definition,
            schema_metadata=schema_metadata
        )
        
        # Call agent
        response = await agent.validate_kpi(agent_request)
        
        return ValidateKPIAPIResponse(
            status=response.status,
            valid=response.valid,
            errors=response.errors,
            warnings=response.warnings,
            suggestions=response.suggestions,
            error=response.error if hasattr(response, 'error') else None
        )
        
    except Exception as e:
        logger.error(f"Error in validate_kpi endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finalize", response_model=FinalizeKPIsAPIResponse)
async def finalize_kpis(
    request: FinalizeKPIsAPIRequest,
    agent: A9_KPI_Assistant_Agent = Depends(get_kpi_assistant_agent)
) -> FinalizeKPIsAPIResponse:
    """
    Finalize KPIs and update data product contract YAML.
    
    Adds validated KPIs to the data product contract and triggers registry updates.
    """
    try:
        mode_str = "extend" if request.extend_mode else "replace"
        logger.info(f"Finalizing {len(request.kpis)} KPIs for {request.data_product_id} (mode: {mode_str})")
        
        # Create agent request
        agent_request = KPIFinalizeRequest(
            data_product_id=request.data_product_id,
            kpis=request.kpis,
            extend_mode=request.extend_mode
        )
        
        # Call agent
        response = await agent.finalize_kpis(agent_request)
        
        return FinalizeKPIsAPIResponse(
            status=response.status,
            updated_contract_yaml=response.updated_contract_yaml,
            registry_updates=response.registry_updates,
            error=response.error_message if response.status == "error" else None
        )
        
    except Exception as e:
        logger.error(f"Error in finalize_kpis endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {"status": "healthy", "service": "kpi-assistant"}
