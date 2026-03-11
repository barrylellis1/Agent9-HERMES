"""
Pydantic models for Value Assurance — Initiative Tracking / Proven ROI (Pillar 5).

Tracks whether accepted AI recommendations (from Solution Finder HITL approval)
actually delivered measurable business results against expected KPI outcomes.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class SolutionStatus(str, Enum):
    ACCEPTED = "accepted"          # HITL approved, implementation pending
    IMPLEMENTING = "implementing"  # In progress
    MEASURING = "measuring"        # Implemented, tracking outcomes
    VALIDATED = "validated"        # Outcome confirmed positive
    FAILED = "failed"              # Outcome did not materialize
    ABANDONED = "abandoned"        # Cancelled before measurement


class AcceptedSolution(BaseModel):
    """Tracks a human-approved recommendation from Solution Finder."""

    id: Optional[str] = None  # UUID, set on insert
    session_id: str
    principal_id: str
    kpi_name: str
    option_title: str
    option_description: str
    expected_impact: Optional[str] = None          # e.g. "2.1–3.4pp Gross Margin recovery"
    expected_impact_lower: Optional[float] = None  # numeric lower bound
    expected_impact_upper: Optional[float] = None  # numeric upper bound
    status: SolutionStatus = SolutionStatus.ACCEPTED
    accepted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    implementation_start: Optional[str] = None
    measurement_start: Optional[str] = None
    resolved_at: Optional[str] = None
    actual_impact: Optional[float] = None  # measured KPI delta
    notes: Optional[str] = None


class CreateAcceptedSolutionRequest(BaseModel):
    """API request to record a newly approved solution."""

    session_id: str
    principal_id: str
    kpi_name: str
    option_title: str
    option_description: str
    expected_impact: Optional[str] = None
    expected_impact_lower: Optional[float] = None
    expected_impact_upper: Optional[float] = None
    notes: Optional[str] = None


class UpdateAcceptedSolutionRequest(BaseModel):
    """API request to update mutable fields on an accepted solution."""

    status: Optional[SolutionStatus] = None
    actual_impact: Optional[float] = None
    notes: Optional[str] = None
    implementation_start: Optional[str] = None
    measurement_start: Optional[str] = None


class ListAcceptedSolutionsResponse(BaseModel):
    """List of accepted solutions with total count."""

    solutions: List[AcceptedSolution]
    total: int


class ValueAssuranceCheckRequest(BaseModel):
    """Request to check whether an accepted solution has delivered results."""

    accepted_solution_id: str
    current_kpi_value: float
    baseline_kpi_value: float
    measurement_date: str


class ValueAssuranceCheckResponse(BaseModel):
    """Result of a value assurance check."""

    accepted_solution_id: str
    kpi_name: str
    expected_impact_lower: Optional[float]
    expected_impact_upper: Optional[float]
    actual_delta: float       # current_kpi_value - baseline_kpi_value
    within_expected_range: bool
    status: SolutionStatus
    message: str
