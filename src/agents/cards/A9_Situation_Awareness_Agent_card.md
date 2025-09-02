---
configuration:
  name: A9_Situation_Awareness_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Situation_Awareness_Agent
- **Team / Agent Context Tags:** situation_team, situation_awareness
- **Purpose:** Detects, contextualizes, and communicates situations (problems/opportunities) based on KPI monitoring, anomaly detection, and multi-agent outputs.
- **Owner:** <owner_or_squad>
- **Version:** 2.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9SituationAwarenessAgentConfig(BaseModel):
    notification_channels: list[str] = ["decision_studio", "gmail"]
    enable_anomaly_alerts: bool = True
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `detect_situation` | Detect situation from signals | `SituationDetectionRequest` | `DetectedSituation` | sends notifications |
| `summarize_situation` | Summarize situation for stakeholders | `SituationSummaryRequest` | `SituationSummary` | logs events |
| `aggregate_agent_outputs` | Combine outputs from specialized agents | `AggregationRequest` | `AggregatedInsight` | updates context |

Supported hand-off commands / state updates:
- `escalate_to_orchestrator` – escalate critical situations

## 4. Compliance, Testing & KPIs
- **Design-Standards Checklist**
  - Naming follows `A9_*`
  - File size < 300 lines
  - No hard-coded secrets
  - Tests reference Agent9 standards
- **Unit / Integration Test Targets**
  - Unit coverage ≥ 90%
  - Situation detection precision/recall test suite
- **Runtime KPIs & Monitoring Hooks**
  - Situation detection latency < 1 s
  - False-positive rate ≤ 5 %
  - Notification delivery SLA 99 %

---

# MVP Channels of Engagement
- Situation communications are delivered via Decision Studio UI (situation cards) and Gmail notifications only.
- Other channels (push, Slack, webhooks, etc.) are planned for future releases.

**Protocol Flexibility:**
This agent now accepts and emits flexible, untyped (dict, str, or JSON) fields for orchestration entrypoints, supporting both structured and unstructured data. Protocol is A2A compliant and no longer requires strict Pydantic models for input/output. See Orchestration Refactor Plan for migration details.

# Error Handling
Standard error handling via AgentExecutionError and AgentInitializationError.

# Example Usage
```python
from src.agents.new.A9_Situation_Awareness_Agent import A9_Situation_Awareness_Agent
config = {
    "name": "A9_Situation_Awareness_Agent",
    "version": "2.0",
    "capabilities": ["prompt_completion", "summarization", "analytics_query_parsing", "kpi_monitoring", "situation_detection", "anomaly_alerting", "structured_reporting", "aggregation_of_specialized_agent_outputs"],
    "config": {},
    "hitl_enabled": False
}
agent = A9_Situation_Awareness_Agent(config)
```

# LLM Settings
- preferred_model: gpt-4
- temperature: 0.2
- max_tokens: 2048

# Compliance & Discoverability
- registry_compliant: true
- a2a_ready: true
- tags: [situation, awareness, kpi_monitoring, anomaly_alerting, reporting, agent9, a2a_protocol]
- agent9_design_standards: true
- prd_reference: true

> This agent card is compliant with Agent9 Agent Design Standards and the MVP PRD. See docs/Agent9_Agent_Design_Standards.md and docs/prd/agents/clarity/a9_situation_awareness_agent_prd.md for boundaries and protocol details.

## Notes

- This agent expects principal, situation, and business context to be supplied per request (not in the card).
- LLM prompt/response/metadata fields are set at runtime only.
- Card and config are validated against the V2-compliant base model for protocol and automation compliance.
- See [Agent9_Agent_Design_Standards.md](../docs/Agent9_Agent_Design_Standards.md) for context model details and protocol compliance.
---
