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
    kpisScanned,
    selectedSituation,
    delegatedKpiNames,
    analyzing,
    analysisResults,
    analysisError,
    daViewMode,
    showRefinementChat,
    refinementResult,
    marketSignals,
    marketConflict,
    framingRequired,
    framingDecision,
    showPersonaSelector,
    useHybridCouncil,
    councilType,
    selectedPreset,
    selectedPersonas,
    selectedPrincipal,
    currentPrincipal,
    principalInput,
    timeframe,
    selectedClientId,
    availablePrincipals,

    // Actions
    handleRefresh,
    handleDeepAnalysis,
    setSelectedSituation,
    setDaViewMode,
    setShowRefinementChat,
    setRefinementResult,
    applyRefinementProgress,
    setShowPersonaSelector,
    setUseHybridCouncil,
    setCouncilType,
    setSelectedPreset,
    setSelectedPersonas,
    setSelectedPrincipal,
    setTimeframe,

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
        framingRequired={framingRequired}
        framingDecision={framingDecision}
        onTopicProgress={(progress) => {
            if (selectedSituation) applyRefinementProgress(selectedSituation.situation_id, progress);
        }}
        onRefinementComplete={(result) => {
            setRefinementResult(result);
            setShowRefinementChat(false);
            setShowPersonaSelector(true);
        }}
        // Phase 19 / real pre-existing bug fixed alongside it: Cancel used to
        // ALSO open the persona selector — advancing toward Solution Finder
        // on cancel, independent of this feature and also a clean gate
        // bypass (framing pending or not, Cancel got you to State D anyway).
        // Cancel now only closes the chat, full stop.
        onRefinementCancel={() => {
            setShowRefinementChat(false);
        }}
        onStartRefinement={() => setShowRefinementChat(true)}

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
        initialMarketConflict={marketConflict}
        principalContext={{
            principal_id: selectedPrincipal,
            // CouncilDebatePage reads this object back (router state / localStorage) and
            // uses principalContext.client_id as the tenant for the SF workflow run. Without
            // it the run — and therefore the VA solution registered on HITL approval — is
            // written with client_id=NULL and is invisible to every tenant-scoped read,
            // including the Solutions-in-Progress tracker on this dashboard.
            client_id: selectedClientId,
            role: currentPrincipal.title,
            decision_style: currentPrincipal.decision_style,
            name: currentPrincipal.name,
            input: principalInput
        }}
        clientId={selectedClientId}
        timeframe={timeframe}
      />
    );
  }

  return (
    <DashboardView
      scanComplete={scanComplete}
      loading={loading}
      situations={situations}
      opportunities={opportunities}
      kpisScanned={kpisScanned}
      breachCount={situations.length}
      impactLevel={situations.length > 3 ? 'High' : situations.length > 0 ? 'Medium' : 'Low'}
      impactColor={situations.length > 3 ? 'text-red-400' : situations.length > 0 ? 'text-amber-400' : 'text-green-400'}
      
      selectedPrincipal={selectedPrincipal}
      availablePrincipals={availablePrincipals}
      currentPrincipal={currentPrincipal}
      onSelectPrincipal={setSelectedPrincipal}

      timeframe={timeframe}
      onSelectTimeframe={setTimeframe}

      onRefresh={handleRefresh}
      onSelectSituation={(sit) => { setSelectedSituation(sit); handleDeepAnalysis(sit); }}
      statusMsg={statusMsg}
      error={error}
      delegatedKpiNames={delegatedKpiNames}
    />
  );
}
