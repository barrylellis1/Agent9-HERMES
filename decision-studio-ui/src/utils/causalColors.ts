import type { FramingAlternative } from '../api/types';

/**
 * Phase 20 §14 decision 8 — the connective tissue between the compact
 * right-panel FramingGateCard list and the left-panel "Causal Neighbourhood"
 * evidence section (chart + detailed cards): the SAME categorical hue for a
 * given KPI is used in both places, so someone answering a compact question
 * on the right can reference rich evidence on the left with no scroll-sync
 * or new interaction plumbing — just color.
 *
 * Dataviz skill categorical slots 1-3 (blue/orange/aqua, dark-mode steps),
 * validated with the skill's own validator against this app's actual
 * #020617 surface — see CausalTrendChart.tsx and problem_framing_design.md
 * §14 decision 7 for the full validation record. Primary KPI (the one being
 * framed) gets ink-white, never a categorical hue, so it's never confused
 * with a candidate being compared to it.
 */
export const CAUSAL_SECONDARY_HUES = ['#3987e5', '#d95926', '#199e70'];
export const CAUSAL_PRIMARY_HUE = '#ffffff';
/** Fallback for market_signal or any alternative with no kpi_id — never undefined/transparent. */
export const CAUSAL_FALLBACK_HUE = '#94a3b8'; // slate-400

/**
 * The ranked, capped `causal_graph` kpi_ids from a FramingPrompt's
 * `alternatives`, in the SAME order the backend already ranked them
 * (hop-tier first, then magnitude — see problem_framing_design.md §14
 * decision 3). Both the chart and the compact list derive their color from
 * THIS order, computed once and shared, so a re-render never silently
 * reassigns colors out of sync between the two panels.
 */
export function orderedCausalKpiIds(alternatives: FramingAlternative[]): string[] {
  return alternatives
    .filter(a => a.source === 'causal_graph' && !!a.kpi_id)
    .map(a => a.kpi_id as string);
}

/** Color for a specific KPI id, given the shared ranked order. */
export function causalColorFor(kpiId: string | null | undefined, ordered: string[]): string {
  if (!kpiId) return CAUSAL_FALLBACK_HUE;
  const idx = ordered.indexOf(kpiId);
  if (idx < 0) return CAUSAL_FALLBACK_HUE;
  return CAUSAL_SECONDARY_HUES[idx % CAUSAL_SECONDARY_HUES.length];
}

/**
 * Short label for an alternative — the neighbour KPI's own name, not the
 * full templated sentence ("Addressing X instead of Y directly — connected
 * N hops..."). Used by both the compact right-panel list (which has no room
 * for the full sentence) and the trend chart's legend/end-labels. Falls back
 * to kpi_id or the raw objective_text when the template doesn't match (a
 * market_signal alternative, or a future template change).
 */
export function alternativeShortLabel(alt: { source: string; objective_text: string; kpi_id?: string | null }): string {
  if (alt.source === 'market_signal') return 'External market signal';
  const m = alt.objective_text.match(/^Addressing (.+?) instead of/);
  return m ? m[1] : (alt.kpi_id || alt.objective_text);
}
