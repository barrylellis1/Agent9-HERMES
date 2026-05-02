# LLM Service Agent PRD — Updated Alignment

## Overview

**Agent Name:** A9_LLM_Service_Agent  
**Status:** [MVP] — 2 of 4 entrypoints implemented  
**Last PRD Sync:** 2026-05-02  
**Code Location:** `src/agents/new/a9_llm_service_agent.py`  
**Provider Service:** `src/llm_services/claude_service.py`  
**Alignment:** 80% → 100% (removed audit_log, retry/circuit-breaker; documented task-based model routing)

---

## 1. Purpose & Role in Workflow

The LLM Service Agent is the **single router for all LLM calls** across all agents:
- **Provider abstraction** — Anthropic Claude (primary), OpenAI GPT (fallback)
- **Model selection** — Task-based routing (Stage 1 personas → Haiku; synthesis → Sonnet; NLP parsing → Haiku)
- **Token tracking** — Count input/output tokens for cost accounting
- **Guardrails** — Content filtering, prompt injection detection (future)
- **Fallback handling** — If Claude unavailable, retry with GPT-4 (Phase 10+)

Operates as a **routing layer** — NO agent instantiates OpenAI or Anthropic clients directly. ALL LLM calls go through `A9_LLM_Service_Agent.generate()`.

---

## 2. Design Philosophy

### 2.1 Provider-Agnostic Interface

LLM Service exposes a single `generate()` method regardless of underlying provider:

```python
response = await llm_service.generate(
    prompt="Analyze this situation...",
    model="claude-sonnet-4-6",  # or "gpt-4-turbo"
    system_prompt="You are a financial analyst...",
    temperature=0.7,
    max_tokens=2000
)

# Returns same LLMResponse regardless of provider
assert isinstance(response, A9_LLMResponse)
assert response.text  # Extracted completion
assert response.usage  # {input_tokens, output_tokens}
```

### 2.2 Task-Based Model Routing (Implemented)

Different tasks use different models for cost/latency optimization:

```
Task → Model Assignment:

Stage 1 LLM Persona Calls (SF agent):
  - KPI domain expert, market analyst, implementation lead
  - Model: claude-haiku-4-5-20251001
  - Rationale: 3 parallel calls; Haiku is 75% cheaper, 2x faster

Synthesis/Cross-Review (SF agent):
  - Review + consolidate Stage 1 outputs
  - Model: claude-sonnet-4-6
  - Rationale: Requires cross-domain reasoning; Sonnet better quality

NLP Parsing (NLP Interface agent):
  - Extract KPI/timeframe/grouping from natural language
  - Model: claude-haiku-4-5-20251001 (default)
  - Rationale: Deterministic regex better than LLM; Haiku fallback only

Deep Analysis Insights (DA agent):
  - Root-cause hypothesis generation
  - Model: claude-sonnet-4-6 (default)
  - Rationale: Complex dimensional analysis requires higher reasoning

Other Agents (MA, DPA, DGA):
  - Model: claude-sonnet-4-6 (default)
  - Can override via A9_LLM_Request.model field
```

### 2.3 Runtime Model Override (Implemented)

Agents can override task-default models via request field:

```python
request = A9_LLMAnalysisRequest(
    model="claude-opus-4-6",  # Override: use best model for this call
    prompt="This is mission-critical...",
    task="root_cause_analysis"
)

response = await llm_service.generate(request)
# Uses claude-opus-4-6, not the task-default claude-sonnet-4-6
```

**Precedence:** Runtime override > Task default > Provider default (Anthropic)

### 2.4 Scope: Core Routing Only

**Implemented:**
- Single generate() method
- Task-based model routing
- Runtime model override
- Token tracking (input/output count)
- Provider abstraction (Anthropic SDK)
- Error handling (rate limits, API errors)

**Out of Scope (Not in Current Development Plan):**
- Audit logging of all LLM calls — not in DEVELOPMENT_PLAN; may be revisited for Infra B2 enterprise deployments (line 558) with regulated-industry requirements
- Automatic retry with exponential backoff — not in plan; simpler to have caller implement backoff via orchestrator
- Circuit breaker (fallback to GPT if Claude unavailable) — not in plan; Anthropic API reliability sufficient for MVP
- Prompt caching (Claude Prompt Cache API) — not in plan; Phase 10D is MCP Abstraction, not prompt caching; caching deferred to Phase 13+ optimizations
- Fine-tuned models — not in plan; Phase 10E (Native AI Capabilities) covers Cortex/Mosaic, not fine-tuning

---

## 3. Entrypoints (2 Implemented + 2 Deferred)

### 3.1 generate() [IMPLEMENTED]

```
Input:
  A9_LLMRequest or A9_LLMAnalysisRequest:
    - prompt: str
    - system_prompt: Optional[str]
    - model: Optional[str]  # Override default
    - task: Optional[str]  # "stage1", "synthesis", "npl_parsing", etc.
    - temperature: float = 0.7
    - max_tokens: int = 2000
    - top_p: float = 1.0

Output:
  A9_LLMResponse:
    - text: str  # Extracted completion
    - model: str  # Actual model used
    - usage: TokenUsage  # {input_tokens, output_tokens, total_tokens}
    - stop_reason: str  # "end_turn" | "max_tokens" | "stop_sequence"
    - cached: bool  # Whether response was from cache (Phase 10D+)
```

**Behavior (Lines 145–280):**
1. Determine model:
   - If request.model provided → use it (runtime override)
   - Else if request.task provided → look up task-default model
   - Else → use provider default ("claude-sonnet-4-6")
2. Validate input constraints (max_tokens ≤ 4096, temperature 0.0–2.0)
3. Format Messages API call (Anthropic SDK):
   ```python
   response = await self.client.messages.create(
       model=model,
       max_tokens=max_tokens,
       system=system_prompt,
       messages=[{"role": "user", "content": prompt}],
       temperature=temperature,
       top_p=top_p
   )
   ```
4. Extract completion + token usage from response
5. Track tokens for cost accounting (Phase 10: write to Supabase)
6. Return A9_LLMResponse

**Error handling:**
- Rate limit (429) → raise RateLimitError (caller handles backoff)
- Authentication error (401) → raise AuthenticationError (configuration issue)
- API error (500+) → raise LLMServiceError (transient; caller may retry)

**Provider implementation:**
- **Anthropic (primary):** `src/llm_services/claude_service.py` uses Messages API
- **OpenAI (fallback, Phase 10+):** Not implemented; placeholder in factory

### 3.2 estimate_tokens() [IMPLEMENTED]

```
Input:
  prompt: str
  model: Optional[str] = None

Output:
  TokenEstimate:
    - input_tokens: int
    - estimated_output_tokens: int  # Conservative estimate
    - total_estimated_tokens: int
```

**Behavior (Lines 290–330):**
1. Use Anthropic's token counting tool (if available)
2. Or use regex heuristic: ~4 chars per token average
3. Return conservative estimate (useful for cost projection before calling generate())

**Note:** Estimate is approximate; actual usage from generate() response is authoritative.

### 3.3 log_audit_trail() [DEFERRED — Not in Current Development Plan]

**Original plan (v1.0):** Log all LLM calls to audit table (prompt, model, response, tokens, cost) for compliance.

**Status:** Not implemented. LLM Service Agent does NOT maintain an audit log in MVP.

**When relevant:** Infra B2 (Enterprise LLM Deployment Options, DEVELOPMENT_PLAN line 558) mentions "LLM prompt audit export" as a UI download feature for compliance review, but that's different from continuous logging. Audit logging not scheduled in DEVELOPMENT_PLAN.

**Deferred reason:** Token tracking sufficient for cost accounting in MVP; comprehensive audit logging deferred.

### 3.4 configure_fallback_provider() [DEFERRED — Not in Current Development Plan]

**Original plan (v1.0):** Enable automatic fallback to OpenAI if Claude unavailable (circuit breaker).

**Status:** Not implemented. Single-provider (Anthropic) only in MVP.

**When relevant:** Not in DEVELOPMENT_PLAN. Infra B2 (line 558) mentions "Azure OpenAI provider" but that's explicit customer selection, not automatic circuit breaker. Circuit breaker fallback deferred.

**Deferred reason:** Anthropic API reliability sufficient for MVP. Multi-provider automatic fallback deferred to Phase 13+ if demand emerges.

---

## 4. Provider Strategy

### 4.1 Anthropic Claude (Primary)

**Configuration:**
```python
# .env or environment variable
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

**Supported Models:**
- `claude-opus-4-6` — Flagship; best reasoning (used for critical analysis)
- `claude-sonnet-4-6` — Balanced; speed + quality (default for synthesis)
- `claude-haiku-4-5-20251001` — Fast + cheap (default for Stage 1 personas)

**SDK:** `anthropic>=0.84.0` (upgraded Feb 2026; uses Messages API)

### 4.2 OpenAI GPT (Fallback — Not Implemented)

**Status:** Placeholder in factory; not wired in MVP.

**When implemented:** Phase 10+ multi-provider strategy.

**Models (future):**
- `gpt-4-turbo` — Equivalent to Sonnet
- `gpt-4` — Equivalent to Haiku

---

## 5. Token Tracking & Cost Accounting

**Tracked:**
- Input tokens per call
- Output tokens per call
- Model used
- Timestamp

**Not persisted in MVP** — tokens counted in-memory, not logged to database. Phase 10+ will add Supabase logging for cost analytics.

**Cost calculation (for reference):**
```
Anthropic pricing (as of May 2026):
  - Haiku: $0.80 / 1M input, $4.00 / 1M output
  - Sonnet: $3 / 1M input, $15 / 1M output
  - Opus: $15 / 1M input, $75 / 1M output

Example Stage 1 call (Haiku):
  - 2000 input tokens × ($0.80 / 1M) ≈ $0.0016
  - 500 output tokens × ($4.00 / 1M) ≈ $0.002
  - Total: ~$0.004 per persona × 3 = $0.012 per SF workflow

Synthesis call (Sonnet):
  - 4000 input tokens × ($3 / 1M) ≈ $0.012
  - 1000 output tokens × ($15 / 1M) ≈ $0.015
  - Total: ~$0.027 per SF workflow

Full SF workflow: ~$0.040 (4 cents)
```

---

## 6. Implementation Status

| Entrypoint | Status | Lines | Notes |
|---|---|---|---|
| `generate()` | ✅ Production | 145–280 | Anthropic Messages API; task-based routing + override |
| `estimate_tokens()` | ✅ Production | 290–330 | Token counter for cost projection |
| `log_audit_trail()` | ❌ Deferred (Not in plan) | — | Compliance logging not scheduled in DEVELOPMENT_PLAN |
| `configure_fallback_provider()` | ❌ Deferred (Not in plan) | — | Multi-provider fallback not scheduled; Anthropic reliability sufficient for MVP |
| Anthropic SDK integration | ✅ Production | all | Messages API; async/await |
| OpenAI SDK integration | ❌ Not started | — | Deferred to Phase 10+ if multi-provider strategy approved |
| Prompt caching (Claude Prompt Cache) | ❌ Not implemented | — | Phase 13+ optimization; Phase 10D is MCP Abstraction, not caching |
| Fine-tuned models | ❌ Not implemented | — | Not in DEVELOPMENT_PLAN; Phase 10E covers Cortex/Mosaic, not fine-tuning |

---

## 7. Dependencies

- **Anthropic SDK** — `anthropic>=0.84.0`
- **A9_LLMRequest, A9_LLMResponse Pydantic models** — src/agents/models/llm_service_models.py
- **.env configuration** — `LLM_PROVIDER`, `ANTHROPIC_API_KEY`

---

## 8. Testing

**Unit tests:** `tests/unit/test_a9_llm_service_agent.py`
- ✅ generate() with default model
- ✅ generate() with runtime override
- ✅ Task-based model routing
- ✅ Token counting
- ✅ Error handling (rate limit, auth)
- ✅ Anthropic SDK integration (mocked; no live API calls in CI)

**Integration tests:** Run against live Anthropic API
- generate() with real Haiku model
- generate() with real Sonnet model
- Token usage matches estimate within 10%

---

## 9. Known Limitations

1. **Single-provider architecture** — Anthropic only; no fallback if Claude unavailable

2. **No retry logic** — Rate limits (429) or transient errors (5xx) not automatically retried; caller must implement backoff

3. **No prompt caching** — Every call re-processes full context; Claude Prompt Cache (Phase 13+) would reduce token usage ~10%

4. **No audit logging** — LLM calls not logged for compliance/debugging; Phase 10+ may revisit for enterprise deployments

5. **Fixed token budgets** — Max output always 2000 tokens; no adaptive budgeting based on task complexity

6. **No fine-tuned models** — All calls use base models; custom instruction sets not supported

---

## 10. Removed from v1.0 PRD (Not Implemented)

1. **Audit trail logging** — Original plan to log all calls to database for compliance and debugging. Not in DEVELOPMENT_PLAN. Deferred; Infra B2 may add UI-based audit export instead of continuous logging.

2. **Retry with exponential backoff** — Original plan to automatically retry transient failures (rate limits, 5xx errors). Not in DEVELOPMENT_PLAN. Deferred; simpler to have caller implement backoff via orchestrator.

3. **Circuit breaker + fallback provider** — Original plan to switch to OpenAI if Claude unavailable. Not in DEVELOPMENT_PLAN. Deferred; Anthropic API reliability sufficient for MVP.

4. **Prompt caching** — Original plan to use Claude Prompt Cache API to reduce token usage for cached contexts. Not in DEVELOPMENT_PLAN; Phase 10D is MCP Abstraction, not caching. Deferred to Phase 13+ optimizations.

---

## 11. Changelog

**v1.0 (2025-12-15)** — Initial MVP with ambitious scope (audit logging, retry, multi-provider, caching)

**v1.1 (2026-02-28)** — Anthropic SDK upgraded to 0.84.0 (Messages API); removed OpenAI support temporarily

**v2.0 (2026-05-02)** — Aligned with DEVELOPMENT_PLAN:
- Documented 2 core entrypoints (generate, estimate_tokens); 2 deferred with corrected rationale
- Removed audit_log entrypoint; clarified not in DEVELOPMENT_PLAN (may be UI-based in Infra B2 instead)
- Removed configure_fallback_provider; clarified not in DEVELOPMENT_PLAN
- Clarified single-provider (Anthropic) with placeholder for OpenAI Phase 10+
- Documented task-based model routing (Haiku for Stage 1, Sonnet for synthesis)
- Documented runtime model override precedence
- Updated implementation status to show MVP scope
- Added known limitations (no retry, no audit, no caching, no fine-tuning)
- Updated provider strategy section with cost breakdown
- Noted Phase 10D is MCP Abstraction (not prompt caching)

---
