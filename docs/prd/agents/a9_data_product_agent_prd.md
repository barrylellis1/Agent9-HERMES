# A9_Data_Product_Agent Product Requirements Document

<!-- 
CANONICAL PRD DOCUMENT
Last updated: 2026-04-07
MCP-first architecture locked; multi-warehouse SaaS connectivity
-->

## 1. Overview

### 1.1 Purpose

The A9_Data_Product_Agent (DPA) is Decision Studio's universal data access layer. It connects to enterprise clients' existing data warehouses (Snowflake, BigQuery, Databricks, SAP HANA, PostgreSQL) without requiring custom connector development per client. DPA manages the lifecycle of data products, schema inspection, KPI time-series queries, and contract-driven governance.

### 1.2 Design Philosophy

**MCP-first external connectivity.** Decision Studio uses vendor-provided MCP (Model Context Protocol) servers for external warehouses, eliminating the need for per-client Python connectors and full SQL dialect translators. Vendors maintain the MCP server; Decision Studio maintains connection profiles and thin query dialect adapters.

**Three-tier execution model:**
- **Tier 1 (MCP):** External warehouses (Snowflake, Databricks, SAP Datasphere, HANA, PostgreSQL) → via vendor MCP servers
- **Tier 2 (Direct SDK):** BigQuery → via google-cloud-bigquery SDK (mature SDK, no MCP server needed)
- **Tier 3 (Embedded):** DuckDB → in-process, no external connection

### 1.3 Scope

This document covers:
- Multi-tenant connection profile resolution
- Three-tier execution router
- QueryDialect abstraction for SQL syntax differences
- Schema inspection adapters (DuckDB, BigQuery; Snowflake/Databricks/HANA follow on first client onboarding)
- KPI time-series query entrypoint (`get_kpi_monthly_series`)
- Data product discovery and contract management
- LLM-assisted KPI definition workflow (API-only, no UI)
- Error handling and governance integration

## 2. Business Requirements

### 2.1 Multi-Tenant SaaS Data Connectivity

Decision Studio targets enterprise clients ($200M–$2B revenue) who operate multiple data warehouses:
- Snowflake (most common for analytics)
- BigQuery (Google Cloud native)
- Databricks (lakehouse, Unity Catalog)
- SAP HANA / SAP Datasphere (ERP-integrated)
- PostgreSQL (legacy OLTP systems)

**Requirement:** Connection must work without custom integration work per client. Each client provides:
- Connection profile YAML with warehouse credentials (via env vars, never in code)
- Dataset/schema name
- Optional date column for time-series defaults

DPA resolves the profile, routes execution to the correct tier (MCP/SDK/embedded), and normalises the response. No Python connector or SQL translator per client.

### 2.2 Key Metrics

- Query execution latency: < 2 seconds (Tier 1 MCP; Tier 2/3 < 500ms)
- Schema inspection latency: < 5 seconds per table (via MCP or SDK)
- Connection profile resolution: < 100ms (Supabase registry lookup)
- KPI monthly series: 9 months of data in < 1 second
- Uptime: 99.5% (MCP endpoint availability varies by vendor)

## 3. Functional Requirements

### 3.1 Data Connectivity & Execution

#### 3.1.1 Connection Profile Resolution

Each client provides a `connection_profile` in the Supabase registry or via API request:

```yaml
connection_profile:
  source_system: snowflake              # snowflake | databricks | bigquery | hana | datasphere | duckdb | postgres
  connectivity_type: mcp                # mcp | direct_bq | direct_duckdb
  mcp_endpoint: https://mcp.customer.com  # MCP server endpoint (MCP type only)
  mcp_auth_type: bearer                 # bearer | api_key | oauth2
  mcp_api_key_env: CUSTOMER_MCP_KEY    # env var name; credentials never in YAML
  dataset: FINANCE_SCHEMA               # schema/dataset/database name
  date_column: transaction_date         # default date column for time-series
```

**Validation rules:**
- `connectivity_type` must match `source_system`:
  - `snowflake/databricks/postgres/hana/datasphere` → `mcp`
  - `bigquery` → `direct_bq`
  - `duckdb` → `direct_duckdb`
- If `mcp` type, `mcp_endpoint` and `mcp_api_key_env` are required
- `dataset` is required
- Credentials are resolved from environment variables, never hardcoded in YAML

#### 3.1.2 Execution Router (Three-Tier Model)

DPA routes queries based on `connectivity_type`:

| Tier | Source Systems | Execution Method | Vendor Responsibility | Decision Studio Responsibility |
|---|---|---|---|---|
| **MCP** | Snowflake, Databricks, PostgreSQL, HANA, SAP Datasphere | HTTP POST to MCP endpoint | Connection pooling, auth, SQL dialect, query execution | Connection profile, MCP server discovery, response normalization |
| **Direct SDK** | BigQuery | google-cloud-bigquery SDK | Managed service, auth via GCP credentials | Service account resolution, query construction |
| **Embedded** | DuckDB | In-process execution (duckdb library) | N/A | All execution and schema inspection |

**Routing logic:**
```python
if connectivity_type == "mcp":
    result = await mcp_execute(mcp_endpoint, query_params)
elif connectivity_type == "direct_bq":
    result = await bigquery_execute(query, credentials)
elif connectivity_type == "direct_duckdb":
    result = duckdb.execute(query)
```

#### 3.1.3 QueryDialect Layer

QueryDialect is a thin SQL syntax abstraction (~50 lines per dialect) for time-aware query building. It is **not** a database connector; MCP/SDK handles connectivity. QueryDialect only handles date/time function syntax differences.

**Supported dialects:**

| Dialect | Date Function Example | Usage |
|---|---|---|
| `BigQueryDialect` | `FORMAT_DATE('%Y-%m', col)` | BigQuery SDK execution |
| `DuckDBDialect` | `strftime('%Y-%m', col)` | Embedded DuckDB execution |
| `SnowflakeDialect` | `TO_CHAR(DATE_TRUNC('month', col), 'YYYY-MM')` | Snowflake MCP (Phase 10C) |
| `DatabricksDialect` | `DATE_FORMAT(date_trunc('month', col), 'yyyy-MM')` | Databricks MCP (Phase 10C) |
| `HanaDialect` | `TO_VARCHAR(col, 'YYYY-MM')` | SAP HANA MCP (Phase 10C) |
| `DatasphereDialect` | `TO_VARCHAR(col, 'YYYY-MM')` | SAP Datasphere MCP (Phase 10C) |
| `PostgresDialect` | `TO_CHAR(DATE_TRUNC('month', col), 'YYYY-MM')` | PostgreSQL MCP (Phase 10C) |

**Lifecycle:**
- Dialects are added in `src/database/dialects/`
- New dialect = new file (~50 lines) + entry in `DialectFactory`
- No changes to core DPA code required

#### 3.1.4 Data Product Discovery & Matching

DPA leverages the Unified Registry Access Layer to discover data products:
- Map business processes and KPIs to relevant data products
- Use the Data Product Provider to find data products by attribute, domain, or business process
- Support both legacy enum-based discovery and registry-based discovery

#### 3.1.5 KPI Time-Series Queries

**Entrypoint:** `get_kpi_monthly_series(kpi_definition, timeframe, num_months=9)`

This is the canonical entry point for all trend data used by SA and other agents. DPA:
1. Resolves the KPI's data product
2. Looks up the connection profile for that data product
3. Selects the appropriate QueryDialect
4. Constructs SQL using dialect to build time-series grouping
5. Routes query to correct tier (MCP/SDK/embedded)
6. Normalises response: `{"columns": [...], "rows": [...], "row_count": int}`

**Response format (all tiers):**
```python
{
  "columns": ["period", "value"],
  "rows": [
    ["2025-10", 1250000],
    ["2025-09", 1180000],
    ...
  ],
  "row_count": 9
}
```

**SA agent (caller) responsibilities:** None. SA calls one method and never touches SQL, backend detection, or dialects.

#### 3.1.6 Data Product Onboarding

Multi-step workflow for registering a new data warehouse with Decision Studio:

1. **Connection Validation** — test credentials, list datasets
2. **Schema Inspection** — enumerate tables/views, profile columns (via MCP or SDK)
3. **Metadata Analysis** — semantic tag detection (measure, dimension, time, identifier)
4. **Contract Generation** — YAML with table definitions, KPI proposals
5. **KPI & Governance Assistant** — LLM-powered refinement (optional)
6. **Registry Activation** — persist metadata, trigger governance mapping

**Schema Inspection Adapters (three-tier):**
- **DuckDB adapter:** Native INFORMATION_SCHEMA query
- **BigQuery adapter:** google-cloud-bigquery TableSchema API + INFORMATION_SCHEMA
- **MCP adapters (Snowflake/Databricks/HANA):** MCP server's INFORMATION_SCHEMA access

Each adapter returns normalized `TableProfile`:
```python
{
  "table_name": "TRANSACTIONS",
  "row_count": 5000000,
  "columns": [
    {"name": "DATE", "type": "DATE", "semantic_tags": ["time"]},
    {"name": "AMOUNT", "type": "DECIMAL", "semantic_tags": ["measure"]},
    {"name": "PRODUCT_ID", "type": "STRING", "semantic_tags": ["dimension", "identifier"]}
  ]
}
```

#### 3.1.7 LLM-Assisted KPI Definition Workflow (API-Only)

Interactive LLM-powered chat during onboarding to define comprehensive KPIs with all required registry attributes.

**API Endpoints:**

| Endpoint | Input | Output |
|---|---|---|
| `POST /api/v1/data-product-onboarding/kpi-assistant/suggest` | `{ data_product_id, schema_metadata, user_context }` | `{ suggested_kpis: [...], conversation_id }` |
| `POST /api/v1/data-product-onboarding/kpi-assistant/chat` | `{ conversation_id, message, current_kpis }` | `{ response, updated_kpis, actions }` |
| `POST /api/v1/data-product-onboarding/kpi-assistant/validate` | `{ kpi_definition, schema_metadata }` | `{ valid, errors, warnings }` |
| `POST /api/v1/data-product-onboarding/kpi-assistant/finalize` | `{ data_product_id, kpis }` | `{ updated_contract_yaml, registry_updates }` |

**Core Capabilities:**

1. **Auto-Suggestion Engine** — Analyze schema (columns, semantic tags) to suggest 3-7 business KPIs
2. **Interactive Refinement** — Accept NL requests to customize KPI attributes (thresholds, comparison types, dimensions, owners)
3. **Attribute Generation** — For each KPI, generate all required registry attributes:
   - Core: id, name, domain, description, unit, data_product_id
   - Calculation: sql_query, filters
   - Thresholds: comparison_type, green/yellow/red, inverse_logic
   - Governance: business_process_ids, tags, owner_role, stakeholder_roles
   - Strategic Metadata: line, altitude, profit_driver_type, lens_affinity

**Strategic Metadata Tags:**

- **line:** top_line (revenue) | middle_line (efficiency) | bottom_line (cost control)
- **altitude:** strategic (C-suite) | tactical (department) | operational (day-to-day)
- **profit_driver_type:** revenue | expense | efficiency | risk
- **lens_affinity:** bcg | bain | mckinsey (consulting persona routing in Solution Finder)

### 3.2 Error Handling

**Error Response Format (all methods):**
```python
{
  "status": "error" | "partial_error" | "success",
  "error": "Detailed error message",
  "timestamp": "ISO format",
  "method": "calling_method_name"
}
```

**Error Types:**
- `ConfigurationError` — Invalid connection profile or credentials
- `RegistrationError` — Failed to register with registry
- `ProcessingError` — Query execution or schema inspection failure
- `ValidationError` — Invalid input (e.g., KPI definition missing required field)
- `ConnectionError` — MCP endpoint unreachable, BigQuery auth failure, DuckDB file not found
- `TimeoutError` — Query execution exceeded timeout
- `NotFoundError` — Data product, connection profile, or table not found

### 3.3 Configuration Management

**DPA Configuration:**

| Setting | Purpose | Default | Required |
|---|---|---|---|
| `mcp_timeout_ms` | HTTP timeout for MCP calls | 30000 | No |
| `bigquery_timeout_sec` | BigQuery SDK timeout | 60 | No |
| `duckdb_memory_limit` | DuckDB in-memory size | 4GB | No |
| `validate_sql` | Enforce SELECT-only pre-checks | true | No |
| `log_queries` | Log query headers (redact parameters) | false | No |

**Connection Profile Validation:**
- `source_system` must be supported (snowflake, databricks, bigquery, hana, datasphere, duckdb, postgres)
- `connectivity_type` must match `source_system`
- MCP profiles must have `mcp_endpoint` and `mcp_api_key_env`
- DuckDB profiles must have valid file path
- BigQuery profiles must have valid GCP project ID

## 4. Technical Architecture

### 4.1 Module Structure

```
src/agents/new/
├── a9_data_product_agent.py     # Main agent implementation
└── models/
    └── data_product_models.py   # Pydantic models

src/database/
├── managers/
│   ├── database_manager.py      # Abstract base
│   ├── duckdb_manager.py        # Tier 3
│   └── bigquery_manager.py      # Tier 2
├── dialects/
│   ├── base_dialect.py
│   ├── bigquery_dialect.py
│   ├── duckdb_dialect.py
│   ├── snowflake_dialect.py     # Phase 10C stub
│   └── ... (others)
└── factory.py                   # DialectFactory, DatabaseManagerFactory

src/registry/
└── connection_profiles/         # YAML-backed registry of connection profiles
```

### 4.2 Protocol Compliance

**Agent Lifecycle:**
- Instantiation: `await AgentRegistry.get_agent("a9_data_product_agent")`
- Never: `agent = A9_Data_Product_Agent(config)` (direct instantiation forbidden)
- I/O: Pydantic models only (no raw dicts in agent-to-agent communication)

**Logging:**
- No `print()` statements; use `logging.getLogger(__name__)`
- All LLM calls route through A9_LLM_Service_Agent
- Async/await for all I/O operations

### 4.3 Integration Points

- **Orchestrator:** Dependency resolution, agent instantiation
- **Principal Context Agent:** Principal/role resolution for query filtering
- **Data Governance Agent:** Business term translation, KPI validation
- **LLM Service Agent:** SQL generation (DA/SF agents), KPI suggestions, conversational responses
- **Registry Factory:** Connection profile lookup, data product metadata
- **Supabase:** Registry persistence (connection profiles, data products, KPIs)

## 5. Implementation Status

**Phase 10C** (Current):

| Capability | Status | Notes |
|---|---|---|
| **Execution Router** | Partial | BigQuery + DuckDB only; MCP infrastructure stubbed |
| **Connection Profile Resolution** | Partial | Supabase registry lookup works; MCP credential routing TBD |
| **QueryDialect: BigQuery** | Production | Phase 9B |
| **QueryDialect: DuckDB** | Production | Phase 9B |
| **QueryDialect: Snowflake** | Stub | Phase 10C; live when first Snowflake client onboards |
| **QueryDialect: Databricks** | Stub | Phase 10C; live when first Databricks client onboards |
| **QueryDialect: HANA/Datasphere** | Stub | Phase 10C; live when first SAP client onboards |
| **QueryDialect: PostgreSQL** | Stub | Phase 10C; live when first Postgres client onboards |
| **`get_kpi_monthly_series`** | Phase 10C | Entry point for SA agent; BigQuery/DuckDB working, MCP pending |
| **Schema Inspection: DuckDB** | Production | Phase 5, used in onboarding |
| **Schema Inspection: BigQuery** | Production | Phase 5, used in onboarding |
| **Schema Inspection: Snowflake/Databricks/HANA** | Stub | Phase 10C; MCP adapters follow dialect implementation |
| **Data Product Onboarding Workflow** | Production | Phase 5-6, 8-step automation |
| **KPI Assistant API** | Production | Phase 7A (API routes exist; React UI not yet built) |
| **LLM-Assisted KPI Definition** | Production | Phase 7A endpoints working; UI integration pending |

## 6. Known Limitations

1. **MCP Execution Not Yet Live:** Snowflake, Databricks, HANA, Datasphere, PostgreSQL profiles are defined but execution routes to MCP stub. Live when first client using that backend is onboarded.

2. **Schema Inspection Adapters:** DuckDB and BigQuery adapters are complete. Snowflake/Databricks adapters follow MCP dialect completion.

3. **Connection Profile Credentials:** Currently resolved from environment variables only. OAuth2 flow for SaaS clients is planned but not implemented.

4. **Cost Control for External Warehouses:** MCP and BigQuery queries may incur per-query warehouse costs. Rate limiting and result row capping are planned.

## 7. Non-Functional Requirements

### 7.1 Performance
- KPI time-series query: 9 months in < 1 second
- Schema inspection: < 5 seconds per table
- Connection profile resolution: < 100ms

### 7.2 Reliability
- Connection failure recovery: exponential backoff retry (3x, 1s/4s/16s)
- Credential rotation support: env var refresh without DPA restart
- Audit logging: all queries logged with principal ID, query hash, execution time

### 7.3 Security
- SELECT-only enforcement (no INSERT/UPDATE/DELETE)
- Parameterized queries (no string concatenation)
- Principal-scoped filtering (via Principal Context Agent)
- Credential isolation (env vars, never in YAML/logs)

## 8. Testing Strategy

**Unit Tests (Tier 3: DuckDB):**
- Connection profile validation
- QueryDialect syntax construction
- Schema inspection
- KPI time-series construction
- Error handling (connection failures, invalid SQL, missing tables)

**Integration Tests (Tier 2: BigQuery):**
- BigQuery authentication
- Real schema inspection
- Time-series query execution
- Cost controls (result capping)

**E2E Tests (Tiers 1–3):**
- Full onboarding workflow (schema → contract → KPI registration)
- Multi-client profile switching
- MCP endpoint failure recovery (when available)

## 9. Dependencies

**External SDKs:**
- `google-cloud-bigquery` (Tier 2)
- `duckdb` (Tier 3)
- `httpx` (MCP endpoint calls, Tier 1)

**Internal:**
- `src/registry/factory.py` — registry initialization
- `src/agents/new/a9_principal_context_agent.py` — principal/role resolution
- `src/agents/new/a9_llm_service_agent.py` — SQL generation, KPI suggestions
- `src/agents/new/a9_data_governance_agent.py` — business term validation

**Infrastructure:**
- Supabase (connection profiles, data products, KPIs)
- MCP servers (Snowflake, Databricks, etc. — vendor-managed)
- BigQuery (client's GCP project)
- DuckDB (local file or memory)

## 10. Change Log

**2026-04-07 (v2.0)** — MCP-first architecture locked
- Removed deprecated A9_Data_Product_MCP_Service_Agent references
- Clarified three-tier execution model
- Added QueryDialect abstraction (no full connectors per client)
- Honest implementation status: BigQuery/DuckDB production, Snowflake/Databricks/HANA stubs
- Removed hackathon content, synthetic data methods, outdated timelines
- Focused on multi-tenant SaaS connectivity requirement

**2025-07-17 (v1.1)** — KPI Assistant, onboarding, governance integration
