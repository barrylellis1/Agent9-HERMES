---
configuration:
  name: A9_Risk_Management_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Risk_Management_Agent
- **Team / Agent Context Tags:** risk_team, risk_management
- **Purpose:** Manages mitigation, monitoring, and reporting of identified risks, ensuring compliance and proactive management across projects and operations.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9RiskManagementAgentConfig(BaseModel):
    enable_hitl: bool = False  # Toggle Human-in-the-Loop for compliance/audit
    reporting_interval_days: int = 30
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `mitigate_risk` | Create mitigation plan | `RiskMitigationRequest` | `MitigationPlan` | logs events |
| `monitor_risk` | Monitor ongoing risk | `RiskMonitoringRequest` | `RiskStatus` | triggers alerts |
| `report_risk` | Generate risk report | `RiskReportRequest` | `RiskReport` | logs events |

Supported hand-off commands / state updates:
- `request_hitl_approval` – escalate to HITL when high-impact risk requires human sign-off

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
  - Mitigation plan turnaround < 2 h
  - Risk report delivery SLA 100 % on schedule
  - HITL approval response time < 24 h

---
description: |
  Manages risk mitigation, monitoring, and reporting for projects and business operations, ensuring compliance and proactive management.
team: solution_architect
agent_context: risk_management
capabilities:
  - risk_mitigation
  - risk_monitoring
  - risk_reporting
  - compliance_management
input_model: A9_Risk_Management_Input
output_model: A9_Risk_Management_Output  # Includes HITL fields (human_action_required, human_action_type, human_action_context, human_action_result, human_action_timestamp)
configuration:
  - name: A9_Risk_Management_Agent
    version: "1.0"
    capabilities:
      - risk_management
      - mitigation_tracking
      - incident_response
    config: {}
    hitl_enabled: false  # For protocol compliance; see config model/PRD for rationale
  - name: compliance_management
    config: {}
    hitl_enabled: false  # Enables Human-in-the-Loop support for compliance/audit
error_handling: Standard error handling via AgentExecutionError and AgentInitializationError.
example_usage: |
  from src.agents.new.A9_Risk_Management_Agent import A9_Risk_Management_Agent
  from src.agents.new.agent_config_models import A9RiskManagementAgentConfig
  config = {
      "name": "A9_Risk_Management_Agent",
      "version": "1.0",
      "capabilities": [
          "risk_management",
          "mitigation_tracking",
          "incident_response"
      ],
      "config": {},
      "hitl_enabled": False
  }
  agent = A9_Risk_Management_Agent(config)
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
    - risk
    - management
    - a2a_protocol
    - hitl
compliance:
  - HITL (Human-in-the-Loop) support enables auditability and escalation for high-risk scenarios or when explicitly enabled in config.
---
