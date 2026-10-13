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

## Assumption Grading Write-Back (Phase 17 T3, 2026-08-30)

`evaluate_solution_impact()` now closes the theory layer's accretion loop: after the verdict above is
computed, `_grade_assumptions_from_verdict()` (module-level helper) writes it back onto every
`assumptions` row this solution pre-registered at HITL approval (`linked_solution_id` match, via
`AssumptionProvider.get_for_solution`).

| Verdict | Assumption.status write |
|---|---|
| `VALIDATED` | `held` |
| `FAILED` | `falsified` |
| `PARTIAL` / `MEASURING` | left `active` — insufficient signal to grade *which* assumption held vs. broke |

**Honest scope — this is solution-level, not per-assumption, grading.** A verdict says whether the
*solution* worked; it does not say which specific lever inside it did. Distinguishing "the lever worked
but was offset" from "the lever did not work" needs the Phase 17 T2 KPI decomposition model's mechanism
mapping — a further follow-up, not attempted here. Never overwrites an already-graded row (`status !=
'active'` rows are skipped). Non-fatal, same posture as the Supabase evaluation persist immediately
above it.

## Density-Gate Write-Back Infrastructure (Phase 17, 2026-08-30)

`register_solution()` now captures `StrategySnapshot.claimed_causal_edge` — the approved option's
`moderator_grade.causal_grounding`, normalized via `src.analysis.mechanism.normalize_causal_edge` to a
sorted `"a<->b"` string, threaded in from `src/api/routes/workflows.py` at the same approval call site
that already threads `bets_on_assumptions` (same "commit to the claim before the outcome is known"
discipline).

`evaluate_solution_impact()` then calls `_confirm_causal_edge_from_verdict()`: when the verdict is
`VALIDATED` and `claimed_causal_edge` names a real, currently-registered `kpi_relationships` edge, that
SPECIFIC edge is written back as `causal_rung='intervention_tested'` + `provenance='va_validated'` —
respecting `KPIRelationship`'s own model validator, which requires exactly that pairing. Never fires
speculatively: no claimed edge, `'ungrounded'`/`'insufficient_data'`, no matching registered row, or a
non-`VALIDATED` verdict are all documented no-ops.

**This is infrastructure, not a result.** It lets confirmed edges accumulate through real subsequent
pipeline runs. It does NOT itself get any client over the Causal Edges density gate (confirmed edges
outnumbering template ones) — that requires real use over time (`DEVELOPMENT_PLAN.md` Phase 17); no
amount of code closes it.

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

**Supabase is the read authority; `_solutions_store` is a write-through cache, not a snapshot.**
`get_portfolio_summary()` re-reads the requested `(principal_id, client_id)` scope from Supabase on
every call and merges the rows in. Do not re-gate that read on "load only if the in-memory store is
empty" — that turns the store into a process-lifetime cache that can never be corrected, so rows
written by any other process (seed/backfill scripts, a second Railway replica, the assessment
pipeline) stay invisible until restart. It also breaks the tenant filter below it: the load is
scoped to one `(principal, client)` pair but fills a global dict, so a first unscoped call satisfies
the emptiness check and leaves later client-scoped calls filtering a cache that predates the tenant
they asked for. See the Aug 2026 entry under Change History.

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
**Input:** kpi_id, situation_id, principal_id, solution_description, expected_impact_lower/upper, measurement_window_days, optional strategy_snapshot, `analysis_mode` ("problem" | "opportunity")
**Output:** solution_id (deterministic hash), phase=APPROVED, status=MEASURING
**Idempotence:** Same (kpi_id, situation_id) always produces same solution_id; subsequent calls upsert rather than duplicate.

**Opportunity mode inaction trend (May 2026):**
- `analysis_mode = "opportunity"` → `pre_slope = 0.0` (flat inaction trend at baseline)
- Rationale: for opportunity solutions, inaction = foregone replication benefit (modeled in `expected_trend`), not a continuing deterioration
- `expected_trend` still rises linearly — representing the uplift that would be captured by acting
- This prevents the "inaction looks like continued success" artifact where a rising `pre_slope` made doing nothing appear attractive

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

- May 2026: `get_portfolio_summary` — added client_id + principal_id isolation filter on in-memory store so cross-tenant solutions never appear in a client-scoped portfolio summary.
- Aug 2026: `get_portfolio_summary` — the Supabase load is no longer gated on an empty
  `_solutions_store`; it refreshes the requested scope per call and merges. Found via the
  Solutions-in-Progress tracker rendering nothing for lubricants in production while the
  production DB held the correct seven rows: the live Railway process was serving an
  in-memory snapshot taken before a backfill and would never have re-read it. Two of the
  three defects behind that symptom were outside this agent — see the note on 11I-C bug 2
  below, and `scripts/seed_va_demo_data.py` (was hardcoded to local Supabase, so production
  still carried a pre-migration row generation with `client_id` unset and prefixed `kpi_id`s).

## Phase 11I-C: Plan/Budget Trajectory + Compliance Severity (Jul 2026)

**Fourth trajectory:** with `plan_version_value` (11I-A) available on budget-tracked KPIs, VA now captures a plan/budget baseline at approval and tracks position against it as a fourth line alongside inaction/expected/actual.

| Deliverable | Description |
|---|---|
| `RegisterSolutionRequest.plan_value_at_approval` / `AcceptedSolution.plan_value_at_approval` | Optional float, caller-supplied. Workflow wiring (`workflows.py` HITL approval) sources it from the originating `Situation.plan_value` via `SituationsStore.get_situation(situation_id)['full_payload']` — populated only when the situation was a `plan_variance`/`projected_breach` alert. `None` when the KPI has no budget data. |
| `VsPlanVerdict` enum | `ahead_of_plan` \| `on_plan` \| `behind_plan` \| `no_plan_data`. Computed in `evaluate_solution_impact()` as `(current - plan) / abs(plan)`; `on_plan` band is ±2%. Literal — no `inverse_logic` flip (describes numeric position, not good/bad framing). |
| `ImpactEvaluation.vs_plan_verdict` / `.vs_plan_pct` | Attached alongside the existing DiD verdict/composite fields. |
| `StrategyAwarePortfolio.ahead_of_plan_count` / `on_plan_count` / `behind_plan_count` / `no_plan_data_count` | Aggregated in `get_portfolio_summary()` from evaluated solutions only (unevaluated solutions don't count toward any bucket). |
| Covenant/regulatory rejection | `register_solution()` looks up `kpi_type` via `RegistryFactory.get_provider("kpi")` before registering; raises `ValueError` for `kpi_type in ("covenant", "regulatory")`. Compliance obligations are not value-tracked opportunities. Lookup failure is non-fatal (logged, registration proceeds) — matches the agent's existing registry-unavailable fallback pattern. |
| Frontend | `TrajectoryChart.tsx` renders `planValue` as a flat dashed-amber reference line (not a trend array — a single baseline) with legend + tooltip entries. `PortfolioDashboard.tsx` shows a secondary `VsPlanBadge` next to the verdict badge (omitted for `no_plan_data`). |
| Migration | `supabase/migrations/20260703_va_plan_tracking.sql` — `plan_value_at_approval` on `value_assurance_solutions`; `vs_plan_verdict` + `vs_plan_pct` on `value_assurance_evaluations`. |
| Not yet built | PIB "Budget Performance" section and portfolio-summary plan-performance sentence are Phase 11I-D scope, not this phase. |

**Two pre-existing bugs found and fixed by the SA→DA→MA→SF→VA E2E test** (`tests/regression/test_plan_variance_e2e.py`, `tests/regression/_plan_variance_runner.py`) while validating this phase — both predate 11I-C and affected every real HITL approval, not just plan-variance ones:
1. **`kpi_id` was always empty string at registration.** `workflows.py`'s approve handler read `da_output.get("kpi_name")`, but `DeepAnalysisResponse` has no top-level `kpi_name` field (only nested under `plan`). Every real (non-test-stub) HITL approval registered its VA solution with `kpi_id=""`, silently breaking the covenant/regulatory check, the strategy-snapshot threshold lookup, and any KPI-scoped query. Fixed by sourcing `kpi_id` from the originating SA `Situation.kpi_id` (looked up once via `SituationsStore.get_situation(situation_id)` — the same lookup now also used for `plan_value_at_approval`), falling back to `Situation.kpi_name` then DA's nested `plan.kpi_name`.
2. **`client_id` was never passed to `RegisterSolutionRequest`.** Every VA solution registered via the real HITL flow had `client_id=None`, invisible to client-scoped `get_portfolio_summary()` queries and a genuine multi-tenant isolation gap (CLAUDE.md Protocol #7). Fixed by threading `wf_payload.get("client_id")` through.
   ⚠️ **This fix was only half the path, and the symptom persisted until Aug 2026.** Threading
   `wf_payload["client_id"]` cannot help when the workflow was *started* without one, and the
   route the UI actually navigates to — `CouncilDebatePage` — passed `principalContext?.client_id`
   to `runSolutionFinder`, while `DecisionStudio.tsx` built that `principalContext` object without
   a `client_id` key at all. So real approvals kept writing `client_id=NULL`. When auditing a
   tenant-scoped write, verify the tenant is resolved at the *entry point* of the flow, not just
   at the last hop before the insert.

Also confirmed while building the test: the legacy `GET /value-assurance/solutions/{solution_id}` route reads a **module-level dict in `value_assurance.py`** that the real `register_solution` flow never writes to (it writes to the VA agent singleton's own `_solutions_store` via `AgentRegistry`). That route 404s for anything registered through the real HITL path — use `GET /portfolio/{principal_id}` (which correctly resolves the singleton via `_get_va_agent()`) instead, until the legacy route is rewired or removed.

**Test also simulates the real HITL lifecycle clicks**, not just approve: Approve → "Mark Implementing" → "Go Live" (`PATCH /solutions/{id}/phase`, exactly what `Portfolio.tsx`'s buttons call) → `evaluate`. This matters because the LIVE transition is what resets `actual_trend` to a fresh measurement baseline in production.

## Third `kpi_id` bug in the same handler, found the same way (Aug 2026)

The two Aug 2026 bugs above (`kpi_id=""`, `client_id=None`) were both fixed in `workflows.py`'s approve
handler — but that fix still always resolved `kpi_id` from the *situation's* original KPI. Found live
2026-08-22 testing a genuine reframe (Gross Margin % → COGS via the Phase 19 framing gate): a solution
approved after a reframe would register and go on to be measured against `gross_margin_pct`, not the
KPI the framing decision — and the approved solution's own mechanism — actually targeted.

Fixed via `_resolve_va_kpi_id_and_framing()` (`workflows.py`, module-level and pure, deliberately
extracted so it's unit-testable without the full route/runtime stack): prefers
`framing_decision.chosen_kpi_id` when `choice != "confirm_stated"`, falls back to the situation's
stated KPI otherwise. `framing_decision` reaches this handler the same way it already reaches SF's own
dispatch (`preferences.refinement_result`) — no new plumbing, just a consumer that was missing.

**New `AcceptedSolution` fields, same session:** `framing_snapshot` (a new `FramingSnapshot` model —
`choice`/`chosen_kpi_id`/`chosen_objective_text`/`falsification_criterion`/`stated_kpi_id`, durable even
if the causal graph is later reclassified) and `target_metric` (the approved option's own
`impact_estimate.metric`). Both had to be threaded through **three** separate hand-maintained field
lists to actually persist — `register_solution`'s `AcceptedSolution(...)` construction here,
`VASolutionsStore.upsert_solution`'s `row` dict, and the new migration's columns — the same
explicit-field-list trap that already silently dropped `KPIRelationship.causal_direction` twice
elsewhere in this codebase. Migration `20260822_va_solutions_framing_snapshot.sql`, applied and
verified live against local Supabase. 6 new regression tests in `test_va_registration_framing_kpi.py`.

**Not yet built:** the full reframe chain (margin → COGS → base_oil_cost) still only preserves the last
hop's decision — no `reframed_from_id` lineage field exists yet to link successive framing records.
`alternatives_considered` (what else was offered, not just what was chosen) also isn't captured — that
needs `framing_prompt`/`framing_record` threaded through the frontend's `debateConfig.refinementResult`
the same way `framing_decision` already is, which doesn't happen today. See
`docs/architecture/reframe_relaunch_and_lineage_design.md`.

## Accounting-identity links are never marked as tested (Oct 2026)

`_confirm_causal_edge_from_verdict()` now returns without writing when the matched
`kpi_relationships` row has `basis == "accounting_identity"`. Arithmetic cannot be outcome-tested:
moving a component moves its parent by definition, so a VALIDATED solution says nothing new about
the link. Found live: `sales_order_count<->net_revenue` (an identity) had been recorded as
`intervention_tested` / `va_validated` and was counting toward the tested total.

Test: `test_va_causal_edge_confirmation.py::TestAccountingIdentityIsNeverConfirmed`.

## A weak verdict no longer marks a link as tested (Oct 2026)

`_confirm_causal_edge_from_verdict()` takes a required keyword `confidence` and returns without
writing unless it is `MODERATE` or `HIGH`. A `LOW`-confidence verdict had no control group and no
market or seasonal estimate, so its "attributable" figure is the total KPI change: a
before-and-after reading. That cannot support the reader-facing claim "held up when a past decision
was measured". `None` is treated as not good enough, and the keyword has no default so a caller
cannot skip the check by omission.

Found live: both links marked tested in the local lubricants registry
(`premium_mix_pct<->gross_margin_pct`, `units_sold<->net_revenue`) were written by `VALIDATED`
verdicts at `LOW` confidence with control, market and seasonal components all zero. A Solution
Finder run then preferred an option because its link was "the one that has been outcome-tested".

Known limit: `MODERATE` is reached with any one of the three inputs, so a market estimate alone,
with no control group, still passes. Requiring a control group specifically is the stricter rule
and has not been applied.

Tests: `test_va_causal_edge_confirmation.py::TestWeakVerdictNeverConfirms`.

## Evaluations are read back with their solutions (Oct 2026)

`VASolutionsStore.upsert_evaluation` has always written to `value_assurance_evaluations`, but nothing
read those rows. `get_portfolio_summary()` rebuilds each solution from its `value_assurance_solutions`
row on every call, so every solution came back with a verdict and `impact_evaluation=None`: lost on
restart, and also lost in the same process the first time the portfolio was read after an
evaluation. Found live: the portfolio API returned no evaluation for any of 12 lubricants solutions,
including ones with a full row stored. The Value Assurance panel and the breakdown chart could
never render, and the trajectory chart said "first measurement period in progress" beside a final
verdict.

- New `VASolutionsStore.get_evaluations_for_solutions(solution_ids)` returns rows keyed by
  `solution_id`, shaped for `ImpactEvaluation(**row)` (the `strategy_alignment` column maps to the
  `strategy_check` field).
- New module-level `_attach_evaluation(solution, stored_row, previous, logger)` in the agent. It
  prefers the stored row, then the evaluation this process already held for that solution (its
  persist may have failed), then none. A row that does not parse is logged and treated as absent,
  never replaced by a default.
- `get_portfolio_summary()` calls both when it reloads from Supabase.

Tests: `tests/unit/test_va_evaluation_readback.py` (7).

## Two gates tightened: ROI counting and "tested" (Oct 2026)

**ROI.** `A9ValueAssuranceAgentConfig.min_confidence_for_roi` (default `MODERATE`) was declared and
never read. `include_in_roi_totals` came from the verdict x alignment matrix alone, so a `LOW`
confidence, before-and-after result counted toward the ROI total and showed "Include in ROI".
`_apply_roi_confidence_floor()` now clears the flag below the floor, in two places:
`evaluate_solution_impact()` for new evaluations, and `get_portfolio_summary()` for evaluations
stored before the floor existed, so the total and the per-solution flag agree. The verdict and the
composite label are unchanged; only ROI eligibility moves.

Known and not fixed here: `total_attributable_impact` adds raw figures across KPIs, so dollars and
percentage points are summed together. The Portfolio page no longer uses it and computes a
dollar-only figure from the solutions list.

**Tested.** `_confirm_causal_edge_from_verdict()` gained a second required keyword,
`has_control_group`. A link is marked tested only when the verdict is `VALIDATED`, confidence is
`MODERATE` or `HIGH`, and the evaluation was compared with segments the decision did not touch.
This closes the limit recorded in the entry above: a single market or seasonal number no longer
passes.

Tests: `test_a9_value_assurance_agent_unit.py::test_low_confidence_result_is_not_counted_in_roi`,
`::test_roi_floor_applies_to_evaluations_stored_before_it_existed`,
`test_va_causal_edge_confirmation.py::TestWeakVerdictNeverConfirms`.

## The baseline is the KPI's actual value at approval (Oct 2026)

**Defect.** `evaluate_solution_impact()` used `strategy_snapshot.kpi_threshold_at_approval` as the
baseline: the KPI's warning threshold, or 0 when it had none. The KPI's own value was never
recorded. Found live: every locally "measured" solution had a baseline of 0, so `total_kpi_change`
was simply the number the caller supplied. The stored outcomes (+$575K, +1.725pp) were the demo
script's `expected_lower x 1.15`, written within 150 ms of approval. A real Net Revenue of $35M
would have read as a +$35M change.

**Fix.**
- `StrategySnapshot` gains `kpi_value_at_approval` and `kpi_value_period` ("YYYY-MM"), separate from
  the threshold. They live in the existing `strategy_snapshot` JSONB, so there is no migration.
- `RegisterSolutionRequest` gains `baseline_kpi_value` / `baseline_period`, threaded into the
  snapshot the same way as `claimed_causal_edge`.
- `workflows.py::_baseline_from_situation()` (module-level, pure) takes the value from the monthly
  series Situation Awareness already measured: the latest month strictly before the current one.
  The current month is partial, and a warehouse may hold later-dated rows (the demo data does). It
  returns `(None, None)` when the solution targets a different KPI than the situation measured (a
  reframed objective), or when no earlier month exists. It never guesses.
- `evaluate_solution_impact()` raises `BaselineNotRecordedError` (a `ValueError`; the route returns
  409) when no value was recorded. It does not fall back to the threshold or to zero.
- Projection lines (`inaction_trend`, `expected_trend`, `actual_trend[0]`) start from the recorded
  value when there is one, and from the threshold otherwise, as before.

**Still open, deliberately not built here** (each is a method decision, not a wiring fix):
- `current_kpi_value` and `control_group_kpi_values` are still supplied by the caller. Nothing pulls
  them from the warehouse.
- `control_change = mean(control_group_kpi_values)` is subtracted directly from the enterprise-level
  change. For a dollar KPI that mixes scales (an enterprise total minus an average segment change).
- The expected range from Solution Finder states no period, while the baseline is monthly.
- A reframed objective gets no baseline.

Tests: `tests/unit/test_va_baseline_at_approval.py` (12).

### Follow-up the same day: the baseline helper rejects a series it cannot trust

The end-to-end regression run on Hess (SQL Server) recorded a baseline for period "2026-00". The
monthly series Situation Awareness returns for that backend is labelled
`['2025-01', '2025-01', '2026-00', '2026-00', ...]`: 3-digit fiscal periods are truncated when the
label is built (the SQL Server copy of the monthly-series builder, already listed as a known
duplicate in `A9_Data_Product_Agent_card.md`, Phase 25). `_baseline_from_situation()` now uses a
series only when every label is a distinct calendar month; otherwise it records nothing. Until the
SQL Server labels are fixed, solutions on that backend get no baseline and cannot be evaluated.
`tests/regression/test_plan_variance_e2e.py` reports this as an expected failure.

Also seen in that run, not fixed: within one process a newly approved solution is listed twice in
the portfolio, once under its 32-character id and once under the dashed UUID Supabase returns for
the same row. It clears on restart.

## The three-line comparison, brought into line with the settled design (Oct 2026)

The settled design: an outcome is judged by three monthly lines from acceptance. **Solution** (the
projected value if the solution works), **No Action** (the projected value if the trend at acceptance
continued) and **Actual** (measured values since acceptance). A regression check on 2026-10-13 found
five places where the code did not do this. They are fixed one at a time below.

Shared helper: `src/analysis/monthly_series.py` (pure functions over a `[{period, value}]` series;
uses a series only when every label is a distinct calendar month, and only complete months).

### 1. No Action line follows the measured trend

The slope was read from `deep_analysis_output["aggregates"]`, a field `DeepAnalysisResponse` has never
had, so every No Action line was flat. `workflows.py::_trend_slope_from_situation()` now takes the
recent trend from the situation's own monthly series (`monthly_series.recent_trend_slope`): the last
six complete months if a straight line fits them (r-squared of at least 0.4, the bar Situation
Awareness already uses before projecting a breach), else the last three, else none. Six months alone
was wrong on the first live run: Net Revenue had risen for four months and then fallen for two, and
a line through all six sloped up, projecting growth for a KPI flagged for falling. It passes the
result as
`RegisterSolutionRequest.pre_approval_monthly_slope`. Opportunity solutions stay flat by design. The
older single-value input (`pre_approval_kpi_value`) still works for callers that send it.

Tests: `tests/unit/test_monthly_series.py`.

### 2. Actual line comes from the warehouse

The only source of actual values was `record_kpi_measurement()`, called by the manual entry box on
the Portfolio page. `_refresh_actuals()` now rebuilds the line from the KPI's monthly values: the
baseline month, then every complete month since. The series comes through
`A9_Data_Product_Agent` (`get_kpi_definition(kpi_id, client_id=...)` then
`generate_monthly_series_sql` and `execute_sql`), so SQL stays with that agent and the lookup is
tenant-scoped.

- `_actuals_are_stale()` decides from dates alone whether a new month has closed, so
  `get_portfolio_summary()` costs a warehouse query only for a solution whose line is behind the
  calendar. Once current, it does not query again until the next month closes.
- Warehouse points are dated by period ("2026-10"), not by timestamp.
- Nothing usable (no series for the backend, untrusted labels, an error) leaves the line as it was.
- A warehouse refresh replaces manually entered points. Manual entry still works for a solution with
  no recorded baseline or no series.
- `generate_monthly_series_sql` covers BigQuery-backed KPIs only today, so other backends still rely
  on manual entry.

Tests: `tests/unit/test_va_actuals_from_warehouse.py`.

### 3. The verdict is read from the three lines, at window close

`evaluate_solution_impact()` compared one caller-supplied number with the baseline and the expected
range. It never looked at the No Action line, and it produced a verdict whenever it was called: a
solution with a 90-day window, evaluated the instant after approval, came back VALIDATED and
COMPLETE.

- `_actual_at_window_close()` picks the value to judge. If the Actual line holds the closing month
  (month `window_days // 30`, minimum 1) that point is used and any supplied number is ignored. If
  it does not, but the window has closed by the calendar and the caller supplied a reading, the
  reading is used. Otherwise it raises `MeasurementWindowOpenError` (route: 409) and nothing about
  the solution changes.
- `_verdict_from_three_lines()` is the rule:
  - VALIDATED: Actual reached the Solution line's lower bound (change since acceptance, less any
    adjustment, is at least `expected_impact_lower`).
  - PARTIAL: it did not, but Actual is better than No Action at that month.
  - FAILED: Actual is no better than No Action.
- `attributable_impact` is now Actual minus No Action at the closing month, less the adjustments
  (untouched segments, market, seasonal). `total_kpi_change` is still Actual minus the baseline.
- Direction: `StrategySnapshot.kpi_lower_is_better` is recorded at approval from the situation's
  `inverse_logic`. For a cost the Solution line points down and "better" means lower. When it was not
  recorded, higher is treated as better, as before.
- `EvaluateSolutionRequest.current_kpi_value` is now optional.

With a flat No Action line and a window that has closed, results are the same as before; the
existing verdict tests pass unchanged apart from their fixture declaring the window closed.

Not changed here: the adjustments are still supplied by the caller and still subtracted as raw
numbers (see items 4 and 5).

Tests: `tests/unit/test_va_three_line_verdict.py`.

### One solution, one entry

`_solutions_store` is now a `_SolutionStore`, a dict that treats the 32-character and dashed
spellings of a solution id as the same key. A solution approved in the running process was being
listed twice in the portfolio (once as registered, once as reloaded from Supabase) until the next
restart. Test: `test_va_evaluation_readback.py::TestOneSolutionOneEntry`.

## One id spelling from creation (Oct 2026)

`register_solution` created the solution id as 32 bare hex characters; Supabase returns the same
id as a dashed uuid. `_SolutionStore` made both find the same in-memory solution, but approval
still answered with the bare spelling while the portfolio listed the dashed one, so a caller
matching by equality missed (the regression run failed with "not found in portfolio" straight
after approval; the briefing-to-portfolio link uses the same match).

`_solution_id_from()` now spells the id as a dashed uuid when it is created. The value is the same
hash as before, so re-approving the same option still resolves to the same solution.
Test: `tests/unit/test_va_solution_id_spelling.py`.
