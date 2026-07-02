import { test, expect } from '@playwright/test';
import { loginAsDemo, mockSituationsScan } from './helpers/api';
import { PLAN_VARIANCE_SITUATION } from './fixtures/situations/plan-variance';
import { PROJECTED_BREACH_SITUATION } from './fixtures/situations/projected-breach';
import { COMPOUND_SITUATION_REVENUE, COMPOUND_SITUATION_MARGIN } from './fixtures/situations/compound-alert';
import { ACCELERATION_SITUATION } from './fixtures/situations/acceleration';
import { FILLER_SITUATION } from './fixtures/situations/filler';

// The dashboard promotes situations[0] to a hero briefing; situations[1+] land in
// the KPITile grid. Tests that assert on KPITile badges must place FILLER_SITUATION
// first so the real subject is in the grid, not consumed by the hero slot.
async function waitForSituationGrid(page: any, timeout = 20_000) {
  await page.waitForSelector('[data-testid="situation-grid"]', { timeout });
}

// ── Plan Variance ───────────────────────────────────────────────────────────

test.describe('Phase 11I — Plan Variance Alert', () => {
  test('renders "Plan Variance" badge on KPI tile', async ({ page }) => {
    await mockSituationsScan(page, 'test_pv_001', [FILLER_SITUATION, PLAN_VARIANCE_SITUATION]);
    await loginAsDemo(page);
    await waitForSituationGrid(page);

    const badge = page.locator('[data-testid="alert-type-badge"]').first();
    await expect(badge).toBeVisible();
    await expect(badge).toContainText('Plan Variance');
  });

  test('plan_variance situation card is present in grid', async ({ page }) => {
    await mockSituationsScan(page, 'test_pv_002', [FILLER_SITUATION, PLAN_VARIANCE_SITUATION]);
    await loginAsDemo(page);
    await waitForSituationGrid(page);

    const card = page.locator('[data-testid="situation-card-sit_test_pv_001"]');
    await expect(card).toBeVisible();
  });

  test('deviation percentage renders correctly for plan_variance', async ({ page }) => {
    await mockSituationsScan(page, 'test_pv_003', [FILLER_SITUATION, PLAN_VARIANCE_SITUATION]);
    await loginAsDemo(page);
    await waitForSituationGrid(page);

    const deviation = page.locator('[data-testid="kpi-deviation"]').first();
    await expect(deviation).toContainText('-8.5%');
  });
});

// ── Projected Breach ────────────────────────────────────────────────────────

test.describe('Phase 11I — Projected Breach Alert', () => {
  test('renders "Projected Breach" badge on KPI tile', async ({ page }) => {
    await mockSituationsScan(page, 'test_pb_001', [FILLER_SITUATION, PROJECTED_BREACH_SITUATION]);
    await loginAsDemo(page);
    await waitForSituationGrid(page);

    const badge = page.locator('[data-testid="alert-type-badge"]').first();
    await expect(badge).toBeVisible();
    await expect(badge).toContainText('Projected Breach');
  });
});

// ── Acceleration ────────────────────────────────────────────────────────────

test.describe('Phase 11I — Acceleration Alert', () => {
  test('renders "Accelerating" badge on KPI tile', async ({ page }) => {
    await mockSituationsScan(page, 'test_accel_001', [FILLER_SITUATION, ACCELERATION_SITUATION]);
    await loginAsDemo(page);
    await waitForSituationGrid(page);

    const badge = page.locator('[data-testid="alert-type-badge"]').first();
    await expect(badge).toBeVisible();
    await expect(badge).toContainText('Accelerating');
  });
});

// ── Compound Alert ──────────────────────────────────────────────────────────

test.describe('Phase 11I-B — Compound Cross-KPI Alert', () => {
  test('renders "Compound" badge on both linked KPI tiles', async ({ page }) => {
    await mockSituationsScan(page, 'test_comp_001', [
      FILLER_SITUATION,
      COMPOUND_SITUATION_REVENUE,
      COMPOUND_SITUATION_MARGIN,
    ]);
    await loginAsDemo(page);
    await waitForSituationGrid(page);

    const compoundBadges = page.locator('[data-testid="compound-alert-badge"]');
    await expect(compoundBadges).toHaveCount(2);
  });

  test('compound pattern text is accessible in both compound situation cards', async ({ page }) => {
    await mockSituationsScan(page, 'test_comp_002', [
      FILLER_SITUATION,
      COMPOUND_SITUATION_REVENUE,
      COMPOUND_SITUATION_MARGIN,
    ]);
    await loginAsDemo(page);
    await waitForSituationGrid(page);

    await expect(page.locator('[data-testid="situation-card-sit_test_comp_rev_001"]')).toBeVisible();
    await expect(page.locator('[data-testid="situation-card-sit_test_comp_mgn_001"]')).toBeVisible();
  });
});

// ── Mixed scan: all 4 alert types in one scan ───────────────────────────────

test.describe('Phase 11I — Mixed alert types in single scan', () => {
  test('all four alert-type badges render in a mixed scan', async ({ page }) => {
    // FILLER occupies the hero slot; all four labelled situations land in the grid
    await mockSituationsScan(page, 'test_mixed_001', [
      FILLER_SITUATION,
      PLAN_VARIANCE_SITUATION,
      PROJECTED_BREACH_SITUATION,
      ACCELERATION_SITUATION,
      COMPOUND_SITUATION_REVENUE,
      COMPOUND_SITUATION_MARGIN,
    ]);
    await loginAsDemo(page);
    await waitForSituationGrid(page);

    const alertBadges = page.locator('[data-testid="alert-type-badge"]');
    const compoundBadges = page.locator('[data-testid="compound-alert-badge"]');
    await expect(alertBadges.first()).toBeVisible();
    await expect(compoundBadges.first()).toBeVisible();

    await expect(alertBadges.filter({ hasText: 'Plan Variance' })).toHaveCount(1);
    await expect(alertBadges.filter({ hasText: 'Projected Breach' })).toHaveCount(1);
    await expect(alertBadges.filter({ hasText: 'Accelerating' })).toHaveCount(1);
  });

  test('threshold_breach alert does NOT show an alert-type badge', async ({ page }) => {
    const thresholdSituation = {
      ...PLAN_VARIANCE_SITUATION,
      situation_id: 'sit_test_tb_001',
      alert_type: 'threshold_breach',
    };
    // FILLER is hero; threshold situation is in the grid
    await mockSituationsScan(page, 'test_tb_001', [FILLER_SITUATION, thresholdSituation]);
    await loginAsDemo(page);
    await waitForSituationGrid(page);

    const badges = page.locator('[data-testid="alert-type-badge"]');
    await expect(badges).toHaveCount(0);
  });
});

// ── Scan with no situations ─────────────────────────────────────────────────

test.describe('Empty scan state', () => {
  test('shows "All KPIs within normal range" when no situations returned', async ({ page }) => {
    await mockSituationsScan(page, 'test_empty_001', []);
    await loginAsDemo(page);
    await page.waitForSelector('text=All KPIs within normal range', { timeout: 15_000 });
    await expect(page.locator('text=All KPIs within normal range')).toBeVisible();
  });
});
