import React from 'react';
import { ArrowUpRight, ArrowDownRight, TrendingUp } from 'lucide-react';
import { Situation } from '../../api/types';

interface KPITileProps {
  situation: Situation;
  onClick: () => void;
}

export const KPITile: React.FC<KPITileProps> = ({ situation, onClick }) => {
  const isOpportunity = situation.card_type === 'opportunity';

  // Color mapping
  const colors = {
    critical: { border: 'border-red-500', bg: 'bg-red-500/10', text: 'text-red-400', stroke: '#ef4444' },
    high: { border: 'border-orange-500', bg: 'bg-orange-500/10', text: 'text-orange-400', stroke: '#f97316' },
    medium: { border: 'border-amber-500', bg: 'bg-amber-500/10', text: 'text-amber-400', stroke: '#f59e0b' },
    low: { border: 'border-emerald-500', bg: 'bg-emerald-500/10', text: 'text-emerald-400', stroke: '#10b981' },
  };

  const opportunityColors = { border: 'border-green-500', bg: 'bg-green-500/10', text: 'text-green-400', stroke: '#22c55e' };
  const status = isOpportunity ? opportunityColors : (colors[situation.severity as keyof typeof colors] || colors.medium);
  const isNegative = !isOpportunity && (situation.severity === 'critical' || situation.severity === 'high');

  const width = 120;
  const height = 40;

  const monthlyValues = situation.kpi_value?.monthly_values;

  return (
    <button
      onClick={onClick}
      className={`relative flex flex-col items-start p-5 rounded-xl border ${status.border} ${status.bg} hover:bg-slate-800 transition-all duration-200 group w-full text-left h-full overflow-hidden`}
    >
      <div className="flex justify-between items-start w-full mb-4">
        <div>
          <span className={`text-[10px] font-bold uppercase tracking-wider ${status.text} border border-current px-1.5 py-0.5 rounded`}>
            {isOpportunity ? 'Growth Opportunity' : situation.severity}
          </span>
          <h3 className="text-lg font-bold text-white mt-2 leading-tight group-hover:text-blue-400 transition-colors">
            {situation.kpi_name}
          </h3>
        </div>
        <div className={`p-2 rounded-full bg-slate-900/50 ${status.text}`}>
          {isOpportunity ? <TrendingUp className="w-5 h-5" /> : isNegative ? <ArrowDownRight className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
        </div>
      </div>

      <div className="flex-1 w-full">
        <p className="text-xs text-slate-400 line-clamp-2 mb-4">
          {situation.description}
        </p>
      </div>

      <div className="w-full flex items-end justify-between mt-auto">
        <div className="flex flex-col">
            <span className="text-[10px] text-slate-500 uppercase">Current Value</span>
            <span className="text-xl font-mono text-white">
                {situation.kpi_value ?
                    `${situation.kpi_value.currency || ''}${situation.kpi_value.value.toLocaleString()}` :
                    '--'
                }
            </span>
        </div>

        {/* Monthly trend bars */}
        {monthlyValues && monthlyValues.length > 0 && (
          <div className="opacity-60 group-hover:opacity-100 transition-opacity">
            <svg width={width} height={height}>
              {(() => {
                const barWidth = Math.max(1, (width / monthlyValues.length) - 2);
                const gap = 2;
                const values = monthlyValues.map(m => m.value);
                const minVal = Math.min(...values);
                const maxVal = Math.max(...values);
                const range = maxVal - minVal || 1;

                return monthlyValues.map((m, i) => {
                  const barHeight = Math.max(2, ((m.value - minVal) / range) * (height - 4));
                  const isLatest = i === monthlyValues.length - 1;
                  return (
                    <rect
                      key={m.period}
                      x={i * (barWidth + gap)}
                      y={height - barHeight}
                      width={barWidth}
                      height={barHeight}
                      rx={2}
                      fill={isLatest ? status.stroke : '#334155'}
                      opacity={isLatest ? 1 : 0.7}
                    />
                  );
                });
              })()}
            </svg>
          </div>
        )}
      </div>
    </button>
  );
};
