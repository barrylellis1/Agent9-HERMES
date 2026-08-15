/**
 * OnboardingDayView — onboarding wizard shell (System Admin Mode, Mode 1).
 *
 * Routes (unchanged from the previous static day-view):
 *   /settings/onboarding/day-1  — Workspace Setup (Company Profile, embedded)
 *   /settings/onboarding/day-2  — Principal Profiles (PrincipalCardList)
 *   /settings/onboarding/day-3  — KPI Library (KPI Intelligence, embedded)
 *   /settings/onboarding/day-4  — Assign Ownership (Accountability interview)
 *   /settings/onboarding/day-5  — Connect Data (Data Product Onboarding, embedded)
 *   /settings/onboarding/day-6  — Validate & Launch (Connection health + launch)
 *
 * Replaces the old static "6 links to full pages" shell with an embedded
 * wizard whose completion is driven by GET /api/v1/onboarding/progress
 * (see hooks/useOnboardingProgress.ts) instead of a route-position heuristic.
 *
 * Full design rationale: docs/architecture/onboarding_wizard_redesign.md
 */

import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { CheckCircle2, ChevronLeft, ChevronRight, LogOut, RotateCcw, X } from 'lucide-react'
import { SettingsLayout } from '../components/SettingsLayout'
import { getSettingsClientId } from '../utils/settingsMode'
import { exitAdminMode } from '../utils/adminMode'
import { useOnboardingProgress } from '../hooks/useOnboardingProgress'
import { ONBOARDING_STEPS } from '../config/onboardingSteps'
import CompanyProfile from './CompanyProfile'
import { BusinessProcessIntelligence } from './BusinessProcessIntelligence'
import { KPIIntelligence } from './KPIIntelligence'
import { PrincipalCardList } from '../components/PrincipalEditor'
import { AccountabilityInterviewPanel } from '../components/AccountabilityInterviewPanel'
import { DataProductOnboardingNew } from './DataProductOnboardingNew'
import { ConnectionHealthPanel } from '../components/ConnectionHealthPanel'
import { SliceValidityPanel } from '../components/SliceValidityPanel'

function clampDay(n: number): number {
  if (Number.isNaN(n)) return 1
  return Math.min(6, Math.max(1, n))
}

export function OnboardingDayView() {
  const { day: dayParam } = useParams<{ day?: string }>()
  const day = clampDay(parseInt((dayParam ?? 'day-1').replace('day-', ''), 10))
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()

  const clientId = getSettingsClientId()
  const { progress, error, isStepUnlocked, refetch } = useOnboardingProgress(clientId)

  // Resumed-session chip — read once on mount, not derived reactively on every render.
  const [showResumedChip, setShowResumedChip] = useState(() => searchParams.get('resumed') === '1')

  // Day 5 (Connect Data) sub-wizard progress — Continue is gated on registration success.
  // dp5Ready tracks a registration that just happened in THIS session; it must be OR'd with
  // the server's own connect_data.complete so a returning admin who already has a data product
  // registered (e.g. after clicking Back from Step 6) isn't stuck behind a permanently-disabled
  // Continue button.
  const [dp5RegisteredThisSession, setDp5RegisteredThisSession] = useState(false)
  const dp5Ready = dp5RegisteredThisSession || (progress?.steps.connect_data?.complete ?? false)

  // Non-linear jump banner — dismissible, state resets per navigation.
  const [jumpBannerDismissed, setJumpBannerDismissed] = useState(false)
  useEffect(() => { setJumpBannerDismissed(false) }, [day])

  // Day 3 (KPI Library) is a two-panel sequence — Business Processes first,
  // then KPI Intelligence — sharing the single day-3 route rather than
  // becoming its own numbered wizard step (avoids renumbering every day-N
  // route, clampDay, and both frontend/backend _STEP_ORDER arrays).
  const [day3SubStep, setDay3SubStep] = useState<'business_processes' | 'kpis'>('business_processes')
  useEffect(() => { setDay3SubStep('business_processes') }, [day])

  const clearResumedParam = () => {
    if (!showResumedChip) return
    setShowResumedChip(false)
    setSearchParams((prev) => {
      prev.delete('resumed')
      return prev
    }, { replace: true })
  }

  const goToDay = async (n: number) => {
    clearResumedParam()
    await refetch()
    navigate(`/settings/onboarding/day-${clampDay(n)}`)
  }

  const handleBack = () => {
    if (day === 3 && day3SubStep === 'kpis') {
      setDay3SubStep('business_processes')
      return
    }
    void goToDay(day - 1)
  }
  const handleSkip = () => { void goToDay(day + 1) }

  const handleLaunch = async () => {
    clearResumedParam()
    await refetch()
    // Admin mode gates /dashboard behind AdminGuard (redirects back to
    // /settings) — hand off the target client as the active session client
    // and drop just the admin-mode flag so the dashboard's auto-scan
    // (useDecisionStudio's mount effect) can run for this client.
    if (clientId) {
      localStorage.setItem('a9_active_client_id', clientId)
    }
    localStorage.removeItem('a9_admin_mode')
    navigate('/dashboard', { state: { clientId } })
  }

  const handleContinue = () => {
    if (day === 6) {
      void handleLaunch()
    } else {
      void goToDay(day + 1)
    }
  }

  const handleExit = () => {
    exitAdminMode()
    navigate('/login')
  }

  const currentStepDef = ONBOARDING_STEPS.find((s) => s.step === day) ?? ONBOARDING_STEPS[0]
  const StepIcon = currentStepDef.icon
  const stepUnlocked = isStepUnlocked(day)

  return (
    <SettingsLayout>
      <div className="p-8 font-sans min-h-full max-w-3xl">
        {/* Resumed-session chip */}
        {showResumedChip && (
          <div className="mb-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-950/50 border border-indigo-700/40 text-xs text-indigo-300">
            <RotateCcw className="w-3.5 h-3.5" />
            Resumed from your last session
          </div>
        )}

        {error && (
          <div className="mb-4 flex items-center justify-between gap-3 px-4 py-2.5 rounded-lg bg-red-950/30 border border-red-700/40 text-red-300 text-xs">
            <span>Couldn't load onboarding progress — showing last known state.</span>
            <button onClick={() => void refetch()} className="text-red-200 hover:text-white underline flex-shrink-0">
              Retry
            </button>
          </div>
        )}

        {/* 6-segment progress strip */}
        <div className="mb-6 flex items-center gap-1.5">
          {ONBOARDING_STEPS.map((s) => {
            const complete = progress?.steps[s.key]?.complete ?? false
            const active = s.step === day
            return (
              <div
                key={s.step}
                title={s.label}
                className={`h-1.5 flex-1 rounded-full transition-colors ${
                  active ? 'bg-indigo-400' : complete ? 'bg-emerald-600' : 'bg-slate-800'
                }`}
              />
            )
          })}
        </div>

        {/* Step header */}
        <div className="mb-6 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 flex-shrink-0">
            <StepIcon className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-indigo-400 mb-0.5">
              Step {day} of 6
            </p>
            <h1 className="text-2xl font-bold text-white">{currentStepDef.label}</h1>
          </div>
        </div>

        {clientId && (
          <div className="mb-4 flex items-center gap-2">
            <span className="text-xs text-slate-500">Onboarding client:</span>
            <span className="text-xs font-mono text-amber-300 bg-amber-950/40 border border-amber-700/30 px-2 py-0.5 rounded">{clientId}</span>
          </div>
        )}

        {/* Non-linear jump banner — advisory only, never blocks navigation */}
        {!stepUnlocked && !jumpBannerDismissed && (
          <div className="mb-4 flex items-start justify-between gap-3 px-4 py-3 rounded-lg bg-amber-950/30 border border-amber-700/40 text-amber-200 text-sm">
            <span>You're jumping ahead — Step {day} isn't complete yet.</span>
            <button onClick={() => setJumpBannerDismissed(true)} className="text-amber-400 hover:text-white flex-shrink-0">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        <p className="mb-6 text-sm text-slate-300 leading-relaxed">{currentStepDef.summary}</p>

        {/* Day 3 sub-step indicator — two panels share this one wizard step */}
        {day === 3 && (
          <div className="mb-4 flex items-center gap-2 text-xs">
            <span className={day3SubStep === 'business_processes' ? 'text-indigo-300 font-semibold' : 'text-emerald-400'}>
              1. Business Processes
            </span>
            <span className="text-slate-600">→</span>
            <span className={day3SubStep === 'kpis' ? 'text-indigo-300 font-semibold' : 'text-slate-500'}>
              2. KPI Library
            </span>
          </div>
        )}

        {/* Step body */}
        <div className="mb-8">
          {day === 1 && <CompanyProfile embedded />}
          {day === 2 && <PrincipalCardList clientId={clientId} />}
          {day === 3 && day3SubStep === 'business_processes' && (
            <BusinessProcessIntelligence embedded onContinue={() => setDay3SubStep('kpis')} />
          )}
          {day === 3 && day3SubStep === 'kpis' && (
            <KPIIntelligence embedded onContinue={() => { void goToDay(4) }} />
          )}
          {day === 4 && <AccountabilityInterviewPanel clientId={clientId} />}
          {day === 5 && (
            <DataProductOnboardingNew
              embedded
              initialMode={progress?.steps.connect_data?.complete ? undefined : 'new'}
              onRegistrationSuccess={() => setDp5RegisteredThisSession(true)}
            />
          )}
          {day === 6 && (
            <div className="space-y-8">
              <ConnectionHealthPanel clientId={clientId} />
              <div className="border-t border-slate-800/60 pt-8">
                <SliceValidityPanel clientId={clientId} />
              </div>
            </div>
          )}
        </div>

        {/* Footer nav */}
        <div className="pt-6 border-t border-slate-800/60 flex items-center justify-between gap-3">
          <button
            onClick={handleBack}
            disabled={day === 1}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm text-slate-400 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <ChevronLeft className="w-4 h-4" /> Back
          </button>

          <div className="flex items-center gap-3">
            {day <= 5 && (
              <button
                onClick={handleSkip}
                className="px-4 py-2 rounded-lg text-sm text-slate-400 hover:text-white transition-colors"
              >
                Skip
              </button>
            )}
            <button
              onClick={handleContinue}
              disabled={day === 5 && !dp5Ready}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-semibold transition-colors"
            >
              {day === 6 ? (
                <>
                  Run First Assessment &amp; Launch
                  <CheckCircle2 className="w-4 h-4" />
                </>
              ) : (
                <>
                  Continue
                  <ChevronRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Exit Admin Mode — day 6 only, deliberately separate from the primary launch action */}
        {day === 6 && (
          <div className="pt-4 flex justify-end">
            <button
              onClick={handleExit}
              className="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-slate-500 hover:text-slate-300 hover:bg-slate-800/40 transition-colors"
            >
              <LogOut className="w-3.5 h-3.5" />
              Exit Admin Mode
            </button>
          </div>
        )}
      </div>
    </SettingsLayout>
  )
}
