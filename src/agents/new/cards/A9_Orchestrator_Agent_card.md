# A9_Orchestrator_Agent Card

**Status:** Active — central coordinator, agent registry singleton  
**Last Updated:** 2026-05-08  
**File:** `src/agents/new/a9_orchestrator_agent.py`  
**Models:** `src/agents/models/` (per-agent model files)

---

## What This Agent Does

The Orchestrator is the **glue layer** — it holds the registry of all running agents, routes calls between them, and exposes the high-level workflow methods used by the API routes. It does NOT contain any business logic itself; it delegates everything to the appropriate specialist agent.

Two distinct classes live in this file:

| Class | Role |
|---|---|
| `AgentRegistry` | Class-level singleton that stores agent instances and factories by name |
| `A9_Orchestrator_Agent` | Instance-level orchestrator that wraps the registry and exposes workflow methods |

---

## AgentRegistry — The Singleton

**Never instantiate directly.** One instance is created at module load: `agent_registry = AgentRegistry()`.

```python
# Register an already-created agent instance
AgentRegistry.register_agent(agent_name: str, agent_instance: Any) -> None

# Register a factory function (agent created on first get_agent call)
AgentRegistry.register_agent_factory(agent_name: str, factory_func: Callable) -> None

# Get an agent by name — creates via factory if not yet instantiated
await AgentRegistry.get_agent(agent_name: str, config: Dict = None) -> Any

# List all registered agent names
AgentRegistry.list_agents() -> List[str]

# Register dependency chain (used during bootstrap)
AgentRegistry.register_agent_dependency(agent_name: str, depends_on: List[str]) -> None

# Get dependencies for an agent
AgentRegistry.get_agent_dependencies(agent_name: str) -> List[str]

# Mark/check initialization status
AgentRegistry.set_agent_initialization_status(agent_name: str, status: bool) -> None
AgentRegistry.get_agent_initialization_status(agent_name: str) -> bool

# Wipe all registered agents (test teardown only)
AgentRegistry.clear() -> None
```

---

## A9_Orchestrator_Agent — Protocol Entrypoints

### Registry Access

```python
# Get any registered agent by name (resolves dependencies first)
await orchestrator.get_agent(
    agent_name: str,
    config: Dict = None,
    resolve_dependencies: bool = True
) -> Any

# Call a method on any registered agent by name
await orchestrator.execute_agent_method(
    agent_name: str,
    method_name: str,
    params: Any          # passed as **params to the method
) -> Any
```

`execute_agent_method` is the primary inter-agent call pattern. All agent-to-agent calls go through this, not direct method calls.

---

### Workflow Methods (the 4 main pipelines)

```python
# 1. Situation Awareness — detect KPI threshold breaches
await orchestrator.orchestrate_situation_detection(
    request: SituationDetectionRequest
) -> Dict[str, Any]
# Returns: {"status": "success"|"error", "situations": [...], "metadata": {...}, "logs": [...]}
# Delegates to: A9_Situation_Awareness_Agent.detect_situations()

# 2. Deep Analysis — Is/Is Not dimensional analysis on a specific KPI breach
await orchestrator.orchestrate_deep_analysis(
    request: DeepAnalysisRequest
) -> DeepAnalysisResponse
# Steps: plan_deep_analysis() → execute_deep_analysis()
# Returns: DeepAnalysisResponse (or .error() on failure)
# Delegates to: A9_Deep_Analysis_Agent

# 3. Solution Finding — multi-persona debate + ranked recommendations
await orchestrator.orchestrate_solution_finding(
    request: SolutionFinderRequest
) -> SolutionFinderResponse
# Returns: SolutionFinderResponse with options_ranked list
# Delegates to: A9_Solution_Finder_Agent.recommend_actions()

# 4. Value Assurance — DiD evaluation after a solution goes live
await orchestrator.run_value_assurance(
    solution_id: str,
    principal_id: str,
    current_kpi_value: float,
    control_group_kpi_values: Optional[List[float]] = None,
    market_recovery_estimate: Optional[float] = None,
    seasonal_estimate: Optional[float] = None,
) -> Dict[str, Any]
# Returns: {"evaluation": {...}, "narrative": "..."} or {"error": "..."}
# Steps: evaluate_solution_impact() → generate_narrative()
# Delegates to: A9_Value_Assurance_Agent
```

---

### Data Product Onboarding Workflow

```python
# Full 8-step onboarding: inspect → contract → register → KPIs → BPs → principals → QA
await orchestrator.orchestrate_data_product_onboarding(
    request: DataProductOnboardingWorkflowRequest
) -> DataProductOnboardingWorkflowResponse
# Delegates to: A9_Data_Product_Agent (step execution), A9_Data_Governance_Agent (validation)
```

---

### Batch / Headless Helpers

```python
# Headless SA scan — used by run_enterprise_assessment.py
await orchestrator.detect_situations_batch(
    request: Dict[str, Any]   # dict compatible with SituationDetectionRequest
) -> Dict[str, Any]

# Prepare DuckDB environment from a YAML contract (headless, no UI)
await orchestrator.prepare_environment(
    contract_path: str,
    view_name: str = "FI_Star_View",
    schema: str = "main"
) -> Dict[str, Any]

# YAML-driven multi-step workflow (minimal implementation — placeholder)
await orchestrator.orchestrate_workflow(
    workflow_config: Dict[str, Any]
) -> Dict[str, Any]
```

---

### Lifecycle

```python
# Factory method — always use instead of __init__
orchestrator = await A9_Orchestrator_Agent.create(config: Dict = None)

# Connect all registered agents
await orchestrator.connect()

# Disconnect all registered agents
await orchestrator.disconnect()

# Inject business context (called during bootstrap with problem statement YAML)
orchestrator.inject_business_context(
    problem_statement: Any,
    default_path: Optional[str] = None
) -> Any
```

---

## Initialization Sequence

Bootstrap wires agents in this order (see `src/api/runtime.py`):

```
1. RegistryFactory (Supabase providers)
2. A9_Orchestrator_Agent.create()
3. A9_Data_Governance_Agent   — registered, connected
4. A9_Principal_Context_Agent — registered, connected
5. A9_Data_Product_Agent      — registered, connected
6. A9_Situation_Awareness_Agent
7. A9_Deep_Analysis_Agent
8. A9_Solution_Finder_Agent
9. A9_LLM_Service_Agent
10. A9_Value_Assurance_Agent
11. runtime._wire_governance_dependencies()  ← DGA injected into DPA post-bootstrap
```

If `get_agent("X")` is called before agent X is registered, it raises `ValueError`. The registry does NOT auto-create agents not registered during bootstrap.

---

## What the Orchestrator Must NOT Do

- Contain business logic (KPI evaluation, SQL generation, LLM calls) — delegate all of this
- Be instantiated directly: `A9_Orchestrator_Agent()` — always use `create()`
- Call agent methods directly (bypassing `execute_agent_method`) in new code
- Import `openai` or `anthropic` — LLM calls go through A9_LLM_Service_Agent

---

## Error Behaviour

| Method | On failure |
|---|---|
| `orchestrate_situation_detection` | Returns `{"status": "error", "message": "...", "situations": []}` |
| `orchestrate_deep_analysis` | Returns `DeepAnalysisResponse.error(...)` |
| `orchestrate_solution_finding` | Returns `SolutionFinderResponse(status="error", ...)` |
| `run_value_assurance` | Returns `{"error": "..."}` |
| `get_agent` (unregistered name) | Raises `ValueError` |
| `execute_agent_method` | Propagates exception from the agent method |

---

## Dependencies

The Orchestrator itself has no agent dependencies — it IS the registry. All other agents depend on it.
