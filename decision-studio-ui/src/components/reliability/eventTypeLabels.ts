/**
 * Shared display labels for the stage-wise reliability.* event family
 * (docs/architecture/audit_event_system_design.md), used by both the
 * operator ReliabilityPanel and the analyst ReliabilityDrillDown so the two
 * surfaces can't drift into naming the same signal differently.
 */
export const RELIABILITY_EVENT_TYPE_LABELS: Record<string, string> = {
  'reliability.detection_confidence': 'SA — Detection confidence',
  'reliability.kpi_coverage': 'SA — KPI coverage',
  'reliability.rollup_check': 'DA — Variance rollup check',
  'reliability.slice_validity': 'DGA — Slice validity',
  'reliability.tree_reconciliation': 'Theory layer — Tree reconciliation',
  'reliability.citation_quality': 'MA — Citation quality',
  'reliability.decision_quality': 'SF — Decision Quality link',
}

export function reliabilityEventLabel(eventType: string): string {
  return RELIABILITY_EVENT_TYPE_LABELS[eventType] ?? eventType
}
