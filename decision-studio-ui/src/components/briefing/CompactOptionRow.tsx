import { CheckCircle, ChevronRight, AlertTriangle, Users, Zap } from 'lucide-react';
import { RangeBar } from './RangeBar';
import { AssumptionsPanel } from './AssumptionsPanel';
import { condenseTimeToValue } from '../../utils/briefingUtils';

/**
 * CompactOptionRow — replaces the comparison `<table>` + the per-option full
 * card's header/metrics band, per the 2026-08-28 compact-brief restructure.
 *
 * One format at every breakpoint (no `hidden lg:block` split) — a vertical
 * list has no width constraint the table did, which is what forced the old
 * table into a `lg`-only, `print:!block` existence in the first place.
 *
 * The narrative content the old full card held below its header (description,
 * print-only pros/cons/council-lenses, side-effects chip, AssumptionsPanel,
 * "View full analysis" drawer trigger) is unchanged and un-simplified — only
 * the header/metrics band above it is restructured from
 * table-row-plus-separate-4-box-grid into one compact row + a RangeBar.
 *
 * Print: this row IS the printed comparison exhibit now (the table used to
 * be, forced visible via `print:!block` regardless of screen width — see the
 * 2026-08-28 plan note). Nothing here is `print:hidden`; RangeBar hides
 * itself on print and the ROI number carries the substance instead.
 */
interface CompactOptionRowProps {
  option: any;
  letter: string;
  dominatorLetter: string | null;
  maxRange: number | null;
  onOpenDrawer: () => void;
}
// Staggered entrance stays owned by the caller (ExecutiveBriefing.tsx already
// wraps each row in a motion.div with a reduceMotion-aware stagger delay) —
// not duplicated in here.

/** Self-describing phrasing, matching the reference mockup's own chip style
 *  ("Easily reversed", "Hard to undo") rather than a bare enum value with no
 *  label — a bare "high"/"medium"/"low" chip is ambiguous out of context
 *  (high WHAT?) in a way "Moderate Effort" or "0-90 days" naturally aren't.
 *  Falls back to the raw value (title-cased) for anything unmapped (e.g.
 *  Option 0's 'n/a'), so a new backend value never renders blank. */
const REVERSIBILITY_LABEL: Record<string, string> = {
  high: 'Easily reversed',
  medium: 'Partly reversible',
  low: 'Hard to undo',
};

function reversibilityLabel(value: string | undefined): string {
  if (!value) return 'Reversibility unknown';
  return REVERSIBILITY_LABEL[value.toLowerCase()] || value.charAt(0).toUpperCase() + value.slice(1);
}

function ScopeChip({ scopeQualifier }: { scopeQualifier: any }) {
  if (scopeQualifier?.scope === 'enterprise') {
    return (
      <span className="inline-block px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide bg-slate-700/60 text-slate-300 print:bg-slate-200 print:text-slate-700">
        Enterprise
      </span>
    );
  }
  if (scopeQualifier?.scope === 'segment') {
    return (
      <span className="inline-block px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide bg-indigo-900/40 text-indigo-300 print:bg-indigo-100 print:text-indigo-700">
        Segment{scopeQualifier.label ? `: ${scopeQualifier.label}` : ''}
      </span>
    );
  }
  return (
    <span className="inline-block px-1.5 py-0.5 rounded text-[9px] font-semibold uppercase tracking-wide bg-severity-warning/20 text-severity-warning/90 print:bg-amber-100 print:text-amber-700">
      Scope unverified
    </span>
  );
}

export function CompactOptionRow({ option, letter, dominatorLetter, maxRange, onOpenDrawer }: CompactOptionRowProps) {
  const dominated = !!dominatorLetter;
  const range = option.impactRangeNumeric;
  const tone: 'recommended' | 'default' | 'dominated' = dominated ? 'dominated' : option.recommended ? 'recommended' : 'default';

  return (
    <div
      className={`rounded-xl border overflow-hidden print:overflow-visible ${
        option.recommended ? 'border-slate-600 border-l-4 border-l-severity-opportunity bg-slate-900' : 'border-slate-700 bg-slate-900'
      } print:bg-white print:border-slate-200 ${option.recommended ? 'print:border-l-slate-800' : ''} ${dominated ? 'opacity-60' : ''}`}
    >
      {option.recommended && (
        <div className="bg-severity-opportunity/40 text-severity-opportunity px-4 py-1.5 text-xs font-semibold flex items-center gap-2 print:bg-slate-800 print:text-white">
          <CheckCircle className="w-3.5 h-3.5" /> RECOMMENDED
        </div>
      )}

      <div className="p-5">
        {/* Compact header: letter + title + chip row + range bar/ROI. */}
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-start gap-2">
              <span className="text-[10px] font-bold text-slate-400 border border-slate-700 rounded w-4 h-4 flex items-center justify-center flex-shrink-0 mt-0.5 print:text-slate-600 print:border-slate-400">
                {letter}
              </span>
              <h3 className="text-base font-bold text-white print:text-slate-900 line-clamp-3 min-w-0">
                {option.title}
              </h3>
            </div>
            {dominated && (
              <p className="text-[11px] text-severity-warning/90 mt-1 ml-6 leading-snug print:text-amber-700">
                Dominated by Option {dominatorLetter} — matches or underperforms it on modelled impact, cost, and risk.
              </p>
            )}
            <div className="flex flex-wrap items-center gap-1.5 mt-2 ml-6">
              <span className="text-[9px] font-medium uppercase tracking-wide px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 print:bg-slate-100 print:text-slate-600">
                {option.investment}
              </span>
              <span
                className="text-[9px] font-medium uppercase tracking-wide px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 print:bg-slate-100 print:text-slate-600"
                title={option.timeline}
              >
                {condenseTimeToValue(option.timeline)}
              </span>
              <span
                className="text-[9px] font-medium uppercase tracking-wide px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 print:bg-slate-100 print:text-slate-600"
                title={`Reversibility: ${option.reversibility}`}
              >
                {reversibilityLabel(option.reversibility)}
              </span>
              <ScopeChip scopeQualifier={option.scopeQualifier} />
            </div>
          </div>

          {/* Measure panel */}
          <div className="sm:w-48 flex-shrink-0 ml-6 sm:ml-0">
            <p className="text-[10px] text-slate-500 uppercase tracking-wider print:text-slate-500">Est. ROI</p>
            <p className="text-lg font-bold text-severity-opportunity print:text-emerald-600">{option.roi}</p>
            {range && maxRange && (
              <div className="mt-1.5">
                <RangeBar low={range.low} high={range.high} max={maxRange} tone={tone} />
              </div>
            )}
          </div>
        </div>

        <p className="text-slate-300 text-sm leading-relaxed mb-4 print:text-slate-700">{option.description}</p>

        {/* Full narrative: PRINT ONLY — unchanged from the prior full-card
            markup. On screen this lives in the drawer; on paper there is no
            drawer to open. */}
        <div className="hidden print:block">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <h4 className="font-semibold text-slate-300 mb-2 flex items-center gap-1.5 text-sm print:text-slate-700">
                <CheckCircle className="w-3.5 h-3.5 text-slate-500" /> Arguments For
              </h4>
              <ul className="space-y-1.5">
                {option.prosDetailed?.map((pro: any, j: number) => (
                  <li key={j} className="text-xs text-slate-400 flex items-start gap-1.5 print:text-slate-700">
                    <ChevronRight className="w-3.5 h-3.5 text-slate-600 flex-shrink-0 mt-0.5" />
                    <span>{pro.point?.replace(/[:]+$/, '')}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-slate-300 mb-2 flex items-center gap-1.5 text-sm print:text-slate-700">
                <AlertTriangle className="w-3.5 h-3.5 text-slate-500" /> Arguments Against
              </h4>
              <ul className="space-y-1.5">
                {option.consDetailed?.map((con: any, j: number) => (
                  <li key={j} className="text-xs text-slate-400 flex items-start gap-1.5 print:text-slate-700">
                    <ChevronRight className="w-3.5 h-3.5 text-slate-600 flex-shrink-0 mt-0.5" />
                    <span>{con.point?.replace(/[:]+$/, '')}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          {option.lens_views && (
            <div className="mt-4 pt-4 border-t border-slate-700 print:border-slate-200">
              <h4 className="font-semibold text-slate-200 mb-2 flex items-center gap-1.5 text-sm print:text-slate-900">
                <Users className="w-3.5 h-3.5" /> Council Lenses
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {option.lens_views.map((p: any, j: number) => (
                  <div key={j} className="bg-slate-800/60 p-2.5 rounded-lg print:bg-slate-50">
                    <p className="font-medium text-slate-200 text-xs print:text-slate-900">{p.role}</p>
                    <p className="text-xs text-slate-400 mt-0.5 print:text-slate-600">{p.view}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {option.flagged_side_effects?.length > 0 && (
          <div data-testid="side-effects-chip" className="print:hidden mt-3 flex items-start gap-2 rounded-lg border border-severity-warning/50 bg-severity-warning/20 px-3 py-2">
            <Zap className="w-3.5 h-3.5 text-severity-warning flex-shrink-0 mt-0.5" />
            <p className="text-xs text-severity-warning/90">
              {option.flagged_side_effects.length} side effect{option.flagged_side_effects.length === 1 ? '' : 's'} flagged
              against the causal model — see full analysis.
            </p>
          </div>
        )}

        <AssumptionsPanel assumptions={option.key_assumptions || []} impactLabel={option.roi} />

        <button
          onClick={onOpenDrawer}
          className="print:hidden mt-4 inline-flex items-center gap-1.5 rounded-lg border border-slate-700 px-3 py-1.5 text-xs font-medium text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-800 hover:text-white"
        >
          View full analysis
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
