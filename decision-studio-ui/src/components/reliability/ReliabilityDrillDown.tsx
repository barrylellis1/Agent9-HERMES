/**
 * ReliabilityDrillDown — the "analyst drill-down" from docs/DEVELOPMENT_
 * BACKLOG.md's "Cross-view: Reliability signal surfaces" (#4), built
 * 2026-10-03. Embedded in DeepFocusView's "Analysis" accordion: which checks
 * ran on THIS run, which were not applicable, which failed — the complete
 * picture, not the briefing footer's exception-only summary
 * (ReliabilityAuditStrip).
 *
 * Shows every reliability.* event scoped to this run's request_id, including
 * `abstain` (unlike the footer strip, which is fail-only) — distinguishing
 * "didn't apply" from "ran clean" matters here. Surfaces `reason_class` on
 * slice-validity denials (structural vs pipeline_gap) per the backlog's
 * explicit ask: that field is what tells an analyst whether to fix the
 * client's ETL or accept the gap as a permanent fact about the data.
 *
 * Collapsing + plain-language explanations added 2026-10-04 (user-caught,
 * live): the first version rendered one raw row per dimension — ten
 * identical "DA — Variance rollup check: abstain" rows for one KPI — and the
 * bare word "abstain" itself, which reads to anyone who isn't the engineer
 * who wrote the house rule (True/False/None, src/analysis/) like a vote
 * declined, not "this check doesn't apply here." Checks that share an
 * event_type, outcome, and reason now collapse into one row with a count;
 * `explainOutcome()` turns the payload into a sentence instead of a status
 * word wherever the event's own `detail` field doesn't already supply one.
 *
 * One-line synthesis added same day, same finding: even collapsed and
 * reworded, the panel still handed a reader two separate technical facts
 * ("citation quality," "ratio-margin bridge") and left them to conclude
 * "so none of this is actionable" themselves — translation work the panel
 * should do, not the reader. The headline now states that conclusion
 * directly; the per-check detail stays visible underneath for whoever wants
 * to verify it rather than take the headline's word for it.
 */
import { useEffect, useState } from 'react'
import { AlertTriangle, CheckCircle2, Loader2, ShieldQuestion } from 'lucide-react'
import { type AuditEventRecord, getReliabilityEvents } from '../../api/client'
import { OutcomeBadge } from './OutcomeBadge'
import { reliabilityEventLabel } from './eventTypeLabels'

// Only used when the event's own payload.detail doesn't already supply a
// sentence (reliability.decision_quality's does, via score_run() — this
// exists for the event types that only carry structured fields).
function explainOutcome(e: AuditEventRecord): string | null {
  const p = e.payload ?? {}
  if (typeof p.detail === 'string' && p.detail) return p.detail
  if (e.outcome !== 'abstain') return null
  switch (e.event_type) {
    case 'reliability.rollup_check':
      // _rollup_check_outcome() abstains for exactly two reasons (src/agents/
      // new/a9_deep_analysis_agent.py) — distinguished here by which field is
      // missing, since the payload doesn't carry a reason code of its own.
      if (p.warehouse_delta === null || p.warehouse_delta === undefined) {
        return 'No comparison figure was available for this period, so there was nothing to check against.'
      }
      return 'This check only runs for ratio KPIs such as margins. This KPI is a plain total, so it did not run.'
    case 'reliability.citation_quality':
      return 'No web search ran, so the market commentary has no source to check.'
    case 'reliability.kpi_coverage':
      return 'No KPIs are registered yet for this client.'
    case 'reliability.detection_confidence':
      return 'No detection score was available for this KPI.'
    default:
      return null
  }
}

interface Group {
  eventType: string
  outcome: AuditEventRecord['outcome']
  explanation: string | null
  resourceIds: string[]
  reasonClasses: string[]
  latestId: string
}

function groupEvents(events: AuditEventRecord[]): Group[] {
  const map = new Map<string, Group>()
  for (const e of events) {
    const explanation = explainOutcome(e)
    const key = `${e.event_type}::${e.outcome}::${explanation ?? ''}`
    const existing = map.get(key)
    const reasonClass = typeof e.payload?.reason_class === 'string' ? e.payload.reason_class : null
    if (existing) {
      if (e.resource_id) existing.resourceIds.push(e.resource_id)
      if (reasonClass && !existing.reasonClasses.includes(reasonClass)) existing.reasonClasses.push(reasonClass)
    } else {
      map.set(key, {
        eventType: e.event_type,
        outcome: e.outcome,
        explanation,
        resourceIds: e.resource_id ? [e.resource_id] : [],
        reasonClasses: reasonClass ? [reasonClass] : [],
        latestId: e.id,
      })
    }
  }
  const order: Record<string, number> = { fail: 0, pass: 1, abstain: 2 }
  return Array.from(map.values()).sort(
    (a, b) => (order[a.outcome ?? ''] ?? 3) - (order[b.outcome ?? ''] ?? 3),
  )
}

// A count only. The ids behind it are registry keys (often the same KPI id
// repeated once per breakdown), which told a reader nothing.
function resourceSummary(ids: string[]): string | null {
  return ids.length > 1 ? `${ids.length} checks of this kind` : null
}

// Reader-facing names for this panel. The operator ReliabilityPanel keeps the
// stage-prefixed labels in eventTypeLabels.ts.
const PLAIN_LABELS: Record<string, string> = {
  'reliability.detection_confidence': 'Detection strength',
  'reliability.kpi_coverage': 'KPI coverage',
  'reliability.rollup_check': 'Segments add up to the total',
  'reliability.slice_validity': 'Breakdowns allowed for this KPI',
  'reliability.tree_reconciliation': 'Parts add up to the KPI',
  'reliability.citation_quality': 'Market sources',
  'reliability.decision_quality': 'Decision quality',
}

// The one-sentence synthesis a reader should walk away with, stated directly
// rather than left for them to infer from the per-check rows below it.
function Headline({ groups }: { groups: Group[] }) {
  const fails = groups.filter((g) => g.outcome === 'fail').length
  const notApplicable = groups.filter((g) => g.outcome === 'abstain').length
  const passes = groups.filter((g) => g.outcome === 'pass').length

  if (fails > 0) {
    return (
      <div className="flex items-center gap-2 text-sm font-medium text-severity-critical mb-1">
        <AlertTriangle className="w-4 h-4 shrink-0" />
        {fails === 1 ? '1 check found a problem' : `${fails} checks found a problem`} — see below.
      </div>
    )
  }
  if (notApplicable > 0) {
    return (
      <div className="flex items-center gap-2 text-sm font-medium text-slate-300 mb-1">
        <ShieldQuestion className="w-4 h-4 shrink-0 text-slate-500" />
        Nothing flagged, but {notApplicable === 1 ? '1 check could not run' : `${notApplicable} checks could not run`} on this analysis. The reason is under each.
      </div>
    )
  }
  if (passes > 0) {
    return (
      <div className="flex items-center gap-2 text-sm font-medium text-severity-opportunity mb-1">
        <CheckCircle2 className="w-4 h-4 shrink-0" />
        All reliability checks passed.
      </div>
    )
  }
  return null
}

export function ReliabilityDrillDown({ clientId, requestId }: { clientId?: string; requestId?: string | null }) {
  const [events, setEvents] = useState<AuditEventRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [degraded, setDegraded] = useState(false)

  useEffect(() => {
    if (!clientId || !requestId) { setEvents([]); return }
    setLoading(true)
    getReliabilityEvents(clientId, requestId)
      .then((r) => { setEvents(r.events); setDegraded(r.status === 'degraded') })
      .catch(() => setEvents([]))
      .finally(() => setLoading(false))
  }, [clientId, requestId])

  if (!requestId) {
    return <p className="text-xs text-slate-500 italic">No reliability evidence available — this analysis has no request id to look evidence up by.</p>
  }
  if (loading) {
    return <Loader2 className="w-4 h-4 animate-spin text-slate-500" />
  }
  if (degraded) {
    return <p className="text-xs text-severity-warning italic">Reliability panel database unavailable — this is not the same as every check passing.</p>
  }
  if (events.length === 0) {
    return <p className="text-xs text-slate-500 italic">No reliability checks recorded for this run.</p>
  }

  const groups = groupEvents(events)

  return (
    <div>
      <Headline groups={groups} />
      <div className="space-y-2 mt-2">
      {groups.map((g) => (
        <div key={g.latestId} className="flex items-start justify-between gap-3 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2">
          <div className="min-w-0">
            <div className="text-xs font-medium text-white">{PLAIN_LABELS[g.eventType] ?? reliabilityEventLabel(g.eventType)}</div>
            {resourceSummary(g.resourceIds) && (
              <div className="text-[10px] text-slate-500">{resourceSummary(g.resourceIds)}</div>
            )}
            {g.reasonClasses.length > 0 && (
              <div className="text-[10px] text-severity-warning mt-0.5">
                reason: {g.reasonClasses.join(', ')}
              </div>
            )}
            {g.explanation && (
              <div className="text-[10px] text-slate-400 mt-0.5">{g.explanation}</div>
            )}
          </div>
          <OutcomeBadge outcome={g.outcome} />
        </div>
      ))}
      </div>
    </div>
  )
}
