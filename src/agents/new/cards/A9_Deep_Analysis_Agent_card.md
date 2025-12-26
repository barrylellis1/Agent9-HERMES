# A9_Deep_Analysis_Agent Card

Status: MVP (contract-driven planning)

## Overview
The `A9_Deep_Analysis_Agent` plans and executes transparent, auditable deep analysis for KPIs using KT "Is/Is Not" as the core method, with lightweight SCQA/MECE framing. It delegates all SQL to the Data Product Agent (DPA) and uses `A9_LLM_Service` for narrative-only summarization/hypotheses (no direct LLM calls).

## Protocol Entrypoints
- `enumerate_dimensions(request: DeepAnalysisRequest) -> DeepAnalysisResponse`
- `plan_deep_analysis(request: DeepAnalysisRequest) -> DeepAnalysisResponse`
- `execute_deep_analysis(plan: DeepAnalysisPlan) -> DeepAnalysisResponse`

Models defined in `src/agents/models/deep_analysis_models.py`.

## Configuration Schema
Defined in `src/agents/agent_config_models.py`:

```python
class A9_Deep_Analysis_Agent_Config(BaseModel):
    model_config = ConfigDict(extra="allow")
    hitl_enabled: bool = False
    max_dimensions: int = 5
    max_groups_per_dim: int = 10
    enable_percent_growth: bool = False
    require_orchestrator: bool = True
    log_all_requests: bool = True
```

## Dependencies
- `A9_Data_Product_Agent` (deterministic grouped/timeframe comparisons, joins `time_dim`)
- `A9_Data_Governance_Agent` (glossary/KPI context)
- `A9_LLM_Service_Agent` (optional narrative summarization via orchestrator)

## LLM Configuration
| Task Type | Optimal Model | Rationale |
|-----------|---------------|-----------|
| `reasoning` | `o1-mini` | Complex reasoning for narrative summarization and hypothesis generation |

Environment variable override: `OPENAI_MODEL_REASONING`

## Planning and Execution
- Dimensions are sourced from the Data Product Contract YAML (`src/registry_references/data_product_registry/data_products/fi_star_schema.yaml`) using `llm_profile.dimension_semantics` for `FI_Star_View`.
- Planned steps are grouped comparisons per selected dimension with a "current vs previous" timeframe.
- Dimension scan limit increased to 15 (from 5) for broader coverage.
- **Default timeframe**: When no timeframe is specified, defaults to `current_quarter` to ensure dimensional scans have time boundaries.
- KT Where/When are computed by executing grouped queries via `A9_Data_Product_Agent` for the current timeframe and the derived previous timeframe, then ranking by absolute delta.
- **Delta calculation**: Uses CTE-based SQL with `delta_prev` metric comparing current vs previous timeframe values.
- Change points are globally sorted by absolute delta and truncated to top 5 for focused analysis.
- Output fields include: `plan`, `dimensions_suggested`, `scqa_summary`, `kt_is_is_not`, `change_points`, `timeframe_mapping`, and `when_started` (earliest significant time bucket derived from time deltas).

## Recent Updates (Dec 2025)
- Contract path consolidated to single source of truth in `registry_references`
- Added default timeframe (`current_quarter`) when none specified
- Fixed dimension extraction from Data Governance fallback to properly extract field names from objects
- Added `DataQualityFilter` utility for filtering unassigned/anomalous dimension values
- Deduplication of IS/IS-NOT lists by (dimension, key) pairs

## Principal-Driven KT Framing (Dec 2025)
The Deep Analysis Agent adapts its KT IS/IS-NOT output framing based on the principal's `decision_style`:

| Decision Style | KT Focus | Language Style | Metrics Emphasized |
|----------------|----------|----------------|-------------------|
| `analytical` | Root cause decomposition, MECE breakdown | Statistical, precise, hypothesis-driven | Variance %, confidence intervals |
| `visionary` | Strategic implications, portfolio view | Narrative, forward-looking, market context | Strategic value at risk, opportunity cost |
| `pragmatic` | Operational fixes, quick wins | Action-oriented, owners, timelines | Recovery $, days to fix, owner assignments |

**Guardrails**: The agent adapts presentation FOR the principal, does NOT speak FOR the principal.
- ✅ "Analysis presented with MECE decomposition per your analytical decision style."
- ❌ "The CFO believes the root cause is..."

## Compliance
- A2A Pydantic IO for requests/responses
- Orchestrator-driven lifecycle; no direct LLM API calls
- Deterministic core logic, narrative layer separated
- Audit-first: plan, dimension choices (MECE), timeframe mapping (CURRENT vs PREVIOUS) are logged

## Notes
- CURRENT timeframe honors Decision Studio selection; PREVIOUS derived relative to CURRENT (QoQ/MoM/YoY).
- Optional percent growth `(curr - prev) / NULLIF(prev, 0)`; rankings remain deterministic.
