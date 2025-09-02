---
configuration:
  name: A9_Data_Governance_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Data_Governance_Agent
- **Team / Agent Context Tags:** solution_architect, data_governance
- **Purpose:** Enforces data governance rules, validates KPIs and data sources, and resolves data asset paths.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9DataGovernanceAgentConfig(BaseModel):
    """Configuration parameters for A9_Data_Governance_Agent."""
    # validation_mode: str = "strict"  # strict or lenient mode
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `get_data_asset_path` | Resolve asset path | `DataAssetPathRequest` | `DataAssetPathResponse` | logs events |
| `validate_kpi` | Validate KPI definition | `KPIDefinition` | `ValidationResult` | logs validation |

Supported hand-off commands / state updates:
- `refresh_governance_cache` – triggers background cache update

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

# Error Handling
Standard error handling via AgentExecutionError and AgentInitializationError.

# Example Usage
# Registration is orchestrator-controlled; do not instantiate directly except via orchestrator.
# All event logging must be async and awaited (A9_SharedLogger).
# YAML contract context is always propagated via the context kwarg.
```python
from src.agents.new.A9_Data_Governance_Agent import A9_Data_Governance_Agent
from src.agents.new.data_governance_models import DataAssetPathRequest
config = {
    "name": "A9_Data_Governance_Agent",
    "version": "1.0",
    "capabilities": [
        "kpi_validation",
        "data_source_validation",
        "term_translation",
        "data_asset_path_resolution"
    ],
    "config": {},
    "hitl_enabled": False
}
agent = A9_Data_Governance_Agent(config)
# Example: Dynamic asset path resolution
# To access the propagated YAML contract context in a protocol-compliant method:
# def some_method(self, input_model, context=None):
#     yaml_contract = context.get('yaml_contract_text') if context else None
request = DataAssetPathRequest(asset_name="example_asset")
response = await agent.get_data_asset_path(request)
print(response)
```

# LLM Settings
- preferred_model: gpt-4
- temperature: 0.2
- max_tokens: 2048

# Discoverability
- registry_compliant: true
- a2a_ready: true
- tags: [data, governance, a2a_protocol]
---
