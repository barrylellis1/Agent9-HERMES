import { test, expect } from '@playwright/test';
import { buildExecutiveBriefing, projectKpiTrend } from '../../src/utils/briefingUtils';

/**
 * Cost-of-Inaction trend direction — pure-function tests, no browser, no LLM.
 *
 * THE BUG
 * -------
 * A real briefing told a CFO "Trend: Recovering | Confidence: High" directly
 * above numbers that got worse every period:
 *
 *     In 30 days: $-58.3M (-$601K)
 *     In 90 days: $-59.5M (-$1.8M)
 *
 * Cause: `percent_change = delta / prev`. For a DECLINING segment both values
 * are negative, so the negatives cancel to a POSITIVE ratio, which the banner
 * reads as improvement — while the projection multiplies a negative current
 * value by (1 + rate) and drives it further negative. Label and arithmetic
 * disagreed because the direction of change was destroyed by the division.
 *
 * Dividing by the MAGNITUDE of the prior value preserves the numerator's sign,
 * which is the actual direction of travel.
 *
 * The enterprise branch is also pinned here: it must CONSUME the backend's
 * typed `KPIValue.percent_change` (which SA already resolved correctly,
 * inverse_logic included) and never recompute it.
 */

// Verbatim from the real briefing: Chain A gross profit, both values negative.
const CHAIN_A_CURRENT = -57_700_000;
const CHAIN_A_PRIOR = -51_200_000;
const CHAIN_A_DELTA = -6_409_279;

function analysisWithDecliningSegment() {
  return {
    change_points: [{
      dimension: 'customer_name', key: 'National Auto Parts Chain A',
      current: CHAIN_A_CURRENT, previous: CHAIN_A_PRIOR, delta: CHAIN_A_DELTA,
    }],
    kt_is_is_not: { where_is: [] },
    aggregates: { comparison_value: 50_800_000 },
  };
}

function situation(kpiValue: any = {}) {
  return {
    kpi_name: 'Gross Profit', severity: 'critical',
    kpi_value: { value: 34_100_000, unit: '$', ...kpiValue },
  };
}

const SOL = { options_ranked: [], recommendation: {} };

function kpiData(sit: any, ana: any) {
  return (buildExecutiveBriefing(sit, ana, SOL, []) as any).kpiData;
}

test.describe('Cost of Inaction — trend direction', () => {
  test('REGRESSION: a declining segment is not reported as recovering', async () => {
    const kd = kpiData(situation(), analysisWithDecliningSegment());

    // The sign of percent_change IS the direction. Negative = deteriorating.
    expect(kd.percent_change).toBeLessThan(0);
    expect(kd.percent_change).toBeCloseTo(CHAIN_A_DELTA / Math.abs(CHAIN_A_PRIOR), 5);

    // The old formula produced +0.125 and printed "Recovering".
    const oldBuggy = CHAIN_A_DELTA / CHAIN_A_PRIOR;
    expect(oldBuggy).toBeGreaterThan(0);
    expect(Math.sign(kd.percent_change)).not.toBe(Math.sign(oldBuggy));
  });

  test('direction survives when both current and prior are negative', async () => {
    // The specific arithmetic trap: negatives cancelling under division.
    const kd = kpiData(situation(), analysisWithDecliningSegment());
    expect(kd.current_value).toBeLessThan(0);
    expect(kd.comparison_value).toBeLessThan(0);
    expect(kd.percent_change).toBeLessThan(0);
  });

  test('an improving segment still reads as improving', async () => {
    // Guard against over-correcting into "always negative".
    const ana = {
      change_points: [
        { dimension: 'd', key: 'Falling', current: -10, previous: -8, delta: -2 },
        { dimension: 'd', key: 'Rising', current: 12, previous: 8, delta: 4 },
      ],
      kt_is_is_not: { where_is: [] }, aggregates: {},
    };
    const kd = kpiData(situation(), ana);
    // The worst DECLINER is selected for the warning, by design.
    expect(kd.segment_label).toBe('Falling');
    expect(kd.percent_change).toBeLessThan(0);
  });

  test('segment slices are labelled as segments, not as the enterprise KPI', async () => {
    const kd = kpiData(situation(), analysisWithDecliningSegment());
    expect(kd.measurement_scope).toBe('segment');
    expect(kd.segment_label).toBe('National Auto Parts Chain A');
    expect(kd.kpi_name).toContain('National Auto Parts Chain A');
  });
});

test.describe('Enterprise branch — consume, never recompute', () => {
  const noDecliners = { change_points: [], kt_is_is_not: { where_is: [] }, aggregates: { comparison_value: 50_800_000 } };

  test('uses the backend percent_change verbatim', async () => {
    // SA resolves this correctly (inverse_logic included) and stamps provenance.
    // Re-deriving it in the UI is what put a wrong number in front of a CFO.
    const kd = kpiData(situation({ percent_change: -0.144 }), noDecliners);
    expect(kd.percent_change).toBe(-0.144);
    expect(kd.measurement_scope).toBe('enterprise');
  });

  test('does not invent a percent_change when the backend supplies none', async () => {
    const kd = kpiData(situation({ percent_change: null }), noDecliners);
    expect(kd.percent_change).toBeNull();
  });

  test('carries the resolved measurement window through to the briefing', async () => {
    const kd = kpiData(situation({
      percent_change: -0.144,
      context: { window_start: '2026-01-01', window_end: '2026-08-08', version: 'Actual', source_system: 'bigquery' },
    }), noDecliners);
    expect(kd.context.window_start).toBe('2026-01-01');
    expect(kd.context.version).toBe('Actual');
  });

  test('absent context is null, never fabricated', async () => {
    // Unknown provenance must stay visibly unknown.
    const kd = kpiData(situation({ percent_change: -0.1 }), noDecliners);
    expect(kd.context ?? null).toBeNull();
  });
});

test.describe('projectKpiTrend — the number an executive reads first', () => {
  test('REGRESSION: negative KPI deteriorating projects MORE negative', async () => {
    // The real case. Multiplicative projection moved this toward zero and
    // rendered deterioration as improvement.
    const r = projectKpiTrend(CHAIN_A_CURRENT, CHAIN_A_DELTA / Math.abs(CHAIN_A_PRIOR));
    expect(r.trend).toBe('deteriorating');
    expect(r.projected30d).toBeLessThan(CHAIN_A_CURRENT);
    expect(r.projected90d).toBeLessThan(r.projected30d);
    // Matches the figures the real briefing printed, now with the right label.
    expect(r.projected30d / 1e6).toBeCloseTo(-58.3, 1);
    expect(r.projected90d / 1e6).toBeCloseTo(-59.5, 1);
  });

  test('positive KPI deteriorating projects downward', async () => {
    const r = projectKpiTrend(100, -0.12);
    expect(r.trend).toBe('deteriorating');
    expect(r.projected30d).toBeCloseTo(99.0, 1);
    expect(r.projected90d).toBeLessThan(r.projected30d);
  });

  test('positive KPI recovering projects upward', async () => {
    const r = projectKpiTrend(100, 0.12);
    expect(r.trend).toBe('recovering');
    expect(r.projected30d).toBeGreaterThan(100);
  });

  test('negative KPI recovering moves toward zero', async () => {
    const r = projectKpiTrend(-1000, 0.12);
    expect(r.trend).toBe('recovering');
    expect(r.projected30d).toBeGreaterThan(-1000);
  });

  test('accepts percent-points as well as fractions', async () => {
    // percent_change arrives either way depending on source.
    expect(projectKpiTrend(100, -12).projected30d).toBeCloseTo(projectKpiTrend(100, -0.12).projected30d, 6);
  });

  test('falls back to comparison_value, preserving direction', async () => {
    // |comparison| as denominator — the same trap as percent_change.
    const r = projectKpiTrend(-57.7e6, null, -51.2e6);
    expect(r.trend).toBe('deteriorating');
    expect(r.projected30d).toBeLessThan(-57.7e6);
  });

  test('flat KPI is stable, not a spurious direction', async () => {
    expect(projectKpiTrend(100, 0).trend).toBe('stable');
    expect(projectKpiTrend(100, null).trend).toBe('stable');
    expect(projectKpiTrend(100, 0).projected30d).toBe(100);
  });

  test('caps an implausible rate instead of projecting to absurdity', async () => {
    // percent_change is sometimes a raw delta, not a percentage.
    const r = projectKpiTrend(100, -50000);
    expect(Math.abs(r.monthlyRate)).toBeLessThanOrEqual(1 / 12 + 1e-9);
    expect(r.projected90d).toBeGreaterThan(50);
  });
});
