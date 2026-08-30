import { test, expect } from '@playwright/test';

/**
 * LIVE, one-off test — drives the REAL Admin Console onboarding wizard
 * (DataProductOnboardingNew.tsx) against hess's real SQL Server database,
 * registering a NEW data product under a throwaway test id
 * (dp_hess_financials_test) rather than touching the real dp_hess_financials
 * record. Purpose: answer "does the wizard populate the registry as
 * completely as the manual seed script does?" empirically, not just by
 * reading code — this is Phase 16's own O6 acceptance test in miniature.
 *
 * Stops after Step 4 (Metadata Analysis) deliberately: register_data_product
 * (a9_data_product_agent.py) fires unconditionally right after schema
 * inspection inside orchestrate_data_product_onboarding, so the
 * `data_products` row is already written by the time this step completes —
 * no need to drive the KPI-definition chat / validation / final-register
 * steps to answer the registry-population question.
 *
 * Phase 16 Onboarding item O2's confirmation gate (DEVELOPMENT_PLAN.md): the
 * wizard now pauses on a "Confirm Sign Convention" card after Metadata
 * Analysis, since hess has a live-detectable account_type/amount pair. This
 * spec drives through it — confirming as-detected — before checking
 * KPI Definition is reached, and is also how the confirmation gate itself
 * gets live-verified end to end (not just unit-tested against a mocked
 * provider).
 *
 * Run:  npx playwright test live-onboarding-hess-test
 * (uses the default playwright.config.ts — reuses the already-running dev
 * server started by restart_decision_studio_ui.ps1; NOT the mocked/fast
 * suite's assumptions, this hits the real backend/SQL Server/Supabase.)
 */

test.setTimeout(3 * 60_000);

test('onboarding wizard: register hess as a new (test-id) data product and inspect what gets written', async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem('a9_admin_mode', 'true');
    localStorage.setItem('a9_admin_target_client', 'hess');
  });

  await page.goto('/settings/data-onboarding');

  // ── Mode picker ─────────────────────────────────────────────────────────
  await page.getByRole('button', { name: /New Data Product/i }).click();

  // ── Step 1: Connection Setup ────────────────────────────────────────────
  await page.locator('select').first().selectOption('sqlserver');
  await page.getByPlaceholder('localhost').fill('localhost');
  await page.getByPlaceholder('agent9_lubricants').fill('agent9_lubricants');
  await page.getByPlaceholder('dbo').fill('dbo');
  await page.getByPlaceholder('sa').fill('sa');
  await page.getByPlaceholder('••••••••').fill('Agent9Test!2024');
  await page.getByRole('button', { name: /Continue to Discovery/i }).click();

  // ── Step 2: Schema Discovery ─────────────────────────────────────────────
  await page.getByRole('button', { name: /Start Discovery/i }).click();
  const hessTable = page.getByText('HessStarSchemaView', { exact: true });
  await hessTable.waitFor({ state: 'visible', timeout: 90_000 });
  await hessTable.click(); // selects the row (toggleTableSelection)
  await page.getByRole('button', { name: /Continue to Selection/i }).click();

  // ── Step 3: Data Product Selection ──────────────────────────────────────
  const TEST_DP_ID = 'dp_hess_financials_test';
  await page.getByPlaceholder('dp_sales_analytics').fill(TEST_DP_ID);
  await page.getByPlaceholder('Sales Analytics').fill('Hess Financials (Wizard Test)');
  await page.getByPlaceholder('Describe the business purpose of this data product...')
    .fill('Throwaway test registration via the onboarding wizard -- Phase 16 O6 acceptance check. Safe to delete.');
  await page.getByRole('button', { name: /Continue to Analysis/i }).click();

  // ── Step 4: Metadata Analysis -- this is where register_data_product fires ──
  await page.getByRole('button', { name: /Start Analysis/i }).click();

  // Wait for whichever comes first: the O2 confirmation card (hess has a
  // detectable convention, so this is the expected path), success with
  // nothing to confirm (moves straight to KPI Definition), or a visible
  // error -- any of the three tells us registration was attempted.
  const kpiDefHeading = page.getByRole('heading', { name: 'KPI Definition' });
  const errorBanner = page.locator('text=/Analysis failed|Registry registration error/i');
  const confirmButton = page.getByRole('button', { name: /Confirm Sign Convention/i });
  await Promise.race([
    kpiDefHeading.waitFor({ state: 'visible', timeout: 90_000 }),
    errorBanner.waitFor({ state: 'visible', timeout: 90_000 }),
    confirmButton.waitFor({ state: 'visible', timeout: 90_000 }),
  ]);

  const reachedConfirmationCard = await confirmButton.isVisible().catch(() => false);
  console.log(`[onboarding-test] reached O2 confirmation card: ${reachedConfirmationCard}`);
  expect(reachedConfirmationCard, 'hess has a live-detectable sign convention -- the confirmation gate must appear, not be silently skipped').toBe(true);

  await page.screenshot({ path: 'playwright-results/onboarding-hess-test-confirmation-card.png', fullPage: true });

  // Confirm as-detected (this spec doesn't test the "admin corrects it" path
  // -- that's covered by the unit tests) and wait for KPI Definition.
  await confirmButton.click();
  await kpiDefHeading.waitFor({ state: 'visible', timeout: 30_000 });

  await page.screenshot({ path: 'playwright-results/onboarding-hess-test-step4.png', fullPage: true });

  const reachedKpiStep = await kpiDefHeading.isVisible().catch(() => false);
  console.log(`[onboarding-test] reached KPI Definition step: ${reachedKpiStep}`);
  if (!reachedKpiStep) {
    const errText = await errorBanner.first().textContent().catch(() => null);
    console.log(`[onboarding-test] error banner text: ${errText}`);
  }

  // The actual assertion happens out-of-band: a direct Supabase query against
  // data_products WHERE id='dp_hess_financials_test' (see the conversation
  // for the query and result) -- Playwright's job here is only to drive the
  // real wizard and prove registration was attempted with real inputs.
  expect(reachedKpiStep, 'wizard must reach the KPI Definition step for register_data_product to have run').toBe(true);
});
