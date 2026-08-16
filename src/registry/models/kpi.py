"""
KPI Models

Defines the data structures for KPIs in the registry system.
This replaces the enum-based approach with a flexible, data-driven model.
"""

import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class ComparisonType(str, Enum):
    """Types of comparisons supported for KPIs."""
    QOQ = "qoq"  # Quarter over Quarter
    YOY = "yoy"  # Year over Year
    MOM = "mom"  # Month over Month
    TARGET = "target"  # Against Target
    BUDGET = "budget"  # Against Budget
    PLAN_VARIANCE = "plan_variance"  # Actual vs Budget/Plan — tolerance bands for 11I-A detection
    PROJECTED_BREACH = "projected_breach"  # Absolute native-unit floor/ceiling for trend-projection breach (11I-A)
    ACCELERATION = "acceleration"  # Volatility-normalised sensitivity for deterioration-acceleration (11I-A)
    GREATER_THAN = "greater_than"  # Simple threshold check >
    LESS_THAN = "less_than"  # Simple threshold check <


class KPIEvaluationStatus(str, Enum):
    """Possible evaluation statuses for KPIs."""
    GREEN = "green"  # Performing well
    YELLOW = "yellow"  # Warning/needs attention
    RED = "red"  # Critical/not meeting expectations
    NEUTRAL = "neutral"  # Neutral or informational only
    UNKNOWN = "unknown"  # Not enough data to evaluate


class KPIThreshold(BaseModel):
    """
    Thresholds for determining KPI status.
    
    These thresholds define the boundaries for evaluating a KPI
    as green (good), yellow (warning), or red (critical).
    """
    
    comparison_type: ComparisonType = Field(..., description="Type of comparison")
    green_threshold: Optional[float] = Field(None, description="Threshold for green status")
    yellow_threshold: Optional[float] = Field(None, description="Threshold for yellow status")
    red_threshold: Optional[float] = Field(None, description="Threshold for red status")
    inverse_logic: bool = Field(False, description="If True, lower values are better")


class KPIDimension(BaseModel):
    """
    Dimension for analyzing a KPI.
    
    Dimensions represent different ways to slice and analyze a KPI,
    such as by region, product, customer segment, etc.
    """
    
    name: str = Field(..., description="Name of the dimension")
    field: str = Field(..., description="Field name in the data")
    values: List[str] = Field(default_factory=list, description="Possible values for this dimension")
    description: Optional[str] = Field(None, description="Description of the dimension")


class KPIMonitoringProfile(BaseModel):
    """Per-KPI calibration parameters for the Enterprise Assessment Engine.

    Controls how SA evaluates breach significance before deciding whether to
    escalate to Deep Analysis. Set by KPI Assistant (Phase 9F) from historical
    volatility analysis; defaults apply until calibrated.
    """
    comparison_period: str = Field("QoQ", description="Comparison cadence: 'MoM', 'QoQ', or 'YoY'.")
    volatility_band: float = Field(0.05, ge=0.0, le=1.0, description="Fractional band (e.g. 0.05 = ±5%). Breach must exceed this to be significant.")
    min_breach_duration: int = Field(1, ge=1, description="Consecutive periods in breach before SA escalates.")
    confidence_floor: float = Field(0.6, ge=0.0, le=1.0, description="Minimum SA confidence to escalate to DA; below this → 'monitoring' status.")
    urgency_window_days: int = Field(14, ge=1, description="SLA window in days for this KPI type.")


class NotSliceableByEntry(BaseModel):
    """One denied (KPI x dimension) cut. docs/architecture/kpi_semantic_contract.md §4.

    Two independent axes, not one — collapsing them into a plain dimension
    name (the original shape of this field) defeats the reason a deny list
    is safer than an allow list at all: §4.6 calls a deny list "a place to
    hide bugs" unless reason_class distinguishes a permanent fact from a
    fixable data gap.

    - `reason_class`: 'structural' = a permanent fact about how THIS
      CLIENT's business data works (e.g. COGS booked at product level, not
      customer level) — declare once, deny forever, nothing to fix.
      'pipeline_gap' = the data SHOULD reach this grain and doesn't — a
      genuine completeness gap in the CLIENT's own source system/ETL, not a
      permanent fact about their business. NOT an Agent9 code defect —
      Agent9 does not own the client's warehouse pipeline and cannot fix
      this by writing code. Worth surfacing as a known data-quality finding
      to whoever DOES own that pipeline (the client's data team, or
      Agent9's onboarding/implementation function for that account), not
      left to sit silently mislabeled as a permanent fact. Defaults to
      pipeline_gap: profiling alone cannot tell the two apart, and §4.3's
      "prefer loud" principle means treating an unclassified gap as worth
      flagging until a human overrides it, not assuming it's permanent by
      default.
    - `source`: 'derived' = produced by coverage profiling (reproducible,
      re-runnable, dated). 'declared' = a human asserted it without data
      support — the escape hatch for cases the profiler can't see.
    """
    dimension: str = Field(..., description="The denied dimension field name")
    reason_class: str = Field(
        "pipeline_gap",
        description="'structural' (permanent fact about the client's business data, declare and keep) | 'pipeline_gap' (a completeness gap in the client's own source data/ETL — not an Agent9 defect) — see class docstring",
    )
    note: Optional[str] = Field(None, description="Human-readable detail — which check failed, coverage numbers, etc.")
    source: str = Field(
        "derived",
        description="'derived' (produced by coverage profiling) | 'declared' (a human asserted it without data support)",
    )


class KPI(BaseModel):
    """
    Represents a KPI (Key Performance Indicator) in the registry.

    This model replaces the enum-based approach with a flexible,
    data-driven model that can be extended by customers.
    """
    
    id: str = Field(..., description="Unique identifier for the KPI")
    client_id: str = Field(default_factory=lambda: os.getenv("ACTIVE_CLIENT_ID", "lubricants"), description="Client/tenant this KPI belongs to")
    name: str = Field(..., description="Human-readable name of the KPI")
    domain: str = Field(..., description="Business domain this KPI belongs to (e.g., Finance, HR, Sales)")
    description: Optional[str] = Field(None, description="Detailed description of the KPI")
    unit: Optional[str] = Field(None, description="Unit of measurement (%, $, #, etc.)")
    data_product_id: str = Field(..., description="ID of the data product containing this KPI's data")
    view_name: Optional[str] = Field(None, description="Name of the view/table this KPI queries against")
    business_process_ids: List[str] = Field(default_factory=list, description="Business processes this KPI belongs to")
    sql_query: Optional[str] = Field(None, description="SQL query to calculate the KPI")
    filters: Optional[Dict[str, Union[str, int, float, bool, List[str], List[int], List[float]]]] = Field(None, description="Static filters to apply for this KPI")
    thresholds: List[KPIThreshold] = Field(default_factory=list, description="Thresholds for evaluating the KPI")
    dimensions: List[KPIDimension] = Field(default_factory=list, description="Dimensions for analyzing the KPI")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    owner_role: Optional[str] = Field(None, description="Primary role responsible for this KPI")
    stakeholder_roles: List[str] = Field(default_factory=list, description="Roles with a stake in this KPI")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Additional metadata for extensions")
    monitoring_profile: Optional[KPIMonitoringProfile] = Field(
        None,
        description="Per-KPI monitoring calibration. None = use engine defaults. Set by KPI Assistant after volatility analysis."
    )
    # Phase 12A — template lifecycle
    status: str = Field(
        "active",
        description="KPI lifecycle: 'template' = research artifact pending data connection (SA skips); 'active' = monitored"
    )
    benchmark_range: Optional[str] = Field(
        None,
        description="Display-friendly industry benchmark range (e.g. '12-18%'). Populated by Phase 12A template generator."
    )
    benchmark_source: Optional[str] = Field(
        None,
        description="Provenance of benchmark_range: 'filing' | 'peer' | 'inferred'."
    )
    plan_version_value: Optional[str] = Field(
        None,
        description=(
            "Version filter value for plan/budget data (e.g. 'Budget', 'Plan', 'Forecast'). "
            "When set, SA derives the plan SQL by substituting this value for 'Actual' in sql_query. "
            "None = skip plan variance detection for this KPI."
        )
    )
    kpi_type: str = Field(
        "operational",
        description="KPI classification: 'operational' | 'concentration' | 'covenant' | 'regulatory'"
    )
    # docs/architecture/kpi_semantic_contract.md §4 — sliceability. Safe to store
    # as a flat list here (not a per-data-product mapping) because data_product_id
    # above is a scalar: one KPI record, for one client, always resolves to
    # exactly one data product, so there is never an ambiguity about which
    # schema/grain a not_sliceable_by entry refers to.
    #
    # A DENY list, not an allow list, deliberately — defaults to "every
    # dimension is fine to slice by" until check_slice_validity finds otherwise.
    # An allow list decays silently (a new column never gets analysed and
    # nobody notices); a deny list fails loud (an unexpected verdict is visible
    # immediately). Populated only by
    # A9_Data_Governance_Agent.check_slice_validity() — never authored by hand.
    #
    # Advisory only. Nothing reads this field to gate Deep Analysis's dimension
    # selection or block onboarding — that was designed and explicitly rejected
    # as scope creep at demo stage (DEVELOPMENT_PLAN.md -> Phase 15 -> Stage I).
    # If a future change makes this field load-bearing rather than advisory,
    # that is a decision to make consciously, not one to drift into.
    not_sliceable_by: List[NotSliceableByEntry] = Field(
        default_factory=list,
        description=(
            "Dimensions this KPI (single-component sum or multi-component ratio) must NOT be "
            "sliced by — the UNION of two checks (completeness + cross-component). Consumed by "
            "A9_Deep_Analysis_Agent (docs/architecture/kpi_semantic_contract.md §4.5): excluded "
            "from dims_to_process before the max_dimensions cut, and recorded on "
            "DeepAnalysisResponse.dimensions_excluded so exclusion is never silent (§4.6's "
            "trap — a deny list is a place bugs hide unless every exclusion stays visible)."
        )
    )

    @field_validator("not_sliceable_by", mode="before")
    @classmethod
    def _normalize_not_sliceable_by(cls, v: Any) -> Any:
        """Accept legacy flat-string entries alongside the current structured shape.

        Real KPI records were persisted with `not_sliceable_by` as a bare list
        of dimension names before this field carried reason_class/source/note
        (2026-08-16) — normalizing here means those records still load instead
        of failing validation. A bare string is wrapped as
        reason_class='pipeline_gap' (prefer loud — see NotSliceableByEntry)
        and source='derived' (it WAS produced by profiling, just before this
        field existed to record that explicitly).
        """
        if not v:
            return v
        normalized = []
        for item in v:
            if isinstance(item, str):
                normalized.append({"dimension": item, "reason_class": "pipeline_gap", "source": "derived", "note": None})
            else:
                normalized.append(item)
        return normalized
    slice_validity_details: Optional[Dict[str, Any]] = Field(
        None,
        description="Last check_slice_validity run's raw per-dimension result — {dimension: {'completeness': {counts,coverage,verdict}, 'cross_component': {...} | absent}} — so a human can see WHICH check failed and why, not just that one did. cross_component is absent when the KPI has fewer than 2 components (nothing to compare); completeness always runs."
    )
    slice_validity_checked_at: Optional[datetime] = Field(
        None,
        description="When check_slice_validity last ran for this KPI. Displayed prominently wherever not_sliceable_by is shown — staleness must be visible, not silent."
    )

    @classmethod
    def from_enum_value(cls, enum_value: str, domain: str = "Finance") -> "KPI":
        """
        Create a KPI instance from a legacy enum value.
        
        This method provides backward compatibility with the enum-based approach.
        
        Args:
            enum_value: The enum value string (e.g., "GROSS_MARGIN")
            domain: The business domain this KPI belongs to
            
        Returns:
            A KPI instance
        """
        # Create a normalized name from the enum value
        name = " ".join(word.capitalize() for word in enum_value.lower().split("_"))
        
        # Create a normalized ID from the enum value
        kpi_id = enum_value.lower()
        
        return cls(
            id=kpi_id,
            name=name,
            domain=domain,
            description=f"{name} KPI for {domain}",
            unit="%",  # Default unit
            data_product_id="finance_data",  # Default data product
            sql_query=f"SELECT * FROM kpi_{kpi_id}",  # Default query
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return self.model_dump()
    
    @property
    def legacy_id(self) -> str:
        """
        Get the legacy enum ID for backward compatibility.
        
        This property allows seamless migration from enum-based code.
        
        Returns:
            The legacy enum ID as a string (e.g., "GROSS_MARGIN")
        """
        return self.name.upper().replace(" ", "_").replace("-", "_")
    
    def evaluate(self, value: float, comparison_type: ComparisonType) -> KPIEvaluationStatus:
        """
        Evaluate the KPI based on the provided value and comparison type.
        
        Args:
            value: The value to evaluate
            comparison_type: The type of comparison to use
            
        Returns:
            The evaluation status (GREEN, YELLOW, RED, etc.)
        """
        # Find the threshold for the specified comparison type
        threshold = next((t for t in self.thresholds if t.comparison_type == comparison_type), None)
        
        if not threshold:
            return KPIEvaluationStatus.UNKNOWN
        
        # Apply threshold logic
        if threshold.inverse_logic:
            # For inverse logic, lower is better
            if threshold.green_threshold is not None and value <= threshold.green_threshold:
                return KPIEvaluationStatus.GREEN
            elif threshold.yellow_threshold is not None and value <= threshold.yellow_threshold:
                return KPIEvaluationStatus.YELLOW
            elif threshold.red_threshold is not None and value <= threshold.red_threshold:
                return KPIEvaluationStatus.RED
            else:
                return KPIEvaluationStatus.RED
        else:
            # For normal logic, higher is better
            if threshold.green_threshold is not None and value >= threshold.green_threshold:
                return KPIEvaluationStatus.GREEN
            elif threshold.yellow_threshold is not None and value >= threshold.yellow_threshold:
                return KPIEvaluationStatus.YELLOW
            elif threshold.red_threshold is not None and value >= threshold.red_threshold:
                return KPIEvaluationStatus.RED
            else:
                return KPIEvaluationStatus.RED
