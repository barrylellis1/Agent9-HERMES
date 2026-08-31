/**
 * TheoryLayerDevPage — DEV-ONLY harness for the Phase 17 theory-layer exhibit.
 *
 * NOT linked from production navigation, deliberately. DEVELOPMENT_PLAN.md
 * Phase 17's delivery rule: "Do not ship a partial four-panel layout... Either
 * all four sections carry content for the client being demonstrated, or the
 * exhibit stays off." The Causal Edges density gate is not passed for any
 * client yet (0 tested edges), and that bar is cleared by accumulated VA
 * verdicts over real use — never by seeding. So this route exists to prove the
 * rendering works end-to-end against real data, without putting the exhibit in
 * front of anyone as though it were finished.
 *
 * Reachable only by typing the URL: /dev/theory-layer
 */
import { useState } from 'react';
import { TheoryLayerExhibit } from '../components/theory/TheoryLayerExhibit';

const SAMPLE_KPIS = ['gross_margin_pct', 'gross_profit', 'net_revenue', 'cogs'];

export function TheoryLayerDevPage() {
  const [kpiId, setKpiId] = useState('gross_margin_pct');
  const [clientId, setClientId] = useState('lubricants');
  const [includeValues, setIncludeValues] = useState(false);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8 font-sans">
      <header className="max-w-4xl mb-6">
        <div className="inline-flex items-center gap-2 px-2 py-1 rounded bg-severity-warning/30 border border-severity-warning/50 mb-3">
          <span className="text-[10px] uppercase tracking-widest text-severity-warning/90 font-semibold">
            Dev prototype — not shipped
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
