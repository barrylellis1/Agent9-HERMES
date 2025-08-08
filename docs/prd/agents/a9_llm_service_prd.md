# A9_LLM_Service PRD

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2025-07-17
-->


## Project Testing Standard (Mandatory)

**All agent tests in Agent9 must use Pydantic model instances for both input and output.**

- No raw dicts/lists are permitted in agent-to-agent or agent-to-test communication.
- All test fixtures, scenario data, and assertions must use Pydantic models and their attributes.
- This is required for:
  - Strict A2A protocol compliance
  - Early validation and error catching
  - Production-like test coverage
  - Demo and audit readiness
- This standard applies to all new and refactored tests, and is tracked in the project backlog (see: 'Refactor all integration and unit tests to use Pydantic model instances').

*See below for rationale and implementation details.*


## Purpose
Centralize and standardize all LLM (Large Language Model) operations for Agent9 agents, ensuring protocol compliance, auditability, and extensibility.

## Objectives
- Provide a single service interface for all LLM operations (generation, summarization, analysis, validation, etc.).
- Abstract away LLM provider details (OpenAI, Anthropic, local models, etc.) from agents.
- Enforce all LLM requests and responses to use strict Pydantic models for validation.
- Route all LLM calls through the Orchestrator Agent for logging, access control, and policy enforcement.
- Support future extensibility: multi-model, ensemble querying, escalation, and environment awareness.

## Key Features

- **Trade-Off Analysis Deliverable:** The Solution Finder Agent generates a structured trade-off analysis whenever a decision point arises (e.g., speed vs. rigor, cost vs. benefit). This deliverable compares all viable options across criteria such as time, confidence, risk, business impact, and cost, and is presented to the principal for review and decision. All decisions and rationales are logged for audit and learning.
- **Centralized LLM Service:** All agents use A9_LLM_Service for LLM operations; no direct LLM API calls from agents.
- **Provider Abstraction:** Switch between LLM providers/models without changing agent code.
- **Task-Based Model Selection:** The LLM service can select or accept a model/provider for each task or operation, based on request parameters or internal policy.
- **Pydantic Validation:** Strict input/output validation for all LLM payloads.
- **Orchestrator Routing:** All LLM calls go through the Orchestrator Agent for logging and compliance.
- **Extensible Architecture:** Ready for ensemble querying, multi-model support, and escalation logic.
- **Environment Awareness:** Use stubs/mocks in dev/test, real APIs in prod.

## Inputs/Outputs
- **Input:** LLMRequest (Pydantic model: prompt, context, operation, etc.)
- **Output:** LLMResponse (Pydantic model: response, confidence, timestamp, etc.)

## Acceptance Criteria
1. All LLM operations in Agent9 are performed via A9_LLM_Service.
2. No agent directly calls LLM APIs.
3. All LLM requests and responses are validated using Pydantic models.
4. All LLM calls are logged and auditable via the Orchestrator Agent.
5. The service supports configuration for multiple providers/models and future ensemble features.
6. The LLM service can select or accept a model per task/operation, using the `model` field in LLMRequest.
7. The Solution Finder Agent produces a trade-off analysis deliverable at decision points, presenting options, criteria (time, confidence, risk, business impact, cost), and capturing the principal's choice for audit and learning.



## Hackathon Quick Start

### Development Environment Setup
- Clone the Agent9-Hackathon-Template repository
- Install required dependencies from requirements.txt
- Configure environment variables in .env file based on .env.template

### Key Files and Entry Points
- Main agent implementation: `src/agents/new/A9_LLM_Service_Agent_Agent.py`
- Configuration model: `src/agents/new/agent_config_models.py`
- Agent card: `src/agents/new/cards/a9_llm_service_agent_agent_card.py`

### Test Data Location
- Sample data available in `test-data/` directory
- Test harnesses in `test-harnesses/` directory

### Integration Points
- Integrates with Agent Registry for orchestration
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

## Best Practices for LLM-Agent Integration

### Overview

> **2025-05-13 Update:**
> The A9_LLM_Service_Agent is now fully refactored and compliant with Agent9 protocol and architectural standards. It uses a Pydantic config model, structured logging (`A9_SharedLogger`), orchestrator-controlled registry integration, and protocol entrypoints with Pydantic models. HITL is documented as not required for this agent. Card/config/code are now fully synchronized.

Agent9 agents must interact with LLMs exclusively via the centralized A9_LLM_Service, with all requests and responses routed through the Orchestrator Agent. This ensures protocol compliance, auditability, security, and extensibility for all LLM-powered features.

### Key Principles
- **Centralized LLM Service:** All LLM operations (generation, summarization, analysis, validation, etc.) are performed via A9_LLM_Service. Agents never call LLM APIs directly.
- **Pydantic Validation:** Strict input/output validation using Pydantic models for all LLM requests and responses.
- **Orchestrator Routing:** All LLM calls are routed through the Orchestrator Agent for logging, access control, and compliance.
- **Provider Abstraction:** The LLM service abstracts away provider/model details and supports task-based model selection.
- **Operation-Based API:** LLM requests specify an operation (e.g., "summarize", "analyze", "ideate"), enabling multi-purpose LLM usage.
- **Source Attribution:** All LLM-derived outputs are explicitly marked with `source: "llm"` and include operation/type metadata for traceability and downstream clarity.
- **Extensible Output Block:** LLM outputs are structured in a flexible, typed block (e.g., insights, summaries, recommendations, citations) to support current and future use cases.
- **Prompt Flexibility:** Agents may supply prompt fragments or context, but final prompt assembly and validation are handled centrally in the LLM service.
- **Auditability:** All LLM interactions are logged and auditable via the Orchestrator.
- **Environment Awareness:** Stubs/mocks are used in dev/test environments, with real APIs in prod.

### Industry Alignment
This approach aligns with enterprise best practices for security, compliance, observability, and future-proofing. It supports both current and anticipated agent-LLM interaction patterns, including multi-turn, streaming, and ensemble querying.

### Recommendations
- Document all supported LLM output types and operations in the LLM service PRD and models.
- Maintain strict adherence to protocol and validation standards for all LLM agent interactions.
- Plan for future extensibility (e.g., streaming, multi-turn sessions, new output types).

---

## Out of Scope
- Direct LLM API usage by agents
- Provider-specific logic in agent code

## Status
- MVP: Centralized LLM service, orchestrator routing, Pydantic validation
- Future: Ensemble querying, advanced provider selection, escalation, and environment-based logic

---

## Testing Implications: Integration by Default

**All tests involving the A9_LLM_Service and Orchestrator Agent are now integration tests.**

- **Agent Interdependence:** Every test exercises at least two agents (the agent under test and the orchestrator/LLM service), and often more.
- **No True Unit Isolation:** Unit tests that mock the orchestrator/LLM service are discouraged for dev/prod parity; all tests are integration tests by default.
- **Test Setup:** Fixtures must spin up the orchestrator and LLM service agent for all test runs.
- **Test Coverage:** Tests must cover agent-to-agent communication, error propagation, and end-to-end validation using Pydantic models.
- **Naming/Documentation:** Test files and comments should reflect their integration nature. Update PRD/testing docs to clarify this paradigm shift.
- **Edge Cases:** Ensure tests cover both happy path and error scenarios across agent boundaries, not just within a single agent.

This approach ensures production-like coverage and validates the orchestration patterns that are now core to Agent9's architecture.
