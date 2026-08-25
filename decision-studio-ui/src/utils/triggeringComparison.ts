import type { Situation } from '../api/types';

/**
 * The number that actually triggered a situation's severity, when it differs
 * from the KPI's YoY/MoM/QoQ percent_change.
 *
 * Found live 2026-08-24: a KPI tile always displays kpi_value.percent_change
 * (the YoY comparison) as its headline deviation figure, regardless of which
 * detection pattern (Phase 11I-A) actually produced the severity. A
 * plan_variance-primary situation — e.g. Net Revenue +3.2% YoY, badged
 * CRITICAL via a budget variance the tile never showed — reads as "up 3.2%
 * and critical" with no visible reason. The percentage shown was not the
 * percentage that fired the alert.
 *
 * This recomputes the plan-variance percentage from fields already shipped
 * to the frontend (Situation.plan_value, KPIValue.value) — the identical
 * arithmetic A9_Situation_Awareness_Agent runs server-side
 * (variance_pct = (value - plan_value) / abs(plan_value)) — rather than
 * requiring a new backend field.
 *
 * Returns null when the situation's primary alert_type is anything else
 * (threshold_breach, acceleration, projected_breach, covenant, regulatory),
 * or when plan_value is unavailable — callers should fall back to
 * kpi_value.percent_change / the existing YoY-style comparisonLabel in that
 * case. projected_breach and acceleration are deliberately not handled here:
 * neither carries a stored value on Situation that reconstructs the number
 * that actually crossed their threshold (projected_breach has no stored
 * projected value; acceleration's own signal is a normalised magnitude, not
 * a percentage a reader would recognise) — closing those needs a new
 * backend field, not a frontend recomputation, and is out of scope here.
 */
export interface TriggeringComparison {
  /** Percentage value, already scaled (e.g. 12.4 means "12.4%"), signed. */
  value: number;
  /** Short label describing what it's measured against, e.g. "vs Plan". */
  label: string;
}

export function getTriggeringComparison(situation: Situation): TriggeringComparison | null {
  if (situation.alert_type !== 'plan_variance') return null;

  const planValue = situation.plan_value;
  const actualValue = situation.kpi_value?.value;
  if (planValue == null || actualValue == null || Math.abs(planValue) === 0) return null;

  const variancePct = ((actualValue - planValue) / Math.abs(planValue)) * 100;
  if (!isFinite(variancePct)) return null;

  return { value: variancePct, label: 'vs Plan' };
}
