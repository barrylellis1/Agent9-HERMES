# A9_LLM_Service_Agent Card

**Last Updated:** 2026-05-08  
**Status:** MVP (Centralized LLM Gateway)

## Overview
The `A9_LLM_Service_Agent` is the shared LLM gateway for Agent9. It standardizes all large-language-model operations, enforces guardrails, applies prompt templates, and abstracts provider-specific APIs (OpenAI, Anthropic). All other agents must route LLM interactions through this agent to guarantee policy compliance, logging, and consistent model selection.

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
    provider: str = "openai"
    model_name: Optional[str] = None
    task_type: str = "general"
    api_key_env_var: str = "OPENAI_API_KEY"
    max_tokens: int = 4096
    temperature: float = 0.7
    guardrails_path: str = "docs/cascade_guardrails.yaml"
    prompt_templates_path: str = "docs/cascade_prompt_templates.md"
    system_prompt_override: Optional[str] = None
    require_orchestrator: bool = True
    log_all_requests: bool = True
    use_mocks_in_test: bool = True
```

## Guardrails & Prompt Templates
- Guardrails YAML defines provider-specific system prompts, prohibited patterns, and required behaviors.
- Prompt templates are parsed from Markdown (`docs/cascade_prompt_templates.md`) and can be formatted with runtime variables.
- System prompts fall back to guardrail defaults unless `system_prompt_override` is supplied.

## Provider Abstraction
- **OpenAI**: Auto-selects model via `task_type` when explicit `model_name` not provided (e.g., `solution_finding` → `o1-mini`).
- **Anthropic**: Defaults to `claude-3-sonnet-20240229` unless overridden.
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
| Invalid JSON response | `analyze()`, `evaluate()` | Fallback to raw response or empty dict; confidence reduced |
| Template not found | `generate_with_template()` | status="error", returns empty A9_LLM_Response |
| SQL validation fails | `generate_sql()` | confidence reduced (0.7×) + warnings appended |
| Timeout/network | All methods | Exception propagates; caller must handle or retry |

## Recent Updates (Mar 2026)
- Switched to Anthropic Claude as primary provider (OpenAI fallback supported)
- Task-based model routing: `CLAUDE_MODEL_STAGE1`, `CLAUDE_MODEL_SYNTHESIS`, etc.
- SQL generation confidence scoring with validation warnings (unsafe patterns, non-SELECT start)
- Template support via Jinja2 formatting (in-memory cache via service layer)

## Dependencies
- `src/llm_services/claude_service.py` (async Messages API)
- `src/llm_services/openai_service.py` (sync, fallback)
- Guardrails file: `docs/cascade_guardrails.yaml`
- Prompt templates: `docs/cascade_prompt_templates.md`
