# A9_Value_Assurance_Agent PRD

<!--
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2026-03-13
-->

## 1. Overview

**Purpose:** The A9_Value_Assurance_Agent closes the insight-to-outcome loop by measuring whether HITL-approved solutions from the Solution Finder Agent actually delivered their predicted KPI impact. It constructs counterfactual baselines using data from SA, DA, and MA to separate intervention-driven recovery from market tailwinds, seasonal normalization, and organic reversion — producing honest, defensible ROI attribution that executives can trust.

**Agent Type:** Outcome Measurement / Accountability Agent
**Version:** 1.0
**Template:** Inherits from A9_Agent_Template

> **COMPLIANCE NOTE:**
> - This agent must ONLY be invoked via the AgentRegistry and orchestrator pattern.
> - Do NOT instantiate directly; always use the async factory method `create_from_registry`.
> - **Usage Example:**
> ```python
> va_agent = await AgentRegistry.get_agent("A9_Value_Assurance_Agent")
> result = await va_agent.evaluate_solution_impact(request)
> ```

**Config Validation:** Uses Pydantic config model (`A9ValueAssuranceAgentConfig`) with `hitl_enabled` field for protocol compliance.

**Logging:** All agent logging and error handling use structured logging via `logging.getLogger(__name__)` (interim; target: `A9_SharedLogger`).

**Registration:** Agent must be created via the async `create_from_registry` method and registered only by the orchestrator/AgentRegistry.

---

## 2. Strategic Context

### Why This Agent Exists

The SA → DA → MA → SF pipeline detects problems, diagnoses root causes, gathers market context, and recommends solutions. But without Value Assurance, the story ends at HITL approval. Executives are left wondering:

- "Did the solution I approved actually work?"
- "How much of the KPI recovery was our doing vs. market tailwinds?"
- "What's the total value Agent9 has delivered this quarter?"
- "What's the cost of the situations I chose NOT to act on?"

**Without VA**, Agent9 is a recommendation engine. **With VA**, Agent9 is an accountability system that proves its own ROI.

### Competitive Differentiation

No competing BI/analytics platform closes this loop with causal attribution:
- **Dashboards** show before/after but can't isolate causation
- **Project management tools** track task completion, not KPI outcomes
- **MBB consultants** deliver recommendations but rarely measure outcomes rigorously
- **Agent9 + VA** detects the problem, recommends the fix, AND proves the fix worked — with honest attribution that separates intervention impact from external factors

### The Cost of Inaction

VA also quantifies the **counterfactual cost of NOT acting** — projecting what would have happened to KPIs if no solution had been implemented. This creates urgency at the HITL decision point and retrospective justification for the investment.

---

## 3. Position in the Pipeline

```
SA: Detect KPI breach
 → DA: Root cause analysis (Is/Is Not, change-point detection)
   → MA: Market context (competitor moves, industry trends)
     → SF: Generate solution options with quantified impact_estimate
       → HITL: Principal approves solution
         → VA: Track → Measure → Attribute → Report  ← THIS AGENT
              ↑                         │
              │    Feedback loops       │
              └─── SA re-monitors ──────┘
                   MA re-analyses market
```

### Agent Dependencies

| Agent | What VA Needs From It |
|-------|----------------------|
| **Solution Finder** | `impact_estimate` (metric, unit, recovery_range {low, high}, basis), approved option details, HITL timestamp |
| **Deep Analysis** | Change-point data, pre-intervention trend, Is/Is Not dimensional breakdown (affected vs. unaffected dimensions) |
| **Market Analysis** | Market signals at time of breach AND at measurement time — to isolate market-driven recovery |
| **Situation Awareness** | Ongoing KPI monitoring data post-implementation, historical baselines, seasonal patterns |
| **Principal Context** | Principal profile for reporting preferences and accountability routing |
| **Data Product Agent** | SQL execution for KPI re-measurement queries |

### HITL Integration Notes (2026-03-18)

**Solution Q&A Engagement Signal (Planned, not yet built):** The approval payload should capture whether the principal completed Q&A before approving. This is tracked as `qa_engagement: bool` — true if the principal sent at least one question via the Decision Workspace before clicking Approve & Track. This engagement signal will be used in future VA analysis to correlate Q&A engagement with solution success rates.

**Multi-initiative Batch Registration (Deferred):** Batch `register_solution` for multiple initiatives from a single briefing is designed but deferred. The current flow registers one solution per approval. When multi-initiative is built, each approved initiative will become a separate VA-tracked solution with its own `impact_estimate` and monitoring window.

---

## 4. Core Capabilities (MVP)

### 4.1 Solution Registration

When the SF HITL approval event fires, VA records the approved solution with all context needed for future measurement:

- **Solution snapshot:** option_title, option_description, expected impact_estimate
- **Baseline snapshot:** KPI value at approval time, pre-intervention trend (from DA change-point)
- **Dimensional context:** affected dimensions (from DA Is/Is Not) — these become the treatment group
- **Unaffected dimensions:** from DA Is/Is Not — these become the control group
- **Market context snapshot:** MA signals at time of breach (for later comparison)
- **Timing:** HITL approval timestamp, estimated time_to_value (from SF option)
- **Persistence:** Supabase `value_assurance_solutions` table (not in-memory)

**Input Model:** `RegisterSolutionRequest` — accepts SF output + DA context + MA context
**Output Model:** `RegisteredSolution` — stored record with generated UUID and measurement schedule

### 4.2 Counterfactual Baseline Construction

The core analytical capability. Constructs a "what would have happened without intervention" baseline using four inputs:

#### 4.2.1 Pre-Intervention Trend Projection

- Uses DA's change-point detection data to identify the trajectory before and after the problem onset
- Projects the post-problem trend forward from the HITL approval date
- Method: linear extrapolation of the post-change-point, pre-intervention slope
- Result: `projected_no_action_value` — where the KPI would be at measurement time without intervention

#### 4.2.2 Control Group Comparison (Difference-in-Differences)

- DA's Is/Is Not analysis identifies affected dimensions (e.g., Region East) and unaffected dimensions (e.g., Region West)
- Unaffected dimensions serve as a natural control group
- If the control group also recovered → some/all recovery is NOT attributable to the solution
- Delta: `control_group_change` — organic recovery observable in unaffected dimensions

#### 4.2.3 Market Factor Adjustment

- MA provides market signals at breach time AND at measurement time
- If the entire industry recovered (e.g., commodity prices dropped), MA quantifies the market-driven portion
- Method: compare company KPI movement to industry benchmark movement
- Delta: `market_driven_recovery` — portion of KPI change driven by external market forces

#### 4.2.4 Seasonal Adjustment

- SA's historical KPI data reveals seasonal patterns
- If measurement spans a known seasonal uptick, that portion is subtracted
- Method: year-over-year comparison for the same period
- Delta: `seasonal_component` — expected KPI movement from seasonal factors alone

#### Counterfactual Formula

```
attributable_impact = actual_kpi_change
                    - control_group_change
                    - market_driven_recovery
                    - seasonal_component

confidence_level = f(control_group_quality, data_volume, time_since_intervention)
```

### 4.3 Impact Evaluation

Compares actual KPI movement against the SF's predicted `impact_estimate.recovery_range`:

| Scenario | Verdict | Meaning |
|----------|---------|---------|
| `attributable_impact >= recovery_range.low` | `VALIDATED` | Solution delivered at or above expected impact |
| `attributable_impact > 0 but < recovery_range.low` | `PARTIAL` | Solution helped but underperformed expectations |
| `attributable_impact <= 0` | `FAILED` | No measurable improvement attributable to the solution |
| Measurement window not yet reached | `MEASURING` | Too early to evaluate; interim tracking active |

**Output Model:** `ImpactEvaluation`
```python
class ImpactEvaluation(BaseModel):
    solution_id: str
    kpi_name: str
    measurement_date: str

    # Raw observation
    baseline_kpi_value: float          # KPI at time of HITL approval
    current_kpi_value: float           # KPI at measurement time
    total_kpi_change: float            # current - baseline

    # Attribution breakdown
    control_group_change: float        # recovery in unaffected dimensions
    market_driven_recovery: float      # industry-wide recovery (from MA)
    seasonal_component: float          # seasonal normalization
    attributable_impact: float         # net impact after adjustments

    # Evaluation
    expected_impact_lower: float       # from SF impact_estimate.recovery_range.low
    expected_impact_upper: float       # from SF impact_estimate.recovery_range.high
    verdict: SolutionVerdict           # VALIDATED | PARTIAL | FAILED | MEASURING
    confidence: ConfidenceLevel        # HIGH | MODERATE | LOW
    confidence_rationale: str          # why this confidence level

    # Context
    attribution_method: str            # "difference_in_differences" | "trend_projection" | "simple_before_after"
    control_group_description: Optional[str]  # e.g., "Region West (unaffected)"
    market_context_summary: Optional[str]     # e.g., "Industry commodity prices -8% in period"

    # Strategy alignment (see Section 4.7)
    strategy_check: StrategyAlignmentCheck   # full drift analysis
    composite_verdict: CompositeVerdict      # two-dimensional verdict (KPI × Strategy)
```

### 4.4 Cost of Inaction

For situations where the principal chose NOT to act (no HITL approval, or solution abandoned), VA projects the ongoing KPI deterioration:

- Uses the same trend projection from 4.2.1
- Calculates: `cost_of_inaction = current_kpi_value - projected_if_acted_value`
- Translates KPI delta to business impact using KPI metadata (e.g., "1pp Gross Margin = $X revenue impact")
- Surfaced in the portfolio dashboard as motivation for future action

**Output Model:** `InactionCostProjection`
```python
class InactionCostProjection(BaseModel):
    situation_id: str
    kpi_name: str
    projection_date: str
    kpi_at_detection: float
    kpi_current: float
    kpi_projected_trend: float          # where it's heading without action
    cumulative_kpi_erosion: float       # total deterioration since detection
    estimated_business_impact: Optional[str]  # e.g., "$1.2M margin loss"
    recommended_action: str             # "Re-evaluate — situation has worsened"
```

### 4.5 Portfolio Dashboard Data

Aggregates across all tracked solutions and unaddressed situations, segmented by strategic alignment:

```python
class ValueAssurancePortfolio(BaseModel):
    # Solutions in flight (all)
    total_tracked_solutions: int
    by_status: Dict[SolutionVerdict, int]   # {VALIDATED: 3, MEASURING: 2, FAILED: 1, ...}
    by_strategy: Dict[StrategyAlignment, int]  # {ALIGNED: 4, DRIFTED: 1, SUPERSEDED: 1}

    # Value delivered (ALIGNED only — the honest number)
    aligned_attributable_value: str          # e.g., "+4.7pp combined margin recovery"
    validated_solutions: List[SolutionSummary]
    failed_solutions: List[SolutionSummary]

    # Drifted (needs executive attention)
    drifted_solutions: List[SolutionSummary]
    drifted_attention_note: Optional[str]    # e.g., "2 solutions need review — priorities shifted"

    # Superseded (archived)
    superseded_solutions: List[SolutionSummary]
    superseded_historical_value: str         # e.g., "$200K recovered (no longer tracked)"

    # Value at risk (ALIGNED situations only)
    unaddressed_aligned_situations: int
    total_projected_erosion: str             # e.g., "$800K margin at risk"
    inaction_costs: List[InactionCostProjection]

    # Meta
    average_attribution_confidence: ConfidenceLevel
    strategy_health: str                     # "Stable" | "Evolving" | "Major shift detected"
    methodology_note: str
```

### 4.7 Strategy Alignment Assessment

KPI attribution alone is insufficient. A solution can be `VALIDATED` on its metric while being strategically irrelevant — because the business pivoted, priorities shifted, or the entire business unit was divested. VA must evaluate solutions on two axes: **KPI impact** (did the number move?) and **strategic fit** (does the number still matter?).

#### 4.7.1 Strategy Snapshot at Registration

When a solution is registered (HITL approval), VA captures a point-in-time snapshot of the strategic context that justified the solution:

```python
class StrategySnapshot(BaseModel):
    """Strategic context at the time the solution was approved."""
    principal_priorities: List[str]          # from PrincipalProfile.priorities
    principal_role: str                      # from PrincipalProfile.role
    business_process_domain: str             # from Business Process registry
    data_product_id: str                     # which data product the KPI belongs to
    kpi_threshold_at_approval: float         # SA threshold at approval time
    key_assumptions: List[str]               # from SF problem_reframe.key_assumptions
    business_context_name: str               # e.g., "Summit Lubricants" or "Bicycle Retail"
    strategic_rationale: Optional[str]       # why this solution was chosen (from HITL context)
    captured_at: str                         # ISO timestamp
```

This snapshot is stored in the `strategy_snapshot` JSONB column on `value_assurance_solutions` and becomes the baseline against which drift is measured.

#### 4.7.2 Strategy Drift Detection

At each measurement evaluation, VA re-queries the live registry state and diffs against the snapshot:

```python
class StrategyAlignmentCheck(BaseModel):
    """Compares current strategic context against the approval-time snapshot."""

    # Priority drift
    original_priorities: List[str]
    current_priorities: List[str]
    priority_drift: bool                     # did relevant priorities change?
    priority_overlap: float                  # % of original priorities still present (0.0–1.0)

    # Operational continuity
    kpi_still_monitored: bool                # is SA still tracking this KPI?
    threshold_changed: bool                  # did the target threshold move?
    current_threshold: Optional[float]       # new threshold if changed
    business_process_active: bool            # is the domain still operational?
    data_product_active: bool                # is the data product still registered?

    # Accountability continuity
    principal_still_accountable: bool        # same owner?
    current_principal_id: Optional[str]      # new owner if changed

    # Verdict
    alignment_verdict: StrategyAlignment     # ALIGNED | DRIFTED | SUPERSEDED
    drift_factors: List[str]                 # list of what changed
    drift_summary: Optional[str]            # LLM narrative of what changed and implications
```

**Alignment verdict logic:**

| Condition | Verdict | Meaning |
|-----------|---------|---------|
| All checks pass, priorities overlap >= 0.7 | `ALIGNED` | Strategy is consistent — KPI verdict is fully meaningful |
| Some priorities shifted OR threshold moved OR principal changed | `DRIFTED` | Strategy evolved — KPI verdict is valid but context has changed |
| Business process inactive OR data product deregistered OR priority overlap < 0.3 | `SUPERSEDED` | Strategic frame no longer applies — KPI verdict is informational only |

#### 4.7.3 Two-Dimensional Verdict Matrix

VA produces a composite verdict combining KPI impact and strategic alignment:

| | Strategy: ALIGNED | Strategy: DRIFTED | Strategy: SUPERSEDED |
|---|---|---|---|
| **KPI: VALIDATED** | **Full success** — solution worked, still matters. Count in ROI totals. | **Contextual success** — solution worked but priorities shifted. Flag for executive review. | **Historical success** — KPI improved but goal is no longer relevant. Exclude from active ROI. |
| **KPI: PARTIAL** | **Underperformed** — still strategically important. Consider follow-up SA → DA cycle. | **Mixed signal** — underperformed AND priorities shifted. Executive decides whether to continue tracking. | **Close out** — partial impact on a superseded goal. Archive. |
| **KPI: FAILED** | **Action needed** — didn't work on a KPI that still matters. Re-trigger SA → DA. | **Acceptable loss** — didn't work, and priority shifted. Document learnings, close. | **Irrelevant** — no impact on a goal that no longer exists. Archive with no further action. |

```python
class CompositeVerdict(BaseModel):
    """Two-dimensional evaluation: KPI impact × strategic alignment."""
    kpi_verdict: SolutionVerdict             # VALIDATED | PARTIAL | FAILED | MEASURING
    strategy_verdict: StrategyAlignment      # ALIGNED | DRIFTED | SUPERSEDED
    composite_label: str                     # e.g., "Full success", "Acceptable loss"
    include_in_roi_totals: bool              # only True for ALIGNED solutions
    recommended_action: str                  # e.g., "Count in portfolio ROI" or "Archive — business unit divested"
    executive_attention_required: bool       # True for DRIFTED cases that need judgment
```

#### 4.7.4 Strategy-Aware Portfolio Aggregation

The portfolio dashboard filters by strategic alignment:

- **Active ROI totals** count only `ALIGNED` solutions — this is the honest number
- **Drifted solutions** shown separately with flag: "Executive review needed — strategic context has changed"
- **Superseded solutions** archived — shown only in historical view
- **Cost of inaction** calculated only for strategically aligned situations — don't alarm executives about KPIs they've deprioritized

```python
class StrategyAwarePortfolio(BaseModel):
    # Strategically aligned (the numbers that matter)
    aligned_solutions: PortfolioSegment      # active ROI tracking
    aligned_value_recovered: str             # e.g., "+$1.2M"
    aligned_value_at_risk: str               # from inaction costs on aligned situations

    # Strategically drifted (needs executive judgment)
    drifted_solutions: PortfolioSegment
    drifted_attention_items: List[DriftAttentionItem]  # solutions needing review

    # Strategically superseded (historical record)
    superseded_solutions: PortfolioSegment
    superseded_note: str                     # e.g., "3 solutions archived due to portfolio changes"

    # Meta
    strategy_health: str                     # "Stable" | "Evolving" | "Major shift detected"
    last_strategy_check: str                 # ISO timestamp
```

#### 4.7.5 Strategy Drift as a Signal

When VA detects significant strategy drift across multiple solutions, this is itself a signal worth surfacing:

- If 3+ solutions drift simultaneously → likely an org-wide strategic shift
- VA can surface: "Strategy shift detected — 3 active solutions are no longer aligned with current priorities. Portfolio rebalancing may be needed."
- This gives executives a **meta-view**: not just "are solutions working?" but "are we working on the right things?"

#### 4.7.6 Data Sources for Strategy Checks

All required data already exists in the system:

| Check | Data Source | Already Built? |
|-------|-------------|----------------|
| Principal priorities | `PrincipalProfile.priorities` via Principal Context Agent | Yes |
| Principal accountability | `PrincipalProfile.principal_id` via PC Agent | Yes |
| Business process status | Business Process registry via Registry Factory | Yes |
| KPI thresholds | KPI registry via Registry Factory | Yes |
| KPI monitoring status | SA agent's active KPI list | Yes |
| Data product status | Data Product registry via Registry Factory | Yes |
| Key assumptions | SF `problem_reframe.key_assumptions` in output | Yes |
| Business context | `business_context.yaml` files via `_DP_CONTEXT_MAP` | Yes |

**New work required:** snapshot capture at registration, diff logic at evaluation, composite verdict calculation, and LLM drift narrative generation.

---

### 4.8 LLM-Powered Narrative Generation

Uses A9_LLM_Service_Agent to generate executive-ready narratives from the quantitative attribution data and strategy alignment context:

- **Solution impact summary:** "The supplier renegotiation delivered +2.2pp Gross Margin recovery. Of the total +3.9pp recovery observed, 1.2pp was attributable to falling commodity prices (industry-wide) and 0.5pp to seasonal Q2 normalization. Confidence: MODERATE, based on Region West as control group."
- **Strategy-aware summary:** "The supplier renegotiation delivered +2.3pp Gross Margin recovery (VALIDATED). However, the Board approved product line divestiture on 2026-04-15 — this business unit is no longer in the strategic plan. Recommendation: Archive this solution. Capture the renegotiation playbook for application to remaining portfolio."
- **Portfolio summary:** "Agent9 has validated $1.2M in recovered margin this quarter across 3 strategically aligned solutions. One validated solution ($200K) is excluded from active ROI due to business unit divestiture. Two aligned situations remain unaddressed with $800K projected erosion."
- **Strategy drift alert:** "Strategy shift detected: 3 of 6 tracked solutions are no longer aligned with current CFO priorities (shifted from cost reduction to revenue growth in Q1 2026). Consider portfolio rebalancing."
- **Model routing:** Narrative generation → `claude-haiku-4-5-20251001` (cost-efficient, structured output)

---

## 5. Entrypoints (Protocol Methods)

| Method | Trigger | Input | Output |
|--------|---------|-------|--------|
| `register_solution` | SF HITL approval event | `RegisterSolutionRequest` | `RegisteredSolution` (includes `StrategySnapshot`) |
| `evaluate_solution_impact` | Scheduled or on-demand | `EvaluateImpactRequest` | `ImpactEvaluation` (includes `StrategyAlignmentCheck` + `CompositeVerdict`) |
| `check_strategy_alignment` | On-demand or as part of evaluate | `StrategyCheckRequest` | `StrategyAlignmentCheck` |
| `project_inaction_cost` | On-demand (portfolio view) | `InactionCostRequest` | `InactionCostProjection` (only for ALIGNED situations) |
| `get_portfolio_summary` | On-demand (dashboard) | `PortfolioRequest` | `StrategyAwarePortfolio` |
| `generate_narrative` | After evaluation | `NarrativeRequest` | `NarrativeResponse` (strategy-aware) |

All entrypoints accept and return Pydantic models (A2A protocol compliance).

---

## 6. Data Persistence (Supabase)

### 6.1 Tables

**`value_assurance_solutions`** — One row per HITL-approved solution:

| Column | Type | Source |
|--------|------|--------|
| `id` | UUID (PK) | Generated |
| `session_id` | TEXT | SF session |
| `situation_id` | TEXT | SA situation card |
| `principal_id` | TEXT | HITL principal |
| `kpi_id` | TEXT | KPI registry |
| `kpi_name` | TEXT | KPI registry |
| `data_product_id` | TEXT | KPI registry → data product |
| `option_title` | TEXT | SF approved option |
| `option_description` | TEXT | SF approved option |
| `expected_impact_lower` | FLOAT | SF impact_estimate.recovery_range.low |
| `expected_impact_upper` | FLOAT | SF impact_estimate.recovery_range.high |
| `expected_impact_unit` | TEXT | SF impact_estimate.unit |
| `expected_impact_metric` | TEXT | SF impact_estimate.metric |
| `expected_impact_basis` | TEXT | SF impact_estimate.basis |
| `baseline_kpi_value` | FLOAT | KPI value at approval time |
| `time_to_value` | TEXT | SF option time_to_value |
| `affected_dimensions` | JSONB | DA Is/Is Not — treatment group |
| `unaffected_dimensions` | JSONB | DA Is/Is Not — control group |
| `market_context_at_breach` | JSONB | MA signals at detection time |
| `pre_intervention_trend` | JSONB | DA change-point slope data |
| `status` | TEXT | ACCEPTED → MEASURING → VALIDATED/PARTIAL/FAILED/ABANDONED |
| `accepted_at` | TIMESTAMPTZ | HITL approval time |
| `measurement_start` | TIMESTAMPTZ | When measurement window opens |
| `resolved_at` | TIMESTAMPTZ | When verdict is rendered |
| `actual_impact` | FLOAT | Measured attributable impact |
| `verdict` | TEXT | VALIDATED/PARTIAL/FAILED |
| `confidence` | TEXT | HIGH/MODERATE/LOW |
| `attribution_breakdown` | JSONB | Full breakdown (control, market, seasonal, attributable) |
| `strategy_snapshot` | JSONB | StrategySnapshot at approval time (priorities, assumptions, thresholds) |
| `strategy_alignment` | TEXT | ALIGNED / DRIFTED / SUPERSEDED (updated at each evaluation) |
| `strategy_drift_factors` | JSONB | List of what changed since approval |
| `composite_verdict` | TEXT | Two-dimensional label (e.g., "Full success", "Acceptable loss") |
| `include_in_roi` | BOOLEAN | Whether to count in active portfolio ROI totals |
| `notes` | TEXT | Free-form notes |
| `created_at` | TIMESTAMPTZ | Row creation |
| `updated_at` | TIMESTAMPTZ | Last update |

**`value_assurance_evaluations`** — One row per measurement check (multiple per solution):

| Column | Type | Purpose |
|--------|------|---------|
| `id` | UUID (PK) | Generated |
| `solution_id` | UUID (FK) | References value_assurance_solutions |
| `measurement_date` | TIMESTAMPTZ | When this check was performed |
| `current_kpi_value` | FLOAT | KPI value at check time |
| `total_kpi_change` | FLOAT | current - baseline |
| `control_group_change` | FLOAT | Recovery in unaffected dimensions |
| `market_driven_recovery` | FLOAT | Industry-wide recovery |
| `seasonal_component` | FLOAT | Seasonal normalization |
| `attributable_impact` | FLOAT | Net after adjustments |
| `verdict` | TEXT | Verdict at this point in time |
| `confidence` | TEXT | Confidence at this point |
| `strategy_alignment` | TEXT | ALIGNED / DRIFTED / SUPERSEDED at this check |
| `strategy_check_data` | JSONB | Full StrategyAlignmentCheck for audit |
| `composite_verdict` | TEXT | Two-dimensional verdict label |
| `narrative` | TEXT | LLM-generated summary (strategy-aware) |
| `raw_data` | JSONB | Full measurement data for audit |

### 6.2 Migration Strategy

- Phase 1 (MVP): Supabase tables via migration script
- Backward compatibility: existing in-memory `value_assurance.py` API routes continue to work but delegate to the agent
- The 5 existing API endpoints are refactored to call the VA agent instead of managing an in-memory dict

---

## 7. Measurement Methodology — Confidence Scoring

Attribution confidence is scored based on the quality of available evidence:

| Factor | HIGH | MODERATE | LOW |
|--------|------|----------|-----|
| **Control group** | Unaffected dimensions available (DA Is/Is Not) | Partial control (some dimensions ambiguous) | No control group; before/after only |
| **Data volume** | 8+ weeks post-intervention data | 4-8 weeks | < 4 weeks |
| **Market data** | MA re-analysis at measurement time | MA signals at breach time only | No market data |
| **Seasonal data** | 2+ years historical for seasonal adjustment | 1 year | No seasonal baseline |
| **Confounders** | No other known initiatives on same KPI | Minor confounders documented | Multiple simultaneous interventions |

**Confidence algorithm:**
```python
def calculate_confidence(factors: Dict[str, str]) -> ConfidenceLevel:
    scores = {"high": 3, "moderate": 2, "low": 1}
    avg = mean([scores[f] for f in factors.values()])
    if avg >= 2.5:
        return ConfidenceLevel.HIGH
    elif avg >= 1.5:
        return ConfidenceLevel.MODERATE
    return ConfidenceLevel.LOW
```

**Transparency requirement:** Every evaluation MUST include `confidence_rationale` explaining why the confidence level was assigned, referencing specific factors. Executives must understand the limits of the attribution.

---

## 8. Integration with Existing API Routes

The existing 5 endpoints at `/api/v1/value-assurance/` are preserved and extended:

| Existing Endpoint | Change |
|--------------------|--------|
| `POST /solutions` | Delegates to `va_agent.register_solution()` — adds DA/MA context capture |
| `GET /solutions` | Delegates to `va_agent.get_portfolio_summary()` |
| `GET /solutions/{id}` | Returns enriched `RegisteredSolution` with attribution data |
| `PATCH /solutions/{id}` | Delegates to agent for status transitions |
| `POST /solutions/{id}/check` | Delegates to `va_agent.evaluate_solution_impact()` — adds counterfactual |

**New endpoints:**

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/value-assurance/portfolio` | Aggregated portfolio dashboard data |
| `POST /api/v1/value-assurance/solutions/{id}/narrative` | Generate LLM narrative for a solution |
| `GET /api/v1/value-assurance/inaction-costs` | List all unaddressed situations with projected costs |
| `POST /api/v1/value-assurance/inaction-costs/{situation_id}` | Calculate inaction cost for specific situation |

---

## 9. UI Requirements (Decision Studio)

### 9.1 Value Assurance Panel (new tab or section in main workflow)

**After HITL approval:**
- Solution card transitions from "Approved" to "Tracking" state
- Shows: expected impact range, measurement window countdown, interim KPI trend

**At measurement time:**
- Attribution breakdown visualization (stacked bar or waterfall chart):
  - Green: attributable to solution
  - Blue: market-driven recovery
  - Gray: seasonal normalization
  - Orange: control group (organic) recovery
- Verdict badge: VALIDATED / PARTIAL / FAILED with confidence indicator
- Narrative summary (LLM-generated)

### 9.2 Portfolio Dashboard

- Summary cards: total value recovered, solutions in flight, value at risk
- Table: all tracked solutions with status, expected vs. actual, confidence
- Cost of inaction section: unaddressed situations with projected erosion
- Trend chart: cumulative value delivered over time

### 9.3 Cost of Inaction (at HITL decision point)

- Before the principal approves/rejects, show projected cost of inaction
- Uses DA trend data to project forward: "If no action taken, estimated impact: -$X over Y weeks"
- Displayed alongside SF solution options as motivation

---

## 10. Distinction from Implementation Tracker Agent

The Implementation Tracker Agent PRD exists but will NOT be built. Its scope (task tracking, milestone management, owner accountability) is better served by existing enterprise tools (Jira, Monday, Asana). Value Assurance is uniquely positioned because it has hooks into the original problem data that external tools cannot access.

| | Value Assurance Agent | Implementation Tracker (not building) |
|---|---|---|
| **Question** | "Did the solution deliver KPI impact?" | "Are the tasks being completed on schedule?" |
| **Data source** | SA/DA/MA/SF pipeline data | Task assignments, deadlines |
| **Unique value** | Causal attribution using internal data pipeline | Duplicates existing PM tools |
| **When** | Post-implementation measurement | During implementation |
| **Output** | ROI attribution with confidence scoring | Progress dashboards |

---

## 11. Technical Requirements

- Modular, maintainable architecture aligned with A9_Agent_Template
- Registry integration via `create_from_registry` and `AgentRegistry.get_agent()`
- All LLM calls routed through A9_LLM_Service_Agent via Orchestrator
- Async operations throughout (`async def` entrypoints)
- Pydantic models for all I/O (A2A protocol compliance)
- Structured logging via `logging.getLogger(__name__)`
- Supabase persistence for all solution tracking and evaluation data
- No direct imports of `openai` or `anthropic`
- Error handling with context preservation — never lose evaluation data on failure

---

## 12. Testing Strategy

- **Unit tests:** Attribution calculation logic, confidence scoring, verdict determination
- **Integration tests:** End-to-end flow from SF HITL approval → VA registration → measurement → evaluation
- **Mock strategy:** Mock DA/MA/SA data inputs; test attribution math against known scenarios
- **Scenario tests:**
  - Solution fully successful (attributable > expected)
  - Solution partially successful (attributable > 0 but < expected)
  - Solution failed (no attributable impact — all recovery was market-driven)
  - No control group available (falls back to simple before/after with LOW confidence)
  - Multiple simultaneous interventions on same KPI (confidence downgrade)
  - Strategy ALIGNED — KPI VALIDATED (full success, counted in ROI)
  - Strategy DRIFTED — KPI VALIDATED (flagged for executive review, not auto-counted)
  - Strategy SUPERSEDED — KPI VALIDATED (archived, excluded from active ROI)
  - Strategy DRIFTED — KPI FAILED (acceptable loss, closed)
  - Multiple solutions drift simultaneously (strategy shift alert triggered)
  - Principal ownership change mid-measurement (accountability transfer)
  - KPI threshold recalibration after approval (original target vs. new target)

---

## 13. Success Metrics

- **Adoption:** % of HITL-approved solutions that proceed to measurement
- **Attribution quality:** % of evaluations with MODERATE or HIGH confidence
- **Executive trust:** Do principals reference VA data in decision-making?
- **Platform ROI:** Can Agent9 demonstrate cumulative value delivered using VA data?
- **Honest accounting:** Does VA correctly attribute market-driven recovery (not over-claim)?

---

## 14. Future Scope (Not in MVP)

- Automated measurement scheduling (trigger evaluation after time_to_value window)
- Predictive analytics: forecast solution success probability based on historical VA data
- Cross-solution learning: which types of solutions (cost reduction vs. revenue growth) have highest validation rates?
- Integration with financial systems for dollar-value ROI translation
- Automated re-triggering of SA → DA cycle when a solution is FAILED
- Email/Slack notifications when solutions are VALIDATED or FAILED

---

## 15. Change Log

- **2026-03-13:** Initial PRD created. Defines counterfactual attribution methodology using DA (Is/Is Not, change-point), MA (market factor adjustment), SA (seasonal baselines). Supabase persistence design. Portfolio dashboard and Cost of Inaction capabilities. Decision to not build Implementation Tracker Agent (superseded by VA + external PM tools).
- **2026-03-13:** Added Section 4.7 — Strategy Alignment Assessment. Two-dimensional verdict matrix (KPI impact × strategic fit). Strategy snapshot at registration, drift detection at measurement. Portfolio segmentation by alignment status (ALIGNED/DRIFTED/SUPERSEDED). Only ALIGNED solutions count in active ROI totals. Strategy drift as a meta-signal. Updated entrypoints, Supabase schema, ImpactEvaluation model, portfolio model, and test scenarios.
