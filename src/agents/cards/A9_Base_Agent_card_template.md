# Agent9 Standard Agent Card Template (V3)

configuration:
  name: <REQUIRED_AGENT_NAME>
  version: "<REQUIRED_VERSION>"
  capabilities:
    - <capability_1>
    - <capability_2>
  config: {}
  hitl_enabled: false

---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** <REQUIRED_AGENT_NAME>
- **Team / Agent Context Tags:** <team_context>, <agent_context>
- **Purpose:** <one-sentence purpose statement>
- **Owner:** <owner_or_squad>
- **Version:** <REQUIRED_VERSION>

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class <AgentConfigModel>(BaseModel):
    """Configuration parameters for <REQUIRED_AGENT_NAME>."""
    # <param_name>: <type> = <default>   # description
    # ...
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** <list_if_any>

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `run()` | Main execution method | `<InputModel>` | `<OutputModel>` | logs events |
| ... | | | | |

Supported hand-off commands / state updates:
- `<command>` – description

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

## Notes
- Context fields (`principal_context`, `situation_context`, `business_context`) supplied at runtime.
- LLM prompt/response/metadata fields are set at runtime only.
- Card and config validate against V3-compliant base model.
- See [Agent9_Agent_Design_Standards.md](../../docs/Agent9_Agent_Design_Standards.md) for protocol compliance details.

