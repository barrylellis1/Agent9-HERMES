# Market Analysis Agent PRD — Updated Alignment

## Overview

**Agent Name:** A9_Market_Analysis_Agent  
**Status:** [PARTIAL MVP] — 1 of 3 entrypoints implemented  
**Last PRD Sync:** 2026-05-02  
**Code Location:** `src/agents/new/a9_market_analysis_agent.py`  
**Implemented Entrypoints:** `analyze_market_opportunity`  
**Deferred to Phase 10D+:** `scan_for_opportunities`, `get_competitive_context`

---

## 1. Purpose & Role in Workflow

The Market Analysis Agent enriches Solution Finder recommendations with external market context:
- Competitive positioning signals (is the recommended action aligned with market trends?)
- Customer/industry sentiment (is the solution timely?)
- Regulatory or macro headwinds that could impact ROI

**In the SF Workflow:**
- After SF synthesizes trade-off matrix + recommendations
- MA is called to gather market context for each proposed solution
- Results enrich the briefing email and HITL approval narrative

---

## 2. Design

### 2.1 Analytical Approach (Implemented)

**Perplexity Web Search + Claude Synthesis (LLM-Only Fallback)**

When real market data providers are unavailable (Phase 10D+ MCP integration deferred), MA uses:
1. Perplexity AI API to search for recent market signals relevant to the KPI domain
2. Claude to synthesize findings into actionable competitive context

**Entry condition:** SF agent calls `analyze_market_opportunity(kpi_name, solution_recommendation)` after generating solutions

**Output:** Structured market signal (source citations, sentiment, confidence score) suitable for HITL approval briefing

### 2.2 Scope (MVP)

**Implemented:**
- Perplexity search integration
- Claude synthesis of market signals
- Confidence scoring (low/medium/high)
- Citation tracking for transparency

**Out of Scope (Not in Current Development Plan):**
- Direct integration with Bloomberg, Refinitiv, or other premium data vendors
- Scheduled scanning for emerging opportunities (no scheduler; current architecture synchronous)
- Competitive intelligence deep-dives
- Real-time market monitoring

---

## 3. Entrypoints

### 3.1 analyze_market_opportunity() [IMPLEMENTED]

```
Input:
  kpi_name: str              # E.g., "Gross Revenue"
  solution_recommendation: str  # The proposed action
  context: dict (optional)   # Additional domain hints

Output:
  MarketSignalResponse
    - signal_summary: str
    - competitor_context: str
    - sentiment: Literal["positive", "neutral", "negative"]
    - confidence: Literal["low", "medium", "high"]
    - source_citations: List[Citation]
    - recommendation_alignment: str
```

**Behavior:**
1. Constructs Perplexity query: `"{kpi_name} {solution_recommendation} market trends {domain}"`
2. Fetches recent articles/signals (last 30 days)
3. Passes signals to Claude with prompt: "Synthesize this market context for a business decision on {solution_recommendation}. Is this action aligned with current market signals? Provide 2–3 key findings."
4. Returns structured response with citations

**Example:**
- Input: kpi_name="Gross Revenue", solution="Expand into emerging markets"
- Output: Market sentiment positive (GDP growth in target regions), confidence=high, citations from recent analyst reports

---

### 3.2 scan_for_opportunities() [DEFERRED — Not in Current Development Plan]

**Status: Roadmap concept — not scheduled in DEVELOPMENT_PLAN.**

Autonomous periodic scan of market data for emerging opportunities matched to company's KPI portfolio.

**Rationale for deferral:**
- DEVELOPMENT_PLAN Phase 11F covers "Market Signal Conflict Detection" (responding to existing signals) but not proactive opportunity scanning
- Requires scheduled/offline execution framework (not yet built)
- Requires vendor data integrations (Bloomberg, Refinitiv, etc.) — out of scope MVP
- Current architecture is synchronous, embedded in SF workflow

---

### 3.3 get_competitive_context() [DEFERRED — Not in Current Development Plan]

**Status: Roadmap concept — not scheduled in DEVELOPMENT_PLAN.**

Deep competitor profiling for a specific market segment (requires premium data vendors and extensive context gathering).

**Rationale for deferral:**
- DEVELOPMENT_PLAN doesn't schedule this entrypoint; Phase 11F covers market signal conflict detection but not independent competitive profiling
- Requires Bloomberg/Refinitiv/S&P Capital IQ integration
- Out of scope for Perplexity LLM-only MVP
- Can be built as a standalone workflow after Phase 10D+ vendor integrations mature

---

## 4. Implementation Status

| Component | Status | Notes |
|---|---|---|
| `analyze_market_opportunity()` | ✅ Production | Perplexity + Claude synthesis working; used by SF agent in production |
| `scan_for_opportunities()` | 🔄 Deferred (Not in plan) | Roadmap concept; no scheduled phase |
| `get_competitive_context()` | 🔄 Deferred (Not in plan) | Roadmap concept; no scheduled phase |
| Perplexity API integration | ✅ Production | Fully integrated; authentication via env var |
| Citation tracking | ✅ Production | Sources extracted from Perplexity results |
| Sentiment analysis | ✅ Production | Claude-based classification |

---

## 5. Known Limitations

1. **Perplexity API rate limits** — ~20 queries per minute. High-volume SA scans (50+ KPIs) may queue.
2. **Search freshness** — Last 30 days. Older historical trends not captured.
3. **Domain-specific signal detection** — Relies on LLM prompt engineering. Premium data vendors (Phase 10D+) will improve signal quality.
4. **No real-time streaming** — Results delivered as batch after search completes.
5. **Citation accuracy** — Perplexity citations are best-effort; verify in briefing.

---

## 6. Dependencies

- **A9_LLM_Service_Agent** — all Claude calls routed through LLM service
- **A9_Solution_Finder_Agent** — orchestrates calls to MA after generating recommendations
- **Perplexity API** — external service; credentials in env var `PERPLEXITY_API_KEY`

---

## 7. Testing

**Unit tests:** `tests/unit/test_a9_market_analysis_agent.py`
- ✅ Perplexity response parsing
- ✅ Citation extraction
- ✅ Sentiment classification
- ✅ LLM response mocking (no live API calls in CI)

**Integration tests:** Run live Perplexity queries against prod API (manual, not in CI)

---

## 8. Changelog

**v1.0 (2026-02-28)** — Initial MVP with `analyze_market_opportunity()` only

**v1.1 (2026-05-02)** — Aligned PRD with actual implementation:
- Marked as [PARTIAL MVP] (1 of 3 entrypoints)
- Corrected deferred features: `scan_for_opportunities` and `get_competitive_context` are **not in DEVELOPMENT_PLAN** (were incorrectly marked as Phase 10D)
- Clarified scope: Perplexity + Claude synthesis only (no premium vendor integration)
- Documented known limitations and dependency on future vendor maturity
- Noted Phase 11F (Market Signal Conflict Detection) covers market signal integration but not autonomous scanning

---
