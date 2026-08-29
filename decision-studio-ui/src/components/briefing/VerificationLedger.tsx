import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';

/**
 * VerificationLedger — the distilled "did this survive scrutiny" check, per
 * the 2026-08-28 compact-brief restructure.
 *
 * The data (`moderator_grades`) already flowed through the briefing payload
 * before this — it was rendered in full on this page until the Stage 1/2/
 * Moderator Verdicts accordions moved out to /debate earlier this session.
 * This is that same real data, read again, distilled to 3 lines instead of
 * the full per-option breakdown — not new data, not a new call.
 *
 * Chip color logic copied verbatim from CouncilDebatePage.tsx's own
 * `moderator grades` render (pass→opportunity, fail/flag→critical, else→
 * warning) rather than inventing a second mapping for the same concept.
 *
 * The closing line is the real `grade_rationale` string — the moderator's
 * own prose, explicitly labeled as such. No synthesized "the council
 * converged" summary: no such field exists in the data, and this session
 * has repeatedly declined to fabricate wording that isn't the model's own.
 */
interface VerificationLedgerProps {
  grade: {
    constraint_survival?: string;
    violated_constraints?: string[];
    causal_grounding?: string;
    arithmetic_consistency?: string;
    arithmetic_note?: string | null;
    grade_rationale?: string;
  } | null;
  optionLabel: string;
  situationId: string | undefined;
}

const chipClass = (v: string | undefined) =>
  v === 'pass'
    ? 'text-severity-opportunity border-severity-opportunity print:text-emerald-700 print:border-emerald-600'
    : v === 'fail' || v === 'flag'
      ? 'text-severity-critical border-severity-critical print:text-red-700 print:border-red-600'
      : 'text-severity-warning border-severity-warning print:text-amber-700 print:border-amber-600';

export function VerificationLedger({ grade, optionLabel, situationId }: VerificationLedgerProps) {
  if (!grade) return null;

  return (
    <div className="p-5 space-y-3">
      <p className="text-xs text-slate-400 print:text-slate-600">
        Verification for the recommended option, Option {optionLabel} — graded against the client's
        constraint register, causal model, and the critic's findings.
      </p>

      <div className="space-y-2">
        <div className="flex items-start justify-between gap-3 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 print:border-slate-200 print:bg-white">
          <span className="text-xs text-slate-300 print:text-slate-700">Constraint survival</span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded border font-mono uppercase ${chipClass(grade.constraint_survival)}`}>
            {grade.constraint_survival ?? 'ungraded'}
          </span>
        </div>
        {grade.violated_constraints && grade.violated_constraints.length > 0 && (
          <p className="text-[11px] text-severity-critical pl-3 print:text-red-700">
            Violates: {grade.violated_constraints.join('; ')}
          </p>
        )}

        <div className="flex items-start justify-between gap-3 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 print:border-slate-200 print:bg-white">
          <span className="text-xs text-slate-300 print:text-slate-700">Causal grounding</span>
          <span className="text-[11px] text-slate-400 text-right max-w-[60%] print:text-slate-600">
            {grade.causal_grounding || 'insufficient_data'}
          </span>
        </div>

        <div className="flex items-start justify-between gap-3 rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 print:border-slate-200 print:bg-white">
          <span className="text-xs text-slate-300 print:text-slate-700">Arithmetic consistency</span>
          <span className={`text-[10px] px-1.5 py-0.5 rounded border font-mono uppercase ${chipClass(grade.arithmetic_consistency)}`}>
            {grade.arithmetic_consistency ?? 'ungraded'}
          </span>
        </div>
        {grade.arithmetic_note && (
          <p className="text-[11px] text-severity-warning pl-3 print:text-amber-700">{grade.arithmetic_note}</p>
        )}
      </div>

      {grade.grade_rationale && (
        <p className="text-xs text-slate-500 italic leading-relaxed print:text-slate-600">
          Moderator's rationale: {grade.grade_rationale}
        </p>
      )}

      {situationId && (
        <Link
          to={`/debate/${situationId}`}
          className="print:hidden inline-flex items-center gap-1.5 text-xs text-indigo-300 hover:brightness-125"
        >
          Full council record <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      )}
    </div>
  );
}
