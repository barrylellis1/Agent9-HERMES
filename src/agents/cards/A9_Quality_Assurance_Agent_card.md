---
configuration:
  name: A9_Quality_Assurance_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Quality_Assurance_Agent
- **Team / Agent Context Tags:** qa_team, quality_assurance
- **Purpose:** Ensures software and process quality via automated testing, metrics tracking, and compliance validation across all agents and workflows.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9QualityAssuranceAgentConfig(BaseModel):
    enable_llm_review: bool = False
    test_coverage_target: float = 0.9
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `generate_test_cases` | Generate test cases | `TestCaseGenerationRequest` | `TestCaseGenerationResponse` | logs events |
| `validate_output` | Validate agent output | `ValidationRequest` | `ValidationResult` | logs events |
| `track_defects` | Record defects & metrics | `DefectReport` | `DefectTrackingAck` | updates metrics store |

Supported hand-off commands / state updates:
- `raise_blocker` – escalate critical defect to Orchestrator

## 4. Compliance, Testing & KPIs
- **Design-Standards Checklist**
  - Naming follows `A9_*`
  - File size < 300 lines
  - No hard-coded secrets
  - Tests reference Agent9 standards
- **Unit / Integration Test Targets**
  - Unit coverage ≥ 90%
  - End-to-end quality gate enforced
- **Runtime KPIs & Monitoring Hooks**
  - Defect leakage rate ≤ 1 %
  - Automated test pass-rate ≥ 98 %
  - Validation latency < 1 s

---
description: |
  Ensures software and process quality through automated test case management, metrics tracking, and compliance validation. Integrates with other agents for continuous quality improvement.
team: solution_architect
agent_context: quality_assurance
capabilities:
  - quality_standards_definition
  - test_case_generation
  - validation
  - defect_tracking
input_model: A9_Quality_Assurance_Input
output_model: A9_Quality_Assurance_Output
configuration:
  - name: A9_Quality_Assurance_Agent
    version: "1.0"
    capabilities:
      - quality_standards_definition
      - test_case_generation
      - validation
      - defect_tracking
    config: {}
    hitl_enabled: false  # For protocol compliance; see config model/PRD for rationale
    logging: A9_SharedLogger
    registry: Async registration pattern
    note: Logging via A9_SharedLogger, registration is orchestrator-controlled
error_handling: Standard error handling via AgentExecutionError and AgentInitializationError.
example_usage: |
  from src.agents.new.A9_Quality_Assurance_Agent import A9_Quality_Assurance_Agent
  from src.agents.new.agent_config_models import A9QualityAssuranceAgentConfig
  config = {
      "name": "A9_Quality_Assurance_Agent",
      "version": "1.0",
      "capabilities": [
          "quality_standards_definition",
          "test_case_generation",
          "validation",
          "defect_tracking"
      ],
      "config": {},
      "hitl_enabled": False
  }
  agent = A9_Quality_Assurance_Agent(config)
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
    - quality
    - assurance
    - a2a_protocol
---
