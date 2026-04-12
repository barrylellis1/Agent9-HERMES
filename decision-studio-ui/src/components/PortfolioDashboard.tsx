import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Loader2,
  TrendingUp,
  Eye,
} from 'lucide-react';
import { AcceptedSolution, SolutionVerdict, SolutionPhase } from '../types/valueAssurance';

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

function isPercentageKpi(kpiId?: string): boolean {
  return !!kpiId && kpiId.endsWith('_pct');
}

/** Cost/expense KPIs where a decrease is a positive business outcome */
function isCostKpi(kpiId?: string): boolean {
  if (!kpiId) return false;
  return /cost|cogs|expense/i.test(kpiId);
}

/** Convert raw delta to business benefit (flip sign for cost KPIs) */
function toBenefit(rawDelta: number, kpiId?: string): number {
  return isCostKpi(kpiId) ? -rawDelta : rawDelta;
}

function formatImpact(value: number, kpiId?: string): string {
  const sign = value >= 0 ? '+' : '';
  if (isPercentageKpi(kpiId)) {
    return `${sign}${value.toFixed(1)}%`;
  }
  // Dollar amounts — abbreviate large values
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `${sign}$${(value / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${sign}$${(value / 1_000).toFixed(0)}K`;
  return `${sign}$${value.toFixed(0)}`;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return iso;
  }
}

function humanizeKpiId(raw: string): string {
  const withoutPrefix = raw.replace(/^[a-z]{2,5}_/, '');
  return withoutPrefix
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

const PHASE_STYLE: Record<SolutionPhase, { label: string; className: string }> = {
  APPROVED: { label: 'Approved', className: 'text-slate-300 bg-slate-700/50' },
  IMPLEMENTING: { label: 'Implementing', className: 'text-amber-400 bg-amber-900/30' },
  LIVE: { label: 'Live', className: 'text-emerald-400 bg-emerald-900/30' },
  MEASURING: { label: 'Measuring', className: 'text-blue-400 bg-blue-900/30' },
  COMPLETE: { label: 'Complete', className: 'text-indigo-400 bg-indigo-900/30' },
};

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
  // Compute total realized benefit — flip sign for cost KPIs so savings count positive
  const dollarBenefit = solutions.reduce((sum, sol) => {
    if (isPercentageKpi(sol.kpi_id)) return sum;
    let rawDelta: number | undefined;
    if (sol.impact_evaluation?.attributable_impact != null) rawDelta = sol.impact_evaluation.attributable_impact;
    else if (sol.actual_trend.length > 1) rawDelta = sol.actual_trend[sol.actual_trend.length - 1] - sol.actual_trend[0];
    if (rawDelta === undefined) return sum;
    return sum + toBenefit(rawDelta, sol.kpi_id);
  }, 0);
  const computedImpact = totalAttributableImpact !== 0 ? totalAttributableImpact : dollarBenefit;

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <SummaryCard
          label="Total ROI (est.)"
          value={formatImpact(computedImpact)}
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
          <div className="grid grid-cols-[1.8fr_0.8fr_0.7fr_0.7fr_0.7fr_auto] gap-4 px-5 py-3 border-b border-slate-800 bg-slate-950">
            {['KPI', 'Approved', 'Phase', 'Verdict', 'Impact', ''].map((h, i) => (
              <span key={i} className={`text-[10px] font-bold text-slate-500 uppercase tracking-wider ${i === 4 ? 'text-right' : ''}`}>
                {h}
              </span>
            ))}
          </div>

          {/* Rows */}
          <div className="divide-y divide-slate-800/50">
            {solutions.map((sol) => {
              const needsAttention = executiveAttentionRequired.includes(sol.solution_id);
              const rawDelta = sol.impact_evaluation?.attributable_impact
                ?? (sol.actual_trend.length > 1
                  ? sol.actual_trend[sol.actual_trend.length - 1] - sol.actual_trend[0]
                  : undefined);
              const attributable = rawDelta !== undefined ? toBenefit(rawDelta, sol.kpi_id) : undefined;
              const phase: SolutionPhase = sol.phase || 'APPROVED';
              const phaseStyle = PHASE_STYLE[phase] || PHASE_STYLE.APPROVED;

              return (
                <div
                  key={sol.solution_id}
                  onClick={() => onSelectSolution?.(sol.solution_id)}
                  className={`grid grid-cols-[1.8fr_0.8fr_0.7fr_0.7fr_0.7fr_auto] gap-4 px-5 py-4 items-center transition-colors cursor-pointer hover:bg-slate-800/40 ${
                    needsAttention ? 'border-l-4 border-amber-500' : 'border-l-4 border-transparent'
                  }`}
                >
                  {/* KPI — humanized name + truncated description */}
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-white truncate">
                      {humanizeKpiId(sol.kpi_id)}
                    </p>
                    <p className="text-[11px] text-slate-500 truncate mt-0.5">{sol.solution_description}</p>
                  </div>

                  {/* Approved date */}
                  <p className="text-xs text-slate-400 whitespace-nowrap">{formatDate(sol.approved_at)}</p>

                  {/* Phase badge */}
                  <div>
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold ${phaseStyle.className}`}>
                      {phaseStyle.label}
                    </span>
                  </div>

                  {/* Verdict badge */}
                  <VerdictBadge status={sol.status} />

                  {/* Impact — right-aligned */}
                  <span
                    className={`text-sm font-mono font-bold whitespace-nowrap text-right ${
                      attributable !== undefined
                        ? attributable >= 0 ? 'text-emerald-400' : 'text-red-400'
                        : 'text-slate-600'
                    }`}
                  >
                    {attributable !== undefined ? formatImpact(attributable, sol.kpi_id) : '—'}
                  </span>

                  {/* Arrow indicator */}
                  <Eye className="w-4 h-4 text-slate-600" />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
