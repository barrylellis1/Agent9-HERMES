import React from 'react';
import { ArrowRight } from 'lucide-react';
import { Situation } from '../../api/types';

interface HeroBriefingProps {
  situation: Situation;
  onClick: () => void;
  isDelegated?: boolean;
  hasActiveSolution?: boolean;
}

export const HeroBriefing: React.FC<HeroBriefingProps> = ({
  situation,
  onClick,
  isDelegated = false,
  hasActiveSolution = false,
}) => {
  const isOpportunity = situation.direction === 'up' || situation.card_type === 'opportunity';

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

  const percentChange  = situation.kpi_value?.percent_change;
  const inverseLogic   = situation.kpi_value?.inverse_logic ?? false;

  const isGoodTrend = isOpportunity
    ? true
    : inverseLogic
      ? (percentChange ?? 0) <= 0
      : (percentChange ?? 0) >= 0;

  const badgeLabelColor = (() => {
    if (isOpportunity) return 'text-severity-opportunity';
    if (isGoodTrend && (situation.severity === 'medium' || situation.severity === 'low')) {
      return 'text-severity-healthy';
    }
    return 'text-slate-500';
  })();

  const deviationDisplay = percentChange != null && isFinite(percentChange)
    ? `${percentChange >= 0 ? '+' : ''}${percentChange.toFixed(1)}%`
    : null;

  const deviationColor = (() => {
    if (percentChange == null) return 'text-slate-400';
    if (isOpportunity) return 'text-severity-opportunity';
    if (inverseLogic) return percentChange > 0 ? 'text-severity-critical' : 'text-severity-opportunity';
    if (percentChange < 0) return 'text-severity-critical';
    // Positive % for a non-inverse KPI: could be inverse_logic missing from registry.
    // A CRITICAL/HIGH problem should never render green — use severity color as safety net.
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

  const comparisonLabel = (() => {
    const comparisonType = situation.kpi_value?.comparison_type;
    if (!comparisonType) return null;
    const year = new Date().getFullYear();
    const lower = comparisonType.toLowerCase();
    if (lower.includes('year') || lower === 'yoy')    return `YoY · ${year} vs ${year - 1}`;
    if (lower.includes('month') || lower === 'mom')   return 'Month over Month';
    if (lower.includes('quarter') || lower === 'qoq') return 'Quarter over Quarter';
    return comparisonType.replace(/_/g, ' ');
  })();

  const whyItMatters = situation.business_impact || situation.description;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={e => e.key === 'Enter' && onClick()}
      className={`group relative rounded-xl border-l-[3px] ${borderColor} bg-slate-900/80 hover:bg-slate-800/90 transition-all duration-200 cursor-pointer overflow-hidden`}
    >
      <div className="p-6 flex flex-col md:flex-row gap-6 items-start">

        {/* Left — severity + KPI name + hero number */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
            <span className={`text-[11px] font-semibold uppercase tracking-wider ${badgeLabelColor}`}>
              {isOpportunity ? 'Opportunity' : situation.severity}
            </span>
            <span className="text-[11px] uppercase tracking-wider text-slate-500 border border-slate-700 rounded px-1.5 py-0.5">
              Lead finding
            </span>
            {isDelegated && (
              <span className="text-[11px] uppercase tracking-wider text-slate-500">Delegated</span>
            )}
            {hasActiveSolution && (
              <span className="text-[11px] uppercase tracking-wider text-indigo-400">Solution Active</span>
            )}
          </div>

          <h2 className="text-2xl font-semibold text-white leading-tight mb-4">
            {situation.kpi_name}
          </h2>

          <div className="flex items-baseline gap-3">
            {deviationDisplay && (
              <span className={`text-5xl font-mono font-bold tracking-tight leading-none ${deviationColor}`}>
                {deviationDisplay}
              </span>
            )}
            {absoluteDisplay && (
              <span className="text-sm text-slate-400 font-mono">{absoluteDisplay}</span>
            )}
          </div>

          {comparisonLabel && (
            <span className="block text-[11px] text-slate-500 uppercase tracking-wider mt-2">
              {comparisonLabel}
            </span>
          )}
        </div>

        {/* Right — why it matters */}
        {whyItMatters && (
          <div className="flex-1 min-w-0 bg-slate-950/50 rounded-lg p-4 border border-slate-800/60">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2">
              Why it matters
            </p>
            <p className="text-sm text-slate-300 leading-relaxed">{whyItMatters}</p>
            {situation.key_observations && situation.key_observations.length > 0 && (
              <ul className="mt-3 space-y-1">
                {situation.key_observations.slice(0, 2).map((obs, i) => (
                  <li key={i} className="text-[11px] text-slate-400 leading-snug before:content-['·'] before:mr-1.5 before:text-slate-600">
                    {obs}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {/* Hover action strip */}
      <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-150 border-t border-slate-800/60 px-6 py-3 flex items-center justify-between">
        <span className="text-[10px] text-slate-600 uppercase tracking-wider">
          Click to open deep analysis
        </span>
        <span className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-widest text-indigo-400">
          Analyze <ArrowRight className="w-3 h-3" />
        </span>
      </div>
    </div>
  );
};
