"""
Pydantic models for the A9 NLP Interface Agent protocol.
This module defines request/response models for:
- parse_business_query
- entity_extraction (MVP core)

Models are business-level only. Business-to-technical translation is handled by the
Data Governance Agent (DGA). SQL/timeframe enforcement is handled by the
Data Product Agent (DPA).
"""
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class TopNSpec(BaseModel):
    """Represents Top/Bottom N intent extracted from NLQ."""
    limit_type: Literal["top", "bottom"] = Field(..., description="Top or Bottom")
    limit_n: int = Field(..., description="N to return")
    limit_field: Optional[str] = Field(
        None, description="Field to rank by (e.g., 'revenue' or 'margin')"
    )


class TimeFilterSpec(BaseModel):
    """Normalized timeframe hint. Concrete date logic is handled by DPA."""
    expression: str = Field(
        ..., description="Normalized timeframe (e.g., 'current', 'last_quarter', 'ytd')"
    )
    granularity: Optional[Literal["year", "quarter", "month", "week", "day"]] = Field(
        None, description="Optional hint for downstream handling"
    )


class MatchedView(BaseModel):
    """
    Candidate interpretation of a business query.
    Uses business-level dimensions/filters; DGA will translate later.
    """
    kpi_name: str = Field(..., description="Resolved KPI name (from KPI registry; synonym aware)")
    data_product_id: Optional[str] = Field(
        None, description="Resolved data product id (if identified)"
    )
    view_name: Optional[str] = Field(None, description="Resolved view name (if identified)")
    groupings: List[str] = Field(
        default_factory=list, description="Business-level dimensions to group by"
    )
    time_filter: Optional[TimeFilterSpec] = Field(
        None, description="Normalized timeframe intent"
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Business-level filters; DGA will translate keys/values",
    )


class NLPBusinessQueryInput(BaseModel):
    """Input for parse_business_query. Either query or business_terms must be provided."""
    query: Optional[str] = Field(
        None, description="Natural language question, e.g. 'top 5 regions by revenue in 2024'"
    )
    business_terms: Optional[List[str]] = Field(
        None, description="Tokenized/phrase-based form of the request"
    )
    principal_context: Optional[Dict[str, Any]] = Field(
        None, description="Principal defaults (filters/timeframes) from orchestrator"
    )
    kpi_hints: Optional[List[str]] = Field(
        None, description="Optional KPI candidates to bias resolution"
    )
    hitl_enabled: bool = Field(False, description="Enable HITL escalation in pipeline")

    model_config = {
        "extra": "ignore"
    }


class NLPBusinessQueryResult(BaseModel):
    """Output for parse_business_query."""
    matched_views: List[MatchedView] = Field(
        default_factory=list, description="Candidate interpretations"
    )
    unmapped_terms: List[str] = Field(
        default_factory=list, description="Terms not mapped during parsing"
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Business-level filters produced by parsing; DGA will translate",
    )
    topn: Optional[TopNSpec] = Field(None, description="Top/Bottom N intent if present")
    principal_context: Dict[str, Any] = Field(
        default_factory=dict, description="Context used while parsing"
    )

    # HITL protocol fields
    human_action_required: bool = Field(
        False, description="If True, prompt for clarification"
    )
    human_action_type: Optional[str] = Field(
        None, description="Type of action (e.g., 'clarification')"
    )
    human_action_context: Optional[Dict[str, Any]] = Field(
        None, description="Details for user triage (e.g., unmapped terms)"
    )


class ExtractedEntity(BaseModel):
    """Represents a detected entity in the input text."""
    type: str = Field(..., description="Entity type (e.g., 'region', 'product', 'date')")
    value: str = Field(..., description="Canonical or surface form")
    start_char: Optional[int] = Field(None, description="Start index in text")
    end_char: Optional[int] = Field(None, description="End index in text")
    confidence: Optional[float] = Field(None, description="0.0 - 1.0")


class EntityExtractionInput(BaseModel):
    """Input for entity_extraction (MVP core)."""
    text: str = Field(..., description="Input text to extract entities from")
    principal_context: Optional[Dict[str, Any]] = Field(
        None, description="Optional context used for normalization"
    )
    allowed_types: Optional[List[str]] = Field(
        None, description="Restrict extraction to these types if provided"
    )
    hitl_enabled: bool = Field(False, description="Enable HITL escalation on ambiguity")


class EntityExtractionResult(BaseModel):
    """Output for entity_extraction."""
    entities: List[ExtractedEntity] = Field(
        default_factory=list, description="Extracted entities"
    )
    unmapped_terms: List[str] = Field(
        default_factory=list, description="Terms not mapped to known entities"
    )

    # HITL protocol fields
    human_action_required: bool = Field(
        False, description="If True, prompt for clarification"
    )
    human_action_type: Optional[str] = Field(
        None, description="Type of action (e.g., 'clarification')"
    )
    human_action_context: Optional[Dict[str, Any]] = Field(
        None, description="Details for user triage (e.g., conflicting candidates)"
    )
