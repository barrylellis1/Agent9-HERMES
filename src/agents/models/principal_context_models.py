"""
Pydantic models for the Principal Context Agent.

These models define the input/output structures for the Principal Context Agent
following the A2A protocol and Agent9 standards.
"""

from typing import Dict, List, Any, Optional, ForwardRef, TYPE_CHECKING, Union, Annotated
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Import base models first to avoid circular imports
from src.agents.models.situation_awareness_models import (
    PrincipalRole, BusinessProcess, TimeFrame, BaseRequest, BaseResponse
)

# Import PrincipalContext directly to avoid annotation issues with Pydantic v2
from src.agents.models.situation_awareness_models import PrincipalContext

class PrincipalProfileRequest(BaseRequest):
    """Request for principal profile."""
    principal_id: str = Field(description="ID of the principal")
    include_context_history: bool = Field(False, description="Whether to include context history")

class PrincipalProfileResponse(BaseResponse):
    """Response with principal profile."""
    profile: Dict[str, Any] = Field(description="Principal profile")
    responsibilities: List[str] = Field(default_factory=list, description="Business responsibilities")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filter criteria")
    context: Optional[PrincipalContext] = Field(None, description="Principal context object")

class SetPrincipalContextRequest(BaseRequest):
    """Request to set principal context."""
    principal_id: str = Field(description="ID of the principal")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context data")

class SetPrincipalContextResponse(BaseResponse):
    """Response after setting principal context."""
    profile: Dict[str, Any] = Field(description="Updated principal profile")
    responsibilities: List[str] = Field(default_factory=list, description="Business responsibilities")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filter criteria")

class ExtractedFilter(BaseModel):
    """Extracted filter from job description."""
    dimension: str = Field(description="Dimension name (e.g., Region, Product)")
    value: str = Field(description="Filter value")
    confidence: float = Field(description="Confidence score (0-1)")
    
    model_config = ConfigDict(extra="allow")

class ExtractFiltersRequest(BaseRequest):
    """Request to extract filters from job description."""
    job_description: str = Field(description="Job description text")
    
class ExtractFiltersResponse(BaseResponse):
    """Response with extracted filters."""
    extracted_filters: List[ExtractedFilter] = Field(default_factory=list, description="Extracted filters")
    normalized_filters: Dict[str, str] = Field(default_factory=dict, description="Normalized filters as key-value pairs")

# Update forward references after all models are defined
PrincipalProfileResponse.update_forward_refs()
