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
```

## Protocol Entrypoints
| Method | Description | Request Model | Response Model |
|--------|-------------|---------------|----------------|
| `detect_situations` | Detect situations across KPIs based on principal context | `SituationDetectionRequest` | `SituationDetectionResponse` |
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
- `"opportunity"` — green card (used when a `Situation` is created from an opportunity signal
  in future UI wiring; `card_type` is set at creation time).

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

## Future Enhancements
- Integration with A9_NLP_Interface_Agent for advanced query parsing
- Enhanced business impact analysis using LLM
- Machine learning-based anomaly detection
- Multi-dimensional trend analysis
- Enhanced visualization capabilities in Decision Studio UI
- UI green card rendering for `card_type = "opportunity"` in Decision Studio
