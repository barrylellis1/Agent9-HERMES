import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * LIVE run — Phase 13 Cat 3 briefing UI against a real lubricants pipeline.
 *
 * Sibling of live-causal-grounding.spec.ts, which drives the same SA -> DA -> SF
 * sequence but stops at /debate. This one carries on to /briefing/:id, because
 * Cat 3's components live only on that page and nothing has ever rendered them
 * with real data.
 *
 * WHAT THIS IS ACTUALLY TESTING
 * -----------------------------
 * The defect Cat 3 fixed was not a missing component — it was four fields that
 * the backend produced, typed, and shipped over the wire, which buildExecutiveBriefing
 * then dropped one map() short of the screen. A test that only asserts "a panel
 * rendered" would not have caught that and will not catch its recurrence.
 *
 * So the core assertions compare the SF PAYLOAD against the DOM:
 *   payload has decision_ask  <=>  the ask is on screen
 *   payload immediate_actions <=>  the same number of checklist rows
 *   payload key_assumptions   <=>  an assumptions panel on that option
 * Disagreement between the two is the finding, in either direction.
 *
 * Fields the model may legitimately omit are RECORDED, not failed. Failing a live
 * run because one LLM response had no flagged side effect would make this a test
 * of the model's mood. The structural agreement above is what must hold.
 *
 * Run:  npx playwright test --config=playwright.live.config.ts live-briefing-cat3
 * Costs real tokens (~1 Haiku stage-1 + 1 Sonnet synthesis w/ critic + moderator).
 */

const SCAN_TIMEOUT = 240_000;
const DA_TIMEOUT = 300_000;
const SF_TIMEOUT = 1_800_000;

/**
 * Phase 18 / M3 settlement: no consulting-firm identity on the briefing surface.
 *
 * Word-boundary matched so "Bain" cannot fire on "bargain" and "EY" cannot fire
 * on every third word. This is the one assertion here that is genuinely binary —
 * a firm name either appears in the exported artifact or it does not.
 */
const FIRM_NAMES = [
  /\bMcKinsey\b/i, /\bBCG\b/, /\bBoston Consulting\b/i, /\bBain\b/i,
  /\bDeloitte\b/i, /\bAccenture\b/i, /\bKPMG\b/, /\bPwC\b/i, /\bParthenon\b/i,
];

test.describe('Live — Phase 13 Cat 3 briefing UI', () => {
  test.describe.configure({ mode: 'serial', timeout: 40 * 60_000 });

  test('drive the pipeline and render the briefing from real SF output', async ({ page }, testInfo) => {
    const consoleErrors: string[] = [];
    page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
    page.on('pageerror', e => consoleErrors.push(`pageerror: ${e.message}`));

    // Capture the synthesis payload off the wire — see live-causal-grounding for
    // why matching the request_id matters: BOTH dispatches hit the same endpoint
    // and grading the stage1_only response scores a document that has not been
    // written yet.
    let synthesisRequestId: string | null = null;
    let sfPayload: any = null;
    const stagesSeen: string[] = [];

    page.on('response', async res => {
      const u = res.url();
      try {
        if (u.includes('/workflows/solutions/run') && res.request().method() === 'POST') {
          const body = JSON.parse(res.request().postData() || '{}');
          const stage = body?.preferences?.debate_stage ?? 'unspecified';
          stagesSeen.push(stage);
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
    const preferred = ['cost of goods', 'cogs', 'raw materials', 'gross margin'];
    let target = 0;
    outer: for (const term of preferred) {
      for (let i = 0; i < cardCount; i++) {
        if (cardText[i].toLowerCase().includes(term)) { target = i; break outer; }
      }
    }
    console.log(`[cat3] driving card [${target}]: ${cardText[target].slice(0, 120)}`);
    await cards.nth(target).click();

    // ── DA ────────────────────────────────────────────────────────────────────
    // Same signal as live-causal-grounding: the Action Center's LOCKED state
    // clearing. Every cheaper signal there turned out to render regardless of
    // whether DA had produced anything.
    const daTimedOut = page.getByText(/workflow timed out/i);
    const daLocked = page.getByText(/run deep analysis to unlock/i);
    await expect(async () => {
      if (await daTimedOut.count()) throw new Error('DA reported "Workflow timed out" in the UI');
      await expect(daLocked).toHaveCount(0);
    }).toPass({ timeout: DA_TIMEOUT, intervals: [2_000] });

    const openActionCenter = page.getByRole('button', { name: /open action center/i });
    if (await openActionCenter.count()) await openActionCenter.first().click();

    // ── SF: four interactions, none of which dispatch on their own ────────────
    const focusRecovery = page.getByRole('button', { name: /focus on recovery/i });
    const generate = page.getByRole('button', { name: /^generate solutions/i });
    await expect(async () => {
      const [nR, nG] = await Promise.all([focusRecovery.count(), generate.count()]);
      expect(nR + nG).toBeGreaterThan(0);
    }).toPass({ timeout: 120_000, intervals: [1_000] });

    if (await focusRecovery.count()) await focusRecovery.first().click();
    await generate.waitFor({ state: 'visible', timeout: 60_000 });
    await generate.click();
    await page.getByRole('heading', { name: /assemble council/i })
      .waitFor({ state: 'visible', timeout: 60_000 });
    await generate.click();
    await page.waitForURL('**/debate/**', { timeout: 60_000 });

    await page.waitForRequest(r => r.url().includes('/workflows/solutions/run'), { timeout: 120_000 });
    console.log('[cat3] solutions/run dispatched — waiting on synthesis');
    await expect.poll(() => sfPayload !== null, { timeout: SF_TIMEOUT, intervals: [10_000] }).toBe(true);
    await page.waitForTimeout(5_000);

    fs.mkdirSync(testInfo.outputDir, { recursive: true });
    fs.writeFileSync(
      path.join(testInfo.outputDir, 'sf-synthesis-payload.json'),
      JSON.stringify(sfPayload, null, 2), 'utf-8',
    );
    console.log(`[cat3] stages: ${stagesSeen.join(' -> ')}`);

    // ── Into the briefing ─────────────────────────────────────────────────────
    const viewBriefing = page.getByRole('button', { name: /view executive briefing/i });
    await viewBriefing.waitFor({ state: 'visible', timeout: 120_000 });
    await viewBriefing.click();
    await page.waitForURL('**/briefing/**', { timeout: 60_000 });
    await page.waitForTimeout(2_000);
    await page.screenshot({ path: testInfo.outputPath('10-briefing-top.png') });
    await page.screenshot({ path: testInfo.outputPath('11-briefing-full.png'), fullPage: true });

    // The page must not have fallen back to the empty state — that would mean
    // buildExecutiveBriefing never wrote localStorage, and every assertion below
    // would then be vacuously "absent".
    await expect(
      page.getByRole('heading', { name: /briefing not generated yet/i }),
      'briefing page fell back to the not-generated empty state',
    ).toHaveCount(0);

    // The status endpoint returns `result` as `{ solutions: {...} }` — the SF
    // response is nested one level down, which is also the level the UI consumes
    // (buildExecutiveBriefing's `sol`). Reading the outer object instead makes
    // every field look absent and turns the payload-vs-DOM comparison below into
    // a comparison against undefined. That is exactly how the first run of this
    // spec reported a phantom "decision_ask is NOT in the payload but the DOM
    // shows it" against output that was entirely correct.
    //
    // `?? sfPayload` tolerates an unwrapped shape rather than assuming one.
    const sol = sfPayload?.solutions ?? sfPayload;
    expect(sol, 'SF result had neither a solutions wrapper nor a usable body').toBeTruthy();

    // ── 1. Decision ask: payload and DOM must agree ───────────────────────────
    const askInPayload = Boolean(sol?.decision_ask?.decision_text);
    await expect(page.getByTestId('decision-ask-block')).toBeVisible();
    const askTextCount = await page.getByTestId('decision-ask-text').count();
    const askAbsentCount = await page.getByTestId('decision-ask-absent').count();

    expect(askTextCount + askAbsentCount,
      'the ask block rendered neither an ask nor the honest-absence line').toBe(1);
    expect(askTextCount === 1,
      `decision_ask ${askInPayload ? 'IS' : 'is NOT'} in the payload but the DOM ${
        askTextCount ? 'shows' : 'does not show'} it — the drop-on-the-floor bug class`,
    ).toBe(askInPayload);

    const askText = askTextCount ? (await page.getByTestId('decision-ask-text').innerText()).trim() : null;
    if (askText) {
      // M2's ≤25-word cap is enforced at schema validation on the backend. Checking
      // it here too is cheap and catches a validator that silently stopped running.
      const words = askText.split(/\s+/).filter(Boolean).length;
      console.log(`[cat3] decision ask (${words} words): ${askText}`);
      expect(words, `decision ask is ${words} words, M2 caps it at 25`).toBeLessThanOrEqual(25);
    }

    // ── 2. Immediate actions: counts must match exactly ───────────────────────
    const actionsInPayload: any[] = sol?.immediate_actions ?? [];
    const renderedActions = await page.getByTestId('immediate-action').count();
    console.log(`[cat3] immediate actions — payload ${actionsInPayload.length}, rendered ${renderedActions}`);
    if (actionsInPayload.length) {
      expect(renderedActions,
        'immediate_actions were in the payload but did not all reach the checklist',
      ).toBe(actionsInPayload.length);
    }

    // ── 3. Assumptions panels: one per option that has assumptions ────────────
    const optionsInPayload: any[] = sol?.options_ranked ?? [];
    // The briefing renders the top 3 ranked options, so compare against that slice.
    const optionsWithAssumptions = optionsInPayload
      .slice(0, 3)
      .filter(o => Array.isArray(o?.key_assumptions) && o.key_assumptions.length > 0).length;
    const renderedPanels = await page.getByTestId('assumptions-panel').count();
    console.log(`[cat3] assumptions panels — options carrying them ${optionsWithAssumptions}, panels rendered ${renderedPanels}`);
    expect(renderedPanels,
      'an option carried key_assumptions but no panel rendered for it (or vice versa)',
    ).toBe(optionsWithAssumptions);

    // ── 4. Option 0 ───────────────────────────────────────────────────────────
    // deriveStatusQuo always returns an object (M4: never blank), so the column is
    // unconditional once the options accordion is open.
    await expect(page.getByTestId('status-quo-column'),
      'Option 0 baseline column is missing from the comparison table',
    ).toBeVisible();

    // ── 5. Stage E side effects, recorded not required ────────────────────────
    const sideEffectOptions = optionsInPayload
      .slice(0, 3)
      .filter(o => Array.isArray(o?.flagged_side_effects) && o.flagged_side_effects.length > 0).length;
    const renderedChips = await page.getByTestId('side-effects-chip').count();
    console.log(`[cat3] critic side effects — options flagged ${sideEffectOptions}, chips rendered ${renderedChips}`);
    expect(renderedChips, 'a flagged side effect did not reach the option card').toBe(sideEffectOptions);

    // ── 6. De-branding: binary, and the whole point of the M3 settlement ──────
    const pageText = await page.locator('body').innerText();
    const leaked = FIRM_NAMES.filter(re => re.test(pageText)).map(re => re.source);
    expect(leaked, `consulting-firm names on the briefing surface: ${leaked.join(', ')}`).toEqual([]);

    // ── 7. The drawer, which is where the narrative now lives ─────────────────
    // Also where lens_views actually lands — the ONE live check this run exists
    // for. 2026-08-17: PerspectiveAnalysis -> LensView, option.perspectives ->
    // option.lens_views, and the synthesis prompt's JSON key was renamed to
    // match. Every other check today is regression coverage for things already
    // proven live; this is the one genuine behavior risk — whether the model
    // honours a renamed key as reliably as the old one, first time, with no
    // prior live data to compare against.
    const viewFull = page.getByRole('button', { name: /view full analysis/i });
    if (await viewFull.count()) {
      await viewFull.first().click();
      await page.waitForTimeout(600);
      await page.screenshot({ path: testInfo.outputPath('12-option-drawer.png') });
      await expect(page.getByRole('button', { name: /close option detail/i })).toBeVisible();

      // Payload-vs-DOM, same discipline as the other checks in this file: count
      // what the model returned under EITHER key, and confirm the same count
      // rendered. `lens_views` is what the prompt now asks for; `perspectives`
      // is the pre-rename key a model might still emit, and the parser's
      // dual-key fallback exists precisely so that doesn't silently drop data —
      // this is what actually proves that fallback fires correctly against a
      // real (not synthetic) model response.
      // .first() always opens the DOM-order-first "View full analysis" button,
      // which is the briefing's option index 0 (the top-ranked option, since
      // the briefing renders data.options in ranked order).
      const optForDrawer = optionsInPayload[0]
      const lensViewsInPayload: any[] = optForDrawer?.lens_views ?? optForDrawer?.perspectives ?? []
      const renderedLensItems = await page.getByTestId('council-lens-item').count()
      console.log(`[cat3] lens_views (opt idx 0) — payload ${lensViewsInPayload.length}, rendered ${renderedLensItems}`)
      expect(renderedLensItems,
        'lens_views/perspectives count mismatch — the rename or its dual-key fallback dropped data',
      ).toBe(lensViewsInPayload.length)
      if (lensViewsInPayload.length) {
        // Confirms the prompt's renamed key round-tripped as STRUCTURED data,
        // not just that a count matched by coincidence.
        const firstLensText = await page.getByTestId('council-lens-item').first().innerText()
        expect(firstLensText.trim().length,
          'a lens_views entry rendered with no readable content',
        ).toBeGreaterThan(0)
      }

      await page.keyboard.press('Escape');
      await page.waitForTimeout(400);
      await expect(page.getByRole('button', { name: /close option detail/i })).toHaveCount(0);
    }

    // ── 8. No React failures on the restructured page ─────────────────────────
    // Filter network noise: a failed supplementary fetch is not a rendering defect
    // and this page deliberately tolerates several.
    const realErrors = consoleErrors.filter(e =>
      !/favicon|net::ERR|Failed to load resource|429|404/i.test(e));
    await testInfo.attach('console-errors.json', {
      body: JSON.stringify({ all: consoleErrors, filtered: realErrors }, null, 2),
      contentType: 'application/json',
    });
    expect(realErrors, `console errors on the briefing page: ${realErrors.slice(0, 3).join(' | ')}`).toEqual([]);

    // ── Evidence bundle ───────────────────────────────────────────────────────
    const summary = {
      decision_ask: { in_payload: askInPayload, rendered: askTextCount === 1, text: askText },
      immediate_actions: { in_payload: actionsInPayload.length, rendered: renderedActions },
      assumptions: { options_carrying: optionsWithAssumptions, panels_rendered: renderedPanels },
      side_effects: { options_flagged: sideEffectOptions, chips_rendered: renderedChips },
      status_quo_column: true,
      firm_names_leaked: leaked,
      stages: stagesSeen,
    };
    fs.writeFileSync(
      path.join(testInfo.outputDir, 'cat3-summary.json'),
      JSON.stringify(summary, null, 2), 'utf-8',
    );
    await testInfo.attach('cat3-summary.json', {
      body: JSON.stringify(summary, null, 2), contentType: 'application/json',
    });
    console.log('[cat3] summary:', JSON.stringify(summary, null, 2));
  });
});
