import { test, expect } from '@playwright/test';
import { mockSituationsScan } from './helpers/api';
import { FILLER_SITUATION } from './fixtures/situations/filler';
import { ACCELERATION_SITUATION } from './fixtures/situations/acceleration';

/**
 * DeepFocusView's Action Center panel used to be a hardcoded w-[450px] with
 * no responsive variant at all -- on any viewport under ~500px it either
 * forced the whole 3-column layout into horizontal overflow or left the
 * main analysis pane a sliver. Found in the 2026-08-29 audit (item #2).
 *
 * Fixed to a full-screen overlay below the `lg` breakpoint (the mobile
 * "detail panel takes over the screen" pattern) while staying an inline
 * 450px sidebar at `lg`+ -- same content, same close control, only the
 * position/inset strategy changes per viewport.
 */
async function openDeepFocus(page: any) {
  await mockSituationsScan(page, 'test_dfv_001', [FILLER_SITUATION, ACCELERATION_SITUATION]);
  await page.goto('/login?mode=demo');
  await page.waitForSelector('text=Rachel Kim', { timeout: 15_000 });
  await page.locator('text=Rachel Kim').click();
  await page.locator('[data-testid="demo-enter-btn"]').click();
  await page.waitForURL('**/dashboard', { timeout: 5_000 });
  await page.waitForSelector('[data-testid="situation-grid"]', { timeout: 20_000 });
  await page.locator('[data-testid="situation-card-sit_test_accel_001"]').click();
  await page.getByRole('button', { name: 'Open Action Center' }).waitFor({ timeout: 10_000 });
}

test('full-screen overlay on mobile, no horizontal overflow', async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await openDeepFocus(page);
  await page.getByRole('button', { name: 'Open Action Center' }).click();
  await page.getByRole('button', { name: 'Collapse Action Center' }).waitFor({ timeout: 5_000 });

  // No horizontal scroll anywhere on the page at this width -- the original defect.
  const hasHorizontalOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth
  );
  expect(hasHorizontalOverflow, 'page has horizontal overflow at 375px').toBe(false);

  // Panel actually covers the full viewport width (the overlay behavior).
  const panelBox = await page.getByTestId('action-center-panel').boundingBox();
  expect(panelBox?.width).toBeGreaterThan(360);

  // Close button meets the 44px-adjacent touch-target bump (was p-1.5/28px).
  const closeBox = await page.getByRole('button', { name: 'Collapse Action Center' }).boundingBox();
  expect(closeBox?.width).toBeGreaterThanOrEqual(36);
  expect(closeBox?.height).toBeGreaterThanOrEqual(36);

  // Close it and confirm we're back to the rail.
  await page.getByRole('button', { name: 'Collapse Action Center' }).click();
  await page.getByRole('button', { name: 'Open Action Center' }).waitFor({ timeout: 5_000 });
});

test('still a fixed 450px sidebar on desktop, unchanged', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await openDeepFocus(page);
  await page.getByRole('button', { name: 'Open Action Center' }).click();
  await page.getByRole('button', { name: 'Collapse Action Center' }).waitFor({ timeout: 5_000 });

  const panelBox = await page.getByTestId('action-center-panel').boundingBox();
  // Roughly 450px, not full-width -- desktop behavior must stay unchanged.
  expect(panelBox?.width).toBeGreaterThan(400);
  expect(panelBox?.width).toBeLessThan(500);
});
