# A9 Data Product MCP Service PRD

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2025-07-17
-->


## Registry-Driven KPI Logic & Pluggable Analytics Backend (2025-05-18)

**Future Consideration:**
Not all numeric columns are additive. In the future, the registry and MCP service may distinguish between additive measures (where SUM is appropriate) and non-additive numeric attributes (where only AVG, MIN, MAX make sense). For now, all numeric columns that could be meaningfully aggregated are listed as direct measures. This can be refined later if needed.

- The MCP service must parse `kpi_calculations` and `kpi_filters` from the registry for each product.
- It must dynamically generate SQL for both direct measures and KPIs (including formulas and standardized filters).
- The query execution layer must be pluggable, supporting local (DuckDB) and cloud (e.g., Google BigQuery) backends via configuration, with no change to business logic.
- This enables future-proof, standardized analytics for all users and easy adoption of new analytics engines.

## Overview
The A9_Data_Product_MCP_Service (Managed Compute Platform for Data Products) is the single authoritative layer for SQL execution and validation for Agent9 data products. Dynamic SQL generation is performed exclusively by the A9_LLM_Service Agent. All logic for registry-scoped validation (SELECT-only, identifier checks, parameterization) and execution (dialect transform + query run) has been migrated here from the agent layer. The legacy DynamicSQLBuilder in agent utilities has been fully removed to avoid duplication and confusion.

This service (embedded as an execution backend library for MVP) provides business-ready, summarized, filtered, and pre-joined data products to Agent9 agents and orchestrators. It is initially enabled with tools for SAP Sample CSV test data (test-mode only), and is designed to be extensible to other data source types and platforms (e.g., SAP DataSphere, Snowflake, Google BigQuery).
**Note:** Other MCP services may be created in the future to serve different specialized functions (e.g., workflow orchestration, analytics, or ML serving). This PRD covers only the Data Product MCP Service.



## Hackathon Quick Start

### Development Environment Setup
- Clone the Agent9-Hackathon-Template repository
- Install required dependencies from requirements.txt
- Configure environment variables in .env file based on .env.template

### Key Files and Entry Points
- MVP execution core is an embedded library invoked by `A9_Data_Product_Agent`; no standalone MCP "agent" is required in MVP.
- Optional future remote wrapper: REST endpoint `/execute-sql` that delegates to the same embedded core.
- Configuration model: `src/agents/new/agent_config_models.py`
- Agent card: `src/agents/new/cards/a9_data_product_mcp_service_agent_card.py` (deprecated in MVP; retained for documentation)

### Test Data Location
- Sample data available in `test-data/` directory
- Test harnesses in `test-harnesses/` directory

### Integration Points
- Integrates with Agent Registry for orchestration
- Follows A2A protocol for agent communication
- Uses shared logging utility for consistent error reporting

## Implementation Guidance

### Suggested Implementation Approach
1. Start with the agent's core functionality
2. Implement required protocol methods
3. Add registry integration
4. Implement error handling and logging
5. Add validation and testing

### Core Functionality to Focus On
- Protocol compliance (A2A)
- Registry integration
- Error handling and logging
- Proper model validation

### Testing Strategy
- Unit tests for core functionality
- Integration tests with mock registry
- End-to-end tests with test harnesses

### Common Pitfalls to Avoid
- Direct agent instantiation (use registry pattern)
- Missing error handling
- Incomplete logging
- Improper model validation

## Success Criteria

### Minimum Viable Implementation
- Agent implements all required protocol methods
- Agent properly integrates with registry
- Agent handles errors and logs appropriately
- Agent validates inputs and outputs

### Stretch Goals
- Enhanced error handling and recovery
- Performance optimizations
- Additional features from Future Enhancements section

### Evaluation Metrics
- Protocol compliance
- Registry integration
- Error handling
- Logging quality
- Input/output validation

---

## Purpose
- Centralize all join, filter, and aggregation operations for data products (Data Product MCP Service)
- Deliver business-ready data to Agent9 agents via simple, secure API endpoints
- Ensure compliance, auditability, and performance at scale
- Establish a pattern for future MCP services with other specialized roles

---

## Initial Scope
- **Data Sources:** SAP Sample CSV test data (local or networked)
- **Operations:** Summarization (aggregation), filtering, pre-joining of data products as defined in the Agent9 registry
- **API:** REST or gRPC endpoints for requesting data products by product_id, with filter/KPI/group-by parameters
- **Governance:** RBAC, audit logging, registry-driven validation

---

## Future Scope
- Support for additional data source types:
  - SAP DataSphere
  - Snowflake
  - Google BigQuery
  - Other cloud/on-prem data platforms
- Dynamic query pushdown and optimization for large-scale datasets
- Materialized/cached result management for performance
- Enhanced monitoring and lineage tracking

---

## Technical Requirements
- **Single Source of SQL Execution & Validation:** All SQL validation and execution (including SELECT-only enforcement, identifier validation, parameterization, and dialect transform) is handled exclusively by the MCP execution library. SQL generation is handled exclusively by the A9_LLM_Service Agent. There is no dynamic SQL generation in the Data Product Agent.
- Registry-driven: All data product metadata, joins, and KPIs defined in the Agent9 registry
- Modular connectors for each supported data source type
- Secure API endpoints with RBAC and audit logging
- **Centralized Logging:** All logging, error, and audit events in the Data Product MCP Service must use the `A9_SharedLogger` (see backlog rationale). No local logger instances or ad-hoc logging are permitted. Logging must be structured, centralized, and propagated to the orchestrator where relevant, supporting compliance and maintainability.
- Configurable for dev/test/prod environments
- Extensible architecture for new data platforms
### Temporal Additivity for Account-Like Data Models
- The MCP service must support correct aggregation logic for Account-like data models (e.g., General Ledger, FinancialTransactions) where measures (such as VALUE) can be mixed in terms of temporal additivity.
- The service must leverage AccountType (or equivalent master data) to distinguish between additive (e.g., P&L accounts) and non-additive (e.g., Balance Sheet accounts) measures.
- For additive measures (P&L), aggregation (e.g., SUM) across time is valid.
- For non-additive measures (Balance Sheet), aggregation across time is not valid; only period-end values should be reported.
- KPI definitions must explicitly specify AccountType-based aggregation rules when referencing such measures.

---

## API Contract (MVP, as of 2025-06-22)
- Embedded mode (default for MVP): the Data Product Agent calls the MCP execution library in-process using `SQLExecutionRequest`/`SQLExecutionResponse` models.
- Optional remote mode (future):
  - **POST /execute-sql**
    - Accepts: protocol-compliant LLM-generated SQL (DuckDB backend only for MVP)
    - Input model: `SQLExecutionRequest` (fields: `sql: str`, `context: Optional[dict]`, `principal_id: str`, `limit?: int`, `timeout_ms?: int`)
    - Output model: `SQLExecutionResponse` (fields: `columns: List[str]`, `rows: List[List[Any]]` or `List[Dict]`, `row_count: int`, `query_time_ms: int`, `transaction_id: str`, `status: str`, `message?: str`, `error?: str`, `metadata?: dict`)
    - Security: Only `SELECT` statements allowed (DDL/DML rejected), RBAC stub, audit logging via `A9_SharedLogger`
    - Returns: query result rows and columns, or error if invalid

- (Legacy/Planned) **GET /data-product/{product_id}**
  - Registry-driven, summarized, filtered, pre-joined business-ready data (CSV, JSON, or DataFrame)
- (Legacy/Planned) **POST /data-product/{product_id}/refresh**
  - Triggers rebuild of temp/pre-joined source
- (Legacy/Planned) **GET /data-product/{product_id}/preview**
  - Returns sample rows for UI/testing

---

## Compliance & Governance
- All requests and results logged for audit using `A9_SharedLogger`
- RBAC enforced per product and operation
- Registry is the single source of truth for allowed joins, filters, and KPIs
- All API errors and access denials are structured and logged via the shared logger

---

## Impact Analysis
- **Positive:**
  - Simplifies agent logic, improves maintainability and compliance
  - Centralizes governance, audit, and performance optimization
  - Enables future support for enterprise-scale data sources
- **Risks:**
  - Initial performance may be limited by CSV/local test data
  - Requires robust registry and API validation to prevent errors

---

## Agent9 Design Standards Compliance

The Data Product MCP Service conforms to Agent9's core architectural and compliance standards as follows:

| Design Standard                | Applies to MCP? | Notes                                                      |
|------------------------------- |:--------------:|------------------------------------------------------------|
| Centralized Logging            |      Yes       | Must use `A9_SharedLogger`                                 |
| Registry-Driven                |      Yes       | All product/source metadata from registry                  |
| RBAC & Audit Logging           |      Yes       | Required for all access                                    |
| Environment Awareness          |      Yes       | Dev/test/prod config support                               |
| Extensibility                  |      Yes       | Modular for new source types                               |
| Error Handling Patterns        |      Yes       | Use structured/template patterns                           |
| Documentation & PRD Process    |      Yes       | PRD, impact analysis, test case tracking                   |
| Test Planning                  |      Yes       | Integration-first, document test impact                    |
| SDK/Template Compliance        |   Partial      | Follow patterns, not inheritance                           |
| Agent Template Inheritance     |      No        | Not an agent                                               |
| Agent Registration/Discovery   |      No        | Referenced, not registered                                 |
| HITL Support                   |      No        | Not required                                               |
| Agent-to-Agent Protocols       |      No        | Service endpoints only                                     |
| Agent Naming/Prefix            |      No        | Use service-oriented naming                                |

The MCP service follows all applicable Agent9 standards for logging, registry-driven logic, RBAC, extensibility, and compliance. See the backlog for refactoring and enforcement tasks.

---

## Test Cases (Initial)
- Requesting a summarized data product with filters returns correct, business-ready data
- RBAC prevents unauthorized access to restricted data products
- Audit logs contain all access and error events
- Registry changes are reflected in MCP endpoints
- Extensibility: Add new data source connector and validate with integration test

---

## Documentation
- API reference and usage examples
- Registry integration guide
- Data source connector documentation
- Governance and compliance policies

---

## Implementation Details

### Fallback Logging Implementation
- Implements an in-line `DummyLogger` class as a fallback when the standard `A9_SharedLogger` is not available
- Ensures logging capabilities are maintained even in standalone or test environments
- Provides consistent logging interface regardless of environment context
- Automatically falls back to standard logging patterns when shared logger is unavailable

### RBAC Stub Implementation
- Includes a stub implementation of Role-Based Access Control (RBAC) for future expansion
- Provides placeholder methods for access control validation
- Supports future integration with enterprise authentication systems
- Includes audit logging for all access attempts and authorizations

### Logical-to-Physical Column Mapping
- Implements logical-to-physical column mapping inside the `execute_sql` method
- Translates business-friendly column names to actual database field names
- Supports dynamic mapping based on data source and schema
- Handles special cases and naming conventions across different data sources

### Registry-Driven Measures Extraction
- Implements registry-driven direct measures extraction logic
- Dynamically builds measure selection based on registry definitions
- Supports both direct measures and calculated KPIs
- Handles measure validation against available data sources

### CSV-Based Dynamic Column Extraction
- Note: Test-mode only; not used in dev/prod runtime paths.
- Implements CSV-based dynamic column extraction for the `select_fields` method
- Supports flexible field selection based on user queries
- Handles CSV file format variations and encoding issues
- Includes validation to ensure selected fields exist in the data source

### SQL Builder Usage and Error Handling
- Implements comprehensive error handling and logging patterns for SQL preview/generation
- Provides detailed error messages for invalid SQL or missing data
- Includes validation for SQL injection prevention
- Supports graceful degradation when errors occur

### Pandas Integration
- Note: Test-mode only; not used in dev/prod runtime paths.
- Uses pandas for registry and CSV operations
- Provides DataFrame-based intermediate representations
- Supports efficient data transformation and manipulation
- Includes optimized memory usage patterns for large datasets

### Duplicate Endpoint Implementation
- Contains duplicate definition of `execute_sql` to support backward compatibility
- Maintains consistent behavior across different API versions
- Includes deprecation warnings for legacy endpoint usage
- Provides migration path for clients using older API versions

---

## LLM-first SQL Generation (MVP Contract)

The A9_LLM_Service Agent is the single source of dynamic SQL generation. The MCP execution library validates and executes SQL with strict guardrails and scope control.

### Guardrails
- Schema-scoped prompts only: the LLM service builds prompts from the registry/contract-defined schema for the requested product and view(s). No extra schema is exposed to the LLM.
- SELECT-only: SQL must be validated as a single SELECT statement. DDL/DML is rejected. Enforced by `db_manager.validate_sql()` and code-level checks.
- Parameterization: principal filters and user-provided constraints are passed as parameters, never string-concatenated.
- Identifier validation: parse/normalize identifiers (e.g., via sqlglot or backend parser) and ensure all identifiers exist in the allowed schema subset.
- Optional dry-run: PREPARE/EXPLAIN checks may be used before execution to surface errors early.
- Timeouts and budgets: wrap generation/execution in timeouts; set token/compute budgets per environment.
- Auditability: persist prompt, model, SQL output, and transaction_id via `A9_SharedLogger`.

### Principal Context Injection
- MCP receives principal context in the request and injects required filters as validated parameters into the generated SQL.
- Presentation preferences (currency, number formatting) are handled at the explainability layer (optional LLM summarize pass), not inside SQL.

### Multi-backend Strategy
- Generate ANSI SQL from the LLM.
- Transform dialect as needed via `DatabaseManager.transform_sql()` (e.g., DuckDB, BigQuery, HANA, Snowflake, Databricks).
- Keep schema canonical in contracts/registry so prompts remain consistent across backends.

### Modes of Operation
- Embedded mode (dev/unit tests): agents call MCP core in-process to avoid HTTP and keep tests fast and stable.
- Remote mode (integration/E2E/prod): agents call the REST endpoint (POST `/execute-sql`). Both modes share the same core and request/response models.

### Acceptance Criteria (Additions)
- SELECT-only enforcement with schema-scoped prompting is mandatory.
- Principal filters are parameterized and validated server-side.
- Identifier validation against provided schema; unknown identifiers cause a structured error.
- Structured audit logs (prompt/model/sql/transaction_id) emitted for every request.
- Dialect transform is applied per configured backend.
