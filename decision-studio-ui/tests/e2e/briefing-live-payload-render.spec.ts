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

  test('the trade-off table shows Reversibility', async ({ page }) => {
    // It varies (medium/medium/low) and was on the payload but absent from the
    // comparison, so the table omitted a criterion that separated the options.
    await openBuiltBriefing(page);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    await expect(page.getByRole('cell', { name: /^Reversibility/i })).toBeVisible();
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
    // The comparison table is the point of this review — capture it on its own so
    // the discrimination markers are legible without scrolling a full-page shot.
    const table = page.locator('table').first();
    if (await table.count()) {
      await table.scrollIntoViewIfNeeded();
      await table.screenshot({ path: 'playwright-results/exec-briefing-tradeoff.png' });
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
