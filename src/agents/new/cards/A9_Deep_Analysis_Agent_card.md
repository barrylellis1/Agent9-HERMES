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

**Alert-type context fields** (added Phase 11I-B): `DeepAnalysisRequest` and `DeepAnalysisPlan` both carry `alert_type: Optional[str]`, `compound_alert: bool = False`, and `compound_pattern: Optional[str]`. These flow from SA through the workflow to `_generate_scqa_summary()` to adjust narrative framing.

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

## LLM Configuration (Anthropic — via A9_LLM_Service_Agent)
| Task Type | Model | Rationale |
|-----------|-------|-----------|
| `nlp_parsing` | `claude-haiku-4-5-20251001` | Insight extraction — pure JSON classification, no reasoning needed |
| `reasoning` (default) | `claude-sonnet-5` | Narrative summarization (SCQA) and refinement question generation (11O-B: 4.6 → 5) |

Environment variable overrides: `CLAUDE_MODEL_NLP`, `CLAUDE_MODEL_REASONING`

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
- `_classify_benchmark_segments()`: classifies IS NOT items into `internal_benchmark` (top quartile) or `control_group`; computes `effect_size_pct` (segment |delta| / total variance) and `is_outlier` (|delta| > mean + 2σ) on every `BenchmarkSegment`. Outlier segments are forced to `control_group` with `replication_potential=None` regardless of quartile rank — a statistical outlier cannot be a reliable replication target.

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
When DA returns `analysis_mode="mixed"` (and `mixed_framing=True`), the frontend intercepts before calling Solution Finder. A HITL resolution panel in `DeepFocusView` presents both sides:
- **Quantified both sides**: net |delta| of problem segments vs opportunity segments
- **Three choices**: "Focus on Recovery" (→ problem mode), "Focus on Opportunity" (→ opportunity mode), "Let Agent9 Decide" (auto-picks larger absolute delta side with reasoning)
- **Resolved binary mode**: After resolution, the chosen mode (`"problem"` or `"opportunity"`) is passed to Solution Finder as `analysis_mode`
- **SF and VA execution**: Both agents then run in the resolved binary mode — no dual-tracking, no mixed-mode complexity downstream
- **Reset on new result**: The resolution state resets whenever a new `analysis_mode="mixed"` DA result arrives, preventing stale resolution from a prior KPI flowing through
- **Disabled state**: Refinement and Generate Solutions buttons are rendered greyed-out (`opacity-40 pointer-events-none`) until the mixed-mode resolution is made

**`mixed_framing` field** (on `DeepAnalysisResponse`): `bool`, default `False`. Set to `True` by `execute_deep_analysis` when `_effective_mode_final == "mixed"`. Signals the frontend to show the HITL mode-resolution gate.

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

## Phase 11I-B — Alert-Type-Aware SCQA Framing (Jun 2026)

`_generate_scqa_summary()` now accepts `alert_type: Optional[str]` and `compound_pattern: Optional[str]`. Both the LLM prompt and the deterministic fallback produce distinct Situation/Complication framing per alert type:

| `alert_type` | Situation framing | Complication framing |
|---|---|---|
| `"threshold_breach"` (default) | `"is under-performing vs. {comparator}"` | Dimensional concentration (existing behaviour) |
| `"plan_variance"` | `"is tracking below plan"` | Which segments are responsible for the budget gap |
| `"projected_breach"` | `"is trending toward breach"` (not "has breached") | Which segments are driving the projected deterioration |
| `"acceleration"` | standard | Decline is accelerating, not just present |
| Compound (`compound_pattern` set) | standard | Leads with cross-KPI tension before dimensional segments |

### `DeepAnalysisRequest` / `DeepAnalysisPlan` new fields
| Field | Type | Default | Description |
|---|---|---|---|
| `alert_type` | `Optional[str]` | `None` | Alert pattern that triggered this analysis |
| `compound_alert` | `bool` | `False` | Cross-KPI compound conflict triggered this analysis |
| `compound_pattern` | `Optional[str]` | `None` | Human-readable compound tension string |

Compound framing example:
> **Complication:** "Despite revenue growing 8%, gross margin declined 3pp — the divergence suggests a mix shift or pricing compression, not a volume problem."

When `alert_type` is `None` (caller did not set it), the SCQA narrative is unchanged from pre-11I behaviour.

## Phase 11I-D — Alert-Type-Aware Comparator Selection + On-Demand Drill (Jul 2026)

**Two pre-existing gaps this closes** (the 11I-B framing above was effectively dead in production until now):
1. `/deep-analysis/run` never populated `alert_type` from the originating situation, so the 11I-B framing branches never fired — DA always narrated as a generic threshold breach.
2. `comparator_main` was chosen purely from KPI-registry threshold preference (hard bias toward time-based over budget), **independent of which alert fired** — so a KPI that fired `plan_variance` was still diagnosed vs prior period, not vs budget.

### Wiring (server-side lookup, not frontend-passed)
`_run_deep_analysis_workflow` (`workflows.py`) now looks up the originating situation via `SituationsStore.get_situation(situation_id)` — mirroring the VA HITL-approve handler — and reads `alert_type`, `merged_alert_types`, and the per-pattern scalars (`plan_value`, `projected_breach_at_period`, `periods_until_breach`, `acceleration_signal`) from `full_payload`. Non-fatal: any failure degrades to the pre-11I-D registry-default selection + generic framing.

### Comparator selection precedence — `_resolve_da_comparator(plan, kpi_def, registry_comparator)`
Chooses the single Is/Is-Not comparison basis (`"previous"` vs prior period, `"budget"` vs plan, same period):
1. `comparator_override` present (on-demand drill) → use it verbatim.
2. else `alert_type == "plan_variance"` **and** the KPI has budget data (`_kpi_has_budget_data`: `plan_version_value` set, or a `"budget"`/`"plan_variance"`-typed threshold) → `"budget"`; `alert_type == "threshold_breach"` → `"previous"`.
3. else → today's registry-preference default (`registry_comparator`), unchanged for direct/non-situation calls.

`_kpi_has_budget_data` checks `plan_version_value` first and both `"budget"` **and** `"plan_variance"` comparison_types — SA's `plan_variance` is `ComparisonType.PLAN_VARIANCE`, a different enum member than the narrow `"budget"` scan `_pick_threshold_spec` does, so a plan_variance-only KPI would otherwise look budget-less. After resolution, `spec_main["comparison_type"]` is reconciled to match the chosen basis.

**Still one KT table, one comparator, one LLM call per run** — no dual-pass, no structural refactor of `execute_deep_analysis`. The rejected dual-comparator design (two tables synthesized by the LLM) was dropped on comprehension grounds (KT = one problem per analysis; LLM cross-table synthesis goes muddy at the diagnosis step).

### Bounded secondary-fact narration — `_build_secondary_alert_appendix()`
When `merged_alert_types` has entries beyond the diagnosed `alert_type`, a **deterministic** appendix (no LLM, no second diagnosis) is appended to `scqa_summary` — one bounded flag line per other pattern from SA's scalars, capped at 3, e.g. *"Additional signals for this KPI: also flagged for plan variance vs its Budget baseline (Budget ≈ …) — use 'Diagnose vs Budget' for the dimensional breakdown; …"*. This is what keeps the compound case comprehensible: primary basis gets the full diagnosis, other patterns get a flag + a pointer to the drill.

### Response propagation (fixes gap #1's downstream half)
`DeepAnalysisResponse` now carries `alert_type`, `comparator` (`"previous"`|`"budget"`), and `merged_alert_types` — so SF/PIB can label the basis and the frontend can offer the drill. Additive/optional; no existing consumer breaks. (Prior to this, `alert_type` existed only on Request/Plan, never on the Response — SF never saw it.)

### On-demand "diagnose vs the other basis" drill
`DeepAnalysisWorkflowRequest.comparator_override` (client-supplied — explicit user action) forces the basis end-to-end via `DeepAnalysisRequest.comparator_override` → `_resolve_da_comparator` step 1. `DeepFocusView.tsx` shows a "Diagnose vs Budget" / "Diagnose vs prior period" button when the situation's `merged_alert_types` implies a basis the current diagnosis didn't use; the drill runs a fresh single-comparator DA and swaps the displayed IS/IS-NOT (one table on screen — never two fused). "Back to primary" restores the original.

### New model fields (11I-D)
| Model | Field | Type | Purpose |
|---|---|---|---|
| `DeepAnalysisRequest`/`Plan` | `merged_alert_types` | `Optional[List[str]]` | All patterns that fired; dominant is `alert_type` |
| `DeepAnalysisRequest`/`Plan` | `secondary_alert_facts` | `Optional[Dict[str,Any]]` | Scalars for the bounded appendix (facts only) |
| `DeepAnalysisRequest`/`Plan` | `comparator_override` | `Optional[Literal["previous","budget"]]` | Forces the basis (drill) |
| `DeepAnalysisResponse` | `alert_type` / `comparator` / `merged_alert_types` | — | Which basis was diagnosed + what else fired |

**Default when both `threshold_breach` and `plan_variance` fired:** follows the merge's dominant `alert_type` (highest-severity / first-detected). The other basis is one click away via the drill. Revisit if demo feedback wants budget to lead.

## Phase 11I-D (matrix) — Same-axis two-basis segment matrix (Jul 2026)

When a KPI breached on BOTH *cross-sectional* bases — previous-period (`threshold_breach`) AND plan-variance — DA no longer diagnoses just one; it builds a **segment × basis matrix** in the single primary `kt_is_is_not` table. Temporal/relational patterns (`projected_breach`, `acceleration`, `compound`) are NOT matrix columns — they stay as the bounded `_build_secondary_alert_appendix` annotation (and are excluded from the appendix's double-narration when the matrix ran).

**Why a matrix, not two tables:** KT is one problem per Is/Is-Not; two separate tables + LLM narrative fusion was rejected (too much LLM reasoning load). Same-axis bases (same KPI, same segments, different baseline) share the dimensional *frame*, so the synthesis is **structural** — one table, an extra delta column, the reader/LLM reads across a single row. Different-axis breaches (temporal/relational) can't be columns.

**Mechanism (cheap reuse, no block extraction):**
1. `_is_matrix_eligible(plan, kpi_def, comparator_main)` — true when `merged_alert_types ⊇ {threshold_breach, plan_variance}`, `comparator_main ∈ {previous, budget}`, and `_kpi_has_budget_data`.
2. After the primary pass finalises `kt`, run the dimensional grouping a **second time** for the other basis by reusing the already-comparator-parameterized `_maps_for_level(dim, comparator_secondary)` (budget path returns `delta = actual − budget` per segment). No extraction of the 1200-line `execute_deep_analysis` block, no second full KT table.
3. Join `secondary_delta` onto each primary `where_is`/`where_is_not` row by `(dimension, key)`, plus a `basis_agreement` tier from `_classify_basis_agreement(primary_delta, secondary_delta, trend_positive, side)`:
   - `confirmed` — adverse on both bases → the genuine problem
   - `basis_specific` — adverse on primary only (e.g. down YoY but on-plan) → likely a comparison-timing artifact
   - `secondary_only` — adverse on the secondary basis only → missed by the primary diagnosis
   - `healthy` — favorable on both
   - `None` — segment had no secondary delta (not cross-checked)
4. Guarded by try/except — any failure degrades to primary-only (`matrix_ran=False`), never errors the run. `matrix_ran`/`comparator_secondary` on the response; rows carry `secondary_delta`/`basis_agreement`.

**SCQA (`_generate_scqa_summary`)** gains a matrix branch (fallback + LLM) that reads across the tiers in ONE narrative: leads with `confirmed`, explicitly flags `basis_specific` as probable artifacts, surfaces `secondary_only`. Bounded — the LLM reads one enriched table with per-row tiers, never two tables.

**Downstream (bounded projections, not the raw matrix):**
- **SF** `_extract_deep_analysis_summary` derives `confirmed_problem_segments` / `basis_specific_segments` from `basis_agreement` (only when `matrix_ran`); a CROSS-BASIS SCOPING line tells the option LLM to prioritise confirmed and treat basis_specific as artifacts. No new `SolutionFinderRequest` field.
- **Frontend** `IsIsNotExhibit` renders a second delta column + tier chips (confirmed / artifact? / 2nd-basis) + a matrix banner, driven by `matrix_ran`/`comparator`/`comparator_secondary`. One exhibit, two columns — never two tables.
- **SA** `_merge_compound_kpi_situations` now folds a `plan_variance` situation into the KPI's primary problem card even when it resolved to `card_type="opportunity"` (ahead of a conservative plan) — fixing the bug where a KPI down 70% YoY also rendered a contradictory green "ahead of plan" card. Genuine standalone opportunities (no problem card for that KPI) still pass through.

**On-demand drill:** demoted to optional — with the matrix showing both cross-sectional bases at once, switching between YoY and Plan no longer needs the drill. The `comparator_override` plumbing is retained (harmless, still forces a basis for single-basis re-analysis).

**New response fields (matrix):** `comparator_secondary: Optional[Literal["previous","budget"]]`, `matrix_ran: bool`. `KTIsIsNot` rows gain free-form `secondary_delta` / `basis_agreement` keys (no model-field change — rows are `Dict[str,Any]`).

**Deferred (explicit):** VA DiD **basis-tagged control groups**. Today `control_group_segments` is a flat, time-basis-defaulted list, so a solution scoped/measured on the budget basis may subtract the wrong DiD counterfactual — a latent correctness gap, to be **pressure-tested after this lands** then addressed (basis-tag the control set; evaluate picks the basis-matched set; label the AttributionBreakdown/TrajectoryChart basis). The new `comparator`/`comparator_secondary` fields are the hook.

**v1 scope note:** secondary deltas are joined onto the **primary** basis's segment set; a full union of both bases' top-N segments is a v2 refinement.
