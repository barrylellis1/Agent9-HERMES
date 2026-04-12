# A9_Situation_Awareness_Agent Card

## Agent Description
The Situation Awareness Agent provides automated KPI monitoring and situation detection based on principal context and business processes. It analyzes Finance KPIs from the FI Star Schema to detect anomalies, trends, and insights, presenting them as actionable situations with severity levels, business impact analysis, and suggested next steps.

## Primary Purpose
To provide personalized situation awareness for Finance KPIs, enabling principals to quickly understand the current state of their business metrics, identify anomalies, and take appropriate action.

## Core Capabilities
- Finance KPI monitoring and anomaly detection
- Principal-specific situation awareness based on role and context
- Business process-aligned KPI prioritization
- Principal KPI preference-aware ordering using KPI `metadata.line` / `metadata.altitude` and principal profile `metadata.kpi_line_preference` / `metadata.kpi_altitude_preference`
- Natural language query processing for KPI insights
- Human-in-the-loop feedback handling
- Recommended diagnostic questions
- Contract-driven KPI enrichment with defensive registry fallbacks (normalized KPI IDs, view/date column resolution, filter injection)

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

## LLM Configuration
| Task Type | Optimal Model | Rationale |
|-----------|---------------|-----------|
| `sql_generation` | `gpt-4o-mini` | Fast, cost-effective SQL generation from natural language |

Environment variable override: `OPENAI_MODEL_SQL`

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

## Opportunity Detection (Mar 2026)

### Overview
Alongside problem detection, the agent now detects **positive KPI opportunities** — KPIs that are
trending significantly better than expected or crossing back above performance thresholds. These
surface as `OpportunitySignal` objects in `SituationDetectionResponse.opportunities`.

### Card Type
`Situation.card_type` distinguishes display intent:
- `"problem"` (default) — red card in the UI; existing behaviour unchanged.
- `"opportunity"` — green card; `Situation` objects with this type are now created automatically
  from `OpportunitySignal` objects with `confidence >= 0.7` via `Situation.from_opportunity_signal()`.
  These appear as clickable cards in the Decision Studio dashboard alongside problem cards.

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

### `SituationDetectionResponse` — new field
```python
class SituationDetectionResponse(BaseResponse):
    situations: List[Situation]             # Unchanged — problem cards
    opportunities: List[OpportunitySignal]  # NEW — opportunity signals (default [])
    ...
```

### Design Notes
- Opportunity detection is additive: problem detection logic is **not** changed.
- `_detect_opportunities()` is called per-KPI immediately after `_detect_kpi_situations()`.
- Errors in `_detect_opportunities` are caught and logged at WARNING level — they never
  interrupt the main problem-detection pipeline.
- Directional awareness: inverse-logic KPIs (lower is better, e.g. COGS) use inverted
  comparison logic so "doing better" always maps to a positive `delta_pct`.

## Phase 8 Update (Mar 2026)
- `Situation.from_opportunity_signal(signal, kpi_value)` classmethod added to `situation_awareness_models.py` — converts an `OpportunitySignal` with `confidence >= 0.7` into a `Situation` with `card_type="opportunity"`, dedupe key `opp_{kpi_name}_{opportunity_type}`, and severity mapped from opportunity type (`outperformance` → HIGH, `recovery` → MEDIUM, `trend_reversal` → LOW).
- SA agent `detect_situations` now appends these opportunity Situations to the main situations list after each per-KPI opportunity scan.

## Monthly Series for Trend Visualization (Apr 2026)
- `_bq_monthly_series_sql(base_sql, date_col, num_months=9)` — generates BigQuery SQL returning monthly aggregates for the last N months
- Monthly series query runs after current + comparison queries in `_get_kpi_value()`, BigQuery KPIs only (DuckDB TODO)
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
- When multiple KPI thresholds trigger for the same KPI, keeps highest-severity entry only
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

### Impact
- Workflow-level client isolation now enforced at KPI retrieval, not post-hoc filtering
- Assessment engine can safely run parallel per-KPI scans across multiple principals without cross-client data leakage

## Future Enhancements
- Integration with A9_NLP_Interface_Agent for advanced query parsing
- Enhanced business impact analysis using LLM
- Machine learning-based anomaly detection
- Multi-dimensional trend analysis
- Enhanced visualization capabilities in Decision Studio UI
