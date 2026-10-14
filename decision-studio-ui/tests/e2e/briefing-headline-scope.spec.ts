import { test, expect } from '@playwright/test';
import { buildExecutiveBriefing, cardComparisonValue, aggregateIsAdverse } from '../../src/utils/briefingUtils';

/**
 * Which figure heads the briefing — pure-function tests, no browser, no LLM.
 *
 * Found live 2026-10-14 (production, lubricants Gross Margin %): the business fell
 * 34.43% -> 29.95% (4.48 points) against prior year, and every one of 75 segments fell.
 * The header read "Gross Margin % — Product Name: Synthetic Blend Engine Oil", "Why now"
 * showed that product's -7.14pp, and the model turned the mismatch into an FP&A task to
 * reconcile the two figures. Separately, no enterprise option range was ever shown as a
 * share of the decline, because the decline was read from a field Deep Analysis never
 * produces.
 */

const SYNTH = { dimension: 'product_name', key: 'Synthetic Blend Engine Oil', current: 20.62, previous: 27.76, delta: -7.14 };

function gmSituation(overrides: any = {}) {
  return {
    kpi_name: 'Gross Margin %',
    card_type: 'problem',
    alert_type: 'threshold_breach',
    description: 'Gross Margin % fell 4.5 points (13.0%) vs prior year',
    kpi_value: { value: 29.95, comparison_value: 34.43, percent_change: -13.0, unit: '%', inverse_logic: false },
    ...overrides,
  };
}

test.describe('the headline is the business when the business declined', () => {
  test('a decline everywhere heads with the KPI, not the worst segment', () => {
    const b: any = buildExecutiveBriefing(gmSituation(), { change_points: [SYNTH] }, { options_ranked: [] });
    expect(b.kpiData.kpi_name).toBe('Gross Margin %');
    expect(b.kpiData.measurement_scope).toBe('enterprise');
    expect(b.kpiData.current_value).toBe(29.95);
    expect(b.kpiData.comparison_value).toBe(34.43);
  });

  test('the mixed case still heads with the declining segment', () => {
    const up = gmSituation({ kpi_value: { value: 36.0, comparison_value: 34.43, percent_change: 4.6, unit: '%', inverse_logic: false } });
    const b: any = buildExecutiveBriefing(up, { change_points: [SYNTH] }, { options_ranked: [] });
    expect(b.kpiData.measurement_scope).toBe('segment');
    expect(b.kpiData.kpi_name).toContain('Synthetic Blend Engine Oil');
  });

  test('a cost that rose is adverse; one that fell is not', () => {
    const cost = (v: number) => ({ kpi_value: { value: v, comparison_value: 100, inverse_logic: true } });
    expect(aggregateIsAdverse(cost(110), 100)).toBe(true);
    expect(aggregateIsAdverse(cost(90), 100)).toBe(false);
    expect(aggregateIsAdverse(cost(110), null)).toBe(false);
  });
});

test.describe('the comparison the card was raised against', () => {
  test('a plan-variance card is compared with the plan, not prior year', () => {
    const s = { alert_type: 'plan_variance', plan_value: 50.9, kpi_value: { value: 42.68, comparison_value: 41.42 } };
    expect(cardComparisonValue(s, {})).toBe(50.9);
  });

  test('otherwise the KPI comparison value; a Deep Analysis aggregate only as a last resort', () => {
    expect(cardComparisonValue({ kpi_value: { comparison_value: 34.43 } }, { aggregates: { comparison_value: 1 } })).toBe(34.43);
    expect(cardComparisonValue({ kpi_value: {} }, { aggregates: { comparison_value: 7 } })).toBe(7);
    expect(cardComparisonValue({}, {})).toBeNull();
  });

  test('an enterprise range larger than the whole decline is now shown as a share and flagged', () => {
    const opt = {
      id: 'opt_2', title: 'Tiered price escalators', description: 'd', expected_impact: 0.6, cost: 0.3, risk: 0.3,
      impact_estimate: { metric: 'Gross Margin %', unit: '%', basis: 'b', scope: 'enterprise', scope_label: null,
                         recovery_range: { low: 2.1, high: 4.8 } },
    };
    const b: any = buildExecutiveBriefing(gmSituation(), { change_points: [SYNTH] }, { options_ranked: [opt], recommendation: { id: 'opt_2' } });
    const roi = String(b.options[0].roi);
    expect(roi).toContain('of the enterprise decline');
    expect(roi).toContain('exceeds the loss');
  });
});
