---
configuration:
  name: A9_Implementation_Planning_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Implementation_Planning_Agent
- **Team / Agent Context Tags:** solution_architect, implementation_planning
- **Purpose:** Generates comprehensive multi-phase implementation plans with resource allocation, timelines, and risk mitigation.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9ImplementationPlanningAgentConfig(BaseModel):
    """Configuration parameters for A9_Implementation_Planning_Agent."""
    # enable_hitl: bool = False  # Require human approval gate
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `plan_implementation` | Produce implementation plan | `A9_Implementation_Planning_Input` | `A9_Implementation_Planning_Output` | logs events |

Supported hand-off commands / state updates:
- `schedule_milestone_review` – schedules review meeting after plan generation

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
version: "1.0"
description: |
  Provides comprehensive planning for solution implementation, including resource allocation, timeline management, risk assessment, and monitoring.
team: solution_architect
agent_context: implementation_planning
capabilities:
  - multi_phase_planning
  - resource_allocation
  - timeline_management
  - risk_assessment
  - monitoring_setup
input_model: A9_Implementation_Planning_Input
output_model: A9_Implementation_Planning_Output
configuration:
  - name: A9_Implementation_Planning_Agent
    version: "1.0"
    capabilities:
      - multi_phase_planning
      - resource_allocation
      - timeline_management
      - risk_assessment
      - monitoring_setup
    config: {}
    hitl_enabled: false  # Can be enabled for protocol compliance
error_handling: Standard error handling via AgentExecutionError and AgentInitializationError.
example_usage: |
  from src.agents.new.A9_Implementation_Planning_Agent import A9_Implementation_Planning_Agent
  from src.agents.new.agent_config_models import A9ImplementationPlanningAgentConfig
  config = {
      "name": "A9_Implementation_Planning_Agent",
      "version": "1.0",
      "capabilities": ["multi_phase_planning", "resource_allocation"],
      "config": {},
      "hitl_enabled": False
  }
  agent = A9_Implementation_Planning_Agent(config)
  # Use agent.plan_implementation(...)

---

## Prompt Templates

"**Implementation Planning Agent (LLM-enabled, HITL-compliant):**"

```
You are an Agent9 Implementation Planning Agent. Your task is to provide comprehensive, actionable implementation plans for solutions, including resource allocation, timeline management, risk assessment, and monitoring setup.

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
- Solution Requirements:
"""
[PASTE SOLUTION REQUIREMENTS HERE]
"""
- Constraints and Risks:
"""
[PASTE KNOWN CONSTRAINTS, RISKS, AND DEPENDENCIES HERE]
"""

Instructions:
- Propose a multi-phase implementation plan, including phase definitions, dependencies, and milestones.
- Allocate human, technical, and infrastructure resources to each phase.
- Estimate durations and identify the critical path.
- Identify risks and propose mitigation and contingency plans.
- Specify monitoring and reporting requirements for the implementation.
- Structure your output as a JSON object with the following fields:
  - "phases": List of phases with name, description, dependencies, milestones, and resource assignments
  - "timeline": Estimated durations and critical path
  - "risks": List of identified risks and mitigation strategies
  - "monitoring": Monitoring and reporting requirements
  - "llm_derived": Boolean flag (true if any field is based on LLM output)
  - "human_action_required": Boolean (true if HITL approval is needed)
  - "human_action_type": String (e.g., "approval", "signoff", "escalation")
  - "human_action_context": Object (reason, affected stakeholders, etc.)
- Do not include any information outside the JSON object.

Respond ONLY with the JSON object as specified.
```
---
