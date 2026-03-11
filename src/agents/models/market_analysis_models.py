"""
Pydantic models for the A9_Market_Analysis_Agent.

Defines request/response contracts for market signal retrieval and synthesis.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MarketSignal(BaseModel):
    """A single market signal sourced from external data (e.g. Perplexity web search)."""

    source: str = Field(..., description="Signal source identifier, e.g. 'perplexity', 'news'")
    title: str = Field(..., description="Short headline or title for the signal")
    summary: str = Field(..., description="One or two sentence summary of the signal")
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Relevance of this signal to the KPI context (0–1)"
    )
    published_at: Optional[str] = Field(None, description="ISO date string of publication")
    url: Optional[str] = Field(None, description="Source URL if available")


class MarketAnalysisRequest(BaseModel):
    """
    Request to the A9_Market_Analysis_Agent.

    Callers supply a KPI name plus a short business context string describing the
    observed anomaly so the agent can craft a targeted market-intelligence query.
    """

    session_id: str = Field(..., description="Caller-supplied session identifier")
    kpi_name: str = Field(..., description="Name of the KPI under investigation")
    kpi_context: str = Field(
        ...,
        description="Short description of the KPI anomaly, e.g. 'Gross Margin dropped 2.3pp in lubricants'",
    )
    industry: Optional[str] = Field(
        None, description="Industry segment, e.g. 'lubricants' or 'bicycles'"
    )
    principal_id: Optional[str] = Field(
        None, description="Principal ID of the requesting user"
    )
    max_signals: int = Field(
        default=5, ge=1, le=20, description="Maximum number of market signals to return"
    )


class MarketAnalysisResponse(BaseModel):
    """
    Response from the A9_Market_Analysis_Agent.

    Contains raw signals gathered from external sources plus an LLM-synthesized
    executive narrative explaining what those signals mean for the KPI.
    """

    session_id: str = Field(..., description="Echoed session identifier")
    kpi_name: str = Field(..., description="Echoed KPI name")
    signals: List[MarketSignal] = Field(
        default_factory=list,
        description="Market signals retrieved from external sources",
    )
    synthesis: str = Field(
        ...,
        description="LLM-synthesized executive narrative about external signal impact on this KPI",
    )
    competitor_context: Optional[str] = Field(
        None, description="Additional competitor or benchmarking context if available"
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Agent confidence in the synthesis (0–1)"
    )
    sources_queried: List[str] = Field(
        default_factory=list,
        description="List of source identifiers that were queried",
    )
    error: Optional[str] = Field(None, description="Error message if the agent encountered a failure")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp when this response was generated",
    )
