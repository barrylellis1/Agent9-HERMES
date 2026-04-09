import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Situation } from '../../api/types';

interface KPITileProps {
  situation: Situation;
  onClick: () => void;
  isDelegated?: boolean;
}

export const KPITile: React.FC<KPITileProps> = ({ situation, onClick, isDelegated = false }) => {
  const isOpportunity = situation.card_type === 'opportunity';

  const severityBorderColor: Record<string, string> = {
    critical: 'border-l-red-500',
    high:     'border-l-red-500',
    medium:   'border-l-amber-500',
    low:      'border-l-green-500',
  };

  const severityTextColor: Record<string, string> = {
    critical: 'text-red-400',
    high:     'text-red-400',
    medium:   'text-amber-400',
    low:      'text-green-400',
  };

  const borderColor = isOpportunity ? 'border-l-green-500' : (severityBorderColor[situation.severity] ?? 'border-l-amber-500');
  const textColor   = isOpportunity ? 'text-green-400'     : (severityTextColor[situation.severity]   ?? 'text-amber-400');

  const monthlyValues   = situation.kpi_value?.monthly_values ?? [];
  const comparisonType  = situation.kpi_value?.comparison_type;
  const percentChange   = situation.kpi_value?.percent_change;
  const inverseLogic    = situation.kpi_value?.inverse_logic ?? false;
  const hasComparisonValues = monthlyValues.some(m => m.comparison_value !== undefined);

  // Format percent deviation — hero number
  // For inverse_logic KPIs (costs), percent_change is already normalised by the backend
  // so that positive = costs went up (bad). We show the sign as-is.
  const deviationDisplay = (() => {
    if (percentChange == null) return null;
    const sign = percentChange >= 0 ? '+' : '';
    return `${sign}${percentChange.toFixed(1)}%`;
  })();

  const deviationColor = (() => {
    if (percentChange == null) return 'text-slate-400';
    if (isOpportunity) return percentChange >= 0 ? 'text-green-400' : 'text-slate-400';
    // For cost/expense KPIs: positive change (higher cost) = bad = red
    if (inverseLogic) return percentChange > 0 ? 'text-red-400' : 'text-green-400';
    return percentChange >= 0 ? 'text-green-400' : 'text-red-400';
  })();

  // Format absolute value — supporting number
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

  // Top drivers subtitle
  const topDriversText = (() => {
    const drivers = situation.top_drivers;
    if (!drivers || drivers.length === 0) return null;
    return drivers.slice(0, 2).map(d => {
      const sign = d.delta >= 0 ? '+' : '−';
      const abs  = Math.abs(d.delta);
      const formatted = d.currency
        ? `${d.currency}${abs >= 1_000_000 ? `${(abs / 1_000_000).toFixed(1)}M` : abs >= 1_000 ? `${(abs / 1_000).toFixed(0)}K` : abs.toFixed(0)}`
        : abs.toFixed(1);
      return `${d.label} ${sign}${formatted}`;
    }).join(' · ');
  })();

  // Chart dimensions
  const chartW = 96;
  const chartH = 36;

  return (
    <button
      onClick={onClick}
      className={`relative flex flex-col items-start p-4 rounded-xl border-l-2 ${borderColor} bg-slate-900 hover:bg-slate-800 transition-all duration-200 group w-full text-left h-full overflow-hidden`}
    >
      {/* ── Row 1: severity + KPI name ── */}
      <div className="w-full mb-3">
        <div className="flex items-center gap-3 mb-1">
          <span className={`text-[10px] font-mono uppercase tracking-widest ${textColor}`}>
            {isOpportunity ? 'Growth' : situation.severity}
          </span>
          {isDelegated && (
            <span className="text-[10px] font-mono uppercase tracking-widest text-slate-500">
              Delegated
            </span>
          )}
        </div>
        <h3 className="text-sm font-semibold text-white leading-tight">
          {situation.kpi_name}
        </h3>
      </div>

      {/* ── Row 2: deviation (hero) + direction icon ── */}
      <div className="w-full flex items-end justify-between mb-1">
        <div>
          {deviationDisplay ? (
            <>
              <span className={`text-2xl font-mono font-bold leading-none ${deviationColor}`}>
                {deviationDisplay}
              </span>
              {comparisonType && (
                <span className="block text-[9px] text-slate-500 font-mono uppercase tracking-wider mt-0.5">
                  {comparisonType.replace(/_/g, ' ')}
                </span>
              )}
            </>
          ) : (
            <span className="text-xs text-slate-500 italic">No comparison</span>
          )}
        </div>
        <div className={`${deviationColor} opacity-70`}>
          {isOpportunity
            ? <TrendingUp className="w-4 h-4" />
            : percentChange == null
            ? <Minus className="w-4 h-4 text-slate-500" />
            : percentChange < 0
            ? <TrendingDown className="w-4 h-4" />
            : <TrendingUp className="w-4 h-4" />
          }
        </div>
      </div>

      {/* ── Row 3: absolute value (supporting) ── */}
      {absoluteDisplay && (
        <div className="w-full mb-2">
          <span className="text-[10px] text-slate-500 font-mono">{absoluteDisplay}</span>
        </div>
      )}

      {/* ── Row 4: top drivers ── */}
      {topDriversText && (
        <div className="w-full mb-2">
          <p className="text-[10px] text-slate-500 truncate">{topDriversText}</p>
        </div>
      )}

      {/* ── Row 5: bar chart (activates when monthly_values present) ── */}
      {monthlyValues.length > 0 && (
        <div className="w-full mt-auto pt-2 opacity-70 group-hover:opacity-100 transition-opacity">
          <svg width={chartW} height={chartH}>
            {hasComparisonValues ? (
              (() => {
                const barWidth = Math.max(1, (chartW / monthlyValues.length) - 2);
                const gap = 2;
                const deltas = monthlyValues.map(m => (m.value ?? 0) - (m.comparison_value ?? m.value ?? 0));
                const maxAbs = Math.max(...deltas.map(d => Math.abs(d)), 1);
                const midY = chartH / 2;
                return monthlyValues.map((m, i) => {
                  const delta = (m.value ?? 0) - (m.comparison_value ?? m.value ?? 0);
                  const barH = Math.max(2, (Math.abs(delta) / maxAbs) * (midY - 2));
                  const isPos = delta >= 0;
                  return (
                    <rect key={m.period}
                      x={i * (barWidth + gap)} y={isPos ? midY - barH : midY}
                      width={barWidth} height={barH} rx={1}
                      fill={isPos ? '#22c55e' : '#ef4444'} opacity={0.85}
                    />
                  );
                });
              })()
            ) : (
              (() => {
                const barWidth = Math.max(1, (chartW / monthlyValues.length) - 2);
                const gap = 2;
                const values = monthlyValues.map(m => m.value);
                const minVal = Math.min(...values);
                const range  = (Math.max(...values) - minVal) || 1;
                return monthlyValues.map((m, i) => {
                  const barH = Math.max(2, ((m.value - minVal) / range) * (chartH - 4));
                  const isLatest = i === monthlyValues.length - 1;
                  return (
                    <rect key={m.period}
                      x={i * (barWidth + gap)} y={chartH - barH}
                      width={barWidth} height={barH} rx={1}
                      fill={isLatest ? '#94a3b8' : '#334155'}
                      opacity={isLatest ? 1 : 0.6}
                    />
                  );
                });
              })()
            )}
          </svg>
        </div>
      )}
    </button>
  );
};
