---
configuration:
  name: A9_Stakeholder_Engagement_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Stakeholder_Engagement_Agent
- **Team / Agent Context Tags:** stakeholder_team, stakeholder_engagement
- **Purpose:** Manages stakeholder engagement activities, communications, and feedback loops to drive buy-in and collaboration.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9StakeholderEngagementAgentConfig(BaseModel):
    enable_hitl: bool = True  # Require human approval before sending communications
    default_channel: str = "email"
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `track_engagement` | Track engagement interactions | `EngagementTrackingRequest` | `EngagementTrackingAck` | logs events |
| `manage_communication` | Create communication messages | `CommunicationRequest` | `DraftCommunications` | triggers HITL |
| `collect_feedback` | Collect and analyze feedback | `FeedbackCollectionRequest` | `FeedbackAnalysis` | logs events |

Supported hand-off commands / state updates:
- `submit_for_hitl_approval` – escalate drafted messages for human approval

## 4. Compliance, Testing & KPIs
- **Design-Standards Checklist**
  - Naming follows `A9_*`
  - File size < 300 lines
  - No hard-coded secrets
  - Tests reference Agent9 standards
- **Unit / Integration Test Targets**
  - Unit coverage ≥ 90%
  - HITL workflow integration test present
- **Runtime KPIs & Monitoring Hooks**
  - Engagement data update latency < 1 s
  - Communication approval turnaround < 24 h
  - Stakeholder satisfaction score ≥ 80 %

---
version: "1.0"
description: |
  Manages and tracks stakeholder engagement activities, communication, and feedback to ensure effective collaboration and buy-in.
team: innovation
agent_context: stakeholder_engagement
capabilities:
  - engagement_tracking
  - communication_management
  - feedback_collection
  - collaboration_support
input_model: A9_Stakeholder_Engagement_Input
output_model: A9_Stakeholder_Engagement_Output
configuration:
  - name: A9_Stakeholder_Engagement_Agent
    version: "1.0"
    capabilities:
      - engagement_tracking
      - communication_management
      - feedback_collection
      - collaboration_support
    config: {}
    hitl_enabled: false  # For protocol compliance; see config model/PRD for rationale
error_handling: Standard error handling via AgentExecutionError and AgentInitializationError.
example_usage: |
  # Orchestrator-controlled instantiation (Agent9 standard)
  from src.agents.new.A9_Stakeholder_Engagement_Agent import A9_Stakeholder_Engagement_Agent
  from src.agents.new.agent_registry import AgentRegistry

  config = {
      "name": "A9_Stakeholder_Engagement_Agent",
      "version": "1.0",
      "capabilities": [
          "engagement_tracking",
          "communication_management",
          "feedback_collection",
          "collaboration_support"
      ],
      "config": {},
      "hitl_enabled": False
  }
  registry = AgentRegistry()

  # Always instantiate via async factory for protocol compliance
  agent = await A9_Stakeholder_Engagement_Agent.create_from_registry(registry, config)

---

## Prompt Templates

"**Stakeholder Engagement Agent (LLM-enabled, HITL-compliant):**"

```
You are an Agent9 Stakeholder Engagement Agent. Your task is to manage and track stakeholder engagement activities, communication, and feedback to ensure effective collaboration and buy-in for organizational change.

Context:
- Principal Context (stakeholder, persona, or decision-maker perspective):
"""
[PASTE PRINCIPAL CONTEXT HERE]
"""
- Business Process Context (relevant business process, workflow, or objective):
"""
[PASTE BUSINESS PROCESS CONTEXT HERE]
"""
- Industry Context (industry, sector, or market segment details):
"""
[PASTE INDUSTRY CONTEXT HERE]
"""
- Engagement Data:
"""
[PASTE ENGAGEMENT PLANS, RELATIONSHIP DATA, COMMUNICATION RECORDS, METRICS HERE]
"""
- Management Parameters:
"""
[PASTE ENGAGEMENT GOALS, RELATIONSHIP PRIORITIES, COMMUNICATION PREFERENCES, TRACKING REQUIREMENTS HERE]
"""

Instructions:
- Summarize the current state of stakeholder engagement, highlighting strengths, risks, and opportunities.
- Suggest targeted engagement strategies and communication plans tailored to the provided contexts.
- Identify any gaps or potential resistance and recommend actions to address them.
- For each key stakeholder, draft individualized communication messages for HITL (Human-in-the-Loop) review and approval before sending.
- Structure your findings as a JSON object with the following fields:
  - "summary": Brief summary of engagement status
  - "strengths": List of current engagement strengths
  - "risks": List of risks or gaps
  - "opportunities": List of opportunities for improved engagement
  - "recommendations": List of actionable recommendations
  - "draft_communications": List of individualized draft messages (one per stakeholder)
  - "llm_derived": Boolean flag (true if any field is based on LLM output)
  - "human_action_required": Boolean (true if HITL approval is needed)
  - "human_action_type": String (e.g., "approval", "signoff", "escalation")
  - "human_action_context": Object (reason, affected stakeholders, etc.)
- Do not include any information outside the JSON object.

Respond ONLY with the JSON object as specified.
```
  agent = A9_Stakeholder_Engagement_Agent(config)
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
    - stakeholder
    - engagement
    - a2a_protocol
---
