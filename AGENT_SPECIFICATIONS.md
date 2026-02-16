# Agent Specifications Reference (from PRDs)

## CRITICAL PROTOCOL REQUIREMENTS

### Universal Agent Requirements (ALL AGENTS)

1. **Instantiation Pattern** 🔴 MANDATORY
   - ❌ NEVER instantiate agents directly
   - ✅ ALWAYS use: `await AgentRegistry.get_agent("Agent_Name")`
   - ✅ OR use: `await Agent.create_from_registry(config)`
   - This is documented in EVERY agent PRD

2. **Pydantic Model Requirement** 🔴 MANDATORY
   - ALL agent inputs/outputs MUST use Pydantic models
   - NO raw dicts/lists in agent-to-agent communication
   - NO raw dicts/lists in tests
   - This is the A2A (Agent-to-Agent) protocol standard

3. **Logging Standard** 🔴 MANDATORY
   - Use `A9_SharedLogger` exclusively
   - NO print statements
   - NO direct logging module usage
   - Standardized across all agents

4. **Orchestrator Routing** 🔴 MANDATORY
   - All LLM calls MUST go through A9_LLM_Service_Agent
   - All LLM calls MUST be routed through Orchestrator
   - NO direct LLM API calls from agents
   - This is documented in LLM Service PRD

5. **Lifecycle Methods** 🔴 MANDATORY
   - Implement: `create`, `connect`, `disconnect`
   - Async operations throughout
   - Proper dependency resolution before `connect()`

6. **HITL Protocol Fields** ℹ️ REQUIRED
   - Include in outputs: `human_action_required`, `human_action_type`, `human_action_context`
   - HITL enforcement is configurable (defaults to OFF)
   - Must be present in response models even if not enforced

## Agent-Specific Specifications

### A9_Orchestrator_Agent

**Purpose**: Central coordinator for Agent9 workflows

**Key Responsibilities**:
- Workflow orchestration and state management
- Agent registration and lifecycle management
- Agent dependency resolution
- Message routing between agents
- Decision tracking and logging

**Initialization Sequence** (DOCUMENTED):
1. Initialize Registry Factory and providers
2. Create and connect Orchestrator Agent
3. Create and register Data Governance Agent
4. Create and register Principal Context Agent
5. Create and register Data Product Agent
6. Create and register Situation Awareness Agent
7. Connect agents in same order

**Agent Dependencies Management**:
- Tracks agent dependencies via registry
- Resolves dependencies recursively
- Prevents circular dependencies
- Method: `register_agent_dependency(agent_name, [dependencies])`
- Method: `create_agent_with_dependencies(agent_name)`

**Critical Methods**:
- `run_workflow()` - Execute multi-step workflows
- `get_agent(agent_name)` - Retrieve registered agents
- `register_agent()` - Register agent instances
- `create_agent_with_dependencies()` - Create with dep resolution

### A9_Principal_Context_Agent

**Purpose**: Manage principal (user) context, profiles, access control

**Key Responsibilities**:
- Principal profile management (via Principal Profile Provider)
- Access control and permissions (RBAC)
- Business process mapping
- Context-aware recommendations
- **Decision style to analysis lens mapping**

**Critical Specifications**:
- Uses **principal ID** as primary key (NOT role names)
  - Current Issue: Implementation uses role-based lookup (case-sensitive)
  - Target: Migrate to ID-based lookup (`ceo_001`, `cfo_001`, etc.)
  - Migration plan documented in `principal_id_based_lookup_plan.md`

- **Output Structure** (MUST include):
  ```python
  {
    "profile": {
      "principal_id": "cfo_001",
      "role": "CFO",
      "decision_style": "analytical",  # Maps to analysis lens
      "responsibilities": ["Revenue by Business Unit"],  # Business terms
      "filters": {"Region": "North America"}  # Business dimensions
    }
  }
  ```

- **Decision Style Mapping**:
  - `analytical` → McKinsey-style (MECE, root cause)
  - `visionary` → BCG-style (strategic, portfolio)
  - `pragmatic` → Bain-style (quick wins, operations)
  - `decisive` → McKinsey-style (structured decisions)

- **LLM Integration**:
  - Uses A9_LLM_Service for recommendation descriptions
  - Extracts filters from job descriptions via LLM/NLP
  - All LLM calls are orchestrator-routed

- **Registry Integration**:
  - Uses Unified Registry Access Layer
  - Principal Profile Provider for profiles
  - Business Process Provider for mappings
  - KPI Registry for entity canonicalization

**Guardrails**:
- ❌ "The CFO believes..." (attribution violation)
- ✅ "Tailored for analytical decision style..." (personalization OK)

### A9_Data_Governance_Agent

**Purpose**: Enforce data governance policies, access control, compliance

**Key Responsibilities**:
- Data access control and validation
- Data quality monitoring
- Compliance validation
- Audit trail maintenance
- View name resolution for Data Product Agent

**Critical Specifications**:
- **Should be connected to Data Product Agent** (currently missing)
- Connection pattern documented in `data_governance_agent_connection.md`
- Provides governance rules to Data Product Agent
- Validates owner roles and stakeholder principals

**Dependencies**:
- No dependencies (initializes early in sequence)

### A9_Data_Product_Agent

**Purpose**: Manage data products, schemas, SQL execution

**Key Responsibilities**:
- Data product registration and discovery
- Schema validation and transformation
- SQL query execution (delegates to MCP Service Agent)
- View name resolution (should delegate to Data Governance Agent)

**Critical Specifications**:
- **Depends on**: A9_Data_Governance_Agent (view name resolution)
- **Depends on**: A9_Data_Product_MCP_Service_Agent (SQL execution)
- **Current Issue**: Data Governance Agent not properly connected
  - Falls back to local resolution (works but bypasses governance)
  - Should use: `await orchestrator.get_agent("data_governance")`
  - Pattern similar to how it initializes MCP Service Agent

**MCP Service Integration** (CORRECT PATTERN):
```python
# In _async_init
self.mcp_service_agent = await A9_Data_Product_MCP_Service_Agent.create({
    "database": {
        "type": "duckdb",
        "path": self.db_path
    }
}, logger=self.logger)
```

**Missing Data Governance Connection** (SHOULD BE):
```python
# In connect() method
if self.orchestrator:
    self.data_governance_agent = await self.orchestrator.get_agent("data_governance")
```

### A9_Situation_Awareness_Agent

**Purpose**: Identify business situations requiring attention

**Key Responsibilities**:
- Monitor KPIs and thresholds
- Detect anomalies and patterns
- Prioritize situations by impact
- Generate situation summaries
- Domain-level business process matching

**Critical Specifications**:
- **Depends on**: A9_Data_Product_Agent (KPI data)
- **Depends on**: A9_Principal_Context_Agent (principal context)

**Business Process Handling**:
- Supports domain-level business processes (e.g., "Finance")
- Enhanced `_get_relevant_kpis` for domain-level matching
- Works with simplified business process registry (MVP)

### A9_Deep_Analysis_Agent

**Purpose**: Perform detailed analysis of identified situations

**Key Responsibilities**:
- Root cause analysis (Kepner-Tregoe IS/IS-NOT)
- Impact assessment and trend analysis
- Correlation detection
- Contextual enrichment

**Critical Specifications**:
- Uses `decision_style` from Principal Context for analysis framing
- Routes analysis through A9_LLM_Service_Agent
- All LLM calls are orchestrator-routed

### A9_Solution_Finder_Agent

**Purpose**: Generate and evaluate potential solutions

**Key Responsibilities**:
- Solution generation and evaluation
- Implementation planning
- Outcome prediction
- **Trade-off analysis deliverable**

**Critical Specifications**:
- Uses `decision_style` for consulting persona selection
- **Trade-Off Analysis**: Structured comparison at decision points
  - Compares options across: time, confidence, risk, business impact, cost
  - Presented to principal for review
  - Decisions logged for audit and learning
- Routes through A9_LLM_Service_Agent

### A9_LLM_Service_Agent

**Purpose**: Centralized LLM operations for all agents

**Key Responsibilities**:
- Provider abstraction (OpenAI, Anthropic, etc.)
- Task-based model selection
- Prompt assembly and validation
- Response parsing and validation
- Orchestrator routing and logging

**Critical Specifications** (CORE TO ARCHITECTURE):
- **ALL** LLM operations MUST go through this agent
- NO direct LLM API calls from any agent
- ALL requests/responses use Pydantic models
- ALL calls routed through Orchestrator
- Supports multiple providers/models
- Environment awareness (stubs in dev/test, real in prod)

**Operations**:
- `generate` - General text generation
- `summarize` - Text summarization
- `analyze` - Data/text analysis
- `parse_business_query` - NLQ to structured intent
- `nl2sql` / `kpi_sql` - SQL generation with safety notes

**Source Attribution**:
- All LLM outputs marked with `source: "llm"`
- Includes operation/type metadata
- Enables traceability

**SQL Generation** (MVP):
- Single source of dynamic SQL generation
- Registry-scoped context in prompts
- SELECT-only enforcement via prompt constraints
- Includes rationale + safety notes

### A9_NLP_Interface_Agent

**Purpose**: Natural language processing capabilities

**Key Responsibilities**:
- Query parsing and understanding
- Intent recognition
- Entity extraction
- Response generation

**Critical Specifications**:
- Routes through A9_LLM_Service_Agent
- Orchestrator-mediated communication

### A9_Data_Product_MCP_Service_Agent

**Purpose**: SQL execution service for Data Product Agent

**Key Responsibilities**:
- Execute SQL queries against DuckDB/BigQuery
- Query validation
- Result formatting

**Critical Specifications**:
- Created by Data Product Agent (not via orchestrator)
- Direct instantiation pattern (service, not agent)
- Properly initialized in Data Product Agent's `_async_init`

### A9_KPI_Assistant_Agent

**Purpose**: LLM-powered KPI definition during data product onboarding

**Key Responsibilities**:
- Schema-based KPI generation (3-7 suggestions)
- Strategic metadata enforcement (line, altitude, profit_driver_type, lens_affinity)
- Conversational refinement interface
- KPI validation and finalization

**Critical Specifications**:
- Uses A9_LLM_Service_Agent for all NLP
- Validates all KPI attributes (100% completeness)
- Enforces strategic metadata tags
- Maintains conversation history (in-memory, not persisted)
- Coordinates with Data Product Agent for contract updates

**Strategic Metadata Tags**:
- `line`: top_line (revenue), middle_line (operational), bottom_line (profit/cost)
- `altitude`: strategic, tactical, operational  
- `profit_driver_type`: revenue, expense, efficiency, risk
- `lens_affinity`: bcg, bain, mckinsey, etc.

## Common Anti-Patterns to FLAG

### Instantiation Violations
```python
# ❌ WRONG - Direct instantiation
agent = A9_Principal_Context_Agent(config)

# ✅ CORRECT - Registry pattern
agent = await AgentRegistry.get_agent("A9_Principal_Context_Agent")
```

### LLM Call Violations
```python
# ❌ WRONG - Direct LLM call
response = openai.ChatCompletion.create(...)

# ✅ CORRECT - Via LLM Service + Orchestrator
llm_service = await orchestrator.get_agent("llm_service")
response = await llm_service.generate(request)
```

### Pydantic Violations
```python
# ❌ WRONG - Raw dict
result = {"status": "ok", "data": [...]}

# ✅ CORRECT - Pydantic model
result = ResponseModel(status="ok", data=[...])
```

### Agent Communication Violations
```python
# ❌ WRONG - Direct agent reference
self.data_product_agent = DataProductAgent()

# ✅ CORRECT - Via orchestrator
self.data_product_agent = await self.orchestrator.get_agent("data_product")
```

### Registry Access Violations
```python
# ❌ WRONG - Direct YAML loading
with open("registry.yaml") as f:
    data = yaml.load(f)

# ✅ CORRECT - Via Registry Factory
provider = self.registry_factory.get_provider("kpi")
data = provider.get_all()
```

## Testing Requirements (ALL AGENTS)

**Pydantic Model Requirement** 🔴 MANDATORY:
- All tests MUST use Pydantic model instances
- NO raw dicts/lists in test data
- NO mocking with dicts
- This ensures A2A protocol compliance in tests

**Integration by Default**:
- All tests involving Orchestrator + LLM Service are integration tests
- No true unit isolation (agents are interdependent)
- Test fixtures must spin up orchestrator and dependencies
- Tests must cover agent-to-agent communication

## Review Checklist

When reviewing agent code, check for:

- [ ] Uses `create_from_registry` or `AgentRegistry.get_agent()` for instantiation
- [ ] All I/O uses Pydantic models (no raw dicts/lists)
- [ ] Uses `A9_SharedLogger` for logging (no print/direct logging)
- [ ] LLM calls go through A9_LLM_Service_Agent + Orchestrator
- [ ] Implements lifecycle methods (create, connect, disconnect)
- [ ] Gets other agents via `orchestrator.get_agent()` not direct references
- [ ] Uses Registry Factory for registry access, not direct YAML loading
- [ ] Includes HITL protocol fields in response models
- [ ] Async/await used correctly throughout
- [ ] Error handling with proper agent error classes
- [ ] Tests use Pydantic models, not dicts/mocks
