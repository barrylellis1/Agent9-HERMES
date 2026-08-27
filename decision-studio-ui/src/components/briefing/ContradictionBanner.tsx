/**
 * ContradictionBanner — move #1 of the Executive Briefing redesign
 * (executive_briefing_redesign.md §4, §2.1).
 *
 * A live run's own unresolved_tensions[0] stated that two of its three
 * options rested on contradictory hypotheses about the same root cause —
 * "both cannot be the dominant driver" — from a collapsed accordion at
 * the bottom of a ten-section page. That contradiction IS the decision:
 * not "pick one of three" but "we cannot yet tell which hypothesis is
 * true, and the recommended first action finds out." This component
 * surfaces the FIRST tension above the fold; the full list stays exactly
 * where it already was (the Blind Spots & Tensions accordion) — this is
 * a headline, not a replacement.
 *
 * Sibling to CostOfInactionBanner: same unconditional (non-accordion)
 * placement, same severity-toned treatment. Deliberately NOT folded into
 * DecisionAskBlock, whose own M1 invariant comment says that block is
 * "IDENTICAL for every principal" — a new callout row there would have
 * mixed a workflow-adaptive element into a block designed to never vary.
 */
import { AlertTriangle } from 'lucide-react';
import type { UnresolvedTension } from '../../api/types';

interface ContradictionBannerProps {
  tension: UnresolvedTension;
  /** Opens (if collapsed) and scrolls to the full Blind Spots & Tensions
   *  section — a plain href anchor isn't enough here, since that section's
   *  content is display:none while its accordion is collapsed. Omit to
   *  disable the link (e.g. print view, where the appendix is reached by
   *  reading on, not clicking). */
  onViewDetail?: () => void;
  /** `headline` promotes the tension to the page's lead statement and its
   *  only <h1>. `inline` is the original supporting-callout treatment, kept
   *  for the print path. Default `inline` so no existing caller changes. */
  variant?: 'headline' | 'inline';
}

export function ContradictionBanner({ tension, onViewDetail, variant = 'inline' }: ContradictionBannerProps) {
  const tensionText = typeof tension === 'string' ? tension : tension?.tension;
  if (!tensionText) return null;

  const detailLink = onViewDetail && (
    <button
      type="button"
      onClick={onViewDetail}
      className="inline-block text-xs text-severity-warning hover:text-severity-warning underline mt-2 print:hidden"
    >
      See the full analysis in Blind Spots &amp; Tensions ↓
    </button>
  );

  /* Headline variant — move #1 of executive_briefing_redesign.md, finally at
     the top of the page rather than fifth down it. Two deliberate choices:

     1. The tension text IS the <h1>. There is no "THE OPEN QUESTION" kicker
        above it any more. An uppercase micro-label stacked over a larger
        heading is decoration that the heading already earns on its own, and
        this page had no <h1> at all before now.
     2. The framing that label used to carry moves into a supporting line
        underneath, written as the BLUF consequence — the reader is told what
        the open question MEANS for the decision, not just that one exists. */
  if (variant === 'headline') {
    return (
      <div className="mb-6 border-l-[3px] border-l-severity-warning pl-4 sm:pl-5 print:border-l-amber-600">
        <div className="flex items-start gap-2.5">
          <AlertTriangle className="w-5 h-5 text-severity-warning shrink-0 mt-1.5 print:text-amber-600" />
          <div className="min-w-0">
            <h1 className="text-xl sm:text-2xl font-semibold text-white leading-snug tracking-tight print:text-slate-900">
              {tensionText}
            </h1>
            <p className="text-sm text-severity-warning/80 leading-relaxed mt-2 print:text-amber-800">
              This is unresolved. The recommended first action below is the one that settles it.
            </p>
            {tension?.requires && (
              <p className="text-xs text-slate-400 mt-2 print:text-slate-600">
                Requires: {tension.requires}
              </p>
            )}
            {detailLink}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-severity-warning/40 bg-severity-warning/20 p-4 mb-6 print:bg-amber-50 print:border-amber-200">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-severity-warning shrink-0 mt-0.5 print:text-amber-600" />
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-severity-warning/90 mb-1 print:text-amber-700">
            The open question
          </p>
          <p className="text-sm text-severity-warning leading-relaxed print:text-amber-900">{tensionText}</p>
          {tension?.requires && (
            <p className="text-xs text-severity-warning/80 mt-1.5 print:text-amber-700">
              Requires: {tension.requires}
            </p>
          )}
          {detailLink}
        </div>
      </div>
    </div>
  );
}
