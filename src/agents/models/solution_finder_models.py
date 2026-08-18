"""
Pydantic models for the Solution Finder Agent (A2A-compliant).
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import AliasChoices, Field, field_validator

from src.agents.shared.a9_agent_base_model import (
    A9AgentBaseModel,
    A9AgentBaseRequest,
    A9AgentBaseResponse,
)


# ---------------------------------------------------------------------------
# Phase 15 Stage B — unified trust/output schema
#
# SolutionAssumption is the single typed assumption object shared by Phase 11J
# P1 (validity monitoring, source-classified) and Phase 15 (per-option "bets
# on" list + calibrated confidence) — see DEVELOPMENT_PLAN.md Phase 15 §Stage B.
# Do not introduce a second assumption model; extend this one.
# ---------------------------------------------------------------------------

_HEDGE_WORDS = {"consider", "potentially", "might", "could possibly", "may want to"}


class SolutionAssumption(A9AgentBaseModel):
    """A single assumption a solution option bets on, source-classified and gradeable."""
    assumption: str
    validated_by: Literal["sa_assessment", "ma_query", "human_confirmation"]
    validated_at: Optional[str] = None  # ISO datetime; None = not yet confirmed
    revalidation_days: Optional[int] = None  # for human_confirmation: days before re-confirmation needed
    # Phase 15 additions (trustworthy generation):
    grounded: bool = Field(
        default=False,
        description="True if verifiable from SA/MA data at synthesis time; False if inferred by the LLM.",
    )
    confidence: Optional[Literal["high", "moderate", "low"]] = None
    provenance: Optional[str] = Field(
        default=None,
        description="What would confirm or falsify this assumption — never 'proved', at most 'consistent with'.",
    )


class DecisionAsk(A9AgentBaseModel):
    """The single decision an executive is being asked to make (Phase 13 M2)."""
    decision_text: str
    decision_owner: Optional[str] = None
    deadline: Optional[str] = None
    approval_type: Optional[str] = None

    @field_validator("decision_text")
    @classmethod
    def _validate_decision_text(cls, v: str) -> str:
        words = v.split()
        if len(words) > 25:
            raise ValueError(f"decision_text must be <=25 words, got {len(words)}")
        lowered = v.lower()
        for hedge in _HEDGE_WORDS:
            if hedge in lowered:
                raise ValueError(f"decision_text must not hedge — found '{hedge}'")
        return v


class ImmediateAction(A9AgentBaseModel):
    """A single actionable next step (Phase 13 M5)."""
    action_text: str
    owner: Optional[str] = None
    due_by_days: Optional[int] = None
    why_it_matters: Optional[str] = None


class RecoveryRange(A9AgentBaseModel):
    low: Optional[float] = None
    high: Optional[float] = None


class ImpactEstimate(A9AgentBaseModel):
    """Typed replacement for the previously untyped impact_estimate dict.

    ``scope`` was added after live runs produced recovery ranges of 18.5-28.3
    percentage points on a Gross Margin % of 31.08 whose annual decline was
    5.08pp. The numbers were not invented: the ``basis`` text traced them to
    "50-65% of the 43.24pp Chain A decline" and "40-50% of Synthetic Blend's
    16.76pp loss" — real DIMENSIONAL magnitudes from DA's change_points, worn
    under the ENTERPRISE KPI's name. Reproduced in both fast and full debate
    mode, so it is structural rather than model noise.

    Without a scope field the two readings are indistinguishable downstream, and
    the consumer that matters is not the briefing but VA: solution registration
    reads recovery_range verbatim into impact bounds, so an unqualified segment
    figure becomes an enterprise commitment that VA later grades against a
    target that was never attainable.

    Prompt wording alone cannot fix this — the synthesis prompt already asks for
    enterprise units AND tells the model to anchor ``basis`` in change_points,
    which are segment-level. Faced with that, it resolves toward the larger, more
    salient number. Making scope explicit is what removes the ambiguity.
    """
    metric: Optional[str] = None
    unit: Optional[str] = None
    recovery_range: Optional[RecoveryRange] = None
    basis: Optional[str] = None

    # "enterprise" = moves the headline KPI by this much.
    # "segment"    = moves the named segment only; scope_label carries which one.
    # None         = unstated (pre-existing payloads, and any model that ignores
    #                the instruction). Treated as UNVERIFIED by consumers rather
    #                than silently assumed to be enterprise — that assumption is
    #                the bug this field exists to prevent.
    scope: Optional[Literal["enterprise", "segment"]] = None
    scope_label: Optional[str] = None  # e.g. "National Auto Parts Chain A"


class TradeOffCriterion(A9AgentBaseModel):
    name: str
    weight: float = 1.0


class LensView(A9AgentBaseModel):
    """One council lens's reading of an option.

    RENAMED FROM `PerspectiveAnalysis` (2026-08-16) to settle a vocabulary
    collision. "Lens" and "Perspective" were both being used for both of two
    unrelated concepts:

      * **Lens** — an *analytical territory* a council member reasons from
        (`commercial` / `operational` / `structural`). This class.
      * **Perspective** — a *comparison basis* for appraising a KPI
        (Plan / Trend / Peer / Value-gap / Bridge), per
        `principal_lens_weighting_design.md`. Design-stage; no code yet.

    The convention is now: lens = who is looking, Perspective = what they compare
    against. This class was the one built site holding the wrong word.
    """
    lens: str  # "Financial", "Operational", "Strategic", etc.
    arguments_for: List[str] = Field(default_factory=list)
    arguments_against: List[str] = Field(default_factory=list)
    key_questions: List[str] = Field(default_factory=list)


# Import-compatibility alias. Cheap to keep, and an external caller or a pickled
# object referencing the old name should not explode on a vocabulary change.
PerspectiveAnalysis = LensView


class UnresolvedTension(A9AgentBaseModel):
    tension: str
    options_affected: List[str] = Field(default_factory=list)
    requires: str  # Specific operational action to resolve this tension — NOT meta-labels.
               # Must be: "Who does what specific task by when", e.g.:
               # "Finance team to commission SKU cost-to-serve analysis before negotiating with [customer] (target: by Week 2)"


class SolutionOption(A9AgentBaseModel):
    id: str
    title: str
    description: Optional[str] = None
    expected_impact: Optional[float] = None  # 0-1 normalized ranking score (+ means beneficial); NOT a dollar/pp estimate — see impact_estimate for that
    cost: Optional[float] = None             # normalized cost estimate
    risk: Optional[float] = None             # normalized risk estimate
    evidence: Optional[List[str]] = None     # URLs/refs or citations
    rationale: Optional[str] = None

    # Enhanced Decision Briefing Fields
    time_to_value: Optional[str] = None
    reversibility: Optional[str] = None  # high/medium/low
    # Renamed from `perspectives` (2026-08-16) — see LensView. The alias is NOT
    # decoration: briefing snapshots are persisted to Supabase and replayed by the
    # Portfolio view, and localStorage holds more of them, so payloads written
    # under the old key must keep loading. Reading accepts either spelling;
    # everything written from here on uses `lens_views`.
    lens_views: List[LensView] = Field(
        default_factory=list,
        validation_alias=AliasChoices("lens_views", "perspectives"),
    )
    implementation_triggers: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    impact_estimate: Optional[ImpactEstimate] = None  # business-unit (dollar/pp) recovery range — distinct from expected_impact above
    # Phase 15 Stage B: what this option bets on, per-option, gradeable by VA
    key_assumptions: List[SolutionAssumption] = Field(default_factory=list)
    # Phase 15 Stage E: critic-pass findings for this option — genuine
    # cross-KPI consequences or violated assumptions traced through the
    # causal graph, not a generic risk list. Empty when the critic pass is
    # disabled or found no basis for concern (see Stage G: "Risk block
    # surfacing Stage E side-effects").
    flagged_side_effects: List[str] = Field(default_factory=list)


class TradeOffMatrix(A9AgentBaseModel):
    criteria: List[TradeOffCriterion] = Field(default_factory=list)
    options: List[SolutionOption] = Field(default_factory=list)
    # "principal" = weights supplied for this decision; "config_default" = the
    # agent's own constant. A rendered matrix looks identical either way, which
    # is how every run shipped an unexamined system default without anyone
    # noticing. Optional so payloads written before this field remain readable.
    criteria_source: Optional[str] = Field(
        None, description="Provenance of `criteria`: 'principal' or 'config_default'"
    )


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
    principal_context: Optional[Dict[str, Any]] = None  # Principal context with decision_style for Principal-driven approach


class SolutionFinderResponse(A9AgentBaseResponse):
    """Ranked options, recommendation, and HITL context."""
    analysis_degraded: bool = Field(
        False,
        description=(
            "True when these options are the generic heuristic stub rather than model "
            "output. The stub ('Tighten spend controls' / 'Optimize pricing') is "
            "indistinguishable from a real recommendation to a reader, and worse than a "
            "wrong number because a wrong number can at least be argued with. Observed "
            "live 2026-08-09: the Anthropic account hit zero credit, EVERY LLM call "
            "failed, and the workflow returned state=completed with two plausible "
            "generic options and no signal. Consumers MUST surface this to the reader, "
            "not merely log it."
        ),
    )
    degraded_reason: Optional[Literal["llm_unavailable", "llm_yielded_no_options"]] = Field(
        None,
        description=(
            "'llm_unavailable' — the LLM calls themselves errored (outage, no credit, "
            "auth). No analysis happened at all; treat the run as failed. "
            "'llm_yielded_no_options' — the LLM responded but the synthesis could not be "
            "parsed into options, typically max_tokens truncation. Partial signal may "
            "still exist (Stage 1 hypotheses survive), so this degrades rather than fails."
        ),
    )
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
    stage_1_hypotheses: Optional[Dict[str, Any]] = None  # Per-persona Stage 1 hypotheses (multi-call)
    # Phase 15 Stage H: theory-guided moderator verdicts, keyed by option id.
    # Mutually exclusive with cross_review in practice: the moderator arm emits
    # grades (constraint_survival / causal_grounding / arithmetic_consistency /
    # critic_findings_response / grade_rationale), the baseline arm emits the
    # simulated cross_review. Untyped dict deliberately — the typed ModeratorGrade
    # model lands with the structured-output flip (PM-4: one variable per run).
    moderator_grades: Optional[Dict[str, Any]] = None

    # Stage I B-2 — deterministic constraint exposure. Computed in Python on every
    # run, independent of enable_theory_moderator, because safety must not depend
    # on an optional LLM pass. Reports WHO SAW WHAT, never whether an option
    # violates a constraint — that is a semantic judgement no regex makes honestly.
    # Shape: {union_size, by_persona{seen,unseen}, by_option{...}, moderator_checked}
    constraint_exposure: Optional[Dict[str, Any]] = None

    # Principal-Driven Framing Context (per PRD guardrails)
    framing_context: Optional[Dict[str, Any]] = None  # decision_style, personas_used, presentation_note, disclaimer

    # Market Intelligence enrichment (optional — populated when A9_Market_Analysis_Agent is available)
    market_intelligence: Optional[Dict[str, Any]] = None

    # Phase 15 / Phase 13 Cat 2: structured decision ask + immediate actions
    decision_ask: Optional[DecisionAsk] = None
    immediate_actions: List[ImmediateAction] = Field(default_factory=list)

    # Pending market signals for HITL confirmation before synthesis
    # Populated after Stage 1 (stage1_only); empty on subsequent debate stages.
    pending_market_signals: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Market signals returned after Stage 1 for user HITL confirmation before synthesis."
    )

    # Single HITL event fields per PRD
    human_action_required: bool = False
    human_action_type: Optional[str] = None
    human_action_context: Optional[Dict[str, Any]] = None
    human_action_result: Optional[str] = None
    human_action_timestamp: Optional[str] = None

    # Audit
    audit_log: Optional[List[Dict[str, Any]]] = None


# ---------------------------------------------------------------------------
# Phase 15 Stage A — forced tool-use structured output for the synthesis call
#
# SFSynthesisSchema mirrors the synthesis JSON shape the prompt already asks
# for (see a9_solution_finder_agent.py debate_spec/output_instruction). It
# exists purely so ClaudeService.generate_structured() can derive a JSON
# schema via .model_json_schema() — the existing manual parsing loop in
# a9_solution_finder_agent.py is NOT replaced by validating against this
# model; it stays as a defensive second layer. Used only when
# A9_Solution_Finder_Agent_Config.use_structured_output is True (default
# False — flip only after the live A/B compliance run, per Phase 15 M2/M5).
# ---------------------------------------------------------------------------

class ProblemReframe(A9AgentBaseModel):
    situation: str
    complication: str
    question: str
    key_assumptions: List[str] = Field(default_factory=list)  # overall analysis assumptions (prose) — distinct from SolutionOption.key_assumptions (per-option bets)


class CrossReviewCritique(A9AgentBaseModel):
    target: str
    concern: str


class CrossReviewEndorsement(A9AgentBaseModel):
    target: str
    reason: str


class CrossReviewEntry(A9AgentBaseModel):
    critiques: List[CrossReviewCritique] = Field(default_factory=list)
    endorsements: List[CrossReviewEndorsement] = Field(default_factory=list)


class RecommendationRef(A9AgentBaseModel):
    id: str
    title: str


class SFSynthesisSchema(A9AgentBaseModel):
    problem_reframe: ProblemReframe
    options: List[SolutionOption]
    recommendation: RecommendationRef
    recommendation_rationale: str
    unresolved_tensions: List[UnresolvedTension] = Field(default_factory=list)
    blind_spots: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    cross_review: Dict[str, CrossReviewEntry] = Field(default_factory=dict)
    decision_ask: Optional[DecisionAsk] = None
    immediate_actions: List[ImmediateAction] = Field(default_factory=list)
