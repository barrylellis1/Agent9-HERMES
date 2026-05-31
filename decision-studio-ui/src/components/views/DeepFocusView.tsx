import React, { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Microscope,
  Lightbulb,
  Loader2,
  Users,
  X,
  Sparkles,
  CircleDot,
  TrendingUp,
  SplitSquareHorizontal,
  ExternalLink
} from 'lucide-react';
import { Situation, ProblemRefinementResult, MarketSignal, MarketConflict } from '../../api/types';
import { formatExecutive } from '../../utils/formatExecutive';
import { ProblemRefinementChat } from '../ProblemRefinementChat';
import { IsIsNotExhibit } from '../visualizations/DivergingBarChart';
import { BrandLogo } from '../BrandLogo';

// ─── SCQA parser — extracts Answer/Situation/Complication/Question from flat text ───
function parseScqa(raw: string): Record<string, string> {
  const labels = ['Situation', 'Complication', 'Question', 'Answer'];
  const result: Record<string, string> = {};
  for (let i = 0; i < labels.length; i++) {
    const label = labels[i];
    const marker = `${label}:`;
    const start = raw.indexOf(marker);
    if (start === -1) continue;
    const contentStart = start + marker.length;
    const nextIdx = labels.slice(i + 1).reduce((min, next) => {
      const idx = raw.indexOf(`${next}:`, contentStart);
      return idx !== -1 && idx < min ? idx : min;
    }, raw.length);
    result[label.toLowerCase()] = raw.slice(contentStart, nextIdx).trim();
  }
  return result;
}

// ─── Market signal source formatter — rec #4 ───
function formatSignalSource(source: string, url?: string): React.ReactNode {
  const lower = source?.toLowerCase() ?? '';
  if (!source || lower === 'llm_knowledge' || lower.includes('llm') || lower.includes('claude')) {
    return <span>Analyst synthesis (Claude Sonnet 4.6) · No live citation</span>;
  }
  if (url) {
    return (
      <a href={url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 hover:underline">
        {source} <ExternalLink className="w-2.5 h-2.5" />
      </a>
    );
  }
  return <span>{source}</span>;
}

// ─── Solution Proposal Panel moved to Executive Briefing page ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

// ─── ScqaBlock — answer-first SCQA display ─────────────────────────────────────
function ScqaBlock({ scqa, raw, hasStructure }: { scqa: Record<string, string>; raw: string; hasStructure: boolean }) {
  const [showReasoning, setShowReasoning] = useState(false);

  if (!hasStructure) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <div className="whitespace-pre-wrap font-sans text-slate-300 text-sm leading-relaxed">{raw}</div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Answer — BLUF, shown first */}
      {scqa.answer && (
        <div className="bg-slate-900/80 border border-indigo-500/20 rounded-xl p-6">
          <p className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider mb-2">Recommendation</p>
          <p className="text-lg font-medium text-white leading-relaxed">{scqa.answer}</p>
        </div>
      )}

      {/* S / C / Q — collapsed by default */}
      <button
        onClick={() => setShowReasoning(v => !v)}
        className="flex items-center gap-2 text-[11px] text-slate-500 hover:text-slate-300 transition-colors"
      >
        <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-150 ${showReasoning ? 'rotate-180' : ''}`} />
        {showReasoning ? 'Hide reasoning' : 'Show reasoning'}
      </button>

      {showReasoning && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-3 text-sm animate-in fade-in slide-in-from-top-2 duration-150">
          {scqa.situation && (
            <div>
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Situation</span>
              <p className="text-slate-300 mt-1 leading-relaxed">{scqa.situation}</p>
            </div>
          )}
          {scqa.complication && (
            <div>
              <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Complication</span>
              <p className="text-slate-300 mt-1 leading-relaxed">{scqa.complication}</p>
              {scqa.question && (
                <p className="text-slate-500 italic text-xs mt-1.5">→ {scqa.question}</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── DeepFocusView ─────────────────────────────────────────────────────────────

interface DeepFocusViewProps {
  situation: Situation;
  onBack: () => void;
  // Analysis State
  analyzing: boolean;
  analysisResults: any;
  analysisError: string | null;
  // Variance/Deep Analysis View
  daViewMode: 'list' | 'snowflake';
  setDaViewMode: (mode: 'list' | 'snowflake') => void;
  // Refinement Chat
  showRefinementChat: boolean;
  refinementResult: ProblemRefinementResult | null;
  onRefinementComplete: (result: ProblemRefinementResult) => void;
  onRefinementCancel: () => void;
  onStartRefinement: () => void;
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
  initialMarketSignals?: MarketSignal[];
  initialMarketConflict?: MarketConflict | null;
}

export const DeepFocusView: React.FC<DeepFocusViewProps> = ({
  situation,
  onBack,
  analyzing,
  analysisResults,
  analysisError,
  daViewMode: _daViewMode,
  setDaViewMode: _setDaViewMode,
  showRefinementChat,
  refinementResult,
  onRefinementComplete,
  onRefinementCancel,
  onStartRefinement,
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
  principalId,
  initialMarketSignals,
  initialMarketConflict,
}) => {
  const navigate = useNavigate();
  const currentAnalysis = analysisResults;

  // Effective analysis mode: use DA result when available, fall back to situation framing
  const situationIsOpportunity = situation.direction === 'up' || situation.card_type === 'opportunity';
  const analysisMode: 'problem' | 'opportunity' | 'mixed' =
    currentAnalysis?.analysis_mode ?? (situationIsOpportunity ? 'opportunity' : 'problem');

  // Action Center collapse state — auto-opens when analysis arrives
  const [actionCenterOpen, setActionCenterOpen] = useState(false);
  useEffect(() => {
    if (analysisResults) setActionCenterOpen(true);
  }, [analysisResults]);

  // Mixed-mode HITL resolution state
  const [resolvedAnalysisMode, setResolvedAnalysisMode] = useState<'problem' | 'opportunity' | null>(null);
  const [agentDecisionMessage, setAgentDecisionMessage] = useState<string | null>(null);

  // Net absolute delta per segment type — drives the "Let Agent9 Decide" logic
  const { netProblemDelta, netOppDelta } = useMemo(() => {
    if (!currentAnalysis?.kt_is_is_not?.where_is) return { netProblemDelta: 0, netOppDelta: 0 };
    const items: any[] = currentAnalysis.kt_is_is_not.where_is;
    const netProblemDelta = items
      .filter((i: any) => i.segment_type !== 'opportunity')
      .reduce((s: number, i: any) => s + Math.abs(i.delta || 0), 0);
    const netOppDelta = items
      .filter((i: any) => i.segment_type === 'opportunity')
      .reduce((s: number, i: any) => s + Math.abs(i.delta || 0), 0);
    return { netProblemDelta, netOppDelta };
  }, [currentAnalysis]);

  // The mode that will be handed to the debate — resolvedAnalysisMode when mixed, else analysisMode
  const effectiveDebateMode: 'problem' | 'opportunity' =
    resolvedAnalysisMode ?? (analysisMode !== 'mixed' ? analysisMode : 'problem');

  // Accordion state — Situation Summary and Root Cause expanded by default
  const [openSections, setOpenSections] = useState<Set<string>>(new Set(['situation-summary', 'root-cause']));

  const toggleSection = (id: string) => {
    setOpenSections(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const AccordionSection = ({ id, title, icon, summary, children }: { id: string; title: string; icon: React.ReactNode; summary?: string; children: React.ReactNode }) => {
    const isOpen = openSections.has(id);
    return (
      <section className="bg-slate-900 border border-slate-800 rounded-xl shadow-lg overflow-hidden">
        <button
          onClick={() => toggleSection(id)}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-slate-800/50 transition-colors"
        >
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            {icon}
            {title}
          </h2>
          <div className="flex items-center gap-3">
            {!isOpen && summary && (
              <span className="text-xs text-slate-500">{summary}</span>
            )}
            <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
          </div>
        </button>
        {isOpen && <div className="px-6 pb-6">{children}</div>}
      </section>
    );
  };

  // Render Variance Analysis Section (Embedded)

  return (
    <div className="h-screen bg-slate-950 text-white font-sans flex flex-col overflow-hidden">
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
               <span className={`px-2 py-0.5 text-xs font-bold rounded uppercase ${
                 analysisMode === 'opportunity' ? 'bg-green-500/20 text-green-400' :
                 analysisMode === 'mixed' ? 'bg-amber-500/20 text-amber-400' :
                 'bg-red-500/20 text-red-400'
               }`}>
                 {analysisMode === 'opportunity' ? 'Opportunity' : analysisMode === 'mixed' ? 'Mixed' : situation.severity}
               </span>
               <span className="text-slate-500 text-xs uppercase tracking-wider">
                 ID: {situation.situation_id?.substring(0, 8)}
               </span>
            </div>
            <h1 className="text-xl font-bold text-white">{situation.kpi_name} {
              analysisMode === 'opportunity' ? 'Opportunity' :
              analysisMode === 'mixed' ? 'Mixed Analysis' :
              'Variance'
            }</h1>
          </div>
        </div>
        
        {/* Actions or Context */}
        <div className="flex items-center gap-6">
            <div className="text-right">
                <div className="text-xs text-slate-500 uppercase">Detected</div>
                <div className="text-sm font-medium">{new Date().toLocaleDateString(undefined, { month: 'short', day: 'numeric' })} · {new Date().toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}</div>
                {currentAnalysis && (
                  <div className="text-[10px] text-slate-600 mt-0.5">YTD 2026 vs YTD 2025</div>
                )}
            </div>
            <BrandLogo size={28} />
        </div>
      </header>

      <div className="flex-1 min-h-0 flex overflow-hidden">
        {/* LEFT COLUMN: Analysis & Data (Scrollable) */}
        <div className="flex-1 overflow-y-auto p-8 border-r border-slate-800 scrollbar-hide">
            <div className="max-w-4xl mx-auto space-y-8">
                
                {/* 1. Situation Summary Card */}
                <AccordionSection
                    id="situation-summary"
                    title="Situation Summary"
                    icon={
                      analysisMode === 'opportunity'
                        ? <TrendingUp className="w-5 h-5 text-green-400" />
                        : analysisMode === 'mixed'
                        ? <AlertTriangle className="w-5 h-5 text-amber-500" />
                        : <AlertTriangle className="w-5 h-5 text-red-400" />
                    }
                    summary={situation.description?.substring(0, 80) + (situation.description && situation.description.length > 80 ? '...' : '') || "Significant variance detected"}
                >
                    <p className="text-lg text-slate-200 mb-4 leading-relaxed">
                        {situation.description || "The system has detected a significant anomaly in this KPI."}
                    </p>
                    <div className="p-4 bg-slate-950/50 rounded-lg border border-slate-800/50">
                         <h4 className="text-xs font-bold text-slate-500 uppercase mb-2">Business Impact</h4>
                         <p className="text-sm text-slate-400">
                             {situation.business_impact || "Significant variance detected against operational thresholds. Immediate attention recommended."}
                         </p>
                    </div>
                </AccordionSection>

                {/* 2. Deep Analysis Results (or Trigger) */}
                <section>
                    {/* Section header — shown when DA not yet run */}
                    {!currentAnalysis && !analyzing && (
                        <div className="flex items-center mb-4">
                            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                <Microscope className="w-5 h-5 text-blue-400" />
                                Root Cause Analysis
                            </h2>
                        </div>
                    )}

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
                </section>

                {/* Root Cause Analysis — collapsible accordion */}
                {currentAnalysis && (
                    <AccordionSection
                        id="root-cause"
                        title="Root Cause Analysis"
                        icon={<Microscope className="w-5 h-5 text-blue-400" />}
                        summary={`${currentAnalysis.change_points?.length || 0} dimensions analyzed`}
                    >
                        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4">
                            {/* SCQA — answer-first */}
                            {currentAnalysis.scqa_summary && (() => {
                                const scqa = parseScqa(currentAnalysis.scqa_summary);
                                const hasStructure = !!(scqa.answer || scqa.situation);
                                return (
                                  <ScqaBlock scqa={scqa} raw={currentAnalysis.scqa_summary} hasStructure={hasStructure} />
                                );
                            })()}

                            {/* Change Points list — compact fallback when no Is/Is Not data */}
                            {!currentAnalysis.kt_is_is_not && currentAnalysis.change_points && currentAnalysis.change_points.length > 0 && (
                            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
                                 <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Dimension Breakdown</h3>
                                 <div className="space-y-2">
                                     {currentAnalysis.change_points.map((cp: any, i: number) => (
                                         <div key={i} className="flex justify-between items-center bg-slate-950 p-3 rounded border border-slate-800">
                                             <div className="flex flex-col">
                                                 <span className="text-[10px] text-slate-500 uppercase">{cp.dimension}</span>
                                                 <span className="text-sm font-medium text-white">{cp.key}</span>
                                             </div>
                                             <span className={`text-sm font-mono ${cp.delta < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                                                 {formatExecutive(cp.delta || 0)}
                                             </span>
                                         </div>
                                     ))}
                                 </div>
                            </div>
                            )}
                        </div>
                    </AccordionSection>
                )}

                {/* Is / Is Not Analysis — separate accordion, collapsed by default */}
                {currentAnalysis?.kt_is_is_not && (
                    <AccordionSection
                        id="is-is-not"
                        title={analysisMode === 'opportunity' ? 'Opportunity Breakdown' : 'Variance Breakdown'}
                        icon={<Microscope className="w-5 h-5 text-blue-400" />}
                        summary={`${currentAnalysis.kt_is_is_not.where_is?.length ?? 0} segments`}
                    >
                        <IsIsNotExhibit
                            data={currentAnalysis.kt_is_is_not}
                            kpiName={situation.kpi_name}
                            analysisMode={analysisMode}
                        />
                    </AccordionSection>
                )}

                {/* Replication Targets — separate accordion section */}
                {currentAnalysis?.kt_is_is_not?.benchmark_segments && currentAnalysis.kt_is_is_not.benchmark_segments.length > 0 && (() => {
                  const benchmarks = currentAnalysis.kt_is_is_not.benchmark_segments.filter((s: any) => s.benchmark_type === 'internal_benchmark');
                  const controls = currentAnalysis.kt_is_is_not.benchmark_segments.filter((s: any) => s.benchmark_type === 'control_group');
                  const sectionTitle = analysisMode === 'opportunity' ? "Success Blueprints" : analysisMode === 'mixed' ? "Replication Targets & Blueprints" : "Replication Targets";
                  const sectionDesc = analysisMode === 'opportunity'
                    ? "These leading segments have proven the margin-expansion playbook — replicate their approach across the portfolio."
                    : analysisMode === 'mixed'
                    ? "These outperforming segments are internal proof that the gap is closeable — replicate their playbook across lagging segments."
                    : "These segments are outperforming the KPI target — internal proof that the gap is closeable.";
                  return benchmarks.length > 0 || controls.length > 0 ? (
                    <AccordionSection
                        id="replication-targets"
                        title={sectionTitle}
                        icon={<TrendingUp className="w-4 h-4 text-green-400" />}
                        summary={`${benchmarks.length} ${analysisMode === 'opportunity' ? 'leading segment' : 'internal benchmark'}${benchmarks.length === 1 ? '' : 's'}`}
                    >
                      <div className="bg-slate-900/50 border border-green-500/20 rounded-xl p-6">
                        <p className="text-xs text-slate-500 mb-4">
                          {sectionDesc}
                        </p>
                        {benchmarks.length > 0 && (
                          <div className="space-y-2 mb-4">
                            {benchmarks.map((seg: any, i: number) => (
                              <div key={i} className="flex items-center justify-between bg-slate-950 border border-green-500/10 rounded-lg px-4 py-3">
                                <div>
                                  <span className="text-xs text-slate-500 uppercase">{seg.dimension}</span>
                                  <div className="text-sm font-medium text-white">{seg.key}</div>
                                </div>
                                <div className="flex items-center gap-3">
                                  <span className="text-sm font-mono text-green-400">{formatExecutive(seg.delta || 0)}</span>
                                  {seg.is_outlier && (
                                    <span
                                      className="text-[10px] px-1.5 py-0.5 bg-amber-900/40 text-amber-300 rounded font-medium cursor-help"
                                      title="This segment's variance is a statistical outlier — it accounts for a disproportionate share of the gap"
                                    >
                                      Outlier
                                    </span>
                                  )}
                                  {seg.effect_size_pct != null && (
                                    <span
                                      className="text-[10px] px-2 py-0.5 bg-slate-800 text-slate-400 rounded font-mono cursor-help"
                                      title={`This segment accounts for ${Math.round(seg.effect_size_pct * 100)}% of total variance across all segments`}
                                    >
                                      {Math.round(seg.effect_size_pct * 100)}% of gap
                                    </span>
                                  )}
                                  {seg.replication_potential != null && (
                                    <span
                                      className="text-[10px] px-2 py-0.5 bg-green-900/40 text-green-300 rounded-full font-medium cursor-help"
                                      title={seg.replication_potential >= 1 ? "This segment is performing at 100% of its own target — a proven playbook to replicate" : `Estimated ${Math.round(seg.replication_potential * 100)}% of the gap could be closed by replicating this segment's approach`}
                                    >
                                      {Math.round(seg.replication_potential * 100)}% potential
                                    </span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                        {controls.length > 0 && (
                          <details className="group">
                            <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-400 select-none">Control Group ({controls.length} segments)</summary>
                            <p className="text-[10px] text-slate-600 mt-1 mb-2 pl-1">Segments performing at or near target — used to isolate factors driving the variance.</p>
                            <div className="mt-1 space-y-1">
                              {controls.map((seg: any, i: number) => (
                                <div key={i} className="flex items-center justify-between bg-slate-950/50 rounded px-3 py-2 text-xs text-slate-400">
                                  <span>{seg.dimension}: {seg.key}</span>
                                  <div className="flex items-center gap-2">
                                    {seg.is_outlier && (
                                      <span
                                        className="text-[10px] px-1.5 py-0.5 bg-amber-900/30 text-amber-400 rounded font-medium cursor-help"
                                        title="Statistical outlier — delta exceeds mean + 2σ of peer segments. Excluded from replication candidates; interpret with caution."
                                      >
                                        Outlier
                                      </span>
                                    )}
                                    {seg.effect_size_pct != null && (
                                      <span
                                        className="text-[10px] px-1.5 py-0.5 bg-slate-800 text-slate-500 rounded font-mono cursor-help"
                                        title={`Accounts for ${Math.round(seg.effect_size_pct * 100)}% of total variance across all segments`}
                                      >
                                        {Math.round(seg.effect_size_pct * 100)}% of gap
                                      </span>
                                    )}
                                    <span className="font-mono">{formatExecutive(seg.delta || 0)}</span>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </details>
                        )}
                      </div>
                    </AccordionSection>
                  ) : null;
                })()}

                {/* Market Intelligence — separate accordion section */}
                {(initialMarketSignals && initialMarketSignals.length > 0 || initialMarketConflict?.detected) && (
                    <AccordionSection
                        id="market-intelligence"
                        title="Market Intelligence"
                        icon={<Sparkles className={`w-4 h-4 ${initialMarketConflict?.detected ? 'text-amber-400' : 'text-amber-400'}`} />}
                        summary={initialMarketSignals && initialMarketSignals.length > 0 ? `${initialMarketSignals.length} signal${initialMarketSignals.length === 1 ? '' : 's'}` : 'conflict detected'}
                    >
                        <div className="space-y-3">
                            {/* Conflict banner — shown at top when MA signals contradict DA conclusion */}
                            {initialMarketConflict?.detected && initialMarketConflict.summary && (
                              <div className="flex gap-3 bg-amber-950/40 border border-amber-600/30 rounded-lg px-4 py-3">
                                <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                                <div>
                                  <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 block mb-0.5">
                                    Signal Conflict
                                    {initialMarketConflict.confidence != null && (
                                      <span className="ml-2 font-normal normal-case text-amber-500">
                                        ({Math.round(initialMarketConflict.confidence * 100)}% confidence)
                                      </span>
                                    )}
                                  </span>
                                  <p className="text-xs text-amber-200/80">{initialMarketConflict.summary}</p>
                                </div>
                              </div>
                            )}
                            {initialMarketSignals && initialMarketSignals.map((signal, i) => (
                                <div key={i} className="bg-slate-950 border border-slate-800 rounded-lg p-4">
                                    <div className="flex items-start justify-between mb-1">
                                        <h4 className="text-sm font-semibold text-white">{signal.title}</h4>
                                        {signal.relevance_score != null && (
                                            <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                                                signal.relevance_score >= 0.7 ? 'bg-amber-900/50 text-amber-300' :
                                                signal.relevance_score >= 0.4 ? 'bg-slate-800 text-slate-300' :
                                                'bg-slate-800 text-slate-500'
                                            }`}>
                                                {Math.round(signal.relevance_score * 100)}% relevant
                                            </span>
                                        )}
                                    </div>
                                    <p className="text-xs text-slate-400 leading-relaxed">{signal.summary}</p>
                                    <span className="text-[10px] text-slate-600 mt-2 block">
                                      Source: {formatSignalSource(signal.source, signal.url)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </AccordionSection>
                )}
            </div>
        </div>

        {/* RIGHT COLUMN: Action Center — collapsible */}
        {!actionCenterOpen ? (
          <div className="w-12 min-h-0 bg-slate-900 border-l border-slate-800 flex flex-col items-center py-4 gap-3 cursor-pointer hover:bg-slate-800/50 transition-colors"
            onClick={() => setActionCenterOpen(true)}
            role="button"
            aria-label="Open Action Center"
          >
            <ChevronRight className="w-5 h-5 text-slate-500" />
            <span className="text-[9px] font-semibold uppercase tracking-widest text-slate-600 whitespace-nowrap"
              style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', marginTop: '8px' }}>
              Action Center
            </span>
          </div>
        ) : (
        <div className="w-[450px] min-h-0 bg-slate-900 border-l border-slate-800 flex flex-col">

             {/* Header */}
             <div className="flex-shrink-0 p-4 border-b border-slate-800 bg-slate-900 z-10 flex items-center justify-between">
               <div>
                 <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-1">
                     Action Center
                 </h2>
                 <p className="text-xs text-slate-500">Refine context and generate solutions</p>
               </div>
               <button
                 onClick={() => setActionCenterOpen(false)}
                 className="p-1.5 hover:bg-slate-800 rounded text-slate-500 hover:text-white transition-colors"
                 aria-label="Collapse Action Center"
               >
                 <ChevronRight className="w-4 h-4" />
               </button>
             </div>

             <div className={`flex-1 min-h-0 ${showRefinementChat ? 'overflow-hidden flex flex-col p-2' : 'overflow-y-auto p-4 space-y-4'}`}>
                 {/* State A: Waiting for Analysis */}
                 {!currentAnalysis && (
                     <div className="flex flex-col items-center justify-center h-64 text-center p-6 opacity-50">
                         <Microscope className="w-12 h-12 text-slate-600 mb-4" />
                         <p className="text-slate-400 text-sm">Run Deep Analysis to unlock problem refinement and solutions.</p>
                     </div>
                 )}

                 {/* State B: Analysis Done, Start Refinement or Generate Solutions */}
                 {currentAnalysis && !showRefinementChat && !showPersonaSelector && (analysisMode !== 'mixed' || resolvedAnalysisMode !== null) && (
                     <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
                         {agentDecisionMessage && (
                           <div className="bg-amber-900/15 border border-amber-500/30 rounded-lg px-4 py-3 text-xs text-amber-300 flex items-start gap-2">
                             <Sparkles className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
                             <span>{agentDecisionMessage}</span>
                           </div>
                         )}
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
                             <button
                                 onClick={() => setShowPersonaSelector(true)}
                                 className="w-full mt-2 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded font-medium flex items-center justify-center gap-2"
                             >
                                 <CircleDot className="w-3 h-3" />
                                 Generate Solutions →
                             </button>
                         </div>
                     </div>
                 )}

                 {/* State E: Mixed-mode HITL resolution panel */}
                 {currentAnalysis && !showRefinementChat && !showPersonaSelector && analysisMode === 'mixed' && resolvedAnalysisMode === null && (
                   <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
                     <div className="bg-amber-900/10 border border-amber-500/30 rounded-xl p-5">
                       <div className="flex items-center gap-2 mb-2">
                         <SplitSquareHorizontal className="w-4 h-4 text-amber-400" />
                         <h3 className="text-sm font-semibold text-amber-300">Mixed Signals Detected</h3>
                       </div>
                       <p className="text-xs text-slate-400 mb-4 leading-relaxed">
                         This KPI shows both underperforming and outperforming segments. To generate focused solutions, choose which direction Agent9 should prioritise.
                       </p>

                       <div className="space-y-2 mb-4 text-xs">
                         <div className="flex items-center justify-between bg-red-900/20 border border-red-800/40 rounded-lg px-3 py-2">
                           <span className="text-red-300 font-medium">Problem exposure</span>
                           <span className="font-mono text-red-400">{formatExecutive(netProblemDelta, '$', false)}</span>
                         </div>
                         <div className="flex items-center justify-between bg-emerald-900/20 border border-emerald-800/40 rounded-lg px-3 py-2">
                           <span className="text-emerald-300 font-medium">Opportunity upside</span>
                           <span className="font-mono text-emerald-400">{formatExecutive(netOppDelta, '$', false)}</span>
                         </div>
                       </div>

                       <div className="space-y-2">
                         <button
                           onClick={() => setResolvedAnalysisMode('problem')}
                           className="w-full py-2.5 bg-red-900/40 hover:bg-red-900/60 border border-red-700/50 text-red-300 rounded-lg text-sm font-medium transition-colors"
                         >
                           Focus on Recovery
                         </button>
                         <button
                           onClick={() => setResolvedAnalysisMode('opportunity')}
                           className="w-full py-2.5 bg-emerald-900/40 hover:bg-emerald-900/60 border border-emerald-700/50 text-emerald-300 rounded-lg text-sm font-medium transition-colors"
                         >
                           Focus on Opportunity
                         </button>
                         <button
                           onClick={() => {
                             const decided = netOppDelta > netProblemDelta ? 'opportunity' : 'problem';
                             setResolvedAnalysisMode(decided);
                             setAgentDecisionMessage(
                               decided === 'opportunity'
                                 ? `Agent9 chose Opportunity — the upside delta (${formatExecutive(netOppDelta, '$', false)}) outweighs the problem exposure (${formatExecutive(netProblemDelta, '$', false)}).`
                                 : `Agent9 chose Recovery — the problem exposure (${formatExecutive(netProblemDelta, '$', false)}) outweighs the opportunity upside (${formatExecutive(netOppDelta, '$', false)}).`
                             );
                           }}
                           className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-300 rounded-lg text-sm font-medium flex items-center justify-center gap-2 transition-colors"
                         >
                           <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                           Let Agent9 Decide
                         </button>
                       </div>
                     </div>
                   </div>
                 )}

                 {/* State C: Refinement Chat Active */}
                 {showRefinementChat && (
                     <div className="flex-1 min-h-0 flex flex-col overflow-hidden animate-in fade-in">
                         <ProblemRefinementChat
                             deepAnalysisOutput={{
                                 plan: currentAnalysis.plan || {},
                                 execution: currentAnalysis,
                                 market_signals: initialMarketSignals && initialMarketSignals.length > 0 ? initialMarketSignals : undefined,
                                 market_conflict: initialMarketConflict ?? undefined,
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
                             initialMarketSignals={initialMarketSignals}
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
                            <div className="bg-indigo-900/15 rounded-lg p-4 border border-purple-500/30">
                                <div className="flex items-center gap-2 mb-3">
                                    <Sparkles className="w-3.5 h-3.5 text-purple-400" />
                                    <h4 className="text-xs font-bold uppercase tracking-wider text-purple-300">
                                      AI Recommends — {refinementResult.recommended_council_members.map(m => m.persona_name).join(' · ')}
                                    </h4>
                                </div>
                                <div className="space-y-3 mb-4">
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
                                    onClick={() => {
                                      const debateConfig = {
                                        selectedPersonas: refinementResult?.recommended_council_members?.map(m => m.persona_id) ?? ['mckinsey', 'bcg', 'bain'],
                                        councilType: 'preset',
                                        selectedPreset: 'recommended',
                                        useHybridCouncil: false,
                                        resolvedAnalysisMode: effectiveDebateMode,
                                      };
                                      try {
                                        localStorage.setItem(`situation_${situation.situation_id}`, JSON.stringify(situation));
                                        localStorage.setItem(`analysis_${situation.situation_id}`, JSON.stringify(currentAnalysis));
                                        localStorage.setItem(`market_signals_${situation.situation_id}`, JSON.stringify(initialMarketSignals || []));
                                        localStorage.setItem(`principal_context_${situation.situation_id}`, JSON.stringify(principalContext || {}));
                                        localStorage.setItem(`debate_config_${situation.situation_id}`, JSON.stringify(debateConfig));
                                      } catch (_) { /* quota exceeded */ }
                                      navigate(`/debate/${situation.situation_id}`, { state: { situation, analysis: currentAnalysis, marketSignals: initialMarketSignals || [], principalContext: principalContext || {}, debateConfig } });
                                    }}
                                    className="w-full py-2 bg-purple-700 hover:bg-purple-600 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
                                >
                                    <CircleDot className="w-3 h-3" />
                                    Use this recommendation →
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
                                 onClick={() => {
                                   const debateConfig = {
                                     selectedPersonas: useHybridCouncil ? selectedPersonas : (refinementResult?.recommended_council_members?.map(m => m.persona_id) ?? ['mckinsey', 'bcg', 'bain']),
                                     councilType: councilType,
                                     selectedPreset: selectedPreset,
                                     useHybridCouncil: useHybridCouncil,
                                     resolvedAnalysisMode: effectiveDebateMode,
                                   };
                                   try {
                                     localStorage.setItem(`situation_${situation.situation_id}`, JSON.stringify(situation));
                                     localStorage.setItem(`analysis_${situation.situation_id}`, JSON.stringify(currentAnalysis));
                                     localStorage.setItem(`market_signals_${situation.situation_id}`, JSON.stringify(initialMarketSignals || []));
                                     localStorage.setItem(`principal_context_${situation.situation_id}`, JSON.stringify(principalContext || {}));
                                     localStorage.setItem(`debate_config_${situation.situation_id}`, JSON.stringify(debateConfig));
                                   } catch (_) { /* quota exceeded */ }
                                   navigate(`/debate/${situation.situation_id}`, { state: { situation, analysis: currentAnalysis, marketSignals: initialMarketSignals || [], principalContext: principalContext || {}, debateConfig } });
                                 }}
                                 className="w-full mt-2 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded font-medium flex items-center justify-center gap-2"
                             >
                                 <Users className="w-4 h-4" />
                                 Generate Solutions →
                             </button>
                         </div>
                     </div>
                 )}


             </div>
        </div>
        )}
      </div>
    </div>
  );
};
