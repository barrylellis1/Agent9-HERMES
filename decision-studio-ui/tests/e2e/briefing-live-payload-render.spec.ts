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

  test('a criterion every option shares is called out, not left implying a choice', async ({ page }) => {
    await openBuiltBriefing(page);
    await expect(page.getByText(/strategic options/i).first()).toBeVisible({ timeout: 20_000 });
    // Either marker is acceptable — which appears depends on the payload. What
    // must NOT happen is identical values presented as a silent comparison.
    const markers = page.getByText(/same for all|of \d+ distinct/i);
    expect(await markers.count()).toBeGreaterThan(0);
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
