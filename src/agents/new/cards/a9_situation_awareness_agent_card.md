# A9_Situation_Awareness_Agent Card

## Agent Description
The Situation Awareness Agent provides automated KPI monitoring and situation detection based on principal context and business processes. It analyzes KPIs from any registered data product (BigQuery, SQL Server, DuckDB) to detect anomalies, trends, and insights, presenting them as actionable situations with severity levels, business impact analysis, and suggested next steps. Propagates `data_product_id` through the generate→execute pipeline for correct backend routing. DGA is mandatory for `process_nl_query` — raises `RuntimeError` if not wired via `_wire_governance_dependencies()`. SQL Server KPIs (bracket-quoted T-SQL) receive ISO date filters via `_bq_apply_period` directly in `_get_kpi_value`, bypassing DPA's comparison SQL generation which cannot inject timeframe conditions into stored T-SQL without an existing date filter.

## Primary Purpose
To provide personalized situation awareness for Finance KPIs, enabling principals to quickly understand the current state of their business metrics, identify anomalies, and take appropriate action.

## Core Capabilities
- Finance KPI monitoring and anomaly detection
- Principal-specific situation awareness based on role and context
- Business process-aligned KPI prioritization
- Principal KPI preference-aware ordering using KPI `metadata.line` / `metadata.altitude` and principal profile `metadata.kpi_line_preference` / `metadata.kpi_altitude_preference`
- Natural language query processing for KPI insights
- Lightweight Haiku LLM call per detected situation generates `key_observations` (2–3 plain-language insight bullets: pattern, magnitude, context); stored on `Situation.key_observations`; rendered on KPI tiles and in PIB email in place of sparkline
- Human-in-the-loop feedback handling
- Recommended diagnostic questions
- Contract-driven KPI enrichment with defensive registry fallbacks (normalized KPI IDs, view/date column resolution, filter injection)
- Per-KPI multi-horizon alert detection: threshold breach (existing), plan variance vs budget, forward-looking projected breach (linear regression), and rate-of-change acceleration (second derivative) — each produces a distinct situation card with its own `alert_type`
- KPI type classification: `kpi_type` field (`operational` | `concentration` | `covenant` | `regulatory`) — covenant/regulatory KPIs always fire at `severity = CRITICAL` regardless of threshold band
- Compound cross-KPI alert detection: post-processing step after all situations are computed; flags KPI pairs in declared `KPIRelationship` registry when their directions conflict per the relationship's `conflict_direction` (`diverging` | `converging`); sets `compound_alert = True`, `related_kpi_id`, and `compound_pattern` on both situation cards

## Configuration Model
```python
class SituationAwarenessAgentConfig(BaseModel):
    """Configuration for the Situation Awareness Agent."""
    
    # Required configuration
    contract_path: str = Field(
        description="Path to the data contract YAML file"
    )
    
    # Optional configuration
    kpi_thresholds: Optional[Dict[str, Dict[str, float]]] = Field(
        None,
        description="Custom KPI thresholds, overriding contract defaults"
    )
    principal_profile_path: Optional[str] = Field(
        None,
        description="Optional path to custom principal profile definitions"
    )
    assessment_mode: bool = Field(
        False,
        description="When True, processes one KPI at a time (called by assessment engine). When False, processes all principal KPIs (interactive mode)."
    )
    use_monitoring_profiles: bool = Field(
        True,
        description="When True, use per-KPI MonitoringProfile from registry instead of global timeframe. Requires Phase 9A KPI registry fields."
    )
```

## Protocol Entrypoints
| Method | Description | Request Model | Response Model |
|--------|-------------|---------------|----------------|
| `detect_situations` | Detect situations across KPIs for a principal context. Does **not** itself read MonitoringProfile fields or take an assessment-mode parameter — see the "Card correction" note under Phase 9A below for where that logic actually lives and why this row previously said otherwise. | `SituationDetectionRequest` | `SituationDetectionResponse` |
| `process_nl_query` | Process natural language queries about KPIs | `NLQueryRequest` | `NLQueryResponse` |
| `process_hitl_feedback` | Handle human-in-the-loop feedback for situations | `HITLRequest` | `HITLResponse` |
| `get_recommended_questions` | Get recommended questions based on principal context | N/A | `List[str]` |
| `get_kpi_definitions` | Get KPI definitions relevant to the principal | N/A | `Dict[str, KPIDefinition]` |

## Input/Output Schema
```python
# Key Request Models
class SituationDetectionRequest(BaseRequest):
    principal_context: PrincipalContext
    business_processes: List[BusinessProcess]
    timeframe: TimeFrame
    comparison_type: Optional[ComparisonType]
    filters: Optional[Dict[str, Any]]

class NLQueryRequest(BaseRequest):
    principal_context: PrincipalContext
    query: str

# Key Response Models
class SituationDetectionResponse(BaseResponse):
    situations: List[Situation]

class NLQueryResponse(BaseResponse):
    answer: str
    kpi_values: Optional[List[KPIValue]]
    sql_query: Optional[str]
```

## Dependencies
- A9_Data_Product_MCP_Service_Agent: For data query execution
- A9_Principal_Context_Agent: For principal context retrieval (future)
- A9_Data_Governance_Agent: For business term mapping and contract-driven KPI enrichment metadata
- A9_NLP_Interface_Agent: For advanced natural language processing (future)
- A9_LLM_Service_Agent: For SQL generation from natural language queries
- `AuditService` (`src/services/audit_service.py`, 2026-10-02) — plain static service, not an agent, not registry-instantiated. `detect_situations` writes a `reliability.kpi_coverage` event per call (see Phase 9A correction section above). Never raises; a missing pool or failed write degrades silently.

## LLM Configuration (Anthropic — via A9_LLM_Service_Agent)
| Use | Task Type | Model | Rationale |
|-----|-----------|-------|-----------|
| Situation-card observations | `nlp_parsing` (temperature 0.2) | `claude-haiku-4-5-20251001` | 2–3 short plain-language KPI observations as JSON array |
| Headline-vs-trend tension one-liner | `nlp_parsing` (temperature 0.2) | `claude-haiku-4-5-20251001` | Single-sentence tension framing for CFO |
| `sql_generation` (NL query path) | `sql_generation` | `claude-haiku-4-5-20251001` | Fast, cost-effective SQL generation from natural language |

Environment variable overrides: `CLAUDE_MODEL_NLP` (observations + tension line), `CLAUDE_MODEL_SQL`. As of Jul 2026 all SA call sites resolve models via `get_claude_model_for_task()` — no hardcoded model strings remain.

## Assignment & HITL
- Delayed assignment until Deep Analysis completes; ownership mapping can be more precise once scope is identified across dimensions.
- Fallback child breakdown dimensions are defined in the Data Product YAML (e.g., `fallback_group_by_dimensions`).
- Action types supported: `notify`, `assign`, `delegate`, `escalate`, `snooze`, `open_view`, `export`.
- Situation model fields extended:
  - `parent_id`, `status`, `hitl_required`, `assignee_id`
  - `assignment_candidates[]`, `assignment_decision{}`
  - `dedupe_key`, `cooldown_until`, `tags`, `provenance`, `lineage`
- Entrypoints (orchestrated):
  - `propose_assignment_candidates(situation_id)` – delegates to Principal Context/HR; fallback to Process Owner from Business Process registry when HR mapping is unavailable.
  - `apply_action(situation_id, action)` – applies `ActionType` (including `DELEGATE`) and updates situation state.

## Compliance Status
- [x] Follows A9 Agent naming convention (A9_Situation_Awareness_Agent)
- [x] Implements required protocol methods
- [x] Provides proper Pydantic v2 models
- [x] Includes factory method
- [x] Has agent card documentation
- [ ] Has comprehensive test suite (to be implemented)

## Usage Examples

### Detecting Situations for a CFO
```python
from src.agents.new.a9_situation_awareness_agent import create_situation_awareness_agent
from src.agents.models.situation_awareness_models import (
    SituationDetectionRequest, PrincipalContext, PrincipalRole, 
    BusinessProcess, TimeFrame, ComparisonType
)

# Create the agent
agent = create_situation_awareness_agent({
    "contract_path": "path/to/fi_star_schema.yaml"
})
await agent.connect()

# Define principal context for CFO
cfo_context = PrincipalContext(
    role=PrincipalRole.CFO,
    business_processes=[
        BusinessProcess.PROFITABILITY_ANALYSIS,
        BusinessProcess.REVENUE_GROWTH
    ],
    default_filters={},
    decision_style="strategic",
    communication_style="executive_summary",
    preferred_timeframes=[TimeFrame.CURRENT_QUARTER]
)

# Create request
request = SituationDetectionRequest(
    request_id="req-123",
    principal_context=cfo_context,
    business_processes=[BusinessProcess.PROFITABILITY_ANALYSIS],
    timeframe=TimeFrame.CURRENT_QUARTER,
    comparison_type=ComparisonType.QUARTER_OVER_QUARTER
)

# Detect situations
response = await agent.detect_situations(request)

# Process results
for situation in response.situations:
    print(f"{situation.severity}: {situation.description}")
    print(f"Business Impact: {situation.business_impact}")
    if situation.suggested_actions:
        print("Suggested Actions:")
        for action in situation.suggested_actions:
            print(f"- {action}")
    print()
```

## Recent Updates (Dec 2025)
- Contract path consolidated to single source of truth in `registry_references`
- Default contract path: `src/registry_references/data_product_registry/data_products/fi_star_schema.yaml`
- Principal KPI preference support added: KPI ordering now respects principal profile metadata (`kpi_line_preference`, `kpi_altitude_preference`) and KPI registry metadata (`line`, `altitude`) before situation detection

## Recent Updates (Feb 2026)
- Multi-tenant `client_id` support: KPI scan filters by `client_id` from request; passes `client_id` to SA request model
- BigQuery KPI detection: checks `sql_query`/`calculation` for backtick-qualified table refs; bypasses DuckDB/time_dim path and uses `_bq_apply_period()` for date filtering

## Opportunity Detection (Mar 2026, updated Phase 11C)

### Overview
Alongside problem detection, the agent detects **positive KPI opportunities** — KPIs trending
significantly better than expected. High-confidence signals (≥ 0.7) are converted to `Situation`
cards with `direction='up'` via `Situation.from_opportunity_signal()` and appear in the unified
`situations` list. **`SituationDetectionResponse.opportunities` is always empty as of Phase 11C.**

### Direction Field (Phase 11C)
`Situation.direction` is the canonical signal direction:
- `'down'` — breach/problem card (red in UI)
- `'up'` — opportunity/outperformance card (green in UI)

`card_type` (`"problem"` / `"opportunity"`) is retained for backward compatibility but `direction`
takes precedence in new code.

### Opportunity Types
| Type | When fired |
|---|---|
| `outperformance` | Current value exceeds the best defined threshold × `opportunity_threshold_multiplier` |
| `recovery` | KPI was previously below a threshold and has now crossed back above it, with ≥ `opportunity_recovery_min_delta_pct` % improvement |
| `trend_reversal` | No absolute threshold but period-on-period improvement ≥ `opportunity_threshold_multiplier × 10` % |

### Configuration (`A9_Situation_Awareness_Agent_Config`)
| Field | Default | Description |
|---|---|---|
| `opportunity_threshold_multiplier` | `1.5` | How much above threshold (×) the current value must be for outperformance. Must be ≥ 1.0. |
| `opportunity_recovery_min_delta_pct` | `5.0` | Minimum % improvement to qualify as a recovery signal. |

Pass config overrides via the `config` dict on agent construction:
```python
agent = A9_Situation_Awareness_Agent({
    "opportunity_threshold_multiplier": 2.0,
    "opportunity_recovery_min_delta_pct": 8.0,
})
```

### `OpportunitySignal` Model
```python
class OpportunitySignal(BaseModel):
    kpi_name: str                      # Internal KPI name
    kpi_display_name: str              # Human-readable name
    current_value: float               # Current period value
    baseline_value: float              # Comparison baseline (threshold or prior period)
    delta_pct: float                   # Positive = improvement
    dimension: Optional[str]           # Populated if signal is dimension-specific
    dimension_value: Optional[str]
    opportunity_type: str              # "outperformance" | "recovery" | "trend_reversal"
    headline: str                      # e.g. "Gross Margin up 3.2pp vs prior period"
    confidence: float                  # 0.0–1.0
```

### `SituationDetectionResponse`
```python
class SituationDetectionResponse(BaseResponse):
    situations: List[Situation]             # unified stream — both problem and opportunity cards
    opportunities: List[OpportunitySignal]  # DEPRECATED (Phase 11C) — always []
    ...
```

### Design Notes
- `_detect_opportunities()` still runs per-KPI; high-confidence results become `Situation` cards with `direction='up'`.
- `opportunities` field in the response is always `[]` — consumers should read `situations` only.
- Situations sorted: severity desc, then `abs(percent_change)` desc within each severity bucket.

## Monthly Series for Trend Visualization (Apr 2026)
- `_bq_monthly_series_sql(base_sql, date_col, num_months=9)` — generates BigQuery/Snowflake/DuckDB SQL returning monthly aggregates for the last N months via `LEFT(date_col, 7)` + `LIMIT n`
- `_ss_monthly_series_sql(base_sql, year_col, period_col, num_months=9)` — T-SQL equivalent: `TOP n` subquery grouping on fiscal_year + fiscal_period integer columns; period returned as `YYYY-PP`; used for SQL Server (Hess) KPIs when `TimeDimensionSpec.type == "fiscal_year_period"`
- `_sf_monthly_series_sql(base_sql, year_col, period_col, num_months=9)` — Snowflake equivalent: `LIMIT n` subquery, `||` concatenation, bare column names; used for Snowflake (Apex Lubricants) KPIs when `TimeDimensionSpec.type == "fiscal_year_period"`
- `_resolve_time_spec_sa(data_product_id)` — reads `TimeDimensionSpec` dict from the data product registry; used to determine year/period column names for the SS monthly builder
- Monthly series query runs after current + comparison queries in `_get_kpi_value()` for BQ, SF, and SS KPIs
- Results stored as `KPIValue.monthly_values: Optional[List[Dict[str, Any]]]` — each entry: `{period: str, value: float}`
- Frontend KPITile renders real 9-month bar charts from this data (replaces previous fake sparklines)

## Phase 9A Behaviour Changes

**Card correction (2026-10-02) — this section describes `run_enterprise_assessment.py`'s
`EnterpriseAssessmentEngine._assess_kpi`, not this agent.** Verified by grep while wiring the
stage-wise reliability panel (`docs/architecture/audit_event_system_design.md`): `confidence_floor`,
`monitoring_profile`, `assessment_mode`, and `escalate_to_da` do not appear anywhere in
`a9_situation_awareness_agent.py`. `detect_situations` itself has no monitoring-profile gating,
no `assessment_mode` parameter, and never sets a `"monitoring"` or `"below_threshold"` status —
those are `KPIAssessmentStatus` values the assessment script derives *after* calling
`detect_situations`, by reading `monitoring_profile` off the KPI registry record itself and
comparing SA's returned `confidence`/`severity` against the script's own floors. This matches
root `CLAUDE.md`'s own "What's NOT Built Yet" note — "SA runtime use pending Phase 9B" — which this
section's prose contradicted by describing the gate as already live inside SA. The section below is
kept as a description of the *assessment engine's* behavior, with the call sites corrected; treat
it as documentation of `run_enterprise_assessment.py`, not of this agent, until Phase 9B actually
moves this logic into `detect_situations`.

### Monitoring Profile Support (actually: `run_enterprise_assessment.py::_assess_kpi`)
`EnterpriseAssessmentEngine._assess_kpi` reads each KPI's `monitoring_profile` from the KPI
registry record it was handed (not from a `detect_situations` parameter) and, after calling
`detect_situations`, applies:
- `volatility_band` — read but not yet used to filter noise in the current implementation
- `confidence_floor` — gate on SA's returned `confidence`; below floor → `KPIAssessmentStatus.MONITORING`

**Correction (code-review, 2026-10-02): `comparison_period` IS read** — `_timeframe_for_kpi()` (`run_enterprise_assessment.py:226-233`) reads `monitoring_profile.comparison_period` and maps it to a `TimeFrame` via `_COMPARISON_PERIOD_TO_TIMEFRAME`; `_assess_kpi` calls it at line 340. Only `min_breach_duration` (`MonitoringProfile`, `src/registry/models/kpi.py`) is genuinely unread today — Phase 9B scope. The line above was wrong when first written in this same correction pass; verified by grep, not assumed.

### Assessment Engine Integration (actually: `run_enterprise_assessment.py`)
`EnterpriseAssessmentEngine.run()` processes one KPI per `_assess_kpi` call. `KPIAssessment`
(`src/agents/models/assessment_models.py`) carries `escalated_to_da: bool` — currently always
`False` by explicit design ("DA is HITL — principal decides from Decision Studio UI"), so despite
the field's name this is not live automatic routing to DA.

### KPIAssessment Status Values (in the assessment script, not SituationDetectionResponse)
| Status | Meaning |
|--------|---------|
| `DETECTED` | Confidence ≥ floor and severity ≥ floor; also emits a `reliability.detection_confidence` `pass` audit event (2026-10-02) |
| `MONITORING` | Confidence < floor; also emits the same event_type with `outcome="abstain"` — inconclusive, not a defect, per the audit-event design note's retention table |
| `BELOW_THRESHOLD` | Severity < `severity_floor`, or no matching situation returned at all; no reliability event — this is a severity gate, deliberately not conflated with the confidence signal |
| `ERROR` | `detect_situations` raised; also emits `outcome="fail"` — rare by construction, unlike `MONITORING`'s abstain |

`"problem"` and `"opportunity"` card_type values are **deprecated** (Phase 9G removal). SA is a sensor only.

### Reliability panel signal (2026-10-02 — fifth and final pilot, after DA's `[ROLLUP-CHECK]`, SA's own detection-confidence gate above, DGA's slice-validity check, and the theory-layer exhibit's tree-reconciliation check)
`detect_situations` now emits one `reliability.kpi_coverage` audit event per call via `AuditService` (`src/services/audit_service.py`) — the only one of the five signals that did not already compute anything. `_get_relevant_kpis()` gained an optional `coverage_out: Dict[str, int]` parameter, populated in place with `{"registered": N, "evaluated": M}` before it returns (`registered` = every KPI this client has at all, before any filter; `evaluated` = how many survived every filter). The method stays synchronous (three call sites) and has no idea `AuditService` exists; `detect_situations` reads the dict after the call and does the actual `await AuditService.log(...)`.

`_kpi_coverage_outcome(registered, evaluated)` (module-level function, same file) is the decision: `registered == 0` → skip entirely (nothing registered yet is not a defect); `registered > 0 and evaluated == 0` → `fail`; any other nonzero `evaluated` → `pass`. This is deliberately narrow — it does **not** flag every principal whose relevant set is smaller than the client's full registry (normal business-process scoping), only the Brookshire Brothers shape: every registered KPI dropped at once. **Known, disclosed false positive:** a principal whose own `business_processes` genuinely share no overlap with anything registered for this client also evaluates to zero, correctly, and also reads as `fail` — advisory telemetry, same non-gating posture as `not_sliceable_by` and the ROLLUP-CHECK warning, not a hard assertion that every `fail` is a bug.

Tests: `tests/unit/test_sa_kpi_coverage_reliability_event.py`, including a fixture reproducing the Brookshire Brothers shape (non-empty, non-overlapping `business_processes` on both sides) against today's already-fixed fail-open logic, to prove the signal fires on a genuine zero-overlap case and not only on the empty-list shortcut the original bug exploited.

**`request_id` was missing here too (found and fixed 2026-10-03, same sweep as DA and MA's identical
bug).** The `AuditService.log()` call never passed `request_id` — fixed with `request_id=
original_request_id` (already minted at the top of `detect_situations` for the response). Lower
stakes than DA/MA's fix since `kpi_coverage` is a fleet-level-per-call signal with no natural
per-situation correlation target anyway, but consistent with every other signal now carrying one.

## Phase 10B Improvements (Apr 2026)

### Client Scoping Refactor
- `_get_relevant_kpis()` now accepts `client_id` parameter
- Prevents cross-client KPI name collisions (two clients may have "Gross Revenue")
- Client scoping happens at KPI retrieval time, not post-filtering
- Supports Phase 10B-DGA architecture where DGA routes correct Data Products per client

### Situation Deduplication
- Deduplicates by `(kpi_name, alert_type)` — each distinct alert pattern (threshold_breach, plan_variance, projected_breach, acceleration) produces its own card. Within the same `(kpi_name, alert_type)` pair, keeps highest-severity entry only.
- Prevents duplicate situation cards in the UI when a KPI crosses multiple severity lines
- Preserves sort order (critical → high → medium → low)

### Threshold Format Support (YAML + Supabase)
- **Format A (YAML KPIs):** `severity`/`value` structure with optional `inverse_logic` flag
- **Format B (Supabase KPIs):** `comparison_type` + `variance_thresholds` metadata
- Both formats support inverse_logic for cost/expense KPIs where lower is better

### Inverse Logic (Cost KPI) Improvements
- Reads `inverse_logic` flag from threshold config or `positive_trend_is_good` metadata
- Sign-flips `percent_change` so "costs went up" always shows as a positive number
- Applies to both situation detection and opportunity signals
- Handles both YAML and Supabase KPI formats

### Opportunity Detection for Supabase KPIs
- Format B percent-change-based detection using `variance_thresholds` metadata
- Detects outperformance when `percent_change` exceeds green threshold
- Handles inverse_logic (costs fell below target, showing as opportunity)
- Confidence: 0.75 for outperformance, 0.75 for recovery with inverse logic

### Opportunity Threshold Calibration
- Changed `opportunity_threshold_multiplier` from 1.5 → 1.1 (more sensitive to upside)
- Captures more KPI recovery and outperformance signals
- Aligns with Phase 8 opportunity detection design

## inverse_logic Sign-Flip Fix (Apr 2026)

### Root Cause
`_get_kpi_value()` applied `percent_change = -percent_change` for ALL inverse_logic KPIs (line ~2256).
This worked for KPIs where SQL returns raw negative debits (`SUM(amount)` with negative amount records).
For lubricants BigQuery/SS KPIs that negate at SQL level (`SUM(-amount)`), values are already positive —
applying the sign-flip created double-negation: a 19.5% cost increase became -19.5%, which the
`vt_cfg` inverse_logic threshold check (`percent_change <= green_threshold`) treated as "within green."

### Fix
Guard the sign-flip: only apply when `current_value < 0` (actual negative raw values).
KPIs with SQL-level negation (`SUM(-amount)`) return positive values — skip the flip.

### Downstream Impact Fixed
- SA severity: INFORMATION → CRITICAL for threshold-breaching cost KPIs
- SA direction: "decreased" → "increased" in situation descriptions
- DA SCQA framing: now uses correct direction ("over-performing vs prior period" for cost overruns)
- DA dimensional IS/IS NOT: BigQuery breakdown preserves SUM(-amount) → positive deltas →
  correctly classifies segments with `delta > 0` as IS (problem) when `trend_positive=False`

## Phase 10B-DGA: Data Governance Wiring (Apr 2026)

### client_id Propagation to KPI Filtering
- `_get_relevant_kpis()` now accepts `client_id` parameter; all 3 call sites pass `principal_context.client_id`
- KPIs without business_processes no longer bypass client filter — client scoping happens at retrieval time
- Prevents cross-client KPI name collisions (e.g., two clients both have "Gross Revenue")
- DG agent no longer has fallback acquisition in `_async_init()` — client_id flows through properly scoped KPI queries

### Circular Dependency Elimination
- Removed broken DGA fallback acquisition from `_async_init()` — was silently failing and losing error context
- DGA is now wired post-bootstrap by A9_Orchestrator via `runtime._wire_governance_dependencies()`
- SA agent sets `data_governance_agent = None` at init; runtime injects DGA after connection phase
- All view/KPI resolution calls (detect_situations, process_nl_query, get_kpi_definitions) use the injected agent

### DGA Governance as Mandatory Path (Fallback Cleanup)
- Removed 3 remaining `if self.data_governance_agent:` guards from `process_nl_query()`:
  - `translate_business_terms()` (line ~648): DGA call now always attempted
  - `map_kpis_to_data_products()` (line ~686): DGA call now always attempted
  - HITL unmapped terms check (line ~951): removed DGA None dependency
- DGA unavailability logs at WARNING level (fallback paths still work if DGA fails, but operator sees the warning)
- Ensures governance is never silently skipped — if DGA is None, exception is caught and logged

### Impact
- Workflow-level client isolation now enforced at KPI retrieval, not post-hoc filtering
- Assessment engine can safely run parallel per-KPI scans across multiple principals without cross-client data leakage
- DGA is now a primary dependency (failures are visible), not an optional optimization

## Phase 11I-A — Advanced Alert Intelligence (Jun 2026)

### Four New Detection Patterns

All patterns run in the per-KPI loop after `_detect_kpi_situations()`. Each sets `Situation.alert_type` to distinguish it from a standard threshold breach.

#### Threshold-presence gating (Option A)
Each statistical pattern runs **only if the KPI carries a registry `KPIThreshold` row for the matching `comparison_type`** — presence of the row is the per-KPI on/off switch. A KPI's "nature" is expressed by which threshold rows its seed carries (a covenant flag might carry only `yoy`; a smooth revenue KPI carries all four). Registry `KPIThreshold` rows are mapped into `kpi_def.metadata['variance_thresholds'][<key>]` by `_convert_to_kpi_definition()`. Relevant `ComparisonType` keys: the period comparisons (threshold_breach; `ytd_vs_pytd` is what every scan reads today), `plan_variance`, `projected_breach`, `acceleration`. Rows are filed and looked up through `_threshold_key()` (Phase 26, below).

#### Pattern 1: Plan / Budget Variance (`alert_type = "plan_variance"`)
- Requires `KPI.plan_version_value` set (e.g. `"Budget"`). SA derives the plan SQL at runtime by substituting the version filter in `sql_query` via `_derive_plan_sql()` — no separate SQL field stored.
- `_fetch_plan_value()` executes the plan SQL via DPA using a `model_copy`-substituted KPI definition.
- Severity bands read per-KPI from `variance_thresholds['plan_variance']` (green→MEDIUM trigger, yellow→HIGH, red→CRITICAL, as percent magnitudes); falls back to 2% / 8% / 15% when unconfigured.
- `bad_direction = variance_pct < 0` (sign already encodes direction for both positive-stored revenue and negative-stored costs — `inverse_logic` is NOT re-applied). Wording is **polarity-aware**: a cost over budget reads "above plan", a cost under budget "below plan"; revenue reversed.
- `Situation.plan_value` stores the budget reference value.

#### Pattern 2: Projected Threshold Breach (`alert_type = "projected_breach"`)
- Gated on `variance_thresholds['projected_breach']` **and** `plan_version_value` (needs the budget value).
- **Budget-anchored (dominant FP&A practice):** the registry row stores a percent-of-budget tolerance (`red`), NOT a static dollar floor. At scan time SA derives the absolute floor: `monthly_budget = budget / months-in-timeframe` (additive `$` KPIs) or `= budget` (rate `%` KPIs — no division), then `floor = monthly_budget − |monthly_budget| × (red%/100)`. `_timeframe_month_count()` supplies the run-rate divisor.
- `_project_trend()` fits a linear regression over `KPIValue.monthly_values` (trailing `lookback=6`), projects `horizon=3` forward, and fires when the projected value falls below `floor` (always `inverse_logic=False` — negative-stored costs already encode direction).
- Suppressed if R² < 0.4 (noisy data) or if a `threshold_breach` already fired for the same KPI in the same run.
- Fields set: `plan_value` (budget), `projected_breach_at_period`, `projection_confidence` (R²), `periods_until_breach`.

#### Pattern 3: Rate-of-Change Acceleration (`alert_type = "acceleration"`)
- Gated on `variance_thresholds['acceleration']`. `_compute_acceleration()` computes the second derivative of `monthly_values`; fires when `|second_derivative| > fire_multiplier × rolling std dev of velocity`.
- Sensitivity is per-KPI: `yellow` = fire floor multiplier (default 2.0), `red` = HIGH-severity cutoff on the normalised signal (default 3.0, else MEDIUM).
- `Situation.acceleration_signal` = normalised second-derivative magnitude (signal / velocity_std).
- Requires ≥4 periods of monthly history. Does not suppress for threshold breaches — a KPI can be in-threshold but accelerating toward it.

#### Pattern 4: KPI Type Classification (`kpi_type` field)
- New field on `KPI` registry model and `KPIDefinition`: `"operational"` (default) | `"concentration"` | `"covenant"` | `"regulatory"`.
- Covenant/regulatory KPIs: severity overridden to `CRITICAL`; `alert_type` set to `"covenant"` or `"regulatory"`.
- Concentration KPIs: monitored identically; `kpi_type` flows to DA and PIB for framing only.

### New Situation Fields (11I-A)
| Field | Type | Description |
|---|---|---|
| `alert_type` | `Optional[str]` | `"threshold_breach"` \| `"plan_variance"` \| `"projected_breach"` \| `"acceleration"` \| `"concentration"` \| `"covenant"` |
| `plan_value` | `Optional[float]` | Budget/plan reference value (plan_variance alerts) |
| `projected_breach_at_period` | `Optional[str]` | Estimated period string e.g. `"t+2"` |
| `projection_confidence` | `Optional[float]` | R² of linear trend fit |
| `periods_until_breach` | `Optional[int]` | Estimated periods until threshold crossing |
| `acceleration_signal` | `Optional[float]` | Second-derivative magnitude / velocity std |

### New KPI Registry Fields (11I-A)
| Field | Type | Description |
|---|---|---|
| `plan_version_value` | `Optional[str]` | Version filter for plan SQL (e.g. `"Budget"`). `None` = skip plan variance. |
| `kpi_type` | `str` | `"operational"` \| `"concentration"` \| `"covenant"` \| `"regulatory"` |

### New `ComparisonType` values (11I-A)
`ComparisonType` (`src/registry/models/kpi.py`) gains `PLAN_VARIANCE`, `PROJECTED_BREACH`, and `ACCELERATION`. Seed a `KPIThreshold` row with the matching `comparison_type` to enable that pattern per-KPI (threshold-presence gating). Conventions: `plan_variance`/`projected_breach` store percent-of-budget tolerances in green/yellow/red; `acceleration` stores `yellow` (fire ×) and `red` (HIGH ×) multipliers (green unused).

## Phase 11I-B — Compound Cross-KPI Alert Detection (Jun 2026)

### KPI Relationship Registry
- New `KPIRelationship` model (`src/registry/models/kpi_relationship.py`): `kpi_id`, `related_kpi_id`, `client_id`, `relationship_type` (`volume_margin` | `receivables_revenue` | `cost_revenue` | `custom`), `conflict_direction` (`diverging` | `converging`), `description`.
- Backed by `kpi_relationships` Supabase table with composite PK `(client_id, kpi_id, related_kpi_id)`.
- `KPIRelationshipProvider` follows the direct-instantiation asyncpg pattern (not registered in `RegistryFactory`).
- REST API: `GET/POST/DELETE /api/v1/registry/kpi-relationships/`.

### Compound Detection (`_detect_compound_alerts()`)
Post-processing step called in `detect_situations()` after the main KPI loop, before deduplication.
1. Builds a `{kpi_id: normalised_direction}` map from all current-run situations (+1 = good, -1 = bad, accounting for `inverse_logic`).
2. For each KPI with a situation, loads its declared relationships via `KPIRelationshipProvider`.
3. If both KPIs in a pair have situations and the conflict condition is met (`diverging` = opposite directions, `converging` = same direction), sets `compound_alert = True`, `related_kpi_id`, and `compound_pattern` on both situations.

### New Situation Fields (11I-B)
| Field | Type | Description |
|---|---|---|
| `compound_alert` | `bool` | `True` when part of a declared cross-KPI conflict |
| `related_kpi_id` | `Optional[str]` | The other KPI in the compound pair |
| `compound_pattern` | `Optional[str]` | Human-readable tension e.g. `"Revenue UP / Gross Margin DOWN — pricing or mix pressure"` |

## Same-KPI Multi-Alert-Type Consolidation (`_merge_compound_kpi_situations()`) (Jul 2026)

A single KPI can trigger several 11I-A/11I-B patterns in one scan (e.g. `threshold_breach` + `plan_variance`; per live Hess data this is the *common* case for revenue/profitability KPIs, not an edge case). Without consolidation each pattern becomes its own `Situation`, duplicating the KPI in the UI and inflating finding counts.

Called in `detect_situations()` after `_detect_compound_alerts()` and after the `(kpi_name, alert_type)` dedup step, right before sorting:
1. Groups all `card_type == "problem"` situations by `kpi_name` (`card_type == "opportunity"` passes through untouched — never merged).
2. Sorts each group by severity; the most-severe member becomes `primary` (ties broken by original list order — `threshold_breach` is detected before `plan_variance`/`projected_breach`/`acceleration` in the per-KPI loop, so it usually wins ties and becomes primary).
3. Builds the merged card via `primary.model_copy(update={...})`:
   - `merged_alert_types`: every distinct `alert_type` folded in (`primary.alert_type` itself is left unchanged — it still reflects only the primary member's own pattern).
   - `business_impact`: concatenated bullets from all members (` • `-joined, capped at 4).
   - `key_observations`: deduped union, capped at 6.
   - `hitl_required`: `True` if **any** member requires it.
   - `tags`: union of all members' tags, plus `"compound_multi_alert"`.

**Pattern-specific fields are pulled from whichever member set them, not from `primary` alone** (fixed Jul 2026 — see below): `plan_value`, `projected_breach_at_period`, `projection_confidence`, `periods_until_breach`, `acceleration_signal`, `compound_alert`, `related_kpi_id`, `compound_pattern`. These fields are mutually exclusive by construction — only the plan_variance-tagged situation ever sets `plan_value`, only the projected_breach one sets `projected_breach_at_period`, etc. — so scanning all members for a non-`None` value has no conflict to resolve.

**Bug fixed Jul 2026:** the initial version only copied the five fields above (`merged_alert_types`/`business_impact`/`key_observations`/`hitl_required`/`tags`) via `model_copy`; every pattern-specific field silently fell back to `primary`'s own value. Since `threshold_breach` usually wins the primary slot, this meant `plan_value` was `None` on most merged cards despite `merged_alert_types` correctly listing `plan_variance` as present — breaking VA's `plan_value_at_approval` capture (11I-C) for any KPI with a compound alert, and suppressing the `KPITile` alert badge (which reads `alert_type`, sees `threshold_breach`, and renders nothing). Verified fixed against a live Hess scan: 3 of 4 merged cards had `threshold_breach` as primary, all three now correctly carry `plan_value`.

**Known follow-up (not yet built):** `KPITile.tsx`'s alert badge still reads only `situation.alert_type` (singular) — it will show the primary pattern's badge but not surface the other folded-in patterns from `merged_alert_types`. Separately, DA's own alert-type-aware SCQA framing (`DeepAnalysisRequest.alert_type`/`.compound_pattern`, consumed in `a9_deep_analysis_agent.py`'s prompt construction) is structurally unreachable from the live workflow — `DeepAnalysisWorkflowRequest` (the HTTP-level model `workflows.py` actually builds) has no field to carry `alert_type`/`compound_pattern`/`merged_alert_types` through, and the route never looks them up from the situation. This predates this fix and is a separate, untracked gap.

## Future Enhancements
- Integration with A9_NLP_Interface_Agent for advanced query parsing
- Enhanced business impact analysis using LLM
- Machine learning-based anomaly detection
- Multi-dimensional trend analysis
- Enhanced visualization capabilities in Decision Studio UI

- May 2026: Bug fixes — NaN normalization, multi-tenant kpi_registry collision fix, comparison value extraction
- May 2026 (Infra A4-a): Per-request KPI registry refresh — `detect_situations`, `process_nl_query`, and `get_kpi_definitions` now call `_load_kpi_registry()` on every invocation so new clients/KPIs seeded post-startup are visible without a service restart.
- May 2026: `_convert_to_kpi_definition` propagates `id` (machine key) from raw KPI so accountability filtering in `_get_relevant_kpis` can match `kpi_accountability.kpi_id`.
- May 2026: `_assess_kpi_opportunity()` — `percent_change` now reads from `kpi_value.percent_change` (which has `inverse_logic` sign-flip already applied) rather than recomputing raw `(current − comparison) / abs(comparison)`. Recomputation used wrong-sign values for cost KPIs stored as negative debits, causing cost decreases to appear as worsening.
- May 2026: `trend_reversal` signal gated behind `not _has_vt` — skipped when the KPI has Supabase `variance_thresholds` metadata. `trend_reversal` fires at confidence 0.65 (below the 0.7 Situation threshold), and its presence in `signals` was blocking the Format-B variance-threshold check via the `not signals` guard, preventing correct CRITICAL/HIGH severity detection for Format-B KPIs.
- May 2026: Format-B `_assess_kpi_variance_threshold()` — `percent_change` also reads from `kpi_value.percent_change` for the same inverse_logic correctness reason.
- Jul 2026 (fail-open relevance gates): `_get_relevant_kpis()` had two gates that could silently zero out a real, correctly-configured KPI with no error surfaced. Found live 2026-07-25 onboarding Brookshire Brothers: 5 newly-registered KPIs (real thresholds, real SQL) produced zero situations.
  1. **Business-process match**: an empty `principal.business_processes` (never assigned during onboarding — Day 2 runs before Day 3 creates real BPs) was read as "match nothing" rather than "no filter configured," excluding every KPI that *does* have `business_process_ids`. Now: `if not process_strings or not kpi_def.business_processes:` — empty on either side means include, not exclude.
  2. **Accountability filter**: `detect_situations` now fetches the whole client's accountability assignments (`KPIAccountabilityProvider().get_all(client_id)`, not just `get_for_principal`) to build `assigned_anywhere_kpi_ids` alongside the principal's own `accountable_kpi_ids`. A KPI is only excluded when it's assigned to *someone* and not this principal — a KPI nobody has claimed yet stays visible instead of being hidden just because the requesting principal happens to have unrelated assignments elsewhere (CFO's 4 assignments against old KPIs were previously hiding 5 brand-new, wholly-unassigned KPIs from every principal).
- Jul 2026: **`KPIValue.unit` was never populated, system-wide, for every situation card ever produced.** `_get_kpi_value()` builds `KPIValue` at two return points and neither ever set `unit=`, despite the field existing on the model — `KPIDefinition.unit` (a sibling model, correctly populated from the registry) was simply never threaded through. Found via the Action Center's "Problem exposure $3 / Opportunity upside $139" — those were raw percentage-point deltas with a hardcoded dollar sign slapped on by the frontend, since it had no real unit to go on. Fixed by adding `unit=getattr(kpi_definition, 'unit', None)` to both `KPIValue(...)` construction points. This also fixes the equivalent bug in `A9_Deep_Analysis_Agent`'s SCQA narrative (see its card) and the Executive Briefing's Cost of Inaction banner, all of which read this same field.
  Both are deliberately "fail open on incomplete registry data" defaults, kept intentionally narrow pending a possible broader RACI-based accountability model (see `docs/architecture/kpi_accountability_model.md`) — not a redesign of the relevance/accountability mechanism itself.
- **Aug 2026 — silent data loss now counted, not swallowed.** An architecture sweep by failure class found `except: pass` around the monthly-series `float()` coercion: unparseable rows were dropped and the log then reported `"Got N monthly values"`, i.e. the SURVIVING count as if it were the queried count. Not cosmetic — `_compute_acceleration` needs ≥4 points, so a silent drop to 3 makes that signal never fire *invisibly*, and `_project_trend` fits the projected-breach regression over whatever survives. Drops are now counted and warned; the handler still does not raise (defensive coercion is correct here) but a loss must announce itself.
- **Aug 2026: `KPIValue.context` (`MeasurementContext`) — provenance stamped on every reading.** `KPIValue.timeframe` records the *token* (`"year_to_date"`), which is an instruction, not a fact. SA resolves windows with its own `_bq_get_period_dates`; the DPA uses the shared `TimeFilter` (**38 uses in DPA, 0 in SA** — SA's BigQuery path bypasses it by design, see the comment at `_bq_get_period_dates`). They currently agree, and nothing enforced that they keep agreeing. Now every `KPIValue` carries the **resolved** window/comparison window, `version` (`Actual` | `Budget` | `plan_version_value`), filters, `source_system`, `data_product_id`, and a 12-char `sql_hash`.
  - **What it fixed immediately:** an assessment legitimately reads the same KPI twice — Actual, then Budget via `_fetch_plan_value`, which rewrites `calculation` to the plan variant. With no version stamp, the log showed `Net Revenue = 94,271,804.70` and `Net Revenue = 107,769,900.00` one second apart under one name, which reads as corruption and cost real time to rule out. Log lines now carry `[Actual | 2026-01-01..2026-08-08 | bigquery]`.
  - **Version detection uses the SQL, not the KPI name** — `_fetch_plan_value` leaves the name unchanged, so the substituted `plan_version_value` appearing in the executed SQL is the only reliable marker.
  - **Why this before unifying the window implementations:** stamping converts an invisible risk into a testable assertion (`sa.context.window() == da.context.window()`), and tells us whether the riskier SA→`TimeFilter` refactor is needed rather than assuming it.
  - **`comparison_basis` — not every KPI comparison is current-vs-prior.** The first cut asked `_bq_get_period_dates` for a comparison window regardless of type; that helper only understands PERIODS and falls back to *last month* for anything it does not recognise, so `budget_vs_actual`, `target_vs_actual` and `benchmark` were all stamped `2025-12-01..2025-12-31` — a real-looking range that means nothing. A fabricated window is worse than an absent one: something downstream can compare against it and "confirm" agreement never checked. Now:

    | basis | comparison is | window stamped |
    |---|---|---|
    | `temporal` | prior window (YoY / QoQ / MoM) | prior period |
    | `version` | **same window**, other version (`budget_vs_actual`, `target_vs_actual`) | = current window |
    | `peer` | benchmark cohort, no time shift | **none** |
    | `projection` | forecast vs a budget-derived floor (`floor = monthly_budget − |monthly_budget| × tol`), horizon in `periods_until_breach` | **none** |
    | `series` | 2nd derivative over ≥4 monthly points (`_compute_acceleration`) | **none** |

    Cross-agent window equality is therefore only meaningful **within** a basis — comparing a plan variance against a YoY would flag a difference that is correct by definition.
  - Every field optional — purely additive; absence means "unknown provenance" and must **never** be read as a match. `_build_measurement_context()` never raises: provenance is bookkeeping and must not be able to break a measurement. Tests: `tests/unit/test_measurement_context.py` (24).

## Situation Description States the Window It Measured — `_window_suffix()` (Aug 2026)

**Bug fixed:** a live 12-page executive briefing carried **three** different characterisations of "the KPI's decline" on adjacent pages, none of them labelled:

| stated | source | actual window |
|---|---|---|
| "decreased by **12.9%** vs prior year" | SA situation description | one pair |
| "32.63% → 29.94% (Δ **-2.69pp**, **-8.2%**)" | DA enterprise | FY2025 → YTD2026 |
| "**-7.14pp**" (−25.7%) | DA anchor segment | a third pair |

Checked against BigQuery, the windows genuinely differ, so the numbers are **not** in conflict — but nothing said so, and a reader sees a contradiction on page one. SA's description is a sentence with a number baked into it, and Solution Finder carries that sentence **verbatim** into the briefing's problem statement (`a9_solution_finder_agent.py`, "use situation_context.description as the PRIMARY problem statement"), so the unlabelled figure propagates untouched.

**Fix:** `_window_suffix(kpi_value)` renders the resolved window from the `MeasurementContext` already stamped on the reading, appended to both threshold-path descriptions. Emitted **only** for `comparison_basis in ("temporal", "version")` — `peer`, `projection` and `series` have no comparison window, and a fabricated range is worse than none because something downstream can compare against it and "confirm" nothing. Returns `""` when context is absent or incomplete, so an unstamped value degrades to the previous wording rather than inventing dates.

**Related, not fixed here:** the underlying pattern is prose *restating* a figure instead of referencing it. Token substitution (the LLM references `{{kpi.current}}` rather than restating the number, with a basis-aware vocabulary) is the structural fix — see `DEVELOPMENT_PLAN.md` → Phase 15.

## Severity Calibration — AMBER Band Was Unreachable (Aug 2026)

**Bug fixed:** the threshold-breach severity emulation (mirroring `KPI.evaluate()` in
`src/registry/models/kpi.py`) checked the red-threshold condition and then fell through to an
identical `else` — both produced RED. There was no way to distinguish "just missed yellow" (e.g.
+3.3% growth against a yellow=5 band) from "genuinely below red" (e.g. -20%). Every KPI that merely
fell short of yellow reported as CRITICAL. Found live 2026-08-24: 11 of 12 KPIs on a single CFO scan
flagged CRITICAL, several with small positive percent changes.

**Fix:** a genuine `'amber'` evaluation outcome for "missed yellow but still within the red band,"
mapped to `SituationSeverity.MEDIUM` (not CRITICAL). Kept in sync with the canonical model's own
`KPIEvaluationStatus.AMBER`. Verified live: CRITICAL count on the same scan dropped to 5 of 12, with
2 correctly landing in the new MEDIUM tier. Tests: `tests/unit/test_kpi_evaluate_amber_band.py` (11).

## Complete periods only, for period-keyed data products (Oct 2026) 🔴

A data product declares how it keys time in `time_dimensions[0].type`. The declaration now decides
what "the current period" means for a reading (`src/analysis/complete_periods.py`):

| Declared type | Reading taken |
|---|---|
| `fiscal_year_period`, `fiscal_year` (or `date` with a year column and no date column) | as of the last closed month: closed periods only |
| `date` | to the day, as before |

On 13 October, for a period-keyed product: "year to date" is January to September, "current
quarter" is July to September (no month of Q4 has closed), "current month" is September. Each is
compared with the same periods a year earlier. `month_over_month` and `quarter_over_quarter` now
compare whole periods with whole periods.

Before this, the card sliced period-keyed data to the day (1-13 Oct against 1-13 Oct) using a
hard-coded date column, while Deep Analysis read the declared period key. Found live 2026-10-13 on
lubricants Premium Product Mix %: the card said it fell, the analysis said it rose.

How: `_period_as_of(data_product_id)` reads the declaration (remembered for 60 seconds) and returns
the last closed day or None. `_get_kpi_value` passes it as `as_of` to `_bq_apply_period`,
`_bq_get_period_dates` and `_build_measurement_context`; the projected-breach month count uses it
too. The shared `TimeFilter` applies the same rule to its `fiscal_year_period` branch, so Deep
Analysis and the Data Product Agent path resolve the same periods.

Consequences to know:
- Cards for period-keyed products change once a month, when a period closes, not daily.
- A problem that starts in the open month is not flagged until that month closes.
- "Closed" means the calendar month has ended. There is no posting-close calendar; a client whose
  books close on working day 5 will see the prior month before it is final.
- The card still filters on a date column (`metadata.date_column`, default `transaction_date`) with
  whole-month date ranges, while the analysis filters on the year and period columns. They name the
  same periods only where postings are dated inside their own fiscal period and the fiscal year
  starts in January.

Tests: `tests/unit/test_complete_periods.py`, `tests/unit/test_time_filter.py`.

## A KPI that moved the right way but fell short says so (Oct 2026)

Whether a rise is favourable is recorded on the KPI: `inverse_logic` on each threshold row (true =
lower is better), mirrored by `metadata.positive_trend_is_good`. A higher-is-better KPI is still
flagged when its growth is under the green threshold (B2B Revenue: +3.1% against a 5% growth
target). The card was correct; its sentence, "B2B Revenue increased by 3.1% vs prior year", gave no
reason and read as an error. Found live 2026-10-13 on five lubricants KPIs.

`_threshold_sentence()` now writes "grew 3.1% vs prior year, short of the 5.0% growth target" (and
the mirror for a cost that fell by too little, or rose past its limit). With no green threshold the
sentence is unchanged. Test: `tests/unit/test_sa_threshold_sentence.py`.

**Severity follows the distance from target (decided 2026-10-13).** `_severity_for_band()`: `yellow`
(missed green only) is MEDIUM, `amber` (missed yellow too) is HIGH, `red` is CRITICAL. Before this,
`yellow` was HIGH and `amber` MEDIUM, so the smaller miss outranked the larger (live: B2B Revenue
+3.1% against a 5% target was HIGH; E-Commerce Revenue +3.0% against a 15% target was MEDIUM). This
supersedes the "amber maps to MEDIUM" statement in the Aug 2026 amber-band section above.

## Monthly series labels: the period is read as a number (Oct 2026) 🔴

`_ss_monthly_series_sql` built the label with `CAST(fiscal_period AS VARCHAR(2))`. Hess stores the
period as text ('001'..'012'), so every month was labelled `2026-00`. Downstream, a series whose
labels are not distinct calendar months is not trusted (`src/analysis/monthly_series.py`), so no KPI
value was recorded at approval and Value Assurance could not measure any Hess decision. The
Snowflake builder had the same cut waiting (`LPAD(text, 2)` truncates).

Both now convert the period to a number first (`TRY_CAST(... AS INT)` / `TRY_TO_NUMBER`).
Test: `tests/unit/test_sa_monthly_series_labels.py`.

## The card's monthly series holds closed months only (Oct 2026) 🔴

The series fetched for each KPI took the 9 most recent periods as they came. On lubricants that
included October (13 days in) and rows dated November and December. Everything read off the end
of the series inherited them: the tile sparkline, `_generate_trend_note` ("declining 7.6% over the
last three months" described Oct to Dec), `_project_trend`, `_compute_acceleration`, and the
baseline read at approval.

`_fetch_monthly` now asks for `_SERIES_FETCH_MONTHS` (13) and passes the result through
`monthly_series.closed_months_only(keep=9)`, which drops the open month and anything later. A
series whose labels are not distinct calendar months is returned unchanged.
Test: `tests/unit/test_monthly_series.py::TestClosedMonthsOnly`.

## A scan reports the KPIs it could not read (Oct 2026) 🔴

`detect_situations` dropped a KPI whose value could not be read (warehouse unreachable, query
error, no rows) without trace. Found live 2026-10-13: Apex's Snowflake key was missing, every KPI
failed, and the dashboard showed "0 cards", identical to a business with nothing to flag. The
screen's "N KPIs evaluated" was also the number of CARDS, because the UI client dropped
`kpi_evaluated_count`.

`SituationDetectionResponse.kpis_unread` now lists every in-scope KPI with no value (falsy result,
`value is None`, or an exception). The UI client passes it and `kpi_evaluated_count` through; the
summary strip shows "N KPIs could not be read" or, when nothing was read, "No KPI could be read from
the data source … not a clean result". Test: `tests/unit/test_sa_unread_kpis.py`.

**A failed or empty read is not zero.** `_get_kpi_value` turned a failed query, no rows, or a NULL
total into `current_value = 0.0`. With Snowflake unreachable every Apex KPI read 0.0 against a
prior-year 0.0 and nothing was flagged. It now returns None (the KPI is reported in `kpis_unread`).
Live check with the Snowflake key made unreachable: Apex 7 of 7 unread with the "No KPI could be
read" warning on screen; lubricants 2 unread (Gross Revenue, Sales Tax Collected) and Hess 5 unread,
all of which had been reading as 0.0. The orchestrator now passes `kpi_evaluated_count` and
`kpis_unread` through, and the `/situations/run` route marks an orchestrator "error" as a failed
workflow.

**A percentage KPI's change is stated in points (2026-10-14).** "Gross Margin % decreased by 13.0%"
read as 13 points; the fall was 4.48 points (34.43% to 29.95%), seen in a production briefing.
`_point_change()` detects a percentage KPI (unit or name ends in "%") and `_threshold_sentence` /
the opportunity headline now say "decreased by 4.5 points (13.0%)". Targets stay in relative %
because the thresholds are relative growth rates.

## Threshold rows are filed by period comparison name (Phase 26 step 2, Oct 2026)

Phase 26 names ten period comparisons (`src/analysis/period_comparisons.py`) and renamed the
threshold rows: `yoy` → `ytd_vs_pytd`, `qoq` → `quarter_vs_prev_quarter`, `mom` →
`month_vs_prev_month`. `_threshold_key()` files a row under its canonical name and a request looks
up the same way (`year_over_year` → `ytd_vs_pytd`, since every such request has read YTD vs previous
year YTD), so an old row and a renamed one find the same entry. Budget and target keep their
substring match; any other name is its own key. Behaviour is unchanged: live 2026-10-15, lubricants
(13 cards) and Apex (7 cards) scanned identically before and after the local registry was re-seeded
with the new names. Test: `tests/unit/test_period_settings.py::TestSituationAwarenessFilesRowsByComparison`.

Not yet applied (step 3): the data product's period settings (`src/analysis/period_settings.py`:
which comparisons may raise a card, the minimum complete months, a KPI's own reading) and a
threshold row's `raises_card`. SA still reads the comparison the request names.

## Each reading uses a named period comparison (Phase 26 steps 3b–3c, Oct 2026)

**What a reading measures.** `_get_kpi_value` resolves the comparison first: the request's
`period_comparison` (new optional field on `SituationDetectionRequest`; a token may carry the
reference day an earlier reading used, `"ytd_vs_pytd@2026-07-31"`), else the old timeframe +
comparison words through `period_comparisons.from_request()` (the dashboard's year_to_date +
year_over_year = `ytd_vs_pytd`, as every scan has read it). On the warehouse paths (BigQuery,
Snowflake, SQL Server) the monthly series now runs FIRST: its latest month (with the KPI's own version
filter) says how far the actuals reach, and `period_comparisons.reference_day()` stops the spans there
(rule 2). Base and comparison SQL are the raw KPI SQL plus `_apply_span()` on its date column.
Removed: `_bq_get_period_dates`, `_bq_apply_period`, `_period_as_of`, `_timeframe_month_count`
(replaced by `_months_in_reading`, which counts the reading's own span). The DuckDB/DPA path still
sends the old words; its stamped spans are SA's reading of them.

**The plan is read over the actuals' spans.** `_fetch_plan_value` passes `_period_token(kpi_value)`,
so a Budget reading uses the actual reading's reference day. Plan rows run past the actuals (Hess:
actuals to July, plan to December).

**What a reading records.** `MeasurementContext` gains `period_comparison`, `period_label`,
`reference_day`, `actuals_end` (set when the actuals stop before the calendar's last closed month),
`card_hold_reason` and `plan_card_hold_reason`. `_window_suffix` adds "; actuals end Jul 2026" when
`actuals_end` is set, so a stopped feed does not read as current. The threshold row is looked up for
the reading's own comparison (`context.period_comparison`).

**Which readings may raise a card (3c).** The data product's period settings
(`src/analysis/period_settings.py`, `metadata.period_settings`, cached by `_period_settings_cached`;
an invalid setting is logged and the defaults used) and a threshold row's `raises_card` (carried into
`variance_thresholds`) decide, once per actual reading. `_apply_card_settings` holds threshold-breach
and plan-variance cards (and the scan holds opportunity cards from the same reading) whose comparison is
context-only or whose span has too few complete months; covenant/regulatory, projected breach and
acceleration are never held. Held readings are listed with the reason in
`SituationDetectionResponse.readings_held`, passed through by the orchestrator. Defaults: YTD vs
previous year YTD and year vs previous year raise cards; 2 complete months.

**Live, 2026-10-16:** lubricants (13 cards) and Apex (7) identical to the 2026-10-15 scans, every card
stamped `ytd_vs_pytd` as of 2026-09-30, nothing held. Hess now reads Jan–Jul 2026 vs Jan–Jul 2025 with
"actuals end Jul 2026" on every card (falls of 2–8%, where the calendar quarter had read 61–66% down),
and its Budget readings use the same span. Tests: `tests/unit/test_sa_period_comparisons.py`.
