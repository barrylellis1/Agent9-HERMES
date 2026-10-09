/**
 * "How your KPIs connect" — pick a KPI, see how it is calculated, what drives
 * it, and which of those links are Tested, Assumed or Calculated.
 *
 * Linked from LeftNav's Workspace group as "KPI Drivers" (route unchanged:
 * /dev/theory-layer). Linked 2026-10-04 once real Value Assurance verdicts
 * had confirmed a link for premium_mix_pct through the normal write-back
 * path; most other KPIs still show mostly assumed links, which the page says
 * in plain words.
 */
import { useEffect, useState } from 'react';
import { TheoryLayerExhibit } from '../components/theory/TheoryLayerExhibit';
import { listKpis } from '../api/client';

const PREFERRED_DEFAULT = 'premium_mix_pct';

export function TheoryLayerDevPage() {
  const clientId = (() => {
    try { return localStorage.getItem('a9_active_client_id') ?? ''; } catch { return ''; }
  })();
  const [kpis, setKpis] = useState<{ id: string; name: string }[]>([]);
  const [kpiId, setKpiId] = useState('');
  const [includeValues, setIncludeValues] = useState(false);

  useEffect(() => {
    if (!clientId) return;
    listKpis(clientId)
      .then((rows) => {
        const list = rows
          .map((k) => ({ id: k.id as string, name: (k.name as string) || (k.id as string) }))
          .sort((a, b) => a.name.localeCompare(b.name));
        setKpis(list);
        setKpiId(list.find((k) => k.id === PREFERRED_DEFAULT)?.id ?? list[0]?.id ?? '');
      })
      .catch(() => setKpis([]));
  }, [clientId]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8 font-sans">
      <header className="max-w-4xl mb-6">
        <h1 className="text-2xl font-bold text-white tracking-tight">How your KPIs connect</h1>
        <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
          How a KPI is calculated, what drives it, and how far each link has been tested.
        </p>
      </header>

      {!clientId ? (
        <p className="text-sm text-slate-500">Sign in to a client to see its KPIs.</p>
      ) : (
        <>
          <div className="max-w-4xl flex flex-wrap items-end gap-4 mb-6">
            <label className="flex flex-col gap-1">
              <span className="text-[11px] uppercase tracking-widest text-slate-500">KPI</span>
              <select
                data-testid="kpi-picker"
                value={kpiId}
                onChange={(e) => setKpiId(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200"
              >
                {kpis.map((k) => <option key={k.id} value={k.id}>{k.name}</option>)}
              </select>
            </label>
            <label className="flex items-center gap-2 pb-1.5 cursor-pointer">
              <input
                type="checkbox"
                checked={includeValues}
                onChange={(e) => setIncludeValues(e.target.checked)}
                className="accent-indigo-500"
              />
              <span className="text-sm text-slate-300">Show current values</span>
            </label>
          </div>

          {kpiId && <TheoryLayerExhibit kpiId={kpiId} clientId={clientId} includeValues={includeValues} />}
        </>
      )}
    </div>
  );
}
