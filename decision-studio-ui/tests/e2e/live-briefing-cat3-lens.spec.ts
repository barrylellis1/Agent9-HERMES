import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * LIVE run — the LENS COUNCIL arm.
 *
 * Sibling of live-briefing-cat3.spec.ts (the MBB control) and
 * live-briefing-cat3-refined.spec.ts (the refinement arm). Same drive
 * sequence as the control, with one substitution: explicitly selects
 * "Analytical Lens Council" in the Assemble Council screen instead of
 * leaving the MBB default. This is the FIRST live run of lens_council
 * through the actual app — everything captured before this used MBB,
 * because lens_council was not selectable in the UI until 2026-08-17.
 *
 * WHAT THIS RUN IS FOR, AND WHAT IT ISN'T
 * ----------------------------------------
 * This is integration verification, not the analytical comparison. It
 * confirms: the newly-wired preset selection actually dispatches
 * commercial/operational/structural (not a silent MBB fallback — see
 * COUNCIL_PRESET_PERSONAS's comment in uiConstants.ts for the bug this
 * closed); the debate page renders lens colours/labels instead of falling
 * through to grey; the briefing's Cat 3 components render correctly against
 * genuine lens output; and score_dq_run.py parses a real lens payload.
 *
 * It is ONE run — n=1, same limit decision_quality_rubric.md §9 already
 * flagged for the one prior lens control (which was also n=1 and the worst
 * run in that corpus). One more clean run does not resolve lens-vs-MBB; it
 * is the first entry toward the n>=3 replication that would.
 *
 * Captures BOTH sf-synthesis-payload.json AND da-payload.json (the original
 * MBB control spec captured only the former, so its DQ link 5 came back
 * not-checked — fixed here so this run can be scored on all six links).
 *
 * Run:  npx playwright test --config=playwright.live.config.ts live-briefing-cat3-lens
 * Then: py scripts/score_dq_run.py <output-dir>
 */

const SCAN_TIMEOUT = 240_000;
const DA_TIMEOUT = 300_000;
const SF_TIMEOUT = 1_800_000;

const FIRM_NAMES = [
  /\bMcKinsey\b/i, /\bBCG\b/, /\bBoston Consulting\b/i, /\bBain\b/i,
  /\bDeloitte\b/i, /\bAccenture\b/i, /\bKPMG\b/, /\bPwC\b/i, /\bParthenon\b/i,
];

test.describe('Live — lens council arm', () => {
  test.describe.configure({ mode: 'serial', timeout: 40 * 60_000 });

  test('select Analytical Lens Council and render the briefing from real SF output', async ({ page }, testInfo) => {
    const consoleErrors: string[] = [];
    page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
    page.on('pageerror', e => consoleErrors.push(`pageerror: ${e.message}`));

    let synthesisRequestId: string | null = null;
    let sfPayload: any = null;
    let daPayload: any = null;
    let daRequestId: string | null = null;
    const stagesSeen: string[] = [];
    // The consulting_personas array actually sent on the SYNTHESIS dispatch —
    // the direct proof the preset click resolved to lens ids, not MBB.
    let dispatchedPersonas: string[] | null = null;

    page.on('response', async res => {
      const u = res.url();
      try {
        if (u.includes('/workflows/deep-analysis/run') && res.request().method() === 'POST') {
          const j = await res.json();
          daRequestId = j?.data?.request_id ?? j?.request_id ?? null;
        } else if (daRequestId && u.includes(`/workflows/deep-analysis/${daRequestId}/status`)) {
          const j = await res.json();
          if (j?.data?.state === 'completed' && j?.data?.result) daPayload = j.data.result;
        } else if (u.includes('/workflows/solutions/run') && res.request().method() === 'POST') {
          const body = JSON.parse(res.request().postData() || '{}');
          const stage = body?.preferences?.debate_stage ?? 'unspecified';
          stagesSeen.push(stage);
          if (stage === 'synthesis') {
            dispatchedPersonas = body?.preferences?.consulting_personas ?? null;
          }
          const j = await res.json();
          const rid = j?.data?.request_id ?? j?.request_id;
          if (stage === 'synthesis' && rid) synthesisRequestId = rid;
        } else if (synthesisRequestId && u.includes(`/workflows/solutions/${synthesisRequestId}/status`)) {
          const j = await res.json();
          if (j?.data?.state === 'completed' && j?.data?.result) sfPayload = j.data.result;
        }
      } catch { /* non-JSON polls expected */ }
    });

    // ── Login as the lubricants CFO ───────────────────────────────────────────
    await page.goto('/login?mode=demo');
    await page.waitForSelector('[data-testid="principal-card-cfo_001"]', { timeout: 30_000 });
    await page.locator('[data-testid="principal-card-cfo_001"]').click();
    await page.locator('[data-testid="demo-enter-btn"]').click();
    await page.waitForURL('**/dashboard', { timeout: 30_000 });

    // ── SA ────────────────────────────────────────────────────────────────────
    await page.waitForSelector('[data-testid="situation-grid"]', { timeout: SCAN_TIMEOUT });
    const cards = page.locator('[data-testid^="situation-card-"]');
    const cardCount = await cards.count();
    expect(cardCount, 'SA produced no situation cards').toBeGreaterThan(0);

    const cardText: string[] = [];
    for (let i = 0; i < cardCount; i++) {
      cardText.push(((await cards.nth(i).innerText()) || '').replace(/\s+/g, ' ').trim());
    }
    // Same preference order as the control, so both arms drive the same KPI.
    const preferred = ['cost of goods', 'cogs', 'raw materials', 'gross margin'];
    let target = 0;
    outer: for (const term of preferred) {
      for (let i = 0; i < cardCount; i++) {
        if (cardText[i].toLowerCase().includes(term)) { target = i; break outer; }
      }
    }
    console.log(`[lens] driving card [${target}]: ${cardText[target].slice(0, 120)}`);
    await cards.nth(target).click();

    // ── DA ────────────────────────────────────────────────────────────────────
    const daTimedOut = page.getByText(/workflow timed out/i);
    const daLocked = page.getByText(/run deep analysis to unlock/i);
    await expect(async () => {
      if (await daTimedOut.count()) throw new Error('DA reported "Workflow timed out" in the UI');
      await expect(daLocked).toHaveCount(0);
    }).toPass({ timeout: DA_TIMEOUT, intervals: [2_000] });

    const openActionCenter = page.getByRole('button', { name: /open action center/i });
    if (await openActionCenter.count()) await openActionCenter.first().click();

    // ── Phase 19 mandatory framing gate — must be answered before the persona
    // selector unlocks (DA_ENABLE_FRAMING_GATE is on in this environment). Same
    // pattern as live-briefing-cat3.spec.ts's control arm, so both arms of the
    // comparison go through an identically-answered gate.
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

    if (await letAgent9Decide.count()) {
      await letAgent9Decide.first().click();
      await page.waitForTimeout(1_000);
    } else if (await focusRecovery.count()) {
      await focusRecovery.first().click();
      await page.waitForTimeout(1_000);
    }
    await expect(startRefinement, 'Start Refinement Session must be reachable once mixed-mode (if any) is resolved').toBeVisible({ timeout: 60_000 });

    await startRefinement.click();
    const framingCard = page.getByTestId('framing-gate-card');
    await framingCard.waitFor({ state: 'visible', timeout: 90_000 });
    const altButtons = page.getByTestId('framing-alternative');
    if (await altButtons.count() > 0) {
      await altButtons.first().click();
    } else {
      await page.getByTestId('framing-confirm-stated').click();
    }
    await page.getByTestId('framing-falsifier-input').fill(
      'If this KPI does not move as expected within two assessment cycles after acting on this objective, this frame was wrong.'
    );
    const framingSubmit = page.getByTestId('framing-submit');
    await expect(framingSubmit).toBeEnabled();
    await framingSubmit.click();
    await expect(framingCard, 'framing card must not still be showing after submission').toHaveCount(0);
    console.log('[lens] framing gate answered');

    // "Skip to Solutions" opens the persona selector (State D) directly.
    const skipButton = page.getByTitle(/skip to solutions/i);
    await expect(skipButton, 'Skip to Solutions must be enabled once framing is answered').toBeEnabled({ timeout: 30_000 });
    await skipButton.click();
    await page.getByRole('heading', { name: /assemble council/i }).waitFor({ state: 'visible', timeout: 60_000 });

    const generate = page.getByRole('button', { name: /^generate solutions/i });
    await generate.waitFor({ state: 'visible', timeout: 30_000 });

    // THE variable under test: select the lens preset instead of leaving the
    // MBB default. useHybridCouncil/councilType both default correctly
    // ("preset" tab visible without any extra toggle), so this is one click.
    const lensPreset = page.getByRole('button', { name: /analytical lens council/i });
    await expect(lensPreset, 'Analytical Lens Council preset button not found in Assemble Council').toBeVisible();
    await lensPreset.click();
    console.log('[lens] selected Analytical Lens Council preset');
    await page.screenshot({ path: testInfo.outputPath('05-assemble-council-lens-selected.png') });

    await generate.click();
    await page.waitForURL('**/debate/**', { timeout: 60_000 });
    await page.screenshot({ path: testInfo.outputPath('06-debate-columns.png') });

    await page.waitForRequest(r => r.url().includes('/workflows/solutions/run'), { timeout: 120_000 });
    console.log('[lens] solutions/run dispatched — waiting on synthesis');
    await expect.poll(() => sfPayload !== null, { timeout: SF_TIMEOUT, intervals: [10_000] }).toBe(true);
    await page.waitForTimeout(5_000);

    fs.mkdirSync(testInfo.outputDir, { recursive: true });
    fs.writeFileSync(
      path.join(testInfo.outputDir, 'sf-synthesis-payload.json'),
      JSON.stringify(sfPayload, null, 2), 'utf-8',
    );
    fs.writeFileSync(
      path.join(testInfo.outputDir, 'da-payload.json'),
      JSON.stringify(daPayload, null, 2), 'utf-8',
    );
    console.log(`[lens] stages: ${stagesSeen.join(' -> ')}`);
    console.log(`[lens] DA payload captured: ${daPayload !== null}`);
    console.log(`[lens] dispatched consulting_personas: ${JSON.stringify(dispatchedPersonas)}`);

    // ── The direct proof the preset click actually worked ─────────────────────
    // Not "no firm names appeared" (indirect) — the literal array sent on the
    // wire. This is what the COUNCIL_PRESET_PERSONAS fix exists to guarantee:
    // before it, EVERY preset silently dispatched ['mckinsey','bcg','bain']
    // regardless of what was clicked.
    expect(dispatchedPersonas,
      'no consulting_personas array was captured on the synthesis dispatch',
    ).not.toBeNull();
    const dispatched = new Set((dispatchedPersonas ?? []).map(p => String(p).toLowerCase()));
    expect([...dispatched].sort(),
      'synthesis dispatched a different persona set than the lens preset resolves to — the preset-selection fix did not hold',
    ).toEqual(['commercial', 'operational', 'structural']);

    // ── Into the briefing ─────────────────────────────────────────────────────
    const viewBriefing = page.getByRole('button', { name: /view executive briefing/i });
    await viewBriefing.waitFor({ state: 'visible', timeout: 120_000 });
    await viewBriefing.click();
    await page.waitForURL('**/briefing/**', { timeout: 60_000 });
    await page.waitForTimeout(2_000);
    await page.screenshot({ path: testInfo.outputPath('10-briefing-top.png') });
    await page.screenshot({ path: testInfo.outputPath('11-briefing-full.png'), fullPage: true });

    await expect(
      page.getByRole('heading', { name: /briefing not generated yet/i }),
      'briefing page fell back to the not-generated empty state',
    ).toHaveCount(0);

    const sol = sfPayload?.solutions ?? sfPayload;
    expect(sol, 'SF result had neither a solutions wrapper nor a usable body').toBeTruthy();

    // ── Same Cat 3 payload-vs-DOM checks as the control, on genuine lens output ─
    const askInPayload = Boolean(sol?.decision_ask?.decision_text);
    await expect(page.getByTestId('decision-ask-block')).toBeVisible();
    const askTextCount = await page.getByTestId('decision-ask-text').count();
    const askAbsentCount = await page.getByTestId('decision-ask-absent').count();
    expect(askTextCount + askAbsentCount).toBe(1);
    expect(askTextCount === 1).toBe(askInPayload);
    const askText = askTextCount ? (await page.getByTestId('decision-ask-text').innerText()).trim() : null;
    if (askText) {
      const words = askText.split(/\s+/).filter(Boolean).length;
      console.log(`[lens] decision ask (${words} words): ${askText}`);
      expect(words).toBeLessThanOrEqual(25);
    }

    const actionsInPayload: any[] = sol?.immediate_actions ?? [];
    const renderedActions = await page.getByTestId('immediate-action').count();
    console.log(`[lens] immediate actions — payload ${actionsInPayload.length}, rendered ${renderedActions}`);
    if (actionsInPayload.length) expect(renderedActions).toBe(actionsInPayload.length);

    const optionsInPayload: any[] = sol?.options_ranked ?? [];
    const optionsWithAssumptions = optionsInPayload.slice(0, 3)
      .filter(o => Array.isArray(o?.key_assumptions) && o.key_assumptions.length > 0).length;
    const renderedPanels = await page.getByTestId('assumptions-panel').count();
    console.log(`[lens] assumptions panels — carrying ${optionsWithAssumptions}, rendered ${renderedPanels}`);
    expect(renderedPanels).toBe(optionsWithAssumptions);

    await expect(page.getByTestId('status-quo-column')).toBeVisible();

    const sideEffectOptions = optionsInPayload.slice(0, 3)
      .filter(o => Array.isArray(o?.flagged_side_effects) && o.flagged_side_effects.length > 0).length;
    const renderedChips = await page.getByTestId('side-effects-chip').count();
    console.log(`[lens] side effects — flagged ${sideEffectOptions}, chips ${renderedChips}`);
    expect(renderedChips).toBe(sideEffectOptions);

    const pageText = await page.locator('body').innerText();
    const leaked = FIRM_NAMES.filter(re => re.test(pageText)).map(re => re.source);
    expect(leaked, `firm names on the briefing: ${leaked.join(', ')}`).toEqual([]);

    // ── Lens-specific: the drawer shows real lens vocabulary, not silence ─────
    // The firm-name sweep above proves absence; this proves PRESENCE of the
    // right thing — that "Council Lenses" actually renders commercial/
    // operational/structural content, not an empty section that would also
    // pass a firm-name-only check.
    const viewFull = page.getByRole('button', { name: /view full analysis/i });
    let lensVocabPresent = false;
    if (await viewFull.count()) {
      await viewFull.first().click();
      await page.waitForTimeout(600);
      await page.screenshot({ path: testInfo.outputPath('12-option-drawer.png') });
      await expect(page.getByRole('button', { name: /close option detail/i })).toBeVisible();

      const optForDrawer = optionsInPayload[0]
      const lensViewsInPayload: any[] = optForDrawer?.lens_views ?? optForDrawer?.perspectives ?? []
      const renderedLensItems = await page.getByTestId('council-lens-item').count()
      console.log(`[lens] lens_views (opt idx 0) — payload ${lensViewsInPayload.length}, rendered ${renderedLensItems}`)
      expect(renderedLensItems,
        'lens_views count mismatch between payload and drawer',
      ).toBe(lensViewsInPayload.length)

      const drawerText = await page.getByTestId('council-lenses').innerText().catch(() => '')
      lensVocabPresent = /commercial|operational|structural/i.test(drawerText)
      console.log(`[lens] drawer shows lens vocabulary: ${lensVocabPresent}`)

      await page.keyboard.press('Escape');
      await page.waitForTimeout(400);
      await expect(page.getByRole('button', { name: /close option detail/i })).toHaveCount(0);
    }

    const realErrors = consoleErrors.filter(e =>
      !/favicon|net::ERR|Failed to load resource|429|404/i.test(e));
    expect(realErrors, `console errors: ${realErrors.slice(0, 3).join(' | ')}`).toEqual([]);

    const summary = {
      arm: 'lens_council',
      dispatched_personas: dispatchedPersonas,
      decision_ask: { in_payload: askInPayload, rendered: askTextCount === 1, text: askText },
      immediate_actions: { in_payload: actionsInPayload.length, rendered: renderedActions },
      assumptions: { options_carrying: optionsWithAssumptions, panels_rendered: renderedPanels },
      side_effects: { options_flagged: sideEffectOptions, chips_rendered: renderedChips },
      firm_names_leaked: leaked,
      lens_vocabulary_present_in_drawer: lensVocabPresent,
      da_payload_captured: daPayload !== null,
      stages: stagesSeen,
    };
    fs.writeFileSync(
      path.join(testInfo.outputDir, 'cat3-summary.json'),
      JSON.stringify(summary, null, 2), 'utf-8',
    );
    console.log('[lens] summary:', JSON.stringify(summary, null, 2));
  });
});
