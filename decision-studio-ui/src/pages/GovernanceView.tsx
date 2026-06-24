/**
 * GovernanceView — Executive Settings Mode (Mode 3)
 *
 * Read-mostly views for C-level principals:
 *   /settings/governance/ownership  — KPI Ownership Map
 *   /settings/governance/coverage   — Coverage Summary
 *   /settings/governance/kpis       — KPI Definitions (read-only)
 *   /settings/governance/principals — Principal Directory (read-only)
 *
 * Wraps in SettingsLayout automatically.
 */

import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Target, Loader2 } from 'lucide-react'
import { SettingsLayout } from '../components/SettingsLayout'
import { getSettingsClientId } from '../utils/settingsMode'
import {
  listKpis,
  listPrincipals,
  getAccountabilityCoverage,
  listAccountabilities,
  type AccountabilityCoverage,
  type KPIAccountability,
} from '../api/client'

// ─────────────────────────────────────────────────
// Section: KPI Ownership Map
// ─────────────────────────────────────────────────

function OwnershipMap({ clientId }: { clientId: string }) {
  const [accountabilities, setAccountabilities] = useState<KPIAccountability[]>([])
  const [kpis, setKpis] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!clientId) return
    Promise.all([
      listAccountabilities(clientId),
      listKpis(clientId),
    ])
      .then(([acc, kpiList]) => {
        setAccountabilities(acc || [])
        setKpis(kpiList || [])
      })
      .finally(() => setLoading(false))
  }, [clientId])

  if (!clientId) return <NoClient />
  if (loading) return <Spinner />

  // Build kpi_id → name map
  const kpiNames: Record<string, string> = {}
  for (const k of kpis) kpiNames[k.id] = k.name || k.id

  // Group by KPI
  const byKpi: Record<string, KPIAccountability[]> = {}
  for (const a of accountabilities) {
    if (!byKpi[a.kpi_id]) byKpi[a.kpi_id] = []
    byKpi[a.kpi_id].push(a)
  }

  const unowned = kpis.filter((k) => !byKpi[k.id])

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">KPI Ownership Map</h2>
        <p className="text-sm text-slate-400">Every KPI and its accountable principal.</p>
      </div>

      {Object.keys(byKpi).length === 0 && unowned.length === 0 && (
        <p className="text-sm text-slate-500 italic">No KPIs or accountability records found for this client.</p>
      )}

      {Object.entries(byKpi).map(([kpiId, records]) => (
        <div key={kpiId} className="rounded-xl bg-card border border-border p-4">
          <p className="text-sm font-semibold text-white mb-2">{kpiNames[kpiId] || kpiId}</p>
          <div className="space-y-1.5">
            {records.map((r) => (
              <div key={r.id} className="flex items-center gap-3 text-sm">
                <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                  r.role === 'accountable'
                    ? 'bg-indigo-950/60 text-indigo-300 border border-indigo-700/40'
                    : 'bg-slate-800 text-slate-400 border border-slate-700'
                }`}>
                  {r.role}
                </span>
                <span className="text-slate-300">{r.principal_id}</span>
                {r.scope_dimension && (
                  <span className="text-xs text-slate-500">
                    {r.scope_dimension}: {r.scope_value}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}

      {unowned.length > 0 && (
        <div>
          <p className="text-sm font-medium text-amber-400 mb-2 flex items-center gap-2">
            <Target className="w-4 h-4" />
            {unowned.length} KPI{unowned.length > 1 ? 's' : ''} without an owner
          </p>
          <div className="space-y-1.5">
            {unowned.map((k) => (
              <div key={k.id} className="flex items-center gap-2 rounded-lg bg-amber-950/20 border border-amber-700/20 px-3 py-2">
                <span className="text-sm text-amber-200">{k.name || k.id}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────
// Section: Coverage Summary
// ─────────────────────────────────────────────────

function CoverageSummary({ clientId }: { clientId: string }) {
  const [coverage, setCoverage] = useState<AccountabilityCoverage | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!clientId) return
    getAccountabilityCoverage(clientId)
      .then(setCoverage)
      .finally(() => setLoading(false))
  }, [clientId])

  if (!clientId) return <NoClient />
  if (loading) return <Spinner />
  if (!coverage) return <p className="text-sm text-slate-500">No coverage data available.</p>

  const pct = Math.round(coverage.coverage_pct)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Coverage Summary</h2>
        <p className="text-sm text-slate-400">KPI accountability coverage for this client.</p>
      </div>

      {/* Big number */}
      <div className="rounded-xl bg-card border border-border p-6 flex items-center gap-6">
        <div>
          <p className={`text-5xl font-bold ${pct >= 100 ? 'text-emerald-400' : pct >= 75 ? 'text-amber-400' : 'text-red-400'}`}>
            {pct}%
          </p>
          <p className="text-sm text-slate-400 mt-1">
            {coverage.covered_kpis} of {coverage.total_kpis} KPIs have an accountable owner
          </p>
        </div>
        <div className="flex-1 h-3 rounded-full bg-slate-800 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${pct >= 100 ? 'bg-emerald-500' : pct >= 75 ? 'bg-amber-500' : 'bg-red-500'}`}
            style={{ width: `${Math.min(pct, 100)}%` }}
          />
        </div>
      </div>

      {/* Unassigned */}
      {coverage.unassigned_kpis.length > 0 && (
        <div>
          <p className="text-sm font-medium text-amber-400 mb-2">Unassigned KPIs ({coverage.unassigned_kpis.length})</p>
          <div className="space-y-1">
            {coverage.unassigned_kpis.map((k) => (
              <div key={k.id} className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-amber-950/20 border border-amber-700/20 text-sm text-amber-200">
                {k.name}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Conflicts */}
      {coverage.conflicts.length > 0 && (
        <div>
          <p className="text-sm font-medium text-red-400 mb-2">Conflicts ({coverage.conflicts.length})</p>
          <div className="space-y-1">
            {coverage.conflicts.map((c) => (
              <div key={c.kpi_id} className="px-3 py-1.5 rounded-lg bg-red-950/20 border border-red-700/20 text-sm text-red-200">
                {c.kpi_name} — {c.principal_count} accountable principals
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────
// Section: KPI Definitions (read-only)
// ─────────────────────────────────────────────────

function KpiDefinitions({ clientId }: { clientId: string }) {
  const [kpis, setKpis] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')

  useEffect(() => {
    if (!clientId) return
    listKpis(clientId).then(setKpis).finally(() => setLoading(false))
  }, [clientId])

  if (!clientId) return <NoClient />
  if (loading) return <Spinner />

  const filtered = search
    ? kpis.filter((k) => `${k.name} ${k.domain} ${k.description}`.toLowerCase().includes(search.toLowerCase()))
    : kpis

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">KPI Definitions</h2>
        <p className="text-sm text-slate-400">Read-only view of all KPIs monitored for this client.</p>
      </div>

      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search KPIs…"
        className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500"
      />

      <div className="space-y-2">
        {filtered.map((k) => (
          <div key={k.id} className="rounded-xl bg-card border border-border p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-white">{k.name}</p>
                <p className="text-xs text-slate-500 mt-0.5">{k.domain} · {k.unit}</p>
                {k.description && (
                  <p className="text-xs text-slate-400 mt-1 leading-relaxed">{k.description}</p>
                )}
              </div>
              {k.benchmark_range && (
                <span className="text-xs text-slate-400 flex-shrink-0">
                  Benchmark: <span className="text-slate-200">{k.benchmark_range}</span>
                </span>
              )}
            </div>
          </div>
        ))}
        {filtered.length === 0 && (
          <p className="text-sm text-slate-500 italic">No KPIs found.</p>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────
// Section: Principal Directory (read-only)
// ─────────────────────────────────────────────────

function PrincipalDirectory({ clientId }: { clientId: string }) {
  const [principals, setPrincipals] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!clientId) return
    listPrincipals(clientId).then(setPrincipals).finally(() => setLoading(false))
  }, [clientId])

  if (!clientId) return <NoClient />
  if (loading) return <Spinner />

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-white mb-1">Principal Directory</h2>
        <p className="text-sm text-slate-400">All principals registered for this client.</p>
      </div>

      <div className="space-y-2">
        {principals.map((p) => (
          <div key={p.id} className="rounded-xl bg-card border border-border p-4 flex items-center gap-4">
            <div className="w-10 h-10 rounded-full bg-indigo-600/20 flex items-center justify-center text-sm font-bold text-indigo-300 flex-shrink-0">
              {(p.name || p.id).split(' ').map((w: string) => w[0]).join('').slice(0, 2).toUpperCase()}
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-white">{p.name || p.id}</p>
              <p className="text-xs text-slate-400">{p.title || p.role || ''}</p>
            </div>
            {p.email && (
              <p className="text-xs text-slate-500">{p.email}</p>
            )}
            {!p.email && (
              <span className="text-[10px] text-amber-500 border border-amber-700/40 px-1.5 py-0.5 rounded">No email</span>
            )}
          </div>
        ))}
        {principals.length === 0 && (
          <p className="text-sm text-slate-500 italic">No principals found.</p>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────
// Shared helpers
// ─────────────────────────────────────────────────

function Spinner() {
  return (
    <div className="flex items-center gap-2 text-slate-400 py-8">
      <Loader2 className="w-4 h-4 animate-spin" />
      <span className="text-sm">Loading…</span>
    </div>
  )
}

function NoClient() {
  return (
    <div className="py-8 text-sm text-slate-500 italic">
      No client selected. Log in as a principal to see governance data.
    </div>
  )
}

// ─────────────────────────────────────────────────
// Public export — routes to the right sub-section
// ─────────────────────────────────────────────────

export function GovernanceView() {
  const clientId = getSettingsClientId()
  const { subsection } = useParams<{ subsection?: string }>()
  const section = subsection ?? 'ownership'

  const sectionContent: Record<string, React.ReactNode> = {
    ownership:  <OwnershipMap clientId={clientId} />,
    coverage:   <CoverageSummary clientId={clientId} />,
    kpis:       <KpiDefinitions clientId={clientId} />,
    principals: <PrincipalDirectory clientId={clientId} />,
  }

  return (
    <SettingsLayout>
      <div className="p-8 font-sans min-h-full">
        {sectionContent[section] ?? sectionContent['ownership']}
      </div>
    </SettingsLayout>
  )
}
