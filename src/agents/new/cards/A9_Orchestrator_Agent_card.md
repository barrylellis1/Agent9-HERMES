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

**client_id must reach every step, not just registration (Aug 2026):** the principal-ownership
step's `ownership_payload` did not include `request.client_id` — found live, running this
workflow end to end for the first time, when it resolved a different tenant's principal as
owner. Fixed by threading `client_id` into `ownership_payload`; see
`A9_Principal_Context_Agent_card.md`'s Aug 2026 entry for the full fix (also required changes
inside that agent — this was not a one-line fix). When adding a new conditional step to this
workflow, don't assume `client_id` is already reachable at that step just because it's on the
top-level request — check the step's own payload dict explicitly includes it.

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

---

## Agent factory registration — single path (Jul 2026)

`initialize_agent_registry()` in `a9_orchestrator_agent.py` is now the **only**
thing that registers agent factories. The legacy `AgentBootstrap` path — invoked
from `src/registry/bootstrap.py`, which scanned `src/agents/*.py` and discovered
the pre-`new/` agent classes — has been removed along with those implementations.

This closes a long-standing source of confusing startup noise: `AgentBootstrap`
logged warnings for every legacy file it failed to import
(`Error discovering agents in src/agents/a9_principal_context_agent.py: No module
named 'src.agents.agent_provider_connector'`, `Found agent class
A9_KPI_Assistant_Agent but it lacks a create method`) on every single boot, none
of which affected the running system — the new-stack agents were registered
separately the whole time.

Practical consequence: an agent that is not registered by
`initialize_agent_registry()` does not exist as far as the orchestrator is
concerned. There is no longer a second, filesystem-scanning path that might
pick it up.

## Feature Flags Must Be Wired, Not Just Declared (Aug 2026)

`use_structured_output` (Stage A, forced tool-use synthesis) had a config field on `A9_Solution_Finder_Agent_Config` and two consuming call sites in the agent — but the orchestrator's SF config block never populated it. It sat pinned to its Pydantic default of `False`, and **no deployment could turn it on**.

This surfaced only when `/healthz` began reporting `SF_USE_STRUCTURED_OUTPUT`. Setting that variable would have displayed `true` for a flag the agent never read, reintroducing the exact false confidence the endpoint exists to remove — with the endpoint itself as the source. A reader trusts `/healthz` precisely because it is meant to describe the running system rather than an intention.

**Rule:** any flag reported by `/healthz` must be read here and threaded into the owning agent's config, and must default to `"false"` so a gated feature is opt-in rather than enabled wherever the variable happens to be absent. `tests/unit/test_feature_flag_wiring.py` enforces both, parametrised over `_REPORTED_FLAGS` in `src/api/main.py`, so adding a reported flag without wiring it fails the build.

Found while setting up the PM-2 A/B for the structured-output flip — the experiment could not have run at all, since both arms would have executed identical code.

## `orchestrate_data_product_onboarding` planted a junk registry row on every Schema Discovery click (Aug 2026)
- Found by actually driving the real Admin Console onboarding wizard live against hess's SQL Server database (`decision-studio-ui/tests/e2e/live-onboarding-hess-test.spec.ts`) — the wizard's "Schema Discovery" step calls this workflow purely to preview tables, posting `data_product_id='temp_discovery'` with no `data_product_name`/`domain`/`description`. `register_data_product` ran unconditionally right after `inspect_source_schema` on every call to this method, with no distinction between a preview call and a real registration — so every discovery click silently persisted a `temp_discovery` data product into the real Supabase `data_products` table for whichever client was targeted. Found two stray rows this way, one from 2026-07-24 (a different client, `brookshire_brothers`) — this had been happening for over a month before it was noticed.
- Fixed: new `discovery_only: bool = False` field on `DataProductOnboardingWorkflowRequest` (and the API-facing `DataProductOnboardingWorkflowApiRequest` in `workflows.py`), threaded through `_run_data_product_onboarding_workflow`. When `True`, `orchestrate_data_product_onboarding` skips `register_data_product` (and everything gated on it — KPI/business-process registration) entirely; `inspect_source_schema` still runs and its result still flows back unaffected, since the UI only reads that one step from the response during discovery. The wizard's `handleSchemaDiscovery` now sends `discovery_only: true`.
- Defaults to `False` deliberately — an omitted field on any existing caller (or a future one) must keep registering, not silently stop; only the one call site that genuinely doesn't want registration opts in explicitly.
- Verified live: re-ran the same wizard test against hess after the fix — no `temp_discovery` row appears, and the real registration (triggered later, at the "Metadata Analysis" step, with a real `data_product_id`) still succeeds and still writes `dimension_semantics` correctly (see the Phase 16 O3 entry above).
- Tests: `tests/unit/test_orchestrator_data_product_onboarding.py` — `discovery_only=True` calls only `inspect_source_schema`, never `register_data_product`; a normal call (default `discovery_only=False`) still registers; the inspection result still reaches the response's `steps` list; the field's default is pinned to `False`.

## `prepare_environment` and `onboard_data_product` deleted — confirmed dead (Aug 2026)

Phase 16 step 5 (DEVELOPMENT_PLAN.md): these two "headless orchestration helper" methods
(YAML-contract-driven table/view registration + a composite onboarding workflow calling
DGA's `validate_registry_integrity`/`compute_and_persist_top_dimensions`) were traced during
the step-5 `yaml.safe_load` audit and found to have **zero callers anywhere** in `src/`,
`scripts/`, the UI, or tests — `onboard_data_product` was self-referenced only in its own
error handler, and `prepare_environment`'s only other callers were an unimported Streamlit
prototype (`decision_studio.py`, last touched Dec 2025) and one integration test (updated to
skip instead, see `tests/integration/test_cogs_validation.py`). Not "narrow" or "bicycle-only"
like the DPA/DGA methods they called — genuinely unreachable from any live entrypoint. Deleted
along with `A9_Data_Product_Agent.register_tables_from_contract`/`create_view_from_contract`
and `A9_Data_Governance_Agent.validate_registry_integrity`/`compute_and_persist_top_dimensions`
(see those agents' own cards) in the same pass. 1484 unit tests unaffected (none exercised
this code).
