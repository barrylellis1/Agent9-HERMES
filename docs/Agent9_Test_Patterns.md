# Agent Test Patterns

> **Agent9 MVP Testing Philosophy (2025-07)**
>
> - For MVP, only protocol-compliant, orchestrator-driven, "happy path" tests are required.
> - Defensive/negative-path tests (e.g., passing dicts, invalid models, or invalid workflow steps) are **not required** for MVP and should be deferred until after MVP stabilization.
> - All workflow step inputs and outputs **must** be Pydantic v2 model instances—not dicts or legacy models. This is critical for protocol compliance and to avoid subtle runtime errors (see Pydantic v2 `__private_attributes__` lesson below).
> - The Agent9 orchestrator is responsible for enforcing protocol compliance at all workflow boundaries. Negative-path and error handling is centralized here, not in every agent or test. Agent tests should focus on positive-path, protocol-compliant scenarios.
> - See project memory and commit history for details on the Pydantic v2 `__private_attributes__` requirement. Direct dicts are not supported as workflow step inputs/outputs and will cause errors in orchestrator-driven workflows.
> - This is the current Agent9 standard for MVP. Full test coverage and negative-path scenarios will be revisited post-MVP, once the orchestrator and protocol boundaries are stable.


> **Reference:** The canonical Agent9 orchestrator-driven protocol test template is located at:
> `tests/TEST_PATTERNS_orchestrator_template.py`
> Use this template for all protocol entrypoint tests to ensure compliance with Agent9 standards.


> **Agent9 Orchestration-Driven Testing Standard (2025-06):**
> - All integration and protocol compliance tests must use the orchestrator to manage agent discovery, registration, and invocation.
> - **Manual agent registration or direct instantiation is strictly prohibited in orchestration-driven tests.**
> - Tests must only provide workflow input and assert on output and event logs; never register agents or call bootstrap logic directly.

This document outlines the recommended test patterns for Agent9 agents, based on the successful implementation in the Data Governance Agent.

## Test Factory Pattern

The test factory pattern uses factory functions to create consistent test data and reduce boilerplate in tests.

> **Agent9 Standard:**
> All agent test factories must build config dictionaries using the canonical fields and structure defined in the agent card (see `src/agents/new/cards/AGENT_CARD.md` for each agent). Always reference the agent card for required config and capabilities. This ensures protocol compliance and prevents drift between tests and agent config validation.

### Key Components

1. **Factory Functions**
   - Defined in `tests/agents/new/factories/`
   - Use a consistent naming convention: `{ModelName}Factory`
   - Must generate inputs and outputs as **Pydantic model instances** (not plain dicts or untyped objects). This ensures all test data is protocol-compliant and validates against the agent's schema.
   - Support both default and custom attribute overrides

2. **Test Structure**
   - One test class per agent
   - Grouped test methods by functionality
   - Clear, descriptive test names

### Example Implementation

```python
# In tests/agents/new/factories/__init__.py
from factory import Factory, Faker
from src.agents.new.data_governance_models import TermTranslationInput, FilterTranslationInput

class TermTranslationInputFactory(Factory):
    class Meta:
        model = TermTranslationInput
    
    source_terms = Faker('words', nb=3)
    source_domain = Faker('word')
    target_domain = Faker('word')
```

### Test Categories

1. **Core Functionality Tests**
   - Test main operational capabilities
   - Cover all public methods
   - Include both success and error cases

2. **Model Validation Tests**
   - Test Pydantic model validation
   - Include edge cases and invalid inputs
   - Verify error messages

3. **Error Handling Tests**
   - Test error conditions
   - Verify proper exception types and messages
   - Test error recovery

4. **Integration & Orchestration Tests**
   - Use the orchestrator to execute workflows and manage all agent lifecycle (discovery, registration, invocation)
   - Never register agents or instantiate them directly in tests—rely on orchestrator-internal logic and agent cards/configs
   - Provide only workflow input and assert on orchestrator output and agent event logs for protocol compliance
   - Use mocks only for true external dependencies (APIs, DBs), never for agent registration or instantiation

### Best Practices

1. **Test Data**
   - Use factories for consistent test data
   - Keep test data realistic but minimal
   - Avoid hardcoded values when possible

2. **Test Organization**
   - Group related tests
   - Use descriptive test names
   - Keep tests focused and independent

3. **Assertions**
   - Use specific assertions
   - Include descriptive failure messages
   - Test both positive and negative cases

4. **Performance**
   - Keep tests fast
   - Use mocks for slow operations
   - Avoid unnecessary setup/teardown

## Canonical Orchestration-Driven Test Patterns

### Best Practice: Selective Agent/Component Loading

- **Do NOT** globally import or register all agents/registries in `conftest.py`.
- **DO** register only the agent(s) and supporting components (models, cards, factories, etc.) needed for each test, ideally within the test function or a local fixture.
- This avoids unrelated registry/model errors and enables isolated, protocol-compliant testing.
- Example:

```python
@pytest.fixture
def orchestrator():
    # Only register the agent(s) needed for this test
    registry = AgentRegistry()
    config_map = {"A9_Quality_Assurance_Agent": load_agent_config("A9_Quality_Assurance_Agent")}
    orchestrator = A9_Orchestrator_Agent(config={}, registry=registry, config_map=config_map)
    return orchestrator
```

- See the orchestrator-driven unit test template for a working example.

## Canonical Orchestration-Driven Test Template (2025-06)

> **This is the up-to-date, protocol-compliant pattern for all orchestrator-driven agent tests in Agent9.**
> Use this as the reference for all new and refactored agent tests. See `test_A9_situation_awareness_agent.py` for the full implementation.

```python
import pytest
from src.agents.new.A9_Orchestrator_Agent import A9_Orchestrator_Agent, OrchestratorWorkflowInput, WorkflowStep
from tests.agents.new.factories.situation_awareness_factories import SituationAwarenessInputFactory

@pytest.mark.asyncio
async def test_analyze_situation():
    """
    Canonical orchestrator-driven test for Agent9 agents.
    - All agent lifecycle is managed by the orchestrator from workflow input.
    - Asserts protocol-required events are logged:
        - 'agent_registration': Agent was registered automatically
        - 'situation_analysis': Entrypoint method was executed
    - Validates protocol-compliant output structure.
    """
    orchestrator = A9_Orchestrator_Agent()
    input_data = SituationAwarenessInputFactory()
    workflow_input = OrchestratorWorkflowInput(
        workflow_name="situation_awareness_single",
        steps=[
            WorkflowStep(
                agent_name="A9_Situation_Awareness_Agent",
                method="analyze_situation",
                input=input_data
            )
        ]
    )
    result = await orchestrator.orchestrate_workflow(workflow_input)
    if hasattr(result, "model_dump"):
        result = result.model_dump()
    agent_output = result["output"]["A9_Situation_Awareness_Agent"]
    assert isinstance(agent_output, dict)
    for key in ['summary', 'metrics', 'trends', 'anomalies', 'timestamp', 'executive_notes', 'status', 'message']:
        assert key in agent_output
    # Assert protocol-required events are present
    events = []
    try:
        events = orchestrator.agent_registry.get_agent_events("A9_Situation_Awareness_Agent")
    except Exception as e:
        print(f"DEBUG: Could not retrieve events: {e}")
    event_types = [event.get("type") for event in events]
    required_events = ["agent_registration", "situation_analysis"]
    for evt in required_events:
        assert evt in event_types, f"Missing required event: {evt}"
```

**Protocol Compliance Notes:**
- Never instantiate or register agents directly in tests; always use the orchestrator and workflow input.
- Always assert on protocol-required events and output fields.
- Use this template for all new or refactored agent tests to ensure A2A compliance and maintainability.

## Test Coverage Goals

- 100% line coverage for core functionality
- 100% branch coverage for error handling
- All public methods tested
- All error conditions tested
- All model validations tested

## Running Tests

**Agent9 Unit Test Reporting Policy:**
- Always use verbose (`-v`) and skip-reporting (`-rs`) flags when running pytest for unit tests.
- Never use quiet reporting (`-q`) for unit testing.
- Test output summaries must always explicitly report all skipped and xfailed tests, with reasons.

To run tests with coverage:

```bash
pytest tests/agents/new/test_a9_data_governance_agent.py -v -rs --cov=src.agents.new.A9_Data_Governance_Agent --cov-report=term-missing
```
