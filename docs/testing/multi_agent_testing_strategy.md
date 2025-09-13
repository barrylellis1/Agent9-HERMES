# Multi-Agent Testing Strategy for Agent9

## Overview

Testing the Agent9 platform presents unique challenges due to its multi-agent architecture. Each agent has dependencies on other agents and shared services, creating a complex web of interactions. This document outlines a comprehensive testing strategy that addresses these challenges.

## Testing Layers

### 1. Unit Tests

**Purpose**: Test individual agent methods in isolation.

**Implementation**:
- Mock all dependencies (other agents, registries, services)
- Focus on specific functionality (e.g., KPI loading, SQL generation)
- Verify correct handling of edge cases and error conditions

**Example**: Testing the `_convert_to_kpi_definition` method in the Situation Awareness Agent with mock KPI data.

### 2. Component Tests

**Purpose**: Test a single agent with minimal dependencies.

**Implementation**:
- Create standardized mock implementations for common dependencies
- Test agent initialization, configuration loading, and basic operations
- Verify protocol compliance

**Example**: Testing the Situation Awareness Agent with mock KPI registry and mock Data Product Agent.

### 3. Integration Tests (Agent Pairs)

**Purpose**: Test interactions between pairs of agents.

**Implementation**:
- Focus on specific integration points (e.g., SA Agent + Data Product Agent)
- Mock external dependencies not part of the tested pair
- Verify correct message passing and protocol adherence

**Example**: Testing SQL delegation from Situation Awareness Agent to Data Product Agent.

### 4. Subsystem Tests

**Purpose**: Test a group of related agents working together.

**Implementation**:
- Test complete workflows that span multiple agents
- Mock external systems (databases, external APIs)
- Verify end-to-end functionality for specific use cases

**Example**: Testing the complete KPI situation detection workflow with real Situation Awareness Agent, Data Product Agent, and Principal Context Agent.

### 5. End-to-End Tests

**Purpose**: Test the entire system with minimal mocking.

**Implementation**:
- Use real agent implementations wherever possible
- Test complete business scenarios
- Verify system behavior from user perspective

**Example**: Testing the complete situation awareness workflow from user request to situation detection and response.

## Reusable Testing Components

### 1. Mock Agent Factory

A factory for creating standardized mock agents that implement the required protocols:

```python
class MockAgentFactory:
    @staticmethod
    def create_mock_data_product_agent():
        # Return a standardized mock Data Product Agent
        pass
        
    @staticmethod
    def create_mock_principal_context_agent():
        # Return a standardized mock Principal Context Agent
        pass
```

### 2. Test Fixtures

Standard test fixtures for common test scenarios:

```python
@pytest.fixture
def mock_kpi_registry():
    # Return a standardized mock KPI registry
    pass
    
@pytest.fixture
def mock_principal_profiles():
    # Return standardized mock principal profiles
    pass
```

### 3. Test Data

Standardized test data for KPIs, principal profiles, and business processes:

```python
# Standard test KPIs
TEST_KPIS = [
    {
        "id": "fin_revenue",
        "name": "Revenue",
        "description": "Total revenue across all business units",
        # ...
    },
    # ...
]

# Standard test principal profiles
TEST_PRINCIPAL_PROFILES = [
    {
        "principal_id": "cfo_001",
        "role": "CFO",
        # ...
    },
    # ...
]
```

## Implementation Plan

1. **Create reusable mock implementations**:
   - Develop standardized mock agents that implement required protocols
   - Create test fixtures for common dependencies
   - Define standard test data

2. **Implement unit tests**:
   - Focus on core agent methods
   - Use mocks for all dependencies

3. **Implement component tests**:
   - Test each agent in isolation
   - Use standardized mock implementations

4. **Implement integration tests**:
   - Test agent pairs
   - Focus on key integration points

5. **Implement subsystem tests**:
   - Test complete workflows
   - Use real agent implementations where possible

6. **Implement end-to-end tests**:
   - Test complete business scenarios
   - Minimize mocking

## Best Practices

1. **Dependency Injection**:
   - Design agents to accept dependencies via constructor or factory method
   - Use dependency injection to facilitate testing

2. **Protocol Compliance**:
   - Ensure all agents strictly adhere to their defined protocols
   - Use protocol interfaces to define agent interactions

3. **Test Isolation**:
   - Ensure tests do not depend on each other
   - Clean up resources after each test

4. **Test Coverage**:
   - Aim for high test coverage of core functionality
   - Prioritize testing of critical paths and error handling

5. **Continuous Integration**:
   - Run tests automatically on code changes
   - Maintain a stable test suite

## Conclusion

This multi-layered testing strategy addresses the complexities of testing the Agent9 multi-agent system. By creating standardized mock implementations and test fixtures, we can effectively test individual agents, agent pairs, and complete workflows while managing the complexity of agent dependencies.
