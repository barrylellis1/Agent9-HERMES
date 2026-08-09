import { test, expect } from '@playwright/test';
import { buildExecutiveBriefing } from '../../src/utils/briefingUtils';

/**
 * Recovery-share on the ROI line — pure-function tests, no browser, no LLM.
 *
 * WHY
 * ---
 * A real briefing showed all three options as "+$3.2M to +$5.1M", reading as
 * three equally attractive choices. Against their own targets those same
 * numbers meant 50-80%, 59-94% and 75-119% of the decline — the third claiming
 * to recover MORE than the entire loss it addressed. The moderator had already
 * flagged two of the three; the reader could not see it because the headline
 * figure never showed its denominator.
 *
 * Rounding made it worse: opt_1's high was $5,127,423 and opt_3's $5,114,511,
 * and .toFixed(1) at millions scale printed both as "$5.1M".
 *
 * Playwright's runner executes TypeScript directly, so these run as unit tests
 * (~1s) despite living in the e2e folder — the project has no jest/vitest.
 */

const CHAIN_A = 6_409_279;
const DIY_RETAIL = 5_429_733;
const ENGINE_OILS = 4_270_488;

function situation(overrides: any = {}) {
  return {
    kpi_name: 'Gross Profit',
    severity: 'critical',
    description: 'Gross Profit decreased by 14.4% vs prior year',
    kpi_value: { value: 34_100_000, unit: '$', percent_change: -32.9 },
    ...overrides,
  };
}

function analysis(overrides: any = {}) {
  return {
    kt_is_is_not: {
      where_is: [
        { dimension: 'customer_name', key: 'National Auto Parts Chain A', current: -57_700_000, previous: -51_200_000, delta: -CHAIN_A },
        { dimension: 'channel_name', key: 'DIY Retail', current: -30_100_000, previous: -24_700_000, delta: -DIY_RETAIL },
        { dimension: 'product_line', key: 'Engine Oils', current: -13_800_000, previous: -9_600_000, delta: -ENGINE_OILS },
      ],
    },
    aggregates: { comparison_value: 50_800_000 },
    ...overrides,
  };
}

function option(id: string, label: string | null, low: number, high: number, scope: string | null = 'segment') {
  return {
    id, title: `Option ${id}`, description: 'd', expected_impact: 0.7, cost: 0.3, risk: 0.3,
    impact_estimate: {
      metric: 'Gross Profit', unit: '$', basis: 'b',
      scope, scope_label: label, recovery_range: { low, high },
    },
  };
}

function roiFor(opts: any[], sit = situation(), ana = analysis()): string[] {
  const b: any = buildExecutiveBriefing(sit, ana, { options_ranked: opts, recommendation: { id: opts[0]?.id } }, []);
  return b.options.map((o: any) => o.roi);
}

test.describe('ROI recovery share', () => {
  test('THE REGRESSION: identical ranges no longer read as identical value', async () => {
    // Verbatim from the real briefing: same range, three different targets.
    const rois = roiFor([
      option('opt_1', 'National Auto Parts Chain A', 3_204_640, 5_127_423),
      option('opt_2', 'DIY Retail', 3_200_000, 5_100_000),
      option('opt_3', 'Engine Oils', 3_200_000, 5_114_511),
    ]);

    // The absolute figures still round to the same text — that is the display
    // limit that fooled the reader. The SHARE is what separates them.
    expect(rois[0]).toContain('50-80% of');
    expect(rois[1]).toContain('59-94% of');
    expect(rois[2]).toContain('75-120% of');
    expect(new Set(rois).size, 'three options must not render one identical string').toBe(3);
  });

  test('a claim exceeding the loss it targets is marked, not passed silently', async () => {
    const [roi] = roiFor([option('opt_1', 'Engine Oils', 3_200_000, 5_114_511)]);
    expect(roi).toContain('exceeds the loss');
  });

  test('possessive of a plural segment name is not mangled', async () => {
    // Segment names are frequently plural, and this sits on the first line an
    // executive reads: "Engine Oils' decline", never "Engine Oils's decline".
    const [plural] = roiFor([option('opt_1', 'Engine Oils', 1_000_000, 2_000_000)]);
    expect(plural).toContain("Engine Oils' decline");
    expect(plural).not.toContain("Oils's");

    const [singular] = roiFor([option('opt_1', 'DIY Retail', 1_000_000, 2_000_000)]);
    expect(singular).toContain("DIY Retail's decline");
  });

  test('a claim within the loss carries no warning', async () => {
    const [roi] = roiFor([option('opt_1', 'National Auto Parts Chain A', 3_204_640, 5_127_423)]);
    expect(roi).toContain('50-80%');
    expect(roi).not.toContain('exceeds the loss');
  });

  test('enterprise scope divides by the headline movement, not a segment', async () => {
    // Headline: 34.1M now vs 50.8M prior -> 16.7M decline.
    const [roi] = roiFor([option('opt_1', null, 3_340_000, 8_350_000, 'enterprise')]);
    expect(roi).toContain('(enterprise)');
    expect(roi).toContain('20-50% of the enterprise decline');
  });

  test('compound scope takes the LARGEST named segment, never the sum', async () => {
    // Summing segment deltas across differently-weighted segments is the exact
    // arithmetic error this display exists to surface — it must not be made here.
    const [roi] = roiFor([option('opt_1', 'National Auto Parts Chain A & DIY Retail', 3_200_000, 6_409_279)]);
    expect(roi).toContain('100%');           // 6.41M / 6.41M, the larger segment
    expect(roi).not.toContain('54%');        // 6.41M / (6.41M + 5.43M) if summed
  });

  test('unknown segment label yields no share rather than a guessed one', async () => {
    const [roi] = roiFor([option('opt_1', 'Some Segment Not In The Analysis', 3_200_000, 5_100_000)]);
    expect(roi).toContain('only');
    expect(roi).not.toContain('% of');
  });

  test('unstated scope is called out as unstated, with no share', async () => {
    // Wording changed 2026-08-09: "(scope unverified)" read to a buyer as "we do
    // not trust our own number". What is actually missing is the model's
    // DECLARATION of whether the figure is enterprise-wide or one segment — which
    // changes its size by an order of magnitude. The figure itself is not in doubt.
    const [roi] = roiFor([option('opt_1', null, 3_200_000, 5_100_000, null)]);
    expect(roi).toContain('scope not stated');
    expect(roi).not.toContain('unverified');
    expect(roi).not.toContain('% of');
  });

  test('missing enterprise baseline suppresses the share instead of inventing one', async () => {
    const ana = analysis({ aggregates: {} });
    const rois = roiFor([option('opt_1', null, 3_200_000, 5_100_000, 'enterprise')], situation(), ana);
    expect(rois[0]).toContain('(enterprise)');
    expect(rois[0]).not.toContain('% of');
  });

  test('option id is carried through so verdicts can resolve a title', async () => {
    const b: any = buildExecutiveBriefing(
      situation(), analysis(),
      { options_ranked: [option('opt_2', 'DIY Retail', 1, 2)], recommendation: { id: 'opt_2' } }, []
    );
    expect(b.options[0].id).toBe('opt_2');
  });
});
