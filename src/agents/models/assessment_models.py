"""
Pydantic models for the enterprise assessment pipeline.

These models represent the data contracts for assessment runs, per-KPI
calibration, and the read-side summary returned by the assessment API.
They map directly to the `assessment_runs` and `kpi_assessments` Supabase
tables.  No agent, registry, or database imports belong here.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AssessmentStatus(str, Enum):
    RUNNING = "running"
    COMPLETE = "complete"
    ERROR = "error"


class KPIAssessmentStatus(str, Enum):
    DETECTED = "detected"
    MONITORING = "monitoring"
    BELOW_THRESHOLD = "below_threshold"
    ERROR = "error"


class ComparisonPeriod(str, Enum):
    MOM = "MoM"
    QOQ = "QoQ"
    YOY = "YoY"


# ---------------------------------------------------------------------------
# Calibration / configuration
# ---------------------------------------------------------------------------

class MonitoringProfile(BaseModel):
    """Per-KPI calibration overrides applied during an assessment run."""

    comparison_period: ComparisonPeriod = Field(
        default=ComparisonPeriod.QOQ,
        description=(
            "The look-back window used to compute the comparison value. "
            "MoM = month-over-month, QoQ = quarter-over-quarter, "
            "YoY = year-over-year."
        ),
    )
    volatility_band: float = Field(
        default=0.05,
        description=(
            "Fractional tolerance band around the comparison value before a "
            "deviation is counted as a breach. E.g. 0.05 = ±5 %."
        ),
    )
    min_breach_duration: int = Field(
        default=1,
        description=(
            "Minimum number of consecutive assessment cycles a KPI must "
            "remain in breach before it is escalated to Deep Analysis."
        ),
    )
    confidence_floor: float = Field(
        default=0.6,
        description=(
            "Minimum confidence score (0.0–1.0) required for a situation "
            "card to be promoted. Detections below this floor are flagged "
            "as monitoring-only."
        ),
    )
    urgency_window_days: int = Field(
        default=14,
        description=(
            "Lookback window in days used to assess whether a KPI trend "
            "is accelerating. Detections within this window receive an "
            "elevated urgency rating."
        ),
    )


class SituationActionType(str, Enum):
    SNOOZE = "snooze"
    DELEGATE = "delegate"
    REQUEST_INFO = "request_info"
    ACKNOWLEDGE = "acknowledge"


class AssessmentConfig(BaseModel):
    """Run-level configuration applied to a single assessment execution."""

    severity_floor: float = Field(
        default=0.3,
        description=(
            "Minimum severity score (0.0–1.0) for a KPI deviation to be "
            "included in the assessment output. Deviations below this "
            "threshold are silently dropped."
        ),
    )
    principal_id: Optional[str] = Field(
        default=None,
        description=(
            "Principal ID for this assessment run. Required — both "
            "principal_id and client_id must be set for a valid run."
        ),
    )
    client_id: Optional[str] = Field(
        default=None,
        description=(
            "Client ID scoping this assessment run (e.g. 'lubricants_inc'). "
            "Required — both principal_id and client_id must be set."
        ),
    )
    dry_run: bool = Field(
        default=False,
        description=(
            "When True the assessment executes all detection logic but "
            "does not persist results or escalate to Deep Analysis."
        ),
    )


# ---------------------------------------------------------------------------
# Persistence models (map to Supabase tables)
# ---------------------------------------------------------------------------

class AssessmentRun(BaseModel):
    """
    Top-level record for a single assessment execution.

    Maps to the `assessment_runs` table.  Counts reflect the state at the
    time the run completes; they are populated by the engine after all
    per-KPI work is finished.
    """

    id: str = Field(
        description="Unique identifier for the assessment run (UUID).",
    )
    started_at: datetime = Field(
        description="UTC timestamp when the assessment run was initiated.",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description=(
            "UTC timestamp when the assessment run finished. None if the "
            "run is still in progress or ended in error before completion."
        ),
    )
    status: AssessmentStatus = Field(
        default=AssessmentStatus.RUNNING,
        description="Current lifecycle status of this assessment run.",
    )
    kpi_count: int = Field(
        default=0,
        description="Total number of KPIs evaluated in this run.",
    )
    kpis_escalated: int = Field(
        default=0,
        description=(
            "Number of KPIs whose severity and confidence exceeded "
            "thresholds and were escalated to Deep Analysis."
        ),
    )
    kpis_monitored: int = Field(
        default=0,
        description=(
            "Number of KPIs that breached a threshold but did not meet "
            "the confidence or severity floor for escalation."
        ),
    )
    kpis_below_threshold: int = Field(
        default=0,
        description="Number of KPIs that showed no breach during this run.",
    )
    kpis_errored: int = Field(
        default=0,
        description=(
            "Number of KPIs where data retrieval or computation failed. "
            "These are logged in the corresponding KPIAssessment records."
        ),
    )
    new_situation_count: int = Field(
        default=0,
        description="Number of situations detected that were not present in the previous run.",
    )
    previous_run_id: Optional[str] = Field(
        default=None,
        description="ID of the immediately preceding completed run for the same principal+client.",
    )
    client_id: Optional[str] = Field(
        default=None,
        description="Client ID this run was scoped to. Denormalised from config for query convenience.",
    )
    config: AssessmentConfig = Field(
        default_factory=AssessmentConfig,
        description="Configuration snapshot used for this assessment run.",
    )


class KPIAssessment(BaseModel):
    """
    Per-KPI result record for a single assessment run.

    Maps to the `kpi_assessments` table.  One row is written per KPI per
    run regardless of outcome so that the full picture is auditable.
    """

    id: str = Field(
        description="Unique identifier for this KPI assessment row (UUID).",
    )
    run_id: str = Field(
        description="Foreign key reference to the parent AssessmentRun.id.",
    )
    kpi_id: str = Field(
        description="Registry identifier of the KPI being assessed.",
    )
    kpi_name: Optional[str] = Field(
        default=None,
        description="Human-readable display name of the KPI.",
    )
    kpi_value: Optional[float] = Field(
        default=None,
        description=(
            "Most-recent observed value for the KPI at the time of "
            "assessment. None when data retrieval failed."
        ),
    )
    comparison_value: Optional[float] = Field(
        default=None,
        description=(
            "Reference value derived from the MonitoringProfile "
            "comparison_period (e.g. prior-quarter average). None when "
            "data retrieval failed."
        ),
    )
    severity: Optional[float] = Field(
        default=None,
        description=(
            "Normalised severity score in [0.0, 1.0]. Higher values "
            "indicate a more significant deviation. None on error."
        ),
    )
    confidence: Optional[float] = Field(
        default=None,
        description=(
            "Detection confidence score in [0.0, 1.0]. Reflects data "
            "quality, signal consistency, and sample size. None on error."
        ),
    )
    status: KPIAssessmentStatus = Field(
        description="Outcome classification for this individual KPI.",
    )
    escalated_to_da: bool = Field(
        default=False,
        description=(
            "True when this KPI assessment was submitted to the Deep "
            "Analysis agent for dimensional drill-down."
        ),
    )
    da_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Serialised Deep Analysis response payload. Populated only "
            "when escalated_to_da is True and the DA agent has returned "
            "a result."
        ),
    )
    benchmark_segments: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description=(
            "BenchmarkSegment dicts returned by the DA agent's Is/Is Not "
            "classification. Used downstream for DiD control-group "
            "attribution in Value Assurance."
        ),
    )
    error_message: Optional[str] = Field(
        default=None,
        description=(
            "Human-readable description of the failure when status is "
            "KPIAssessmentStatus.ERROR. None for successful assessments."
        ),
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when this KPI assessment row was created.",
    )


# ---------------------------------------------------------------------------
# API read model
# ---------------------------------------------------------------------------

class AssessmentSummary(BaseModel):
    """
    Composite read model returned by the assessment summary API endpoint.

    Combines the top-level AssessmentRun with all child KPIAssessment
    records and exposes two computed properties for convenient filtering.
    """

    run: AssessmentRun = Field(
        description="The parent assessment run record.",
    )
    assessments: List[KPIAssessment] = Field(
        description="All KPI assessment records belonging to this run.",
    )

    @property
    def escalated(self) -> List[KPIAssessment]:
        """KPI assessments that were escalated to Deep Analysis."""
        return [a for a in self.assessments if a.escalated_to_da]

    @property
    def monitoring(self) -> List[KPIAssessment]:
        """KPI assessments held at monitoring level (not yet escalated)."""
        return [
            a for a in self.assessments
            if a.status == KPIAssessmentStatus.MONITORING
        ]


# ---------------------------------------------------------------------------
# Situation action model (maps to situation_actions table)
# ---------------------------------------------------------------------------

class SituationAction(BaseModel):
    """
    Records a principal action taken on a detected situation.

    Maps to the `situation_actions` table.  One row per action — a situation
    may have multiple actions over time (e.g. snoozed then re-acknowledged).
    """

    id: str = Field(
        default_factory=lambda: str(__import__("uuid").uuid4()),
        description="Unique identifier for this action record (UUID).",
    )
    situation_id: str = Field(
        description="SA situation_id or kpi_name used as the situation key.",
    )
    kpi_assessment_id: Optional[str] = Field(
        default=None,
        description="FK to kpi_assessments.id for the related assessment row.",
    )
    run_id: Optional[str] = Field(
        default=None,
        description="FK to assessment_runs.id — the run that surfaced this situation.",
    )
    principal_id: str = Field(
        description="Principal who took the action.",
    )
    action_type: SituationActionType = Field(
        description="Type of action taken.",
    )
    target_principal_id: Optional[str] = Field(
        default=None,
        description="Target principal for delegate actions.",
    )
    snooze_expires_at: Optional[datetime] = Field(
        default=None,
        description="Expiry timestamp for snooze actions.",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Optional principal note or context for this action.",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when this action was recorded.",
    )
