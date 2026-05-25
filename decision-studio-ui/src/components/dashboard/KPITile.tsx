import React from 'react';
import { ArrowRight } from 'lucide-react';
import { Situation } from '../../api/types';

interface KPITileProps {
  situation: Situation;
  onClick: () => void;
  isDelegated?: boolean;
  hasActiveSolution?: boolean;
}

export const KPITile: React.FC<KPITileProps> = ({ situation, onClick, isDelegated = false, hasActiveSolution = false }) => {
  const isUp = situation.direction === 'up' || situation.card_type === 'opportunity';
  const isOpportunity = isUp;

  const severityBorder: Record<string, string> = {
    critical: 'border-l-severity-critical',
    high:     'border-l-severity-critical',
    medium:   'border-l-severity-warning',
    low:      'border-l-severity-healthy',
  };
  const severityDot: Record<string, string> = {
    critical: 'bg-severity-critical',
    high:     'bg-severity-critical',
    medium:   'bg-severity-warning',
    low:      'bg-severity-healthy',
  };

  const borderColor = isOpportunity ? 'border-l-severity-opportunity' : (severityBorder[situation.severity] ?? 'border-l-severity-warning');
  const dotColor    = isOpportunity ? 'bg-severity-opportunity'       : (severityDot[situation.severity]    ?? 'bg-severity-warning');

  const monthlyValues  = situation.kpi_value?.monthly_values ?? [];
  const comparisonType = situation.kpi_value?.comparison_type;
  const percentChange  = situation.kpi_value?.percent_change;
  const inverseLogic   = situation.kpi_value?.inverse_logic ?? false;

  // ── Trend direction — computed early so it drives label colour (#5) ──
  const isGoodTrend = isOpportunity
    ? true
    : inverseLogic
      ? (percentChange ?? 0) <= 0
      : (percentChange ?? 0) >= 0;

  // #4: Border-left is the primary severity signal — badge label is muted.
  // #5: For benign medium/low findings that are trending correctly, use healthy (green) not amber.
  const badgeLabelColor = (() => {
    if (isOpportunity) return 'text-severity-opportunity';
    if (isGoodTrend && (situation.severity === 'medium' || situation.severity === 'low')) {
      return 'text-severity-healthy';
    }
    return 'text-slate-500';
  })();

  // ── Formatted displays ──

  const deviationDisplay = (() => {
    if (percentChange == null || !isFinite(percentChange)) return null;
    const sign = percentChange >= 0 ? '+' : '';
    return `${sign}${percentChange.toFixed(1)}%`;
  })();

  const deviationColor = (() => {
    if (percentChange == null) return 'text-slate-400';
    if (isOpportunity) return 'text-severity-opportunity';
    if (inverseLogic) return percentChange > 0 ? 'text-severity-critical' : 'text-severity-opportunity';
    if (percentChange < 0) return 'text-severity-critical';
    // Positive % without inverse_logic: CRITICAL/HIGH problems should never show green.
    if (situation.severity === 'critical' || situation.severity === 'high') return 'text-severity-critical';
    return 'text-severity-opportunity';
  })();

  const absoluteDisplay = (() => {
    if (!situation.kpi_value) return null;
    const { value, currency, unit } = situation.kpi_value;
    if (value == null) return null;
    const prefix = currency || '';
    if (Math.abs(value) >= 1_000_000_000) return `${prefix}${(value / 1_000_000_000).toFixed(1)}B`;
    if (Math.abs(value) >= 1_000_000)     return `${prefix}${(value / 1_000_000).toFixed(1)}M`;
    if (Math.abs(value) >= 1_000)         return `${prefix}${(value / 1_000).toFixed(0)}K`;
    return `${prefix}${value.toLocaleString()}${unit && unit !== '$' ? ` ${unit}` : ''}`;
  })();

  // #7: Temporal grounding — enrich generic comparison type labels with year context
  const comparisonLabel = (() => {
    if (!comparisonType) return null;
    const year = new Date().getFullYear();
    const lower = comparisonType.toLowerCase();
    if (lower.includes('year') || lower === 'yoy')     return `YoY · ${year} vs ${year - 1}`;
    if (lower.includes('month') || lower === 'mom')    return 'Month over Month';
    if (lower.includes('quarter') || lower === 'qoq')  return 'Quarter over Quarter';
    return comparisonType.replace(/_/g, ' ');
  })();

  // ── Sparkline: taller with always-visible mean baseline ──

  const lineColor = isOpportunity ? '#34d399' : (isGoodTrend ? '#34d399' : '#f87171');

  const VB_W     = 200;
  const VB_H     = 80;
  const PLOT_TOP = 6;
  const PLOT_BOT = 72;
  const PLOT_H   = PLOT_BOT - PLOT_TOP;

  const sparkline = (() => {
    const vals = monthlyValues.length > 0
      ? monthlyValues.map(m => m.value)
      : (() => {
          if (percentChange == null) return null;
          const pct = Math.min(Math.abs(percentChange), 80) / 100;
          const base = 100;
          const pts: number[] = [];
          const trendUp = (percentChange ?? 0) >= 0;
          for (let i = 0; i < 9; i++) {
            const t = i / 8;
            const ease = t * t;
            const drift = trendUp ? base * (1 + ease * pct) : base * (1 - ease * pct);
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

    // Mean baseline — always visible, shows above/below-average months at a glance
    const meanV = vals.reduce((a, b) => a + b, 0) / vals.length;
    const baselineY = PLOT_BOT - ((meanV - minV) / range) * PLOT_H;

    const minPointY = Math.min(...points.map(p => p.y));
    const polyline = points.map(p => `${p.x},${p.y}`).join(' ');
    const areaPath =
      `M ${points[0].x},${points[0].y} ` +
      points.slice(1).map(p => `L ${p.x},${p.y}`).join(' ') +
      ` L ${VB_W},${VB_H} L 0,${VB_H} Z`;

    const gradId = `sf-${situation.situation_id}`;

    return (
      <svg width="100%" height="72" viewBox={`0 0 ${VB_W} ${VB_H}`} preserveAspectRatio="none">
        <defs>
          {/* gradientUnits=userSpaceOnUse anchors to sparkline peak → always visible fill */}
          <linearGradient id={gradId} x1="0" y1={minPointY} x2="0" y2={VB_H} gradientUnits="userSpaceOnUse">
            <stop offset="0%"   stopColor={lineColor} stopOpacity="0.35" />
            <stop offset="100%" stopColor={lineColor} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill={`url(#${gradId})`} />
        {/* Mean baseline — drawn after fill so it's always visible */}
        {baselineY > PLOT_TOP + 2 && baselineY < PLOT_BOT - 2 && (
          <line
            x1="0" y1={baselineY} x2={VB_W} y2={baselineY}
            stroke={lineColor} strokeWidth="0.75" strokeDasharray="4 4" opacity="0.45"
          />
        )}
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
      className={`group relative flex flex-col justify-between p-5 pb-0 rounded-xl border-l-[3px] ${borderColor} bg-slate-900/80 hover:bg-slate-800/90 transition-all duration-200 w-full text-left overflow-hidden`}
    >
      {/* ── Severity + KPI name (#13: tighter rhythm) ── */}
      <div className="mb-3">
        <div className="flex items-center gap-2 mb-1">
          <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
          <span className={`text-[11px] font-semibold uppercase tracking-wider ${badgeLabelColor}`}>
            {isOpportunity ? 'Opportunity' : situation.severity}
          </span>
          {isDelegated && (
            <span className="text-[11px] uppercase tracking-wider text-slate-500 ml-1">
              Delegated
            </span>
          )}
          {hasActiveSolution && (
            <span className="text-[11px] uppercase tracking-wider text-indigo-400 ml-1">
              Solution Active
            </span>
          )}
        </div>
        <h3 className="text-base font-semibold text-white leading-snug">
          {situation.kpi_name}
        </h3>
      </div>

      {/* ── Hero number + context (#13: tighter) ── */}
      <div className="mb-3">
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
          <span className="block text-[10px] text-slate-500 uppercase tracking-wider mt-1">
            {comparisonLabel}
          </span>
        )}
      </div>

      {/* ── Lead finding + sparkline (always together at bottom) ── */}
      <div className="mt-auto">
        {situation.trend_note ? (
          <p className="text-[11px] text-amber-400/80 leading-snug px-0 pb-2 line-clamp-2">
            {situation.trend_note}
          </p>
        ) : situation.key_observations && situation.key_observations.length > 0 ? (
          <p className="text-[11px] text-slate-400 leading-snug px-0 pb-2 line-clamp-2">
            {situation.key_observations[0]}
          </p>
        ) : null}
        {sparkline && (
          <div className="-mx-5">
            {sparkline}
          </div>
        )}
      </div>

      {/* ── Hover action overlay ── */}
      <div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none flex items-end justify-end p-4"
        style={{ background: 'linear-gradient(to top, rgba(15,23,42,0.85) 0%, transparent 60%)' }}
      >
        <span className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-widest text-indigo-400">
          Analyze <ArrowRight className="w-3 h-3" />
        </span>
      </div>
    </button>
  );
};
