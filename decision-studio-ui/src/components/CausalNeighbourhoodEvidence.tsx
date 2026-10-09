import { useEffect, useState } from 'react';
import { Newspaper, ExternalLink, Globe } from 'lucide-react';
import type { FramingPrompt, FramingAlternative } from '../api/types';
import { getTheoryLayer, TheoryLayerPayload, TheoryPort } from '../api/client';
import { CausalTrendChart } from './visualizations/CausalTrendChart';
import { buildCausalTrendChart } from '../utils/causalTrendSeries';
import { orderedCausalKpiIds, causalColorFor, alternativeShortLabel, CAUSAL_PRIMARY_HUE } from '../utils/causalColors';
import { openInvestigateTab } from '../utils/investigateLink';
import { linkTrust, distanceInWords } from '../utils/trustState';
import { TrustBadge } from './shared/TrustBadge';

/**
 * "Related drivers" — the LEFT-panel (primary DA pane) half of the
 * evidence/decision split (Phase 20 §14 decision 8). FramingGateCard (right
 * panel) collects the decision; this holds the evidence: the trend chart and
 * one tile per related driver.
 *
 * Each tile shows a name, one of three trust states (utils/trustState.ts) and
 * one plain sentence. Everything an analyst needs to check the claim —
 * mechanism, distance, confidence, source, caveats — sits behind "Why".
 *
 * Auto-expands the moment the framing gate activates (§14 decision 9). See
 * DeepFocusView.tsx's `openSections` effect.
 */

function fmtPct(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return '—';
  const sign = v > 0 ? '+' : '';
  return `${sign}${v.toFixed(1)}%`;
}

function EvidenceCard({
  alt,
  dotColor,
  kpiName,
  clientId,
  principalId,
}: {
  alt: FramingAlternative;
  dotColor: string;
  kpiName: string;
  clientId?: string;
  principalId?: string;
}) {
  const isMarket = alt.source === 'market_signal';
  const snap = alt.neighbour_snapshot;
  const trust = isMarket ? null : linkTrust(alt, kpiName);
  const distance = isMarket ? null : distanceInWords(alt.hops);
  const canAnalyze = !isMarket && !!alt.kpi_id;
  const hasDetail = !!(alt.mechanism || distance || alt.confidence || alt.lag_periods != null
    || alt.provenance || alt.provenance_caveat || alt.evidence_caveats?.length);

  return (
    <div data-testid="related-driver-tile" className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3">
      <div className="flex items-center gap-2.5">
        {isMarket ? (
          <Newspaper className="h-3.5 w-3.5 flex-shrink-0 text-cyan-400" />
        ) : (
          <span className="h-2.5 w-2.5 flex-shrink-0 rounded-full" style={{ backgroundColor: dotColor }} />
        )}
        <p className="min-w-0 flex-1 text-sm font-medium leading-snug text-slate-100">
          {isMarket ? alt.objective_text : alternativeShortLabel(alt)}
        </p>
        {trust ? (
          <TrustBadge state={trust.state} held={trust.held} />
        ) : (
          <span className="flex-shrink-0 rounded border border-slate-600 px-1.5 py-0.5 text-[10px] font-medium text-slate-400">
            Market signal
          </span>
        )}
        {snap && snap.value !== null && snap.value !== undefined && (
          <span className="flex-shrink-0 text-right text-xs">
            <span className="font-medium text-slate-200">{fmtPct(snap.percent_change)}</span>
            <span className="ml-1 text-slate-500">this period</span>
          </span>
        )}
        {canAnalyze && (
          <button
            type="button"
            data-testid="causal-neighbour-analyze"
            title={`Open a separate analysis of ${alternativeShortLabel(alt)} in a new tab. This decision is not affected.`}
            onClick={() => openInvestigateTab(alt.kpi_id as string, clientId, principalId, alternativeShortLabel(alt))}
            className="flex flex-shrink-0 items-center gap-1 rounded border border-slate-600 px-1.5 py-0.5 text-[10px] text-slate-400 hover:border-indigo-500 hover:text-indigo-300"
          >
            Analyze <ExternalLink className="h-2.5 w-2.5" />
          </button>
        )}
      </div>

      {trust && <p className="mt-1.5 pl-5 text-xs text-slate-400">{trust.line}</p>}

      {hasDetail && (
        <details className="mt-1.5 pl-5">
          <summary className="cursor-pointer list-none text-[11px] text-slate-500 hover:text-slate-300">
            ▸ Why
          </summary>
          <div data-testid="related-driver-detail" className="mt-1.5 space-y-1 text-xs text-slate-400">
            {alt.mechanism && <p>{alt.mechanism}</p>}
            {(distance || alt.confidence || alt.lag_periods != null) && (
              <p className="text-slate-500">
                {[
                  distance,
                  alt.confidence ? `${alt.confidence} confidence` : null,
                  alt.lag_periods != null ? `${alt.lag_periods}-month lag` : null,
                ].filter(Boolean).join(' · ')}
              </p>
            )}
            {alt.provenance_caveat && <p className="text-slate-500">{alt.provenance_caveat}</p>}
            {alt.evidence_caveats?.map((c, i) => (
              <p key={i} className="text-slate-500">{c}</p>
            ))}
            {alt.provenance && (
              <p className="font-mono text-[10px] text-slate-600">source: {alt.provenance}</p>
            )}
          </div>
        </details>
      )}
    </div>
  );
}

/**
 * An outside factor (a market price, a rate) recorded as acting on a KPI in
 * this picture. It is not a KPI, so it can never appear as a tile above; for
 * a KPI at the edge of the model it is often the only known driver.
 */
function OutsideFactorCard({ port }: { port: TheoryPort }) {
  const detail = [
    port.lag_periods != null ? `About ${port.lag_periods} month${port.lag_periods === 1 ? '' : 's'} before it shows up` : null,
    port.source === 'manual' ? 'Entered by hand, not a live feed' : 'From a market search',
  ].filter(Boolean).join(' · ');
  return (
    <div data-testid="outside-factor" className="rounded-lg border border-slate-800 bg-slate-900/60 px-4 py-3">
      <div className="flex items-center gap-2.5">
        <Globe className="h-3.5 w-3.5 flex-shrink-0 text-slate-400" />
        <p className="min-w-0 flex-1 text-sm font-medium leading-snug text-slate-100">{port.name}</p>
        <span className="flex-shrink-0 rounded border border-slate-600 px-1.5 py-0.5 text-[10px] font-medium text-slate-400">
          Outside factor
        </span>
      </div>
      <p className="mt-1.5 pl-6 text-xs text-slate-400">Acts on {port.linked_kpi_name || port.linked_kpi_id}.</p>
      {(port.current_signal || port.buffer_description) && (
        <details className="mt-1.5 pl-6">
          <summary className="cursor-pointer list-none text-[11px] text-slate-500 hover:text-slate-300">▸ Why</summary>
          <div className="mt-1.5 space-y-1 text-xs text-slate-400">
            {port.current_signal && <p>{port.current_signal}</p>}
            {port.buffer_description && <p className="text-slate-500">{port.buffer_description}</p>}
            <p className="text-slate-500">{detail}</p>
          </div>
        </details>
      )}
    </div>
  );
}

/** KPIs this one feeds into, nearest first, following recorded direction only. */
export function feedsInto(kpiId: string, edges: TheoryLayerPayload['causal_edges']): string[] {
  const next = (id: string) => edges.flatMap(e => {
    if (e.kpi_id === id && e.causal_direction === 'kpi_causes_related') return [[e.related_kpi_id, e.related_kpi_name || e.related_kpi_id]];
    if (e.related_kpi_id === id && e.causal_direction === 'related_causes_kpi') return [[e.kpi_id, e.kpi_name || e.kpi_id]];
    return [];
  });
  const seen = new Set([kpiId]);
  const names: string[] = [];
  let frontier = [kpiId];
  while (frontier.length) {
    const found: string[] = [];
    for (const id of frontier) {
      for (const [nid, name] of next(id)) {
        if (!seen.has(nid)) { seen.add(nid); names.push(name); found.push(nid); }
      }
    }
    frontier = found;
  }
  return names;
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

  // Outside factors and downstream KPIs come from the same registry picture
  // the KPI Drivers page shows. Best-effort: the tiles never wait on it.
  const [layer, setLayer] = useState<TheoryLayerPayload | null>(null);
  useEffect(() => {
    if (!prompt.kpi_id || !clientId) return;
    let cancelled = false;
    getTheoryLayer(prompt.kpi_id, clientId).then(d => { if (!cancelled) setLayer(d); }).catch(() => {});
    return () => { cancelled = true; };
  }, [prompt.kpi_id, clientId]);
  const outsideFactors = layer?.ports ?? [];
  const downstream = layer && prompt.kpi_id ? feedsInto(prompt.kpi_id, layer.causal_edges) : [];

  if (prompt.alternatives.length === 0 && outsideFactors.length === 0 && downstream.length === 0) {
    return (
      <p className="text-xs italic text-slate-500">
        Nothing is recorded as driving {kpiName}, and it is not recorded as feeding into another KPI.
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

      {prompt.alternatives.length === 0 && (
        <p className="text-xs italic text-slate-500">No other KPI is recorded as driving {kpiName}.</p>
      )}

      <div className="space-y-2">
        {prompt.alternatives.map((alt, i) => (
          <EvidenceCard
            key={`${alt.source}-${alt.kpi_id ?? i}`}
            alt={alt}
            dotColor={alt.source === 'causal_graph' ? causalColorFor(alt.kpi_id, ordered) : CAUSAL_PRIMARY_HUE}
            kpiName={kpiName}
            clientId={clientId}
            principalId={principalId}
          />
        ))}
      </div>

      {outsideFactors.length > 0 && (
        <div className="space-y-2">
          {outsideFactors.map(p => <OutsideFactorCard key={p.id || p.name} port={p} />)}
        </div>
      )}

      {downstream.length > 0 && (
        <p data-testid="feeds-into" className="text-xs text-slate-400">
          <span className="text-slate-500">{kpiName} feeds into:</span> {downstream.join(', then ')}
        </p>
      )}

      {prompt.additional_causal_measures_count > 0 && (
        <p className="text-xs italic text-slate-500">
          +{prompt.additional_causal_measures_count} more related driver{prompt.additional_causal_measures_count === 1 ? '' : 's'} checked,
          not shown — ranked lower by current relevance.
        </p>
      )}
    </div>
  );
}

export default CausalNeighbourhoodEvidence;
