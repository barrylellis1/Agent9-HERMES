/**
 * ConnectionHealthPanel — extracted from RegistryExplorer.tsx (Settings ›
 * Connection Health tab) so it can also be embedded in the onboarding
 * wizard's Day 6 (Validate & Launch) step. No behavior change from the
 * inline version this replaces.
 */
import { useCallback, useEffect, useState } from 'react'
import { Activity, CheckCircle2, Loader2, XCircle } from 'lucide-react'
import {
  type ConnectionHealthResult,
  type ConnectionHealthResponse,
  getConnectionHealth,
  testConnectionHealth,
} from '../api/client'

function StatusBadge({ status }: { status: ConnectionHealthResult['status'] }) {
  if (status === 'ok') return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-severity-opportunity">
      <CheckCircle2 className="w-3.5 h-3.5" /> Connected
    </span>
  )
  if (status === 'error') return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-severity-critical">
      <XCircle className="w-3.5 h-3.5" /> Error
    </span>
  )
  return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-500">
      <Activity className="w-3.5 h-3.5" /> {status}
    </span>
  )
}

export function ConnectionHealthPanel({ clientId }: { clientId?: string }) {
  const [health, setHealth] = useState<ConnectionHealthResponse | null>(null)
  const [probing, setProbing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const data = await getConnectionHealth(clientId)
      setHealth(data)
    } catch (e: any) {
      setError(e.message ?? 'Failed to load health data')
    }
  }, [clientId])

  useEffect(() => { load() }, [load])

  const probe = async () => {
    setProbing(true)
    setError(null)
    try {
      const data = await testConnectionHealth(clientId)
      setHealth(data)
    } catch (e: any) {
      setError(e.message ?? 'Probe failed')
    } finally {
      setProbing(false)
    }
  }

  const results = health?.results ?? []
  const probedAt = health?.probed_at ? new Date(health.probed_at).toLocaleString() : null

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Connection Health</h2>
          <p className="text-sm text-slate-400">
            {probedAt ? `Last probed: ${probedAt}` : 'Not yet probed — click Test All to run.'}
          </p>
        </div>
        <button
          onClick={probe}
          disabled={probing}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white text-sm font-medium"
        >
          {probing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Activity className="w-4 h-4" />}
          {probing ? 'Probing…' : 'Test All Connections'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg border border-severity-critical/30 bg-severity-critical/10 text-severity-critical text-sm">{error}</div>
      )}

      {results.length === 0 && !probing ? (
        <p className="text-sm text-slate-500 italic">No data products found. Click Test All Connections to probe.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left">
                <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Data Product</th>
                <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Client</th>
                <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Source System</th>
                <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Status</th>
                <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Latency</th>
                <th className="pb-2 text-xs font-semibold text-slate-400 uppercase tracking-wide">Error</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r) => (
                <tr key={r.data_product_id} className="border-b border-slate-800/60 hover:bg-slate-800/20">
                  <td className="py-2.5 pr-4 text-white font-medium">{r.name ?? r.data_product_id}</td>
                  <td className="py-2.5 pr-4 text-slate-400 font-mono text-xs">{r.client_id ?? '—'}</td>
                  <td className="py-2.5 pr-4">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-800 text-slate-300 font-mono">{r.source_system}</span>
                  </td>
                  <td className="py-2.5 pr-4"><StatusBadge status={r.status} /></td>
                  <td className="py-2.5 pr-4 text-slate-400 text-xs">{r.latency_ms > 0 ? `${r.latency_ms} ms` : '—'}</td>
                  <td className="py-2.5 text-severity-critical text-xs truncate max-w-[300px]" title={r.error ?? undefined}>{r.error ?? (r.note ?? '—')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
