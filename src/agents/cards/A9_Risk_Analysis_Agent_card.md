---
configuration:
  name: A9_Risk_Analysis_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Risk_Analysis_Agent
- **Team / Agent Context Tags:** risk_team, risk_analysis
- **Purpose:** Performs comprehensive risk identification, evaluation, and mitigation recommendation across market, operational, and financial domains.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9RiskAnalysisAgentConfig(BaseModel):
    risk_threshold: float = 0.5  # Probability threshold for flagging high risk
    enable_llm_scenario: bool = False
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `analyze_risk` | Run risk analysis | `A9_Risk_Analysis_Input` | `A9_Risk_Analysis_Output` | logs + audit |
| `recommend_mitigation` | Suggest mitigation actions | `MitigationRequest` | `MitigationRecommendation` | logs events |

Supported hand-off commands / state updates:
- `escalate_to_risk_management` – send high risk event to Risk Management Agent

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
  - Risk analysis latency < 1 s
  - High-risk detection precision ≥ 95 %
  - False-negative rate ≤ 3 %

---
description: |
  Performs risk analysis on market, operational, and financial domains. Adheres to A2A protocol, provides audit logging, and integrates with Situation Awareness and Data Governance agents for compliance and transparency.
team: solution_architect
agent_context: risk_analysis
capabilities:
  - risk_identification
  - risk_evaluation
  - risk_prioritization
  - mitigation_recommendation
input_model: A9_Risk_Analysis_Input
output_model: A9_Risk_Analysis_Output
configuration:
  - name: A9_Risk_Analysis_Agent
    version: "1.0"
    capabilities:
      - risk_identification
      - risk_assessment
      - mitigation_planning
      - mitigation_recommendation
    config: {}
    hitl_enabled: false  # For protocol compliance; see config model/PRD for rationale (HITL is not implemented for this agent)

error_handling: Standard error handling via AgentExecutionError and AgentInitializationError.
example_usage: |
  from src.agents.new.A9_Risk_Analysis_Agent import A9_Risk_Analysis_Agent
  from src.agents.new.agent_config_models import A9RiskAnalysisAgentConfig
  config = {
      "name": "A9_Risk_Analysis_Agent",
      "version": "1.0",
      "capabilities": [
          "risk_identification",
          "risk_assessment",
          "mitigation_planning",
          "mitigation_recommendation"
      ],
      "config": {},
      "hitl_enabled": False
  }
  agent = A9_Risk_Analysis_Agent(config)
  # Logging is structured and handled via A9_SharedLogger
llm_settings:
  preferred_model: gpt-4
  temperature: 0.2
  max_tokens: 2048
discoverability:
  registry_compliant: true
  a2a_ready: true
  tags:
    - risk
    - analysis
    - a2a_protocol
---
