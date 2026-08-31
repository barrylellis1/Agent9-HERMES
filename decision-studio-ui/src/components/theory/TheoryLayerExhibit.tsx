/**
 * TheoryLayerExhibit — the theory layer rendered as one conditional stack
 * (Phase 17, Stage 6). DEV-ONLY PROTOTYPE, not linked into production nav.
 *
 * STRUCTURE follows docs/architecture/kpi_relationship_basis_design.md §5,
 * which explicitly REJECTED the fixed four-quadrant grid Phase 17's own
 * headline describes: "a rigid grid reserving space for all four concepts on
 * every KPI recreates exactly that failure at the panel level" — Spine only
 * exists for an FI-anchored KPI, Ports only when MA's conflict fires. So
 * Spine → Edges → Ports stack full-width and render ONLY with real content.
 *
 * ASSUMPTIONS IS NOT A SECTION, deliberately. Same §5: "Assumptions was never
 * a fourth section to begin with... A holding/breaking verdict is a marker ON
 * an edge, not independent content with its own chart." It appears here as a
 * per-card verdict badge, and while T3 grades assumptions per SOLUTION (not
 * per edge) the badge honestly reads "verdict pending" rather than being
 * silently omitted — §5's own stated default.
 *
 * THE VISUAL GRAMMAR — certainty is the primary visual variable, because
 * "the difference is not how the recommendation READS, it is what can be
 * CHECKED" (DEVELOPMENT_PLAN.md Phase 17). Line/border style encodes the
 * provenance ladder (theory_layer_design.md §4):
 *
 *   solid   = certain      — accounting identity (arithmetic) or DiD-tested
 *   dashed  = asserted     — a domain fact someone blessed, not tested
 *   dotted  = assumed      — industry template, or an external port
 *
 * NUMBERS LIVE ONLY ON THE SPINE. The annotations carry words and grades,
 * never invented figures. This is the one rule that keeps the qualitative
 * layers from borrowing the arithmetic's authority — Phase 17's own warning
 * that "a wrong number in a diagram is harder to challenge than one in a
 * table; the picture carries authority the arithmetic has not earned."
 */
import { useEffect, useState } from 'react';
import {
  Loader2, CheckCircle2, AlertTriangle, ArrowDown, Plug, GitBranch, Calculator,
} from 'lucide-react';
import {
  getTheoryLayer, TheoryLayerPayload, TheoryCausalEdge, TheoryPort, TheorySpineNode, TheorySpineEdge,
} from '../../api/client';

interface Props {
  kpiId: string;
  clientId: string;
  includeValues?: boolean;
}

/** Certainty tier — the single encoding every card and line derives from. */
type Tier = 'certain' | 'asserted' | 'assumed';

function edgeTier(e: TheoryCausalEdge): Tier {
  if (e.basis === 'accounting_identity') return 'certain';
  if (e.causal_rung === 'intervention_tested') return 'certain';
  if (e.provenance === 'template') return 'assumed';
  return 'asserted';
}

const TIER_STYLE: Record<Tier, { border: string; label: string; chip: string }> = {
  certain: {
    border: 'border-solid border-slate-500',
    label: 'text-slate-200',
    chip: 'bg-slate-700/60 text-slate-200',
  },
  asserted: {
    border: 'border-dashed border-slate-600',
    label: 'text-slate-300',
    chip: 'bg-slate-800 text-slate-400',
  },
  assumed: {
    border: 'border-dotted border-slate-700',
    label: 'text-slate-400',
    chip: 'bg-slate-800/60 text-slate-500',
  },
};

function fmtValue(n: TheorySpineNode): string {
  if (n.value === null || n.value === undefined) return '—';
  if (n.unit_class === 'ratio') return `${n.value.toFixed(2)}%`;
  if (Math.abs(n.value) >= 1_000_000) return `$${(n.value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(n.value) >= 1_000) return `$${(n.value / 1_000).toFixed(1)}K`;
  return `${n.value}`;
}

/** Section shell — never renders when it has nothing real to show (§5). */
function Section({
  title, kind, icon, children,
}: {
  title: string; kind: string; icon: React.ReactNode; children: React.ReactNode;
}) {
  return (
    <section className="border-t border-slate-800 pt-5">
      <header className="flex items-baseline gap-2 mb-3">
        <span className="text-slate-500">{icon}</span>
        <h3 className="text-sm font-semibold tracking-wide text-white uppercase">{title}</h3>
        <span className="text-[11px] uppercase tracking-widest text-slate-600">{kind}</span>
      </header>
      {children}
    </section>
  );
}

function SpineNode({ node, role }: { node: TheorySpineNode; role?: string }) {
  return (
    <div className="border border-solid border-slate-600 rounded-lg bg-slate-900 px-3 py-2 min-w-[160px]">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-xs text-slate-400 font-mono">{node.kpi_id}</span>
        {role && <span className="text-[10px] uppercase tracking-wider text-slate-600">{role}</span>}
      </div>
      <div className="text-lg font-semibold text-white tabular-nums">{fmtValue(node)}</div>
      {node.additive_across_dimensions === false && (
        <div className="text-[10px] text-severity-warning/80 mt-0.5">
          not additive · {node.aggregation_method || 'weighted'}
        </div>
      )}
    </div>
  );
}

/**
 * The Spine's chart: a VARIANCE bridge (waterfall), not a composition bridge.
 *
 * kpi_relationship_basis_design.md §4 rejected the composition shape by name —
 * "the framing question is 'why did this move, and is this the right KPI to be
 * looking at' — inherently about the DELTA between periods, not the current
 * value's arithmetic. A composition bridge doesn't answer that at all."
 *
 * Bars are drawn from the effects the backend computed by sequential
 * substitution, which close on the observed move with no residual for two
 * inputs. When `exact` is false the note is shown rather than suppressed: an
 * order-dependent split presented as exact is precisely the fabricated
 * precision this whole design note exists to prevent.
 */
function VarianceBridge({
  bridge, nodes, unit,
}: {
  bridge: NonNullable<TheoryLayerPayload['spine']['variance_bridge']>;
  nodes: TheorySpineNode[];
  unit: string;
}) {
  const nameOf = (id: string) => nodes.find((n) => n.kpi_id === id)?.kpi_id || id;
  const magnitudes = [
    Math.abs(bridge.prior_value), Math.abs(bridge.current_value),
    ...bridge.effects.map((e) => Math.abs(e.effect)),
  ];
  const scale = Math.max(...magnitudes, 1);
  const pct = (v: number) => `${Math.max((Math.abs(v) / scale) * 100, 1.5)}%`;

  const rows: { label: string; value: number; kind: 'anchor' | 'effect' }[] = [
    { label: 'prior period', value: bridge.prior_value, kind: 'anchor' },
    ...bridge.effects.map((e) => ({ label: nameOf(e.kpi_id), value: e.effect, kind: 'effect' as const })),
    { label: 'current period', value: bridge.current_value, kind: 'anchor' },
  ];

  return (
    <div className="space-y-1.5">
      {rows.map((r, i) => {
        const positive = r.value >= 0;
        return (
          <div key={i} className="flex items-center gap-3">
            <span className={`w-36 shrink-0 text-xs font-mono truncate ${
              r.kind === 'anchor' ? 'text-slate-300' : 'text-slate-400'
            }`}>
              {r.label}
            </span>
            <div className="flex-1 h-5 flex items-center">
              <div
                className={`h-3 rounded-sm ${
                  r.kind === 'anchor'
                    ? 'bg-slate-600'
                    : positive ? 'bg-severity-opportunity/70' : 'bg-severity-critical/70'
                }`}
                style={{ width: pct(r.value) }}
              />
            </div>
            <span className={`w-24 shrink-0 text-right text-sm tabular-nums font-semibold ${
              r.kind === 'anchor'
                ? 'text-white'
                : positive ? 'text-severity-opportunity' : 'text-severity-critical'
            }`}>
              {r.kind === 'effect' && positive ? '+' : ''}
              {r.value.toFixed(2)}{unit}
            </span>
          </div>
        );
      })}
      <div className="pt-2 mt-1 border-t border-slate-800 flex items-baseline gap-2 text-xs">
        <span className="text-slate-500">observed move</span>
        <span className={`font-semibold tabular-nums ${
          bridge.total_move >= 0 ? 'text-severity-opportunity' : 'text-severity-critical'
        }`}>
          {bridge.total_move >= 0 ? '+' : ''}{bridge.total_move.toFixed(2)}{unit}
        </span>
        {bridge.exact ? (
          <span className="text-slate-600">
            · effects close exactly (residual {bridge.residual.toFixed(4)}{unit})
          </span>
        ) : (
          <span className="text-severity-warning/80">· {bridge.note}</span>
        )}
      </div>
    </div>
  );
}

/**
 * One level of the spine's STRUCTURE, rendered at its real depth.
 *
 * Kept alongside the bridge above, not instead of it: the bridge answers "why
 * did it move", the structure answers "what is it made of, and does that
 * reconcile" — §4 rejected composition as *the chart*, not as context beneath
 * one. Shown collapsed-by-default so the bridge stays the headline.
 *
 * `seen` guards against a cycle in the decomposition data producing infinite
 * recursion — the provider's own get_full_tree applies the same guard
 * server-side, and a diagram is the worst place to discover a data-entry loop.
 */
function SpineBranch({
  kpiId, nodes, edges, depth, seen,
}: {
  kpiId: string;
  nodes: TheorySpineNode[];
  edges: TheorySpineEdge[];
  depth: number;
  seen: Set<string>;
}) {
  const node = nodes.find((n) => n.kpi_id === kpiId);
  if (!node || seen.has(kpiId) || depth > 4) return null;
  const nextSeen = new Set(seen).add(kpiId);
  const childEdges = edges.filter((e) => e.parent_kpi_id === kpiId);

  // A ratio edge's denominator is a real participant in the arithmetic but is
  // NOT a child branch — showing it as one would claim net_revenue decomposes
  // out of gross_margin_pct, which it does not.
  const ratioEdge = childEdges.find((e) => e.operation === 'ratio');
  const denominator = ratioEdge?.weight_kpi_id
    ? nodes.find((n) => n.kpi_id === ratioEdge.weight_kpi_id)
    : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-end gap-2 flex-wrap">
        <SpineNode node={node} role={depth === 0 ? 'parent' : undefined} />
        {denominator && (
          <>
            <span className="text-slate-600 text-lg pb-2">÷</span>
            <SpineNode node={denominator} role="denominator" />
          </>
        )}
      </div>
      {childEdges.length > 0 && (
        <div className="pl-5 border-l border-slate-800 ml-3 pt-1 flex flex-col gap-1.5">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-widest text-slate-600">
            <ArrowDown className="w-3 h-3" />
            {ratioEdge ? 'ratio of' : 'sums to'}
          </div>
          {childEdges.map((e) => (
            <div key={e.child_kpi_id} className="flex items-start gap-2">
              {e.operation === 'linear' && (
                <span className="text-slate-500 text-sm pt-2 w-3 shrink-0">
                  {e.sign === -1 ? '−' : '+'}
                </span>
              )}
              <SpineBranch
                kpiId={e.child_kpi_id}
                nodes={nodes}
                edges={edges}
                depth={depth + 1}
                seen={nextSeen}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CausalEdgeCard({ edge }: { edge: TheoryCausalEdge }) {
  const tier = edgeTier(edge);
  const s = TIER_STYLE[tier];
  const arrow = tier === 'certain' ? '——▸' : tier === 'asserted' ? '– –▸' : '⋯⋯▸';
  return (
    <div className={`border ${s.border} rounded-lg bg-slate-900/60 p-3`}>
      <div className="flex items-center gap-2 flex-wrap">
        <span className={`font-mono text-xs ${s.label}`}>{edge.kpi_id}</span>
        <span className="text-slate-600 text-xs">{arrow}</span>
        <span className={`font-mono text-xs ${s.label}`}>{edge.related_kpi_id}</span>
        <span className={`text-[10px] px-1.5 py-0.5 rounded ${s.chip} uppercase tracking-wider`}>
          {edge.basis === 'accounting_identity' ? 'identity · certain' : tier}
        </span>
        {edge.hops > 1 && (
          <span className="text-[10px] text-slate-600">{edge.hops} hops</span>
        )}
      </div>
      {edge.mechanism && (
        <p className="text-xs text-slate-400 mt-2 leading-relaxed">{edge.mechanism}</p>
      )}
      <div className="flex items-center gap-3 mt-2 text-[10px] text-slate-600">
        {edge.basis === 'accounting_identity' ? (
          <span>true by construction — no confidence applies to arithmetic</span>
        ) : (
          <>
            <span>{edge.provenance}</span>
            {edge.confidence && <span>· {edge.confidence} confidence</span>}
            {edge.lag_periods !== null && <span>· {edge.lag_periods}mo lag</span>}
            {/* §5: Assumptions is a MARKER, never a section. */}
            <span className="text-slate-700">· ○ verdict pending</span>
          </>
        )}
      </div>
    </div>
  );
}

function PortCard({ port }: { port: TheoryPort }) {
  return (
    <div className="border border-dotted border-severity-warning/60 rounded-lg bg-severity-warning/10 p-3">
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-xs font-semibold text-severity-warning/90">{port.name}</span>
        <span className="text-slate-600 text-xs">⋯⋯▸</span>
        <span className="font-mono text-xs text-slate-300">{port.linked_kpi_id}</span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-severity-warning/30 text-severity-warning/80 uppercase tracking-wider">
          {port.port_type.replace(/_/g, ' ')}
        </span>
      </div>
      {port.current_signal && (
        <p className="text-xs text-slate-400 mt-2 leading-relaxed">{port.current_signal}</p>
      )}
      <div className="flex flex-wrap items-center gap-3 mt-2 text-[10px] text-slate-600">
        {port.lag_periods !== null && <span>{port.lag_periods}mo lag</span>}
        {port.buffer_description && (
          <span className="max-w-xl">· buffer: {port.buffer_description}</span>
        )}
        <span>· {port.source === 'manual' ? 'hand-entered, not live-queried' : 'market query'}</span>
      </div>
    </div>
  );
}

export function TheoryLayerExhibit({ kpiId, clientId, includeValues = false }: Props) {
  const [data, setData] = useState<TheoryLayerPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError(null);
    getTheoryLayer(kpiId, clientId, includeValues)
      .then((d) => { if (!cancelled) setData(d); })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load theory layer');
      });
    return () => { cancelled = true; };
  }, [kpiId, clientId, includeValues]);

  if (error) {
    return (
      <div className="p-4 border border-severity-critical/30 bg-severity-critical/10 rounded-lg text-sm text-severity-critical">
        {error}
      </div>
    );
  }
  if (!data) {
    return (
      <div className="flex items-center gap-2 text-slate-500 text-sm py-12 justify-center">
        <Loader2 className="w-4 h-4 animate-spin" /> Assembling theory layer…
      </div>
    );
  }

  const { spine, causal_edges, ports, epistemic_summary: es } = data;
  const identities = causal_edges.filter((e) => e.basis === 'accounting_identity');
  const claims = causal_edges.filter((e) => e.basis !== 'accounting_identity');
  const primary = spine.nodes.find((n) => n.kpi_id === data.kpi_id);

  return (
    <div className="bg-slate-950 text-slate-200 rounded-xl border border-slate-800 p-6 space-y-5 max-w-4xl">
      {/* ---- Header + epistemic summary --------------------------------- */}
      <header>
        <div className="flex items-baseline gap-3 flex-wrap">
          <h2 className="text-lg font-bold text-white">{data.kpi_name}</h2>
          <span className="text-xs text-slate-500 font-mono">{data.client_id}</span>
        </div>
        {/* Makes VERIFIABILITY visible — the exhibit's stated job. Identities
            are counted apart from causal claims on purpose: arithmetic is not
            verified theory, and folding it in would inflate "confirmed". */}
        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
          <span className="text-slate-300">
            <strong className="text-white tabular-nums">{es.identities}</strong> arithmetic identities
            <span className="text-slate-600"> (certain)</span>
          </span>
          <span className="text-slate-600">·</span>
          <span className="text-slate-300">
            <strong className="text-white tabular-nums">{es.causal_claims}</strong> causal claims:
            <span className="text-slate-400"> {es.tested} tested</span>
            <span className="text-slate-500"> · {es.asserted} asserted</span>
            <span className="text-slate-600"> · {es.template} template</span>
          </span>
        </div>
        {!es.density_gate_passed && (
          <p className="mt-2 text-[11px] text-severity-warning/70 leading-relaxed">
            <AlertTriangle className="w-3 h-3 inline mr-1 -mt-0.5" />
            Density gate not passed — tested edges do not yet outnumber unconfirmed ones.
            This bar is cleared by accumulated Value Assurance verdicts, never by seeding.
          </p>
        )}
      </header>

      {/* ---- 1. CORE SPINE (conditional) -------------------------------- */}
      {spine.edges.length > 0 && primary && (
        <Section title="Core Spine" kind="arithmetic" icon={<Calculator className="w-4 h-4" />}>
          {/* THE CHART is the variance bridge (§4). Composition is context
              underneath it, collapsed — never the headline. */}
          {spine.variance_bridge ? (
            <VarianceBridge
              bridge={spine.variance_bridge}
              nodes={spine.nodes}
              unit={primary.unit_class === 'ratio' ? 'pp' : ''}
            />
          ) : (
            <p className="text-[11px] text-slate-600 mb-3">
              {spine.reconciliation
                ? 'Variance bridge unavailable — prior-period values missing, so the move cannot be decomposed.'
                : 'Structure only — enable live values to decompose the period-over-period move.'}
            </p>
          )}

          <details className="mt-4 group">
            <summary className="text-[11px] uppercase tracking-widest text-slate-600 cursor-pointer hover:text-slate-400 list-none">
              ▸ composition (what it is made of)
            </summary>
            <div className="mt-3">
              {/* Rendered by ACTUAL depth, not flattened. The lubricants tree
                  is two levels (gross_margin_pct = ratio(gross_profit,
                  net_revenue); gross_profit = net_revenue - cogs) and an
                  earlier flat render showed net_revenue/cogs as direct
                  children of gross_margin_pct. A wrong STRUCTURE in a diagram
                  is the same failure class Phase 17 names for a wrong number. */}
              <SpineBranch
                kpiId={data.kpi_id}
                nodes={spine.nodes}
                edges={spine.edges}
                depth={0}
                seen={new Set()}
              />
              {spine.reconciliation ? (
                <div className={`mt-3 text-xs flex items-start gap-1.5 ${
                  spine.reconciliation.ok ? 'text-severity-opportunity/80' : 'text-severity-critical'
                }`}>
                  {spine.reconciliation.ok
                    ? <><CheckCircle2 className="w-3.5 h-3.5 mt-px" /> children reconcile to parent</>
                    : <><AlertTriangle className="w-3.5 h-3.5 mt-px" /> {spine.reconciliation.detail}</>}
                </div>
              ) : (
                <p className="mt-3 text-[11px] text-slate-600">
                  Live values not requested, so reconciliation is unchecked.
                </p>
              )}
            </div>
          </details>
        </Section>
      )}

      {/* ---- 2. CAUSAL EDGES (conditional) ------------------------------ */}
      {causal_edges.length > 0 && (
        <Section title="Causal Edges" kind="theory" icon={<GitBranch className="w-4 h-4" />}>
          <div className="space-y-2">
            {identities.length > 0 && (
              <>
                <p className="text-[11px] text-slate-600 uppercase tracking-widest">
                  True by construction
                </p>
                {identities.map((e) => (
                  <CausalEdgeCard key={`${e.kpi_id}-${e.related_kpi_id}`} edge={e} />
                ))}
              </>
            )}
            {claims.length > 0 && (
              <>
                <p className="text-[11px] text-slate-600 uppercase tracking-widest pt-2">
                  Empirical claims
                </p>
                {claims.map((e) => (
                  <CausalEdgeCard key={`${e.kpi_id}-${e.related_kpi_id}`} edge={e} />
                ))}
              </>
            )}
          </div>
        </Section>
      )}

      {/* ---- 3. EXTERNAL PORTS (conditional) ---------------------------- */}
      {ports.length > 0 && (
        <Section title="External Ports" kind="outside the ledger" icon={<Plug className="w-4 h-4" />}>
          <div className="space-y-2">
            {ports.map((p) => <PortCard key={p.id || p.name} port={p} />)}
          </div>
        </Section>
      )}

      {/* ---- Honest notes ----------------------------------------------- */}
      {data.notes.length > 0 && (
        <footer className="border-t border-slate-800 pt-3 space-y-1">
          {data.notes.map((n, i) => (
            <p key={i} className="text-[11px] text-slate-600 leading-relaxed">{n}</p>
          ))}
        </footer>
      )}
    </div>
  );
}
