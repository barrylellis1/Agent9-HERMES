# A9_Market_Analysis_Agent Card

**Last Updated:** 2026-05-08  
**Status:** MVP Active

## Overview
The `A9_Market_Analysis_Agent` retrieves external market signals relevant to a KPI anomaly and synthesises them into an executive-ready narrative using A9_LLM_Service_Agent. It is called optionally from the Solution Finder synthesis stage to enrich recommendations with external context.

## Protocol Entrypoints

| Method | Signature | Returns |
|--------|-----------|---------|
| `analyze_market` | `async def analyze_market(request: MarketAnalysisRequest) -> MarketAnalysisResponse` | Market signals + synthesis + confidence |

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

## Request/Response Models

### MarketAnalysisRequest
```python
session_id: str                     # Caller-supplied session ID
kpi_name: str                       # Name of KPI under investigation
kpi_context: str                    # Anomaly description (e.g., "Gross Margin dropped 2.3pp")
industry: Optional[str]             # Industry segment (e.g., "lubricants")
principal_id: Optional[str]         # Principal making the request
max_signals: int = 5                # Max signals to return (1–20)
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
competitor_context: Optional[str]   # Reserved for future enrichment
confidence: float                   # Agent confidence (0.0–1.0)
sources_queried: List[str]          # ["perplexity"] or ["llm_knowledge"] (or both as fallback)
error: Optional[str]                # Error message if search/synthesis failed
timestamp: str                      # ISO timestamp of response generation
```

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
