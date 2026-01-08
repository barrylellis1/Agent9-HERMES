import React from 'react';
import { CheckCircle2, Clock, TrendingUp, ArrowRight } from 'lucide-react';
import { SolutionOption } from '../../api/types';

interface TradeOffAnalysisProps {
  options: SolutionOption[];
  recommendedId?: string;
  onViewBriefing: () => void;
}

export const TradeOffAnalysis: React.FC<TradeOffAnalysisProps> = ({
  options,
  recommendedId,
  onViewBriefing
}) => {
  // Helper to format 0-1 scores
  const getRiskLabel = (score: number) => {
    if (score >= 0.7) return { label: 'High', color: 'text-red-400 bg-red-900/20 border-red-500/30' };
    if (score >= 0.4) return { label: 'Medium', color: 'text-amber-400 bg-amber-900/20 border-amber-500/30' };
    return { label: 'Low', color: 'text-emerald-400 bg-emerald-900/20 border-emerald-500/30' };
  };

  const getImpactLabel = (score: number) => {
    if (score >= 0.7) return { label: 'High', color: 'text-emerald-400' };
    if (score >= 0.4) return { label: 'Medium', color: 'text-blue-400' };
    return { label: 'Low', color: 'text-slate-400' };
  };

  const getCostLabel = (score: number) => {
    if (score >= 0.7) return { label: '$$$', color: 'text-slate-400' }; // High cost
    if (score >= 0.4) return { label: '$$', color: 'text-slate-400' };
    return { label: '$', color: 'text-emerald-400' }; // Low cost
  };

  if (!options || options.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/50 rounded-xl border border-slate-800 border-dashed">
        <div className="text-slate-500 mb-2">No strategic options generated</div>
        <p className="text-xs text-slate-600">The analysis did not yield viable trade-off options.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-indigo-400" />
                Strategic Trade-off Analysis
            </h3>
            <p className="text-sm text-slate-400">Comparing viable options against key decision criteria</p>
        </div>
        <button 
            onClick={onViewBriefing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors"
        >
            View Full Briefing <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {options.slice(0, 3).map((opt) => {
          const isRecommended = opt.id === recommendedId;
          const risk = getRiskLabel(opt.risk);
          const impact = getImpactLabel(opt.impact || opt.expected_impact || 0);
          const cost = getCostLabel(opt.cost);

          return (
            <div 
                key={opt.id}
                className={`relative flex flex-col rounded-xl border p-5 transition-all ${
                    isRecommended 
                        ? 'bg-indigo-900/20 border-indigo-500 ring-1 ring-indigo-500/50 shadow-lg shadow-indigo-900/20' 
                        : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                }`}
            >
                {isRecommended && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-indigo-600 text-white text-xs font-bold uppercase tracking-wider rounded-full flex items-center gap-1 shadow-lg">
                        <CheckCircle2 className="w-3 h-3" />
                        Recommended
                    </div>
                )}

                {/* Title & Desc */}
                <div className="mb-4 mt-2">
                    <h4 className={`font-bold text-lg mb-2 ${isRecommended ? 'text-white' : 'text-slate-200'}`}>
                        {opt.title}
                    </h4>
                    <p className="text-xs text-slate-400 line-clamp-3 min-h-[3rem]">
                        {opt.description}
                    </p>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 gap-3 mb-4 bg-slate-950/50 rounded-lg p-3">
                    <div>
                        <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Impact</div>
                        <div className={`text-sm font-bold ${impact.color}`}>{impact.label}</div>
                    </div>
                    <div>
                        <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Cost</div>
                        <div className={`text-sm font-bold ${cost.color}`}>{cost.label}</div>
                    </div>
                    <div>
                        <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Time</div>
                        <div className="text-sm font-medium text-slate-300 flex items-center gap-1">
                            <Clock className="w-3 h-3 text-slate-500" />
                            {opt.time_to_value}
                        </div>
                    </div>
                    <div>
                        <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1">Reversibility</div>
                        <div className="text-sm font-medium text-slate-300 capitalize">{opt.reversibility}</div>
                    </div>
                </div>

                {/* Risk Profile */}
                <div className="mb-4">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] text-slate-500 uppercase">Risk Profile</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded border ${risk.color} font-medium`}>
                            {risk.label}
                        </span>
                    </div>
                    {/* Mock simple bar for visual flair */}
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                        <div 
                            className={`h-full rounded-full ${opt.risk >= 0.7 ? 'bg-red-500' : opt.risk >= 0.4 ? 'bg-amber-500' : 'bg-emerald-500'}`} 
                            style={{ width: `${opt.risk * 100}%` }}
                        />
                    </div>
                </div>

                {/* Council Perspectives (Compact) */}
                <div className="mt-auto pt-4 border-t border-slate-800/50">
                    <div className="space-y-2">
                        {opt.perspectives.slice(0, 2).map((p, i) => ( // Show top 2 perspectives
                            <div key={i} className="flex gap-2">
                                <div className="min-w-[4px] w-[4px] rounded-full bg-slate-700" />
                                <div>
                                    <div className="text-[10px] font-bold text-slate-400">{p.lens}</div>
                                    <div className="text-[11px] text-slate-300 leading-tight">
                                        {p.arguments_for[0] || p.arguments_against[0]}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

            </div>
          );
        })}
      </div>
    </div>
  );
};
