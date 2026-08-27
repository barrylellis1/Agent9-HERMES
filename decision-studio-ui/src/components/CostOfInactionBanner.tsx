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

/** True when a value is clearly a currency amount, not a percentage/ratio.
 * kpiUnit is now reliably populated (see KPIValue.unit fix) — trust it
 * directly rather than the old magnitude-based guess, which assumed an
 * empty/percent unit meant "actually dollars in disguise" and therefore
 * excluded a genuine '$' unit, producing "2614901.0$" instead of "$2.6M". */
function isCurrencyValue(value: number, unit: string): boolean {
  if (unit === '$') return true;
  if (unit === '%' || unit === 'pp') return false;
  // Genuinely unknown unit — fall back to the old magnitude heuristic.
  return Math.abs(value) >= 1_000 && unit === '';
}

function formatValue(value: number, unit: string): string {
  if (isCurrencyValue(value, unit)) return formatRevenue(value);
  return `${value.toFixed(1)}${unit}`;
}

function formatDelta(delta: number, unit: string): string {
  if (isCurrencyValue(delta, unit)) {
    return `${delta >= 0 ? '+' : ''}${formatRevenue(delta)}`;
  }
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

/**
 * Dark-first, like every other surface in this app.
 *
 * `deteriorating` and `recovering` were `bg-amber-50` and `bg-emerald-50` —
 * light panels on a slate-950 page. Rendered, that made this banner the
 * single brightest object in the Executive Briefing's first viewport, and it
 * is not the decision; the decision sat next to it in slate. `stable` was
 * already dark, so the component disagreed with itself depending on which way
 * the KPI happened to be moving.
 *
 * Every per-trend colour now lives here rather than in five ternaries spread
 * through the render, which is how the three states drifted apart in the first
 * place. `print:` variants restore light backgrounds for Print/Export — on
 * paper the original light treatment was right.
 */
const TREND_CONFIG: Record<
  TrendKey,
  {
    containerClass: string;
    headerClass: string;
    iconClass: string;
    /** Intro line above the projections. */
    introClass: string;
    /** Projection list body text. */
    bodyClass: string;
    /** The delta — the primary figure in each row. */
    deltaClass: string;
    /** Projected level + supporting context. */
    subtleClass: string;
    /** Footer divider + trend/confidence text. */
    footerClass: string;
    Icon: React.ElementType;
    label: string;
  }
> = {
  deteriorating: {
    containerClass: 'bg-amber-950/20 border border-amber-700/40 print:bg-amber-50 print:border-amber-300',
    headerClass: 'text-amber-100 print:text-amber-900',
    iconClass: 'text-amber-500 print:text-amber-600',
    introClass: 'text-amber-200/70 print:text-amber-800',
    bodyClass: 'text-amber-50 print:text-amber-900',
    deltaClass: 'text-amber-300 font-semibold print:text-amber-800',
    subtleClass: 'text-amber-300/70 print:text-amber-700',
    footerClass: 'border-amber-800/40 text-amber-300/80 print:border-amber-200 print:text-amber-700',
    Icon: AlertTriangle,
    label: 'Deteriorating',
  },
  stable: {
    containerClass: 'bg-slate-800 border border-slate-700 print:bg-slate-50 print:border-slate-300',
    headerClass: 'text-slate-200 print:text-slate-900',
    iconClass: 'text-slate-400 print:text-slate-600',
    introClass: 'text-slate-400 print:text-slate-700',
    bodyClass: 'text-slate-300 print:text-slate-900',
    deltaClass: 'text-slate-200 font-semibold print:text-slate-900',
    subtleClass: 'text-slate-400 print:text-slate-600',
    footerClass: 'border-slate-700 text-slate-400 print:border-slate-200 print:text-slate-600',
    Icon: Minus,
    label: 'Stable',
  },
  recovering: {
    containerClass: 'bg-emerald-950/20 border border-emerald-700/40 print:bg-emerald-50 print:border-emerald-300',
    headerClass: 'text-emerald-100 print:text-emerald-900',
    iconClass: 'text-emerald-400 print:text-emerald-600',
    introClass: 'text-emerald-200/70 print:text-emerald-800',
    bodyClass: 'text-emerald-50 print:text-emerald-900',
    deltaClass: 'text-emerald-300 font-semibold print:text-emerald-700',
    subtleClass: 'text-emerald-300/70 print:text-emerald-700',
    footerClass: 'border-emerald-800/40 text-emerald-300/80 print:border-emerald-200 print:text-emerald-700',
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

  // The DELTA is now the primary figure, the projected LEVEL the smaller
  // supporting context — reversed 2026-08-24. Found live: the level (e.g.
  // "$-74.0M", a projected EBITDA level) rendered semibold/normal-size while
  // the delta (e.g. "$-618K", the actual 30-day erosion) rendered at
  // text-xs in parentheses — an order of magnitude apart, with the smaller
  // number answering the section's own question ("what does waiting cost?")
  // and the larger, more prominent one answering a different question
  // nobody asked here.
  const cfg = TREND_CONFIG[trendDirection];
  const TrendIcon = isNegative ? TrendingDown : TrendingUp;

  return (
    <li className="flex items-start gap-2 text-sm">
      <TrendIcon
        className={`w-4 h-4 flex-shrink-0 mt-0.5 ${
          isNegative ? 'text-red-400 print:text-red-600' : 'text-emerald-400 print:text-emerald-600'
        }`}
      />
      <span>
        <span className="font-medium">In {horizon}:</span>{' '}
        <span className={`font-mono ${cfg.deltaClass}`}>
          {formatDelta(delta, kpiUnit)}
        </span>{' '}
        <span className={`font-mono text-xs ${cfg.subtleClass}`}>
          (projected: {formatValue(projectedValue, kpiUnit)})
        </span>
        {revenueImpact !== undefined && (
          <>
            {' — '}
            <span className="text-xs text-slate-400 print:text-slate-600">
              est. revenue impact:{' '}
              <span className={`font-semibold ${
                revenueImpact < 0
                  ? 'text-red-400 print:text-red-600'
                  : 'text-emerald-400 print:text-emerald-600'
              }`}>
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
  kpiUnit = '',
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
      <p className={`text-xs mb-3 ${cfg.introClass}`}>
        If no solution is implemented, {kpiName} is projected to:
      </p>

      {/* Projection rows */}
      <ul className={`space-y-2 mb-4 ${cfg.bodyClass}`}>
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
      <div className={`flex items-center gap-3 text-xs pt-3 border-t ${cfg.footerClass}`}>
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
