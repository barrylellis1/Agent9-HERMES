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

export interface Situation {
  situation_id: string;
  kpi_name: string;
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
  };
  severity: 'low' | 'medium' | 'high' | 'critical';
  card_type?: 'problem' | 'opportunity';
  description: string;
  business_impact?: string;
  suggested_actions?: string[];
  top_drivers?: TopDriver[];
  timestamp?: string;
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
}

export interface KTIsIsNotData {
  where_is: IsIsNotItem[];
  where_is_not: IsIsNotItem[];
  what_is?: any[];
  what_is_not?: any[];
  when_is?: any[];
  when_is_not?: any[];
  benchmark_segments?: BenchmarkSegment[];
}

export interface DeepAnalysisExecution {
  scqa_summary?: string;
  change_points?: ChangePoint[];
  kt_is_is_not?: KTIsIsNotData;
  when_started?: string;
  plan?: any;
  kpi_name?: string;
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

export interface SolutionOption {
  id: string;
  title: string;
  description: string;
  rationale?: string;
  cost: number;
  impact: number; // expected_impact in backend
  risk: number;
  time_to_value: string;
  reversibility: 'low' | 'medium' | 'high';
  perspectives: Perspective[];
  prerequisites: string[];
  implementation_triggers: string[];
  expected_impact?: number; // Alias for impact
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
