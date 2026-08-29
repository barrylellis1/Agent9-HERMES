/**
 * SliceValidityPanel — docs/architecture/kpi_semantic_contract.md §4.
 *
 * Sibling to ConnectionHealthPanel.tsx, same dual-use shape: embedded in the
 * onboarding wizard's Day 6 (Validate & Launch) step AND in Settings ›
 * Maintenance, so the same check that runs once at onboarding can be
 * re-run later when a client's data model changes.
 *
 * One real difference from ConnectionHealthPanel: this is scoped to ONE
 * caller-chosen KPI, not an automatic scan of everything — a human picks a
 * KPI and clicks Run, deliberately, matching the "human-triggered
 * diagnostic, not a batch job" design in DEVELOPMENT_PLAN.md -> Phase 15 ->
 * Stage I. Loading the KPI list itself is read-only and automatic; running
 * the actual check is not.
 *
 * Not purely advisory (as of 2026-08-16) — A9_Deep_Analysis_Agent now
 * excludes every dimension in not_sliceable_by from analysis before running
 * (docs/architecture/kpi_semantic_contract.md §4.5) and reports each
 * exclusion on DeepAnalysisResponse.dimensions_excluded, so this panel is no
 * longer just a display: what a human runs here changes what DA will and
 * won't cut this KPI by on every subsequent run. Onboarding/UI flows
 * themselves still aren't gated by it — only DA's own dimension selection is.
 */
import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2, Loader2, ShieldAlert } from 'lucide-react'
import {
  type SliceValidityResponse,
  getSliceValidity,
  listKpis,
  testSliceValidity,
} from '../api/client'

function VerdictBadge({ verdict }: { verdict: SliceValidityResponse['completeness_results'][number]['verdict'] }) {
  if (verdict === 'ok') return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-severity-opportunity">
      <CheckCircle2 className="w-3.5 h-3.5" /> ok
    </span>
  )
  if (verdict === 'INVALID') return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-severity-critical">
      <ShieldAlert className="w-3.5 h-3.5" /> INVALID
    </span>
  )
  if (verdict === 'degraded') return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-severity-warning">
      <AlertTriangle className="w-3.5 h-3.5" /> degraded
    </span>
  )
  return <span className="text-xs font-medium text-slate-500">unknown</span>
}

function ResultsTable({
  title, subtitle, results, countsLabel,
}: {
  title: string
  subtitle: string
  results: SliceValidityResponse['completeness_results']
  countsLabel: string
}) {
  if (results.length === 0) return null
  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-white mb-0.5">{title}</h3>
      <p className="text-xs text-slate-500 mb-2">{subtitle}</p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left">
              <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Dimension</th>
              <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Coverage</th>
              <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Verdict</th>
              <th className="pb-2 text-xs font-semibold text-slate-400 uppercase tracking-wide">{countsLabel}</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r) => (
              <tr key={r.dimension} className="border-b border-slate-800/60 hover:bg-slate-800/20">
                <td className="py-2.5 pr-4 text-white font-medium">{r.dimension}</td>
                <td className="py-2.5 pr-4 text-slate-400 text-xs">{(r.coverage * 100).toFixed(0)}%</td>
                <td className="py-2.5 pr-4"><VerdictBadge verdict={r.verdict} /></td>
                <td className="py-2.5 text-slate-400 text-xs font-mono">
                  {Object.entries(r.counts).map(([c, n]) => `${c}=${n}`).join('  ')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// A stale "last checked" reads as current unless it's called out — the
// primary false-confidence failure mode this feature exists to prevent
// (see the plan's premortem #2). Escalate the visual treatment past 90 days.
function staleness(checkedAt: string | null): { label: string; className: string } {
  if (!checkedAt) return { label: 'Never checked', className: 'text-slate-500' }
  const days = (Date.now() - new Date(checkedAt).getTime()) / 86_400_000
  const label = `Last checked: ${new Date(checkedAt).toLocaleString()}`
  if (days > 90) return { label: `${label} (over 90 days ago)`, className: 'text-severity-warning font-medium' }
  return { label, className: 'text-slate-400' }
}

export function SliceValidityPanel({ clientId }: { clientId?: string }) {
  const [kpis, setKpis] = useState<{ id: string; name?: string }[]>([])
  const [selectedKpiId, setSelectedKpiId] = useState<string>('')
  const [result, setResult] = useState<SliceValidityResponse | null>(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listKpis(clientId)
      .then((list) => {
        setKpis(list)
        if (list.length > 0 && !selectedKpiId) setSelectedKpiId(list[0].id)
      })
      .catch((e: any) => setError(e.message ?? 'Failed to load KPI list'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clientId])

  const loadCached = useCallback(async (kpiId: string) => {
    if (!kpiId || !clientId) return
    try {
      const data = await getSliceValidity(kpiId, clientId)
      setResult(data)
    } catch (e: any) {
      setError(e.message ?? 'Failed to load slice-validity result')
    }
  }, [clientId])

  useEffect(() => { loadCached(selectedKpiId) }, [selectedKpiId, loadCached])

  const runCheck = async () => {
    if (!selectedKpiId || !clientId) return
    setRunning(true)
    setError(null)
    try {
      const data = await testSliceValidity(selectedKpiId, clientId)
      setResult(data)
    } catch (e: any) {
      setError(e.message ?? 'Slice-validity check failed')
    } finally {
      setRunning(false)
    }
  }

  const completenessResults = result?.completeness_results ?? []
  const crossComponentResults = result?.cross_component_results ?? []
  const notSliceableBy = result?.not_sliceable_by ?? []
  const componentsUsed = result?.components_used ?? []
  const stale = staleness(result?.checked_at ?? null)
  const hasAnyResults = completenessResults.length > 0 || crossComponentResults.length > 0

  return (
    <div>
      <div className="flex items-center justify-between mb-4 gap-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Slice Validity</h2>
          <p className={`text-sm ${stale.className}`}>{stale.label}</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={selectedKpiId}
            onChange={(e) => setSelectedKpiId(e.target.value)}
            className="rounded-lg bg-slate-800 border border-slate-700 text-white text-sm px-3 py-2"
          >
            {kpis.length === 0 && <option value="">No KPIs found</option>}
            {kpis.map((k) => (
              <option key={k.id} value={k.id}>{k.name ?? k.id}</option>
            ))}
          </select>
          <button
            onClick={runCheck}
            disabled={running || !selectedKpiId}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white text-sm font-medium"
          >
            {running ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldAlert className="w-4 h-4" />}
            {running ? 'Checking…' : 'Run Check'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg border border-severity-critical/30 bg-severity-critical/10 text-severity-critical text-sm">{error}</div>
      )}

      {result?.status === 'error' && result.error_message && (
        <div className="mb-4 p-3 rounded-lg border border-severity-critical/30 bg-severity-critical/10 text-severity-critical text-sm">{result.error_message}</div>
      )}

      {notSliceableBy.length > 0 && (
        <div className="mb-4 p-3 rounded-lg border border-severity-critical/30 bg-severity-critical/10 text-severity-critical text-sm">
          <span className="font-semibold">Deep Analysis will not slice this KPI by:</span>{' '}
          {notSliceableBy.map((e) => e.dimension).join(', ')} — either some rows have no value for the dimension at
          all, or the component measures don't reach it the same way. Either way, slicing by it produces a
          confident, wrong number, so Deep Analysis excludes these dimensions before it runs (§4.5).
          <ul className="mt-2 space-y-0.5">
            {notSliceableBy.map((e) => (
              <li key={e.dimension} className="text-xs text-severity-critical/80">
                <span className="font-mono">{e.dimension}</span> —{' '}
                {e.reason_class === 'structural' ? 'structural (a permanent fact about how this business’s data works)' : 'data gap in this client’s source system — worth flagging to whoever owns their data pipeline'}
                {e.note ? `: ${e.note}` : ''}
              </li>
            ))}
          </ul>
        </div>
      )}

      {componentsUsed.length > 0 && (
        <p className="text-xs text-slate-500 mb-4">
          Checked as built from: <span className="font-mono text-slate-400">{componentsUsed.join(', ')}</span>
        </p>
      )}

      {!hasAnyResults && !running ? (
        <p className="text-sm text-slate-500 italic">
          {selectedKpiId ? 'Not yet checked — click Run Check.' : 'Select a KPI to check.'}
        </p>
      ) : (
        <>
          <ResultsTable
            title="Completeness"
            subtitle="Of this KPI's own rows, what fraction have a value for this dimension at all — applies whether the KPI is a plain sum or built from several components."
            results={completenessResults}
            countsLabel="Rows (total / with value)"
          />
          <ResultsTable
            title="Cross-Component Coverage"
            subtitle="Do this KPI's component measures (e.g. Revenue vs COGS) reach the same values for this dimension — only meaningful with 2+ components."
            results={crossComponentResults}
            countsLabel="Distinct values per component"
          />
        </>
      )}
    </div>
  )
}
