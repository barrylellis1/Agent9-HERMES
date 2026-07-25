/**
 * useOnboardingProgress — fetches GET /api/v1/onboarding/progress for a client
 * and exposes step-completion + "is this step unlocked" helpers to the
 * onboarding wizard shell (OnboardingDayView) and its sidebar (SettingsLayout).
 *
 * Design notes (see docs/architecture/onboarding_wizard_redesign.md):
 *  - isStepUnlocked() is advisory only — it must never hard-block navigation,
 *    only drive a dismissible "you're jumping ahead" visual treatment.
 *  - On fetch error we keep the last-known-good `progress` rather than nulling
 *    it out, so a transient network blip doesn't collapse the UI mid-wizard.
 */
import { useCallback, useEffect, useRef, useState } from 'react'
import { getOnboardingProgress } from '../api/client'

export interface OnboardingProgress {
  clientId: string
  steps: Record<string, { complete: boolean; [metric: string]: any }>
  firstIncompleteStep: number // 1-7
}

const STEP_ORDER = [
  'workspace_setup',
  'principals',
  'kpi_library',
  'ownership',
  'connect_data',
  'validate_launch',
]

// The wizard shell and its sidebar (SettingsLayout's OnboardingNav) both call
// this hook for the same clientId on every onboarding page — dedupe concurrent
// fetches for the same client so that doesn't double the request.
const inFlightByClientId = new Map<string, ReturnType<typeof getOnboardingProgress>>()

function fetchOnboardingProgress(clientId: string) {
  let promise = inFlightByClientId.get(clientId)
  if (!promise) {
    promise = getOnboardingProgress(clientId).finally(() => {
      inFlightByClientId.delete(clientId)
    })
    inFlightByClientId.set(clientId, promise)
  }
  return promise
}

export function useOnboardingProgress(clientId: string | null): {
  progress: OnboardingProgress | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  isStepUnlocked: (step: number) => boolean
} {
  const [progress, setProgress] = useState<OnboardingProgress | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const progressRef = useRef<OnboardingProgress | null>(null)

  const fetchProgress = useCallback(async () => {
    if (!clientId) return
    setLoading(true)
    setError(null)
    try {
      const raw = await fetchOnboardingProgress(clientId)
      const next: OnboardingProgress = {
        clientId: raw.client_id,
        steps: raw.steps,
        firstIncompleteStep: raw.first_incomplete_step,
      }
      progressRef.current = next
      setProgress(next)
    } catch (e: unknown) {
      // Keep the last-known-good progress — don't null it out on transient errors.
      setError(e instanceof Error ? e.message : 'Failed to load onboarding progress')
    } finally {
      setLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    if (!clientId) return
    void fetchProgress()
  }, [clientId, fetchProgress])

  const isStepUnlocked = useCallback(
    (step: number): boolean => {
      if (step <= 1) return true
      const current = progressRef.current ?? progress
      if (!current) return true
      if (step <= current.firstIncompleteStep) return true
      const prevKey = STEP_ORDER[step - 2]
      return Boolean(prevKey && current.steps[prevKey]?.complete)
    },
    [progress],
  )

  return { progress, loading, error, refetch: fetchProgress, isStepUnlocked }
}
