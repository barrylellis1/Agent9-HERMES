import { useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Search,
  Sparkles,
  XCircle,
  FileText,
  Building2,
  Brain,
} from 'lucide-react'
import {
  researchCompanyKpiProfile,
  commitKpiTemplates,
  type CompanyKPIProfile,
  type TemplateKPI,
  type AcceptedTemplateKPI,
  type BenchmarkSource,
  type CommitTemplatesResponse,
} from '../api/client'
import { getToolTargetClientId, isAdminMode } from '../utils/adminMode'
import { SettingsLayout } from '../components/SettingsLayout'

type FlowState = 'input' | 'researching' | 'review' | 'committed' | 'error'

// ─────────────────────────────────────────────────
// Source badge — M1 trust provenance
// ─────────────────────────────────────────────────
function SourceBadge({ source }: { source: BenchmarkSource | null }) {
  if (!source) {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-500 border border-slate-700">
        No benchmark
      </span>
    )
  }
  const config: Record<BenchmarkSource, { icon: typeof FileText; label: string; classes: string }> = {
    filing: {
      icon: FileText,
      label: 'Company filing',
      classes: 'bg-emerald-950/60 text-emerald-300 border-emerald-700/50',
    },
    peer: {
      icon: Building2,
      label: 'Industry peer',
      classes: 'bg-blue-950/60 text-blue-300 border-blue-700/50',
    },
    inferred: {
      icon: Brain,
      label: 'Inferred',
      classes: 'bg-amber-950/60 text-amber-300 border-amber-700/50',
    },
  }
  const cfg = config[source]
  const Icon = cfg.icon
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs border ${cfg.classes}`}>
      <Icon className="w-3 h-3" />
      {cfg.label}
    </span>
  )
}

// ─────────────────────────────────────────────────
// State 2 — Research progress
// ─────────────────────────────────────────────────
function ResearchProgress({ companyName }: { companyName: string }) {
  const beats = [
    { label: 'Searching public filings & annual reports', icon: FileText },
    { label: 'Mapping business segments and operating metrics', icon: Building2 },
    { label: 'Gathering industry peer benchmarks', icon: Search },
    { label: 'Reviewing strategic priorities from investor communications', icon: Sparkles },
  ]
  return (
    <div className="bg-card border border-border rounded-xl p-8">
      <div className="flex items-center gap-3 mb-6">
        <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
        <div>
          <h3 className="text-lg font-semibold text-white">Researching {companyName}</h3>
          <p className="text-sm text-slate-400">This typically takes 30–60 seconds.</p>
        </div>
      </div>
      <ul className="space-y-3">
        {beats.map((beat) => {
          const Icon = beat.icon
          return (
            <li key={beat.label} className="flex items-center gap-3 text-sm text-slate-300">
              <Icon className="w-4 h-4 text-indigo-400 flex-shrink-0" />
              <span>{beat.label}</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

// ─────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────
export function KPIIntelligence() {
  const clientId = getToolTargetClientId()
  const adminMode = isAdminMode()

  const [state, setState] = useState<FlowState>('input')
  const [errorMsg, setErrorMsg] = useState<string>('')

  // Input form
  const [companyName, setCompanyName] = useState('')
  const [industryHint, setIndustryHint] = useState('')
  const [subSector, setSubSector] = useState('')
  const [businessDescription, setBusinessDescription] = useState('')
  const [maxKpis, setMaxKpis] = useState(15)

  // Research result
  const [profile, setProfile] = useState<CompanyKPIProfile | null>(null)
  // Accept toggles — Set of KPI indices to commit
  const [accepted, setAccepted] = useState<Set<number>>(new Set())
  // Per-row edits (name, domain, definition, benchmark range)
  const [edits, setEdits] = useState<Record<number, Partial<TemplateKPI>>>({})
  // Track which KPI rows are in edit mode
  const [editingIdx, setEditingIdx] = useState<number | null>(null)

  // Commit result
  const [commitResult, setCommitResult] = useState<CommitTemplatesResponse | null>(null)

  const canSubmit = companyName.trim().length > 0 && clientId.length > 0

  async function handleResearch() {
    if (!canSubmit) return
    setState('researching')
    setErrorMsg('')
    try {
      const res = await researchCompanyKpiProfile({
        company_name: companyName.trim(),
        client_id: clientId,
        industry_hint: industryHint.trim() || undefined,
        sub_sector: subSector.trim() || undefined,
        business_description: businessDescription.trim() || undefined,
        max_kpis: maxKpis,
      })
      if (res.status === 'error' || !res.profile) {
        setErrorMsg(res.error || 'Research failed unexpectedly.')
        setState('error')
        return
      }
      setProfile(res.profile)
      // Default: accept all KPIs the agent returned
      setAccepted(new Set(res.profile.template_kpis.map((_, i) => i)))
      setEdits({})
      setState('review')
    } catch (exc) {
      setErrorMsg(exc instanceof Error ? exc.message : String(exc))
      setState('error')
    }
  }

  function toggleAccept(idx: number) {
    setAccepted((prev) => {
      const next = new Set(prev)
      if (next.has(idx)) {
        next.delete(idx)
      } else {
        next.add(idx)
      }
      return next
    })
  }

  function updateEdit(idx: number, field: keyof TemplateKPI, value: string) {
    setEdits((prev) => ({
      ...prev,
      [idx]: { ...prev[idx], [field]: value },
    }))
  }

  const acceptedKpis: AcceptedTemplateKPI[] = useMemo(() => {
    if (!profile) return []
    return profile.template_kpis
      .map((kpi, idx) => ({ kpi, idx }))
      .filter(({ idx }) => accepted.has(idx))
      .map(({ kpi, idx }) => {
        const editOverrides = edits[idx] || {}
        return {
          ...kpi,
          ...editOverrides,
        } as AcceptedTemplateKPI
      })
  }, [profile, accepted, edits])

  async function handleCommit() {
    if (acceptedKpis.length === 0) {
      setErrorMsg('Accept at least one KPI before committing.')
      return
    }
    setErrorMsg('')
    try {
      const res = await commitKpiTemplates({
        client_id: clientId,
        accepted_kpis: acceptedKpis,
        created_by: 'kpi_intelligence_ui',
      })
      setCommitResult(res)
      setState('committed')
    } catch (exc) {
      setErrorMsg(exc instanceof Error ? exc.message : String(exc))
    }
  }

  function handleReset() {
    setState('input')
    setCompanyName('')
    setIndustryHint('')
    setSubSector('')
    setBusinessDescription('')
    setProfile(null)
    setAccepted(new Set())
    setEdits({})
    setEditingIdx(null)
    setCommitResult(null)
    setErrorMsg('')
  }

  return (
    <SettingsLayout>
    <div className="p-8 font-sans min-h-full">
      <header className="mb-6 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <Link to="/settings" className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">KPI Intelligence</h1>
            <p className="text-sm text-slate-400">
              Research a company's public footprint and generate benchmark-anchored KPI templates
            </p>
          </div>
          {clientId && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-indigo-700/50 bg-indigo-950/40">
              <span className="text-xs text-indigo-400">Client</span>
              <span className="text-xs font-semibold text-indigo-300 font-mono">{clientId}</span>
            </div>
          )}
        </div>
      </header>

      <main className="space-y-6">
        {/* No client selected — block */}
        {!clientId && (
          <div className="bg-amber-950/30 border border-amber-700/50 rounded-xl p-6 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
            <p className="text-sm text-amber-200">
              {adminMode
                ? 'Select or create a client workspace in Settings before researching KPI templates.'
                : 'Select a workspace client before researching KPI templates. Use the workspace selector in the Situation Console.'}
            </p>
          </div>
        )}

        {/* State 1 — Input */}
        {state === 'input' && clientId && (
          <div className="bg-card border border-border rounded-xl p-8 space-y-5">
            <div>
              <h2 className="text-lg font-semibold text-white mb-1">Step 1 — Describe the company</h2>
              <p className="text-sm text-slate-400">
                Tell the agent what to research. A clear sub-sector and one-line description produce sharper templates.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Company name *</label>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="e.g. Valvoline Inc."
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Industry hint</label>
                <input
                  type="text"
                  value={industryHint}
                  onChange={(e) => setIndustryHint(e.target.value)}
                  placeholder="e.g. Specialty Chemicals"
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Sub-sector</label>
                <input
                  type="text"
                  value={subSector}
                  onChange={(e) => setSubSector(e.target.value)}
                  placeholder="e.g. Industrial Lubricants"
                  className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Business description</label>
              <textarea
                value={businessDescription}
                onChange={(e) => setBusinessDescription(e.target.value)}
                placeholder="One line — what this business actually does that's distinctive. e.g. 'B2B distributor of industrial lubricants to manufacturing accounts across North America.'"
                rows={2}
                maxLength={400}
                className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm resize-none focus:outline-none focus:border-indigo-500"
              />
              <p className="mt-1 text-xs text-slate-500">{businessDescription.length}/400</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Target KPI count</label>
              <input
                type="number"
                value={maxKpis}
                onChange={(e) => setMaxKpis(Math.max(5, Math.min(30, parseInt(e.target.value) || 15)))}
                min={5}
                max={30}
                className="w-32 px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
              <span className="ml-3 text-xs text-slate-500">5–30; agent may return fewer</span>
            </div>

            <div className="pt-2 flex items-center justify-end gap-3">
              <button
                onClick={handleResearch}
                disabled={!canSubmit}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-white text-sm font-semibold"
              >
                <Sparkles className="w-4 h-4" />
                Research company
              </button>
            </div>
          </div>
        )}

        {/* State 2 — Researching */}
        {state === 'researching' && <ResearchProgress companyName={companyName} />}

        {/* State 3 — Review */}
        {state === 'review' && profile && (
          <>
            <div className="bg-card border border-border rounded-xl p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-white mb-1">
                    Step 2 — Review {profile.template_kpis.length} suggested KPIs
                  </h2>
                  <p className="text-sm text-slate-400">
                    Accept, reject, or edit. Only checked rows are written to the registry on commit.
                  </p>
                </div>
                <div className="text-right text-xs text-slate-400">
                  <p>
                    Industry inferred:{' '}
                    <span className="text-slate-200 font-medium">{profile.industry_inferred || '—'}</span>
                  </p>
                  <p>
                    {accepted.size} of {profile.template_kpis.length} selected
                  </p>
                </div>
              </div>

              {profile.degraded && (
                <div className="mt-4 px-4 py-3 rounded-lg bg-amber-950/30 border border-amber-700/50 flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <p className="text-amber-200 font-medium">Degraded research mode</p>
                    <p className="text-amber-300/80 mt-0.5">
                      Live web search was unavailable. All benchmarks are inferred from training knowledge.
                      Treat ranges as directional only.
                    </p>
                  </div>
                </div>
              )}

              {profile.research_sources.length > 0 && (
                <p className="mt-4 text-xs text-slate-500">
                  Sources consulted: {profile.research_sources.join('; ')}
                </p>
              )}
            </div>

            <div className="bg-card border border-border rounded-xl divide-y divide-slate-800 overflow-hidden">
              {profile.template_kpis.map((kpi, idx) => {
                const isAccepted = accepted.has(idx)
                const editName = edits[idx]?.name ?? kpi.name
                const editDomain = edits[idx]?.domain ?? kpi.domain
                const editRange = edits[idx]?.benchmark_range ?? kpi.benchmark_range ?? ''
                return (
                  <div
                    key={`${kpi.name}-${idx}`}
                    className={`flex gap-4 px-5 py-4 transition-colors ${isAccepted ? 'bg-transparent hover:bg-slate-900/40' : 'opacity-40 bg-transparent'}`}
                  >
                    {/* Checkbox */}
                    <div className="pt-0.5 flex-shrink-0">
                      <input
                        type="checkbox"
                        checked={isAccepted}
                        onChange={() => toggleAccept(idx)}
                        className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
                      />
                    </div>

                    {/* Main content */}
                    <div className="flex-1 min-w-0 space-y-1.5">
                      {/* KPI name — click to edit */}
                      {editingIdx === idx ? (
                        <input
                          type="text"
                          value={editName}
                          onChange={(e) => updateEdit(idx, 'name', e.target.value)}
                          onBlur={() => setEditingIdx(null)}
                          onKeyDown={(e) => { if (e.key === 'Escape' || e.key === 'Enter') setEditingIdx(null) }}
                          autoFocus
                          className="w-full px-2 py-0.5 rounded bg-slate-800 border border-indigo-500 text-white text-sm font-semibold focus:outline-none"
                        />
                      ) : (
                        <button
                          onClick={() => isAccepted && setEditingIdx(idx)}
                          className="text-left text-white text-sm font-semibold leading-snug hover:text-indigo-300 transition-colors focus:outline-none"
                          title="Click to edit KPI name"
                        >
                          {editName || <span className="text-slate-500 italic">Unnamed KPI</span>}
                        </button>
                      )}

                      {/* Definition — secondary, truncated */}
                      <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed" title={kpi.definition}>
                        {kpi.definition}
                      </p>

                      {/* Meta row: benchmark + unit */}
                      <div className="flex items-center gap-3 pt-0.5">
                        {editRange ? (
                          <span className="text-xs text-slate-300 font-mono bg-slate-800 px-2 py-0.5 rounded">
                            {editRange}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-600 italic">No benchmark · {kpi.unit}</span>
                        )}
                      </div>
                    </div>

                    {/* Right column: domain + source + confidence */}
                    <div className="flex-shrink-0 flex flex-col items-end gap-2 min-w-[140px]">
                      {/* Domain — small editable badge */}
                      {editingIdx === idx ? (
                        <input
                          type="text"
                          value={editDomain}
                          onChange={(e) => updateEdit(idx, 'domain', e.target.value)}
                          onBlur={() => setEditingIdx(null)}
                          className="px-2 py-0.5 rounded bg-slate-800 border border-slate-600 text-white text-xs focus:outline-none focus:border-indigo-500 w-full text-right"
                        />
                      ) : (
                        <span className="text-xs text-slate-300 font-medium truncate max-w-[140px] text-right" title={editDomain}>
                          {editDomain}
                        </span>
                      )}
                      <SourceBadge source={kpi.benchmark_source} />
                      <span className="text-xs font-mono text-slate-500">{Math.round(kpi.confidence * 100)}% confidence</span>
                    </div>
                  </div>
                )
              })}
            </div>

            {errorMsg && (
              <div className="bg-red-950/30 border border-red-700/50 rounded-xl p-4 flex items-start gap-3">
                <XCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-300">{errorMsg}</p>
              </div>
            )}

            <div className="flex items-center justify-end gap-3">
              <button
                onClick={handleReset}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleCommit}
                disabled={accepted.size === 0}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-white text-sm font-semibold"
              >
                <CheckCircle2 className="w-4 h-4" />
                Commit {accepted.size} KPI{accepted.size === 1 ? '' : 's'} to registry
              </button>
            </div>
          </>
        )}

        {/* State 4 — Committed */}
        {state === 'committed' && commitResult && (
          <div className="bg-card border border-border rounded-xl p-8 space-y-6">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
              <div>
                <h2 className="text-xl font-semibold text-white">Templates committed</h2>
                <p className="text-sm text-slate-400">
                  KPIs are written with <code className="text-indigo-300">status='template'</code>. They are visible
                  in the KPI registry but excluded from situation detection until you connect data sources.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-lg bg-emerald-950/30 border border-emerald-700/50 px-4 py-3">
                <p className="text-xs text-emerald-300 uppercase tracking-wider">Written</p>
                <p className="text-2xl font-bold text-emerald-200">{commitResult.rows_written}</p>
              </div>
              <div className="rounded-lg bg-slate-900/60 border border-slate-700/50 px-4 py-3">
                <p className="text-xs text-slate-400 uppercase tracking-wider">Skipped (duplicate)</p>
                <p className="text-2xl font-bold text-slate-300">{commitResult.rows_skipped}</p>
              </div>
              <div className="rounded-lg bg-red-950/30 border border-red-700/50 px-4 py-3">
                <p className="text-xs text-red-300 uppercase tracking-wider">Failed</p>
                <p className="text-2xl font-bold text-red-200">{commitResult.rows_failed}</p>
              </div>
            </div>

            {commitResult.rows_failed > 0 && (
              <div className="rounded-lg bg-red-950/30 border border-red-700/50 px-4 py-3">
                <p className="text-sm font-medium text-red-300 mb-2">Errors:</p>
                <ul className="text-xs text-red-200 space-y-1">
                  {commitResult.results
                    .filter((r) => r.status === 'error')
                    .map((r) => (
                      <li key={r.kpi_id}>
                        • <span className="font-mono">{r.name}</span>: {r.error}
                      </li>
                    ))}
                </ul>
              </div>
            )}

            <div className="border-t border-slate-800 pt-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-white">Next step</p>
                <p className="text-sm text-slate-400">
                  Connect your data sources so these template KPIs can be promoted to active monitoring.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleReset}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-sm"
                >
                  Research another company
                </button>
                <Link
                  to="/settings/onboarding"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold"
                >
                  Connect data sources
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Error fallback */}
        {state === 'error' && (
          <div className="bg-red-950/30 border border-red-700/50 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-3">
              <XCircle className="w-6 h-6 text-red-400" />
              <h2 className="text-lg font-semibold text-white">Research failed</h2>
            </div>
            <p className="text-sm text-red-200">{errorMsg}</p>
            <button
              onClick={handleReset}
              className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-sm"
            >
              Start over
            </button>
          </div>
        )}
      </main>
    </div>
    </SettingsLayout>
  )
}
