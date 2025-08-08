# A9_Data_Governance_Agent PRD

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2025-07-17
-->


## Overview
**Purpose:** Ensure data quality, security, and compliance through comprehensive data governance, policy enforcement, and continuous monitoring

**YAML Contract Context:**
The agent must read and respond to `yaml_contract_text` provided in the context by the orchestrator, supporting protocol-compliant workflows that leverage YAML-driven data product contracts for schema, mapping, dependencies, and governance enforcement.
**Agent Type:** Core Agent
**Version:** 1.0
**Template:** Follows A9_Agent_Template patterns

## Functional Requirements

- When present, the agent must use `yaml_contract_text` from the context to inform schema, mapping, dependency resolution, and policy enforcement.

### Calculated KPI Support
- The Data Governance Agent SHALL support calculated KPIs, where the value is computed from a formula defined in the business glossary/registry (e.g., Gross Margin = Gross Revenue - Cost of Goods Sold).
- The agent SHALL resolve dependencies between KPIs, allowing formulas to reference other KPIs recursively.
- All formulas and dependencies SHALL be documented, versioned, and auditable in the business glossary/registry.
- The agent SHALL log and escalate (via HITL) any missing data or unmapped KPI references encountered during calculation.

### DuckDB View Strategy for KPI Calculation
- The primary mechanism for implementing calculated KPIs SHALL be via DuckDB views, where business logic and formulas are defined in the database schema.
- Agents SHALL map business terms to DuckDB view names and columns, leveraging the business glossary/registry for governance and traceability.
- Routine KPI calculations and multi-step formulas SHOULD be implemented in DuckDB SQL/views whenever feasible, using CTEs, CASE WHEN, and window functions as needed.
- The agent layer SHALL only escalate to HITL or perform Python-side calculation if a KPI cannot be computed via DuckDB view logic (e.g., missing data, ambiguous mapping, or business rule not expressible in SQL).
- View definitions SHOULD be version-controlled and referenced in the business glossary/registry for auditability.


### Business Glossary and Synonym Matching
- The Data Governance Agent SHALL use a governed Business Glossary (registry/data asset) as the authoritative source for business terms, synonyms, aliases, definitions, and technical attribute mappings.
- The glossary SHALL support dynamic synonym and alias matching for business term and filter translation, enabling robust NLP and business query support.
- The glossary SHALL be versioned, auditable, and updatable by data stewards/governance teams without code changes.
- The Data Governance Agent SHALL load and use this registry for all mapping operations, and log all unmapped or ambiguous terms for HITL escalation and audit.



### HITL Escalation for Unmapped Terms
If, after business glossary resolution, any business terms remain unmapped to canonical data product columns or KPIs, the agent must:
- Set `human_action_required: True` in the protocol output.
- Set `human_action_type: "clarification"` and provide a `human_action_context` that lists the unmapped terms and a message for the user.
- Downstream agents or the UI must prompt the principal for clarification or mapping of these terms before proceeding to query execution.

Example protocol output:
```json
{
  "resolved_terms": ["REVENUE_GROWTH"],
  "unmapped_terms": ["sales velocity"],
  "human_action_required": true,
  "human_action_type": "clarification",
  "human_action_context": {
    "unmapped_terms": ["sales velocity"],
    "message": "Please clarify or map these terms before proceeding."
  }
}
```

### Core Capabilities

- **YAML Contract Context Support:** Reads and applies YAML-driven data product contract metadata from the workflow context for schema, mapping, and policy enforcement.
1. Business-to-Technical Translation (NEW, MVP Alignment)
   - Translate business terms (responsibilities, filters) into technical attribute names and code values
   - Resolve ambiguities and map business language to data product metadata
   - Provide code value normalization for filter values
   - Implement Pydantic model-based input/output interfaces:
     - `async def translate_terms(input_model: A9_Data_Governance_TermTranslationInput) -> A9_Data_Governance_TermTranslationOutput`
     - `async def translate_filters(input_model: A9_Data_Governance_FilterTranslationInput) -> A9_Data_Governance_FilterTranslationOutput`
   - Return technical names and code values matching Data Product Agent expectations
   - Handle unmapped or ambiguous terms with robust error handling and logging
   - Provide usage statistics and metadata for translated terms
   - Calculate quality scores for term translations
   - Support key-value mapping for business-to-technical term translation
   - Implement configurable mapping dictionaries for terms and values
   - Log all translation activities with timestamps for audit purposes
   - Support protocol-compliant event logging for all translation operations

2. Dimensional Filter Translation and Forwarding
   - The agent must accept business filters (e.g., {"region": "North America"}) and translate both the filter keys (dimensions) and values to technical column names and code values as required by the Data Product/Data Source Agent.
   - After translation, all technical filters must be included in the agent protocol output and forwarded to the Data Source Agent for query processing.
   - If any filter key or value cannot be mapped, escalate to HITL for clarification, listing unmapped filters in `human_action_context`.

   Example protocol output:
   ```json
   {
     "resolved_terms": ["REVENUE_GROWTH"],
     "resolved_filters": {"REGION_CODE": "NA", "PROD_CODE": "CE"},
     "unmapped_terms": [],
     "unmapped_filters": {"region": "Europe"},
     "human_action_required": true,
     "human_action_type": "clarification",
     "human_action_context": {
       "unmapped_filters": {"region": "Europe"},
       "message": "Please clarify or map these filters before proceeding."
     }
   }
   ```

2. Data Quality Management
   - Monitor data quality through comprehensive metrics
   - Implement quality rules with configurable thresholds
   - Track quality metrics including completeness, accuracy, consistency, and timeliness
   - Generate detailed quality reports with scores and recommendations
   - Create data-driven improvement plans based on quality analysis
   - Support Pydantic model-based quality assessment
   - Provide structured input/output models for quality analysis
   - Implement threshold-based quality alerting
   - Generate actionable recommendations based on quality scores

3. Data Lineage Tracking
   - Track data sources
   - Resolve data asset paths via orchestrator-mediated workflows
   - Support role-based access control for data assets
   - Provide audit logs for data access and lineage

4. Protocol-Compliant Event Logging
   - Implement registry-based event logging for all agent operations
   - Log agent registration events with timestamps
   - Track all term and filter translation activities
   - Provide detailed debug logging for troubleshooting

5. Configuration Management
   - Support dynamic configuration updates with validation
   - Implement Pydantic v2 model validation for all configurations
   - Provide structured error handling for configuration issues
   - Support orchestrator-controlled registration compliance

6. KPI Registry Integration
   - Query KPIs by business process
   - Support business-to-technical term mapping
   - Implement KPI dependency resolution
   - Provide structured output models for KPI queries
   - Monitor data flow
   - Maintain data history
   - Generate lineage reports
   - Create lineage documentation

4. Data Access Control
   - Implement access policies
   - Manage user permissions
   - Track access logs
   - Generate access reports
   - Create audit trails

5. Policy Enforcement
   - Implement data policies
   - Monitor policy compliance
   - Generate policy reports
   - Create policy documentation
   - Update policy guidelines

6. Compliance Monitoring
   - Monitor regulatory compliance
   - Track compliance metrics
   - Generate compliance reports
   - Create compliance documentation
   - Update compliance status



## Hackathon Quick Start

### Development Environment Setup
- Clone the Agent9-Hackathon-Template repository
- Install required dependencies from requirements.txt
- Configure environment variables in .env file based on .env.template

### Key Files and Entry Points
- Main agent implementation: `src/agents/new/A9_Data_Governance_Agent_Agent.py`
- Configuration model: `src/agents/new/agent_config_models.py`
- Agent card: `src/agents/new/cards/a9_data_governance_agent_agent_card.py`

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

## Compliance: YAML Contract Context
- The Data Governance Agent must always check for and apply `yaml_contract_text` from the context if present, for all agent entrypoints. This is required for A2A protocol compliance and is enforced by orchestrator-driven workflow execution and tests.

### Example: Accessing YAML Contract Context in a Protocol-Compliant Method
```python
# In any protocol-compliant agent method:
def some_method(self, input_model, context=None):
    yaml_contract = context.get('yaml_contract_text') if context else None
    # Use yaml_contract for schema, mapping, governance enforcement, etc.
```

## New Core Capability: Semantic Query Validation & Enforcement

### Purpose
Ensure that all semantic queries generated for analytic requests are compliant with data governance, access control, and KPI definition policies.

### Function to Add
- `validate_semantic_query(query: str, user_context: dict) -> dict`:
  Validates the generated query for compliance, access, and policy. Returns approval, redactions, or warnings.

### Usage Flow
1. Orchestrator receives a semantic query from the Data Product Agent.
2. Orchestrator calls Data Governance Agent to validate the query before execution.
3. Data Governance Agent returns approval, warnings, or required changes.

### Test Cases
- Given a query and user context, the agent approves or blocks access based on policy.
- Redacts sensitive fields for unauthorized users.

### Modification History
- 2025-05-24: Added semantic query validation and enforcement function for NLP-driven analytics.

### Integration Requirements (NEW, MVP Alignment)
- Support registry-based integration (A9_Agent_Template pattern)
- All translation and governance functions must be async
- Use absolute imports
- Standardize error handling (ConfigurationError, ProcessingError, ValidationError)
- Log translation attempts, successes, and failures

### Test Requirements (NEW, MVP Alignment)
- Test translation of business terms to technical names (including edge cases and unmapped terms)
- Test filter value normalization (English → code values)
- Test error handling for ambiguous/unmapped terms
- Test async operation and registry integration
- Document test coverage and assumptions

### Example Request/Response
```python
# Example: Translate business responsibilities and filters
governance_agent = ... # Registry lookup
tech_terms = await governance_agent.translate_terms(["Revenue by Business Unit"])
tech_filters = await governance_agent.translate_filters({"Region": "North America"})
# tech_terms -> ["REV_BY_BU"]
# tech_filters -> {"REGION_CODE": "NA"}
```

### Input Requirements
1. Data Governance Data
   - Data quality metrics
   - Access logs
   - Policy documents
   - Compliance requirements
   - Audit records

2. Analysis Parameters
   - Quality thresholds
   - Compliance requirements
   - Access controls
   - Policy guidelines
   - Monitoring schedules

### Output Specifications
1. Governance Artifacts
   - Quality reports
   - Lineage documentation
   - Access logs
   - Policy documentation
   - Compliance reports

2. Analytics
   - Quality dashboards
   - Lineage metrics
   - Access metrics
   - Policy compliance
   - Compliance status

3. Reports
   - Quality analysis
   - Lineage reports
   - Access reports
   - Policy status
   - Compliance metrics

## Technical Requirements

### Agent Implementation
- Follow A9_Agent_Template patterns
- All agent instantiation must use the async `create_from_registry` factory method, with no direct construction or manual registry instantiation.
- All agent entrypoints must strictly comply with the A2A protocol, accepting and returning **Pydantic model instances** for all inputs and outputs. Raw dicts/lists are not permitted.
- All registry lookups, agent creation, and agent-to-agent calls must be async and registry-compliant.
- Use standard error handling patterns from the template, including ConfigurationError, ProcessingError, ValidationError, and RegistrationError.
- Use absolute imports for all dependencies.

---

## Dynamic Data Asset Discovery & Path Resolution (2025-05-14)

### Overview
- Data Governance Agent is the authoritative source for all data asset locations in Agent9.
- All requests for data asset paths (e.g., KPI CSVs) must be resolved dynamically, not hardcoded.
- Asset path resolution is performed via async, registry-compliant APIs, delegating to the Data Product Agent for catalog lookups as needed.

### Responsibilities
- Maintain and validate the authoritative data sources registry (e.g., `data_sources.csv`).
- Implement and document `async get_data_asset_path(asset_name: str) -> DataAssetPathResponse`.
- Enforce role-based access control and compliance for asset path requests.
- Integrate with Data Product Agent for physical path resolution.
- Ensure all integration tests and orchestrator flows use dynamic path lookup.

### Integration Flow
1. Orchestrator or agent requests asset path from Data Governance Agent.
2. Data Governance Agent validates request, checks registry, and delegates to Data Product Agent as needed.
3. Data Product Agent returns the physical path, which is validated and returned to the caller.
4. All operations are async and fully registry-compliant.

### Checklist (see BACKLOG_REFOCUS.md for full tracking)
- [ ] Define Pydantic models for asset path requests/responses
- [ ] Implement `get_data_asset_path` in Data Governance Agent
- [ ] Implement `get_data_source_path` in Data Product Agent
- [ ] Refactor tests and orchestrator to use dynamic lookup
- [ ] Document and standardize the data sources registry
- [ ] Add/expand integration tests
- [ ] DRY up code and maintain organization

**See BACKLOG_REFOCUS.md for status and detailed tracking.**

## Protocol Compliance
- All agent entrypoints must strictly comply with the A2A protocol, accepting and returning **Pydantic models** for type safety, validation, and interoperability.
- The agent must implement all MCP (Minimum Compliance Protocol) requirements, including compliance checks, reporting, and error handling.
- Protocol compliance is mandatory for registry integration and agent orchestration.
- All agent-to-agent communication and registry interactions must use the async `create_from_registry` pattern for instantiation and dependency management.
- All test scripts and integration scenarios must use Pydantic models for all agent calls and assertions.

---
- Implement `create_from_registry` method for all agent instantiation
- Use standard error handling patterns
- Support async operations

### Integration Points
1. Data Systems
   - Connect to data sources
   - Interface with data warehouses
   - Integrate with data lakes
   - Connect to analytics systems
   - Interface with security systems

2. Output Systems
   - Generate reports
   - Create dashboards
   - Export metrics
   - Generate documentation

### Performance Requirements
1. Analysis Time
   - Basic analysis: < 1 hour
   - Comprehensive analysis: < 4 hours
   - Real-time monitoring: < 15 minutes

2. Processing
   - Handle large data volumes
   - Process complex data relationships
   - Maintain data accuracy
   - Support concurrent operations

### Scalability
1. Support for multiple data sources
2. Handle large data volumes
3. Scale with increasing complexity
4. Support cross-system analysis

## Error Handling
- Use standard error classes from A9_Agent_Template
- Error types:
  - ConfigurationError: Invalid configuration
  - RegistrationError: Failed to register with registry
  - ProcessingError: Failed to process data
  - ValidationError: Invalid input data
  - ConnectionError: Connection failures

## Security Requirements
1. Data Security
   - Secure data access
   - Protect sensitive data
   - Secure audit trails
   - Secure documentation

2. Access Control
   - Role-based access
   - Secure data sharing
   - Audit trail for changes
   - Policy approval workflows

## Monitoring and Maintenance
1. Regular data quality checks
2. Continuous policy monitoring
3. Periodic compliance reviews
4. Regular access audits

## Success Metrics
1. Data quality improvement
2. Policy compliance rate
3. Access control effectiveness
4. Compliance status
5. Governance efficiency

## Usage Flow
```
graph TD
    subgraph "Data Quality Management"
        DQM[Monitor Quality] -->|Implement Rules| DQM2[Track Metrics]
    end

    subgraph "Data Lineage Tracking"
        DLT[Track Sources] -->|Monitor Flow| DLT2[Generate Reports]
    end

    subgraph "Access Control"
        AC[Implement Policies] -->|Manage Permissions| AC2[Track Access]
    end

    subgraph "Policy Enforcement"
        PE[Implement Policies] -->|Monitor Compliance| PE2[Generate Reports]
    end

    subgraph "Compliance Monitoring"
        CM[Monitor Compliance] -->|Track Metrics| CM2[Generate Reports]
    end

    DQM2 --> DLT
    DLT2 --> AC
    AC2 --> PE
    PE2 --> CM
    CM2 --> DQM
```

## Notes
- Focuses on comprehensive data governance
- Works with data systems for governance
- Generates strategic governance recommendations
- Maintains governance baselines
- Supports continuous governance improvement

---

## Future Architecture & Roadmap



### Vision
The long-term architecture for business term conversion and NLP/data governance will combine the power of LLMs with a governed, dynamic, and auditable business glossary registry. This hybrid approach will enable:
- **LLM-accelerated planning and analysis**: LLMs will parse, strategize, and adapt analysis plans, but all business term/attribute mapping decisions will be validated against the business glossary registry.
- **Retrieval-Augmented Generation (RAG)**: LLMs will retrieve the latest glossary mappings and definitions at inference time, ensuring up-to-date, compliant mapping.
- **Agentic Deep Analysis**: Autonomous agents will decompose high-level goals into multi-step analysis plans, orchestrate sub-queries, and synthesize results, collaborating with Data Governance, Context, Data Product, and HITL agents.
- **Situation and Context Awareness**: Agents will maintain and update persistent situation models, supporting multi-turn, context-rich workflows.
- **Feedback & Learning Loops**: All mapping requests, errors, and human escalations will be logged, reviewed, and used to continuously improve glossary quality, LLM prompts, and analysis strategies.
- **Marketplace & Extensibility**: The architecture will support agent discoverability, reuse, and compliance for internal and external marketplace scenarios.

### Roadmap Highlights
- Integrate LLM-driven planning and adaptive querying in Deep Analysis Agent
- Implement RAG pattern for glossary lookups at inference time
- Enable multi-agent orchestration and persistent situation models
- Establish feedback and learning loops for continuous improvement
- Ensure all components are compliant, auditable, and marketplace-ready

---

## Post-MVP Enhancement: Business Glossary & Synonym Management

**Requirement:**
After MVP, the Data Governance Agent shall maintain and expose a centralized business glossary, including:
- Canonical business terms (e.g., “revenue”, “gross margin”, “customer”)
- Approved synonyms and alternate terms
- Mappings from business terms to technical fields/metrics/entities in SAP and non-SAP systems
- APIs/message types for term resolution, synonym lookup, and validation
- Governance workflows for adding, updating, and deprecating terms (with audit trails)

**Rationale:**
This enables consistent, governed, and explainable business semantics across all Agent9 agents and workflows. It supports NLP/LLM integration, cross-agent consistency, and semantic compliance.

**Integration Points:**
- NLP Integration Agent
- Data Product Agent
- Deep Analysis Agent
- Principal Context Agent

**Backlog Reference:**
Add to Agent9 backlog as “Data Governance Agent: Business Glossary & Synonym Management (Post-MVP Upgrade)”.
