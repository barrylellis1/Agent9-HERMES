---
configuration:
  name: A9_Opportunity_Analysis_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Opportunity_Analysis_Agent
- **Team / Agent Context Tags:** innovation, opportunity_analysis
- **Purpose:** Identifies, evaluates, and prioritizes opportunities across market, product, and optimization domains using structured analysis and scenario modeling.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9OpportunityAnalysisAgentConfig(BaseModel):
    enable_llm: bool = False
    scenario_model_limit: int = 10
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `identify_opportunities` | Detect potential opportunities | `A9_Opportunity_Analysis_Input` | `A9_Opportunity_List` | logs events |
| `evaluate_opportunity` | Evaluate single opportunity | `OpportunityEvaluationRequest` | `OpportunityEvaluation` | logs events |
| `prioritize` | Rank opportunities | `OpportunityPrioritizationRequest` | `OpportunityPrioritization` | logs events |

Supported hand-off commands / state updates:
- `notify_risk_team` – escalate to Risk Analysis Agent if high risk detected

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
description: |
  Identifies, evaluates, and prioritizes innovation, market, and optimization opportunities using structured analysis and scenario modeling.
team: innovation
agent_context: opportunity_analysis
capabilities:
  - opportunity_identification
  - opportunity_evaluation
  - prioritization
  - scenario_modeling
input_model: A9_Opportunity_Analysis_Input
output_model: A9_Opportunity_Analysis_Output
configuration:
  - name: A9_Opportunity_Analysis_Agent
    version: "1.0"
    capabilities:
      - opportunity_identification
      - opportunity_evaluation
      - prioritization
      - scenario_modeling
    config: {}
    hitl_enabled: false  # For protocol compliance; see config model/PRD for rationale
error_handling: Standard error handling via AgentExecutionError and AgentInitializationError.
example_usage: |
  from src.agents.new.A9_Opportunity_Analysis_Agent import A9_Opportunity_Analysis_Agent
  from src.agents.new.agent_config_models import A9OpportunityAnalysisAgentConfig
  config = A9OpportunityAnalysisAgentConfig(
      name="A9_Opportunity_Analysis_Agent",
      version="1.0",
      capabilities=[
      "name": "A9_Opportunity_Analysis_Agent",
      "version": "1.0",
      "capabilities": [
          "opportunity_identification",
          "risk_assessment",
          "value_estimation"
      ],
      "config": {},
      "hitl_enabled": False
  }
  agent = A9_Opportunity_Analysis_Agent(config)
  # Logging is structured and handled via A9_SharedLogger
  # Registration is orchestrator-controlled; do not instantiate directly except via orchestrator
llm_settings:
  preferred_model: gpt-4
  temperature: 0.2
  max_tokens: 2048
discoverability:
  registry_compliant: true
  a2a_ready: true
  tags:
    - opportunity
    - analysis
    - a2a_protocol
---
