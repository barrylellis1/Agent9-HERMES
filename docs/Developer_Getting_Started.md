# Agent9 Developer Getting Started Guide

## Introduction

Welcome to the Agent9 MVP Development! This guide will help you get started with implementing the Agent9 platform based on the provided Product Requirement Documents (PRDs) and architectural guidelines.

## Prerequisites

Before you begin, make sure you have:

1. Python 3.10+ installed
2. Git installed
3. A code editor or IDE (e.g., VS Code, PyCharm)
4. Access to the required LLM APIs (see `.env.example` for details)

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/Agent9-MVP-Template.git
cd Agent9-MVP-Template
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

## Project Structure Overview

- `docs/`: Documentation, including PRDs, architecture diagrams, and guidelines
- `src/`: Source code for the Agent9 platform
- `test-harnesses/`: Test harnesses for validating your implementation
- `src/registry-references/`: Reference implementations for registries

## Implementation Workflow

### 1. Understand the Requirements

1. Start with the [PRD Quick Start Guide](prd/PRD_Quick_Start_Guide.md) to understand the PRD structure
2. Review the [Core Workflow Diagram](architecture/core_workflow_diagram.md) to understand agent interactions
3. Read the [Agent9 Agent Design Standards](Agent9_Agent_Design_Standards.md) for mandatory standards

### 2. Implement Core Agents

Implement the following agents in order:

1. **Orchestrator Agent**: [PRD](prd/agents/a9_orchestrator_agent_prd.md)
2. **Principal Context Agent**: [PRD](prd/agents/a9_principal_context_agent_prd.md)
3. **Data Product Agent**: [PRD](prd/agents/a9_data_product_agent_prd.md)
4. **Data Governance Agent**: [PRD](prd/agents/a9_data_governance_agent_prd.md)
5. **NLP Interface Agent**: [PRD](prd/agents/a9_nlp_interface_agent_prd.md)
6. **LLM Service Agent**: [PRD](prd/agents/a9_llm_service_agent_prd.md)
7. **Situation Awareness Agent**: [PRD](prd/agents/a9_situation_awareness_agent_prd.md)
8. **Deep Analysis Agent**: [PRD](prd/agents/a9_deep_analysis_agent_prd.md)
9. **Solution Finder Agent**: [PRD](prd/agents/a9_solution_finder_agent_prd.md)

### 3. Implement Supporting Services

1. **Data Product MCP Service**: [PRD](prd/services/a9_data_product_mcp_service_prd.md)

### 4. Test Your Implementation

Use the provided test harnesses to validate your implementation:

```bash
# Run tests for a specific agent
python -m test-harnesses.run_agent_test --agent orchestrator

# Run integration tests
python -m test-harnesses.run_integration_test
```

## Key Implementation Requirements

### Protocol Compliance

All agents must follow the A2A protocol:

```python
# Example of protocol-compliant agent method
async def analyze_situation(self, input_model: SituationInput) -> SituationOutput:
    # Validate input
    if not isinstance(input_model, SituationInput):
        raise ValueError("Input must be a SituationInput model")
    
    # Process input
    # ...
    
    # Return validated output
    return SituationOutput(
        status="success",
        situation_id=situation_id,
        insights=insights,
        principal_context=input_model.principal_context,
        # Other required fields
    )
```

### Registry Integration

All agents must integrate with the Agent Registry:

```python
# Example of registry integration
@classmethod
async def create_from_registry(cls, registry, config=None):
    # Validate config using Pydantic model
    validated_config = A9YourAgentConfig(**(config or {}))
    
    # Create instance
    instance = cls(registry=registry, config=validated_config.model_dump())
    
    # Register with registry
    await registry.register_agent(instance)
    
    return instance
```

### Error Handling

Implement comprehensive error handling:

```python
# Example of error handling
try:
    result = await self.process_data(input_data)
    return SuccessOutput(data=result)
except DataNotFoundError as e:
    self.logger.error(f"Data not found: {str(e)}")
    return ErrorOutput(error=f"Data not found: {str(e)}")
except Exception as e:
    self.logger.error(f"Unexpected error: {str(e)}")
    return ErrorOutput(error=f"Internal error: {str(e)}")
```

## Common Pitfalls to Avoid

1. **Direct Agent Instantiation**: Never instantiate agents directly; always use the registry pattern
2. **Missing Error Handling**: Ensure comprehensive error handling and logging
3. **Incomplete Validation**: Always validate inputs and outputs using Pydantic models
4. **Protocol Violations**: Strictly adhere to the A2A protocol for all agent interactions
5. **Ignoring Context Propagation**: Ensure proper propagation of context fields between agents

## Resources

- [PRD Index](prd/index.md): Index of all PRDs
- [Agent9 Agent Design Standards](Agent9_Agent_Design_Standards.md): Mandatory standards for agent development
- [Test Data Usage Guide](Test_Data_Usage_Guide.md): Guidelines for using test data
- [LLM Model Specifications](LLM_Model_Specifications.md): Specifications for LLM models

## Getting Help

If you encounter issues or have questions, refer to:
- The [Agent9 Agent Design Standards](Agent9_Agent_Design_Standards.md)
- The test harnesses in the `test-harnesses/` directory
- The reference implementations in the `src/registry-references/` directory
