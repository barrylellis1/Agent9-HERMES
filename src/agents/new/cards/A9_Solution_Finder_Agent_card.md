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
| `synthesis` | `claude-sonnet-5` | Cross-review and consensus synthesis; `max_tokens=32000` (11O-B: 4.6 → 5 after A/B win — Sonnet 5 caught a data contradiction 4.6 glossed over, 32% faster) |

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

## Stage 1 Attribution Fix (Aug 2026)
Stage 1 results are keyed **positionally** from `asyncio.gather()` order — never by the LLM
echoing `persona_id` back. The old keying silently discarded a successful call whose JSON
omitted or renamed that field (observed live: council quietly ran with 2 of 3 firms). A
mismatched echo is logged and ignored; dropped personas emit a warning plus a
`dropped_personas` field on the `stage1_calls_complete` audit event.

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
