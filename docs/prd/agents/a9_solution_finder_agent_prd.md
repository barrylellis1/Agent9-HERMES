# A9_Solution_Finder_Agent PRD

<!--
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2026-02-28
-->


> **2026-02-28 Phase 10 Update — Multi-Call LLM Architecture:**
> The Solution Finder Agent now uses a 4-call parallel architecture for the council debate:
> - **Stage 1 (parallel):** 3 independent LLM calls, one per consulting persona. Each produces a focused hypothesis + one proposed option with a quantified `impact_estimate`. Runs concurrently via `asyncio.gather`.
> - **Stage 2 (synthesis):** 1 synthesis LLM call receives all 3 Stage 1 proposals as `stage_1_persona_hypotheses`. Expands each into a full option with perspectives, prerequisites, and cross-review. No token budget shared with hypothesis generation.
> - `SolutionFinderResponse` now includes `stage_1_hypotheses` field (per-persona hypothesis objects from Stage 1).
> - `SolutionOption` now carries `impact_estimate` with `metric`, `unit`, `recovery_range: {low, high}`, `basis`.
> - Input data enriched with: `situation_metadata` (KPI unit, current/comparison values), `decision_maker` (name, role, priorities), `business_context` (multi-tenant, resolved via `data_product_id` lookup), IS-NOT data from DA (`where_is_not`, `what_is_not`, `when_is_not`).
> - `debate_stage` preference check skips Stage 1 for `cross_review`/`synthesis` frontend stages to prevent redundant calls.

> **2025-05-13 Update:**
> The A9_Solution_Finder_Agent is now fully refactored and compliant with Agent9 protocol and architectural standards. It uses a Pydantic config model, structured logging, orchestrator-driven registry integration (via `create_from_registry`), and protocol entrypoints with Pydantic models. HITL is supported for all actions. Card/config/code are now fully synchronized. Next steps: update/add tests, compliance, and monitoring as needed.


## Overview
**Purpose:** Systematically generate, evaluate, and recommend solutions to specific problems or diagnoses—especially those surfaced by the Deep Analysis Agent. This agent acts as a driver for problem-solving workflows, scenario evaluation, and decision support, with a human-in-the-loop and iterative refinement. Leverages the Unified Registry Access Layer for business processes, KPIs, and data products.



## Hackathon Quick Start

### Development Environment Setup
- Clone the Agent9-Hackathon-Template repository
- Install required dependencies from requirements.txt
- Configure environment variables in .env file based on .env.example

### Key Files and Entry Points
- Main agent implementation: `src/agents/new/A9_Solution_Finder_Agent_Agent.py`
- Configuration model: `src/agents/new/agent_config_models.py`
- Agent card: `src/agents/new/cards/a9_solution_finder_agent_agent_card.py`

### Test Data Location
- Sample data available in `test-data/` directory
- Test harnesses in `test-harnesses/` directory

### Integration Points
- Integrates with Agent Registry for orchestration
- Integrates with the Unified Registry Access Layer for business processes, KPIs, and data products
- Uses Registry Factory for provider initialization and configuration
- Follows A2A protocol for agent communication
- Uses shared logging utility for consistent error reporting

## Implementation Guidance

### Suggested Implementation Approach
1. Start with the agent's core functionality
2. Implement required protocol methods
3. Add registry integration
4. Implement error handling and logging
5. Add validation and testing

### Core Functionality to Focus On
- Protocol compliance (A2A)
- Registry integration
- Error handling and logging
- Proper model validation

### Testing Strategy
- Unit tests for core functionality
- Integration tests with mock registry
- End-to-end tests with test harnesses

### Common Pitfalls to Avoid
- Direct agent instantiation (use registry pattern)
- Missing error handling
- Incomplete logging
- Improper model validation
- Direct enum usage (use registry providers instead)
- Hardcoded business logic or KPI definitions (use registry data)
- Initializing registry providers directly (use Registry Factory)
- Bypassing the Unified Registry Access Layer
- Duplicating registry access logic
- Caching registry data locally instead of using the registry providers

## Success Criteria

### Minimum Viable Implementation
- Agent implements all required protocol methods
- Agent properly integrates with registry
- Agent handles errors and logs appropriately
- Agent validates inputs and outputs

### Stretch Goals
- Enhanced error handling and recovery
- Performance optimizations
- Additional features from Future Enhancements section

### Evaluation Metrics
- Protocol compliance
- Registry integration
- Error handling
- Logging quality
- Input/output validation

---

## LLM Integration Prioritization (2025-05-07)

Agent9 agents are prioritized for LLM integration as follows (see BACKLOG_REFOCUS.md for full table):

- **A9_Innovation_Agent:** Highest benefit from LLMs for idea generation, creative synthesis, and debate simulation.
- **A9_Solution_Finder_Agent:** Major benefit for generating solution options, trade-off analysis, and rationale writing.
- **A9_Deep_Analysis_Agent:** Major benefit for extracting insights, summarizing findings, and generating recommendations.
- **A9_Market_Research_Agent:** High benefit for synthesizing market trends and generating competitive intelligence.
- **A9_Stakeholder_Engagement/Analysis, A9_UI_Design_Agent:** Moderate benefit for summarization, engagement planning, and UI text/design suggestions.
- **Deterministic/Core Agents:** LLMs used only for explainability, not core logic (audit, compliance, access control, etc.).

**Reference:** See "Agents Prioritized for LLM Integration" in BACKLOG_REFOCUS.md for rationale and full table.

---
**Purpose:** Systematically generate, evaluate, and recommend solutions to specific problems or diagnoses—especially those surfaced by the Deep Analysis Agent. This agent acts as a driver for problem-solving workflows, scenario evaluation, and decision support, with a human-in-the-loop and iterative refinement. Utilizes the Unified Registry Access Layer to access business processes, KPIs, and data products for context-aware solution generation.
**Agent Type:** Core/Driver Agent
**Version:** 1.0

## MVP Functional Requirements

### Scientific Method, Evidence-Based Validation & Disciplined Reasoning (Updated 2025-05-06)
- The agent must follow a disciplined, unbiased process: hypothesis formation, evidence gathering, and validation before escalating to human input.
- All solution recommendations must be supported by internal or external evidence of effectiveness. If such evidence is lacking, the agent must propose a pilot/experiment and a plan for gathering validation data before adoption.
- LLMs are used to search, summarize, and present supporting evidence or to draft pilot protocols and study plans.
- Escalation to human (via NLP agent prompt or UI) only occurs when analytic/scientific methods are exhausted or when human wisdom, sensory ability, or creativity is likely to yield a breakthrough.
- If no proven or pilotable solutions are available, and human-in-the-loop brainstorming fails to produce actionable ideas, the Solution Finder Agent will escalate the problem to the A9_Innovation_Driver_Agent for creative, out-of-the-box ideation using innovation frameworks and LLM-supported approaches.
- All reasoning steps, failed attempts, escalation triggers, and innovation escalations must be logged for transparency and learning.

### Core Capabilities (MVP)
1. **Problem Intake**
   - Accepts a problem statement, diagnosis, or root cause (from Deep Analysis Agent or user)
   - Validates and structures the problem context using Pydantic models
   - Enriches problem context with relevant business processes, KPIs, and data products from the registry
   - Integrates directly with Deep Analysis Agent for seamless problem intake
   - Supports direct use of Deep Analysis Agent output (A9_Deep_Analysis_Output) as structured input, including insights and recommendations
   - Integrates directly with Market Analysis Agent for tailored market research and intelligence as structured input (A9_Market_Analysis_Output), including LLM-powered insights when available.
   - Market research can be requested and injected as structured Pydantic models into the solution finding process to enhance relevance and decision quality.
2. **Solution Generation**
   - Systematically generates multiple solution options/alternatives for the problem
   - Supports both automated and user-guided brainstorming
   - Allows user to supply constraints, preferences, and iterative feedback
   - Uses registry data to ensure solutions are relevant to business context and constraints
3. **Solution Evaluation**
    - Evaluates and ranks solutions based on criteria provided by Deep Analysis Agent or user (criteria are context-dependent)
    - Supports trade-off analysis and scenario comparison
    - Leverages registry data (KPIs, business processes) for evaluation criteria and impact assessment
    - Creates a trade-off matrix with a recommendation for conflicting objectives
    - **Generates a Trade-Off Analysis Deliverable:** For every major decision point (e.g., speed vs. rigor, cost vs. benefit), the agent produces a structured deliverable comparing all viable options. This includes: option descriptions, expected time to result, confidence level, risks, business impact, and required resources/cost. The deliverable is presented to the principal for review and decision, and all decisions/rationales are logged for audit and learning.
4. **Recommendation & Human-in-the-Loop**
   - Recommends the best solution(s) with supporting rationale and confidence score
   - Provides a clear, actionable summary for decision makers
   - Requires human review, feedback, and iterative solution refinement before finalizing recommendations
   - Supports user-guided cycles: each solution round must allow user feedback and resubmission, enabling iterative improvement until the user is satisfied
   - **Escalation to human (via NLP agent prompt or UI) is only triggered after all analytic/scientific methods are exhausted, in accordance with the scientific method requirement above.**
5. **Audit Logging**
   - Logs all problem statements, solution options, evaluation criteria, and recommendations
   - Logs all solution generation and evaluation steps in detail, including intermediate iterations, user feedback, and rationale for each decision
   - Logs all market research requests, responses, and usage in solution generation for auditability and compliance (including LLM-powered insights).
   - Supports exportable audit trails for compliance and review

### Input Requirements (MVP)
- Pydantic input model for problem statement/diagnosis and context
- Optional: user-supplied constraints, preferences, and feedback

### Output Specifications (MVP)
- Pydantic output model (`SolutionFinderResponse`) with:
  - `options_ranked`: Ranked solution options (list of `SolutionOption`)
  - `recommendation`: Recommended option
  - `recommendation_rationale`: Rationale string
  - `problem_reframe`: SCQA-style problem reframe (`situation`, `complication`, `question`, `key_assumptions`)
  - `tradeoff_matrix`: Criteria + options matrix
  - `unresolved_tensions`: Tensions requiring human judgment
  - `blind_spots`: Identified risk areas
  - `next_steps`: Actionable next steps
  - `cross_review`: Per-persona critiques and endorsements (dict keyed by persona_id)
  - `stage_1_hypotheses`: Per-persona Stage 1 hypothesis objects (dict keyed by persona_id) — *added Phase 10*
  - `framing_context`: Persona selection source, presentation note, disclaimer
  - `audit_log`: All events including Stage 1 call results
  - HITL fields: `human_action_required`, `human_action_type`, `human_action_context`
- Each `SolutionOption` includes:
  - `id`, `title`, `description`, `expected_impact`, `cost`, `risk` (0–1 normalized)
  - `impact_estimate`: `{metric, unit, recovery_range: {low, high}, basis}` — quantified KPI recovery estimate
  - `time_to_value`, `reversibility`, `perspectives`, `implementation_triggers`, `prerequisites`
  - **Trade-Off Analysis Deliverable:**
    - Structured comparison of options (table/matrix format)
    - Narrative summary of tradeoffs, pros/cons, and recommendations
    - Explicit prompt for human-in-the-loop decision
    - Captures principal's choice and rationale for audit
  - Audit log reference

---

### Human-in-the-Loop (HITL) Event Design

**Pattern:**
- Only **one HITL event is emitted per solution-finding cycle** (not per solution option).
- This event prompts the principal (human) to review all proposed solutions and either approve the agent's recommended solution or select a different option for downstream processing.
- The HITL event and context are included in the output model fields:
  - `human_action_required: bool`
  - `human_action_type: str` (e.g., "approval")
  - `human_action_context: dict` (includes summary of all options, agent recommendation, rationale, and any special instructions for the principal)
  - `human_action_result: Optional[str]` (principal's decision, set by orchestrator/UI)
  - `human_action_timestamp: Optional[str]`

**Workflow:**
1. Agent generates and ranks solution options, recommends one, and emits a single HITL event in the output.
2. Orchestrator/UI presents all options and the agent's recommendation to the principal.
3. Principal reviews, approves, or overrides the recommendation, and selects one solution to proceed.
4. Principal's decision is recorded in `human_action_result` and `human_action_timestamp`.
5. The approved solution is then passed to the next agent in the workflow.

**Rationale:**
- Simplifies workflow and user experience.
- Matches real-world decision-making (one principal approval per decision cycle).
- Ensures auditability: all HITL events, triggers, and outcomes are logged for compliance and review.
- Avoids unnecessary complexity and approval fatigue from per-option HITL events.

**Audit & Compliance:**
- All HITL triggers and actions are logged in the agent's audit log.
- HITL fields are surfaced to orchestrator/UI for workflow and compliance management.
- Ensures the agent meets regulatory and operational requirements for human oversight.

---

### Principal-Driven Solution Generation

**6. Decision Style to Consulting Persona Mapping**

The Solution Finder Agent uses the principal's `decision_style` to select appropriate consulting personas for the LLM council debate. This ensures solutions are framed in a way that resonates with the principal's decision-making approach.

#### Decision Style to Persona Mapping

| Decision Style | Primary Persona | Council Preset | Solution Focus |
|----------------|-----------------|----------------|----------------|
| `analytical` | McKinsey | mbb_council | Root cause fixes, MECE options, hypothesis validation |
| `visionary` | BCG | growth_council | Strategic pivots, portfolio rebalancing, value creation |
| `pragmatic` | Bain | cost_council | Quick wins, operational fixes, clear owners/timelines |
| `decisive` | McKinsey | mbb_council | Clear trade-offs, decision criteria, risk assessment |

#### Persona Selection Priority

1. **Request-level override**: `preferences.consulting_personas` or `preferences.council_preset`
2. **KPI lens_affinity**: Use KPI metadata to select personas (NEW - see below)
3. **Principal decision_style**: Maps to appropriate council via table above
4. **Principal role affinity**: Falls back to role-based persona mapping (CFO → analytical personas)
5. **Default**: MBB Council (McKinsey, BCG, Bain)

#### KPI Lens Affinity Integration (2026-01-22)

**Purpose:** When generating solutions for KPI-related situations, use the KPI's `metadata.lens_affinity` tag to select the most appropriate consulting personas for analysis.

**Integration Flow:**
```
Situation Awareness detects KPI anomaly
  ↓
Retrieves KPI definition from registry
  ↓
Extracts metadata.lens_affinity (e.g., "bcg,bain")
  ↓
Passes to Solution Finder as context
  ↓
Solution Finder selects personas based on lens_affinity
  ↓
Generates solutions using selected consulting frameworks
```

**Lens Affinity Values:**
- `bcg`: Portfolio view, growth-share matrix, value creation, strategic positioning
- `bain`: Operational excellence, quick wins, results-first, pragmatic implementation
- `mckinsey` or `mbb_council`: Root cause analysis, MECE frameworks, hypothesis-driven
- Combined: `"bcg,bain"` uses both personas in council debate

**Selection Logic:**
```python
def select_personas_for_kpi(kpi: KPI, principal_context: PrincipalContext) -> List[str]:
    # Priority 1: Request-level override
    if principal_context.preferences.consulting_personas:
        return principal_context.preferences.consulting_personas
    
    # Priority 2: KPI lens_affinity
    if kpi.metadata.get('lens_affinity'):
        personas = kpi.metadata['lens_affinity'].split(',')
        return [p.strip() for p in personas]
    
    # Priority 3: Principal decision_style
    return map_decision_style_to_personas(principal_context.decision_style)
```

**Example Scenarios:**

**Revenue Growth KPI:**
```yaml
kpi:
  id: total_revenue
  metadata:
    lens_affinity: bcg,mckinsey
```
→ Solution Finder uses BCG (growth strategy) + McKinsey (market analysis)

**Cost Reduction KPI:**
```yaml
kpi:
  id: operating_expenses
  metadata:
    lens_affinity: bain
```
→ Solution Finder uses Bain (operational excellence, quick wins)

**Efficiency KPI:**
```yaml
kpi:
  id: gross_margin
  metadata:
    lens_affinity: bain
```
→ Solution Finder uses Bain (process optimization)

**Strategic Risk KPI:**
```yaml
kpi:
  id: customer_churn_rate
  metadata:
    lens_affinity: mckinsey,bain
```
→ Solution Finder uses McKinsey (root cause) + Bain (retention tactics)

**API Integration:**

**Input Model Enhancement:**
```python
class SolutionFinderInput(BaseModel):
    situation: Situation
    principal_context: PrincipalContext
    kpi_context: Optional[KPIContext] = None  # NEW

class KPIContext(BaseModel):
    kpi_id: str
    kpi_name: str
    lens_affinity: Optional[str] = None
    profit_driver_type: Optional[str] = None
    altitude: Optional[str] = None
```

**Output Model Enhancement:**
```python
class SolutionFinderOutput(BaseModel):
    solutions: List[Solution]
    framing_context: FramingContext

class FramingContext(BaseModel):
    decision_style: str
    personas_used: List[str]
    persona_source: str  # "kpi_lens_affinity" | "decision_style" | "role_affinity" | "default"
    kpi_context: Optional[str] = None  # Explanation of KPI-driven persona selection
    presentation_note: str
    disclaimer: str
```

**Transparency Requirements:**

When using KPI lens_affinity, include in framing_context:
```json
{
  "framing_context": {
    "personas_used": ["bcg", "bain"],
    "persona_source": "kpi_lens_affinity",
    "kpi_context": "Selected BCG and Bain personas based on Total Revenue KPI's strategic growth and operational focus.",
    "presentation_note": "Solutions emphasize portfolio growth (BCG) and execution excellence (Bain) per KPI characteristics."
  }
}
```

---

### Guardrails: Personalization vs Attribution

**CRITICAL**: The Solution Finder generates solutions FOR the principal's consideration. It does NOT speak FOR the principal or impersonate colleagues.

#### Consulting Personas vs Colleague Personas

The LLM council uses **external consulting firm personas** (McKinsey, BCG, Bain), NOT internal colleague personas. This is intentional:

- ✅ "McKinsey perspective: Focus on root cause analysis..."
- ✅ "BCG perspective: Consider portfolio implications..."
- ❌ "The CFO would recommend..."
- ❌ "Based on the COO's pragmatic style, she believes..."

#### Prohibited Patterns

- ❌ "Your colleague [Name] would likely prefer..."
- ❌ "The [Role] believes this solution is best..."
- ❌ "Based on [Name]'s decision style, they would choose..."
- ❌ "Speaking on behalf of the executive team..."

#### Required Patterns

- ✅ "This solution aligns with your analytical decision style, emphasizing root cause resolution."
- ✅ "Presented with implementation timelines per your pragmatic preferences."
- ✅ "The McKinsey framework suggests... while the Bain perspective emphasizes..."
- ✅ "Trade-offs are presented for YOUR decision—the agent does not choose for you."

#### Transparency Requirements

All Solution Finder outputs MUST include:
```json
{
  "framing_context": {
    "decision_style": "analytical",
    "personas_used": ["mckinsey", "bcg", "bain"],
    "presentation_note": "Solutions presented with MECE structure and root cause focus per your analytical profile.",
    "disclaimer": "Consulting perspectives are analytical frameworks, not colleague opinions."
  }
}
```

#### Principal Control

- Principal can override persona selection per session
- Principal can request alternative framing (e.g., "Show me the pragmatic view")
- Principal can disable persona-based framing entirely
- All framing choices are logged for audit

---

---

## Multi-Call LLM Architecture (Phase 10 — 2026-02-28)

The single-call LLM bottleneck was replaced with a parallel 4-call architecture that solves the token budget problem (all personas + synthesis competing for output tokens in one call).

### Call Topology

```
recommend_actions()
  │
  ├── STAGE 1 (parallel, asyncio.gather)
  │     ├── LLM call: McKinsey hypothesis + proposed_option
  │     ├── LLM call: BCG hypothesis + proposed_option
  │     └── LLM call: Bain hypothesis + proposed_option
  │           ↓ (3 compact results collected as stage_1_hyps_dict)
  │
  └── STAGE 2 (synthesis)
        LLM call: receives stage_1_persona_hypotheses in data_payload
        → expands each into full option with perspectives + impact_estimate
        → generates cross_review (each firm critiques other firms' options)
        → outputs: problem_reframe, options[3], recommendation, tensions, blind_spots
```

### Stage 1 Per-Persona Prompt (compact)

Each Stage 1 call receives only:
- Own persona profile (`to_prompt_context()`)
- Problem statement
- Compact DA signals: `kpi_name`, `top_change_points[:3]`, `where_signals[:3]`, `where_is_not[:3]`
- Compact business context: `name`, `industry`, `operational_context`
- `situation_metadata`: severity, kpi_name, current_value, comparison_value, unit

Output per persona:
```json
{
  "persona_id": "mckinsey",
  "framework": "...",
  "hypothesis": "...",
  "key_evidence": ["...", "...", "..."],
  "recommended_focus": "...",
  "conviction": "High|Medium|Low",
  "proposed_option": {
    "title": "...",
    "description": "...",
    "mechanism": "...",
    "time_horizon": "0-90 days|3-12 months|12+ months",
    "impact_estimate": { "metric": "...", "unit": "...", "recovery_range": {"low": 0.0, "high": 0.0}, "basis": "..." },
    "cost_signal": "High|Medium|Low",
    "risk_signal": "High|Medium|Low"
  }
}
```

### Stage 2 Synthesis Prompt

Receives `stage_1_persona_hypotheses` in `data_payload`. Instruction: use each persona's `proposed_option` as the basis for one of 3 output options, then expand with full `perspectives`, `prerequisites`, `implementation_triggers`. Output schema includes `problem_reframe`, `options[3]`, `recommendation`, `recommendation_rationale`, `unresolved_tensions`, `blind_spots`, `next_steps`, `cross_review`. Stage 1 hypotheses are **excluded** from synthesis output schema to save output tokens.

### `debate_stage` Optimization

The React frontend calls the SF API 3 times (stages: `hypothesis`, `cross_review`, `synthesis`). To prevent running Stage 1 three times:
- If `prefs["debate_stage"] in ("cross_review", "synthesis")`: Stage 1 is skipped
- Stage 1 only runs on the `hypothesis` stage (first call) or when `debate_stage` is unset

### Enriched Input Data (`data_payload`)

| Key | Source | Purpose |
|-----|--------|---------|
| `problem_statement` | situation_context.description + DA | Authoritative KPI direction |
| `situation_metadata` | situation_context | KPI unit, current/comparison values, severity |
| `decision_maker` | principal_context | Name, role, decision_style, priorities |
| `business_context` | Resolved via `data_product_id` → YAML | Multi-tenant context (Summit Lubricants vs. Bicycle Retail) |
| `deep_analysis_context` | Trimmed DA output | Change points, KT Is/Is-Not |
| `deep_analysis_summary` | Extracted from DA | kpi_name, where_signals, where_is_not, what_is_not |
| `stage_1_persona_hypotheses` | Stage 1 results | 3 proposed options for synthesis to expand |

### Business Context Resolution (`_DP_CONTEXT_MAP`)

Business context is resolved by looking up the KPI's `data_product_id` in the KPI registry, then mapping to a context YAML file:
```python
_DP_CONTEXT_MAP: Dict[str, str] = {
    "dp_lubricants_financials": "lubricants_context.yaml",
    # default → bicycle_retail_context.yaml
}
```

---

## Technical Requirements
- Modular, maintainable architecture
- Registry integration and async operations
- Secure configuration and error handling
- Seamless integration with Deep Analysis Agent (accepts A9_Deep_Analysis_Output as input)
- Seamless integration with Market Analysis Agent (accepts A9_Market_Analysis_Output as input, including LLM-powered market research)
- Human-in-the-loop and iterative refinement are required; agent must support user feedback and resubmission cycles
- All solution generation and evaluation steps must be logged for auditability and compliance
- All market research usage (including LLM-sourced insights) must include source attribution and be logged for compliance.
- Decision style to persona mapping must be implemented via consulting_persona_provider
- KPI lens_affinity must be retrieved from Data Governance Agent and used for persona selection
- Persona selection priority: request override > KPI lens_affinity > decision_style > role affinity > default
- Guardrails for personalization vs attribution must be enforced in all LLM prompts
- All persona selection decisions must be logged with source (lens_affinity, decision_style, etc.)

---

### Integration-First Testing & Interface Refactor (2025-05-11)
- As agent interdependencies increase, brittle unit tests are deprioritized in favor of integration and compliance testing.
- All agents are being refactored for clear boundaries and minimal, well-documented interfaces.
- Testing now prioritizes real agent-to-agent workflows, protocol adherence, and end-to-end compliance.
- Excessive mocking is minimized—only true external dependencies (e.g., APIs, databases) are mocked.
- All agent entrypoints and outputs must be designed for seamless integration, not just isolated logic.
- Regression and compliance suites are used to ensure standards across the ecosystem.
- This approach is now the standard for all Solution Finder Agent compliance and regression testing, and will be applied to all future agent migrations.

---

## Protocol Compliance
- All agent entrypoints must strictly comply with the A2A protocol, accepting and returning Pydantic models for type safety, validation, and interoperability.
- The agent must implement all MCP (Minimum Compliance Protocol) requirements, including compliance checks, reporting, and error handling.
- Protocol compliance is mandatory for registry integration and agent orchestration.

## Problem Mindmap & Agent Network Diagram UI (MVP Requirement, 2025-05-05)
- Implement interactive UI components to visualize problem decomposition as a mindmap and show dynamic agent recruitment/orchestration as a network diagram.
- Rationale: Windsurf Persona Debate consensus (2025-05-05) found these features critical for demo, onboarding, explainability, and market differentiation, provided implementation is low-risk and does not delay core agent delivery.
- Action Items:
  - Use existing visualization libraries (e.g., react-flow, Cytoscape.js) for rapid prototyping.
  - Integrate with orchestrator logs/registry for real-time and historical visualization.
  - Ship a minimal, non-blocking version for MVP (static or read-only acceptable if needed).

> **Tracking:** See BACKLOG_REFOCUS.md for backlog status and actionable items.

## Future Scope (Not in MVP)
- Automated scenario simulation and optimization
- Integration with external solution libraries or expert systems
- Real-time collaborative problem-solving
- User-customizable evaluation criteria and workflows
- Agent learning from solution outcomes and user feedback

## Change Log
- **2026-02-28 (Phase 10):** Multi-call LLM architecture. Replaced single monolithic LLM call with 3 parallel Stage 1 persona calls + 1 synthesis call. Added `stage_1_hypotheses` to `SolutionFinderResponse`. Added `impact_estimate` to `SolutionOption`. Enriched `data_payload` with `situation_metadata`, `decision_maker`, multi-tenant `business_context`. Added IS-NOT data extraction from DA output. Added `debate_stage` check to skip Stage 1 for `cross_review`/`synthesis` frontend calls. Expanded opt_2/opt_3 to full schemas (token budget freed). UI: Stage 1 rich consulting cards in `ExecutiveBriefing.tsx`.
- **2026-02-xx (Phase 9):** Enriched data_payload with decision_maker, situation_metadata, business_context (explicit). Added IS-NOT side extraction from Deep Analysis (`where_is_not`, `what_is_not`, `when_is_not`). Fixed business context multi-tenant resolution via `_DP_CONTEXT_MAP` and KPI registry lookup. Added QUANTIFIED IMPACT REQUIREMENT, SCOPING REQUIREMENT, OPTION DIVERSITY REQUIREMENT constraints.
- **2026-02-xx (Phase 8):** Added `impact_estimate` block to options schema. Expanded Stage 1 hypothesis display with `key_evidence`, `conviction`, consulting firm card UI. Added dynamic persona_ids template for `stage_1_hypotheses` and `cross_review` schema.
- **2025-05-12:** Implemented full HITL escalation logic in Solution Finder Agent; output model and logging now strictly protocol-compliant. Documentation and checklist updated; unit tests cover HITL scenarios and protocol compliance.
- **2025-04-20:** Updated PRD to reflect MVP debate outcomes and Product Owner answers (integration with Deep Analysis, mixed solution generation, human-in-the-loop, trade-off matrix, auditability, strict A2A/MCP compliance).

---

## Implementation Details

### Fallback Logger Implementation
- Implements a fallback logger mechanism when the standard logging system is unavailable
- Provides consistent logging interface across all environments
- Ensures critical events are always captured even in degraded operation modes
- Supports seamless transition between logging systems based on availability

### Debug Logging Approach
- Implements comprehensive debug statements for option and tradeoff generation
- Uses standardized `[DEBUG]` prefix for all debug-level logging
- Provides detailed visibility into solution generation and evaluation process
- Supports troubleshooting and performance optimization

### Test Stability Features
- Ensures at least two dummy solution options are always generated for test stability
- Implements fallback mechanisms to guarantee consistent test results
- Provides deterministic behavior for automated testing scenarios
- Supports both unit and integration testing patterns

### Configuration Update Method
- Implements a dynamic configuration update method
- Supports runtime adjustment of agent parameters
- Validates configuration changes against protocol requirements
- Ensures configuration consistency across agent lifecycle

### Deep Analysis Recommendation Extraction
- Implements specialized extraction logic for Deep Analysis Agent recommendations
- Transforms unstructured analysis into actionable solution components
- Supports direct integration with Deep Analysis Agent output models
- Provides confidence scoring for extracted recommendations

### Audit Logging Implementation
- Implements comprehensive audit logging for all agent operations
- Records all solution generation steps, evaluations, and recommendations
- Provides traceability for regulatory compliance
- Supports detailed review of decision-making process

### Fallback Rationale Generation
- Implements fallback mechanisms for rationale generation when dependencies are unavailable
- Ensures solution options always include supporting rationale
- Provides consistent user experience even in degraded operation modes
- Supports graceful degradation of functionality

### Tradeoff Matrix Population
- Implements robust tradeoff matrix population logic
- Handles missing dependencies through fallback mechanisms
- Ensures complete matrix generation for all solution comparisons
- Supports consistent decision support even with partial information
