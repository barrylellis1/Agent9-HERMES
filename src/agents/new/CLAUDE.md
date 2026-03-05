# Agent Development — src/agents/new/

## Agent Dependency Graph

```
A9_Orchestrator_Agent (no dependencies)
├── A9_Data_Governance_Agent (no dependencies)
├── A9_Principal_Context_Agent (no dependencies)
│   └── Uses: Principal Profile Provider, Business Process Provider, KPI Registry
├── A9_Data_Product_Agent
│   ├── SHOULD depend on: A9_Data_Governance_Agent (view name resolution) ⚠️ MISSING
│   └── DOES depend on: A9_Data_Product_MCP_Service_Agent (SQL execution) ✅
├── A9_Situation_Awareness_Agent
│   ├── Depends on: A9_Data_Product_Agent (KPI data)
│   └── Depends on: A9_Principal_Context_Agent (principal context)
├── A9_Deep_Analysis_Agent
│   └── Uses: A9_LLM_Service_Agent (via orchestrator)
├── A9_Solution_Finder_Agent
│   └── Uses: A9_LLM_Service_Agent (via orchestrator)
├── A9_NLP_Interface_Agent
│   └── Uses: A9_LLM_Service_Agent (via orchestrator)
├── A9_KPI_Assistant_Agent
│   ├── Uses: A9_LLM_Service_Agent (via orchestrator)
│   └── Coordinates with: A9_Data_Product_Agent (contract updates)
└── A9_LLM_Service_Agent
    └── Routes ALL LLM calls through Orchestrator (logging, audit)
```

**Correct initialization sequence:**
Registry Factory → Orchestrator → Data Governance → Principal Context → Data Product → Situation Awareness

## Agent Lifecycle (Target Pattern)

- Creation: `agent = await AgentClass.create_from_registry(config)` or `await AgentRegistry.get_agent("name")`
- Async initialization in `_async_init` method
- Standard sequence: `create()` → `connect()` → process requests → `disconnect()`
- Discovery at runtime: `await self.orchestrator.get_agent("A9_LLM_Service_Agent")`
- Registry access: `self.registry_factory.get_provider("kpi")`
- Context fields to propagate: `principal_context`, `situation_context`, `business_context`, `extra`

## Anti-Patterns: Agent Instantiation 🔴 CRITICAL

```python
# NEVER — direct instantiation bypasses registry and lifecycle
agent = A9_Principal_Context_Agent(config)
agent = AgentClass()

# ALWAYS
agent = await AgentRegistry.get_agent("agent_name")
agent = await AgentClass.create_from_registry(config)
```

## Anti-Patterns: LLM Calls 🔴 CRITICAL

```python
# NEVER — direct API calls bypass audit, routing, and guardrails
import openai; openai.ChatCompletion.create(...)
import anthropic; anthropic.messages.create(...)
# Any import of openai or anthropic in agent files (except a9_llm_service_agent.py)

# ALWAYS — route through orchestrator → LLM Service Agent
llm_service = await orchestrator.get_agent("A9_LLM_Service_Agent")
response = await llm_service.generate(request)
# OR via execute_agent_method:
response = await self.orchestrator.execute_agent_method("A9_LLM_Service_Agent", "analyze", {"request": req})
```

## Anti-Patterns: Pydantic Models 🔴 CRITICAL

```python
# NEVER — raw dicts break A2A protocol compliance
return {"status": "ok", "data": [...]}
request = {"principal_id": "cfo_001"}
# Using plain dicts in test fixtures

# ALWAYS — Pydantic models for all agent I/O
return ResponseModel(status="ok", data=[...])
request = RequestModel(principal_id="cfo_001")
```

## Anti-Patterns: Inter-Agent Communication ⚠️ HIGH PRIORITY

```python
# NEVER — direct instantiation or import bypasses orchestrator
self.data_governance_agent = DataGovernanceAgent()
from ..agents import SomeAgent; agent = SomeAgent()

# ALWAYS — via orchestrator
self.agent = await self.orchestrator.get_agent("agent_name")
```

## Anti-Patterns: Registry Access ⚠️ HIGH PRIORITY

```python
# NEVER — direct file or class access bypasses factory pattern
with open("kpi_registry.yaml") as f: data = yaml.load(f)
registry = KPIRegistry()

# ALWAYS — via Registry Factory
provider = self.registry_factory.get_provider("kpi")
data = provider.get_all()
```

## Anti-Patterns: Logging ℹ️ MEDIUM

```python
# NEVER
print("Debug message")
import logging; logger = logging.getLogger()

# TARGET: self.logger via A9_SharedLogger (not yet implemented)
# INTERIM (all agents currently use): logging.getLogger(__name__)
# When A9_SharedLogger is implemented, migrate to: self.logger.info("Message")
```

## Business Process Handling

- MVP uses domain-level only: `"Finance"`, `"Operations"`, `"Sales"`, etc. (39 across 12 domains)
- Mixed formats are **known tech debt**: support snake_case, display names, and IDs
- Always use case-insensitive comparison for business process matching
- Do NOT hardcode business process lists — load from registry
- Future design: hierarchical (Domain → Process → Sub-Process → Activity)
  See: `docs/architecture/business_process_hierarchy_blueprint.md`

## Naming Conventions

- **Files**: snake_case — `a9_orchestrator_agent.py`
- **Classes**: PascalCase — `A9_Orchestrator_Agent`
- **Methods/functions**: snake_case — `get_principal_context`
- **Constants**: UPPER_SNAKE_CASE — `DEFAULT_TIMEOUT`
- **Agent names**: `A9_[Name]_Agent` — `A9_Principal_Context_Agent`
- **Pydantic models**: PascalCase + descriptive suffix — `PrincipalProfileRequest`, `SituationAwarenessResponse`

## Agent File Index

| File | Description |
|---|---|
| `a9_orchestrator_agent.py` | Central coordinator; agent registry singleton; dependency resolution; 7 workflow methods |
| `a9_principal_context_agent.py` | 8 principal profiles; dual lookup (role + ID); business process mapping |
| `a9_situation_awareness_agent.py` | KPI threshold monitoring; anomaly detection; situation card generation; NL query processing |
| `a9_deep_analysis_agent.py` | Dimensional Is/Is Not analysis; change-point detection; SCQA framing; BigQuery support |
| `a9_solution_finder_agent.py` | Multi-call parallel LLM debate (3×Stage1 + synthesis); trade-off matrix; HITL events |
| `a9_data_product_agent.py` | Schema inspection (DuckDB/BigQuery/Postgres); contract YAML; SQL execution; view management |
| `a9_data_governance_agent.py` | Business term translation; KPI-to-data-product mapping; MVP allows all access |
| `a9_nlp_interface_agent.py` | Deterministic regex parsing (no LLM); TopN intent; timeframe/grouping extraction |
| `a9_llm_service_agent.py` | Multi-provider (Claude/OpenAI); template prompting; model routing; token tracking |
| `a9_kpi_assistant_agent.py` | LLM-powered KPI suggestions; conversational refinement; API-only (no UI) |
| `a9_data_product_mcp_service_agent.py` | SQL execution via MCP — **DEPRECATED** (removal after 2025-11-30) |

**Shared models:** `src/agents/models/` — Pydantic request/response models per agent
**Base model:** `src/agents/shared/a9_agent_base_model.py` — `A9AgentBaseRequest` requires `request_id` + `principal_id`
**Agent PRDs:** `docs/prd/agents/` — read before adding new capabilities to any agent
