# A9_NLP_Interface_Agent Product Requirements Document

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2025-07-17
-->


## Modification History
- 2025-05-26: Added async method `parse_business_query` for orchestrator-driven, LLM-powered business query parsing. Updated Functional Requirements and compliance notes. (Cascade)

## 1. Overview

### 1.1 Purpose
The A9_NLP_Interface_Agent provides a unified interface for natural language processing capabilities across different ERP systems, enabling seamless integration of business intelligence and analytics with enterprise systems.

**YAML Contract Context:**
The agent must read and respond to `yaml_contract_text` provided in the context by the orchestrator, supporting protocol-compliant workflows that leverage YAML-driven data product contracts for schema, mapping, and constraints.

### 1.2 Scope
This document outlines the requirements for version 1.0 of the A9_NLP_Interface_Agent, focusing on core NLP capabilities and ERP system integration.

### 1.3 Target Audience
- System Administrators
- Integration Developers
- Business Analysts
- Data Scientists

## 2. Business Requirements

### 2.1 Business Objectives
1. Provide a standardized NLP interface for enterprise systems
2. Enable business context-aware document processing
3. Support enterprise-grade data processing and analysis
4. Facilitate integration with existing ERP systems

### 2.2 Key Metrics
- Processing latency: < 1 second for small documents
- Accuracy: > 90% for standard document types
- System availability: 99.9% uptime
- Error rate: < 1%



## Hackathon Quick Start

### Development Environment Setup
- Clone the Agent9-Hackathon-Template repository
- Install required dependencies from requirements.txt
- Configure environment variables in .env file based on .env.template

### Key Files and Entry Points
- Main agent implementation: `src/agents/new/A9_NLP_Interface_Agent_Agent.py`
- Configuration model: `src/agents/new/agent_config_models.py`
- Agent card: `src/agents/new/cards/a9_nlp_interface_agent_agent_card.py`

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

## Compliance & Integration Update (2025-05-12)
- HITL (Human-in-the-Loop) enablement is fully implemented and enforced for all key actions:
  - The agent config supports a `hitl_enabled` flag.
  - Output protocol fields (`human_action_required`, `human_action_type`, `human_action_context`) are present and validated.
  - When HITL is enabled, all outputs require human approval and set these fields accordingly.
- All integration and testing for this agent is orchestrator-driven and production-like:
  - Agent inputs and outputs are always real Pydantic model instances, never mocked or stubbed.
  - Integration tests simulate true production workflows, with the orchestrator coordinating all agent calls and data flows.
- Logging uses `A9_SharedLogger` and is propagated to the Orchestrator Agent.
- Error handling is standardized and protocol-compliant.
- Strict A2A protocol compliance (Pydantic models for all entrypoints/outputs) is maintained.
- HITL escalation and LLM integration priorities are referenced per the Agent9 LLM Benefit Table and scientific method enforcement in the backlog.

## 3. Functional Requirements

### 3.0 Protocol Compliance Update (2025-06-24)
- All entrypoints use Pydantic models: `NLPBusinessQueryInput` (input) and `NLPBusinessQueryResult` (output).
- HITL protocol fields (`human_action_required`, `human_action_type`, `human_action_context`) are present and validated.
- All event logging is async/awaited and structured.
- YAML contract context (`yaml_contract_text`) is always propagated via the orchestrator and accessed in all protocol-compliant methods.
- Orchestrator controls all agent instantiation and registration; no self-registration logic.
- All integration and end-to-end tests must use orchestrator-driven workflows.
- Example usage and documentation must show orchestrator-driven invocation and registry integration.
- All input/output model references must match those in `agent_config_models.py`.

### 3.1 Core NLP Capabilities

#### 3.1.5 Natural Language to Data Query (NLQ) Capability

- The agent must support matching business questions to KPIs using both the `kpi_name` and all synonyms defined in the KPI registry. The registry now includes a `synonyms` column (comma-separated), and the agent must check both the technical name and all synonyms when resolving a KPI from a business question.
- This enables robust matching for business terms such as "sales", "revenue", "discounts", and other common synonyms, ensuring user queries are mapped to the correct technical KPI.


- When present, the agent must use `yaml_contract_text` from the context to inform schema mapping, business term resolution, and query validation.

- The agent must detect and extract TopN/BottomN intent (e.g., "top 5 regions by revenue", "bottom 10 products by sales") from the user's natural language query. This must be passed as a structured parameter (e.g., {"limit_type": "top", "limit_n": 5, "limit_field": "revenue"}) in the protocol output for downstream query assembly and enforcement. If the user's request is ambiguous (e.g., "top regions" without a number), default to a configurable N (e.g., 10).

- The agent pipeline must invoke the Data Governance Agent to resolve business terms to technical columns/KPIs.
- If any terms cannot be mapped, the agent must escalate to HITL by setting output fields:
    - `human_action_required: True`
    - `human_action_type: "clarification"`
    - `human_action_context`: includes unmapped terms and a user-facing message.
- The LLM or UI must prompt the principal to clarify or select mappings for these terms before continuing.
- The agent must support interpreting natural language business queries from Principals or Agents and transforming them into structured data queries against the MCP data service.
- The pipeline must include:
  1. **Intent Parsing**: Extract the data product, aggregation/groupby, filters, and other query parameters from the user's natural language question.
  2. **Schema Awareness**: Reference the available data products and columns (from the MCP registry or a cached schema) to validate and ground the query.
  3. **Query Generation**: Translate the parsed intent into a structured API call (HTTP GET with query parameters) to the MCP service. Optionally, support SQL query generation if the MCP exposes a SQL endpoint.
  4. **MCP Integration**: Call the MCP service endpoint, handle the response, and format it for the user or downstream agent.
  5. **Synonym/Mapping Support**: Map business terms (e.g., "customer" or "revenue") to technical attribute names used in the data registry.
  6. **Robust Error Handling**: Handle unmapped terms, unsupported queries, and MCP errors gracefully, providing actionable feedback.

- Example workflow:
  - Input: "Show me total value by customer for product X in 2024"
  - Intent Parsing Output: {product_id: ..., groupby: "customer", filters: {product: "X", year: 2024}, aggregation: "sum", measure: "value"}
  - API Call: `/data-product/{product_id}?groupby=customer&filter=product:X,year:2024`
  - MCP returns JSON result, which is formatted for the end user.

- The agent must be extensible to support new query types, filters, and aggregations as the MCP evolves.
- The NLQ capability must be covered by integration and end-to-end tests with example business queries and expected API calls/results.

#### 3.1.6 Entity Extraction as Core Capability (MVP)

#### 3.1.7 LLM Explainability Compliance (2025-06-24)
- All summary and key point fields in document analysis are routed through the A9_LLM_Service_Agent for explainability and business-user-friendly output.
- LLM calls are protocol-compliant, orchestrator-driven, and fully async with structured event logging and error handling.
- See agent card for implementation and compliance details.

- When present, the agent must use `yaml_contract_text` from the context to improve entity mapping and validation.

- **Objective:**
  - Extract business-relevant entities (e.g., company, department, region, product, date) from user business questions and natural language queries.
  - Output structured entities that can be mapped to principal context and used as filters in downstream data product/API calls.

- **Justification:**
  - Many filters required for secure, context-aware query generation are derived from the Principal context (e.g., department, region, business unit).
  - Robust entity extraction is essential to ensure that queries are properly scoped, access-controlled, and relevant to the user's business context.
  - Without entity extraction, Agent9 cannot reliably map user intent to secure, personalized queries.

- **Requirements:**
  1. The agent MUST implement and expose only the `entity_extraction` NLP model for the MVP. All other NLP models (document analysis, relationship analysis, sentiment analysis) are to be omitted or stubbed until post-MVP.
  2. Entity extraction MUST:
     - Accept a natural language business question as input.
     - Return a list of entities, each with at least `type` and `value` fields (e.g., `{type: "department", value: "Finance"}`).
     - Support extensibility for additional entity types as business needs evolve.
     - Be directly integrated with the orchestrator's principal context filter application logic.
     - Be covered by integration and end-to-end tests using real-world business queries and principal contexts.
  3. The entity extraction method MUST be robust to synonyms, abbreviations, and common business language variations.
  4. The agent MUST escalate to HITL if ambiguous or unmapped entities are detected, with actionable feedback for the user.

- **Example Workflow:**
  - Principal context: `{ department: "Finance", region: "EMEA" }`
  - User question: "Show payroll for April 2023"
  - Entity extraction output: `[{'type': 'date', 'value': 'April 2023'}]`
  - Orchestrator applies principal context: `[{'type': 'department', 'value': 'Finance'}, {'type': 'region', 'value': 'EMEA'}]`
  - Final query is filtered by both extracted and principal context entities.

- **Notes:**
  - Entity extraction is the foundation for secure, context-aware NLQ-to-SQL/data product workflows in Agent9.
  - All future NLP model enhancements should build on this robust entity extraction core.

#### 3.1.6 Business Query Parsing via LLM (NEW)
- The agent provides an async method `parse_business_query(input: NLPBusinessQueryInput) -> NLPBusinessQueryResult`.
- This method is orchestrator-driven, protocol-compliant (Pydantic input/output), and delegates intent parsing to the LLM Service Agent.
- It takes a business query (as business terms) and a data product agent reference, retrieves the KPI registry, and uses the LLM to extract structured intent (KPI, groupings, filters).
- Handles errors according to protocol, logs all actions, and enforces HITL protocol if enabled (fields: `human_action_required`, `human_action_type`, `human_action_context`).
- Only accessible via the orchestrator/registry pattern; not for direct instantiation.
- Example input/output:
  - Input: `NLPBusinessQueryInput(business_terms=["total revenue by region 2024"], data_product_agent=...)`
  - Output: `NLPBusinessQueryResult(matched_views=[{"kpi_name": ..., "groupings": ..., "time_filter": ...}], unmapped_terms=[...], ... )`
- Test coverage must include integration with the orchestrator, LLM agent, error/HITL handling, and edge cases for unmapped terms.
- Usage documentation and examples:

  **parse_business_query usage example:**
  ```python
  from src.agents.new.A9_NLP_Interface_Agent import A9_NLP_Interface_Agent
  from src.agents.new.agent_config_models import A9NLPInterfaceAgentConfig, NLPBusinessQueryInput
  config = {
      "name": "A9_NLP_Interface_Agent",
      "version": "1.0",
      "capabilities": ["nlq", "document_analysis", "parse_business_query"],
      "config": {},
      "hitl_enabled": False
  }
  agent = A9_NLP_Interface_Agent(config)
  input_model = NLPBusinessQueryInput(
      business_terms=["Show me the top 5 regions by revenue for 2024"],
      data_product_agent=...,
      principal_context={"filters": {"region": "North America"}}
  )
  result = await agent.parse_business_query(input_model)
  # Access result.topn, result.filters, result.principal_context, result.human_action_required, etc.
  ```

- **Output Protocol Fields:**
  - `matched_views`: List[dict] — NLQ intent resolution (KPI/groupings/time/filter)
  - `unmapped_terms`: List[str] — Terms not mapped during parsing
  - `filters`: dict — Final filters applied (business or technical)
  - `topn`: dict — TopN/BottomN extraction (e.g., {"limit_type": "top", "limit_n": 5, "limit_field": "revenue"})
  - `principal_context`: dict — Principal context used for defaults/filters
  - `human_action_required`: bool — True if HITL escalation is required
  - `human_action_type`: str — Type of HITL action (e.g., "clarification")
  - `human_action_context`: dict — Context for HITL (e.g., unmapped terms, user message)


#### 3.1.1 Document Analysis
- Process structured and unstructured documents
- Extract key information and entities
- Perform sentiment analysis
- Identify relationships between entities
- Accept technical attribute names and code values as filters (not business English)
- Example interface:
  - `async def analyze_document(document: str, filters: Dict[str, Any]) -> DocumentAnalysis`
- Input must be output from Data Governance Agent (already translated)
- Output: Structured summary, key points, entities, relationships, and confidence score
- Example:
```python
# Input (from governance agent)
filters = {"REGION_CODE": "NA", "PROD_CODE": "CE"}
result = await nlp_agent.analyze_document("Revenue by Business Unit for Q1", filters=filters)
# Output (DocumentAnalysis)
{
  "summary": "Revenue for North America, Consumer Electronics is above target.",
  "key_points": ["Growth YoY: 8%", "Margin: 12%"],
  "entities": [...],
  "relationships": [...],
  "confidence": 0.95
}
```
- Must validate all filter keys/values and handle unmapped filters with robust error handling
- Log all analysis attempts, successes, and failures

#### 3.1.2 Entity Recognition
- Identify business-specific entities
- Classify entities by type
- Extract relationships between entities
- Handle enterprise-specific terminology

#### 3.1.3 Relationship Analysis
- Identify relationships between business entities
- Analyze document relationships
- Create entity relationship graphs
- Generate relationship visualizations

#### 3.1.4 Business Context
- Understand business-specific terminology
- Process industry-specific documents
- Handle enterprise-specific data formats
- Maintain business context awareness

### 3.2 ERP System Integration

#### 3.2.1 Supported Systems
- SAP (S/4HANA, BW, HANA)
- Oracle (E-Business Suite, Cloud ERP)
- Microsoft Dynamics
- Other major ERP systems

#### 3.2.2 Integration Features
- Secure connection to ERP systems
- Data format conversion
- Error handling and recovery
- Performance optimization

### 3.3 Security Requirements
- Secure data transmission
- Role-based access control
- Audit logging
- Compliance with data protection regulations

## 4. Non-Functional Requirements

### 4.1 Performance
- Process documents in real-time
- Handle large document volumes
- Maintain consistent performance
- Support concurrent processing

### 4.2 Scalability
- Scale horizontally
- Support multiple ERP connections
- Handle increasing document volumes
- Maintain performance under load

### 4.3 Reliability
- High availability architecture
- Automatic failover
- Data backup and recovery
- Error handling and recovery

## 5. Technical Requirements

### 5.1 System Architecture
- Microservices-based architecture
- RESTful API interface
- Containerized deployment
- Cloud-native design

### 5.2 Technology Stack
- Python 3.10+
- FastAPI for REST API
- SQLAlchemy for database
- Docker for containerization
- Kubernetes for orchestration

### 5.3 Integration Points
- ERP system APIs
- Authentication services
- Logging infrastructure
- Monitoring system

### 5.4 Performance Optimization
- Implements YAML contract caching mechanism for improved performance
- Provides optimized contract access during agent operation
- Reduces redundant parsing and processing of YAML contracts

### 5.5 Entity Extraction Implementation
- Implements regex-based entity extraction for standard entity types
- Provides extensible pattern matching for custom entity recognition
- Supports entity normalization and standardization
- Includes confidence scoring for extracted entities

### 5.6 HITL Escalation
- Implements protocol-compliant HITL escalation logic
- Provides structured context for human review and intervention
- Supports configurable escalation thresholds
- Includes detailed logging of escalation events

### 5.7 Error Handling
- Implements comprehensive error handling for all agent operations
- Provides standardized error response format
- Supports graceful degradation for partial failures
- Includes detailed error logging for troubleshooting

## 6. Implementation Phases

### Phase 1: Core NLP Engine (2 weeks)
- Basic NLP processing
- Core document analysis
- Basic entity recognition
- Initial error handling

### Phase 2: ERP Integration (2 weeks)
- ERP system connections
- Data format conversion
- Basic integration tests
- Security implementation

### Phase 3: Advanced Features (2 weeks)
- Relationship analysis
- Business context processing
- Performance optimization
- Advanced error handling

### Phase 4: Testing and Documentation (1 week)
- Comprehensive testing
- Performance testing
- Security testing
- Documentation creation

## 7. Dependencies

### 7.1 External Dependencies
- ERP system licenses
- NLP service subscriptions
- Cloud infrastructure
- Security services

### 7.2 Internal Dependencies
- Agent Registry
- Authentication System
- Logging Infrastructure
- Monitoring System

## 8. Agent Requirements

### 8.1 Core Agent Interface
- Follow Agent9 agent registry interface requirements
- Implement required registry integration methods
- All document analysis functions must be async
- Input must be compatible with Data Governance Agent output
- Use standard error handling patterns
- Maintain consistent logging
- Log all integration attempts and failures

### 8.2 Configuration Management
- Support default configuration values
- Validate configuration on initialization
- Maintain configuration state
- Handle agent-specific configuration

### 8.3 Error Handling
- Implement structured error handling
- Log errors appropriately
- Return consistent error responses
- Handle common error types (connection, processing, validation)
- Validate all technical attribute names and filter code values
- Handle unmapped filters/attributes with robust error handling

### 8.4 Logging
- Initialize agent-specific logger
- Log initialization and major operations
- Support different log levels
- Include timestamps in logs

### 8.5 Core Methods
- Implement _initialize for setup
- Implement _setup_logging for logging
- Implement _setup_error_handling for error management
- Implement create_from_registry class method
- Implement analyze_document as async, accepting technical filters

### 8.6 Error Types
- ConfigurationError: Invalid configuration
- RegistrationError: Failed to register with registry
- ProcessingError: Failed to process data
- ValidationError: Invalid input data
- ConnectionError: Connection failures
- UnmappedFilterError: Provided filter could not be mapped to a technical attribute

## 9. Testing Requirements (NEW, MVP Alignment)
- Test orchestrator-driven business query parsing (parse_business_query) with LLM Service Agent
- Validate protocol compliance (Pydantic input/output)
- Test error and HITL handling paths
- Test unmapped terms and edge cases
- Document test coverage and assumptions (pending usage example update)

- Test document analysis with technical filters (integration with Data Governance Agent)
- Test input validation for technical attribute names/code values
- Test error handling for unmapped filters/attributes
- Test async operation and registry integration
- Test integration with Data Product Agent (end-to-end flow)
- Document test coverage and assumptions

## 10. Acceptance Criteria

### 10.0 Protocol Compliance (2025-06-24)
- All entrypoints use only protocol-compliant models as defined in code.
- Orchestrator-driven lifecycle is enforced; no agent-side registration or direct instantiation in documentation or code samples.
- All event logging is async/awaited and uses `A9_SharedLogger`.
- YAML contract context is always propagated and accessed via the context kwarg.
- All tests and usage examples are orchestrator-driven.

### 10.1 Functional
- Successful ERP system integration
- Accurate document processing
- Proper error handling
- Complete documentation

### 10.2 Non-Functional
- Performance meets requirements
- Security requirements met
- Scalability verified
- Documentation complete

## 11. Maintenance and Support

## 12. Compliance: YAML Contract Context
- The agent must always check for and apply `yaml_contract_text` from the context if present, for all entrypoints. This is required for A2A protocol compliance and is enforced by orchestrator-driven workflow execution and tests.

### Example: Accessing YAML Contract Context in a Protocol-Compliant Method
```python
# In any protocol-compliant agent method:
def some_method(self, input_model, context=None):
    yaml_contract = context.get('yaml_contract_text') if context else None
    # Use yaml_contract for schema mapping, validation, etc.
```

## 13. Roadmap and Future Enhancements

- **SQL Query Support:**
  - Future versions will support generating SQL statements from natural language queries and submitting them to the MCP data service if a SQL endpoint is available.
  - The agent will be able to translate NLQ into SQL for advanced analytics and BI tool compatibility.
  - Planned support for SQL dialects compatible with DuckDB and major enterprise data platforms.

### 13.1 Maintenance
### 11.1 Maintenance
- Regular updates
- Security patches
- Performance optimization
- Documentation updates

### 11.2 Support
- User documentation
- API documentation
- Troubleshooting guide
- Support channels

