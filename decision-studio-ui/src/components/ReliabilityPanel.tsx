/**
 * ReliabilityPanel — Settings > Workspace > Reliability. The operator surface
 * for the stage-wise reliability panel (docs/architecture/audit_event_system_
 * design.md), built 2026-10-03 after confirming the backend (6 reliability.*
 * signals, the audit_events table, the admin read/sweep endpoints) was fully
 * wired and tested but had NO UI anywhere — a human with curl and the admin
 * key could read this table; nobody using the product could.
 *
 * Deliberately listed ahead of Connection Health and Slice Validity in the
 * Workspace nav group (docs/DEVELOPMENT_BACKLOG.md's "Cross-view: Reliability
 * signal surfaces" calls this panel their parent) — those two ARE two of this
 * panel's own five stage-wise signals (reliability.slice_validity reuses the
 * Slice Validity check directly), so this page links out to both rather than
 * re-rendering them; LeftNav.tsx has no actual parent/child nesting to put
 * them literally inside this one.
 *
 * AUTH: this calls GET /api/v1/admin/audit-events, the X-Admin-Key gated,
 * cross-tenant ops endpoint — the one surface in this codebase where that is
 * the right call, because "fleet-level rates across every client" is
 * genuinely privileged and nothing else here needs it. The key is typed in
 * by the operator each session and held only in sessionStorage; it is NEVER
 * baked into the shipped JS bundle the way an env-var default would be —
 * anyone who opens devtools on a production bundle can read a bundled
 * constant, which would defeat the entire point of X-Admin-Key gating the
 * registry-reload and retention-sweep endpoints too.
 */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { KeyRound, Loader2, RefreshCw, ShieldAlert } from 'lucide-react'
import { type AuditEventRecord, getAuditEventsAdmin, listClients } from '../api/client'
import { OutcomeBadge } from './reliability/OutcomeBadge'
import { RELIABILITY_EVENT_TYPE_LABELS as EVENT_TYPE_LABELS } from './reliability/eventTypeLabels'

const SESSION_KEY = 'a9_reliability_admin_key'

interface EventTypeRate {
  eventType: string
  pass: number
  fail: number
  abstain: number
  // Checked excludes outcome=null (narrative events with no verdict) from
  // both numerator and denominator — same "absent ≠ pass" discipline
  // src/analysis/ and the reliability signals themselves use throughout.
  checked: number
}

function summarizeByEventType(events: AuditEventRecord[]): EventTypeRate[] {
  const byType = new Map<string, EventTypeRate>()
  for (const e of events) {
    if (!e.event_type.startsWith('reliability.')) continue
    const row = byType.get(e.event_type) ?? { eventType: e.event_type, pass: 0, fail: 0, abstain: 0, checked: 0 }
    if (e.outcome === 'pass') { row.pass++; row.checked++ }
    else if (e.outcome === 'fail') { row.fail++; row.checked++ }
    else if (e.outcome === 'abstain') { row.abstain++; row.checked++ }
    byType.set(e.event_type, row)
  }
  return Array.from(byType.values()).sort((a, b) => b.fail - a.fail || a.eventType.localeCompare(b.eventType))
}

export function ReliabilityPanel() {
  const [adminKey, setAdminKey] = useState<string>(() => sessionStorage.getItem(SESSION_KEY) ?? '')
  const [keyInput, setKeyInput] = useState('')
  const [clients, setClients] = useState<{ id: string; name?: string }[]>([])
  const [clientFilter, setClientFilter] = useState('')
  const [events, setEvents] = useState<AuditEventRecord[]>([])
  const [status, setStatus] = useState<'ok' | 'degraded' | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listClients().then(setClients).catch(() => setClients([]))
  }, [])

  const load = useCallback(async (key: string) => {
    if (!key) return
    setLoading(true)
    setError(null)
    try {
      const result = await getAuditEventsAdmin(key, {
        clientId: clientFilter || undefined,
        eventType: undefined,
        limit: 500,
      })
      setEvents(result.events.filter((e) => e.event_type.startsWith('reliability.')))
      setStatus(result.status)
    } catch (e: any) {
      const msg = String(e?.message ?? '')
      if (msg.includes('403') || msg.toLowerCase().includes('invalid admin key')) {
        setError('Invalid admin key.')
        sessionStorage.removeItem(SESSION_KEY)
        setAdminKey('')
      } else if (msg.includes('503')) {
        setError('Admin API key not configured on this server.')
      } else {
        setError(msg || 'Failed to load reliability events.')
      }
    } finally {
      setLoading(false)
    }
  }, [clientFilter])

  useEffect(() => { if (adminKey) load(adminKey) }, [adminKey, load])

  const submitKey = () => {
    const trimmed = keyInput.trim()
    if (!trimmed) return
    sessionStorage.setItem(SESSION_KEY, trimmed)
    setAdminKey(trimmed)
    setKeyInput('')
  }

  const rates = useMemo(() => summarizeByEventType(events), [events])

  const failuresByResource = useMemo(() => {
    const map = new Map<string, { resourceId: string; eventType: string; count: number; latest: AuditEventRecord }>()
    for (const e of events) {
      if (e.outcome !== 'fail' || !e.resource_id) continue
      const key = `${e.event_type}::${e.resource_id}`
      const existing = map.get(key)
      if (existing) {
        existing.count++
        if (e.created_at > existing.latest.created_at) existing.latest = e
      } else {
        map.set(key, { resourceId: e.resource_id, eventType: e.event_type, count: 1, latest: e })
      }
    }
    return Array.from(map.values()).sort((a, b) => b.count - a.count)
  }, [events])

  const coverageGaps = useMemo(
    () => events.filter((e) => e.event_type === 'reliability.kpi_coverage' && e.outcome !== 'pass'),
    [events],
  )

  if (!adminKey) {
    return (
      <div className="max-w-md">
        <h2 className="text-lg font-semibold text-white mb-1">Reliability</h2>
        <p className="text-sm text-slate-400 mb-4">
          Fleet-wide reliability evidence spans every tenant, so this page requires the admin API key —
          the same one used for <code className="text-xs bg-slate-800 px-1 py-0.5 rounded">curl</code> access today.
          Stored only for this browser tab's session, never saved to disk.
        </p>
        {error && (
          <div className="mb-4 p-3 rounded-lg border border-severity-critical/30 bg-severity-critical/10 text-severity-critical text-sm">{error}</div>
        )}
        <div className="flex gap-2">
          <input
            type="password"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') submitKey() }}
            placeholder="X-Admin-Key"
            className="flex-1 px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm font-mono"
          />
          <button
            onClick={submitKey}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium"
          >
            <KeyRound className="w-4 h-4" /> Unlock
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Reliability</h2>
          <p className="text-sm text-slate-400">
            Stage-wise evidence from SA, DA, MA, and SF — what each pipeline stage checked, and what it found.
          </p>
        </div>
        <button
          onClick={() => load(adminKey)}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white text-sm font-medium"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          Refresh
        </button>
      </div>

      <div className="mb-4 flex items-center gap-3">
        <label className="text-xs text-slate-400">Client</label>
        <select
          value={clientFilter}
          onChange={(e) => setClientFilter(e.target.value)}
          className="px-2 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm"
        >
          <option value="">All clients</option>
          {clients.map((c) => <option key={c.id} value={c.id}>{c.name ?? c.id}</option>)}
        </select>
        <div className="flex gap-3 ml-auto text-xs">
          <Link to="/settings/connection-health" className="text-slate-400 hover:text-white">Connection Health →</Link>
          <Link to="/settings/slice-validity" className="text-slate-400 hover:text-white">Slice Validity →</Link>
        </div>
      </div>

      {status === 'degraded' && (
        <div className="mb-4 p-3 rounded-lg border border-severity-warning/30 bg-severity-warning/10 text-severity-warning text-sm flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 shrink-0" />
          No database pool available — the reliability panel is not writing anywhere right now. This is not a clean bill of health.
        </div>
      )}
      {error && (
        <div className="mb-4 p-3 rounded-lg border border-severity-critical/30 bg-severity-critical/10 text-severity-critical text-sm">{error}</div>
      )}

      {/* Fleet-level rates by signal */}
      <section className="mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-2">Rates by signal (last {events.length} events loaded)</h3>
        {rates.length === 0 ? (
          <p className="text-sm text-slate-500 italic">No reliability events in range.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-left">
                  <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Signal</th>
                  <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Pass</th>
                  <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Fail</th>
                  <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Abstain</th>
                  <th className="pb-2 text-xs font-semibold text-slate-400 uppercase tracking-wide">Fail rate (of checked)</th>
                </tr>
              </thead>
              <tbody>
                {rates.map((r) => (
                  <tr key={r.eventType} className="border-b border-slate-800/60 hover:bg-slate-800/20">
                    <td className="py-2.5 pr-4 text-white font-medium">{EVENT_TYPE_LABELS[r.eventType] ?? r.eventType}</td>
                    <td className="py-2.5 pr-4 text-severity-opportunity">{r.pass}</td>
                    <td className="py-2.5 pr-4 text-severity-critical">{r.fail}</td>
                    <td className="py-2.5 pr-4 text-severity-warning">{r.abstain}</td>
                    <td className="py-2.5 text-slate-300">{r.checked ? `${((r.fail / r.checked) * 100).toFixed(0)}%` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Per-KPI / per-resource failures */}
      <section className="mb-6">
        <h3 className="text-sm font-semibold text-slate-300 mb-2">Per-resource failures</h3>
        {failuresByResource.length === 0 ? (
          <p className="text-sm text-slate-500 italic">No failures in range.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-left">
                  <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Signal</th>
                  <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Resource</th>
                  <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Occurrences</th>
                  <th className="pb-2 text-xs font-semibold text-slate-400 uppercase tracking-wide">Latest detail</th>
                </tr>
              </thead>
              <tbody>
                {failuresByResource.map((f) => (
                  <tr key={`${f.eventType}::${f.resourceId}`} className="border-b border-slate-800/60 hover:bg-slate-800/20">
                    <td className="py-2.5 pr-4 text-white">{EVENT_TYPE_LABELS[f.eventType] ?? f.eventType}</td>
                    <td className="py-2.5 pr-4 text-slate-300 font-mono text-xs">{f.resourceId}</td>
                    <td className="py-2.5 pr-4 text-severity-critical">{f.count}</td>
                    <td className="py-2.5 text-slate-400 text-xs truncate max-w-[400px]" title={JSON.stringify(f.latest.payload)}>
                      {typeof f.latest.payload?.detail === 'string' ? f.latest.payload.detail : JSON.stringify(f.latest.payload)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Coverage gaps */}
      <section>
        <h3 className="text-sm font-semibold text-slate-300 mb-2">Coverage gaps (registered KPIs never evaluated)</h3>
        {coverageGaps.length === 0 ? (
          <p className="text-sm text-slate-500 italic">No coverage gaps in range.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-left">
                  <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Client</th>
                  <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Outcome</th>
                  <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">When</th>
                  <th className="pb-2 text-xs font-semibold text-slate-400 uppercase tracking-wide">Detail</th>
                </tr>
              </thead>
              <tbody>
                {coverageGaps.map((e) => (
                  <tr key={e.id} className="border-b border-slate-800/60 hover:bg-slate-800/20">
                    <td className="py-2.5 pr-4 text-white font-mono text-xs">{e.client_id}</td>
                    <td className="py-2.5 pr-4"><OutcomeBadge outcome={e.outcome} /></td>
                    <td className="py-2.5 pr-4 text-slate-400 text-xs">{new Date(e.created_at).toLocaleString()}</td>
                    <td className="py-2.5 text-slate-400 text-xs truncate max-w-[400px]">{JSON.stringify(e.payload)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
