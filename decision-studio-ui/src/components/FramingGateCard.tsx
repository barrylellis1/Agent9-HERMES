import { useState } from 'react';
import { Target, Lock, History, User } from 'lucide-react';
import type { FramingPrompt, FramingDecision } from '../api/client';

/**
 * The mandatory framing gate (Phase 19) — a genuinely new visual moment, not
 * a chat-bubble variant. Rendered by ProblemRefinementChat INSTEAD OF the
 * input row and suggested-response chips when `result.framing_prompt` is
 * present: a chip is a click, and the whole point of a structured submit
 * (Decision #4 of the implementation plan) is that a click cannot be
 * mistaken for a considered choice.
 *
 * Phase 20 §14 decision 8 — this card is deliberately LEAN. It used to carry
 * mechanism text, hop/confidence/provenance badges, and caveats per
 * alternative, crammed into the Action Center's narrow column. That evidence
 * now lives in DeepFocusView's LEFT-panel "Causal Neighbourhood" section
 * (CausalNeighbourhoodEvidence.tsx), where there's room for it — plus the
 * trend chart, which never fit here at all.
 *
 * 2026-10-07 — the "alternative" choice (reframe the objective to a
 * different KPI) is retired. It never re-ran DA on the chosen KPI
 * (DeepFocusView.tsx:618's long-standing note: a reframe "still reflects the
 * original KPI's own analysis, re-framed to this decision"), so SF would
 * generate solutions that LOOK like a decided, falsifiable answer for e.g.
 * "Cost of Goods Sold" while actually being grounded in gross_margin_pct's
 * own change-point data — the exact looks-rigorous-but-isn't gap Phase 19
 * exists to catch elsewhere. The honest version of "I think it's really a
 * different KPI" is now the Causal Neighbourhood panel's "Analyze" action,
 * which runs a real, independent DA in a new tab. This card only ever offers
 * two choices: confirm the stated objective, or restate the goal in free
 * text while staying on THIS analysis (e.g. a different success criterion or
 * stakeholder angle — not a KPI switch).
 *
 * NOTHING is pre-selected. Submit stays disabled until a choice is made AND
 * the falsification criterion is non-blank — both are required on every
 * submission (Decision #6), including confirming the stated objective.
 */

interface FramingGateCardProps {
  prompt: FramingPrompt;
  onSubmit: (decision: FramingDecision) => void;
  isSubmitting?: boolean;
}

type Choice = 'confirm_stated' | 'other';

/**
 * Decisions recorded before 2026-10-07 stored a templated sentence
 * ("The objective is Addressing X instead of Y directly — connected N hops
 * away in the causal graph, not recovering Y."). Shown as "Focus on X
 * instead of Y." Anything that does not match is shown unchanged.
 */
function plainPriorObjective(text: string): string {
  const m = text.match(/Addressing (.+?) instead of (.+?) directly/);
  return m ? `Focus on ${m[1]} instead of ${m[2]}.` : text;
}

export function FramingGateCard({ prompt, onSubmit, isSubmitting = false }: FramingGateCardProps) {
  const [choice, setChoice] = useState<Choice | null>(null);
  const [otherText, setOtherText] = useState('');
  const [falsifier, setFalsifier] = useState('');

  const isValid = choice !== null && falsifier.trim().length > 0 &&
    (choice !== 'other' || otherText.trim().length > 0);

  const handleSubmit = () => {
    if (!isValid || choice === null) return;
    const decision: FramingDecision = choice === 'confirm_stated'
      ? {
          choice: 'confirm_stated',
          chosen_objective_text: prompt.stated_objective_text,
          falsification_criterion: falsifier.trim(),
        }
      : {
          choice: 'other',
          chosen_objective_text: otherText.trim(),
          other_text: otherText.trim(),
          falsification_criterion: falsifier.trim(),
        };
    onSubmit(decision);
  };

  return (
    <div data-testid="framing-gate-card" className="flex flex-1 min-h-0 flex-col gap-3 overflow-y-auto p-4">
      <div className="flex items-start gap-2">
        <Target className="mt-0.5 h-4 w-4 flex-shrink-0 text-indigo-400" />
        <div>
          <h4 className="text-sm font-semibold text-white">Confirm the objective</h4>
          <p className="mt-0.5 text-xs text-slate-400">{prompt.question}</p>
        </div>
      </div>

      {/* Owner attribution — non-owners see whose KPI it is before submitting (Decision #5) */}
      {prompt.owner_role && (
        <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
          <User className="h-3 w-3" />
          {prompt.viewer_is_owner
            ? <span>You own this KPI ({prompt.owner_role}).</span>
            : <span>Owned by {prompt.owner_role}. You may still submit — your role will be recorded with the decision.</span>}
        </div>
      )}

      {/* Prior frame — re-presented with its reasoning, never pre-ticked (Decision #5) */}
      {prompt.prior_frame && (
        <div className="flex items-start gap-2 rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2">
          <History className="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-slate-500" />
          <div className="min-w-0 text-[11px] text-slate-400">
            <span className="font-medium text-slate-300">Previously decided:</span>{' '}
            {plainPriorObjective(prompt.prior_frame.chosen_objective_text)}
            {prompt.prior_frame.falsification_criterion && (
              <span className="block mt-0.5 italic text-slate-500">
                Would have been wrong if: {prompt.prior_frame.falsification_criterion}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Active constraints */}
      {prompt.active_constraints?.length > 0 && (
        <div className="rounded-lg border border-slate-700 bg-slate-900/40 px-3 py-2">
          <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-slate-500">
            <Lock className="h-3 w-3" /> Known constraints
          </div>
          <ul className="mt-1 space-y-0.5">
            {prompt.active_constraints.map(c => (
              <li key={c.id} className="text-[11px] text-slate-400">· {c.text}</li>
            ))}
          </ul>
        </div>
      )}

      {prompt.alternatives.length > 0 && (
        <p className="text-[11px] text-slate-500">
          Think a different driver is the real issue? Use <span className="text-slate-400">Analyze</span> on it under <span className="text-slate-400">Related drivers</span>.
        </p>
      )}

      {/* The stated objective — one clearly-labelled option among the others, not pre-selected */}
      <div className="space-y-1.5">
        <button
          type="button"
          data-testid="framing-confirm-stated"
          onClick={() => setChoice('confirm_stated')}
          className={`w-full text-left rounded-lg border px-3 py-2 transition-colors ${
            choice === 'confirm_stated'
              ? 'border-indigo-500 bg-indigo-950/40'
              : 'border-slate-700 bg-slate-800/40 hover:bg-slate-800/70 hover:border-slate-600'
          }`}
        >
          <div className="flex items-center gap-2">
            <Target className="h-3 w-3 flex-shrink-0 text-indigo-400" />
            <span className="text-sm leading-snug text-slate-100">{prompt.stated_objective_text}</span>
            <span className="ml-auto flex-shrink-0 rounded border border-indigo-800 px-1.5 py-px text-[9px] uppercase tracking-wider text-indigo-400">
              stated
            </span>
          </div>
        </button>

        {/* "framing-alternative" buttons used to render here, one per
            prompt.alternatives entry, letting the principal pick a
            different KPI as the objective without ever analysing it. See
            this file's header comment for why that was retired 2026-10-07
            — kept as a plain data-testid-free comment, not a disabled
            stub, so there's nothing here for a stale selector to match. */}

        {/* "Other" free-text option */}
        <div
          className={`rounded-lg border px-3 py-2 transition-colors ${
            choice === 'other' ? 'border-indigo-500 bg-indigo-950/40' : 'border-slate-700 bg-slate-800/40'
          }`}
        >
          <button
            type="button"
            onClick={() => setChoice('other')}
            className="flex w-full items-center gap-2 text-left"
          >
            <span className="text-sm text-slate-100">A different objective</span>
          </button>
          {choice === 'other' && (
            <textarea
              value={otherText}
              onChange={e => setOtherText(e.target.value)}
              placeholder="State the objective this analysis should serve..."
              rows={2}
              className="mt-2 w-full rounded-md border border-slate-600 bg-slate-900 px-2 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          )}
        </div>
      </div>

      {/* Required falsification criterion — every submission, no exceptions */}
      <div>
        <label className="block text-xs font-medium text-slate-300">
          What would tell you this was the wrong objective? <span className="text-severity-critical">*</span>
        </label>
        <textarea
          data-testid="framing-falsifier-input"
          value={falsifier}
          onChange={e => setFalsifier(e.target.value)}
          placeholder="e.g. If the metric doesn't recover after this action, the objective was misidentified."
          rows={2}
          className="mt-1 w-full rounded-md border border-slate-600 bg-slate-900 px-2 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <button
        type="button"
        data-testid="framing-submit"
        onClick={handleSubmit}
        disabled={!isValid || isSubmitting}
        className="w-full rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-700 disabled:text-slate-500"
      >
        {isSubmitting ? 'Recording…' : 'Confirm objective'}
      </button>
    </div>
  );
}

export default FramingGateCard;
