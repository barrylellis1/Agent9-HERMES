# A9_Business_Optimization_Agent PRD

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2026-05-20
Status: Planned (Phase 3 — 2028)
-->

## Overview

**Purpose:** Orchestrate portfolio-level KPI optimization by reasoning across simultaneous interventions, detecting causal conflicts between solutions, and recommending sequencing and prioritization aligned with corporate strategy.

**Agent Type:** Strategic Portfolio Agent  
**Version:** 0.1 (Design phase)

The Business Optimization Agent operates at Layer 3 (Portfolio Optimization) of Decision Studio's analytical intelligence framework. Whereas Situation Awareness (Layer 1) detects anomalies and Deep Analysis (Layer 2) provides statistical rigor through Kepner-Tregoe variance analysis, the Business Optimization Agent reasons about the portfolio of simultaneous interventions across all active KPIs and recommends constrained optimization that maximizes aggregate strategic value.

---

## Strategic Context

**Three-Layer Analytical Intelligence:**

| Layer | Agent | Function |
|-------|-------|----------|
| **Layer 1 — Detection** | SA Agent | Identify KPI breaches, anomalies, opportunities |
| **Layer 2 — Diagnosis** | DA Agent | Structured IS/IS NOT variance analysis; dimensional drivers; confidence scoring |
| **Layer 3 — Portfolio Optimization** | **BO Agent (this)** | Conflict detection, sequencing, strategic alignment, aggregate impact forecasting |

**Key ICP Stakeholders:**
- CEO / Executive team (portfolio view)
- CSO / Head of Strategy (corporate strategy alignment)
- PE-backed CFOs (value creation plan management)
- Enterprise PMO / Transformation offices (concurrent initiative sequencing)

---

## Functional Requirements

### Core Capabilities

**1. Cross-Intervention Conflict Detection**

Analyze the active solution portfolio and identify causal couplings:

- **Conflict Detection:** When SF recommends Action A on KPI X and Action B on KPI Y simultaneously, this agent queries the DGA's causal KPI map to determine if A and B are causally coupled and will partially cancel each other.
  - Example: Revenue growth action + margin expansion action may conflict if both require price increases with volume elasticity tradeoffs.
  - Output: `conflicts[]` array with `pair`, `mechanism`, `net_impact_reduction_pct`, `severity` (Critical / High / Medium / Low).

- **Dependency Mapping:** Surfaces which solutions are prerequisites for others (must execute A before B).
  - Example: Customer acquisition improvements may require preceding service quality fixes.

**2. Strategic Priority Alignment**

Evaluate the portfolio against declared corporate strategy:

- **Strategy Weighting:** Principal's strategy statement is decomposed into explicit priorities (Growth % / Margin % / Efficiency %).
  - Example: "Profitable growth" → Growth 60%, Margin 35%, Efficiency 5%.

- **Impact Scoring:** Each solution in the portfolio is scored against all three strategic dimensions.
  - A solution improving Gross Margin % but reducing Revenue Growth may be misaligned if strategy is "profitable growth."

- **Alignment Report:** `strategic_alignment_score` (0-1) + per-dimension breakdown + recommendation to pause/resequence misaligned solutions.

**3. Sequencing Recommendations**

When multiple solutions are approved or pending execution:

- **Causal Dependency Graph:** Build a DAG from conflict/dependency data.
  - Example: Service quality fix → revenue growth action → margin optimization (sequence order).

- **Execution Plan:** Recommend optimal order based on:
  - Causal dependencies (must-do-first constraints)
  - Interaction effects (second mover advantage / disadvantage)
  - Time-to-value clustering (execute quick wins first, strategic moves in parallel)
  - Risk management (de-risk before betting on upside).

- **Sequencing Output:** `{phase_1: [solutions], phase_2: [solutions], ...}` with rationale and projected timeline.

**4. Portfolio-Level KPI Trajectory Forecasting**

Project the aggregate movement of all KPIs under the proposed solution portfolio:

- **Baseline Trajectory:** Current KPI path (trend, seasonality, known drivers).

- **Isolated Impact:** Each solution's projected impact on its target KPI (from SF `impact_estimate`).

- **Interaction Effects:** Model second-order effects when solutions execute in proposed sequence.
  - Example: Reduce inventory carrying cost (Cost solution) → improve cash flow → fund pricing optimization (Revenue solution).

- **Aggregate Path:** Composite KPI movement across all dimensions if portfolio executes as planned.

- **Uncertainty Bands:** Confidence intervals around trajectory (accounting for interaction uncertainty).

**5. Solution Portfolio Verification**

Before handing off to execution, verify portfolio completeness and coherence:

- **Coverage Assessment:** Does the portfolio address all material root causes identified in DA output, or are gaps intentional?

- **Redundancy Detection:** Are multiple solutions attacking the same driver? (May be intentional or unneeded.)

- **Feasibility Reality Check:** Do solutions' prerequisites and timelines align? Can they realistically execute in parallel or in proposed sequence?

---

## Input Requirements

### Data Sources

| Source | Provider | Contents | Usage |
|--------|----------|----------|-------|
| **Active Solutions** | Workflow state / VA Agent | All approved + pending solutions for the client, with `impact_estimate` | Conflict analysis, alignment scoring, impact aggregation |
| **DA Outputs** | Deep Analysis Agent | IS/IS NOT maps, dimensional drivers, change points for each KPI breach | Root cause coverage assessment |
| **Causal Map** | Data Governance Agent | KPI interdependencies, causal direction, interaction strength | Conflict detection, dependency graphing |
| **Corporate Strategy** | Principal Context Agent | Declared growth/margin/efficiency weighting | Strategic alignment scoring |
| **Client KPI Registry** | KPI Provider | Baseline, targets, units, historical context | Trajectory baseline modeling |

### Input Model

```python
class BusinessOptimizationInput(A9AgentBaseModel):
    """Portfolio optimization request."""
    client_id: str                                  # Tenant identifier
    active_solutions: List[ApprovedSolution]        # All pending/approved solutions
    deep_analysis_context: Dict[str, Any]           # DA outputs for all active KPIs
    causal_map: Optional[CausalKPIMap] = None       # DGA KPI relationships
    corporate_strategy: CorporateStrategyProfile    # Growth/Margin/Efficiency weighting
    principal_context: PrincipalContext             # Decision style, role, priorities
    scenario_name: Optional[str] = None             # "best_case", "worst_case", "realistic"
    optimization_objective: str = "max_strategic"   # max_strategic | max_aggregate_kpi | cost_minimized
```

---

## Output Specifications

```python
class BusinessOptimizationResult(A9AgentBaseModel):
    """Portfolio optimization analysis."""
    
    # Conflict Analysis
    conflicts: List[ConflictDetection] = []
    # Each: {pair: [sol1_id, sol2_id], mechanism, net_impact_reduction_pct, severity, recommendation}
    
    # Dependency Analysis
    dependencies: List[SolutionDependency] = []
    # Each: {prerequisite_sol_id, dependent_sol_id, dependency_type, rationale}
    
    # Sequencing Recommendation
    execution_phases: List[ExecutionPhase]
    # Each: {phase_num, solutions: [sol_ids], rationale, timeline_weeks, risk_level}
    recommended_sequence_id: str
    sequence_rationale: str
    
    # Strategic Alignment
    strategic_alignment_score: float                # 0.0 - 1.0
    alignment_by_dimension: Dict[str, float]        # growth, margin, efficiency
    misaligned_solutions: List[str]                 # Solution IDs out of strategic bounds
    alignment_recommendations: List[str]            # Actions (pause, resequence, replace)
    
    # Portfolio Impact Forecasting
    portfolio_kpi_forecast: List[KPIForecast]
    # Baseline trend vs. portfolio trajectory (with confidence bands)
    aggregate_value_impact: Dict[str, float]        # net revenue, margin $, etc.
    value_at_risk_if_not_executed: Dict[str, float] # Cost of inaction per KPI
    
    # Portfolio Verification
    root_cause_coverage: Dict[str, CoverageAssessment]
    # For each DA-identified driver: {covered_by: [sol_ids], gaps: [], redundancy: []}
    feasibility_check: FeasibilityReport
    # Constraint violations, timeline conflicts, resource conflicts
    
    # Audit & Transparency
    audit_log: List[str]                            # Analysis steps, decisions
    methodology_notes: str                          # Explain assumptions, approximations
    
    # HITL (human-in-the-loop) fields
    human_action_required: bool = False
    human_action_type: Optional[str] = None         # "decision" | "review" | "none"
    human_action_context: Optional[Dict] = None
```

---

## Technical Approach

### Conflict Detection Logic

**Input:** Two solutions S1, S2 with `target_kpi_id`.

**Algorithm:**
1. Look up both KPIs in causal map
2. Find edges connecting them: `causal_map.get_path(kpi_1, kpi_2)`
3. If path exists with `interaction_strength` > threshold:
   - Fetch S1 `impact_estimate`, S2 `impact_estimate`
   - Apply interaction penalty: `net_impact = impact_1 + impact_2 - (interaction_strength * avg(impact_1, impact_2))`
   - If net impact < sum of individual impacts, flag as conflict
4. Output conflict object with mechanism, severity, net reduction %

### Sequencing Algorithm

**Build Execution DAG:**
- Nodes: solutions
- Edges: prerequisite dependencies (S1 → S2 means S1 must complete before S2 starts)
- Topological sort to ensure no circular deps

**Assign Phases:**
- Phase 1: No dependencies (execute immediately)
- Phase 2: Depends on Phase 1 only (start after Phase 1 checkpoint)
- Phase N: Depends on Phase N-1 or earlier

**Optimize for:** Time-to-value + interaction benefit + risk management
- Co-locate non-interacting solutions in same phase (parallel execution)
- Sequence dependent solutions (do prerequisite first)
- Move de-risking solutions to early phases

### Strategic Alignment Scoring

**Formula:**
```
alignment_score = Σ(strategy_weight[dim] * solution_score[dim]) / Σ(strategy_weight[dim])

Where solution_score[dim] ∈ [-1, 1]:
  +1 = Strongly improves this dimension
   0 = Neutral
  -1 = Significantly degrades this dimension
```

**Dimensions:** growth, margin, efficiency (from corporate strategy profile)

**Assessment:** Extract from SF solution narratives + DA context (LLM-assisted analysis)

### KPI Trajectory Forecasting

**Baseline (no portfolio):**
- Fetch historical KPI data (trend, seasonality)
- Project forward using LOESS / exponential smoothing

**Portfolio Impact:**
- For each solution: apply `impact_estimate` to baseline trajectory
- Sequence solutions (Phase 1 hits baseline at week 4, Phase 2 at week 8, etc.)
- Layer interaction effects (if solution B depends on solution A executing)

**Output:** Time-series projection with confidence intervals (accounting for interaction uncertainty)

---

## Integration Points

- **Data Governance Agent:** Causal KPI map, business glossary
- **Value Assurance Agent:** Active solution portfolio, approval status
- **Solution Finder Agent:** Solution details (`impact_estimate`, prerequisites)
- **Deep Analysis Agent:** Root cause drivers, dimensional breakdown
- **Principal Context Agent:** Strategy statement, decision style

---

## Not in Scope (Phase 1)

- Real-time workflow execution monitoring
- Cost/resource constraint optimization (budget allocation, staffing)
- Machine learning ensemble conflict prediction
- Predictive outcome measurement (will actually achieve estimated impact?)

These may be prioritized in Phase 4+.

---

## Change Log

- **2026-05-20 (Initial Design):** PRD created. Established Layer 3 portfolio optimization role, five core capabilities (conflict detection, strategic alignment, sequencing, trajectory forecasting, portfolio verification). Input/output models defined. Integration points scoped. Status: Planned for Phase 3 (2028).

---

## Acceptance Criteria (Upon Implementation)

1. Agent successfully detects conflicts between solutions via causal map lookups.
2. Strategic alignment scoring correlates with principal's declared priorities.
3. Sequencing recommendations respect causal dependencies and optimize for time-to-value.
4. KPI trajectory forecasts account for baseline trend and interaction effects.
5. Portfolio verification surfaces gaps and redundancies in solution coverage.
6. All outputs are auditable with full methodology documentation.
7. Agent complies with A2A protocol, A9 registry patterns, and Pydantic model validation.
