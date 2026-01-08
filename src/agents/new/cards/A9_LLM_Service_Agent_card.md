# A9_LLM_Service_Agent Card

Status: MVP (Centralized LLM Gateway)

## Overview
The `A9_LLM_Service_Agent` is the shared LLM gateway for Agent9. It standardizes all large-language-model operations, enforces guardrails, applies prompt templates, and abstracts provider-specific APIs (OpenAI, Anthropic). All other agents must route LLM interactions through this agent to guarantee policy compliance, logging, and consistent model selection.

## Protocol Entrypoints
- `generate(request: A9_LLM_Request) -> A9_LLM_Response`
- `generate_template(request: A9_LLM_TemplateRequest) -> A9_LLM_Response`
- `analyze(request: A9_LLM_AnalysisRequest) -> A9_LLM_AnalysisResponse`
- `summarize(request: A9_LLM_SummaryRequest) -> A9_LLM_SummaryResponse`
- `evaluate(request: A9_LLM_EvaluationRequest) -> A9_LLM_EvaluationResponse`
- `generate_sql(request: A9_LLM_SQLGenerationRequest) -> A9_LLM_SQLGenerationResponse`

(Protocols defined in `src/agents/models` alongside their request/response Pydantic models.)

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

## Recent Updates (Jan 2026)
- Introduced provider-agnostic service with guardrail/template loading.
- Added task-type based model routing for OpenAI.
- Exposed unified SQL generation interface for downstream agents (Situation Awareness, Data Product, Solution Finder).

## Dependencies
- `src/llm_services/openai_service.py`
- `src/llm_services/claude_service.py`
- Guardrails file: `docs/cascade_guardrails.yaml`
- Prompt templates: `docs/cascade_prompt_templates.md`
