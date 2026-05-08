# Decision Studio UI — Component Reference

## State Management Architecture

Decision Studio uses **no Redux, Zustand, or context API for workflow state**. Instead:

- **`useDecisionStudio` hook** owns all workflow state (situations, deep analysis, solutions, debate phases, council config). This is the single source of truth for the SA → DA → SF → VA pipeline.
- **Session context** (principal, client, timeframe, available principals) is lifted to `App.tsx` and seeded via router state on login.
- **Page-level props drilling** connects `DecisionStudio` page to `DashboardView` and `DeepFocusView`, which pass everything down via props. No middleware, no async reducers.
- **localStorage persistence**: briefing + solutions payloads saved after SF synthesis; VA snapshot fetched on briefing approval.

This design ensures tight coupling between state changes and UI re-renders, making the multi-stage debate flow (Stage 1 Hypothesis → Cross-Review → Synthesis) traceable and debuggable without middleware ceremony.

---

## Pages (Route-Level Components)

### DecisionStudio
**File:** `src/pages/DecisionStudio.tsx`  
**Type:** Page  
**Renders:** Router for SA → DA → SF workflow. Shows DashboardView (KPI tiles) or DeepFocusView (situation drill-down).  
**Owns:** None — reads all state from `useDecisionStudio` hook.  
**Depends on:** `useDecisionStudio`, `DashboardView`, `DeepFocusView`, router state (principalId, clientId, kpiName).  
**Must NOT:** Persist workflow state itself — hook owns that.

### Login
**File:** `src/pages/Login.tsx`  
**Type:** Page  
**Renders:** Client selector dropdown, principal identity selector, sign-in button. Styled card UI.  
**Owns:** selectedClientId, selectedId (principal), availableClients, principals, loading state.  
**Depends on:** `listClients()`, `listPrincipals()` API calls; `BrandLogo`; router navigation.  
**Must NOT:** Persist principal selection beyond route state — `useDecisionStudio` loads principals again on mount.

### ExecutiveBriefing
**File:** `src/pages/ExecutiveBriefing.tsx`  
**Type:** Page  
**Renders:** Two-panel briefing: left = solution options + analysis (collapsible sections); right = decision chat panel with Q&A, initiative selection, approval.  
**Owns:** briefing data (from localStorage or snapshot fetch), approveState, vaSolutionId, openSections (accordion state), showAttribution.  
**Depends on:** `approveSolution()`, `askBriefingQuestion()`, `storeBriefingSnapshot()`, `getVASolution()`, `DecisionChat`, `ValueAssurancePanel`, `AttributionBreakdown`, `CostOfInactionBanner`.  
**Must NOT:** Call SA or DA agents directly — briefing is pre-computed from previous stage.

### WhitePaperReport
**File:** `src/pages/WhitePaperReport.tsx`  
**Type:** Page  
**Renders:** Print-optimized white-paper document with narrative arc. Cover, situation, problem statement, market context, options, roadmap.  
**Owns:** data (from localStorage), approveState, reportRef (for PDF export).  
**Depends on:** `html2pdf.js` (export), `BrandLogo`, localStorage read.  
**Must NOT:** Persist data — read-only view of briefing generated elsewhere.

### Portfolio
**File:** `src/pages/Portfolio.tsx`  
**Type:** Page  
**Renders:** Portfolio dashboard showing all approved solutions, their phase (Approved → Implementing → Live → Measuring → Complete), attributed impact, and detail panels.  
**Owns:** selectedSolution, solutions, principal filter, measurement input, phase transition UI.  
**Depends on:** `getVAPortfolio()`, `recordKPIMeasurement()`, `updateSolutionPhase()`, `TrajectoryChart`, `ValueAssurancePanel`, `AttributionBreakdown`.  
**Must NOT:** Own approval workflow — VA Agent manages that server-side.

### AdminConsole
**File:** `src/pages/AdminConsole.tsx`  
**Type:** Page  
**Renders:** Hub linking to sub-admin pages: onboard data product, registry explorer, principal management.  
**Owns:** None.  
**Depends on:** Router links to `/admin/onboarding`, `/admin/registry`, `/admin/principals`.  
**Must NOT:** Implement admin features directly — each link goes to a dedicated form page.

### HowItWorks
**File:** `src/pages/HowItWorks.tsx`  
**Type:** Page  
**Renders:** Animated educational landing page explaining the SA → DA → SF workflow with Framer Motion and custom animations.  
**Owns:** None — purely presentation.  
**Depends on:** `AgentAnimations` (custom motion components), Satoshi font.  
**Must NOT:** Have any side effects — static content + animations only.

### LandingPage
**File:** `src/pages/LandingPage.tsx`  
**Type:** Page  
**Renders:** Marketing landing page with hero, product narrative, CTAs to login/demo.  
**Owns:** None — purely presentation.  
**Depends on:** `AgentAnimations`, Satoshi font, router links.  
**Must NOT:** Have any side effects — static content + animations only.

### Additional Pages (Stubs/In Progress)
- **ContextExplorer** — placeholder
- **CompanyProfile** — placeholder
- **RegistryExplorer** — placeholder (registry maintenance UI)
- **DataProductOnboarding**, **DataOnboarding**, **DataProductOnboardingNew** — data product onboarding flows
- **PrincipalManagement** — principal CRUD
- **CouncilDebatePage** — standalone debate demo (not used in main flow)
- **InsightsBIModernization**, **LandingPageAlternate** — alternate landing concepts

---

## Views (Sub-Page Layout Components)

### DashboardView
**File:** `src/components/views/DashboardView.tsx`  
**Type:** View  
**Renders:** KPI scanner dashboard. Header with principal/timeframe selectors, status banner, portfolio link, KPI tile grid, opportunity cards, delegated badge.  
**Owns:** portfolio data (fetched from VA API for selected principal).  
**Depends on:** `KPITile`, `OpportunityCard`, `getVAPortfolio()`, router navigation.  
**Must NOT:** Trigger situation selection — parent `DecisionStudio` handles that via `onSelectSituation` callback.

### DeepFocusView
**File:** `src/components/views/DeepFocusView.tsx`  
**Type:** View  
**Renders:** Multi-tab situation drill-down. Tabs: situation summary, deep analysis (Is/Is Not exhibit), market signals, refinement chat (optional), council debate modal, solution trade-off.  
**Owns:** openSections (accordion state), internal expand/collapse toggles.  
**Depends on:** `ProblemRefinementChat`, `IsIsNotExhibit`, `CouncilDebate`, `TradeOffAnalysis`, `runDeepAnalysis()`, `runSolutionFinder()`.  
**Must NOT:** Manage debate phase state — `useDecisionStudio` owns that; view only renders phase UI.

---

## Dashboard Components

### KPITile
**File:** `src/components/dashboard/KPITile.tsx`  
**Type:** Component  
**Renders:** Single KPI card showing status, percent change, absolute value, sparkline chart, delegated badge (optional).  
**Owns:** Sparkline SVG generation, severity/opportunity color logic, variance/delta calculations.  
**Depends on:** Situation data (read-only), onClick callback.  
**Must NOT:** Manage situation state — parent passes immutable situation object.

### PortfolioDashboard
**File:** `src/components/PortfolioDashboard.tsx`  
**Type:** Component  
**Renders:** Portfolio summary: solution count by verdict (VALIDATED/PARTIAL/FAILED/MEASURING), total attributed impact, executive alerts, solution grid with phase badges.  
**Owns:** Solution card rendering, verdict/phase badge styling, impact aggregation.  
**Depends on:** AcceptedSolution[], onSelectSolution callback.  
**Must NOT:** Persist solution data — parent owns that.

---

## Visualizations

### DivergingBarChart (IsIsNotExhibit)
**File:** `src/components/visualizations/DivergingBarChart.tsx`  
**Type:** Visualization  
**Renders:** Two-level expandable Is/Is Not analysis exhibit. Top level by dimension (customer, product, region), second level shows "is" vs "is not" segments with diverging bars.  
**Owns:** Dimension grouping, expansion state, bar width calculations.  
**Depends on:** KTIsIsNotData (immutable).  
**Must NOT:** Fetch DA output — parent passes pre-computed data.

### TradeOffAnalysis
**File:** `src/components/visualizations/TradeOffAnalysis.tsx`  
**Type:** Visualization  
**Renders:** 3-column option grid (up to 3 options) showing risk/impact/cost badges, title, estimated ROI.  
**Owns:** Option card rendering, label derivation (High/Medium/Low from 0-1 scores).  
**Depends on:** SolutionOption[], recommendedId, onViewBriefing callback.  
**Must NOT:** Manage option selection — parent owns that.

### VarianceCharts
**File:** `src/components/visualizations/VarianceCharts.tsx`  
**Type:** Visualization  
**Renders:** Monthly variance sparkline for KPI comparison type and value.  
**Owns:** SVG rendering, scaling logic.  
**Depends on:** KPI value data (immutable).  
**Must NOT:** Fetch KPI history.

### TrajectoryChart
**File:** `src/components/visualizations/TrajectoryChart.tsx`  
**Type:** Visualization  
**Renders:** Line chart showing solution impact trajectory: actual measured points + expected range band.  
**Owns:** D3/Visx chart rendering, date/value scaling.  
**Depends on:** AcceptedSolution evaluation data.  
**Must NOT:** Trigger measurements — parent owns that.

---

## Decision Workflow Components

### ProblemRefinementChat
**File:** `src/components/ProblemRefinementChat.tsx`  
**Type:** Component  
**Renders:** Multi-turn conversational chat for problem refinement before solution generation. Messages, suggested responses, topic progression (hypothesis → scope → constraints).  
**Owns:** messages[], currentTopic, topicsCompleted, suggestedResponses, refinement state, turn counter.  
**Depends on:** `refineProblem()` API, principalContext, deepAnalysisOutput.  
**Must NOT:** Own debate phase — parent `useDecisionStudio` manages that.

### CouncilDebate
**File:** `src/components/CouncilDebate.tsx`  
**Type:** Component  
**Renders:** Animated "council in session" terminal UI showing phase label, active personas, thought streaming (persona-specific framework language), stage completion.  
**Owns:** Phase-specific thought animation, persona filtering, terminal effect.  
**Depends on:** phase (1-3), activePersonas, stageOneHypotheses (immutable).  
**Must NOT:** Trigger API calls — parent manages that.

### TradeOffAnalysis
(See Visualizations above)

---

## Value Assurance Components

### ValueAssurancePanel
**File:** `src/components/ValueAssurancePanel.tsx`  
**Type:** Component  
**Renders:** VA card showing solution ID, approval timestamp, status badge (MEASURING/VALIDATED/PARTIAL/FAILED), expected impact range, measured impact, composite verdict heatmap.  
**Owns:** Status badge styling, verdict heatmap color scheme.  
**Depends on:** AcceptedSolution data, ImpactEvaluation (immutable).  
**Must NOT:** Trigger measurements — parent owns that.

### AttributionBreakdown
**File:** `src/components/AttributionBreakdown.tsx`  
**Type:** Component  
**Renders:** Horizontal stacked bar showing impact attribution: attributable → market-driven → seasonal → control group. Expected range annotation.  
**Owns:** Segment ordering, bar width proportions, legend.  
**Depends on:** Impact evaluation data (immutable).  
**Must NOT:** Recalculate attribution — assumes pre-computed.

### CostOfInactionBanner
**File:** `src/components/CostOfInactionBanner.tsx`  
**Type:** Component  
**Renders:** Trend-colored alert banner showing projected KPI trajectory if no solution is implemented. 30d/90d projections, revenue impact.  
**Owns:** Trend badge styling, projection calculations.  
**Depends on:** KPI current/comparison values, trend direction, confidence level.  
**Must NOT:** Persist projections — read-only display.

### OpportunityCard
**File:** `src/components/OpportunityCard.tsx`  
**Type:** Component  
**Renders:** Single opportunity card showing headline, delta %, KPI name, confidence score, opportunity type badge.  
**Owns:** Opportunity type label mapping.  
**Depends on:** OpportunitySignal data (immutable), onClick callback.  
**Must NOT:** Manage opportunity selection.

---

## Utility Components

### BrandLogo
**File:** `src/components/BrandLogo.tsx`  
**Type:** Component  
**Renders:** Decision Studio aperture mark (three concentric squares: frame ring + hollow middle + solid center) + optional wordmark.  
**Owns:** SVG rendering, size/color scheme logic.  
**Depends on:** None (pure presentational).  
**Must NOT:** Have any side effects.

---

## Helper Components (Internal/Nested)

### DecisionChat (inside ExecutiveBriefing)
**File:** `src/pages/ExecutiveBriefing.tsx` (lines ~75-274)  
**Type:** Internal component  
**Renders:** Right-panel chat UI for Q&A, initiative selection, approval button. Sticky input + option selector at bottom.  
**Owns:** messages[], input, selectedOption (radio select), loading state.  
**Depends on:** `askBriefingQuestion()`, `approveSolution()`, briefing options data.  
**Must NOT:** Persist chat history — localStorage holds solution payload.

### AccordionSection (inside ExecutiveBriefing)
**File:** `src/pages/ExecutiveBriefing.tsx` (lines ~36-62)  
**Type:** Internal component  
**Renders:** Reusable accordion header + content with toggle button.  
**Owns:** isOpen state (derived from Set in parent).  
**Depends on:** openSections Set, onToggle callback.  
**Must NOT:** Manage its own expanded state — parent owns that.

### StatusBadge, PhaseBadge, VerdictBadge (inside Portfolio, ValueAssurancePanel)
**Type:** Internal component (utility)  
**Renders:** Status/phase/verdict badge with color mapping.  
**Owns:** Style mapping logic.  
**Depends on:** Status/verdict enum value.  
**Must NOT:** Have any side effects.

---

## Hook

### useDecisionStudio
**File:** `src/hooks/useDecisionStudio.ts`  
**Type:** Hook  
**Returns:** Massive state object containing:
- **SA state**: situations, opportunities, scanComplete, kpisScanned, selectedSituation, delegatedKpiNames
- **DA state**: analyzing, analysisResults, analysisError, daViewMode, comparing, comparisonData
- **Refinement state**: showRefinementChat, refinementResult, marketSignals
- **SF state**: findingSolutions, solutions, solutionRequestId, debatePhase, debateHypotheses, approveState
- **Council config**: useHybridCouncil, councilType, selectedPreset, selectedPersonas, showPersonaSelector
- **Session context**: selectedPrincipal, selectedClientId, availablePrincipals, availableClients, timeframe, principalInput
- **Actions**: handleRefresh(), handleDeepAnalysis(), handleCompare(), handleStartDebate(), handleApproveSolution()
- **Constants**: AVAILABLE_COUNCILS, AVAILABLE_PERSONAS

**Key flows:**
1. **Auto-scan on mount**: refs track previous principal/timeframe/client; triggers `detectSituations()` on change.
2. **Deep-link KPI support**: router state provides kpiName; useEffect matches and auto-selects situation.
3. **Solutions persistence**: saves to localStorage after synthesis; restores on situation change.
4. **Debate flow**: Phase 1 (Stage1) → auto-advance if VITE_DEBATE_MODE=fast; Phase 2/3 optional; Phase 4 (synthesis).

**Must NOT:** Modify hook's internal state management — it's tightly coupled to the 3-stage debate architecture.

---

## File Organization Rules

- **pages/**: One route per file. Props drilled from hook to views.
- **components/views/**: DashboardView and DeepFocusView. Accept massive prop objects; don't own workflow state.
- **components/dashboard/**: KPITile (immutable situation card).
- **components/visualizations/**: Charts (DivergingBarChart, TradeOffAnalysis, VarianceCharts, TrajectoryChart).
- **components/** (root): Leaf components (ProblemRefinementChat, CouncilDebate, ValueAssurancePanel, etc.). No nesting of full pages.
- **hooks/**: Only useDecisionStudio. API client imports live in src/api/.

---

## Anti-Patterns to Avoid

1. **Don't split workflow state across multiple hooks** — useDecisionStudio is the single source of truth.
2. **Don't fetch principals/clients in component trees** — fetch once in useDecisionStudio, pass via props.
3. **Don't localStorage.setItem in components** — only useDecisionStudio (or dedicated save effects) should persist.
4. **Don't call runSolutionFinder() or runDeepAnalysis() from views** — call from useDecisionStudio actions only.
5. **Don't add new route-level pages without updating DecisionStudio.tsx routing logic** — page must read from hook.
6. **Don't hardcode URLs in components** — import from src/api/client.ts base URL.
7. **Don't add Redux/Context wrappers** — violates the design.

---

## Testing Notes

- No jest/vitest configured. Manual testing in browser.
- localStorage used for persistence across route changes and page refreshes.
- Router state (principalId, clientId, kpiName) seeds initial hook state on mount.
- API calls all use httpx-based axios client in src/api/client.ts.
