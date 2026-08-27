import { useState } from 'react'
import { ChevronDown, ChevronRight, ShieldCheck, HelpCircle } from 'lucide-react'
import type { SolutionAssumption } from '../../api/types'

/**
 * What an option bets on — the panel behind every impact range.
 *
 * Phase 13 Cat 3 / M6: an ROI range with no visible assumptions is not shown.
 * This is the answer to the CFO challenge scenario ("where does that number come
 * from"), and it is the single AssumptionsPanel called for by Phase 15 Stage G —
 * there is deliberately no second assumption component.
 *
 * GROUNDED vs INFERRED IS THE POINT
 * ---------------------------------
 * `grounded` says whether the assumption rests on something measured
 * (an SA assessment, a market query) or on the model's reasoning. Collapsing the
 * two into one undifferentiated bullet list is what makes an inferred claim read
 * with the authority of a measured one. `provenance` names the specific source
 * where one exists.
 *
 * LANGUAGE CAP (theory §4): nothing here says "proved" or "validated" as a
 * verdict. A grounded assumption is one that is *consistent with* what was
 * measured, and the labels are written to stay inside that.
 */

interface AssumptionsPanelProps {
  assumptions: SolutionAssumption[]
  /** Rendered in the summary line so the reader knows what the bets are attached to. */
  impactLabel?: string | null
  /** Collapsed by default, per Cat 3. */
  defaultOpen?: boolean
}

const VALIDATED_BY_LABELS: Record<string, string> = {
  sa_assessment: 'Situation assessment',
  ma_query: 'Market query',
  human_confirmation: 'Confirmed by a person',
}

const CONFIDENCE_TONE: Record<string, string> = {
  high: 'text-emerald-400 border-emerald-700 print:text-emerald-700',
  moderate: 'text-amber-400 border-amber-700 print:text-amber-700',
  low: 'text-red-400 border-red-700 print:text-red-700',
}

export function AssumptionsPanel({ assumptions, impactLabel, defaultOpen = false }: AssumptionsPanelProps) {
  const [open, setOpen] = useState(defaultOpen)
  if (!assumptions.length) return null

  const groundedCount = assumptions.filter(a => a.grounded === true).length
  const inferredCount = assumptions.length - groundedCount

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
        <span className="flex-shrink-0 text-[10px] font-mono text-slate-500">
          {groundedCount} grounded · {inferredCount} inferred
        </span>
      </button>

      {/* Print always expands: an assumptions panel that only exists behind a
          click does not survive the PDF an executive actually forwards. */}
      <div className={`${open ? 'block' : 'hidden'} print:block px-4 pb-3 pt-1 print:pt-3`}>
        <p className="mb-2 hidden text-[10px] font-mono uppercase tracking-wider text-slate-500 print:block">
          What this bets on
        </p>
        <ul className="space-y-2.5">
          {assumptions.map((a, i) => {
            const grounded = a.grounded === true
            return (
              <li key={i} data-testid="assumption-item" className="flex items-start gap-2">
                {grounded ? (
                  <ShieldCheck className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-emerald-500 print:text-emerald-700" />
                ) : (
                  <HelpCircle className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-slate-500 print:text-slate-500" />
                )}
                <div className="min-w-0 flex-1">
                  <p className="text-xs leading-snug text-slate-300 print:text-slate-700">{a.assumption}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-1.5">
                    <span
                      className={`rounded border px-1.5 py-px text-[9px] uppercase tracking-wider ${
                        grounded
                          ? 'border-emerald-800 text-emerald-500 print:text-emerald-700'
                          : 'border-slate-600 text-slate-500'
                      }`}
                    >
                      {grounded ? 'grounded' : 'inferred'}
                    </span>
                    {a.confidence && (
                      <span className={`rounded border px-1.5 py-px text-[9px] uppercase tracking-wider ${CONFIDENCE_TONE[a.confidence] ?? 'border-slate-600 text-slate-500'}`}>
                        {a.confidence} confidence
                      </span>
                    )}
                    {a.validated_by && (
                      <span className="text-[9px] text-slate-400 print:text-slate-500">
                        {VALIDATED_BY_LABELS[a.validated_by] ?? a.validated_by}
                      </span>
                    )}
                    {/* The specific source, when one was recorded. This is what
                        turns "grounded" from a badge into something checkable. */}
                    {a.provenance && (
                      <span className="text-[9px] font-mono text-slate-400 print:text-slate-500">· {a.provenance}</span>
                    )}
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}

export default AssumptionsPanel
