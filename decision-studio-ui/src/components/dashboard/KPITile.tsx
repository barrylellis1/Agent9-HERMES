import React from 'react';
import { Situation } from '../../api/types';

interface KPITileProps {
  situation: Situation;
  onClick: () => void;
  isDelegated?: boolean;
}

export const KPITile: React.FC<KPITileProps> = ({ situation, onClick, isDelegated = false }) => {
  const isOpportunity = situation.card_type === 'opportunity';

  const severityBorder: Record<string, string> = {
    critical: 'border-l-red-500',
    high:     'border-l-red-500',
    medium:   'border-l-amber-500',
    low:      'border-l-green-500',
  };
  const severityDot: Record<string, string> = {
    critical: 'bg-red-400',
    high:     'bg-red-400',
    medium:   'bg-amber-400',
    low:      'bg-green-400',
  };
  const severityText: Record<string, string> = {
    critical: 'text-red-400',
    high:     'text-red-400',
    medium:   'text-amber-400',
    low:      'text-green-400',
  };

  const borderColor = isOpportunity ? 'border-l-emerald-500' : (severityBorder[situation.severity] ?? 'border-l-amber-500');
  const dotColor    = isOpportunity ? 'bg-emerald-400'       : (severityDot[situation.severity]    ?? 'bg-amber-400');
  const labelColor  = isOpportunity ? 'text-emerald-400'     : (severityText[situation.severity]   ?? 'text-amber-400');

  const monthlyValues  = situation.kpi_value?.monthly_values ?? [];
  const comparisonType = situation.kpi_value?.comparison_type;
  const percentChange  = situation.kpi_value?.percent_change;
  const inverseLogic   = situation.kpi_value?.inverse_logic ?? false;

  // ── Formatted displays ──

  const deviationDisplay = (() => {
    if (percentChange == null) return null;
    const sign = percentChange >= 0 ? '+' : '';
    return `${sign}${percentChange.toFixed(1)}%`;
  })();

  const deviationColor = (() => {
    if (percentChange == null) return 'text-slate-400';
    if (isOpportunity) return percentChange >= 0 ? 'text-emerald-400' : 'text-slate-400';
    if (inverseLogic) return percentChange > 0 ? 'text-red-400' : 'text-emerald-400';
    return percentChange >= 0 ? 'text-emerald-400' : 'text-red-400';
  })();

  const absoluteDisplay = (() => {
    if (!situation.kpi_value) return null;
    const { value, currency, unit } = situation.kpi_value;
    const prefix = currency || '';
    if (Math.abs(value) >= 1_000_000_000)
      return `${prefix}${(value / 1_000_000_000).toFixed(1)}B`;
    if (Math.abs(value) >= 1_000_000)
      return `${prefix}${(value / 1_000_000).toFixed(1)}M`;
    if (Math.abs(value) >= 1_000)
      return `${prefix}${(value / 1_000).toFixed(0)}K`;
    return `${prefix}${value.toLocaleString()}${unit && unit !== '$' ? ` ${unit}` : ''}`;
  })();

  const comparisonLabel = comparisonType
    ? comparisonType.replace(/_/g, ' ')
    : null;

  // ── Sparkline colour ──

  const isGoodTrend = isOpportunity
    ? true
    : inverseLogic
      ? (percentChange ?? 0) <= 0
      : (percentChange ?? 0) >= 0;
  const lineColor = isOpportunity ? '#10b981' : (isGoodTrend ? '#10b981' : '#ef4444');

  // ── Sparkline SVG ──

  const VB_W = 200;
  const VB_H = 40;
  const PLOT_TOP = 4;
  const PLOT_BOT = 32;
  const PLOT_H = PLOT_BOT - PLOT_TOP;

  const sparkline = (() => {
    const vals = monthlyValues.length > 0
      ? monthlyValues.map(m => m.value)
      : (() => {
          if (percentChange == null) return null;
          // Synthetic trajectory — 9 points showing the drift
          const pct = Math.min(Math.abs(percentChange), 80) / 100;
          const base = 100;
          const pts: number[] = [];
          // Direction follows the raw value movement (positive % = line up, negative = line down).
          // Color already communicates good/bad; direction matches what real monthly data would show.
          const trendUp = (percentChange ?? 0) >= 0;
          for (let i = 0; i < 9; i++) {
            const t = i / 8;
            // Ease-in curve: most of the movement happens in later periods
            const ease = t * t;
            const drift = trendUp
              ? base * (1 + ease * pct)       // value increasing
              : base * (1 - ease * pct);      // value decreasing
            pts.push(drift);
          }
          return pts;
        })();

    if (!vals || vals.length < 2) return null;

    const minV = Math.min(...vals);
    const maxV = Math.max(...vals);
    const range = (maxV - minV) || 1;

    const n = vals.length;
    const points = vals.map((v, i) => ({
      x: (i / (n - 1)) * VB_W,
      y: PLOT_BOT - ((v - minV) / range) * PLOT_H,
    }));

    const polyline = points.map(p => `${p.x},${p.y}`).join(' ');

    // Area fill under the line
    const areaPath =
      `M ${points[0].x},${points[0].y} ` +
      points.slice(1).map(p => `L ${p.x},${p.y}`).join(' ') +
      ` L ${VB_W},${VB_H} L 0,${VB_H} Z`;

    const gradId = `sf-${situation.situation_id}`;

    return (
      <svg
        width="100%"
        height="36"
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor={lineColor} stopOpacity="0.28" />
            <stop offset="100%" stopColor={lineColor} stopOpacity="0.03" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill={`url(#${gradId})`} />
        <polyline
          points={polyline}
          fill="none"
          stroke={lineColor}
          strokeWidth="1.5"
          strokeLinejoin="round"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
          opacity="0.85"
        />
      </svg>
    );
  })();

  return (
    <button
      onClick={onClick}
      className={`relative flex flex-col justify-between p-5 pb-0 rounded-xl border-l-[3px] ${borderColor} bg-slate-900/80 hover:bg-slate-800/90 transition-all duration-200 w-full text-left overflow-hidden`}
    >
      {/* ── Severity + KPI name ── */}
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
          <span className={`text-[11px] font-semibold uppercase tracking-wider ${labelColor}`}>
            {isOpportunity ? 'Opportunity' : situation.severity}
          </span>
          {isDelegated && (
            <span className="text-[11px] uppercase tracking-wider text-slate-500 ml-1">
              Delegated
            </span>
          )}
        </div>
        <h3 className="text-base font-semibold text-white leading-snug">
          {situation.kpi_name}
        </h3>
      </div>

      {/* ── Hero number + context ── */}
      <div className="mb-4">
        {deviationDisplay ? (
          <div className="flex items-baseline gap-3">
            <span className={`text-3xl font-mono font-bold tracking-tight leading-none ${deviationColor}`}>
              {deviationDisplay}
            </span>
            {absoluteDisplay && (
              <span className="text-xs text-slate-500 font-mono">
                {absoluteDisplay}
              </span>
            )}
          </div>
        ) : (
          <span className="text-sm text-slate-500 italic">No comparison data</span>
        )}
        {comparisonLabel && (
          <span className="block text-[11px] text-slate-500 uppercase tracking-wider mt-1">
            {comparisonLabel}
          </span>
        )}
      </div>

      {/* ── Sparkline (edge-to-edge at bottom) ── */}
      {sparkline && (
        <div className="-mx-5 mt-auto">
          {sparkline}
        </div>
      )}
    </button>
  );
};
