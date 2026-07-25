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
    synthesis_model: str    # default follows the SYNTHESIS routing table entry (claude-sonnet-5 as of 11O-B; honours CLAUDE_MODEL_SYNTHESIS)
    require_orchestrator: bool = False  # Can run standalone
    log_all_requests: bool = True
```

## Pipeline
1. Build a search query from `(kpi_name, industry, da_structural_context)` — structural segment names included for specificity; **no DA conclusion** at this stage to avoid confirmation bias
2. Call `PerplexityService` to fetch web-search results (signals + citations)
3. Convert Perplexity citations into `MarketSignal` objects
4. Send signals + `kpi_context` + `analysis_mode` to `A9_LLM_Service_Agent` (SYNTHESIS routing — claude-sonnet-5) for synthesis and conflict assessment — DA conclusion (analysis_mode/scqa) enters here, not at signal fetch
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

## LLM Configuration
| Task Type | Model | Rationale |
|-----------|-------|-----------|
| `synthesis` | `claude-sonnet-5` | Executive-quality market narrative synthesis (11O-B: 4.6 → 5) |

Environment variable override: `CLAUDE_MODEL_SYNTHESIS`

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
