# Agent9-HERMES Project

## Project Overview
Agent9-HERMES is a multi-agent automation system designed to provide automated business insights and solutions through orchestrated workflows involving specialized agents. The system is built on protocol-driven, registry-based architecture with 100,000 lines of backend and UI code.

## Development Workflow Rules

### MANDATORY: Always Use restart_decision_studio_ui.ps1
- **NEVER** start the backend or frontend independently (e.g. `uvicorn ...` or `npm run dev` directly)
- **ALWAYS** use `.\restart_decision_studio_ui.ps1` to start/restart the full stack (FastAPI + React)
- This script handles port cleanup, Docker/Supabase startup, and process sequencing in the correct order
- To run: open PowerShell in the project root and run `.\restart_decision_studio_ui.ps1`

---

## Current Status
- **Development Duration**: 10 months
- **Codebase Size**: ~100K lines (backend + UI)
- **Known Issues**: 
  - Architectural inconsistencies from multiple refactors
  - Mixed code authoring styles from different AI models
  - Potential dead code from earlier iterations
  - Pattern drift across the codebase
  - Business process provider initialization issues
  - Data Governance Agent connection patterns incomplete
  - Registry provider replacement warnings

## Current Capabilities (What Actually Works Today)

### Working End-to-End Pipelines

**1. Situation Awareness → Deep Analysis → Solution Finding**
- Full detection-to-recommendation pipeline operational via Decision Studio UI
- Sidebar: Select principal (8 profiles), business processes (39 available), timeframe, comparison type
- Click "Detect Situations" → SA Agent queries KPIs against thresholds → generates situation cards
- Per-situation "Initiate Deep Analysis" → DA Agent runs dimensional Is/Is Not analysis with change-point detection
- Per-situation or standalone "Run Debate" → SF Agent runs **multi-call architecture**: 3 parallel Stage 1 LLM calls (one per persona) + 1 synthesis call → ranked solutions with quantified impact_estimate
- Follow-up NL questions per situation → NLP Interface Agent parses → Data Product Agent executes SQL → inline results
- HITL approval workflow for solution recommendations

**2. Data Product Onboarding (Admin Console)**
- Full Streamlit form (25+ fields) → FastAPI POST → Orchestrator → Data Product Agent
- 8-step orchestrated workflow: inspect schema → generate contract YAML → register data product → KPI registration → business process mapping → principal ownership → QA validation
- Supports DuckDB (local), BigQuery, PostgreSQL source systems
- Connection Profiles panel: create/edit/test/save profiles for any supported database
- Async status polling with real-time progress display
- Contract YAML auto-generation from inspected schema

**3. KPI Assistant (API Only — No UI)**
- 4 FastAPI endpoints wired at `/api/v1/data-product-onboarding/kpi-assistant/`
  - POST `/suggest` — LLM-powered KPI suggestions from schema metadata
  - POST `/chat` — Conversational KPI refinement
  - POST `/validate` — KPI validation against schema and governance rules
  - POST `/finalize` — Finalize KPIs and update contract YAML
- Agent: A9_KPI_Assistant_Agent with conversation history tracking
- **No Streamlit UI exists** — API endpoints only

### Implemented Agents (12 Total)

| Agent | Key Capabilities | Status |
|-------|-----------------|--------|
| **A9_Orchestrator_Agent** | Agent registry (singleton), dependency resolution with cycle detection, 7 workflow methods, `execute_agent_method()` for inter-agent calls | Core — operational |
| **A9_Principal_Context_Agent** | 8 principal profiles, dual lookup (role-based legacy + ID-based), business process mapping, data product ownership identification | Operational |
| **A9_Situation_Awareness_Agent** | KPI threshold monitoring, anomaly detection, situation card generation, per-KPI SQL generation, NL query processing | Operational |
| **A9_Deep_Analysis_Agent** | Dimensional Is/Is Not analysis, grouped comparisons, variance analysis, change-point detection, SCQA framing | Operational |
| **A9_Solution_Finder_Agent** | Multi-call parallel architecture (3 Stage 1 + 1 synthesis LLM calls), consulting council debate, trade-off matrix, quantified impact_estimate per option, stage_1_hypotheses, HITL events | Operational |
| **A9_Data_Product_Agent** | Schema inspection (DuckDB/BigQuery/Postgres), contract YAML generation, SQL execution, view management, data product registration | Operational — largest agent |
| **A9_Data_Governance_Agent** | Business term translation, KPI-to-data-product mapping, registry integrity validation, top dimension computation | Operational (MVP: allows all access) |
| **A9_NLP_Interface_Agent** | Deterministic regex-based parsing (no LLM), TopN intent, timeframe hints, grouping extraction, KPI resolution | Operational |
| **A9_LLM_Service_Agent** | Multi-provider (Claude/OpenAI), template-based prompting, model routing by task type, token tracking, guardrails | Operational |
| **A9_KPI_Assistant_Agent** | LLM-powered KPI suggestions from schema, conversational refinement, validation, contract updates | API-only (no UI) |
| **A9_Data_Product_MCP_Service_Agent** | SQL execution via MCP protocol | **DEPRECATED** (removal after 2025-11-30) |
| **A9_Risk_Analysis_Agent** | Weighted risk scoring (market/operational/financial), severity classification | **Dead code** — no tests, no registration, redundant with Solution Finder |

### Decision Studio UI Surfaces

**Decision Studio Mode (main):**
- Principal selector (dropdown, 8 profiles with name+role display)
- Business process multi-select (39 options, auto-loads from registry)
- Timeframe selector (LAST_QUARTER, CURRENT_QUARTER, YEAR_TO_DATE, etc.)
- Comparison type selector (QoQ, YoY, etc.)
- Detect Situations button → async situation detection
- Situation Worklist (radio buttons, severity-colored cards with KPI details)
- Per-situation: Details expander, diagnostic question buttons, Deep Analysis button, Solutions button
- Per-situation: Follow-up question text input with SQL generation and execution
- Solutions Studio: weight sliders (impact/cost/risk), problem statement, debate persona selector, Run Debate button
- Solutions display: recommendation, option scores table, debate transcript, KT Is/Is Not, executive summary with Stage 1 per-persona hypothesis cards and quantified impact estimates
- Debug mode: SQL per KPI, data governance mappings, diagnostics trace, state HUD
- NL Q&A section: free-text question → answer with generated SQL

**Admin Console Mode:**
- Data Product Onboarding: 25+ field form with connection profile integration
- Connection Profiles Manager: create/edit/test/delete profiles (DuckDB, BigQuery, Postgres, Snowflake, Redshift)
- Data Governance: placeholder ("coming soon")
- Registry Maintenance: placeholder ("coming soon")

### API Endpoints (55 Total)

**Workflow Routes** (`/api/v1/workflows/`):
- Situation detection: POST `/situations/run`, GET `/situations/{id}/status`, POST `/{id}/annotations`
- Deep analysis: POST `/deep-analysis/run`, GET `/{id}/status`, POST `/refine`
- Solutions: POST `/solutions/run`, GET `/{id}/status`, POST `/{id}/actions/approve|request-changes|iterate`
- Deep analysis revision: POST `/{id}/actions/request-revision`
- Data product onboarding: POST `/data-product-onboarding/run`, GET `/{id}/status`, POST `/validate-kpi-queries`

**Registry Routes** (`/api/v1/registry/`):
- KPIs: full CRUD (GET list, GET by id, POST, PUT, PATCH, DELETE) — 6 endpoints
- Principals: full CRUD — 6 endpoints
- Data Products: full CRUD with filtering — 6 endpoints
- Business Processes: full CRUD — 6 endpoints
- Business Glossary: CRUD — 5 endpoints

**KPI Assistant Routes** (`/api/v1/data-product-onboarding/kpi-assistant/`):
- POST `/suggest`, `/chat`, `/validate`, `/finalize`, GET `/health`

**Connection Profiles** (`/api/v1/connection-profiles/`):
- GET list, GET by id, POST, PUT, DELETE

**File Upload**: POST `/api/v1/upload`

### Database Backends (3 Operational)

| Backend | Status | Capabilities |
|---------|--------|-------------|
| **DuckDB** | Production-ready (local dev) | Full CRUD, CSV registration, view management, fallback views, European decimal support |
| **PostgreSQL/Supabase** | Production-ready (cloud) | Connection pooling (asyncpg), upsert, SSL, hybrid schema (columns + JSONB) |
| **BigQuery** | Production-ready (analytics) | Read-only by design, async query execution, service account auth, parameter substitution |

**Database Factory**: Supports `duckdb`, `postgres`/`postgresql`, `supabase` (alias→Postgres), `bigquery`

**SQL Security**: SELECT/WITH only enforcement, SQL injection pattern detection, DuckDB dialect transformations

### Registry System

**6 Registries with dual persistence (YAML + Supabase):**

| Registry | YAML Items | Supabase Migration | Current Backend |
|----------|-----------|-------------------|-----------------|
| Principal Profiles | 8 profiles | Migration 0002 ready | .env says `supabase` but **SUPABASE_DB_URL missing** → falls back to YAML |
| KPI | 25 KPIs (Finance domain) | Migration 0003 ready | Same — YAML fallback |
| Business Processes | 39 processes (12 domains) | Migration 0004 ready | Same — YAML fallback |
| Data Products | 9 products | Migration 0005 ready | Same — YAML fallback |
| Business Glossary | Defined | Migration 0001 ready | Same — YAML fallback |
| Business Contexts | 2 demo contexts | Migration 0006 **ACTIVE** | Supabase (REST API via SUPABASE_URL) |

**Blocking issue**: `.env` has all backends set to `supabase` but missing `SUPABASE_DB_URL=postgresql://postgres:postgres@127.0.0.1:54322/postgres`. Only Business Contexts works because it uses REST API (`SUPABASE_URL`), not Postgres DSN. `load_dotenv()` was added to bootstrap.py (fixed).

### Data Products and Contracts

**Configured data products**: 9 registered (Finance, HR, Sales domains)
- **FI Star Schema** (dp_fi_20250516_001): Finance star schema with 25 KPIs, DuckDB source
- **GL Accounts** (dp_fi_20250516_002): General ledger master data
- **Employee Headcount/Performance/Personal** (3 HR products): SAP HR data
- **Sales Orders/Order Items** (2 products): BigQuery source, project `agent9-465818`, dataset `SalesOrders`

**12 contract YAML files** in `src/contracts/` — auto-generated by Data Product Agent during onboarding

**BigQuery integration**: BigQueryManager (334 lines), service account auth via `GOOGLE_APPLICATION_CREDENTIALS`, connection profile "Google BigQuery" configured

### Workflow Definitions (10 Defined, 3 Fully Implemented)

| Workflow | Implementation Status |
|----------|---------------------|
| Automated Situational Awareness | **Fully implemented** — SA Agent + orchestrator |
| Problem Deep Analysis | **Fully implemented** — DA Agent + orchestrator |
| Solution Finding | **Fully implemented** — SF Agent + orchestrator |
| Data Product Onboarding | **Fully implemented** — 8-step orchestrator method |
| Opportunity Deep Analysis | Defined in YAML — core agents exist |
| Solution Deployment | Defined — references unbuilt agents (QA, Change Mgmt) |
| Value Assurance | Defined — post-deployment review |
| Business Optimization | Defined — references unbuilt agents |
| Agent9 Environment Administration | Defined — enterprise admin scope |
| Innovation Driver | Defined — references unbuilt agents |

### Connection Profiles

**Configured in `src/config/connection_profiles.yaml`**: Currently empty (profiles created via UI are stored at runtime)
**Supported system types**: DuckDB, PostgreSQL, BigQuery, Snowflake, Redshift, Other
**BigQuery profile**: Project `agent9-465818`, Dataset `SalesOrders`, service account credentials

### What's NOT Built Yet

- **KPI Assistant Streamlit UI** — API routes exist but no Decision Studio panel
- **13+ agents referenced in workflow YAMLs** not implemented: Business Optimization, Market Analysis, Risk Management, Stakeholder Analysis/Engagement, Opportunity Analysis, QA, Change Management, Solution Architect, GenAI Expert, Implementation Planner, Innovation, UI Design
- **Registry Maintenance UI** — placeholder in Admin Console
- **Data Governance Admin UI** — placeholder in Admin Console
- **Supabase activation for 5 registries** — migrations ready, `SUPABASE_DB_URL` missing from `.env`
- **Hierarchical business processes** — MVP uses domain-level only
- **A9_SharedLogger** — documented in PRDs but never implemented; all agents use `logging.getLogger(__name__)`

## Technology Stack

**Backend:**
- Language: Python 3.x
- Framework: Custom agent-based architecture (async/await patterns)
- Database: DuckDB (local development), Cloud database (production)
- Data Validation: Pydantic models
- Protocol: A2A (Agent-to-Agent) protocol with standardized I/O

**Frontend/UI:**
- Framework: Streamlit (Decision Studio)
- State Management: Streamlit session state
- Visualization: Custom components for situation cards, workflows

**Multi-Agent Infrastructure:**
- Agent Framework: Custom orchestrator-driven architecture
- Registry System: YAML-based registries (Agent, KPI, Principal, Data Product, Business Process)
- LLM Integration: A9_LLM_Service_Agent (model routing and management)
- Agent Communication: Protocol-driven with Pydantic models
- Data Integration: SAP DataSphere via Data Product MCP Service

## Architecture

### CRITICAL PROTOCOL REQUIREMENTS (from PRDs)

**These are NON-NEGOTIABLE requirements documented in every agent PRD:**

1. **Agent Instantiation** 🔴 MANDATORY
   - ❌ NEVER: `agent = AgentClass(config)`
   - ✅ ALWAYS: `agent = await AgentRegistry.get_agent("Agent_Name")`
   - ✅ OR: `agent = await AgentClass.create_from_registry(config)`
   - **Every single agent PRD states this**

2. **Pydantic Models Only** 🔴 MANDATORY  
   - ALL agent I/O must use Pydantic models
   - NO raw dicts or lists in agent-to-agent communication
   - NO raw dicts in tests (tests must use Pydantic instances)
   - This is the A2A (Agent-to-Agent) protocol

3. **LLM Call Routing** 🔴 MANDATORY
   - ALL LLM calls MUST go through A9_LLM_Service_Agent
   - ALL LLM calls MUST be routed through Orchestrator
   - NO direct LLM API calls (OpenAI, Anthropic, etc.)
   - **Single point of failure to check**

4. **Logging Standard** 🔴 MANDATORY
   - Use `A9_SharedLogger` exclusively
   - NO print statements
   - NO direct logging module usage

5. **Lifecycle Methods** 🔴 MANDATORY
   - Implement: `create()`, `connect()`, `disconnect()`
   - All async operations
   - Dependencies resolved before `connect()`

**See AGENT_SPECIFICATIONS.md for complete PRD-based requirements**

### Core Architectural Principles (INTENDED DESIGN)

1. **Protocol-Driven Design**: All agent interactions MUST follow well-defined protocols with standardized Pydantic input/output models
2. **Registry-Based Component Management**: Agents, KPIs, data products, and principal profiles managed through dedicated YAML registries
3. **Orchestrator-Driven Workflows**: A9_Orchestrator_Agent coordinates ALL multi-step workflows and agent lifecycle
4. **Card-Based Agent Configuration**: Agents configured and registered using standardized agent cards
5. **Asynchronous Processing**: Core workflows support async/await for improved performance

### Agent System Design

**Documented Agent Dependencies** (from PRDs):
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

**Core Workflow Agents:**
1. **A9_Orchestrator_Agent** - Central coordinator
   - Manages multi-step workflows
   - Handles agent registration and lifecycle
   - Validates workflow protocols
   - Tracks state and progress
   - Error handling and recovery
   - **Should manage agent dependencies and initialization order**

2. **A9_Principal_Context_Agent** - User context management
   - Principal profile management
   - Access control and permissions
   - Context-aware decision support
   - **Current issue: Uses role-based lookup, should use principal ID**
   - Business process provider initialization with fallback

3. **A9_Situation_Awareness_Agent** - Business situation detection
   - Monitors KPIs and thresholds
   - Detects anomalies and patterns
   - Prioritizes situations by impact
   - Domain-level business process matching

4. **A9_Deep_Analysis_Agent** - Detailed situation analysis
   - Root cause analysis
   - Impact assessment and trend analysis
   - Correlation detection

5. **A9_Solution_Finder_Agent** - Solution generation
   - Solution generation and evaluation
   - Implementation planning
   - Outcome prediction

**Supporting Agents:**
1. **A9_Data_Governance_Agent** - Data governance policies
   - Data access control
   - Data quality monitoring
   - Compliance validation
   - **Current issue: Not properly connected to Data Product Agent**

2. **A9_Data_Product_Agent** - Data product management
   - Data product registration and discovery
   - Schema validation and transformation
   - **Uses A9_Data_Product_MCP_Service_Agent for SQL execution**
   - **Should delegate view name resolution to Data Governance Agent**

3. **A9_NLP_Interface_Agent** - Natural language processing
   - Query parsing and intent recognition
   - Entity extraction and response generation

4. **A9_LLM_Service_Agent** - LLM interaction management
   - Prompt engineering
   - Context and response management
   - Model selection and routing

5. **A9_Data_Product_MCP_Service_Agent** - SQL execution service
   - SQL query execution against DuckDB
   - Properly initialized by Data Product Agent

### Registry Architecture

**Registries (YAML-based):**
1. **Agent Registry** - Agent lifecycle, configuration, discovery, events
2. **KPI Registry** - KPI definitions, thresholds, business process mapping
3. **Principal Profiles Registry** - User profiles, RBAC, preferences
4. **Data Product Registry** - Data product definitions, schemas, contracts
5. **Business Process Registry** - Domain-level business processes (simplified for MVP)

**Current MVP Implementation:**
- Business processes simplified to domain level (e.g., "Finance", "Operations")
- Future: Hierarchical structure (Domain → Process → Sub-Process → Activity)
- Registries use snake_case IDs consistently

### Agent Communication Patterns

**Intended Pattern:**
- Orchestrator-driven agent registration
- Agents discover each other through Orchestrator
- Protocol-based communication with Pydantic models
- Proper initialization sequence: Registry Factory → Orchestrator → Data Governance → Principal Context → Data Product → Situation Awareness

**Current Issues to Identify:**
- Direct agent-to-agent communication bypassing orchestrator
- Hardcoded agent references instead of registry lookup
- Missing dependency declarations
- Inconsistent initialization patterns

### Data Flow (INTENDED)

```
Principal Profile 
  → (contract-driven filters) → Orchestrator
  → (business process) → Data Governance Agent
  → (data product + filters) → Data Product Agent
  → (read contract with KPIs) → Situation Awareness Agent
  → (for each KPI) → NLP Interface Agent
  → Data Product Agent
  → Situation/Attention Card
```

### UI Architecture

**Decision Studio (Streamlit-based):**
- Workflow orchestration interface
- Situation monitoring and visualization
- Analysis and solution evaluation
- Configuration management
- **Current state: Uses domain-level business processes**
- **Has warnings during provider initialization (expected)**

## Coding Standards & Patterns

### Preferred Patterns (TARGET STATE - from architecture docs)

**Agent Lifecycle:**
- All agents MUST register with Agent Registry
- Agent creation via `create_from_registry` factory method
- Standard lifecycle: create → connect → process → disconnect
- Async initialization in `_async_init` method
- Proper dependency declaration and resolution

**Protocol Compliance:**
- All agent I/O uses Pydantic models
- Standard entrypoints: `check_access`, `process_request`
- Context propagation: `principal_context`, `situation_context`, `business_context`, `extra`
- Proper event logging at each step
- Consistent error handling patterns

**Registry Provider Patterns:**
- Providers loaded through Registry Factory
- YAML-based configuration files
- Explicit path specification for reliability
- Proper async `load()` method calls
- Caching for performance

**Agent Connection Patterns:**
- Agents get other agents through Orchestrator: `await orchestrator.get_agent("agent_name")`
- NOT through direct instantiation
- Fallback mechanisms for graceful degradation
- Proper logging of connection attempts

**Data Models:**
- Pydantic for all validation
- Consistent naming: PascalCase for classes, snake_case for fields
- Schema validation at runtime
- Support serialization/deserialization
- Include comprehensive documentation

### Known Anti-Patterns to IDENTIFY and FLAG

**Agent Initialization:**
- ❌ Hardcoded file paths (e.g., `C:\\Users\\barry\\...`)
- ❌ Direct agent instantiation instead of registry lookup
- ❌ Missing dependency declarations
- ❌ Initialization without proper async/await
- ❌ Creating providers without registering them
- ❌ Skipping the `connect()` lifecycle method

**Communication Patterns:**
- ❌ Direct agent-to-agent calls bypassing orchestrator
- ❌ Hardcoded agent references
- ❌ Missing context field propagation
- ❌ Non-Pydantic request/response models
- ❌ Inconsistent error handling

### Known Anti-Patterns to IDENTIFY and FLAG

**Agent Instantiation Violations** 🔴 CRITICAL:
- ❌ `agent = A9_Principal_Context_Agent(config)` - Direct instantiation
- ❌ `agent = AgentClass()` - No registry pattern
- ✅ `agent = await AgentRegistry.get_agent("agent_name")` - Correct
- ✅ `agent = await AgentClass.create_from_registry(config)` - Correct
- **Check every single agent creation in the codebase**

**LLM Call Violations** 🔴 CRITICAL:
- ❌ `openai.ChatCompletion.create(...)` - Direct API call
- ❌ `anthropic.messages.create(...)` - Direct API call
- ❌ Any import of `openai` or `anthropic` in agent files (except LLM Service Agent)
- ✅ `llm_service = await orchestrator.get_agent("llm_service")`
- ✅ `response = await llm_service.generate(request)` - Via service
- **Single most important architectural violation to catch**

**Pydantic Model Violations** 🔴 CRITICAL:
- ❌ `return {"status": "ok", "data": [...]}` - Raw dict
- ❌ `request = {"principal_id": "cfo_001"}` - Raw dict input
- ❌ Using dicts in test fixtures
- ✅ `return ResponseModel(status="ok", data=[...])` - Pydantic
- ✅ `request = RequestModel(principal_id="cfo_001")` - Pydantic
- **Affects protocol compliance across entire system**

**Agent Communication Violations** ⚠️ HIGH PRIORITY:
- ❌ `self.data_governance_agent = DataGovernanceAgent()` - Direct reference
- ❌ `from ..agents import SomeAgent; agent = SomeAgent()` - Import and instantiate
- ✅ `self.agent = await self.orchestrator.get_agent("agent_name")` - Via orchestrator
- **Check all inter-agent communication**

**Registry Access Violations** ⚠️ HIGH PRIORITY:
- ❌ `with open("kpi_registry.yaml") as f: data = yaml.load(f)` - Direct file access
- ❌ `KPIRegistry()` - Direct registry instantiation
- ✅ `provider = self.registry_factory.get_provider("kpi")` - Via factory
- ✅ `data = provider.get_all()` - Via provider

**Logging Violations** ℹ️ MEDIUM:
- ❌ `print("Debug message")` - Print statements
- ❌ `import logging; logger = logging.getLogger()` - Direct logging
- ✅ `self.logger.info("Message")` - A9_SharedLogger

**Business Process Handling:**
- ❌ Mixed formats (display names vs IDs vs snake_case)
- ❌ Case-sensitive comparisons
- ❌ Not supporting domain-level processes
- ❌ Hardcoded business process lists

**Registry Access:**
- ❌ Direct YAML file access instead of provider
- ❌ Not using Registry Factory
- ❌ Missing fallback mechanisms
- ❌ Synchronous loading of async resources

**Error Handling:**
- ❌ Silent failures without logging
- ❌ Catching Exception without specificity
- ❌ Not implementing graceful degradation
- ❌ Missing user-friendly error messages

### Naming Conventions (CURRENT)
- **Files**: snake_case for Python modules (e.g., `a9_orchestrator_agent.py`)
- **Classes**: PascalCase (e.g., `A9_Orchestrator_Agent`)
- **Functions/Methods**: snake_case (e.g., `get_principal_context`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_TIMEOUT`)
- **Agents**: A9_[Name]_Agent pattern (e.g., `A9_Principal_Context_Agent`)
- **Pydantic Models**: PascalCase with descriptive suffixes (e.g., `PrincipalProfileRequest`, `SituationAwarenessResponse`)

### Code Style Inconsistencies to IDENTIFY
Look for variations that suggest different "authoring eras":
- Different async/await patterns (callbacks vs async/await)
- Different error handling approaches (try/except vs error returns)
- Different logging patterns (print vs logger.info vs logger.debug)
- Different import organization styles
- Different docstring formats (Google vs NumPy vs missing)
- Different type hinting completeness (full vs partial vs none)
- Different Pydantic validation approaches (validators vs root_validators)

## Development Workflow

### Project Structure (Key Locations)

```
Agent9-HERMES/
├── src/
│   ├── agents/
│   │   └── new/                    # Core agent implementations
│   │       ├── a9_orchestrator_agent.py
│   │       ├── a9_principal_context_agent.py
│   │       ├── a9_situation_awareness_agent.py
│   │       ├── a9_deep_analysis_agent.py
│   │       ├── a9_solution_finder_agent.py
│   │       ├── a9_data_governance_agent.py
│   │       ├── a9_data_product_agent.py
│   │       ├── a9_nlp_interface_agent.py
│   │       ├── a9_llm_service_agent.py
│   │       └── a9_data_product_mcp_service_agent.py
│   ├── registry/
│   │   ├── factory.py              # Registry factory for provider management
│   │   ├── agent/                  # Agent registry
│   │   ├── kpi/                    # KPI registry (YAML)
│   │   ├── principal/              # Principal profiles (YAML)
│   │   ├── business_process/       # Business process registry (YAML)
│   │   ├── data_product/           # Data product registry (YAML)
│   │   └── providers/              # Registry provider implementations
│   ├── models/                     # Pydantic models
│   └── utils/                      # Shared utilities
├── docs/
│   └── architecture/               # Architecture documentation (this folder)
├── decision_studio.py              # Main Streamlit UI application
├── tests/                          # Test suites
└── requirements.txt                # Python dependencies
```

### Build & Run

```bash
# Install dependencies
pip install -r requirements.txt --break-system-packages

# Run Decision Studio (Streamlit UI)
streamlit run decision_studio.py

# Or use the restart script
.\restart_app.ps1  # Windows
./restart_app.sh   # Linux/Mac

# Run tests
pytest tests/

# Run specific agent test
pytest tests/test_orchestrator_agent.py -v
```

### Testing

- **Unit Tests**: Test individual agent methods
- **Integration Tests**: Test agent-to-agent communication
- **Protocol Tests**: Validate A2A protocol compliance
- **Workflow Tests**: End-to-end workflow execution
- **Note**: Test coverage varies by module age (identify gaps in Phase 3)

### Database

- **Development**: DuckDB (local file-based)
- **Production**: Cloud database (exact tech TBD - check actual deployment)
- **Location**: Database files typically in project root or data/ directory
- **Data Source**: SAP DataSphere integration via Data Product MCP Service

### Configuration

- Environment variables for sensitive config
- YAML files for registry data
- Agent cards for agent configuration
- **Issue**: Hardcoded paths exist that should be configurable

## Areas Requiring Review

### Phase 1: Architectural Consistency (PRIORITY)

**Focus Areas:**

1. **Agent Initialization & Lifecycle**
   - Are agents created via `create_from_registry` or direct instantiation?
   - Is the initialization sequence correct? (Registry Factory → Orchestrator → DG → PC → DP → SA)
   - Do agents properly implement lifecycle methods (create, connect, disconnect)?
   - Are dependencies declared and resolved properly?
   - Find all hardcoded file paths (especially `C:\\Users\\barry\\...`)

2. **Orchestrator-Driven vs Direct Communication**
   - Which agents get other agents through the orchestrator?
   - Which agents bypass the orchestrator with direct references?
   - Map all agent-to-agent communication patterns
   - Identify places where `orchestrator.get_agent()` should be used but isn't

3. **Registry Provider Initialization**
   - How many different patterns for initializing registry providers exist?
   - Are providers loaded through Registry Factory consistently?
   - Where are providers created with explicit paths vs factory lookup?
   - Document the fallback mechanism patterns (are they consistent?)

4. **Protocol Compliance**
   - Do all agent interactions use Pydantic models for I/O?
   - Are standard entrypoints (`check_access`, `process_request`) implemented consistently?
   - Is context properly propagated (`principal_context`, `situation_context`, etc.)?
   - Where is the A2A protocol bypassed?

5. **Business Process Handling**
   - How many different formats for business processes exist? (display names, IDs, snake_case, domain-level)
   - Where is case-sensitive comparison used inappropriately?
   - Which agents support domain-level business processes vs specific processes?
   - Document the inconsistencies between KPI Registry and Principal Registry

**Specific Known Issues to Validate:**
- Data Governance Agent not connected to Data Product Agent (see `data_governance_agent_connection.md`)
- Principal Context Agent uses role-based lookup instead of principal ID (see `principal_id_based_lookup_plan.md`)
- Business Process Provider initialization warnings (see `business_process_provider_initialization.md`)
- Registry provider replacement warnings during Decision Studio startup

**Questions to Answer:**
1. What are the 3-5 most common architectural patterns for agent initialization?
2. How many agents bypass the orchestrator for inter-agent communication?
3. Where does the actual implementation diverge most from the documented architecture?
4. Which architectural inconsistencies would break the system if not fixed?
5. Which are just technical debt vs actual bugs?

### Phase 2: Code Style Analysis

**Focus Areas:**

1. **Async/Await Patterns**
   - Pure async/await vs callback patterns vs mixed
   - Consistent use of `await` for async methods
   - Proper error handling in async contexts

2. **Error Handling Styles**
   - Try/except with specific exceptions vs broad Exception catching
   - Error logging patterns (logger.error vs logger.warning vs print)
   - Graceful degradation vs hard failures
   - User-facing error messages vs developer error messages

3. **Import Organization**
   - Standard library vs third-party vs local imports
   - Absolute vs relative imports
   - Import grouping and sorting patterns

4. **Logging Patterns**
   - logger.info vs logger.debug vs logger.warning vs print statements
   - Consistency in log message formats
   - Structured logging vs string formatting

5. **Documentation Styles**
   - Docstring formats (Google vs NumPy vs missing)
   - Type hint completeness
   - Inline comment patterns

6. **Pydantic Model Patterns**
   - Use of validators vs root_validators
   - Field definitions (Field() vs bare types)
   - Model inheritance patterns

**Questions to Answer:**
1. Can you identify 3-4 distinct "eras" of code based on style?
2. Which style is most prevalent (by line count)?
3. Which style is most aligned with modern Python best practices?
4. Are there correlation between style and file modification dates?
5. What are the quick wins for style unification?

### Phase 3: Dead Code Detection

**Focus Areas:**

1. **Unused Imports**
   - Imports that are never referenced in the file
   - Redundant imports (imported multiple ways)

2. **Unreachable Code**
   - Code after return statements
   - Code in unreachable branches
   - Functions/methods that are never called

3. **Deprecated Patterns**
   - Old agent initialization patterns that were replaced
   - Legacy registry access methods
   - Commented-out code blocks from refactors

4. **Unused Components**
   - Agent classes that are defined but never instantiated
   - Registry entries that are never queried
   - Workflow definitions that are never executed
   - UI components that are never imported

5. **Orphaned Files**
   - Python files with no imports from other files
   - YAML files not referenced in code
   - Test files for deleted components

**Questions to Answer:**
1. What percentage of the codebase appears to be dead code?
2. Are there entire agent implementations that can be removed?
3. Which registry entries are orphaned?
4. What's the estimated LOC reduction from dead code removal?
5. Are there patterns in where dead code accumulates (old feature branches, deprecated approaches)?

### Phase 4: Consolidation Planning

**Deliverables:**

1. **Architectural Unification Plan**
   - Steps to align all agent initialization with orchestrator-driven pattern
   - Migration path for direct agent communication to orchestrator-mediated
   - Registry provider initialization consolidation
   - Business process format standardization

2. **Code Style Unification Plan**
   - Target style guide (based on most prevalent + best practices)
   - Automated fixes (imports, formatting, simple patterns)
   - Manual review needed (complex logic, error handling)

3. **Dead Code Removal Plan**
   - Safe-to-remove (no references anywhere)
   - Verify-then-remove (low confidence, needs testing)
   - Deprecated-mark-for-removal (legacy fallbacks still in use)

4. **Prioritized Refactoring Roadmap**
   - P0 (Breaks documented architecture, causes bugs): Fix immediately
   - P1 (Technical debt, prevents clean evolution): Fix in next sprint
   - P2 (Style inconsistencies, code smell): Fix when touching the code
   - P3 (Dead code, minor issues): Fix in cleanup sprint

5. **Risk Assessment**
   - High-risk changes (core orchestration, agent lifecycle)
   - Medium-risk (data flow, registry access)
   - Low-risk (style, imports, dead code)
   - Estimated effort for each category

## Critical Areas (Handle with Care)

### Mission-Critical Agent Code
- `/src/agents/new/a9_orchestrator_agent.py` - Central coordinator, any changes affect all workflows
- `/src/agents/new/a9_principal_context_agent.py` - User context, affects security and access control
- `/src/agents/new/a9_data_governance_agent.py` - Data access policies, compliance critical
- `/src/registry/factory.py` - Registry initialization, affects system startup

### Stable Registry Files (Verify Before Modifying)
- `/src/registry/principal/principal_registry.yaml` - Principal profiles and permissions
- `/src/registry/kpi/kpi_registry.yaml` - KPI definitions and thresholds
- `/src/registry/business_process/business_process_registry.yaml` - Business process definitions
- `/src/registry/data_product/data_product_registry.yaml` - Data product contracts

### Integration Points (External Dependencies)
- SAP DataSphere integration code - Affects production data pipelines
- A9_Data_Product_MCP_Service_Agent - SQL execution, data access
- Any authentication/authorization modules

### Do Not Modify Without Explicit Permission
- Production database migration files
- Deployed agent cards in production registries
- Environment-specific configuration files

## Known Issues & Technical Debt

### Documented Architectural Issues

1. **Business Process Provider Initialization** ⚠️
   - Provider not found in registry factory on startup
   - Agent creates default provider with fallback mechanism
   - Generates expected warnings (not errors, but indicates initialization sequence issue)
   - Should be initialized by Orchestrator before agent creation

2. **Data Governance Agent Connection** ⚠️
   - Data Product Agent attempts to use Data Governance Agent
   - Connection never properly initialized
   - Missing in `_async_init` or `connect` method
   - Falls back to local resolution (works but bypasses governance)
   - Should follow MCP Service Agent connection pattern

3. **Principal ID vs Role-Based Lookup** 🔴 HIGH PRIORITY
   - Principal Context Agent uses role names as primary lookup keys
   - Should use principal IDs (`ceo_001`, `cfo_001`, etc.)
   - Current approach has case sensitivity issues
   - Doesn't support multiple roles per principal
   - Full migration plan documented in `principal_id_based_lookup_plan.md`

4. **Business Process Format Inconsistencies** ⚠️
   - Mixed formats across registries (display names, IDs, snake_case)
   - MVP uses simplified domain-level (e.g., "Finance")
   - Future design: Hierarchical (Domain → Process → Sub-Process → Activity)
   - KPI Registry and Principal Registry not fully aligned
   - Blueprint exists in `business_process_hierarchy_blueprint.md`

5. **Registry Provider Replacement Warnings** ℹ️
   - Multiple warnings about replacing existing providers
   - Indicates duplicate initialization or improper singleton pattern
   - Not breaking but indicates lifecycle management issues

6. **Hardcoded File Paths** 🔴
   - Absolute paths like `C:\\Users\\barry\\CascadeProjects\\...`
   - Should use relative paths or configuration-based paths
   - Breaks portability and deployment

7. **Agent Initialization Sequence** ⚠️
   - Correct sequence documented: Registry Factory → Orchestrator → DG → PC → DP → SA
   - Not consistently followed in all code paths
   - Decision Studio may initialize in different order
   - Dependencies not explicitly declared in all cases

### Expected Warnings (Not Errors)

These warnings are currently expected during startup:
```
WARNING:src.registry.factory:Provider 'business_process' not found in registry factory
WARNING:src.agents.new.a9_principal_context_agent.A9_Principal_Context_Agent:Business process provider not found, creating default provider
WARNING:src.registry.factory:Provider 'business_process' exists but may not be properly initialized
WARNING:src.agents.new.a9_data_product_agent:Data Governance Agent not available for view name resolution
WARNING:src.registry.factory:Replacing existing kpi provider with new instance
WARNING:src.registry.factory:Replacing existing principal_profile provider with new instance
WARNING:src.registry.factory:Replacing existing data_product provider with new instance
WARNING:src.registry.factory:Replacing existing business_glossary provider with new instance
```

These indicate initialization sequence issues but have fallback mechanisms in place.

### Test Coverage Gaps

- [ ] Protocol compliance testing inconsistent
- [ ] Agent dependency resolution not fully tested
- [ ] Registry provider lifecycle not comprehensively tested
- [ ] Multi-agent workflow integration tests vary by module age
- [ ] Performance testing for large-scale operations missing

## Dependencies & Integrations

### Core Python Dependencies
- **Pydantic**: Data validation and settings management (all models)
- **Streamlit**: Decision Studio UI framework
- **DuckDB**: Local database for development
- **asyncio**: Async/await support for agent operations
- **PyYAML**: Registry file parsing
- **Logging**: Standard Python logging throughout

### External Services

**SAP DataSphere Integration:**
- Primary data source for business KPIs
- Data product mapping and extraction
- Analytical model integration
- Accessed via A9_Data_Product_MCP_Service_Agent

**LLM Services:**
- Managed through A9_LLM_Service_Agent
- Multiple model support and routing
- Context management and prompt engineering

### Internal Dependencies

**Agent Dependencies (Documented):**
```
A9_Orchestrator_Agent (no dependencies)
├── A9_Data_Governance_Agent (no dependencies)
├── A9_Principal_Context_Agent (no dependencies)
├── A9_Data_Product_Agent
│   ├── requires: A9_Data_Governance_Agent (view name resolution)
│   └── requires: A9_Data_Product_MCP_Service_Agent (SQL execution)
└── A9_Situation_Awareness_Agent
    ├── requires: A9_Data_Product_Agent (KPI data)
    └── requires: A9_Principal_Context_Agent (principal context)
```

**Registry Providers:**
- KPI Provider (loads kpi_registry.yaml)
- Principal Provider (loads principal_registry.yaml)  
- Business Process Provider (loads business_process_registry.yaml)
- Data Product Provider (loads data_product_registry.yaml)
- Agent Provider (manages agent registry)

### Key Integration Points

1. **SAP DataSphere ↔ Data Product Agent**
   - Via MCP Service Agent
   - SQL query execution
   - Data product contract validation

2. **Registry Files ↔ Registry Providers**
   - YAML parsing and validation
   - Provider initialization through Registry Factory
   - Caching for performance

3. **Agents ↔ Orchestrator**
   - Agent registration and discovery
   - Workflow coordination
   - Lifecycle management (create, connect, disconnect)

4. **Decision Studio ↔ Agents**
   - Streamlit UI for workflow triggering
   - Session state management
   - Real-time situation monitoring

## Review Session Guidelines

### For Claude Code Reviewers

When reviewing this codebase, keep in mind:

**Context:**
- 10 months of development with multiple AI models
- Several architectural refactors along the way
- Protocol-driven design that may not be fully implemented everywhere
- Registry-based system where the intended vs actual patterns may diverge
- Production system with real SAP DataSphere integration

**Review Approach:**

1. **Start with Architectural Understanding (Phase 1 First)**
   - Read the agent initialization code in orchestrator and agents
   - Map actual communication patterns vs documented orchestrator-driven pattern
   - Identify where implementation diverges from documented architecture
   - DO NOT suggest changes yet - just document patterns

2. **Look for Patterns, Not Just Individual Issues**
   - Don't flag every missing docstring - identify if there's a systemic documentation issue
   - Don't flag every hardcoded path - identify if this is a pattern or isolated
   - Group findings by architectural pattern rather than by file

3. **Consider Refactor History**
   - Code style changes likely indicate refactor boundaries
   - Older code may use different patterns (not wrong, just different era)
   - Some "anti-patterns" may be intentional fallbacks from refactors

4. **Prioritize by Architectural Impact**
   - Agent initialization sequence issues > style inconsistencies
   - Protocol violations > naming conventions
   - Missing dependencies > missing docstrings
   - Data governance bypasses > import ordering

5. **Provide Migration Paths, Not Just Critique**
   - For each major pattern inconsistency, suggest how to migrate
   - Consider the effort: some fixes are 1-line, others are multi-day refactors
   - Acknowledge when fallback mechanisms are working (even if not ideal)

6. **Be Specific with Evidence**
   - Always provide file paths and line numbers
   - Show the pattern you found, don't just describe it
   - For inconsistencies, show examples of both patterns

7. **Respect the Documented Architecture**
   - The architecture docs represent the INTENDED design
   - Deviations from this design should be flagged
   - But understand some deviations may be pragmatic workarounds

8. **Understand the Business Context**
   - This is a business insights system with KPIs, situations, and solutions
   - Business process alignment is critical
   - Data governance is not optional - it's compliance-related

### Review Output Format

For each finding, provide:

```markdown
**Location**: `src/agents/new/example_agent.py:145-167`

**Category**: Architecture | Style | Dead Code | Performance | Security | Protocol

**Severity**: 
- 🔴 Critical (Breaks documented architecture or causes bugs)
- ⚠️ High (Significant technical debt, prevents clean evolution)
- ℹ️ Medium (Code smell, inconsistency, but system works)
- 💡 Low (Nice-to-have improvement)

**Issue**: 
[What's wrong or inconsistent - be specific]

**Evidence**:
```python
# Show the actual code
```

**Impact**: 
[Why this matters - business impact, technical impact, or maintainability impact]

**Pattern Analysis**:
- Found in: [List other locations with same pattern]
- Affects: [Which agents/components]
- Introduced: [If you can tell from code style/comments when this pattern emerged]

**Recommendation**: 
[Specific fix or consolidation approach - include code example if helpful]

**Migration Path**:
1. [Step-by-step approach]
2. [Consider dependencies]
3. [Testing approach]

**Effort Estimate**: 
- Quick fix (< 1 hour)
- Moderate (1-4 hours)
- Significant (1-2 days)
- Major refactor (> 2 days)

**Risk Level**:
- Low (Safe to change, well-tested area)
- Medium (Needs testing, some coupling)
- High (Core system, many dependencies)
```

### Phase-Specific Guidelines

**Phase 1 - Architectural Review:**
- Focus on agent lifecycle and communication patterns
- Map actual vs intended architecture
- Identify systemic issues, not individual bugs
- Output: Architectural pattern report with specific examples

**Phase 2 - Style Analysis:**
- Look for coding style "fingerprints" that indicate different authors/eras
- Don't just list style violations - identify patterns
- Suggest the target style based on prevalence + best practices
- Output: Style analysis with "eras" identified and unification recommendations

**Phase 3 - Dead Code Detection:**
- Be conservative - flag only high-confidence dead code
- Check for references in strings, dynamic imports, registry references
- Consider test code separately from production code
- Output: Dead code inventory with confidence levels

**Phase 4 - Consolidation Planning:**
- Synthesize findings from Phases 1-3
- Create actionable roadmap with priorities
- Estimate effort realistically (this is a 100K LOC project)
- Output: Prioritized refactoring plan with effort and risk estimates

## Questions for Initial Review (Calibration Phase)

Before diving deep into the 4-phase review, answer these to calibrate your understanding:

### Architectural Understanding

1. **Agent Initialization Patterns**
   - What are the 3-5 different patterns for agent initialization you observe?
   - How many agents use `create_from_registry` vs direct instantiation?
   - Which agents follow the documented initialization sequence?
   - Where are Registry Factory providers initialized?

2. **Agent Communication Patterns**
   - How many agents get other agents through `orchestrator.get_agent()`?
   - How many agents have direct references to other agents?
   - Map the actual agent dependency graph vs the documented one
   - Which agents properly implement the `connect()` lifecycle method?

3. **Protocol Compliance**
   - What percentage of agent interactions use Pydantic models?
   - Are there agents that bypass the A2A protocol?
   - How consistently are context fields (`principal_context`, etc.) propagated?

4. **Registry Access Patterns**
   - How many different ways are registries accessed?
   - Which code uses Registry Factory vs direct YAML loading?
   - Where are providers properly initialized vs fallback patterns?

### Code Style Analysis

5. **Style Eras**
   - Can you identify 3-4 distinct "eras" of code based on style?
   - What are the key differentiators (async patterns, error handling, imports)?
   - Which style is most prevalent by line count?
   - Do file modification times correlate with style changes?

6. **Async/Await Evolution**
   - What patterns exist: pure async/await, callbacks, mixed?
   - Where are `await` keywords missing for async methods?
   - Are there synchronous calls to async functions?

### Dead Code Assessment

7. **Unused Code Volume**
   - Rough estimate: what percentage appears to be dead code?
   - Are there entire agent implementations that aren't used?
   - How many registry entries (agents, KPIs, principals) are orphaned?
   - Are there whole Python files with no imports from other files?

### Quick Wins Identification

8. **Low-Hanging Fruit**
   - What are the top 5 quick wins (< 1 hour each)?
   - Which style inconsistencies could be auto-fixed?
   - Which imports could be cleaned up automatically?
   - Where could simple constants replace hardcoded values?

### Risk Assessment

9. **High-Risk Areas**
   - Which architectural issues could cause production bugs?
   - Where is the documented design most severely violated?
   - Which agents have the most dependencies on them?
   - Where would refactoring have the highest ripple effect?

### Specific Known Issues Validation

10. **Documented Issues**
    - Confirm: Is Data Governance Agent connected to Data Product Agent?
    - Confirm: Does Principal Context Agent use role-based or ID-based lookup?
    - Confirm: Are business processes in consistent format across registries?
    - Confirm: How many hardcoded file paths exist?
    - Confirm: What's the actual initialization sequence in Decision Studio?

### Summary Questions

11. **Overall Assessment**
    - If you had to describe the codebase's "evolutionary history" in 3 paragraphs, what would you say?
    - What's the single biggest architectural inconsistency by impact?
    - What's the single biggest source of technical debt by volume?
    - If you could wave a magic wand and fix one thing, what would it be?
    - On a scale of 1-10, how far is the implementation from the documented architecture?

## Success Metrics

The review will be considered successful when:

1. ✅ All major architectural patterns are documented with evidence
2. ✅ Code style "eras" are identified with differentiating characteristics  
3. ✅ Dead code is inventoried with confidence levels
4. ✅ A prioritized refactoring roadmap exists with effort estimates
5. ✅ Quick wins are identified for immediate action
6. ✅ High-risk areas are clearly flagged
7. ✅ Migration paths are provided for major architectural changes
8. ✅ The review helps decide: refactor incrementally or rewrite subsystems?

---

## Architecture Documentation References

The following architecture documents provide detailed context for this review:

### Core Architecture Documents
1. **Agent9_Architecture_Overview.md** - Complete system architecture, principles, and components
2. **orchestration_architecture.md** - Orchestrator-driven design principles and workflow execution
3. **orchestrator_implementation.md** - Detailed orchestrator implementation with dependency resolution
4. **core_workflow_diagram.md** - Visual workflow diagrams and agent interaction sequences

### Agent PRD Documents (Specifications)
10 agent PRD documents define the INTENDED behavior and protocol requirements:
- **a9_orchestrator_agent_prd.md** - Central coordinator, agent lifecycle, dependency resolution
- **a9_principal_context_agent_prd.md** - Principal profiles, access control, decision style mapping
- **a9_data_governance_agent_prd.md** - Data governance policies, compliance, audit trails
- **a9_data_product_agent_prd.md** - Data product management, SQL execution delegation
- **a9_situation_awareness_agent_prd.md** - KPI monitoring, anomaly detection, situation generation
- **a9_deep_analysis_agent_prd.md** - Root cause analysis, impact assessment
- **a9_solution_finder_agent_prd.md** - Solution generation, trade-off analysis
- **a9_llm_service_prd.md** - Centralized LLM operations, provider abstraction, SQL generation
- **a9_nlp_interface_agent_prd.md** - Natural language processing interface
- **a9_kpi_assistant_agent_prd.md** - LLM-powered KPI definition, strategic metadata

**See AGENT_SPECIFICATIONS.md for extracted PRD requirements and protocol violations to check**

### Technical Debt and Known Issues
5. **business_process_alignment_summary.md** - Business process registry alignment work
6. **business_process_hierarchy_blueprint.md** - Future hierarchical business process design
7. **business_process_provider_initialization.md** - Provider initialization patterns and issues
8. **data_governance_agent_connection.md** - Missing connection pattern between DG and DP agents
9. **principal_id_based_lookup_plan.md** - Migration plan from role-based to ID-based lookup
10. **registry_display_ui_updates.md** - Decision Studio UI updates for business processes
11. **registry_explorer_updates.md** - Registry explorer tool enhancements

All architecture docs: `C:\Users\barry\CascadeProjects\Agent9-HERMES\docs\architecture\`
All agent PRDs: `C:\Users\barry\CascadeProjects\Agent9-HERMES\docs\prd\agents\`

## Notes for Future Sessions

### Session History
- [Initial Creation]: Comprehensive CLAUDE.md created from architecture documentation
- [Next]: Phase 1 Architectural Review - Agent initialization and communication patterns

### Key Patterns to Watch For
- Agent initialization: `create_from_registry` vs direct instantiation
- Inter-agent communication: orchestrator-mediated vs direct
- Registry access: Factory pattern vs direct YAML loading
- Error handling: try/except patterns and logging
- Async patterns: proper await usage
- Business process formats: domain-level vs hierarchical vs mixed

### Refactoring Progress Tracking
- [ ] Phase 1: Architectural pattern analysis
- [ ] Phase 2: Code style era identification  
- [ ] Phase 3: Dead code inventory
- [ ] Phase 4: Consolidation roadmap

### Important Reminders
- This is a 10-month, multi-model development - expect significant pattern variation
- The architecture docs represent INTENDED design - reality may differ
- Fallback mechanisms exist for many issues - they work but indicate tech debt
- SAP DataSphere integration is production-critical
- Principal context and data governance have compliance implications
