import React from 'react';
import { AlertTriangle, TrendingDown, TrendingUp, Minus } from 'lucide-react';
import { ConfidenceLevel } from '../types/valueAssurance';

interface CostOfInactionBannerProps {
  kpiName: string;
  currentValue: number;
  projected30d: number;
  projected90d: number;
  trendDirection: 'deteriorating' | 'stable' | 'recovering';
  trendConfidence: ConfidenceLevel;
  estimatedRevenueImpact30d?: number;
  estimatedRevenueImpact90d?: number;
  /** e.g. "%" or "$M" — defaults to "%" */
  kpiUnit?: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function formatValue(value: number, unit: string): string {
  return `${value.toFixed(1)}${unit}`;
}

function formatDelta(delta: number, unit: string): string {
  const sign = delta >= 0 ? '+' : '';
  return `${sign}${delta.toFixed(1)}${unit}`;
}

function formatRevenue(value: number): string {
  if (Math.abs(value) >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`;
  }
  return `$${value.toFixed(0)}`;
}

// ─── Trend config ─────────────────────────────────────────────────────────────

type TrendKey = CostOfInactionBannerProps['trendDirection'];

const TREND_CONFIG: Record<
  TrendKey,
  {
    containerClass: string;
    headerClass: string;
    iconClass: string;
    Icon: React.ElementType;
    label: string;
  }
> = {
  deteriorating: {
    containerClass: 'bg-amber-50 border border-amber-300',
    headerClass: 'text-amber-900',
    iconClass: 'text-amber-600',
    Icon: AlertTriangle,
    label: 'Deteriorating',
  },
  stable: {
    containerClass: 'bg-slate-800 border border-slate-700',
    headerClass: 'text-slate-200',
    iconClass: 'text-slate-400',
    Icon: Minus,
    label: 'Stable',
  },
  recovering: {
    containerClass: 'bg-emerald-50 border border-emerald-300',
    headerClass: 'text-emerald-900',
    iconClass: 'text-emerald-600',
    Icon: TrendingUp,
    label: 'Recovering',
  },
};

const CONFIDENCE_LABEL: Record<ConfidenceLevel, string> = {
  HIGH: 'High',
  MODERATE: 'Moderate',
  LOW: 'Low',
};

// ─── Projection row ───────────────────────────────────────────────────────────

interface ProjectionRowProps {
  horizon: string;
  projectedValue: number;
  currentValue: number;
  kpiUnit: string;
  revenueImpact?: number;
  trendDirection: TrendKey;
}

function ProjectionRow({
  horizon,
  projectedValue,
  currentValue,
  kpiUnit,
  revenueImpact,
  trendDirection,
}: ProjectionRowProps) {
  const delta = projectedValue - currentValue;
  const isNegative = delta < 0;

  const valueColorClass =
    trendDirection === 'deteriorating'
      ? 'text-amber-800 font-semibold'
      : trendDirection === 'recovering'
      ? 'text-emerald-700 font-semibold'
      : 'text-slate-400';

  const TrendIcon = isNegative ? TrendingDown : TrendingUp;

  return (
    <li className="flex items-start gap-2 text-sm">
      <TrendIcon
        className={`w-4 h-4 flex-shrink-0 mt-0.5 ${isNegative ? 'text-red-500' : 'text-emerald-500'}`}
      />
      <span>
        <span className="font-medium">In {horizon}:</span>{' '}
        <span className={`font-mono ${valueColorClass}`}>
          {formatValue(projectedValue, kpiUnit)}
        </span>{' '}
        <span className={`font-mono text-xs ${isNegative ? 'text-red-600' : 'text-emerald-600'}`}>
          ({formatDelta(delta, kpiUnit)})
        </span>
        {revenueImpact !== undefined && (
          <>
            {' — '}
            <span className="text-xs text-slate-600">
              est. revenue impact:{' '}
              <span className={`font-semibold ${revenueImpact < 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                {formatRevenue(revenueImpact)}
              </span>
            </span>
          </>
        )}
      </span>
    </li>
  );
}

// ─── Main component ───────────────────────────────────────────────────────────

export const CostOfInactionBanner: React.FC<CostOfInactionBannerProps> = ({
  kpiName,
  currentValue,
  projected30d,
  projected90d,
  trendDirection,
  trendConfidence,
  estimatedRevenueImpact30d,
  estimatedRevenueImpact90d,
  kpiUnit = '%',
}) => {
  const cfg = TREND_CONFIG[trendDirection];
  const { Icon } = cfg;

  return (
    <div className={`rounded-xl px-5 py-4 ${cfg.containerClass}`}>
      {/* Header */}
      <div className={`flex items-center gap-2 mb-3 ${cfg.headerClass}`}>
        <Icon className={`w-4 h-4 flex-shrink-0 ${cfg.iconClass}`} />
        <span className="text-sm font-bold uppercase tracking-wider">Cost of Inaction</span>
      </div>

      {/* Intro line */}
      <p className={`text-xs mb-3 ${trendDirection === 'deteriorating' ? 'text-amber-800' : trendDirection === 'recovering' ? 'text-emerald-800' : 'text-slate-400'}`}>
        If no solution is implemented, {kpiName} is projected to:
      </p>

      {/* Projection rows */}
      <ul className={`space-y-2 mb-4 ${trendDirection === 'deteriorating' ? 'text-amber-900' : trendDirection === 'recovering' ? 'text-emerald-900' : 'text-slate-300'}`}>
        <ProjectionRow
          horizon="30 days"
          projectedValue={projected30d}
          currentValue={currentValue}
          kpiUnit={kpiUnit}
          revenueImpact={estimatedRevenueImpact30d}
          trendDirection={trendDirection}
        />
        <ProjectionRow
          horizon="90 days"
          projectedValue={projected90d}
          currentValue={currentValue}
          kpiUnit={kpiUnit}
          revenueImpact={estimatedRevenueImpact90d}
          trendDirection={trendDirection}
        />
      </ul>

      {/* Footer: trend + confidence */}
      <div className={`flex items-center gap-3 text-xs pt-3 border-t ${
        trendDirection === 'deteriorating'
          ? 'border-amber-200 text-amber-700'
          : trendDirection === 'recovering'
          ? 'border-emerald-200 text-emerald-700'
          : 'border-slate-700 text-slate-500'
      }`}>
        <span>
          Trend:{' '}
          <span className="font-semibold capitalize">{cfg.label}</span>
        </span>
        <span className="opacity-40">|</span>
        <span>
          Confidence:{' '}
          <span className="font-semibold">{CONFIDENCE_LABEL[trendConfidence]}</span>
        </span>
      </div>
    </div>
  );
};
