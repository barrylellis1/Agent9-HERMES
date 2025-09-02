---
configuration:
  name: A9_Market_Research_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Market_Research_Agent
- **Team / Agent Context Tags:** market_research, market_research
- **Purpose:** Conducts comprehensive market research, trend analysis, and competitive intelligence to inform strategy and innovation.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9MarketResearchAgentConfig(BaseModel):
    use_llm: bool = False
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `research_market` | Perform market research | `A9MarketResearchInput` | `A9MarketResearchOutput` | logs events |
| `generate_report` | Produce research report | `ReportRequest` | `MarketReport` | logs events |

Supported hand-off commands / state updates:
- `flag_opportunity` – notify Opportunity Analysis Agent when opportunity detected

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

# A9_Market_Research_Agent Card

## Agent Overview
- **Team:** Market
- **Purpose:** Provides market research, trend analysis, and competitive intelligence for business strategy and innovation.
- **Version:** 1.0
- **A2A Protocol:** Strictly enforced (Pydantic models for all input/output)
- **Registry Integration:** Yes (orchestrator-controlled)
- **Logging:** Uses A9_SharedLogger; logs are propagated to Orchestrator Agent

# Situation Context Handoff
- This agent supports the `situation_context` field (type: `A9_Situation_Context`) in its input model for unified handoff of problems or opportunities, ensuring protocol compliance and downstream context continuity.

## Configuration
- **Config Model:** `A9MarketResearchAgentConfig`
- **Fields:**
    - `name` (str)
    - `version` (str)
    - `capabilities` (List[str])
    - `config` (Dict[str, Any])
    - `hitl_enabled` (bool, default: False)
- **Input Model:** `A9MarketResearchInput` (includes `situation_context: Optional[A9_Situation_Context]` for unified problem/opportunity handoff)
- **HITL Enablement:**
    - **NOT required for this agent.**
    - The `hitl_enabled` field is included for protocol consistency only. It should remain False in all environments (DEV/QA/Prod).
    - Rationale: Market Research Agent's workflows are highly technical, automated, and not suitable for human-in-the-loop intervention. See PRD for details.

## Key Behaviors
- Accepts only orchestrator-controlled registration (no self-registration)
- All LLM integration is routed through A9_LLM_Service and Orchestrator Agent
- All input/output is validated using strict Pydantic models
- No legacy or duplicate registration logic

## Compliance
- Follows Agent9 standards for config, logging, and registry
- No HITL or prompt review workflows are implemented or supported
- All code and documentation reflect this rationale

## References
- See PRD and BACKLOG_REFOCUS.md for rationale and compliance notes
- See `A9MarketResearchAgentConfig` in `agent_config_models.py` for config details

---

## Prompt Templates

"**Market Research Agent (leveraging Situation Awareness context):**"

```
You are an Agent9 Market Research Agent. Your task is to perform comprehensive, multi-perspective market research and analysis using advanced business intelligence methods.

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
- Situation Context (problem/opportunity context):
"""
[PASTE SITUATION CONTEXT HERE]
"""
```
---
