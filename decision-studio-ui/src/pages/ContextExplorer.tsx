import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeft,
  BarChart3,
  Database,
  GitBranch,
  Loader2,
  Users,
} from 'lucide-react'
import {
  listPrincipals,
  listBusinessProcesses,
  listKpis,
  listDataProducts,
} from '../api/client'

// ── Types ────────────────────────────────────────────────────────────────────

type ActiveDetail =
  | { kind: 'principal'; item: any }
  | { kind: 'bp'; item: any }
  | { kind: 'kpi'; item: any }
  | { kind: 'dp'; item: any }
  | null

// ── Column component ─────────────────────────────────────────────────────────

interface ColumnProps {
  icon: React.ReactNode
  title: string
  count: number
  hint?: string
  items: any[]
  selectedId: string | null
  getId: (item: any) => string
  getLabel: (item: any) => string
  getSubLabel?: (item: any) => string | undefined
  onSelect: (id: string, item: any) => void
  loading?: boolean
}

function Column({
  icon,
  title,
  count,
  hint,
  items,
  selectedId,
  getId,
  getLabel,
  getSubLabel,
  onSelect,
  loading,
}: ColumnProps) {
  return (
    <div className="flex flex-col flex-1 min-w-[200px] border-r border-slate-800 last:border-r-0">
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-3 border-b border-slate-800 bg-slate-900/60">
        <span className="text-slate-400">{icon}</span>
        <span className="text-sm font-semibold text-slate-200 truncate">{title}</span>
        <span className="ml-auto shrink-0 text-xs font-medium text-slate-500 bg-slate-800 rounded-full px-2 py-0.5">
          {count}
        </span>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-10 text-slate-500">
            <Loader2 className="w-4 h-4 animate-spin mr-2" />
            <span className="text-xs">Loading…</span>
          </div>
        ) : items.length === 0 ? (
          <p className="text-xs text-slate-600 px-3 py-4 italic">
            {hint ?? 'No items found'}
          </p>
        ) : (
          <ul>
            {items.map((item) => {
              const id = getId(item)
              const isSelected = selectedId === id
              const subLabel = getSubLabel?.(item)
              return (
                <li
                  key={id}
                  onClick={() => onSelect(id, item)}
                  className={[
                    'cursor-pointer px-3 py-2.5 border-l-2 transition-colors',
                    isSelected
                      ? 'bg-indigo-900/30 border-indigo-400 text-slate-100'
                      : 'border-transparent hover:bg-slate-800 text-slate-300',
                  ].join(' ')}
                >
                  <p className="text-sm font-medium leading-snug truncate">
                    {getLabel(item)}
                  </p>
                  {subLabel && (
                    <p className="text-xs text-slate-500 truncate mt-0.5">{subLabel}</p>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}

// ── Detail panel ─────────────────────────────────────────────────────────────

function DetailPanel({ detail }: { detail: ActiveDetail }) {
  if (!detail) return null

  const kindLabel: Record<NonNullable<ActiveDetail>['kind'], string> = {
    principal: 'Principal',
    bp: 'Business Process',
    kpi: 'KPI',
    dp: 'Data Product',
  }

  const kindColor: Record<NonNullable<ActiveDetail>['kind'], string> = {
    principal: 'text-violet-400',
    bp: 'text-amber-400',
    kpi: 'text-sky-400',
    dp: 'text-emerald-400',
  }

  const item = detail.item
  const kind = detail.kind

  // Render all fields generically, skipping nulls and empty arrays
  const entries = Object.entries(item).filter(([, v]) => {
    if (v === null || v === undefined) return false
    if (Array.isArray(v) && v.length === 0) return false
    return true
  })

  return (
    <div className="mt-4 rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <p className={`text-xs font-semibold uppercase tracking-wider mb-3 ${kindColor[kind]}`}>
        {kindLabel[kind]} Detail
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-3">
        {entries.map(([key, value]) => (
          <div key={key} className="min-w-0">
            <p className="text-xs text-slate-500 uppercase tracking-wide mb-0.5">
              {key.replace(/_/g, ' ')}
            </p>
            <p className="text-sm text-slate-200 break-words">
              {Array.isArray(value)
                ? value.join(', ')
                : typeof value === 'object'
                ? JSON.stringify(value)
                : String(value)}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function ContextExplorer() {
  // Raw data
  const [principals, setPrincipals] = useState<any[]>([])
  const [businessProcesses, setBusinessProcesses] = useState<any[]>([])
  const [kpis, setKpis] = useState<any[]>([])
  const [dataProducts, setDataProducts] = useState<any[]>([])

  // Selections
  const [selectedPrincipal, setSelectedPrincipal] = useState<string | null>(null)
  const [selectedBP, setSelectedBP] = useState<string | null>(null)
  const [selectedKPI, setSelectedKPI] = useState<string | null>(null)
  const [selectedDP, setSelectedDP] = useState<string | null>(null)

  // Last clicked detail
  const [activeDetail, setActiveDetail] = useState<ActiveDetail>(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // ── Load all data once ──────────────────────────────────────────────────────
  useEffect(() => {
    Promise.all([
      listPrincipals(),
      listBusinessProcesses(),
      listKpis(),
      listDataProducts(),
    ])
      .then(([p, bp, k, dp]) => {
        setPrincipals(p)
        setBusinessProcesses(bp)
        setKpis(k)
        setDataProducts(dp)
      })
      .catch((err) => setError(err.message ?? 'Failed to load registry data'))
      .finally(() => setLoading(false))
  }, [])

  // ── Filtered views ──────────────────────────────────────────────────────────
  const filteredBPs = selectedPrincipal
    ? businessProcesses.filter((bp) => {
        const principal = principals.find((p) => p.id === selectedPrincipal)
        return principal?.business_processes?.includes(bp.id)
      })
    : businessProcesses

  const filteredKPIs = selectedBP
    ? kpis.filter((k) => k.business_process_ids?.includes(selectedBP))
    : selectedPrincipal
    ? kpis.filter((k) => {
        const principal = principals.find((p) => p.id === selectedPrincipal)
        return principal?.kpis?.includes(k.id)
      })
    : kpis

  const filteredDPs = selectedKPI
    ? dataProducts.filter((dp) => {
        const kpi = kpis.find((k) => k.id === selectedKPI)
        return dp.id === kpi?.data_product_id
      })
    : dataProducts

  // ── Selection handlers ──────────────────────────────────────────────────────
  function handleSelectPrincipal(id: string, item: any) {
    setSelectedPrincipal(id)
    setSelectedBP(null)
    setSelectedKPI(null)
    setSelectedDP(null)
    setActiveDetail({ kind: 'principal', item })
  }

  function handleSelectBP(id: string, item: any) {
    setSelectedBP(id)
    setSelectedKPI(null)
    setSelectedDP(null)
    setActiveDetail({ kind: 'bp', item })
  }

  function handleSelectKPI(id: string, item: any) {
    setSelectedKPI(id)
    setSelectedDP(null)
    setActiveDetail({ kind: 'kpi', item })
  }

  function handleSelectDP(id: string, item: any) {
    setSelectedDP(id)
    setActiveDetail({ kind: 'dp', item })
  }

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Page header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm px-6 py-4 flex items-center gap-4 shrink-0">
        <Link
          to="/dashboard"
          className="flex items-center gap-1.5 text-slate-400 hover:text-slate-100 transition-colors text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          Back
        </Link>
        <div className="w-px h-5 bg-slate-700" />
        <div>
          <h1 className="text-lg font-semibold text-slate-100 leading-none">
            Context Explorer
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Navigate relationships between principals, processes, KPIs, and data
          </p>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 flex flex-col p-6 min-h-0 overflow-auto">
        {error ? (
          <div className="rounded-lg border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        ) : (
          <>
            {/* Column browser */}
            <div className="flex border border-slate-800 rounded-lg overflow-hidden bg-slate-900 shrink-0 overflow-x-auto">
              {/* Column 1 — Principals */}
              <Column
                icon={<Users className="w-4 h-4" />}
                title="Principals"
                count={principals.length}
                items={principals}
                selectedId={selectedPrincipal}
                getId={(p) => p.id}
                getLabel={(p) => p.name}
                getSubLabel={(p) => p.title ?? p.role}
                onSelect={handleSelectPrincipal}
                loading={loading}
              />

              {/* Column 2 — Business Processes */}
              <Column
                icon={<GitBranch className="w-4 h-4" />}
                title="Business Processes"
                count={filteredBPs.length}
                hint={
                  selectedPrincipal
                    ? 'No processes linked to this principal'
                    : 'Select a Principal to filter'
                }
                items={filteredBPs}
                selectedId={selectedBP}
                getId={(bp) => bp.id}
                getLabel={(bp) => bp.name}
                getSubLabel={(bp) => bp.domain}
                onSelect={handleSelectBP}
                loading={loading}
              />

              {/* Column 3 — KPIs */}
              <Column
                icon={<BarChart3 className="w-4 h-4" />}
                title="KPIs"
                count={filteredKPIs.length}
                hint={
                  selectedBP
                    ? 'No KPIs linked to this process'
                    : selectedPrincipal
                    ? 'No KPIs linked to this principal'
                    : 'Select a Business Process to filter'
                }
                items={filteredKPIs}
                selectedId={selectedKPI}
                getId={(k) => k.id}
                getLabel={(k) => k.name ?? k.display_name}
                getSubLabel={(k) => k.domain ?? k.unit}
                onSelect={handleSelectKPI}
                loading={loading}
              />

              {/* Column 4 — Data Products */}
              <Column
                icon={<Database className="w-4 h-4" />}
                title="Data Products"
                count={filteredDPs.length}
                hint={
                  selectedKPI
                    ? 'No data product linked to this KPI'
                    : 'Select a KPI to filter'
                }
                items={filteredDPs}
                selectedId={selectedDP}
                getId={(dp) => dp.id}
                getLabel={(dp) => dp.name}
                getSubLabel={(dp) => dp.domain ?? dp.owner}
                onSelect={handleSelectDP}
                loading={loading}
              />
            </div>

            {/* Hint row when nothing selected */}
            {!selectedPrincipal && !loading && (
              <p className="text-xs text-slate-600 mt-2 italic text-center">
                Click a Principal to begin exploring relationships
              </p>
            )}

            {/* Detail panel */}
            <DetailPanel detail={activeDetail} />
          </>
        )}
      </main>
    </div>
  )
}
