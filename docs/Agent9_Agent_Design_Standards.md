# Agent9 Agent Design Standards

This document defines the architectural, naming, compliance, and process standards for all agents in the Agent9 platform. **Adherence is mandatory for all new and existing agents.**

---

> **Critical Orchestration Compliance Principle (2025-06):**
> - All agent discovery and registration must be orchestrator-internal and fully automated.
> - The orchestrator must scan workflow steps, load agent cards/configs, dynamically import agent classes, and register agents as needed.
> - **Manual agent registration in tests or production is strictly prohibited.**
> - All event logging (e.g., agent_registration, situation_analysis) must be performed via the registry and must be awaited (async) for protocol compliance.
> - Tests must only provide workflow input and assert on output/events; no test or harness may register agents directly.
> - Tests must assert on registry event logs using only public APIs (see Agent9_Test_Patterns.md).
> - Bootstrap/card scanning logic, if needed, must be invoked by the orchestrator itself, never by test or production harnesses.
> - The A9_Situation_Awareness_Agent is the reference implementation for this pattern.

---

## 1. Naming and Structure
- All agent files, classes, and cards must use the `A9_` prefix.
- Names must include team context (e.g., `innovation_`, `solution_`, `market_`) and agent context (e.g., `catalyst_`, `architect_`).
- Use `snake_case` for functions/variables and `CamelCase` for classes.
- Each agent must reside in its own file under `src/agents/new/`.

## 2. Agent Card (Architectural Requirement)
- Every agent MUST have a corresponding agent card in `src/agents/new/cards/` (e.g., `A9_My_Agent_card.py` or `.md`).
- The agent card must describe the agent, config, protocol entrypoints, and compliance notes.
- The card must be kept in sync with the agent code and config model.

## 3. Config Model
- Each agent requiring configuration must have a Pydantic config model in `src/agents/new/agent_config_models.py`.
- Changes to agent implementation must be reflected in both the card and config model to maintain compliance and validation.

## 4. Imports and Dependencies
- Use relative imports for all internal modules.
- Only import dependencies required for the agent’s operation.
- Avoid importing templates or unused code.

## 5. Protocol Compliance

### Pydantic v2 & Hybrid Protocol Compliance (Critical)

All Agent9 agent input/output models MUST use Pydantic v2 patterns:
- Use `model_config = ConfigDict(extra="allow")` (import `ConfigDict` from `pydantic`).
- Do NOT use `class Config: ...`; this is deprecated in v2.
- Always use `.model_dump()` for serialization and logging (never `.dict()` or `.json()`).
- Never access private/internal Pydantic attributes (e.g., `__private_attributes__`, `__pydantic_fields__`).
- All models must include required audit/logging fields (`request_id`, `timestamp`, `principal_id`) and flexible context fields (`principal_context`, `situation_context`, `business_context`, `extra`).
- All agent cards and orchestrator-driven workflows must assert on both protocol-required and flexible fields.
- See the Orchestration Refactor Plan for the full migration checklist.

- All agent interactions must comply with the Agent9 protocol, including registry integration, config validation, and logging.
- Agents must be instantiable via an orchestrator or registry using a `create_from_registry` class method.

## 5a. Scientific Method, Evidence-Based Validation & Human-in-the-Loop Escalation (2025-05-06)
- All Agent9 agents must follow a disciplined, unbiased process: hypothesis formation, evidence gathering, and validation before escalating to human input.
- All solution recommendations must be supported by internal or external evidence of effectiveness. If such evidence is lacking, agents must propose a pilot/experiment and a plan for gathering validation data before adoption.
- LLMs are used to search, summarize, and present supporting evidence or to draft pilot protocols and study plans.
- Escalation to human (via NLP agent prompt or UI) only occurs when analytic/scientific methods are exhausted or when human wisdom, sensory ability, or creativity is likely to yield a breakthrough.
- If no proven or pilotable solutions are available, and human-in-the-loop brainstorming fails to produce actionable ideas, the Solution Finder Agent will escalate the problem to the A9_Innovation_Driver_Agent for creative, out-of-the-box ideation.
- All reasoning steps, failed attempts, escalation triggers, and innovation escalations are logged for transparency and learning.

## 6. Security and Environment
- API keys and secrets must be loaded from environment variables, never hardcoded.
- `.env` files must never be overwritten or committed without explicit confirmation.

## 7. Testing and Documentation
- Each agent must have thorough unit and integration tests covering major functionality and error handling.
- PRD (Product Requirements Document) must be updated before implementation, with modification history, impact analysis, and test cases listed.
- Documentation and usage examples must be updated post-implementation.

### Migration & Testing Strategy

As agent interdependencies increase, unit testing becomes less effective and more brittle. To ensure robust compliance and maintainability, we will:

- **Refactor all agents for clear boundaries and minimal, well-documented interfaces.**
- **Prioritize integration and compliance testing** over isolated unit tests. Focus on real agent-to-agent workflows and protocol adherence.
- **Minimize excessive mocking**—only mock true external dependencies (e.g., external APIs, databases).
- **Continuously refactor agent interfaces** and orchestration logic to keep integration smooth as protocols evolve.
- **Build regression and compliance suites** to ensure protocol and workflow standards across the ecosystem.

## 7a. UI Wireframe Coverage (Process Requirement)
- Every new agent or workflow must have a dedicated markdown wireframe (`*_wireframe.md`) in `/docs/prd/agents/`.
- The wireframe must follow the standard dashboard layout: sections for tabular data, metrics, alerts, recommendations, summary, and status.
- This requirement applies to both MVP and future agent additions.
- The naming convention and directory structure are mandatory for consistency, onboarding, and review.
- Reference: This process was established as a backlog item and is now a permanent part of the Agent9 standards.

This approach will be applied to all agent migrations and MVP enhancements going forward.

## 8. Code Quality and Maintainability
- Avoid code duplication—check for existing logic before adding new code.
- Do not introduce new patterns or technology unless necessary, and remove deprecated logic if you do.
- Keep files under 200–300 lines; refactor if necessary.
- Avoid scripts or one-off logic in agent files.
- No stubbing or fake data in dev/prod code (mocking is only for tests).

## 8a. Agent9 Test Guidelines

All test scripts (unit, integration, system) must strictly adhere to the following:

1. **No Direct Agent Instantiation**
   - Agents must only be instantiated via the orchestrator or AgentRegistry (e.g., `get_agent`, `async_get_agent`, `create_from_registry`).
   - Direct instantiation (e.g., `A9_NLP_Interface_Agent({})`) is prohibited in tests.
2. **No Monkeypatching Core Methods**
   - Do not monkeypatch or override registry/agent methods (such as `get_agent`). Use only official extension points or dependency injection.
3. **No Manual Agent Registration**
   - **Manual agent registration in tests or production is strictly prohibited.**
   - The orchestrator is responsible for discovering and registering all required agents from workflow steps and agent cards/configs automatically.
   - Tests must never register agents directly or via test-specific bootstrap logic.
4. **No Direct Attribute Manipulation**
   - Do not set internal attributes (e.g., `_registry`, `_config`) directly in tests. Use only public/documented APIs.
5. **Protocol-Compliant Input/Output Only**
   - All test data passed to agents must use the appropriate Pydantic models, never raw dicts/lists.
6. **Test Registration and Compliance**
   - Tests must assert that agents are discoverable via the registry, agent cards exist/validate, and protocol entrypoints are callable via orchestrator/registry.
7. **No Circumventing Orchestrator Logic**
   - All agent workflows in tests must go through the orchestrator when that is the production path.
8. **No Unregistered Test/Mock Agents**
   - Any dummy/mock agents must be registered and discoverable via the registry, and protocol documented in the agent card.
9. **No Skipping Protocol Validation**
   - Never bypass config or protocol validation in tests.
10. **Documentation and Review**
    - All test scripts must reference these guidelines and the Agent9 Agent Design Standards. Code reviews and CI must enforce compliance.

> These guidelines are mandatory. Automated checks and code reviews must enforce them. Reference this section in all test PRs and onboarding.

## 9. Compliance and Guardrails
- No template artifacts (e.g., `A9_Agent_Template`) should be present in agent code.
- Use the official template from the `templates/` directory for new agents, never copy by hand from source directories.
- Compliance scripts/tests must be run to ensure all standards are met.

## Registration and Lifecycle Management

> **Compliance Note:** All agent registration and instantiation must be orchestrator/registry-controlled. Self-registration by agent instances is strictly prohibited. This ensures uniformity, maintainability, and A2A protocol compliance.
- Block implementation until PRD is updated.
- Require documentation updates before marking as complete.
- Verify test coverage before finalizing changes.
- Maintain consistent error handling patterns.

## 10. Change Management
- Block implementation until PRD is updated.
- Require documentation updates before marking as complete.
- Verify test coverage before finalizing changes.
- Maintain consistent error handling patterns.

---

## Checklist for New Agents
- [ ] Agent file and class follow naming conventions
- [ ] Agent card created and in sync
- [ ] Config model present and in sync
- [ ] **No manual agent registration in tests or production; orchestrator must discover/register agents from workflow and cards**
- [ ] All agent registration and instantiation is orchestrator/registry-controlled (self-registration is strictly prohibited)
- [ ] Relative imports only
- [ ] Protocol entrypoints defined
- [ ] No hardcoded secrets
- [ ] All error logging uses A9_SharedLogger and is compatible with orchestration-level aggregation
- [ ] Tests written
- [ ] PRD updated
- [ ] No template artifacts
- [ ] Documentation complete

---

**Reference this document in all onboarding, code reviews, and PRs.**

---

## 11. Multi-Agent System Design Principles

To ensure Agent9 is robust, scalable, and maintainable as a multi-agent platform, all new and existing agent workflows must adhere to the following architectural and protocol standards:

### 11.1. Contract-First Protocol Definition

- **All agent entrypoints and outputs must be defined by strict protocol schemas** (e.g., Pydantic models, OpenAPI, or Protobuf).
- **Every agent method invoked by the orchestrator must accept and return protocol-compliant models**—never bare dicts, lists, or ad hoc objects.
- Protocol models must be versioned, documented, and referenced in agent cards and orchestrator workflow definitions.

### 11.2. Centralized Orchestrator Control

- **The orchestrator is the sole authority for agent registration, instantiation, and protocol enforcement.**
- Agent discovery, config loading, and dynamic import/registration must occur only within orchestrator-driven code paths.
- No agent or test code may register or instantiate agents outside orchestrator or registry logic.

### 11.3. Declarative Workflow Definitions

- **Workflows should be defined declaratively** (YAML/JSON/DSL), not as hard-coded Python logic.
- This enables:
  - Auditable, versioned workflow definitions.
  - Dynamic step generation, looping, and branching.
  - Easier integration with workflow engines (e.g., LangChain, Prefect).

### 11.4. Strict Separation of Concerns

- **Agent logic must be completely decoupled from orchestration and other agents.**
- Agents implement only their protocol contract; context propagation, error handling, and output mapping are orchestrator responsibilities.
- Tests must invoke agents only via orchestrator APIs, never directly.

### 11.5. Automated Protocol Compliance

- **Automated scripts and CI must enforce protocol compliance**:
  - All agent entrypoints must use protocol models.
  - No top-level protocol model imports in orchestrator code.
  - No duplicate or redundant agent/model registration.
  - All agent outputs must include required protocol fields (e.g., `status`, `profile`, etc.).

### 11.6. Continuous Integration and Auditability

- **All changes to agent protocols, workflows, or registration logic must be reviewed for protocol compliance and auditability.**
- Automated checks must block merges that violate these standards.

### 11.7. Hybrid Pydantic/Text Model Structure (A9AgentBaseModel Pattern)

- All protocol models must inherit from `A9AgentBaseModel` (or a compliant base).
- **Hybrid Structure**: These models are designed to support both strict Pydantic validation and flexible, LLM-friendly text serialization.
- **Context Fields**: The fields `principal_context`, `situation_context`, `business_context`, and `extra` must be present and:
  - Accept both structured (dict/Pydantic) and natural language (text) representations.
  - Be serializable for LLM input (prompting) and deserializable from LLM output.
- **Usage**: When passing context between agents, always use the protocol fields. When interacting with LLMs, serialize the context fields as text using `.model_dump()` or a dedicated prompt builder.
- **Rationale**: This pattern enables robust protocol compliance for code-driven workflows, while supporting advanced LLM-driven reasoning and context propagation.

---

**Reference this section in all new agent proposals, workflow designs, and code reviews. Deviation from these principles must be justified and documented in the PRD and design docs.**
