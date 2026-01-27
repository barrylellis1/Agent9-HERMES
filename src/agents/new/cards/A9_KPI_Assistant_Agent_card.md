# A9_KPI_Assistant_Agent Card

Status: Active (LLM-powered KPI definition assistant)

## Overview
The `A9_KPI_Assistant_Agent` provides an LLM-powered conversational interface for defining comprehensive KPIs during data product onboarding. It analyzes schema metadata from the Data Product Agent, suggests business-relevant KPIs with complete attribute sets including strategic metadata tags (line, altitude, profit_driver_type, lens_affinity), and enables iterative refinement through natural language interaction.

## Protocol Entrypoints
- KPI suggestion and refinement:
  - `suggest_kpis(KPISuggestionRequest) -> KPISuggestionResponse`
  - `chat(KPIChatRequest) -> KPIChatResponse`
  - `validate_kpi(KPIValidationRequest) -> KPIValidationResponse`
  - `finalize_kpis(KPIFinalizeRequest) -> KPIFinalizeResponse` (supports `extend_mode` for merging with existing KPIs)

## Configuration Schema
Defined in `src/agents/agent_config_models.py`:

```python
class A9_KPI_Assistant_Agent_Config(BaseModel):
    model_config = ConfigDict(extra="allow")
    
    # LLM settings
    llm_provider: str = "openai"
    llm_model: str = "gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # Suggestion settings
    default_num_suggestions: int = 5
    include_rationale: bool = True
    validate_sql: bool = True
    
    # Metadata validation
    enforce_strategic_metadata: bool = True
    warn_on_inconsistencies: bool = True
    
    # Conversation settings
    max_conversation_history: int = 20
    conversation_timeout_minutes: int = 60
```

## Dependencies
- `A9_LLM_Service_Agent` (required, for natural language processing)
- `A9_Data_Product_Agent` (required, for schema metadata and contract updates)
- `A9_Data_Governance_Agent` (optional, for ownership validation)
- `A9_Orchestrator_Agent` (required, orchestrator-driven lifecycle)

## Strategic Metadata Framework
The agent enforces complete strategic metadata on all KPIs:

### Line (P&L Position)
- `top_line`: Revenue-focused metrics (sales, bookings, ARR)
- `middle_line`: Operational metrics (efficiency, throughput, quality)
- `bottom_line`: Profit/cost metrics (EBITDA, operating margin, cost per unit)

### Altitude (Decision Level)
- `strategic`: Executive-level, long-term impact (market share, brand value)
- `tactical`: Management-level, medium-term (quarterly targets, campaign ROI)
- `operational`: Day-to-day operations (daily sales, inventory turns)

### Profit Driver Type
- `revenue`: Drives top-line growth
- `expense`: Impacts cost structure
- `efficiency`: Improves resource utilization
- `risk`: Manages downside exposure

### Lens Affinity (Strategic Framework)
- `bcg`: BCG Growth-Share Matrix alignment
- `bain`: Bain RAPID decision model
- `mckinsey`: McKinsey 7S framework
- `porter`: Porter's Five Forces
- `balanced_scorecard`: Kaplan & Norton BSC

## KPI Suggestion Workflow

### 1. Schema Analysis
- Receives schema metadata from Data Product Agent's `inspect_source_schema`
- Identifies measures (numeric columns for aggregation)
- Identifies dimensions (categorical columns for grouping)
- Identifies time columns (for temporal analysis)
- Identifies identifiers (for entity tracking)

### 2. LLM-Powered Suggestion
- Builds domain-specific prompt with schema context
- Calls A9_LLM_Service_Agent with structured request
- Parses LLM response into structured KPI definitions
- Extracts JSON from code blocks and markdown formatting
- Validates completeness of all required attributes

### 3. Strategic Metadata Assignment
- Infers strategic metadata based on KPI semantics
- Validates logical consistency (e.g., revenue KPIs → top_line)
- Provides rationale for metadata assignments
- Warns on potential inconsistencies

### 4. Conversational Refinement
- Maintains conversation history per session
- Accepts natural language modification requests
- Updates KPI definitions based on user feedback
- Provides real-time validation and suggestions

### 5. Finalization
- Validates all KPIs against schema and governance rules
- Formats KPIs for data product contract YAML
- Coordinates with Data Product Agent for contract updates
- Triggers registry updates

## Validation Rules

### Required Attributes
- Core: id, name, domain, description, unit, data_product_id
- SQL: sql_query (validated against schema)
- Dimensions: At least one dimension for drill-down
- Strategic metadata: line, altitude, profit_driver_type, lens_affinity
- Governance: owner_role, stakeholders, business_process

### Consistency Checks
- Top-line KPIs should have revenue driver type
- Bottom-line KPIs should have expense/efficiency driver type
- Strategic altitude KPIs should have executive-level descriptions
- SQL queries must reference valid schema elements
- Dimensions must exist in schema

### Warnings (Non-Blocking)
- Missing thresholds for situation detection
- Inconsistent strategic metadata combinations
- Dimension fields not found in schema
- Missing governance metadata

## Integration Points

### Data Product Onboarding Workflow
1. User completes schema discovery (Step 2)
2. User selects tables and provides metadata (Step 3)
3. Data Product Agent performs metadata analysis (Step 4)
4. **KPI Assistant generates suggestions (Step 5)**
5. User refines KPIs via chat interface
6. User finalizes and proceeds to review (Step 6)
7. Data Product Agent registers with KPIs included

### UI Integration
- Embedded chat component: `decision-studio-ui/src/components/KPIAssistantChat.tsx`
- Integrated into: `decision-studio-ui/src/pages/DataProductOnboardingNew.tsx`
- Real-time KPI card updates during conversation
- Color-coded strategic metadata badges
- Validation feedback and error messages

### API Endpoints
- POST `/api/v1/data-product-onboarding/kpi-assistant/suggest`
- POST `/api/v1/data-product-onboarding/kpi-assistant/chat`
- POST `/api/v1/data-product-onboarding/kpi-assistant/validate`
- POST `/api/v1/data-product-onboarding/kpi-assistant/finalize`
- GET `/api/v1/data-product-onboarding/kpi-assistant/health`

## Prompt Engineering

### System Prompt Structure
- Role definition: Expert business analyst and KPI designer
- Context: Schema metadata, domain, source system
- Task: Generate N KPIs with complete attributes
- Constraints: Strategic metadata requirements, SQL validity
- Format: JSON array with specific structure

### User Prompt Structure
- Schema summary: Available measures, dimensions, time columns
- Business context: Domain, data product purpose
- Requirements: Number of suggestions, specific focus areas
- Examples: Sample KPI structure with all attributes

### Chat Prompt Structure
- Conversation history: Previous messages and context
- Current KPIs: Existing definitions for reference
- User request: Natural language modification
- Response format: Updated KPIs as JSON if applicable

## Error Handling

### LLM Service Errors
- Retry with exponential backoff for transient errors
- Fallback to manual KPI definition if LLM unavailable
- Log all errors with request_id for debugging
- Return user-friendly error messages

### Validation Errors
- Detailed error messages with field-level specificity
- Suggestions for fixing common issues
- Non-blocking warnings for best practices
- Allow manual override for edge cases

### Schema Mismatch Errors
- Detect when SQL references non-existent columns
- Suggest alternative columns from schema
- Validate dimension fields exist
- Check measure columns are numeric

## Performance Characteristics
- KPI suggestion generation: < 10 seconds (LLM-dependent)
- Chat response latency: < 5 seconds (LLM-dependent)
- Validation checks: < 1 second (local processing)
- Concurrent sessions: 10+ simultaneous users

## Security and Compliance
- No persistent storage of conversation history
- Audit logging via request_id tracking
- Principal-based access control
- LLM API key management via environment variables
- Redaction of sensitive data in logs

## Testing Coverage
- Unit tests: JSON parsing, validation logic, prompt building
- Integration tests: End-to-end with LLM Service Agent
- Mock tests: LLM responses for deterministic testing
- User acceptance tests: Business user KPI definition scenarios

## Recent Updates (Jan 2026)
- Initial implementation with LLM Service Agent integration
- Strategic metadata framework enforcement
- Conversational refinement capability
- Integration with data product onboarding workflow
- UI chat component with real-time updates
- Validation rules for schema and governance compliance

## Compliance Status
- ✅ Orchestrator-driven lifecycle (async factory pattern)
- ✅ Protocol-compliant A2A communication (Pydantic models)
- ✅ Structured logging with request_id tracking
- ✅ Agent card documentation
- ✅ PRD document: `docs/prd/agents/a9_kpi_assistant_agent_prd.md`
- ✅ Configuration model in `agent_config_models.py`
- ✅ Dependencies declared and managed
- ✅ Error handling with graceful degradation
