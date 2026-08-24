# A9_Solution_Finder_Agent Card

Status: MVP Active

## Overview
The `A9_Solution_Finder_Agent` systematically generates, evaluates, and recommends solutions for diagnosed problems (often from Deep Analysis). It produces a trade-off matrix and emits a single HITL approval event per cycle (per PRD). It leverages the LLM Service to run an expert persona debate and synthesize a consensus rationale, with business context injection for domain-specific recommendations.

## Protocol Entrypoints
- `recommend_actions(request: SolutionFinderRequest) -> SolutionFinderResponse`
- `evaluate_options(request: SolutionFinderRequest) -> SolutionFinderResponse`

Models defined in `src/agents/models/solution_finder_models.py`.

## Configuration Schema
Defined in `src/agents/agent_config_models.py`:

```python
class A9_Solution_Finder_Agent_Config(BaseModel):
    model_config = ConfigDict(extra="allow")
    # Core behavior
    hitl_enabled: bool = True  # Single HITL event per cycle
    enable_llm_debate: bool = False  # Toggle persona debate and consensus
    expert_personas: List[str] = [
        "QA Lead", "Operations Manager", "Finance Controller"
    ]
    # Scoring weights
    weight_impact: float = 0.5
    weight_cost: float = 0.25
    weight_risk: float = 0.25
    
    # Hybrid Council settings
    enable_hybrid_council: bool = False
    consulting_personas: List[str] = []
    council_preset: Optional[str] = None

    # Orchestration & logging
    require_orchestrator: bool = True
    log_all_requests: bool = True
```

## Dependencies
- `A9_Deep_Analysis_Agent` (consumes its output for context)
- `A9_LLM_Service_Agent` (persona debate and narrative synthesis; fallback acquisition from AgentRegistry if not injected)

## LLM Configuration (Anthropic — via A9_LLM_Service_Agent)
| Task Type | Model | Rationale |
|-----------|-------|-----------|
| `stage1_persona` | `claude-haiku-4-5-20251001` | 3 parallel focused single-persona calls; temperature=0.0 for deterministic hypotheses |
| `synthesis` | `claude-sonnet-5` | Cross-review/moderator synthesis; `max_tokens=64000` — raised from 32000 after the moderator arm's first live run generated 30,303 output tokens (94.7% of budget, past the PM-6 90% threshold). Ledger rows carry `max_tokens` so utilization is checkable from the payload; the live harness fails any run at ≥90%. (11O-B: 4.6 → 5 after A/B win) |

**All calls stream** (`messages.stream`) via an `AsyncAnthropic` client. Both properties are
load-bearing, not incidental:
- **Streaming** is what permits `max_tokens > 20000` at all — the SDK rejects non-streaming
  requests whose `max_tokens` implies a >10-minute generation.
- **Async client** is what makes the three Stage 1 personas actually concurrent. With the
  sync client they were `gather`-ed but ran strictly serially (measured 0/3 overlapping
  pairs), and each one blocked the FastAPI event loop for every other request in flight.

⚠️ **`hypothesis`, `cross_review` and `synthesis` are three IDENTICAL requests.** `debate_stage`
only controls whether Stage 1 is skipped and whether the call short-circuits (`stage1_only`);
it does not vary the prompt or the budget. The UI sends `prior_transcript` forward each stage
but **no backend code reads it** — the stages do not build on one another; the only state that
carries forward is `prior_stage1_hypotheses`. So full mode pays for three full-size Sonnet
synthesis generations, not one (measured 233s / 272s / 191s, ~35k tokens each), and the
`hypothesis` stage's output is consumed by nothing. Read the `token_usage` audit event for the
actual per-stage split. **This architecture is scheduled for replacement** — see the 2026-08-04
block in `docs/prd/agents/a9_solution_finder_agent_prd.md` (council redesign: theory-guided
moderator, critic dual-duty, frontend collapse; DEVELOPMENT_PLAN.md Phase 15 Stage H).

Environment variable overrides: `CLAUDE_MODEL_STAGE1`, `CLAUDE_MODEL_SYNTHESIS`

## Key Features (Dec 2024)
- **Business Context Injection**: Loads domain-specific context from `src/registry_references/business_context/*.yaml` to inform LLM recommendations
- **Enhanced Problem Statement**: Dynamically constructs quantitative problem statements from Deep Analysis change points (KPI, delta, dimension, attribute)
- **Principal Input Support**: Accepts user-defined priorities and constraints via `PrincipalInputPreferences` to guide solution generation
- **Fallback LLM Acquisition**: If LLM service not injected by orchestrator, acquires directly from `AgentRegistry`
- **Prompt Constraints**: Forbids "more analysis" solutions; requires actionable, implementable recommendations

## Principal-Driven Approach (Dec 2024)
- **Decision Style to Persona Mapping**: Uses principal's `decision_style` from their profile to select appropriate consulting personas:
  - `analytical` → McKinsey-style (root cause, MECE, hypothesis-driven)
  - `visionary` → BCG-style (portfolio view, growth-share, value creation)
  - `pragmatic` → Bain-style (operational excellence, quick wins, results-first)
  - `decisive` → McKinsey-style (structured decision-making, clear trade-offs)
- **Persona Selection Priority**: Request override → decision_style → role affinity → MBB default
- **Framing Context**: All responses include `framing_context` with transparency about personas used and presentation style
- **Guardrails**: Agent adapts presentation FOR the principal, does NOT speak FOR the principal or impersonate colleagues

## Dynamic Diverse Council (Dec 2025)
- **Recommended Council Integration**: Accepts `recommended_council_members` from Deep Analysis Problem Refinement
- **Dynamic Cross-Review**: Cross-review section uses actual persona IDs from the diverse council (not hardcoded MBB)
- **Persona Resolution**: Uses `get_consulting_persona()` to resolve persona IDs from the consulting personas registry
- **LLM Instruction**: Explicit instruction to LLM to use the exact persona IDs provided in the cross-review JSON template
- **Persona Safety**: Initializes `persona_ids` before prompt construction to guarantee identifiers are always defined, even when debate presets are overridden.

## Multi-Call Architecture + Quality Fixes (Mar 2026 — Phase 11)
- **Multi-call debate stages**: `stage1_only` → `hypothesis` → `cross_review` → `synthesis`; Stage 1 runs 3 parallel Haiku calls (McKinsey/BCG/Bain); synthesis uses Sonnet
- **`impact_estimate` field**: Added to `SolutionOption` Pydantic model; LLM-generated recovery range extracted from synthesis output (e.g. "2.1–3.4pp Gross Margin recovery")
- **`impact_estimate.scope` / `scope_label`**: `enterprise` moves the headline KPI; `segment` moves one dimension member only. `None` means UNSTATED and must be read as unverified — never assumed enterprise. Exists because live runs emitted segment-sized ranges (18.5–28.3pp) under the enterprise KPI's name, sized from a single segment's 43.24pp decline, which VA registration reads verbatim into impact bounds it later grades against. **Prompt elicitation is currently DEFERRED** (synthesis is at its output ceiling — see `max_tokens` comment), so in practice scope is always `None` today and the VA approve path warns on every registration.
- **Synthesis output ceiling (FIXED — was a known defect)**: synthesis generated *exactly* 20000 output tokens against a 20000 `max_tokens` limit, truncated mid-object, parsed to `{"raw_response": ...}`, and returned the hardcoded heuristic stub ("Tighten spend controls") under `status="success"`. The 20000 wall was the SDK's non-streaming limit, not the model's — 24000/32000/64000 were all refused outright. Fixed by streaming the call; budget now 32000. The truncation was never prompt-size driven (it recurred with `debate_spec` back at baseline, on a *longer* body), so if it returns, watch the `heuristic_stub_fallback` audit event rather than prompt length.
- **Recommendation rationale**: Fixed extraction — now reads `parsed.get("recommendation_rationale")` instead of hardcoded boilerplate text
- **Stage 1 hypothesis restoration**: `stage_1_hypotheses` re-attached to cross_review/synthesis responses for progressive reveal in Council In Session UI
- **`max_tokens`**: Raised to 16384 to prevent synthesis truncation on complex briefings (superseded — now 32000, see above)

## Stage H — Theory-Guided Moderator (Aug 2026)
`enable_theory_moderator` (env: `SF_ENABLE_THEORY_MODERATOR`; requires `enable_causal_grounding`)
selects the NEW arm of the PM-2 A/B on the synthesis call:

- **Baseline arm (flag off, default):** the original simulated cross-review prompt, byte-for-byte
  untouched — one author writes all firms' critiques. Emits `cross_review`. Ledger label `synthesis`.
- **Moderator arm (flag on):** replaces the simulation with a MODERATOR DUTY section that grades
  every option against ground truth — constraint survival (vs the assumption register), causal
  grounding (named `kpi_relationships` edge or `ungrounded`), arithmetic consistency (recovery_range
  vs the actual data magnitudes), and critic-findings response (answered vs standing). Emits
  `moderator_grades` keyed by option id; `cross_review` is neither requested nor accepted (a stray
  one in the output is dropped — arms must not cross-contaminate). Ledger label `moderator`.
- **PM-1 denominator:** the prompt states exactly how much register it grades against ("Active
  constraints: N / Causal edges: M (by provenance: ...)"); zero constraints grades as
  `insufficient_data`, NEVER `pass`.
- **Scope elicitation (moderator arm only):** `impact_estimate` must carry `scope`/`scope_label`.
  PM-7 guard: `scope="enterprise"` + a named `scope_label` is self-contradictory — parser resets
  scope to `None` (label kept) and the call site emits an `impact_scope_contradiction` audit event.
- **PM-9 seam:** `moderator_protocol` config — `"judge"` implemented; `"integrator"` designed,
  gated, falls back to judge with a log line.
- Frontend runs TWO dispatches (`stage1_only` → `synthesis`); the dead `hypothesis`/`cross_review`
  dispatches and the never-read `prior_transcript` are gone; `VITE_DEBATE_MODE` is retired.

## Stage J — Enterprise Tradeoff Weights (Aug 2026) 🔴
Option ranking no longer uses the agent's own constant. `_rank_options` consumes
`request.evaluation_criteria`, resolved in this order by `_tradeoff_weights_to_criteria()`:

1. `request.evaluation_criteria` — explicit caller override → `criteria_source="request"`
2. `business_context.tradeoff_weights` → `criteria_source="business_context"`
3. `A9_Solution_Finder_Agent_Config.weight_impact/_cost/_risk` → `criteria_source="config_default"`

**The defect this closes.** `evaluation_criteria` existed on the request model and was read at both
call sites, but **nothing ever populated it** — so every ranking the product had ever produced used
`impact=0.5 / cost=0.25 / risk=0.25` regardless of client. Invisible because the rendered matrix looks
complete and fully weighted. Decision Quality link 4 failed 11/11 on the retrospective baseline.

**Weights are ENTERPRISE, never principal.** They live on `A9_PS_BusinessContext`
(`tradeoff_weights` + `strategic_posture`), round-tripped through the existing
`business_contexts.metadata` JSONB — no migration. Per-principal weights would violate the **M1
invariant** stated in this agent's own synthesis prompt (role adaptation controls entry point and
depth only; the conclusion is identical for every role), because ranking weights change which option
wins — measured: 4 of 11 saved arms flip across plausible CEO/COO/CFO profiles.

**`tradeoff_weights` are withheld from the LLM prompt** — `_business_context_for_prompt()` strips
them while keeping `strategic_posture`. The model authors the `expected_impact`/`cost`/`risk` scalars
that `_rank_options` then weights; letting it read the weighting invites it to tilt the scalars and
have the ranker apply the same weighting a second time. **Text drives generation, numbers drive
selection.** The `business_context` field on `A9_LLM_AnalysisRequest` never reaches prompt text (no
provider reads it) and the `llm_debate_analysis_req` audit event keeps the full context deliberately —
that is provenance, not input.

**Weights are relative, not normalised.** `_rank_options` computes
`impact_w*impact - cost_w*cost - risk_w*risk` with no rescaling. (Note `A9_PS_DecisionCriteria` in
`a9_debate_protocol_models.py` requires weights to sum to 1.0 — it is dead code, referenced nowhere,
and does NOT govern this path.)

**`TradeOffMatrix.criteria_source`** records provenance rather than leaving it inferable from values;
`src/analysis/decision_quality.py` reads it for link 4 and falls back to value comparison only for
payloads written before the field existed.

**Not built:** `_rank_options` has no tie band — an exact 0.0000 top-two tie is still presented as a
confident recommendation (observed on arm B0). No UI surfaces the weighting to a reader.

## Narrative Claim Validation (Aug 2026)
Every other guard in SF scores the **options**. The **prose** — `problem_reframe` and
`recommendation_rationale` — leads page one of the Executive Briefing, above the fold, and had
no check at all. Two real errors shipped past everything (2026-08-08, live run):

1. **Segment presented as the headline KPI** — *"headline KPI move recorded as a -43.24 point
   deterioration to a current level of -445.01"*. Gross Margin % was **30.29%**; `-445.01` /
   `-43.24` are Chain A's change-point `current_value` / `delta`. The model reached past the typed
   `KPIValue` into the change points and promoted one customer's slice to the enterprise number.
2. **Stated sum contradicting its own components** — *"-43.24pp … -16.76pp … -15.18pp … 140.4pp of
   combined drag"*. Those three sum to **75.18**, not 140.4 — overstated 1.9×.

Both are arithmetic, so `src/analysis/narrative_claims.py` checks them **without an LLM**: a model
reviewer could make the same slip and would make the check itself stochastic. Findings append a
`narrative_claim_mismatch` audit event (absent when clean — an event asserting "no problems" is
indistinguishable from a check that never ran) and log a warning. Non-fatal by design.

**False positives were the hard part.** A bare `/headline/` cue produced 4 false positives out of 6
findings on the real payload, all from one sentence enumerating segments *beneath* the headline.
Flags that cry wolf get ignored, which is worse than no flags. The cue now requires an assertion
verb, rejects subordinating prepositions (`beneath|below|under|behind`), and only considers numbers
within 90 chars of the cue. Result on the real payload: **exactly the 2 real errors, 0 false
positives.** Tests: `tests/unit/test_narrative_claims.py` (20), several pinning the *absence* of
those false positives.

## Stage 1 Attribution Fix (Aug 2026)
Stage 1 results are keyed **positionally** from `asyncio.gather()` order — never by the LLM
echoing `persona_id` back. The old keying silently discarded a successful call whose JSON
omitted or renamed that field (observed live: council quietly ran with 2 of 3 firms). A
mismatched echo is logged and ignored; dropped personas emit a warning plus a
`dropped_personas` field on the `stage1_calls_complete` audit event.

## Constraint Provenance and Exposure (Aug 2026, Stage I B-2)

Constraints previously travelled as bare strings, so nothing recorded whether one came from the
principal's interview or the assumption register. `ConstraintItem`
(`src/agents/models/deep_analysis_models.py`) attaches provenance: `id` (sha1 of normalized text —
the dedup key across turns and sources), `text`, `source`
(`refinement` | `assumption_register` | `kpi_relationship`), `discovered_by`, `asked_by`,
`turn_index`. `ProblemRefinementResult.constraints` remains the flat union of texts, so every
existing consumer is untouched.

### Two named budgets, not one outer cap 🔴

The Stage 1 merge previously read `(refinement + register)[:5]`. Five interview constraints therefore
crowded the assumption register out **entirely** — and the register is the Stage H moderator's whole
grading denominator, so a talkative refinement chat could silently disarm adjudication while the
prompt still reported a constraint count. Nothing asserted this. Now
`_MAX_REFINEMENT_CONSTRAINTS_S1` and `_MAX_REGISTER_CONSTRAINTS_S1` are applied separately and
concatenated with no outer cap.

### `compute_constraint_exposure()` — deterministic, always on

`enable_theory_moderator` defaults **False**, so on a default install nothing checks an option
against the constraints the principal stated. Safety must not depend on an optional LLM pass, so
exposure is computed in Python on every run:

```
{union_size, by_persona{pid: {seen, unseen}}, by_option{...}, moderator_checked}
```

It reports **who was told what**. It deliberately does **not** judge violation — whether an option
breaches a constraint is a semantic question, and a regex claiming to answer it would be exactly the
false confidence `src/analysis/` exists to avoid.

A persona has seen a constraint when `source != "refinement"` (register and relationship constraints
always reach every persona — splitting them would degrade the moderator whose denominator they are)
or its id is in `discovered_by`. **An empty `discovered_by` means every persona saw it**, which is
today's behaviour — so the report currently shows no exposure gap. That is the correct reading, not a
bug: the gap opens only once constraint sets are actually split (B-4, gated behind the B-3 test).
The net is installed before the thing that needs it.

### HITL surface states whether a check happened

`human_action_context` gains `constraint_union`, `recommended_option_unseen_constraints`, and
`constraint_check_performed`, with summary text conditional on the check. The load-bearing case is
moderator-off:

> *"N constraint(s) were captured, but no adjudication pass ran — no option has been checked against them."*

The previous unconditional "Review ranked options and approve or select an alternative" implied a
review had occurred when nothing had checked anything. Silence there is a claim.

New response field: `SolutionFinderResponse.constraint_exposure`.
Tests: `tests/unit/test_sf_constraint_exposure.py` (15).

### Found by the live run: `refinement_result` reached SF by only one of its two documented paths 🔴

The first live exposure report came back with `union_size: 1` — the assumption-register constraint,
**not the principal's own**. Two independent wiring gaps, both silent:

1. **`SolutionWorkflowRequest.refinement_result` was declared and never read.** SF only ever reads
   `preferences["refinement_result"]`, so a caller using the documented top-level field got no
   constraints, no exclusions, and no error. Same failure class as the never-wired
   `use_structured_output` flag: the field existed, typechecked, and did nothing. `workflows.py` now
   folds it into `preferences` (without clobbering an explicit entry) and a test asserts the wiring.
2. **The UI's `refinement_result` payload is an explicit field allow-list**
   (`useDecisionStudio.ts`), so `constraint_items` would never have reached SF from the real app
   either. Adding a field to `ProblemRefinementResult` is not sufficient — it must be added there
   too, and omitting it fails silently because the flat `constraints` list masks the loss.

**Rule:** a new field on `ProblemRefinementResult` needs THREE edits to reach Solution Finder — the
model, the UI allow-list in `useDecisionStudio.ts`, and (for non-UI callers) the top-level passthrough
in `workflows.py`. Verified live afterwards: `union_size: 2`, one `refinement` and one
`assumption_register`, each labelled with its provenance.

## Causal Traversal — reaching the upstream cause (Aug 2026) 🔴

**The defect.** Stage D fetched causal context with `get_relationships_for_kpi`, which returns only
edges that *touch* the analysed KPI. Measured against the live lubricants graph:

```
max_hops=1  ->  3 of 6 edges   (gross_margin_pct<->cogs, net_revenue, premium_mix_pct)
max_hops=2  ->  6 of 6 edges   base_oil_cost, distribution_cost, product_sales_revenue reachable
```

The three invisible edges included **`base_oil_cost -> cogs`** — labelled in the seed file as "the 11F
anchor scenario" and carrying that client's single most important causal fact:

> *"Base oil is the primary raw-material input (~50-60% of COGS). Price moves pass through to reported
> COGS with an inventory-buffered lag of roughly one month, so a spot-price spike shows up in margin a
> period later."*

The real chain is `base_oil_cost -> cogs -> gross_margin_pct` — **two hops**. SF saw one, so a margin
analysis could never reach the cause of its own margin problem. **A dimensional breakdown answers
WHERE a KPI moved; the causal graph is the only thing that answers WHY**, and it was read one hop too
shallow.

**The fix.** `KPIRelationshipProvider.get_causal_neighbourhood(kpi_id, client_id, max_hops=2,
max_edges=25)` — BFS over the undirected edge set, returning `[(relationship, hops), ...]` at shortest
distance. One `get_all` query, traversal in memory. Cycles terminate (each KPI expanded once);
bounded twice so a dense graph cannot flood a prompt. SF calls it with `_CAUSAL_MAX_HOPS = 2`.

**`get_relationships_for_kpi` is unchanged and still single-hop** — SA's compound-alert detection
(11I-B) and the registry API both genuinely want direct edges only. `max_hops=1` returns exactly the
old set, which is pinned by test.

**Hop distance is surfaced, never flattened.** `_build_causal_context_section` labels each entry
`[DIRECT]` or `[INDIRECT via N hops]`, and when any indirect edge is present adds:

> *"Entries marked INDIRECT are reached through another KPI rather than attached to this one. They
> often carry the upstream cause — a dimensional breakdown shows WHERE a KPI moved, not WHY — but the
> link is inferred across a chain, so treat it as a hypothesis to test with the principal, never as an
> established fact about this KPI."*

Presenting a two-hop chain as equivalent to a direct edge would manufacture confidence the graph does
not support — the same discipline as the provenance caveats. The moderator's denominator line reports
the split too (`Causal edges: 6 (3 direct, 3 indirect; by provenance: …)`), while a **zero** register
still renders exactly `Causal edges: 0 (by provenance: none)` — the PM-1 wording is pinned by test.

The section accepts bare relationships as well as tuples, so any caller not yet traversing still
renders. Tests: `tests/unit/test_causal_neighbourhood.py` (11).

## Market Signal Routing — own label, own budget, own path (Aug 2026) 🔴

**Three defects, one root shape.** Market Analysis runs at the end of the DA workflow and attaches
`market_signals` to the DA output. Solution Finder **never read that field.** The only route in was
`refinement_result["external_context"]`, populated by turn-0 seeding of the refinement chat.

1. **Skipping the refinement chat dropped every signal.** MA ran, signals were attached, and nothing
   downstream read them — only the `market_conflict` flag survived. Personas were told two things
   disagreed without being told what the external one said.
2. **Signals were attributed to the executive.** They rendered as `PRINCIPAL-PROVIDED CONTEXT (from
   refinement)` — market research presented as the principal's own words.
3. **Shared budget.** Signals and principal statements competed for the same `external_context[:3]`,
   so seeded signals crowded out what the executive actually said. Same failure shape as the
   refinement/register constraint budgets.

**Fix — `_format_market_signals(da_ctx, refinement_result)`:**

- Reads `da_ctx["market_signals"]` **first**, so signals arrive whether or not refinement ran; the
  seeded path remains a fallback for DA payloads that predate the field.
- Renders under its own heading: *"EXTERNAL MARKET SIGNALS (from Market Analysis — not the
  principal's own words)"*.
- Preserves `source` and `relevance_score` — flattening to a bare string discarded the provenance a
  persona needs to weigh a signal.
- Separate budgets: `_MAX_MARKET_SIGNALS = 5`, `_MAX_PRINCIPAL_CONTEXT = 3`.
- `_split_external_context()` separates MA-seeded items (prefix `Market signal: `) from what the
  principal typed, so each is presented under its true provenance and neither is double-counted.
- Dedup is on **content**, not the rendered line — the same signal arrives structured from DA and as
  a seeded string, and comparing rendered lines never matched (caught by test, not by review).

Reaches both the dataset recap **and** Stage 1 (`da_compact_s1["external_market_signals"]`); Stage 1
previously saw only the conflict flag. Tests: `tests/unit/test_sf_market_signal_routing.py` (10).

## Cost Observability — `token_usage` audit event (Aug 2026)
Every LLM call SF makes records into a per-run ledger; the totals are appended to the audit
log as a single `token_usage` event:

```json
{"event": "token_usage", "calls": 5, "input_tokens": 10447, "output_tokens": 21200,
 "total_tokens": 31647,
 "by_call": [{"call": "stage1_mckinsey", "model": "...", "input_tokens": ..., "output_tokens": ...}]}
```

- `call` labels: `stage1_{persona_id}`, `critic_pass`, `synthesis`.
- Stage 1 usage is recorded **before** the status check — a persona call that errors after
  generating tokens is billed just the same, so it must still appear.
- An **empty ledger emits no event at all**, rather than one reporting zero cost, which would
  be indistinguishable from a run that legitimately made no LLM calls.
- Recording never raises; cost accounting must not be able to break solution generation.

This exists because usage was already captured by `ClaudeService` but only reached a log line
in a detached console window, so "what did that debate cost" was unanswerable from the payload
and a stage quietly doubling in size was invisible.

## Synthesis Prompt Quality Improvements (Mar 2026 — Phase 12)
- **next_steps**: Requires minimum 4 items with action verb + named role + specific deliverable + deadline; rejects generic boilerplate
- **recovery_range**: RECOVERY RANGE ANCHORS include failure-mode fallback (30–60% of observed variance) to prevent LLM outputting 0.0
- **CONSISTENCY CHECK**: Validates that mix-shift recommendations target segments with better margins than the problem segment; forces explicit paradox resolution if not
- **unresolved_tensions.requires**: Format instruction with concrete example replaces enum placeholder ("human judgment / more data / stakeholder input")
- **recommendation_rationale**: Explicitly requires entity-specific rationale citing named data points; forbids generic boilerplate
- **UnresolvedTension model**: `requires` field docstring corrected to describe expected format, preventing LLM from echoing meta-labels verbatim

## Dual-Framing Pipeline — Benchmark Replication (Mar 2026)
- **`_extract_deep_analysis_summary()`**: Extracts top-3 `internal_benchmark` segments from DA output into `summary["benchmark_segments"]`
- **`_trim_deep_analysis_context()`**: Passes benchmark segments through in the trimmed DA context dict
- **Stage 1 prompts**: When `internal_benchmarks` present, task item 5 instructs each persona to consider replication strategies
- **Synthesis prompt**: `INTERNAL BENCHMARK FEASIBILITY` section added — at least one option MUST address replication when benchmark_segments are present

## Market Analysis Integration (Mar 2026)
- **Deep Analysis Workflow**: Market Analysis Agent now runs at the END of Deep Analysis workflow. Market signals are attached to DA output as `market_signals` field and passed downstream.
- **Problem Refinement Pipeline**: Problem Refinement Chat receives signals from DA output via `external_context`, enabling targeted questions anchored in market facts.
- **Solution Finding**: Market signals arrive via DA output → SF preferences as external_context. No separate MA call in SF. Post-synthesis enrichment has been removed.
- **`pending_market_signals` field**: Reserved on `SolutionFinderResponse` for future HITL signal confirmation workflow (not yet actively populated).
- **Backward Compatibility**: `market_intelligence` field is now always None (deprecated).

## Compliance
- A2A Pydantic IO for requests/responses
- Orchestrator-driven lifecycle; single HITL event per cycle
- Full audit logging of options, scoring, recommendation, and human approvals

## Deliverables (MVP)
- Ranked options with perspectives from expert personas
- Trade-off matrix (impact/cost/risk)
- Problem reframe (Situation/Complication/Question)
- Recommendation + rationale
- HITL approval context and audit trail

## Fast Debate Mode — Phase 10D (Apr 2026)

**Dev/prod performance split** controlled by `VITE_DEBATE_MODE` env var:

| Mode | Stages | API Calls | Latency | Use Case |
|------|--------|-----------|---------|----------|
| `fast` | stage1_only → synthesis | 2 | ~3 min | Development testing |
| `full` | stage1_only → hypothesis → cross_review → synthesis | 4 | ~9 min | Production |

- `.env.development`: `VITE_DEBATE_MODE=fast` — skips hypothesis + cross_review stages
- `.env.production`: `VITE_DEBATE_MODE=full` — all 4 stages for maximum depth
- Frontend conditional in `useDecisionStudio.ts` and `CouncilDebatePage.tsx`
- Backend stages 2-4 hit identical Sonnet endpoint — skipping 2-3 saves ~6 min with equivalent output quality

**DA context trimming** (token optimization):
- When Stage 1 hypotheses are present, `deep_analysis_context` (~8-12K tokens) is excluded from synthesis payload
- `da_summary` carries all key signals — full DA context is redundant when hypotheses already incorporate it
- Conditional: `_include_full_da = not stage_1_hyps_dict`

## Recent Updates (Apr 2026)
- Removed debug print statements from exception handling (cleanup)
- Error logging via logger.info() for LLM debate failures (fallback to heuristic)
- Phase 10D fast debate mode and DA context trimming shipped

- May 2026: Bug fixes — NaN normalization, multi-tenant kpi_registry collision fix, comparison value extraction
- Jun 2026: Cross-tenant business context fix — `_extract_deep_analysis_summary` now extracts `client_id` from `DeepAnalysisPlan`; unsafe unscoped KPI name scan removed from business context resolution; `client_id` threaded through `SolutionWorkflowRequest` → `SolutionFinderRequest` and all `runSolutionFinder` call sites. `change_points` NameError fixed (hoisted above `if not ps:` block).

## Opportunity Mode Framing (May 2026)

When the upstream DA output carries `plan.analysis_mode = "opportunity"`, SF switches its framing from problem-solving to replication/scaling:

**`analysis_mode` detection (priority order):**
- Primary: `request.preferences["analysis_mode"]` when it is a resolved binary mode (`"problem"` or `"opportunity"`) — this carries the HITL-resolved principal choice and overrides DA plan
- Secondary: `da_ctx["plan"]["analysis_mode"]` (DA plan's auto-detected mode; may be `"mixed"`)
- Default: `"problem"`

The HITL-resolved mode wins over `"mixed"` in the DA plan — a `"mixed"` plan value must never suppress a principal's explicit `"opportunity"` resolution.

**Stage 1 task (per-persona Haiku calls):**
| Mode | Task | hypothesis field | recommended_focus |
|------|------|-----------------|-------------------|
| `problem` | "Form hypothesis about root cause; propose intervention" | Root cause of decline | Underperforming segment |
| `opportunity` | "Form hypothesis about WHY the IS segment outperforms; propose replication strategy" | Outperformance driver | Leading IS segment entity |

**`problem_statement` construction:**
- Problem: `[KPI_DIRECTION: DECREASED] <KPI> dropped by X...`
- Opportunity: `[ANALYSIS_MODE: OPPORTUNITY] <KPI> is outperforming... The leading IS segment is '<key>' — replicate its outperformance.`

**Synthesis CRITICAL ACCURACY REQUIREMENT:**
- Problem: "situation MUST reflect OVERALL direction; complication = mixed performance"
- Opportunity: "situation MUST describe outperformance; complication = replication gap; all 3 options must address scaling, not fixing"

**`da_compact_s1`** now includes `"analysis_mode"` key so Stage 1 personas see it in KEY ANALYSIS SIGNALS.

**`where_signals` mode-filtering (May 2026):** In mixed mode the IS list carries both `segment_type="problem"` and `segment_type="opportunity"` items. Before Stage 1, `da_compact_s1["where_signals"]` is filtered by the resolved mode:
- `opportunity`: only opportunity-tagged IS items → `where_is_not` receives problem-tagged items as replication targets
- `problem`: no filtering — all IS items passed as-is
This eliminates LLM oscillation between "scale winners" and "fix losers" framings across repeated runs on identical data.

**Stage 1 temperature:** Fixed at `0.0` — ensures identical inputs always produce identical hypotheses, making recommendation output deterministic across repeated runs on the same DA result.

**Market Conflict Propagation (May 2026):** When `deep_analysis_output.market_conflict.detected` is true, the conflict summary is injected at both prompt stages:
- Stage 1: added to `da_compact_s1["market_signal_conflict"]` — each persona's hypothesis must account for the external contradiction
- Stage 2: added to `dataset_recap_lines` as `MARKET SIGNAL CONFLICT:` alongside principal context and refinement constraints

- May 2026: Business context client_id resolution — `_enrich_with_business_context` now resolves `client_id` from `da_summary["client_id"]` or `request.client_id` before falling back to KPI name scan, preventing cross-tenant context loading when two clients share a KPI name.

## Phase 11G — Mixed-Mode Input Resolution (May 2026)

When upstream DA executes in `analysis_mode="mixed"`, the frontend HITL resolution layer intercepts before SF is invoked. The HITL panel presents both sides (problem + opportunity segments) and offers three choices:
- **"Focus on Recovery"** → passes `analysis_mode="problem"` to SF
- **"Focus on Opportunity"** → passes `analysis_mode="opportunity"` to SF  
- **"Let Agent9 Decide"** → auto-selects the side with larger absolute net delta and shows reasoning

SF does **not** need to handle mixed mode directly. By the time SF receives a request, `analysis_mode` is always `"problem"` or `"opportunity"` (a HITL-resolved binary mode). If SF receives a mixed value, it should treat it as a protocol error and default to `"problem"`.

This design ensures:
- SF operates on binary modes only (no dual-tracking of options)
- VA receives consistent control group semantics (no ambiguous DiD setup)
- Principal engagement is focused (binary choice at a single HITL gate, not throughout SF)

---

## Assumption metadata elicitation (Aug 2026)

**Defect found:** five of seven `SolutionAssumption` fields were never populated. Only `assumption` and `validated_by` carried data on any option of any run; `grounded`, `confidence`, `provenance`, `validated_at` and `revalidation_days` all sat at their model defaults. The cause was simply that the synthesis JSON template asked for two fields and nothing else. Not visible from reading the schema — the fields look correct there — so only inspecting a live run surfaces it.

This mattered beyond cosmetics: `grounded` ("verifiable from SA/MA data at synthesis time vs. inferred by the LLM") is the signal separating a well-founded recommendation from a speculative one, and the assumption pre-registration in `workflows.py` maps `falsification_criterion` from `provenance`, so every persisted record carried `None` for it.

**Elicitation is deliberately designed against self-report inflation** — the model is being asked to report the fields it would be judged on:
- `grounded=true` requires naming the specific fact in the INPUT DATA supporting it
- the prompt states plainly that ungrounded is the *normal* case, and that mislabelling an inference as grounded is worse than admitting it
- the template example shows `false`, not `true`
- an explicit instruction not to list fewer assumptions in order to appear more certain

Observed behaviour on a live run: 2 of 9 assumptions claimed `grounded`, both traceable to the client-confirmed base-oil→COGS edge, while assumptions resting on `template`-provenance relationships were marked ungrounded **and** low confidence — the provenance ladder propagating into confidence, which is the intended behaviour.

**Rejected alternative:** an assumption-to-constraint ratio as a numeric confidence score. It inverts the incentive (assumption count as denominator rewards listing fewer, but naming assumptions is the honest act, and the model self-reports the list), treats constraints and assumptions as commensurable when one is a wall and the other a bet, confuses cardinality with criticality, and manufactures false precision. Preferred instead: constraint checks as a binary gate, naming the load-bearing assumption, and displaying the provenance mix rather than collapsing it to a scalar.

## Two silent-failure paths hardened (Aug 2026)

- **`_parse_key_assumptions`** caught every exception and dropped the entire assumption. Requesting three additional fields multiplies the chance one returns malformed, so a validation error would have silently destroyed the assumption *text* — the load-bearing part that VA later grades and that gets pre-registered at approval. Now salvages the text, discards only the bad metadata, and logs. Also coerces confidence synonyms; `"Medium"` is the likeliest slip because the same prompt uses Medium for risk and investment levels while this field only accepts `"moderate"`.

- **`_run_stage1`** logged on exception but had two paths returning `None` with no log at all (non-success status, or non-dict `analysis`). Observed 2026-08-02: two of three personas dropped out of the council with nothing logged anywhere, leaving the run impossible to diagnose after the fact — the only trace was a shorter list in `Stage 1 complete: [...]`. Now warns with status, analysis type, and error.

## Two fabricated-content paths closed; `lens_views` rename; Cat 2 firm-name rule (Aug 2026)

**`problem_reframe` no longer fabricated when the model's response carried none.** When `parsed.get("problem_reframe")` was empty, code used to synthesize `{"situation": kpi+" analysis", "question": "How to mitigate risk?", "key_assumptions": ["Data is accurate"]}` — a fabricated frame AND a fabricated assumption, neither of which the model said. With `AssumptionsPanel` now rendering `key_assumptions` with grounded/inferred provenance (Phase 13 Cat 3), that invented entry would have displayed as if the model had made a real, gradeable claim. Now stays whatever the parse actually returned — a bare `parsed.get("problem_reframe")`, flowing into `SolutionFinderResponse.problem_reframe: Optional[Dict] = None`. **Deliberately not touched:** the separate `heuristic_stub_fallback` branch further down (`options = [SolutionOption(title="Tighten spend controls", ...), ...]`, fired when the LLM yields zero parseable options) — that one already sets `analysis_degraded`/`degraded_reason` on the response and is a real, reasoned design tradeoff (preserves Stage 1 hypotheses on a truncated synthesis rather than discarding partial work), not an oversight. The UI-side gap it left — nothing stopped a degraded run's stub from being approved into Value Assurance — was closed the same session in `ExecutiveBriefing.tsx`.

**Firm names must not appear in output text (Phase 13 Cat 2).** Recorded as shipped via Phase 15 Stages A–B; never actually built. A live e2e run rendered *"This is Bain's Full Potential Transformation..."* into an option description and *"McKinsey's MECE cost-driver framing"* into the recommendation rationale — the council profiles name each firm and instruct "apply signature frameworks," so naming the firm in the answer was the obvious reading. New CONSTRAINTS-block rule forbids firm names (and possessives/paraphrases of them) in every returned field, while keeping persona identity as the reasoning anchor — this changes the words returned, not the analysis performed. Shipped without a dedicated live verification run: the leak is intermittent (one clean run, one leaking, same pipeline), so a single green run would not have proven much either way. `live-briefing-cat3.spec.ts`/`live-briefing-cat3-refined.spec.ts`'s firm-name sweep is the standing regression test.

**`PerspectiveAnalysis` → `LensView`, `SolutionOption.perspectives` → `lens_views`.** Settles a vocabulary collision — see `docs/architecture/principal_perspective_weighting_design.md`'s new disambiguation note. The synthesis prompt's JSON template key was renamed to match; the parser accepts EITHER key (`o.get("lens_views") or o.get("perspectives")`) so a model that hasn't fully adopted the renamed key, or an in-flight request against the old prompt, doesn't silently parse to zero lens views. Verified live: a real synthesis call returned `lens_views`, payload-vs-DOM count matched in the briefing drawer.

## Phase 19, Slice 7 — Solution Finder expresses the reframe (Aug 2026)

Without this, DA's framing gate (`A9_Deep_Analysis_Agent_card.md`) records and displays a
chosen objective but SF never acts on it — the whole feature would be hollow. New module
function `_build_chosen_frame_section(framing_decision) -> str` reads
`preferences.get("refinement_result", {}).get("framing_decision")` (a raw dict — the shape
`FramingDecision` serializes to over the wire: `choice`/`chosen_kpi_id`/`chosen_objective_text`/
`falsification_criterion`/`other_text`) and returns a `## CHOSEN FRAME` section stating the
objective and that every option MUST serve it, or `""` when no decision was recorded (never
fabricates a frame nobody chose — same discipline as the `problem_reframe` fix above).
Computed ONCE (persona-invariant text) right after `refinement_result` is extracted, closed
over by Stage 1's per-persona `_run_stage1` and reused directly in the synthesis prompt —
injected last among Stage 1's directive sections (after `principal_constraints_section`, right
before `## YOUR TASK`) and first among synthesis's (right after `debate_spec`, before
`decision_maker_synthesis_section` — the chosen frame governs how every other section should
be read, not the reverse).

**Reuses the SHAPE of `stage1_allow_frame_challenge` (below), not its mechanism.** That flag
phrases an alternative frame as *permission* ("you MAY instead propose a portfolio-level
response") — already tested and found insufficient
(`docs/architecture/persona_council_experiments.md` §7b, the D-arm null: permission alone
changed nothing measurable across 21 real-run options). This is the same underlying idea — an
option may serve an objective other than raw KPI recovery — but driven by a *recorded
decision* instead of optional per-persona license, which had never been tested until this. No
separate config flag gates it: the natural gate is data presence, since `framing_decision` can
only be non-None once a principal has actually submitted DA's mandatory gate.

Tests: `tests/unit/test_sf_chosen_frame_section.py` — the pure function (empty on
None/non-dict/blank objective, correctly labeled for `confirm_stated` vs `alternative`/`other`)
and, via the same `_CapturingOrchestrator` stub-harness `test_sf_stage_d_causal_grounding.py`
established, an end-to-end proof the section reaches BOTH the synthesis prompt AND every Stage
1 persona's prompt when a decision is present, and reaches neither when it's absent (the
flag-off-equivalent control).

## Stage 1 failure logging swallowed the real error message (Aug 2026)

Found live 2026-08-23: the first real production run of the Lens Council preset (Commercial /
Operational / Structural) had all three Stage 1 calls fail (`status=error`), but every log line
read `error=<bound method A9AgentBaseResponse.error of ...>` instead of the actual reason —
`A9AgentBaseResponse.error` is a classmethod constructor (`error(cls, request_id, error_message,
**kwargs)`), not a data field, so `getattr(s1_resp, "error", None)` always returned that bound
method object (truthy), and the `getattr(..., "error_message", None)` fallback in the same `or`
expression never evaluated. `error_message` is the only real field. Fixed by dropping the dead
`"error"` lookup entirely.

Ruled out persona resolution and `to_prompt_context()` as the cause — tested directly against
the live registry for all three lens personas, each resolves and builds a real prompt context
cleanly, no exceptions. The actual `A9_LLM_Service_Agent.analyze()` call is the remaining
suspect (three parallel calls via `asyncio.gather` failing identically and simultaneously is
consistent with something environmental at that moment — rate/concurrency limit, transient API
issue — rather than a persona-content defect, but unconfirmed). This fix means the next
occurrence logs the real reason instead of a useless method reference.
