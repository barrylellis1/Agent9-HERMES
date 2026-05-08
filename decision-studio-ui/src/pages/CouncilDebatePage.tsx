import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, Loader2, CheckCircle2 } from 'lucide-react';
import { runSolutionFinder } from '../api/client';
import { BrandLogo } from '../components/BrandLogo';
import { buildExecutiveBriefing } from '../utils/briefingUtils';

// ─── Firm colour palette ───────────────────────────────────────────────────────

const FIRM_COLORS: Record<string, { label: string; accent: string; border: string; badge: string }> = {
  mckinsey: {
    label: 'McKinsey',
    accent: 'text-blue-300',
    border: 'border-blue-500/30',
    badge: 'bg-blue-900/30 text-blue-300',
  },
  bcg: {
    label: 'BCG',
    accent: 'text-emerald-300',
    border: 'border-emerald-500/30',
    badge: 'bg-emerald-900/30 text-emerald-300',
  },
  bain: {
    label: 'Bain',
    accent: 'text-amber-300',
    border: 'border-amber-500/30',
    badge: 'bg-amber-900/30 text-amber-300',
  },
};

const getFirmColor = (id: string) =>
  FIRM_COLORS[id.toLowerCase()] ?? {
    label: id,
    accent: 'text-slate-300',
    border: 'border-slate-700',
    badge: 'bg-slate-800 text-slate-300',
  };

// ─── Stage progress bar ────────────────────────────────────────────────────────

const STAGE_LABELS = ['Hypothesis', 'Cross-Review', 'Synthesis'];

const StageProgress: React.FC<{ phase: number }> = ({ phase }) => (
  <div className="flex gap-3 mb-8">
    {STAGE_LABELS.map((label, i) => {
      const stageNum = i + 1;
      const isDone = phase > stageNum;
      const isActive = phase === stageNum || (phase === 0 && stageNum === 1);
      return (
        <div key={i} className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-bold uppercase tracking-wider ${isDone ? 'text-emerald-400' : isActive ? 'text-white' : 'text-slate-600'}`}>
              {isDone ? <CheckCircle2 className="inline w-3.5 h-3.5 mr-1" /> : null}
              Stage {stageNum} — {label}
            </span>
          </div>
          <div className="h-1 rounded-full bg-slate-800 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${isDone ? 'bg-emerald-400 w-full' : isActive ? 'bg-indigo-400 animate-pulse w-2/3' : 'w-0'}`}
            />
          </div>
        </div>
      );
    })}
  </div>
);

// ─── Per-firm loading animation ────────────────────────────────────────────────

const FirmThinking: React.FC<{ label: string; accent: string; stageLabel: string }> = ({ label, accent, stageLabel }) => {
  const [dots, setDots] = useState('');
  useEffect(() => {
    const t = setInterval(() => setDots(d => d.length >= 3 ? '' : d + '.'), 500);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="flex items-center gap-2 py-4">
      <Loader2 className={`w-3.5 h-3.5 animate-spin ${accent}`} />
      <span className="text-xs text-slate-500">{label} {stageLabel}{dots}</span>
    </div>
  );
};

// ─── CouncilDebatePage ─────────────────────────────────────────────────────────

export const CouncilDebatePage: React.FC = () => {
  const { situationId } = useParams<{ situationId: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  const [phase, setPhase] = useState<number>(0);
  const [stageOneHypotheses, setStageOneHypotheses] = useState<Record<string, any> | null>(null);
  const [crossReview, setCrossReview] = useState<Record<string, any> | null>(null);
  const [synthesis, setSynthesis] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [situation, setSituation] = useState<any>(null);
  const [debateConfig, setDebateConfig] = useState<any>(null);
  const [deepAnalysisResults, setDeepAnalysisResults] = useState<any>(null);
  const [marketSignals, setMarketSignals] = useState<any>(null);
  const [principalContext, setPrincipalContext] = useState<any>(null);

  const debateStarted = useRef(false);

  // Load data on mount — prefer router state (client-side nav), fall back to localStorage (page refresh)
  useEffect(() => {
    if (!situationId) { setError('No situation ID'); setLoading(false); return; }

    try {
      const routerState = location.state as any;

      // Situation: router state first, then localStorage
      const sitData = routerState?.situation || (() => {
        const raw = localStorage.getItem(`situation_${situationId}`);
        return raw ? JSON.parse(raw) : null;
      })();
      if (!sitData) { setError('Situation data not found'); setLoading(false); return; }
      setSituation(sitData);

      // Debate config
      const cfgData = routerState?.debateConfig || (() => {
        const raw = localStorage.getItem(`debate_config_${situationId}`);
        return raw ? JSON.parse(raw) : null;
      })();
      if (cfgData) setDebateConfig(cfgData);

      // Analysis
      const analysisData = routerState?.analysis || (() => {
        const raw = localStorage.getItem(`analysis_${situationId}`);
        return raw ? JSON.parse(raw) : null;
      })();
      if (analysisData) setDeepAnalysisResults(analysisData);

      // Market signals
      const signalsData = routerState?.marketSignals || (() => {
        const raw = localStorage.getItem(`market_signals_${situationId}`);
        return raw ? JSON.parse(raw) : null;
      })();
      if (signalsData) setMarketSignals(signalsData);

      // Principal context
      const ctxData = routerState?.principalContext || (() => {
        const raw = localStorage.getItem(`principal_context_${situationId}`);
        return raw ? JSON.parse(raw) : null;
      })();
      if (ctxData) setPrincipalContext(ctxData);

      // If debate already ran, restore results from localStorage
      const saved = localStorage.getItem(`solutions_${situationId}`);
      if (saved) {
        const s = JSON.parse(saved);
        setStageOneHypotheses(s.stage_1_hypotheses || null);
        setCrossReview(s.cross_review || null);
        setSynthesis(s);
        setPhase(4);
      }

      setLoading(false);
    } catch (err) {
      setError('Failed to load debate data');
      setLoading(false);
    }
  }, [situationId]);

  // Run debate once data is ready
  useEffect(() => {
    if (loading || phase !== 0 || !situation || !debateConfig || debateStarted.current) return;
    debateStarted.current = true;
    runDebate();
  }, [loading, situation, debateConfig]);

  const runDebate = async () => {
    if (!situation || !debateConfig) return;

    try {
      setPhase(1);

      const deepAnalysisPayload = deepAnalysisResults || {
        situation_id: situation.situation_id,
        kpi_name: situation.kpi_name,
      };

      const preferencesBase = {
        consulting_personas: debateConfig.selectedPersonas || ['mckinsey', 'bcg', 'bain'],
        council_preset: debateConfig.selectedPreset || 'recommended',
      };

      const stageResults: any[] = [];
      let hyps: any = null;
      let crossReviewData: any = null;
      let lastRequestId: string | null = null;

      // ── Stage 1: Hypotheses ────────────────────────────────────────────────
      const s1Result = await runSolutionFinder(
        deepAnalysisPayload, [], null,
        situation.principal_id || 'default',
        { ...preferencesBase, debate_stage: 'stage1_only' },
        principalContext || {}, situation.situation_id
      );
      lastRequestId = s1Result.request_id;
      stageResults.push(s1Result.result);
      hyps = s1Result.result?.solutions?.stage_1_hypotheses || null;
      if (hyps) setStageOneHypotheses(hyps);

      // Fast mode (VITE_DEBATE_MODE=fast): skip intermediate stages, go straight to synthesis
      // Full mode (VITE_DEBATE_MODE=full): run all 4 stages for maximum depth
      const debateMode = import.meta.env.VITE_DEBATE_MODE || 'fast';
      if (debateMode === 'full') {
        // ── Stage 2: Hypothesis synthesis ─────────────────────────────────────
        const s2Result = await runSolutionFinder(
          deepAnalysisPayload, [], null,
          situation.principal_id || 'default',
          {
            ...preferencesBase,
            debate_stage: 'hypothesis',
            prior_transcript: stageResults[stageResults.length - 1]?.solutions?.debate_transcript,
            prior_stage1_hypotheses: hyps,
          },
          principalContext || {}, situation.situation_id
        );
        lastRequestId = s2Result.request_id;
        stageResults.push(s2Result.result);
        setPhase(2);

        // ── Stage 3: Cross-review ──────────────────────────────────────────────
        const s3Result = await runSolutionFinder(
          deepAnalysisPayload, [], null,
          situation.principal_id || 'default',
          {
            ...preferencesBase,
            debate_stage: 'cross_review',
            prior_transcript: stageResults[stageResults.length - 1]?.solutions?.debate_transcript,
            prior_stage1_hypotheses: hyps,
          },
          principalContext || {}, situation.situation_id
        );
        lastRequestId = s3Result.request_id;
        stageResults.push(s3Result.result);
        crossReviewData = s3Result.result?.solutions?.cross_review || null;
        if (crossReviewData) setCrossReview(crossReviewData);
      }
      setPhase(3);

      // ── Stage 4: Synthesis ─────────────────────────────────────────────────
      const s4Result = await runSolutionFinder(
        deepAnalysisPayload, [], null,
        situation.principal_id || 'default',
        {
          ...preferencesBase,
          debate_stage: 'synthesis',
          prior_transcript: stageResults[stageResults.length - 1]?.solutions?.debate_transcript,
          prior_stage1_hypotheses: hyps,
        },
        principalContext || {}, situation.situation_id
      );
      lastRequestId = s4Result.request_id;
      const finalSol = s4Result.result?.solutions || stageResults[stageResults.length - 1]?.solutions;
      const enriched = finalSol ? { ...finalSol } : null;
      if (enriched) {
        if (hyps && !enriched.stage_1_hypotheses) enriched.stage_1_hypotheses = hyps;
        if (crossReviewData) enriched.cross_review = crossReviewData;
      }
      setSynthesis(enriched || null);

      // Persist
      if (enriched && situationId) {
        localStorage.setItem(`solutions_${situationId}`, JSON.stringify(enriched));
        const bp = buildExecutiveBriefing(situation, deepAnalysisResults, enriched, marketSignals || []);
        localStorage.setItem(`briefing_${situationId}`, JSON.stringify(bp));
        if (lastRequestId) localStorage.setItem(`solution_request_${situationId}`, lastRequestId);
      }

      setPhase(4);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Debate failed');
      setPhase(0);
    }
  };

  // ── Derived: firm list in a stable order ────────────────────────────────────
  const firms: string[] = debateConfig?.selectedPersonas || ['mckinsey', 'bcg', 'bain'];

  // For cross-review: given a firm, return the other firms' reviews of it
  const getReviewsOf = (targetFirm: string): Array<{ reviewer: string; critiques: any[]; endorsements: any[] }> => {
    if (!crossReview) return [];
    return firms
      .filter(f => f !== targetFirm)
      .map(reviewer => {
        const r = crossReview[reviewer] || {};
        // Critiques/endorsements are all mixed — filter those targeting this firm's option
        // Since targets are option IDs not firm names, show all from this reviewer
        return {
          reviewer,
          critiques: r.critiques || [],
          endorsements: r.endorsements || [],
        };
      })
      .filter(r => r.critiques.length > 0 || r.endorsements.length > 0);
  };

  const recommendedId = synthesis?.recommendation?.option_id || synthesis?.recommendation?.id;

  // Helper: normalize value to 1-10 scale for bar chart
  const normalizeScore = (value: any, defaultVal = 5): number => {
    if (typeof value !== 'number') return defaultVal;
    // If value is 0-1, scale to 1-10; if already 0-5, scale to 1-10
    let normalized = value;
    if (value <= 1) {
      normalized = (value * 9) + 1; // 0-1 → 1-10
    } else if (value <= 5) {
      normalized = (value * 2) - 1; // 0-5 → -1-9, then +2 to get 1-10
      normalized = Math.max(1, Math.min(10, (value / 5) * 10)); // 0-5 → 0-10, then clamp 1-10
    }
    return Math.max(1, Math.min(10, normalized));
  };

  // Extract metrics from options_ranked
  const getMetrics = (opt: any) => ({
    impact: normalizeScore(opt.expected_impact),
    cost: normalizeScore(opt.cost),
    risk: normalizeScore(opt.risk),
  });

  // Single option bar chart
  const OptionBarChart: React.FC<{ option: any }> = ({ option }) => {
    const metrics = getMetrics(option);
    const metricList = [
      { key: 'impact', label: 'Impact', color: '#3b82f6' },
      { key: 'cost', label: 'Cost', color: '#10b981' },
      { key: 'risk', label: 'Risk', color: '#f59e0b' },
    ];

    return (
      <div className="space-y-2 pt-3 border-t border-slate-800">
        {metricList.map(({ key, label, color }) => {
          const value = metrics[key as keyof typeof metrics];
          const pct = (value / 10) * 100;
          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-slate-300">{label}</span>
                <span className="text-xs text-slate-400 font-mono">{value.toFixed(1)}</span>
              </div>
              <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${pct}%`, backgroundColor: color }}
                />
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // ── Early returns ────────────────────────────────────────────────────────────

  if (loading) return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-background text-foreground p-8">
      <button onClick={() => navigate(-1)} className="flex items-center gap-2 text-slate-400 hover:text-white mb-8">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>
      <div className="max-w-xl bg-red-500/10 border border-red-500/30 rounded-lg p-6 flex gap-4">
        <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-red-400 font-semibold mb-1">Debate Error</p>
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      </div>
    </div>
  );

  // ── Main render ──────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">
      {/* Header */}
      <header className="sticky top-0 z-50 px-8 py-4 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="p-2 text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-xl font-semibold text-white">{situation?.kpi_name || 'KPI Analysis'}</h1>
            <p className="text-xs text-slate-500 uppercase tracking-wider mt-0.5">Council Debate</p>
          </div>
        </div>
        <BrandLogo size={28} />
      </header>

      <div className="p-8 max-w-7xl mx-auto">
        {/* Stage progress */}
        <StageProgress phase={phase} />

        {/* Three-column grid — one column per firm, persists across all stages */}
        <div className="grid grid-cols-3 gap-6 mb-12">
          {firms.map(firmId => {
            const c = getFirmColor(firmId);
            const hyp = stageOneHypotheses?.[firmId];
            const reviews = getReviewsOf(firmId);

            return (
              <div key={firmId} className="flex flex-col gap-4">

                {/* ── Firm header ──────────────────────────────────────── */}
                <div className={`px-4 py-3 rounded-lg border ${c.border} bg-slate-900/60 flex items-center justify-between`}>
                  <span className={`text-sm font-bold uppercase tracking-wider ${c.accent}`}>{c.label}</span>
                  {phase >= 1 && hyp?.conviction && (
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      hyp.conviction === 'High' ? 'bg-emerald-900/40 text-emerald-300' :
                      hyp.conviction === 'Medium' ? 'bg-amber-900/40 text-amber-300' :
                      'bg-slate-800 text-slate-400'
                    }`}>
                      {hyp.conviction} conviction
                    </span>
                  )}
                </div>

                {/* ── Stage 1: Hypothesis ──────────────────────────────── */}
                <div className={`rounded-xl border ${c.border} bg-slate-900 overflow-hidden`}>
                  <div className="px-4 py-2 border-b border-slate-800 bg-slate-950/40">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Stage 1 — Hypothesis</span>
                  </div>
                  <div className="p-4">
                    {!hyp && phase < 2 ? (
                      <FirmThinking label={c.label} accent={c.accent} stageLabel="forming hypothesis" />
                    ) : hyp ? (
                      <div className="space-y-3 animate-in fade-in">
                        <div>
                          <p className="text-[10px] text-slate-500 uppercase mb-1">Framework</p>
                          <p className="text-sm text-slate-200">{hyp.framework}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-slate-500 uppercase mb-1">Hypothesis</p>
                          <p className="text-sm text-slate-300 leading-relaxed">{hyp.hypothesis}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-slate-500 uppercase mb-1">Proposed Direction</p>
                          <p className={`text-sm font-medium ${c.accent}`}>{hyp.proposed_option?.title || '—'}</p>
                        </div>
                      </div>
                    ) : (
                      <p className="text-xs text-slate-600 italic">No hypothesis data</p>
                    )}
                  </div>
                </div>

                {/* ── Stage 2: Cross-Review ────────────────────────────── */}
                <div className="rounded-xl border border-slate-800 bg-slate-900 overflow-hidden">
                  <div className="px-4 py-2 border-b border-slate-800 bg-slate-950/40">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Stage 2 — Peer Review</span>
                  </div>
                  <div className="p-4">
                    {phase < 2 && !crossReview ? (
                      <p className="text-xs text-slate-700 italic">Awaiting Stage 1…</p>
                    ) : phase === 2 && !crossReview ? (
                      <FirmThinking label="Council" accent="text-slate-400" stageLabel="cross-reviewing" />
                    ) : reviews.length === 0 && phase >= 2 ? (
                      <p className="text-xs text-slate-600 italic">No peer review data</p>
                    ) : (
                      <div className="space-y-4 animate-in fade-in">
                        {reviews.map(({ reviewer, critiques, endorsements }) => {
                          const rc = getFirmColor(reviewer);
                          return (
                            <div key={reviewer}>
                              <p className={`text-[10px] font-bold uppercase tracking-wider mb-2 ${rc.accent}`}>
                                {rc.label}
                              </p>
                              {endorsements.length > 0 && (
                                <div className="mb-2">
                                  <p className="text-[10px] text-emerald-500 uppercase mb-1">Endorses</p>
                                  <ul className="space-y-1">
                                    {endorsements.slice(0, 2).map((e: any, i: number) => (
                                      <li key={i} className="flex items-start gap-1.5 text-xs text-slate-300">
                                        <span className="text-emerald-500 mt-0.5 flex-shrink-0">+</span>
                                        <span>{e.reason}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {critiques.length > 0 && (
                                <div>
                                  <p className="text-[10px] text-red-400 uppercase mb-1">Challenges</p>
                                  <ul className="space-y-1">
                                    {critiques.slice(0, 2).map((c: any, i: number) => (
                                      <li key={i} className="flex items-start gap-1.5 text-xs text-slate-400">
                                        <span className="text-red-400 mt-0.5 flex-shrink-0">−</span>
                                        <span>{c.concern}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </div>


              </div>
            );
          })}
        </div>

        {/* ── Stage 3: Trade-Off Analysis ────────────────────────────────────── */}
        {phase === 4 && synthesis?.options_ranked && (
          <div className="mb-12">
            <div className="mb-6">
              <h2 className="text-xl font-semibold text-white mb-1">Stage 3 — Synthesis & Trade-Off Analysis</h2>
              <p className="text-sm text-slate-400">Each option rated on impact, cost, and risk (1-10 scale)</p>
            </div>

            {/* Option cards with individual bar charts */}
            <div className="grid grid-cols-3 gap-6">
              {synthesis.options_ranked.map((option: any, idx: number) => {
                const isRec = option.option_id === recommendedId;

                return (
                  <div
                    key={idx}
                    className={`rounded-xl border p-4 transition-all ${
                      isRec
                        ? 'border-emerald-500/50 bg-emerald-950/20'
                        : 'border-slate-700 bg-slate-900'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <h3 className="text-sm font-semibold text-white leading-snug">{option.title || `Option ${idx + 1}`}</h3>
                      {isRec && (
                        <span className="text-[10px] font-bold px-2 py-1 rounded-full bg-emerald-500/20 text-emerald-400 whitespace-nowrap flex-shrink-0">
                          Recommended
                        </span>
                      )}
                    </div>
                    {option.summary && (
                      <p className="text-xs text-slate-400 leading-relaxed mb-3">{option.summary}</p>
                    )}
                    <OptionBarChart option={option} />
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* CTA */}
        {phase === 4 && (
          <div className="flex justify-center">
            <button
              onClick={() => navigate(`/briefing/${situationId}`)}
              className="px-8 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-white font-semibold transition-colors"
            >
              View Executive Briefing →
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
