"""
Pydantic models for the Solution Finder Agent (A2A-compliant).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import Field

from src.agents.shared.a9_agent_base_model import (
    A9AgentBaseModel,
    A9AgentBaseRequest,
    A9AgentBaseResponse,
)


class TradeOffCriterion(A9AgentBaseModel):
    name: str
    weight: float = 1.0


class PerspectiveAnalysis(A9AgentBaseModel):
    lens: str  # "Financial", "Operational", "Strategic", etc.
    arguments_for: List[str] = Field(default_factory=list)
    arguments_against: List[str] = Field(default_factory=list)
    key_questions: List[str] = Field(default_factory=list)


class UnresolvedTension(A9AgentBaseModel):
    tension: str
    options_affected: List[str] = Field(default_factory=list)
    requires: str  # "human judgment", "more data", "stakeholder input"


class SolutionOption(A9AgentBaseModel):
    id: str
    title: str
    description: Optional[str] = None
    expected_impact: Optional[float] = None  # + means beneficial
    cost: Optional[float] = None             # normalized cost estimate
    risk: Optional[float] = None             # normalized risk estimate
    evidence: Optional[List[str]] = None     # URLs/refs or citations
    rationale: Optional[str] = None
    
    # Enhanced Decision Briefing Fields
    time_to_value: Optional[str] = None
    reversibility: Optional[str] = None  # high/medium/low
    perspectives: List[PerspectiveAnalysis] = Field(default_factory=list)
    implementation_triggers: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)


class TradeOffMatrix(A9AgentBaseModel):
    criteria: List[TradeOffCriterion] = Field(default_factory=list)
    options: List[SolutionOption] = Field(default_factory=list)


class PrincipalInputPreferences(A9AgentBaseModel):
    """Optional principal-supplied context to ground analysis."""
    current_priorities: List[str] = Field(default_factory=list)  # e.g., ["cost control", "speed"]
    known_constraints: List[str] = Field(default_factory=list)   # e.g., ["no M&A", "Q4 freeze"]
    questions_to_explore: List[str] = Field(default_factory=list)
    vetoes: List[str] = Field(default_factory=list)              # Options to exclude


class SolutionFinderRequest(A9AgentBaseRequest):
    """Problem intake/evaluation request."""
    problem_statement: Optional[str] = None
    deep_analysis_output: Optional[Dict[str, Any]] = None
    market_analysis_input: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    principal_input: Optional[PrincipalInputPreferences] = None
    evaluation_criteria: Optional[List[TradeOffCriterion]] = None


class SolutionFinderResponse(A9AgentBaseResponse):
    """Ranked options, recommendation, and HITL context."""
    options_ranked: List[SolutionOption] = Field(default_factory=list)
    tradeoff_matrix: Optional[TradeOffMatrix] = None
    recommendation: Optional[SolutionOption] = None
    recommendation_rationale: Optional[str] = None

    # Enhanced Decision Briefing Fields
    problem_reframe: Optional[Dict[str, Any]] = None
    unresolved_tensions: List[UnresolvedTension] = Field(default_factory=list)
    blind_spots: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    cross_review: Optional[Dict[str, Any]] = None  # Hybrid Council debate artifacts

    # Single HITL event fields per PRD
    human_action_required: bool = False
    human_action_type: Optional[str] = None
    human_action_context: Optional[Dict[str, Any]] = None
    human_action_result: Optional[str] = None
    human_action_timestamp: Optional[str] = None

    # Audit
    audit_log: Optional[List[Dict[str, Any]]] = None
