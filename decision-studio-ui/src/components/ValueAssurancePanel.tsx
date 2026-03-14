import React from 'react';
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Loader2,
  TrendingUp,
  FileText,
  BarChart2,
  Clock,
} from 'lucide-react';
import {
  SolutionVerdict,
  ImpactEvaluation,
  CompositeVerdict,
  StrategyAlignment,
} from '../types/valueAssurance';

interface ValueAssurancePanelProps {
  solutionId: string;
  solutionDescription: string;
  approvedAt: string;
  status: SolutionVerdict;
  evaluation?: ImpactEvaluation;
  compositeVerdict?: CompositeVerdict;
  onViewAttribution?: () => void;
  onViewNarrative?: () => void;
}

// ─── Badge helpers ──────────────────────────────────────────────────────────

const VERDICT_CONFIG: Record<
  SolutionVerdict,
  { label: string; className: string; Icon: React.ElementType; pulse: boolean }
> = {
  VALIDATED: {
    label: 'Validated',
    className: 'bg-green-100 text-green-800',
    Icon: CheckCircle2,
    pulse: false,
  },
  PARTIAL: {
    label: 'Partial',
    className: 'bg-yellow-100 text-yellow-800',
    Icon: AlertTriangle,
    pulse: false,
  },
  FAILED: {
    label: 'Failed',
    className: 'bg-red-100 text-red-800',
    Icon: XCircle,
    pulse: false,
  },
  MEASURING: {
    label: 'Measuring',
    className: 'bg-blue-100 text-blue-700',
    Icon: Loader2,
    pulse: true,
  },
};

const ALIGNMENT_CONFIG: Record<
  StrategyAlignment,
  { label: string; className: string; Icon: React.ElementType; iconClass: string }
> = {
  ALIGNED: {
    label: 'Aligned',
    className: 'bg-green-900/20 border border-green-500/30 text-green-400',
    Icon: CheckCircle2,
    iconClass: 'text-green-400',
  },
  DRIFTED: {
    label: 'Drifted',
    className: 'bg-amber-900/20 border border-amber-500/30 text-amber-400',
    Icon: AlertTriangle,
    iconClass: 'text-amber-400',
  },
  SUPERSEDED: {
    label: 'Superseded',
    className: 'bg-slate-800 border border-slate-700 text-slate-500 line-through',
    Icon: XCircle,
    iconClass: 'text-slate-500',
  },
};

const CONFIDENCE_COLORS: Record<string, string> = {
  HIGH: 'text-green-400',
  MODERATE: 'text-amber-400',
  LOW: 'text-red-400',
};

// ─── Sub-components ──────────────────────────────────────────────────────────

function VerdictBadge({ status }: { status: SolutionVerdict }) {
  const cfg = VERDICT_CONFIG[status];
  const { Icon } = cfg;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${cfg.className} ${cfg.pulse ? 'animate-pulse' : ''}`}
    >
      <Icon className="w-3 h-3" />
      {cfg.label}
    </span>
  );
}

function AlignmentBadge({ verdict }: { verdict: StrategyAlignment }) {
  const cfg = ALIGNMENT_CONFIG[verdict];
  const { Icon } = cfg;
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${cfg.className}`}
    >
      <Icon className={`w-3 h-3 ${cfg.iconClass}`} />
      {cfg.label}
    </span>
  );
}

function formatDelta(value: number, unit = '%'): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}${unit}`;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  } catch {
    return iso;
  }
}

// ─── Measuring placeholder ───────────────────────────────────────────────────

function MeasuringPlaceholder({
  solutionDescription,
  approvedAt,
}: {
  solutionDescription: string;
  approvedAt: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-center gap-4 opacity-70">
      <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
      <div>
        <p className="text-sm font-medium text-slate-300">Measurement in progress</p>
        <p className="text-xs text-slate-500 mt-1">
          Approved {formatDate(approvedAt)} &mdash; results expected once the measurement window
          closes.
        </p>
      </div>
      <div className="flex items-center gap-2 text-xs text-blue-400 bg-blue-900/20 border border-blue-500/20 rounded-lg px-4 py-2">
        <Clock className="w-3.5 h-3.5" />
        <span>Tracking: {solutionDescription}</span>
      </div>
    </div>
  );
}

// ─── Main component ──────────────────────────────────────────────────────────

export const ValueAssurancePanel: React.FC<ValueAssurancePanelProps> = ({
  solutionId: _solutionId,
  solutionDescription,
  approvedAt,
  status,
  evaluation,
  compositeVerdict,
  onViewAttribution,
  onViewNarrative,
}) => {
  const alignmentVerdict = evaluation?.strategy_check?.alignment_verdict;
  const driftSummary = evaluation?.strategy_check?.drift_summary;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
      {/* Header row */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <TrendingUp className="w-4 h-4 text-indigo-400 flex-shrink-0" />
          <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider">
            Value Assurance
          </h3>
          <VerdictBadge status={status} />
        </div>
        <p className="text-xs text-slate-500 truncate max-w-[260px]">
          {solutionDescription} &mdash; approved {formatDate(approvedAt)}
        </p>
      </div>

      {/* Body */}
      {status === 'MEASURING' ? (
        <MeasuringPlaceholder
          solutionDescription={solutionDescription}
          approvedAt={approvedAt}
        />
      ) : evaluation ? (
        <>
          {/* KPI Impact + Strategy row */}
          <div className="grid grid-cols-2 divide-x divide-slate-800 border-b border-slate-800">
            {/* KPI Impact */}
            <div className="px-6 py-5 space-y-3">
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                KPI Impact
              </p>

              {/* Total change */}
              <div className="flex items-baseline gap-2">
                <span
                  className={`text-2xl font-bold ${
                    evaluation.total_kpi_change >= 0 ? 'text-emerald-400' : 'text-red-400'
                  }`}
                >
                  {formatDelta(evaluation.total_kpi_change)}
                </span>
                <span className="text-xs text-slate-500">
                  (expected: {formatDelta(evaluation.expected_impact_lower)} to{' '}
                  {formatDelta(evaluation.expected_impact_upper)})
                </span>
              </div>

              {/* Attribution rows */}
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Attributable</span>
                  <span
                    className={`font-mono font-medium ${
                      evaluation.attributable_impact >= 0 ? 'text-emerald-400' : 'text-red-400'
                    }`}
                  >
                    {formatDelta(evaluation.attributable_impact)}
                  </span>
                </div>
                {evaluation.market_driven_recovery !== 0 && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Market recovery</span>
                    <span className="font-mono text-blue-400">
                      {formatDelta(evaluation.market_driven_recovery)}
                    </span>
                  </div>
                )}
                {evaluation.seasonal_component !== 0 && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Seasonal</span>
                    <span className="font-mono text-purple-400">
                      {formatDelta(evaluation.seasonal_component)}
                    </span>
                  </div>
                )}
                {evaluation.control_group_change !== 0 && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Control group adj.</span>
                    <span className="font-mono text-slate-400">
                      {formatDelta(evaluation.control_group_change)}
                    </span>
                  </div>
                )}
              </div>
            </div>

            {/* Strategy Alignment */}
            <div className="px-6 py-5 space-y-3">
              <p className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Strategy Alignment
              </p>
              {alignmentVerdict ? (
                <>
                  <AlignmentBadge verdict={alignmentVerdict} />
                  {driftSummary && (
                    <p className="text-xs text-slate-400 leading-relaxed">{driftSummary}</p>
                  )}
                  {!driftSummary && alignmentVerdict === 'ALIGNED' && (
                    <p className="text-xs text-slate-500">Priorities unchanged since approval.</p>
                  )}
                </>
              ) : (
                <span className="text-xs text-slate-600 italic">No alignment data</span>
              )}
            </div>
          </div>

          {/* Confidence row */}
          <div className="px-6 py-4 border-b border-slate-800 space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Confidence
              </span>
              <span
                className={`text-xs font-semibold ${CONFIDENCE_COLORS[evaluation.confidence] ?? 'text-slate-400'}`}
              >
                {evaluation.confidence}
              </span>
            </div>
            {evaluation.confidence_rationale && (
              <p className="text-xs text-slate-500">{evaluation.confidence_rationale}</p>
            )}
            {evaluation.control_group_description && (
              <p className="text-xs text-slate-600 italic">
                Control group: {evaluation.control_group_description}
              </p>
            )}
          </div>

          {/* Composite verdict + actions */}
          <div className="px-6 py-4 flex items-center justify-between flex-wrap gap-3">
            <div className="space-y-1">
              {compositeVerdict && (
                <>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-500 uppercase tracking-wider">
                      Composite
                    </span>
                    <span className="text-sm font-bold text-white">
                      {compositeVerdict.composite_label}
                    </span>
                    {compositeVerdict.include_in_roi_totals ? (
                      <span className="inline-flex items-center gap-1 text-[10px] bg-emerald-900/30 border border-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded-full">
                        <CheckCircle2 className="w-2.5 h-2.5" /> Include in ROI
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-[10px] bg-slate-800 border border-slate-700 text-slate-500 px-2 py-0.5 rounded-full">
                        <XCircle className="w-2.5 h-2.5" /> Excluded from ROI
                      </span>
                    )}
                  </div>
                  {compositeVerdict.executive_attention_required && (
                    <p className="text-xs text-amber-400 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      Executive attention required
                    </p>
                  )}
                  <p className="text-xs text-slate-500">{compositeVerdict.recommended_action}</p>
                </>
              )}
            </div>
            <div className="flex items-center gap-2">
              {onViewAttribution && (
                <button
                  onClick={onViewAttribution}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors"
                >
                  <BarChart2 className="w-3.5 h-3.5" />
                  View Attribution
                </button>
              )}
              {onViewNarrative && (
                <button
                  onClick={onViewNarrative}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors"
                >
                  <FileText className="w-3.5 h-3.5" />
                  Read Narrative
                </button>
              )}
            </div>
          </div>
        </>
      ) : (
        /* Evaluated but no data returned — graceful fallback */
        <div className="px-6 py-10 text-center text-slate-600 text-sm italic">
          No evaluation data available.
        </div>
      )}
    </div>
  );
};
