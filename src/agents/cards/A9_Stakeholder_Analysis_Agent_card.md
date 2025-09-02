---
configuration:
  name: A9_Stakeholder_Analysis_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Stakeholder_Analysis_Agent
- **Team / Agent Context Tags:** stakeholder_team, stakeholder_analysis
- **Purpose:** Identifies stakeholders, maps influence, and advises on engagement strategies for initiatives.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9StakeholderAnalysisAgentConfig(BaseModel):
    influence_threshold: float = 0.6
    enable_risk_flagging: bool = True
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `analyze` | Perform stakeholder analysis | `A9_Stakeholder_Analysis_Input` | `A9_Stakeholder_Analysis_Output` | logs events |
| `_analyze_stakeholder_type` | Analyze stakeholders of a type | `StakeholderTypeRequest` | `StakeholderAnalysisResult` | logs events |

Supported hand-off commands / state updates:
- `request_engagement_plan` – handoff to Stakeholder Engagement Agent

## 4. Compliance, Testing & KPIs
- **Design-Standards Checklist**
  - Naming follows `A9_*`
  - File size < 300 lines
  - No hard-coded secrets
  - Tests reference Agent9 standards
- **Unit / Integration Test Targets**
  - Unit coverage ≥ 90%
  - Stakeholder analysis accuracy tests present
- **Runtime KPIs & Monitoring Hooks**
  - Analysis latency < 1 s
  - Influence mapping precision ≥ 90 %

---
version: "1.0"
description: |
  Identifies, analyzes, and manages stakeholder relationships, influence, and engagement strategies for projects and initiatives.

### Situation Context Handoff
- **Field:** `situation_context: Optional[A9_Situation_Context]`
- **Purpose:** Enables seamless, protocol-compliant handoff of structured problem/opportunity context from upstream agents or orchestrator.
- **Optionality:** This field is optional. It is included when the analysis is triggered as part of a larger workflow or by another agent, but may be omitted for principal-driven, ad hoc stakeholder analysis requests.
- **Protocol Compliance:** Fully aligns with Agent9 Agent Design Standards for context continuity and multi-agent workflows.

team: innovation
agent_context: stakeholder_analysis
capabilities:
  - stakeholder_identification
  - influence_mapping
  - engagement_analysis
  - risk_assessment
input_model: A9_Stakeholder_Analysis_Input (with optional situation_context for protocol compliance)
output_model: A9_Stakeholder_Analysis_Output
configuration:
  - name: name
    type: str
    description: Agent name
  - name: version
    type: str
    description: Agent version
  - name: capabilities
    type: List[str]
    description: List of enabled capabilities
  - name: config
    type: dict
    description: Additional config options
  - name: hitl_enabled
    type: bool
    description: Human-in-the-loop enablement (always False; present for protocol compliance)
config_model: A9_Stakeholder_Analysis_Config (Pydantic)
protocol_entrypoints:
  - name: analyze
    input_model: A9_Stakeholder_Analysis_Input (with optional situation_context for protocol compliance) (Pydantic)
    output_model: A9_Stakeholder_Analysis_Output (Pydantic)
    async: false
  - name: _analyze_customer_stakeholders
    input: customers (List[dict])
    output: StakeholderAnalysisResult (Pydantic)
    async: false
  - name: _analyze_employee_stakeholders
    input: employees (List[dict])
    output: StakeholderAnalysisResult (Pydantic)
    async: false
  - name: _analyze_stakeholder_type
    input: StakeholderType, data (List[dict])
    output: StakeholderAnalysisResult (Pydantic)
    async: false
error_handling: |
  Standard error handling using AgentExecutionError, AgentInitializationError, and ValueError for invalid input. Follows A9_Agent_Template patterns.
llm_settings:
  preferred_model: gpt-4
  temperature: 0.2
  max_tokens: 2048
discoverability:
  registry_compliant: true
  a2a_ready: true
  tags:
    - stakeholder
    - analysis
    - a2a_protocol
compliance:
  a2a_protocol: true
  logging: true
  registration: orchestrator/AgentRegistry only
  hitl_field: present (always False; not required for this agent)
  card_config_code_sync: true
  last_sync: 2025-05-28
test_coverage: |
  All protocol entrypoints are covered by orchestrator-driven, model-based tests in tests/agents/new/test_stakeholder_analysis_agent.py. Logging/event emission is tested. No legacy or dict-based tests remain. Inputs/outputs are strictly Pydantic models.
example_usage: |
  from src.agents.new.A9_Stakeholder_Analysis_Agent import A9_Stakeholder_Analysis_Agent
  config = {"name": "A9_Stakeholder_Analysis_Agent", "version": "1.0", "capabilities": ["stakeholder_identification"], "config": {}, "hitl_enabled": False}
  agent = A9_Stakeholder_Analysis_Agent(config)
  # Recommended: use orchestrator/AgentRegistry for instantiation
---
