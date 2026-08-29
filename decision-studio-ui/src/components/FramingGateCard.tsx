import { useState } from 'react';
import { Target, Newspaper, Lock, History, User } from 'lucide-react';
import type { FramingPrompt, FramingDecision } from '../api/client';
import { orderedCausalKpiIds, causalColorFor, alternativeShortLabel } from '../utils/causalColors';

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
 * trend chart, which never fit here at all. This card asks a question and
 * collects a decision; it doesn't argue the case. Each option is a color dot
 * (matching the LEFT panel's chart/evidence via utils/causalColors.ts) and a
 * short label — someone answering here references the rich evidence there.
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

type Choice = 'confirm_stated' | { alternative: string } | 'other';

export function FramingGateCard({ prompt, onSubmit, isSubmitting = false }: FramingGateCardProps) {
  const [choice, setChoice] = useState<Choice | null>(null);
  const [otherText, setOtherText] = useState('');
  const [falsifier, setFalsifier] = useState('');

  const ordered = orderedCausalKpiIds(prompt.alternatives);

  const isValid = choice !== null && falsifier.trim().length > 0 &&
    (choice !== 'other' || otherText.trim().length > 0);

  const handleSubmit = () => {
    if (!isValid || choice === null) return;
    let decision: FramingDecision;
    if (choice === 'confirm_stated') {
      decision = {
        choice: 'confirm_stated',
        chosen_objective_text: prompt.stated_objective_text,
        falsification_criterion: falsifier.trim(),
      };
    } else if (choice === 'other') {
      decision = {
        choice: 'other',
        chosen_objective_text: otherText.trim(),
        other_text: otherText.trim(),
        falsification_criterion: falsifier.trim(),
      };
    } else {
      const alt = prompt.alternatives.find(a => a.kpi_id === choice.alternative);
      decision = {
        choice: 'alternative',
        chosen_kpi_id: choice.alternative,
        chosen_objective_text: alt?.objective_text || choice.alternative,
        falsification_criterion: falsifier.trim(),
      };
    }
    onSubmit(decision);
  };

  const isAlternativeSelected = (kpiId: string | null | undefined) =>
    typeof choice === 'object' && choice !== null && 'alternative' in choice && choice.alternative === kpiId;

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
            {prompt.prior_frame.chosen_objective_text}
            {prompt.prior_frame.falsification_criterion && (
              <span className="block mt-0.5 italic text-slate-500">
                Falsifier: {prompt.prior_frame.falsification_criterion}
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
          See <span className="text-slate-400">Causal Neighbourhood</span> on the left for the evidence behind each option below.
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

        {prompt.alternatives.length === 0 && (
          <p className="px-1 text-[11px] italic text-slate-500">
            No specific alternative is suggested by the causal graph or market signals for this KPI —
            confirming is the only option, but the falsifier below still records what would change your mind.
          </p>
        )}

        {prompt.alternatives.map((alt, i) => {
          const isMarket = alt.source === 'market_signal';
          const selected = isAlternativeSelected(alt.kpi_id);
          const dotColor = isMarket ? null : causalColorFor(alt.kpi_id, ordered);
          return (
            <button
              key={`${alt.source}-${alt.kpi_id ?? i}`}
              type="button"
              data-testid="framing-alternative"
              data-source={alt.source}
              data-kpi-id={alt.kpi_id ?? ''}
              onClick={() => alt.kpi_id && setChoice({ alternative: alt.kpi_id })}
              disabled={!alt.kpi_id}
              className={`w-full text-left rounded-lg border px-3 py-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                selected
                  ? 'border-indigo-500 bg-indigo-950/40'
                  : 'border-slate-700 bg-slate-800/40 hover:bg-slate-800/70 hover:border-slate-600'
              }`}
            >
              <div className="flex items-center gap-2">
                {isMarket ? (
                  <Newspaper className="h-3 w-3 flex-shrink-0 text-cyan-400" />
                ) : (
                  <span className="h-2 w-2 flex-shrink-0 rounded-full" style={{ backgroundColor: dotColor ?? undefined }} />
                )}
                <span className="text-sm leading-snug text-slate-100 truncate">{alternativeShortLabel(alt)}</span>
                {alt.neighbour_snapshot?.percent_change != null && (
                  <span className="ml-auto flex-shrink-0 text-[11px] text-slate-400">
                    {alt.neighbour_snapshot.percent_change > 0 ? '+' : ''}
                    {alt.neighbour_snapshot.percent_change.toFixed(1)}%
                  </span>
                )}
              </div>
            </button>
          );
        })}

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
            <span className="text-sm text-slate-100">Something else</span>
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
          What would tell you this frame was wrong? <span className="text-severity-critical">*</span>
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
