import { useEffect, useState, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Sparkles,
  XCircle,
  Library,
  Lightbulb,
} from 'lucide-react'
import {
  researchCompanyBusinessProcesses,
  commitBusinessProcessTemplates,
  getCompanyProfile,
  type CompanyBusinessProcessProfile,
  type TemplateBusinessProcess,
  type AcceptedTemplateBusinessProcess,
  type BusinessProcessSource,
  type CommitBusinessProcessTemplatesResponse,
} from '../api/client'
import { getToolTargetClientId, isAdminMode } from '../utils/adminMode'
import { SettingsLayout } from '../components/SettingsLayout'

type FlowState = 'input' | 'researching' | 'review' | 'committed' | 'error'

// ─────────────────────────────────────────────────
// Source badge — canonical taxonomy vs. LLM-proposed gap
// ─────────────────────────────────────────────────
function SourceBadge({ source }: { source: BusinessProcessSource }) {
  if (source === 'canonical') {
    return (
      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs border bg-severity-opportunity/60 text-severity-opportunity border-severity-opportunity/50">
        <Library className="w-3 h-3" />
        Standard taxonomy
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs border bg-blue-950/60 text-blue-300 border-blue-700/50">
      <Lightbulb className="w-3 h-3" />
      New — industry-specific
    </span>
  )
}

// ─────────────────────────────────────────────────
// State 2 — Research progress
// ─────────────────────────────────────────────────
function ResearchProgress() {
  return (
    <div className="bg-card border border-border rounded-xl p-8">
      <div className="flex items-center gap-3">
        <Loader2 className="w-6 h-6 text-indigo-400 animate-spin" />
        <div>
          <h3 className="text-lg font-semibold text-white">Selecting relevant business processes</h3>
          <p className="text-sm text-slate-400">Matching your industry against the standard taxonomy — usually a few seconds.</p>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────
export function BusinessProcessIntelligence({
  embedded = false,
  onContinue,
}: { embedded?: boolean; onContinue?: () => void } = {}) {
  const clientId = getToolTargetClientId()
  const adminMode = isAdminMode()

  const [state, setState] = useState<FlowState>('input')
  const [errorMsg, setErrorMsg] = useState<string>('')

  // Stored company profile (Day 1) — drives industry, never re-asked when present
  const [profileIndustry, setProfileIndustry] = useState<string | null>(null)
  const [profileLoaded, setProfileLoaded] = useState(false)
  const [industryOverride, setIndustryOverride] = useState('')
  const [maxExtraProcesses, setMaxExtraProcesses] = useState(5)

  useEffect(() => {
    if (!clientId) return
    let cancelled = false
    getCompanyProfile(clientId).then((profile) => {
      if (cancelled) return
      const industry = profile?.industry ? String(profile.industry) : null
      setProfileIndustry(industry)
      setProfileLoaded(true)
    })
    return () => { cancelled = true }
  }, [clientId])

  // Research result
  const [profile, setProfile] = useState<CompanyBusinessProcessProfile | null>(null)
  const [accepted, setAccepted] = useState<Set<number>>(new Set())

  // Commit result
  const [commitResult, setCommitResult] = useState<CommitBusinessProcessTemplatesResponse | null>(null)

  const canSubmit = clientId.length > 0 && profileLoaded

  async function handleResearch() {
    if (!canSubmit) return
    setState('researching')
    setErrorMsg('')
    try {
      const res = await researchCompanyBusinessProcesses({
        client_id: clientId,
        industry_override: profileIndustry ? undefined : (industryOverride.trim() || undefined),
        max_extra_processes: maxExtraProcesses,
      })
      if (res.status === 'error' || !res.profile) {
        setErrorMsg(res.error || 'Selection failed unexpectedly.')
        setState('error')
        return
      }
      setProfile(res.profile)
      // Default: accept every selected process
      setAccepted(new Set(res.profile.selected.map((_, i) => i)))
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

  const acceptedProcesses: AcceptedTemplateBusinessProcess[] = useMemo(() => {
    if (!profile) return []
    return profile.selected
      .map((bp, idx) => ({ bp, idx }))
      .filter(({ idx }) => accepted.has(idx))
      .map(({ bp }) => {
        const { rationale: _rationale, ...rest } = bp as TemplateBusinessProcess
        return rest as AcceptedTemplateBusinessProcess
      })
  }, [profile, accepted])

  async function handleCommit() {
    if (acceptedProcesses.length === 0) {
      setErrorMsg('Accept at least one business process before committing.')
      return
    }
    setErrorMsg('')
    try {
      const res = await commitBusinessProcessTemplates({
        client_id: clientId,
        accepted_processes: acceptedProcesses,
        created_by: 'bp_intelligence_ui',
      })
      setCommitResult(res)
      setState('committed')
    } catch (exc) {
      setErrorMsg(exc instanceof Error ? exc.message : String(exc))
    }
  }

  function handleReset() {
    setState('input')
    setProfile(null)
    setAccepted(new Set())
    setCommitResult(null)
    setErrorMsg('')
  }

  const content = (
    <div className="p-8 font-sans min-h-full">
      <header className="mb-6 flex justify-between items-center">
        <div className="flex items-center gap-4">
          {!embedded && (
            <Link to="/settings" className="p-2 -ml-2 text-slate-400 hover:text-white transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
          )}
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">Business Process Intelligence</h1>
            <p className="text-sm text-slate-400">
              Select the business processes relevant to this client from the standard taxonomy
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
        {!clientId && (
          <div className="bg-severity-warning/30 border border-severity-warning/50 rounded-xl p-6 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-severity-warning flex-shrink-0" />
            <p className="text-sm text-severity-warning">
              {adminMode
                ? 'Select or create a client workspace in Settings before selecting business processes.'
                : 'Select a workspace client before selecting business processes.'}
            </p>
          </div>
        )}

        {/* State 1 — Input */}
        {state === 'input' && clientId && (
          <div className="bg-card border border-border rounded-xl p-8 space-y-5">
            <div>
              <h2 className="text-lg font-semibold text-white mb-1">Step 1 — Confirm industry context</h2>
              <p className="text-sm text-slate-400">
                We select from a taxonomy of 39 standard business processes across 12 domains, then propose
                a few industry-specific additions.
              </p>
            </div>

            {profileLoaded && profileIndustry && (
              <div className="px-4 py-3 rounded-lg bg-severity-opportunity/30 border border-severity-opportunity/50 flex items-center gap-2.5">
                <CheckCircle2 className="w-4 h-4 text-severity-opportunity flex-shrink-0" />
                <p className="text-sm text-severity-opportunity">
                  Using industry from company profile: <span className="font-semibold">{profileIndustry}</span>
                </p>
              </div>
            )}

            {profileLoaded && !profileIndustry && (
              <div className="space-y-3">
                <div className="px-4 py-3 rounded-lg bg-severity-warning/30 border border-severity-warning/50 flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-severity-warning flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-severity-warning">
                    No company profile found for this client. Selection will use a generic cross-industry
                    subset unless you provide an industry below — or{' '}
                    <Link to="/settings/onboarding/day-1" className="underline hover:text-severity-warning">
                      set up the company profile first
                    </Link>.
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">Industry (optional)</label>
                  <input
                    type="text"
                    value={industryOverride}
                    onChange={(e) => setIndustryOverride(e.target.value)}
                    placeholder="e.g. Grocery / Specialty Retail"
                    className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Max industry-specific additions</label>
              <input
                type="number"
                value={maxExtraProcesses}
                onChange={(e) => setMaxExtraProcesses(Math.max(0, Math.min(15, parseInt(e.target.value) || 0)))}
                min={0}
                max={15}
                className="w-32 px-3 py-2 rounded-lg bg-slate-900 border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
              <span className="ml-3 text-xs text-slate-500">0–15; processes not already in the standard taxonomy</span>
            </div>

            <div className="pt-2 flex items-center justify-end gap-3">
              <button
                onClick={handleResearch}
                disabled={!canSubmit}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-white text-sm font-semibold"
              >
                <Sparkles className="w-4 h-4" />
                Select business processes
              </button>
            </div>
          </div>
        )}

        {/* State 2 — Researching */}
        {state === 'researching' && <ResearchProgress />}

        {/* State 3 — Review */}
        {state === 'review' && profile && (
          <>
            <div className="bg-card border border-border rounded-xl p-6">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-lg font-semibold text-white mb-1">
                    Step 2 — Review {profile.selected.length} business processes
                  </h2>
                  <p className="text-sm text-slate-400">
                    Accept or reject. Only checked rows are written to the registry on commit.
                  </p>
                </div>
                <div className="text-right text-xs text-slate-400">
                  <p>
                    Industry used:{' '}
                    <span className="text-slate-200 font-medium">{profile.industry_used || '—'}</span>
                  </p>
                  <p>
                    {accepted.size} of {profile.selected.length} selected
                  </p>
                </div>
              </div>

              {profile.degraded && (
                <div className="mt-4 px-4 py-3 rounded-lg bg-severity-warning/30 border border-severity-warning/50 flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-severity-warning flex-shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <p className="text-severity-warning font-medium">No industry context available</p>
                    <p className="text-severity-warning/80 mt-0.5">
                      Selection used a generic cross-industry subset of the standard taxonomy. Set up the
                      company profile for a more targeted selection.
                    </p>
                  </div>
                </div>
              )}
            </div>

            <div className="bg-card border border-border rounded-xl divide-y divide-slate-800 overflow-hidden">
              {profile.selected.map((bp, idx) => {
                const isAccepted = accepted.has(idx)
                return (
                  <div
                    key={`${bp.domain}-${bp.name}-${idx}`}
                    className={`flex gap-4 px-5 py-4 transition-colors ${isAccepted ? 'bg-transparent hover:bg-slate-900/40' : 'opacity-40 bg-transparent'}`}
                  >
                    <div className="pt-0.5 flex-shrink-0">
                      <input
                        type="checkbox"
                        checked={isAccepted}
                        onChange={() => toggleAccept(idx)}
                        className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-indigo-600 focus:ring-indigo-500"
                      />
                    </div>

                    <div className="flex-1 min-w-0 space-y-1.5">
                      <p className="text-white text-sm font-semibold leading-snug">{bp.name}</p>
                      {bp.description && (
                        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed" title={bp.description}>
                          {bp.description}
                        </p>
                      )}
                      {bp.rationale && (
                        <p className="text-xs text-slate-500 italic line-clamp-1" title={bp.rationale}>
                          {bp.rationale}
                        </p>
                      )}
                      {bp.owner_role && (
                        <span className="text-xs text-slate-300 font-mono bg-slate-800 px-2 py-0.5 rounded inline-block">
                          Owner: {bp.owner_role}
                        </span>
                      )}
                    </div>

                    <div className="flex-shrink-0 flex flex-col items-end gap-2 min-w-[160px]">
                      <span className="text-xs text-slate-300 font-medium truncate max-w-[160px] text-right" title={bp.domain}>
                        {bp.domain}
                      </span>
                      <SourceBadge source={bp.source} />
                    </div>
                  </div>
                )
              })}
            </div>

            {errorMsg && (
              <div className="bg-severity-critical/30 border border-severity-critical/50 rounded-xl p-4 flex items-start gap-3">
                <XCircle className="w-4 h-4 text-severity-critical flex-shrink-0 mt-0.5" />
                <p className="text-sm text-severity-critical">{errorMsg}</p>
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
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-severity-opportunity hover:bg-severity-opportunity disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed text-white text-sm font-semibold"
              >
                <CheckCircle2 className="w-4 h-4" />
                Commit {accepted.size} process{accepted.size === 1 ? '' : 'es'} to registry
              </button>
            </div>
          </>
        )}

        {/* State 4 — Committed */}
        {state === 'committed' && commitResult && (
          <div className="bg-card border border-border rounded-xl p-8 space-y-6">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-8 h-8 text-severity-opportunity" />
              <div>
                <h2 className="text-xl font-semibold text-white">Business processes committed</h2>
                <p className="text-sm text-slate-400">
                  Visible immediately in Context Explorer and the accountability interview.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-lg bg-severity-opportunity/30 border border-severity-opportunity/50 px-4 py-3">
                <p className="text-xs text-severity-opportunity uppercase tracking-wider">Written</p>
                <p className="text-2xl font-bold text-severity-opportunity">{commitResult.rows_written}</p>
              </div>
              <div className="rounded-lg bg-slate-900/60 border border-slate-700/50 px-4 py-3">
                <p className="text-xs text-slate-400 uppercase tracking-wider">Skipped (duplicate)</p>
                <p className="text-2xl font-bold text-slate-300">{commitResult.rows_skipped}</p>
              </div>
              <div className="rounded-lg bg-severity-critical/30 border border-severity-critical/50 px-4 py-3">
                <p className="text-xs text-severity-critical uppercase tracking-wider">Failed</p>
                <p className="text-2xl font-bold text-severity-critical">{commitResult.rows_failed}</p>
              </div>
            </div>

            {commitResult.rows_failed > 0 && (
              <div className="rounded-lg bg-severity-critical/30 border border-severity-critical/50 px-4 py-3">
                <p className="text-sm font-medium text-severity-critical mb-2">Errors:</p>
                <ul className="text-xs text-severity-critical space-y-1">
                  {commitResult.results
                    .filter((r) => r.status === 'error')
                    .map((r) => (
                      <li key={r.id}>
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
                  Define KPIs and map them to these business processes.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleReset}
                  className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-sm"
                >
                  Run again
                </button>
                {embedded && onContinue ? (
                  <button
                    onClick={onContinue}
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold"
                  >
                    Continue to KPI Library
                    <ArrowRight className="w-4 h-4" />
                  </button>
                ) : (
                  <Link
                    to="/settings/kpi-intelligence"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold"
                  >
                    Go to KPI Intelligence
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Error fallback */}
        {state === 'error' && (
          <div className="bg-severity-critical/30 border border-severity-critical/50 rounded-xl p-6 space-y-4">
            <div className="flex items-center gap-3">
              <XCircle className="w-6 h-6 text-severity-critical" />
              <h2 className="text-lg font-semibold text-white">Selection failed</h2>
            </div>
            <p className="text-sm text-severity-critical">{errorMsg}</p>
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
  )

  return embedded ? content : <SettingsLayout>{content}</SettingsLayout>
}
