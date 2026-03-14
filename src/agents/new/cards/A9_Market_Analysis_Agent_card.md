# A9_Market_Analysis_Agent Card

Status: MVP Active

## Overview
The `A9_Market_Analysis_Agent` retrieves external market signals relevant to a KPI anomaly and synthesises them into an executive-ready narrative using A9_LLM_Service_Agent. It is called optionally from the Solution Finder synthesis stage to enrich recommendations with external context.

## Protocol Entrypoints
- `analyze_market(request: MarketAnalysisRequest) -> MarketAnalysisResponse`

Models defined in `src/agents/models/market_analysis_models.py`.

## Configuration Schema
Defined in `src/agents/agent_config_models.py`:

```python
class A9_Market_Analysis_Agent_Config(BaseModel):
    model_config = ConfigDict(extra="allow")
    enable_perplexity: bool = True   # Set False for LLM-only mode
    max_signals: int = 5             # Max market signals per request
    synthesis_model: str = "claude-sonnet-4-6"
    require_orchestrator: bool = False  # Can run standalone
    log_all_requests: bool = True
```

## Pipeline
1. Build a targeted search query from `(kpi_name, industry, kpi_context)`
2. Call `PerplexityService` to fetch web-search results (signals + citations)
3. Convert Perplexity citations into `MarketSignal` objects
4. Send signals + `kpi_context` to `A9_LLM_Service_Agent` (claude-sonnet-4-6) for synthesis
5. Return `MarketAnalysisResponse` with signals, synthesis narrative, and confidence score

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
| `synthesis` | `claude-sonnet-4-6` | Executive-quality market narrative synthesis |

Environment variable override: `CLAUDE_MODEL_SYNTHESIS`

## Integration Points (Mar 2026)
- **SF Agent**: Called after synthesis completes; result stored in `SolutionFinderResponse.market_intelligence`
- **Refinement endpoint**: Called in parallel with turn 0 of Problem Refinement Chat; signals injected as `initial_external_context` so refinement LLM asks targeted questions
- **Perplexity model**: `sonar` (search-enabled); override via `PERPLEXITY_MODEL` env var

## LLM-Only Signal Generation (Mar 2026)
When `PERPLEXITY_API_KEY` is not set, `_llm_generate_signals()` asks the LLM (claude-sonnet-4-6)
to produce structured `MarketSignal` JSON objects from its training knowledge of the KPI and
industry. Signals are tagged `source="llm_knowledge"` and `sources_queried=["llm_knowledge"]`.
This ensures `MarketAnalysisResponse.signals` is always populated (not empty) so the refinement
amber panel renders and `external_context` is seeded even without a Perplexity subscription.

## Compliance
- A2A Pydantic IO for requests/responses
- Orchestrator-compatible lifecycle: `create()`, `connect()`, `disconnect()`
- Non-blocking — all failures are caught and logged; never breaks the SF pipeline
