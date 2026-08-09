import { test, expect } from '@playwright/test';
import { truncateProse, endsSentence } from '../../src/utils/briefingUtils';

/**
 * Flash Briefing prose truncation — pure functions, no browser, no LLM.
 *
 * THE DEFECT
 * ----------
 * The Flash Briefing is the first paragraph an executive reads. It used raw
 * character slicing — `scqa.slice(0, 200)` and `rationale.slice(0, 120)` — and a
 * live 12-page briefing went out reading:
 *
 *   "...with the business overall also underperform…"
 *   "...Option 1 is the right first move because it…."
 *
 * Two separate faults: the cut landed mid-word, and the caller appended its own
 * period after the ellipsis, producing four dots. Neither changes a number, but
 * the hero summary reading like unfinished work costs more credibility than the
 * omitted words were worth.
 */
test.describe('truncateProse', () => {
  test('leaves text under the limit completely untouched', () => {
    const s = 'Gross margin fell 7.14 points in Synthetic Blend Engine Oil.';
    expect(truncateProse(s, 200)).toBe(s);
  });

  test('never cuts mid-word — the exact production failure', () => {
    const s = 'Year-to-date Gross Margin % has fallen 7.14 percentage points to a current level '
            + 'of 20.64% at its most severely impacted point (Synthetic Blend Engine Oil), with '
            + 'the business overall also underperforming against plan across every division.';
    const out = truncateProse(s, 200);
    expect(out.length).toBeLessThanOrEqual(201);   // +1 for the ellipsis
    expect(out).not.toContain('underperform…');
    // Whatever was kept must be a clean prefix of the original.
    const kept = out.replace(/…$/, '');
    expect(s.startsWith(kept)).toBe(true);
  });

  test('prefers a complete sentence and then needs no ellipsis at all', () => {
    const s = 'Margin fell sharply in Engine Oils. A base-oil cost spike is the confirmed driver '
            + 'and contractual price locks prevent recovery until renewal.';
    const out = truncateProse(s, 60);
    expect(out).toBe('Margin fell sharply in Engine Oils.');
    expect(out).not.toContain('…');
  });

  test('never produces a dangling separator before the ellipsis', () => {
    const s = 'Option 1 is the right first move because it, uniquely among the three, confines '
            + 'pricing action to non-locked channels and therefore cannot breach the clause.';
    const out = truncateProse(s, 40);
    expect(out).not.toMatch(/[,;:—-]…$/);
    expect(out.endsWith('…')).toBe(true);
  });

  test('empty and null return empty rather than an orphan ellipsis', () => {
    expect(truncateProse('', 100)).toBe('');
    expect(truncateProse(null, 100)).toBe('');
    expect(truncateProse(undefined, 100)).toBe('');
  });
});

test.describe('endsSentence — prevents the four-dot artefact', () => {
  test('recognises an ellipsis as already terminal', () => {
    // This is the specific guard: the caller must not append '.' after '…'.
    expect(endsSentence('because it…')).toBe(true);
  });

  test('recognises normal terminators', () => {
    expect(endsSentence('a full sentence.')).toBe(true);
    expect(endsSentence('really?')).toBe(true);
    expect(endsSentence('stop!')).toBe(true);
  });

  test('an unterminated clause still needs a period', () => {
    expect(endsSentence('The council recommends Dual-Track Pricing Recovery')).toBe(false);
  });

  test('tolerates trailing whitespace', () => {
    expect(endsSentence('done.   ')).toBe(true);
  });

  test('composed guard never yields ".." or "…."', () => {
    const cases = [
      'The council recommends X: because it…',
      'The council recommends X: a short reason.',
      'The council recommends X',
    ];
    for (const line of cases) {
      const out = endsSentence(line) ? line : `${line}.`;
      expect(out).not.toContain('..');
      expect(out).not.toContain('….');
    }
  });
});
