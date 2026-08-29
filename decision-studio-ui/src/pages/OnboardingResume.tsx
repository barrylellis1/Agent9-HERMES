/**
 * OnboardingResume — entry point for /settings/onboarding.
 *
 * Fresh client (nothing started yet) → redirect straight into Step 1.
 * In-progress client → show a short "resume where you left off" summary
 * with the per-step metric that's most relevant to what's incomplete.
 */
import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { SettingsLayout } from '../components/SettingsLayout'
import { getSettingsClientId } from '../utils/settingsMode'
import { useOnboardingProgress } from '../hooks/useOnboardingProgress'
import { ONBOARDING_STEPS } from '../config/onboardingSteps'

/** Human-readable in-progress metric per step, using whatever fields that
 *  step's progress object has (see src/api/routes/onboarding.py). */
function stepMetricText(key: string, stepData: Record<string, any> | undefined): string | null {
  if (!stepData) return null
  switch (key) {
    case 'workspace_setup':
      return stepData.complete ? 'Company profile complete' : 'Company profile not yet started'
    case 'principals': {
      const count = stepData.count ?? 0
      const withEmail = stepData.with_email ?? 0
      if (count === 0) return 'No principals added yet'
      return `${count} principal${count === 1 ? '' : 's'}, ${count - withEmail} missing email`
    }
    case 'kpi_library': {
      const count = stepData.count ?? 0
      return count === 0 ? 'No KPIs defined yet' : `${count} KPI${count === 1 ? '' : 's'} in the library`
    }
    case 'ownership': {
      const assigned = stepData.assigned ?? 0
      const total = stepData.total ?? 0
      return total === 0 ? 'No KPIs to assign yet' : `${assigned} / ${total} KPIs assigned`
    }
    case 'connect_data': {
      const count = stepData.data_products ?? 0
      return count === 0 ? 'No data products connected yet' : `${count} data product${count === 1 ? '' : 's'} connected`
    }
    case 'validate_launch': {
      const runs = stepData.assessment_runs ?? 0
      const connOk = stepData.connection_ok
      if (runs > 0) return `${runs} assessment run${runs === 1 ? '' : 's'} completed`
      return connOk ? 'Connections healthy — ready for first assessment' : 'Connections not yet validated'
    }
    default:
      return null
  }
}

export function OnboardingResume() {
  const clientId = getSettingsClientId()
  const { progress, loading } = useOnboardingProgress(clientId)
  const navigate = useNavigate()

  useEffect(() => {
    // No client selected yet (e.g. fresh admin login before Step 1 has ever
    // created one) — useOnboardingProgress never fetches without a clientId,
    // so `loading`/`progress` would otherwise stay stuck forever. Nothing to
    // resume in that case either way — go straight to Step 1.
    if (!clientId) {
      navigate('/settings/onboarding/day-1', { replace: true })
      return
    }
    if (
      !loading &&
      progress &&
      progress.firstIncompleteStep === 1 &&
      Object.values(progress.steps).every((s) => !s.complete)
    ) {
      navigate('/settings/onboarding/day-1', { replace: true })
    }
  }, [clientId, loading, progress, navigate])

  if (!clientId || loading || !progress) {
    return (
      <SettingsLayout>
        <div className="p-8 font-sans min-h-full flex items-center gap-3 text-slate-400 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" />
          Loading onboarding progress…
        </div>
      </SettingsLayout>
    )
  }

  const nextStep = Math.min(progress.firstIncompleteStep, 6)
  const nextStepDef = ONBOARDING_STEPS.find((s) => s.step === nextStep) ?? ONBOARDING_STEPS[0]
  const allComplete = progress.firstIncompleteStep === 7

  return (
    <SettingsLayout>
      <div className="p-8 font-sans min-h-full max-w-3xl">
        <div className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-1">
            Onboarding
          </p>
          <h1 className="text-2xl font-bold text-white">
            {allComplete ? 'Onboarding complete' : 'Welcome back'}
          </h1>
          {clientId && (
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs text-slate-500">Client:</span>
              <span className="text-xs font-mono text-severity-warning bg-severity-warning/40 border border-severity-warning/30 px-2 py-0.5 rounded">{clientId}</span>
            </div>
          )}
        </div>

        {/* Progress strip */}
        <div className="mb-6 flex items-center gap-1.5">
          {ONBOARDING_STEPS.map((s) => {
            const complete = progress.steps[s.key]?.complete ?? false
            return (
              <div
                key={s.step}
                title={s.label}
                className={`h-1.5 flex-1 rounded-full ${complete ? 'bg-severity-opportunity' : 'bg-slate-800'}`}
              />
            )
          })}
        </div>

        {allComplete ? (
          <div className="p-5 rounded-xl bg-card border border-border mb-6">
            <p className="text-sm text-severity-opportunity">
              All 6 onboarding steps are complete for this client. You can still revisit any step below.
            </p>
          </div>
        ) : (
          <div className="p-5 rounded-xl bg-card border border-border mb-6">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-1">
              Last worked on
            </p>
            <h2 className="text-lg font-semibold text-white mb-1">
              Step {nextStepDef.step} — {nextStepDef.label}
            </h2>
            <p className="text-sm text-slate-400">
              {stepMetricText(nextStepDef.key, progress.steps[nextStepDef.key]) ?? 'Not yet started'}
            </p>
          </div>
        )}

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(allComplete ? '/settings/onboarding/day-1' : `/settings/onboarding/day-${nextStep}?resumed=1`)}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition-colors"
          >
            {allComplete ? 'Review Step 1' : `Resume Step ${nextStep}`}
            <span aria-hidden>→</span>
          </button>
          <button
            onClick={() => navigate('/settings/onboarding/day-1')}
            className="px-5 py-2.5 rounded-lg border border-slate-700 text-slate-300 hover:text-white hover:border-slate-500 text-sm font-medium transition-colors"
          >
            Review all steps
          </button>
        </div>
      </div>
    </SettingsLayout>
  )
}
