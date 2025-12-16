# A9_Situation_Awareness_Agent Card

## Agent Description
The Situation Awareness Agent provides automated KPI monitoring and situation detection based on principal context and business processes. It analyzes Finance KPIs from the FI Star Schema to detect anomalies, trends, and insights, presenting them as actionable situations with severity levels, business impact analysis, and suggested next steps.

## Primary Purpose
To provide personalized situation awareness for Finance KPIs, enabling principals to quickly understand the current state of their business metrics, identify anomalies, and take appropriate action.

## Core Capabilities
- Finance KPI monitoring and anomaly detection
- Principal-specific situation awareness based on role and context
- Business process-aligned KPI prioritization
- Natural language query processing for KPI insights
- Human-in-the-loop feedback handling
- Recommended diagnostic questions

## Configuration Model
```python
class SituationAwarenessAgentConfig(BaseModel):
    """Configuration for the Situation Awareness Agent."""
    
    # Required configuration
    contract_path: str = Field(
        description="Path to the data contract YAML file"
    )
    
    # Optional configuration
    kpi_thresholds: Optional[Dict[str, Dict[str, float]]] = Field(
        None,
        description="Custom KPI thresholds, overriding contract defaults"
    )
    principal_profile_path: Optional[str] = Field(
        None,
        description="Optional path to custom principal profile definitions"
    )
```

## Protocol Entrypoints
| Method | Description | Request Model | Response Model |
|--------|-------------|---------------|----------------|
| `detect_situations` | Detect situations across KPIs based on principal context | `SituationDetectionRequest` | `SituationDetectionResponse` |
| `process_nl_query` | Process natural language queries about KPIs | `NLQueryRequest` | `NLQueryResponse` |
| `process_hitl_feedback` | Handle human-in-the-loop feedback for situations | `HITLRequest` | `HITLResponse` |
| `get_recommended_questions` | Get recommended questions based on principal context | N/A | `List[str]` |
| `get_kpi_definitions` | Get KPI definitions relevant to the principal | N/A | `Dict[str, KPIDefinition]` |

## Input/Output Schema
```python
# Key Request Models
class SituationDetectionRequest(BaseRequest):
    principal_context: PrincipalContext
    business_processes: List[BusinessProcess]
    timeframe: TimeFrame
    comparison_type: Optional[ComparisonType]
    filters: Optional[Dict[str, Any]]

class NLQueryRequest(BaseRequest):
    principal_context: PrincipalContext
    query: str

# Key Response Models
class SituationDetectionResponse(BaseResponse):
    situations: List[Situation]

class NLQueryResponse(BaseResponse):
    answer: str
    kpi_values: Optional[List[KPIValue]]
    sql_query: Optional[str]
```

## Dependencies
- A9_Data_Product_MCP_Service_Agent: For data query execution
- A9_Principal_Context_Agent: For principal context retrieval (future)
- A9_Data_Governance_Agent: For business term mapping (future)
- A9_NLP_Interface_Agent: For advanced natural language processing (future)
- A9_LLM_Service_Agent: For SQL generation from natural language queries

## LLM Configuration
| Task Type | Optimal Model | Rationale |
|-----------|---------------|-----------|
| `sql_generation` | `gpt-4o-mini` | Fast, cost-effective SQL generation from natural language |

Environment variable override: `OPENAI_MODEL_SQL`

## Assignment & HITL
- Delayed assignment until Deep Analysis completes; ownership mapping can be more precise once scope is identified across dimensions.
- Fallback child breakdown dimensions are defined in the Data Product YAML (e.g., `fallback_group_by_dimensions`).
- Action types supported: `notify`, `assign`, `delegate`, `escalate`, `snooze`, `open_view`, `export`.
- Situation model fields extended:
  - `parent_id`, `status`, `hitl_required`, `assignee_id`
  - `assignment_candidates[]`, `assignment_decision{}`
  - `dedupe_key`, `cooldown_until`, `tags`, `provenance`, `lineage`
- Entrypoints (orchestrated):
  - `propose_assignment_candidates(situation_id)` – delegates to Principal Context/HR; fallback to Process Owner from Business Process registry when HR mapping is unavailable.
  - `apply_action(situation_id, action)` – applies `ActionType` (including `DELEGATE`) and updates situation state.

## Compliance Status
- [x] Follows A9 Agent naming convention (A9_Situation_Awareness_Agent)
- [x] Implements required protocol methods
- [x] Provides proper Pydantic v2 models
- [x] Includes factory method
- [x] Has agent card documentation
- [ ] Has comprehensive test suite (to be implemented)

## Usage Examples

### Detecting Situations for a CFO
```python
from src.agents.new.a9_situation_awareness_agent import create_situation_awareness_agent
from src.agents.models.situation_awareness_models import (
    SituationDetectionRequest, PrincipalContext, PrincipalRole, 
    BusinessProcess, TimeFrame, ComparisonType
)

# Create the agent
agent = create_situation_awareness_agent({
    "contract_path": "path/to/fi_star_schema.yaml"
})
await agent.connect()

# Define principal context for CFO
cfo_context = PrincipalContext(
    role=PrincipalRole.CFO,
    business_processes=[
        BusinessProcess.PROFITABILITY_ANALYSIS,
        BusinessProcess.REVENUE_GROWTH
    ],
    default_filters={},
    decision_style="strategic",
    communication_style="executive_summary",
    preferred_timeframes=[TimeFrame.CURRENT_QUARTER]
)

# Create request
request = SituationDetectionRequest(
    request_id="req-123",
    principal_context=cfo_context,
    business_processes=[BusinessProcess.PROFITABILITY_ANALYSIS],
    timeframe=TimeFrame.CURRENT_QUARTER,
    comparison_type=ComparisonType.QUARTER_OVER_QUARTER
)

# Detect situations
response = await agent.detect_situations(request)

# Process results
for situation in response.situations:
    print(f"{situation.severity}: {situation.description}")
    print(f"Business Impact: {situation.business_impact}")
    if situation.suggested_actions:
        print("Suggested Actions:")
        for action in situation.suggested_actions:
            print(f"- {action}")
    print()
```

## Future Enhancements
- Integration with A9_NLP_Interface_Agent for advanced query parsing
- Enhanced business impact analysis using LLM
- Machine learning-based anomaly detection
- Multi-dimensional trend analysis
- Enhanced visualization capabilities in Decision Studio UI
