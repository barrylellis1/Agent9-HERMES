import { defineConfig, devices } from '@playwright/test';

/**
 * Config for LIVE, unmocked pipeline runs — separate from playwright.config.ts.
 *
 * The default config exists for the hermetic mocked suite: short timeouts, parallel
 * workers, retries. Every one of those is wrong for a run that spends real LLM
 * tokens and takes ~10 minutes, so this keeps them apart rather than loosening the
 * fast suite to accommodate the slow one.
 *
 * Run:  npx playwright test --config=playwright.live.config.ts
 */
export default defineConfig({
  testDir: './tests/e2e',

  // Only live-*.spec.ts. Without this the mocked suite would be dragged in and run
  // under 35-minute timeouts against a full-mode server, which helps nobody.
  testMatch: /live-.*\.spec\.ts/,

  fullyParallel: false,
  workers: 1,

  // No retries. A retry silently re-spends a full debate's tokens, and a live run
  // that fails intermittently is itself the finding — hiding it behind a retry is
  // exactly the "non-fatal degradation looks like success" pattern this suite is
  // meant to catch.
  retries: 0,

  // Full debate is ~9 min of LLM time (vs ~3 in fast mode), plus the SA scan over
  // 15 KPIs against BigQuery and the DA dimensional pass on 39 segments.
  timeout: 35 * 60_000,
  expect: { timeout: 30_000 },

  // html so testInfo.attach() artifacts survive; list for readable console progress.
  // Passing --reporter=list on the CLI OVERRIDES this and silently discards every
  // attachment — the spec also writes its payload to disk with fs for that reason.
  reporter: [['html', { outputFolder: 'playwright-report-live', open: 'never' }], ['list']],

  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
    screenshot: 'on',
    video: 'retain-on-failure',
    actionTimeout: 60_000,
    navigationTimeout: 60_000,
  },

  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],

  webServer: {
    command: 'npm run dev',
    port: 5173,

    // PRODUCTION PARITY — the point of this config.
    // .env.development sets VITE_DEBATE_MODE=fast (stage1_only -> synthesis, 2 LLM
    // calls). Production sets full (stage1_only -> hypothesis -> cross_review ->
    // synthesis, 4 calls). Judging solution QUALITY against fast mode would grade a
    // materially different pipeline from the one customers see.
    //
    // Only this one variable is overridden. Running vite with `--mode production`
    // would also swap VITE_API_URL to https://api.trydecisionstudio.com and the
    // Supabase keys to placeholders — i.e. drive production and break auth. The
    // backend stays local; only debate depth matches production.
    //
    // Vite gives already-present process env the highest priority and will not let
    // .env files overwrite it, so this beats .env.development's `fast`.
    env: { VITE_DEBATE_MODE: 'full' },

    // Must NOT reuse a server started under fast mode — it would silently ignore
    // the override above and produce a fast-mode result labelled production-like.
    reuseExistingServer: false,
    timeout: 120_000,
    stdout: 'pipe',
    stderr: 'pipe',
  },

  outputDir: 'playwright-results-live',
});
