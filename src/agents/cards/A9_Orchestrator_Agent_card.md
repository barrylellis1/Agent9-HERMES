---
configuration:
  name: A9_Orchestrator_Agent
  version: ''
  capabilities: [data_product_onboarding]
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_Orchestrator_Agent
- **Team / Agent Context Tags:** core, orchestrator
- **Purpose:** Central brain that enforces the A2A protocol, manages agent registry & lifecycle, coordinates multi-agent workflows, handles logging/audit, and propagates YAML contract context.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9OrchestratorConfig(BaseModel):
    registry_path: str = "src/agents/new/agent_registry.yaml"
    logging_level: str = "INFO"
    enable_audit: bool = True
    continue_on_error: bool = False
    max_concurrent_workflows: int = 10
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `orchestrate_workflow` | Execute multi-step workflow | `OrchestratorWorkflowInput` | `OrchestratorWorkflowOutput` | logs + audit |
| `register_agent` | Register agent class & config | `AgentRegistrationRequest` | `Dict` | updates registry |
| `run_workflow` (deprecated) | Legacy wrapper | `OrchestratorWorkflowInput` | `Dict` | logs events |
| `onboard_data_product` | Orchestrated onboarding: register tables, create view, validate registry integrity, compute KPI enrichment | kwargs dict | `{success, steps, artifacts}` | writes `src/registry/kpi/kpi_enrichment.yaml` |

Supported hand-off commands / state updates:
- `propagate_yaml_contract` – inject `yaml_contract_text` into downstream context

## 4. Compliance, Testing & KPIs
- **Design-Standards Checklist**
  - Naming follows `A9_*`
  - File size < 300 lines
  - No hard-coded secrets
  - Tests reference Agent9 standards
- **Unit / Integration Test Targets**
  - Unit coverage ≥ 95% (critical path)
  - Concurrency & error-propagation integration tests
- **Runtime KPIs & Monitoring Hooks**
  - Avg orchestration latency target < 500 ms per step
  - Workflow success-rate ≥ 99 %
  - Audit log completeness ≥ 99 %

---
description: |
  Central orchestrator for Agent9 that enforces the A2A protocol, manages agent handoffs, 
  handles logging, and coordinates hybrid integration. This agent is responsible for 
  executing workflows, managing the agent registry, and ensuring compliance with the A2A protocol.

team: core
agent_context: orchestrator
capabilities:
  - workflow_execution
  - concurrent_workflow_processing
  - agent_registry_management
  - error_handling
  - audit_logging
  - protocol_enforcement
  - yaml_contract_propagation

configuration:
  registry_path: str
  logging_level: str
  enable_audit: bool
  continue_on_error: bool
  max_concurrent_workflows: int

# Protocol Compliance and Dynamic Agent Loading
- Agent card config loading is strictly orchestrator-private. No agent, sub-agent, or test code may load or use card config directly.
- The orchestrator uses private methods (_load_agent_card_config, _resolve_agent_class) to:
  - Load agent configuration from the agent card for each agent required by the workflow.
  - Map agent names to their Python classes for registration.
- Only agents listed in the workflow steps are registered and instantiated for each workflow execution.
- No agent is registered or instantiated unless required by the current workflow.
- All agent config must be sourced and validated by the orchestrator using the Agent Card as the single source of truth.
- See orchestrator code for private method details and usage pattern.
- WARNING: Any attempt to load agent card config outside the orchestrator is a protocol violation and will be flagged in code review and CI.

# YAML Contract Metadata Propagation
- The orchestrator detects and propagates `yaml_contract_text` from the `extras` field of any agent step result.
- This YAML contract text is injected into the shared context and passed to all downstream steps via the `context` kwarg.
- Downstream agents always receive the latest YAML contract context in their `context` argument.
- Unit tests verify propagation through multi-step workflows for strict protocol compliance.

config:
  registry_path: "src/agents/new/agent_registry.yaml"
  logging_level: "INFO"
  enable_audit: true
  continue_on_error: false
  max_concurrent_workflows: 10  # Maximum number of workflows to process concurrently

protocol_entrypoints:
  - name: orchestrate_workflow
    description: Execute a multi-agent workflow with comprehensive error handling and logging
    input_model: OrchestratorWorkflowInput
    output_model: OrchestratorWorkflowOutput
    example: |
      ```python
      result = await orchestrator.orchestrate_workflow(
          OrchestratorWorkflowInput(
              workflow_name="data_processing",
              steps=[
                  WorkflowStep(
                      agent_name="data_loader",
                      method="load_data",
                      input=DataLoaderInput(source="database", query="SELECT * FROM data")
                  ),
                  WorkflowStep(
                      agent_name="data_processor",
                      method="process_data",
                      input=DataProcessorInput(transformations=["normalize", "clean"])
                  )
              ]
          )
      )
      ```

  - name: register_agent
    description: Register a new agent in the registry with optional configuration
    input_model: type  # Agent class to register
    output_model: Dict[str, Any]
    example: |
      ```python
      result = await orchestrator.register_agent(
          agent_class=MyCustomAgent,
          agent_id="custom_agent",
          config={"api_key": "12345"}
      )
      ```

  - name: run_workflow
    description: Legacy method for workflow execution (backward compatibility)
    input_model: OrchestratorWorkflowInput
    output_model: Dict
    deprecated: true
    note: Use orchestrate_workflow instead for new code

compliance:
  A2A_protocol: true
  structured_logging: true
  card_exists: true
  input_validation: true
  error_handling: comprehensive
  concurrency: true
  documentation: complete
  last_updated: "2024-12-10"

# Workflow Status Codes
# - success: All steps completed successfully
# - partial_success: Some steps completed successfully, but others failed
# - error: The workflow failed to execute
---

## Usage Examples

### Basic Workflow Execution
```python
from src.agents.new.A9_Orchestrator_Agent import OrchestratorWorkflowInput, WorkflowStep

# Create a workflow with multiple steps
workflow = OrchestratorWorkflowInput(
    workflow_name="example_workflow",
    steps=[
        WorkflowStep(
            agent_name="data_loader",
            method="load_data",
            input=DataLoaderInput(source="api", endpoint="/data")
        ),
        WorkflowStep(
            agent_name="data_processor",
            method="process_data",
            input=DataProcessorInput(transformations=["clean", "transform"])
        )
    ]
)

# Execute the workflow
result = await orchestrator.orchestrate_workflow(workflow)
```

### Error Handling
```python
try:
    result = await orchestrator.orchestrate_workflow(workflow)
    if result.status == "error":
        print(f"Workflow failed: {result.output}")
    elif result.status == "partial_success":
        print("Workflow completed with some errors")
        for agent, output in result.output.items():
            if isinstance(output, AgentErrorOutput):
                print(f"Error in {agent}: {output.error}")
    else:
        print("Workflow completed successfully")
except Exception as e:
    print(f"Fatal error: {str(e)}")
```

## Concurrency Support
The orchestrator supports concurrent workflow execution with the following features:

- Configurable maximum number of concurrent workflows
- Thread-safe execution of workflow steps
- Isolated context for each workflow execution
- Proper error isolation between concurrent workflows

### Example: Running Concurrent Workflows
```python
import asyncio

async def run_concurrent_workflows(orchestrator, workflows):
    """Run multiple workflows concurrently."""
    tasks = [orchestrator.orchestrate_workflow(workflow) for workflow in workflows]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Create multiple workflows
workflow1 = OrchestratorWorkflowInput(
    workflow_name="workflow1",
    steps=[...]
)
workflow2 = OrchestratorWorkflowInput(
    workflow_name="workflow2",
    steps=[...]
)

# Run them concurrently
results = await run_concurrent_workflows(orchestrator, [workflow1, workflow2])
```

## Best Practices
1. Always use `orchestrate_workflow` for new code (preferred over `run_workflow`)
2. Implement proper error handling for workflow steps
3. Use Pydantic models for all input/output to ensure type safety
4. Keep workflow steps focused and single-purpose
5. Use the audit log for debugging and compliance
6. When running concurrent workflows, ensure they are independent to avoid race conditions
7. Monitor system resources when increasing `max_concurrent_workflows`
8. Use the `continue_on_error` flag to control whether workflow execution should continue after a step fails
---
