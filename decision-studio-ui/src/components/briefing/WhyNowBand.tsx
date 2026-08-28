import { CostOfInactionBanner, CostOfInactionBannerProps } from '../CostOfInactionBanner';
import { formatExecutive } from '../../utils/formatExecutive';

/**
 * WhyNowBand — merges "why now" (the situation) and "cost of waiting" into
 * one two-column band, per the 2026-08-28 compact-brief restructure. Both
 * used to be two separate cards (situation bullets inside DecisionAskBlock,
 * CostOfInactionBanner on its own); the mockup this mirrors treats them as
 * one question with two halves.
 *
 * Note on scope, corrected during implementation: the original plan's
 * component-boundary table said DecisionAskBlock "keeps" the situation
 * bullets AND said this component takes them over — an internal
 * contradiction. Resolved in favour of the mockup's actual structure: "the
 * ask" is one sentence with no supporting bullets; the situation bullets
 * belong here, in the "why now" pane. DecisionAskBlock's situationBullets
 * prop is no longer passed a value at the ExecutiveBriefing.tsx call site.
 *
 * Divider-grid idiom matches DecisionAskBlock.tsx's own 2-col footer
 * (`grid grid-cols-1 gap-px border-t border-slate-800 bg-slate-800
 * sm:grid-cols-2`) — not a new pattern.
 */
interface WhyNowBandProps {
  /** The situation's own problem statement — real prose, unedited. */
  problem?: string | null;
  /** Up to 2 root-cause bullets, same shape ExecutiveBriefing.tsx already
   *  builds from `data.situation.rootCauses` (driver/dimension/impact). */
  bullets: string[];
  /** The KPI-level delta driving this briefing (current - comparison),
   *  already computed by the caller — real, not derived here. Null when
   *  there's no comparison value to diff against. */
  headlineDelta: number | null;
  headlineUnit?: string | null;
  /** Bug caught rendering this against real data: the stat used to be
   *  hardcoded critical/red regardless of sign, which is backwards for an
   *  opportunity situation (a positive delta there is good news). Driven by
   *  the same `data.cardType === 'opportunity'` check the page's own
   *  opportunity badge already uses, not re-derived from the sign of
   *  headlineDelta alone — some KPIs are inverse-logic (a cost going down is
   *  good), so sign alone isn't a reliable tone signal. */
  isOpportunity?: boolean;
  costOfInaction: Omit<CostOfInactionBannerProps, 'bare'> | null;
}

export function WhyNowBand({ problem, bullets, headlineDelta, headlineUnit, isOpportunity, costOfInaction }: WhyNowBandProps) {
  const isPercent = headlineUnit === '%' || headlineUnit === 'pp';
  const statText = headlineDelta != null
    ? formatExecutive(headlineDelta, { showSign: false, isPercent, unit: isPercent ? undefined : (headlineUnit || '$') })
    : null;
  const statTone = isOpportunity
    ? 'text-severity-opportunity print:text-emerald-600'
    : 'text-severity-critical print:text-red-600';

  return (
    <div
      className="mb-6 rounded-xl border border-slate-700 bg-slate-800 grid grid-cols-1 gap-px sm:grid-cols-2 overflow-hidden print:border-slate-200 print:bg-white"
      data-testid="why-now-band"
    >
      <div className="bg-slate-900 px-6 py-5 print:bg-white">
        <span className="text-[10px] font-mono uppercase tracking-widest text-slate-500">Why now</span>
        {statText && (
          <p className={`text-3xl font-mono font-bold tracking-tight mt-1 ${statTone}`}>
            {statText}
          </p>
        )}
        {problem && (
          <p className="text-xs text-slate-400 leading-relaxed mt-2 print:text-slate-700">{problem}</p>
        )}
        {bullets.length > 0 && (
          <ul className="mt-2.5 space-y-1 text-xs text-slate-400 print:text-slate-600">
            {bullets.map((b, i) => (
              <li key={i} className="flex gap-1.5">
                <span className="text-slate-600 print:text-slate-400">·</span>
                <span>{b}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div className="bg-slate-900 px-6 py-5 print:bg-white">
        {costOfInaction ? (
          <CostOfInactionBanner {...costOfInaction} bare />
        ) : (
          <p className="text-xs text-slate-500">No cost-of-inaction projection available for this KPI.</p>
        )}
      </div>
    </div>
  );
}
