/**
 * DecisionMasthead — screen-only chrome (eyebrow, subtitle, a stamp badge,
 * the page's one <h1>) opening the compact brief, per the 2026-08-28
 * compact-brief restructure.
 *
 * 2026-08-29: this used to conditionally wrap `ContradictionBanner` in its
 * `headline` variant, making an open question the page's lead statement and
 * its <h1>. That moved — see ExecutiveBriefing.tsx's fold-order comment and
 * ContradictionBanner's own docstring for why. This component no longer
 * knows about tensions at all; it always renders the plain title.
 *
 * IMPORTANT: this wrapper is NOT `print:hidden` as a whole, even though the
 * new chrome it adds (eyebrow / subtitle / stamp) IS screen-only below. The
 * print-only header block earlier in ExecutiveBriefing.tsx (`hidden
 * print:block`) already renders KPI name, principal, and an "Internal —
 * Decision Sensitive" stamp for the print path — duplicating that text here
 * for print would be the same "recommendation restated three times" problem
 * this page's own comments have fought elsewhere.
 */
interface DecisionMastheadProps {
  kpiName?: string | null;
  principalId?: string | null;
  deadline?: string | null;
}

export function DecisionMasthead({ kpiName, principalId, deadline }: DecisionMastheadProps) {
  const subtitleParts = [kpiName, principalId, deadline].filter(Boolean);

  return (
    <div className="mb-6">
      <div className="print:hidden flex items-center justify-between gap-3 mb-2">
        <span className="text-[10px] font-mono uppercase tracking-widest text-slate-500">Decision brief</span>
        <span className="px-1.5 py-0.5 border border-slate-700 text-slate-500 rounded text-[9px] uppercase tracking-wider whitespace-nowrap">
          Internal — decision sensitive
        </span>
      </div>

      <h1 className="text-xl sm:text-2xl font-semibold text-white leading-snug tracking-tight mb-6 print:text-slate-900">
        {kpiName || 'Executive Briefing'}
      </h1>

      {subtitleParts.length > 0 && (
        <p className="print:hidden text-xs text-slate-500 mt-2">
          {subtitleParts.join(' · ')}
        </p>
      )}
    </div>
  );
}
