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
- `_get_topic_sequence(da_output)` — **signature changed Aug 2026**, see below
- `_build_benchmark_summary(da_output)` — formats internal benchmarks as context for the replication question

### Problem-Shape-Routed Topics (Aug 2026, Stage I B-1)

`_get_topic_sequence(da_output) -> (sequence, ProblemProfile | None, rules_applied)` now routes the
interview off the problem's **measured structure** instead of running a fixed five-topic sequence.
This is the first production consumer of `src/analysis/problem_profile.py`, which classified these
facets deterministically and was previously called only by tests.

**The routing is deterministic — no LLM.** Only the wording of each question is generated.

| Rule | Facet | Effect | Why |
|---|---|---|---|
| R1 | `compound_alert` | add `tradeoff_tolerance` | a cross-KPI tension makes "which one gives?" the first real question |
| R2 | `concentration == "concentrated"` (dominance ≥ 2.0) | **drop** `scope_boundaries`, add `segment_specific_causation` | one segment carries the variance, so the data already answered "which segments" — that turn was being spent to repeat ourselves |
| R2′ | `concentration == "distributed"` | `scope_boundaries` leads | with diffuse variance, scope genuinely is the first question |
| R3 | `has_control_group == False` | add `comparison_baseline` | an empty IS-NOT set means "why here and not there" is unanswerable from data; the contrast must come from the principal |
| R4 | `market_conflict` | suppress the turn-0 auto-skip of `external_context` | a market-vs-internal disagreement is the reason to ask, not a substitute for asking |
| R5 | `mode == "opportunity"` + benchmarks | `replication_potential` before `constraints` | replication barriers *are* constraints |
| — | none fire | unchanged five-topic sequence | |

Early-slot inserts compose in fixed priority (`tradeoff_tolerance` → `segment_specific_causation` →
`comparison_baseline`) so a given problem always produces the same sequence.

**`PROTECTED_TOPICS` / `MAX_TOPICS_IN_SEQUENCE = 6`.** Sequences are capped, and
`hypothesis_validation` / `constraints` / `success_criteria` are never truncated. `MAX_TOTAL_TURNS` is
10, so at ~2 turns per topic a 9-topic sequence would guarantee `constraints` is never reached — and
Solution Finder would then run with an empty bound set, the exact defect Stage I exists to fix.

Classification failure degrades to the base sequence with a warning; a routing error must never cost
the principal their interview.

**Observability** — `ProblemRefinementResult` carries `problem_profile_cell` (e.g.
`problem/concentrated/no-control/single`), `topic_sequence`, and `topic_routing_rules_applied`.
Without these a routed conversation is indistinguishable from the default one.

### Two conversation-state defects fixed alongside (same commit)

Both would have made the routing unobservable or raced its own progress:

- **`_extract_completed_topics` REMOVED.** It scanned assistant prose for the literal substrings
  `"moving to {topic}"` / `"completed {topic}"` — phrases nothing in the codebase emits, so it
  returned `[]` on every turn — and iterated the *static* `REFINEMENT_TOPIC_SEQUENCE`, so it could
  never recognise `replication_potential` or any routed topic. Replaced by
  `ProblemRefinementInput.topics_completed`, round-tripped from the client, which already held the
  state and simply never sent it back. **The endpoint remains stateless.**
- **`_check_topic_complete` turn counting.** It counted *every* assistant message in the
  conversation rather than messages since the last topic change, so from turn 3 onward every topic
  auto-completed on arrival. Now takes `turns_on_current_topic`, maintained client-side and reset on
  topic change.

The refine endpoint's error path also now echoes `topics_completed` back instead of `[]` — returning
an empty list told the client it had covered nothing, so one transient error silently reset the
interview's progress and re-asked answered topics.

### Two defects found by the live run, not by the tests (2026-08-11)

Both were invisible to unit tests and only appeared when a real conversation ran end to end.

1. **`effective_turn_budget(topic_sequence)`** — `PROTECTED_TOPICS` stops `constraints` being
   *truncated* out of the sequence; it does nothing about it never being *reached*. `MAX_TOTAL_TURNS`
   was a fixed 10, and a 6-topic sequence at ~2 turns each needs ~12 — so the interview ended two
   topics short and Solution Finder received no constraints, the same starvation arriving by a
   different route. The budget now scales with sequence length, with `MAX_TOTAL_TURNS` as the floor
   so the default 5-topic path is unchanged.
2. **A successful LLM question was being discarded.** `_generate_refinement_question`'s parse branch
   indexed `default_questions[current_topic]` to build a fallback. For any topic absent from that
   dict this raised `KeyError`, the surrounding `except Exception` swallowed it, and the generic
   "Please share any additional context." was returned — throwing away a good generation because of a
   lookup it never needed. Now `.get(..., _GENERIC_QUESTION)`, and all three routed topics have
   authored defaults so the no-LLM path does not degrade either.

**Rule this reinforces:** every topic the router can emit needs an entry in `TOPIC_OBJECTIVES`,
`default_questions`, `_check_topic_complete`, and the UI's `TOPIC_LABELS`. Tests now assert the first
two for every reachable topic.

### Constraint Provenance (Aug 2026, Stage I B-2)

`_accumulate_refinements(history, prior_constraint_items, prior_exclusions)` no longer rebuilds prior
turns by replaying user messages through the **keyword** extractor. That replay discarded the
structured LLM output those turns had already produced, and lost `exclusions` **permanently** — the
`"general"` branch never populates them, so a principal's "leave International out of this" ceased to
exist one turn later and never reached the refined problem statement.

The client now echoes the typed state it already holds (`prior_constraint_items`,
`prior_exclusions`); keyword replay remains the fallback for callers that send nothing, so older
clients are unaffected. **The endpoint stays stateless** — we ask the caller for state it has rather
than reconstructing it from prose.

`_merge_refinements(..., source, turn_index, discovered_by)` merges by `ConstraintItem.id`, so a
constraint restated on a later turn unions its `discovered_by` instead of appearing twice, and mints
typed items for bare constraint strings so `constraint_items` mirrors `constraints` on every path.
`ProblemRefinementResult.constraint_items` carries them downstream to Solution Finder — see
`A9_Solution_Finder_Agent_card.md` → Constraint Provenance and Exposure.

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

#### ⚠️ Known defect — the "four-firm" council has two real choices and can seat a firm twice (found Aug 2026)

`PARTNER_RULES` (`_recommend_diverse_council`) declares four categories, but:

- **`technology` and `risk` have exactly one member each** — Accenture and KPMG Advisory. They are not selections; they appear on every diverse council regardless of the problem. Only `mbb` and `big4` are genuine choices, so a "four-firm" council makes **two** decisions.
- **KPMG is a member of BOTH `big4` and `risk`.** The loop appends one winner per category, so a risk-flavoured problem (keywords `risk`, `compliance`, `governance`, `regulatory`, `esg`, `audit`, `controls`) wins KPMG the Big4 slot as well and the council returns **KPMG twice** — four seats, three firms, with no warning. Same failure class as the Stage 1 attribution bug: a council quietly running with fewer members than it reports.

Not yet fixed. A dedupe (skip a firm already selected by an earlier category) is the minimal change; the single-member categories need more members or an honest rename. Observed live on the lubricants margin problem the council resolved cleanly to McKinsey / PwC Strategy& / Accenture / KPMG — the duplication is latent, not constant.

## Configuration Schema
Defined in `src/agents/agent_config_models.py`:

```python
class A9_Deep_Analysis_Agent_Config(BaseModel):
    model_config = ConfigDict(extra="allow")
    hitl_enabled: bool = False
    max_dimensions: int = 5
    max_groups_per_dim: int = 10
    enable_percent_growth: bool = False
    enable_framing_gate: bool = False  # Phase 19 — see below
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
- Dimensions are sourced **per tenant** from that client's Data Product Contract YAML (`src/registry_references/data_product_registry/data_products/<contract>.yaml`), resolved by `_contract_path_for_kpi` via the KPI's `data_product_id`. Resolution precedence and ordering: see **Dimension Selection** below.
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
- **Aug 2026 — dropped segments now counted.** `except: continue` around the top-N diff coercion silently removed a SEGMENT from `diffs_topn`, which feeds top-N selection → `change_points` → the whole Is/Is-Not analysis: a real driver could vanish from the diagnosis with no signal. Drops are now counted and warned.
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

## Tenant-Scoped KPI Resolution — `_lookup_kpi_scoped()` (Jul 2026)

**Bug fixed:** three clients share KPI id `gross_margin_pct` (composite PK `(client_id, id)`). DA's KPI lookups matched by display name only — but the workflow passes the KPI **id** in `kpi_name` — so they always missed, and the unscoped `provider.get(id)` fallback returned another tenant's record (apex_lubricants → `dp_lubricants_snowflake`), routing all dimension queries to the wrong backend. Every query failed → empty Is/Is-Not. A second leak: `_contract_path_for_kpi` defaulted to the bicycle FI contract on a total miss, injecting FI star dimension names into other clients' plans.

**Fix:** `_lookup_kpi_scoped(kpi_ref, client_id)` resolves by id OR display name with strict tenant isolation — when `client_id` is known, a same-id record from another tenant is never returned (scoped miss → `None` + error log). Used at all three resolution sites: `_contract_path_for_kpi` (scoped miss now returns `""`, never the FI contract default), plan-phase Priority 2 dims, and the execute-phase KPI load (unscoped `provider.get()` retained only for the legacy no-client_id path). Regression tests: `tests/unit/test_da_kpi_scoped_lookup.py`.

## Magnitude-Aware Mixed-Mode SCQA Framing (Jul 2026)

**Bug fixed:** `_generate_scqa_summary`'s `analysis_mode="mixed"` branch (both the LLM prompt and its deterministic fallback) always structured the narrative as "fix the laggards, then replicate the leaders" — hardcoded ordering, regardless of relative size. On a real situation where the outperformance (~138pp combined) was ~48x the underperformance drag (~2.9pp combined), this produced a confident recommendation to urgently fix the small problem while treating the much larger opportunity as secondary — exactly backwards, and self-contradictory next to the Action Center's own problem/opportunity exposure figures.

**Fix:** both the fallback and the LLM prompt now compute `net_problem`/`net_opp` (sum of `abs(delta)` per `segment_type` in `kt.where_is`) and branch on relative magnitude: opportunity leads when it's >3x the problem, problem leads when it's >3x the opportunity, otherwise both get even billing (unchanged behavior). The LLM prompt is instructed with an explicit magnitude comparison and "do not default to fix-first when the numbers say otherwise." Also fixed a unit bug in the same code path: percentage-point deltas were unitless in the narrative text; `kpi_unit` is now threaded from `execute_deep_analysis`'s already-resolved `kpi_def` through `_generate_scqa_summary`, formatted as `"pp"` for `%` KPIs (matches the equivalent frontend fix in `DeepFocusView.tsx`'s `formatDelta`). Verified live: real DA run now explicitly states "The outperformance opportunity is 48 times larger than the underperformance drag" and leads the Answer with scaling the opportunity.

## Ratio Totals Come From the Warehouse — `dimension_totals` + `GROUP BY ROLLUP` (Aug 2026)

**Bug fixed:** the Variance Breakdown header summed every segment's `delta` and printed **-53pp** for products and **-50pp** for customers, against an enterprise move of about **-5pp**. Summing the margin *levels* the same way gives **452.95%** against a true **29.43%** — overstated 15.4x, measured on live BigQuery.

A ratio's members cannot be added, and the total cannot be recovered from them at all: it has to be re-aggregated from the underlying components (`SUM(gp)/SUM(rev)`). Only the query can do that.

**Fix — the total is the warehouse's job.** `generate_sql_for_kpi(..., include_total=True)` appends `GROUP BY ROLLUP(<dim>)`, adding one row with a NULL dimension carrying the aggregate over all rows, computed from the KPI's **own registered expression**. DA lifts that row out via `_pop_total()` and records `KTIsIsNot.dimension_totals[dim] = DimensionTotal(..., source="rollup")`. `DimensionTotal.source` is a `Literal["rollup", "unavailable"]` — `"sum"` is not representable, so the bug cannot be re-encoded. No per-KPI metadata is needed and a KPI nobody configured still gets a correct total.

- **`_ROLLUP_TOTAL_KEY` contains a NUL byte**, so it cannot collide with a real dimension value. `_as_map` tests the raw value for `None` rather than `str(key) == "None"`, so a segment legitimately named "None" is never mistaken for the grand total.
- **`_pop_total` must be called on every grouped map before iterating it.** Left in place the total row becomes a phantom segment that outweighs every real one and ranks as the top change point.
- **ROLLUP is not applied on the topn branch**, which ends in `ORDER BY ... LIMIT n`: a LIMIT either clips the total row or keeps it and drops a real member, and which one is lost is not stable.

**`delta` now has one meaning, always: the segment's own change.** It previously carried a revenue-weighted contribution when a KPI declared ratio-bridge metadata and a raw change otherwise — one field, two meanings ~8x apart, selected by whether someone remembered two SQL strings. Because `change_points` feed Solution Finder, that let a config flag silently change what the MBB personas reasoned about. The weighted contribution moved to its own field, `ChangePoint.contribution_pp` (and `contribution_pp` on the where-entry), populated only where the bridge is configured. `None` means *not computed* — never zero, which would read as "contributed nothing".

**The bridge is now a decomposition, not a fallback.** It answers a different question from ROLLUP ("how much of the move came from this segment") and is not a backup for it. Where both run they **cross-check**: the sum of weighted contributions should land on the warehouse total. `[ROLLUP-CHECK]` logs a warning when the decomposition *overshoots* the quantity it decomposes (only overshoot is checkable — members are top-N, so their sum is a subset). Logged, not raised: the total is authoritative and correct on its own, and a bad decomposition must not take down a good analysis.

**Live verification (2026-08-09) found the first cut inert, and then a second bug.**

Run 1 on the real server logged `bridge=0/0 dimension_totals=0` on an otherwise successful analysis: this KPI takes the **topn/CTE path** (`topn={'type':'top','n':3}` → `WITH curr … ORDER BY delta_prev DESC LIMIT n`), not `_maps_for_level`, so `include_total` was never requested and the ROLLUP wiring never executed. Editing a code path proves nothing until a live run confirms that path is the one used.

**Fix:** an overall figure is now fetched **path-independently** at the end of `execute_deep_analysis` — two ungrouped queries (current and `comparison_period=True`) using the KPI's own registered expression, applied to every dimension present. The dimensional breakdowns cover the same rows under the same filters, so the overall figure is identical for every dimension; one scalar pair, not per-dimension work. Non-fatal on failure: an absent total renders as no total, and must never fall back to summing members.

Run 2 then exposed a second defect: **`_build_bq_dimensional_sql` ignored `comparison_period` on the non-breakdown path**, so the prior-period scalar silently returned the CURRENT value — `current=29.94 previous=29.94 delta=0.0`, which would have rendered a confident "0.00pp" on a KPI that had actually moved. The breakdown branch had always honoured the flag; only the scalar path did not, and nothing had exercised it. Fixed.

Run 3 verified end to end and cross-checked independently against BigQuery: **YTD 2026 = 29.94%, YTD 2025 = 34.43%, delta = −4.49pp**, matching DA exactly; `dimension_totals` populated for all 5 dimensions; 34 members with **no phantom total row** leaked in. `source` is `"scalar_query"` on this path, not `"rollup"` — labelling it `rollup` would overstate how the number was obtained.

**Design rule this encodes:** *any number requiring arithmetic is computed by the query, not by Agent9.* The agents decide what to ask and interpret what comes back; they do not aggregate. Tests: `tests/unit/test_rollup_total_sql.py`, `tests/unit/test_ratio_delta_additivity.py`.

## Dimension Selection — declared order, auditable (Aug 2026, Stage I Part A)

**Resolved defect.** `_dims_from_contract` used to re-rank candidate dimensions against a static literal:

```python
preferred = ["profit_center_name", "customer_name", "product_name",
             "product_line", "channel_name", "customer_segment", ...]
```

A hand-copy of bicycle and lubricants field names, merged and frozen, applied to every KPI, client and problem type — so each tenant was investigated in an order nobody had chosen for them, and it **silently overrode each client's own contract**. For lubricants it forced profit-centre first against a contract whose `dimension_semantics` is grouped and commented Product → Customer → Organization → Channel → Account → Time.

**Now: declared order wins, and which declaration won is recorded.**

| Precedence | Source | Notes |
|---|---|---|
| 1 | contract `llm_profile.dimension_semantics` | declared order, de-duplicated |
| 2 | `KPI.dimensions[].field` from the Supabase registry | only when the contract yields nothing |
| 3 | DGA view metadata | last resort |
| — | ban filter (`flag`, `hierarchy`, `_id`, `transaction_date`, `version`, `fiscal ytd/qtd/mtd`) | unchanged |

`DeepAnalysisPlan.dimension_rank_source` (`contract_semantics` \| `kpi_registry` \| `dga_metadata` \| `hierarchy_vectors` \| `none`) records the winner; `DeepAnalysisPlan.dimensions_considered` carries the full pre-truncation candidate set.

**Accepted failure mode:** a client whose contract lists dimensions in ETL or alphabetical order now gets that order, where the literal was accidentally acting as a safety net. This is the correct trade — it surfaces as a contract-authoring problem instead of being masked. `dimension_rank_source` is what makes it visible.

**The same literal existed on the hierarchical drill path** — `vector_order = [k for k in ["customer","product","profit_center"] if k in hmap] or list(hmap.keys())`. Inert in practice (no live contract names its vectors that way; only `hess_financials.yaml` declares `dimension_hierarchies` at all, using `geography`/`segment`/`financials`), but a trap for the first contract that does. Now `list(hmap.keys())`.

### Two different 5s — search width vs report width

These are independent caps and are routinely confused:

| Cap | Where | What it bounds |
|---|---|---|
| `max_dimensions` (**10** as of Stage I Part A, was 5) | `execute_deep_analysis` `dims_to_process` | how many dimensions get **queried** |
| `change_points[:5]` | post-loop, globally sorted by \|delta\| | how many drivers reach SCQA / Solution Finder |

Raising `max_dimensions` therefore **widens the search without widening the funnel** — a better-selected top 5, not more of them. SF's evidence base and KT's one-problem-per-analysis discipline are unchanged. Cost is ~1 extra query per added dimension (2 on the budget comparator, roughly double again when the two-basis matrix runs), executed sequentially.

`DeepAnalysisResponse.dimensions_analyzed` records the dimensions actually queried. Before it existed, a run reported N suggested, analyzed `max_dimensions` of them, and recorded nowhere which ones.

**Formerly a known exposure, now closed (Aug 2026):** a wider search increases the surface for the slice-validity failure class (a ratio cut by a dimension whose components are not allocated at the same grain — see the −457% / 100.00% margin case). DA now enforces `KPI.not_sliceable_by` directly — see "§4.5 Enforcement" below.

**Still true:** nothing about the *problem* influences what gets investigated — not the alert type, not the concentration of the variance, not whether a contrast group exists. Only the client's declaration does. Problem-shape routing is Part B (`DEVELOPMENT_PLAN.md` → Phase 15 → Stage I).

## One Comparison Basis Per Analysis — `_compute_overall_summary` (Aug 2026)

**Bug fixed:** the overall/headline summary asked the DPA for `timeframe=prev_tf`, and `prev_tf` for `year_to_date` is `"last_year"` — the **full prior year**. Every dimensional query in the same method uses `cur_tf` with `comparison_period=True`, i.e. prior **year-to-date**. One payload therefore carried two comparison bases, both labelled year-over-year:

| surface | baseline | movement |
|---|---|---|
| `kt_is_is_not.what_is[0]` (headline) | 32.63 (FY-2025) | −2.69pp / −8.2% |
| `dimension_totals`, segments, SA | 34.43 (YTD-2025) | −4.49pp / −13.1% |

Verified against BigQuery: YTD-2025 = 34.43%, FY-2025 = 32.63%.

**How it surfaced.** A live production briefing. The model noticed both baselines, could not choose, and wrote them into `key_assumptions`, raised an `unresolved_tension`, and produced a next step asking the CFO to *"reconcile the two reported baselines into a single authoritative figure"*. It escalated our inconsistency to the reader as a finding — the briefing was internally consistent about being inconsistent. Worth remembering as a detection channel: when the LLM asks the reader to reconcile two of our own numbers, that is a bug report.

**Fix:** `comparison_period=True` on the current timeframe, so the headline shares the dimensional basis. `comparator_label` changed with it — it read `"last_year"` while describing a year-to-date window, and **a label naming a different period than the number is how this stayed invisible for so long.**

**Rule:** every figure in one analysis must be measured against the same basis, and the label must name the window actually measured. Related: `MeasurementContext.comparison_basis` on the SA side, and `_window_suffix` on situation descriptions.

**Enforced, not just fixed.** The trap that produced this still sits in `TimeFilter.previous_period_name`, which maps every `*_to_date` token to a FULL prior period (`year_to_date` → `last_year`, `quarter_to_date` → `last_quarter`). Its name invites the misuse. It is now used **only** as an availability guard — "does a prior period exist" — and its docstring says so with the production numbers attached.

`tests/unit/test_equal_duration_comparison.py` fails the build if any DA query is built from a previous-timeframe token (`timeframe=prev_tf`). An equality assertion on one call site would not have caught the original bug: the wrong call was one of several and the others were correct, so what matters is that the **shape** is unrepresentable. The same file pins that labels derive from the current timeframe — the headline read `"last_year"` while measuring prior year-to-date, and both label and figure looked reasonable in isolation.

**The rule, stated plainly:** two Actual periods are comparable only when they are the same length. YTD compares against prior YTD. Version comparisons (budget/plan) are the separate case — same window, different version, `comparison_basis="version"`.

## Budget Comparator: Two Live Bugs in the Same Fallback Block (Aug 2026)

Both found via manual UI click-through on Net Revenue's "Diagnose vs Budget/Plan" drill, both in `execute_deep_analysis`'s per-dimension loop's dual-query fallback.

**Bug A — only the first dimension ever populated the Variance Breakdown table.** The fallback's gate was `if not kt.where_is:` — intended as "did THIS dimension's TopN pass fail to find anything," but `kt.where_is` accumulates across *every* dimension processed in the loop, not per-dimension. The budget comparator forces every dimension through this fallback (TopN's `delta_prev` metric is a period-over-period column; budget lives in a different `version` value of the same rows, not a second time window, so there's no single-query shortcut for it — TopN is skipped outright for `comp_fb == "budget"`, not attempted-and-failed). Once dimension 1 populated `kt.where_is`, the gate stayed permanently closed for every dimension after it. **Fix:** snapshot `len(kt.where_is)` before each dimension's own pass (`_where_is_count_before_dim`), compare after — judges each dimension on what it added, not the loop's running total.

**Bug B — the "vs Budget/Plan" table was actually showing prior-period data, mislabeled.** Found while fixing A: the same fallback, for `comp_fb == "budget"`, ran an unconditional actual-vs-PRIOR-PERIOD dual query (`comparison_period=True`) — never touching budget data. A correct budget-aware pattern already existed elsewhere in this method (`_maps_for_level` + `_budget_variant_kpi`, used by the hierarchical vector path and by `_compute_overall_summary`/`_record_dimension_total`) but the flat/legacy loop — what every real client (no client declares a hierarchical dimension map today) actually runs through — never called it. **Fix:** branch the fallback on `comp_fb`, reusing `_budget_variant_kpi` the same way the correct paths already did.

Verified live both ways (broken → fixed) via direct `comparator_override` API calls, backend restarted between each: broken state showed byte-identical deltas between `comparator="previous"` and `comparator="budget"` runs of the same KPI; fixed state shows genuinely divergent numbers (`product_name="Conventional Engine Oil"`: previous +$918K, budget −$2.19M).

**Related, deliberately unfixed:** budget data can be recorded at a coarser grain than actuals in the source system — confirmed live in the lubricants seed data itself (`generate_lubricants_demo_data.py`): revenue/COGS budget is correctly distributed at full grain, but budget SG&A is a single row pinned to one customer/product. Reproduced the consequence: `operating_income` (includes SG&A) sliced by `customer_name` shows the pinned customer at a −$11.59M outlier, 6–20× every other customer, purely from silently absorbing 100% of budget SG&A. No general coverage-gate exists yet to catch this on a *real* client's genuinely coarse budget data — recorded in `DEVELOPMENT_PLAN.md` as a follow-up (extend `check_slice_validity` to compare Budget's distinct-value coverage against Actual's, same shape as `check_completeness()` applied to the version axis instead of the account-component axis).

## §4.5 Enforcement — `not_sliceable_by` Excludes Dimensions, Not Just Displays Them (Aug 2026)

`docs/architecture/kpi_semantic_contract.md` §4.5 always specified DA should exclude denied dimensions from analysis, not just let a human read them in a panel — only a partial (display-only) build had shipped as of the slice-validity work earlier this session. Reopened deliberately (not a silent scope drift — see the plan's own premortem #4 on this exact risk) once live evidence showed the cost of not doing it: a `degraded`-not-`INVALID` dimension (`profit_center_name`) on `apex_lubricants`/`gross_margin_pct` produced a −68.3% garbage change-point value that reached DA's output with nothing distinguishing it from a trustworthy one.

**What changed:**
- `kpi_def.not_sliceable_by` is read once `kpi_def` resolves and indexed into `_denied_dims` (dimension name → `{reason_class, source}`), tolerant of both `NotSliceableByEntry` objects and plain dicts.
- `dims` is filtered against `_denied_dims` immediately after assembly (from `plan.dimensions` or `_dims_from_contract()`), **before** `unique_dims`/`dims_to_process`'s `max_dimensions` cut — a denied slot frees room for a valid dimension rather than wasting a query on a cut already known meaningless (§4.5's stated "useful interaction"). Every exclusion appended to `_dimensions_excluded`.
- The hierarchical vector path (`for lvl in levels:`, unused by any client today — none declares a hierarchical dimension map) filters identically, for consistency: "DA respects not_sliceable_by" should be true regardless of which internal path a future client's data happens to route through.
- New `DeepAnalysisResponse.dimensions_excluded: List[Dict]` (`{dimension, reason_class, source}`) — populated on every response, empty when nothing was excluded. Never silent: §4.5's explicit rule is that a deny list quietly shrinking the investigation with no trace is the same defect a hardcoded dimension-preference list already caused once (see "Dimension Selection" above).

**`reason_class` on each `not_sliceable_by` entry** (`src/registry/models/kpi.py`'s `NotSliceableByEntry`, mirrored in `data_governance_models.py`) distinguishes `structural` (a permanent fact about the client's own business data — declare once, deny forever) from `pipeline_gap` (a completeness gap in the client's own source data/ETL — **not an Agent9 code defect**, Agent9 doesn't own the client's warehouse pipeline; worth flagging to whoever does). Defaults to `pipeline_gap` — profiling alone can't tell the two apart, and §4.3's "prefer loud" principle means treating an unclassified gap as worth flagging until a human overrides it via `source="declared"`, not assuming it's permanent by default.

Verified live end-to-end against `apex_lubricants`/`gross_margin_pct`, reusing real persisted (pre-this-change, flat-string-shape) deny-list data: `channel_name`/`customer_segment` (flagged `INVALID` in an earlier run) came back correctly excluded — absent from `dimensions_analyzed`/`where_is`, present in `dimensions_excluded`. `dimensions_analyzed` grew into two previously-unreached dimensions (`account_name`, `account_type`), confirming the freed-slot mechanic. `profit_center_name` (`degraded`, not `INVALID`) correctly stayed in — the existing ok/degraded/INVALID threshold is unchanged; only `INVALID` lands in the deny list.

No direct unit test for the exclusion logic itself — matches the pre-existing gap for the rest of `execute_deep_analysis`, which nothing in this codebase unit-tests end-to-end (heavy mocking required, no established pattern); live verification is the coverage here, same as the two budget-comparator bugs above. `tests/unit/test_kpi_not_sliceable_by_model.py` covers the model/validator layer.

## SCQA Failure No Longer Fabricates a Frame — `_safe_generate_scqa_summary()` (Aug 2026)

The outer `try/except` around the call to `_generate_scqa_summary()` in `execute_deep_analysis` used to substitute a hardcoded question on ANY exception: `"Situation: Reviewing {kpi}. Complication: Variance detected vs target. Question: Which segments drive the change?"`. SCQA is a framing device — its Q *is* the frame — so this asserted a dimensional-attribution frame as a constant on the failure path, and every downstream stage (the council, the moderator, HITL) then answered it faithfully with nobody having actually asked it. See `docs/architecture/problem_framing_design.md` §1b, which names this exact bug. **Fix:** the branch now returns `None`. Absence is the honest output — every consumer already treats a missing `scqa_summary` as missing.

**Do not confuse this with `_generate_scqa_summary`'s own internal fallback.** That method has a separate, legitimate `_fallback()` closure used when the LLM call *inside* it fails — it reconstructs a narrative from real, measured `change_points`/`kt` data (is/is-not segments, matrix tiers), never fabricates content with no data behind it, and is unchanged. The outer catch-all fixed here only fires when the whole method call raises — a bug, bad input, or something outside that method's own error handling.

**Extracted into `_safe_generate_scqa_summary()`** so this is independently testable — nothing in this suite drives the ~850-line `execute_deep_analysis()` end to end, so the inline `try/except` was untestable in principle before this. Pure extraction, no behavior change to the success path. New test: `tests/unit/test_da_scqa_failure_no_fallback.py` — asserts the exception path returns `None` (never the old string), the happy path passes through unchanged, and the failure is still logged (absence must stay observable, not silent).

## Phase 19 — Problem Framing Gate (Aug 2026, in progress)

**Goal:** the problem frame (what SCQA's Question asserts as the objective) is chosen by a human
and recorded, not authored by DA and inherited unexamined by everything downstream. Full design:
`docs/architecture/problem_framing_design.md`. Build sequencing: the implementation plan referenced
from `DEVELOPMENT_PLAN.md` Phase 19. Gated behind `enable_framing_gate` (env `DA_ENABLE_FRAMING_GATE`,
default `false`) — every change below is a no-op with the flag off.

**Mechanism (decided, being built in independently-committable slices):** the framing question
becomes the mandatory first topic (`problem_framing`) of the existing Problem Refinement interview,
not a standalone pre-DA step. "Generate Solutions" is unreachable until it's answered. SCQA generation
is **deferred** until the frame is chosen, then generated *against* the chosen objective.

### Slice 2 — `_build_framing_prompt(da_output, principal_ctx)` (unwired — nothing calls it yet)

Builds the evidence shown at the gate from TWO sources, never conflated:
- **Causal graph** (`KPIRelationshipProvider.get_causal_neighbourhood`, 1–2 hops, **unfiltered by
  direction** — the schema is undirected, `direction_confirmed` is always `False`). Replays the
  provider's own visited-set BFS order to identify one alternative per distinct neighbour KPI,
  shortest-hop de-duplicated.
- **Market Analysis conflict** (Decision #12 of the implementation plan): reads
  `da_output["market_conflict"]` directly — MA's call timing is **unchanged** (still fires once in
  `workflows.py`, after DA's Is/Is-Not + change points exist); what changes is that its output now
  feeds DA's own framing construction, not only Problem Refinement's `initial_external_context` seed
  and SF's synthesis prompt as a passive sidecar. A detected conflict becomes a distinct
  `source="market_signal"` `FramingAlternative`, never fabricated on a missing/negative/malformed
  signal.

New `_FRAMING_PROVENANCE_CAVEAT` module dict — deliberately **new human-facing copy**, not
`a9_solution_finder_agent.py`'s `_PROVENANCE_CAVEAT` (that dict is LLM-instruction language — "respect
the caveat" — addressed to a model; this is addressed directly to the person deciding the frame).

**ONE outer `try/except`** around the whole method body — a provider exception anywhere (KPI lookup,
causal graph, constraints, prior frame) returns `None` for the WHOLE prompt, same posture as SF's
existing causal-grounding block. No partial degradation, unlike `_build_causal_context_section`'s
per-field tolerance.

New models in `deep_analysis_models.py`: `FramingAlternative`, `PriorFrameRecord`, `FramingPrompt`,
`FramingDecision`, `FramingRecord`. `Assumption` (`src/registry/models/assumption.py`) gained
`record_type="framing"`, `source="da_hitl"`, `expiry_event` (event-based expiry — a frame expires on a
VA verdict, not a calendar date), and attribution fields `framing_choice`/`decided_by_role`/
`decided_by_is_owner` (the last three found necessary mid-build: re-presenting a prior frame needs to
know which kind of decision it was and who made it, which isn't recoverable from `text` without
parsing prose). Two additive migrations, **not yet applied to live Supabase**:
`20260818_framing_records.sql`, `20260818_framing_decision_attribution.sql`.

### Slice 3 — SCQA deferral + `generate_scqa_for_frame()` (unwired — nothing calls the new method yet)

`execute_deep_analysis`'s inline SCQA call is now conditional on `enable_framing_gate`: off is
byte-identical to before; on sets `scqa_summary=None`, `DeepAnalysisResponse.scqa_deferred=True`, and
populates `.scqa_inputs` (`comparison_type`/`inverse_logic`/`kpi_unit` — the scalars
`_generate_scqa_summary` needs that aren't otherwise serialized on the response).

New `generate_scqa_for_frame(da_output, principal_id, frame, decided_by_role=None)` reconstructs
`_generate_scqa_summary`'s inputs from a serialized `da_output` dict (same reconstruction-from-dict
approach `_build_kt_summary` already uses), calls the existing `_safe_generate_scqa_summary` (not
`_generate_scqa_summary` directly — the "never fabricate on failure" wrapper isn't duplicated), and
prefixes the result with `"Frame (chosen by {role}): {objective}"`.

`_generate_scqa_summary` gained `frame: Optional[FramingDecision] = None`. LLM path: a `CHOSEN FRAME`
instruction block is prepended to the prompt (best-effort steering, same posture as every other
framing rule in that prompt). Deterministic fallback: a new `_question_line(default)` helper replaces
**all 6** hardcoded `"Question: ..."` constructions across every branch (matrix, opportunity, mixed
×3 magnitude cases, problem-mode default) — `frame` present ⇒ every branch emits
`f"Question: {frame.chosen_objective_text}"` instead of its own guess; `frame=None` (every existing
call site) reproduces the original text exactly. This is the single highest-risk detail in the whole
build — skipping any one of the 6 sites reintroduces, one layer up, the exact fabricated-frame defect
`_safe_generate_scqa_summary` (above) was extracted to fix.

**Pre-existing production bug found and fixed in this slice's audit, unrelated to the flag being
on:** `_create_final_result` (the refinement's terminal result), `_determine_council_type`, and
`_recommend_diverse_council` all read `da_output.get("scqa_summary")` at the **top level** — but the
client sends `{"plan": ..., "execution": ...}` with `scqa_summary` nested under `"execution"` (same
shape `_build_kt_summary` has always read correctly). This had been silently returning `"Analysis
complete."` as the refined problem statement for every refinement session in production, and starving
council-type keyword matching of the SCQA text entirely. Fixed to read the correct nesting level, with
`or ""` added at the two keyword-matching sites since a corrected read can now legitimately be a real
`None` (deferred SCQA) rather than merely absent, and `" ".join([None, ...])` raises.
`_build_briefing_context` (`workflows.py`) had the identical bug in its `problem_statement` fallback,
fixed alongside.

`workflows.py`'s MA `kpi_context` (the string MA searches on) upgrades from "bare KPI name" to "KPI
name + top-3 `where_is` driver keys" whenever `scqa_summary` is absent — necessary once the flag is on
(scqa_summary genuinely won't exist yet at MA-call-time), and a real quality improvement regardless
(commit `c7cf144` already showed DA's structural facts sharpen MA's signal specificity; this extends
the same principle to the fallback path). Built only from `kt_is_is_not`'s top drivers, never from the
`analysis_mode`/scqa conclusion — preserves the "conclusion firewall" MA's own card documents.

### Slice 4 — wired into the interview, with server-side bypass guards

`FRAMING_TOPIC = "problem_framing"` is a real `REFINEMENT_TOPIC_SEQUENCE` entry, inserted at index 0
by `_maybe_prepend_framing_topic()` — called from BOTH of `_get_topic_sequence`'s return paths (the
normal routed path, after the cap so it can never be trimmed; and the `classify()`-failure fallback,
so a profiling failure doesn't also cost the principal the gate).

**New `_handle_framing_gate(...)`** is the single entry point `refine_analysis` calls, evaluated
BEFORE every other branch (early-exit, skip-command, max-turns, all-topics-complete). This IS the
server-side bypass guard, achieved by WHERE it's called from rather than by patching each of those
branches individually: while framing is pending (flag on, `FRAMING_TOPIC` not yet in
`topics_completed`), this method returns unconditionally without ever inspecting `user_message` — so
early-exit/skip/"proceed to solutions" keywords are silently ignored, not rejected by their own logic.
There is deliberately **no turn-budget escape valve** either — running out the clock does not
auto-finalize past a pending frame, unlike a normal topic.

Two sub-flows:
- **Present** (no `framing_decision` in the request): calls `_build_framing_prompt`; if it returns
  `None` (its own documented "nothing to show this turn" contract), still blocks —
  `framing_required=True`, empty `suggested_responses`, never silently proceeds.
- **Submit** (`framing_decision` present — already Pydantic-validated as a real `FramingDecision` by
  `ProblemRefinementInput`'s field type; `falsification_criterion` non-blank and
  `choice='alternative' ⇒ chosen_kpi_id` set are both guaranteed before this method runs). What
  Pydantic *cannot* check: whether `chosen_kpi_id` was actually one of the alternatives offered — a
  **fresh** `_build_framing_prompt` call re-derives the offer set rather than trusting a client-echoed
  one; an unoffered id re-shows the (fresh) gate rather than being accepted. On acceptance: resolves
  `client_id`/`kpi_id`/`owner_role` the same way `_build_framing_prompt` does; stamps
  `decided_by_role`/`decided_by_is_owner` server-side (never client-claimed); **lift-then-insert**
  (Decision #9) — any prior active framing row for this KPI is marked `status='lifted'` via its own
  `upsert` call before the new row is inserted, so a changed mind stays on the audit trail; writes the
  `Assumption` (`record_type='framing'`); calls `generate_scqa_for_frame`; appends `FRAMING_TOPIC` to
  `topics_completed`; generates the **next topic's question in the same response** so the interview
  doesn't stall on a dead turn. A register-write failure (`persisted=False` + `persist_error`) does
  **not** lose the chat — losing the write is the smaller failure.

**Turn budget**: `effective_turn_budget()` is computed on the sequence with `FRAMING_TOPIC` excluded,
then +1 added back when framing is present — the presentation-only round trip is pure overhead (one
turn); the submission round trip pulls its own weight (it also asks the next real question), so it
needs no extra allowance.

**Transcript, not a chat message**: a successful submission appends
`{"role": "user", "content": "[Framing decision] {choice}: {chosen_objective_text}"}` to
`conversation_history` — readable in a human review, but `_accumulate_refinements`'s legacy
keyword-replay fallback (only reachable when a caller sends no typed `prior_constraint_items`) now
skips any entry with that prefix, so it's never misfiled as a constraint via `_simple_extraction`.
`_extract_refinements_from_response` is never invoked on a framing turn at all (no `user_message`
exists on one) — this is structural (the early return above), not a separate check.

**Error handler fix (same commit)**: the agent-level `except Exception` in `refine_analysis` used to
reset `topics_completed=[]` on any transient error — a second instance of the exact bug already fixed
at the endpoint level (`workflows.py`'s `refine_deep_analysis` except block, `topics_completed`
comment). Now echoes `input_model.topics_completed` back. Also now sets
`framing_required=bool(self.config.enable_framing_gate)` — fails closed for flag-on deployments
without falsely claiming the gate applies for flag-off ones (unconditional `True` would have been a
regression hiding inside a safety fix).

**`workflows.py`**: `ProblemRefinementRequest.framing_decision: Optional[FramingDecision]` — typed as
the real model, not a raw dict, so a malformed submission (missing falsifier, invalid choice, a
missing `chosen_kpi_id`) fails FastAPI's request validation with a 422 before the handler runs, rather
than surfacing as a generic in-chat error. Threaded into both `ProblemRefinementInput` construction
sites (turn-0 and subsequent). The endpoint's own exception fallback gained
`"framing_required": os.getenv("DA_ENABLE_FRAMING_GATE", ...)` — same fail-closed-to-actual-state
reasoning as the agent-level fix, read fresh from the same env var `runtime.py` bakes into agent config
at startup.

New `tests/unit/test_da_framing_gate.py` (20 tests, all passing on first run): topic-sequence
insertion (position 0, absent when off, survives a classify() failure, survives a 7-topic capped
sequence); the presentation turn including the `_build_framing_prompt→None` fail-closed case;
early-exit/skip-command/max-turns/proceed-to-solutions all silently ignored while framing is pending;
the extraction pipeline rigged to raise if ever called, proving it genuinely isn't; falsification/
chosen_kpi_id rejected at the Pydantic layer; an unoffered `chosen_kpi_id` rejected at the agent layer
and the gate re-shown; a valid submission advancing with a real SCQA and next-topic question in one
response; lift-then-insert verified via call-order assertions on the mocked provider; a register-write
failure still proceeding the chat; an unresolvable KPI still proceeding without persisting.

### Not yet built (see the implementation plan for remaining slices)
Slices 1–4 above are committed. Still to come: frontend types + the framing card (Slice 5); closing
the three Solution-Finder bypass paths + a pre-existing Cancel-button bug (Slice 6); Solution Finder
expressing the reframe in its task text (Slice 7).

### Owner-attribution role matching (found live 2026-08-18, fixed)
`decided_by_is_owner` and `viewer_is_owner` (both set from `owner_role` vs. `principal_ctx["role"]`)
originally used plain case-insensitive string equality. Live e2e verification found a real CFO
viewing a CFO-owned KPI reported `viewer_is_owner=False`, because the registry's `KPI.owner_role`
is a short code ("CFO") while `principal_context.role`, as sent by the frontend, is the principal's
full title ("Chief Financial Officer") — see `useDecisionStudio.ts` / `DecisionStudio.tsx`
(`role: currentPrincipal.title`). Fixed with a module-level `_roles_match(role_a, role_b)` helper
(a small abbreviation↔full-title expansion table for CEO/CFO/COO/CTO/CMO/CIO; blank/None never
matches) used at both comparison sites. This is a narrow, local fix scoped to the framing gate's
owner comparison only — it does not touch the broader role-vs-principal-ID lookup tech debt already
tracked in the top-level `CLAUDE.md` ("Principal ID vs Role-Based Lookup"), which needs a real
registry-level (ID-based) resolution. Covered by `TestRolesMatch` and
`test_owner_attribution_tolerates_full_title_vs_short_code` in `tests/unit/test_da_framing_prompt.py`.

### Pre-framing Analysis panel was empty (found live 2026-08-19, fixed)
With `enable_framing_gate` on, `execute_deep_analysis` defers the entire 4-part SCQA blob
(Situation/Complication/Question/Answer) as one field until a frame is chosen. The frontend's
"Analysis" accordion (`DeepFocusView.tsx`) has no other content source once a Variance Breakdown
accordion already exists (its change-points fallback only fires when there's no Is/Is-Not
breakdown) — so the panel rendered completely empty pre-framing, a real regression its own
in-code comment ("the sole situation narrative once DA completes") predates. Fixed by observing
that Situation+Complication are pure facts — `_generate_scqa_summary`'s own deterministic
`_fallback()` never references the chosen frame for those two parts, only for the Question line
(via `_question_line()`). New `_build_situation_complication_facts()` mirrors (does not refactor)
those per-mode branches up to the Question line, called unconditionally in the `scqa_deferred`
branch of `execute_deep_analysis` (deterministic, no LLM call, no added cost/latency) and exposed
as `DeepAnalysisResponse.situation_complication_summary`. The frontend renders it as a
"Preliminary Analysis" block whenever `scqa_summary` is absent but this field is present;
`scqa_summary` supersedes it automatically once framing is submitted. Covered by
`TestSituationComplicationFacts` / `TestExecuteDeepAnalysisWiring` in `tests/unit/test_da_scqa_deferral.py`
— every mode/alert-type branch is asserted to never contain "Question:"/"Answer:" text.

## Phase 20 — causal-neighbourhood evidence + Market Analysis field wiring (2026-08-19)

Full decision record: `docs/architecture/problem_framing_design.md` §14. `FramingAlternative` carried
only relationship metadata (hops, mechanism, confidence enum) for each causal neighbour — never its own
current value or trend. Fixed with a lightweight, non-dimensional evidence fetch — deliberately NOT
`execute_deep_analysis`'s full pipeline (measured ~3-4x latency/query cost per framing decision if run
on every candidate).

**New methods** (all on `A9_Deep_Analysis_Agent`, called from `_build_framing_prompt`):
- `_fetch_neighbour_snapshot(kpi_definition, timeframe, filters)` — one current + one comparison-period
  rollup query via `self.data_product_agent.generate_sql_for_kpi(..., breakdown left False)` /
  `execute_sql` — the exact same DPA call pattern this agent already uses for its own KPI's rollup
  totals, just for a different KPI, no dimensional loop. Always compares vs. the immediately preceding
  period, regardless of what basis the primary KPI's own analysis used (not every neighbour has a
  budget variant registered — a deliberate simplification, not an oversight).
- `_fetch_neighbour_monthly_trend(kpi_definition, num_months=9)` — **BigQuery-backed KPIs only in this
  pass** (hardening the live demo path, 100% BigQuery today, rather than speculatively covering SQL
  Server/Snowflake before they're needed here). Calls DPA's `generate_monthly_series_sql()` for the SQL
  text and `execute_sql()` to run it — this method's own job is only to call DPA and shape the result.
  **Corrected same-day (2026-08-19):** the original version of this method built the monthly-series SQL
  itself, directly in DA, bypassing DPA entirely — a real violation of CLAUDE.md's SQL Backend Routing
  rule (§9) and this agent's own stated boundary ("Uses Data Product Agent for deterministic grouped/
  timeframe comparisons," this file's header). Found live, mid-build, when a user asked "isn't all SQL
  supposed to go through the DPA?" The SQL-generation logic now lives in
  `A9_Data_Product_Agent.generate_monthly_series_sql`/`_build_bq_monthly_series_sql` — see that agent's
  own card for the full story, including the sobering detail that the method copied from
  (`A9_Situation_Awareness_Agent._bq_monthly_series_sql`) had already been named **dead code to be
  removed** in this project's own Phase 10C decision record, not a pattern to extend. SA's duplicate is
  deliberately left untouched in this pass (pre-existing, separately tracked — not refactored the night
  before a demo).
- `_fetch_neighbour_evidence(...)` — combines both into one `NeighbourSnapshot`; independent fetches (a
  non-BigQuery KPI still gets its scalar snapshot, just no trend line).
- Module-level `_first_numeric_value(exec_result)` — parses a non-dimensional `execute_sql` result's
  single scalar (mirrors the `_as_map` closures' value-lives-in-the-last-column convention elsewhere in
  this file, without needing a full key→value map for a query that never had a grouping key).

**Concurrency**: fetched via `asyncio.Semaphore(6)`-bounded `asyncio.gather(..., return_exceptions=True)`
across every causal-graph alternative PLUS the primary KPI itself (for the chart's primary line) — never
sequentially, which would reintroduce the latency problem this design exists to avoid. `return_exceptions=True`
is load-bearing: it's what makes a raised exception (including `AttributeError` from a test stub with no
`data_product_agent` set) degrade to a `None` snapshot instead of aborting the whole framing prompt.

**Ranking + cap** (`_FRAMING_ALTERNATIVES_LIST_CAP = 5`): hop-tier first (fill 1-hop slots before
2-hop), then `|percent_change|` within a tier — confidence/provenance are a floor/tiebreaker, not the
sort key. Whatever doesn't make the cut is disclosed via `FramingPrompt.additional_causal_measures_count`,
never silently dropped. The market-signal alternative (if any) is exempt from this cap — appended after,
untouched. The chart component (`CausalTrendChart.tsx`) caps its own plotted lines at 3 independently —
5 vs. 3 is deliberate: text is cheaper to scan than an extra overlapping chart line.

**Frontend evidence/decision split** (§14 decision 8): `FramingGateCard.tsx` (Action Center, right panel)
was slimmed to a compact color-dot + short-label list — the mechanism/hop/confidence/provenance detail it
used to carry moved to a new `CausalNeighbourhoodEvidence.tsx`, rendered in a new "Causal Neighbourhood"
accordion in `DeepFocusView.tsx`'s left (primary) pane that **auto-expands** the moment the framing gate
activates (§14 decision 9 — evidence must be *seen*, not just fetched-and-collapsed). Color continuity
between the two panels (`decision-studio-ui/src/utils/causalColors.ts`) is the connective tissue — no
scroll-sync needed.

Covered by 50 new/extended tests in `tests/unit/test_da_framing_prompt.py` (`TestFirstNumericValue`,
`TestFetchNeighbourSnapshot`, `TestFetchNeighbourMonthlyTrend`, `TestFramingPromptRankingAndSnapshots`) —
ranking order (hop-tier beats magnitude), the cap + disclosure count, non-fatal degradation on every
failure mode (no `data_product_agent`, `generate_sql_for_kpi` failure, `execute_sql` raising, malformed
rows), and the market-signal alternative surviving the cap untouched.

## Causal direction filtering for hop 2+ alternatives (2026-08-20)

Found live: a Net Revenue framing gate offered COGS as a candidate alternative objective. COGS has no
real relationship to Net Revenue — the only path is two hops through `gross_margin_pct`, and the
connecting edge's own `mechanism` text says COGS causes margin, not the reverse; `get_causal_neighbourhood`
walked it backward because `KPIRelationship` had no field for which KPI causes which. Full design:
`docs/architecture/causal_edge_direction_and_magnitude_design.md`.

**Model + migration**: `KPIRelationship.causal_direction: Literal["kpi_causes_related",
"related_causes_kpi", "bidirectional", "unknown"]`, default `"unknown"` (additive — an edge nobody has
reviewed just can't be used as a stepping stone, not silently wrong). Migration
`20260820_kpi_relationship_causal_direction.sql`. **Same trap the causal-typing fields above already
warn about**: `KPIRelationshipProvider._row_to_model` and its `upsert()` INSERT/UPDATE both had an
explicit field allow-list that didn't know about the new column — reads silently defaulted back to
`"unknown"` regardless of what the DB actually held, exactly the failure mode the existing comment in
that file warns about. Fixed in the same commit; verified live by checking the DB directly (correct
values) against what the provider actually returned (wrong, until fixed).

**Filter lives in `_build_framing_prompt`, not `get_causal_neighbourhood`'s BFS.** The BFS stays
undirected on purpose — SA's compound-alert detection is right that two KPIs breaching together are
worth flagging regardless of which is upstream. `_build_framing_prompt`'s own visited-set replay now
also tracks `_validly_reached: Dict[str, bool]`, seeded `{kpi_id: True}`: hop 1 stays completely
unfiltered (decision #3, unchanged — a direct neighbour is shown regardless of its edge's direction).
For hop 2+, an alternative is only offered if **both** (a) the node being extended from was itself
validly reached, and (b) the current edge's `causal_direction`, read toward the origin, confirms the new
neighbour causes the known node. One unknown-direction edge anywhere on the path kills everything beyond
it, regardless of how well-directed the edges past that point are — chaining through a combining/ratio
node (like `gross_margin_pct`, which has both a revenue-side and a cost-side edge) doesn't compose into
a real inference about the original KPI unless every link back is confirmed.

Verified live against the real lubricants graph, not just unit-tested: analysing `net_revenue` now
returns only `gross_margin_pct` (1 hop); analysing `gross_margin_pct` still returns `base_oil_cost` and
`distribution_cost` at 2 hops (the 11F anchor scenario `get_causal_neighbourhood`'s own docstring was
written to support) while correctly excluding `product_sales_revenue` at 2 hops (its connecting edge to
`cogs` has no recorded direction).

5 new tests in `tests/unit/test_da_framing_prompt.py::TestCausalDirectionFiltering` — the real bug
reproduced directly (unknown-direction connecting edge), a second case where both edges are individually
directed but the second one is walked backward, the 11F chain staying included, hop-1 staying unfiltered
regardless of direction, and `"bidirectional"` confirming either walk. Two pre-existing tests
(`test_two_hop_edge_preserves_hop_distance_not_flattened`,
`test_ranking_hop_tier_first_then_magnitude`) needed their stub edges given an explicit
`causal_direction` to keep passing — their 2-hop stubs previously defaulted to `"unknown"`, which this
fix now correctly excludes; not a regression, a corrected assumption.
