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
    opportunities,
    scanComplete,
    selectedSituation,
    analyzing,
    analysisResults,
    analysisError,
    daViewMode,
    showRefinementChat,
    refinementResult,
    marketSignals,
    findingSolutions,
    solutions,
    showPersonaSelector,
    debatePhase,
    debateHypotheses,
    useHybridCouncil,
    councilType,
    selectedPreset,
    selectedPersonas,
    selectedPrincipal,
    currentPrincipal,
    principalInput,
    timeframe,
    selectedClientId,
    availableClients,
    availablePrincipals,

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
    setSelectedClientId,

    // Constants
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
        debateHypotheses={debateHypotheses}
        solutions={solutions}
        onStartDebate={(mode) => handleStartDebate(mode)}
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
        initialMarketSignals={marketSignals}
        principalContext={{
            principal_id: selectedPrincipal,
            role: currentPrincipal.title,
            decision_style: currentPrincipal.decision_style,
            name: currentPrincipal.name,
            input: principalInput,
            client_id: selectedClientId
        }}
      />
    );
  }

  return (
    <DashboardView
      scanComplete={scanComplete}
      loading={loading}
      situations={situations}
      opportunities={opportunities}
      kpisScanned={14} // Mock
      breachCount={situations.length}
      impactLevel={situations.length > 3 ? 'High' : situations.length > 0 ? 'Medium' : 'Low'}
      impactColor={situations.length > 3 ? 'text-red-400' : situations.length > 0 ? 'text-amber-400' : 'text-green-400'}
      
      selectedPrincipal={selectedPrincipal}
      availablePrincipals={availablePrincipals}
      currentPrincipal={currentPrincipal}
      onSelectPrincipal={setSelectedPrincipal}

      timeframe={timeframe}
      onSelectTimeframe={setTimeframe}

      availableClients={availableClients}
      selectedClientId={selectedClientId}
      onSelectClient={setSelectedClientId}

      onRefresh={handleRefresh}
      onSelectSituation={(sit) => { setSelectedSituation(sit); handleDeepAnalysis(sit); }}
      statusMsg={statusMsg}
      error={error}
    />
  );
}
