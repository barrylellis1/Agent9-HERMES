"""
Pydantic models for the Deep Analysis Agent (A2A-compliant).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import Field

from src.agents.shared.a9_agent_base_model import (
    A9AgentBaseModel,
    A9AgentBaseRequest,
    A9AgentBaseResponse,
)


class DeepAnalysisRequest(A9AgentBaseRequest):
    """Request to enumerate, plan, or execute deep analysis for a KPI."""
    kpi_name: str = Field(..., description="Target KPI to analyze")
    timeframe: Optional[str] = Field(None, description="Timeframe token from Decision Studio (e.g., last_quarter)")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional KPI filters")
    target_count: int = Field(5, description="Desired number of top results or dimensions to consider")
    enable_percent_growth: bool = Field(False, description="Whether to compute/display percent growth outputs")
    threshold: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional threshold spec to guide breach detection (e.g., metric: budget|mom, inverse_logic: bool, yellow_threshold: float, budget_version: 'Budget')."
    )


class DeepAnalysisPlan(A9AgentBaseModel):
    """Planned steps for a deep analysis execution."""
    kpi_name: str
    timeframe: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    dimensions: List[str] = Field(default_factory=list, description="Candidate dimensions to analyze (MECE-guided)")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Ordered execution steps for DPA (grouped/timeframe comparisons)")
    notes: Optional[str] = None


class KTIsIsNot(A9AgentBaseModel):
    """Structured KT table representation."""
    what_is: List[Dict[str, Any]] = Field(default_factory=list)
    what_is_not: List[Dict[str, Any]] = Field(default_factory=list)
    where_is: List[Dict[str, Any]] = Field(default_factory=list)
    where_is_not: List[Dict[str, Any]] = Field(default_factory=list)
    when_is: List[Dict[str, Any]] = Field(default_factory=list)
    when_is_not: List[Dict[str, Any]] = Field(default_factory=list)
    extent_is: List[Dict[str, Any]] = Field(default_factory=list)
    extent_is_not: List[Dict[str, Any]] = Field(default_factory=list)


class ChangePoint(A9AgentBaseModel):
    """Detected change-point with pre/post stats."""
    dimension: Optional[str] = None
    key: Optional[str] = None
    timestamp: Optional[str] = None
    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    delta: Optional[float] = None
    percent_growth: Optional[float] = None


class DeepAnalysisResponse(A9AgentBaseResponse):
    """Response containing analysis planning and results."""
    # Planning outputs
    plan: Optional[DeepAnalysisPlan] = None
    dimensions_suggested: List[str] = Field(default_factory=list)

    # Analysis outputs
    scqa_summary: Optional[str] = None
    kt_is_is_not: Optional[KTIsIsNot] = None
    change_points: List[ChangePoint] = Field(default_factory=list)
    timeframe_mapping: Optional[Dict[str, str]] = Field(default=None, description="{'current': 'X', 'previous': 'Y'}")
    percent_growth_enabled: bool = Field(False)

    # Raw data excerpts (optional)
    samples: Optional[Dict[str, Any]] = None
