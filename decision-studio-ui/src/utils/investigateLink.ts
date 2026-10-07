/**
 * Opens a second, fully independent SA→DA→SF→approval instance for a causal
 * neighbour KPI in a new tab — no merge back into the primary workflow
 * (2026-10-07). Lives in CausalNeighbourhoodEvidence.tsx's per-tile "Analyze"
 * action, not the compact FramingGateCard decision list (that card stays
 * lean by design — see its own header comment).
 *
 * Offered for EVERY causal-graph neighbour, regardless of `basis`. An
 * accounting_identity neighbour is a COMPONENT of this KPI's own formula
 * (e.g. cogs is one of the two terms gross_margin_pct is computed from), not
 * the same quantity restated — a separate DA on it is genuinely informative
 * (the problem can be concentrated on one side of a ratio while the other
 * side is stable). What `basis` actually gates is downstream, in VA/the
 * theory layer: a validated solution on an identity component shouldn't
 * register as confirming a NEW causal claim, since moving a component moves
 * the parent by arithmetic necessity. That distinction is surfaced in the
 * caveat text, not by withholding this button.
 */
export function openInvestigateTab(kpiId: string, clientId?: string, principalId?: string) {
  const params = new URLSearchParams({ investigate: kpiId });
  if (clientId) params.set('client', clientId);
  if (principalId) params.set('principal', principalId);
  window.open(`/dashboard?${params.toString()}`, '_blank');
}
