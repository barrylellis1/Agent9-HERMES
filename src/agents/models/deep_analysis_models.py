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
    when_started: Optional[str] = Field(default=None, description="Earliest time bucket when the issue began (e.g., '2025-08')")
    percent_growth_enabled: bool = Field(False)

    # Raw data excerpts (optional)
    samples: Optional[Dict[str, Any]] = None


# ============================================================================
# Problem Refinement Chat Models (MBB-Style Principal Engagement)
# ============================================================================

class RefinementExclusion(A9AgentBaseModel):
    """A dimension/value exclusion specified by the principal."""
    dimension: str = Field(..., description="Dimension name (e.g., 'Profit Center')")
    value: str = Field(..., description="Value to exclude (e.g., 'Mountain Cycles')")
    reason: Optional[str] = Field(None, description="Principal's reason for exclusion")


class ProblemRefinementInput(A9AgentBaseModel):
    """Input for problem refinement chat."""
    deep_analysis_output: Dict[str, Any] = Field(..., description="KT IS/IS-NOT results from execute_deep_analysis")
    principal_context: Dict[str, Any] = Field(..., description="Role, decision_style, filters from principal profile")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Multi-turn chat history")
    user_message: Optional[str] = Field(None, description="Latest principal response")
    current_topic: Optional[str] = Field(None, description="Current topic in sequence (auto-managed)")
    turn_count: int = Field(0, description="Current turn number (auto-managed)")


class ExtractedRefinements(A9AgentBaseModel):
    """Refinements extracted from a single turn."""
    exclusions: List[RefinementExclusion] = Field(default_factory=list)
    external_context: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    validated_hypotheses: List[str] = Field(default_factory=list)
    invalidated_hypotheses: List[str] = Field(default_factory=list)


class ProblemRefinementResult(A9AgentBaseModel):
    """Output from problem refinement chat."""
    # Chat response
    agent_message: str = Field(..., description="Next question or acknowledgment")
    suggested_responses: List[str] = Field(default_factory=list, description="Quick-select options for UI")
    
    # Accumulated refinements (across all turns)
    exclusions: List[RefinementExclusion] = Field(default_factory=list)
    external_context: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    validated_hypotheses: List[str] = Field(default_factory=list)
    invalidated_hypotheses: List[str] = Field(default_factory=list)
    
    # Topic tracking
    current_topic: str = Field(..., description="Current topic being discussed")
    topic_complete: bool = Field(False, description="Whether current topic is sufficiently covered")
    topics_completed: List[str] = Field(default_factory=list, description="Topics already covered")
    
    # Handoff readiness
    ready_for_solutions: bool = Field(False, description="Principal approved refinement, ready for Solution Finder")
    refined_problem_statement: Optional[str] = Field(None, description="Sharpened problem statement for Solution Finder")
    
    # Solution Council routing
    recommended_council_type: Optional[str] = Field(None, description="strategic/operational/technical/innovation/financial")
    council_routing_rationale: Optional[str] = Field(None, description="Why this council type was recommended")
    
    # Diverse Council recommendation (one from each category: MBB, Big4, Technology, Risk)
    recommended_council_members: Optional[List[Dict[str, str]]] = Field(
        None, 
        description="Recommended diverse council: [{category, persona_id, persona_name, rationale}]"
    )
    
    # Conversation state
    turn_count: int = Field(0, description="Current turn number")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Full conversation history")
