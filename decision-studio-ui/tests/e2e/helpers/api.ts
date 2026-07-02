import { Page } from '@playwright/test';

export const MOCK_CLIENTS = [
  { id: 'lubricants', name: 'Lubricants Business', industry: 'Oil & Gas / Specialty Chemicals', data_product_ids: ['dp_lubricants_financials'] },
];

export const MOCK_PRINCIPALS = [
  { id: 'cfo_001', name: 'Sarah Chen', title: 'CFO', role: 'CFO', decision_style: 'analytical', color: 'bg-blue-500/20 text-blue-400' },
  { id: 'ceo_001', name: 'David Torres', title: 'CEO', role: 'CEO', decision_style: 'visionary', color: 'bg-purple-500/20 text-purple-400' },
];

/** Mock all background registry/VA calls that fire automatically on dashboard load. */
export async function mockBackgroundCalls(page: Page, clientId = 'lubricants') {
  await page.route(`**/api/v1/registry/clients**`, route =>
    route.fulfill({ json: MOCK_CLIENTS })
  );
  await page.route(`**/api/v1/registry/principals**`, route =>
    route.fulfill({ json: MOCK_PRINCIPALS })
  );
  await page.route(`**/api/v1/registry/kpis**`, route =>
    route.fulfill({ json: [] })
  );
  await page.route(`**/api/v1/value-assurance/portfolio/**`, route =>
    route.fulfill({ json: { solutions: [], total_solutions: 0 } })
  );
  // Health + auth endpoints
  await page.route(`**/healthz`, route => route.fulfill({ json: { status: 'ok' } }));
}

/** Navigate through demo mode login as the given principal. */
export async function loginAsDemo(page: Page, principalId = 'cfo_001', clientId = 'lubricants') {
  await mockBackgroundCalls(page, clientId);
  await page.goto('/login?mode=demo');
  await page.waitForSelector(`[data-testid="principal-card-${principalId}"]`, { timeout: 10_000 });
  await page.locator(`[data-testid="principal-card-${principalId}"]`).click();
  await page.locator('[data-testid="demo-enter-btn"]').click();
  await page.waitForURL('**/dashboard', { timeout: 5_000 });
}

/**
 * Set up API route mocks for a situations workflow that returns the given situations immediately.
 * Must be called BEFORE loginAsDemo (routes are matched from registration time).
 */
/**
 * Set up API route mocks for a situations workflow that returns the given situations immediately.
 * Must be called BEFORE loginAsDemo (routes are matched from registration time).
 *
 * Two invariants from client.ts:
 *  1. request_id must start with 'situation_' or detectSituations() throws immediately.
 *  2. The workflow result is stored as result.situations (the serialised SA response object),
 *     so the client reads data.result.situations.situations to get the array.
 */
export async function mockSituationsScan(
  page: Page,
  requestId: string,
  situations: any[],
  opportunities: any[] = [],
  kpiEvaluatedCount = 15,
) {
  // Ensure the id satisfies the client's startsWith('situation_') guard
  const fullRequestId = requestId.startsWith('situation_') ? requestId : `situation_${requestId}`;

  await page.route('**/api/v1/workflows/situations/run', route =>
    route.fulfill({
      json: { status: 'ok', data: { request_id: fullRequestId, state: 'pending' } },
    })
  );
  await page.route(`**/api/v1/workflows/situations/${fullRequestId}/status`, route =>
    route.fulfill({
      json: {
        status: 'ok',
        data: {
          request_id: fullRequestId,
          workflow_type: 'situations',
          state: 'completed',
          payload: {},
          // result.situations mirrors the serialised SA response: { situations, opportunities, ... }
          // client.ts line 398: const output = data.result.situations; output.situations → array
          result: {
            situations: {
              status: 'success',
              situations,
              opportunities,
              kpi_evaluated_count: kpiEvaluatedCount,
            },
          },
          error: null,
          annotations: [],
          actions: [],
        },
      },
    })
  );
}
