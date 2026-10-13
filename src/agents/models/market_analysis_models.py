"""
Pydantic models for the A9_Market_Analysis_Agent.

Defines request/response contracts for market signal retrieval and synthesis.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

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
    request_id: Optional[str] = Field(
        None,
        description=(
            "The DA run's own request_id (DeepAnalysisResponse.request_id) when MA is "
            "invoked from the DA->MA integration call -- NOT the outer workflow-tracking "
            "id (those differ: execute_deep_analysis mints its own internally). Passing "
            "DA's id here lets reliability.citation_quality (2026-10-02) correlate to the "
            "same run as DA's own reliability.rollup_check events, so a per-run reliability "
            "view can show both. None for callers outside that integration (e.g. company-"
            "profile's industry-research endpoint) -- the event is simply written without "
            "a request_id in that case, same posture as client_id above."
        ),
    )
    client_id: Optional[str] = Field(
        None,
        description=(
            "Tenant this request belongs to. Optional because not every caller has one "
            "(e.g. company-profile's industry-research endpoint, run before a client_id "
            "exists) -- but when present it scopes the reliability.citation_quality audit "
            "event (2026-10-02); a caller that omits it simply gets no event, matching "
            "every other reliability signal's own missing-client_id behavior."
        ),
    )
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
    general_deviation: Optional[str] = Field(
        None,
        description=(
            "Set when Deep Analysis found no IS NOT: every segment is off, so the cause is "
            "common to all (src/analysis/deviation_scope.py). The reader's sentence describing "
            "that. Used at SYNTHESIS only, to ask whether the signals support a market-level "
            "shift. Never used to fetch signals: same conclusion firewall as analysis_mode."
        ),
    )
    analysis_mode: Optional[str] = Field(
        None,
        description="DA-determined analysis mode ('problem'|'opportunity'|'mixed') — used to detect signal conflicts"
    )
    business_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Full enterprise business context (industry, subindustry, products_services, regions, etc.) to focus signal generation"
    )
    da_structural_context: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Structural facts from Deep Analysis — dimension names analyzed, key segment values, "
            "change-point segments. Passed to signal generation to make signals business-specific "
            "WITHOUT revealing the DA conclusion (no analysis_mode or scqa here)."
        )
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
    market_shift: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Answer to the confirming question asked when Deep Analysis found the gap is general "
            "(no IS NOT): do the external signals support a market-level shift? assessment "
            "('supported'|'not_supported'|'insufficient'), confidence (0-1), summary (str), and "
            "grounded (bool: at least one signal carries a real source URL). None when the "
            "question was not asked."
        ),
    )
    conflict: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Conflict assessment produced by the LLM: detected (bool), type "
            "('headwind_vs_opportunity'|'tailwind_vs_problem'|null), confidence (0–1), summary (str)"
        )
    )
    error: Optional[str] = Field(None, description="Error message if the agent encountered a failure")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="ISO timestamp when this response was generated",
    )
