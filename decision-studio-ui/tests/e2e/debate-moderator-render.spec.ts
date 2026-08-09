import { test, expect } from '@playwright/test';
import { loginAsDemo } from './helpers/api';
import { MODERATOR_BRIEFING } from './fixtures/moderator-briefing';

/**
 * Council Debate page — moderator verdicts render. Mocked, no LLM cost.
 *
 * WHY THIS EXISTS
 * ---------------
 * The Moderator Verdicts panel on this page was written, shipped, and never
 * executed by any test. Exactly the gap that let the Executive Briefing's
 * equivalent panel ship untested a few days earlier — a component that threw
 * here would reach a user before it reached a test.
 *
 * The page normally runs a live debate on mount. But when navigated to
 * DIRECTLY (no router state), it treats that as a page refresh and restores
 * `solutions_{situationId}` from localStorage, setting phase 4 — which also
 * suppresses `runDebate()`, since that only fires at phase 0. So the whole
 * completed-debate view is reachable with no backend and no LLM spend.
 */

const SITUATION_ID = 'sit_debate_render_001';

// Shaped like a real SF response: ranked order is NOT opt_1/2/3 order, because
// the winner is frequently opt_2 — the reason verdicts must resolve titles by
// ID rather than by position.
const SOLUTIONS = {
  options_ranked: [
    { id: 'opt_2', title: 'Trigger-Based Base Oil Indexation Clause', description: 'd',
      expected_impact: 0.72, cost: 0.25, risk: 0.3 },
    { id: 'opt_1', title: 'Synthetic Blend Pricing Corridor Reset', description: 'd',
      expected_impact: 0.6, cost: 0.4, risk: 0.35 },
    { id: 'opt_3', title: 'Volume-for-Margin Portfolio Reset', description: 'd',
      expected_impact: 0.45, cost: 0.7, risk: 0.6 },
  ],
  recommendation: { id: 'opt_2', title: 'Trigger-Based Base Oil Indexation Clause' },
  recommendation_rationale: 'Survives the mid-quarter price-lock by deferring to renewal.',
  stage_1_hypotheses: {
    mckinsey: { framework: 'MECE', hypothesis: 'Base oil pass-through', conviction: 'High' },
    bcg: { framework: 'Growth-Share', hypothesis: 'Channel economics', conviction: 'High' },
    bain: { framework: 'Full Potential', hypothesis: 'Account economics', conviction: 'High' },
  },
  cross_review: null,
  moderator_grades: MODERATOR_BRIEFING.moderator_grades,
};

const SITUATION = { situation_id: SITUATION_ID, kpi_name: 'Gross Margin %', severity: 'critical',
                    principal_id: 'cfo_001', description: 'Gross margin declined' };

async function openDebate(page: any, solutions: unknown) {
  await page.addInitScript(([id, sol, sit]: [string, string, string]) => {
    window.localStorage.setItem(`solutions_${id}`, sol);
    window.localStorage.setItem(`situation_${id}`, sit);
    window.localStorage.setItem(`debate_config_${id}`, JSON.stringify({
      selectedPersonas: ['mckinsey', 'bcg', 'bain'], selectedPreset: 'recommended',
    }));
  }, [SITUATION_ID, JSON.stringify(solutions), JSON.stringify(SITUATION)]);
  await loginAsDemo(page);
  // Direct navigation = no router state = restore-from-storage path, phase 4.
  await page.goto(`/debate/${SITUATION_ID}`);
}

test.describe('Council Debate — moderator verdicts', () => {
  test('renders the completed debate without a React failure', async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', e => errors.push(String(e)));
    await openDebate(page, SOLUTIONS);
    await expect(page.getByText(/trade-off analysis/i)).toBeVisible({ timeout: 20_000 });
    expect(errors, `uncaught page errors: ${errors.join(' | ')}`).toHaveLength(0);
  });

  test('shows Moderator Verdicts with a grade per option', async ({ page }) => {
    await openDebate(page, SOLUTIONS);
    const panel = page.getByRole('heading', { name: /moderator verdicts/i });
    await expect(panel).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/constraints:/i).first()).toBeVisible();
    await expect(page.getByText(/arithmetic:/i).first()).toBeVisible();
  });

  test('verdicts name the OPTION TITLE, resolved by id not position', async ({ page }) => {
    // Ranked order here is opt_2, opt_1, opt_3 on purpose. Mapping by position
    // would mislabel every verdict; the briefing shipped raw "opt_1" for this
    // reason before it was fixed.
    await openDebate(page, SOLUTIONS);
    await expect(page.getByRole('heading', { name: /moderator verdicts/i })).toBeVisible({ timeout: 20_000 });
    // Title, not the raw id — and NOT opt_1, which position-mapping would pick.
    await expect(page.getByText('Trigger-Based Base Oil Indexation Clause').first()).toBeVisible();
  });

  test('stage 2 panel does not claim peer review happened', async ({ page }) => {
    // Pre-fix this read "Peer review not captured for this run" on EVERY
    // moderator run, which looks like a failure when a better-grounded
    // adjudication actually took place.
    await openDebate(page, SOLUTIONS);
    await expect(page.getByText(/trade-off analysis/i)).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/peer review not captured/i)).toHaveCount(0);
    await expect(page.getByText(/evidence check/i).first()).toBeVisible();
  });

  test('stage bar shows two stages, not the retired cross-review step', async ({ page }) => {
    // The bar previously ticked "Stage 2 - Cross-Review" green on runs where no
    // cross-review happened or could happen.
    await openDebate(page, SOLUTIONS);
    await expect(page.getByText(/adjudication & synthesis/i)).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText(/cross-review/i)).toHaveCount(0);
  });

  test('baseline arm still renders peer review when present', async ({ page }) => {
    // The other arm must keep working: cross_review present, no grades.
    const legacy = {
      ...SOLUTIONS, moderator_grades: null,
      cross_review: {
        mckinsey: { critiques: [{ target: 'opt_1', concern: 'Execution risk is understated' }], endorsements: [] },
        bcg: { critiques: [], endorsements: [{ target: 'opt_2', reason: 'Targets the confirmed driver' }] },
      },
    };
    const errors: string[] = [];
    page.on('pageerror', e => errors.push(String(e)));
    await openDebate(page, legacy);
    await expect(page.getByText(/trade-off analysis/i)).toBeVisible({ timeout: 20_000 });
    await expect(page.getByRole('heading', { name: /moderator verdicts/i })).toHaveCount(0);
    expect(errors, `uncaught page errors: ${errors.join(' | ')}`).toHaveLength(0);
  });

  test('survives a payload with neither adjudication artifact', async ({ page }) => {
    const bare = { ...SOLUTIONS, moderator_grades: null, cross_review: null };
    const errors: string[] = [];
    page.on('pageerror', e => errors.push(String(e)));
    await openDebate(page, bare);
    await expect(page.getByText(/trade-off analysis/i)).toBeVisible({ timeout: 20_000 });
    expect(errors, `uncaught page errors: ${errors.join(' | ')}`).toHaveLength(0);
  });
});
