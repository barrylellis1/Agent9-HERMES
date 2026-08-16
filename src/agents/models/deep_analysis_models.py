"""
Pydantic models for the Deep Analysis Agent (A2A-compliant).
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import Field

from src.agents.shared.a9_agent_base_model import (
    A9AgentBaseModel,
    A9AgentBaseRequest,
    A9AgentBaseResponse,
)


class DeepAnalysisRequest(A9AgentBaseRequest):
    """Request to enumerate, plan, or execute deep analysis for a KPI."""
    kpi_name: str = Field(..., description="Target KPI to analyze")
    client_id: Optional[str] = Field(None, description="Client/tenant ID — scopes KPI lookup to this client only")
    timeframe: Optional[str] = Field(None, description="Timeframe token from Decision Studio (e.g., last_quarter)")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional KPI filters")
    target_count: int = Field(5, description="Desired number of top results or dimensions to consider")
    enable_percent_growth: bool = Field(False, description="Whether to compute/display percent growth outputs")
    threshold: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional threshold spec to guide breach detection (e.g., metric: budget|mom, inverse_logic: bool, yellow_threshold: float, budget_version: 'Budget')."
    )
    analysis_mode: Literal["problem", "opportunity", "mixed"] = Field(
        default="problem",
        description="Caller hint — DA overrides this by inspecting segment variance."
    )
    # Phase 11I-B: alert-type-aware SCQA framing
    alert_type: Optional[str] = Field(
        None,
        description="Alert pattern that triggered this analysis: 'threshold_breach' | 'plan_variance' | 'projected_breach' | 'acceleration' | 'compound'"
    )
    compound_alert: bool = Field(False, description="True when a cross-KPI compound conflict triggered this analysis")
    compound_pattern: Optional[str] = Field(None, description="Human-readable compound tension, e.g. 'Revenue UP / Gross Margin DOWN'")
    # Phase 11I-D: alert-type-aware comparator selection + bounded secondary-fact narration
    merged_alert_types: Optional[List[str]] = Field(
        None,
        description="All alert patterns that fired for this KPI in the originating SA scan (from Situation.merged_alert_types). The dominant one is `alert_type`; the rest are narrated as bounded scalar facts, not a second diagnosis."
    )
    secondary_alert_facts: Optional[Dict[str, Any]] = Field(
        None,
        description="Scalar values from the originating situation for narrating non-primary alert types (plan_value, projected_breach_at_period, periods_until_breach, acceleration_signal). Facts only — no second dimensional analysis."
    )
    comparator_override: Optional[Literal["previous", "budget"]] = Field(
        None,
        description="Explicit comparator basis for the on-demand 'diagnose vs the other basis' drill. When set, forces comparator_main and bypasses alert-type/registry selection. None on the normal path."
    )


class DeepAnalysisPlan(A9AgentBaseModel):
    """Planned steps for a deep analysis execution."""
    kpi_name: str
    client_id: Optional[str] = None
    timeframe: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    dimensions: List[str] = Field(default_factory=list, description="Candidate dimensions to analyze (MECE-guided)")
    steps: List[Dict[str, Any]] = Field(default_factory=list, description="Ordered execution steps for DPA (grouped/timeframe comparisons)")
    notes: Optional[str] = None
    # Stage I Part A — make the dimension choice auditable. Ranking is by DECLARED
    # order (contract, then KPI registry, then DGA); recording which declaration won
    # is what turns a badly-authored contract into a visible data-quality finding
    # rather than a silently odd investigation.
    dimensions_considered: List[str] = Field(
        default_factory=list,
        description="Full candidate set from the winning source, before max_dimensions truncation."
    )
    dimension_rank_source: Optional[Literal["contract_semantics", "kpi_registry", "dga_metadata", "hierarchy_vectors", "none"]] = Field(
        None,
        description="Which declaration decided the dimension order. 'none' means no source produced any candidates."
    )
    analysis_mode: Literal["problem", "opportunity", "mixed"] = Field(
        default="problem",
        description="Propagated from DeepAnalysisRequest — controls IS/IS NOT framing and SCQA narrative direction."
    )
    # Phase 11I-B: alert-type-aware SCQA framing
    alert_type: Optional[str] = Field(
        None,
        description="Alert pattern that triggered this analysis: 'threshold_breach' | 'plan_variance' | 'projected_breach' | 'acceleration' | 'compound'"
    )
    compound_alert: bool = Field(False, description="True when a cross-KPI compound conflict triggered this analysis")
    compound_pattern: Optional[str] = Field(None, description="Human-readable compound tension, e.g. 'Revenue UP / Gross Margin DOWN'")
    # Phase 11I-D: alert-type-aware comparator selection + bounded secondary-fact narration (propagated from request)
    merged_alert_types: Optional[List[str]] = Field(
        None,
        description="All alert patterns that fired for this KPI in the originating SA scan. Dominant one is `alert_type`; rest narrated as bounded facts."
    )
    secondary_alert_facts: Optional[Dict[str, Any]] = Field(
        None,
        description="Scalar values for narrating non-primary alert types (plan_value, projected_breach_at_period, periods_until_breach, acceleration_signal)."
    )
    comparator_override: Optional[Literal["previous", "budget"]] = Field(
        None,
        description="Explicit comparator basis for the on-demand drill. When set, forces comparator_main. None on the normal path."
    )


class BenchmarkSegment(A9AgentBaseModel):
    """An IS NOT segment classified as control group or internal benchmark."""
    dimension: str = Field(..., description="Dimension name (e.g., 'Profit Center')")
    key: str = Field(..., description="Dimension member value (e.g., 'Mountain Bikes')")
    current_value: float = Field(..., description="Current period value for this segment")
    previous_value: float = Field(..., description="Previous period value for this segment")
    delta: float = Field(..., description="Absolute delta (current - previous)")
    delta_pct: Optional[float] = Field(None, description="Percentage change vs previous")
    benchmark_type: Literal["control_group", "internal_benchmark"] = Field(
        default="control_group",
        description="'internal_benchmark' = top-quartile outperformer (replication candidate); 'control_group' = stable segment (DiD baseline)"
    )
    replication_potential: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Estimated replication potential (0.0–1.0); set for internal_benchmark segments only"
    )
    effect_size_pct: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="This segment's |delta| as a fraction of total absolute variance across all peer segments (0–1)"
    )
    is_outlier: bool = Field(
        False,
        description="True when this segment's |delta| exceeds mean + 2σ of peer segment deltas"
    )


class DimensionTotal(A9AgentBaseModel):
    """The overall movement for one dimension, as the warehouse computed it.

    WHY THIS IS NOT A SUM
    ---------------------
    For an additive KPI (revenue, cost) the total happens to equal the sum of its
    members. For a RATIO KPI it does not, and the gap is enormous — a live panel
    added the per-product gross margins and printed 452.95% where the truth was
    29.43%, and added the pp deltas to print -53pp where the enterprise moved
    about -5pp.

    So the total is always re-aggregated by the query (GROUP BY ROLLUP), using the
    KPI's own registered expression, rather than derived in application code. That
    keeps the calculation inside the curated data product where it is defined, and
    means a KPI nobody configured still gets a correct total.
    """
    current: Optional[float] = Field(None, description="Overall value for the current window")
    previous: Optional[float] = Field(None, description="Overall value for the comparison window")
    delta: Optional[float] = Field(None, description="current - previous, in the KPI's own units")
    source: Literal["rollup", "scalar_query", "unavailable"] = Field(
        "unavailable",
        description=(
            "How the total was obtained. 'rollup' = a GROUP BY ROLLUP row on the same "
            "grouped query as the members. 'scalar_query' = a separate ungrouped query "
            "using the KPI's own expression (used when the dimensional path ends in "
            "ORDER BY ... LIMIT and cannot carry a ROLLUP row). Both mean the WAREHOUSE "
            "computed it. There is deliberately no 'sum' — deriving a ratio's total by "
            "adding its members is the bug this field exists to prevent, and leaving it "
            "unrepresentable means it cannot be reintroduced by accident."
        ),
    )


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
    benchmark_segments: List[BenchmarkSegment] = Field(
        default_factory=list,
        description="IS NOT items classified as control_group or internal_benchmark after analysis"
    )
    dimension_totals: Dict[str, "DimensionTotal"] = Field(
        default_factory=dict,
        description=(
            "Per-dimension overall movement, keyed by dimension name — computed by the "
            "WAREHOUSE via GROUP BY ROLLUP, never by summing the member rows. A ratio's "
            "members cannot be added: summing gross margin per product gives 452.95% "
            "against a true 29.43%, and summing the pp deltas gives -53pp against an "
            "enterprise move of about -5pp. Empty when the source did not supply a total; "
            "consumers must render nothing rather than deriving one."
        ),
    )


class ChangePoint(A9AgentBaseModel):
    """Detected change-point with pre/post stats."""
    dimension: Optional[str] = None
    key: Optional[str] = None
    timestamp: Optional[str] = None
    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    # `delta` ALWAYS means this segment's own change (current - previous), whatever
    # the KPI and whatever is configured. It previously flipped meaning — carrying a
    # revenue-weighted contribution when a KPI declared ratio-bridge metadata and a
    # raw change otherwise, roughly 8x apart, same field name. Since change_points
    # feed Solution Finder, that made a config flag silently alter what the LLM
    # reasoned about. Contribution now lives in its own field below.
    delta: Optional[float] = None
    percent_growth: Optional[float] = None
    contribution_pp: Optional[float] = Field(
        None,
        description=(
            "This segment's WEIGHTED contribution to the KPI's overall movement "
            "(share of denominator x its own rate change) — additive across segments, "
            "unlike `delta`. Populated only for ratio KPIs configured with bridge SQL; "
            "None means not computed, never zero."
        ),
    )


class DeepAnalysisResponse(A9AgentBaseResponse):
    """Response containing analysis planning and results."""
    # Planning outputs
    plan: Optional[DeepAnalysisPlan] = None
    dimensions_suggested: List[str] = Field(default_factory=list)
    dimensions_analyzed: List[str] = Field(
        default_factory=list,
        description=(
            "Dimensions actually queried, after the max_dimensions cut. Distinct from "
            "dimensions_suggested: a run can suggest 15 and analyze 10, and before this "
            "field existed nothing recorded which 10."
        ),
    )
    dimensions_excluded: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Dimensions dropped from analysis because the KPI's own not_sliceable_by deny "
            "list flagged them (docs/architecture/kpi_semantic_contract.md §4.5) — each entry "
            "{dimension, reason_class, source}. Excluded BEFORE the max_dimensions cut, so a "
            "denied slot frees room for a valid one rather than just wasting a query on a cut "
            "already known to be meaningless. Must be recorded, never silent: a deny list that "
            "quietly shrinks the investigation with no trace is the same defect a hardcoded "
            "dimension-preference list already caused once (§4.5)."
        ),
    )

    # Analysis outputs
    scqa_summary: Optional[str] = None
    kt_is_is_not: Optional[KTIsIsNot] = None
    change_points: List[ChangePoint] = Field(default_factory=list)
    timeframe_mapping: Optional[Dict[str, str]] = Field(default=None, description="{'current': 'X', 'previous': 'Y'}")
    when_started: Optional[str] = Field(default=None, description="Earliest time bucket when the issue began (e.g., '2025-08')")
    percent_growth_enabled: bool = Field(False)

    # Effective analysis mode as determined by DA
    analysis_mode: Literal["problem", "opportunity", "mixed"] = Field(
        default="problem",
        description="Effective analysis mode as determined by DA."
    )
    mixed_framing: bool = Field(
        False,
        description="True when DA determined analysis_mode='mixed' from segment variance — signals the frontend to show the HITL mode-resolution gate before invoking SF."
    )
    # Phase 11I-D: which alert basis was actually diagnosed, so SF/PIB/frontend can label it and
    # the frontend can offer the on-demand 'diagnose vs the other basis' drill.
    alert_type: Optional[str] = Field(
        None,
        description="The dominant alert pattern this analysis was framed for (propagated from the originating situation)."
    )
    comparator: Optional[Literal["previous", "budget"]] = Field(
        None,
        description="Which comparison basis this run's Is/Is-Not used: 'previous' (vs prior period) or 'budget' (vs plan/budget, same period)."
    )
    merged_alert_types: Optional[List[str]] = Field(
        None,
        description="All alert patterns that fired for this KPI. If it contains a basis other than `comparator`, the frontend can offer an on-demand drill to diagnose that basis."
    )
    # Phase 11I-D segment matrix: when a KPI breached on BOTH cross-sectional bases (YoY + Plan),
    # the primary kt_is_is_not table's rows are enriched with `secondary_delta` + `basis_agreement`
    # (confirmed | basis_specific | secondary_only | healthy) forming a segment × basis matrix.
    comparator_secondary: Optional[Literal["previous", "budget"]] = Field(
        None,
        description="The second comparison basis whose per-segment deltas were joined onto the primary Is/Is-Not table as an extra column. None when only one basis was analyzed."
    )
    matrix_ran: bool = Field(
        False,
        description="True when the segment matrix (both cross-sectional bases joined) was built. When False, kt_is_is_not rows carry no secondary_delta/basis_agreement."
    )

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


def constraint_id(text: str) -> str:
    """Stable id for a constraint, derived from its normalized text.

    The dedup key across turns, personas and sources. Normalization is
    deliberately crude — lowercase and whitespace-collapse only — because the
    goal is catching the same sentence arriving twice, not semantic matching,
    and anything cleverer would silently merge two genuinely different
    constraints.
    """
    import hashlib
    import re as _re

    normalized = _re.sub(r"\s+", " ", str(text or "")).strip().lower()
    return "c_" + hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:8]


class ConstraintItem(A9AgentBaseModel):
    """A constraint plus where it came from and who knows about it.

    Constraints previously travelled as bare strings, so nothing recorded
    whether one came from the principal's interview or the assumption register.
    That distinction is load-bearing twice over: register constraints must reach
    every persona regardless of who asked, and adjudication has to grade options
    against constraints their author may never have seen.
    """
    id: str = Field(..., description="Stable id from constraint_id(text) — the dedup key")
    text: str = Field(..., description="The constraint as stated")
    source: Literal["refinement", "assumption_register", "kpi_relationship"] = Field(
        ..., description="Where this constraint came from. Only 'refinement' constraints are persona-specific."
    )
    discovered_by: List[str] = Field(
        default_factory=list,
        description=(
            "Persona ids whose extractor surfaced this. Empty means every persona has it — "
            "either it is not a refinement constraint, or per-persona extraction is not enabled."
        ),
    )
    asked_by: Optional[str] = Field(
        None,
        description="Persona whose question elicited the turn. Known deterministically by the agent, never inferred from LLM output."
    )
    turn_index: Optional[int] = Field(None, description="Refinement turn that produced this")


class ProblemRefinementInput(A9AgentBaseModel):
    """Input for problem refinement chat."""
    deep_analysis_output: Dict[str, Any] = Field(..., description="KT IS/IS-NOT results from execute_deep_analysis")
    principal_context: Dict[str, Any] = Field(..., description="Role, decision_style, filters from principal profile")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Multi-turn chat history")
    user_message: Optional[str] = Field(None, description="Latest principal response")
    current_topic: Optional[str] = Field(None, description="Current topic in sequence (auto-managed)")
    turn_count: int = Field(0, description="Current turn number (auto-managed)")
    # Stage I B-1 — client-held conversation state, round-tripped rather than
    # re-derived server-side. The refinement endpoint is deliberately stateless;
    # the client already holds both of these and previously just never sent them.
    topics_completed: List[str] = Field(
        default_factory=list,
        description=(
            "Topics already covered, echoed back from the previous result. Replaces "
            "server-side recovery by pattern-matching LLM prose, which never worked."
        ),
    )
    turns_on_current_topic: int = Field(
        0,
        description=(
            "Turns spent on `current_topic`, reset by the client whenever the topic "
            "changes. Distinct from turn_count: completion is judged per topic, and "
            "counting all turns auto-completed every topic from turn 3 onward."
        ),
    )
    prior_constraint_items: List[ConstraintItem] = Field(
        default_factory=list,
        description=(
            "Typed constraints captured on earlier turns, echoed back by the client. "
            "Without this the agent re-derives prior turns heuristically from raw "
            "message text, discarding provenance and losing exclusions entirely."
        ),
    )
    prior_exclusions: List[RefinementExclusion] = Field(
        default_factory=list,
        description="Exclusions captured on earlier turns. The keyword replay path never produced these, so they were lost permanently."
    )
    # Market Analysis signals pre-fetched by the endpoint on turn 0.
    # These are injected into accumulated.external_context so the refinement LLM references
    # specific market signals in its questions rather than asking generic open-ended questions.
    initial_external_context: List[str] = Field(
        default_factory=list,
        description="MA-derived external context strings to seed the refinement (turn 0 only)."
    )


class ExtractedRefinements(A9AgentBaseModel):
    """Refinements extracted from a single turn."""
    exclusions: List[RefinementExclusion] = Field(default_factory=list)
    external_context: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    validated_hypotheses: List[str] = Field(default_factory=list)
    invalidated_hypotheses: List[str] = Field(default_factory=list)
    replication_constraints: List[str] = Field(default_factory=list)
    # `constraints` stays as the plain-string list every existing consumer reads.
    # constraint_items carries the same content with provenance attached.
    constraint_items: List[ConstraintItem] = Field(default_factory=list)


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

    # Market Intelligence signals detected at turn 0 (for display in the refinement UI)
    market_signals: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="MA signals returned on turn 0; shown as context cards above the refinement chat."
    )

    # Replication opportunity findings
    replication_constraints: List[str] = Field(
        default_factory=list,
        description="Structural barriers preventing replication of internal benchmark segments."
    )

    # Stage I B-1 — why this interview asked what it asked. Without these the
    # routing is invisible: a differently-routed conversation is indistinguishable
    # from the fixed sequence unless the decision is reported.
    constraint_items: List[ConstraintItem] = Field(
        default_factory=list,
        description=(
            "Accumulated constraints with provenance. `constraints` above remains the "
            "full flat union of texts, so every existing consumer is unaffected."
        ),
    )
    problem_profile_cell: Optional[str] = Field(
        None,
        description="ProblemProfile.cell_key() for this analysis, e.g. 'problem/concentrated/no-control/single'. None if classification failed."
    )
    topic_sequence: List[str] = Field(
        default_factory=list,
        description="The routed topic sequence for this problem. Equals REFINEMENT_TOPIC_SEQUENCE when no rule fired."
    )
    topic_routing_rules_applied: List[str] = Field(
        default_factory=list,
        description="Which routing rules fired and what each did. Empty means the default sequence was used."
    )
