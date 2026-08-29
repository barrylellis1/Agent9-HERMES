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
 *
 * 2026-08-29: the `headline` variant (the tension promoted to the page's
 * lead statement and its <h1>) was removed. Stage 8's own reasoning for it
 * still stands on its own terms — the old five-assertion order (situation,
 * ask, recommended path, owner, cost of inaction, "recommendation at a
 * glance") really did bury a genuine open question behind a wall of
 * false confidence. But leading with it, unconditionally, on every run —
 * including the common case where the open question is a minor,
 * bounded-scope caveat rather than a live-run-grade "both cannot be the
 * dominant driver" — read as alarmist rather than diagnostic, and there
 * was no field signal yet on how often a real production run even carries
 * one. This is a warning now: after Situation + Ask, before the options,
 * not before either of them. See DecisionMasthead and ExecutiveBriefing.tsx's
 * fold-order comment for where it moved to.
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
}

export function ContradictionBanner({ tension, onViewDetail }: ContradictionBannerProps) {
  const tensionText = typeof tension === 'string' ? tension : tension?.tension;
  if (!tensionText) return null;

  const detailLink = onViewDetail && (
    <button
      type="button"
      onClick={onViewDetail}
 className="hover:brightness-125 inline-block text-xs text-severity-warning underline mt-2 print:hidden"
    >
      See the full analysis in Blind Spots &amp; Tensions ↓
    </button>
  );

  return (
    <div data-testid="contradiction-banner" className="rounded-xl border border-severity-warning/40 bg-severity-warning/20 p-4 mb-6 print:bg-amber-50 print:border-amber-200">
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
