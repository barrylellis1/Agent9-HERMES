/**
 * ReliabilityDrillDown — the "analyst drill-down" from docs/DEVELOPMENT_
 * BACKLOG.md's "Cross-view: Reliability signal surfaces" (#4), built
 * 2026-10-03. Embedded in DeepFocusView's "Analysis" accordion: which checks
 * ran on THIS run, which abstained, which failed — the complete picture, not
 * the briefing footer's exception-only summary (ReliabilityAuditStrip).
 *
 * Shows every reliability.* event scoped to this run's request_id, including
 * `abstain` (unlike the footer strip) — an analyst deciding whether to trust
 * this output needs to see "didn't run" as distinct from "ran clean", not
 * just "found a problem". Surfaces `reason_class` on slice-validity denials
 * (structural vs pipeline_gap) per the backlog's explicit ask: that field is
 * what tells an analyst whether to fix the client's ETL or accept the gap as
 * a permanent fact about the data.
 */
import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { type AuditEventRecord, getReliabilityEvents } from '../../api/client'
import { OutcomeBadge } from './OutcomeBadge'
import { reliabilityEventLabel } from './eventTypeLabels'

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

  return (
    <div className="space-y-2">
      {events.map((e) => (
        <div key={e.id} className="flex items-start justify-between gap-3 bg-slate-950 border border-slate-800 rounded-lg px-3 py-2">
          <div className="min-w-0">
            <div className="text-xs font-medium text-white">{reliabilityEventLabel(e.event_type)}</div>
            {e.resource_id && (
              <div className="text-[10px] text-slate-500 font-mono truncate">{e.resource_id}</div>
            )}
            {typeof e.payload?.reason_class === 'string' && (
              <div className="text-[10px] text-severity-warning mt-0.5">
                reason: {e.payload.reason_class as string}
              </div>
            )}
            {typeof e.payload?.detail === 'string' && (
              <div className="text-[10px] text-slate-400 mt-0.5">{e.payload.detail as string}</div>
            )}
          </div>
          <OutcomeBadge outcome={e.outcome} />
        </div>
      ))}
    </div>
  )
}
