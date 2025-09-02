---
configuration:
  name: A9_Solution_Finder_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Solution_Finder_Agent
- **Team / Agent Context Tags:** solution_team, solution_finder
- **Purpose:** Generates, evaluates, and recommends optimal solutions to identified business problems leveraging multi-context analysis.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9SolutionFinderAgentConfig(BaseModel):
    max_solution_options: int = 3
    enable_risk_assessment: bool = True
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `generate_solutions` | Generate solution options | `SolutionGenerationRequest` | `SolutionOptions` | logs events |
| `evaluate_solutions` | Evaluate & score options | `SolutionEvaluationRequest` | `SolutionScores` | logs events |
| `recommend_solution` | Recommend best solution | `SolutionRecommendationRequest` | `SolutionRecommendation` | logs events |

Supported hand-off commands / state updates:
- `handoff_to_risk_management` – send selected solution for risk evaluation

## 4. Compliance, Testing & KPIs
- **Design-Standards Checklist**
  - Naming follows `A9_*`
  - File size < 300 lines
  - No hard-coded secrets
  - Tests reference Agent9 standards
- **Unit / Integration Test Targets**
  - Unit coverage ≥ 90%
  - End-to-end solution workflow test present
- **Runtime KPIs & Monitoring Hooks**
  - Solution generation latency < 1 s
  - Recommendation acceptance rate ≥ 80 %

---

# Situation Context Handoff
- This agent supports the `situation_context` field (type: `A9_Situation_Context`) for unified handoff of problems or opportunities, ensuring protocol compliance and downstream context continuity.

You are an Agent9 Solution Finder Agent. Your task is to generate and evaluate solutions to the following business problem, leveraging the detailed analysis provided.

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
- Deep Analysis Output:
"""
[PASTE OUTPUT FROM DEEP ANALYSIS AGENT HERE]
"""
- Organizational constraints: [LIST ANY CONSTRAINTS, e.g., budget, timeline, compliance]
- Relevant past solutions: [OPTIONAL: INSERT LIST/EXAMPLES]

Business Problem:
"""
[INSERT PROBLEM DESCRIPTION HERE]
"""

Instructions:
- Use the insights from Deep Analysis and all provided contexts to propose 2–3 distinct solution options.
- For each solution, provide:
  - A brief description
  - Key benefits and potential risks
  - Estimated impact (qualitative or quantitative)
- Recommend the best solution and justify your choice.

Respond in the following format:
1. **Solution Options:**  
   - Option 1: [Description, Benefits, Risks, Impact]  
   - Option 2: [Description, Benefits, Risks, Impact]  
   - Option 3: [Description, Benefits, Risks, Impact]  
2. **Recommendation:**  
   - [State the recommended option and justification]

fig: {}
error_handling: Standard error handling via AgentExecutionError and AgentInitializationError.
example_usage: |
  from src.agents.new.A9_Solution_Finder_Agent import A9_Solution_Finder_Agent
  config = {"name": "A9_Solution_Finder_Agent", "version": "1.0", "capabilities": ["solution_identification"], "config": {}}
llm_settings:
  preferred_model: gpt-4
  temperature: 0.2
  max_tokens: 2048
discoverability:
  registry_compliant: true
  a2a_ready: true
  tags:
    - solution
    - finder
    - a2a_protocol
---
