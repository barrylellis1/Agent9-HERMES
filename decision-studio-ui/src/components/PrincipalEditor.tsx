/**
 * PrincipalEditor — extract-then-extend of RegistryExplorer.tsx's inline
 * principals tab (formerly `renderPrincipalForm()` + the shared generic
 * table). Exposes two pieces:
 *
 *   PrincipalCardList — richer card-based summary (avatar/title/decision
 *     style/business-process count/KPI count) used by both the Settings
 *     principals tab and the onboarding wizard's Day 2 step.
 *   PrincipalForm — the edit form, extracted as a self-contained component
 *     (owns its own fetch/save/delete) so it can be embedded in a modal
 *     from PrincipalCardList without depending on RegistryExplorer's state.
 *
 * Note: PrincipalProfile has no avatar/avatar_url field in the registry
 * model (src/registry/models/principal.py) — cards use an initials-based
 * placeholder instead of inventing a new backend field.
 */
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Loader2, Mail, Plus, Save, Search, ShieldCheck, Trash2, X } from 'lucide-react'
import {
  type KPIAccountability,
  createPrincipal,
  deletePrincipal,
  getPrincipal,
  listAccountabilities,
  listPrincipals,
  replacePrincipal,
} from '../api/client'

interface PrincipalRecord {
  id: string
  name: string
  title?: string
  description?: string
  decision_style?: string
  /** Workflow-stage default. STRICTLY a registry attribute set here by an
   *  admin — never inferred from title/name anywhere in this codebase. */
  workflow_role?: 'framer' | 'decision_maker'
  business_processes?: string[]
  kpis?: string[]
  responsibilities?: string[]
  email?: string | null
  metadata?: Record<string, unknown>
  [key: string]: any
}

function initials(name: string): string {
  const parts = (name || '').trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

// Matches Login.tsx's exact check for which principals land in read-write
// "maintenance" mode vs read-only "governance" mode after onboarding.
function isSettingsAdmin(p: PrincipalRecord): boolean {
  return p.metadata?.settings_admin === true || p.metadata?.settings_admin === 'true'
}

// ── PrincipalForm ──────────────────────────────────────────────────────────

export function PrincipalForm({
  clientId,
  principalId,
  onSaved,
  onDeleted,
}: {
  clientId: string
  principalId?: string
  onSaved?: () => void
  onDeleted?: () => void
}) {
  const isEditing = Boolean(principalId)
  const [draft, setDraft] = useState<PrincipalRecord>(() => ({
    id: '', name: '', title: '', description: '',
    business_processes: [], kpis: [], responsibilities: [],
    decision_style: 'analytical', workflow_role: 'framer', email: '', metadata: {},
  }))
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!principalId) return
    let canceled = false
    setLoading(true)
    getPrincipal(principalId, clientId)
      .then((data) => { if (!canceled) setDraft({ ...data }) })
      .catch((e: unknown) => { if (!canceled) setError(e instanceof Error ? e.message : 'Failed to load principal') })
      .finally(() => { if (!canceled) setLoading(false) })
    return () => { canceled = true }
  }, [principalId, clientId])

  const update = (key: string, value: any) => setDraft((prev) => ({ ...prev, [key]: value }))
  const csvToArray = (text: string) => text.split(',').map((s) => s.trim()).filter(Boolean)
  const arrayToCsv = (arr: any) => (Array.isArray(arr) ? arr.join(', ') : '')

  const handleSave = async () => {
    if (!draft.id || !draft.name) {
      setError('ID and Name are required')
      return
    }
    setSaving(true)
    setError(null)
    try {
      if (isEditing) await replacePrincipal(draft.id, draft)
      else await createPrincipal(draft)
      onSaved?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save principal')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!principalId) return
    setSaving(true)
    setError(null)
    try {
      await deletePrincipal(principalId, clientId)
      onDeleted?.()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to delete principal')
    } finally {
      setSaving(false)
    }
  }

  const inputCls = 'w-full px-3 py-2 rounded-lg bg-slate-900/40 border border-slate-700 text-white text-sm'
  const labelCls = 'block text-xs text-slate-400 mb-1'

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-slate-400 text-sm py-8 justify-center">
        <Loader2 className="w-4 h-4 animate-spin" /> Loading…
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="p-3 rounded-lg border border-severity-critical/30 bg-severity-critical/10 text-severity-critical text-sm">{error}</div>
      )}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelCls}>ID</label>
          <input value={draft.id || ''} onChange={(e) => update('id', e.target.value)}
            disabled={isEditing} className={inputCls + (isEditing ? ' opacity-50' : '')} />
        </div>
        <div>
          <label className={labelCls}>Name</label>
          <input value={draft.name || ''} onChange={(e) => update('name', e.target.value)} className={inputCls} />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className={labelCls}>Title</label>
          <input value={draft.title || ''} onChange={(e) => update('title', e.target.value)} className={inputCls} placeholder="CFO, CEO, Finance Manager" />
        </div>
        <div>
          <label className={labelCls}>Decision Style</label>
          <input value={draft.decision_style || ''} onChange={(e) => update('decision_style', e.target.value)} className={inputCls} placeholder="analytical, visionary, pragmatic" />
        </div>
      </div>
      <div>
        <label className={labelCls}>Workflow Role</label>
        <select value={draft.workflow_role || 'framer'} onChange={(e) => update('workflow_role', e.target.value)} className={inputCls}>
          <option value="framer">Framer — stewards SA → DA → SF, runs refinement</option>
          <option value="decision_maker">Decision Maker — reviews a distilled brief, approves</option>
        </select>
        <p className="text-xs text-slate-600 mt-1">
          Sets the default landing view only, never a permission — either role can always reach the
          full pipeline.
        </p>
      </div>
      <div>
        <label className={labelCls}>Email <span className="text-slate-600">(required for briefing delivery)</span></label>
        <input type="email" value={draft.email || ''} onChange={(e) => update('email', e.target.value)} className={inputCls} placeholder="cfo@client.com" />
      </div>
      <div>
        <label className={labelCls}>Description</label>
        <textarea value={draft.description || ''} onChange={(e) => update('description', e.target.value)} rows={2} className={inputCls} />
      </div>
      <div>
        <label className={labelCls}>Business Processes (comma-separated)</label>
        <input value={arrayToCsv(draft.business_processes)} onChange={(e) => update('business_processes', csvToArray(e.target.value))} className={inputCls} />
      </div>
      <div>
        <label className={labelCls}>KPIs (comma-separated)</label>
        <input value={arrayToCsv(draft.kpis)} onChange={(e) => update('kpis', csvToArray(e.target.value))} className={inputCls} />
      </div>
      <div>
        <label className={labelCls}>Responsibilities (comma-separated)</label>
        <input value={arrayToCsv(draft.responsibilities)} onChange={(e) => update('responsibilities', csvToArray(e.target.value))} className={inputCls} />
      </div>
      <div className="flex items-start gap-2.5 p-3 rounded-lg border border-slate-800 bg-slate-900/30">
        <input
          type="checkbox"
          id={`settings-admin-${draft.id || 'new'}`}
          checked={isSettingsAdmin(draft)}
          onChange={(e) => update('metadata', { ...(draft.metadata ?? {}), settings_admin: e.target.checked ? 'true' : 'false' })}
          className="mt-0.5 w-4 h-4 rounded border-slate-600 bg-slate-900 text-indigo-500 focus:ring-indigo-500"
        />
        <label htmlFor={`settings-admin-${draft.id || 'new'}`} className="text-sm text-slate-300 cursor-pointer">
          <span className="font-medium text-white">Grant Settings Admin</span>
          <span className="block text-xs text-slate-500 mt-0.5">
            When this principal logs in normally (not as System Admin), they can maintain the KPI/registry
            data instead of getting read-only access. At least one principal per client needs this checked,
            or nobody will be able to edit KPIs after onboarding is complete.
          </span>
        </label>
      </div>
      <div className="flex items-center gap-2 pt-2">
        <button onClick={handleSave} disabled={saving}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-60 text-white text-sm">
          <Save className="w-4 h-4" /> Save
        </button>
        {isEditing && (
          <button onClick={handleDelete} disabled={saving}
            className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 disabled:opacity-60 text-white text-sm">
            <Trash2 className="w-4 h-4" /> Delete
          </button>
        )}
      </div>
    </div>
  )
}

// ── PrincipalCardList ───────────────────────────────────────────────────────

export function PrincipalCardList({ clientId }: { clientId: string }) {
  const [principals, setPrincipals] = useState<PrincipalRecord[]>([])
  const [accountabilities, setAccountabilities] = useState<KPIAccountability[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null) // '__new__' for create
  const [searchText, setSearchText] = useState('')

  // Escape closes the edit modal -- it already had backdrop-click and an X
  // button, but no keyboard path (2026-08-29 audit P2). Only listens while
  // the modal is actually open.
  useEffect(() => {
    if (!editingId) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setEditingId(null)
    }
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [editingId])

  const load = useCallback(async () => {
    if (!clientId) return
    setLoading(true)
    setError(null)
    try {
      const [ps, accts] = await Promise.all([
        listPrincipals(clientId),
        listAccountabilities(clientId).catch(() => [] as KPIAccountability[]),
      ])
      setPrincipals(Array.isArray(ps) ? ps : [])
      setAccountabilities(Array.isArray(accts) ? accts : [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load principals')
    } finally {
      setLoading(false)
    }
  }, [clientId])

  useEffect(() => { void load() }, [load])

  // Cross-reference accountability rows to compute a per-principal KPI count
  // client-side — no new backend endpoint needed.
  const kpiCountByPrincipal = useMemo(() => {
    const counts: Record<string, number> = {}
    for (const a of accountabilities) {
      counts[a.principal_id] = (counts[a.principal_id] ?? 0) + 1
    }
    return counts
  }, [accountabilities])

  const filteredPrincipals = useMemo(() => {
    const q = searchText.trim().toLowerCase()
    if (!q) return principals
    return principals.filter((p) => {
      const haystack = `${p.id} ${p.name} ${p.title ?? ''} ${p.description ?? ''}`.toLowerCase()
      return haystack.includes(q)
    })
  }, [principals, searchText])

  const adminCount = useMemo(() => principals.filter(isSettingsAdmin).length, [principals])

  if (!clientId) {
    return <p className="text-sm text-slate-500 italic py-8 text-center">Select a client workspace first.</p>
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white">Principals</h2>
          <p className="text-sm text-slate-400">
            The C-level and operational leaders who will use Agent9. Each needs a name, title, and email.
          </p>
        </div>
        <button
          onClick={() => setEditingId('__new__')}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium"
        >
          <Plus className="w-4 h-4" /> Add Principal
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg border border-severity-critical/30 bg-severity-critical/10 text-severity-critical text-sm">{error}</div>
      )}

      {principals.length > 0 && adminCount === 0 && (
        <div className="mb-4 p-3 rounded-lg border border-severity-warning/40 bg-severity-warning/30 text-severity-warning text-sm">
          <span className="font-medium">No principal has Settings Admin rights yet.</span>{' '}
          Once onboarding is complete and this client logs in normally, nobody will be able to maintain
          KPIs or the registry unless at least one principal below has "Grant Settings Admin" checked.
        </div>
      )}

      {principals.length > 0 && (
        <div className="relative mb-4">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder="Search principals..."
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-slate-900/40 border border-slate-700 text-white text-sm"
          />
        </div>
      )}

      {loading && principals.length === 0 ? (
        <div className="flex items-center gap-2 text-slate-400 text-sm py-8 justify-center">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading principals…
        </div>
      ) : principals.length === 0 ? (
        <p className="text-sm text-slate-500 italic py-8 text-center">No principals yet — add the first one.</p>
      ) : filteredPrincipals.length === 0 ? (
        <p className="text-sm text-slate-500 italic py-8 text-center">No principals match "{searchText}".</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredPrincipals.map((p) => {
            const bpCount = (p.business_processes ?? []).length
            const kpiCount = kpiCountByPrincipal[p.id] ?? 0
            return (
              <button
                key={p.id}
                onClick={() => setEditingId(p.id)}
                className="text-left p-4 rounded-xl border border-slate-800 bg-slate-900/40 hover:border-indigo-500/50 hover:bg-slate-900/70 transition-colors"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-300 text-sm font-semibold shrink-0">
                    {initials(p.name)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-white truncate">{p.name}</p>
                    <p className="text-xs text-slate-400 truncate">{p.title || '—'}</p>
                  </div>
                  {isSettingsAdmin(p) && (
                    <span title="Has Settings Admin rights" className="inline-flex items-center gap-1 text-indigo-400 shrink-0">
                      <ShieldCheck className="w-4 h-4" />
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-2 text-xs">
                  {p.decision_style && (
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300">{p.decision_style}</span>
                  )}
                  <span
                    className={`px-2 py-0.5 rounded ${p.workflow_role === 'decision_maker' ? 'bg-severity-opportunity/40 text-severity-opportunity' : 'bg-slate-800 text-slate-400'}`}
                  >
                    {p.workflow_role === 'decision_maker' ? 'Decision Maker' : 'Framer'}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                    {bpCount} process{bpCount === 1 ? '' : 'es'}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                    {kpiCount} KPI{kpiCount === 1 ? '' : 's'}
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-1.5 text-xs">
                  {p.email ? (
                    <span className="inline-flex items-center gap-1 text-severity-opportunity">
                      <Mail className="w-3 h-3" /> {p.email}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-severity-warning">
                      <Mail className="w-3 h-3" /> No email — excluded from briefings
                    </span>
                  )}
                </div>
              </button>
            )
          })}
        </div>
      )}

      {editingId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => setEditingId(null)}
        >
          <div
            className="w-full max-w-2xl max-h-[85vh] overflow-y-auto rounded-xl border border-slate-800 bg-slate-950 p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-semibold text-white">
                {editingId === '__new__' ? 'New Principal' : 'Edit Principal'}
              </h3>
              <button onClick={() => setEditingId(null)} className="text-slate-500 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>
            <PrincipalForm
              clientId={clientId}
              principalId={editingId === '__new__' ? undefined : editingId}
              onSaved={() => {
                setEditingId(null)
                void load()
              }}
              onDeleted={() => {
                setEditingId(null)
                void load()
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
