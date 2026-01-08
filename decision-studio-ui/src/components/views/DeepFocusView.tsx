import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  AlertTriangle, 
  CheckCircle2, 
  Microscope, 
  Lightbulb, 
  Loader2, 
  Users,
  X
} from 'lucide-react';
import { Situation, ProblemRefinementResult } from '../../api/types';
import { ProblemRefinementChat } from '../ProblemRefinementChat';
import { VarianceBarList, VarianceSummary } from '../visualizations/VarianceCharts';
import { DivergingBarChart } from '../visualizations/DivergingBarChart';
import { TradeOffAnalysis } from '../visualizations/TradeOffAnalysis';
import { CouncilDebate } from '../CouncilDebate';

interface DeepFocusViewProps {
  situation: Situation;
  onBack: () => void;
  // Analysis State
  analyzing: boolean;
  analysisResults: any;
  analysisError: string | null;
  onRunAnalysis: () => void;
  // Variance/Deep Analysis View
  daViewMode: 'list' | 'snowflake';
  setDaViewMode: (mode: 'list' | 'snowflake') => void;
  // Refinement Chat
  showRefinementChat: boolean;
  refinementResult: ProblemRefinementResult | null;
  onRefinementComplete: (result: ProblemRefinementResult) => void;
  onRefinementCancel: () => void;
  onStartRefinement: () => void;
  // Solutions / Debate
  findingSolutions: boolean;
  debatePhase: number;
  solutions: any;
  onStartDebate: () => void;
  // Council Config
  useHybridCouncil: boolean;
  setUseHybridCouncil: (val: boolean) => void;
  councilType: 'preset' | 'custom';
  setCouncilType: (val: 'preset' | 'custom') => void;
  selectedPreset: string;
  setSelectedPreset: (val: string) => void;
  selectedPersonas: string[];
  setSelectedPersonas: (val: string[]) => void;
  showPersonaSelector: boolean;
  setShowPersonaSelector: (val: boolean) => void;
  // Context
  availableCouncils: any[];
  availablePersonas: any[];
  principalContext: any;
  principalId: string;
}

export const DeepFocusView: React.FC<DeepFocusViewProps> = ({
  situation,
  onBack,
  analyzing,
  analysisResults,
  analysisError,
  onRunAnalysis,
  daViewMode,
  setDaViewMode,
  showRefinementChat,
  refinementResult,
  onRefinementComplete,
  onRefinementCancel,
  onStartRefinement,
  findingSolutions,
  debatePhase,
  solutions,
  onStartDebate,
  useHybridCouncil,
  setUseHybridCouncil,
  councilType,
  setCouncilType,
  selectedPreset,
  setSelectedPreset,
  selectedPersonas,
  setSelectedPersonas,
  showPersonaSelector,
  setShowPersonaSelector,
  availableCouncils,
  availablePersonas,
  principalContext,
  principalId
}) => {
  const navigate = useNavigate();
  const currentAnalysis = analysisResults;

  // Render Variance Analysis Section (Embedded)
  const renderVarianceAnalysis = () => {
    if (!currentAnalysis?.kt_is_is_not) return null;

    // Process data for charts
    const { where_is, where_is_not } = currentAnalysis.kt_is_is_not;
    // Simple transform for the chart component expectations
    const isItems = where_is?.map((i: any) => ({ ...i, delta: i.delta || 0 })) || [];
    const isNotItems = where_is_not?.map((i: any) => ({ ...i, delta: i.delta || 0 })) || [];
    
    // Calculate max delta
    let max = 1;
    [...isItems, ...isNotItems].forEach(item => {
        max = Math.max(max, Math.abs(item.delta || 0));
    });

    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 mb-6">
        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
           <Microscope className="w-4 h-4" />
           Variance Analysis (Is / Is Not)
        </h3>
        
        <div className="flex flex-col lg:flex-row gap-6">
             <VarianceBarList items={isItems} maxDelta={max} type="is" title="Problem Areas" />
             <VarianceSummary isItems={isItems} isNotItems={isNotItems} kpiName={situation.kpi_name} />
             <VarianceBarList items={isNotItems} maxDelta={max} type="isNot" title="Healthy Areas" />
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans flex flex-col">
      {/* Header */}
      <header className="px-8 py-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-4">
          <button 
            onClick={onBack}
            className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <div className="flex items-center gap-2 mb-1">
               <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-xs font-bold rounded uppercase">
                 {situation.severity}
               </span>
               <span className="text-slate-500 text-xs uppercase tracking-wider">
                 ID: {situation.situation_id?.substring(0, 8)}
               </span>
            </div>
            <h1 className="text-xl font-bold text-white">{situation.kpi_name} Variance</h1>
          </div>
        </div>
        
        {/* Actions or Context */}
        <div className="flex items-center gap-4">
            <div className="text-right">
                <div className="text-xs text-slate-500 uppercase">Detected</div>
                <div className="text-sm font-medium">{new Date().toLocaleTimeString()}</div>
            </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* LEFT COLUMN: Analysis & Data (Scrollable) */}
        <div className="flex-1 overflow-y-auto p-8 border-r border-slate-800 scrollbar-hide">
            <div className="max-w-4xl mx-auto space-y-8">
                
                {/* 1. Executive Briefing Card */}
                <section className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-lg">
                    <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-amber-500" />
                        Executive Briefing
                    </h2>
                    <p className="text-lg text-slate-200 mb-4 leading-relaxed">
                        {situation.description || "The system has detected a significant anomaly in this KPI."}
                    </p>
                    <div className="p-4 bg-slate-950/50 rounded-lg border border-slate-800/50">
                         <h4 className="text-xs font-bold text-slate-500 uppercase mb-2">Business Impact</h4>
                         <p className="text-sm text-slate-400">
                             {situation.business_impact || "Significant variance detected against operational thresholds. Immediate attention recommended."}
                         </p>
                    </div>
                </section>

                {/* 2. Deep Analysis Results (or Trigger) */}
                <section>
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                            <Microscope className="w-5 h-5 text-blue-400" />
                            Root Cause Analysis
                        </h2>
                        {!currentAnalysis && !analyzing && (
                             <button 
                                onClick={onRunAnalysis}
                                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg transition-colors flex items-center gap-2"
                             >
                                <Microscope className="w-4 h-4" />
                                Run Deep Analysis
                             </button>
                        )}
                    </div>

                    {analyzing && (
                        <div className="p-12 border border-blue-500/20 bg-blue-500/5 rounded-xl flex flex-col items-center justify-center animate-pulse">
                            <Loader2 className="w-8 h-8 text-blue-400 animate-spin mb-4" />
                            <span className="text-blue-300 font-medium">Analyzing Root Causes & Patterns...</span>
                        </div>
                    )}

                    {analysisError && (
                         <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg text-red-300">
                             {analysisError}
                         </div>
                    )}

                    {currentAnalysis && (
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
                            {/* SCQA Summary */}
                            {currentAnalysis.scqa_summary && (
                                <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                                     <div className="prose prose-invert prose-sm max-w-none">
                                        <div className="whitespace-pre-wrap font-sans text-slate-300">{currentAnalysis.scqa_summary}</div>
                                     </div>
                                </div>
                            )}

                            {/* Embedded Variance Analysis (Is/Is Not) */}
                            {renderVarianceAnalysis()}
                            
                            {/* Snowflake / Change Points */}
                            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                                 <div className="flex items-center justify-between mb-4">
                                     <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Dimension Breakdown</h3>
                                     <div className="flex bg-slate-950 rounded p-1 border border-slate-800">
                                        <button 
                                            onClick={() => setDaViewMode("list")}
                                            className={`px-3 py-1 text-xs rounded transition-all ${daViewMode === 'list' ? 'bg-slate-800 text-white' : 'text-slate-500 hover:text-slate-300'}`}
                                        >
                                            List
                                        </button>
                                        <button 
                                            onClick={() => setDaViewMode("snowflake")}
                                            className={`px-3 py-1 text-xs rounded transition-all ${daViewMode === 'snowflake' ? 'bg-slate-800 text-white' : 'text-slate-500 hover:text-slate-300'}`}
                                        >
                                            Is / Is Not
                                        </button>
                                     </div>
                                 </div>
                                 
                                 {daViewMode === 'snowflake' && currentAnalysis.kt_is_is_not ? (
                                     <DivergingBarChart 
                                        data={currentAnalysis.kt_is_is_not} 
                                        kpiName={situation.kpi_name} 
                                        width={600} 
                                     />
                                 ) : (
                                     <div className="space-y-2">
                                         {currentAnalysis.change_points?.map((cp: any, i: number) => (
                                             <div key={i} className="flex justify-between items-center bg-slate-950 p-3 rounded border border-slate-800">
                                                 <div className="flex flex-col">
                                                     <span className="text-[10px] text-slate-500 uppercase">{cp.dimension}</span>
                                                     <span className="text-sm font-medium text-white">{cp.key}</span>
                                                 </div>
                                                 <span className={`text-sm font-mono ${cp.delta < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                                                     {cp.delta > 0 ? '+' : ''}{cp.delta?.toLocaleString()}
                                                 </span>
                                             </div>
                                         ))}
                                     </div>
                                 )}
                            </div>
                        </div>
                    )}
                </section>

                {/* 3. Strategic Options (Trade-off Analysis) */}
                {solutions && console.log("[DeepFocusView] solutions:", solutions, "options_ranked:", solutions?.options_ranked)}
                {solutions && (
                    <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
                        {solutions.status === 'error' ? (
                            <div className="p-4 bg-red-900/20 border border-red-500/30 rounded-lg flex items-center gap-3">
                                <AlertTriangle className="w-5 h-5 text-red-400" />
                                <div>
                                    <h3 className="text-sm font-bold text-red-400">Solution Generation Failed</h3>
                                    <p className="text-xs text-red-300">{solutions.error_message || "An unknown error occurred."}</p>
                                </div>
                            </div>
                        ) : (
                            <TradeOffAnalysis 
                                options={solutions.options_ranked || []}
                                recommendedId={solutions.recommendation?.id}
                                onViewBriefing={() => navigate(`/briefing/${situation.situation_id}`)}
                            />
                        )}
                    </section>
                )}
            </div>
        </div>

        {/* RIGHT COLUMN: Action Center (Chat & Debate) */}
        <div className="w-[450px] bg-slate-900 border-l border-slate-800 flex flex-col">
             
             {/* Mode Switcher / Header */}
             <div className="p-4 border-b border-slate-800 bg-slate-900 z-10">
                 <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-1">
                     Action Center
                 </h2>
                 <p className="text-xs text-slate-500">Refine context and generate solutions</p>
             </div>

             <div className="flex-1 overflow-y-auto p-4 space-y-4">
                 {/* State A: Waiting for Analysis */}
                 {!currentAnalysis && (
                     <div className="flex flex-col items-center justify-center h-64 text-center p-6 opacity-50">
                         <Microscope className="w-12 h-12 text-slate-600 mb-4" />
                         <p className="text-slate-400 text-sm">Run Deep Analysis to unlock problem refinement and solutions.</p>
                     </div>
                 )}

                 {/* State B: Analysis Done, Start Refinement */}
                 {currentAnalysis && !showRefinementChat && !solutions && !findingSolutions && !showPersonaSelector && (
                     <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
                         <div className="bg-indigo-900/10 border border-indigo-500/20 rounded-xl p-6 text-center">
                             <Lightbulb className="w-10 h-10 text-indigo-400 mx-auto mb-3" />
                             <h3 className="text-white font-medium mb-2">Refine Problem Statement</h3>
                             <p className="text-sm text-slate-400 mb-4">
                                 Collaborate with the AI to validate hypotheses and set constraints before solving.
                             </p>
                             <button 
                                 onClick={onStartRefinement}
                                 className="w-full py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium transition-colors"
                             >
                                 Start Refinement Session
                             </button>
                         </div>
                     </div>
                 )}

                 {/* State C: Refinement Chat Active */}
                 {showRefinementChat && (
                     <div className="h-full flex flex-col animate-in fade-in">
                         <ProblemRefinementChat 
                             deepAnalysisOutput={{
                                 plan: currentAnalysis.plan || {},
                                 execution: currentAnalysis,
                                 situation_context: {
                                     kpi_name: situation.kpi_name,
                                     description: situation.description,
                                     severity: situation.severity,
                                     situation_id: situation.situation_id
                                 }
                             }}
                             principalContext={principalContext}
                             principalId={principalId}
                             onComplete={onRefinementComplete}
                             onCancel={onRefinementCancel}
                         />
                     </div>
                 )}

                 {/* State D: Persona Selector (Pre-Debate) */}
                 {showPersonaSelector && (
                     <div className="space-y-4 animate-in fade-in slide-in-from-right-4">
                         <div className="flex items-center justify-between mb-2">
                            <h3 className="font-semibold text-white">Assemble Council</h3>
                            <button onClick={() => setShowPersonaSelector(false)} className="text-slate-500 hover:text-white"><X className="w-4 h-4"/></button>
                         </div>

                         {/* Recommended Council */}
                         {refinementResult?.recommended_council_members && refinementResult.recommended_council_members.length > 0 && (
                            <div className="bg-purple-900/20 rounded-lg p-4 border border-purple-500/30">
                                <h4 className="text-xs font-bold text-purple-400 uppercase tracking-wider mb-2">AI Recommendation</h4>
                                <div className="space-y-3 mb-3">
                                    {refinementResult.recommended_council_members.map((m, i) => (
                                        <div key={i} className="text-xs text-slate-300">
                                            <div className="flex items-center gap-2 mb-1">
                                                <CheckCircle2 className="w-3 h-3 text-purple-500" />
                                                <span className="font-medium">{m.persona_name}</span>
                                            </div>
                                            {m.rationale && (
                                                <p className="pl-5 text-[11px] text-slate-500 leading-snug">
                                                    {m.rationale}
                                                </p>
                                            )}
                                        </div>
                                    ))}
                                </div>
                                <button
                                    onClick={onStartDebate}
                                    className="w-full py-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold uppercase rounded transition-colors"
                                >
                                    Convening Recommended Council
                                </button>
                            </div>
                         )}

                         {/* Manual Selection Fallback */}
                         <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
                             <div className="flex gap-2 mb-4">
                                 <button 
                                     onClick={() => setUseHybridCouncil(false)}
                                     className={`flex-1 py-1.5 text-xs rounded border ${!useHybridCouncil ? 'bg-slate-800 border-white/20 text-white' : 'border-transparent text-slate-500'}`}
                                 >
                                     Internal
                                 </button>
                                 <button 
                                     onClick={() => setUseHybridCouncil(true)}
                                     className={`flex-1 py-1.5 text-xs rounded border ${useHybridCouncil ? 'bg-indigo-600 border-indigo-500 text-white' : 'border-transparent text-slate-500'}`}
                                 >
                                     Hybrid Council
                                 </button>
                             </div>

                             {useHybridCouncil && (
                                 <div className="mb-4">
                                     <div className="flex gap-2 mb-3">
                                         <button 
                                             onClick={() => setCouncilType('preset')}
                                             className={`px-3 py-1 text-xs rounded border ${councilType === 'preset' ? 'bg-indigo-900/30 border-indigo-500 text-indigo-300' : 'bg-transparent border-slate-700 text-slate-500'}`}
                                         >
                                             Presets
                                         </button>
                                         <button 
                                             onClick={() => setCouncilType('custom')}
                                             className={`px-3 py-1 text-xs rounded border ${councilType === 'custom' ? 'bg-indigo-900/30 border-indigo-500 text-indigo-300' : 'bg-transparent border-slate-700 text-slate-500'}`}
                                         >
                                             Custom
                                         </button>
                                     </div>

                                     {councilType === 'preset' ? (
                                         <div className="space-y-2">
                                             {availableCouncils.map(c => (
                                                 <button
                                                     key={c.id}
                                                     onClick={() => setSelectedPreset(c.id)}
                                                     className={`w-full text-left p-3 rounded border transition-all ${selectedPreset === c.id ? 'bg-slate-800 border-indigo-500' : 'bg-slate-900/50 border-slate-800 hover:border-slate-700'}`}
                                                 >
                                                     <div className="flex items-center gap-2">
                                                         <Users className={`w-4 h-4 ${c.color}`} />
                                                         <span className={`text-sm font-medium ${selectedPreset === c.id ? 'text-white' : 'text-slate-300'}`}>{c.label}</span>
                                                     </div>
                                                 </button>
                                             ))}
                                         </div>
                                     ) : (
                                         <div className="space-y-2">
                                             <p className="text-xs text-slate-500 mb-2">Select 2-5 firms:</p>
                                             {availablePersonas.filter(p => p.type === 'firm').map(persona => {
                                                 const isSelected = selectedPersonas.includes(persona.id);
                                                 return (
                                                     <button 
                                                         key={persona.id}
                                                         onClick={() => {
                                                             if (isSelected) setSelectedPersonas(selectedPersonas.filter(id => id !== persona.id));
                                                             else {
                                                                 if (selectedPersonas.length < 5) setSelectedPersonas([...selectedPersonas, persona.id]);
                                                             }
                                                         }}
                                                         className={`w-full flex items-center gap-3 p-2 rounded border transition-all ${isSelected ? 'bg-slate-800 border-indigo-500/50' : 'bg-slate-900/50 border-slate-800 opacity-80 hover:opacity-100'}`}
                                                     >
                                                         <div className={`w-6 h-6 rounded bg-slate-900 flex items-center justify-center border ${isSelected ? 'border-indigo-500/30' : 'border-slate-700'}`}>
                                                             <span className={`text-xs font-bold ${persona.color}`}>{persona.label[0]}</span>
                                                         </div>
                                                         <span className={`text-sm ${isSelected ? 'text-white font-medium' : 'text-slate-500'}`}>{persona.label}</span>
                                                         {isSelected && <CheckCircle2 className="w-4 h-4 text-indigo-500 ml-auto" />}
                                                     </button>
                                                 );
                                             })}
                                         </div>
                                     )}
                                 </div>
                             )}

                             <button 
                                 onClick={onStartDebate}
                                 className="w-full mt-2 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-medium flex items-center justify-center gap-2"
                             >
                                 <Users className="w-4 h-4" />
                                 Start Debate
                             </button>
                         </div>
                     </div>
                 )}

                 {/* State E: Debate In Progress */}
                 {findingSolutions && (
                     <div className="animate-in fade-in">
                         <CouncilDebate 
                             phase={debatePhase} 
                             activePersonas={(() => {
                                 if (selectedPersonas.length > 0) {
                                     return selectedPersonas;
                                 }
                                 const recommended = refinementResult?.recommended_council_members?.map(m => m.persona_id) ?? [];
                                 if (recommended.length > 0) {
                                     return recommended;
                                 }
                                 return availablePersonas.map(p => p.id).slice(0, 3);
                             })()}
                             availablePersonas={availablePersonas}
                         />
                     </div>
                 )}

                 {/* State F: Solutions (Results) */}
                 {solutions && !findingSolutions && (
                     <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
                         <div className="bg-emerald-900/10 border border-emerald-500/20 rounded-xl p-4">
                             <div className="flex items-center gap-2 mb-2">
                                 <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                                 <h3 className="font-semibold text-white">Consensus Reached</h3>
                             </div>
                             <p className="text-sm text-slate-400">
                                 The council has generated {solutions.options_ranked?.length || 0} viable options.
                             </p>
                         </div>

                         {solutions.recommendation && (
                             <div className="bg-slate-800 rounded-lg p-4 border border-slate-700">
                                 <div className="text-xs text-slate-500 uppercase mb-1">Top Recommendation</div>
                                 <div className="text-white font-medium mb-2">{solutions.recommendation.title}</div>
                                 <p className="text-xs text-slate-400 line-clamp-3">{solutions.recommendation_rationale}</p>
                             </div>
                         )}
                         
                         <a 
                             href={`/briefing/${situation.situation_id}`}
                             className="block w-full py-3 bg-blue-600 hover:bg-blue-500 text-white text-center rounded-lg font-bold transition-colors"
                         >
                             View Full Decision Briefing
                         </a>
                     </div>
                 )}

             </div>
        </div>
      </div>
    </div>
  );
};
