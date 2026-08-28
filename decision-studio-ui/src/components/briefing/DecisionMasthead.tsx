import { ContradictionBanner } from './ContradictionBanner';
import type { UnresolvedTension } from '../../api/types';

/**
 * DecisionMasthead — screen-only chrome (eyebrow, subtitle, a stamp badge)
 * wrapped around the existing `ContradictionBanner` headline, per the
 * 2026-08-28 compact-brief restructure.
 *
 * IMPORTANT: this wrapper is NOT `print:hidden`. `ContradictionBanner`
 * already carries its own `print:` classes on every element (verified
 * directly in that file) — it renders on paper today, styled differently
 * from screen, not hidden. A `print:hidden` wrapper here would silently
 * remove the contradiction headline from every exported PDF. Only the NEW
 * chrome this component adds (eyebrow / subtitle / stamp) is screen-only,
 * and that's a deliberate choice, not an oversight: the print-only header
 * block earlier in ExecutiveBriefing.tsx (`hidden print:block`) already
 * renders KPI name, principal, and an "Internal — Decision Sensitive" stamp
 * for the print path — duplicating that text here for print would be the
 * same "recommendation restated three times" problem this page's own
 * comments have fought elsewhere.
 */
interface DecisionMastheadProps {
  tension: UnresolvedTension | undefined;
  onViewDetail?: () => void;
  kpiName?: string | null;
  principalId?: string | null;
  deadline?: string | null;
}

export function DecisionMasthead({ tension, onViewDetail, kpiName, principalId, deadline }: DecisionMastheadProps) {
  const subtitleParts = [kpiName, principalId, deadline].filter(Boolean);

  return (
    <div className="mb-6">
      <div className="print:hidden flex items-center justify-between gap-3 mb-2">
        <span className="text-[10px] font-mono uppercase tracking-widest text-slate-500">Decision brief</span>
        <span className="px-1.5 py-0.5 border border-slate-700 text-slate-500 rounded text-[9px] uppercase tracking-wider whitespace-nowrap">
          Internal — decision sensitive
        </span>
      </div>

      {tension ? (
        <ContradictionBanner tension={tension} onViewDetail={onViewDetail} variant="headline" />
      ) : (
        // No unresolved tension on this run — the page still needs exactly
        // one <h1>. Falls back to the plain title, same as before this
        // component existed.
        <h1 className="text-xl sm:text-2xl font-semibold text-white leading-snug tracking-tight mb-6 print:text-slate-900">
          {kpiName || 'Executive Briefing'}
        </h1>
      )}

      {subtitleParts.length > 0 && (
        <p className="print:hidden text-xs text-slate-500 mt-2">
          {subtitleParts.join(' · ')}
        </p>
      )}
    </div>
  );
}
