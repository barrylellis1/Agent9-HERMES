import { useDecisionStudio } from '../hooks/useDecisionStudio';
import { DashboardView } from '../components/views/DashboardView';
import { DeepFocusView } from '../components/views/DeepFocusView';

export function DecisionStudio() {
  const {
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
    currentPrincipal,
    principalInput,
    timeframe,
    
    // Actions
    handleRefresh,
    handleDeepAnalysis,
    handleStartDebate,
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
    setTimeframe,
    
    // Constants
    AVAILABLE_PRINCIPALS,
    AVAILABLE_COUNCILS,
    AVAILABLE_PERSONAS
  } = useDecisionStudio();

  // View Routing
  if (selectedSituation) {
    return (
      <DeepFocusView
        situation={selectedSituation}
        onBack={() => setSelectedSituation(null)}
        
        // Analysis
        analyzing={analyzing}
        analysisResults={analysisResults[selectedSituation.situation_id]}
        analysisError={analysisError}
        onRunAnalysis={handleDeepAnalysis}
        daViewMode={daViewMode}
        setDaViewMode={setDaViewMode}
        
        // Refinement
        showRefinementChat={showRefinementChat}
        refinementResult={refinementResult}
        onRefinementComplete={(result) => {
            setRefinementResult(result);
            setShowRefinementChat(false);
            setShowPersonaSelector(true);
        }}
        onRefinementCancel={() => {
            setShowRefinementChat(false);
            setShowPersonaSelector(true);
        }}
        onStartRefinement={() => setShowRefinementChat(true)}
        
        // Solutions
        findingSolutions={findingSolutions}
        debatePhase={debatePhase}
        solutions={solutions}
        onStartDebate={() => handleStartDebate()}
        
        // Council Config
        useHybridCouncil={useHybridCouncil}
        setUseHybridCouncil={setUseHybridCouncil}
        councilType={councilType}
        setCouncilType={setCouncilType}
        selectedPreset={selectedPreset}
        setSelectedPreset={setSelectedPreset}
        selectedPersonas={selectedPersonas}
        setSelectedPersonas={setSelectedPersonas}
        showPersonaSelector={showPersonaSelector}
        setShowPersonaSelector={setShowPersonaSelector}
        
        // Context
        availableCouncils={AVAILABLE_COUNCILS}
        availablePersonas={AVAILABLE_PERSONAS}
        principalId={selectedPrincipal}
        principalContext={{
            principal_id: selectedPrincipal,
            role: currentPrincipal.title,
            decision_style: currentPrincipal.decision_style,
            name: currentPrincipal.name,
            input: principalInput
        }}
      />
    );
  }

  return (
    <DashboardView
      scanComplete={scanComplete}
      loading={loading}
      situations={situations}
      kpisScanned={14} // Mock
      breachCount={situations.length}
      impactLevel={situations.length > 3 ? 'High' : situations.length > 0 ? 'Medium' : 'Low'}
      impactColor={situations.length > 3 ? 'text-red-400' : situations.length > 0 ? 'text-amber-400' : 'text-green-400'}
      
      selectedPrincipal={selectedPrincipal}
      availablePrincipals={AVAILABLE_PRINCIPALS}
      currentPrincipal={currentPrincipal}
      onSelectPrincipal={setSelectedPrincipal}
      
      timeframe={timeframe}
      onSelectTimeframe={setTimeframe}

      onRefresh={handleRefresh}
      onSelectSituation={setSelectedSituation}
      statusMsg={statusMsg}
      error={error}
    />
  );
}
