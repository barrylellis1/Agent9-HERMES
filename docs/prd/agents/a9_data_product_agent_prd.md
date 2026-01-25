# A9_Data_Product_Agent Product Requirements Document

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2025-07-17
-->


## 1. Overview

### 1.1 Purpose
The A9_Data_Product_Agent manages the lifecycle of data products, including creation, version management, deployment tracking, and usage monitoring. It leverages the Unified Registry Access Layer to discover, register, and provide access to data products. It follows Agent9's architectural principles of simplicity, independence, and reliability.

### 1.2 Scope
This document outlines the requirements for version 1.0 of the A9_Data_Product_Agent, focusing on core data product management capabilities.

### 1.3 Target Audience
- System Administrators
- Data Engineers
- Business Analysts
- Data Scientists

## 2. Business Requirements

### 2.1 Business Objectives
1. Provide a standardized interface for data product management
2. Enable efficient data product lifecycle management
3. Support data quality and performance monitoring
4. Facilitate integration with data systems

### 2.2 Key Metrics
- Data processing latency: < 1 second
- Data quality metrics accuracy: > 95%
- System availability: 99.9% uptime
- Error rate: < 1%

## 3. Functional Requirements

### 3.1 Core Data Product Management

#### 3.1.1 Data Product Creation and Registry Integration
- Create new data products with unique IDs
- Configure product properties including version and capabilities
- Set up versioning and status tracking
- Define data sources and transformations
- Register data products with the Unified Registry Access Layer
- Support loading data products from various sources (YAML, JSON, Python modules)
- Provide registry access to data product definitions for other agents

#### 3.1.2 Data Processing
- All SQL execution (joining, filtering, aggregation) is performed via the MCP execution library (DuckDB backend) invoked by the Data Product Agent.
- The agent must never use direct pandas, file I/O, or agent-side data transformation in production.
- The agent calls the embedded execution library and returns standardized `SQLExecutionResponse` results to callers.
- Handle data quality validation and monitor processing performance based on execution responses only.

##### 3.1.2.1 Execution via MCP Library (LLM-first)
- The Data Product Agent MUST NOT generate SQL.
- SQL generation is delegated to the `A9_LLM_Service` Agent; execution is performed by the Data Product Agent through the embedded MCP execution library.
- The agent supports two modes for the execution core:
  - Embedded (unit tests/dev): direct in-process call into MCP core to keep tests fast and deterministic.
  - Remote (integration/E2E/prod, future): HTTP POST to an `/execute-sql` endpoint using the same request/response models.
- Principal context is injected into the MCP request so the MCP can parameterize filters (no string concatenation).
- The execution library enforces guardrails (SELECT-only, identifier validation, parameterization, timeouts, audit logging). Schema-scoped prompting is applied in the LLM Service during SQL generation.

#### 3.1.3 Analysis
- Calculate quality metrics (completeness, consistency, accuracy, timeliness)
- Track performance metrics (processing time, resource usage, throughput)
- Monitor usage metrics (requests, errors, success rate)
- Generate comprehensive analysis reports

#### 3.1.4 Data Product Discovery & Matching with Registry Integration (NEW, MVP Alignment)
- Leverage the Unified Registry Access Layer to discover data products
- Map business processes and KPIs to relevant data products
- Use the Data Product Provider to find data products by attribute, domain, or business process
- Support both legacy enum-based discovery and new registry-based discovery

#### 3.1.5 Data Factory Onboarding Capability (NEW, Phase 5 hybrid)
- Provide a **pluggable adapter framework** for multi-platform schema inspection (DuckDB, BigQuery → Snowflake → Databricks → Datasphere). Each adapter wraps the vendor SDK (e.g., `google-cloud-bigquery`) and emits normalized `TableProfile`, `KPIProposal`, and metadata payloads.
- Accept `connection_profiles` + `connection_overrides` so customers can supply credentials securely (no `.env` edits required). Service account paths, warehouse names, and datasets live outside the repo.
- Workflow automation:
  1. `inspect_source_schema` dynamically selects the appropriate database manager (DuckDB or BigQuery) based on `source_system` metadata from the request, registry entry, or connection profile. The method uses helper functions:
     - `_resolve_inspection_settings`: Merges metadata from request, registry, and connection profile to determine source system, schema/dataset, project, and connection parameters.
     - `_prepare_inspection_manager`: Instantiates and connects the correct `DatabaseManager` via `DatabaseManagerFactory`. For DuckDB, reuses the existing agent connection; for BigQuery, creates a new manager with scoped credentials and ensures cleanup.
     - `_discover_tables_for_inspection`: Queries the appropriate INFORMATION_SCHEMA (DuckDB or BigQuery) to enumerate tables/views for profiling.
     - `_profile_table`: Dispatches to backend-specific profiling methods (`_profile_table_duckdb` or `_profile_table_bigquery`) that gather column metadata, row counts, samples, and semantic tags.
  2. `generate_contract_yaml` assembles table, view, KPI, and relationship sections from inspection output plus business overrides.
  3. `register_data_product` persists Supabase registry entries (metadata, yaml path, multi-source connection info) and triggers governance/ownership mapping.
- The onboarding workflow must publish `activation_context` so Decision Studio, Situation Awareness, and downstream agents immediately "see" the new data product without manual cache flushes.
- Guardrails: adapter implementations must enforce SELECT-only profiling, cost/rate limiting (warehouse auto-suspend, result row caps), and cache snapshot metadata (refresh_ts, source_platform) so embedded insight cards can display provenance.
- Implementation Status: DuckDB and BigQuery adapters are **implemented and tested**. Snowflake/Datasphere/Databricks follow once FI Star schema pilot succeeds. All connectors reuse shared heuristics for measure/dimension detection, KPI inference, and Supabase metadata mapping.

#### 3.1.5 LLM Explainability Compliance (2025-06-24)
- All summary and recommendation text fields are routed through the A9_LLM_Service_Agent for explainability and business-user-friendly output.
- LLM calls are protocol-compliant, orchestrator-driven, and fully async with structured event logging and error handling.
- See agent card for implementation and compliance details.
- Accept technical process names and code values as input (not business English)
- Example interface:
  - `async def find_products_for_processes(processes: List[str]) -> List[Dict]`
- Input must be output from Data Governance Agent (already translated)
- Output: List of data products/KPIs, each with technical metadata (e.g., name, description, attributes)
- Example:
```python
# Input (from governance agent)
tech_processes = ["REV_BY_BU", "COST_BY_PROD"]
kpis = await data_product_agent.find_products_for_processes(tech_processes)
# Output
[
  {"name": "REV_BY_BU", "description": "Revenue by Business Unit", "attributes": ["BU_CODE", "REV_AMT"]},
  {"name": "COST_BY_PROD", "description": "Cost by Product Line", "attributes": ["PROD_CODE", "COST_AMT"]}
]
```
- Must validate all input terms and handle unmapped processes with robust error handling
- Log all matching attempts, successes, and failures

#### 3.1.6 LLM-Assisted KPI Definition Workflow (2026-01-22)

##### Purpose
Provide an interactive, LLM-powered chat interface during data product onboarding to help users define comprehensive KPIs with all required registry attributes, strategic metadata tags, and governance mappings.

##### Workflow Integration
The KPI definition step occurs between "Metadata Analysis" and "Review & Register" in the onboarding workflow:
1. Connection Setup ✓
2. Schema Discovery ✓
3. Table Selection ✓
4. Metadata Analysis ✓
5. **KPI & Governance Assistant** (NEW)
6. Review & Register ✓

##### Core Capabilities

**1. Auto-Suggestion Engine**
- Analyze inspected schema (columns, semantic tags, table roles) to suggest 3-7 business KPIs
- Leverage semantic tags to identify:
  - Measures (columns tagged as "measure")
  - Dimensions (columns tagged as "dimension")
  - Time columns (columns tagged as "time")
  - Identifiers (columns tagged as "identifier")
- Generate KPI suggestions with complete attribute sets including strategic metadata

**2. Interactive Refinement**
- Accept natural language requests to customize KPIs
- Support conversational clarification of:
  - Threshold values (green/yellow/red boundaries)
  - Comparison types (YoY, QoQ, MoM, target, budget)
  - Dimension selections for slicing
  - Owner roles and stakeholder roles
  - Business process mappings
- Validate SQL queries against available schema
- Explain business rationale for each suggestion

**3. Complete KPI Attribute Generation**
For each KPI, generate ALL required attributes per `src/registry/models/kpi.py`:

- **Core Identity:** id, name, domain, description, unit, data_product_id
- **Calculation:** sql_query, filters (optional)
- **Dimensions:** name, field, description, values
- **Thresholds:** comparison_type, green/yellow/red thresholds, inverse_logic
- **Governance:** business_process_ids, tags, owner_role, stakeholder_roles
- **Strategic Metadata:**
  - `line` (top_line/middle_line/bottom_line)
  - `altitude` (strategic/tactical/operational)
  - `profit_driver_type` (revenue/expense/efficiency/risk)
  - `lens_affinity` (bcg/bain/mckinsey combinations)
  - `refresh_frequency`, `data_latency`, `calculation_complexity`

##### Strategic Metadata Tag Specifications

**metadata.line** - Financial Statement Classification
- `top_line`: Revenue/growth metrics (e.g., Total Revenue, Sales Growth)
- `middle_line`: Operational efficiency (e.g., Gross Margin, Conversion Rate)
- `bottom_line`: Profitability/cost control (e.g., Net Profit, Operating Expenses)

**metadata.altitude** - Decision Level
- `strategic`: C-suite, long-term planning (3-5 years)
- `tactical`: Department heads, quarterly goals
- `operational`: Day-to-day management

**metadata.profit_driver_type** - P&L Impact
- `revenue`: Drives top-line growth
- `expense`: Cost reduction/control
- `efficiency`: Resource optimization (do more with less)
- `risk`: Downside protection

**metadata.lens_affinity** - Consulting Persona Mapping
- `bcg`: Portfolio view, growth-share matrix, value creation
- `bain`: Operational excellence, quick wins, results-first
- `mckinsey` or `mbb_council`: Root cause, MECE, hypothesis-driven
- Can combine: "bcg,bain" or "mckinsey,bain"

**Usage:** Solution Finder Agent selects consulting personas based on KPI's lens_affinity

##### API Endpoints

**POST /api/v1/data-product-onboarding/kpi-assistant/suggest**
- Input: `{ data_product_id, schema_metadata, user_context }`
- Output: `{ suggested_kpis: [KPI], conversation_id }`

**POST /api/v1/data-product-onboarding/kpi-assistant/chat**
- Input: `{ conversation_id, message, current_kpis }`
- Output: `{ response, updated_kpis, actions }`

**POST /api/v1/data-product-onboarding/kpi-assistant/validate**
- Input: `{ kpi_definition, schema_metadata }`
- Output: `{ valid, errors, warnings }`

**POST /api/v1/data-product-onboarding/kpi-assistant/finalize**
- Input: `{ data_product_id, kpis }`
- Output: `{ updated_contract_yaml, registry_updates }`

##### Backend Requirements

**Agent Collaboration:**
- A9_LLM_Service_Agent: Generate KPI suggestions and conversational responses
- A9_Data_Governance_Agent: Validate business terms and governance mappings
- A9_Data_Product_Agent: Validate SQL queries against schema, update contracts

**LLM System Prompt Template:**
```
You are a KPI definition assistant for Agent9's data product onboarding.

CONTEXT:
- Data Product ID: {data_product_id}
- Domain: {domain}
- Source System: {source_system}
- Available Measures: {measures}
- Available Dimensions: {dimensions}
- Time Columns: {time_columns}

YOUR ROLE:
Help users define comprehensive KPIs with ALL required attributes.

KPI STRUCTURE (ALL fields required):
1. Core Identity: id, name, domain, description, unit, data_product_id
2. Calculation: sql_query, filters
3. Dimensions: name, field, description, values
4. Thresholds: comparison_type, green/yellow/red, inverse_logic
5. Governance: business_process_ids, tags, owner_role, stakeholder_roles
6. Strategic Metadata: line, altitude, profit_driver_type, lens_affinity

STRATEGIC METADATA GUIDANCE:
- Revenue KPIs → line:top_line, altitude:strategic, driver:revenue, lens:bcg,mckinsey
- Efficiency KPIs → line:middle_line, altitude:tactical, driver:efficiency, lens:bain
- Cost KPIs → line:bottom_line, altitude:operational, driver:expense, lens:bain

INTERACTION STYLE:
- Initially suggest 3-5 KPIs with complete attributes
- Explain WHY you chose each metadata value
- Ask clarifying questions to refine thresholds
- Validate SQL against available schema
- Format suggestions as YAML with all attributes
```

##### UI Components

**Left Panel: Contract Preview**
- Display inspected schema with semantic tags
- Highlight measures, dimensions, time columns
- Show detected table roles (FACT/DIMENSION)
- Provide expandable full schema view

**Right Panel: LLM Chat Interface**
- Conversational message history
- KPI suggestion cards with:
  - Expandable YAML preview
  - Action buttons: [Accept] [Customize] [Reject]
  - Metadata tag explanations
- User input field with send button
- Batch actions: [Accept All] [Export YAML]

**KPI Suggestion Card Format:**
```
📊 Total Revenue
   SUM(SalesOrder_GROSSAMOUNT)
   
   Strategic Tags:
   • Line: Top Line (revenue metric)
   • Altitude: Strategic (C-suite focus)
   • Driver: Revenue (P&L top line)
   • Lens: BCG + McKinsey (growth + analysis)
   
   Dimensions: Company, Fiscal Period, Product
   Thresholds: YoY >10% = Green
   Owner: CFO | Stakeholders: CEO, Sales VP
   
   [View YAML] [Accept] [Customize] [Reject]
```

##### Implementation Requirements

**Phase 1: Backend Agent (1 week)**
- Create A9_KPI_Assistant_Agent with LLM integration
- Implement KPI suggestion engine using schema analysis
- Add conversational refinement capability
- Implement SQL validation against schema
- Add YAML contract update functionality

**Phase 2: API Endpoints (3 days)**
- Implement suggest, chat, validate, finalize endpoints
- Add conversation state management
- Implement error handling and validation
- Add audit logging for KPI definitions

**Phase 3: UI Integration (1 week)**
- Add KPI Assistant step to onboarding workflow
- Implement chat interface with message history
- Create KPI suggestion cards with actions
- Add contract preview panel
- Implement batch operations

**Phase 4: Testing & Refinement (3 days)**
- Test with BigQuery SalesOrders dataset
- Validate strategic metadata tag assignments
- Test conversational refinement flows
- Verify contract YAML generation
- End-to-end integration testing

##### Acceptance Criteria

- LLM assistant suggests 3-5 relevant KPIs based on schema analysis
- All suggested KPIs include complete attribute sets (no missing fields)
- Strategic metadata tags are correctly assigned with explanations
- SQL queries are validated against available schema
- Users can refine KPIs through natural language conversation
- Final KPIs are correctly added to data product contract YAML
- Contract updates trigger registry synchronization
- UI provides clear visual feedback for all operations

### 3.2 Error Handling

#### 3.2.1 Error Response Format
All error responses must be in the following format:
```python
{
    'status': str,  # Must be one of: 'success', 'partial_error', 'error'
    'error': str,   # Detailed error message
    'timestamp': str,  # ISO format timestamp
    'method': str   # Calling method name
}
```

#### 3.2.2 Status Codes
- 'success': Operation completed successfully
- 'partial_error': Validation error occurred, some data may be processed
- 'error': Processing or connection error occurred, operation failed

#### 3.2.3 Error Types and Messages
- ConfigurationError: "Invalid configuration: {specific_error}"
- RegistrationError: "Failed to register with registry: {specific_error}"
- ProcessingError: "Processing error: {specific_error}"
- ValidationError: "Validation error: {specific_error}"
- TypeError: "Invalid type: {expected_type}. Received: {received_type}"
- FormatError: "Invalid format: {expected_format}. Received: {received_format}"
- MissingFieldError: "Missing required field: {field_name}"
- EmptyValueError: "Empty value for required field: {field_name}"
- ConnectionError: "Connection error: {specific_error}"

#### 3.2.4 Error Handling Requirements
- All methods must validate input parameters before processing
- Must use template's error handling patterns
- Must return error responses instead of raising exceptions
- Error logging must include:
  - Method name
  - Error type
  - Detailed error message
  - Timestamp
  - Stack trace (for processing errors)
- Error responses must be consistent across all methods
- Must handle all error types with appropriate status codes
- Must validate configuration on initialization
- Must validate data format before processing

#### 3.2.5 Registry & Integration Requirements (NEW, MVP Alignment)
- Must use template's register_with_registry method
- Must properly handle registration errors
- Must return proper error responses on failure
- Must properly set up registry reference
- Must validate agent ID format before registration
- Must handle concurrent registration attempts
- All discovery/matching functions must be async
- Input must be compatible with Data Governance Agent output
- Registry integration must follow A9_Agent_Template
- Log all integration attempts and failures

#### 3.2.6 Test Requirements (NEW, MVP Alignment)
- All methods must have test cases for:
  - Success scenarios
  - Validation error scenarios
  - Processing error scenarios
  - Connection error scenarios (where applicable)
  - Integration with Data Governance Agent (input translation)
  - Integration with Principal Context Agent (end-to-end flow)
- Test cases must verify:
  - Return type (Dict[str, Any]) or List[Dict]
  - Status code
  - Error message (if applicable)
  - Timestamp presence
  - Method name in response
  - Input validation for technical terms/code values
- Error messages must match exactly what's expected
- Status codes must be properly checked
- Timestamps must be present in responses
- Method names must be correct in responses

### 3.3 Configuration Management
- Support default configuration values
- Validate configuration on initialization
- Maintain configuration state
- Handle agent-specific settings
- Configuration fields:
  - name
  - version
  - capabilities
  - error_handling

#### 3.3.1 MCP Client Configuration (NEW)
- `mcp_mode`: one of `embedded`, `remote` (default `embedded` for unit tests).
- `mcp_base_url`: required when `mcp_mode=remote` (e.g., `http://localhost:8000`).
- `mcp_timeout_ms`: timeout budget for remote calls.
- `validate_sql`: boolean to enforce client-side SELECT-only pre-checks before delegation.
- `log_queries`: boolean to enable query preview logging (headers only, redact parameters).

### 3.4 Logging
- Initialize agent-specific logger
- Log initialization and major operations
- Support different log levels (INFO, ERROR)
- Include timestamps in logs
- Log error details with stack traces

## 4. Non-Functional Requirements

### 4.1 Performance
- Process data in real-time
- Handle large data volumes
- Maintain consistent performance
- Support concurrent operations

### 4.2 Reliability
- High availability architecture
- Automatic failover
- Data backup and recovery
- Error handling and recovery

## 5. Technical Requirements

### 5.0 Registry Architecture Integration
- Must integrate with the Unified Registry Access Layer
- Must use the Registry Factory to access providers
- Must use the Data Product Provider for all data product operations
- Must support loading data products from YAML contracts
- Must support data product registration from multiple sources
- Must provide backward compatibility for legacy code using enum values

### 5.1 Protocol Compliance Update (2025-06-24)
- All entrypoints accept only protocol-compliant models: `DataProductNLQSearchInput` and `DataAssetPathRequest` as input; `DataProductNLQSearchOutput` and `DataAssetPathResponse` as output.
- No legacy, deprecated, or stub models are permitted.
- Agent must be instantiated and registered only by the orchestrator; constructor requires a registry reference.
- `register_with_registry` only stores the registry reference, never performs registration.
- All event logging is async/awaited and uses `A9_SharedLogger`.
- All protocol-compliant workflows must propagate and utilize `yaml_contract_text` from the context kwarg.
- All usage and test examples must reflect orchestrator-driven patterns.

### 5.1 System Architecture
- Microservices-based architecture
- RESTful API interface
- Containerized deployment

### 5.2 Performance Optimization
- Implements YAML contract caching mechanism (`_yaml_contract_cache` and `_get_yaml_contract` method)
- Optimizes repeated contract access during agent operation
- Reduces redundant parsing and processing of YAML contracts

### 5.3 Testing and Integration Support
- Provides `load_synthetic_data` method for testing and integration scenarios
- Implements `get_kpi_values` method for querying synthetic KPI data
- Supports development and testing environments with synthetic data generation

### 5.4 User Preference Management
- Includes `get_user_variance_threshold` method for retrieving user-specific preferences
- Supports personalized data presentation based on user settings
- Enables customized threshold configuration for variance reporting

### 5.5 Agent-to-Agent Communication
- Implements `context_handoff_a2a` method for protocol-compliant context handoff
- Provides `product_documentation_qna_a2a` method for documentation Q&A functionality
- Supports standardized inter-agent communication patterns
- Cloud-native design

### 5.2 Technology Stack
- Python 3.10+
- FastAPI for REST API
- SQLAlchemy for database
- Docker for containerization
- Kubernetes for orchestration

### 5.3 Integration Points
- Data systems
- Logging infrastructure
- Monitoring system
- Agent registry

### 5.4 Module Structure and Imports
- Error handling module structure:
  - All error classes should be exported through the package's __init__.py
  - Error classes should be organized in a dedicated sub-module
  - Common error types should be accessible via the package root
- Import patterns:
  - Use relative imports within agent packages
  - Use explicit import paths for external dependencies
  - Follow PEP 8 import ordering:
    1. Standard library imports
    2. Third-party imports
    3. Local application imports
  - Example import structure:
    ```python
    from typing import Dict, Any  # Standard library
    import pandas as pd            # Third-party
    from ..agent_registry import AgentRegistry  # Local relative import
    from ..errors import ConfigurationError  # Local relative import
    ```

## 6. Implementation Phases

### Phase 1: Core Implementation (1 week)
- Basic data product management
- Core data processing
- Basic error handling
- Initial logging setup

### Phase 2: Advanced Features (1 week)
- Advanced error handling
- Configuration management
- Enhanced logging
- Performance optimization

### Phase 3: Data Factory Adapters & Automated Onboarding (2 weeks, hybrid with Phase 5 hardening)
- Implement BigQuery adapter using service account credentials and INFORMATION_SCHEMA profiling.
- Generalize the Data Product Agent DB manager to load adapters per `source_system`.
- Automate onboarding workflow end-to-end (schema inspection → contract generation → registry/governance ownership → QA).
- Extend Supabase registry metadata to include multi-source connection descriptors, refresh cadence, and provenance.
- Add Snowflake, Datasphere, and Databricks adapters (reusing the same adapter interface) with rate limiting + cost controls.
- Document Decision Studio discovery UX tied to the new metadata fields.

## 7. Dependencies

### 7.1 External Dependencies
- Data storage systems
- Logging services
- Monitoring services
- Configuration management

### 7.2 Internal Dependencies

- Connection Profiles service (`config/connection_profiles.*`) for secure credential routing.
- Supabase registry + YAML contracts for metadata persistence.
- Vendor SDKs: `google-cloud-bigquery`, Snowflake Python Connector, Databricks SQL connector/Unity Catalog APIs, SAP Datasphere Open SQL/OData client libraries.

### Recent Updates (v1.1+)
- **Execution via MCP Library (Embedded for MVP):**
  - The Data Product Agent executes SQL queries generated by the A9_LLM_Service Agent via the embedded MCP execution library (DuckDB backend).
  - The agent does not use pandas, direct file I/O, or agent-side data transformation in production.
  - Remote mode is available for future use but not currently implemented.
  - Registry integration and onboarding remain agent responsibilities; runtime SQL is executed via the embedded library (remote mode optional in future).
- **Return Structure:**
  - `create_data_product` now returns `{'status': 'created', 'data': {...}}` on success, and a structured error dict on failure.
- **Error Handling:**
  - Product creation requires `name` and `description` (both non-empty).
  - Missing/empty fields yield `partial_error` status and a detailed error message.
- **Logging:**
  - All errors and validation failures are logged with method name, error type, and timestamp.
- **Imports:**
  - All imports are absolute (e.g., `from src.agents.new.A9_Data_Product_Agent import ...`).
- **Test Coverage:**
  - 100% coverage for core functionality, error handling, config validation, and async ops.
  - Tests assert on return structure, error handling, and logging patterns.
- **Registry Integration:**
  - Follows A9_Agent_Template registry and creation patterns.
- **Example Code:**
  ```python
  result = await agent.create_data_product({'name': 'foo', 'description': 'bar'})
  assert result['status'] == 'created'
  assert 'data' in result
  ```



## Hackathon Quick Start

### Development Environment Setup
- Clone the Agent9-Hackathon-Template repository
- Install required dependencies from requirements.txt
- Configure environment variables in .env file based on .env.example

### Key Files and Entry Points
- Main agent implementation: `src/agents/new/A9_Data_Product_Agent_Agent.py`
- Configuration model: `src/agents/new/agent_config_models.py`
- Agent card: `src/agents/new/cards/a9_data_product_agent_agent_card.py`

### Test Data Location
- Sample data available in `test-data/` directory
- Test harnesses in `test-harnesses/` directory

### Integration Points
- Integrates with Agent Registry for orchestration
- Follows A2A protocol for agent communication
- Uses shared logging utility for consistent error reporting
- Integrates with the Unified Registry Access Layer for data products and query mappings

### Registry Architecture Integration
- Must use the Registry Factory to initialize and access all registry providers
- Must configure and use appropriate registry providers for data products, contracts, and query templates
- Must use registry data for context-aware data product discovery and access
- Must NOT cache registry data locally; instead, always access the latest data through the Unified Registry Access Layer
- Must support backward compatibility with legacy code
- Must delegate registry operations to the appropriate providers

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

## 8. Modification History

### 8.1 Version 1.0
- Date: 2025-04-14
- Changes:
  - Initial implementation of core functionality
  - Added structured error handling
  - Implemented configuration management
  - Added comprehensive logging
  - Added test coverage
- Affected Test Cases:
  - Registry Integration Tests
  - Error Handling Tests
  - Configuration Tests
  - Data Processing Tests

### 8.2 Planned Modifications

#### 8.2.1 Enhanced Error Handling
- Purpose: Improve error handling robustness
- Impact Analysis:
  - Input Changes: None
  - Output Changes: More detailed error responses
  - Data Flow Changes: None
- Test Impact:
  - Affected Test Cases: Error Handling Tests
  - New Test Cases Needed: None
  - Test Data Changes: None
- Implementation Plan:
  1. Add more specific error types
  2. Improve error recovery mechanisms
  3. Add retry logic
- Documentation Updates:
  - [ ] Update error handling documentation
  - [ ] Update error response structure
  - [ ] Update usage examples

## 9. Acceptance Criteria

### 9.0 Protocol Compliance (2025-06-24)
- All entrypoints use only protocol-compliant models as defined in code.
- Orchestrator-driven lifecycle is enforced; no agent-side registration or direct instantiation in documentation or code samples.
- All event logging is async/awaited and uses `A9_SharedLogger`.
- YAML contract context is always propagated and accessed via the context kwarg.
- All tests and usage examples are orchestrator-driven.

### 9.1 Functional
- Successful data product creation
- Accurate data processing
- Proper error handling
- Complete documentation
- **Compliance:** All joining, filtering, and aggregation must be executed via the MCP execution library (DuckDB backend) invoked by the Data Product Agent. No agent-side pandas/file I/O is permitted in production.

#### 9.1.1 Delegation Acceptance (Additions)
SQL generation is performed by the `A9_LLM_Service` Agent. SQL execution is performed by the `A9_Data_Product_Agent` via the embedded MCP execution library.
Principal filters are provided to MCP as parameters; no string concatenation in the agent.
Embedded mode is used for unit tests; remote mode verified in integration/E2E.
Structured audit fields (transaction_id, prompt/model if applicable) are available in logs.

### 9.2 Non-Functional
- Performance meets requirements
- Error handling implemented
- Documentation complete
- Testing coverage verified

## 10. Agent Requirements

### 10.1 Core Agent Interface
- Follow Agent9 agent registry interface requirements
- Implement required Unified Registry integration methods
- Use the Data Product Provider for registry operations
- Use standard error handling patterns
- Maintain consistent logging

### 10.2 Configuration Management
- Support default configuration values
- Validate configuration on initialization
- Maintain configuration state
- Handle agent-specific configuration

### 10.3 Error Handling
- Implement structured error handling
- Log errors appropriately
- Return consistent error responses
- Handle common error types

### 10.4 Logging
- Initialize agent-specific logger
- Log initialization and major operations
- Support different log levels
- Include timestamps in logs

### 10.5 Core Methods
- Implement _initialize for setup
- Implement _setup_logging for logging
- Implement _setup_error_handling for error management
- Implement create_from_registry class method
- Implement _validate_input for input validation
- Implement _format_error for consistent error messages

### 10.6 Error Types
- ConfigurationError: Invalid configuration
- RegistrationError: Failed to register with registry
- ProcessingError: Failed to process data
- ValidationError: Invalid input data
- TypeError: Invalid data type
- FormatError: Invalid ID format
- MissingFieldError: Required field is missing
- EmptyValueError: Required field is empty
- ConnectionError: Connection failures

## 11. Testing Requirements

### 11.1 Test Coverage
- Core functionality: 100%
- Error handling: 100%
- Performance: 80%
- Integration: 80%

### 11.2 Test Scenarios
1. Data product creation
2. Data processing
3. Error handling
4. Configuration management
5. Integration with registry

## 12. Maintenance

### 12.1 Regular Updates
- Performance optimization
- Bug fixes
- Feature enhancements
- Documentation updates

### 12.2 Support
- User documentation
- API documentation
- Troubleshooting guide
- Support channels
