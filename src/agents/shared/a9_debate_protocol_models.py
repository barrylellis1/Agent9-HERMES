"""
Pydantic v2 protocol models for Agent9 CaaS one-shot and bounded interactive debate.
These models enable a structured ProblemStatement input and standardized outputs
from branded agents and the debate aggregator, aligned with Agent9 standards.

Location: src/agents/shared/a9_debate_protocol_models.py
Imports follow existing shared base model pattern.
"""

from typing import Any, Dict, List, Optional, Literal
from pydantic import Field, ConfigDict, model_validator

from .a9_agent_base_model import (
    A9AgentBaseModel,
    A9AgentBaseRequest,
    A9AgentBaseResponse,
)


# -----------------------------
# Problem Statement (MDP subset)
# -----------------------------

class A9_PS_RegistryRefs(A9AgentBaseModel):
    yaml_contract_id: Optional[str] = Field(
        default=None, description="Registry YAML contract ID if applicable"
    )
    kpi_ids: Optional[List[str]] = Field(default=None, description="Relevant KPI IDs")
    data_product_ids: Optional[List[str]] = Field(
        default=None, description="Relevant data product IDs"
    )


class A9_PS_Segments(A9AgentBaseModel):
    dimensions: Optional[List[str]] = Field(
        default=None, description="Segment dimensions, e.g., ['region','product_line']"
    )
    focus_slices: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Focused slices, e.g., [{ 'region': 'NA', 'product_line': 'CE' }]"
    )


class A9_PS_Scope(A9AgentBaseModel):
    business_process: Optional[str] = Field(
        default=None, description="Named process or view of business context"
    )
    timeframe: Optional[str] = Field(
        default=None,
        description="Timeframe keyword (e.g., 'last_month', 'this_quarter'). Must map to time_dim conditions",
    )
    segments: Optional[A9_PS_Segments] = Field(default=None, description="Segmentation focus")


class A9_PS_Objective(A9AgentBaseModel):
    type: Literal["maximize", "minimize", "target"] = Field(..., description="Objective type")
    kpi_id: str = Field(..., description="KPI identifier for the objective")
    target_value: Optional[float] = Field(
        default=None, description="Target value when type='target'"
    )
    direction: Optional[str] = Field(
        default=None, description="Optional business direction hint"
    )


class A9_PS_Filters(A9AgentBaseModel):
    principal_filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Human/business filters prior to governance translation"
    )
    technical_filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Post-governance technical filters (column -> value)"
    )


class A9_PS_Provenance(A9AgentBaseModel):
    transaction_id: Optional[str] = Field(default=None, description="Query run ID")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp of evidence")
    orchestrator_run_id: Optional[str] = Field(
        default=None, description="Orchestrator run identifier"
    )


class A9_PS_EvidenceItem(A9AgentBaseModel):
    kpi_id: str = Field(..., description="KPI reference for this evidence item")
    data_product_view: Optional[str] = Field(
        default=None, description="Resolved view/table used"
    )
    timeframe_condition: str = Field(
        ..., description="SQL WHERE condition using time_dim attributes only (e.g., t.fiscal_year, t.month, t.'date')"
    )
    filters: Optional[A9_PS_Filters] = Field(
        default=None, description="Filters applied to build this evidence"
    )
    sql_reference_id: Optional[str] = Field(
        default=None, description="Stable identifier for SQL stored elsewhere"
    )
    sql_sample: Optional[str] = Field(
        default=None, description="Optional SQL sample text for transparency"
    )
    current_value: Optional[float] = Field(default=None, description="Current KPI value")
    baseline_value: Optional[float] = Field(default=None, description="Baseline KPI value")
    delta: Optional[float] = Field(default=None, description="Difference current - baseline")
    comparison_type: Optional[Literal["MoM", "QoQ", "YoY", "YTD"]] = Field(
        default=None, description="Comparison type, when applicable"
    )
    provenance: Optional[A9_PS_Provenance] = Field(
        default=None, description="Audit trail for this evidence item"
    )


class A9_PS_ComplianceGuardrails(A9AgentBaseModel):
    data_residency: Optional[str] = Field(default=None, description="Data residency policy")
    pii_policy: Optional[str] = Field(default=None, description="PII handling policy")
    ip_sharing: Optional[Literal["isolated", "aggregated"]] = Field(
        default="isolated", description="IP and rationale sharing policy across brands"
    )


class A9_PS_Constraints(A9AgentBaseModel):
    time_horizon: Optional[str] = Field(default=None, description="Business time horizon")
    budget_cap: Optional[float] = Field(default=None, description="Budget cap in currency units")
    resource_limits: Optional[Dict[str, Any]] = Field(
        default=None, description="Resource limits, e.g., { 'ops_hours': 200 }"
    )
    compliance_guardrails: Optional[A9_PS_ComplianceGuardrails] = Field(
        default=None, description="Compliance guardrails"
    )
    assumptions: Optional[List[str]] = Field(default=None, description="Key assumptions")


class A9_PS_Criterion(A9AgentBaseModel):
    name: str = Field(..., description="Criterion name, e.g., impact, cost, time_to_value, risk")
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight between 0 and 1")
    direction: Literal["higher_is_better", "lower_is_better"] = Field(
        ..., description="Scoring direction"
    )
    measure_hint: Optional[str] = Field(default=None, description="Optional scoring hint")


class A9_PS_AcceptanceThresholds(A9AgentBaseModel):
    min_consensus_ratio: float = Field(0.6, ge=0.0, le=1.0, description="Minimum ratio for consensus")
    min_score_gap: float = Field(0.1, ge=0.0, le=1.0, description="Minimum gap between top two scores")


class A9_PS_DecisionCriteria(A9AgentBaseModel):
    criteria: List[A9_PS_Criterion] = Field(..., description="List of decision criteria")
    risk_tolerance: Literal["low", "medium", "high"] = Field(
        "medium", description="Risk tolerance level"
    )
    acceptance_thresholds: A9_PS_AcceptanceThresholds = Field(
        default_factory=A9_PS_AcceptanceThresholds, description="Acceptance thresholds"
    )

    @model_validator(mode="after")
    def _validate_weights(self):
        total = sum(c.weight for c in self.criteria)
        if not (0.99 <= total <= 1.01):
            raise ValueError(
                f"Decision criteria weights must sum to 1.0 ±0.01, got {total:.3f}"
            )
        return self


class A9_PS_Stakeholders(A9AgentBaseModel):
    owners: Optional[List[str]] = Field(default=None, description="Owners of actions")
    approvers: Optional[List[str]] = Field(default=None, description="Approvers for HITL")
    hitl_required: Optional[bool] = Field(
        default=False, description="Whether human approval is required"
    )
    hitl_notes: Optional[str] = Field(default=None, description="Notes for approvers")


class A9_PS_Participant(A9AgentBaseModel):
    brand_id: str = Field(..., description="Brand identifier")
    agent_id: str = Field(..., description="Agent identifier")
    visibility: Literal["share_rationale", "hide_details"] = Field(
        "share_rationale", description="Rationale visibility"
    )
    rag_connector_id: Optional[str] = Field(
        default=None, description="RAG connector ID for brand IP isolation"
    )


class A9_PS_AggregationWeights(A9AgentBaseModel):
    criteria_weight: float = Field(0.9, ge=0.0, le=1.0, description="Weight for criteria score")
    brand_confidence_weight: float = Field(
        0.1, ge=0.0, le=1.0, description="Weight for brand confidence"
    )


class A9_PS_DebateConfig(A9AgentBaseModel):
    one_shot_mode: bool = Field(True, description="Enable one-shot debate")
    max_rounds: int = Field(1, ge=1, le=5, description="Max total rounds including clarifications")
    time_budget_sec: int = Field(60, ge=1, description="Time budget per round in seconds")
    selection_mode: Literal["fixed", "dynamic"] = Field(
        "fixed", description="Participant selection mode"
    )
    consensus_method: Literal[
        "weighted_score",
        "majority_vote",
        "rank_aggregation",
    ] = Field("weighted_score", description="Consensus aggregation method")
    aggregation_weights: A9_PS_AggregationWeights = Field(
        default_factory=A9_PS_AggregationWeights, description="Weights for aggregation"
    )
    conflict_policy: Literal["escalate_hitl", "request_reframe", "return_top2"] = Field(
        "escalate_hitl", description="Policy when consensus thresholds are unmet"
    )
    participants: List[A9_PS_Participant] = Field(
        default_factory=list, description="Debate participants"
    )

class A9_PS_BusinessContext(A9AgentBaseModel):
    """Stable, concise enterprise context that guides brand recommendations.

    Keep entries short and structured to reduce prompt length while conveying
    industry, scale, and operating constraints that materially affect the
    solution space.
    """
    enterprise_name: str = Field(..., description="Customer/enterprise name")
    industry: str = Field(..., description="Primary industry (e.g., Manufacturing, Healthcare)")
    subindustry: Optional[str] = Field(default=None, description="Optional subindustry")
    revenue_band: Optional[str] = Field(default=None, description="Revenue range, e.g., $100M–$500M")
    employee_band: Optional[str] = Field(default=None, description="Employee range, e.g., 1k–5k")
    regions: Optional[List[str]] = Field(default=None, description="Key operating regions (<=5)")
    go_to_market: Optional[List[str]] = Field(default=None, description="GTM model(s): B2B, B2C, B2B2C")
    products_services: Optional[List[str]] = Field(default=None, description="Core offerings (<=5)")
    primary_systems: Optional[Dict[str, str]] = Field(
        default=None, description="Key systems, e.g., { 'ERP': 'SAP S/4HANA', 'CRM': 'Salesforce' }"
    )
    data_maturity: Optional[Literal["low", "medium", "high"]] = Field(
        default=None, description="Data/analytics maturity"
    )
    risk_posture: Optional[Literal["low", "medium", "high"]] = Field(
        default=None, description="Risk tolerance"
    )
    compliance_requirements: Optional[List[str]] = Field(
        default=None, description="e.g., SOX, HIPAA, GDPR, SOC2"
    )
    strategic_priorities: Optional[List[str]] = Field(
        default=None, description="Top 1–3 strategic priorities"
    )
    operating_model: Optional[str] = Field(
        default=None, description="Centralized, decentralized, or hybrid"
    )
    notes: Optional[str] = Field(default=None, description="Short free-text note (<=160 chars)")

    @model_validator(mode="after")
    def _validate_limits(self):
        # Soft limits to keep prompts concise; raise if exceeded
        if self.regions is not None and len(self.regions) > 5:
            raise ValueError("regions must contain at most 5 items")
        if self.products_services is not None and len(self.products_services) > 5:
            raise ValueError("products_services must contain at most 5 items")
        if self.strategic_priorities is not None and len(self.strategic_priorities) > 3:
            raise ValueError("strategic_priorities must contain at most 3 items")
        if self.notes is not None and len(self.notes) > 160:
            raise ValueError("notes must be <= 160 characters")
        return self


class A9_ProblemStatement(A9AgentBaseRequest):
    """Top-level structured problem statement for debate-enabled workflows."""

    # Context
    role: Optional[str] = Field(default=None, description="Principal role (e.g., CFO)")
    environment: Optional[Literal["dev", "test", "prod"]] = Field(
        default="test", description="Execution environment"
    )
    registry_refs: Optional[A9_PS_RegistryRefs] = Field(
        default=None, description="Registry references (KPI/data product)"
    )
    business_context: Optional[A9_PS_BusinessContext] = Field(
        default=None, description="Stable enterprise profile guiding recommendations"
    )

    # Problem framing
    summary: str = Field(..., description="Short problem summary")
    objective: A9_PS_Objective = Field(..., description="Decision objective")
    scope: Optional[A9_PS_Scope] = Field(default=None, description="Scope of analysis")

    # Evidence & constraints
    evidence_items: List[A9_PS_EvidenceItem] = Field(
        default_factory=list, description="Evidence items grounding the debate"
    )
    constraints: Optional[A9_PS_Constraints] = Field(
        default=None, description="Constraints and guardrails"
    )

    # Decision & governance
    decision_criteria: A9_PS_DecisionCriteria = Field(
        ..., description="Decision rubric with weighted criteria"
    )
    stakeholders: Optional[A9_PS_Stakeholders] = Field(
        default=None, description="Stakeholders and HITL requirements"
    )
    debate_config: Optional[A9_PS_DebateConfig] = Field(
        default_factory=A9_PS_DebateConfig, description="Debate configuration"
    )


# -----------------------------
# Brand Recommendation (per participant)
# -----------------------------

class A9_BrandOption(A9AgentBaseModel):
    title: str = Field(..., description="Option title")
    description: Optional[str] = Field(default=None, description="Option summary")
    expected_impact: Optional[Dict[str, Any]] = Field(
        default=None, description="Expected impact, e.g., { 'kpi_id': 'REV', 'delta': 0.05, 'timeframe': 'next_quarter' }"
    )
    cost: Optional[Dict[str, Any]] = Field(
        default=None, description="Cost breakdown, e.g., { 'one_time': 10000, 'run_rate': 2500 }"
    )
    time_to_value: Optional[Dict[str, Any]] = Field(
        default=None, description="Time to value, e.g., { 'start_weeks': 2, 'full_value_weeks': 8 }"
    )
    risk_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Risk score 0-1")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Confidence 0-1")
    dependencies: Optional[List[str]] = Field(default=None, description="Dependencies")
    blockers: Optional[List[str]] = Field(default=None, description="Blockers")
    evidence_refs: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="References to evidence items"
    )
    compliance_note: Optional[str] = Field(default=None, description="Compliance notes")


class A9_BrandRecommendation(A9AgentBaseModel):
    brand_id: str = Field(..., description="Recommender brand ID")
    agent_id: str = Field(..., description="Recommender agent ID")
    rationale: Optional[str] = Field(default=None, description="Short rationale")
    criteria_scores: Optional[Dict[str, float]] = Field(
        default=None, description="Per-criterion scores (0-1)"
    )
    composite_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Composite score (0-1)"
    )
    options: List[A9_BrandOption] = Field(default_factory=list, description="Option set")
    brand_meta: Optional[Dict[str, Any]] = Field(
        default=None, description="Metadata: model/method, rag_connector_id, timestamp"
    )


# -----------------------------
# Debate Aggregation Result
# -----------------------------

class A9_DebateAggregateResult(A9AgentBaseResponse):
    selected: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Selected option summary: { 'brand_id': str, 'option_index': int, 'composite_score': float }",
    )
    runner_up: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Runner-up summary with same keys as selected",
    )
    acceptance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Acceptance check details (thresholds and observed metrics)",
    )
    rationale_summary: Optional[str] = Field(
        default=None, description="Brief rationale for selection"
    )
    aggregator_meta: Optional[Dict[str, Any]] = Field(
        default=None, description="Aggregator metadata/version"
    )
