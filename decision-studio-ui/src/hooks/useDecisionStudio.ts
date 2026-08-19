import { useState, useEffect, useCallback, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import {
  detectSituations,
  runDeepAnalysis,
  runSolutionFinder,
  approveSolution,
  listPrincipals,
  listClients,
  getPrincipalActions,
  ProblemRefinementResult,
  Situation,
  OpportunitySignal,
  FramingDecision,
  FramingPrompt
} from '../api/client';
import type { RefinementProgress } from '../components/ProblemRefinementChat';
import {
  AVAILABLE_PRINCIPALS,
  AVAILABLE_COUNCILS,
  AVAILABLE_PERSONAS,
  COUNCIL_PRESET_PERSONAS
} from '../config/uiConstants';
import { Client, Principal, MarketSignal, MarketConflict, MarketSynthesis } from '../api/types';
import { buildExecutiveBriefing } from '../utils/briefingUtils';

// ── Principal mapping helpers ─────────────────────────────────────────────────

const STYLE_COLORS: Record<string, string> = {
  analytical: 'bg-blue-500/20 text-blue-400',
  visionary:  'bg-purple-500/20 text-purple-400',
  pragmatic:  'bg-emerald-500/20 text-emerald-400',
  decisive:   'bg-amber-500/20 text-amber-400',
};

function inferDecisionStyle(raw: any): Principal['decision_style'] {
  if (raw.decision_style && STYLE_COLORS[raw.decision_style]) return raw.decision_style;
  const title = (raw.title || raw.role || '').toLowerCase();
  if (title.includes('ceo') || title.includes('executive')) return 'visionary';
  if (title.includes('coo') || title.includes('operat')) return 'pragmatic';
  if (title.includes('cto') || title.includes('technology')) return 'decisive';
  return 'analytical';
}

function toInitials(name: string): string {
  return name.split(/\s+/).filter(Boolean).map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

function mapApiPrincipal(raw: any): Principal {
  const style = inferDecisionStyle(raw);
  return {
    id: raw.id,
    name: raw.name || raw.id,
    title: raw.title || raw.role || '',
    initials: toInitials(raw.name || raw.id),
    decision_style: style,
    color: STYLE_COLORS[style] || 'bg-slate-500/20 text-slate-400',
  };
}

export function useDecisionStudio() {
  const location = useLocation();
  
  // --- State ---
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  
  // Scanner / Situations
  const [situations, setSituations] = useState<Situation[]>([]);
  const [opportunities, setOpportunities] = useState<OpportunitySignal[]>([]);
  const [scanComplete, setScanComplete] = useState(false);
  const [selectedSituation, setSelectedSituation] = useState<Situation | null>(null);
  const [kpisScanned, setKpisScanned] = useState<number>(0);
  // Delegated KPI names — used to badge tiles in the dashboard
  const [delegatedKpiNames, setDelegatedKpiNames] = useState<Set<string>>(new Set());
  
  // Deep Analysis
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<Record<string, any>>({});
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [daViewMode, setDaViewMode] = useState<"list" | "snowflake">("snowflake");
  
  // Comparison
  const [comparing, setComparing] = useState(false);
  const [comparisonData, setComparisonData] = useState<any | null>(null);
  
  // Refinement Chat
  const [showRefinementChat, setShowRefinementChat] = useState(false);
  const [refinementResult, setRefinementResult] = useState<ProblemRefinementResult | null>(null);
  const [marketSignals, setMarketSignals] = useState<MarketSignal[]>([]);
  const [marketConflict, setMarketConflict] = useState<MarketConflict | null>(null);
  // Phase 20 §14 decision 6 — synthesis/confidence/sources_queried, already
  // computed by MA but silently dropped before this fix.
  const [marketSynthesis, setMarketSynthesis] = useState<MarketSynthesis | null>(null);
  // Phase 19 — the framing gate's own decision, remembered independently of
  // `refinementResult`. `refinementResult` only updates ONCE, when the whole
  // interview finishes (ProblemRefinementChat's onComplete fires once, at
  // ready_for_solutions=true) — so by the time the LAST topic's response
  // arrives, `framing_decision` has usually gone back to undefined on that
  // specific turn's payload (only the turn that SUBMITTED it carries the
  // field; the agent doesn't re-echo it on every later turn). Without this,
  // framing_decision would silently be lost by the time SF is dispatched.
  const [framingDecision, setFramingDecision] = useState<FramingDecision | null>(null);
  // `null` = "no live refinement turn has reported a value yet this
  // session" — the derived fallback below covers that window. Once a real
  // turn reports a value it takes over and stays authoritative.
  const [liveFramingRequired, setLiveFramingRequired] = useState<boolean | null>(null);
  // Phase 20 — the turn-0 framing_prompt itself (alternatives, snapshots,
  // additional_causal_measures_count), lifted so DeepFocusView's LEFT-panel
  // "Causal Neighbourhood" evidence section can render off the SAME data the
  // compact right-panel FramingGateCard uses — never a separate fetch.
  const [framingPrompt, setFramingPrompt] = useState<FramingPrompt | null>(null);
  
  // Solution Finder / Council
  const [findingSolutions, setFindingSolutions] = useState(false);
  const [solutions, setSolutions] = useState<any | null>(null);
  const [solutionRequestId, setSolutionRequestId] = useState<string | null>(null);
  const [approveState, setApproveState] = useState<'idle' | 'approving' | 'approved' | 'error'>('idle');
  const [showPersonaSelector, setShowPersonaSelector] = useState(false);
  const [debatePhase, setDebatePhase] = useState<number>(0);
  const [debateHypotheses, setDebateHypotheses] = useState<Record<string, any> | null>(null);
  
  // Council Configuration
  const [useHybridCouncil, setUseHybridCouncil] = useState(true);
  const [councilType, setCouncilType] = useState<"preset" | "custom">("preset");
  const [selectedPreset, setSelectedPreset] = useState("mbb_council");
  // Seeded to match selectedPreset's default, not []. An empty array here is
  // what let the default MBB preset mask the dispatch bug this session found —
  // see COUNCIL_PRESET_PERSONAS's comment in uiConstants.ts.
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>(COUNCIL_PRESET_PERSONAS.mbb_council);
  
  // Context / Principal — seed from router state so there's only one SA scan on mount
  const [selectedPrincipal, setSelectedPrincipal] = useState(location.state?.principalId || "cfo_001");
  const [timeframe, setTimeframe] = useState("year_to_date");
  const [principalInput, setPrincipalInput] = useState<{current_priorities: string[], known_constraints: string[]}>({
      current_priorities: [],
      known_constraints: []
  });

  // Multi-client support — seed from router state so principal load uses the right client immediately
  const [selectedClientId, setSelectedClientId] = useState(location.state?.clientId || "lubricants");
  const [availableClients, setAvailableClients] = useState<Client[]>([]);
  const [availablePrincipals, setAvailablePrincipals] = useState<Principal[]>(AVAILABLE_PRINCIPALS);

  // KPI name passed via router state (e.g. from PIB email deep-link token).
  // State (not ref) so the matching effect re-runs when it arrives after situations load.
  const [pendingKpiName, setPendingKpiName] = useState<string | null>(null);

  // Effect for deep-link KPI name from router state (principal/client already seeded in useState)
  useEffect(() => {
    if (location.state?.kpiName) {
      setPendingKpiName(location.state.kpiName);
    }
  }, [location.state]);

  // Load available clients on mount
  useEffect(() => {
    listClients()
      .then(data => { if (data && data.length > 0) setAvailableClients(data as Client[]); })
      .catch(err => console.warn('Failed to load clients:', err));
  }, []);

  // Load principals for the selected client whenever client changes
  useEffect(() => {
    listPrincipals(selectedClientId)
      .then(data => {
        if (data && data.length > 0) {
          const mapped = data.map(mapApiPrincipal);
          setAvailablePrincipals(mapped);
          // Reset to first principal in new list if current selection not found
          setSelectedPrincipal((prev: string) =>
            mapped.find(p => p.id === prev) ? prev : mapped[0].id
          );
        }
      })
      .catch(err => console.warn('Failed to load principals:', err));
  }, [selectedClientId]);

  // Load delegated KPI names for the current principal — used to badge tiles
  useEffect(() => {
    if (!selectedPrincipal) return;
    getPrincipalActions(selectedPrincipal, 'delegate')
      .then(actions => {
        setDelegatedKpiNames(new Set(actions.map(a => a.situation_id)));
      })
      .catch(() => {/* non-fatal */});
  }, [selectedPrincipal]);

  // Auto-select a situation when a deep-link kpiName arrived via router state.
  // Uses state so it re-runs when EITHER situations loads OR kpiName arrives —
  // whichever happens last wins, avoiding the race condition.
  useEffect(() => {
    if (!pendingKpiName || situations.length === 0) return;
    const match = situations.find(
      s => s.kpi_name?.toLowerCase() === pendingKpiName.toLowerCase()
    );
    if (match) {
      setSelectedSituation(match);
      handleDeepAnalysis(match);
      setPendingKpiName(null);
    }
  }, [situations, pendingKpiName]);

  // Restore solutions from persistence when situation changes
  useEffect(() => {
    if (selectedSituation?.situation_id) {
        const key = `solutions_${selectedSituation.situation_id}`;
        const stored = localStorage.getItem(key);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                setSolutions(parsed);
            } catch (e) {
                console.error("Failed to parse stored solutions", e);
                localStorage.removeItem(key);
            }
        } else {
            setSolutions(null);
        }
    } else {
        setSolutions(null);
    }
  }, [selectedSituation?.situation_id]);
  
  // Derived
  const currentPrincipal = availablePrincipals.find(p => p.id === selectedPrincipal) || availablePrincipals[0] || AVAILABLE_PRINCIPALS[0];
  const currentAnalysis = selectedSituation ? analysisResults[selectedSituation.situation_id] : null;
  // Phase 19 — DERIVED, not a hand-defaulted flag. Before any refinement
  // turn has run this session, fall back to what DA's OWN response already
  // says: `scqa_deferred` is only ever true when the backend's
  // enable_framing_gate flag is genuinely on for THIS analysis, so this is
  // correct in both directions without the frontend needing to guess the
  // flag's value out of band — false (today's exact behavior) in every
  // flag-off deployment, true only when the gate is real AND unresolved.
  // Once a live refinement turn reports framingRequired, that value takes
  // over as the authority (liveFramingRequired stops being null).
  const framingRequired = liveFramingRequired ?? (!!currentAnalysis?.scqa_deferred && !currentAnalysis?.scqa_summary);

  // --- Actions ---

  const handleRefresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    setStatusMsg(null);
    setScanComplete(false);
    setAnalysisResults({});
    setAnalysisError(null);
    setComparisonData(null);
    setSolutions(null);
    setSolutionRequestId(null);
    setApproveState('idle');
    setShowPersonaSelector(false);
    setRefinementResult(null); // Reset refinement
    setFramingDecision(null);
    setLiveFramingRequired(null);
    setFramingPrompt(null);

    try {
      // Use proper comparison type based on timeframe
      const comparisonType = timeframe === 'current_month' ? 'month_over_month' : 'year_over_year';
      const result = await detectSituations(selectedPrincipal, timeframe, comparisonType, selectedClientId);

      setSituations(result.situations);
      setOpportunities(result.opportunities);
      setKpisScanned(result.kpi_evaluated_count ?? result.situations?.length ?? 0);
      setScanComplete(true);

      if (result.situations.length > 0 || result.opportunities.length > 0) {
        const parts: string[] = [];
        if (result.situations.length > 0) parts.push(`${result.situations.length} situation${result.situations.length !== 1 ? 's' : ''}`);
        if (result.opportunities.length > 0) parts.push(`${result.opportunities.length} opportunit${result.opportunities.length !== 1 ? 'ies' : 'y'}`);
        setStatusMsg(`Scan Complete: ${parts.join(', ')} detected.`);
      } else {
        setStatusMsg("Scan Complete: No anomalies detected.");
      }
    } catch (err) {
      console.error("API Error:", err);
      setError(err instanceof Error ? err.message : "Failed to connect to Agent9");
    } finally {
      setLoading(false);
    }
  }, [selectedPrincipal, timeframe, selectedClientId]);

  // Auto-scan on mount and when principal/timeframe/client changes
  const autoScanTriggeredRef = useRef(false);
  const lastPrincipalRef = useRef<string | null>(null);
  const lastTimeframeRef = useRef<string | null>(null);
  const lastClientRef = useRef<string | null>(null);

  useEffect(() => {
    if (!autoScanTriggeredRef.current) {
      autoScanTriggeredRef.current = true;
      lastPrincipalRef.current = selectedPrincipal;
      lastTimeframeRef.current = timeframe;
      lastClientRef.current = selectedClientId;
      handleRefresh();
      return;
    }

    if (
      lastPrincipalRef.current !== selectedPrincipal ||
      lastTimeframeRef.current !== timeframe ||
      lastClientRef.current !== selectedClientId
    ) {
      lastPrincipalRef.current = selectedPrincipal;
      lastTimeframeRef.current = timeframe;
      lastClientRef.current = selectedClientId;
      handleRefresh();
    }
  }, [selectedPrincipal, timeframe, selectedClientId, handleRefresh]);

  const handleDeepAnalysis = async (overrideSituation?: typeof selectedSituation) => {
    const sit = overrideSituation ?? selectedSituation;
    if (!sit) return;
    const sitId = sit.situation_id;

    if (!sit.kpi_name) {
      console.error('[DA] kpi_name missing from situation:', sit);
      setAnalysisError(`Cannot run analysis: situation is missing kpi_name (id=${sitId})`);
      return;
    }

    setAnalyzing(true);
    setAnalysisError(null);
    try {
        const result = await runDeepAnalysis(
          sitId,
          sit.kpi_name,
          selectedPrincipal,
          timeframe,
          (sit.direction === 'up' || sit.card_type === 'opportunity') ? 'opportunity' : 'problem',
          selectedClientId
        );
        
        if (!result || !result.execution) {
            throw new Error("Analysis completed but returned no results.");
        }

        setAnalysisResults(prev => ({
            ...prev,
            [sitId]: result.execution
        }));

        // Extract market signals and conflict from DA result (MA agent runs at end of DA)
        const signals: MarketSignal[] = result.market_signals || [];
        setMarketSignals(signals);
        setMarketConflict(result.market_conflict?.detected ? result.market_conflict : null);
        setMarketSynthesis(result.market_synthesis ?? null);

    } catch (err) {
        console.error("Analysis Failed", err);
        setAnalysisError(err instanceof Error ? err.message : "Analysis failed unexpectedly");
    } finally {
        setAnalyzing(false);
    }
  };

  const handleCompare = async () => {
    setComparing(true);
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1200));
    
    // Dynamic Mock Data logic from original component
    let dimension = "Profit Center";
    let segments = [
        { name: "North America", value: 42000000, target: 45000000, status: "critical" },
        { name: "Europe", value: 38500000, target: 38000000, status: "good" },
        { name: "APAC", value: 31000000, target: 30500000, status: "good" },
        { name: "LatAm", value: 12000000, target: 12200000, status: "warning" }
    ];

    const topDriver = currentAnalysis?.change_points?.[0]?.dimension;
    if (topDriver === 'Customer Type Name') {
        dimension = "Customer Segment";
        segments = [
            { name: "Enterprise (B2B)", value: 85000000, target: 90000000, status: "critical" },
            { name: "SMB", value: 45000000, target: 42000000, status: "good" },
            { name: "Government", value: 28000000, target: 28000000, status: "good" }
        ];
    } else if (topDriver === 'Product Name') {
        dimension = "Product Group";
        segments = [
            { name: "Electronics", value: 12000000, target: 15000000, status: "critical" },
            { name: "Home Goods", value: 8000000, target: 8200000, status: "good" },
            { name: "Apparel", value: 5000000, target: 5100000, status: "good" }
        ];
    }

    setComparisonData({ dimension, segments });
    setComparing(false);
  };

  const handleStartDebate = async (
    mode: 'recommended' | 'manual' = 'manual',
    priorityText?: string,
    constraintText?: string
  ) => {
    // Phase 19 — last line of defence. The real dispatch path in production
    // today is CouncilDebatePage.tsx (navigated to from DeepFocusView, not
    // this function — this function has no callers as of the framing-gate
    // build, kept correct anyway in case it's revived), which has its own
    // equivalent guard. Both must independently refuse to bypass the gate.
    if (framingRequired) {
        setAnalysisError('The framing question must be answered before generating solutions.');
        return;
    }
    setFindingSolutions(true);
    setShowPersonaSelector(false);
    setDebatePhase(1);
    setSolutions(null);
    setAnalysisError(null);
    setDebateHypotheses(null);
    
    try {
        const deepAnalysisPayload = {
            plan: currentAnalysis.plan || {},
            execution: currentAnalysis,
            market_signals: marketSignals.length > 0 ? marketSignals : undefined,
            market_conflict: marketConflict ?? undefined,
            situation_context: selectedSituation ? {
                kpi_name: selectedSituation.kpi_name,
                description: selectedSituation.description,
                severity: selectedSituation.severity,
                situation_id: selectedSituation.situation_id
            } : null
        };
        
        const preferencesBase: any = {
            principal_input: {
                ...principalInput,
                current_priorities: [...principalInput.current_priorities, ...(priorityText ? [priorityText] : [])],
                known_constraints: [...principalInput.known_constraints, ...(constraintText ? [constraintText] : [])]
            },
            refinement_result: refinementResult ? {
                exclusions: refinementResult.exclusions,
                external_context: refinementResult.external_context,
                constraints: refinementResult.constraints,
                // Typed constraints with provenance. This object is an explicit
                // field allow-list, so a new field on ProblemRefinementResult
                // reaches Solution Finder only when added here — omitting it fails
                // silently, with the flat `constraints` list masking the loss.
                constraint_items: refinementResult.constraint_items,
                validated_hypotheses: refinementResult.validated_hypotheses,
                invalidated_hypotheses: refinementResult.invalidated_hypotheses,
                refined_problem_statement: refinementResult.refined_problem_statement,
                recommended_council_type: refinementResult.recommended_council_type,
                council_routing_rationale: refinementResult.council_routing_rationale,
                recommended_council_members: refinementResult.recommended_council_members,
                // Phase 19 — refinementResult.framing_decision only survives on
                // the ONE turn that submitted it; every later turn's result
                // doesn't re-echo it. framingDecision (state, set live via
                // applyRefinementProgress) is the durable copy.
                framing_decision: refinementResult.framing_decision ?? framingDecision,
            } : null
        };

        // Persona selection: 'recommended' mode always wins, then hybrid council, then legacy
        if (mode === 'recommended') {
            const members = refinementResult?.recommended_council_members
                ?? preferencesBase.refinement_result?.recommended_council_members
                ?? [];
            if (members.length > 0) {
                preferencesBase.consulting_personas = members.map((m: any) => m.persona_id);
            }
        } else if (useHybridCouncil) {
            if (councilType === 'preset') {
                preferencesBase.council_preset = selectedPreset;
            } else if (selectedPersonas.length > 0) {
                preferencesBase.consulting_personas = selectedPersonas;
            }
        } else if (selectedPersonas.length > 0) {
            preferencesBase.personas = selectedPersonas;
        }
        
        const principalContext = {
            principal_id: selectedPrincipal,
            role: currentPrincipal.title,
            decision_style: currentPrincipal.decision_style,
            name: currentPrincipal.name,
            client_id: selectedClientId
        };
        
        let stageOneHypotheses: any = null;
        let lastSolutionRequestId: string | null = null;

        // Stage H collapse (2026-08-04): two dispatches, not four.
        //
        // The old flow's `hypothesis` and `cross_review` stages were audited as
        // IDENTICAL requests to the synthesis stage — debate_stage only gates
        // Stage-1 skipping on the backend, and `prior_transcript` (sent forward
        // each stage) is read by no backend code at all. Full mode was three
        // 4-minute Sonnet mega-calls where the first's output was consumed by
        // nothing and the second's only unique product (cross_review) is also
        // emitted by the synthesis call itself. See PRD 2026-08-04 block.
        //
        // VITE_DEBATE_MODE no longer changes anything here — both former modes
        // now run the same two dispatches. The A/B comparison arm (simulated vs
        // staged debate, PM-2) is a BACKEND config choice on the synthesis path,
        // not a frontend dispatch count; the env var is retired rather than
        // left as a knob that silently does nothing different.
        const runStage = async (stage: 'stage1_only' | 'synthesis') => {
            const stagePreferences = {
                ...preferencesBase,
                debate_stage: stage,
                // The only cross-stage state the backend actually consumes.
                prior_stage1_hypotheses: stage !== 'stage1_only' ? stageOneHypotheses : undefined
            };

            const sfResult = await runSolutionFinder(
                deepAnalysisPayload,
                [],
                null,
                selectedPrincipal,
                stagePreferences,
                principalContext,
                selectedSituation?.situation_id,
                selectedClientId
            );
            lastSolutionRequestId = sfResult.request_id;
            return sfResult.result;
        };

        // Stage 1: Quick Haiku-only call — returns firm hypotheses in ~5 seconds for immediate card reveal
        const s1Response = await runStage('stage1_only');
        const hyps = s1Response?.solutions?.stage_1_hypotheses ?? null;
        stageOneHypotheses = hyps;
        setDebateHypotheses(hyps);
        setDebatePhase(2);

        // Synthesis: Stage-1 hypotheses in, options + cross_review + rationale out.
        setDebatePhase(3);
        const finalResult = await runStage('synthesis');
        const solResponse = finalResult?.solutions || s1Response?.solutions;
        const enrichedSolutions = solResponse ? { ...solResponse } : null;

        if (enrichedSolutions && stageOneHypotheses && !enrichedSolutions.stage_1_hypotheses) {
            enrichedSolutions.stage_1_hypotheses = stageOneHypotheses;
        }

        setSolutions(enrichedSolutions || null);
        setSolutionRequestId(lastSolutionRequestId);
        setApproveState('idle');

        try {
          if (enrichedSolutions && selectedSituation?.situation_id) {
            localStorage.setItem(`solutions_${selectedSituation.situation_id}`, JSON.stringify(enrichedSolutions));
            const briefingPayload = buildExecutiveBriefing(selectedSituation, currentAnalysis, enrichedSolutions, marketSignals);
            localStorage.setItem(`briefing_${selectedSituation.situation_id}`, JSON.stringify(briefingPayload));
            if (lastSolutionRequestId) {
              localStorage.setItem(`solution_request_${selectedSituation.situation_id}`, lastSolutionRequestId);
            }
          }
        } catch (e) {
          console.error('Failed to persist briefing/solutions payload', e);
        }
    } catch (err) {
        console.error("Solution Finder Failed", err);
        setAnalysisError(err instanceof Error ? err.message : "Failed to generate solutions. Please try again.");
    } finally {
        setFindingSolutions(false);
        setDebatePhase(0);
    }
  };

  /**
   * Phase 19 — the progress-lifting sink for ProblemRefinementChat's
   * onTopicProgress, fired on EVERY turn (not just completion). Two jobs:
   * (1) keep `liveFramingRequired` current so "Generate Solutions" and the
   * other bypass paths stay blocked for exactly as long as the gate is
   * actually pending, not just retroactively once the whole interview ends;
   * (2) merge an arriving frame-aware SCQA into `analysisResults` — ONE
   * merge point that feeds ScqaBlock, the SF dispatch payload, and (once
   * this reaches the backend via the SF/briefing path) `_build_briefing_context`
   * with no further plumbing needed anywhere else.
   */
  const applyRefinementProgress = useCallback((situationId: string, progress: RefinementProgress) => {
    setLiveFramingRequired(progress.framingRequired);
    if (progress.framingDecision) {
        setFramingDecision(progress.framingDecision);
    }
    // Present only on the presentation turn (matches framingDecision's own
    // only-that-turn shape) — once framing is answered, later turns don't
    // re-echo it, so this correctly stops updating rather than being nulled.
    if (progress.framingPrompt) {
        setFramingPrompt(progress.framingPrompt);
    }
    if (progress.scqaSummary) {
        setAnalysisResults(prev => {
            const existing = prev[situationId];
            if (!existing) return prev;
            return {
                ...prev,
                [situationId]: { ...existing, scqa_summary: progress.scqaSummary, scqa_deferred: false },
            };
        });
    }
  }, []);

  const handleApproveSolution = useCallback(async (optionId: string) => {
    if (!solutionRequestId) return;
    setApproveState('approving');
    try {
      await approveSolution(solutionRequestId, optionId);
      setApproveState('approved');
    } catch (err) {
      console.error('Approve failed:', err);
      setApproveState('error');
    }
  }, [solutionRequestId]);

  return {
    // State
    loading,
    error,
    statusMsg,
    situations,
    opportunities,
    scanComplete,
    kpisScanned,
    selectedSituation,
    delegatedKpiNames,
    analyzing,
    analysisResults,
    analysisError,
    daViewMode,
    comparing,
    comparisonData,
    showRefinementChat,
    refinementResult,
    marketSignals,
    marketConflict,
    marketSynthesis,
    framingRequired,
    framingDecision,
    framingPrompt,
    findingSolutions,
    solutions,
    solutionRequestId,
    approveState,
    showPersonaSelector,
    debatePhase,
    debateHypotheses,
    useHybridCouncil,
    councilType,
    selectedPreset,
    selectedPersonas,
    selectedPrincipal,
    principalInput,
    currentPrincipal,
    currentAnalysis,
    timeframe,
    selectedClientId,
    availableClients,
    availablePrincipals,

    // Setters (if needed directly)
    setSelectedSituation,
    setDaViewMode,
    setShowRefinementChat,
    setRefinementResult,
    setShowPersonaSelector,
    setUseHybridCouncil,
    setCouncilType,
    setSelectedPreset,
    setSelectedPersonas,
    setSelectedPrincipal,
    setPrincipalInput,
    setComparisonData,
    setTimeframe,
    setSelectedClientId,

    // Actions
    handleRefresh,
    handleDeepAnalysis,
    handleCompare,
    handleStartDebate,
    handleApproveSolution,
    applyRefinementProgress,

    // Constants
    AVAILABLE_COUNCILS,
    AVAILABLE_PERSONAS
  };
}
