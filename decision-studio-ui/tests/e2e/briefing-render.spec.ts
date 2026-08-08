import { test, expect } from '@playwright/test';
import { loginAsDemo } from './helpers/api';
import { MODERATOR_BRIEFING } from './fixtures/moderator-briefing';

/**
 * Executive Briefing rendering — mocked, no LLM cost, runs in seconds.
 *
 * WHY THIS EXISTS
 * ---------------
 * The Stage H "Moderator Verdicts" section was written, shipped, and never
 * executed once. Every test stopped at the debate page, so nothing on the
 * briefing — the most customer-facing surface in the product — was covered at
 * all. A component that threw here would have reached a CFO before it reached
 * a test.
 *
 * The live harness now visits this page too, but that costs a full pipeline run
 * (~$0.50, ~9 min) and only exercises whatever that one run happened to
 * produce. These tests seed localStorage directly from a REAL captured payload
 * and assert the render, so regressions surface immediately and for free.
 *
 * The briefing reads `briefing_{situationId}` from localStorage
 * (ExecutiveBriefing.tsx), which is what makes this seedable without a backend.
 */

const SITUATION_ID = 'sit_briefing_render_001';

async function openBriefing(page: any, briefing: unknown) {
  // addInitScript runs before app JS on every navigation, so the value is in
  // place before ExecutiveBriefing's effect reads it — seeding after goto()
  // would race the component.
  await page.addInitScript(
    ([id, payload]: [string, string]) => window.localStorage.setItem(`briefing_${id}`, payload),
    [SITUATION_ID, JSON.stringify(briefing)]
  );
  await loginAsDemo(page);
  await page.goto(`/briefing/${SITUATION_ID}`);
}

test.describe('Executive Briefing — moderator arm', () => {
  test('renders the page without a React failure', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', e => errors.push(String(e)));
    await openBriefing(page, MODERATOR_BRIEFING);

    // Visible content, not just "something matched" — the live harness's first
    // attempt at this assertion latched onto a hidden print-only element and
    // waited 60s for it to become visible, which it never does.
    await expect(page.getByRole('button', { name: /strategic options/i })).toBeVisible({ timeout: 15_000 });
    expect(errors, `uncaught page errors: ${errors.join(' | ')}`).toHaveLength(0);
  });

  test('renders Moderator Verdicts with per-option grades', async ({ page }) => {
    await openBriefing(page, MODERATOR_BRIEFING);

    const section = page.getByRole('button', { name: /moderator verdicts/i });
    await expect(section).toBeVisible({ timeout: 15_000 });
    await section.click();  // accordion starts collapsed

    // Grades are keyed by option id and every option must be graded.
    for (const optId of Object.keys(MODERATOR_BRIEFING.moderator_grades)) {
      await expect(page.getByText(optId, { exact: false }).first()).toBeVisible();
    }
    await expect(page.getByText(/constraints:/i).first()).toBeVisible();
    await expect(page.getByText(/arithmetic:/i).first()).toBeVisible();
  });

  test('states that insufficient data is not a pass', async ({ page }) => {
    // PM-1: a thin theory register must never read as endorsement. The wording
    // is load-bearing, so it is asserted rather than left to drift.
    await openBriefing(page, MODERATOR_BRIEFING);
    const section = page.getByRole('button', { name: /moderator verdicts/i });
    await section.click();
    await expect(page.getByText(/insufficient data.*not that the option passed/i)).toBeVisible();
  });

  test('impact scope qualifier reaches the options table', async ({ page }) => {
    // Segment-sized ranges under the enterprise KPI's name is the defect scope
    // elicitation exists to prevent; the qualifier is only useful if rendered.
    await openBriefing(page, MODERATOR_BRIEFING);
    await expect(page.getByText(/National Auto Parts Chain A only/i).first()).toBeVisible({ timeout: 15_000 });
  });

  test('baseline arm still renders when grades are absent', async ({ page }) => {
    // The moderator arm is behind a flag; a payload from the other arm (or an
    // older briefing replayed from localStorage) carries cross_review and no
    // grades. Neither shape may crash the page.
    const legacy = {
      ...MODERATOR_BRIEFING,
      moderator_grades: null,
      cross_review: { mckinsey: { critiques: [{ target: 'opt_2', concern: 'Execution risk' }], endorsements: [] } },
    };
    const errors: string[] = [];
    page.on('pageerror', e => errors.push(String(e)));
    await openBriefing(page, legacy);

    await expect(page.getByRole('button', { name: /strategic options/i })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByRole('button', { name: /moderator verdicts/i })).toHaveCount(0);
    expect(errors, `uncaught page errors: ${errors.join(' | ')}`).toHaveLength(0);
  });

  test('survives a briefing with neither adjudication artifact', async ({ page }) => {
    const bare = { ...MODERATOR_BRIEFING, moderator_grades: null, cross_review: null };
    const errors: string[] = [];
    page.on('pageerror', e => errors.push(String(e)));
    await openBriefing(page, bare);

    await expect(page.getByRole('button', { name: /strategic options/i })).toBeVisible({ timeout: 15_000 });
    expect(errors, `uncaught page errors: ${errors.join(' | ')}`).toHaveLength(0);
  });
});
