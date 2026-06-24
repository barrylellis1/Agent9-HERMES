# A9_Business_Optimization_Agent PRD

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2026-06-01
Status: Multi-phase: Phase A near-term, Phase B medium-term, Phase C 2028+
-->

## Overview

**Purpose:** Orchestrate portfolio-level KPI optimization by reasoning across simultaneous interventions, detecting causal conflicts between solutions, and recommending sequencing and prioritization aligned with corporate strategy. Phase A establishes the business objectives layer; Phase B adds autonomous portfolio optimization; Phase C enables continuous objective pursuit with full autonomy.

**Agent Type:** Strategic Portfolio Agent  
**Version:** 0.2 (Strategic Expansion)

The Business Optimization Agent operates at Layer 3 (Portfolio Optimization) of Decision Studio's analytical intelligence framework. Whereas Situation Awareness (Layer 1) detects anomalies and Deep Analysis (Layer 2) provides statistical rigor through Kepner-Tregoe variance analysis, the Business Optimization Agent reasons about the portfolio of simultaneous interventions across all active KPIs and recommends constrained optimization that maximizes aggregate strategic value. At full realization, the agent becomes the outer loop that wraps the inner loop (SA → DA → SF → VA), ensuring the system works toward declared Business Objectives continuously.

---

## Executive Summary

The Business Optimization Agent is Decision Studio's outer loop. The existing SA→DA→SF→VA pipeline is the inner loop — it detects situations, diagnoses root causes, recommends solutions, and measures outcomes. The Business Optimization Agent wraps that inner loop with goal-directed execution: principals declare Business Objectives, the system maps those objectives to KPI drivers, autonomously pursues them through the inner loop, tracks composite objective progress, and produces a living Strategic Performance Summary.

At full realization, the system software-displaces the strategic consulting engagement: a CFO or CEO declares "improve EBITDA margin from 12% to 15% by Q4 2026" and the system works toward that objective continuously — monitoring, diagnosing, sequencing solutions, tracking outcomes — escalating to humans only at decision points that exceed its authority.

**Why this matters:** The CFO currently runs manual scenario analysis and hires consultants to diagnose why KPIs moved. The BO Agent eliminates manual analysis for routine variations, and the consultant's work becomes continuous and autonomous.

---

## Market Positioning

### What the Business Optimization Agent Displaces

The inner loop competes with BI tools and junior FP&A analysts.

The outer loop competes with strategy consulting engagements — McKinsey, BCG, Bain charge $500K–$3M per engagement to do what the BO Agent does continuously. They do it manually, once, for 12–18 weeks. The BO Agent does it continuously, autonomously, and adjusts as conditions change.

### Competitive Landscape

| Competitor | What they do | Gap vs. BO Agent |
|---|---|---|
| Anaplan / Workday Adaptive / Oracle EPM | Budgeting, forecasting, scenario modeling | No autonomous diagnosis, no solution recommendation, no outcome attribution — glorified spreadsheets with workflow |
| Cascade / Betterworks / Workboard | OKR tracking | No AI, no analytics — track whether targets are hit but not why they were missed or what to do |
| SAP Joule | NL query over SAP data | Root cause analysis is roadmap, not GA; no solution recommendation, no DiD attribution |
| McKinsey / BCG / Bain | Full strategy engagement | Expensive, one-time, human-dependent, not continuous |
| **No one** | Continuous autonomous objective pursuit with measurable outcome tracking | **This is the gap** |

### The Private Equity Portfolio Angle (Highest-Value Go-to-Market)

A PE firm with 20 portfolio companies runs the same value creation playbook on every one: EBITDA margin improvement, working capital optimisation, revenue growth, cost reduction. They hire the same consultants per company ($200K–$600K per assessment, 12 weeks each).

The BO Agent deploys the PE firm's standard value creation framework as a template, runs autonomous assessments across all portfolio companies simultaneously, and produces a portfolio dashboard: which companies are on plan, which are at risk, where the playbook is working. It flags which companies actually need consultant intervention vs. which are executing autonomously.

This is a platform sale: one PE firm with 20 portfolio companies = 20 deployments under one contract. Replaces $4M/year in assessment fees with a platform subscription.

**Market size:**
- Global strategy consulting market: ~$40B annually
- Software capturing 1% = ~$400M ARR opportunity at enterprise scale
- Mid-market entry (200,000+ companies, $20K–$200K/year SaaS): $500M–$1B ARR at 1,000 clients

---

## Strategic Context

**Three-Layer Analytical Intelligence:**

| Layer | Agent | Function |
|-------|-------|----------|
| **Layer 1 — Detection** | SA Agent | Identify KPI breaches, anomalies, opportunities |
| **Layer 2 — Diagnosis** | DA Agent | Structured IS/IS NOT variance analysis; dimensional drivers; confidence scoring |
| **Layer 3 — Portfolio Optimization** | **BO Agent (this)** | Conflict detection, sequencing, strategic alignment, aggregate impact forecasting |

### Key ICP Stakeholders

| Buyer | What they care about | When they engage |
|---|---|---|
| **CFO / VP FP&A** (inner loop buyer) | Why KPIs moved; trustworthy attribution | Phase A onwards |
| **CEO / Executive team** | Is the company on track to hit declared strategic objectives? | Phase B onwards |
| **COO** | Are operational initiatives moving the right levers? | Phase B onwards |
| **PE Operating Partner** | Are portfolio companies executing their value creation plans? | Phase B/C — platform sale |
| **Strategy / Transformation Officer** | Which of our 12 transformation initiatives are actually working? | Phase C |
| **Board / Audit Committee** | Objective evidence that management is executing against plan | Phase C |

---

## Architectural Role — Outer Loop

### Two-Loop Architecture

```
OUTER LOOP (Business Optimization Agent)
    Business Objectives declared by principal
        ↓
    Objective → KPI driver mapping (weighted)
        ↓
    Objective-weighted monitoring prioritisation
        ↓
    Progress tracking: composite objective health score
        ↓
    Strategic Performance Summary (living document)
        ↓
    Escalate to human at decisions exceeding authority
        ↕
INNER LOOP (SA → DA → MA → SF → VA)
    Detects KPI situations
    Diagnoses root causes
    Recommends solutions
    Tracks outcomes
```

The inner loop processes individual KPI situations. The outer loop steers the inner loop toward declared objectives, aggregates outcomes into objective progress, and ensures the system is working on the right things — not just the most recently breached KPI.

**The inner loop is already built.** The BO Agent adds the steering layer above it. No refactor of the inner loop is required. The architecture is additive.

### Trust Curve and Phasing Rationale

Full autonomy is a trust and readiness question, not a technical one. A mid-market CFO trusting AI-generated situation cards for the first time is not ready to hand over "optimise my enterprise performance" to an autonomous system. Trust is earned incrementally:

| Stage | Trust level | What the system does autonomously |
|---|---|---|
| Months 1–3 | Situation detection | SA flags KPI breaches |
| Months 3–6 | Diagnosis | DA explains root causes |
| Months 6–12 | Recommendation | SF generates solutions, human approves |
| Months 12–18 | Outcome measurement | VA confirms solution worked |
| Months 18+ | Objective pursuit | BO Agent prioritises and sequences autonomously within declared objectives |

This is why the BO Agent is phased: Phase A and B add the objective layer without requiring autonomous decision-making the principal doesn't yet trust. Phase C extends autonomy as that trust is demonstrated.

---

## Functional Requirements

### Phase A Capabilities — Business Objectives Layer (Near-term)

**1. Business Objectives Registry**

Establish business objectives as a first-class registry entity. Principals declare strategic goals with explicit targets and dates; the system maps them to KPI drivers.

- **Registry Model:** `business_objectives` table in Supabase with fields:
  - `id` (natural, semantic ID: "ebitda_margin_improvement_2026")
  - `client_id` (mandatory tenant key)
  - `name` (e.g., "EBITDA Margin Improvement")
  - `description` (narrative)
  - `owner` (Principal ID)
  - `target_value` (numeric: e.g., 15.0 for 15%)
  - `baseline_value` (starting point: e.g., 12.0)
  - `target_date` (deadline as ISO date)
  - `status` (ACTIVE, PAUSED, COMPLETED, ABANDONED)
  - `created_at`, `updated_at`

- **CRUD API:** Registry endpoints for create, list (with client_id filter), get, update, delete. Delete requires ownership validation (cannot delete a different client's objective).

- **UI:** Registry Explorer panel for objectives (alongside KPIs, Principals, Data Products). Principals can declare, edit, and track objectives. Strict multi-tenant isolation via client_id.

**2. Objective → KPI Driver Mapping**

Link objectives to the KPIs that drive them, with configurable weights and direction.

- **Join Table:** `objective_kpi_drivers` with:
  - `objective_id`, `kpi_id` (composite FK)
  - `weight` (0–1, must sum to 1.0 across all drivers for an objective)
  - `contribution_direction` (HIGHER_IS_BETTER or LOWER_IS_BETTER)
  - `client_id` (for multi-tenant consistency)

- **Configuration:** Registry Explorer UI allows principals to:
  - Select an objective
  - Add KPI drivers one at a time
  - Set weight for each driver
  - System validates: weights sum to 1.0 before save

- **Impact:** Enables objective-weighted monitoring (next capability).

**3. Objective-Weighted SA Monitoring**

SA assessment incorporates objective driver weights when computing situation severity. A KPI breach that is a high-weight driver of an active objective scores higher severity and is surfaced first in the assessment results.

- **Algorithm:** For each active objective per principal:
  - Fetch all linked KPI drivers with weights
  - For each KPI in the assessment: if it matches a driver, multiply breach severity by weight
  - Sort situations by weighted severity; return highest first
  
- **Output:** SA assessment results include `objective_context` array showing which objectives are affected by which situation cards.

- **Example:** CFO declares "Improve EBITDA Margin (weight: 0.7)" and "Increase Cash Flow (weight: 0.3)". A breach in Gross Margin KPI is weighted 0.7 and floats to the top. A breach in AR Days Outstanding is weighted 0.3 and ranks lower.

**4. Objective Health Score**

Compute a composite health indicator per objective at each assessment run.

- **Formula:**
  ```
  health_score = Σ(weight_i × kpi_status_i) for all drivers
  
  where kpi_status_i ∈ [0, 1]:
    0.0 = KPI in breach (critical)
    0.5 = KPI at warning level
    1.0 = KPI on-track or ahead
  ```

- **Health Status Label:**
  - 0.0–0.25: CRITICAL (red)
  - 0.25–0.50: AT_RISK (orange)
  - 0.50–0.75: ON_TRACK (yellow)
  - 0.75–1.0: AHEAD (green)

- **Computation:** SA agent calculates and stores in assessment output for each objective. Persisted to Supabase `objective_assessments` table for trend tracking.

- **UI:** Objectives dashboard displays current health score, target date, days remaining at current trajectory, and linked KPI statuses.

**5. Strategic Performance Summary in PIB**

New section in Presidio Intelligence Briefing (PIB) summarizing objective progress.

- **Contents:** For each active objective:
  - Objective name, target, target date
  - Current composite health score
  - Health status (CRITICAL / AT_RISK / ON_TRACK / AHEAD)
  - Estimated days to target at current trajectory (or "off-track" warning)
  - Count of active solutions contributing to this objective
  - Brief narrative: "EBITDA Margin Improvement — 60 days in, tracking at 42% of target. 2 solutions active, 1 on-plan."

- **Placement:** New "Strategic Objectives" section in PIB template (after "Executive Summary", before "Situation Dashboard").

- **Framing:** Shifts the briefing narrative from KPI-centric ("Gross Margin breached") to objective-centric ("EBITDA improvement 60% of the way to target").

**6. Portfolio Objectives View**

New UI tab in the main dashboard: objective-centric rather than KPI-centric.

- **Display:**
  - List of all active objectives for the principal's client
  - For each: health score, target, progress bar, linked KPIs, active solutions count
  - Drill-down: click objective → see linked KPI statuses, active solutions affecting it, and trend

- **Comparison to KPI Dashboard:**
  - Old view: KPIs as rows, statuses as cells, objectives implicit
  - New view: Objectives as rows, composite health as cells, KPI drivers shown on drill-down

- **Navigation:** "Objectives" tab in main nav; "KPIs" tab remains (two views, same data, different aggregation).

---

### Phase B/C Capabilities — Portfolio Optimisation

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
| **Business Objectives** | Objectives Registry | Declared objectives, KPI driver links, weights | Objective health scoring, monitoring prioritisation |

### Input Model

```python
class BusinessOptimizationInput(A9AgentBaseModel):
    """Portfolio optimization request."""
    client_id: str                                  # Tenant identifier
    principal_id: str                               # Principal making the request
    active_solutions: List[ApprovedSolution]        # All pending/approved solutions
    deep_analysis_context: Dict[str, Any]           # DA outputs for all active KPIs
    causal_map: Optional[CausalKPIMap] = None       # DGA KPI relationships
    corporate_strategy: CorporateStrategyProfile    # Growth/Margin/Efficiency weighting
    principal_context: PrincipalContext             # Decision style, role, priorities
    business_objectives: List[BusinessObjective] = []  # Declared objectives for this principal
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
    
    # Objective Progress (Phase A+)
    objective_health_scores: Dict[str, ObjectiveHealth] = {}
    # Per objective: {score, status, days_to_target, contributing_solutions}
    
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

### Objective Health Score Calculation

**Formula:**
```
health_score = Σ(weight_i × kpi_status_i) for all drivers of objective

where:
  weight_i ∈ [0, 1] (from objective_kpi_drivers join table)
  kpi_status_i ∈ [0, 1] (assessed at each SA run):
    0.0 = KPI in breach
    0.5 = KPI at warning threshold
    1.0 = KPI on-track or ahead
```

**Status Mapping:**

```
kpi_status from SA assessment:
  CRITICAL → 0.0
  AT_RISK  → 0.5
  ON_TRACK → 1.0
  AHEAD    → 1.0 (optionally 1.0+ for overachievement)
```

**Days to Target:**

```
if health_score == 1.0:
  days_to_target = 0 (objective is hit)
else if trend_slope < 0 (regressing):
  days_to_target = "off-track" (warn principal)
else:
  days_to_target = (1.0 - health_score) / trend_slope (linear projection)
```

---

## Integration Points

- **Data Governance Agent:** Causal KPI map, business glossary
- **Value Assurance Agent:** Active solution portfolio, approval status
- **Solution Finder Agent:** Solution details (`impact_estimate`, prerequisites)
- **Deep Analysis Agent:** Root cause drivers, dimensional breakdown
- **Principal Context Agent:** Strategy statement, decision style
- **Situation Awareness Agent:** KPI assessments, objective-weighted monitoring
- **Registry Providers:** Business objectives, objective-KPI driver mappings, KPI definitions

---

## Phased Implementation Summary

| Phase | Scope | Timeline | Trust prerequisite |
|---|---|---|---|
| **Phase A** | Business Objectives registry, objective→KPI mapping, objective health score, Strategic Performance Summary in PIB, Portfolio Objectives view | Phase 12C–12D in dev plan | Inner loop trust established (6–12 months post-pilot) |
| **Phase B** | Cross-intervention conflict detection, strategic alignment scoring, sequencing recommendations | Phase 2 (2027) in dev plan | Objective-layer trust established; CFO comfortable with objective health scores |
| **Phase C** | Fully autonomous objective pursuit, KPI trajectory forecasting, living Business Plan generation, portfolio-level optimisation | Phase 3 (2028) in dev plan | Multi-cycle trust; principals comfortable delegating objective prioritisation |

**PE Portfolio Platform (Phase B/C):** The portfolio dashboard and PE go-to-market angle requires Phase A objectives layer to be live and validated with at least one client. PE platform sale targets Month 18–30.

---

## Not in Scope (Phase 1/A)

- Real-time workflow execution monitoring
- Cost/resource constraint optimization (budget allocation, staffing)
- Machine learning ensemble conflict prediction
- Predictive outcome measurement (will actually achieve estimated impact?)

These may be prioritized in Phase 4+.

---

## Change Log

- **2026-06-01 (v0.2 — Strategic Expansion):** Substantially expanded with outer loop architecture, market positioning (software displacing strategy consulting, PE portfolio angle), expanded buyer personas (CEO, COO, PE Operating Partner, Board), trust curve and phasing rationale, Phase A capabilities (Business Objectives registry, objective health score, Strategic Performance Summary). Existing Phase B/C portfolio optimisation capabilities retained. Status updated to multi-phase. Phased Implementation Summary added.

- **2026-05-20 (Initial Design):** PRD created. Established Layer 3 portfolio optimization role, five core capabilities (conflict detection, strategic alignment, sequencing, trajectory forecasting, portfolio verification). Input/output models defined. Integration points scoped. Status: Planned for Phase 3 (2028).

---

## Acceptance Criteria (Upon Implementation)

### Phase A Acceptance Criteria

1. Business Objectives registry supports full CRUD with strict client_id isolation.
2. Objective-KPI driver links enforce weight sum validation (weights must sum to 1.0 per objective).
3. SA agent successfully weights situation severity by objective driver importance; higher-weight breaches surface first.
4. Objective health score formula correctly aggregates driver KPI statuses weighted by objective weights.
5. PIB template includes "Strategic Objectives" section with health scores, target dates, and days-to-target calculations.
6. Portfolio Objectives dashboard displays all active objectives, health scores, linked KPIs, and drill-down to solutions.
7. Registry Explorer UI supports objective and objective-KPI driver management.

### Phase B/C Acceptance Criteria

1. Agent successfully detects conflicts between solutions via causal map lookups.
2. Strategic alignment scoring correlates with principal's declared priorities.
3. Sequencing recommendations respect causal dependencies and optimize for time-to-value.
4. KPI trajectory forecasts account for baseline trend and interaction effects.
5. Portfolio verification surfaces gaps and redundancies in solution coverage.
6. All outputs are auditable with full methodology documentation.
7. Agent complies with A2A protocol, A9 registry patterns, and Pydantic model validation.

