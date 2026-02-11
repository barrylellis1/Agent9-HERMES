import { useState, useEffect, useCallback, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  detectSituations, 
  runDeepAnalysis, 
  runSolutionFinder, 
  ProblemRefinementResult, 
  Situation
} from '../api/client';
import { 
  AVAILABLE_PRINCIPALS, 
  AVAILABLE_COUNCILS, 
  AVAILABLE_PERSONAS 
} from '../config/uiConstants';
import { buildExecutiveBriefing } from '../utils/briefingUtils';

export function useDecisionStudio() {
  const location = useLocation();
  
  // --- State ---
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  
  // Scanner / Situations
  const [situations, setSituations] = useState<Situation[]>([]);
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
  
  // Solution Finder / Council
  const [findingSolutions, setFindingSolutions] = useState(false);
  const [solutions, setSolutions] = useState<any | null>(null);
  const [showPersonaSelector, setShowPersonaSelector] = useState(false);
  const [debatePhase, setDebatePhase] = useState<number>(0);
  
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

  // Effect to set principal from router state
  useEffect(() => {
    if (location.state?.principalId) {
      setSelectedPrincipal(location.state.principalId);
    }
  }, [location.state]);

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
  const currentPrincipal = AVAILABLE_PRINCIPALS.find(p => p.id === selectedPrincipal) || AVAILABLE_PRINCIPALS[0];
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
    setShowPersonaSelector(false);
    setRefinementResult(null); // Reset refinement
    
    try {
      console.log(`Calling Agent9 API for principal: ${selectedPrincipal} timeframe: ${timeframe}...`);
      // Use proper comparison type based on timeframe
      const comparisonType = timeframe === 'current_month' ? 'month_over_month' : 'year_over_year';
      const result = await detectSituations(selectedPrincipal, timeframe, comparisonType);
      console.log("Agent9 Response:", result);
      
      if (result && result.length > 0) {
        setSituations(result);
        setScanComplete(true);
        setStatusMsg(`Scan Complete: ${result.length} situations detected.`);
      } else {
        setSituations([]);
        setScanComplete(true);
        setStatusMsg("Scan Complete: No anomalies detected.");
      }
    } catch (err) {
      console.error("API Error:", err);
      setError(err instanceof Error ? err.message : "Failed to connect to Agent9");
    } finally {
      setLoading(false);
    }
  }, [selectedPrincipal, timeframe]);

  // Auto-scan on mount and when principal/timeframe changes
  const autoScanTriggeredRef = useRef(false);
  const lastPrincipalRef = useRef<string | null>(null);
  const lastTimeframeRef = useRef<string | null>(null);

  useEffect(() => {
    if (!autoScanTriggeredRef.current) {
      autoScanTriggeredRef.current = true;
      lastPrincipalRef.current = selectedPrincipal;
      lastTimeframeRef.current = timeframe;
      handleRefresh();
      return;
    }

    if (lastPrincipalRef.current !== selectedPrincipal || lastTimeframeRef.current !== timeframe) {
      lastPrincipalRef.current = selectedPrincipal;
      lastTimeframeRef.current = timeframe;
      handleRefresh();
    }
  }, [selectedPrincipal, timeframe, handleRefresh]);

  const handleDeepAnalysis = async () => {
    if (!selectedSituation) return;
    const sitId = selectedSituation.situation_id;
    
    setAnalyzing(true);
    setAnalysisError(null);
    try {
        const result = await runDeepAnalysis(sitId, selectedSituation.kpi_name, selectedPrincipal);
        
        if (!result || !result.execution) {
            throw new Error("Analysis completed but returned no results.");
        }

        setAnalysisResults(prev => ({
            ...prev,
            [sitId]: result.execution
        }));
        
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
    
    try {
        const deepAnalysisPayload = {
            plan: currentAnalysis.plan || {},
            execution: currentAnalysis,
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
            name: currentPrincipal.name
        };
        
        const stageResults: any[] = [];
        let stageOneHypotheses: any = null;
        let stageTwoCrossReview: any = null;

        const runStage = async (stage: 'hypothesis' | 'cross_review' | 'synthesis') => {
            const stagePreferences = {
                ...preferencesBase,
                debate_stage: stage,
                prior_transcript: stageResults[stageResults.length - 1]?.solutions?.debate_transcript
            };

            const response = await runSolutionFinder(
                deepAnalysisPayload,
                [],
                null,
                selectedPrincipal,
                stagePreferences,
                principalContext
            );

            stageResults.push(response);

            const stageSolutions = response?.solutions;
            if (stage === 'hypothesis' && stageSolutions?.stage_1_hypotheses) {
                stageOneHypotheses = stageSolutions.stage_1_hypotheses;
            }
            if (stage === 'cross_review' && stageSolutions?.cross_review) {
                stageTwoCrossReview = stageSolutions.cross_review;
            }
            return response;
        };

        await runStage('hypothesis');
        await new Promise(resolve => setTimeout(resolve, 1200));
        setDebatePhase(2);

        await runStage('cross_review');
        await new Promise(resolve => setTimeout(resolve, 1200));
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

        try {
          if (enrichedSolutions && selectedSituation?.situation_id) {
            localStorage.setItem(`solutions_${selectedSituation.situation_id}`, JSON.stringify(enrichedSolutions));
            const briefingPayload = buildExecutiveBriefing(selectedSituation, currentAnalysis, enrichedSolutions);
            localStorage.setItem(`briefing_${selectedSituation.situation_id}`, JSON.stringify(briefingPayload));
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

  return {
    // State
    loading,
    error,
    statusMsg,
    situations,
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
    findingSolutions,
    solutions,
    showPersonaSelector,
    debatePhase,
    useHybridCouncil,
    councilType,
    selectedPreset,
    selectedPersonas,
    selectedPrincipal,
    principalInput,
    currentPrincipal,
    currentAnalysis,
    timeframe,
    
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

    // Actions
    handleRefresh,
    handleDeepAnalysis,
    handleCompare,
    handleStartDebate,
    
    // Constants
    AVAILABLE_PRINCIPALS,
    AVAILABLE_COUNCILS,
    AVAILABLE_PERSONAS
  };
}
