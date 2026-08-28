import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { loginAsDemo } from './helpers/api';
import { buildExecutiveBriefing } from '../../src/utils/briefingUtils';

/**
 * Executive Briefing rendered from a LIVE payload — no LLM cost.
 *
 * WHAT MAKES THIS DIFFERENT FROM briefing-render.spec.ts
 * ------------------------------------------------------
 * That file seeds an already-built briefing object, so it tests the component
 * only. This one starts from the raw inputs and runs `buildExecutiveBriefing`
 * itself, so the transform AND the render are both exercised — which is where
 * every number defect this week actually lived.
 *
 * The inputs are real, not invented:
 *   analysis  — a live Deep Analysis run against BigQuery (2026-08-09), carrying
 *               dimension_totals computed by the warehouse: -4.49pp, independently
 *               confirmed as YTD2026 29.94% vs YTD2025 34.43%.
 *   solutions — a captured Solution Finder payload chosen for having the widest
 *               cost/risk spread (cost 0.25/0.50/0.80, risk 0.50/0.55/0.70). Under
 *               the old three-band display those rendered as Low/Moderate/High
 *               Effort and Medium/Medium/High — collapsing a real spread.
 *
 * Regenerate with a fresh DA run + captured SF payload if the shapes change.
 */

const SITUATION_ID = 'sit_live_render_001';
// ES module scope — no __dirname.
const HERE = path.dirname(fileURLToPath(import.meta.url));
const FIXTURE = path.join(HERE, 'fixtures', 'live-briefing-payload.json');

const raw = JSON.parse(fs.readFileSync(FIXTURE, 'utf-8'));

// Several strings on this page (option titles, the print-only "Internal —
// Decision Sensitive" stamp) legitimately appear more than once — a
// `hidden print:block` copy for paper plus one or more on-screen copies
// (the fork's "Affects:" line, "Proceed with: ..." in Next Steps, the
// option's own CompactOptionRow heading). `.first()`/`.last()` on DOM order
// is fragile to which duplicate happens to sit where; this asserts at least
// one real match is actually rendered visible, regardless of position.
async function expectVisibleSomewhere(page: any, text: string | RegExp) {
  const matches = page.getByText(text, { exact: false });
  await expect.poll(async () => {
    const count = await matches.count();
    for (let i = 0; i < count; i++) {
      if (await matches.nth(i).isVisible()) return true;
    }
    return false;
  }, { timeout: 20_000 }).toBe(true);
}

async function openBuiltBriefing(page: any) {
  const built = buildExecutiveBriefing(raw.situation, raw.analysis, raw.solutions);
  await page.addInitScript(
    ([id, payload]: [string, string]) => window.localStorage.setItem(`briefing_${id}`, payload),
    [SITUATION_ID, JSON.stringify(built)]
  );
  await loginAsDemo(page);
  await page.goto(`/briefing/${SITUATION_ID}`);
  return built;
}

test.describe('Executive Briefing — live payload end to end', () => {
  test('builds and renders with no React failure', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', e => errors.push(String(e)));
    await openBuiltBriefing(page);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    expect(errors, `uncaught page errors: ${errors.join(' | ')}`).toHaveLength(0);
  });

  test('effort and risk keep the spread the model supplied', async ({ page }) => {
    // cost 0.25 / 0.50 / 0.80 and risk 0.50 / 0.55 / 0.70. The old three-band
    // display flattened runs like this to a single repeated label.
    const built = await openBuiltBriefing(page);
    const investments = built.options.map((o: any) => o.investment);
    const risks = built.options.map((o: any) => o.riskLevel);

    expect(new Set(investments).size, `investment collapsed: ${investments}`).toBeGreaterThan(1);
    expect(new Set(risks).size, `risk collapsed: ${risks}`).toBeGreaterThan(1);
    // 0.80 must not read the same as 0.25.
    expect(investments[0]).not.toBe(investments[2]);
  });

  test('two options sharing a band disclose their order within it', async ({ page }) => {
    // risk 0.50 and 0.55 are both "Medium"; hiding that one is lower than the
    // other is what made the column look uninformative.
    const built = await openBuiltBriefing(page);
    const risks: string[] = built.options.map((o: any) => o.riskLevel);
    const medium = risks.filter(r => r.startsWith('Medium'));
    if (medium.length >= 2) {
      expect(medium.some(r => /\((least|most)\)/.test(r)),
        `no within-band order disclosed: ${risks}`).toBe(true);
    }
  });

  test('reversibility is shown per option, not omitted', async ({ page }) => {
    // It varies (medium/medium/low) and was on the payload but absent from the
    // old comparison table, so the table omitted a criterion that separated
    // the options. 2026-08-28: the table is gone (CompactOptionRow replaced
    // it) and reversibility now renders as a self-describing chip
    // ("Easily reversed" / "Partly reversible" / "Hard to undo", matching the
    // reference mockup's own phrasing) rather than a bare "medium" with a
    // column-header label — so this checks for the descriptive text, not a
    // literal "Reversibility" cell.
    await openBuiltBriefing(page);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/easily reversed|partly reversible|hard to undo/i).first()).toBeVisible();
  });

  test('a fully discriminating payload shows NO markers', async ({ page }) => {
    // The refreshed fixture (post data-fix) separates on every criterion:
    // cost 0.3/0.55/0.8, risk 0.3/0.5/0.65, reversibility high/medium/low.
    // Markers must stay rare or readers learn to ignore them.
    await openBuiltBriefing(page);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/same for all/i)).toHaveCount(0);
  });

  test('identical values ARE called out, not left implying a choice', async ({ page }) => {
    // Constructed rather than relying on the fixture happening to contain ties.
    // The previous version of this test asserted a marker was present and broke
    // when the data was corrected — the same trap as pinning a test to one
    // dataset's narrative.
    const tied = {
      ...raw.solutions,
      options_ranked: (raw.solutions.options_ranked as any[]).slice(0, 3)
        .map(o => ({ ...o, cost: 0.5, risk: 0.5, reversibility: 'medium' })),
    };
    const built = buildExecutiveBriefing(raw.situation, raw.analysis, tied);
    await page.addInitScript(
      ([id, payload]: [string, string]) => window.localStorage.setItem(`briefing_${id}`, payload),
      [SITUATION_ID, JSON.stringify(built)]);
    await loginAsDemo(page);
    await page.goto(`/briefing/${SITUATION_ID}`);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/same for all/i).first()).toBeVisible();
  });

  test('percentage KPI never renders a currency symbol on its deltas', async ({ page }) => {
    // "-$7" for a -7.86 percentage-point move reached a live briefing.
    const built = await openBuiltBriefing(page);
    const impacts = (built.situation?.rootCauses ?? []).map((r: any) => String(r.impact));
    expect(impacts.length).toBeGreaterThan(0);
    for (const i of impacts) expect(i, `currency on a % KPI: ${i}`).not.toContain('$');
    expect(impacts.some((i: string) => i.includes('pp'))).toBe(true);
  });

  test('capture the rendered briefing for review', async ({ page }) => {
    await openBuiltBriefing(page);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    // Expand everything so the screenshot shows the sections under accordions.
    const expandAll = page.getByRole('button', { name: /expand all/i });
    if (await expandAll.count()) await expandAll.first().click();
    await page.waitForTimeout(600);
    await page.screenshot({ path: 'playwright-results/exec-briefing-live.png', fullPage: true });
    // 2026-08-28: the comparison <table> was deleted (replaced by
    // CompactOptionRow — see ExecutiveBriefing.tsx's "Strategic Options"
    // AccordionSection). `page.locator('table').first()` now matches an
    // unrelated, hidden table elsewhere on the page (Risk Analysis, inside a
    // collapsed accordion) and hangs on scrollIntoViewIfNeeded. Retarget to
    // the options section itself — that's what this review actually wants.
    const options = page.locator('#accordion-options');
    if (await options.count()) {
      await options.scrollIntoViewIfNeeded();
      await options.screenshot({ path: 'playwright-results/exec-briefing-tradeoff.png' });
    }
  });
});

/**
 * Degraded-analysis banner.
 *
 * On 2026-08-09 an exhausted API quota made every LLM call fail. The workflow
 * returned state=completed / error=None with two generic placeholder options
 * ("Tighten spend controls" / "Optimize pricing"), and nothing the reader could
 * see said the analysis had not run.
 */
test.describe('degraded analysis is visible to the reader', () => {
  async function openWith(page: any, extra: Record<string, unknown>) {
    const built: any = buildExecutiveBriefing(
      raw.situation, raw.analysis, { ...raw.solutions, ...extra });
    await page.addInitScript(
      ([id, payload]: [string, string]) => window.localStorage.setItem(`briefing_${id}`, payload),
      [SITUATION_ID, JSON.stringify(built)]);
    await loginAsDemo(page);
    await page.goto(`/briefing/${SITUATION_ID}`);
    return built;
  }

  test('a healthy payload shows no warning at all', async ({ page }) => {
    // The banner must stay rare, or readers learn to scroll past it.
    const built = await openWith(page, {});
    expect(built.analysis_degraded).toBe(false);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/were not produced by the analysis/i)).toHaveCount(0);
  });

  test('an LLM outage is stated plainly, not softened', async ({ page }) => {
    await openWith(page, { analysis_degraded: true, degraded_reason: 'llm_unavailable' });
    await expect(page.getByText(/were not produced by the analysis/i)).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/language model was unavailable/i)).toBeVisible();
    await expect(page.getByText(/do not act on them/i)).toBeVisible();
  });

  test('truncation gets its own wording, not the outage wording', async ({ page }) => {
    // Different cause, different remedy. Telling a user the model was down when
    // it answered but overran would send them to fix the wrong thing.
    await openWith(page, { analysis_degraded: true, degraded_reason: 'llm_yielded_no_options' });
    await expect(page.getByText(/were not produced by the analysis/i)).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/could not be read as a set of options/i)).toBeVisible();
    await expect(page.getByText(/language model was unavailable/i)).toHaveCount(0);
  });

  test('the flag is read straight through, never inferred', async ({ page }) => {
    // Deriving it (e.g. from stub-looking titles) would recreate the guesswork
    // this replaced. Absent means healthy.
    const built: any = buildExecutiveBriefing(raw.situation, raw.analysis,
      { ...raw.solutions, analysis_degraded: undefined, degraded_reason: undefined });
    expect(built.analysis_degraded).toBe(false);
    expect(built.degraded_reason).toBeNull();
  });
});

/**
 * Largest Variance Contributors — mixed dimensions.
 *
 * A live briefing ranked four profit centres and one CUSTOMER in a single list
 * with no dimension shown:
 *
 *   1. International Division          Impact: -4.98pp
 *   ...
 *   5. National Auto Parts Chain A     Impact: -5.24pp
 *
 * Two problems. "National Auto Parts Chain A" reads as a sixth division. And the
 * entries are not disjoint — that customer's revenue sits inside one of those
 * divisions, so the same margin loss is counted twice and the list cannot be read
 * as a ranking.
 */
test.describe('variance contributors disclose their dimension', () => {
  async function openWith(page: any, rootCauses: any[]) {
    const built: any = buildExecutiveBriefing(raw.situation, raw.analysis, raw.solutions);
    built.situation = { ...built.situation, rootCauses };
    await page.addInitScript(
      ([id, payload]: [string, string]) => window.localStorage.setItem(`briefing_${id}`, payload),
      [SITUATION_ID, JSON.stringify(built)]);
    await loginAsDemo(page);
    await page.goto(`/briefing/${SITUATION_ID}`);
    // This section lives inside a collapsed accordion; without expanding, the
    // assertions would pass or fail on visibility rather than on content.
    const expandAll = page.getByRole('button', { name: /expand all/i });
    await expandAll.first().waitFor({ timeout: 20_000 });
    await expandAll.first().click();
  }

  const MIXED = [
    { driver: 'International Division', dimension: 'Profit Center Name', evidence: 'e', impact: 'Δ -4.98pp' },
    { driver: 'National Auto Parts Chain A', dimension: 'Customer Name', evidence: 'e', impact: 'Δ -5.24pp' },
  ];
  const SINGLE = [
    { driver: 'International Division', dimension: 'Profit Center Name', evidence: 'e', impact: 'Δ -4.98pp' },
    { driver: 'Retail Products Division', dimension: 'Profit Center Name', evidence: 'e', impact: 'Δ -4.26pp' },
  ];

  test('each contributor names the dimension it belongs to', async ({ page }) => {
    await openWith(page, MIXED);
    await expect(page.getByRole('heading', { name: /largest variance contributors/i })).toBeVisible({ timeout: 20_000 });
    // The briefing renders this list TWICE — a `hidden print:block` version and
    // the on-screen one, which comes later in the DOM. `.first()` resolves to the
    // print copy and is always hidden.
    await expect(page.getByText('Customer Name').last()).toBeVisible();
    await expect(page.getByText('Profit Center Name').last()).toBeVisible();
  });

  test('a mixed list warns that the entries overlap', async ({ page }) => {
    await openWith(page, MIXED);
    await expect(page.getByText(/already counted inside its division/i)).toBeVisible({ timeout: 20_000 });
  });

  test('a single-dimension list carries NO caveat', async ({ page }) => {
    // A warning that always appears is a warning nobody reads.
    await openWith(page, SINGLE);
    await expect(page.getByRole('heading', { name: /largest variance contributors/i })).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/already counted inside its division/i)).toHaveCount(0);
  });
});

/**
 * Compact decision-brief restructure (2026-08-28).
 *
 * The comparison <table> and the two-cards-plus-full-option-card layout were
 * replaced with DecisionMasthead / RelatedOptionsFork / WhyNowBand /
 * CompactOptionRow / VerificationLedger — see the plan note in
 * ExecutiveBriefing.tsx and the component docstrings themselves. These tests
 * cover the new structure against the SAME real fixture used above, not a
 * synthetic payload, except where a specific shape (a dominated option) does
 * not occur in the fixture and is constructed the same way the "identical
 * values" test above already does.
 */
test.describe('compact decision-brief restructure', () => {
  test('masthead renders exactly one h1, with eyebrow, stamp, and a subtitle naming the KPI', async ({ page }) => {
    const built = await openBuiltBriefing(page);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.locator('h1')).toHaveCount(1);
    await expect(page.getByText(/^decision brief$/i)).toBeVisible();
    await expectVisibleSomewhere(page, /internal.*decision sensitive/i);
    const kpiName = built.kpiData?.kpi_name;
    expect(kpiName, 'fixture must carry a kpi_name for this assertion to mean anything').toBeTruthy();
    await expect(page.getByText(kpiName, { exact: false }).first()).toBeVisible();
  });

  test('why-now band holds "why now" and "cost of waiting" in one shared container', async ({ page }) => {
    await openBuiltBriefing(page);
    const band = page.getByTestId('why-now-band');
    await expect(band).toBeVisible({ timeout: 20_000 });
    await expect(band.getByText(/why now/i)).toBeVisible();
    await expect(band.getByText(/cost of (waiting|inaction)/i)).toBeVisible();
  });

  test('the fork resolves the headline tension to its real, single affected option', async ({ page }) => {
    // Fixture's tensions[0].options_affected === ['opt_1'] — exactly one, the
    // degrade path with no divider/either-or framing. A test asserting the
    // 2+ card layout would need a payload this fixture doesn't have.
    const built = await openBuiltBriefing(page);
    const firstOption = built.options?.[0];
    expect(firstOption?.title).toBeTruthy();
    await expect(page.getByText('Affects:')).toBeVisible({ timeout: 20_000 });
    await expectVisibleSomewhere(page, firstOption.title);
    await expect(page.getByTestId('related-options-fork')).toHaveCount(0);
  });

  test('no comparison table survives in the options section, at any breakpoint', async ({ page }) => {
    await openBuiltBriefing(page);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    for (const viewport of [{ width: 390, height: 844 }, { width: 1440, height: 900 }]) {
      await page.setViewportSize(viewport);
      await expect(page.locator('#accordion-options table')).toHaveCount(0);
    }
  });

  test('range bars carry the fixture\'s real recovery_range as data attributes', async ({ page }) => {
    const built = await openBuiltBriefing(page);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    const bars = page.getByTestId('range-bar');
    const count = await bars.count();
    const withRange = (built.options ?? []).filter((o: any) => o.impactRangeNumeric);
    expect(count).toBe(withRange.length);
    for (let i = 0; i < count; i++) {
      const bar = bars.nth(i);
      const low = await bar.getAttribute('data-low');
      const high = await bar.getAttribute('data-high');
      const match = withRange.find((o: any) =>
        String(o.impactRangeNumeric.low) === low && String(o.impactRangeNumeric.high) === high);
      expect(match, `no fixture option matches range-bar low=${low} high=${high}`).toBeTruthy();
    }
  });

  test('a dominated option renders faint and named, not silently dropped', async ({ page }) => {
    // Constructed, same pattern as "identical values ARE called out" above —
    // no option in the fixture is actually dominated.
    const dominated: any = {
      ...raw.solutions,
      options_ranked: (raw.solutions.options_ranked as any[]).slice(0, 3)
        .map((o, i) => i === 1 ? { ...o, dominated_by: (raw.solutions.options_ranked as any[])[0].id } : o),
    };
    const built = buildExecutiveBriefing(raw.situation, raw.analysis, dominated);
    await page.addInitScript(
      ([id, payload]: [string, string]) => window.localStorage.setItem(`briefing_${id}`, payload),
      [SITUATION_ID, JSON.stringify(built)]);
    await loginAsDemo(page);
    await page.goto(`/briefing/${SITUATION_ID}`);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/dominated by option a/i)).toBeVisible();
  });

  test('verification ledger stays hidden until "Show the analysis", then reads the real grade', async ({ page }) => {
    const built = await openBuiltBriefing(page);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    const ledgerHeading = page.getByText(/verification ledger/i);
    await expect(ledgerHeading).toBeVisible(); // accordion header itself always renders
    await expect(page.getByText(/constraint survival/i)).toBeHidden();

    await page.getByRole('button', { name: /show the analysis/i }).click();
    await expect(page.getByText(/constraint survival/i)).toBeVisible();
    await expect(page.getByText(/causal grounding/i)).toBeVisible();
    await expect(page.getByText(/arithmetic consistency/i)).toBeVisible();

    const rationale = built.moderator_grades?.opt_1?.grade_rationale;
    expect(rationale, 'fixture must carry a grade_rationale for this assertion to mean anything').toBeTruthy();
    await expect(page.getByText(rationale.slice(0, 40), { exact: false })).toBeVisible();
  });

  test('option titles reach the page unedited, with no "generated as" restatement', async ({ page }) => {
    const built = await openBuiltBriefing(page);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    for (const option of built.options ?? []) {
      await expectVisibleSomewhere(page, option.title);
    }
    await expect(page.getByText(/generated as/i)).toHaveCount(0);
  });

  test('print media keeps the comparative substance readable — no table to fall back on', async ({ page }) => {
    const built = await openBuiltBriefing(page);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    await page.emulateMedia({ media: 'print' });
    for (const option of built.options ?? []) {
      await expectVisibleSomewhere(page, option.title);
      if (option.roi) await expectVisibleSomewhere(page, option.roi);
    }
    await expect(page.locator('h1')).toHaveCount(1);
    await expect(page.getByTestId('why-now-band').getByText(/why now/i)).toBeVisible();
  });
});
