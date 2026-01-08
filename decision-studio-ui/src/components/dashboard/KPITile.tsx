import React, { useMemo } from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { LinePath } from '@visx/shape';
import { scaleLinear } from '@visx/scale';
import { curveMonotoneX } from '@visx/curve';
import { Situation } from '../../api/types';

interface KPITileProps {
  situation: Situation;
  onClick: () => void;
}

export const KPITile: React.FC<KPITileProps> = ({ situation, onClick }) => {
  // Mock sparkline data - in a real app this would come from the API
  const sparkData = useMemo(() => {
    return Array.from({ length: 20 }).map((_, i) => ({
      x: i,
      y: Math.random() * 20 + (situation.severity === 'critical' ? -i : i * 0.5) // Trend down for critical
    }));
  }, [situation.severity]);

  // Color mapping
  const colors = {
    critical: { border: 'border-red-500', bg: 'bg-red-500/10', text: 'text-red-400', stroke: '#ef4444' },
    high: { border: 'border-orange-500', bg: 'bg-orange-500/10', text: 'text-orange-400', stroke: '#f97316' },
    medium: { border: 'border-amber-500', bg: 'bg-amber-500/10', text: 'text-amber-400', stroke: '#f59e0b' },
    low: { border: 'border-emerald-500', bg: 'bg-emerald-500/10', text: 'text-emerald-400', stroke: '#10b981' },
  };

  const status = colors[situation.severity as keyof typeof colors] || colors.medium;
  const isNegative = situation.severity === 'critical' || situation.severity === 'high';

  // Scales for sparkline
  const width = 120;
  const height = 40;
  const xScale = scaleLinear({
    domain: [0, sparkData.length - 1],
    range: [0, width],
  });
  const yScale = scaleLinear({
    domain: [Math.min(...sparkData.map(d => d.y)), Math.max(...sparkData.map(d => d.y))],
    range: [height, 0],
  });

  return (
    <button
      onClick={onClick}
      className={`relative flex flex-col items-start p-5 rounded-xl border ${status.border} ${status.bg} hover:bg-slate-800 transition-all duration-200 group w-full text-left h-full overflow-hidden`}
    >
      <div className="flex justify-between items-start w-full mb-4">
        <div>
          <span className={`text-[10px] font-bold uppercase tracking-wider ${status.text} border border-current px-1.5 py-0.5 rounded`}>
            {situation.severity}
          </span>
          <h3 className="text-lg font-bold text-white mt-2 leading-tight group-hover:text-blue-400 transition-colors">
            {situation.kpi_name}
          </h3>
        </div>
        <div className={`p-2 rounded-full bg-slate-900/50 ${status.text}`}>
          {isNegative ? <ArrowDownRight className="w-5 h-5" /> : <ArrowUpRight className="w-5 h-5" />}
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
        
        {/* Sparkline */}
        <div className="opacity-60 group-hover:opacity-100 transition-opacity">
            <svg width={width} height={height}>
                <LinePath
                    data={sparkData}
                    x={d => xScale(d.x) ?? 0}
                    y={d => yScale(d.y) ?? 0}
                    stroke={status.stroke}
                    strokeWidth={2}
                    curve={curveMonotoneX}
                />
            </svg>
        </div>
      </div>
    </button>
  );
};
