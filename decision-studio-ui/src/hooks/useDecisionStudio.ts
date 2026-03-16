import { useState, useEffect, useCallback, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import {
  detectSituations,
  runDeepAnalysis,
  runSolutionFinder,
  approveSolution,
  listPrincipals,
  listClients,
  ProblemRefinementResult,
  Situation,
  OpportunitySignal
} from '../api/client';
import {
  AVAILABLE_PRINCIPALS,
  AVAILABLE_COUNCILS,
  AVAILABLE_PERSONAS
} from '../config/uiConstants';
import { Client, Principal, MarketSignal } from '../api/types';
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
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>([]);
  
  // Context / Principal
  const [selectedPrincipal, setSelectedPrincipal] = useState("cfo_001");
  const [timeframe, setTimeframe] = useState("year_to_date"); // 'year_to_date' | 'current_month'
  const [principalInput, setPrincipalInput] = useState<{current_priorities: string[], known_constraints: string[]}>({
      current_priorities: [],
      known_constraints: []
  });

  // Multi-client support
  const [selectedClientId, setSelectedClientId] = useState("lubricants");
  const [availableClients, setAvailableClients] = useState<Client[]>([]);
  const [availablePrincipals, setAvailablePrincipals] = useState<Principal[]>(AVAILABLE_PRINCIPALS);

  // Effect to set principal and client from router state (set by Login)
  useEffect(() => {
    if (location.state?.clientId) {
      setSelectedClientId(location.state.clientId);
    }
    if (location.state?.principalId) {
      setSelectedPrincipal(location.state.principalId);
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
          setSelectedPrincipal(prev =>
            mapped.find(p => p.id === prev) ? prev : mapped[0].id
          );
        }
      })
      .catch(err => console.warn('Failed to load principals:', err));
  }, [selectedClientId]);

  // Restore solutions from persistence when situation changes
  useEffect(() => {
    if (selectedSituation?.situation_id) {
        const key = `solutions_${selectedSituation.situation_id}`;
        const stored = localStorage.getItem(key);
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                console.log("Restored solutions for", selectedSituation.situation_id, parsed);
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

    try {
      console.log(`Calling Agent9 API for principal: ${selectedPrincipal} timeframe: ${timeframe}...`);
      // Use proper comparison type based on timeframe
      const comparisonType = timeframe === 'current_month' ? 'month_over_month' : 'year_over_year';
      const result = await detectSituations(selectedPrincipal, timeframe, comparisonType, selectedClientId);
      console.log("Agent9 Response:", result);

      setSituations(result.situations);
      setOpportunities(result.opportunities);
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

    console.log('[DA] sit object:', JSON.stringify(sit, null, 2));

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
          sit.card_type === 'opportunity' ? 'opportunity' : 'problem'
        );
        
        if (!result || !result.execution) {
            throw new Error("Analysis completed but returned no results.");
        }

        setAnalysisResults(prev => ({
            ...prev,
            [sitId]: result.execution
        }));

        // Extract market signals from DA result (MA agent runs at end of DA)
        const signals: MarketSignal[] = result.market_signals || [];
        setMarketSignals(signals);

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
                validated_hypotheses: refinementResult.validated_hypotheses,
                invalidated_hypotheses: refinementResult.invalidated_hypotheses,
                refined_problem_statement: refinementResult.refined_problem_statement,
                recommended_council_type: refinementResult.recommended_council_type,
                council_routing_rationale: refinementResult.council_routing_rationale,
                recommended_council_members: refinementResult.recommended_council_members,
            } : null
        };

        if (
            mode === 'recommended' &&
            refinementResult?.recommended_council_members &&
            refinementResult.recommended_council_members.length > 0
        ) {
            preferencesBase.consulting_personas = refinementResult.recommended_council_members.map(m => m.persona_id);
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
        
        const stageResults: any[] = [];
        let stageOneHypotheses: any = null;
        let stageTwoCrossReview: any = null;
        let lastSolutionRequestId: string | null = null;

        const runStage = async (stage: 'stage1_only' | 'hypothesis' | 'cross_review' | 'synthesis') => {
            const stagePreferences = {
                ...preferencesBase,
                debate_stage: stage,
                prior_transcript: stageResults[stageResults.length - 1]?.solutions?.debate_transcript,
                // Pass Stage 1 hypotheses to all stages except stage1_only itself
                prior_stage1_hypotheses: stage !== 'stage1_only' ? stageOneHypotheses : undefined
            };

            const sfResult = await runSolutionFinder(
                deepAnalysisPayload,
                [],
                null,
                selectedPrincipal,
                stagePreferences,
                principalContext,
                selectedSituation?.situation_id  // NEW: pass situation_id
            );
            const response = sfResult.result;  // unwrap
            lastSolutionRequestId = sfResult.request_id;

            stageResults.push(response);

            const stageSolutions = response?.solutions;
            // Capture Stage 1 hypotheses from either the quick stage1_only call or full hypothesis call
            if ((stage === 'stage1_only' || stage === 'hypothesis') && stageSolutions?.stage_1_hypotheses) {
                stageOneHypotheses = stageSolutions.stage_1_hypotheses;
            }
            if (stage === 'cross_review' && stageSolutions?.cross_review) {
                stageTwoCrossReview = stageSolutions.cross_review;
            }
            return response;
        };

        // Stage 1: Quick Haiku-only call — returns firm hypotheses in ~5 seconds for immediate card reveal
        await runStage('stage1_only');
        const hyps = stageResults[stageResults.length - 1]?.solutions?.stage_1_hypotheses ?? null;
        setDebateHypotheses(hyps);
        setDebatePhase(2);

        // Stage 2: Hypothesis synthesis — Sonnet-only (skips Stage 1, uses prior hypotheses)
        await runStage('hypothesis');

        // Stage 3: Cross-review
        await runStage('cross_review');
        setDebatePhase(3);

        const finalResult = await runStage('synthesis');
        const solResponse = finalResult?.solutions || stageResults[stageResults.length - 1]?.solutions;
        const enrichedSolutions = solResponse ? { ...solResponse } : null;

        if (enrichedSolutions) {
            if (stageOneHypotheses && !enrichedSolutions.stage_1_hypotheses) {
                enrichedSolutions.stage_1_hypotheses = stageOneHypotheses;
            }
            if (stageTwoCrossReview) {
                enrichedSolutions.cross_review = stageTwoCrossReview;
            }
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
    selectedSituation,
    analyzing,
    analysisResults,
    analysisError,
    daViewMode,
    comparing,
    comparisonData,
    showRefinementChat,
    refinementResult,
    marketSignals,
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

    // Constants
    AVAILABLE_COUNCILS,
    AVAILABLE_PERSONAS
  };
}
