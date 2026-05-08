# A9_Value_Assurance_Agent Card

**Last Updated:** 2026-05-08  
**Status:** Active — client_id scoped (Phase 10B) (Phase 7C + VA Lifecycle)

## Overview

The `A9_Value_Assurance_Agent` closes the insight-to-outcome loop for Agent9-HERMES. After a principal approves a solution recommendation at the HITL checkpoint in Solution Finder, this agent tracks whether that solution actually delivered its expected KPI impact.

It uses **Difference-in-Differences (DiD) counterfactual attribution** — exploiting the IS NOT dimensions from Deep Analysis as natural control groups — to isolate the solution's causal contribution from market recovery, seasonal patterns, and organic trends. It also monitors **strategy drift**: comparing the strategic context captured at approval time against the live registry state to detect whether the original business objective is still valid.

## Protocol Entrypoints

| Method | Signature | Returns |
|--------|-----------|---------|
| `register_solution` | `async def register_solution(request: RegisterSolutionRequest) -> RegisterSolutionResponse` | solution_id + phase=APPROVED + status=MEASURING |
| `evaluate_solution_impact` | `async def evaluate_solution_impact(request: EvaluateSolutionRequest) -> EvaluateSolutionResponse` | ImpactEvaluation + verdict + confidence |
| `check_strategy_alignment` | `async def check_strategy_alignment(request: CheckStrategyAlignmentRequest) -> CheckStrategyAlignmentResponse` | StrategyAlignmentCheck + alignment_verdict |
| `record_kpi_measurement` | `async def record_kpi_measurement(request: RecordKPIMeasurementRequest) -> RecordKPIMeasurementResponse` | actual_trend array + actual_trend_dates |
| `update_solution_phase` | `async def update_solution_phase(request: UpdateSolutionPhaseRequest) -> UpdateSolutionPhaseResponse` | phase (validated forward transition) |
| `project_inaction_cost` | `async def project_inaction_cost(request: ProjectInactionCostRequest) -> ProjectInactionCostResponse` | InactionCostProjection + trend forecasts |
| `get_portfolio_summary` | `async def get_portfolio_summary(request: PortfolioSummaryRequest) -> StrategyAwarePortfolio` | Portfolio aggregate + sorted by ROI |
| `generate_narrative` | `async def generate_narrative(request: GenerateNarrativeRequest) -> GenerateNarrativeResponse` | Executive narrative (LLM-generated) |

Models defined in `src/agents/models/value_assurance_models.py`. **All entrypoints are async; idempotence on upsert via deterministic solution_id.**

## Configuration Schema

Defined in `src/agents/agent_config_models.py`:

```python
class A9ValueAssuranceAgentConfig(BaseModel):
    agent_name: str = "A9_Value_Assurance_Agent"
    measurement_window_days: int = 30          # default window before re-evaluation
    min_confidence_for_roi: str = "MODERATE"   # minimum confidence to include in ROI totals
    inaction_cost_revenue_multiplier: float = 0.005  # 0.5% revenue per 1% KPI change (heuristic)
    supabase_enabled: bool = False             # Phase 7A: in-memory; set True for Supabase
```

## Dependencies

| Agent | Role |
|-------|------|
| `A9_Situation_Awareness_Agent` | Re-monitor KPI at evaluation time to get current value |
| `A9_Deep_Analysis_Agent` | Source of IS NOT dimensions → used as DiD control groups |
| `A9_Market_Analysis_Agent` | Market signals at approval time → market_driven_recovery estimate |
| `A9_Solution_Finder_Agent` | Triggers `register_solution` after HITL approval |
| `A9_Principal_Context_Agent` | Provides current principal priorities for strategy drift check |
| `A9_Data_Product_Agent` | Confirms data product is still active |
| `A9_LLM_Service_Agent` | LLM narrative generation (routed via Orchestrator) |

## LLM Configuration

| Task Type | Model | Rationale |
|-----------|-------|-----------|
| Narrative generation | `claude-haiku-4-5-20251001` | Fast, cost-efficient executive summaries |

## Attribution Methodology

**Difference-in-Differences (DiD):**

```
attributable_impact = total_kpi_change
                    - control_group_change     (IS NOT dimensions — organic trend)
                    - market_driven_recovery   (external tailwind from MA signals)
                    - seasonal_component       (seasonal pattern adjustment)
```

**Confidence levels:**
- `HIGH`: control group + market context + sufficient data volume
- `MODERATE`: one of the above available
- `LOW`: no adjustments available — attributable_impact = total_change (directional only)

**Composite verdict matrix** (KPI verdict × Strategy alignment):

| KPI Verdict | Strategy Alignment | Composite Label | ROI Eligible |
|-------------|-------------------|-----------------|--------------|
| VALIDATED   | ALIGNED           | Full success    | ✓ |
| VALIDATED   | DRIFTED           | Misdirected win | ✓ (exec attention) |
| VALIDATED   | SUPERSEDED        | Obsolete win    | ✗ |
| PARTIAL     | ALIGNED           | Work in progress| ✓ |
| PARTIAL     | DRIFTED           | Partial misdirection | ✗ (exec attention) |
| PARTIAL     | SUPERSEDED        | Acceptable loss | ✗ |
| FAILED      | ALIGNED           | Failure         | ✗ (exec attention) |
| FAILED      | DRIFTED           | Strategic waste | ✗ (exec attention) |
| FAILED      | SUPERSEDED        | Irrelevant failure | ✗ |

## Strategy Alignment Check

At registration: a `StrategySnapshot` captures principal priorities, KPI threshold, business process domain, data product ID, and key assumptions.

At evaluation: the agent diffs the snapshot against the live registry:
- `ALIGNED`: priorities stable, KPI still monitored, threshold unchanged (< 20% drift), data product active
- `DRIFTED`: priority overlap < 50% OR threshold changed significantly
- `SUPERSEDED`: data product deactivated OR principal no longer accountable for this KPI

## Storage

**Dual persistence:** In-memory `_solutions_store` + Supabase REST API (`VASolutionsStore`).

Supabase tables: `value_assurance_solutions`, `value_assurance_evaluations`
Migrations:
- `supabase/migrations/20260314_value_assurance_tables.sql` — base tables
- `supabase/migrations/20260318_va_trend_columns.sql` — trend arrays, benchmark segments
- `supabase/migrations/20260321_va_briefing_snapshot.sql` — briefing replay JSONB
- `supabase/migrations/20260410_va_lifecycle_phase.sql` — phase, go_live_at, completed_at columns + backfill

Persistence layer: `src/database/va_solutions_store.py` (follows `SituationsStore` pattern).
On `connect()`, loads all solutions from Supabase into memory. Falls back gracefully when Supabase is unavailable.

## Compliance

- A2A Pydantic I/O for all requests/responses
- Lifecycle: `create_from_registry(config)` → `connect()` → entrypoints → `disconnect()`
- All LLM calls routed through `A9_LLM_Service_Agent` via Orchestrator
- No direct `anthropic` / `openai` imports
- Orchestrator-guarded: all external agent calls wrapped in `if self.orchestrator:` checks

## Solution Lifecycle Phases (Apr 2026)

Solutions follow a 5-phase lifecycle independent of the evaluation verdict:

| Phase | Meaning | Trigger |
|-------|---------|---------|
| **APPROVED** | Decision recorded, not yet started | `register_solution()` sets initial phase |
| **IMPLEMENTING** | Solution being built/deployed | Principal clicks "Mark Implementing" |
| **LIVE** | Solution deployed, measurement begins | Principal clicks "Go Live" (key HITL event) |
| **MEASURING** | DiD attribution running | Auto-transition when evaluation runs |
| **COMPLETE** | Verdict rendered | Auto-transition when `evaluate_solution_impact()` sets verdict |

Phase transitions are validated (must follow order). The `update_solution_phase()` entrypoint handles manual transitions (APPROVED→IMPLEMENTING→LIVE); MEASURING and COMPLETE are auto-set by the agent.

**Key fields:** `phase: SolutionPhase`, `go_live_at: Optional[str]` (set on LIVE), `completed_at: Optional[str]` (set on COMPLETE).

**TrajectoryChart phase-aware rendering:**
- APPROVED/IMPLEMENTING: Cost of Inaction line only (shows money left on the table during delay)
- LIVE/MEASURING: All three lines (inaction + expected + actual)
- COMPLETE: All three lines + verdict annotation

## Request/Response Models — Quick Reference

### RegisterSolutionRequest → RegisterSolutionResponse
**Input:** kpi_id, situation_id, principal_id, solution_description, expected_impact_lower/upper, measurement_window_days, optional strategy_snapshot
**Output:** solution_id (deterministic hash), phase=APPROVED, status=MEASURING
**Idempotence:** Same (kpi_id, situation_id) always produces same solution_id; subsequent calls upsert rather than duplicate.

### EvaluateSolutionRequest → EvaluateSolutionResponse
**Input:** solution_id, current_kpi_value, control_group_kpi_values[], market_recovery_estimate, seasonal_estimate
**Output:** ImpactEvaluation (verdict + confidence + composite + narrative), phase auto-transitions to COMPLETE
**Auto-Transition:** Phase automatically moves APPROVED/IMPLEMENTING/LIVE → MEASURING → COMPLETE on evaluation.

### CheckStrategyAlignmentRequest → CheckStrategyAlignmentResponse
**Input:** solution_id, principal_id
**Output:** StrategyAlignmentCheck (alignment_verdict: ALIGNED|DRIFTED|SUPERSEDED, priority_overlap, drift_factors)
**Called by:** evaluate_solution_impact() internally; also callable standalone for drift detection.

### RecordKPIMeasurementRequest → RecordKPIMeasurementResponse
**Input:** solution_id, kpi_value, measured_at (optional, defaults to now)
**Output:** actual_trend array (appended), actual_trend_dates array (appended)
**Idempotence:** Each call appends one measurement; no deduplication on date (caller must avoid duplicates).

### UpdateSolutionPhaseRequest → UpdateSolutionPhaseResponse
**Input:** solution_id, new_phase (must be forward transition)
**Output:** phase (updated), message
**Validation:** Raises ValueError if attempting backward transition (e.g., LIVE → APPROVED).
**Go-Live Trigger:** On LIVE transition, resets actual_trend to [baseline] and actual_trend_dates to [now] for fresh measurement.

### ProjectInactionCostRequest → ProjectInactionCostResponse
**Input:** kpi_id, situation_id, historical_trend[], current_kpi_value
**Output:** InactionCostProjection (projected_30d, projected_90d, revenue_impact_30d/90d, trend_direction, confidence)
**Confidence:** LOW if <5 data points; MODERATE if ≥5 points.

### GetPortfolioSummaryRequest → StrategyAwarePortfolio
**Input:** client_id, principal_id (optional), filter_by_phase (optional), min_roi_confidence
**Output:** Aggregated portfolio stats: total_roi, solutions_by_verdict, solutions_by_phase, top_solutions_by_impact
**Filtering:** Filters out SUPERSEDED solutions; only includes verdicts with include_in_roi_totals=True.

### GenerateNarrativeRequest → GenerateNarrativeResponse
**Input:** solution_id, narrative_type ("executive" | "detailed")
**Output:** narrative (LLM-generated, ~200 words executive summary)
**Model:** claude-haiku-4-5-20251001 (fast, cost-efficient)

## Error Behaviour

| Scenario | Entrypoint | Raises | Fallback |
|----------|-----------|--------|----------|
| Solution not found | All except register_solution | ValueError | None (exception propagates) |
| Invalid phase transition | update_solution_phase | ValueError | None (user must correct) |
| No historical_trend data | project_inaction_cost | ValueError | None (user must provide at least [1]) |
| control_group_kpi_values empty | evaluate_solution_impact | None (allowed) | confidence = MODERATE or LOW; control_change = 0.0 |
| Principal not in registry | register_solution (building snapshot) | Caught; logs warning | Uses safe defaults: empty priorities, principal_id as principal_name |
| LLM service unavailable | generate_narrative | Caught; logs warning | Returns empty string + status="error" |
| Supabase unavailable | All (except logic) | Non-fatal (try/except) | In-memory store still updated; Supabase persist skipped |
| Market signals not available | register_solution | None (allowed) | ma_market_signals set to empty list |

## Phase Transition Guards

```
APPROVED ──→ IMPLEMENTING ──→ LIVE ──→ MEASURING ──→ COMPLETE
  ↑                                         ↑              ↑
  └─ register_solution() sets              └─ evaluate_solution_impact()
  └─ Backward transitions blocked          └─ update_solution_phase() enforces order
```

**Manual transitions:** APPROVED → IMPLEMENTING → LIVE (via `update_solution_phase()`)
**Auto-transitions:** MEASURING → COMPLETE (via `evaluate_solution_impact()`)

## Pipeline Position

```
SA (detect) → DA (Is/Is Not) → MA (market signals) → SF (solutions + HITL)
                                                              ↓
                                              VA (register_solution)
                                                              ↓
                                              [measurement window]
                                                              ↓
                                              VA (evaluate_solution_impact)
                                                  → DiD attribution
                                                  → strategy alignment
                                                  → composite verdict
                                                  → LLM narrative
```
