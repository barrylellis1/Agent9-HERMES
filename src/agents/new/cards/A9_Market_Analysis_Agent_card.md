# A9_Market_Analysis_Agent Card

**Last Updated:** 2026-06-02  
**Status:** Active (Phase 12A — Company Intelligence KPI Template Generator)

## Overview
The `A9_Market_Analysis_Agent` retrieves external market signals relevant to a KPI anomaly and synthesises them into an executive-ready narrative using A9_LLM_Service_Agent. It is called optionally from the Solution Finder synthesis stage to enrich recommendations with external context.

**Phase 12A extension:** the agent also researches a company's public footprint (filings, segments, peer benchmarks, strategic priorities) and produces a benchmark-anchored `CompanyKPIProfile` for org-first onboarding via `research_company_kpi_profile()`.

## Protocol Entrypoints

| Method | Signature | Returns |
|--------|-----------|---------|
| `analyze_market` | `async def analyze_market(request: MarketAnalysisRequest) -> MarketAnalysisResponse` | Market signals + synthesis + confidence |
| `research_company_kpi_profile` | `async def research_company_kpi_profile(request: CompanyResearchRequest) -> CompanyKPIProfile` | Benchmark-anchored template KPIs grouped by domain |
| `research_company_business_processes` | `async def research_company_business_processes(request: BusinessProcessResearchRequest) -> CompanyBusinessProcessProfile` | Selected canonical + extra business processes for a client |

Models defined in `src/agents/models/market_analysis_models.py`.

## Configuration Schema
Defined in `src/agents/agent_config_models.py`:

```python
class A9_Market_Analysis_Agent_Config(BaseModel):
    model_config = ConfigDict(extra="allow")
    enable_perplexity: bool = True   # Set False for LLM-only mode
    max_signals: int = 5             # Max market signals per request
    synthesis_model: str    # UNUSED by the agent (it passes task_type=SYNTHESIS); default now resolves per configured provider
    require_orchestrator: bool = False  # Can run standalone
    log_all_requests: bool = True
```

## Pipeline
1. Build a search query from `(kpi_name, industry, da_structural_context)` — structural segment names included for specificity; **no DA conclusion** at this stage to avoid confirmation bias
2. Call `PerplexityService` to fetch web-search results (signals + citations)
3. Convert Perplexity citations into `MarketSignal` objects
4. Send signals + `kpi_context` + `analysis_mode` to `A9_LLM_Service_Agent` (SYNTHESIS task type — resolved per provider) for synthesis and conflict assessment — DA conclusion (analysis_mode/scqa) enters here, not at signal fetch
5. Return `MarketAnalysisResponse` with signals, synthesis narrative, conflict dict, and confidence score

## Context Enrichment Strategy (May 2026)
Signal generation uses a two-tier enrichment to produce business-specific signals without confirmation bias:
- **Tier 1 — Registry context** (`business_context`): enterprise industry, subindustry, products/services from `SupabaseBusinessContextProvider`. Loaded in `workflows.py` using `client_id`. Covers high-level search scope.
- **Tier 2 — DA structural context** (`da_structural_context`): dimension names analyzed, IS segment values (product lines, channels, regions), change-point segment keys extracted from the DA response. These are structural facts (what exists in the data), NOT the conclusion (problem/opportunity).
- **Conclusion firewall**: `analysis_mode` and `kpi_context` (SCQA) are passed to `_synthesize()` only — never to `_llm_generate_signals()` or `_build_search_query()`. This ensures conflict detection is semantically meaningful (signals generated independently, then compared to conclusion).

## Graceful Degradation
- If `PERPLEXITY_API_KEY` is not set: skips steps 2–3 and synthesises from `kpi_context` alone (LLM-only mode)
- If the LLM service is unavailable: synthesis falls back to a formatted summary of raw signal text
- If MA agent is not registered in orchestrator: SF synthesis silently skips enrichment (try/except guard)

## Dependencies
- `PerplexityService` (`src/llm_services/perplexity_service.py`) — optional, web search
- `A9_LLM_Service_Agent` — synthesis narrative (acquired from AgentRegistry if not injected)
- `AuditService` (`src/services/audit_service.py`, 2026-10-02) — plain static service, not an
  agent, not registry-instantiated. `analyze_market` writes a `reliability.citation_quality`
  event when `request.client_id` is present. Never raises; a missing pool or failed write
  degrades silently, the analysis's own result is unaffected.

## Reliability panel signal — `reliability.citation_quality` (2026-10-02)

The fifth and final stage-wise signal — the only one of five with no signal at all until a live
SA→DA→MA→SF run showed zero MA entries reaching `audit_events`, confirmed to be because nothing
emitted one rather than because MA ran clean (`docs/architecture/audit_event_system_design.md`).

**`client_id` is new on `MarketAnalysisRequest`** (`src/agents/models/market_analysis_models.py`),
`Optional[str] = None` — the model never carried tenant scoping before. Wired at the one call site
that has it (`src/api/routes/workflows.py`'s DA→MA integration, `request.client_id` was already in
scope there). `company_profile.py`'s industry-research call site has no tenant context at all (it
runs before a client_id exists) and is left passing none — the signal simply skips for that path,
same posture as every other signal's missing-client_id behavior.

**`_citation_quality_outcome(error_msg, signals)`** (module-level pure function, same file):
`fail` when the search itself errored — a genuine availability problem; `pass` when at least one
`MarketSignal` carries a real `url` — the "resolves" half of "a citation resolves, is recent, and
is relevant, or it is not"; `abstain` otherwise (a pure LLM-knowledge fallback with no real search,
or Perplexity's own unattributed answer-text synthesis in `_parse_citations` — an intentional,
accepted shape, not a defect). Recency (`published_at`) and relevance (`relevance_score`) are
deliberately **not** checked: `published_at` is frequently absent even on genuine citations, and
`relevance_score` is LLM-assigned on every signal including fabricated ones, so neither field
reliably distinguishes a real citation from a synthesized one the way URL presence does.

Tests: `tests/unit/test_ma_citation_quality_reliability_event.py` (11) — the pure outcome function
across all three outcomes plus the error-takes-precedence edge case; real Perplexity citations
emit `pass`; the LLM-only fallback emits `abstain` not `fail`; a Perplexity search error emits
`fail`; no `client_id` skips emission entirely; an audit-write failure never breaks the analysis;
a missing `request_id` degrades to `None`, not a crash.

**`request_id` was never forwarded either (found and fixed 2026-10-03, same sweep as DA's identical
bug).** `MarketAnalysisRequest` is a plain `BaseModel`, not `A9AgentBaseRequest` — it had no
`request_id` field at all, so `AuditService.log(..., request_id=...)` would have raised
`AttributeError` the moment it was added naively. Fixed properly: added `request_id: Optional[str]
= None` to the model, and the DA→MA integration call site (`workflows.py`) now passes
`response.request_id` — DA's own `DeepAnalysisResponse.request_id`, the same id that ends up in the
frontend's `currentAnalysis.request_id` — so `reliability.citation_quality` correlates to the exact
same run as the DA `reliability.rollup_check` events it was invoked alongside, letting a per-run
reliability view show both.

## LLM Configuration
The agent names a **task type**, not a model (Sep 2026). It passes
`task_type=SYNTHESIS` on its three `analyze()` calls and the LLM Service Agent
resolves that against whichever provider is configured — the module-level
`_SYNTHESIS_MODEL` constant that pinned a Claude model ID at import time is gone,
replaced by `_SYNTHESIS_TASK`. See `src/llm_services/model_routing.py`.

| Task Type | Resolves to (anthropic) | Resolves to (openai) | Rationale |
|-----------|-------------------------|----------------------|-----------|
| `synthesis` | `claude-sonnet-5` | `gpt-5.6-terra` | Executive-quality market narrative synthesis (11O-B: 4.6 → 5) |

Environment variable override: `CLAUDE_MODEL_SYNTHESIS` / `OPENAI_MODEL_SYNTHESIS`

## Integration Points (Mar 2026)
- **SF Agent**: Called after synthesis completes; result stored in `SolutionFinderResponse.market_intelligence`
- **Refinement endpoint**: Called in parallel with turn 0 of Problem Refinement Chat; signals injected as `initial_external_context` so refinement LLM asks targeted questions
- **Perplexity model**: `sonar` (search-enabled); override via `PERPLEXITY_MODEL` env var

## LLM-Only Signal Generation (Mar 2026)
When `PERPLEXITY_API_KEY` is not set, `_llm_generate_signals()` asks the LLM (SYNTHESIS routing model)
to produce structured `MarketSignal` JSON objects from its training knowledge of the KPI and
industry. Signals are tagged `source="llm_knowledge"` and `sources_queried=["llm_knowledge"]`.
This ensures `MarketAnalysisResponse.signals` is always populated (not empty) so the refinement
amber panel renders and `external_context` is seeded even without a Perplexity subscription.

## Request/Response Models

### MarketAnalysisRequest
```python
session_id: str                     # Caller-supplied session ID
kpi_name: str                       # Name of KPI under investigation
kpi_context: str                    # Anomaly description (e.g., "Gross Margin dropped 2.3pp")
industry: Optional[str]             # Industry segment — loaded from business context registry, not principal profile
principal_id: Optional[str]         # Principal making the request
max_signals: int = 5                # Max signals to return (1–20)
analysis_mode: Optional[str]        # DA-determined mode ("problem"|"opportunity"|"mixed") — synthesis/conflict only, NOT signal fetch
business_context: Optional[Dict]    # Full enterprise context from SupabaseBusinessContextProvider (industry, subindustry, products_services, regions, etc.)
da_structural_context: Optional[Dict]  # Conclusion-neutral DA facts: dimensions analyzed, active IS segment values, change-point segment keys
                                    #   → used in signal generation to produce business-specific signals without revealing DA conclusion
```

### MarketSignal
```python
source: str                         # "perplexity" or "llm_knowledge"
title: str                          # Headline
summary: str                        # 1–2 sentence summary
relevance_score: float              # 0.0–1.0 (relevance to KPI)
published_at: Optional[str]         # ISO date string
url: Optional[str]                  # Source URL
```

### MarketAnalysisResponse
```python
session_id: str                     # Echoed session ID
kpi_name: str                       # Echoed KPI name
signals: List[MarketSignal]         # Retrieved market signals (empty list if no sources found)
synthesis: str                      # LLM-synthesized executive narrative
conflict: Optional[Dict]            # LLM conflict assessment — see below
competitor_context: Optional[str]   # Reserved for future enrichment
confidence: float                   # Agent confidence (0.0–1.0)
sources_queried: List[str]          # ["perplexity"] or ["llm_knowledge"] (or both as fallback)
error: Optional[str]                # Error message if search/synthesis failed
timestamp: str                      # ISO timestamp of response generation
```

### Conflict Assessment (returned inside synthesis call when analysis_mode supplied)
```python
# conflict dict shape:
{
  "detected": bool,                          # True when signals contradict DA conclusion
  "type": str | None,                        # "headwind_vs_opportunity" | "tailwind_vs_problem"
  "confidence": float,                       # LLM confidence in the conflict assessment (0–1)
  "summary": str | None                      # One-sentence executive explanation
}
```
The LLM determines conflict semantically — no keyword lists. Conflict is `None` when `analysis_mode` is not supplied.

## Error Behaviour

| Scenario | Returns | Graceful Fallback |
|----------|---------|-------------------|
| Perplexity API unavailable | sources_queried excludes "perplexity"; signals may be empty or LLM-only | LLM fallback: `_llm_generate_signals()` asks Claude for signals from training knowledge |
| LLM service unavailable | synthesis falls back to formatted signal text; confidence reduced | Plain-text summary of raw signal titles/summaries |
| No signals found from any source | signals=[], synthesis="" | Empty lists + confidence=0.5; do NOT raise exception (non-blocking) |
| Perplexity timeout (>5s) | Caught and logged; skips to LLM fallback | LLM-only mode activated |
| Invalid JSON in LLM signal response | Attempts regex fallback; logs warning | Returns empty signal list; does not break SF pipeline |

**Key Design:** All failures are caught and logged. The agent never raises exceptions that would break the Solution Finder synthesis pipeline — it gracefully degrades to LLM-only or empty signals.

## Compliance
- A2A Pydantic IO for requests/responses
- Orchestrator-compatible lifecycle: `create()`, `connect()`, `disconnect()`
- Non-blocking — all failures are caught and logged; never breaks the SF pipeline
- Registry lookups via orchestrator when available; direct AgentRegistry fallback when not
- LLM calls routed through A9_LLM_Service_Agent (acquired at connect time)

## Phase 12A — Company Intelligence KPI Template Generator (June 2026)

### `research_company_kpi_profile(request) -> CompanyKPIProfile`

Researches a company's public footprint to generate benchmark-anchored KPI templates for org-first onboarding. The admin enters a company name; the agent returns 5–30 candidate KPIs grouped by domain (Finance, Operations, etc.) with industry-relevant benchmark ranges and source attribution.

**Pipeline:**
1. Build 4 targeted Perplexity queries: filings, business segments, peer benchmarks, strategic priorities
2. Run all 4 in parallel via `asyncio.gather`
3. Synthesise via Sonnet into structured `CompanyKPIProfile` with M1 source attribution + M6 source-type-only citations
4. Graceful fallback (M4): when Perplexity is unavailable, single LLM-only call with `degraded=True` and all `benchmark_source='inferred'`

**Pre-mortem mitigations enforced in code:**
- **M1** — every benchmark carries a `benchmark_source` from {filing, peer, inferred}
- **M4** — Perplexity failure or empty results triggers LLM-only fallback; never raises
- **M6** — synthesis prompt forbids specific competitor names and figures-as-fact; cites source TYPES only

**Models** (defined in `src/agents/models/kpi_template_models.py`):
- `TemplateKPI` — name, definition, unit, benchmark_low/high, benchmark_range, benchmark_source, confidence, domain, business_process_id
- `CompanyKPIProfile` — company_name, industry_inferred, is_public, domains, template_kpis, research_sources, generated_at, degraded
- `CompanyResearchRequest` / `CompanyResearchResponse` — API I/O wrappers

**API surface:** `POST /api/v1/templates/research-company` → returns `CompanyResearchResponse`; `POST /api/v1/templates/commit` writes accepted KPIs to the registry with `status='template'`.

**Downstream impact:**
- SA agent skips `status='template'` KPIs during `_load_kpi_registry` — template rows never reach detection until the admin connects data sources and promotes them to `status='active'`
- Template KPIs use `data_product_id='pending'` as a sentinel until data is connected

## Phase 12F — Business Process Template Generator (July 2026)

### `research_company_business_processes(request) -> CompanyBusinessProcessProfile`

Selects the business processes relevant to a client from the canonical taxonomy
(`src/registry/canonical/business_processes.py`, 39 processes across 12 domains — the
existing single source of truth, already used by `scripts/onboard_client.py` for scripted
seeding), plus proposes a small number of client-specific extras not in that taxonomy.

**No external research needed** — unlike KPI templates, this is a pure selection/curation
task over already-known data, not benchmark research. No Perplexity search is performed.

**Pipeline:**
1. Resolve industry context: stored company profile (`business_contexts` table via
   `SupabaseBusinessContextProvider.get_context()`) first, then `request.industry_override`,
   else `degraded=True` and select from a generic cross-industry prompt.
2. Single LLM call (`_llm_json_call`) given the full compact canonical taxonomy listing,
   asking only for `selected_canonical_ids` + `extra_processes` — the LLM never regenerates
   canonical content.
3. **Canonical selections are hydrated server-side from `BP_BY_ID`, verbatim** — protects the
   canonical taxonomy as ground truth even if the LLM echoes different name/description text.
   Extra processes are validated/slugified; any colliding with an existing canonical id is
   dropped (merge-into-canonical, not duplicated).

**Models** (defined in `src/agents/models/business_process_template_models.py`):
- `TemplateBusinessProcess` — id, name, domain, description, owner_role, stakeholder_roles,
  tags, source ('canonical'|'extra'), confidence, rationale
- `CompanyBusinessProcessProfile` — client_id, industry_used, domains, selected, generated_at,
  degraded
- `BusinessProcessResearchRequest` / `Response` — API I/O wrappers

**API surface:** `POST /api/v1/templates/research-business-processes` → returns
`BusinessProcessResearchResponse`; `POST /api/v1/templates/commit-business-processes` writes
accepted processes directly to the `business_processes` registry (no template/active lifecycle
— a committed business process is immediately valid, unlike KPIs).

**Downstream impact:**
- The accountability interview (`a9_accountability_interview_agent.py::_load_registry_context`)
  already queries the real `business_process` provider and falls back to KPI-derived
  pseudo-processes only when the table is empty — once real rows exist for a client it upgrades
  automatically, no code changes needed there.

## The market-shift check: the confirming question for a gap that is everywhere (Oct 2026)

When Deep Analysis finds no IS NOT (every segment is off its own comparison, see
`src/analysis/deviation_scope.py`), the cause is common to the whole business. One of the two
candidates is a shift in the market, and this agent is asked whether its signals support that.

- **Input:** `MarketAnalysisRequest.general_deviation` (the reader's sentence from
  `deviation_scope.describe`). Set by the deep-analysis route in `workflows.py`. None on every
  other request, and then nothing below runs.
- **Firewall:** used at SYNTHESIS only, like `analysis_mode`. It never reaches the search query,
  so the internal finding cannot shape which signals are fetched.
- **Output:** `MarketAnalysisResponse.market_shift` =
  `{"assessment": "supported" | "not_supported" | "insufficient", "confidence": 0-1 or None,
  "summary": str or None, "grounded": bool}`. `grounded` is true only when at least one signal
  carries a source URL.
- **No source, no answer 🔴:** when `grounded` is false (always, in LLM-only mode) the assessment
  is recorded as `insufficient`, confidence None, with the fixed summary
  `UNSOURCED_MARKET_SHIFT_SUMMARY`. What the model said is kept as `unsourced_assessment` /
  `unsourced_summary` for the audit trail only; no surface may show it as the answer. Reason: two
  live runs on the same data (2026-10-13) answered "not_supported" then "supported".
- **Fail-safe:** `_record_market_shift` turns any answer outside the three values into
  `insufficient`. An unreadable answer is not a confirmation. If the question was asked and the
  model returns no `market_shift` (seen live once), `analyze_market` records `insufficient` with
  `unanswered: true` and `UNANSWERED_MARKET_SHIFT_SUMMARY`. None now means only "not asked".
- **Must NOT:** infer a market shift from the internal gap itself (the prompt says so), and must
  not decide between the two candidates. It answers one of them; the other (the plan or the
  comparison itself is off) is not something market signals can settle.

The route attaches the answer to the deep-analysis result as `market_shift`, next to
`market_conflict`. Solution Finder reads it into its synthesis recap.

Tests: `tests/unit/test_ma_market_shift_check.py`.

### Reading the synthesis reply (Oct 2026) 🔴

Found by the first live run of the check above: the model wrote one JSON object, a sentence saying
a compliant one followed, then a second object. The LLM service could not parse it and returned
`{"raw_response": ..., "_parse_error": ...}`; `_synthesize` then returned `str(analysis)`, so the
market briefing shown to the reader was a Python dict repr and the market-shift answer was lost.

`_parse_synthesis_reply` reads every JSON object in the reply and uses the last one that has a
`synthesis`. `raw_response` is now read as reply text. A reply with no readable object and a brace
in it falls to `_plain_text_fallback`: a raw payload is never returned as the synthesis.
