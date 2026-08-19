import { Newspaper } from 'lucide-react';
import type { FramingPrompt, FramingAlternative } from '../api/types';
import { CausalTrendChart } from './visualizations/CausalTrendChart';
import { buildCausalTrendChart } from '../utils/causalTrendSeries';
import { orderedCausalKpiIds, causalColorFor, alternativeShortLabel, CAUSAL_PRIMARY_HUE } from '../utils/causalColors';

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
  high: 'text-emerald-400 border-emerald-700',
  moderate: 'text-amber-400 border-amber-700',
  low: 'text-red-400 border-red-700',
};

function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  const sign = v > 0 ? '+' : '';
  return `${sign}${v.toFixed(1)}%`;
}

function EvidenceCard({ alt, dotColor }: { alt: FramingAlternative; dotColor: string }) {
  const isMarket = alt.source === 'market_signal';
  const confidenceClass = alt.confidence && CONFIDENCE_TONE[alt.confidence]
    ? CONFIDENCE_TONE[alt.confidence]
    : 'text-slate-400 border-slate-600';
  const snap = alt.neighbour_snapshot;

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
            {snap && snap.value !== null && snap.value !== undefined && (
              <span className="flex-shrink-0 text-right text-xs">
                <span className="font-medium text-slate-200">{fmtPct(snap.percent_change)}</span>
                <span className="ml-1 text-slate-500">this period</span>
              </span>
            )}
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
            <p key={i} className="mt-1 text-xs italic text-amber-500/80">{c}</p>
          ))}
        </div>
      </div>
    </div>
  );
}

export function CausalNeighbourhoodEvidence({ prompt, kpiName }: { prompt: FramingPrompt; kpiName: string }) {
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
        </div>
      )}

      <div className="space-y-2">
        {prompt.alternatives.map((alt, i) => (
          <EvidenceCard
            key={`${alt.source}-${alt.kpi_id ?? i}`}
            alt={alt}
            dotColor={alt.source === 'causal_graph' ? causalColorFor(alt.kpi_id, ordered) : CAUSAL_PRIMARY_HUE}
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
