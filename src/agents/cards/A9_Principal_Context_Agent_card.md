---
agent_name: A9_Principal_Context_Agent
configuration:
  name: A9_Principal_Context_Agent
  version: '1.0'
  capabilities:
    - context_provisioning
    - role_identification
    - responsibility_mapping
  config:
    debug_card_source: 'CARD_TEST_20250707'
  hitl_enabled: false
  llm_settings:
    preferred_model: gpt-4
    temperature: 0.2
    max_tokens: 2048
  discoverability:
    registry_compliant: true
    a2a_ready: true
    tags: [principal, context, a2a_protocol]
    last_updated: "2024-12-10"
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Principal_Context_Agent
- **Team / Agent Context Tags:** principal_context_team, principal_context
- **Purpose:** Provides principal (stakeholder/persona) context and mappings for downstream agents, ensuring consistent perspective across workflows.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9PrincipalContextAgentConfig(BaseModel):
    debug_card_source: str | None = None
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `provide_context` | Return principal context | `PrincipalContextRequest` | `PrincipalContext` | logs events |
| `map_role` | Map principal to role/responsibility | `RoleMappingRequest` | `RoleMapping` | logs events |

Supported hand-off commands / state updates:
- `update_context` – update principal context cache

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
  - Context retrieval latency < 100 ms
  - Cache hit-rate ≥ 95 %

---

# A9_Principal_Context_Agent

## Error Handling
Standard error handling via `AgentExecutionError` and `AgentInitializationError`.

## Example Usage
Registration is orchestrator-controlled; do not instantiate directly except via orchestrator. All event logging must be async and awaited (`A9_SharedLogger`). YAML contract context is always propagated via the `context` kwarg.

```python
from src.agents.new.A9_Principal_Context_Agent import A9_Principal_Context_Agent
from src.agents.new.agent_config_models import A9PrincipalContextAgentConfig

# This is for illustrative purposes; in practice, the orchestrator builds the config from this card.
config_model = A9PrincipalContextAgentConfig(
    name="A9_Principal_Context_Agent",
    version="1.0",
    capabilities=[
        "context_provisioning",
        "role_identification",
        "responsibility_mapping"
    ],
    config={},
    hitl_enabled=False
)
# agent = A9_Principal_Context_Agent(config_model)
```
