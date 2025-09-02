## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_LLM_Service_Agent
- **Team / Agent Context Tags:** platform_team, llm_service
- **Purpose:** Centralized gateway for all LLM operations, enforcing guardrails, prompt templates, and provider management.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9LLMServiceAgentConfig(BaseModel):
    provider: str = "anthropic"
    model_name: str = "claude-3-opus"
    guardrails_path: str | None = None
    prompt_templates_path: str | None = None
    api_key_env_var: str = "ANTHROPIC_API_KEY"
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** `${api_key_env_var}` env var with provider API key

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `generate` | Generate text from prompt | `A9_LLM_Request` | `A9_LLM_Response` | logs events |
| `generate_with_template` | Generate using prompt template | `A9_LLM_TemplateRequest` | `A9_LLM_Response` | logs events |
| `analyze` | Analyze text/data | `A9_LLM_AnalysisRequest` | `A9_LLM_AnalysisResponse` | logs events |
| `summarize` | Summarize content | `A9_LLM_SummaryRequest` | `A9_LLM_SummaryResponse` | logs events |
| `evaluate` | Evaluate options | `A9_LLM_EvaluationRequest` | `A9_LLM_EvaluationResponse` | logs events |

Supported hand-off commands / state updates:
- `reload_guardrails` – reload guardrails config

## 4. Compliance, Testing & KPIs
- **Design-Standards Checklist**
  - Naming follows `A9_*`
  - File size < 300 lines
  - No hard-coded secrets
  - Tests reference Agent9 standards
- **Unit / Integration Test Targets**
  - Unit coverage ≥ 90%
  - Integration workflow test present
- **Runtime KPIs & Monitoring Hooks**
  - Avg latency target < 1 s
  - Success-rate target ≥ 99 %
  - Cost per call tracked via `A9_CostTracker`

---

# A9_LLM_Service_Agent Card

## Agent Overview

The A9_LLM_Service_Agent is the centralized service for all LLM (Large Language Model) operations within Agent9-HERMES. It provides a standardized interface for LLM interactions, enforces guardrails, applies prompt templates, and manages provider connections.

## Protocol Entrypoints

| Method | Purpose | Input Model | Output Model |
|--------|---------|-------------|--------------|
| `async def generate(request)` | Generate text from LLM based on prompt | `A9_LLM_Request` | `A9_LLM_Response` |
| `async def generate_with_template(request)` | Generate text using a prompt template | `A9_LLM_TemplateRequest` | `A9_LLM_Response` |
| `async def analyze(request)` | Analyze text or data using LLM | `A9_LLM_AnalysisRequest` | `A9_LLM_AnalysisResponse` |
| `async def summarize(request)` | Create a summary of provided content | `A9_LLM_SummaryRequest` | `A9_LLM_SummaryResponse` |
| `async def evaluate(request)` | Evaluate or rank options using LLM | `A9_LLM_EvaluationRequest` | `A9_LLM_EvaluationResponse` |

## Configuration

This agent uses the `A9_LLM_Service_Agent_Config` model defined in `src/agents/agent_config_models.py`.

Key configuration options:
- `provider`: LLM provider to use (anthropic, openai)
- `model_name`: Default model to use for LLM requests
- `api_key_env_var`: Environment variable containing API key
- `guardrails_path`: Path to guardrails configuration
- `prompt_templates_path`: Path to prompt templates

## Dependencies

- **Environment Variables**: `ANTHROPIC_API_KEY` or specified provider API key variable
- **External Services**: Anthropic Claude API (primary), potentially others
- **Agent Dependencies**: Requires Orchestrator Agent for routing and logging

## Error Handling

| Error Type | Handling Strategy | Recovery |
|------------|-------------------|----------|
| API Connection | Retry with exponential backoff | Fall back to cached responses if available |
| Rate Limiting | Pause and retry with queue management | Prioritize critical requests |
| Invalid Input | Validate with Pydantic models before submission | Return structured error response |
| Context Length | Implement chunking and summarization | Truncate with warning in response |

## Human-in-the-Loop (HITL)

This agent does not require direct HITL interaction. All LLM operations are automated with guardrails enforcement.

## Compliance Status

- **Agent9 Design Standards**: ✅ Compliant
- **Protocol Compliance**: ✅ A2A protocol with Pydantic models
- **Registry Integration**: ✅ Orchestrator-controlled discovery and registration
- **Error Handling**: ✅ Structured logging with A9_SharedLogger
- **Documentation**: ✅ Complete with PRD alignment

## Change Log

| Date | Version | Changes |
|------|---------|---------|
| 2025-08-05 | 0.1.0 | Initial implementation with Claude integration |

## Notes

- All LLM operations must be routed through the Orchestrator for logging and compliance
- The agent supports centralized template management via prompt templates
- Guardrails enforcement is applied to all LLM interactions
