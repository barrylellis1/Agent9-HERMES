import { TrendingUp } from 'lucide-react';
import { OpportunitySignal } from '../api/types';

const OPPORTUNITY_TYPE_LABELS: Record<string, string> = {
  outperformance: 'Outperformance',
  recovery: 'Recovery',
  trend_reversal: 'Trend Reversal',
};

interface OpportunityCardProps {
  signal: OpportunitySignal;
  onClick?: () => void;
}

export function OpportunityCard({ signal, onClick }: OpportunityCardProps) {
  return (
    <div
      className="border-l-2 border-l-green-500 bg-slate-900 hover:bg-slate-800 rounded-xl p-4 cursor-pointer transition-colors"
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-green-400 flex-shrink-0" />
          <span className="text-xs font-semibold text-green-400 uppercase tracking-wider">
            {OPPORTUNITY_TYPE_LABELS[signal.opportunity_type] ?? signal.opportunity_type}
          </span>
        </div>
        <span className="text-green-300 font-bold text-sm">
          +{signal.delta_pct.toFixed(1)}%
        </span>
      </div>
      <p className="text-white font-medium text-sm leading-snug mb-2">{signal.headline}</p>
      {signal.dimension && signal.dimension_value && (
        <p className="text-xs text-slate-400 mb-2">
          {signal.dimension}: {signal.dimension_value}
        </p>
      )}
      <div className="flex items-center justify-between mt-1">
        <span className="text-xs text-slate-500">
          Confidence: {(signal.confidence * 100).toFixed(0)}%
        </span>
        <span className="text-xs text-slate-500 font-medium">{signal.kpi_display_name}</span>
      </div>
    </div>
  );
}
