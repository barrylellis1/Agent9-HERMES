import { type ComponentType, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, BookOpen, Box, Briefcase, Code2, Database, KeyRound, Loader2, Save, Trash2, Plus, X, Building2 } from 'lucide-react'
import { BrandLogo } from '../components/BrandLogo'
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

export function RegistryExplorer() {
  const [registryKey, setRegistryKey] = useState<RegistryKey>('glossary')
  const active = useMemo(() => REGISTRIES.find((r) => r.key === registryKey)!, [registryKey])
  const workspaceId = localStorage.getItem('a9_client_id') ?? 'unknown'

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
      if (registryKey === 'kpis') await deleteKpi(selectedId)
      else if (registryKey === 'principals') await deletePrincipal(selectedId)
      else if (registryKey === 'data-products') await deleteDataProduct(selectedId)
      else if (registryKey === 'business-processes') await deleteBusinessProcess(selectedId)

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

  return (
    <div className="min-h-screen bg-background text-foreground p-8 font-sans">
      <header className="mb-6 flex justify-between items-center max-w-6xl mx-auto">
        <div className="flex items-center gap-4">
          <Link to="/dashboard" className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Settings</h1>
            <p className="text-sm text-slate-400">Registry management &amp; data product onboarding</p>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900/60">
            <Building2 className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs text-slate-400">Workspace</span>
            <span className="text-xs font-semibold text-white font-mono">{workspaceId}</span>
          </div>
        </div>
        <BrandLogo size={32} />
      </header>

      <main className="max-w-6xl mx-auto">
        {/* Horizontal registry tabs */}
        <div className="flex items-center gap-1 mb-6 border-b border-slate-800 pb-0">
          <Link
            to="/settings/company-profile"
            className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600 mr-2"
          >
            <Building2 className="w-4 h-4" />
            Company Profile
          </Link>
          {REGISTRIES.map((r) => {
            const Icon = r.icon
            const isActive = r.key === registryKey
            return (
              <button
                key={r.key}
                onClick={() => setRegistryKey(r.key)}
                className={
                  'flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ' +
                  (isActive
                    ? 'border-indigo-400 text-white'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-600')
                }
              >
                <Icon className="w-4 h-4" />
                {r.label}
              </button>
            )
          })}
        </div>

        <div>
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
        </div>
      </main>
    </div>
  )
}
