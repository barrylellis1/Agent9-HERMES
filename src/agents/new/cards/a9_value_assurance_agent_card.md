# A9_Value_Assurance_Agent Card

Status: Active (Phase 7C + VA Lifecycle)

## Overview

The `A9_Value_Assurance_Agent` closes the insight-to-outcome loop for Agent9-HERMES. After a principal approves a solution recommendation at the HITL checkpoint in Solution Finder, this agent tracks whether that solution actually delivered its expected KPI impact.

It uses **Difference-in-Differences (DiD) counterfactual attribution** — exploiting the IS NOT dimensions from Deep Analysis as natural control groups — to isolate the solution's causal contribution from market recovery, seasonal patterns, and organic trends. It also monitors **strategy drift**: comparing the strategic context captured at approval time against the live registry state to detect whether the original business objective is still valid.

## Protocol Entrypoints

- `register_solution(request: RegisterSolutionRequest) -> RegisterSolutionResponse` — `solution_id` is deterministic: `sha256(kpi_id + situation_id)[:32]`; re-approving the same situation upserts rather than inserts a duplicate
- `evaluate_solution_impact(request: EvaluateSolutionRequest) -> EvaluateSolutionResponse`
- `check_strategy_alignment(request: CheckStrategyAlignmentRequest) -> CheckStrategyAlignmentResponse`
- `project_inaction_cost(request: ProjectInactionCostRequest) -> ProjectInactionCostResponse`
- `get_portfolio_summary(request: PortfolioSummaryRequest) -> StrategyAwarePortfolio`
- `generate_narrative(request: GenerateNarrativeRequest) -> GenerateNarrativeResponse`
- `record_kpi_measurement(request: RecordKPIMeasurementRequest) -> RecordKPIMeasurementResponse`
- `update_solution_phase(request: UpdateSolutionPhaseRequest) -> UpdateSolutionPhaseResponse`

Models defined in `src/agents/models/value_assurance_models.py`.

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
