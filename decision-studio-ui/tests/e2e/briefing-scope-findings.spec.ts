import { test, expect } from '@playwright/test';
import { loginAsDemo } from './helpers/api';
import { MODERATOR_BRIEFING } from './fixtures/moderator-briefing';

/**
 * Scope-check findings reach the reader — mocked, no LLM cost.
 *
 * Solution Finder checks each option's declared scope against the segment figures
 * (src/analysis/general_deviation_gate.py). Until 2026-10-13 the findings reached only
 * the audit log, so an option claiming to recover more than its segment had lost
 * looked identical to one that did not. Seeded the same way as briefing-render.spec.ts.
 */

const SITUATION_ID = 'sit_briefing_scope_findings_001';

const WITH_FINDING = {
  ...MODERATOR_BRIEFING,
  options: MODERATOR_BRIEFING.options.map((o: any, i: number) => ({
    ...o,
    scopeQualifier: i === 0 ? { scope: 'segment', label: 'Retail Partners', reason: 'largest_exposure' } : o.scopeQualifier,
    scopeFindings: i === 0 ? ["Claims to recover more than the named segment's own share of the gap."] : [],
  })),
};

test('an option with a scope-check finding says so; one without does not', async ({ page }) => {
  await page.addInitScript(
    ([id, payload]: [string, string]) => window.localStorage.setItem(`briefing_${id}`, payload),
    [SITUATION_ID, JSON.stringify(WITH_FINDING)]
  );
  await loginAsDemo(page);
  await page.goto(`/briefing/${SITUATION_ID}`);

  const options = page.getByRole('button', { name: /strategic options/i });
  await expect(options).toBeVisible({ timeout: 15_000 });
  if ((await options.getAttribute('aria-expanded')) === 'false') await options.click();

  const findings = page.getByTestId('option-scope-findings');
  await expect(findings).toHaveCount(1);
  await expect(findings.first()).toContainText("Scope check: Claims to recover more than the named segment's own share of the gap.");
  await expect(page.getByText(/Segment \(largest exposure\): Retail Partners/).first()).toBeVisible();
});
