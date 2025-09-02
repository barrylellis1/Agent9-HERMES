---
configuration:
  name: A9_Change_Management_Agent
  version: '1.0'
  capabilities:
  - change_initiative_tracking
  - stakeholder_impact_analysis
  - communication_management
  - change_plan_generation
  - risk_assessment
  - value_realization_tracking
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Change_Management_Agent
- **Team / Agent Context Tags:** solution_architect, change_management
- **Purpose:** Tracks change initiatives, assesses impacts, and generates communication & risk plans.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9ChangeManagementAgentConfig(BaseModel):
    """Configuration parameters for A9_Change_Management_Agent."""
    # communication_channel: str = "email"  # Default comms channel
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `analyze_change` | Main change analysis | `A9_Change_Management_Input` | `A9_Change_Management_Output` | logs events |
| `process_change_request_event` | Handles new change request event | `ChangeRequestCreatedEvent` | None | updates registry |

Supported hand-off commands / state updates:
- `launch_risk_assessment` – delegates to Risk Analysis Agent

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

# Protocol Entrypoints
- **analyze_change**: (input: `A9_Change_Management_Input`, output: `A9_Change_Management_Output`, async: false)
- **process_change_request_event**: (input: `ChangeRequestCreatedEvent`, output: None, async: false)

# Error Handling
Standard error handling via `AgentExecutionError` and `AgentInitializationError`. Logging via `A9_SharedLogger`. Registration is orchestrator-controlled.

# LLM Settings
- preferred_model: gpt-4
- temperature: 0.2
- max_tokens: 2048

# Discoverability
- registry_compliant: true
- a2a_ready: true
- tags: [change, management, a2a_protocol]

# Compliance
- a2a_protocol: true
- logging: true
- registration: orchestrator/AgentRegistry only
- hitl_field: present (protocol-compliant; triggers approval protocol when True)
- card_config_code_sync: true
- last_sync: 2025-05-28

# Test Coverage
All protocol entrypoints are covered by orchestrator-driven, model-based tests in `tests/agents/new/test_a9_change_management_agent.py`. Logging, error handling, HITL, and protocol compliance are tested. No legacy or dict-based tests remain. Inputs/outputs are strictly Pydantic models.

# Example Usage
```python
from src.agents.new.A9_Change_Management_Agent import A9_Change_Management_Agent
from src.agents.new.agent_config_models import A9ChangeManagementAgentConfig
config = {
    "name": "A9_Change_Management_Agent",
    "version": "1.0",
    "capabilities": [
        "change_initiative_tracking",
        "stakeholder_impact_analysis",
        "communication_management",
        "change_plan_generation",
        "risk_assessment",
        "value_realization_tracking"
    ],
    "config": {},
    "hitl_enabled": False
}
agent = A9_Change_Management_Agent(config)
# Logging is structured and handled via A9_SharedLogger
# Registration is orchestrator-controlled; do not instantiate directly except via orchestrator
```

protocol_entrypoints:
  - name: analyze_change
    input_model: A9_Change_Management_Input (Pydantic)
    output_model: A9_Change_Management_Output (Pydantic)
    async: false
  - name: process_change_request_event
    input_model: ChangeRequestCreatedEvent (Pydantic)
    output_model: None
    async: false
error_handling: |
  Standard error handling via AgentExecutionError and AgentInitializationError. Logging via A9_SharedLogger, registration is orchestrator-controlled.
llm_settings:
  preferred_model: gpt-4
  temperature: 0.2
  max_tokens: 2048
discoverability:
  registry_compliant: true
  a2a_ready: true
  tags:
    - change
    - management
    - a2a_protocol
compliance:
  a2a_protocol: true
  logging: true
  registration: orchestrator/AgentRegistry only
  hitl_field: present (protocol-compliant; triggers approval protocol when True)
  card_config_code_sync: true
  last_sync: 2025-05-28
test_coverage: |
  All protocol entrypoints are covered by orchestrator-driven, model-based tests in tests/agents/new/test_a9_change_management_agent.py. Logging, error handling, HITL, and protocol compliance are tested. No legacy or dict-based tests remain. Inputs/outputs are strictly Pydantic models.
example_usage: |
  from src.agents.new.A9_Change_Management_Agent import A9_Change_Management_Agent
  from src.agents.new.agent_config_models import A9ChangeManagementAgentConfig
  config = {
      "name": "A9_Change_Management_Agent",
      "version": "1.0",
      "capabilities": [
          "change_initiative_tracking",
          "stakeholder_impact_analysis",
          "communication_management",
          "change_plan_generation",
          "risk_assessment",
          "value_realization_tracking"
      ],
      "config": {},
      "hitl_enabled": False
  }
  agent = A9_Change_Management_Agent(config)
  # Logging is structured and handled via A9_SharedLogger
  # Registration is orchestrator-controlled; do not instantiate directly except via orchestrator
---
