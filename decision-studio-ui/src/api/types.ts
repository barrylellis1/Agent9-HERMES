export interface PrincipalActionSummary {
  situation_id: string;      // kpi_name used as stable key
  action_type: string;       // "delegate" | "snooze"
  target_principal_id?: string | null;
  created_at?: string | null;
}

export interface TopDriver {
  label: string;
  delta: number;
  currency?: string;
}

/**
 * Provenance for a measured value — mirrors `MeasurementContext` in
 * `src/agents/models/situation_awareness_models.py`.
 *
 * Exists because a KPI reading previously carried only the timeframe TOKEN, so
 * two values could disagree with nothing on either to say which window or data
 * version it covered. Consumers should DISPLAY this rather than re-derive
 * anything from it — re-derivation is what produced a "Recovering" label on a
 * deteriorating segment.
 */
export interface MeasurementContext {
  window_start?: string | null;
  window_end?: string | null;
  comparison_window_start?: string | null;
  comparison_window_end?: string | null;
  /** 'Actual' | 'Budget' | a plan version value — distinguishes same-named readings */
  version?: string | null;
  filters?: Record<string, unknown> | null;
  source_system?: string | null;
  data_product_id?: string | null;
  sql_hash?: string | null;
}

export interface Situation {
  situation_id: string;
  kpi_name: string;
  kpi_id?: string;
  kpi_value?: {
    value: number;
    unit: string;
    currency?: string;
    percent_change?: number | null;
    monthly_values?: Array<{ period: string; value: number; comparison_value?: number }>;
    inverse_logic?: boolean;
    threshold_value?: number | null;
    comparison_period?: string | null;
    comparison_type?: string | null;
    /**
     * What this reading actually measured — resolved, not requested. Mirrors
     * MeasurementContext on the backend KPIValue.
     *
     * `timeframe` alone is a token ("year_to_date") that different code paths can
     * resolve to different windows while both look correct. Absence means UNKNOWN
     * provenance and must never be read as agreement with another value.
     */
    context?: MeasurementContext | null;
  };
  severity: 'low' | 'medium' | 'high' | 'critical';
  card_type?: 'problem' | 'opportunity';
  direction?: 'up' | 'down';
  description: string;
  business_impact?: string;
  suggested_actions?: string[];
  top_drivers?: TopDriver[];
  timestamp?: string;
  key_observations?: string[];
  trend_note?: string | null;
  // Phase 11I — Advanced Alert Intelligence
  alert_type?: 'threshold_breach' | 'plan_variance' | 'projected_breach' | 'acceleration' | 'concentration' | 'covenant';
  plan_value?: number | null;
  projected_breach_at_period?: string | null;
  projection_confidence?: number | null;
  periods_until_breach?: number | null;
  acceleration_signal?: number | null;
  // Phase 11I-B — Compound cross-KPI alerts
  compound_alert?: boolean;
  related_kpi_id?: string | null;
  compound_pattern?: string | null;
  // Same-KPI multi-alert-type consolidation — present when this card folds together
  // more than one alert_type for the same KPI (e.g. threshold_breach + plan_variance)
  merged_alert_types?: string[] | null;
}

export interface OpportunitySignal {
  kpi_name: string;
  kpi_display_name: string;
  current_value: number;
  baseline_value: number;
  delta_pct: number;
  dimension?: string;
  dimension_value?: string;
  opportunity_type: string;
  headline: string;
  confidence: number;
}

export interface SituationDetectionResult {
  situations: Situation[];
  opportunities: OpportunitySignal[];
  kpi_evaluated_count?: number | null;
}

export interface ChangePoint {
  dimension: string;
  key: string;
  delta: number;
  current?: number;
  previous?: number;
}

export interface IsIsNotItem {
  dimension: string;
  key: string;
  current: number;
  previous: number;
  delta: number;
  text?: string;
  segment_type?: 'problem' | 'opportunity';
}

export interface BenchmarkSegment {
  dimension: string;
  key: string;
  current_value: number;
  previous_value: number;
  delta: number;
  delta_pct?: number;
  benchmark_type: 'control_group' | 'internal_benchmark';
  replication_potential?: number;
  effect_size_pct?: number;
  is_outlier?: boolean;
}

export interface KTIsIsNotData {
  where_is: IsIsNotItem[];
  where_is_not: IsIsNotItem[];
  what_is?: any[];
  what_is_not?: any[];
  when_is?: any[];
  when_is_not?: any[];
  benchmark_segments?: BenchmarkSegment[];
  /**
   * Mirrors `KTIsIsNot.dimension_totals`. Per-dimension overall movement as the
   * WAREHOUSE computed it (GROUP BY ROLLUP), keyed by dimension name — never the
   * sum of the member rows. A ratio's members cannot be added: summing gross
   * margin per product gives 452.95% against a true 29.43%. Consumers must render
   * nothing when absent rather than deriving a total.
   */
  dimension_totals?: Record<string, {
    current?: number | null;
    previous?: number | null;
    delta?: number | null;
    source?: 'rollup' | 'unavailable';
  }>;
}

export interface DeepAnalysisExecution {
  scqa_summary?: string;
  change_points?: ChangePoint[];
  kt_is_is_not?: KTIsIsNotData;
  when_started?: string;
  plan?: any;
  kpi_name?: string;
  analysis_mode?: 'problem' | 'opportunity' | 'mixed';
  mixed_framing?: boolean;
}

export interface DeepAnalysisResult {
  plan?: any;
  execution: DeepAnalysisExecution;
  market_signals?: MarketSignal[];
  replication_constraints?: string[];
}

export interface Perspective {
  lens: string;
  key_questions: string[];
  arguments_for: string[];
  arguments_against: string[];
}

// Phase 15 Stage B — unified trust/output schema. Mirrors
// src/agents/models/solution_finder_models.py; SolutionAssumption is the
// single typed object shared by Phase 11J P1 (validity monitoring) and
// Phase 15 (per-option "bets on" list) — do not add a second assumption type.
export interface SolutionAssumption {
  assumption: string;
  validated_by: 'sa_assessment' | 'ma_query' | 'human_confirmation';
  validated_at?: string | null;
  revalidation_days?: number | null;
  grounded?: boolean;
  confidence?: 'high' | 'moderate' | 'low' | null;
  provenance?: string | null;
}

export interface DecisionAsk {
  decision_text: string;
  decision_owner?: string | null;
  deadline?: string | null;
  approval_type?: string | null;
}

export interface ImmediateAction {
  action_text: string;
  owner?: string | null;
  due_by_days?: number | null;
  why_it_matters?: string | null;
}

export interface RecoveryRange {
  low?: number | null;
  high?: number | null;
}

export interface ImpactEstimate {
  metric?: string | null;
  unit?: string | null;
  recovery_range?: RecoveryRange | null;
  basis?: string | null;
  // Stage H scope qualifier. 'enterprise' = the range moves the headline KPI;
  // 'segment' = one dimension member only (scope_label names it). null/absent
  // means UNSTATED and must be rendered as unverified — never assumed
  // enterprise: live runs emitted segment-sized ranges (18.5-38pp) under the
  // enterprise KPI's name, sized from a single segment's decline.
  scope?: 'enterprise' | 'segment' | null;
  scope_label?: string | null;
}

// Stage H: theory-guided moderator verdict for one option. Present only when
// the backend ran the moderator arm (SF_ENABLE_THEORY_MODERATOR); mutually
// exclusive with cross_review in practice.
export interface ModeratorGrade {
  constraint_survival?: 'pass' | 'fail' | 'insufficient_data';
  violated_constraints?: string[];
  causal_grounding?: string; // named causal edge, 'ungrounded', or 'insufficient_data'
  arithmetic_consistency?: 'pass' | 'flag' | 'insufficient_data';
  arithmetic_note?: string | null;
  critic_findings_response?: { finding?: string; disposition?: 'answered' | 'standing' }[];
  grade_rationale?: string;
}

export interface SolutionOption {
  id: string;
  title: string;
  description: string;
  rationale?: string;
  cost: number;
  impact: number; // expected_impact in backend — 0-1 ranking score, distinct from impact_estimate below
  risk: number;
  time_to_value: string;
  reversibility: 'low' | 'medium' | 'high';
  perspectives: Perspective[];
  prerequisites: string[];
  implementation_triggers: string[];
  expected_impact?: number; // Alias for impact
  impact_estimate?: ImpactEstimate; // business-unit ($/pp) recovery range — was untyped, now matches backend
  key_assumptions?: SolutionAssumption[]; // Phase 15 Stage B: what this option bets on
  flagged_side_effects?: string[]; // Phase 15 Stage E: critic-pass findings, grounded in the causal graph — not yet rendered (Stage G Risk block)
}

export interface Recommendation {
  id: string;
  title: string;
  rationale: string;
}

export interface ProblemReframe {
  situation: string;
  complication: string;
  question: string;
  key_assumptions?: string[];
}

export interface UnresolvedTension {
  tension: string;
  requires?: string;
  options_affected?: string[];
}

export interface CrossReviewCritique {
  target: string;
  concern: string;
}

export interface CrossReviewEndorsement {
  target: string;
  reason: string;
}

export interface CrossReview {
  [personaId: string]: {
    critiques: CrossReviewCritique[];
    endorsements: CrossReviewEndorsement[];
  }
}

export interface SolutionResponse {
  options_ranked: SolutionOption[];
  recommendation?: Recommendation;
  recommendation_rationale?: string;
  problem_reframe?: ProblemReframe;
  blind_spots?: string[];
  unresolved_tensions?: UnresolvedTension[];
  next_steps?: string[];
  stage_1_hypotheses?: Record<string, {
    framework?: string;
    hypothesis?: string;
    key_evidence?: string[];
    recommended_focus?: string;
    conviction?: string;
  }>;
  cross_review?: CrossReview;
  // Stage H: moderator verdicts keyed by option id — populated by the moderator
  // arm INSTEAD of cross_review. Components must handle either shape (and old
  // localStorage briefings carrying neither).
  moderator_grades?: Record<string, ModeratorGrade>;
  // Phase 15 / Phase 13 Cat 2 — not yet rendered (Stage G, gated behind schema
  // compliance testing); typed here so API responses round-trip cleanly.
  decision_ask?: DecisionAsk;
  immediate_actions?: ImmediateAction[];
}

export interface Principal {
  id: string;
  name: string;
  title: string;
  initials: string;
  decision_style: 'analytical' | 'visionary' | 'pragmatic' | 'decisive';
  color: string;
}

export interface Client {
  id: string;
  name: string;
  industry: string;
  data_product_ids: string[];
}

export interface Council {
  id: string;
  label: string;
  description: string;
  icon?: any;
  color: string;
}

export interface Persona {
  id: string;
  label: string;
  type: 'firm' | 'role';
  icon?: any;
  color: string;
}

export interface RefinementExclusion {
  dimension: string;
  value: string;
  reason?: string;
}

export interface ProblemRefinementRequest {
  principal_id: string;
  deep_analysis_output: any;
  principal_context: any;
  conversation_history: Array<{ role: string; content: string }>;
  user_message?: string;
  current_topic?: string;
  turn_count: number;
  /**
   * Client-held conversation state echoed back each turn (Stage I B-1). The
   * refine endpoint is stateless by design; the server previously tried to
   * recover topics_completed by pattern-matching LLM prose, which never worked.
   */
  topics_completed?: string[];
  /** Turns spent on current_topic; reset by the client when the topic changes. */
  turns_on_current_topic?: number;
  /**
   * Typed refinement state from prior turns (Stage I B-2). Without these the
   * server re-derives earlier turns with a keyword extractor, which discards
   * constraint provenance and drops exclusions entirely.
   */
  prior_constraint_items?: ConstraintItem[];
  prior_exclusions?: RefinementExclusion[];
}

export interface ConstraintItem {
  id: string;
  text: string;
  source: 'refinement' | 'assumption_register' | 'kpi_relationship';
  /** Persona ids whose extractor surfaced this. Empty = every persona has it. */
  discovered_by?: string[];
  asked_by?: string | null;
  turn_index?: number | null;
}

export interface CouncilMemberRecommendation {
  category: string;
  persona_id: string;
  persona_name: string;
  rationale: string;
}

export interface MarketSignal {
  source: string
  title: string
  summary: string
  relevance_score: number
  published_at?: string
  url?: string
}

export interface MarketConflict {
  detected: boolean;
  type?: 'tailwind_vs_problem' | 'headwind_vs_opportunity';
  confidence?: number;
  summary?: string;
}

export interface ProblemRefinementResult {
  agent_message: string;
  suggested_responses: string[];
  exclusions: RefinementExclusion[];
  external_context: string[];
  constraints: string[];
  validated_hypotheses: string[];
  invalidated_hypotheses: string[];
  current_topic: string;
  topic_complete: boolean;
  topics_completed: string[];
  ready_for_solutions: boolean;
  refined_problem_statement?: string;
  recommended_council_type?: string;
  council_routing_rationale?: string;
  recommended_council_members?: CouncilMemberRecommendation[];
  turn_count: number;
  conversation_history: Array<{ role: string; content: string }>;
  market_signals?: MarketSignal[];
  replication_constraints?: string[];
  /**
   * Why this interview asked what it asked (Stage I B-1). The topic sequence is
   * routed off the problem's measured structure rather than fixed, so these
   * report the decision — without them a routed conversation is
   * indistinguishable from the default one.
   */
  problem_profile_cell?: string;
  topic_sequence?: string[];
  topic_routing_rules_applied?: string[];
  /** Accumulated constraints with provenance. `constraints` remains the flat union of texts. */
  constraint_items?: ConstraintItem[];
}

// ---------------------------------------------------------------------------
// Assessment Pipeline — Phase 9C
// ---------------------------------------------------------------------------

export interface MonitoringProfile {
  comparison_period: 'MoM' | 'QoQ' | 'YoY';
  volatility_band: number;
  min_breach_duration: number;
  confidence_floor: number;
  urgency_window_days: number;
}

export type AssessmentStatus = 'running' | 'complete' | 'error';

export type KPIAssessmentStatus = 'detected' | 'monitoring' | 'below_threshold' | 'error';

export interface AssessmentConfig {
  severity_floor: number;
  principal_id?: string | null;
  dry_run: boolean;
}

export interface AssessmentRun {
  id: string;
  started_at: string;
  completed_at?: string | null;
  status: AssessmentStatus;
  kpi_count: number;
  kpis_escalated: number;
  kpis_monitored: number;
  kpis_below_threshold: number;
  kpis_errored: number;
  config: AssessmentConfig;
}

export interface KPIAssessment {
  id: string;
  run_id: string;
  kpi_id: string;
  kpi_name?: string | null;
  kpi_value?: number | null;
  comparison_value?: number | null;
  severity?: number | null;
  confidence?: number | null;
  status: KPIAssessmentStatus;
  escalated_to_da: boolean;
  da_result?: Record<string, unknown> | null;
  benchmark_segments?: Record<string, unknown>[] | null;
  error_message?: string | null;
  created_at: string;
}

export interface AssessmentSummary {
  run: AssessmentRun;
  assessments: KPIAssessment[];
}
