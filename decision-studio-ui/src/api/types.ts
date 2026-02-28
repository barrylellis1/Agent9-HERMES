export interface Situation {
  situation_id: string;
  kpi_name: string;
  kpi_value?: {
    value: number;
    unit: string;
    currency?: string;
  };
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  business_impact?: string;
  suggested_actions?: string[];
  timestamp?: string;
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

export interface KTIsIsNotData {
  where_is: IsIsNotItem[];
  where_is_not: IsIsNotItem[];
  what_is?: any[];
  what_is_not?: any[];
  when_is?: any[];
  when_is_not?: any[];
}

export interface DeepAnalysisExecution {
  scqa_summary?: string;
  change_points?: ChangePoint[];
  kt_is_is_not?: KTIsIsNotData;
  when_started?: string;
  plan?: any;
  kpi_name?: string;
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
}
