/**
 * ReliabilityAuditStrip — the "decision-maker line" from docs/DEVELOPMENT_
 * BACKLOG.md's "Cross-view: Reliability signal surfaces" (#2), built 2026-10-03
 * once the backend reliability panel (6 reliability.* signals, audit_events
 * table) existed with no UI anywhere reading it back for an ordinary principal.
 *
 * Deliberately EXCEPTION-ONLY: renders nothing when this run's checks all
 * passed or never ran. An indicator present on every briefing is ignored
 * within a week (backlog #5's own stated reasoning for calibrating #2 against
 * an accumulated corpus, not the first run that looks right) — so this only
 * speaks up on a `fail`, never on a clean pass and never on `abstain`
 * (ABSENT ≠ PASS, but absent/abstain also isn't a defect worth a glance-level
 * interruption; the full pass/fail/abstain picture belongs to the richer
 * DeepFocusView drill-down, not this one-line footer strip).
 *
 * Fetches via GET /admin/reliability-events (no admin key — see that
 * endpoint's docstring) scoped to client_id + the SF request_id that produced
 * this briefing, so it reads exactly what THIS run found, not the fleet.
 */
import { useEffect, useState } from 'react'
import { AlertTriangle } from 'lucide-react'
import { type AuditEventRecord, getReliabilityEvents } from '../../api/client'

function describeFailure(e: AuditEventRecord): string {
  const p = e.payload ?? {}
  switch (e.event_type) {
    case 'reliability.rollup_check':
      return 'variance bridge did not reconcile with the warehouse rollup'
    case 'reliability.slice_validity': {
      const dim = e.resource_id ? `${e.resource_id} ` : ''
      return `${dim}dimension excluded for completeness`
    }
    case 'reliability.citation_quality':
      return 'market signals could not be verified against a real source'
    case 'reliability.decision_quality':
      return `decision-quality check "${e.resource_id ?? 'unknown'}" did not pass`
    case 'reliability.kpi_coverage':
      return 'registered KPIs were not evaluated this run'
    case 'reliability.detection_confidence':
      return 'detection confidence below threshold'
    default:
      return typeof p.detail === 'string' ? p.detail : e.event_type.replace('reliability.', '')
  }
}

// Same (dimension excluded) failure can fire once per dimension — collapse to
// one line per event_type so a KPI with three bad dimensions doesn't produce
// three near-identical lines in a one-line strip.
function summarize(events: AuditEventRecord[]): string[] {
  const failures = events.filter((e) => e.outcome === 'fail')
  const byType = new Map<string, AuditEventRecord[]>()
  for (const e of failures) {
    const list = byType.get(e.event_type) ?? []
    list.push(e)
    byType.set(e.event_type, list)
  }
  const lines: string[] = []
  for (const [type, group] of byType) {
    if (type === 'reliability.slice_validity' && group.length > 1) {
      lines.push(`${group.length} dimensions excluded for completeness`)
    } else {
      lines.push(describeFailure(group[0]))
    }
  }
  return lines
}

export function ReliabilityAuditStrip({ clientId, requestId }: { clientId?: string; requestId?: string | null }) {
  const [lines, setLines] = useState<string[]>([])

  useEffect(() => {
    if (!clientId || !requestId) { setLines([]); return }
    let cancelled = false
    getReliabilityEvents(clientId, requestId)
      .then((result) => { if (!cancelled) setLines(summarize(result.events)) })
      .catch(() => { if (!cancelled) setLines([]) })
    return () => { cancelled = true }
  }, [clientId, requestId])

  if (lines.length === 0) return null

  return (
    <div className="mt-2 flex flex-wrap justify-center gap-x-3 gap-y-1 text-[10px] text-severity-warning/80 font-mono print:text-severity-warning">
      <AlertTriangle className="w-3 h-3 shrink-0" aria-hidden="true" />
      {lines.map((line, i) => <span key={i}>{line}</span>)}
    </div>
  )
}
