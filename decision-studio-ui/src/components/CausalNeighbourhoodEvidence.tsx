import { Newspaper, ExternalLink } from 'lucide-react';
import type { FramingPrompt, FramingAlternative } from '../api/types';
import { CausalTrendChart } from './visualizations/CausalTrendChart';
import { buildCausalTrendChart } from '../utils/causalTrendSeries';
import { orderedCausalKpiIds, causalColorFor, alternativeShortLabel, CAUSAL_PRIMARY_HUE } from '../utils/causalColors';
import { openInvestigateTab } from '../utils/investigateLink';

/**
 * Phase 20 §14 decision 8 — the LEFT-panel (primary DA pane) half of the
 * evidence/decision split. FramingGateCard (right panel, Action Center)
 * stays a compact color-dot + label dialog; this component holds the rich
 * evidence that dialog used to cram into its own narrow column: the trend
 * chart, and the detailed per-alternative cards (mechanism, hops,
 * confidence, provenance, caveats). Read-only — selection happens in the
 * compact right-panel list, not here.
 *
 * Rendered inside a new "Causal Neighbourhood" accordion that auto-expands
 * the moment the framing gate activates (§14 decision 9 — evidence must be
 * SEEN, not just fetched-and-collapsed, for the same "skimming isn't
 * examining" reason Phase 19 exists at all). See DeepFocusView.tsx's
 * `openSections` effect.
 */

const CONFIDENCE_TONE: Record<string, string> = {
  high: 'text-severity-opportunity border-severity-opportunity',
  moderate: 'text-severity-warning border-severity-warning',
  low: 'text-severity-critical border-severity-critical',
};

function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  const sign = v > 0 ? '+' : '';
  return `${sign}${v.toFixed(1)}%`;
}

function EvidenceCard({
  alt,
  dotColor,
  clientId,
  principalId,
}: {
  alt: FramingAlternative;
  dotColor: string;
  clientId?: string;
  principalId?: string;
}) {
  const isMarket = alt.source === 'market_signal';
  const confidenceClass = alt.confidence && CONFIDENCE_TONE[alt.confidence]
    ? CONFIDENCE_TONE[alt.confidence]
    : 'text-slate-400 border-slate-600';
  const snap = alt.neighbour_snapshot;
  // Offered for every causal-graph neighbour regardless of basis — see
  // investigateLink.ts for why an accounting_identity component is still
  // worth a separate look (it just can't register as a new causal finding).
  const canAnalyze = !isMarket && !!alt.kpi_id;

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3">
      <div className="flex items-start gap-2.5">
        {isMarket ? (
          <Newspaper className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-cyan-400" />
        ) : (
          <span className="mt-1.5 h-2.5 w-2.5 flex-shrink-0 rounded-full" style={{ backgroundColor: dotColor }} />
        )}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <p className="text-sm leading-snug text-slate-100">{alt.objective_text}</p>
            <div className="flex flex-shrink-0 items-center gap-2">
              {snap && snap.value !== null && snap.value !== undefined && (
                <span className="text-right text-xs">
                  <span className="font-medium text-slate-200">{fmtPct(snap.percent_change)}</span>
                  <span className="ml-1 text-slate-500">this period</span>
                </span>
              )}
              {canAnalyze && (
                <button
                  type="button"
                  data-testid="causal-neighbour-analyze"
                  title={`Open an independent analysis of ${alt.kpi_id} in a new tab — doesn't affect this decision`}
                  onClick={() => openInvestigateTab(alt.kpi_id as string, clientId, principalId)}
                  className="flex items-center gap-1 rounded border border-slate-600 px-1.5 py-0.5 text-[10px] text-slate-400 hover:border-indigo-500 hover:text-indigo-300"
                >
                  Analyze <ExternalLink className="h-2.5 w-2.5" />
                </button>
              )}
            </div>
          </div>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            <span className="rounded border border-slate-600 px-1.5 py-px text-[9px] uppercase tracking-wider text-slate-400">
              {isMarket ? 'external signal' : 'causal graph'}
            </span>
            {!isMarket && alt.hops != null && (
              <span className="rounded border border-slate-600 px-1.5 py-px text-[9px] uppercase tracking-wider text-slate-400">
                {alt.hops} hop{alt.hops === 1 ? '' : 's'} away
              </span>
            )}
            {alt.confidence && (
              <span className={`rounded border px-1.5 py-px text-[9px] uppercase tracking-wider ${confidenceClass}`}>
                {alt.confidence}
              </span>
            )}
            {alt.provenance && (
              <span className="text-[9px] font-mono text-slate-500">· {alt.provenance}</span>
            )}
          </div>
          {alt.mechanism && (
            <p className="mt-1.5 text-xs text-slate-400">Mechanism: {alt.mechanism}</p>
          )}
          {alt.provenance_caveat && (
            <p className="mt-1 text-xs italic text-slate-500">{alt.provenance_caveat}</p>
          )}
          {alt.evidence_caveats?.map((c, i) => (
            <p key={i} className="mt-1 text-xs italic text-severity-warning/80">{c}</p>
          ))}
        </div>
      </div>
    </div>
  );
}

export function CausalNeighbourhoodEvidence({
  prompt,
  kpiName,
  clientId,
  principalId,
}: {
  prompt: FramingPrompt;
  kpiName: string;
  clientId?: string;
  principalId?: string;
}) {
  const ordered = orderedCausalKpiIds(prompt.alternatives);
  const chartData = buildCausalTrendChart(
    { kpiId: prompt.kpi_id || kpiName, label: kpiName, snapshot: prompt.primary_snapshot },
    prompt.alternatives
      .filter(a => a.source === 'causal_graph' && a.kpi_id)
      .map(a => ({ kpiId: a.kpi_id as string, label: alternativeShortLabel(a), snapshot: a.neighbour_snapshot })),
  );

  if (prompt.alternatives.length === 0) {
    return (
      <p className="text-xs italic text-slate-500">
        No specific alternative is suggested by the causal graph or market signals for {kpiName} this period.
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {chartData && (
        <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
            Relative trend — % change from each series' own starting point
          </p>
          <CausalTrendChart periods={chartData.periods} series={chartData.series} height={200} />
          {chartData.omitted.length > 0 && (
            <p className="mt-2 text-[10px] text-slate-500">
              Trend unavailable for {chartData.omitted.join(', ')} — no monthly series returned for
              this measure. Its “this period” figure above is unaffected.
            </p>
          )}
        </div>
      )}

      <div className="space-y-2">
        {prompt.alternatives.map((alt, i) => (
          <EvidenceCard
            key={`${alt.source}-${alt.kpi_id ?? i}`}
            alt={alt}
            dotColor={alt.source === 'causal_graph' ? causalColorFor(alt.kpi_id, ordered) : CAUSAL_PRIMARY_HUE}
            clientId={clientId}
            principalId={principalId}
          />
        ))}
      </div>

      {prompt.additional_causal_measures_count > 0 && (
        <p className="text-xs italic text-slate-500">
          +{prompt.additional_causal_measures_count} more causal measure{prompt.additional_causal_measures_count === 1 ? '' : 's'} evaluated,
          not shown — ranked lower by current relevance.
        </p>
      )}
    </div>
  );
}

export default CausalNeighbourhoodEvidence;
