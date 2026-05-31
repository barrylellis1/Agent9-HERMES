# A9_Deep_Analysis_Agent Card

Status: Active — client_id scoped (Phase 10B) (contract-driven planning; DGA mandatory for dimension resolution)

## Overview
The `A9_Deep_Analysis_Agent` plans and executes transparent, auditable deep analysis for KPIs using KT "Is/Is Not" as the core method, with lightweight SCQA/MECE framing. It delegates all SQL to the Data Product Agent (DPA) and uses `A9_LLM_Service` for narrative-only summarization/hypotheses (no direct LLM calls).

## Protocol Entrypoints
- `enumerate_dimensions(request: DeepAnalysisRequest) -> DeepAnalysisResponse`
- `plan_deep_analysis(request: DeepAnalysisRequest) -> DeepAnalysisResponse`
- `execute_deep_analysis(plan: DeepAnalysisPlan) -> DeepAnalysisResponse`
- `refine_analysis(input_model: ProblemRefinementInput) -> ProblemRefinementResult`

Models defined in `src/agents/models/deep_analysis_models.py`.

## Problem Refinement Chat (Dec 2025)
The `refine_analysis` method implements MBB-style principal engagement:
- Validates Deep Analysis findings with principal's business knowledge
- Gathers external context the data cannot show
- Identifies constraints and exclusions
- Recommends a diverse consulting council based on problem characteristics

### Replication Topic (Mar 2026)
When internal benchmarks exist in the DA output, `refine_analysis` adds a 6th dynamic topic
`replication_potential` via `_get_topic_sequence(da_output)`. This topic asks the principal about
structural barriers to replicating high-performing segments. Extracted barriers are stored as
`replication_constraints: List[str]` on `ExtractedRefinements` and `ProblemRefinementResult`.

Key methods:
- `_get_topic_sequence(da_output)` — returns 5 base topics + `replication_potential` when benchmarks present
- `_build_benchmark_summary(da_output)` — formats internal benchmarks as context for the replication question

### Diverse Council Recommendation
The agent recommends one consulting firm from each category:
- **MBB**: McKinsey, BCG, or Bain (based on keyword matching)
- **Big4**: Deloitte, EY-Parthenon, KPMG, or PwC Strategy& 
- **Technology**: Accenture
- **Risk**: KPMG Advisory

Selection is based on:
1. Keyword matching from SCQA summary and refinement responses
2. Principal role affinity
3. Default selection if no matches

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

## KPI Registry Source (Mar 2026)
KPI definitions are loaded exclusively from the Supabase-backed `RegistryFactory` (single source of truth). The legacy YAML-first `KPIProvider` load path has been removed — it was bypassing Supabase and returning stale objects without metadata extensions.

## Bridge Analysis for Ratio KPIs (Mar 2026)
When a KPI carries `metadata.kpi_type = "ratio"` with `bridge_numerator_sql` and `bridge_denominator_sql` fields, the `_maps_for_level` helper switches to a bridge decomposition instead of running the full ratio formula per segment:
1. Fetches numerator (e.g. Gross Profit) and denominator (e.g. Revenue) per dimension — current and previous periods — via four separate BigQuery queries.
2. Computes `gm_i = numerator_i / denominator_i × 100` per segment for each period.
3. Produces `delta = rev_share_i × (gm_i_cur − gm_i_prev)` — the segment's **weighted pp contribution** to the overall margin change.
4. Falls back to standard path for budget comparisons or on any query failure.

This prevents the "100% margin" artifact that occurs when COGS is not allocated at the same dimensional granularity as Revenue in the source data.

## Phase 8 — Unified Opportunity Analysis (Mar 2026, corrected May 2026)
DA produces both problem segments AND opportunity segments from the same IS/IS NOT table — no separate opportunity analysis agent.

**`analysis_mode` field (on both `DeepAnalysisRequest` and `DeepAnalysisPlan`):**
- `"problem"` (default): IS = underperforming segments (breach drivers); IS NOT = healthy segments (control group)
- `"opportunity"`: IS = outperforming segments (what's driving the win); IS NOT = lagging segments (replication targets — KT POA framing)

**IS/IS NOT framing by mode:**
| | Problem (PA) | Opportunity (POA) |
|---|---|---|
| IS | Where IS the breach? | Where IS the outperformance? |
| IS NOT | Where is it NOT? (control group) | Where is it NOT yet? (replication targets) |
| SCQA answer | Root cause to eliminate | Leading segment to replicate |

**Key logic:**
- `analysis_mode` is now propagated from `DeepAnalysisRequest` → `DeepAnalysisPlan` → `execute_deep_analysis`
- `execute_deep_analysis`: when `analysis_mode="opportunity"`, swaps which list goes to `kt.where_is` vs `kt.where_is_not`
- `_generate_scqa_summary`: direction string and fallback text are both mode-aware
- `_classify_benchmark_segments()`: classifies IS NOT items into `internal_benchmark` (top quartile) or `control_group`; also computes `effect_size_pct` (segment |delta| / total variance) and `is_outlier` (|delta| > mean + 2σ) on every `BenchmarkSegment`

## Phase 10F — Uniform Time Dimension Layer (May 2026)
- `_prev_timeframe()` replaced: now delegates to `TimeFilter.previous_period_name(timeframe)` — consistent mapping for all timeframe strings including `year_to_date`.

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

## Recent Updates (Feb 2026)
- Fixed `UnboundLocalError: when_started` — variable now declared unconditionally before conditional block
- Added RegistryFactory KPI lookup fallback: when YAML KPIProvider returns None, agent falls back to Supabase-backed provider (supports lubricants and other non-YAML KPIs)
- Multi-tenant: passes `client_id` context through KPI resolution chain

## Notes
- CURRENT timeframe honors Decision Studio selection; PREVIOUS derived relative to CURRENT (QoQ/MoM/YoY).
- Optional percent growth `(curr - prev) / NULLIF(prev, 0)`; rankings remain deterministic.

### Market Analysis Context Injection (Mar 2026)

On turn 0 of the Problem Refinement Chat, the `refine_deep_analysis` endpoint calls
`A9_Market_Analysis_Agent` in parallel with the first LLM question generation. The resulting
market signals are converted to plain strings and passed as `initial_external_context` in
`ProblemRefinementInput`. The `refine_analysis` method injects these into `accumulated.external_context`
via `_merge_refinements()` before calling `_generate_refinement_question()`. This ensures the
refinement LLM sees real external market signals in its system prompt for the `external_context`
topic, generating targeted follow-up questions rather than generic open-ended ones.

## Phase 11G — Mixed Analysis Mode (May 2026)

DA now self-determines its `analysis_mode` after the dimension loop, rather than blindly propagating the caller's hint.

### Three-value enum
| Value | Meaning |
|---|---|
| `"problem"` | ≥80% of top-5 items are problem-direction (underperformers) |
| `"opportunity"` | ≥80% of top-5 items are healthy-direction (outperformers) |
| `"mixed"` | Neither direction dominates; both problems and opportunities present |

### Tunable constant
`_MIXED_MODE_PURITY_THRESHOLD = 0.80` — module-level constant. Adjust to change how pure a result set must be before DA declares a single mode.

### `_infer_analysis_mode()` method
- Called after the dimension loop; receives raw `_all_problem_items` and `_all_healthy_items` accumulators
- `n_prob = min(len(problem_items), top_n)`, `n_heal = min(len(healthy_items), top_n)`
- `n_prob / total ≥ 0.80` → "problem"; `n_heal / total ≥ 0.80` → "opportunity"; else "mixed"
- Falls back to `caller_hint` when `total == 0`
- Caller hint (`DeepAnalysisRequest.analysis_mode`) is still accepted and used as tiebreaker on empty data

### Mixed IS/IS NOT layout
In mixed mode, `where_is` is merged (problem + opportunity items) and sorted by `abs(delta)`. `where_is_not` is emptied — no neutral middle in MVP. Every item carries `segment_type` ("problem" or "opportunity") set at collection time, before the reshuffling step.

### Benchmark classification in mixed mode
`_classify_benchmark_segments()` receives only the opportunity-tagged items from `where_is` (filtered by `segment_type == "opportunity"`), so benchmarks represent replication candidates even when the IS list contains a mix.

### Mixed SCQA
- **Fallback**: Bifurcated complication naming both lag segments and outperformers; dual question (fix + replicate); dual answer.
- **LLM prompt**: FRAMING RULES instruct the model to name both drag and opportunity, ask how to fix AND replicate, answer with both a recovery and a replication action.
- **Framing guard**: In mixed mode the LLM-response problem-framing rejection is skipped (both languages are acceptable).

### Framing table (updated)
| Mode | IS | IS NOT | SCQA answer |
|---|---|---|---|
| Problem (PA) | Where IS the breach? | Control group (within threshold) | Root cause to eliminate |
| Opportunity (POA) | Where IS the outperformance? | Replication targets | Leading segment to replicate |
| Mixed | Both problem and opportunity segments (tagged) | Empty (no neutral middle in MVP) | Recover laggards + replicate leaders |

### Flow
1. Dimension loop collects raw `(key, current, previous, delta)` tuples into `_all_problem_items` / `_all_healthy_items`
2. All `_format_where_entry()` calls tag items with `segment_type="problem"` or `"opportunity"` at collection time
3. After the loop: `_infer_analysis_mode()` → sets `plan.analysis_mode` → reshuffling applied → `analysis_mode` written to `DeepAnalysisResponse`

### Mixed Mode Handoff to HITL Resolution (Frontend Decision)
When DA returns `analysis_mode="mixed"`, the frontend intercepts before calling Solution Finder. A HITL resolution panel in `DeepFocusView` presents both sides:
- **Quantified both sides**: net |delta| of problem segments vs opportunity segments
- **Three choices**: "Focus on Recovery" (→ problem mode), "Focus on Opportunity" (→ opportunity mode), "Let Agent9 Decide" (auto-picks larger absolute delta side with reasoning)
- **Resolved binary mode**: After resolution, the chosen mode (`"problem"` or `"opportunity"`) is passed to Solution Finder as `analysis_mode`
- **SF and VA execution**: Both agents then run in the resolved binary mode — no dual-tracking, no mixed-mode complexity downstream

**Design rationale**: Mixed mode is valuable for DA's IS/IS NOT exhibit and SCQA narrative. At the DA→SF boundary it must collapse to a single resolved mode via HITL, avoiding dual-track solutioning, ambiguous DiD control groups in VA, and cognitive overhead.

## Phase 10B-DGA: Data Governance Wiring (Apr 2026)
- Removed broken DGA acquisition from `connect()` — method was failing silently without propagating errors
- `data_governance_agent` initialized to `None` in `__init__`, wired post-bootstrap by A9_Orchestrator via `runtime._wire_governance_dependencies()`
- Eliminates circular dependency: DA no longer tries to pull DGA during its own connection phase
- All `_get_glossary_context()`, KPI validation, and view-resolution calls use the injected DGA reference
- Removed 1 remaining `if self.data_governance_agent is not None:` guard in `plan_deep_analysis()` (line ~438):
  - DGA dimension resolution is now always attempted as primary path
  - Contract-based dimensions fallback to DPA if DGA unavailable

- May 2026: Bug fixes — NaN normalization, multi-tenant kpi_registry collision fix, comparison value extraction
- May 2026 (Phase 10B-DGA final): Added mandatory `is None → raise RuntimeError` guard before DGA call in `plan_deep_analysis()` dimension-supplement branch (line ~441). Previously the call was unguarded — a missing DGA would produce an opaque `AttributeError`. Guard now matches the pattern established in SA and DPA: clean `RuntimeError("Data Governance Agent not initialized…")` surfaces through the outer try/except as `DeepAnalysisResponse(status="error")`.
- May 2026: `_infer_analysis_mode()` — added caller-hint preservation rule: when `caller_hint="opportunity"` and `n_heal == 0`, return "opportunity" rather than falling through to the purity-threshold logic. Zero healthy segments is typically caused by missing per-dimension comparison data (delta = current − 0), not a genuine absence of outperformers. Trusting the caller hint prevents a silent override to "problem" on incomplete dimensional evidence.
- May 2026: IS/IS NOT swap guard — opportunity-mode `where_is` / `where_is_not` swap is now conditional on `kt.where_is_not` being non-empty. If IS NOT is empty (no comparison data per dimension), items already sit in `where_is` and are rendered as leading segments by the opportunity-mode UI; swapping would produce an empty exhibit.
