import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';
import { requireFeatureFlag } from './helpers/live-preflight';

/**
 * LIVE run #2 — Phase 19 mandatory framing gate, deliberately chosen to be
 * the STRUCTURAL OPPOSITE of live-framing-gate.spec.ts (gross_margin_pct):
 *
 *   gross_margin_pct                          ecommerce_revenue
 *   ---------------------------------------   ---------------------------------------
 *   problem mode                              mixed/opportunity-adjacent mode
 *   owned by the viewer (CFO viewing CFO KPI) owned by CFO, viewed by CEO (non-owner)
 *   6 causal-graph neighbours (1-2 hops)      0 causal-graph rows in kpi_relationships
 *                                              (verified via direct query before this
 *                                              run — see docs/architecture/
 *                                              problem_framing_design.md §12)
 *   10 genuine control_group-tagged           no control-group signal (problem mode
 *   benchmark_segments (DiD-shaped)           empties where_is_not)
 *
 * What run #1 could not prove and this run targets specifically:
 *   1. The non-owner attribution path (Decision #5) — "you own this KPI" must NOT
 *      render, and the payload's viewer_is_owner must be false while owner_role
 *      stays CFO — this is the live-verification counterpart to the
 *      _roles_match true-positive case run #1 already proved.
 *   2. The empty-causal-graph path — alternatives must be 0-1 (market-signal only,
 *      if MA detected a conflict) and NEVER fabricated, so this run is expected to
 *      exercise the confirm_stated branch rather than the alternative-reframe
 *      branch run #1 exercised.
 *   3. A mixed-mode analysis (not problem-mode) still produces a coherent framing
 *      prompt and reaches SF correctly — proves the gate isn't problem-mode-only.
 *
 * ceo_001 was picked over coo_001 specifically because SA situation-card
 * relevance is filtered by principal.business_process_ids ∩ kpi.business_process_ids
 * (finance_revenue_growth_analysis) — verified directly against principal_profiles
 * before this run: COO does not have that business process and would see no card
 * for this KPI at all; CEO does.
 *
 * Run:  npx playwright test --config=playwright.live.config.ts live-framing-gate-ecommerce
 * Requires the backend running with DA_ENABLE_FRAMING_GATE=true (verify via
 * GET /healthz -> features.da_enable_framing_gate before running this).
 */

const SCAN_TIMEOUT = 240_000;
const DA_TIMEOUT = 300_000;
const SF_TIMEOUT = 1_800_000;

test.describe('Live — Phase 19 framing gate (ecommerce_revenue, non-owner CEO viewer, mixed-mode)', () => {
  test.describe.configure({ mode: 'serial', timeout: 40 * 60_000 });

  test.beforeAll(async () => {
    await requireFeatureFlag('da_enable_framing_gate');
  });

  test('the gate handles a non-owner viewer and an empty causal graph without fabricating alternatives', async ({ page }, testInfo) => {
    const consoleErrors: string[] = [];
    page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
    page.on('pageerror', e => consoleErrors.push(`pageerror: ${e.message}`));

    // Capture the refine_analysis payloads AND the eventual SF dispatch —
    // both request and response, so the framing_decision the UI sent can be
    // compared against what was actually chosen on screen.
    const refinementTurns: Array<{ request: any; response: any }> = [];
    let sfRequestBody: any = null;
    let synthesisRequestId: string | null = null;
    let sfPayload: any = null;
    const stagesSeen: string[] = [];

    page.on('response', async res => {
      const u = res.url();
      try {
        if (u.includes('/workflows/deep-analysis/refine') && res.request().method() === 'POST') {
          const reqBody = JSON.parse(res.request().postData() || '{}');
          const resBody = await res.json();
          refinementTurns.push({ request: reqBody, response: resBody?.data ?? resBody });
        } else if (u.includes('/workflows/solutions/run') && res.request().method() === 'POST') {
          const body = JSON.parse(res.request().postData() || '{}');
          const stage = body?.preferences?.debate_stage ?? 'unspecified';
          stagesSeen.push(stage);
          if (stage === 'synthesis') sfRequestBody = body;
          const j = await res.json();
          const rid = j?.data?.request_id ?? j?.request_id;
          if (stage === 'synthesis' && rid) synthesisRequestId = rid;
        } else if (synthesisRequestId && u.includes(`/workflows/solutions/${synthesisRequestId}/status`)) {
          const j = await res.json();
          if (j?.data?.state === 'completed' && j?.data?.result) sfPayload = j.data.result;
        }
      } catch { /* non-JSON polls expected */ }
    });

    // ── Login as the lubricants CEO — does NOT own ecommerce_revenue (CFO does), ──
    // ── but shares its business process so the card is actually reachable ────────
    await page.goto('/login?mode=demo');
    await page.waitForSelector('[data-testid="principal-card-ceo_001"]', { timeout: 30_000 });
    await page.locator('[data-testid="principal-card-ceo_001"]').click();
    await page.locator('[data-testid="demo-enter-btn"]').click();
    await page.waitForURL('**/dashboard', { timeout: 30_000 });

    // ── SA ────────────────────────────────────────────────────────────────
    await page.waitForSelector('[data-testid="situation-grid"]', { timeout: SCAN_TIMEOUT });
    const cards = page.locator('[data-testid^="situation-card-"]');
    const cardCount = await cards.count();
    expect(cardCount, 'SA produced no situation cards').toBeGreaterThan(0);

    const cardText: string[] = [];
    for (let i = 0; i < cardCount; i++) {
      cardText.push(((await cards.nth(i).innerText()) || '').replace(/\s+/g, ' ').trim());
    }
    const preferred = ['e-commerce', 'ecommerce'];
    let target = -1;
    outer: for (const term of preferred) {
      for (let i = 0; i < cardCount; i++) {
        if (cardText[i].toLowerCase().includes(term)) { target = i; break outer; }
      }
    }
    expect(target, 'no situation card matched e-commerce/ecommerce for ceo_001 — check business_process_ids overlap').toBeGreaterThanOrEqual(0);
    console.log(`[framing] driving card [${target}]: ${cardText[target].slice(0, 120)}`);
    await cards.nth(target).click();

    // ── DA ────────────────────────────────────────────────────────────────
    const daTimedOut = page.getByText(/workflow timed out/i);
    const daLocked = page.getByText(/run deep analysis to unlock/i);
    await expect(async () => {
      if (await daTimedOut.count()) throw new Error('DA reported "Workflow timed out" in the UI');
      await expect(daLocked).toHaveCount(0);
    }).toPass({ timeout: DA_TIMEOUT, intervals: [2_000] });

    const openActionCenter = page.getByRole('button', { name: /open action center/i });
    if (await openActionCenter.count()) await openActionCenter.first().click();

    // The DA workflow record flips to "completed" only after Market Analysis
    // enrichment finishes too (it runs synchronously after execute_deep_analysis,
    // inside the same workflow) — the UI can briefly still read as locked/
    // re-analyzing for tens of seconds after daLocked's count first hits 0.
    const startRefinement = page.getByRole('button', { name: /start refinement session/i });
    const focusRecovery = page.getByRole('button', { name: /focus on recovery/i });
    const focusOpportunity = page.getByRole('button', { name: /focus on opportunity/i });
    const letAgent9Decide = page.getByRole('button', { name: /let agent9 decide/i });
    await expect(async () => {
      const [nStart, nRec, nOpp, nDec] = await Promise.all([
        startRefinement.count(), focusRecovery.count(), focusOpportunity.count(), letAgent9Decide.count(),
      ]);
      expect(nStart + nRec + nOpp + nDec).toBeGreaterThan(0);
    }).toPass({ timeout: 120_000, intervals: [2_000] });

    // Mixed-mode resolution gate — expected here (this KPI resolves to
    // analysis_mode="mixed" per the §12 investigation) and must be cleared
    // BEFORE framing can be meaningfully tested, otherwise "Generate
    // Solutions is blocked" would be true for the wrong reason.
    if (await letAgent9Decide.count()) {
      console.log('[framing] mixed-mode resolution gate present — resolving via "Let Agent9 Decide"');
      await letAgent9Decide.first().click();
      await page.waitForTimeout(1_000);
    } else if (await focusRecovery.count()) {
      console.log('[framing] mixed-mode resolution gate present — resolving via "Focus on Recovery"');
      await focusRecovery.first().click();
      await page.waitForTimeout(1_000);
    } else if (await focusOpportunity.count()) {
      console.log('[framing] mixed-mode resolution gate present — resolving via "Focus on Opportunity"');
      await focusOpportunity.first().click();
      await page.waitForTimeout(1_000);
    }

    await expect(startRefinement, 'Start Refinement Session must be reachable once mixed-mode (if any) is resolved').toBeVisible({ timeout: 60_000 });

    // ── CHECK 1: pre-gate DA console — real evidence visible, no SCQA block ──
    await page.screenshot({ path: testInfo.outputPath('01-da-pregate-top.png') });
    const rootCauseHeading = page.getByRole('button', { name: /^analysis/i }).first();
    if (await rootCauseHeading.count()) {
      await page.screenshot({ path: testInfo.outputPath('02-da-pregate-analysis-section.png') });
    }
    const scqaSituationLabel = page.getByText(/^situation$/i);
    const scqaPresentPreGate = await scqaSituationLabel.count();
    console.log(`[framing] SCQA label visible pre-gate (should be 0 while deferred): ${scqaPresentPreGate}`);

    // ── CHECK 2: no ENABLED "Generate Solutions" BUTTON reachable directly ──
    const enabledGenerateButton = page.getByRole('button', { name: /^generate solutions/i });
    const enabledCount = await enabledGenerateButton.count();
    console.log(`[framing] enabled "Generate Solutions" buttons visible pre-gate (should be 0): ${enabledCount}`);
    expect(enabledCount, 'a real (enabled) Generate Solutions button is reachable before framing is answered').toBe(0);

    // ── Start refinement — the gate must be the FIRST thing shown ───────────
    await startRefinement.click();
    const framingCard = page.getByTestId('framing-gate-card');
    await framingCard.waitFor({ state: 'visible', timeout: 90_000 });
    await page.waitForTimeout(1_000);
    await page.screenshot({ path: testInfo.outputPath('03-framing-gate-card.png'), fullPage: true });

    // ── CHECK 3: sequence — this must be turn 0's content, nothing else has run yet ──
    expect(refinementTurns.length, 'refine_analysis should have been called exactly once to reach this point').toBe(1);
    const turn0 = refinementTurns[0];
    console.log(`[framing] turn 0 response: current_topic=${turn0.response?.current_topic} framing_required=${turn0.response?.framing_required} has_framing_prompt=${!!turn0.response?.framing_prompt}`);
    expect(turn0.response?.current_topic, 'first topic must be problem_framing').toBe('problem_framing');
    expect(turn0.response?.framing_required, 'framing_required must be true on the presentation turn').toBe(true);
    expect(turn0.response?.topics_completed, 'nothing should be completed yet').toEqual([]);
    const framingPrompt = turn0.response?.framing_prompt;
    expect(framingPrompt, 'no framing_prompt in the turn-0 response').toBeTruthy();

    // ── CHECK 4: owner attribution — CFO owns ecommerce_revenue, CEO is viewing ──
    // This is the non-owner counterpart to run #1's CFO/CFO true-positive case.
    const ownerText = await page.getByText(/you own this kpi/i).count();
    console.log(`[framing] "you own this KPI" shown: ${!!ownerText} (payload owner_role=${framingPrompt?.owner_role}, viewer_is_owner=${framingPrompt?.viewer_is_owner})`);
    expect(framingPrompt?.owner_role, 'owner_role must still be CFO regardless of who is viewing').toBe('CFO');
    expect(framingPrompt?.viewer_is_owner, 'CEO must not be reported as the owner of a CFO-owned KPI').toBe(false);
    expect(ownerText, '"you own this KPI" must not render for a non-owner viewer').toBe(0);

    // ── CHECK 5: alternatives — verified live via direct SQL query before this run ──
    // that kpi_relationships has ZERO rows for ecommerce_revenue on lubricants in
    // either direction, so causal-graph alternatives MUST be empty here — any
    // alternative present must be market_signal-sourced only. This is the empty-
    // graph "never fabricate" path the unit tests assert with mocks; this proves
    // it against the real registry.
    const altButtons = page.getByTestId('framing-alternative');
    const altCount = await altButtons.count();
    console.log(`[framing] alternatives offered: payload=${framingPrompt?.alternatives?.length ?? 0} rendered=${altCount}`);
    expect(altCount, 'alternatives payload/DOM count mismatch').toBe(framingPrompt?.alternatives?.length ?? 0);
    for (const a of (framingPrompt?.alternatives ?? [])) {
      console.log(`  - [${a.source}] ${a.objective_text} (hops=${a.hops ?? 'n/a'}, provenance=${a.provenance ?? 'n/a'}, confidence=${a.confidence ?? 'n/a'})`);
    }
    const causalAlternatives = (framingPrompt?.alternatives ?? []).filter((a: any) => a.source === 'causal_graph');
    expect(causalAlternatives.length, 'kpi_relationships has zero rows for ecommerce_revenue — no causal-graph alternative should have been fabricated').toBe(0);

    // ── CHECK 6: submit is disabled until BOTH a choice AND a falsifier are given ──
    const submitBtn = page.getByTestId('framing-submit');
    await expect(submitBtn, 'submit must start disabled — nothing pre-selected').toBeDisabled();

    // Expected to be the confirm_stated branch (no causal alternatives; a
    // market-signal one may or may not be present depending on whether MA
    // detected a live conflict for this KPI/period) — but stay generic and
    // follow whatever the real payload actually offers, same as run #1.
    let chosenChoice: 'alternative' | 'confirm_stated';
    let chosenObjectiveText: string;
    if (altCount > 0) {
      chosenChoice = 'alternative';
      // Phase 20: the button's visible text is now a short label
      // (alternativeShortLabel), not the full objective_text sent to the
      // backend — read the real value from the already-captured payload via
      // data-kpi-id rather than parsing the DOM.
      const chosenKpiId = await altButtons.first().getAttribute('data-kpi-id');
      const chosenAlt = (framingPrompt?.alternatives ?? []).find((a: any) => a.kpi_id === chosenKpiId);
      chosenObjectiveText = chosenAlt?.objective_text ?? '';
      await altButtons.first().click();
    } else {
      chosenChoice = 'confirm_stated';
      chosenObjectiveText = framingPrompt?.stated_objective_text ?? '';
      await page.getByTestId('framing-confirm-stated').click();
    }
    await expect(submitBtn, 'submit must still be disabled with a choice but no falsifier').toBeDisabled();

    const falsifierText = 'If this KPI does not move as expected within two assessment cycles after acting on this objective, this frame was wrong.';
    await page.getByTestId('framing-falsifier-input').fill(falsifierText);
    await expect(submitBtn, 'submit must enable once both a choice and a falsifier are present').toBeEnabled();
    await page.screenshot({ path: testInfo.outputPath('04-framing-gate-filled.png'), fullPage: true });

    console.log(`[framing] submitting choice=${chosenChoice} objective="${chosenObjectiveText}"`);
    await submitBtn.click();

    // ── The submission turn: SCQA must appear, topics_completed must include problem_framing ──
    await expect.poll(() => refinementTurns.length, { timeout: 60_000, intervals: [1_000] }).toBeGreaterThanOrEqual(2);
    const turn1 = refinementTurns[1];
    console.log(`[framing] turn 1 (submission) response: topics_completed=${JSON.stringify(turn1.response?.topics_completed)} scqa_present=${!!turn1.response?.scqa_summary} framing_required=${turn1.response?.framing_required} next_topic=${turn1.response?.current_topic}`);

    expect(turn1.request?.framing_decision?.choice, 'the request must have carried the choice actually made').toBe(chosenChoice);
    expect(turn1.response?.topics_completed, 'problem_framing must be marked complete after submission').toContain('problem_framing');
    expect(turn1.response?.framing_required, 'framing_required must flip to false once answered').toBe(false);
    expect(turn1.response?.scqa_summary, 'the frame-aware SCQA must be present on the submission turn').toBeTruthy();
    expect(turn1.response?.current_topic, 'the interview must advance to a real next topic, not stall').not.toBe('problem_framing');

    const framingRecord = turn1.response?.framing_record;
    console.log(`[framing] framing_record: persisted=${framingRecord?.persisted} persist_error=${framingRecord?.persist_error ?? 'none'} decided_by_role=${framingRecord?.decided_by_role} decided_by_is_owner=${framingRecord?.decided_by_is_owner}`);
    expect(framingRecord?.decided_by_is_owner, 'CEO deciding on a CFO-owned KPI must be stamped as a non-owner decision').toBe(false);

    await page.waitForTimeout(1_000);
    await page.screenshot({ path: testInfo.outputPath('05-post-framing-next-topic.png'), fullPage: true });

    // The framing card must be GONE, replaced by the normal chat input.
    await expect(framingCard, 'framing card must not still be showing after submission').toHaveCount(0);

    // ── Skip to Solutions is now enabled — jump straight there ──────────────
    const skipButton = page.getByTitle(/skip to solutions/i);
    await expect(skipButton, 'Skip to Solutions must be enabled once framing is answered').toBeEnabled({ timeout: 30_000 });
    await skipButton.click();

    await page.getByRole('heading', { name: /assemble council/i }).waitFor({ state: 'visible', timeout: 60_000 });
    await page.screenshot({ path: testInfo.outputPath('06-persona-selector.png') });

    // ── Into Solution Finder — the one real dispatch click ───────────────────
    const generate = page.getByRole('button', { name: /^generate solutions/i });
    await generate.waitFor({ state: 'visible', timeout: 30_000 });
    await generate.click();
    await page.waitForURL('**/debate/**', { timeout: 60_000 });

    await page.waitForRequest(r => r.url().includes('/workflows/solutions/run'), { timeout: 120_000 });
    console.log('[framing] solutions/run dispatched — waiting on synthesis');
    await expect.poll(() => sfPayload !== null, { timeout: SF_TIMEOUT, intervals: [10_000] }).toBe(true);
    await page.waitForTimeout(3_000);

    // ── CHECK 7: the Slice 6 wiring fix — framing_decision actually reached SF ──
    const sentFramingDecision = sfRequestBody?.preferences?.refinement_result?.framing_decision;
    console.log(`[framing] framing_decision sent to solutions/run: ${JSON.stringify(sentFramingDecision)}`);
    expect(sentFramingDecision, 'framing_decision was not present in preferences.refinement_result sent to SF').toBeTruthy();
    expect(sentFramingDecision?.choice).toBe(chosenChoice);
    expect(sentFramingDecision?.chosen_objective_text).toBe(chosenObjectiveText);

    const sol = sfPayload?.solutions ?? sfPayload;
    console.log(`[framing] SF options: ${(sol?.options_ranked ?? []).map((o: any) => o.title).join(' | ')}`);

    await page.screenshot({ path: testInfo.outputPath('07-debate-complete.png'), fullPage: true });

    // ── Evidence bundle ───────────────────────────────────────────────────
    fs.mkdirSync(testInfo.outputDir, { recursive: true });
    fs.writeFileSync(
      path.join(testInfo.outputDir, 'refinement-turns.json'),
      JSON.stringify(refinementTurns, null, 2), 'utf-8',
    );
    fs.writeFileSync(
      path.join(testInfo.outputDir, 'sf-request-and-response.json'),
      JSON.stringify({ request: sfRequestBody, response: sfPayload }, null, 2), 'utf-8',
    );
    const summary = {
      kpi: 'ecommerce_revenue',
      viewer_principal: 'ceo_001',
      chosen_choice: chosenChoice,
      chosen_objective_text: chosenObjectiveText,
      alternatives_offered: framingPrompt?.alternatives?.map((a: any) => ({ source: a.source, objective_text: a.objective_text, hops: a.hops })) ?? [],
      owner_role: framingPrompt?.owner_role,
      viewer_is_owner: framingPrompt?.viewer_is_owner,
      framing_record: framingRecord,
      scqa_after_submission_present: !!turn1.response?.scqa_summary,
      framing_decision_reached_sf: !!sentFramingDecision,
      stages: stagesSeen,
    };
    fs.writeFileSync(
      path.join(testInfo.outputDir, 'framing-gate-summary.json'),
      JSON.stringify(summary, null, 2), 'utf-8',
    );
    console.log('[framing] summary:', JSON.stringify(summary, null, 2));

    // ── No React failures ────────────────────────────────────────────────
    const realErrors = consoleErrors.filter(e => !/favicon|net::ERR|Failed to load resource|429|404/i.test(e));
    expect(realErrors, `console errors: ${realErrors.slice(0, 5).join(' | ')}`).toEqual([]);
  });
});
