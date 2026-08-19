/**
 * Preflight checks for live-*.spec.ts runs.
 *
 * Live specs spend real LLM tokens and ~5-10 minutes per run — a flag silently
 * being false (env var only ever exported ad hoc in some prior shell session,
 * never persisted anywhere the next restart would pick up) has already produced
 * one misleading "pass" this session, on a code path that runs fine with the
 * gate off and would still exercise the app, just not the thing the test claims
 * to prove. Fail fast and loud instead of trusting a comment telling the human
 * to check first.
 */

const BACKEND_URL = 'http://localhost:8000';

/**
 * Hits GET /healthz and asserts `features[flagKey] === true`. Throws with a
 * clear fix-it message (not just an assertion diff) if the backend is
 * unreachable or the flag isn't set — this is meant to fail in the first
 * second of a 5-10 minute run, not after it burns tokens.
 */
export async function requireFeatureFlag(flagKey: string): Promise<void> {
  let body: any;
  try {
    const res = await fetch(`${BACKEND_URL}/healthz`);
    body = await res.json();
  } catch (err) {
    throw new Error(
      `[live-preflight] Could not reach ${BACKEND_URL}/healthz (${(err as Error).message}). ` +
      `Is the backend running? Use restart_decision_studio_ui.ps1, not npm/uvicorn directly.`
    );
  }
  const actual = body?.features?.[flagKey];
  if (actual !== true) {
    throw new Error(
      `[live-preflight] Required feature flag "${flagKey}" is ${JSON.stringify(actual)}, not true. ` +
      `Set it in .env (see .env.example), then restart via restart_decision_studio_ui.ps1 — ` +
      `the flag is only read at agent creation on backend startup, so editing .env alone is not enough.`
    );
  }
}
