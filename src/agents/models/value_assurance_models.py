"""
Pydantic models for Value Assurance — Initiative Tracking / Proven ROI (Pillar 5).

Phase 7A: full PRD model set with counterfactual attribution, strategy alignment,
composite verdict, and portfolio summary.

Legacy models (SolutionStatus, UpdateAcceptedSolutionRequest,
ValueAssuranceCheckRequest, ValueAssuranceCheckResponse) are preserved at the
bottom so the existing /api/v1/value-assurance routes continue to work unchanged.

The alias CreateAcceptedSolutionRequest is intentionally NOT applied to
RegisterSolutionRequest here so that the old API route (which creates solutions
with legacy fields like session_id / kpi_name / option_title) keeps importing
the legacy shape.  The canonical Phase 7A entry-point is RegisterSolutionRequest.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Phase 7A enums
# ---------------------------------------------------------------------------

class SolutionVerdict(str, Enum):
    VALIDATED = "VALIDATED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    MEASURING = "MEASURING"


class SolutionPhase(str, Enum):
    """5-phase lifecycle tracking, independent of verdict (SolutionVerdict)."""
    APPROVED = "APPROVED"          # Decision recorded, not yet started
    IMPLEMENTING = "IMPLEMENTING"  # Solution being built/deployed
    LIVE = "LIVE"                  # Solution deployed, measurement begins
    MEASURING = "MEASURING"        # DiD attribution running
    COMPLETE = "COMPLETE"          # Verdict rendered


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class StrategyAlignment(str, Enum):
    ALIGNED = "ALIGNED"
    DRIFTED = "DRIFTED"
    SUPERSEDED = "SUPERSEDED"


# ---------------------------------------------------------------------------
# Phase 7A core models
# ---------------------------------------------------------------------------

class StrategySnapshot(BaseModel):
    """Captures the strategic context at the moment a solution is approved."""
    principal_priorities: List[str]
    principal_role: str
    business_process_domain: str
    data_product_id: str
    kpi_threshold_at_approval: float
    key_assumptions: List[str]
    business_context_name: str
    strategic_rationale: Optional[str] = None
    captured_at: str  # ISO datetime string


class StrategyAlignmentCheck(BaseModel):
    """Result of comparing the strategy snapshot against current registry state."""
    original_priorities: List[str]
    current_priorities: List[str]
    priority_drift: bool
    priority_overlap: float  # 0.0–1.0
    kpi_still_monitored: bool
    threshold_changed: bool
    current_threshold: Optional[float] = None
    business_process_active: bool
    data_product_active: bool
    principal_still_accountable: bool
    current_principal_id: Optional[str] = None
    alignment_verdict: StrategyAlignment
    drift_factors: List[str]
    drift_summary: Optional[str] = None


class CompositeVerdict(BaseModel):
    """
    Combined KPI-outcome × strategy-alignment verdict.

    composite_label examples:
        "Full success", "Misdirected win", "Obsolete win",
        "Work in progress", "Partial misdirection", "Acceptable loss",
        "Failure", "Strategic waste", "Irrelevant failure"
    """
    kpi_verdict: SolutionVerdict
    strategy_verdict: StrategyAlignment
    composite_label: str
    include_in_roi_totals: bool
    recommended_action: str
    executive_attention_required: bool


class ImpactEvaluation(BaseModel):
    """Difference-in-Differences attribution result for a single solution."""
    solution_id: str
    baseline_kpi_value: float
    current_kpi_value: float
    total_kpi_change: float
    control_group_change: float
    market_driven_recovery: float
    seasonal_component: float
    attributable_impact: float
    expected_impact_lower: float
    expected_impact_upper: float
    verdict: SolutionVerdict
    confidence: ConfidenceLevel
    confidence_rationale: str
    attribution_method: str
    control_group_description: Optional[str] = None
    market_context_summary: Optional[str] = None
    strategy_check: StrategyAlignmentCheck
    composite_verdict: CompositeVerdict
    evaluated_at: str  # ISO datetime string


class InactionCostProjection(BaseModel):
    """Forward projection of KPI trajectory if no action had been taken."""
    solution_id: str
    kpi_id: str
    current_kpi_value: float
    projected_kpi_value_30d: float
    projected_kpi_value_90d: float
    estimated_revenue_impact_30d: Optional[float] = None
    estimated_revenue_impact_90d: Optional[float] = None
    trend_direction: str  # "deteriorating" | "stable" | "recovering"
    trend_confidence: ConfidenceLevel
    projection_method: str
    projected_at: str


class AcceptedSolution(BaseModel):
    """
    Full lifecycle record for a human-approved solution recommendation.

    Phase 7A model with strategy snapshot, attribution evaluation, inaction cost,
    and composite verdict.  Phase 7C adds three-trajectory tracking arrays and
    benchmark segment storage for future DiD control-group attribution.
    """
    solution_id: str
    situation_id: str
    kpi_id: str
    principal_id: str
    client_id: Optional[str] = None
    approved_at: str
    solution_description: str
    expected_impact_lower: float
    expected_impact_upper: float
    measurement_window_days: int = 30
    status: SolutionVerdict = SolutionVerdict.MEASURING
    phase: SolutionPhase = SolutionPhase.APPROVED
    go_live_at: Optional[str] = None       # ISO datetime — principal confirms deployment
    completed_at: Optional[str] = None     # ISO datetime — verdict rendered
    strategy_snapshot: StrategySnapshot
    impact_evaluation: Optional[ImpactEvaluation] = None
    inaction_cost: Optional[InactionCostProjection] = None
    narrative: Optional[str] = None
    ma_market_signals: Optional[List[str]] = None     # market context at approval
    # Phase 7C: Benchmark segments from DA's Is/Is Not classification
    control_group_segments: Optional[List[dict]] = None  # BenchmarkSegment dicts (type=control_group)
    benchmark_segments: Optional[List[dict]] = None       # All BenchmarkSegment dicts
    # Phase 7C: Three-trajectory tracking arrays
    inaction_trend: List[float] = Field(default_factory=list)   # monthly projected values if no action (longer horizon)
    expected_trend: List[float] = Field(default_factory=list)   # monthly projected values if solution works
    inaction_horizon_months: int = 0                             # max(window_months * 2, 12)
    actual_trend: List[float] = Field(default_factory=list)     # actual KPI values post-approval
    actual_trend_dates: List[str] = Field(default_factory=list) # ISO dates of each measurement
    baseline_kpi_value: float = 0.0
    pre_approval_slope: float = 0.0  # KPI change per month before approval


# ---------------------------------------------------------------------------
# Phase 7A request / response models
# ---------------------------------------------------------------------------

class RegisterSolutionRequest(BaseModel):
    request_id: str
    principal_id: str
    situation_id: str
    kpi_id: str
    solution_description: str
    expected_impact_lower: float
    expected_impact_upper: float
    measurement_window_days: int = 30
    client_id: Optional[str] = None
    ma_market_signals: Optional[List[str]] = None
    strategy_snapshot: Optional[StrategySnapshot] = None
    # Phase 7C: full BenchmarkSegment objects from DA
    control_group_segments: Optional[List[dict]] = None  # BenchmarkSegment dicts (type=control_group)
    benchmark_segments: Optional[List[dict]] = None       # All BenchmarkSegment dicts
    pre_approval_kpi_value: Optional[float] = None        # comparison-period KPI value for slope calc


class RegisterSolutionResponse(BaseModel):
    solution_id: str
    status: SolutionVerdict
    phase: SolutionPhase = SolutionPhase.APPROVED
    message: str


class UpdateSolutionPhaseRequest(BaseModel):
    """Advance a solution through the lifecycle: APPROVED → IMPLEMENTING → LIVE → MEASURING → COMPLETE."""
    request_id: str
    principal_id: str
    solution_id: str
    new_phase: SolutionPhase
    notes: Optional[str] = None


class UpdateSolutionPhaseResponse(BaseModel):
    solution_id: str
    phase: SolutionPhase
    message: str


class EvaluateSolutionRequest(BaseModel):
    request_id: str
    principal_id: str
    solution_id: str
    current_kpi_value: float
    control_group_kpi_values: Optional[List[float]] = None
    market_recovery_estimate: Optional[float] = None
    seasonal_estimate: Optional[float] = None


class EvaluateSolutionResponse(BaseModel):
    solution_id: str
    evaluation: ImpactEvaluation


class CheckStrategyAlignmentRequest(BaseModel):
    request_id: str
    principal_id: str
    solution_id: str


class CheckStrategyAlignmentResponse(BaseModel):
    solution_id: str
    alignment: StrategyAlignmentCheck
    composite: CompositeVerdict


class ProjectInactionCostRequest(BaseModel):
    request_id: str
    principal_id: str
    situation_id: str
    kpi_id: str
    current_kpi_value: float
    historical_trend: List[float]  # recent KPI values for trend fitting


class ProjectInactionCostResponse(BaseModel):
    projection: InactionCostProjection


class PortfolioSummaryRequest(BaseModel):
    request_id: str
    principal_id: str
    include_superseded: bool = False
    client_id: Optional[str] = None


class StrategyAwarePortfolio(BaseModel):
    total_solutions: int
    validated_count: int
    partial_count: int
    failed_count: int
    measuring_count: int
    total_attributable_impact: float
    roi_eligible_solutions: int  # include_in_roi_totals = True
    strategy_aligned_count: int
    strategy_drifted_count: int
    strategy_superseded_count: int
    executive_attention_required: List[str]  # solution_ids
    solutions: List[AcceptedSolution]


class RecordKPIMeasurementRequest(BaseModel):
    """Append a monthly KPI measurement to a solution's actual_trend."""
    request_id: str
    principal_id: str
    solution_id: str
    kpi_value: float
    measured_at: Optional[str] = None  # ISO datetime; defaults to now


class RecordKPIMeasurementResponse(BaseModel):
    solution_id: str
    actual_trend: List[float]
    actual_trend_dates: List[str]
    message: str


class GenerateNarrativeRequest(BaseModel):
    request_id: str
    principal_id: str
    solution_id: str


class GenerateNarrativeResponse(BaseModel):
    solution_id: str
    narrative: str


# ---------------------------------------------------------------------------
# Legacy models — kept intact so the existing /api/v1/value-assurance routes
# continue to work without modification.
# ---------------------------------------------------------------------------

class SolutionStatus(str, Enum):
    ACCEPTED = "accepted"
    IMPLEMENTING = "implementing"
    MEASURING = "measuring"
    VALIDATED = "validated"
    FAILED = "failed"
    ABANDONED = "abandoned"


class LegacyAcceptedSolution(BaseModel):
    """Legacy AcceptedSolution shape used by the existing API routes."""

    id: Optional[str] = None
    session_id: str
    principal_id: str
    kpi_name: str
    option_title: str
    option_description: str
    expected_impact: Optional[str] = None
    expected_impact_lower: Optional[float] = None
    expected_impact_upper: Optional[float] = None
    status: SolutionStatus = SolutionStatus.ACCEPTED
    accepted_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    implementation_start: Optional[str] = None
    measurement_start: Optional[str] = None
    resolved_at: Optional[str] = None
    actual_impact: Optional[float] = None
    notes: Optional[str] = None


class CreateAcceptedSolutionRequest(BaseModel):
    """API request to record a newly approved solution (legacy route)."""

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
    """API request to update mutable fields on an accepted solution (legacy route)."""

    status: Optional[SolutionStatus] = None
    actual_impact: Optional[float] = None
    notes: Optional[str] = None
    implementation_start: Optional[str] = None
    measurement_start: Optional[str] = None


class ListAcceptedSolutionsResponse(BaseModel):
    """List of accepted solutions with total count (legacy route)."""

    solutions: List[LegacyAcceptedSolution]
    total: int


class ValueAssuranceCheckRequest(BaseModel):
    """Request to check whether an accepted solution has delivered results (legacy route)."""

    accepted_solution_id: str
    current_kpi_value: float
    baseline_kpi_value: float
    measurement_date: str


class ValueAssuranceCheckResponse(BaseModel):
    """Result of a value assurance check (legacy route)."""

    accepted_solution_id: str
    kpi_name: str
    expected_impact_lower: Optional[float]
    expected_impact_upper: Optional[float]
    actual_delta: float
    within_expected_range: bool
    status: SolutionStatus
    message: str
