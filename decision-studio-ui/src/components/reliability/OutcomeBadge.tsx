import { AlertTriangle, CheckCircle2, HelpCircle } from 'lucide-react'
import type { AuditEventRecord } from '../../api/client'

/** Shared pass/fail/abstain badge — used by ReliabilityPanel and ReliabilityDrillDown. */
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
    <span className="inline-flex items-center gap-1 text-xs font-medium text-severity-warning">
      <HelpCircle className="w-3.5 h-3.5" /> abstain
    </span>
  )
  return <span className="text-xs text-slate-500">—</span>
}
