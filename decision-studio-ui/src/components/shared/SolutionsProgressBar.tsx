import { Link } from 'react-router-dom';
import { BarChart3, ChevronRight } from 'lucide-react';
import type { StrategyAwarePortfolio } from '../../types/valueAssurance';

interface SolutionsProgressBarProps {
  portfolio: StrategyAwarePortfolio;
  selectedPrincipal: string;
}

// Inline color references so rendering never depends on Tailwind JIT picking up new classes
const C = {
  opportunity: 'rgb(52 211 153)',   // emerald-400  --color-severity-opportunity
  warning:     'rgb(251 191 36)',   // amber-400    --color-severity-warning
  critical:    'rgb(248 113 113)',  // red-400      --color-severity-critical
  measuring:   'rgb(100 116 139)',  // slate-500
} as const;

export function SolutionsProgressBar({ portfolio, selectedPrincipal }: SolutionsProgressBarProps) {
  const total     = portfolio.total_solutions;
  const validated = portfolio.validated_count;
  const partial   = portfolio.partial_count;
  const failed    = portfolio.failed_count;
  const measuring = portfolio.measuring_count;

  const pct = (n: number) => `${Math.round((n / total) * 100)}%`;

  return (
    <section className="animate-in slide-in-from-top-4 fade-in duration-500">
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-slate-800 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-slate-400" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">Solutions in Progress</h3>
              <p className="text-xs text-slate-500 mt-0.5">{total} total</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {portfolio.executive_attention_required.length > 0 && (
              <span
                className="text-xs px-2.5 py-1 rounded-full"
                style={{ color: C.warning, backgroundColor: `${C.warning}1a` }}
              >
                {portfolio.executive_attention_required.length} need attention
              </span>
            )}
            <Link
              to={`/portfolio?principal=${encodeURIComponent(selectedPrincipal)}`}
              className="flex items-center gap-1 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors"
            >
              View All <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Segmented progress bar */}
        <div className="flex h-1.5 rounded-full overflow-hidden gap-px">
          {validated > 0 && (
            <div style={{ width: pct(validated), backgroundColor: C.opportunity }} title={`${validated} validated`} />
          )}
          {measuring > 0 && (
            <div style={{ width: pct(measuring), backgroundColor: C.measuring }} title={`${measuring} measuring`} />
          )}
          {partial > 0 && (
            <div style={{ width: pct(partial), backgroundColor: C.warning }} title={`${partial} partial`} />
          )}
          {failed > 0 && (
            <div style={{ width: pct(failed), backgroundColor: C.critical }} title={`${failed} failed`} />
          )}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 mt-2">
          {validated > 0 && (
            <span className="text-[11px]" style={{ color: C.opportunity }}>{validated} validated</span>
          )}
          {measuring > 0 && (
            <span className="text-[11px] text-slate-400">{measuring} measuring</span>
          )}
          {partial > 0 && (
            <span className="text-[11px]" style={{ color: C.warning }}>{partial} partial</span>
          )}
          {failed > 0 && (
            <span className="text-[11px] font-medium" style={{ color: C.critical }}>{failed} failed</span>
          )}
        </div>
      </div>
    </section>
  );
}
