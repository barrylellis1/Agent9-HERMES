import type { NeighbourSnapshot } from '../api/types';
import type { TrendSeries } from '../components/visualizations/CausalTrendChart';

/**
 * Builds CausalTrendChart's `periods`/`series` props from raw
 * NeighbourSnapshot.monthly_values (Phase 20 §14 decision 7). Each series is
 * indexed to "% change from ITS OWN first available data point" — not
 * necessarily the same calendar period as another series' baseline, since a
 * KPI's monthly window (LIMIT num_months, most-recent-first) isn't
 * guaranteed to start on the same month as a different KPI's. Periods are
 * the UNION across every series, sorted ascending, so nothing is silently
 * misaligned by raw array index.
 *
 * A series with no usable baseline (no monthly_values, or a zero-value
 * first point — can't compute a meaningful % change from zero) is DROPPED,
 * not shown as a broken/fabricated line — degrades to fewer lines, never a
 * wrong one. If the PRIMARY KPI itself has no usable trend, returns null —
 * a chart with candidate lines but no reference line defeats the point.
 */
export function buildCausalTrendChart(
  primary: { kpiId: string; label: string; snapshot: NeighbourSnapshot | null | undefined },
  secondaries: Array<{ kpiId: string; label: string; snapshot: NeighbourSnapshot | null | undefined }>,
): { periods: string[]; series: TrendSeries[]; omitted: string[] } | null {
  const all = [
    { kpiId: primary.kpiId, label: primary.label, isPrimary: true, monthly: primary.snapshot?.monthly_values },
    ...secondaries.map(s => ({ kpiId: s.kpiId, label: s.label, isPrimary: false, monthly: s.snapshot?.monthly_values })),
  ];
  const withData = all.filter(a => a.monthly && a.monthly.length >= 2);
  // Phase 25 step 1: report what was dropped instead of just omitting it. A
  // missing line and a flat line are indistinguishable to a reader, which is
  // how a failing fetch survived to a live screenshot -- the trend fetch is
  // non-fatal by design (correctly), but silence at the UI is not.
  const omitted: string[] = all.filter(a => !(a.monthly && a.monthly.length >= 2)).map(a => a.label);
  if (withData.length === 0) return null;

  const periodSet = new Set<string>();
  withData.forEach(a => a.monthly!.forEach(m => periodSet.add(m.period)));
  const periods = Array.from(periodSet).sort();

  const series: TrendSeries[] = [];
  for (const a of withData) {
    const byPeriod = new Map(a.monthly!.map(m => [m.period, m.value]));
    const baseline = periods.map(p => byPeriod.get(p)).find(v => v !== undefined && v !== null && v !== 0);
    if (baseline === undefined || baseline === null) continue; // no usable baseline for this one series
    const indexedValues = periods.map(p => {
      const v = byPeriod.get(p);
      if (v === undefined || v === null) return null;
      return ((v - baseline) / Math.abs(baseline)) * 100;
    });
    series.push({ kpiId: a.kpiId, label: a.label, isPrimary: a.isPrimary, indexedValues });
  }
  // A series with data but no usable baseline (all-zero or all-null first
  // point) is dropped in the loop above; count it as omitted too.
  for (const a of withData) {
    if (!series.some(s2 => s2.kpiId === a.kpiId)) omitted.push(a.label);
  }

  if (!series.some(s => s.isPrimary)) return null; // no chart without a reference line
  return series.length > 0 ? { periods, series, omitted } : null;
}
