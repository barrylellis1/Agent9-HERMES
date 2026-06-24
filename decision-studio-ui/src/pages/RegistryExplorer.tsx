import { type ComponentType, useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams, useParams, useLocation } from 'react-router-dom'
import { Activity, BookOpen, Box, Briefcase, CheckCircle2, Code2, Database, KeyRound, Loader2, Save, Trash2, Plus, X, XCircle } from 'lucide-react'
import { SettingsLayout } from '../components/SettingsLayout'
import { AccountabilityInterviewPanel } from '../components/AccountabilityInterviewPanel'
import {
  type BusinessTerm,
  type ConnectionHealthResult,
  type ConnectionHealthResponse,
  type KPIAccountability,
  listGlossaryTerms,
  createGlossaryTerm,
  updateGlossaryTerm,
  deleteGlossaryTerm,
  listBusinessProcesses,
  listDataProducts,
  listKpis,
  listPrincipals,
  listClients,
  createClient,
  createKpi, replaceKpi, deleteKpi,
  createPrincipal, replacePrincipal, deletePrincipal,
  createDataProduct, replaceDataProduct, deleteDataProduct,
  createBusinessProcess, replaceBusinessProcess, deleteBusinessProcess,
  getConnectionHealth,
  testConnectionHealth,
  listAccountabilities,
} from '../api/client'

type RegistryKey = 'glossary' | 'data-products' | 'kpis' | 'business-processes' | 'principals'

type RegistryDescriptor = {
  key: RegistryKey
  label: string
  icon: ComponentType<{ className?: string }>
  colorClass: string
  editable: boolean
}

type ColumnDef = {
  key: string
  label: string
  widthClass?: string
  render: (row: any) => string
}

const REGISTRIES: RegistryDescriptor[] = [
  {
    key: 'business-processes',
    label: 'Business Processes',
    icon: Briefcase,
    colorClass: 'text-amber-400 bg-amber-500/10',
    editable: true,
  },
  {
    key: 'data-products',
    label: 'Data Products',
    icon: Box,
    colorClass: 'text-emerald-400 bg-emerald-500/10',
    editable: true,
  },
  {
    key: 'kpis',
    label: 'KPIs',
    icon: Database,
    colorClass: 'text-blue-400 bg-blue-500/10',
    editable: true,
  },
  {
    key: 'principals',
    label: 'Principals',
    icon: KeyRound,
    colorClass: 'text-slate-300 bg-slate-500/10',
    editable: true,
  },
  {
    key: 'glossary',
    label: 'Business Glossary',
    icon: BookOpen,
    colorClass: 'text-purple-400 bg-purple-500/10',
    editable: true,
  },
]

function safeString(value: unknown): string {
  if (value === null || value === undefined) return ''
  return String(value)
}

function rowId(row: any): string {
  return safeString((row && (row.id ?? row.name)) ?? '')
}

function normalizeSearch(value: string): string {
  return value.trim().toLowerCase()
}

function countOf(value: unknown): number {
  if (Array.isArray(value)) return value.length
  if (value && typeof value === 'object') return Object.keys(value as Record<string, unknown>).length
  return 0
}

function columnsForRegistry(key: RegistryKey): ColumnDef[] {
  if (key === 'glossary') {
    return [
      { key: 'name', label: 'Name', widthClass: 'w-[240px]', render: (r) => safeString(r?.name) },
      { key: 'description', label: 'Description', render: (r) => safeString(r?.description) },
      { key: 'synonyms', label: 'Synonyms', widthClass: 'w-[110px]', render: (r) => String(countOf(r?.synonyms)) },
      { key: 'mappings', label: 'Mappings', widthClass: 'w-[110px]', render: (r) => String(countOf(r?.technical_mappings)) },
    ]
  }
  if (key === 'data-products') {
    return [
      { key: 'id', label: 'ID', widthClass: 'w-[240px]', render: (r) => safeString(r?.id) },
      { key: 'name', label: 'Name', render: (r) => safeString(r?.name) },
      { key: 'domain', label: 'Domain', widthClass: 'w-[140px]', render: (r) => safeString(r?.domain) },
      { key: 'owner', label: 'Owner', widthClass: 'w-[160px]', render: (r) => safeString(r?.owner) },
      { key: 'tables', label: 'Tables', widthClass: 'w-[90px]', render: (r) => String(countOf(r?.tables)) },
      { key: 'views', label: 'Views', widthClass: 'w-[90px]', render: (r) => String(countOf(r?.views)) },
    ]
  }
  if (key === 'kpis') {
    return [
      { key: 'id', label: 'ID', widthClass: 'w-[240px]', render: (r) => safeString(r?.id) },
      { key: 'name', label: 'Name', render: (r) => safeString(r?.name) },
      { key: 'domain', label: 'Domain', widthClass: 'w-[140px]', render: (r) => safeString(r?.domain) },
      { key: 'data_product_id', label: 'Data Product', widthClass: 'w-[200px]', render: (r) => safeString(r?.data_product_id) },
      { key: 'owner_role', label: 'Owner Role', widthClass: 'w-[140px]', render: (r) => safeString(r?.owner_role) },
      { key: 'unit', label: 'Unit', widthClass: 'w-[90px]', render: (r) => safeString(r?.unit) },
    ]
  }
  if (key === 'business-processes') {
    return [
      { key: 'id', label: 'ID', widthClass: 'w-[240px]', render: (r) => safeString(r?.id) },
      { key: 'name', label: 'Name', render: (r) => safeString(r?.name) },
      { key: 'domain', label: 'Domain', widthClass: 'w-[140px]', render: (r) => safeString(r?.domain) },
      { key: 'owner_role', label: 'Owner Role', widthClass: 'w-[140px]', render: (r) => safeString(r?.owner_role) },
      { key: 'tags', label: 'Tags', widthClass: 'w-[90px]', render: (r) => String(countOf(r?.tags)) },
    ]
  }
  return [
    { key: 'id', label: 'ID', widthClass: 'w-[240px]', render: (r) => safeString(r?.id) },
    { key: 'name', label: 'Name', render: (r) => safeString(r?.name) },
    { key: 'title', label: 'Title', widthClass: 'w-[200px]', render: (r) => safeString(r?.title) },
    { key: 'decision_style', label: 'Decision Style', widthClass: 'w-[140px]', render: (r) => safeString(r?.decision_style) },
  ]
}

function parseSynonyms(text: string): string[] {
  return text
    .split('\n')
    .map((v) => v.trim())
    .filter(Boolean)
}

function formatSynonyms(list: string[] | undefined): string {
  return (list || []).join('\n')
}

function parseJsonObject(text: string): Record<string, unknown> {
  const trimmed = text.trim()
  if (!trimmed) return {}
  return JSON.parse(trimmed) as Record<string, unknown>
}

// ── Connection Health Panel ───────────────────────────────────────────────────

function StatusBadge({ status }: { status: ConnectionHealthResult['status'] }) {
  if (status === 'ok') return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-400">
      <CheckCircle2 className="w-3.5 h-3.5" /> Connected
    </span>
  )
  if (status === 'error') return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-red-400">
      <XCircle className="w-3.5 h-3.5" /> Error
    </span>
  )
  return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-500">
      <Activity className="w-3.5 h-3.5" /> {status}
    </span>
  )
}

function ConnectionHealthPanel({ clientId }: { clientId?: string }) {
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
        <div className="mb-4 p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-200 text-sm">{error}</div>
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
                  <td className="py-2.5 text-red-400 text-xs truncate max-w-[300px]" title={r.error ?? undefined}>{r.error ?? (r.note ?? '—')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ── Accountability Panel ──────────────────────────────────────────────────────

function AccountabilityPanel({ clientId }: { clientId?: string }) {
  const [rows, setRows] = useState<KPIAccountability[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!clientId) return
    let canceled = false
    setLoading(true)
    setError(null)

    listAccountabilities(clientId)
      .then((data) => { if (!canceled) setRows(data) })
      .catch((e: unknown) => {
        if (!canceled) setError(e instanceof Error ? e.message : 'Failed to load accountability records')
      })
      .finally(() => { if (!canceled) setLoading(false) })

    return () => { canceled = true }
  }, [clientId])

  return (
    <div>
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-white">KPI Accountability</h2>
        <p className="text-sm text-slate-400">
          Principal accountability assignments per KPI — read-only in Phase 11A.
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-slate-400 text-sm py-4">
          <Loader2 className="w-4 h-4 animate-spin" />
          Loading accountability records&hellip;
        </div>
      )}

      {error && !loading && (
        <div className="p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-200 text-sm">{error}</div>
      )}

      {!loading && !error && rows.length === 0 && (
        <p className="text-sm text-slate-500 italic py-4">
          No accountability assignments &mdash; seed data to get started.
        </p>
      )}

      {!loading && !error && rows.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-left">
                <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">KPI</th>
                <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Principal</th>
                <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Scope</th>
                <th className="pb-2 pr-4 text-xs font-semibold text-slate-400 uppercase tracking-wide">Role</th>
                <th className="pb-2 text-xs font-semibold text-slate-400 uppercase tracking-wide">Notes</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-b border-slate-800 hover:bg-slate-800/50">
                  <td className="py-2.5 pr-4 text-white font-mono text-xs">{r.kpi_id}</td>
                  <td className="py-2.5 pr-4 text-slate-300 font-mono text-xs">{r.principal_id}</td>
                  <td className="py-2.5 pr-4">
                    {r.scope_dimension == null ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-700 text-slate-300">
                        Enterprise-wide
                      </span>
                    ) : (
                      <span className="text-slate-300 text-xs">
                        {r.scope_dimension}: {r.scope_value ?? '—'}
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 pr-4">
                    {r.role === 'accountable' ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        accountable
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-700 text-slate-400 border border-slate-600">
                        responsible
                      </span>
                    )}
                  </td>
                  <td className="py-2.5 text-slate-400 text-xs truncate max-w-[280px]" title={r.notes ?? undefined}>
                    {r.notes ?? '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

// ── Admin client selector ────────────────────────────────────────────────────

function AdminClientSelector({
  currentClientId,
  onChange,
}: {
  currentClientId: string
  onChange: (id: string) => void
}) {
  const [clients, setClients] = useState<{ id: string; name: string }[]>([])

  useEffect(() => {
    listClients()
      .then((data) => setClients(data || []))
      .catch(() => {})
  }, [])

  if (clients.length === 0) {
    return (
      <input
        value={currentClientId}
        onChange={(e) => onChange(e.target.value.toLowerCase().replace(/\s+/g, '_'))}
        placeholder="Enter client id…"
        className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500 w-48"
      />
    )
  }

  return (
    <select
      value={currentClientId}
      onChange={(e) => onChange(e.target.value)}
      className="px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500 appearance-none pr-8 w-56"
    >
      <option value="">— select client —</option>
      {clients.map((c) => (
        <option key={c.id} value={c.id}>
          {c.name} ({c.id})
        </option>
      ))}
    </select>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────

export function RegistryExplorer() {
  // Derive section from URL: /settings/registry/kpis → section=kpis
  // or ?section=kpis, or /settings/accountability, /settings/connection-health, etc.
  const { section: routeSection } = useParams<{ section?: string }>()
  const { pathname } = useLocation()
  const [searchParams] = useSearchParams()

  const sectionParam: string = (() => {
    if (routeSection) return routeSection
    const sp = searchParams.get('section')
    if (sp) return sp
    if (pathname === '/settings/accountability') return 'accountability'
    if (pathname === '/settings/ownership-interview') return 'ownership-interview'
    if (pathname === '/settings/connection-health') return 'connection-health'
    return 'glossary'
  })()

  // Map URL section names → internal state
  const showConnectionHealth = sectionParam === 'connection-health'
  const showAccountability   = sectionParam === 'accountability'
  const showInterview        = sectionParam === 'ownership-interview'
  const registryKey: RegistryKey = (
    ['glossary','kpis','principals','data-products','business-processes'].includes(sectionParam)
      ? sectionParam
      : 'glossary'
  ) as RegistryKey

  // Section is now driven purely by URL params — no programmatic setters needed.
  // Left-nav links use <Link to="..."> to change sections.

  const active = useMemo(() => REGISTRIES.find((r) => r.key === registryKey)!, [registryKey])
  // workspaceId removed — Settings header now lives in SettingsLayout sidebar

  // Admin mode state
  const [adminMode] = useState(() => localStorage.getItem('a9_admin_mode') === 'true')
  const [adminTargetClient, setAdminTargetClientState] = useState(
    () => localStorage.getItem('a9_admin_target_client') ?? ''
  )
  const [newClientId, setNewClientId] = useState('')
  const [newClientName, setNewClientName] = useState('')
  const [newClientIndustry, setNewClientIndustry] = useState('')
  const [showNewClientForm, setShowNewClientForm] = useState(false)
  const [creatingClient, setCreatingClient] = useState(false)
  const [clientCreateError, setClientCreateError] = useState<string | null>(null)

  // Active client is:
  //   - in admin mode: the explicitly-selected target client
  //   - in normal mode: the session client from login
  const activeClientId = adminMode
    ? (adminTargetClient || undefined)
    : (localStorage.getItem('a9_active_client_id') ?? undefined)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [items, setItems] = useState<any[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [searchText, setSearchText] = useState('')

  // Glossary specific state
  const [termDraft, setTermDraft] = useState<BusinessTerm | null>(null)
  const [termSynonymsText, setTermSynonymsText] = useState('')
  const [termMappingsText, setTermMappingsText] = useState('')

  // Generic JSON editor state
  const [genericJsonText, setGenericJsonText] = useState('')

  // Form-based editor state
  const [formDraft, setFormDraft] = useState<Record<string, any> | null>(null)
  const [showJsonEditor, setShowJsonEditor] = useState(false)

  const selectedItem = useMemo(() => {
    if (!selectedId) return null
    return items.find((it) => rowId(it) === selectedId) || null
  }, [items, selectedId])

  const filteredItems = useMemo(() => {
    const q = normalizeSearch(searchText)
    if (!q) return items
    return items.filter((it) => {
      const id = rowId(it)
      const name = safeString(it?.name)
      const description = safeString(it?.description)
      const domain = safeString(it?.domain)
      const owner = safeString(it?.owner)
      const haystack = `${id} ${name} ${description} ${domain} ${owner}`.toLowerCase()
      return haystack.includes(q)
    })
  }, [items, searchText])

  useEffect(() => {
    let canceled = false

    const load = async () => {
      setLoading(true)
      setError(null)
      setSelectedId(null)

      // Reset generic state
      setGenericJsonText('')
      setFormDraft(null)
      setShowJsonEditor(false)

      // Reset glossary state
      setTermDraft(null)
      setTermSynonymsText('')
      setTermMappingsText('')

      setSearchText('')

      try {
        let data: any[] = []

        if (registryKey === 'glossary') {
          data = await listGlossaryTerms(activeClientId)
        } else if (registryKey === 'data-products') {
          data = await listDataProducts(activeClientId)
        } else if (registryKey === 'kpis') {
          data = await listKpis(activeClientId)
        } else if (registryKey === 'business-processes') {
          data = await listBusinessProcesses(activeClientId)
        } else if (registryKey === 'principals') {
          data = await listPrincipals(activeClientId)
        }

        if (!canceled) setItems(Array.isArray(data) ? data : [])
      } catch (e) {
        const message = e instanceof Error ? e.message : 'Failed to load registry'
        if (!canceled) setError(message)
      } finally {
        if (!canceled) setLoading(false)
      }
    }

    void load()

    return () => {
      canceled = true
    }
  }, [registryKey])

  useEffect(() => {
    if (!selectedItem) return

    if (registryKey === 'glossary') {
      const term = selectedItem as BusinessTerm
      setTermDraft(term)
      setTermSynonymsText(formatSynonyms(term.synonyms))
      setTermMappingsText(JSON.stringify(term.technical_mappings || {}, null, 2))
    } else {
      // For other registries, load into form + JSON editor
      setFormDraft({ ...selectedItem })
      setShowJsonEditor(false)
      setGenericJsonText(JSON.stringify(selectedItem, null, 2))
    }
  }, [registryKey, selectedItem])

  const onSelect = (it: any) => {
    const id = rowId(it)
    setSelectedId(id)
  }

  const onNewItem = () => {
    setSelectedId('__new__')

    if (registryKey === 'glossary') {
      const draft: BusinessTerm = {
        name: '',
        description: '',
        synonyms: [],
        technical_mappings: {},
      }
      setTermDraft(draft)
      setTermSynonymsText('')
      setTermMappingsText('{}')
    } else {
      setShowJsonEditor(false)
      let template: any = { id: 'new_item', name: 'New Item' }

      if (registryKey === 'kpis') {
        template = {
          id: 'new_kpi', name: 'New KPI', domain: 'Finance', description: '',
          unit: '', data_product_id: '', view_name: '', owner_role: '',
          tags: [], thresholds: [], metadata: {}
        }
      } else if (registryKey === 'principals') {
        template = {
          id: 'new_principal', name: 'New Principal', title: '', description: '',
          business_processes: [], kpis: [], responsibilities: [],
          decision_style: 'analytical', metadata: {}
        }
      } else if (registryKey === 'data-products') {
        template = {
          id: 'new_data_product', name: 'New Data Product', domain: '', description: '',
          owner: '', version: '1.0.0', source_system: 'duckdb',
          tags: [], tables: {}, views: {}
        }
      } else if (registryKey === 'business-processes') {
        template = {
          id: 'new_business_process', name: 'New Business Process', domain: '',
          description: '', owner_role: '', tags: [], metadata: {}
        }
      }

      setFormDraft(template)
      setGenericJsonText(JSON.stringify(template, null, 2))
    }
  }

  const reload = async () => {
    let data: any[] = []
    if (registryKey === 'glossary') data = await listGlossaryTerms(activeClientId)
    if (registryKey === 'data-products') data = await listDataProducts(activeClientId)
    if (registryKey === 'kpis') data = await listKpis(activeClientId)
    if (registryKey === 'business-processes') data = await listBusinessProcesses(activeClientId)
    if (registryKey === 'principals') data = await listPrincipals(activeClientId)
    setItems(data)
  }

  const saveGlossary = async () => {
    if (!termDraft) return

    const payload: BusinessTerm = {
      name: termDraft.name.trim(),
      description: termDraft.description?.trim() || null,
      synonyms: parseSynonyms(termSynonymsText),
      technical_mappings: parseJsonObject(termMappingsText),
    }

    if (!payload.name) {
      setError('Name is required')
      return
    }

    setLoading(true)
    setError(null)

    try {
      if (selectedId === '__new__') {
        await createGlossaryTerm(payload)
      } else {
        await updateGlossaryTerm(payload.name, payload)
      }

      await reload()
      setSelectedId(payload.name)
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to save term'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const saveGeneric = async () => {
    let payload: any

    if (showJsonEditor) {
      if (!genericJsonText) return
      try {
        payload = JSON.parse(genericJsonText)
      } catch (e) {
        setError('Invalid JSON format')
        return
      }
    } else {
      if (!formDraft) return
      payload = { ...formDraft }
    }

    if (!payload.id) {
      setError('ID field is required in JSON')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const isNew = selectedId === '__new__'
      const id = payload.id

      if (registryKey === 'kpis') {
        if (isNew) await createKpi(payload)
        else await replaceKpi(id, payload)
      } else if (registryKey === 'principals') {
        if (isNew) await createPrincipal(payload)
        else await replacePrincipal(id, payload)
      } else if (registryKey === 'data-products') {
        if (isNew) await createDataProduct(payload)
        else await replaceDataProduct(id, payload)
      } else if (registryKey === 'business-processes') {
        if (isNew) await createBusinessProcess(payload)
        else await replaceBusinessProcess(id, payload)
      }

      await reload()
      setSelectedId(id)
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to save item'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const deleteGlossary = async () => {
    if (!termDraft) return
    const termName = termDraft.name?.trim()
    if (!termName) return

    setLoading(true)
    setError(null)

    try {
      await deleteGlossaryTerm(termName)
      await reload()
      setSelectedId(null)
      setTermDraft(null)
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to delete term'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const deleteGeneric = async () => {
    if (!selectedId || selectedId === '__new__') return

    setLoading(true)
    setError(null)

    try {
      if (registryKey === 'kpis') await deleteKpi(selectedId, activeClientId)
      else if (registryKey === 'principals') await deletePrincipal(selectedId, activeClientId)
      else if (registryKey === 'data-products') await deleteDataProduct(selectedId, activeClientId)
      else if (registryKey === 'business-processes') await deleteBusinessProcess(selectedId, activeClientId)

      await reload()
      setSelectedId(null)
      setGenericJsonText('')
      setFormDraft(null)
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to delete item'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  // --- Form helpers ---

  const inputCls = 'w-full px-3 py-2 rounded-lg bg-slate-900/40 border border-slate-700 text-white text-sm'
  const labelCls = 'block text-xs text-slate-400 mb-1'
  const isEditing = selectedId !== '__new__'

  const updateDraft = (key: string, value: any) => {
    setFormDraft(prev => prev ? { ...prev, [key]: value } : prev)
  }

  const csvToArray = (text: string) => text.split(',').map(s => s.trim()).filter(Boolean)
  const arrayToCsv = (arr: any) => (Array.isArray(arr) ? arr.join(', ') : '')

  const handleToggleJsonEditor = () => {
    if (showJsonEditor) {
      // Switching from JSON to form — parse JSON into formDraft
      try {
        const parsed = JSON.parse(genericJsonText)
        setFormDraft(parsed)
        setShowJsonEditor(false)
      } catch {
        setError('Invalid JSON — fix before switching to form view')
      }
    } else {
      // Switching from form to JSON — serialize formDraft
      if (formDraft) setGenericJsonText(JSON.stringify(formDraft, null, 2))
      setShowJsonEditor(true)
    }
  }

  const renderFormActions = () => (
    <div className="flex items-center gap-2 mt-4">
      <button onClick={saveGeneric} disabled={loading}
        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white text-sm">
        <Save className="w-4 h-4" /> Save
      </button>
      <button onClick={deleteGeneric} disabled={loading || selectedId === '__new__'}
        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 disabled:opacity-60 text-white text-sm">
        <Trash2 className="w-4 h-4" /> Delete
      </button>
      <button onClick={handleToggleJsonEditor}
        className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-sm ml-auto">
        <Code2 className="w-4 h-4" /> {showJsonEditor ? 'Form View' : 'View JSON'}
      </button>
    </div>
  )

  const renderJsonFallback = () => (
    <div className="space-y-4">
      <div>
        <label className={labelCls}>JSON Payload</label>
        <textarea value={genericJsonText} onChange={(e) => setGenericJsonText(e.target.value)}
          rows={20} className={inputCls + ' font-mono'} />
      </div>
      {renderFormActions()}
    </div>
  )

  const renderKpiForm = () => {
    if (!formDraft) return null
    const thresholds = formDraft.thresholds || []
    return (
      <div className="space-y-4">
        <p className="text-xs text-slate-500">Edit KPI configuration, thresholds, and data source binding.</p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>ID</label>
            <input value={formDraft.id || ''} onChange={e => updateDraft('id', e.target.value)}
              disabled={isEditing} className={inputCls + (isEditing ? ' opacity-50' : '')} />
          </div>
          <div>
            <label className={labelCls}>Name</label>
            <input value={formDraft.name || ''} onChange={e => updateDraft('name', e.target.value)} className={inputCls} />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className={labelCls}>Domain</label>
            <input value={formDraft.domain || ''} onChange={e => updateDraft('domain', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Unit</label>
            <input value={formDraft.unit || ''} onChange={e => updateDraft('unit', e.target.value)} className={inputCls} placeholder="$, %, #" />
          </div>
          <div>
            <label className={labelCls}>Owner Role</label>
            <input value={formDraft.owner_role || ''} onChange={e => updateDraft('owner_role', e.target.value)} className={inputCls} />
          </div>
        </div>
        <div>
          <label className={labelCls}>Description</label>
          <textarea value={formDraft.description || ''} onChange={e => updateDraft('description', e.target.value)}
            rows={2} className={inputCls} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Data Product ID</label>
            <input value={formDraft.data_product_id || ''} onChange={e => updateDraft('data_product_id', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>View Name</label>
            <input value={formDraft.view_name || ''} onChange={e => updateDraft('view_name', e.target.value)} className={inputCls} />
          </div>
        </div>
        <div>
          <label className={labelCls}>Tags (comma-separated)</label>
          <input value={arrayToCsv(formDraft.tags)} onChange={e => updateDraft('tags', csvToArray(e.target.value))} className={inputCls} />
        </div>

        {/* Thresholds */}
        <div>
          <label className={labelCls}>Thresholds</label>
          <div className="space-y-2">
            {thresholds.map((t: any, i: number) => (
              <div key={i} className="flex items-center gap-2">
                <select value={t.comparison_type || 'target'} onChange={e => {
                  const next = [...thresholds]; next[i] = { ...next[i], comparison_type: e.target.value }; updateDraft('thresholds', next)
                }} className={inputCls + ' w-32'}>
                  {['qoq','yoy','mom','target','budget','greater_than','less_than'].map(v => <option key={v} value={v}>{v}</option>)}
                </select>
                <input type="number" placeholder="Green" value={t.green_threshold ?? ''} onChange={e => {
                  const next = [...thresholds]; next[i] = { ...next[i], green_threshold: e.target.value ? Number(e.target.value) : null }; updateDraft('thresholds', next)
                }} className={inputCls + ' w-24'} />
                <input type="number" placeholder="Yellow" value={t.yellow_threshold ?? ''} onChange={e => {
                  const next = [...thresholds]; next[i] = { ...next[i], yellow_threshold: e.target.value ? Number(e.target.value) : null }; updateDraft('thresholds', next)
                }} className={inputCls + ' w-24'} />
                <input type="number" placeholder="Red" value={t.red_threshold ?? ''} onChange={e => {
                  const next = [...thresholds]; next[i] = { ...next[i], red_threshold: e.target.value ? Number(e.target.value) : null }; updateDraft('thresholds', next)
                }} className={inputCls + ' w-24'} />
                <button onClick={() => { const next = thresholds.filter((_: any, j: number) => j !== i); updateDraft('thresholds', next) }}
                  className="p-1 text-slate-500 hover:text-red-400"><X className="w-4 h-4" /></button>
              </div>
            ))}
            <button onClick={() => updateDraft('thresholds', [...thresholds, { comparison_type: 'target', green_threshold: null, yellow_threshold: null, red_threshold: null }])}
              className="text-xs text-blue-400 hover:text-blue-300">+ Add Threshold</button>
          </div>
        </div>

        <div>
          <label className={labelCls}>Metadata (JSON)</label>
          <textarea value={JSON.stringify(formDraft.metadata || {}, null, 2)}
            onChange={e => { try { updateDraft('metadata', JSON.parse(e.target.value)) } catch { /* ignore parse errors while typing */ } }}
            rows={3} className={inputCls + ' font-mono'} />
        </div>
        {renderFormActions()}
      </div>
    )
  }

  const renderPrincipalForm = () => {
    if (!formDraft) return null
    return (
      <div className="space-y-4">
        <p className="text-xs text-slate-500">Edit principal profile, responsibilities, and preferences.</p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>ID</label>
            <input value={formDraft.id || ''} onChange={e => updateDraft('id', e.target.value)}
              disabled={isEditing} className={inputCls + (isEditing ? ' opacity-50' : '')} />
          </div>
          <div>
            <label className={labelCls}>Name</label>
            <input value={formDraft.name || ''} onChange={e => updateDraft('name', e.target.value)} className={inputCls} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Title</label>
            <input value={formDraft.title || ''} onChange={e => updateDraft('title', e.target.value)} className={inputCls} placeholder="CFO, CEO, Finance Manager" />
          </div>
          <div>
            <label className={labelCls}>Decision Style</label>
            <input value={formDraft.decision_style || ''} onChange={e => updateDraft('decision_style', e.target.value)} className={inputCls} placeholder="analytical, visionary, pragmatic" />
          </div>
        </div>
        <div>
          <label className={labelCls}>Description</label>
          <textarea value={formDraft.description || ''} onChange={e => updateDraft('description', e.target.value)}
            rows={2} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>Business Processes (comma-separated)</label>
          <input value={arrayToCsv(formDraft.business_processes)} onChange={e => updateDraft('business_processes', csvToArray(e.target.value))} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>KPIs (comma-separated)</label>
          <input value={arrayToCsv(formDraft.kpis)} onChange={e => updateDraft('kpis', csvToArray(e.target.value))} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>Responsibilities (comma-separated)</label>
          <input value={arrayToCsv(formDraft.responsibilities)} onChange={e => updateDraft('responsibilities', csvToArray(e.target.value))} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>Metadata (JSON)</label>
          <textarea value={JSON.stringify(formDraft.metadata || {}, null, 2)}
            onChange={e => { try { updateDraft('metadata', JSON.parse(e.target.value)) } catch { /* ignore */ } }}
            rows={3} className={inputCls + ' font-mono'} />
        </div>
        {renderFormActions()}
      </div>
    )
  }

  const renderDataProductForm = () => {
    if (!formDraft) return null
    return (
      <div className="space-y-4">
        <p className="text-xs text-slate-500">Edit data product metadata and source configuration.</p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>ID</label>
            <input value={formDraft.id || ''} onChange={e => updateDraft('id', e.target.value)}
              disabled={isEditing} className={inputCls + (isEditing ? ' opacity-50' : '')} />
          </div>
          <div>
            <label className={labelCls}>Name</label>
            <input value={formDraft.name || ''} onChange={e => updateDraft('name', e.target.value)} className={inputCls} />
          </div>
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className={labelCls}>Domain</label>
            <input value={formDraft.domain || ''} onChange={e => updateDraft('domain', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Owner</label>
            <input value={formDraft.owner || ''} onChange={e => updateDraft('owner', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Source System</label>
            <select value={formDraft.source_system || 'duckdb'} onChange={e => updateDraft('source_system', e.target.value)} className={inputCls}>
              <option value="duckdb">DuckDB</option>
              <option value="bigquery">BigQuery</option>
              <option value="postgresql">PostgreSQL</option>
            </select>
          </div>
        </div>
        <div>
          <label className={labelCls}>Description</label>
          <textarea value={formDraft.description || ''} onChange={e => updateDraft('description', e.target.value)}
            rows={2} className={inputCls} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Version</label>
            <input value={formDraft.version || ''} onChange={e => updateDraft('version', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Tags (comma-separated)</label>
            <input value={arrayToCsv(formDraft.tags)} onChange={e => updateDraft('tags', csvToArray(e.target.value))} className={inputCls} />
          </div>
        </div>
        <div>
          <label className={labelCls}>Tables (JSON)</label>
          <textarea value={JSON.stringify(formDraft.tables || {}, null, 2)}
            onChange={e => { try { updateDraft('tables', JSON.parse(e.target.value)) } catch { /* ignore */ } }}
            rows={6} className={inputCls + ' font-mono'} />
        </div>
        <div>
          <label className={labelCls}>Views (JSON)</label>
          <textarea value={JSON.stringify(formDraft.views || {}, null, 2)}
            onChange={e => { try { updateDraft('views', JSON.parse(e.target.value)) } catch { /* ignore */ } }}
            rows={6} className={inputCls + ' font-mono'} />
        </div>
        {renderFormActions()}
      </div>
    )
  }

  const renderBusinessProcessForm = () => {
    if (!formDraft) return null
    return (
      <div className="space-y-4">
        <p className="text-xs text-slate-500">Edit business process details and ownership.</p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>ID</label>
            <input value={formDraft.id || ''} onChange={e => updateDraft('id', e.target.value)}
              disabled={isEditing} className={inputCls + (isEditing ? ' opacity-50' : '')} />
          </div>
          <div>
            <label className={labelCls}>Name</label>
            <input value={formDraft.name || ''} onChange={e => updateDraft('name', e.target.value)} className={inputCls} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Domain</label>
            <input value={formDraft.domain || ''} onChange={e => updateDraft('domain', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Owner Role</label>
            <input value={formDraft.owner_role || ''} onChange={e => updateDraft('owner_role', e.target.value)} className={inputCls} />
          </div>
        </div>
        <div>
          <label className={labelCls}>Description</label>
          <textarea value={formDraft.description || ''} onChange={e => updateDraft('description', e.target.value)}
            rows={2} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>Tags (comma-separated)</label>
          <input value={arrayToCsv(formDraft.tags)} onChange={e => updateDraft('tags', csvToArray(e.target.value))} className={inputCls} />
        </div>
        <div>
          <label className={labelCls}>Metadata (JSON)</label>
          <textarea value={JSON.stringify(formDraft.metadata || {}, null, 2)}
            onChange={e => { try { updateDraft('metadata', JSON.parse(e.target.value)) } catch { /* ignore */ } }}
            rows={3} className={inputCls + ' font-mono'} />
        </div>
        {renderFormActions()}
      </div>
    )
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  // Admin client management handlers
  async function handleCreateClient() {
    const id = newClientId.trim().toLowerCase().replace(/\s+/g, '_')
    if (!id) return
    setCreatingClient(true)
    setClientCreateError(null)
    try {
      await createClient({ id, name: newClientName.trim() || id, industry: newClientIndustry.trim() })
      localStorage.setItem('a9_admin_target_client', id)
      setAdminTargetClientState(id)
      setShowNewClientForm(false)
      setNewClientId('')
      setNewClientName('')
      setNewClientIndustry('')
    } catch (err) {
      setClientCreateError(err instanceof Error ? err.message : 'Failed to create client')
    } finally {
      setCreatingClient(false)
    }
  }

  // handleExitAdmin moved to SettingsLayout OnboardingNav

  return (
    <SettingsLayout>
      <div className="p-8 font-sans min-h-full">

        {/* Admin client selector — shown in onboarding mode inside content area */}
        {adminMode && (
          <div className="mb-6 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Working on client</p>
            <div className="flex items-start gap-3 flex-wrap">
              <AdminClientSelector
                currentClientId={adminTargetClient}
                onChange={(id) => {
                  localStorage.setItem('a9_admin_target_client', id)
                  setAdminTargetClientState(id)
                  setShowNewClientForm(false)
                }}
              />
              <button
                onClick={() => setShowNewClientForm((v) => !v)}
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-dashed border-slate-600 text-slate-400 hover:text-white hover:border-slate-500 text-xs transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                New client
              </button>
            </div>
            {showNewClientForm && (
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Client ID <span className="text-slate-600">(snake_case)</span></label>
                  <input value={newClientId} onChange={(e) => setNewClientId(e.target.value)} placeholder="valvoline"
                    className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500" />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Display name</label>
                  <input value={newClientName} onChange={(e) => setNewClientName(e.target.value)} placeholder="Valvoline Inc."
                    className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500" />
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Industry <span className="text-slate-600">(optional)</span></label>
                  <input value={newClientIndustry} onChange={(e) => setNewClientIndustry(e.target.value)} placeholder="Specialty Chemicals"
                    className="w-full px-3 py-2 rounded-lg bg-slate-800 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500" />
                </div>
                <div className="sm:col-span-3 flex items-center gap-3">
                  <button onClick={handleCreateClient} disabled={!newClientId.trim() || creatingClient}
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 text-white text-sm font-medium">
                    {creatingClient ? 'Creating…' : 'Create and select'}
                  </button>
                  {clientCreateError && <p className="text-xs text-red-400">{clientCreateError}</p>}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Section header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white">{active?.label ?? 'Registry'}</h1>
            {activeClientId && (
              <div className="flex items-center gap-1.5 mt-1">
                <span className="text-xs text-slate-500">Client:</span>
                <span className="text-xs font-mono text-slate-300">{activeClientId}</span>
              </div>
            )}
          </div>
        </div>

        <div>{/* content start */}

        <div>
          {showConnectionHealth ? (
            <div className="bg-card border border-border rounded-xl p-6">
              <ConnectionHealthPanel clientId={activeClientId} />
            </div>
          ) : null}

          {showAccountability ? (
            <div className="bg-card border border-border rounded-xl p-6">
              <AccountabilityPanel clientId={activeClientId} />
            </div>
          ) : null}

          {showInterview && activeClientId ? (
            <div className="bg-card border border-border rounded-xl p-6">
              <div className="mb-4">
                <h2 className="text-lg font-semibold text-white">Assign KPI Ownership</h2>
                <p className="text-sm text-slate-400">
                  AI-guided interview to assign accountable principals to each KPI.
                </p>
              </div>
              <AccountabilityInterviewPanel clientId={activeClientId} />
            </div>
          ) : showInterview ? (
            <div className="bg-card border border-border rounded-xl p-6">
              <p className="text-sm text-slate-500 italic">Select a client to start the interview.</p>
            </div>
          ) : null}

          <div className={showConnectionHealth || showAccountability || showInterview ? 'hidden' : ''}>
          <div className="bg-card border border-border rounded-xl p-6">
            <div className="flex items-start justify-between gap-4 mb-4">
              <div>
                <h2 className="text-lg font-semibold text-white">{active.label}</h2>
                <p className="text-sm text-slate-400">{active.editable ? 'Create, edit, and delete entries.' : 'View entries.'}</p>
              </div>

              <div className="flex items-center gap-2">
                {loading ? (
                  <div className="inline-flex items-center gap-2 text-slate-400">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Loading</span>
                  </div>
                ) : null}

                {active.editable && registryKey === 'data-products' ? (
                  <Link
                    to="/settings/onboarding"
                    className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium"
                  >
                    <Plus className="w-4 h-4" />
                    Onboard Data Product
                  </Link>
                ) : active.editable ? (
                  <button
                    onClick={onNewItem}
                    className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white text-sm"
                  >
                    <Plus className="w-4 h-4" />
                    New
                  </button>
                ) : null}
              </div>
            </div>

            {error ? (
              <div className="mb-4 p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-200 text-sm">{error}</div>
            ) : null}

            <div className="mb-4">
              <input
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                placeholder={`Search ${active.label}...`}
                className="w-full px-3 py-2 rounded-lg bg-slate-900/40 border border-slate-700 text-white text-sm"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
              <div className="border border-border rounded-xl overflow-hidden">
                <div className="px-4 py-3 bg-slate-900/40 border-b border-border flex items-center justify-between">
                  <div className="text-sm font-semibold text-white">Table</div>
                  <div className="text-xs text-slate-400">{filteredItems.length}</div>
                </div>
                <div className="max-h-[560px] overflow-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-slate-950/90">
                      <tr className="border-b border-border/60">
                        {columnsForRegistry(registryKey).map((col) => (
                          <th
                            key={col.key}
                            className={
                              'px-3 py-2 text-left text-xs font-semibold text-slate-300 ' + (col.widthClass || '')
                            }
                          >
                            {col.label}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {filteredItems.map((row) => {
                        const id = rowId(row)
                        const isSelected = selectedId === id
                        return (
                          <tr
                            key={id}
                            className={
                              'border-b border-border/60 cursor-pointer ' +
                              (isSelected ? 'bg-slate-800/50' : 'hover:bg-slate-800/30')
                            }
                            onClick={() => onSelect(row)}
                          >
                            {columnsForRegistry(registryKey).map((col) => (
                              <td key={col.key} className="px-3 py-2 text-slate-100 truncate max-w-[260px]">
                                {col.render(row) || '—'}
                              </td>
                            ))}
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>

                  {filteredItems.length === 0 && !loading ? (
                    <div className="p-4 text-sm text-slate-400">No items found.</div>
                  ) : null}
                </div>
              </div>

              <div className="border border-border rounded-xl p-4">
                {!selectedId ? (
                  <div className="text-sm text-slate-400">Select an item or create new.</div>
                ) : (
                  <>
                    {/* View/Edit Form Container */}
                    {registryKey === 'glossary' && termDraft ? (
                      <div className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-xs text-slate-400 mb-1">Name</label>
                            <input
                              value={termDraft.name}
                              onChange={(e) => setTermDraft({ ...termDraft, name: e.target.value })}
                              className="w-full px-3 py-2 rounded-lg bg-slate-900/40 border border-slate-700 text-white text-sm"
                            />
                          </div>

                          <div>
                            <label className="block text-xs text-slate-400 mb-1">Description</label>
                            <input
                              value={termDraft.description || ''}
                              onChange={(e) => setTermDraft({ ...termDraft, description: e.target.value })}
                              className="w-full px-3 py-2 rounded-lg bg-slate-900/40 border border-slate-700 text-white text-sm"
                            />
                          </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-xs text-slate-400 mb-1">Synonyms (one per line)</label>
                            <textarea
                              value={termSynonymsText}
                              onChange={(e) => setTermSynonymsText(e.target.value)}
                              rows={8}
                              className="w-full px-3 py-2 rounded-lg bg-slate-900/40 border border-slate-700 text-white text-sm font-mono"
                            />
                          </div>

                          <div>
                            <label className="block text-xs text-slate-400 mb-1">Technical mappings (JSON)</label>
                            <textarea
                              value={termMappingsText}
                              onChange={(e) => setTermMappingsText(e.target.value)}
                              rows={8}
                              className="w-full px-3 py-2 rounded-lg bg-slate-900/40 border border-slate-700 text-white text-sm font-mono"
                            />
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={saveGlossary}
                            disabled={loading}
                            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white text-sm"
                          >
                            <Save className="w-4 h-4" />
                            Save
                          </button>

                          <button
                            onClick={deleteGlossary}
                            disabled={loading || selectedId === '__new__'}
                            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 disabled:opacity-60 text-white text-sm"
                          >
                            <Trash2 className="w-4 h-4" />
                            Delete
                          </button>

                          <div className="text-xs text-slate-500">
                            Raw JSON is hidden in this view to keep maintenance table-first. (We can add an “Advanced” toggle later.)
                          </div>
                        </div>
                      </div>
                    ) : showJsonEditor ? (
                      renderJsonFallback()
                    ) : registryKey === 'kpis' ? (
                      renderKpiForm()
                    ) : registryKey === 'principals' ? (
                      renderPrincipalForm()
                    ) : registryKey === 'data-products' ? (
                      renderDataProductForm()
                    ) : registryKey === 'business-processes' ? (
                      renderBusinessProcessForm()
                    ) : (
                      renderJsonFallback()
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
          </div>{/* end registry panel wrapper */}
        </div>
      </div>{/* content start */}
      </div>{/* p-8 */}
    </SettingsLayout>
  )
}
