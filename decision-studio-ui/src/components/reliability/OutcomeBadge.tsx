import { AlertTriangle, CheckCircle2, HelpCircle } from 'lucide-react'
import type { AuditEventRecord } from '../../api/client'

/**
 * Shared pass/fail/abstain badge — used by ReliabilityPanel and
 * ReliabilityDrillDown.
 *
 * `abstain` displays as "not checked", not the raw word (2026-10-04,
 * user-caught: "what does abstain supposed to mean to a decision maker?!").
 * The underlying data model keeps `abstain` — that is the correct engineering
 * term for the True/False/None house rule `src/analysis/` uses everywhere
 * (None excluded from both numerator and denominator) — but the word itself
 * reads to a non-engineer like a vote declined or evidence withheld, which is
 * backwards: it means this specific check does not apply here, not that
 * something is wrong or unresolved. Rendered neutral (slate, not the amber
 * severity-warning fail nearly always sits next to) so it visually recedes
 * rather than competing with a real fail for attention — an abstain is never
 * something to act on.
 */
export function OutcomeBadge({ outcome }: { outcome: AuditEventRecord['outcome'] }) {
  if (outcome === 'pass') return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-severity-opportunity">
      <CheckCircle2 className="w-3.5 h-3.5" /> pass
    </span>
  )
  if (outcome === 'fail') return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-severity-critical">
      <AlertTriangle className="w-3.5 h-3.5" /> fail
    </span>
  )
  if (outcome === 'abstain') return (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-slate-500">
      <HelpCircle className="w-3.5 h-3.5" /> not checked
    </span>
  )
  return <span className="text-xs text-slate-500">—</span>
}
