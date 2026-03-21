import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Loader2,
  TrendingUp,
  Eye,
} from 'lucide-react';
import { AcceptedSolution, SolutionVerdict, StrategyAlignment } from '../types/valueAssurance';

interface PortfolioDashboardProps {
  solutions: AcceptedSolution[];
  totalAttributableImpact: number;
  validatedCount: number;
  partialCount: number;
  failedCount: number;
  measuringCount: number;
  executiveAttentionRequired: string[];
  onSelectSolution?: (solutionId: string) => void;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatDelta(value: number, unit = '%'): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}${unit}`;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return iso;
  }
}

// ─── Badge components ─────────────────────────────────────────────────────────

function VerdictBadge({ status }: { status: SolutionVerdict }) {
  const map: Record<SolutionVerdict, { label: string; className: string; Icon: React.ElementType; pulse?: boolean }> = {
    VALIDATED: { label: 'Validated', className: 'bg-green-100 text-green-800', Icon: CheckCircle2 },
    PARTIAL: { label: 'Partial', className: 'bg-yellow-100 text-yellow-800', Icon: AlertTriangle },
    FAILED: { label: 'Failed', className: 'bg-red-100 text-red-800', Icon: XCircle },
    MEASURING: { label: 'Measuring', className: 'bg-blue-100 text-blue-700', Icon: Loader2, pulse: true },
  };
  const cfg = map[status];
  const { Icon } = cfg;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${cfg.className} ${cfg.pulse ? 'animate-pulse' : ''}`}
    >
      <Icon className="w-2.5 h-2.5" />
      {cfg.label}
    </span>
  );
}

function StrategyBadge({ verdict }: { verdict: StrategyAlignment }) {
  const map: Record<StrategyAlignment, { label: string; className: string; Icon: React.ElementType }> = {
    ALIGNED: { label: 'Aligned', className: 'text-green-400 bg-green-900/20 border border-green-500/30', Icon: CheckCircle2 },
    DRIFTED: { label: 'Drifted', className: 'text-amber-400 bg-amber-900/20 border border-amber-500/30', Icon: AlertTriangle },
    SUPERSEDED: { label: 'Superseded', className: 'text-slate-500 bg-slate-800 border border-slate-700', Icon: XCircle },
  };
  const cfg = map[verdict];
  const { Icon } = cfg;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold ${cfg.className}`}>
      <Icon className="w-2.5 h-2.5" />
      {cfg.label}
    </span>
  );
}

// ─── Summary card ─────────────────────────────────────────────────────────────

interface SummaryCardProps {
  label: string;
  value: string;
  subtext?: string;
  valueClass?: string;
  borderClass?: string;
}

function SummaryCard({ label, value, subtext, valueClass = 'text-white', borderClass = 'border-slate-800' }: SummaryCardProps) {
  return (
    <div className={`bg-slate-900 border ${borderClass} rounded-xl p-5 flex flex-col gap-1`}>
      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">{label}</p>
      <p className={`text-2xl font-bold ${valueClass}`}>{value}</p>
      {subtext && <p className="text-xs text-slate-500">{subtext}</p>}
    </div>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export const PortfolioDashboard: React.FC<PortfolioDashboardProps> = ({
  solutions,
  totalAttributableImpact,
  validatedCount,
  partialCount,
  failedCount,
  measuringCount,
  executiveAttentionRequired,
  onSelectSolution,
}) => {
  const total = solutions.length;
  const pct = (n: number) => (total > 0 ? `${Math.round((n / total) * 100)}%` : '0%');
  const hasAnyEvaluation = solutions.some((s) => !!s.impact_evaluation);

  // Compute total realized impact from trend data when no formal evaluation exists
  const computedImpact = totalAttributableImpact !== 0
    ? totalAttributableImpact
    : solutions.reduce((sum, sol) => {
        if (sol.actual_trend.length > 1) {
          return sum + (sol.actual_trend[sol.actual_trend.length - 1] - sol.actual_trend[0]);
        }
        return sum;
      }, 0);

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          label="Total ROI (est.)"
          value={formatDelta(computedImpact)}
          subtext="Attributable impact across validated solutions"
          valueClass={computedImpact >= 0 ? 'text-emerald-400' : 'text-red-400'}
          borderClass="border-emerald-800/40"
        />
        <SummaryCard
          label="Validated"
          value={`${validatedCount}`}
          subtext={`${pct(validatedCount)} of tracked solutions`}
          valueClass="text-green-400"
          borderClass="border-green-800/40"
        />
        <SummaryCard
          label="Partial"
          value={`${partialCount}`}
          subtext={`${pct(partialCount)} of tracked solutions`}
          valueClass="text-yellow-400"
          borderClass="border-yellow-800/40"
        />
        <SummaryCard
          label="Failed"
          value={`${failedCount}`}
          subtext={`${pct(failedCount)} of tracked solutions`}
          valueClass="text-red-400"
          borderClass="border-red-800/40"
        />
      </div>

      {/* Measuring count note */}
      {measuringCount > 0 && (
        <div className="flex items-center gap-2 text-xs text-blue-400 bg-blue-900/15 border border-blue-500/20 rounded-lg px-4 py-2.5">
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
          <span>{measuringCount} solution{measuringCount > 1 ? 's' : ''} currently in measurement window — results pending.</span>
        </div>
      )}

      {/* Executive attention banner */}
      {executiveAttentionRequired.length > 0 && (
        <div className="flex items-start gap-3 bg-amber-900/15 border border-amber-500/30 rounded-lg px-4 py-3">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <p className="text-xs text-amber-300">
            <span className="font-semibold">{executiveAttentionRequired.length} solution{executiveAttentionRequired.length > 1 ? 's' : ''} require executive review</span>
            {' '}&mdash; strategic context has shifted since approval. See highlighted rows below.
          </p>
        </div>
      )}

      {/* Solution table */}
      {solutions.length === 0 ? (
        <div className="py-16 text-center border border-dashed border-slate-800 rounded-xl">
          <TrendingUp className="w-8 h-8 text-slate-700 mx-auto mb-3" />
          <p className="text-slate-500 text-sm">No solutions are being tracked yet.</p>
          <p className="text-xs text-slate-600 mt-1">Solutions appear here after HITL approval.</p>
        </div>
      ) : (
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          {/* Table header */}
          <div
            className={`grid ${hasAnyEvaluation ? 'grid-cols-[2fr_1fr_auto_auto_1fr_auto_auto_auto]' : 'grid-cols-[2fr_1fr_auto_auto_auto]'} gap-3 px-5 py-3 border-b border-slate-800 bg-slate-950`}
          >
            {(hasAnyEvaluation
              ? ['KPI / Description', 'Approved', 'Verdict', 'Strategy', 'Composite', 'Impact', 'ROI?', '']
              : ['KPI / Description', 'Approved', 'Verdict', 'Impact', '']
            ).map((h, i) => (
              <span key={i} className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                {h}
              </span>
            ))}
          </div>

          {/* Rows */}
          <div className="divide-y divide-slate-800/50">
            {solutions.map((sol) => {
              const needsAttention = executiveAttentionRequired.includes(sol.solution_id);
              const evaluation = sol.impact_evaluation;
              const composite = evaluation?.composite_verdict;
              const strategy = evaluation?.strategy_check?.alignment_verdict;
              const attributable = evaluation?.attributable_impact
                ?? (sol.actual_trend.length > 1
                  ? sol.actual_trend[sol.actual_trend.length - 1] - sol.actual_trend[0]
                  : undefined);

              return (
                <div
                  key={sol.solution_id}
                  className={`grid ${hasAnyEvaluation ? 'grid-cols-[2fr_1fr_auto_auto_1fr_auto_auto_auto]' : 'grid-cols-[2fr_1fr_auto_auto_auto]'} gap-3 px-5 py-4 items-center transition-colors hover:bg-slate-800/30 ${
                    needsAttention ? 'border-l-4 border-amber-500' : 'border-l-4 border-transparent'
                  }`}
                >
                  {/* KPI / Description */}
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-slate-200 truncate">{sol.solution_description}</p>
                    <p className="text-[10px] text-slate-600 font-mono truncate">{sol.kpi_id}</p>
                  </div>

                  {/* Approved */}
                  <p className="text-xs text-slate-500 whitespace-nowrap">{formatDate(sol.approved_at)}</p>

                  {/* Verdict badge */}
                  <VerdictBadge status={sol.status} />

                  {/* Strategy badge — only when evaluations exist */}
                  {hasAnyEvaluation && (
                    strategy ? (
                      <StrategyBadge verdict={strategy} />
                    ) : (
                      <span className="text-[10px] text-slate-600 italic">—</span>
                    )
                  )}

                  {/* Composite label — only when evaluations exist */}
                  {hasAnyEvaluation && (
                    <p className="text-xs text-slate-300 truncate">
                      {composite?.composite_label ?? '—'}
                    </p>
                  )}

                  {/* Attributable impact */}
                  <span
                    className={`text-xs font-mono font-semibold whitespace-nowrap ${
                      attributable !== undefined
                        ? attributable >= 0
                          ? 'text-emerald-400'
                          : 'text-red-400'
                        : 'text-slate-600'
                    }`}
                  >
                    {attributable !== undefined ? formatDelta(attributable) : '—'}
                  </span>

                  {/* ROI eligible — only when evaluations exist */}
                  {hasAnyEvaluation && (
                    composite ? (
                      composite.include_in_roi_totals ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                      ) : (
                        <XCircle className="w-4 h-4 text-slate-600" />
                      )
                    ) : (
                      <span className="text-slate-600 text-xs">—</span>
                    )
                  )}

                  {/* Action */}
                  <button
                    onClick={() => onSelectSolution?.(sol.solution_id)}
                    className="flex items-center gap-1 px-2.5 py-1.5 text-[10px] font-medium text-slate-400 bg-slate-800 hover:bg-slate-700 hover:text-white border border-slate-700 rounded-lg transition-colors whitespace-nowrap"
                  >
                    <Eye className="w-3 h-3" />
                    Details
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
