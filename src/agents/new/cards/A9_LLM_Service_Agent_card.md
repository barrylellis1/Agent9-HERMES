# A9_LLM_Service_Agent Card

**Last Updated:** 2026-09-04  
**Status:** Operational (Centralized LLM Gateway — Anthropic primary)

## Overview
The `A9_LLM_Service_Agent` is the shared LLM gateway for Agent9. It standardizes all large-language-model operations, enforces guardrails, applies prompt templates, and abstracts provider-specific APIs. **Anthropic (Claude) is the primary provider** (`LLM_PROVIDER=anthropic`, the default); OpenAI is a secondary path (`LLM_PROVIDER=openai`), modernized Sep 2026 for gpt-5.6/gpt-6 model comparison — see Provider Abstraction. All other agents must route LLM interactions through this agent to guarantee policy compliance, logging, and consistent model selection.

## Protocol Entrypoints

| Method | Signature | Returns |
|--------|-----------|---------|
| `generate` | `async def generate(request: A9_LLM_Request) -> A9_LLM_Response` | Content + model + usage + operation |
| `generate_with_template` | `async def generate_with_template(request: A9_LLM_TemplateRequest) -> A9_LLM_Response` | Formatted template + generated content |
| `analyze` | `async def analyze(request: A9_LLM_AnalysisRequest) -> A9_LLM_AnalysisResponse` | Parsed analysis + confidence |
| `summarize` | `async def summarize(request: A9_LLM_SummaryRequest) -> A9_LLM_SummaryResponse` | Summary + compression_ratio |
| `evaluate` | `async def evaluate(request: A9_LLM_EvaluationRequest) -> A9_LLM_EvaluationResponse` | Rankings + rationale |
| `generate_sql` | `async def generate_sql(request: A9_LLM_SQLGenerationRequest) -> A9_LLM_SQLGenerationResponse` | SQL query + confidence + warnings |

(Models defined in `src/agents/new/a9_llm_service_agent.py` — all models inherit from A9AgentBaseRequest/Response)

## Configuration Schema
Defined in `src/agents/agent_config_models.py`:

```python
class A9_LLM_Service_Agent_Config(BaseModel):
    model_config = ConfigDict(extra="allow")
    provider: str            # default from LLM_PROVIDER env var → "anthropic" (default) or "openai"
    model_name: Optional[str] = None   # None → auto-selected from task_type via routing table
    task_type: str = "general"
    api_key_env_var: str     # auto-set from provider: ANTHROPIC_API_KEY / OPENAI_API_KEY
    max_tokens: int = 4096
    temperature: float = 0.7
    guardrails_path: str = "docs/cascade_guardrails.yaml"
    prompt_templates_path: str = "docs/cascade_prompt_templates.md"
    system_prompt_override: Optional[str] = None
    require_orchestrator: bool = True
    log_all_requests: bool = True
    use_mocks_in_test: bool = True
```

## Model Routing (Anthropic — primary provider)

Task-based routing lives in `src/llm_services/claude_service.py` (`get_claude_model_for_task()`). Per-call `model` on the request overrides everything; otherwise env var override, then default:

> **Callers pass `task_type`, not a model ID** (Sep 2026). The table below is the Anthropic *resolution* for each task type, not what call sites name. See `src/llm_services/model_routing.py`; the OpenAI equivalents are under Provider Abstraction.

| ClaudeTaskType | Default model | Env override | Consumed by |
|---|---|---|---|
| `SQL_GENERATION` | `claude-haiku-4-5-20251001` | `CLAUDE_MODEL_SQL` | `generate_sql()` entrypoint |
| `NLP_PARSING` | `claude-haiku-4-5-20251001` | `CLAUDE_MODEL_NLP` | DA insight extraction (JSON classification); VA narrative generation; SA card observations |
| `STAGE1_PERSONA` | `claude-haiku-4-5-20251001` | `CLAUDE_MODEL_STAGE1` | SF Stage 1 — 3 parallel persona calls (temperature=0.0 set by SF) |
| `REASONING` | `claude-sonnet-5` | `CLAUDE_MODEL_REASONING` | DA narrative summarization / hypotheses |
| `SOLUTION_FINDING` | `claude-sonnet-5` | `CLAUDE_MODEL_SOLUTION` | Legacy task type (SF now uses STAGE1_PERSONA + SYNTHESIS) |
| `BRIEFING` | `claude-sonnet-5` | `CLAUDE_MODEL_BRIEFING` | Reserved (PIB briefing composition is deterministic Jinja2, no LLM) |
| `SYNTHESIS` | `claude-sonnet-5` | `CLAUDE_MODEL_SYNTHESIS` | SF synthesis/cross-review; Market Analysis signal synthesis (MA config default follows this entry) |
| `GENERAL` | `claude-sonnet-5` | `CLAUDE_MODEL` | KPI Assistant (config default) |

Sonnet-tier tasks moved 4.6 → 5 in Phase 11O-B (Jul 2026) after a controlled three-way synthesis A/B (see DEVELOPMENT_PLAN.md Phase 11O-B). Rollback: set the env override(s) to `claude-sonnet-4-6`. Note Sonnet 5 rejects non-default sampling params — `build_messages_kwargs()` strips `temperature` for it automatically.

Per-task generation defaults (temperature/max_tokens) are also defined in `claude_service.py` — e.g. SQL/NLP at 0.1, synthesis at 0.7/8192. Callers may override per request (SF raises synthesis `max_tokens` to 16384).

### Known routing deviations (call sites that bypass the routing table)
- `a9_accountability_interview_agent.py`: hardcodes its own constants `MODEL_CHAT = "claude-haiku-4-5-20251001"` and `MODEL_ANALYSIS = "claude-sonnet-4-6"`.
- (Resolved Jul 2026: SA's situation-card observations and tension one-liner previously hardcoded Haiku; both now resolve via `get_claude_model_for_task(NLP_PARSING)` and honour `CLAUDE_MODEL_NLP`.)

## Default System Prompt & Prompt Templates
- **The product default system prompt lives in code**: `A9_DEFAULT_SYSTEM_PROMPT` in `src/llm_services/claude_service.py` — used by every call that doesn't pass its own `system_prompt` (SF briefing Q&A, DA insight extraction, SA card observations). Neutral and format-agnostic; each call site's prompt carries its own format instructions.
- **`docs/cascade_guardrails.yaml` is NOT read at runtime** (decoupled Jul 2026). It is a development-coaching artifact for the Windsurf/Cascade coding assistant that built the codebase — loading it as the runtime default leaked its `PLAN:/VERIFIED_ACTION:` format into a customer-facing answer once Fable 5 followed it literally. The agent's `_load_guardrails()` (unused at runtime) delegates to the in-code constant.
- Prompt templates are parsed from Markdown (`docs/cascade_prompt_templates.md`) for the `generate_with_template` entrypoint — no product code currently calls it.
- `system_prompt_override` config still takes precedence when supplied.

## Provider Abstraction
- **Anthropic (primary)**: `src/llm_services/claude_service.py` — async Messages API (`client.messages.create`), task-based model routing per the table above.
- **Capability-aware request builder (Phase 11O-A, Jul 2026)**: `build_messages_kwargs()` consults a per-model-family `MODEL_CAPABILITIES` map (longest-prefix match) before every call:
  - Drops `temperature` for families that reject sampling params (Sonnet 5, Opus 4.7/4.8, Fable 5); preserves it for Sonnet 4.6 / Haiku 4.5. Unknown model IDs get a conservative profile (no sampling params).
  - `output_config.effort` sent when `A9_LLM_EFFORT` env var is set and the model supports effort (unset = API default `high`). Named `A9_LLM_EFFORT`, not `CLAUDE_EFFORT` — the Claude Code harness injects `CLAUDE_EFFORT` into its shells.
  - Fable 5 requests automatically opt into server-side refusal fallbacks (`server-side-fallback-2026-06-01` beta → falls back to `claude-opus-4-8`; target overridable via `CLAUDE_FABLE_FALLBACK_MODEL`).
  - `stop_reason == "refusal"` returns `{"error": ..., "response": None}` — the agent layer converts this to `status="error"`. Text extraction takes the first `text` content block (Fable responses may lead with fallback/thinking blocks); the returned `model` field reports the model that actually served the response.
  - `max_tokens` clamped to the model family's output ceiling (warn on clamp).
- **OpenAI (secondary, model-comparison path)**: `src/llm_services/openai_service.py` — only initialized when `LLM_PROVIDER=openai`. Not exercised in the current deployment (`.env` sets `LLM_PROVIDER=anthropic`). Modernized Sep 2026 (SDK `openai==3.8.0`; was pinned at 1.30.1 from May 2024):
  - **Task map**: `sql_generation`/`nlp_parsing`/`general` → `gpt-5.6-luna`; `reasoning`/`solution_finding`/`briefing` → `gpt-5.6-terra`. Env overrides unchanged (`OPENAI_MODEL_SQL`, `OPENAI_MODEL_NLP`, …, `OPENAI_MODEL`). **`gpt-6-astra` is deliberately not a default** — at $10/$50 per 1M it must be requested explicitly so it can never be reached by accident under a spend cap.
  - **`max_completion_tokens` is always sent, never `max_tokens`** — gpt-5.x/gpt-6 reject the latter outright; gpt-4-turbo accepts either.
  - **`temperature` is dropped for gpt-5.x/gpt-6** (they accept only the default 1) and a warning is logged. Same constraint and same handling as Sonnet 5 above — `is_frontier_model()` is the OpenAI-side counterpart to `MODEL_CAPABILITIES`.
  - **`reasoning_effort`** (flat param on Chat Completions; the nested `reasoning: {effort}` form is Responses-API-only): `none|low|medium|high|xhigh`. **`max` is rejected by the API despite appearing in the gpt-6-astra model docs.** `none` is unavailable on astra. Exposed as `A9_LLM_Request.reasoning_effort`.
  - **Reasoning tokens bill as output** and are reported separately as `usage.reasoning_tokens`; `finish_reason` is now returned so synthesis truncation is detectable rather than inferred.
  - **Cross-provider guard**: call sites still resolve Claude model IDs via `get_claude_model_for_task()` and pass them as `request.model`. The OpenAI branch detects a non-OpenAI model name, substitutes the task-equivalent OpenAI model, and logs a warning. This is a bridge, not the design — the fix is a provider-neutral task→model resolver so callers pass a task type rather than a provider-specific model ID.
  - `gpt-4-turbo` supports neither structured outputs nor reasoning_effort, and **shuts down 2026-10-23**.
- Validates API key presence via config or environment. Initialization errors raise `RuntimeError` to surface misconfiguration early.

## Usage Notes
- Designed for orchestrator-driven lifecycle via `create`/`create_from_registry` factory methods.
- Returns structured usage metadata (token counts) and optional warnings to support cost and safety monitoring.
- SQL generation responses may include optional explanations/warnings to downstream agents.

## Compliance
- A2A-compliant Pydantic request/response models.
- Centralized logging enforced before returning LLM output.
- No direct environment secret exposure (API keys masked in logs).

## Request/Response Models

### A9_LLM_Request
```python
prompt: str                          # Prompt to send to LLM
model: Optional[str]               # Override default model
temperature: Optional[float]        # Override temperature (0–1)
max_tokens: Optional[int]           # Override max tokens
system_prompt: Optional[str]        # Override system prompt
operation: str = "generate"         # Operation identifier
```

### A9_LLM_Response
```python
content: str                        # Generated text
model_used: Optional[str]           # Model that was used
usage: Dict[str, Any]              # Token counts {prompt_tokens, completion_tokens, total_tokens}
operation: str                      # Operation performed
warnings: Optional[List[str]]       # Any warnings
status: str                         # "success" or "error"
error_message: Optional[str]        # Error details if status="error"
```

### A9_LLM_AnalysisRequest
```python
content: str                        # Content to analyze
analysis_type: str                  # Type: "sentiment", "topics", "entities", "summary", "custom"
context: Optional[str]              # Additional analysis context
model: Optional[str]                # Override model
max_tokens: Optional[int]           # Override max tokens
```

### A9_LLM_AnalysisResponse
```python
analysis: Dict[str, Any]           # Parsed analysis result (always JSON)
model_used: Optional[str]           # Model used
usage: Dict[str, Any]              # Token counts
confidence: float                   # Confidence score (0.0–1.0)
status: str                         # "success" or "error"
```

### A9_LLM_SQLGenerationRequest
```python
natural_language_query: str         # NL query to convert
data_product_id: str                # Target data product
yaml_contract: Optional[str]        # Data product contract YAML
schema_details: Optional[Dict]      # Schema field descriptions
filters: Optional[Dict]             # Additional filters to apply
include_explain: bool = False       # Include explanation in response
model: Optional[str]                # Override model
```

### A9_LLM_SQLGenerationResponse
```python
sql_query: str                      # Generated SQL
model_used: str                     # Model used
usage: Dict[str, Any]              # Token counts
confidence: float                   # Confidence (0.0–1.0) — reduced if validation warnings
explanation: Optional[str]          # SQL explanation if requested
warnings: Optional[List[str]]       # Validation warnings (e.g., unsafe patterns)
status: str                         # "success" or "error"
```

## Error Behaviour

| Scenario | Entrypoint | Returns |
|----------|-----------|---------|
| API key missing | All | `RuntimeError` on init; status="error" in response |
| Provider unavailable | `generate()` | status="error" with error_message |
| Invalid JSON response | `analyze()`, `evaluate()` | Repair attempted via `parse_llm_json`; on genuine failure → `{"raw_response", "_parse_error"}`, confidence 0.5 (see below) |
| Template not found | `generate_with_template()` | status="error", returns empty A9_LLM_Response |
| SQL validation fails | `generate_sql()` | confidence reduced (0.7×) + warnings appended |
| Timeout/network | All methods | Exception propagates; caller must handle or retry |

## JSON Response Parsing (`analyze`) — Aug 2026
`analyze()` routes response parsing through `src/llm_services/response_parsing.py::parse_llm_json`
rather than a bare `json.loads`. Two behaviours matter to callers:

- **Conservative repair**, least-invasive first, stopping at the first success: code-fence
  stripping → outermost `{...}` (handles prose before/after the JSON) → trailing commas →
  unescaped newlines inside strings. A repaired payload carries `_parse_repair: "<method>"` and
  logs a warning — invalid JSON from the model is a signal worth seeing even when recovered.
  Repairs never alter the meaning of an already-valid document, and non-dict JSON is rejected.
- **Diagnostics survive failure.** A genuine failure returns
  `{"raw_response": ..., "_parse_error": {msg, pos, lineno, colno, context, length}}`.

⚠️ **This class has NO `self.logger`** — it logs via the module-level `logger` (line 40). A
`self.logger` call on the parse-failure path raised `AttributeError`, propagated out of `analyze()`,
returned `status="error"`, and sent SF to its heuristic stub — destroying the very diagnostic it was
added to capture, and putting *"Tighten spend controls"* in front of a user. It shipped because 891
tests exercised `parse_llm_json` as a pure function and **nothing exercised the agent's error
branch**. `tests/unit/test_llm_service_parse_failure.py` now drives `analyze()` itself on the failure
path; one test asserts the absence of `self.logger` so the mistake cannot silently return.

Why: SF was falling back to its hardcoded stub in ~1 run in 6 under `status="success"`, on model
output that was complete and well-formed (27k chars, proper closing brace, inside a ```json
fence, far under budget). The `JSONDecodeError` was caught and discarded, so no audit trail could
say which character was rejected. Callers that treat a missing key as "the LLM produced nothing"
(SF's `heuristic_stub_fallback`) should surface `_parse_error` — SF now does.

## Recent Updates
- **Sep 2026**: OpenAI provider path made functional for gpt-5.6/gpt-6 model comparison. SDK `openai` 1.30.1 → 3.8.0 (two major versions; only this one file imports it, and openai 3.x vendors `httpx2` so the project's `httpx==0.25.2` is untouched). Fixes: (1) the agent dropped the caller's `model` on the OpenAI branch, pinning every call to the model fixed at construction — per-task routing was impossible; (2) `max_tokens` → `max_completion_tokens`; (3) `temperature` stripped for gpt-5.x/gpt-6 with a warning; (4) `reasoning_effort` plumbed through `A9_LLM_Request`; (5) `usage.reasoning_tokens` and `finish_reason` now returned; (6) removed an `os.environ` dump logged at INFO on every service init whose masking rule only caught names containing "key"/"secret", leaking `SF_PASSWORD`, `SMTP_PASSWORD` and `SUPABASE_DB_URL` in clear text. Verified live against all four allowed models. Anthropic path untouched and re-verified live; full unit suite green (1587 passed).
  - **Structured output (`response_schema`) now works on both providers.** `OpenAIService.generate_structured()` mirrors the Anthropic method's signature (`tool_schema`, `tool_name`) and return shape, so the agent calls either without branching on provider vocabulary; OpenAI uses native `response_format={"type":"json_schema","strict":true}` where Anthropic uses forced tool-use. Schema adaptation lives in `src/llm_services/openai_schema.py` — strict mode accepts a narrower dialect than `model_json_schema()` emits: every property must appear in `required` (optionals are preserved as `anyOf:[T,null]`), every object needs `additionalProperties:false`, and **open dicts (`Dict[str,X]`) are rejected outright**. `SFSynthesisSchema.cross_review` is `Dict[str, CrossReviewEntry]`, so it is rewritten on the wire as an array of `{key,value}` pairs and restored to dict shape after parsing — callers see the original shape. Dropping strictness for that one field instead would have made OpenAI's output unguaranteed while Anthropic's stayed guaranteed, turning an adapter artifact into an apparent model difference. `$defs`/`$ref` pass through; recursive schemas raise `UnsupportedSchemaError`. Tests: `tests/unit/test_openai_schema_adapter.py` (16). Verified live end-to-end on terra and astra with the real `SFSynthesisSchema`.
  - **Structured output guarantees SHAPE, not business rules** — on either provider. JSON Schema cannot express custom Pydantic validators (e.g. `DecisionAsk.decision_text` ≤25 words), so `model_validate()` can still fail on a schema-valid response; terra tripped that validator live, astra did not. SF's existing defensive parsing loop remains the second layer.
  - **`OpenAIService` is now async** (`AsyncOpenAI`), matching ClaudeService's `AsyncAnthropic` and for the identical reason. `generate()`, `generate_structured()` and `generate_with_template()` are `async def`; the agent awaits them. Measured with three concurrent gpt-5.6-luna calls: sync-in-`gather` 7.56s wall with wall/sum = 1.00 (strictly serialized) and **1 event-loop tick in 5.84s** — uvicorn frozen; `AsyncOpenAI` 2.85s wall with wall/longest = 1.00 (fully overlapped) and 50 ticks in 2.93s. Re-confirmed end-to-end through the agent: wall/longest = 1.00. The 2.7x is secondary; the event-loop figure is the real defect, and it is the same one fixed for Anthropic in Phase 11O-A.
  - **Provider-neutral task routing** (`src/llm_services/model_routing.py`). Call sites used to resolve a Claude model ID via `get_claude_model_for_task()` and pass it as `request.model`, hardcoding provider vocabulary into every caller. They now pass `task_type` and the LLM service agent resolves it against the configured provider's own table, so env overrides (`CLAUDE_MODEL_*` / `OPENAI_MODEL_*`) still apply. Resolution order in `generate()`: explicit `request.model` → `request.task_type` → the service's configured default. `task_type` was added to `A9_LLM_Request` and `A9_LLM_AnalysisRequest`, and is threaded through `analyze()` (SF, MA and VA all reach the LLM that way, so dropping it there would have silently defaulted all three).
    - 12 call sites converted across SF (stage1/critic/synthesis), SA (2), DA (2), MA (3), VA (1) and `workflows.py`. `TaskType` is the union of both vocabularies; the OpenAI table gained `stage1_persona`/`synthesis`/`critic` for parity, and both providers put the same tasks on the cheap tier so a comparison measures models rather than routing choices.
    - **Anthropic resolution is provably unchanged** — `resolve_model("anthropic", t) == get_claude_model_for_task(t)` for all 9 task types, asserted per-task in `tests/unit/test_model_routing.py` (55 tests), which also fails the build if any caller reintroduces a hardcoded model ID. Verified live on both providers: identical call sites resolve haiku/sonnet-5 on Anthropic and luna/terra on OpenAI, by configuration alone.
    - The OpenAI branch's cross-provider substitution is now a **backstop**, not the mechanism: if it warns, a call site has regressed.
- **Aug 2026**: `evaluate()` no longer fabricates a ranking when its JSON parse fails. On `json.JSONDecodeError` it used to synthesize a full `rankings` list — `score: 5.0` for every input option, `rank` = input order — none of it from the model, returned under `status="success"`. Same defect shape as the SF/DA fallback-frame fixes the same session (fabricated content on an LLM-failure path, indistinguishable from real output to a caller checking only `status`). Now routes into the `status="error"` shape that already existed two branches up in the same method (`rankings=[]`, a real error message) instead of inventing scores no one computed. Currently dead code — no caller found anywhere in `src/` — but reachable via the orchestrator's generic `execute_agent_method` dispatch, so closed before something calls it. No new test (no live caller to regress); covered by inspection and the existing full suite passing unchanged.
- **Aug 2026**: Robust `analyze()` JSON parsing + preserved decode diagnostics (above). Shared by DA and MA, not just SF. Tests: `tests/unit/test_llm_response_parsing.py` (16).
- **Jul 2026 (Phase 11O-A)**: Capability-aware request builder shipped — model capability map, sampling-param stripping for Sonnet 5 / Opus 4.7+ / Fable 5, refusal stop_reason handling, Fable server-side fallbacks, `A9_LLM_EFFORT` knob, output-ceiling clamp. `anthropic` SDK 0.84.0 → 0.116.0 (requirements floor `>=0.116.0`). Unit tests: `tests/unit/test_claude_service_capabilities.py` (11 tests). Routing table itself unchanged (still Sonnet 4.6 / Haiku 4.5) — refresh is Phase 11O-B.
- **Jul 2026**: Card refreshed — documented Anthropic-primary routing table, env overrides, per-agent consumers, and known routing deviations (SA hardcoded call sites, since resolved).
- **Mar 2026**: Switched to Anthropic Claude as primary provider (`LLM_PROVIDER=anthropic` default; OpenAI legacy fallback). Task-based model routing (`CLAUDE_MODEL_STAGE1`, `CLAUDE_MODEL_SYNTHESIS`, etc.). SQL generation confidence scoring with validation warnings. Template support via Jinja2 formatting.

## Dependencies
- `src/llm_services/claude_service.py` (async Messages API — primary)
- `src/llm_services/openai_service.py` (sync — still blocking; see the Sep 2026 entry under Recent Updates)
- Guardrails file: `docs/cascade_guardrails.yaml`
- Prompt templates: `docs/cascade_prompt_templates.md`
