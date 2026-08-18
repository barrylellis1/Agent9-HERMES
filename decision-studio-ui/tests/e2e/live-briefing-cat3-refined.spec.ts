import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * LIVE run — the REFINEMENT arm of the Cat 3 briefing check.
 *
 * Paired with live-briefing-cat3.spec.ts, which is the control: identical drive
 * sequence, refinement session SKIPPED. This arm conducts the Problem Refinement
 * interview before generating solutions. One variable differs between the two.
 *
 * WHY A SECOND FILE RATHER THAN A FLAG ON THE FIRST
 * -------------------------------------------------
 * The drive steps below are duplicated from the control ON PURPOSE. The control
 * is a spec that has actually passed against a live pipeline, and re-verifying it
 * after a refactor costs another seven minutes and another round of tokens. A
 * shared helper would be better engineering in the abstract and worse here: the
 * value of this pair is that the control's behaviour is KNOWN, and editing it to
 * extract a helper puts that knowledge back in doubt to save duplication in two
 * files. Revisit if a third arm appears.
 *
 * WHAT "CONDUCTED" MEANS HERE — READ BEFORE TRUSTING THE RESULT
 * -------------------------------------------------------------
 * The interview is answered by clicking the FIRST suggested response each turn.
 * That is a scripted respondent, not a human one. It exercises the real code path
 * (the refinement API, accumulated constraints/exclusions, refinement_result
 * reaching Stage 1) but it does NOT test whether the interview elicits good
 * information from a person — no automated test can. Read any framing improvement
 * as "the mechanism is wired and carries content", not as "the interview works".
 *
 * Run:  npx playwright test --config=playwright.live.config.ts live-briefing-cat3-refined
 */

const SCAN_TIMEOUT = 240_000;
const DA_TIMEOUT = 300_000;
const SF_TIMEOUT = 1_800_000;
/** Interview turns before giving up and letting the session close on its own. */
const MAX_INTERVIEW_TURNS = 14;

const FIRM_NAMES = [
  /\bMcKinsey\b/i, /\bBCG\b/, /\bBoston Consulting\b/i, /\bBain\b/i,
  /\bDeloitte\b/i, /\bAccenture\b/i, /\bKPMG\b/, /\bPwC\b/i, /\bParthenon\b/i,
];

test.describe('Live — Cat 3 briefing, refinement arm', () => {
  test.describe.configure({ mode: 'serial', timeout: 45 * 60_000 });

  test('conduct the refinement interview, then render the briefing', async ({ page }, testInfo) => {
    const consoleErrors: string[] = [];
    page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
    page.on('pageerror', e => consoleErrors.push(`pageerror: ${e.message}`));

    let synthesisRequestId: string | null = null;
    let sfPayload: any = null;
    // Captured so decision_quality.score_run gets its da_result and link 5
    // (sound reasoning) is actually CHECKED rather than degrading to
    // not-checked — the control run omitted this and cannot be scored on it.
    let daPayload: any = null;
    let daRequestId: string | null = null;
    const stagesSeen: string[] = [];
    const refinementTurns: any[] = [];

    page.on('response', async res => {
      const u = res.url();
      try {
        if (u.includes('/workflows/deep-analysis/run') && res.request().method() === 'POST') {
          const j = await res.json();
          daRequestId = j?.data?.request_id ?? j?.request_id ?? null;
        } else if (daRequestId && u.includes(`/workflows/deep-analysis/${daRequestId}/status`)) {
          const j = await res.json();
          if (j?.data?.state === 'completed' && j?.data?.result) daPayload = j.data.result;
        } else if (u.includes('/workflows/deep-analysis/refine') && res.request().method() === 'POST') {
          const j = await res.json();
          const r = j?.data ?? j;
          refinementTurns.push({
            turn: r?.turn_count, topic: r?.current_topic,
            topics_completed: r?.topics_completed,
            ready: r?.ready_for_solutions,
            constraints: r?.constraints, exclusions: r?.exclusions,
          });
        } else if (u.includes('/workflows/solutions/run') && res.request().method() === 'POST') {
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
    // Same preference order as the control, so both arms drive the same KPI.
    const preferred = ['cost of goods', 'cogs', 'raw materials', 'gross margin'];
    let target = 0;
    outer: for (const term of preferred) {
      for (let i = 0; i < cardCount; i++) {
        if (cardText[i].toLowerCase().includes(term)) { target = i; break outer; }
      }
    }
    console.log(`[refined] driving card [${target}]: ${cardText[target].slice(0, 120)}`);
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

    // Resolve the mixed-signal framing choice first — "Start Refinement Session"
    // is gated behind it exactly as "Generate Solutions" is.
    const focusRecovery = page.getByRole('button', { name: /focus on recovery/i });
    const startRefinement = page.getByRole('button', { name: /start refinement session/i });
    const generate = page.getByRole('button', { name: /^generate solutions/i });
    await expect(async () => {
      const [nR, nS, nG] = await Promise.all([
        focusRecovery.count(), startRefinement.count(), generate.count(),
      ]);
      expect(nR + nS + nG).toBeGreaterThan(0);
    }).toPass({ timeout: 120_000, intervals: [1_000] });
    if (await focusRecovery.count()) await focusRecovery.first().click();

    // ── THE VARIABLE UNDER TEST: conduct the interview ────────────────────────
    await startRefinement.waitFor({ state: 'visible', timeout: 60_000 });
    await startRefinement.click();

    const chatInput = page.getByPlaceholder(/type your response/i);
    await chatInput.waitFor({ state: 'visible', timeout: 60_000 });
    console.log('[refined] refinement session opened');
    await page.screenshot({ path: testInfo.outputPath('20-refinement-open.png'), fullPage: true });

    // Answer by clicking the first suggested response until the session closes
    // itself (ready_for_solutions -> onComplete -> the chat unmounts and the
    // persona selector opens). The input disappearing IS the completion signal;
    // polling refinement_result would be reading our own capture back.
    let turns = 0;
    while (turns < MAX_INTERVIEW_TURNS) {
      if (!(await chatInput.count())) break;               // session closed
      // The suggested-response buttons are the only BUTTONS carrying line-clamp-2;
      // the accumulated-refinements strip below reuses that class on divs, which
      // is why this is scoped to `button` rather than the class alone.
      const suggestions = page.locator('button.line-clamp-2');
      const nSug = await suggestions.count();
      if (!nSug) {
        // No suggestions this turn — send a neutral acknowledgement rather than
        // stalling. Deliberately content-free: this harness must not smuggle in
        // domain facts a real principal would have supplied, or the refinement
        // arm would be testing the fixture author's domain knowledge.
        await chatInput.fill('Understood — please continue.');
        await chatInput.press('Enter');
      } else {
        await suggestions.first().click();
      }
      turns++;
      // Each turn is a real LLM call; wait for the spinner to clear rather than
      // racing the next click into a disabled input.
      await page.waitForTimeout(1_500);
      await expect(async () => {
        const busy = await page.locator('.animate-spin').count();
        expect(busy).toBe(0);
      }).toPass({ timeout: 120_000, intervals: [1_000] });
    }
    console.log(`[refined] interview turns taken: ${turns}`);
    await page.screenshot({ path: testInfo.outputPath('21-refinement-done.png'), fullPage: true });

    fs.mkdirSync(testInfo.outputDir, { recursive: true });
    fs.writeFileSync(
      path.join(testInfo.outputDir, 'refinement-turns.json'),
      JSON.stringify(refinementTurns, null, 2), 'utf-8',
    );

    // The interview MUST have actually happened — a zero-turn "session" that
    // fell straight through would make this arm a silent duplicate of the control.
    expect(refinementTurns.length,
      'no /deep-analysis/refine calls were made — the interview did not run',
    ).toBeGreaterThan(0);

    // ── SF ────────────────────────────────────────────────────────────────────
    // onRefinementComplete opens the persona selector directly; onCancel does too.
    // Either way the next control is "Generate Solutions" inside the selector.
    await generate.first().waitFor({ state: 'visible', timeout: 120_000 });
    if (await page.getByRole('heading', { name: /assemble council/i }).count() === 0) {
      // Session ended without auto-advancing (turn cap hit) — open the selector.
      await generate.first().click();
      await page.getByRole('heading', { name: /assemble council/i })
        .waitFor({ state: 'visible', timeout: 60_000 });
    }
    await generate.first().click();
    await page.waitForURL('**/debate/**', { timeout: 60_000 });

    await page.waitForRequest(r => r.url().includes('/workflows/solutions/run'), { timeout: 120_000 });
    console.log('[refined] solutions/run dispatched — waiting on synthesis');
    await expect.poll(() => sfPayload !== null, { timeout: SF_TIMEOUT, intervals: [10_000] }).toBe(true);
    await page.waitForTimeout(5_000);

    fs.writeFileSync(
      path.join(testInfo.outputDir, 'sf-synthesis-payload.json'),
      JSON.stringify(sfPayload, null, 2), 'utf-8',
    );
    fs.writeFileSync(
      path.join(testInfo.outputDir, 'da-payload.json'),
      JSON.stringify(daPayload, null, 2), 'utf-8',
    );
    console.log(`[refined] stages: ${stagesSeen.join(' -> ')}`);
    console.log(`[refined] DA payload captured: ${daPayload !== null}`);

    // ── Briefing ──────────────────────────────────────────────────────────────
    const viewBriefing = page.getByRole('button', { name: /view executive briefing/i });
    await viewBriefing.waitFor({ state: 'visible', timeout: 120_000 });
    await viewBriefing.click();
    await page.waitForURL('**/briefing/**', { timeout: 60_000 });
    await page.waitForTimeout(2_000);
    await page.screenshot({ path: testInfo.outputPath('22-briefing-top.png') });
    await page.screenshot({ path: testInfo.outputPath('23-briefing-full.png'), fullPage: true });

    await expect(
      page.getByRole('heading', { name: /briefing not generated yet/i }),
      'briefing page fell back to the not-generated empty state',
    ).toHaveCount(0);

    // Same nesting as the control: the status result wraps the SF body.
    const sol = sfPayload?.solutions ?? sfPayload;
    expect(sol, 'SF result had neither a solutions wrapper nor a usable body').toBeTruthy();

    const askInPayload = Boolean(sol?.decision_ask?.decision_text);
    await expect(page.getByTestId('decision-ask-block')).toBeVisible();
    const askTextCount = await page.getByTestId('decision-ask-text').count();
    const askAbsentCount = await page.getByTestId('decision-ask-absent').count();
    expect(askTextCount + askAbsentCount).toBe(1);
    expect(askTextCount === 1).toBe(askInPayload);

    const askText = askTextCount ? (await page.getByTestId('decision-ask-text').innerText()).trim() : null;
    if (askText) {
      const words = askText.split(/\s+/).filter(Boolean).length;
      console.log(`[refined] decision ask (${words} words): ${askText}`);
      expect(words).toBeLessThanOrEqual(25);
    }

    const actionsInPayload: any[] = sol?.immediate_actions ?? [];
    const renderedActions = await page.getByTestId('immediate-action').count();
    console.log(`[refined] immediate actions — payload ${actionsInPayload.length}, rendered ${renderedActions}`);
    if (actionsInPayload.length) expect(renderedActions).toBe(actionsInPayload.length);

    const optionsInPayload: any[] = sol?.options_ranked ?? [];
    const optionsWithAssumptions = optionsInPayload.slice(0, 3)
      .filter(o => Array.isArray(o?.key_assumptions) && o.key_assumptions.length > 0).length;
    const renderedPanels = await page.getByTestId('assumptions-panel').count();
    console.log(`[refined] assumptions panels — carrying ${optionsWithAssumptions}, rendered ${renderedPanels}`);
    expect(renderedPanels).toBe(optionsWithAssumptions);

    await expect(page.getByTestId('status-quo-column')).toBeVisible();

    const sideEffectOptions = optionsInPayload.slice(0, 3)
      .filter(o => Array.isArray(o?.flagged_side_effects) && o.flagged_side_effects.length > 0).length;
    const renderedChips = await page.getByTestId('side-effects-chip').count();
    console.log(`[refined] side effects — flagged ${sideEffectOptions}, chips ${renderedChips}`);
    expect(renderedChips).toBe(sideEffectOptions);

    const pageText = await page.locator('body').innerText();
    const leaked = FIRM_NAMES.filter(re => re.test(pageText)).map(re => re.source);
    expect(leaked, `firm names on the briefing: ${leaked.join(', ')}`).toEqual([]);

    const realErrors = consoleErrors.filter(e =>
      !/favicon|net::ERR|Failed to load resource|429|404/i.test(e));
    expect(realErrors, `console errors: ${realErrors.slice(0, 3).join(' | ')}`).toEqual([]);

    const summary = {
      arm: 'refinement',
      interview: {
        turns_taken: turns,
        refine_calls: refinementTurns.length,
        topics_completed: refinementTurns.at(-1)?.topics_completed ?? [],
        ready_for_solutions: refinementTurns.at(-1)?.ready ?? null,
        constraints_captured: refinementTurns.at(-1)?.constraints ?? [],
        exclusions_captured: refinementTurns.at(-1)?.exclusions ?? [],
      },
      decision_ask: { in_payload: askInPayload, rendered: askTextCount === 1, text: askText },
      immediate_actions: { in_payload: actionsInPayload.length, rendered: renderedActions },
      assumptions: { options_carrying: optionsWithAssumptions, panels_rendered: renderedPanels },
      side_effects: { options_flagged: sideEffectOptions, chips_rendered: renderedChips },
      firm_names_leaked: leaked,
      da_payload_captured: daPayload !== null,
      stages: stagesSeen,
    };
    fs.writeFileSync(
      path.join(testInfo.outputDir, 'cat3-summary.json'),
      JSON.stringify(summary, null, 2), 'utf-8',
    );
    console.log('[refined] summary:', JSON.stringify(summary, null, 2));
  });
});
