---
configuration:
  name: A9_UI_Design_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_UI_Design_Agent
- **Team / Agent Context Tags:** solution_architect, ui_design
- **Purpose:** (DEPRECATED) Historically designed and optimized UIs; replaced by persona-based debate flows.
- **Owner:** <owner_or_squad>
- **Version:** 1.0
- **Deprecation:** 2025-05-13 – no further maintenance.

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9UIDesignAgentConfig(BaseModel):
    # No active config – agent deprecated
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `design_ui` | (Deprecated) Generate UI design recommendations | `A9_UI_Design_Input` | `A9_UI_Design_Output` | logs events |

## 4. Compliance, Testing & KPIs
- **Design-Standards Checklist**
  - Naming follows `A9_*`
  - File size < 300 lines
  - No hard-coded secrets
  - Tests reference Agent9 standards (deprecated status noted)
- **Runtime KPIs & Monitoring Hooks** – Not tracked (agent removed from prod)

---
> **DEPRECATION NOTICE (2025-05-13):**
> The UI Design Agent is deprecated and will no longer be maintained or used in Agent9. UI/UX expertise will be provided via Windsurf persona-based debate flows instead of this agent.
version: "1.0"
description: |
  Designs, reviews, and optimizes user interfaces for digital products, ensuring usability, accessibility, and alignment with business goals.
team: solution_architect
agent_context: ui_design
capabilities:
  - ui_design
  - usability_review
  - accessibility_analysis
  - design_optimization
input_model: A9_UI_Design_Input
output_model: A9_UI_Design_Output
configuration:
  - name: name
    version: "1.0"
    capabilities:
      - ui_design
      - usability_review
      - accessibility_analysis
      - design_optimization
    config: {}
error_handling: Standard error handling via AgentExecutionError and AgentInitializationError.
example_usage: |
  from src.agents.new.A9_UI_Design_Agent import A9_UI_Design_Agent
  config = {"name": "A9_UI_Design_Agent", "version": "1.0", "capabilities": ["ui_design"], "config": {}}
llm_settings:
  preferred_model: gpt-4
  temperature: 0.2
  max_tokens: 2048
discoverability:
  registry_compliant: true
  a2a_ready: true
  tags:
    - ui
    - design
    - a2a_protocol
---
