import { test, expect, Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * LIVE run — deliberately unmocked, unlike the rest of tests/e2e.
 *
 * Every other spec here mocks /workflows/** to assert rendering. This one drives
 * the real SA -> DA -> SF pipeline so we can observe what the theory layer
 * actually produces, and captures screenshots + the SF payload as artifacts.
 *
 * Consequences of being live, all intentional:
 *  - It spends real LLM tokens (3 parallel Stage 1 calls + synthesis + critic).
 *  - It is slow. Timeouts below are minutes, not the Playwright 30s default.
 *  - It is NOT hermetic and must never join the CI suite. Run it by name:
 *      npx playwright test live-causal-grounding --headed
 *
 * Requires SF_ENABLE_CAUSAL_GROUNDING=true and SF_ENABLE_CRITIC_PASS=true on the
 * server being driven, plus the corrected lubricants seed (base_oil_cost pointing
 * at 'Raw Materials'; before that fix the confirmed causal edge had no numeric
 * substrate and could not fire).
 */

const SCAN_TIMEOUT = 240_000;   // SA scans 15 KPIs against BigQuery
const DA_TIMEOUT = 300_000;     // Deep Analysis: dimensional Is/Is-Not + change points
// Post-Stage-H the debate is stage1_only (~15s Haiku) + ONE synthesis call
// (critic + moderator + generation on Sonnet, streaming at max_tokens=32000 —
// measured ~3-4.5 min, unbounded above by anything we control). 1800s is
// deliberate headroom over one long generation, not a budget for the retired
// 4-stage flow.
const SF_TIMEOUT = 1_800_000;

test.describe('Live — causal grounding end to end', () => {
  // Must exceed SF_TIMEOUT plus SA + DA, or the describe-level cap fires first and
  // reports a timeout that looks like a pipeline stall but is pure bookkeeping.
  test.describe.configure({ mode: 'serial', timeout: 40 * 60_000 });

  test('drive SA -> DA -> SF and capture what the theory layer produced', async ({ page }, testInfo) => {
    const consoleErrors: string[] = [];
    page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });

    // Capture the SF response off the wire. Reading the rendered DOM tells us what
    // a human sees; the payload tells us what actually came back — and the two
    // disagreeing is itself a finding worth having.
    //
    // CRITICAL: the debate issues TWO sequential POSTs to the SAME endpoint
    // /workflows/solutions/run, distinguished only by preferences.debate_stage:
    //   stage1_only -> synthesis
    // (Stage H collapsed the former 4-stage flow; `hypothesis`/`cross_review`
    // were audited as identical requests to synthesis and dropped.) Capturing
    // the first `completed` status therefore captures stage1_only — a ~5s Haiku
    // call that returns firm hypotheses and none of the synthesis output. A
    // previous run scored exactly that and reported the provenance signals as
    // absent, when in truth the document being scored had not been written yet.
    //
    // So: match the synthesis POST by its body, remember ITS request_id, and read
    // only that id's status. Anything else silently grades the wrong document.
    let synthesisRequestId: string | null = null;
    let sfPayload: any = null;
    const stagesSeen: string[] = [];

    page.on('response', async res => {
      const u = res.url();
      try {
        if (u.includes('/workflows/solutions/run')) {
          const post = res.request().postData() || '';
          const stage = (post.match(/"debate_stage"\s*:\s*"([a-z0-9_]+)"/i) || [])[1] ?? 'unknown';
          const rid = (await res.json())?.data?.request_id ?? null;
          stagesSeen.push(stage);
          if (stage === 'synthesis' && rid) synthesisRequestId = rid;
          console.log(`[live] stage dispatched: ${stage} (request_id=${rid})`);
        } else if (synthesisRequestId && u.includes(`/workflows/solutions/${synthesisRequestId}/status`)) {
          const j = await res.json();
          if (j?.data?.state === 'completed' && j?.data?.result) sfPayload = j.data.result;
          if (j?.data?.state === 'failed') console.log(`[live] synthesis FAILED: ${j?.data?.error}`);
        }
      } catch { /* non-JSON polls are expected */ }
    });

    // ── Login (real, no mocks) ────────────────────────────────────────────────
    await page.goto('/login?mode=demo');
    await page.waitForSelector('[data-testid="principal-card-cfo_001"]', { timeout: 30_000 });
    await page.locator('[data-testid="principal-card-cfo_001"]').click();
    await page.locator('[data-testid="demo-enter-btn"]').click();
    await page.waitForURL('**/dashboard', { timeout: 30_000 });

    // ── SA scan ───────────────────────────────────────────────────────────────
    await page.waitForSelector('[data-testid="situation-grid"]', { timeout: SCAN_TIMEOUT });
    await page.screenshot({ path: testInfo.outputPath('01-dashboard.png'), fullPage: true });

    // Record every card the scan produced. The pre-fix dataset could only ever
    // yield a gross-margin opportunity, because cost KPIs were arithmetically
    // incapable of breaching a red threshold — so the card inventory is the
    // first real evidence that the sign fix changed behaviour.
    const cards = page.locator('[data-testid^="situation-card-"]');
    const cardCount = await cards.count();
    const cardText: string[] = [];
    for (let i = 0; i < cardCount; i++) {
      cardText.push(((await cards.nth(i).innerText()) || '').replace(/\s+/g, ' ').trim());
    }
    await testInfo.attach('situation-cards.json', {
      body: JSON.stringify({ cardCount, cardText }, null, 2),
      contentType: 'application/json',
    });
    console.log(`\n[live] ${cardCount} situation card(s):`);
    cardText.forEach((t, i) => console.log(`  [${i}] ${t.slice(0, 180)}`));

    expect(cardCount, 'SA produced no situation cards').toBeGreaterThan(0);

    // ── Pick the cost/margin card the causal edge is about ────────────────────
    // Prefer a COGS or raw-materials card: base_oil_cost -> cogs is the confirmed,
    // converging edge, and both sides now breach. Fall back to gross margin.
    const preferred = ['cost of goods', 'cogs', 'raw materials', 'gross margin'];
    let target = 0;
    outer: for (const term of preferred) {
      for (let i = 0; i < cardCount; i++) {
        if (cardText[i].toLowerCase().includes(term)) { target = i; break outer; }
      }
    }
    console.log(`[live] driving card [${target}]: ${cardText[target].slice(0, 120)}`);
    await cards.nth(target).click();

    // ── Deep Analysis ─────────────────────────────────────────────────────────
    // Clicking the card opens DeepFocusView and DA runs on its own. Do NOT poll
    // body text for /analysis/ -- that word is in the page heading ("Gross Margin %
    // Mixed Analysis"), so it matches instantly and reports success before DA has
    // done anything. Wait for a control that only exists once DA has produced
    // results: the dimensional breakdown accordion.
    // The DA-complete signal must hold across alert variants. "Variance Breakdown"
    // does NOT: it renders for some analysis types and not others, so keying on it
    // timed out for 5 minutes on a run where DA had actually finished in ~50s
    // (confirmed by driving /workflows/deep-analysis directly).
    //
    // Third attempt at this signal. The first two both keyed on things that render
    // regardless of whether DA produced anything:
    //   - body text /analysis/      -> matches the level-1 page TITLE, passes instantly
    //   - level-2 "Analysis" heading -> the SECTION header, present even on failure
    // The level-2 heading was observed sitting directly above the text "Workflow
    // timed out", having reported DA complete on a run where it had not been.
    //
    // Assert on the Action Center's LOCKED state clearing instead. That paragraph is
    // rendered exactly when downstream controls are unavailable, so its removal is
    // the same condition the user is waiting on, and it holds across DA variants
    // (mixed vs single framing) because it is about gating, not content.
    const daLocked = page.getByText(/run deep analysis to unlock/i);

    // Fail immediately and legibly on the known failure mode rather than letting it
    // surface 60s later as a confusing "Generate Solutions not visible".
    const daTimedOut = page.getByText(/workflow timed out/i);
    await expect(async () => {
      if (await daTimedOut.count()) {
        throw new Error(
          'DA reported "Workflow timed out" in the UI. The backend usually COMPLETED — ' +
          'check logs/backend.log for execute_deep_analysis / analyze_market durations ' +
          'and compare against the poll budget in src/api/client.ts runDeepAnalysis.'
        );
      }
      await expect(daLocked).toHaveCount(0);
    }).toPass({ timeout: DA_TIMEOUT, intervals: [2_000] });

    await page.screenshot({ path: testInfo.outputPath('02-deep-analysis.png'), fullPage: true });

    // The Action Center holds every downstream control and may render collapsed.
    const openActionCenter = page.getByRole('button', { name: /open action center/i });
    if (await openActionCenter.count()) {
      await openActionCenter.first().click();
    }

    // ── Solution Finder ───────────────────────────────────────────────────────
    // The real control is "Generate Solutions →" in the Action Center. Previously
    // this was guarded by `if (await count())`, so a button that had not rendered
    // yet made the click a silent no-op and the run then waited out the full SF
    // timeout for a payload nothing had requested. waitFor() makes absence fail
    // loudly and immediately instead.
    // Reaching SF takes FOUR interactions, none of which dispatch on their own.
    // Discovered by driving it, because each step looks like the final one:
    //   1. "Focus on Recovery"      -> sets resolvedAnalysisMode, unlocks step 2
    //   2. "Generate Solutions ->"  -> opens the persona selector (setShowPersonaSelector)
    //   3. "Generate Solutions ->"  -> navigates to /debate/{id}
    //   4. the /debate route is what actually calls /workflows/solutions/run
    //
    // Step 1 is a framing choice, not a trigger. A "Mixed" DA verdict offers
    // Recovery / Opportunity / Let-Agent9-Decide. Recovery is the right arm here:
    // margin is down 5.08pp, the obvious lever is repricing, and repricing anchor
    // accounts mid-quarter is exactly what the seeded price-lock constraint
    // forbids -- so it is the sharpest test of whether that constraint binds.
    // Step 1 exists ONLY when DA returns a "mixed" verdict. When DA lands on a
    // single framing (e.g. a plan-variance alert), the Recovery/Opportunity cards
    // are never rendered and "Generate Solutions" is directly available. Requiring
    // the cards unconditionally fails on a perfectly healthy run, so this is
    // conditional — but it logs which branch it took, because "mixed vs not" is a
    // real difference in what the pipeline was asked to do.
    const focusRecovery = page.getByRole('button', { name: /focus on recovery/i });

    // Anchored, because the framing cards are themselves buttons whose accessible
    // names are "Focus on Recovery Generate..." and "Focus on Opportunity
    // Generate...". An unanchored /generate solutions/i matches BOTH of them and
    // dies on strict mode. Only the real trigger STARTS with "Generate Solutions".
    const generate = page.getByRole('button', { name: /^generate solutions/i });

    // The Action Center unlocking and its contents rendering are NOT the same
    // moment. count() resolves immediately and never waits, so checking it the
    // instant the lock cleared reported zero framing cards on a run that had two —
    // logging "single framing" and then walking into the strict-mode violation
    // above. Wait for the panel to actually settle into one shape or the other
    // before branching.
    await expect(async () => {
      const [nRecovery, nGenerate] = await Promise.all([
        focusRecovery.count(),
        generate.count(),
      ]);
      expect(nRecovery + nGenerate).toBeGreaterThan(0);
    }).toPass({ timeout: 120_000, intervals: [1_000] });

    // Step 1 is a framing choice, not a trigger, and exists only on a "mixed" DA
    // verdict. Recovery is the right arm here: margin is down 5.24pp, the obvious
    // lever is repricing, and repricing anchor accounts mid-quarter is exactly what
    // the seeded price-lock constraint forbids — the sharpest test of whether that
    // constraint actually binds.
    if (await focusRecovery.count()) {
      console.log('[live] DA verdict = MIXED — selecting Recovery framing');
      await focusRecovery.first().click();
    } else {
      console.log('[live] DA verdict = single framing — no Recovery/Opportunity choice offered');
    }

    // Step 2: opens the persona selector, which REPLACES the Action Center panel
    // rather than stacking over it. So the "Generate Solutions ->" count stays at
    // 1 throughout -- it is simply a different button afterwards. Waiting for the
    // count to exceed 1 times out forever; wait for the selector's own heading.
    await generate.waitFor({ state: 'visible', timeout: 60_000 });
    await generate.click();

    // Step 3: "Assemble Council" only exists once the selector has swapped in, so
    // it is the signal that the next click lands on the selector's button and not
    // a re-click of the panel button that was there a moment ago.
    await page.getByRole('heading', { name: /assemble council/i })
      .waitFor({ state: 'visible', timeout: 60_000 });
    // Council defaults to MBB (mckinsey/bcg/bain) when no hybrid selection is made,
    // which matches the council in the production briefing -- left at default.
    await generate.click();

    // Step 4: the debate route is what dispatches. Assert the navigation so a
    // click that failed to advance is distinguishable from a slow pipeline.
    await page.waitForURL('**/debate/**', { timeout: 60_000 });
    console.log('[live] navigated to /debate — SF dispatch expected from this route');
    await page.screenshot({ path: testInfo.outputPath('03-debate-start.png'), fullPage: true });

    await page.waitForRequest(
      r => r.url().includes('/workflows/solutions/run'),
      { timeout: 120_000 },
    );
    console.log('[live] solutions/run dispatched — waiting on synthesis + critic');

    await expect
      .poll(() => sfPayload !== null, { timeout: SF_TIMEOUT, intervals: [10_000] })
      .toBe(true);
    await page.waitForTimeout(5_000);
    await page.screenshot({ path: testInfo.outputPath('04-solutions.png'), fullPage: true });

    // Write to disk, not just testInfo.attach(). Attachments live only in the HTML
    // report, so running with `--reporter=list` (which overrides the config's html
    // reporter) discards them silently — the screenshots survived only because they
    // were written to explicit paths. Do both: the file is what actually persists.
    const payloadPath = path.join(testInfo.outputDir, 'sf-synthesis-payload.json');
    fs.mkdirSync(testInfo.outputDir, { recursive: true });
    fs.writeFileSync(payloadPath, JSON.stringify(sfPayload, null, 2), 'utf-8');
    console.log(`[live] stages seen: ${stagesSeen.join(' -> ')}`);
    console.log(`[live] synthesis payload written: ${payloadPath}`);

    // Assert the dispatch shape we believe we measured. The stage list is the
    // only honest evidence of which pipeline actually ran — a stale dev server
    // from before the Stage H collapse would still fire the dead 4-stage flow
    // and burn two extra mega-calls, which this catches immediately.
    const expectedStages = ['stage1_only', 'synthesis'];
    if (JSON.stringify(stagesSeen) !== JSON.stringify(expectedStages)) {
      throw new Error(
        `dispatch shape mismatch: saw [${stagesSeen.join(' -> ')}], expected ` +
        `[${expectedStages.join(' -> ')}] — a stale frontend build or a reintroduced stage`
      );
    }
    await testInfo.attach('debate-stages.json', {
      body: JSON.stringify({ stagesSeen }, null, 2),
      contentType: 'application/json',
    });
    await testInfo.attach('sf-payload.json', {
      body: JSON.stringify(sfPayload, null, 2),
      contentType: 'application/json',
    });

    // ── Score the grounding signals against the A/B baseline ──────────────────
    // Arm A (grounding off) scored 0 on every term below. Base oil is deliberately
    // EXCLUDED as a signal: Market Analysis supplies base-oil context in both arms,
    // so counting it would flatter the result.
    const blob = JSON.stringify(sfPayload).toLowerCase();
    const signals: Record<string, number> = {};
    for (const term of ['price-lock', 'price lock', 'anchor account', 'contractual',
                        'non-anchor', 'non-price-locked', 'unconfirmed', 'template']) {
      signals[term] = (blob.match(new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')) || []).length;
    }
    console.log('\n[live] grounding signals in SF payload:');
    Object.entries(signals).forEach(([k, v]) => console.log(`  ${k.padEnd(20)} ${v}`));

    // Impact scope + magnitude. Live runs produced 18.5-28.3 "percentage points"
    // of Gross Margin % against a KPI at 31.08 with a 5.08pp annual decline --
    // segment magnitudes wearing the enterprise KPI's name, which VA registration
    // reads verbatim into impact bounds. scope makes the two distinguishable;
    // print it beside the numbers so an implausible ENTERPRISE range is obvious.
    const opts = (sfPayload?.solutions?.options_ranked ?? []) as any[];
    console.log('\n[live] impact estimates (scope / range / metric):');
    for (const o of opts) {
      const ie = o?.impact_estimate ?? {};
      const rr = ie.recovery_range ?? {};
      const label = ie.scope_label ? ` [${ie.scope_label}]` : '';
      console.log(
        `  ${String(o?.id).padEnd(8)} scope=${String(ie.scope ?? 'UNSTATED').padEnd(10)}${label}` +
        ` ${rr.low} to ${rr.high} ${ie.unit ?? ''} of "${ie.metric ?? ''}"`
      );
    }
    const scopes = opts.map(o => o?.impact_estimate?.scope ?? null);
    console.log(`[live] scope stated on ${scopes.filter(Boolean).length}/${opts.length} options`);
    await testInfo.attach('impact-scopes.json', {
      body: JSON.stringify(opts.map(o => ({ id: o?.id, impact_estimate: o?.impact_estimate })), null, 2),
      contentType: 'application/json',
    });

    // PM-6: token-budget utilization. The ledger rows carry their own max_tokens
    // (self-describing — this check must not need to know the backend config).
    // >=90% means the next verbose run truncates into the heuristic-stub
    // fallback, which reports status="success" and is invisible without this.
    // The moderator arm's FIRST live run hit 94.7% of a 32000 budget; the
    // budget was raised, and this assertion exists so drift back toward the
    // ceiling fails a run instead of waiting for a truncation to be noticed.
    const auditEvents = (sfPayload?.solutions?.audit_log ?? sfPayload?.audit_log ?? []) as any[];
    const tokenUsage = auditEvents.find(e => e?.event === 'token_usage');
    if (tokenUsage) {
      for (const row of tokenUsage.by_call ?? []) {
        if (row?.max_tokens && row?.output_tokens != null) {
          const pct = (100 * row.output_tokens) / row.max_tokens;
          console.log(`[live] ${row.call} output: ${row.output_tokens}/${row.max_tokens} tokens (${pct.toFixed(1)}% of budget)`);
          if (pct >= 90) {
            throw new Error(
              `PM-6: ${row.call} used ${pct.toFixed(1)}% of its ${row.max_tokens}-token budget — ` +
              `raise the budget or shrink the output before a verbose run silently truncates`
            );
          }
        }
      }
    } else {
      console.log('[live] token_usage event absent from payload — utilization unchecked');
    }
    await testInfo.attach('grounding-signals.json', {
      body: JSON.stringify(signals, null, 2),
      contentType: 'application/json',
    });

    // ── Executive Briefing render ─────────────────────────────────────────────
    // No test had EVER rendered this page. The Stage H moderator-verdicts section
    // was written, shipped, and never executed once — the harness stopped at the
    // debate page, so a component that throws on the customer-facing surface
    // would have gone unnoticed. Costs nothing extra: the LLM work is already done.
    // Still on /debate/{situationId} at this point — take the id from the URL
    // rather than threading it down from the card click.
    const situationIdFromUrl = (page.url().match(/\/debate\/([^/?#]+)/) || [])[1];
    const briefingLink = page.getByRole('link', { name: /briefing|executive/i })
      .or(page.getByRole('button', { name: /briefing|executive/i }));
    if (await briefingLink.count()) {
      await briefingLink.first().click();
    } else if (situationIdFromUrl) {
      await page.goto(`/briefing/${situationIdFromUrl}`);
    } else {
      throw new Error(`cannot reach the briefing: no link found and no situation id in ${page.url()}`);
    }
    // Assert a VISIBLE, on-screen control. A broad getByText().first() latched
    // onto a hidden print-stylesheet element ("Situation & Context", 9px, print
    // only) and waited out 60s for it to become visible, failing a run whose
    // pipeline had actually succeeded. The accordion headers are real buttons
    // and are always on screen.
    await page.getByRole('button', { name: /strategic options/i })
      .waitFor({ state: 'visible', timeout: 60_000 });
    await page.screenshot({ path: testInfo.outputPath('05-briefing.png'), fullPage: true });

    const moderatorSection = page.getByText(/moderator verdicts/i);
    const renderedGrades = await moderatorSection.count();
    console.log(`[live] briefing rendered; moderator verdicts section present: ${renderedGrades > 0}`);
    if (sfPayload?.solutions?.moderator_grades && !renderedGrades) {
      throw new Error('payload carries moderator_grades but the briefing renders no verdicts section');
    }

    if (consoleErrors.length) {
      await testInfo.attach('console-errors.txt', {
        body: consoleErrors.join('\n'),
        contentType: 'text/plain',
      });
    }

    // The constraint reaching the model is the one hard assertion. Everything else
    // above is captured for judgement rather than asserted, because this run exists
    // to show what the pipeline produced, not to gate a build.
    const constraintHits = signals['price-lock'] + signals['price lock'] +
                           signals['anchor account'] + signals['contractual'];
    expect(constraintHits, 'no price-lock/anchor-account constraint language in SF output').toBeGreaterThan(0);
  });
});
