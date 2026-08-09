import { test, expect } from '@playwright/test';
import { axisDiscrimination } from '../../src/utils/briefingUtils';

/**
 * Trade-off table discrimination — pure functions, no browser, no LLM.
 *
 * THE DEFECT
 * ----------
 * A live 12-page briefing laid out three options in a comparison table:
 *
 *              Option A          Option B          Option C
 *   Est. ROI   +3.2 to +5.1pp    +2.8 to +4.2pp    +3.2 to +5.1pp   <- A == C
 *   Investment Moderate Effort   Moderate Effort   Moderate Effort  <- all same
 *   Risk       Medium            Medium            Medium           <- all same
 *   Timeline   30-60 days        6-9 months        12-18 months     <- the only signal
 *
 * Three of four rows separated nothing, while being presented as a comparison an
 * executive should choose from. The single row carrying the whole decision sat
 * among them unmarked. And a 12-18 month contract renegotiation claiming the
 * same benefit as a 30-60 day pricing action is not credible on its face.
 *
 * Root cause is upstream — expected_impact / cost / risk are 0-1 values the model
 * assigns in the same call that writes the options, so they cluster, and
 * _rank_options wraps that clustering in a weighted formula resembling rigour.
 * That is a separate change. This makes the table stop overstating itself.
 */
test.describe('axisDiscrimination', () => {
  test('flags a criterion every option shares', () => {
    const d = axisDiscrimination(['Moderate Effort', 'Moderate Effort', 'Moderate Effort']);
    expect(d.uniform).toBe(true);
    expect(d.partial).toBe(false);
    expect(d.distinct).toBe(1);
  });

  test('flags the real Est. ROI case where two of three tie', () => {
    const d = axisDiscrimination([
      '+3.2pp to +5.1pp — Synthetic Blend Engine Oil only',
      '+2.8pp to +4.2pp — Engine Oils product line only',
      '+3.2pp to +5.1pp — Synthetic Blend Engine Oil only',
    ]);
    expect(d.uniform).toBe(false);
    expect(d.partial).toBe(true);
    expect(d.distinct).toBe(2);
    expect(d.total).toBe(3);
  });

  test('a fully discriminating criterion is marked neither way', () => {
    const d = axisDiscrimination(['30-60 days', '6-9 months', '12-18 months']);
    expect(d.uniform).toBe(false);
    expect(d.partial).toBe(false);
    expect(d.distinct).toBe(3);
  });

  test('reversibility discriminates on the real payload — which is why it was added', () => {
    const d = axisDiscrimination(['high', 'medium', 'low']);
    expect(d.distinct).toBe(3);
    expect(d.uniform).toBe(false);
  });

  test('comparison ignores case and surrounding whitespace', () => {
    // "Medium" and "medium " are the same answer; treating them as different
    // would manufacture discrimination that does not exist.
    const d = axisDiscrimination(['Medium', 'medium ', ' MEDIUM']);
    expect(d.uniform).toBe(true);
  });

  test('empty and missing values are excluded, not counted as a distinct answer', () => {
    // An absent value is not evidence of a difference.
    const d = axisDiscrimination(['Moderate Effort', null, undefined, '']);
    expect(d.total).toBe(1);
    expect(d.uniform).toBe(false);   // one value cannot be "same for all"
    expect(d.partial).toBe(false);
  });

  test('a single option is never marked uniform', () => {
    // With one option there is no comparison to make, so neither label applies.
    const d = axisDiscrimination(['Moderate Effort']);
    expect(d.uniform).toBe(false);
    expect(d.partial).toBe(false);
  });

  test('no options at all degrades quietly', () => {
    const d = axisDiscrimination([]);
    expect(d.total).toBe(0);
    expect(d.uniform).toBe(false);
    expect(d.partial).toBe(false);
  });
});

/**
 * Effort and risk banding.
 *
 * CORRECTION TO THE ORIGINAL DIAGNOSIS. The first read was that the model's
 * scores clustered. Measured across nine captured SF runs, they do not:
 *
 *   risk  0.45 / 0.55 / 0.65   -> "Medium", "Medium", "Medium"
 *   cost  0.25 / 0.30 / 0.50   -> "Low", "Low", "Moderate"
 *
 * A 20-point spread rendered identically, because the bands were
 * >=0.7 High / >=0.4 Medium / else Low. The DISPLAY was destroying
 * differentiation the model had supplied.
 */
test.describe('effort and risk banding preserves real differences', () => {
  // Mirrors the five-band maps in buildExecutiveBriefing.
  const risk = (r: number) =>
    r >= 0.8 ? 'Very High' : r >= 0.6 ? 'High' : r >= 0.4 ? 'Medium' : r >= 0.2 ? 'Low' : 'Very Low';
  const cost = (c: number) =>
    c >= 0.8 ? 'Very High Effort' : c >= 0.6 ? 'High Effort' : c >= 0.4 ? 'Moderate Effort'
      : c >= 0.2 ? 'Low Effort' : 'Minimal Effort';

  test('the observed risk spread no longer collapses to one label', () => {
    const labels = [0.45, 0.55, 0.65].map(risk);
    expect(new Set(labels).size).toBeGreaterThan(1);
    expect(axisDiscrimination(labels).uniform).toBe(false);
  });

  test('the observed cost spread stays separated', () => {
    const labels = [0.25, 0.30, 0.50].map(cost);
    expect(new Set(labels).size).toBeGreaterThan(1);
  });

  test('values genuinely close together still share a band — and that is correct', () => {
    // 0.52 / 0.55 really are the same judgement. Splitting them would invent
    // precision that a 0-1 model estimate does not carry.
    expect(risk(0.52)).toBe(risk(0.55));
    expect(axisDiscrimination([risk(0.52), risk(0.55)]).uniform).toBe(true);
  });

  test('band boundaries are ordered and total', () => {
    const seen = [0, 0.19, 0.2, 0.39, 0.4, 0.59, 0.6, 0.79, 0.8, 1].map(risk);
    expect(seen.every(Boolean)).toBe(true);
    expect(new Set(seen).size).toBe(5);
  });
});
