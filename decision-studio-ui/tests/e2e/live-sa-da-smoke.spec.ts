import { test, expect } from '@playwright/test';

/**
 * LIVE run — SA + DA smoke test across all three externally-connected backends
 * (Snowflake / apex_lubricants, BigQuery / lubricants, SQL Server / hess),
 * driven after Phase 16 step 1 (dimension_semantics moving from YAML to the
 * registry, a9_deep_analysis_agent.py's _dims_from_contract). Confirms the
 * change didn't break dimension resolution for ANY of the three — lubricants
 * now reads dimension_semantics from the registry, the other two still read
 * it from the legacy YAML fallback (unmigrated), and both paths need to work.
 *
 * Deliberately narrow scope: SA scan -> click a card -> DA completes with
 * real dimensions analyzed. No framing gate, no Solution Finder — this is a
 * pipeline-health check, not a KPI-correctness check. hess's gross_margin_pct
 * is a KNOWN-wrong number (sign-convention bug, DEVELOPMENT_PLAN.md Phase 16
 * step 3, not yet fixed) — DA completing with dimensions is success here
 * regardless of whether the number itself is right.
 *
 * Run:  npx playwright test --config=playwright.live.config.ts live-sa-da-smoke
 * Backend connectivity pre-checked live via scripts/validate_client_kpis.py
 * before this spec was written — all three backends confirmed reachable.
 */

const SCAN_TIMEOUT = 240_000;
const DA_TIMEOUT = 300_000;

const CLIENTS = [
  { clientId: 'lubricants', backend: 'BigQuery', principalId: 'cfo_001', kpiKeyword: 'gross margin' },
  { clientId: 'apex_lubricants', backend: 'Snowflake', principalId: 'cfo_001', kpiKeyword: 'gross margin' },
  { clientId: 'hess', backend: 'SQL Server', principalId: 'cfo_001', kpiKeyword: 'gross margin' },
];

for (const cfg of CLIENTS) {
  test.describe(`Live — SA+DA smoke (${cfg.clientId}, ${cfg.backend})`, () => {
    test.describe.configure({ mode: 'serial', timeout: 12 * 60_000 });

    test(`SA scans and DA completes with real dimensions`, async ({ page }, testInfo) => {
      const consoleErrors: string[] = [];
      page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
      page.on('pageerror', e => consoleErrors.push(`pageerror: ${e.message}`));

      // DA runs async: POST /deep-analysis/run kicks it off, the client then
      // polls GET /deep-analysis/{id}/status until state==='completed'. The
      // dimensional analysis lives at result.execution.{dimensions_analyzed,
      // change_points} (see workflows.py's result_payload = {plan, execution,
      // market_signals, ...} — execution is DeepAnalysisResponse serialized
      // whole, confirmed by reading the route directly, not assumed).
      let daResult: any = null;
      page.on('response', async res => {
        const u = res.url();
        if (!u.includes('deep-analysis')) return;
        console.log(`[net] ${res.request().method()} ${u} -> ${res.status()}`);
        if (u.includes('/workflows/deep-analysis/') && u.includes('/status') && res.request().method() === 'GET') {
          try {
            const j = await res.json();
            const data = j?.data ?? j;
            console.log(`[net] status body state=${data?.state}`);
            if (data?.state === 'completed' && data?.result) daResult = data.result;
          } catch (e) { console.log(`[net] status parse failed: ${e}`); }
        }
      });

      // ── Login: select client, then principal ──────────────────────────────
      await page.goto('/login?mode=demo');
      const clientSelector = page.getByTestId('client-selector');
      await clientSelector.waitFor({ state: 'visible', timeout: 30_000 });
      await clientSelector.selectOption(cfg.clientId);

      const principalCard = page.getByTestId(`principal-card-${cfg.principalId}`);
      await principalCard.waitFor({ state: 'visible', timeout: 30_000 });
      await principalCard.click();
      await page.getByTestId('demo-enter-btn').click();
      await page.waitForURL('**/dashboard', { timeout: 30_000 });

      // Some principals (Sarah Chen/CFO among them) have workflow_role
      // 'decision_maker' and land on DecisionMakerLanding — a decision-inbox
      // view, not the SA situation grid — until "View full dashboard" is
      // clicked (DecisionStudio.tsx:71, setShowFullView(true)). No testid on
      // that button; match by its visible text. Race it against the grid
      // itself (already-full-view principals skip the landing page entirely)
      // rather than a synchronous count() check, which can run before either
      // has mounted and silently no-op.
      const viewFullDashboard = page.getByRole('button', { name: /view full dashboard/i });
      const situationGrid = page.locator('[data-testid="situation-grid"]');
      await Promise.race([
        viewFullDashboard.waitFor({ state: 'visible', timeout: SCAN_TIMEOUT }),
        situationGrid.waitFor({ state: 'visible', timeout: SCAN_TIMEOUT }),
      ]).catch(() => { /* neither showed up in time; the explicit wait below reports it */ });
      if (await viewFullDashboard.isVisible().catch(() => false)) await viewFullDashboard.click();

      // ── SA ──────────────────────────────────────────────────────────────
      await page.waitForSelector('[data-testid="situation-grid"]', { timeout: SCAN_TIMEOUT });
      const cards = page.locator('[data-testid^="situation-card-"]');
      const cardCount = await cards.count();
      expect(cardCount, `SA produced no situation cards for ${cfg.clientId}`).toBeGreaterThan(0);

      const cardText: string[] = [];
      for (let i = 0; i < cardCount; i++) {
        cardText.push(((await cards.nth(i).innerText()) || '').replace(/\s+/g, ' ').trim());
      }
      let target = 0;
      for (let i = 0; i < cardCount; i++) {
        if (cardText[i].toLowerCase().includes(cfg.kpiKeyword)) { target = i; break; }
      }
      console.log(`[sa-da-smoke:${cfg.clientId}] driving card [${target}]: ${cardText[target].slice(0, 100)}`);
      await cards.nth(target).click();

      // ── DA ──────────────────────────────────────────────────────────────
      // The real completion signal is the network capture (daResult), not UI
      // text: "Workflow timed out"/"Run Deep Analysis to unlock" are both
      // ABSENT during the normal in-flight/analyzing state too, so checking
      // only for their absence passes trivially the instant the click fires,
      // before DA has done anything — caught by an earlier version of this
      // spec (toPass() resolved on its first 0-interval check). Poll the
      // captured client-side status response instead; it's the same signal
      // client.ts itself blocks on.
      const daTimedOut = page.getByText(/workflow timed out/i);
      if (await daTimedOut.count()) throw new Error(`DA reported "Workflow timed out" for ${cfg.clientId}`);
      await expect.poll(() => daResult, { timeout: DA_TIMEOUT, intervals: [2_000] }).not.toBeNull();

      const openActionCenter = page.getByRole('button', { name: /open action center/i });
      if (await openActionCenter.count()) await openActionCenter.first().click();

      await page.screenshot({ path: testInfo.outputPath(`01-${cfg.clientId}-da-complete.png`), fullPage: true });

      // ── Assertions: DA actually produced dimensional analysis ─────────────
      expect(daResult, `no completed DA status response captured for ${cfg.clientId}`).toBeTruthy();
      const dimsAnalyzed = daResult?.execution?.dimensions_analyzed;
      const changePoints = daResult?.execution?.change_points;
      console.log(`[sa-da-smoke:${cfg.clientId}] dimensions_analyzed=${JSON.stringify(dimsAnalyzed)}`);
      console.log(`[sa-da-smoke:${cfg.clientId}] change_points count=${Array.isArray(changePoints) ? changePoints.length : 'n/a'}`);

      expect(
        Array.isArray(dimsAnalyzed) && dimsAnalyzed.length > 0,
        `${cfg.clientId}: DA completed but analyzed zero dimensions — dimension resolution broke for this backend`
      ).toBe(true);

      const realErrors = consoleErrors.filter(e => !/favicon|net::ERR|Failed to load resource|429|404/i.test(e));
      expect(realErrors, `${cfg.clientId} console errors: ${realErrors.slice(0, 5).join(' | ')}`).toEqual([]);
    });
  });
}
