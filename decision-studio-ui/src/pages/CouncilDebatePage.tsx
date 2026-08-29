import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, AlertTriangle, Loader2, CheckCircle2 } from 'lucide-react';
import { runSolutionFinder, storePendingDecisionSnapshot } from '../api/client';
import { BrandLogo } from '../components/BrandLogo';
import { buildExecutiveBriefing } from '../utils/briefingUtils';

// ─── Firm colour palette ───────────────────────────────────────────────────────

// Keyed by persona id, not exclusively firm id — commercial/operational/
// structural (lens_council) run through the exact same column rendering as
// mckinsey/bcg/bain, so they need entries here too or they fall through to
// getFirmColor's generic grey fallback below: label=raw-id, no accent color,
// which reads as "this option is broken" rather than "this is a different,
// equally-supported methodology" (2026-08-17).
const FIRM_COLORS: Record<string, { label: string; accent: string; border: string; badge: string }> = {
  mckinsey: {
    label: 'McKinsey',
    accent: 'text-blue-300',
    border: 'border-blue-500/30',
    badge: 'bg-blue-900/30 text-blue-300',
  },
  bcg: {
    label: 'BCG',
    accent: 'text-severity-opportunity',
    border: 'border-severity-opportunity/30',
    badge: 'bg-severity-opportunity/30 text-severity-opportunity',
  },
  bain: {
    label: 'Bain',
    accent: 'text-severity-warning',
    border: 'border-severity-warning/30',
    badge: 'bg-severity-warning/30 text-severity-warning',
  },
  commercial: {
    label: 'Commercial',
    accent: 'text-cyan-300',
    border: 'border-cyan-500/30',
    badge: 'bg-cyan-900/30 text-cyan-300',
  },
  operational: {
    label: 'Operational',
    accent: 'text-orange-300',
    border: 'border-orange-500/30',
    badge: 'bg-orange-900/30 text-orange-300',
  },
  structural: {
    label: 'Structural',
    accent: 'text-violet-300',
    border: 'border-violet-500/30',
    badge: 'bg-violet-900/30 text-violet-300',
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

// Stage H collapsed the debate to TWO dispatches: stage1_only -> synthesis.
// There is no cross-review stage anymore — adjudication is the critic pass plus
// the theory-guided moderator, both of which run INSIDE the synthesis call.
//
// The old three-label bar ('Hypothesis', 'Cross-Review', 'Synthesis') mapped
// stage N to phase N, so a user watched "Stage 2 — Cross-Review" tick over to
// DONE (green check) during a run where no cross-review had happened or could
// happen. Phases 2 and 3 now fire back-to-back in the same tick, so that label
// was also on screen for about a millisecond before jumping.
//
// Phases: 0 idle · 1 stage-1 dispatched · 2 stage-1 complete · 3 synthesis
// dispatched · 4 complete.
const STAGES: Array<{ label: string; activeAt: number[]; doneFrom: number }> = [
  { label: 'Hypothesis', activeAt: [1, 2], doneFrom: 3 },
  { label: 'Adjudication & Synthesis', activeAt: [3], doneFrom: 4 },
];

const StageProgress: React.FC<{ phase: number }> = ({ phase }) => (
  <div className="flex gap-3 mb-8">
    {STAGES.map((stage, i) => {
      const stageNum = i + 1;
      const label = stage.label;
      const isDone = phase >= stage.doneFrom;
      const isActive = !isDone && (stage.activeAt.includes(phase) || (phase === 0 && i === 0));
      return (
        <div key={i} className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-bold uppercase tracking-wider ${isDone ? 'text-severity-opportunity' : isActive ? 'text-white' : 'text-slate-600'}`}>
              {isDone ? <CheckCircle2 className="inline w-3.5 h-3.5 mr-1" /> : null}
              Stage {stageNum} — {label}
            </span>
          </div>
          <div className="h-1 rounded-full bg-slate-800 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${isDone ? 'bg-severity-opportunity w-full' : isActive ? 'bg-indigo-400 animate-pulse w-2/3' : 'w-0'}`}
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
  const [debateStartTime] = useState<number>(Date.now());
  const [debateDuration, setDebateDuration] = useState<string | null>(null);

  const [situation, setSituation] = useState<any>(null);
  const [debateConfig, setDebateConfig] = useState<any>(null);
  const [deepAnalysisResults, setDeepAnalysisResults] = useState<any>(null);
  const [marketSignals, setMarketSignals] = useState<any>(null);
  const [principalContext, setPrincipalContext] = useState<any>(null);

  const debateStarted = useRef(false);

  // Set browser tab title
  useEffect(() => {
    if (situation?.kpi_name) {
      document.title = `Council Debate — ${situation.kpi_name}`;
      return () => { document.title = 'Decision Studio'; };
    }
  }, [situation?.kpi_name]);

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

      // Restore cached results only on page refresh (no router state).
      // On fresh navigation from DeepFocusView, routerState.situation is always set —
      // in that case always run a new debate so the user sees the full 3-stage flow.
      const isPageRefresh = !routerState?.situation;
      if (isPageRefresh) {
        const saved = localStorage.getItem(`solutions_${situationId}`);
        if (saved) {
          const s = JSON.parse(saved);
          setStageOneHypotheses(s.stage_1_hypotheses || null);
          setCrossReview(s.cross_review || null);
          setSynthesis(s);
          setPhase(4);
        }
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
      // Clear stale solution data for THIS situation before re-running.
      //
      // This used to drop every solutions_*/briefing_*/solution_request_* key in
      // localStorage regardless of which situation it belonged to — so
      // re-running the debate for one KPI silently destroyed the solutions and
      // briefings of every other situation the user had already generated.
      // Scoped to the current id: the new run overwrites these three keys
      // anyway (see the write below), so nothing else needs removing.
      const sid = situation.situation_id;
      for (const key of [`solutions_${sid}`, `briefing_${sid}`, `solution_request_${sid}`]) {
        try { localStorage.removeItem(key); } catch (_) {}
      }

      setPhase(1);

      const deepAnalysisPayload = deepAnalysisResults || {
        situation_id: situation.situation_id,
        kpi_name: situation.kpi_name,
      };

      // Last-resort default only. Any debate launched through DeepFocusView's
      // Assemble Council screen now populates debateConfig.selectedPersonas
      // for BOTH preset and custom selections (see COUNCIL_PRESET_PERSONAS in
      // uiConstants.ts), so this fallback should be unreachable in normal
      // flow — it exists only for a malformed or pre-2026-08-17 debateConfig.
      // Before that fix, EVERY preset silently hit this line, because
      // choosing a preset (as opposed to Custom) never touched
      // selectedPersonas at all — the backend's own resolution order checks
      // consulting_personas before council_preset, so this hardcoded MBB
      // list always won regardless of which preset was actually clicked.
      const preferencesBase: Record<string, any> = {
        consulting_personas: debateConfig.selectedPersonas?.length ? debateConfig.selectedPersonas : ['mckinsey', 'bcg', 'bain'],
        council_preset: debateConfig.selectedPreset || 'recommended',
      };
      if (debateConfig.resolvedAnalysisMode) {
        preferencesBase.analysis_mode = debateConfig.resolvedAnalysisMode;
      }
      // Phase 19 — this is the fix for a real, pre-existing gap found while
      // building the framing gate: `debateConfig` never carried refinement's
      // constraints/exclusions/hypotheses to Solution Finder AT ALL before
      // this (DeepFocusView.tsx's `dispatchToSolutionFinder` is what now
      // populates `debateConfig.refinementResult` — see that function's own
      // comment for why `useDecisionStudio.ts`'s `handleStartDebate`, which
      // LOOKED like the place this happened, turned out to be dead code with
      // zero callers). `SolutionFinderRequest.preferences` is a free-form
      // dict server-side, so nesting it here reaches the backend as
      // `preferences.refinement_result` — matching what
      // a9_solution_finder_agent.py already reads for constraint exposure,
      // and what Slice 7 reads for `refinement_result.framing_decision`.
      if (debateConfig.refinementResult) {
        preferencesBase.refinement_result = debateConfig.refinementResult;
      }

      let lastRequestId: string | null = null;

      // Tenant for this run. principalContext is the primary carrier, but this page
      // can also be entered by refresh/deep-link where that object was cached before
      // it carried client_id — fall back to the session client rather than send the
      // run untenanted, which silently registers the approved VA solution with
      // client_id=NULL and hides it from every tenant-scoped read.
      const runClientId =
        principalContext?.client_id ||
        situation.client_id ||
        localStorage.getItem('a9_active_client_id') ||
        undefined;

      // Same class of bug, same fix: `situation.principal_id || 'default'`
      // below used to be the ONLY source, but Situation has no principal_id
      // field at all -- every SF run ever made through this page tagged
      // itself with the literal string "default", never a real principal.
      // Invisible until something finally queried by principal_id (the new
      // pending-decisions store, 2026-08-26) -- found live when a completed
      // run never appeared in the Decision Maker's own queue. principalContext
      // is the primary carrier (same object runClientId already reads above);
      // the stored session principal is the same deep-link/refresh fallback
      // runClientId uses for client_id.
      const runPrincipalId =
        principalContext?.principal_id ||
        situation.principal_id ||
        localStorage.getItem('a9_selected_principal_id') ||
        'default';

      // Stage H collapse (2026-08-04): two dispatches, not four. The audited
      // `hypothesis` and `cross_review` stages were IDENTICAL requests to
      // synthesis (debate_stage only gates Stage-1 skipping; prior_transcript
      // is read by no backend code) — three ~4-minute Sonnet mega-calls where
      // the first's output fed nothing and the second's cross_review is also
      // produced by the synthesis call. See PRD 2026-08-04 block.

      // ── Stage 1: Hypotheses ────────────────────────────────────────────────
      const s1Result = await runSolutionFinder(
        deepAnalysisPayload, [], null,
        runPrincipalId,
        { ...preferencesBase, debate_stage: 'stage1_only' },
        principalContext || {}, situation.situation_id,
        runClientId
      );
      lastRequestId = s1Result.request_id;
      const hyps = s1Result.result?.solutions?.stage_1_hypotheses || null;
      if (hyps) setStageOneHypotheses(hyps);
      setPhase(2);

      // ── Synthesis: hypotheses in; options + cross_review + rationale out ──
      setPhase(3);
      const s4Result = await runSolutionFinder(
        deepAnalysisPayload, [], null,
        runPrincipalId,
        {
          ...preferencesBase,
          debate_stage: 'synthesis',
          prior_stage1_hypotheses: hyps,
        },
        principalContext || {}, situation.situation_id,
        runClientId
      );
      lastRequestId = s4Result.request_id;
      const finalSol = s4Result.result?.solutions || s1Result.result?.solutions;
      const effectiveCrossReview = finalSol?.cross_review || null;
      if (effectiveCrossReview) setCrossReview(effectiveCrossReview);
      const enriched = finalSol ? { ...finalSol } : null;
      if (enriched && hyps && !enriched.stage_1_hypotheses) enriched.stage_1_hypotheses = hyps;
      setSynthesis(enriched || null);

      // Persist — clear stale solution keys first to avoid localStorage quota errors
      if (enriched && situationId) {
        try {
          // Evict any prior solution/briefing entries before writing new ones
          Object.keys(localStorage)
            .filter(k => k.startsWith('solutions_') || k.startsWith('briefing_') || k.startsWith('solution_request_'))
            .forEach(k => { try { localStorage.removeItem(k); } catch (_) {} });
          localStorage.setItem(`solutions_${situationId}`, JSON.stringify(enriched));
          const bp = buildExecutiveBriefing(situation, deepAnalysisResults, enriched, marketSignals || []);
          localStorage.setItem(`briefing_${situationId}`, JSON.stringify(bp));
          if (lastRequestId) localStorage.setItem(`solution_request_${situationId}`, lastRequestId);
          // Pending-decision snapshot (2026-08-26, user-caught) — the same
          // payload just written to localStorage above, also persisted
          // server-side so the Decision Maker landing view can show the
          // actual completed recommendation without re-running DA/SF, and
          // so it survives beyond this one browser session. Fire-and-forget,
          // same non-fatal contract as VA's own storeBriefingSnapshot.
          if (lastRequestId) {
            storePendingDecisionSnapshot(lastRequestId, bp).catch(() => {});
          }
        } catch (_) { /* quota still exceeded — skip persistence, state held in memory */ }
      }

      const elapsed = Math.round((Date.now() - debateStartTime) / 1000);
      const mins = Math.floor(elapsed / 60);
      const secs = elapsed % 60;
      setDebateDuration(mins > 0 ? `${mins}m ${secs}s` : `${secs}s`);
      setPhase(4);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Debate failed');
      setPhase(0);
    }
  };

  // ── Derived: council-member list in a stable order ──────────────────────────
  // "firm" in the variable name predates lens_council; kept to limit the diff.
  // Same last-resort-only fallback reasoning as preferencesBase above.
  const firms: string[] = debateConfig?.selectedPersonas?.length
    ? debateConfig.selectedPersonas
    : ['mckinsey', 'bcg', 'bain'];

  // For cross-review: given a firm, return the other firms' reviews of it
  const getReviewsOf = (targetFirm: string): Array<{ reviewer: string; critiques: any[]; endorsements: any[] }> => {
    if (!displayCrossReview) return [];
    return firms
      .filter(f => f !== targetFirm)
      .map(reviewer => {
        const r = displayCrossReview[reviewer] || {};
        return {
          reviewer,
          critiques: r.critiques || [],
          endorsements: r.endorsements || [],
        };
      })
      .filter(r => r.critiques.length > 0 || r.endorsements.length > 0);
  };

  const recommendedId = synthesis?.recommendation?.option_id || synthesis?.recommendation?.id;

  // Derived display state — fall back to synthesis payload when dedicated state vars are empty.
  // The synthesis call always returns stage_1_hypotheses and cross_review; the dedicated state
  // vars (set from the stage1_only call) may be null/empty if that call returned no data.
  const displayHypotheses: Record<string, any> | null =
    (stageOneHypotheses && Object.keys(stageOneHypotheses).length > 0)
      ? stageOneHypotheses
      : (synthesis?.stage_1_hypotheses && Object.keys(synthesis.stage_1_hypotheses as object).length > 0)
        ? synthesis.stage_1_hypotheses as Record<string, any>
        : null;

  const displayCrossReview: Record<string, any> | null =
    crossReview || (synthesis?.cross_review as Record<string, any> | null) || null;

  // Stage H: the moderator arm replaces simulated firm-vs-firm peer review with
  // grades against the theory layer, so `cross_review` is absent by design. The
  // panel below must render the adjudication that DID happen — otherwise every
  // moderator run showed a spinner promising "peer review" followed by "not
  // captured for this run", which reads as a failure rather than a different
  // (and better-grounded) method.
  const displayModeratorGrades: Record<string, any> | null =
    (synthesis?.moderator_grades as Record<string, any> | null) || null;
  const adjudicationMode: 'moderator' | 'peer' | null =
    displayModeratorGrades && Object.keys(displayModeratorGrades).length > 0 ? 'moderator'
      : displayCrossReview ? 'peer' : null;

  // Option id -> title, so grades can name the option a reader actually saw.
  const optionTitleById: Record<string, string> = Object.fromEntries(
    ((synthesis?.options_ranked as any[]) || []).map(o => [o?.id, o?.title]).filter(([id]) => id)
  );

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
  // Semantic colour: low values good for cost/risk, high values good for impact
  const metricBarColor = (key: string, value: number): string => {
    if (key === 'impact') {
      return value >= 6 ? '#34d399' : value >= 3 ? '#f59e0b' : '#f87171';
    }
    // cost and risk: lower is better
    return value <= 3 ? '#34d399' : value <= 6 ? '#f59e0b' : '#f87171';
  };

  const OptionBarChart: React.FC<{ option: any }> = ({ option }) => {
    const metrics = getMetrics(option);
    const metricList = [
      { key: 'impact', label: 'Impact' },
      { key: 'cost', label: 'Cost' },
      { key: 'risk', label: 'Risk' },
    ];

    return (
      <div className="space-y-2 pt-3 border-t border-slate-800">
        {metricList.map(({ key, label }) => {
          const value = metrics[key as keyof typeof metrics];
          const pct = (value / 10) * 100;
          const color = metricBarColor(key, value);
          return (
            <div key={key}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-slate-300">{label}</span>
                <span className="text-xs text-slate-400 font-mono">{value.toFixed(1)}/10</span>
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
      <div className="max-w-xl bg-severity-critical/10 border border-severity-critical/30 rounded-lg p-6 flex gap-4">
        <AlertTriangle className="w-5 h-5 text-severity-critical flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-severity-critical font-semibold mb-1">Debate Error</p>
          <p className="text-severity-critical text-sm">{error}</p>
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
            <p className="text-xs text-slate-500 uppercase tracking-wider mt-0.5">
              Council Debate
              {debateDuration && <span className="text-slate-600 ml-2 normal-case">· Completed in {debateDuration}</span>}
            </p>
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
            const hyp = displayHypotheses?.[firmId];
            const reviews = getReviewsOf(firmId);

            return (
              <div key={firmId} className="flex flex-col gap-4">

                {/* ── Firm header ──────────────────────────────────────── */}
                <div className={`px-4 py-3 rounded-lg border ${c.border} bg-slate-900/60 flex items-center justify-between`}>
                  <span className={`text-sm font-bold uppercase tracking-wider ${c.accent}`}>{c.label}</span>
                  {(phase >= 1 || phase === 4) && hyp?.conviction && (
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                      hyp.conviction === 'High' ? 'bg-severity-opportunity/40 text-severity-opportunity' :
                      hyp.conviction === 'Medium' ? 'bg-severity-warning/40 text-severity-warning' :
                      'bg-slate-800 text-slate-400'
                    }`}>
                      {hyp.conviction} conviction
                    </span>
                  )}
                </div>

                {/* ── Stage 1: Hypothesis ──────────────────────────────── */}
                <div className={`rounded-xl border ${c.border} bg-slate-900 overflow-hidden`}>
                  <div className="px-4 py-2 border-b border-slate-800 bg-slate-950/40">
                    {/* No "Stage N —" prefix inside the cards: the progress bar
                        above already numbers the stages, and repeating it here
                        put two competing numbering schemes on one screen. */}
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Hypothesis</span>
                  </div>
                  <div className="p-4">
                    {!hyp && phase < 4 ? (
                      <FirmThinking label={c.label} accent={c.accent} stageLabel={phase === 1 ? "forming hypothesis" : "synthesizing"} />
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
                      <p className="text-xs text-slate-600 italic">Hypothesis not captured for this run</p>
                    )}
                  </div>
                </div>

                {/* ── Stage 2: adjudication (peer review OR moderator grading) ── */}
                <div className="rounded-xl border border-slate-800 bg-slate-900 overflow-hidden">
                  <div className="px-4 py-2 border-b border-slate-800 bg-slate-950/40">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      {adjudicationMode === 'peer' ? 'Peer Review' : 'Evidence Check'}
                    </span>
                  </div>
                  <div className="p-4">
                    {adjudicationMode === 'moderator' ? (
                      // Grades are keyed by option id, and the option->firm mapping is
                      // not carried in the payload, so this per-firm slot deliberately
                      // does NOT guess an attribution. The verdicts render once, below.
                      <p className="text-xs text-slate-500 italic">
                        Adjudicated against the client's constraints and causal model — see Moderator Verdicts below.
                      </p>
                    ) : phase < 2 && !displayCrossReview ? (
                      <p className="text-xs text-slate-700 italic">Awaiting hypotheses…</p>
                    ) : phase < 4 && !displayCrossReview ? (
                      // Arm-neutral wording. Which adjudication ran is a BACKEND
                      // config the frontend cannot know until the payload lands,
                      // so promising "peer review" mid-flight was wrong on every
                      // moderator run — and moderator is now the default arm.
                      <FirmThinking label="Council" accent="text-slate-400" stageLabel="adjudicating" />
                    ) : reviews.length === 0 ? (
                      <p className="text-xs text-slate-600 italic">Adjudication detail not captured for this run</p>
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
                                  <p className="text-[10px] text-severity-opportunity uppercase mb-1">Endorses</p>
                                  <ul className="space-y-1">
                                    {endorsements.slice(0, 2).map((e: any, i: number) => (
                                      <li key={i} className="flex items-start gap-1.5 text-xs text-slate-300">
                                        <span className="text-severity-opportunity mt-0.5 flex-shrink-0">+</span>
                                        <span>{e.reason}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                              {critiques.length > 0 && (
                                <div>
                                  <p className="text-[10px] text-severity-critical uppercase mb-1">Challenges</p>
                                  <ul className="space-y-1">
                                    {critiques.slice(0, 2).map((c: any, i: number) => (
                                      <li key={i} className="flex items-start gap-1.5 text-xs text-slate-400">
                                        <span className="text-severity-critical mt-0.5 flex-shrink-0">−</span>
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

        {/* ── Moderator Verdicts (Stage H arm) ───────────────────────────────
            Replaces simulated firm-vs-firm critique. Each option graded against
            the constraint register, the causal model, and the observed data —
            evidence, not rhetoric. "Insufficient data" means the theory register
            was too thin to grade against, NOT that the option passed. */}
        {phase === 4 && adjudicationMode === 'moderator' && (
          <div className="mb-12">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
              Moderator Verdicts — graded against verified theory
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(displayModeratorGrades || {}).map(([optId, g]: [string, any]) => {
                const chip = (v: string | undefined) =>
                  v === 'pass' ? 'text-severity-opportunity border-severity-opportunity'
                    : v === 'fail' || v === 'flag' ? 'text-severity-critical border-severity-critical'
                      : 'text-severity-warning border-severity-warning';
                return (
                  <div key={optId} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
                    <p className="text-xs font-bold text-slate-200 mb-2">
                      {optionTitleById[optId] || optId}
                    </p>
                    <div className="flex flex-wrap gap-1.5 mb-2 text-[10px]">
                      <span className={`px-1.5 py-0.5 rounded border ${chip(g?.constraint_survival)}`}>
                        constraints: {g?.constraint_survival ?? 'ungraded'}
                      </span>
                      <span className={`px-1.5 py-0.5 rounded border ${chip(g?.arithmetic_consistency)}`}>
                        arithmetic: {g?.arithmetic_consistency ?? 'ungraded'}
                      </span>
                    </div>
                    {g?.causal_grounding && (
                      <p className="text-[11px] text-slate-400 mb-1">
                        <span className="text-slate-600">causal: </span>{g.causal_grounding}
                      </p>
                    )}
                    {Array.isArray(g?.violated_constraints) && g.violated_constraints.length > 0 && (
                      <p className="text-[11px] text-severity-critical mb-1">Violates: {g.violated_constraints.join('; ')}</p>
                    )}
                    {g?.arithmetic_note && (
                      <p className="text-[11px] text-severity-warning mb-1">{g.arithmetic_note}</p>
                    )}
                    {Array.isArray(g?.critic_findings_response) && g.critic_findings_response.length > 0 && (
                      <ul className="space-y-0.5 mb-1">
                        {g.critic_findings_response.map((f: any, i: number) => (
                          <li key={i} className="text-[11px] text-slate-400">
                            <span className={f?.disposition === 'answered' ? 'text-severity-opportunity' : 'text-severity-warning'}>
                              {f?.disposition === 'answered' ? '✓' : '!'}
                            </span>{' '}
                            {f?.finding}
                          </li>
                        ))}
                      </ul>
                    )}
                    {g?.grade_rationale && (
                      <p className="text-[11px] text-slate-500 italic mt-2">{g.grade_rationale}</p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── Trade-Off Analysis (output of stage 2) ─────────────────────────── */}
        {phase === 4 && synthesis?.options_ranked && (
          <div className="mb-12">
            <div className="mb-6">
              {/* Was "Stage 3 — ...", which no longer exists: the flow is two
                  stages, and this is the OUTPUT of the second, not a third. */}
              <h2 className="text-xl font-semibold text-white mb-1">Trade-Off Analysis</h2>
              <p className="text-sm text-slate-400">Each option rated on impact, cost, and risk (1-10 scale)</p>
            </div>

            {/* Option cards with individual bar charts */}
            {(() => {
              // Build title → advocating firmId map from Stage 1 hypotheses
              const advocateMap = new Map<string, string>();
              if (stageOneHypotheses) {
                firms.forEach(firmId => {
                  const title = stageOneHypotheses[firmId]?.proposed_option?.title;
                  if (title) advocateMap.set(title, firmId);
                });
              }
              return (
                <div className="grid grid-cols-3 gap-6">
                  {synthesis.options_ranked.map((option: any, idx: number) => {
                    const isRec = option.option_id === recommendedId;
                    const advocateFirmId = option.title ? advocateMap.get(option.title) : undefined;
                    const advocate = advocateFirmId ? getFirmColor(advocateFirmId) : null;

                    return (
                      <div
                        key={idx}
                        className={`rounded-xl border p-4 transition-all ${
                          isRec
                            ? 'border-severity-opportunity/50 bg-severity-opportunity/20'
                            : 'border-slate-700 bg-slate-900'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <h3 className="text-sm font-semibold text-white leading-snug">{option.title || `Option ${idx + 1}`}</h3>
                          {isRec && (
                            <span className="text-[10px] font-bold px-2 py-1 rounded-full bg-severity-opportunity/20 text-severity-opportunity whitespace-nowrap flex-shrink-0">
                              Recommended
                            </span>
                          )}
                        </div>
                        {advocate && (
                          <div className="mb-3">
                            <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full border ${advocate.badge} ${advocate.border}`}>
                              Advocated by {advocate.label}
                            </span>
                          </div>
                        )}
                        {option.summary && (
                          <p className="text-xs text-slate-400 leading-relaxed mb-3">{option.summary}</p>
                        )}
                        <OptionBarChart option={option} />
                      </div>
                    );
                  })}
                </div>
              );
            })()}
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
