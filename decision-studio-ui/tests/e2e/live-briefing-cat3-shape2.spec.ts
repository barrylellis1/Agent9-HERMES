import { test, expect } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * LIVE run — the SECOND PROBLEM SHAPE.
 *
 * Every run scored this session, and all 13 tools/ab_harness/scope_arm_*.json
 * corpus runs before it, are the same recurring situation: gross_margin_pct,
 * one dominant segment (Synthetic Blend), one confirmed external mechanism, no
 * healthy segment anywhere. problem_framing_design.md §9's own caveat is that
 * "frame fails 11 of 13" stays consistent with "this problem has one right
 * frame" until a second shape is scored. This is that run.
 *
 * TARGET: Net Revenue — "16.7% below plan." Deliberately NOT another
 * year-over-year decline: plan-variance is a different comparator mechanism
 * entirely (budget vs. prior-period), a different code path than every prior
 * run exercised, with an unknown concentration pattern — Revenue, not Margin,
 * so likely driven by a different set of segments altogether.
 *
 * ONE VARIABLE CHANGED, deliberately: the KPI/card. Council selection is left
 * at the MBB default (unchanged) so this run stays comparable to the 13-run
 * corpus, which also used MBB throughout — isolating problem shape as the
 * thing under test, not conflating it with a roster change.
 *
 * WHAT THIS ESTABLISHES, AND WHAT IT DOESN'T
 * -------------------------------------------
 * One run. It answers "is the frame-examination gap specific to this one
 * recurring margin situation, or does it show up on a structurally different
 * problem too" — informative either way, but n=1 on THIS shape, same
 * discipline as every other single run this session. It does not, by itself,
 * establish a general pattern across problem shapes.
 *
 * Captures da-payload.json specifically to compute (not assume) concentration
 * signals directly from kt_is_is_not — where_is/where_is_not counts and
 * relative deltas — the same way the VA control-group finding was established
 * on the first shape, since concentration/has_control_group are DA-internal
 * routing signals never persisted into the response (confirmed earlier this
 * session).
 *
 * Run:  npx playwright test --config=playwright.live.config.ts live-briefing-cat3-shape2
 */

const SCAN_TIMEOUT = 240_000;
const DA_TIMEOUT = 300_000;
const SF_TIMEOUT = 1_800_000;

const FIRM_NAMES = [
  /\bMcKinsey\b/i, /\bBCG\b/, /\bBoston Consulting\b/i, /\bBain\b/i,
  /\bDeloitte\b/i, /\bAccenture\b/i, /\bKPMG\b/, /\bPwC\b/i, /\bParthenon\b/i,
];

test.describe('Live — second problem shape (Net Revenue plan-variance)', () => {
  test.describe.configure({ mode: 'serial', timeout: 40 * 60_000 });

  test('drive Net Revenue and capture what a genuinely different shape produces', async ({ page }, testInfo) => {
    const consoleErrors: string[] = [];
    page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
    page.on('pageerror', e => consoleErrors.push(`pageerror: ${e.message}`));

    let synthesisRequestId: string | null = null;
    let sfPayload: any = null;
    let daPayload: any = null;
    let daRequestId: string | null = null;
    const stagesSeen: string[] = [];
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
    console.log(`[shape2] ${cardCount} card(s) on the grid this scan:`);
    cardText.forEach((t, i) => console.log(`  [${i}] ${t.slice(0, 90)}`));

    // THE variable under test: Net Revenue, not the margin card every prior
    // run targeted. "revenue" alone would also match Product/Service/E-Commerce/
    // B2B Revenue cards, so match the more specific "net revenue" first.
    const preferred = ['net revenue'];
    let target = -1;
    outer: for (const term of preferred) {
      for (let i = 0; i < cardCount; i++) {
        if (cardText[i].toLowerCase().includes(term)) { target = i; break outer; }
      }
    }
    expect(target, 'no Net Revenue card found on this scan').toBeGreaterThanOrEqual(0);
    console.log(`[shape2] driving card [${target}]: ${cardText[target].slice(0, 140)}`);
    await cards.nth(target).click();

    // ── DA ────────────────────────────────────────────────────────────────────
    const daTimedOut = page.getByText(/workflow timed out/i);
    const daLocked = page.getByText(/run deep analysis to unlock/i);
    await expect(async () => {
      if (await daTimedOut.count()) throw new Error('DA reported "Workflow timed out" in the UI');
      await expect(daLocked).toHaveCount(0);
    }).toPass({ timeout: DA_TIMEOUT, intervals: [2_000] });

    await page.screenshot({ path: testInfo.outputPath('02-deep-analysis.png'), fullPage: true });

    const openActionCenter = page.getByRole('button', { name: /open action center/i });
    if (await openActionCenter.count()) await openActionCenter.first().click();

    // ── SF: council left at the MBB default deliberately — see file header ───
    const focusRecovery = page.getByRole('button', { name: /focus on recovery/i });
    const focusOpportunity = page.getByRole('button', { name: /focus on opportunity/i });
    const generate = page.getByRole('button', { name: /^generate solutions/i });
    await expect(async () => {
      const [nR, nO, nG] = await Promise.all([focusRecovery.count(), focusOpportunity.count(), generate.count()]);
      expect(nR + nO + nG).toBeGreaterThan(0);
    }).toPass({ timeout: 120_000, intervals: [1_000] });

    // A plan-variance shortfall is a "problem" framing, not "opportunity" — but
    // handle both branches rather than assume, matching the robustness of the
    // existing control spec. Prefer Recovery if a mixed verdict offers a choice.
    if (await focusRecovery.count()) {
      console.log('[shape2] DA verdict = MIXED — selecting Recovery framing');
      await focusRecovery.first().click();
    } else if (await focusOpportunity.count()) {
      console.log('[shape2] DA verdict = MIXED — selecting Opportunity framing (unexpected for a below-plan shortfall)');
      await focusOpportunity.first().click();
    } else {
      console.log('[shape2] DA verdict = single framing — no Recovery/Opportunity choice offered');
    }

    await generate.waitFor({ state: 'visible', timeout: 60_000 });
    await generate.click();
    await page.getByRole('heading', { name: /assemble council/i })
      .waitFor({ state: 'visible', timeout: 60_000 });
    // No preset click here — MBB is the default, left untouched.
    await generate.click();
    await page.waitForURL('**/debate/**', { timeout: 60_000 });

    await page.waitForRequest(r => r.url().includes('/workflows/solutions/run'), { timeout: 120_000 });
    console.log('[shape2] solutions/run dispatched — waiting on synthesis');
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
    console.log(`[shape2] stages: ${stagesSeen.join(' -> ')}`);
    console.log(`[shape2] dispatched consulting_personas: ${JSON.stringify(dispatchedPersonas)}`);

    // ── Shape signals, computed directly rather than read from an absent field ─
    // concentration/has_control_group are DA-internal routing signals, never
    // persisted into the response (confirmed earlier this session). Compute the
    // same underlying facts from kt_is_is_not directly, exactly as the VA
    // control-group finding on the first shape was established.
    const ex = daPayload?.execution ?? {};
    const kt = ex.kt_is_is_not ?? {};
    const whereIs: any[] = kt.where_is ?? [];
    const whereIsNot: any[] = kt.where_is_not ?? [];
    const benchmarkSegs: any[] = kt.benchmark_segments ?? [];
    const deltas = whereIs.map((r: any) => Math.abs(r?.delta ?? 0)).filter((d: number) => d > 0).sort((a, b) => b - a);
    const dominanceRatio = deltas.length >= 2 ? deltas[0] / deltas[1] : (deltas.length === 1 ? Infinity : null);
    const shapeSignals = {
      alert_type: ex.alert_type ?? null,
      analysis_mode: ex.analysis_mode ?? null,
      comparator: ex.comparator ?? null,
      where_is_count: whereIs.length,
      where_is_not_count: whereIsNot.length,
      benchmark_segments_count: benchmarkSegs.length,
      top_two_deltas: deltas.slice(0, 2),
      dominance_ratio: dominanceRatio,
      // DA's own R2/R2' rule (a9_deep_analysis_agent.py) treats >= 2.0 as
      // "concentrated." Same threshold applied here to the same underlying data.
      concentration_inferred: dominanceRatio === null ? 'unknown'
        : dominanceRatio >= 2.0 ? 'concentrated' : 'distributed',
      has_control_group_inferred: whereIsNot.length > 0,
    };
    console.log('[shape2] shape signals:', JSON.stringify(shapeSignals, null, 2));

    // ── Frame content, for the adjudication read ───────────────────────────────
    const sol = sfPayload?.solutions ?? sfPayload;
    const pr = sol?.problem_reframe ?? {};
    console.log('[shape2] SITUATION:   ', String(pr.situation ?? '').slice(0, 300));
    console.log('[shape2] COMPLICATION:', String(pr.complication ?? '').slice(0, 300));
    console.log('[shape2] QUESTION:    ', String(pr.question ?? '').slice(0, 300));
    const optionsInPayload: any[] = sol?.options_ranked ?? [];
    console.log(`[shape2] ${optionsInPayload.length} option(s):`);
    optionsInPayload.forEach((o: any) => console.log(`  - ${String(o?.title ?? '').slice(0, 100)}`));

    // ── Into the briefing — same Cat 3 checks, free regression coverage on a
    //    shape Cat 3 has never been exercised against either ──────────────────
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
    expect(sol, 'SF result had neither a solutions wrapper nor a usable body').toBeTruthy();

    const askInPayload = Boolean(sol?.decision_ask?.decision_text);
    const askTextCount = await page.getByTestId('decision-ask-text').count();
    const askAbsentCount = await page.getByTestId('decision-ask-absent').count();
    expect(askTextCount + askAbsentCount).toBe(1);
    expect(askTextCount === 1).toBe(askInPayload);

    const actionsInPayload: any[] = sol?.immediate_actions ?? [];
    const renderedActions = await page.getByTestId('immediate-action').count();
    if (actionsInPayload.length) expect(renderedActions).toBe(actionsInPayload.length);

    const pageText = await page.locator('body').innerText();
    const leaked = FIRM_NAMES.filter(re => re.test(pageText)).map(re => re.source);
    expect(leaked, `firm names on the briefing: ${leaked.join(', ')}`).toEqual([]);

    const realErrors = consoleErrors.filter(e =>
      !/favicon|net::ERR|Failed to load resource|429|404/i.test(e));
    expect(realErrors, `console errors: ${realErrors.slice(0, 3).join(' | ')}`).toEqual([]);

    const summary = {
      shape: 'net_revenue_plan_variance',
      shape_signals: shapeSignals,
      problem_reframe: pr,
      options: optionsInPayload.map((o: any) => o?.title),
      dispatched_personas: dispatchedPersonas,
      decision_ask: { in_payload: askInPayload, rendered: askTextCount === 1 },
      immediate_actions: { in_payload: actionsInPayload.length, rendered: renderedActions },
      firm_names_leaked: leaked,
      stages: stagesSeen,
    };
    fs.writeFileSync(
      path.join(testInfo.outputDir, 'cat3-summary.json'),
      JSON.stringify(summary, null, 2), 'utf-8',
    );
    console.log('[shape2] summary:', JSON.stringify(summary, null, 2));
  });
});
