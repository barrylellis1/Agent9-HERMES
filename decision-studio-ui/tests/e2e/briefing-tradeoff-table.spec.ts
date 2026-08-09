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
