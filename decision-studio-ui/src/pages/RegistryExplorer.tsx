import { type ComponentType, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, BookOpen, Box, Briefcase, Database, KeyRound, Loader2, Save, Trash2, Plus } from 'lucide-react'
import {
  type BusinessTerm,
  listGlossaryTerms,
  createGlossaryTerm,
  updateGlossaryTerm,
  deleteGlossaryTerm,
  listBusinessProcesses,
  listDataProducts,
  listKpis,
  listPrincipals,
  createKpi, replaceKpi, deleteKpi,
  createPrincipal, replacePrincipal, deletePrincipal,
  createDataProduct, replaceDataProduct, deleteDataProduct,
  createBusinessProcess, replaceBusinessProcess, deleteBusinessProcess,
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
    key: 'glossary',
    label: 'Business Glossary',
    icon: BookOpen,
    colorClass: 'text-purple-400 bg-purple-500/10',
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
    key: 'business-processes',
    label: 'Business Processes',
    icon: Briefcase,
    colorClass: 'text-amber-400 bg-amber-500/10',
    editable: true,
  },
  {
    key: 'principals',
    label: 'Principals',
    icon: KeyRound,
    colorClass: 'text-slate-300 bg-slate-500/10',
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

export function RegistryExplorer() {
  const [registryKey, setRegistryKey] = useState<RegistryKey>('glossary')
  const active = useMemo(() => REGISTRIES.find((r) => r.key === registryKey)!, [registryKey])

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

      // Reset glossary state
      setTermDraft(null)
      setTermSynonymsText('')
      setTermMappingsText('')

      setSearchText('')

      try {
        let data: any[] = []

        if (registryKey === 'glossary') {
          data = await listGlossaryTerms()
        } else if (registryKey === 'data-products') {
          data = await listDataProducts()
        } else if (registryKey === 'kpis') {
          data = await listKpis()
        } else if (registryKey === 'business-processes') {
          data = await listBusinessProcesses()
        } else if (registryKey === 'principals') {
          data = await listPrincipals()
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
      // For other registries, load into generic JSON editor
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
      // Template for generic items
      let template: any = { id: 'new_item', name: 'New Item' }

      if (registryKey === 'kpis') {
        template = {
          id: 'new_kpi',
          name: 'New KPI',
          domain: 'General',
          description: '',
          unit: '',
          data_product_id: '',
          owner_role: '',
          sql_query: 'SELECT * FROM ...',
          thresholds: []
        }
      } else if (registryKey === 'principals') {
        template = {
          id: 'new_principal',
          name: 'New Principal',
          role: 'Role',
          title: 'Title',
          department: '',
          preferences: {}
        }
      }

      setGenericJsonText(JSON.stringify(template, null, 2))
    }
  }

  const reload = async () => {
    let data: any[] = []
    if (registryKey === 'glossary') data = await listGlossaryTerms()
    if (registryKey === 'data-products') data = await listDataProducts()
    if (registryKey === 'kpis') data = await listKpis()
    if (registryKey === 'business-processes') data = await listBusinessProcesses()
    if (registryKey === 'principals') data = await listPrincipals()
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
    if (!genericJsonText) return

    let payload: any
    try {
      payload = JSON.parse(genericJsonText)
    } catch (e) {
      setError('Invalid JSON format')
      return
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
      if (registryKey === 'kpis') await deleteKpi(selectedId)
      else if (registryKey === 'principals') await deletePrincipal(selectedId)
      else if (registryKey === 'data-products') await deleteDataProduct(selectedId)
      else if (registryKey === 'business-processes') await deleteBusinessProcess(selectedId)

      await reload()
      setSelectedId(null)
      setGenericJsonText('')
    } catch (e) {
      const message = e instanceof Error ? e.message : 'Failed to delete item'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground p-8 font-sans">
      <header className="mb-8 flex justify-between items-center max-w-6xl mx-auto">
        <div className="flex items-center gap-4">
          <Link to="/admin" className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Registry Explorer</h1>
            <p className="text-sm text-slate-400">Manage registry entities</p>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-[260px_1fr] gap-6">
          <div className="bg-card border border-border rounded-xl p-3">
            <div className="space-y-1">
              {REGISTRIES.map((r) => {
                const Icon = r.icon
                const isActive = r.key === registryKey
                return (
                  <button
                    key={r.key}
                    onClick={() => setRegistryKey(r.key)}
                    className={
                      'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ' +
                      (isActive ? 'bg-slate-800/60 border border-slate-700' : 'hover:bg-slate-800/40')
                    }
                  >
                    <span className={
                      'inline-flex items-center justify-center w-9 h-9 rounded-lg ' + r.colorClass
                    }>
                      <Icon className="w-5 h-5" />
                    </span>
                    <div className="flex-1">
                      <div className="text-sm font-semibold text-white">{r.label}</div>
                      <div className="text-xs text-slate-400">{r.editable ? 'CRUD' : 'Read-only'}</div>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

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

                {active.editable ? (
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
                    ) : (
                      /* Generic JSON Editor for other registries */
                      <div className="space-y-4">
                        <div className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-200 text-xs mb-4">
                          This registry uses a generic JSON editor. Ensure the <code>id</code> field is present and unique.
                        </div>

                        <div>
                          <label className="block text-xs text-slate-400 mb-1">JSON Payload</label>
                          <textarea
                            value={genericJsonText}
                            onChange={(e) => setGenericJsonText(e.target.value)}
                            rows={20}
                            className="w-full px-3 py-2 rounded-lg bg-slate-900/40 border border-slate-700 text-white text-sm font-mono"
                          />
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={saveGeneric}
                            disabled={loading}
                            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white text-sm"
                          >
                            <Save className="w-4 h-4" />
                            Save
                          </button>

                          <button
                            onClick={deleteGeneric}
                            disabled={loading || selectedId === '__new__'}
                            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 disabled:opacity-60 text-white text-sm"
                          >
                            <Trash2 className="w-4 h-4" />
                            Delete
                          </button>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
