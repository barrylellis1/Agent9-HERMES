/**
 * De-branded display labels for council personas.
 *
 * WHY
 * ---
 * Phase 13's M3 (May 2026) and Phase 18 (Aug 2026) reached different answers on
 * the same question three months apart. M3 said keep firm names as internal
 * reasoning anchors and strip them from the top-level narrative only; Phase 18
 * said firm identity should stop being a product feature at all — a user
 * selecting "McKinsey" and receiving output attributed to "McKinsey & Company"
 * is a commercial exposure independent of how the analysis compares.
 *
 * Resolved in favour of Phase 18 for the briefing surface (2026-08-16). The
 * briefing is the artifact an executive exports to PDF and forwards, so it is
 * the worst place to carry a real firm's legal name over analysis that firm did
 * not produce.
 *
 * WHAT THIS IS NOT
 * ----------------
 * Not a rename to a different firm's name, and not a blanking-out. Each label
 * states the analytical tradition the persona prompt actually encodes, which is
 * the thing that carries information for the reader — M3's substantive point,
 * kept, with the trademark dropped. The persona id is still the reasoning anchor
 * inside the prompt; nothing about generation changes here.
 *
 * SCOPE: the Executive Briefing only. The persona PICKER, council presets, and
 * the debate loading animation (`uiConstants.ts`, `CouncilDebate.tsx`,
 * `ProblemRefinementChat.tsx`, `DeepFocusView.tsx`) are Phase 18 Category C and
 * are deliberately untouched — that is console work with its own inventory.
 */

/** Firm ids → the tradition the persona prompt encodes. */
const TRADITION_LABELS: Record<string, string> = {
  mckinsey: 'Structured problem-solving',
  bcg: 'Portfolio & unit economics',
  bain: 'Execution & results',
  deloitte: 'Operational transformation',
  accenture: 'Technology-enabled delivery',
  kpmg: 'Risk & controls',
  ey_parthenon: 'Strategy & transactions',
  pwc_strategy: 'Capability-driven strategy',
  mbb: 'Strategy council',
}

/** Lens council ids — already de-branded upstream; kept readable. */
const LENS_LABELS: Record<string, string> = {
  commercial: 'Commercial lens',
  operational: 'Operational lens',
  structural: 'Structural lens',
}

/**
 * Display label for a persona id. Unknown ids are title-cased rather than
 * dropped — an unrecognised persona should still be attributable to the reader,
 * and silently omitting one would understate how many perspectives ran.
 */
export function personaDisplayLabel(personaId: string | null | undefined): string {
  const id = String(personaId ?? '').trim().toLowerCase()
  if (!id) return 'Perspective'
  return LENS_LABELS[id] ?? TRADITION_LABELS[id] ?? (
    id.charAt(0).toUpperCase() + id.slice(1).replace(/_/g, ' ')
  )
}

/** True when the id is a consulting-firm persona rather than a lens. */
export function isFirmPersona(personaId: string | null | undefined): boolean {
  return String(personaId ?? '').trim().toLowerCase() in TRADITION_LABELS
}

/**
 * Council composition line for the audit footer.
 *
 * States how many independent perspectives ran and what they were, without
 * naming firms. The count matters for provenance — it is the difference between
 * one model call and a multi-perspective council — so it is stated explicitly
 * rather than left to be counted off a list.
 */
export function councilCompositionLabel(personaIds: string[]): string | null {
  if (!personaIds.length) return null
  const labels = personaIds.map(personaDisplayLabel)
  return `${labels.length} perspectives: ${labels.join(' · ')}`
}
