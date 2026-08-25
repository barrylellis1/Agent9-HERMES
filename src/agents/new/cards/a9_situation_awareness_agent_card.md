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
| `detect_situations` | Detect situations across KPIs. In assessment mode, processes a single KPI using its MonitoringProfile (comparison_period, volatility_band, min_breach_duration, confidence_floor). Returns `escalate_to_da: bool` for assessment engine routing. | `SituationDetectionRequest` | `SituationDetectionResponse` |
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

### Monitoring Profile Support
When `use_monitoring_profiles=True` (default), `detect_situations` reads each KPI's
`monitoring_profile` from the KPI registry and uses:
- `comparison_period` instead of the global `timeframe` parameter
- `volatility_band` to filter noise — breach must exceed band to qualify
- `min_breach_duration` — consecutive-period check before escalation
- `confidence_floor` — gate for DA escalation; below floor → `status="monitoring"`

### Assessment Engine Integration
When `assessment_mode=True`, processes one KPI per call. `SituationDetectionResponse`
includes `escalate_to_da: bool` for direct routing to DA by the assessment engine.

### Situation Status Values (Updated)
| Status | Meaning |
|--------|---------|
| `"detected"` | Confidence ≥ floor; escalated to DA |
| `"monitoring"` | Confidence < floor; visible in UI, not escalated |
| `"below_threshold"` | Severity < severity_floor; not shown by default |

`"problem"` and `"opportunity"` card_type values are **deprecated** (Phase 9G removal). SA is a sensor only.

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
Each statistical pattern runs **only if the KPI carries a registry `KPIThreshold` row for the matching `comparison_type`** — presence of the row is the per-KPI on/off switch. A KPI's "nature" is expressed by which threshold rows its seed carries (a covenant flag might carry only `yoy`; a smooth revenue KPI carries all four). Registry `KPIThreshold` rows are mapped into `kpi_def.metadata['variance_thresholds'][<key>]` by `_convert_to_kpi_definition()`. Relevant `ComparisonType` keys: `yoy`/`qoq`/`mom` (threshold_breach), `plan_variance`, `projected_breach`, `acceleration`.

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
