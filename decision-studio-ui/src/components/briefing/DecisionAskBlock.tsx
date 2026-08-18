import { AlertCircle, ArrowRight } from 'lucide-react'
import type { DecisionAsk } from '../../api/types'

/**
 * The above-the-fold block: what happened, what is being asked, what it is worth.
 *
 * Phase 13 Cat 3. This is the 2-minute CFO read — everything below it is
 * supporting detail. Four facts, in the order a decision maker needs them:
 * situation, the ask, the recommended path, the impact range.
 *
 * M2 — THE ASK IS NEVER FABRICATED
 * --------------------------------
 * `decision_ask` is a validated backend field (≤25 words, hedge words rejected
 * at schema validation). When it is absent the block says so plainly instead of
 * assembling a plausible sentence from the recommendation title. A manufactured
 * ask is unattributable: the reader cannot tell whether the model committed to
 * it or the UI wrote it, and this is the one line they act on.
 *
 * M1 — this block is IDENTICAL for every principal. Role adaptation controls
 * what is collapsed below, never the facts or the recommendation here.
 */

interface DecisionAskBlockProps {
  /** At most 3, already trimmed by the caller. */
  situationBullets: string[]
  decisionAsk: DecisionAsk | null
  recommendedPath: string | null
  impactRange: string | null
  /** Fallbacks from the recommendation block, used only to fill the footer row. */
  fallbackOwner?: string | null
  fallbackDeadline?: string | null
}

export function DecisionAskBlock({
  situationBullets, decisionAsk, recommendedPath, impactRange, fallbackOwner, fallbackDeadline,
}: DecisionAskBlockProps) {
  const askText = decisionAsk?.decision_text?.trim() || ''
  const owner = decisionAsk?.decision_owner?.trim() || fallbackOwner || null
  const deadline = decisionAsk?.deadline?.trim() || fallbackDeadline || null
  const approvalType = decisionAsk?.approval_type?.trim() || null

  return (
    <section data-testid="decision-ask-block" className="mb-4 rounded-xl border border-slate-700 bg-slate-900 print:border-slate-300 print:bg-white">
      <div className="px-6 pt-5 pb-4">
        <p className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-2">Situation</p>
        {situationBullets.length > 0 ? (
          <ul className="space-y-1.5 mb-5">
            {situationBullets.map((b, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-300 print:text-slate-700">
                <span className="mt-[7px] h-1 w-1 flex-shrink-0 rounded-full bg-slate-500" />
                <span className="leading-snug">{b}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500 mb-5 print:text-slate-600">No situation summary was produced for this run.</p>
        )}

        {/* The ask */}
        <div className="rounded-lg border-l-4 border-l-indigo-500 bg-slate-800/60 px-4 py-3 print:bg-slate-50 print:border-l-slate-800">
          <p className="text-[10px] font-mono uppercase tracking-widest text-indigo-400 mb-1 print:text-slate-600">
            Decision Ask
          </p>
          {askText ? (
            <p data-testid="decision-ask-text" className="text-base font-semibold leading-snug text-white print:text-slate-900">{askText}</p>
          ) : (
            <div data-testid="decision-ask-absent" className="flex items-start gap-2">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0 text-amber-400 print:text-amber-700" />
              <p className="text-sm text-amber-300 print:text-amber-800">
                This run did not produce a decision ask. Read the recommendation below and state the
                decision yourself — nothing here should be treated as one.
              </p>
            </div>
          )}
          {approvalType && askText && (
            <p className="mt-1.5 text-xs text-slate-400 print:text-slate-600">Approval type: {approvalType}</p>
          )}
        </div>
      </div>

      {/* Recommended path + impact */}
      <div className="grid grid-cols-1 gap-px border-t border-slate-800 bg-slate-800 sm:grid-cols-2 print:border-slate-200 print:bg-white">
        <div className="bg-slate-900 px-6 py-3 print:bg-white">
          <p className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-1">Recommended Path</p>
          <p className="flex items-start gap-1.5 text-sm font-semibold text-emerald-400 print:text-emerald-700">
            <ArrowRight className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
            <span className="leading-snug">{recommendedPath || 'No option was recommended'}</span>
          </p>
        </div>
        <div className="bg-slate-900 px-6 py-3 print:bg-white">
          <p className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-1">Impact Range</p>
          {/* Carries the scope qualifier the backend stamped ("— Engine Oils only",
              "(enterprise)"). Stripping it to fit the tile is how a segment figure
              gets read as an enterprise one, an order of magnitude apart. */}
          <p className="text-sm font-semibold leading-snug text-slate-200 print:text-slate-900">
            {impactRange || 'Not quantified'}
          </p>
        </div>
      </div>

      {(owner || deadline) && (
        <div className="flex items-center justify-between border-t border-slate-800 px-6 py-2.5 print:border-slate-200">
          {owner && (
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-600">Decision Owner</span>
              <p className="text-xs font-semibold text-slate-300 print:text-slate-800">{owner}</p>
            </div>
          )}
          {deadline && (
            <div className="text-right">
              <span className="text-[10px] font-mono uppercase tracking-wider text-slate-600">By</span>
              <p className="text-xs font-semibold text-slate-300 print:text-slate-800">{deadline}</p>
            </div>
          )}
        </div>
      )}
    </section>
  )
}

export default DecisionAskBlock
