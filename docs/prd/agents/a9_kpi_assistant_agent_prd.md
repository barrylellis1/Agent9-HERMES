# A9_KPI_Assistant_Agent Product Requirements Document

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2026-01-24
-->

## 1. Overview

### 1.1 Purpose
The A9_KPI_Assistant_Agent provides an LLM-powered conversational interface for defining comprehensive KPIs during data product onboarding. It analyzes schema metadata, suggests business-relevant KPIs with complete attribute sets including strategic metadata tags, and enables iterative refinement through natural language interaction.

### 1.2 Scope
This document outlines the requirements for version 1.0 of the A9_KPI_Assistant_Agent, focusing on KPI suggestion, validation, and conversational refinement capabilities within the data product onboarding workflow.

### 1.3 Target Audience
- Data Product Owners
- Business Analysts
- Data Governance Teams
- Executive Stakeholders

## 2. Business Requirements

### 2.1 Business Objectives
1. Accelerate KPI definition during data product onboarding
2. Ensure KPIs include complete strategic metadata (line, altitude, profit_driver_type, lens_affinity)
3. Reduce manual effort in KPI specification through LLM assistance
4. Enforce governance and ownership metadata from the start
5. Enable business users to define KPIs conversationally without deep technical knowledge

### 2.2 Key Metrics
- KPI suggestion generation time: < 10 seconds
- KPI attribute completeness: 100% (all required fields)
- Strategic metadata coverage: 100% (line, altitude, profit_driver_type, lens_affinity)
- User satisfaction with suggestions: > 80%
- Reduction in manual KPI definition time: > 50%

## 3. Functional Requirements

### 3.1 Core KPI Suggestion

#### 3.1.1 Schema-Based KPI Generation
- Analyze schema metadata from Data Product Agent inspection results
- Identify measures, dimensions, time columns, and identifiers
- Generate 3-7 business-relevant KPI suggestions based on schema analysis
- Include complete KPI attribute sets:
  - Core attributes: id, name, domain, description, unit, data_product_id
  - SQL query using available schema elements
  - Dimensions for drill-down analysis
  - Thresholds for situation detection
  - Strategic metadata tags
  - Governance metadata (owner, stakeholders, business processes)

#### 3.1.2 Strategic Metadata Enforcement
- Ensure all KPIs include strategic metadata tags:
  - **line**: top_line (revenue), middle_line (operational), bottom_line (profit/cost)
  - **altitude**: strategic, tactical, operational
  - **profit_driver_type**: revenue, expense, efficiency, risk
  - **lens_affinity**: bcg, bain, mckinsey, etc.
- Validate logical consistency (e.g., top_line should align with revenue driver)
- Provide rationale for strategic metadata assignments

#### 3.1.3 LLM Service Integration
- Use A9_LLM_Service_Agent for all natural language processing
- Support configurable LLM providers (OpenAI, Anthropic)
- Apply domain-specific prompts about business metrics and strategic frameworks
- Parse LLM responses into structured KPI definitions
- Handle JSON extraction from code blocks and markdown formatting

### 3.2 Conversational Refinement

#### 3.2.1 Interactive Chat Interface
- Maintain conversation history per session
- Accept natural language requests to modify KPIs
- Support operations:
  - Adjust thresholds
  - Change dimensions
  - Modify strategic metadata
  - Update governance mappings
  - Refine SQL queries
  - Add/remove KPIs

#### 3.2.2 Context-Aware Responses
- Provide schema-aware suggestions
- Reference current KPI definitions in responses
- Explain strategic metadata choices
- Suggest improvements based on best practices

### 3.3 KPI Validation

#### 3.3.1 Attribute Validation
- Verify all required fields are present
- Check strategic metadata values against allowed enums
- Validate logical consistency of metadata combinations
- Ensure SQL queries reference valid schema elements

#### 3.3.2 Schema Validation
- Verify dimensions exist in schema
- Check measure columns are available
- Validate time columns for temporal analysis
- Ensure identifiers are properly referenced

#### 3.3.3 Governance Validation
- Validate owner_role is specified
- Check stakeholder lists are non-empty
- Ensure business_process mappings are provided
- Verify governance metadata completeness

### 3.4 KPI Finalization

#### 3.4.1 Contract Integration
- Format validated KPIs for data product contract YAML
- Coordinate with Data Product Agent for contract updates
- Trigger registry updates after finalization
- Maintain KPI versioning and change history

#### 3.4.2 Registry Integration
- Register finalized KPIs with KPI Registry
- Update data product metadata with KPI references
- Enable discovery of KPIs by domain, business process, and strategic tags

## 4. Integration Requirements

### 4.1 Data Product Agent Integration
- Consume schema metadata from `inspect_source_schema` results
- Coordinate with `generate_contract_yaml` for KPI inclusion
- Trigger `register_data_product` after KPI finalization
- Support both DuckDB and BigQuery data sources

### 4.2 Data Governance Agent Integration
- Validate owner roles and stakeholder principals
- Enforce governance policies on KPI definitions
- Coordinate ownership and access control mappings

### 4.3 LLM Service Agent Integration
- Use async `generate` method for all LLM calls
- Provide structured prompts with schema context
- Handle LLM errors gracefully with fallback options
- Log all LLM interactions for audit and debugging

### 4.4 Orchestrator Integration
- Support orchestrator-driven lifecycle (async `create` factory)
- Implement protocol-compliant request/response models
- Enable workflow integration for multi-step onboarding
- Maintain stateless operation (conversation history in memory, not persisted)

## 5. Non-Functional Requirements

### 5.1 Performance
- KPI suggestion generation: < 10 seconds
- Chat response latency: < 5 seconds
- Validation checks: < 1 second
- Support concurrent sessions: 10+ simultaneous users

### 5.2 Reliability
- Graceful degradation if LLM service unavailable
- Fallback to manual KPI definition
- Comprehensive error messages for validation failures
- Retry logic for transient LLM errors

### 5.3 Security
- No storage of sensitive schema data
- Audit logging of all KPI definitions
- Principal-based access control
- Secure LLM API key management

### 5.4 Maintainability
- Clear separation of concerns (suggestion, validation, chat)
- Modular prompt templates for easy updates
- Comprehensive unit and integration tests
- Agent card documentation for compliance

## 6. User Experience Requirements

### 6.1 UI Integration
- Embedded chat interface in data product onboarding workflow
- Real-time KPI card updates during conversation
- Color-coded strategic metadata badges
- Clear error messages and validation feedback

### 6.2 Conversation Flow
1. Auto-generate initial KPI suggestions on schema discovery
2. Display suggestions with rationale
3. Enable natural language refinement
4. Show updated KPIs in real-time
5. Provide "Finalize" action to complete workflow

### 6.3 Help and Guidance
- Inline tooltips for strategic metadata tags
- Example queries for common refinement requests
- Validation warnings with suggested fixes
- Best practice recommendations

## 7. Technical Architecture

### 7.1 Agent Structure
```python
class A9_KPI_Assistant_Agent:
    - config: A9_KPI_Assistant_Agent_Config
    - llm_agent: A9_LLM_Service_Agent
    - conversation_history: Dict[str, List[Dict]]
    
    async def suggest_kpis(request: KPISuggestionRequest) -> KPISuggestionResponse
    async def chat(request: KPIChatRequest) -> KPIChatResponse
    async def validate_kpi(request: KPIValidationRequest) -> KPIValidationResponse
    async def finalize_kpis(request: KPIFinalizeRequest) -> KPIFinalizeResponse
```

### 7.2 Request/Response Models
- All models inherit from `A9AgentBaseRequest` / `A9AgentBaseResponse`
- Include `request_id` and `principal_id` for audit trail
- Support optional fields with sensible defaults
- Enable error responses with detailed messages

### 7.3 Configuration
```python
class A9_KPI_Assistant_Agent_Config:
    llm_provider: str = "openai"
    llm_model: str = "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: int = 4096
    default_num_suggestions: int = 5
    enforce_strategic_metadata: bool = True
    validate_sql: bool = True
```

## 8. Testing Requirements

### 8.1 Unit Tests
- Test KPI suggestion generation with mock LLM responses
- Validate JSON parsing from various LLM output formats
- Test strategic metadata validation logic
- Verify schema validation against mock schemas

### 8.2 Integration Tests
- Test end-to-end with real LLM Service Agent
- Validate Data Product Agent integration
- Test conversation flow with multiple turns
- Verify registry updates after finalization

### 8.3 User Acceptance Tests
- Business users can define KPIs without technical knowledge
- Strategic metadata is consistently applied
- Validation catches common errors
- Conversation refinement produces expected results

## 9. Deployment and Operations

### 9.1 Deployment
- Deploy as part of Agent9 orchestrator ecosystem
- Register with orchestrator agent factory
- Configure LLM provider credentials via environment variables
- Enable/disable via feature flags

### 9.2 Monitoring
- Track LLM token usage and costs
- Monitor suggestion generation latency
- Log validation failure rates
- Alert on LLM service errors

### 9.3 Maintenance
- Update prompt templates based on user feedback
- Refine strategic metadata inference logic
- Expand validation rules as needed
- Keep LLM model versions current

## 10. Future Enhancements

### 10.1 Phase 2 Features
- Persistent conversation history across sessions
- KPI templates library for common patterns
- Multi-language support for international users
- Advanced analytics on KPI usage patterns

### 10.2 Phase 3 Features
- Automated KPI monitoring and alerting
- Integration with BI tools for visualization
- Collaborative KPI definition with multiple stakeholders
- AI-powered KPI optimization recommendations

## 11. Dependencies

### 11.1 Internal Dependencies
- A9_LLM_Service_Agent (required)
- A9_Data_Product_Agent (required)
- A9_Data_Governance_Agent (optional, for validation)
- A9_Orchestrator_Agent (required)

### 11.2 External Dependencies
- OpenAI API or Anthropic API
- Pydantic >= 2.10.6
- Python >= 3.11

## 12. Compliance and Standards

### 12.1 Agent9 Design Standards
- Follows orchestrator-driven lifecycle
- Implements protocol-compliant A2A communication
- Uses async factory pattern for instantiation
- Maintains structured logging
- Includes comprehensive agent card

### 12.2 Data Governance
- Enforces ownership metadata on all KPIs
- Supports audit trail via request_id tracking
- Respects principal-based access control
- Maintains data lineage through registry integration

---
*Version: 1.0  |  Created: 2026-01-24  |  Status: Active*
