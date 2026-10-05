/**
 * TheoryLayerDevPage — harness for the Phase 17 theory-layer exhibit.
 *
 * Linked into LeftNav.tsx's Workspace group (2026-10-04), after an
 * orchestrated batch of real SA->DA->SF->approve->evaluate cycles
 * (scripts/orchestrate_reliability_demo.py) genuinely cleared the Causal
 * Edges density gate for `premium_mix_pct` -- confirmed `gross_margin_pct
 * <-> premium_mix_pct` as `intervention_tested`/`va_validated` through the
 * real write-back mechanism (a9_value_assurance_agent.py's
 * _confirm_causal_edge_from_verdict), not seeded. DEVELOPMENT_PLAN.md Phase
 * 17's delivery rule ("do not ship a partial four-panel layout... either all
 * four sections carry content, or the exhibit stays off") is the reason this
 * stayed unlinked until there was a real KPI to point at -- not a blanket
 * "never link this" rule. Most other KPIs still show an unpassed gate; this
 * page is still a raw KPI-picker harness, not production-styled chrome, so
 * the banner below is softened, not removed.
 *
 * Previously reachable only by typing /dev/theory-layer directly; now also
 * linked from nav, same URL.
 */
import { useState } from 'react';
import { TheoryLayerExhibit } from '../components/theory/TheoryLayerExhibit';

const SAMPLE_KPIS = ['premium_mix_pct', 'gross_margin_pct', 'gross_profit', 'net_revenue', 'cogs'];

export function TheoryLayerDevPage() {
  // premium_mix_pct is the default: it's the one KPI with a genuinely
  // cleared density gate today, per the header comment above.
  const [kpiId, setKpiId] = useState('premium_mix_pct');
  const [clientId, setClientId] = useState('lubricants');
  const [includeValues, setIncludeValues] = useState(false);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8 font-sans">
      <header className="max-w-4xl mb-6">
        <div className="inline-flex items-center gap-2 px-2 py-1 rounded bg-severity-warning/30 border border-severity-warning/50 mb-3">
          <span className="text-[10px] uppercase tracking-widest text-severity-warning/90 font-semibold">
            Early exhibit — real data where the density gate has cleared, raw harness chrome everywhere else
          </span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Theory Layer Exhibit</h1>
        <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
          Conditional stack per <span className="font-mono text-xs">kpi_relationship_basis_design.md §5</span> —
          Spine, Edges and Ports render only when they carry real content; Assumptions is a
          per-card marker, never its own section.
        </p>
      </header>

      <div className="max-w-4xl flex flex-wrap items-end gap-4 mb-6">
        <label className="flex flex-col gap-1">
          <span className="text-[11px] uppercase tracking-widest text-slate-500">KPI</span>
          <select
            value={kpiId}
            onChange={(e) => setKpiId(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200"
          >
            {SAMPLE_KPIS.map((k) => <option key={k} value={k}>{k}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-[11px] uppercase tracking-widest text-slate-500">Client</span>
          <input
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200"
          />
        </label>
        <label className="flex items-center gap-2 pb-1.5 cursor-pointer">
          <input
            type="checkbox"
            checked={includeValues}
            onChange={(e) => setIncludeValues(e.target.checked)}
            className="accent-indigo-500"
          />
          <span className="text-sm text-slate-300">
            Fetch live values
            <span className="text-slate-600 text-xs"> (real warehouse queries)</span>
          </span>
        </label>
      </div>

      <TheoryLayerExhibit kpiId={kpiId} clientId={clientId} includeValues={includeValues} />
    </div>
  );
}
