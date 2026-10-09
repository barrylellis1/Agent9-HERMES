import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { SolutionAssumption } from '../../api/types'
import { assumptionTrust } from '../../utils/trustState'
import { TrustBadge } from '../shared/TrustBadge'

/**
 * What an option bets on — the panel behind every impact range.
 *
 * Phase 13 Cat 3 / M6: an ROI range with no visible assumptions is not shown.
 * This is the answer to the CFO challenge scenario ("where does that number come
 * from"), and it is the single AssumptionsPanel called for by Phase 15 Stage G —
 * there is deliberately no second assumption component.
 *
 * Each bet shows one trust state (utils/trustState.ts) and one plain line
 * saying what backs it. A bet resting on a measurement still reads Assumed:
 * a measurement taken before the decision is not an outcome test, and the
 * line ("Backed by the latest assessment.") carries the difference from one
 * that is only the model's reasoning. Confidence and the raw source sit
 * behind "Why".
 */

interface AssumptionsPanelProps {
  assumptions: SolutionAssumption[]
  /** Rendered in the summary line so the reader knows what the bets are attached to. */
  impactLabel?: string | null
  /** Collapsed by default, per Cat 3. */
  defaultOpen?: boolean
}

export function AssumptionsPanel({ assumptions, impactLabel, defaultOpen = false }: AssumptionsPanelProps) {
  const [open, setOpen] = useState(defaultOpen)
  if (!assumptions.length) return null

  const readings = assumptions.map(assumptionTrust)
  const testedCount = readings.filter(r => r.state === 'tested').length
  const assumedCount = readings.length - testedCount

  return (
    <div data-testid="assumptions-panel" className="mt-4 rounded-lg border border-slate-700 bg-slate-800/30 print:border-slate-200 print:bg-white">
      <button
        onClick={() => setOpen(o => !o)}
        className="flex w-full items-center justify-between gap-2 px-4 py-2.5 text-left transition-colors hover:bg-slate-800/60 print:hidden"
      >
        <span className="flex items-center gap-2 text-xs font-semibold text-slate-300">
          {open ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          What this bets on
          {impactLabel && <span className="font-normal text-slate-500">— behind {impactLabel}</span>}
        </span>
        <span className="flex-shrink-0 text-[10px] text-slate-500">
          {testedCount > 0 && `${testedCount} tested · `}{assumedCount} assumed
        </span>
      </button>

      {/* Print always expands: an assumptions panel that only exists behind a
          click does not survive the PDF an executive actually forwards. */}
      <div className={`${open ? 'block' : 'hidden'} print:block px-4 pb-3 pt-1 print:pt-3`}>
        <p className="mb-2 hidden text-[10px] font-mono uppercase tracking-wider text-slate-500 print:block">
          What this bets on
        </p>
        <ul className="space-y-3">
          {assumptions.map((a, i) => {
            const trust = readings[i]
            const detail = [
              a.confidence ? `${a.confidence} confidence` : null,
              a.validated_at ? `checked ${a.validated_at.slice(0, 10)}` : null,
            ].filter(Boolean).join(' · ')
            return (
              <li key={i} data-testid="assumption-item">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-xs leading-snug text-slate-300 print:text-slate-700">{a.assumption}</p>
                  <TrustBadge state={trust.state} held={trust.held} />
                </div>
                <p className="mt-1 text-[11px] text-slate-500 print:text-slate-600">{trust.line}</p>
                {(detail || a.provenance) && (
                  <>
                    <details className="mt-1 print:hidden">
                      <summary className="cursor-pointer list-none text-[11px] text-slate-500 hover:text-slate-300">
                        ▸ Why
                      </summary>
                      <div className="mt-1 space-y-0.5 text-[11px] text-slate-500">
                        {detail && <p>{detail}</p>}
                        {a.provenance && <p className="font-mono text-[10px]">source: {a.provenance}</p>}
                      </div>
                    </details>
                    {/* A forwarded PDF has no expand, so the checkable source prints. */}
                    {a.provenance && (
                      <p className="mt-0.5 hidden font-mono text-[9px] text-slate-500 print:block">source: {a.provenance}</p>
                    )}
                  </>
                )}
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}

export default AssumptionsPanel
