import { test, expect } from '@playwright/test';
import { condenseTimeToValue } from '../../src/utils/briefingUtils';

/**
 * Time to Value tile — pure-function tests, no browser, no LLM.
 *
 * THE DEFECT
 * ----------
 * `time_to_value` is free prose written by the model, and the model is often
 * expansive. A live production briefing rendered this into a quarter-width
 * metric tile:
 *
 *   "Interim cost-offset actions deliverable in 30-60 days; full escalation
 *    clause activation and quarter-end price reset achievable within one fiscal
 *    quarter, aligning with..."
 *
 * The card overflowed and read as unfinished work — the kind of detail a
 * prospect notices before they notice the analysis. The tile wants the
 * duration; the full sentence survives as a tooltip.
 *
 * The rule that matters most here is the FIRST test: a value that already fits
 * must pass through untouched. A condenser that mangles well-behaved input
 * trades a rare cosmetic bug for a constant one.
 */
test.describe('condenseTimeToValue', () => {
  test('leaves an already-short value completely alone', () => {
    expect(condenseTimeToValue('3-6 months')).toBe('3-6 months');
    expect(condenseTimeToValue('90 days')).toBe('90 days');
    expect(condenseTimeToValue('Q3')).toBe('Q3');
  });

  test('extracts the duration from the real overflowing production string', () => {
    const actual =
      'Interim cost-offset actions deliverable in 30-60 days; full escalation clause ' +
      'activation and quarter-end price reset achievable within one fiscal quarter, ' +
      'aligning with the Q3 contract renewal window';
    expect(condenseTimeToValue(actual)).toBe('30-60 days');
  });

  test('prefers the range over a bare number appearing later', () => {
    // "30-60 days" must win over the "60 days" nested inside it, and over the
    // "12 months" mentioned downstream.
    const s = 'Phased rollout over 30-60 days with full run-rate benefit after 12 months';
    expect(condenseTimeToValue(s)).toBe('30-60 days');
  });

  test('handles en-dash and em-dash ranges, not just hyphens', () => {
    const s = 'Benefits begin to accrue in 6–12 weeks once the clause is countersigned';
    expect(condenseTimeToValue(s)).toBe('6–12 weeks');
  });

  test('falls back to a written-out duration when no digits are present', () => {
    const s = 'Full realisation is expected within one fiscal quarter of board approval, ' +
              'assuming procurement moves in parallel';
    expect(condenseTimeToValue(s)).toBe('Within one fiscal quarter');
  });

  test('truncates on a word boundary when nothing resembles a duration', () => {
    const s = 'Dependent entirely on supplier responsiveness and the outcome of ' +
              'ongoing commercial discussions';
    const out = condenseTimeToValue(s);
    expect(out.endsWith('…')).toBe(true);
    expect(out.length).toBeLessThanOrEqual(30);
    // Word boundary, not mid-word. Checking the char before the ellipsis is
    // useless — a word-boundary cut always ends on a letter. What must be true
    // is that the kept text is a prefix of the input ending where a space was.
    const kept = out.slice(0, -1);
    expect(s.startsWith(kept)).toBe(true);
    expect(s.charAt(kept.length)).toBe(' ');
  });

  test('empty and null degrade to an em-dash rather than throwing', () => {
    // The tile previously rendered `recOption?.timeline || '—'`, so absent data
    // was already handled upstream; the condenser must not regress that.
    expect(condenseTimeToValue('')).toBe('—');
    expect(condenseTimeToValue(null)).toBe('—');
    expect(condenseTimeToValue(undefined)).toBe('—');
  });

  test('never returns something longer than the prose it condensed', () => {
    const inputs = [
      '3-6 months',
      'Immediate',
      'Interim actions in 30-60 days; full activation within one fiscal quarter',
      'Dependent on supplier responsiveness and commercial discussions ongoing',
    ];
    for (const s of inputs) {
      expect(condenseTimeToValue(s).length).toBeLessThanOrEqual(Math.max(s.length, 30));
    }
  });
});
