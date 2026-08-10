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

/**
 * Abbreviation handling.
 *
 * `lastIndexOf('. ')` treats an abbreviation as a sentence end. Real prose from
 * this pipeline reads "29.94% vs. 34.43% prior YTD", where the first ". " sits
 * at position 76 — inside "vs.". Cutting there ends the summary mid-comparison,
 * on the very number it exists to state.
 */
test.describe('truncateProse — abbreviations and clauses', () => {
  test('does not treat "vs." as a sentence end', () => {
    const s = 'Gross margin declined 4.49 points year-to-date (29.94% vs. 34.43% prior YTD) '
            + 'across the portfolio, with no offsetting segment anywhere in the book.';
    const out = truncateProse(s, 90);
    expect(out).not.toBe('Gross margin declined 4.49 points year-to-date (29.94% vs.');
    expect(out).not.toMatch(/vs\.$/);
  });

  test('does not treat a decimal point as a sentence end', () => {
    const s = 'Margin fell to 29.94 percent this period and the decline was concentrated '
            + 'in a small number of product lines rather than spread evenly.';
    const out = truncateProse(s, 60);
    expect(out).not.toMatch(/\d\.$/);
  });

  test('falls back to a clause boundary when there is no sentence end', () => {
    // This pipeline writes long em-dash-joined sentences; a clause boundary ends
    // a thought instead of interrupting one.
    const s = 'Gross Margin % has contracted 4.49 points year-to-date, from 34.43% to 29.94% '
            + '— an enterprise-wide erosion with no fully offsetting segment — and the decline '
            + 'is concentrated in Engine Oils.';
    const out = truncateProse(s, 130);
    expect(out.endsWith('…')).toBe(true);
    expect(out).not.toMatch(/[—-]…$/);
    expect(out.length).toBeLessThanOrEqual(131);
  });

  test('a sentence end past the floor is preferred, and needs no ellipsis', () => {
    const s = 'A base-oil cost spike is the confirmed driver of the decline. Contractual '
            + 'locks — anchor accounts — prevent recovery until renewal.';
    const out = truncateProse(s, 90);
    expect(out).toBe('A base-oil cost spike is the confirmed driver of the decline.');
    expect(out).not.toContain('…');
  });

  test('a very early sentence end does not waste the budget', () => {
    // "Margin fell sharply." ends at char 19 of a 60-char budget. Cutting there
    // would throw away two-thirds of the space available; the clause cut carries
    // more and still ends a thought rather than interrupting one.
    const s = 'Margin fell sharply. A base-oil cost spike — confirmed — is the driver and '
            + 'contractual locks prevent recovery until renewal.';
    const out = truncateProse(s, 60);
    expect(out.length).toBeGreaterThan('Margin fell sharply.'.length);
    expect(out.endsWith('…')).toBe(true);
    expect(out).not.toMatch(/[—-]…$/);
  });

  test('abbreviations mid-text never produce a bare fragment', () => {
    for (const abbr of ['vs.', 'approx.', 'e.g.', 'etc.', 'Q3.']) {
      const s = `The comparison uses ${abbr} the prior period and shows a material decline `
              + 'across every division measured in the current window.';
      const out = truncateProse(s, 70);
      expect(out.trim().length, `empty for ${abbr}`).toBeGreaterThan(10);
    }
  });
});
