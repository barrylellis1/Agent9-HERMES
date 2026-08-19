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
): { periods: string[]; series: TrendSeries[] } | null {
  const all = [
    { kpiId: primary.kpiId, label: primary.label, isPrimary: true, monthly: primary.snapshot?.monthly_values },
    ...secondaries.map(s => ({ kpiId: s.kpiId, label: s.label, isPrimary: false, monthly: s.snapshot?.monthly_values })),
  ];
  const withData = all.filter(a => a.monthly && a.monthly.length >= 2);
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

  if (!series.some(s => s.isPrimary)) return null; // no chart without a reference line
  return series.length > 0 ? { periods, series } : null;
}
