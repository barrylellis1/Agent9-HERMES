# Agent9 Sprint Plan — March 2026
**Created:** 2026-03-10
**Horizon:** ~7 working days
**Goal:** Deliver Market Analysis Agent MVP + Opportunity Detection, wiring MA into the SA→SF pipeline and surfacing both positive and negative KPI signals in the Decision Studio UI.

---

## Sprint Context

The Executive Decision Briefing pipeline is now stable and production-quality (confirmed via lubricants PDF). The following are locked and working:
- SA → DA → SF multi-call architecture (stage1_only → hypothesis → cross_review → synthesis)
- Executive Decision Briefing: 19-page output with firm proposals, cross-review, options, roadmap, risk analysis
- Progressive reveal: real McKinsey/BCG/Bain hypothesis cards appear during Phase 2 of Council In Session
- ROI units (`pp`), recommendation rationale (LLM-generated), argument bullet formatting — all fixed

This sprint adds the **external intelligence layer** and **opportunity detection** on top of the stable foundation.

---

## Value Propositions Being Built

| Pillar | Status Before Sprint | Status After Sprint |
|--------|---------------------|---------------------|
| Problem detection (SA → DA → SF) | ✅ Working | Enriched with market context |
| Opportunity detection (positive KPIs) | ❌ Not built | ✅ SA detects positive signals → opportunity briefing |
| Market intelligence (MA Agent) | ❌ Not built | ✅ Perplexity + Claude → sf_context |
| Initiative tracking / ROI validation | ❌ Not built | 🔄 Data model only (full build Week 2+) |

---

## Day-by-Day Plan

### Day 1 — MA Agent Models + Skeleton (4–6 hrs)

**Deliverables:**
- [ ] `src/agents/models/market_analysis_models.py` — all Pydantic models from PRD Section 5
  - Enums: `MarketSignalType`, `MarketSignalDirection`
  - Models: `MarketSignal`, `CompetitorSignal`, `IndustryContext`
  - Requests: `MarketAnalysisRequest`, `MarketScanRequest`, `CompetitiveContextRequest`
  - Responses: `MarketAnalysisResponse`, `MarketScanResponse`, `CompetitiveContextResponse`
- [ ] `src/agents/new/a9_market_analysis_agent.py` — class skeleton
  - Lifecycle: `create()`, `connect()`, `disconnect()`
  - Stub all three entrypoints returning empty valid responses
  - Registry-compliant instantiation pattern (no direct instantiation)
- [ ] Unit test stubs: `tests/unit/test_a9_market_analysis_agent_unit.py`

**Acceptance:** Agent can be instantiated via registry; all three entrypoints return valid Pydantic responses (empty data, no errors).

---

### Day 2 — Perplexity Service + Haiku Classification (5–7 hrs)

**Deliverables:**
- [ ] `src/llm_services/perplexity_service.py`
  - OpenAI-compatible client (`base_url="https://api.perplexity.ai"`)
  - `PERPLEXITY_API_KEY` env var; graceful failure if missing
  - `async def query(prompt, model="sonar-pro") -> dict`
  - Exponential backoff (max 3 retries, 15s timeout)
  - Returns citations + snippets; raises `PerplexityUnavailableError` on failure
- [ ] Add `PERPLEXITY_API_KEY=` to `.env` (empty by default — fallback to Claude)
- [ ] Haiku KPI classification step in `analyze_market_opportunity`
  - Input: `kpi_name`, `kpi_delta`, `trigger_direction`, `sector`
  - Output: `signal_type`, `search_focus`, `sector_confirmed`
  - Route through `A9_LLM_Service_Agent` via Orchestrator
- [ ] Fallback path: if Perplexity unavailable → Claude native knowledge, `is_llm_derived=True`, `confidence` capped at 0.6

**Acceptance:** Haiku classifies "Gross Margin %" decline into correct signal buckets. Perplexity query executes and returns citations. Fallback works when `PERPLEXITY_API_KEY` is absent.

---

### Day 3 — Sonnet Synthesis + `analyze_market_opportunity` Full Flow (6–8 hrs)

**Deliverables:**
- [ ] Sonnet synthesis step: Perplexity output + KPI context → `MarketAnalysisResponse`
  - Structured JSON prompt targeting all response fields
  - `sf_context` dict populated per the integration contract (Section 6 of PRD)
  - `audit_log` entries for each LLM call + Perplexity query
- [ ] `analyze_market_opportunity` full 3-step flow:
  1. Haiku classification
  2. Perplexity query (with Claude fallback)
  3. Sonnet synthesis → MarketAnalysisResponse
- [ ] End-to-end test: run with lubricants "Gross Margin %" decline situation
  - Validate `sf_context` structure matches PRD contract
  - Validate `market_signals`, `competitor_signals`, `industry_context` populated

**Acceptance:** `analyze_market_opportunity` returns a populated `MarketAnalysisResponse` for a lubricants gross margin decline situation. `sf_context` contains all 6 required keys.

---

### Day 4 — SF Integration of `market_analysis_input` (4–6 hrs)

**Deliverables:**
- [ ] Orchestrator / SF API route: call MA before SF when situation context is available
  - MA called after DA, before SF `hypothesis` stage
  - MA response `.sf_context` passed as `market_analysis_input` in `SolutionFinderRequest`
- [ ] SF synthesis prompt update: inject `market_analysis_input` context into synthesis LLM call
  - When `market_analysis_input` is provided, include signals/competitor/benchmark/risk/opportunity context
  - Brief section added to synthesis output: "Market Context considered"
- [ ] Executive Briefing UI: if `market_analysis_input` was used, show a "Market Intelligence" badge on the briefing header
- [ ] Test: full lubricants run with MA wired in — confirm market signals appear in SF synthesis reasoning

**Acceptance:** End-to-end run produces an Executive Briefing where the SF options have been informed by market context. At least one option references external market signals in its rationale.

---

### Day 5 — Positive KPI Opportunity Detection (5–6 hrs)

**Deliverables:**
- [ ] SA Agent: add positive threshold detection logic
  - `KPIDefinition` supports `positive_threshold` (upper-bound, optional) alongside existing `thresholds`
  - When KPI exceeds positive threshold: create Situation with `severity=INFORMATION`, new tag `signal_type="opportunity"`
  - `positive_trend_is_good` field already exists on `KPIDefinition` — use it to determine threshold direction
- [ ] SA models: add `signal_type: Optional[str]` field to `Situation` (default `"problem"`, set to `"opportunity"` for positive breaches)
- [ ] Decision Studio UI: opportunity card variant
  - Green accent instead of red/amber
  - "Capitalise" action button instead of "Resolve"
  - Different icon (upward arrow / opportunity indicator)
  - Routes to SF with `trigger_direction="opportunity"` — MA produces opportunity-framed context
- [ ] Test: add positive threshold to one lubricants KPI (e.g., Quick Lube Franchise Network margin) and confirm green opportunity card appears

**Acceptance:** SA detects a positive KPI outperformance; a green opportunity card appears in Decision Studio; clicking "Capitalise" routes to the SF pipeline with opportunity framing.

---

### Day 6 — Value Assurance Data Model (3–4 hrs)

**Deliverables:**
- [ ] `AcceptedSolution` data model (backend)
  - Fields: `solution_id`, `situation_id`, `kpi_name`, `kpi_baseline` (value at acceptance), `estimated_roi_low`, `estimated_roi_high`, `estimated_roi_unit`, `accepted_at`, `accepted_by_principal_id`, `option_title`, `option_description`
  - Pydantic model in `src/agents/models/value_assurance_models.py`
- [ ] HITL approval in SF: when principal approves recommendation, persist `AcceptedSolution` record
  - Store in Supabase `accepted_solutions` table (migration script)
  - Link to original `situation_id`
- [ ] API endpoint: `GET /api/v1/solutions/accepted` — returns accepted solutions list for Value Assurance UI (placeholder, no UI yet)
- [ ] No UI required this sprint — data model + persistence only

**Acceptance:** When CFO approves a recommendation in the HITL workflow, an `AcceptedSolution` record is created in Supabase with baseline KPI value and estimated ROI range. Query via API confirms record exists.

---

### Day 7 — Polish, Testing, Docs (3–4 hrs)

**Deliverables:**
- [ ] Restart and run full lubricants pipeline end-to-end with all changes
- [ ] Fix any integration issues surfaced by end-to-end test
- [ ] Update `CLAUDE.md` with new agents/files added this sprint
- [ ] Agent card: `src/agents/new/cards/a9_market_analysis_agent_card.md`
- [ ] Update roadmap milestone dates to reflect accelerated delivery
- [ ] Unit tests: aim for 40% coverage on MA agent entrypoints

**Acceptance:** Full lubricants run produces an Executive Briefing enriched with market context. Positive opportunity detection works. `AcceptedSolution` records persisted. All existing unit tests pass.

---

## Files Created/Modified This Sprint

| File | Action | Day |
|------|--------|-----|
| `src/agents/models/market_analysis_models.py` | Create | 1 |
| `src/agents/models/value_assurance_models.py` | Create | 6 |
| `src/agents/new/a9_market_analysis_agent.py` | Create | 1–3 |
| `src/agents/new/cards/a9_market_analysis_agent_card.md` | Create | 7 |
| `src/llm_services/perplexity_service.py` | Create | 2 |
| `src/agents/new/a9_situation_awareness_agent.py` | Modify | 5 |
| `src/agents/models/situation_awareness_models.py` | Modify | 5 |
| `src/agents/new/a9_solution_finder_agent.py` | Modify | 4 |
| `src/api/routes/` (SF route) | Modify | 4 |
| `decision-studio-ui/src/` (opportunity card UI) | Modify | 5 |
| `decision-studio-ui/src/pages/ExecutiveBriefing.tsx` | Modify | 4 |
| `supabase/migrations/` (accepted_solutions table) | Create | 6 |
| `.env` | Modify (add PERPLEXITY_API_KEY=) | 2 |
| `CLAUDE.md` | Modify | 7 |
| `tests/unit/test_a9_market_analysis_agent_unit.py` | Create | 1, 7 |

---

## Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Perplexity API key not available | Fallback to Claude native knowledge; all tests designed to work without Perplexity |
| MA adds latency to SA→SF pipeline | MA call is async; can be parallelised with DA if needed; target < 15s |
| SA positive threshold needs KPI registry update | Add `positive_threshold` as optional field; existing KPIs unaffected |
| Supabase `accepted_solutions` table migration | Simple schema; migration script straightforward; reversible |

---

## What This Sprint Does NOT Include

- `scan_for_opportunities` proactive mode (Week 2+)
- `get_competitive_context` lightweight mode (Week 2+)
- Value Assurance UI and T+30/60/90 re-analysis (Week 2+)
- Full unit test coverage (40% target this sprint; 70%+ in Week 2)
- Stakeholder Analysis Agent (Phase 1, after first pilot signed)

---

## Success Criteria

At end of sprint, a full lubricants run should:
1. Detect the Gross Margin % decline (existing ✅)
2. Call Market Analysis Agent → return market signals, competitor context, industry benchmarks
3. Pass `sf_context` to SF synthesis → options reference external market context
4. Produce Executive Briefing with "Market Intelligence" badge
5. If a positive KPI threshold is breached, produce a green opportunity card in Decision Studio
6. When CFO approves a recommendation, persist `AcceptedSolution` to Supabase

---

*This sprint plan supersedes the Phase 1 timeline in roadmap.md for Market Analysis Agent (previously Jun 2026 — now accelerated to March/April 2026).*
