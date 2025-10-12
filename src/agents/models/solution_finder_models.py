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


class SolutionOption(A9AgentBaseModel):
    id: str
    title: str
    description: Optional[str] = None
    expected_impact: Optional[float] = None  # + means beneficial
    cost: Optional[float] = None             # normalized cost estimate
    risk: Optional[float] = None             # normalized risk estimate
    evidence: Optional[List[str]] = None     # URLs/refs or citations
    rationale: Optional[str] = None


class TradeOffMatrix(A9AgentBaseModel):
    criteria: List[TradeOffCriterion] = Field(default_factory=list)
    options: List[SolutionOption] = Field(default_factory=list)


class SolutionFinderRequest(A9AgentBaseRequest):
    """Problem intake/evaluation request."""
    problem_statement: Optional[str] = None
    deep_analysis_output: Optional[Dict[str, Any]] = None
    market_analysis_input: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    evaluation_criteria: Optional[List[TradeOffCriterion]] = None


class SolutionFinderResponse(A9AgentBaseResponse):
    """Ranked options, recommendation, and HITL context."""
    options_ranked: List[SolutionOption] = Field(default_factory=list)
    tradeoff_matrix: Optional[TradeOffMatrix] = None
    recommendation: Optional[SolutionOption] = None
    recommendation_rationale: Optional[str] = None

    # Single HITL event fields per PRD
    human_action_required: bool = False
    human_action_type: Optional[str] = None
    human_action_context: Optional[Dict[str, Any]] = None
    human_action_result: Optional[str] = None
    human_action_timestamp: Optional[str] = None

    # Audit
    audit_log: Optional[List[Dict[str, Any]]] = None
