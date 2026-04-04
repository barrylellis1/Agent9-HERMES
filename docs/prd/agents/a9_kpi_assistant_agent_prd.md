# A9_KPI_Assistant_Agent Product Requirements Document

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2026-04-01
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

## 9. Phase 9F: Adaptive Calibration Loop

### 9.1 Purpose

Transform the KPI Assistant from a one-time onboarding helper into an ongoing tuning advisor. The system gets smarter per client over time — this is the compounding moat: after 12 months, switching means losing calibrated profiles for 50+ KPIs, historical noise-vs-signal data, and validated decision outcomes.

### 9.2 Flow

#### Step 1 — Initial Onboarding (existing)
Admin registers KPIs with basic thresholds via existing `suggest_kpis` → `chat` → `finalize_kpis` flow.

#### Step 2 — Monitoring Profile Recommendation (new)
After KPI registration, KPI Assistant analyzes production data for each KPI:
- Queries historical data via `A9_Data_Product_Agent` (last 12–24 months where available)
- Computes: standard deviation, coefficient of variation, seasonality index, data completeness %
- LLM synthesizes statistical analysis into recommended monitoring profile fields:
  - `comparison_period`: `"MoM"` | `"QoQ"` | `"YoY"` — chosen based on natural business cadence
  - `volatility_band`: float — recommended as 1.5–2× the KPI's typical standard deviation
  - `min_breach_duration`: int — recommended based on data pattern (volatile KPIs get higher minimums)
  - `confidence_floor`: float — recommended based on data quality/completeness
  - `urgency_window_days`: int — recommended based on KPI domain (revenue = 7, cost = 30)
- Provides natural-language rationale: *"Gross Margin has ±1.8% quarterly variance and no seasonality. I recommend QoQ comparison, 2% volatility band, 2-period minimum breach duration."*

#### Step 3 — Conversational Refinement (extends existing chat)
Admin can challenge, adjust, or accept recommendations:
- *"That volatility band feels too tight for Q4"* → KPI Assistant adjusts with domain knowledge
- Refinement uses existing `chat` entrypoint with `session_id` context
- Admin accepts via `finalize_monitoring_profile` (new entrypoint — see below)

#### Step 4 — Parameters Persist on KPI Registry
`finalize_monitoring_profile` writes the accepted monitoring profile fields to the KPI registry record. SA uses them at runtime in `detect_situations`.

#### Step 5 — Recalibration After N Assessment Cycles
After N assessment cycles (configurable, default = 6 months / ~26 weekly runs):
- KPI Assistant queries VA outcome data and SA trigger data from Supabase
- Computes trigger accuracy per KPI: `(situations that led to approved action) / (total situations triggered)`
- Flags KPIs where trigger accuracy < configurable threshold (default 40%):
  - *"Revenue triggered 12 times, 5 led to approved action, 7 dismissed as noise. Recommend widening volatility band from ±5% to ±10%."*
- Admin reviews recalibration recommendations via the monitoring profile UI
- Approved recommendations update the KPI registry and take effect on the next assessment run

### 9.3 New Entrypoints

| Method | Description | Request Model | Response Model |
|--------|-------------|---------------|----------------|
| `analyze_kpi_volatility` | Queries production data, computes volatility stats for a KPI | `KPIVolatilityRequest` | `KPIVolatilityResponse` |
| `recommend_monitoring_profile` | LLM synthesizes volatility stats into recommended profile fields with rationale | `MonitoringProfileRequest` | `MonitoringProfileResponse` |
| `finalize_monitoring_profile` | Persists accepted monitoring profile fields to the KPI registry | `FinalizeMonitoringProfileRequest` | `FinalizeMonitoringProfileResponse` |
| `get_recalibration_recommendations` | Queries trigger accuracy data, returns KPIs needing recalibration | `RecalibrationRequest` | `RecalibrationResponse` |

### 9.4 New Request/Response Models

```python
class KPIVolatilityRequest(A9AgentBaseRequest):
    kpi_id: str
    data_product_id: str
    lookback_months: int = 24

class KPIVolatilityResponse(A9AgentBaseResponse):
    kpi_id: str
    std_dev: float
    coefficient_of_variation: float
    seasonality_detected: bool
    data_completeness_pct: float
    recommended_comparison_period: str  # "MoM" | "QoQ" | "YoY"
    analysis_notes: str

class MonitoringProfileRequest(A9AgentBaseRequest):
    kpi_id: str
    volatility_analysis: KPIVolatilityResponse
    admin_domain_notes: Optional[str] = None  # admin context for LLM

class MonitoringProfileResponse(A9AgentBaseResponse):
    kpi_id: str
    recommended_profile: MonitoringProfile
    rationale: str  # natural language explanation
    confidence: float

class MonitoringProfile(BaseModel):
    comparison_period: Literal["MoM", "QoQ", "YoY"]
    volatility_band: float
    min_breach_duration: int
    confidence_floor: float
    urgency_window_days: int

class FinalizeMonitoringProfileRequest(A9AgentBaseRequest):
    kpi_id: str
    monitoring_profile: MonitoringProfile

class FinalizeMonitoringProfileResponse(A9AgentBaseResponse):
    kpi_id: str
    success: bool
    message: str

class RecalibrationRequest(A9AgentBaseRequest):
    min_cycles: int = 26  # minimum assessment cycles before recalibration
    trigger_accuracy_threshold: float = 0.4

class RecalibrationResponse(A9AgentBaseResponse):
    kpis_reviewed: int
    kpis_needing_recalibration: List[KPIRecalibrationRecommendation]

class KPIRecalibrationRecommendation(BaseModel):
    kpi_id: str
    kpi_name: str
    current_profile: MonitoringProfile
    recommended_profile: MonitoringProfile
    trigger_accuracy: float
    total_triggers: int
    approved_actions: int
    rationale: str
```

### 9.5 Dependencies
- Phase 9A: `comparison_period`, `volatility_band`, `min_breach_duration`, `confidence_floor`, `urgency_window_days` fields on KPI registry records
- Phase 9B: assessment engine must be running to accumulate trigger data
- Phase 7 VA: outcome data (`value_assurance_solutions` table) required for recalibration accuracy computation
- KPI Assistant UI (Phase 9F deliverable): React panel for monitoring profile setup and recalibration review

### 9.6 UI Requirements (Phase 9F)

The KPI Assistant currently has API routes but no UI. Phase 9F adds:
- Monitoring profile recommendation panel in the Admin Console (after KPI onboarding step)
- Shows volatility stats, recommended profile fields, LLM rationale
- Editable fields for admin override
- "Accept" / "Adjust" / "Skip" actions
- Recalibration alert badge on Admin Console when KPIs need review
- Recalibration recommendations panel listing KPIs flagged for adjustment

---

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
