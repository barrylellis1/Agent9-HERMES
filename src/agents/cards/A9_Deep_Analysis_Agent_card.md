---
configuration:
  name: A9_Deep_Analysis_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Deep_Analysis_Agent
- **Team / Agent Context Tags:** clarity, deep_analysis
- **Purpose:** Performs in-depth analytical processing of data, generating actionable insights and transparent recommendations.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9DeepAnalysisAgentConfig(BaseModel):
    """Configuration parameters for A9_Deep_Analysis_Agent."""
    # hitl_enabled: bool = True  # Human-in-the-loop review gate
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `analyze()` | Perform deep analysis | `A9_Deep_Analysis_Input` | `A9_Deep_Analysis_Output` | logs events |

Supported hand-off commands / state updates:
- `launch_solution_finder` – delegates to Solution Finder Agent after HITL approval

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

# A9_Deep_Analysis_Agent Card

## Agent Overview
- **Team:** Clarity
- **Purpose:** Performs deep analytical processing of structured data from databases and data warehouses, delivering actionable insights, recommendations, and transparent analysis for decision support.
- **Version:** 1.0
- **A2A Protocol:** Strictly enforced (Pydantic models for all input/output)
- **Registry Integration:** Yes (orchestrator-controlled)
- **Logging:** Uses A9_SharedLogger; logs are propagated to Orchestrator Agent

# Situation Context Handoff
- This agent supports the `situation_context` field (type: `A9_Situation_Context`) in its input model for unified handoff of problems or opportunities, ensuring protocol compliance and downstream context continuity.

## Configuration
- **Config Model:** `A9DeepAnalysisAgentConfig`
- **Fields:**
    - `name` (str)
    - `version` (str)
    - `capabilities` (List[str])
    - `config` (Dict[str, Any])
    - `hitl_enabled` (bool, default: True)
- **Input Model:** `A9_Deep_Analysis_Input` (includes `situation_context: Optional[A9_Situation_Context]` for unified problem/opportunity handoff)
- **HITL Enablement:**
    - **REQUIRED for this agent.**
    - The `hitl_enabled` field MUST be set to `true` in all environments (DEV/QA/Prod).
    - Rationale: After completing deep analysis, a human-in-the-loop (HITL) prompt is required to review the final problem statement or opportunity summary and launch the next workflow. This enables the principal or analyst to:
        - Confirm or refine the problem/opportunity summary.
        - Choose whether to launch the Solution Finder Agent for solution generation or initiate Opportunity Research.
        - Ensure that downstream actions are intentional and contextually appropriate.
    - This pattern supports protocol compliance, traceability, and principal oversight at critical workflow handoff points. See PRD for details.

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
- See `A9DeepAnalysisAgentConfig` in `agent_config_models.py` for config details

---
agent_name: A9_Deep_Analysis_Agent
hitl_enabled: true

## Prompt Templates

"**Deep Analysis Agent (leveraging Situation Awareness context):**"

```
You are an Agent9 Deep Analysis Agent. Your task is to perform a comprehensive, multi-perspective analysis using advanced business intelligence methods.

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
- Situation Awareness Context:
"""
[PASTE OUTPUT FROM SITUATION AWARENESS AGENT HERE]
"""
- Relevant KPIs: [LIST OR TABLE OF KPIS, IF AVAILABLE]
- Data snapshot: [OPTIONAL: INSERT DATA TABLE OR SUMMARY]

Business Question or Scenario:
"""
[INSERT QUESTION OR SCENARIO HERE]
"""

Instructions:
- Analyze the scenario leveraging all provided contexts, especially Situation Awareness.
- Examine from multiple perspectives (financial, operational, market, risk, etc.).
- Identify key drivers, trends, anomalies, risks, and opportunities.
- Summarize findings clearly.

Respond with:
- A summary paragraph
- Bullet points for each key insight
- (Optional) A markdown table of findings
```
---
