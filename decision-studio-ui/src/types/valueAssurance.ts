export type SolutionVerdict = 'VALIDATED' | 'PARTIAL' | 'FAILED' | 'MEASURING';
export type ConfidenceLevel = 'HIGH' | 'MODERATE' | 'LOW';
export type StrategyAlignment = 'ALIGNED' | 'DRIFTED' | 'SUPERSEDED';

export interface StrategySnapshot {
  principal_priorities: string[];
  principal_role: string;
  business_process_domain: string;
  data_product_id: string;
  kpi_threshold_at_approval: number;
  key_assumptions: string[];
  business_context_name: string;
  strategic_rationale?: string;
  captured_at: string;
}

export interface StrategyAlignmentCheck {
  original_priorities: string[];
  current_priorities: string[];
  priority_drift: boolean;
  priority_overlap: number;
  kpi_still_monitored: boolean;
  threshold_changed: boolean;
  current_threshold?: number;
  business_process_active: boolean;
  data_product_active: boolean;
  principal_still_accountable: boolean;
  current_principal_id?: string;
  alignment_verdict: StrategyAlignment;
  drift_factors: string[];
  drift_summary?: string;
}

export interface CompositeVerdict {
  kpi_verdict: SolutionVerdict;
  strategy_verdict: StrategyAlignment;
  composite_label: string;
  include_in_roi_totals: boolean;
  recommended_action: string;
  executive_attention_required: boolean;
}

export interface ImpactEvaluation {
  solution_id: string;
  baseline_kpi_value: number;
  current_kpi_value: number;
  total_kpi_change: number;
  control_group_change: number;
  market_driven_recovery: number;
  seasonal_component: number;
  attributable_impact: number;
  expected_impact_lower: number;
  expected_impact_upper: number;
  verdict: SolutionVerdict;
  confidence: ConfidenceLevel;
  confidence_rationale: string;
  attribution_method: string;
  control_group_description?: string;
  market_context_summary?: string;
  strategy_check: StrategyAlignmentCheck;
  composite_verdict: CompositeVerdict;
  evaluated_at: string;
}

export interface InactionCostProjection {
  solution_id: string;
  kpi_id: string;
  current_kpi_value: number;
  projected_kpi_value_30d: number;
  projected_kpi_value_90d: number;
  estimated_revenue_impact_30d?: number;
  estimated_revenue_impact_90d?: number;
  trend_direction: 'deteriorating' | 'stable' | 'recovering';
  trend_confidence: ConfidenceLevel;
  projection_method: string;
  projected_at: string;
}

export interface AcceptedSolution {
  solution_id: string;
  situation_id: string;
  kpi_id: string;
  principal_id: string;
  approved_at: string;
  solution_description: string;
  expected_impact_lower: number;
  expected_impact_upper: number;
  measurement_window_days: number;
  status: SolutionVerdict;
  strategy_snapshot: StrategySnapshot;
  impact_evaluation?: ImpactEvaluation;
  inaction_cost?: InactionCostProjection;
  narrative?: string;
  da_is_not_dimensions?: string[];
  ma_market_signals?: string[];
}
