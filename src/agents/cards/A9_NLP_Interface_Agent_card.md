---
configuration:
  name: A9_NLP_Interface_Agent
  version: ''
  capabilities: []
  config: {}
  hitl_enabled: false
---

## 1. Agent Overview & Metadata
- **A9-prefixed Name:** A9_NLP_Interface_Agent
- **Team / Agent Context Tags:** nlp_team, nlp_interface
- **Purpose:** Parses natural language business queries/documents into structured queries or insights, supporting protocol-compliant entity extraction and context hand-off.
- **Owner:** <owner_or_squad>
- **Version:** 1.0

## 2. Configuration Schema
```python
from pydantic import BaseModel, ConfigDict

class A9NLPInterfaceAgentConfig(BaseModel):
    enable_llm: bool = True
    default_temperature: float = 0.2
    model_config = ConfigDict(extra="allow")
```
- **Required secrets / external resources:** None

## 3. Protocol Entrypoints & Capabilities
| Entrypoint | Description | Input Model | Output Model | Side-effects |
|------------|-------------|-------------|--------------|--------------|
| `parse_business_query` | Interpret NL business query | `NLPBusinessQueryInput` | `NLPBusinessQueryResult` | logs events |
| `extract_entities` | Entity extraction from text | `str` | `List[Entity]` | logs events |

Supported hand-off commands / state updates:
- `escalate_hitl` – triggers HITL workflow when ambiguous terms detected

## 4. Compliance, Testing & KPIs
- **Design-Standards Checklist**
  - Naming follows `A9_*`
  - File size < 300 lines
  - No hard-coded secrets
  - Tests reference Agent9 standards
- **Unit / Integration Test Targets**
  - Unit coverage ≥ 90%
  - Integration workflow test present
- **Runtime KPIs & Monitoring Hooks**
  - Avg latency target < 1 s
  - Success-rate target ≥ 99 %
  - Cost per call tracked via `A9_CostTracker`

---

# Input Model
- **NLPBusinessQueryInput** fields:
    - business_terms: List[str] (required)
    - data_product_agent: Any (required)
    - filters: Optional[dict]
    - topn: Optional[dict]
    - principal_context: Optional[dict]
    - **situation_context: Optional[A9_Situation_Context]**  
      Unified context model for recognized situations (problem or opportunity), handed off from upstream agents. See `src/agents/new/situation_context_models.py` for schema.

Example:
```python
input_model = NLPBusinessQueryInput(
    business_terms=["Show me the top 5 regions by revenue for 2024"],
    data_product_agent=...,
    principal_context={"filters": {"region": "North America"}},
    situation_context=A9_Situation_Context(
        situation_type="problem",
        situation_context=SituationContext(...),
        description="Detected revenue anomaly in North America",
        recognized_at="2025-06-10T11:58:08-05:00"
    )
)
```

# Protocol Entrypoints
- parse_business_query (async):
    - input: NLPBusinessQueryInput
    - output: NLPBusinessQueryResult
    - description: Parses business queries using LLM, extracts intent, topn/bottomn, filters, principal context, and calls Data Governance Agent for translation. Escalates to HITL if unmapped terms/filters. Supports optional `situation_context` for protocol-compliant handoff.
    - NOTE: The agent matches KPIs using both the `kpi_name` and all synonyms from the KPI registry, enabling robust business language support (e.g., "sales", "revenue", etc.).
- extract_entities (async):
    - input: "text: str"
    - output: List[Entity]
    - description: Extracts business-relevant entities (department, region, company, product, date) from user queries. Escalates to HITL if ambiguous or unmapped.

# Output Protocol Fields
- matched_views: List[dict] (NLQ intent resolution)
- unmapped_terms: List[str] (terms not mapped)
- filters: dict (technical/business filters)
- topn: dict (TopN/BottomN extraction)
- principal_context: dict (principal context used)
- human_action_required: bool (HITL escalation)
- human_action_type: str (type of HITL action)
- human_action_context: dict (context for HITL)

## Entity Extraction (MVP Focus)
- Only entity extraction is implemented as the core NLP model for MVP.
- Extracts entities: department, region, company, product, date.
- Robust to synonyms and common business language.
- Escalates to HITL if no recognizable or ambiguous entities are found, with actionable context for the user.
- All other NLP models (document_analysis, relationship_analysis, sentiment_analysis) are omitted or stubbed until post-MVP.

# Integration
- Data Governance Agent: Used for translating business terms/filters to technical attributes.
- HITL Escalation: Unmapped terms/filters trigger HITL protocol fields in output.

# Compliance
- Agent9 protocol-compliant (Pydantic models for all entrypoints/outputs)
- Atomic agent exposes only parse_business_question as protocol entrypoint; orchestration logic is handled by the orchestrator and tested in integration tests using DRY async mocking (mock_registry, make_registry_get_agent).
- All integration tests use DRY fixtures/helpers for registry/agent mocking; atomic tests are protocol-compliant and independent.
- Registry/orchestrator integration only (no direct instantiation)
- Integration and end-to-end tests in tests/agents/new/test_a9_nlp_interface_agent_enhancements.py
- 2025-06-11: Updated for full atomic/integration test separation, DRY async mocking, and strict protocol/test compliance.
- 2025-06-20: Protocol compliance and test suite passes for all edge cases and strict field validation. parse_business_question always returns all protocol-required fields, even for empty/null input (kpi_name=None, groupings=[]). Entity extraction prints raw LLM response and errors for debugging in all cases. All atomic/integration tests pass as of this date.
- Supports YAML contract context from the context kwarg for all protocol-compliant workflows.

# Error Handling
Standard error handling via AgentExecutionError and AgentInitializationError.

# Example Usage
```python
from src.agents.new.A9_NLP_Interface_Agent import A9_NLP_Interface_Agent
from src.agents.new.agent_config_models import A9NLPInterfaceAgentConfig
config = {
    "name": "A9_NLP_Interface_Agent",
    "version": "1.0",
    "capabilities": ["nlq", "document_analysis", "parse_business_query"],
    "config": {},
    "hitl_enabled": False
}
agent = A9_NLP_Interface_Agent(config)
# Example: parse_business_query (async, orchestrator-driven)
input_model = NLPBusinessQueryInput(
    business_terms=["Show me the top 5 regions by revenue for 2024"],
    data_product_agent=...,
    principal_context={"filters": {"region": "North America"}}
)
result = await agent.parse_business_query(input_model)
# result.topn, result.filters, result.human_action_required, ...
# Use agent.analyze_document(...) for document analysis
```

# Prompt Templates

"**NLP Interface Agent (LLM-enabled, HITL-compliant):**"

```
You are an Agent9 NLP Interface Agent. Your task is to interpret natural language business queries and documents, transforming them into structured data queries or extracting actionable insights for enterprise analytics.

Context:
- Principal Context (stakeholder, persona, or decision-maker perspective):
"""
[PASTE PRINCIPAL CONTEXT HERE]
"""
- Business Process Context (relevant business process, workflow, or objective):
"""
[PASTE BUSINESS PROCESS CONTEXT HERE]
"""
- Industry Context (industry, sector, or market segment details):
"""
[PASTE INDUSTRY CONTEXT HERE]
"""
- Available Data Products and Schemas:
"""
[PASTE DATA PRODUCT REGISTRY AND SCHEMA INFO HERE]
"""
- User Query or Document:
"""
[PASTE USER NATURAL LANGUAGE QUERY OR DOCUMENT HERE]
"""

Instructions:
- If the input is a business query, extract the intent: data product, aggregation/groupby, filters, and other query parameters.
- Map business terms to technical attribute names using the registry/schema context.
- Generate a structured API call or SQL query for the MCP service, and clearly show the mapping from NLQ to technical query.
- If the input is a document, extract key entities, relationships, and sentiment, and summarize findings.
- Structure your output as a JSON object with the following fields:
  - "intent_parsing": Extracted intent (for NLQ)
  - "schema_validation": How terms were mapped/validated
  - "query": Structured API or SQL query (if applicable)
  - "document_analysis": Summary, key points, entities, relationships, sentiment (if applicable)
  - "llm_derived": Boolean flag (true if any field is based on LLM output)
  - "human_action_required": Boolean (true if HITL approval is needed)
  - "human_action_type": String (e.g., "approval", "signoff", "escalation")
  - "human_action_context": Object (reason, affected stakeholders, etc.)
- Do not include any information outside the JSON object.

Respond ONLY with the JSON object as specified.
```


## Prompt Templates

"**NLP Interface Agent (LLM-enabled, HITL-compliant):**"

```
You are an Agent9 NLP Interface Agent. Your task is to interpret natural language business queries and documents, transforming them into structured data queries or extracting actionable insights for enterprise analytics.

Context:
- Principal Context (stakeholder, persona, or decision-maker perspective):
"""
[PASTE PRINCIPAL CONTEXT HERE]
"""
- Business Process Context (relevant business process, workflow, or objective):
"""
[PASTE BUSINESS PROCESS CONTEXT HERE]
"""
- Industry Context (industry, sector, or market segment details):
"""
[PASTE INDUSTRY CONTEXT HERE]
"""
- Available Data Products and Schemas:
"""
[PASTE DATA PRODUCT REGISTRY AND SCHEMA INFO HERE]
"""
- User Query or Document:
"""
[PASTE USER NATURAL LANGUAGE QUERY OR DOCUMENT HERE]
"""

Instructions:
- If the input is a business query, extract the intent: data product, aggregation/groupby, filters, and other query parameters.
- Map business terms to technical attribute names using the registry/schema context.
- Generate a structured API call or SQL query for the MCP service, and clearly show the mapping from NLQ to technical query.
- If the input is a document, extract key entities, relationships, and sentiment, and summarize findings.
- Structure your output as a JSON object with the following fields:
  - "intent_parsing": Extracted intent (for NLQ)
  - "schema_validation": How terms were mapped/validated
  - "query": Structured API or SQL query (if applicable)
  - "document_analysis": Summary, key points, entities, relationships, sentiment (if applicable)
  - "llm_derived": Boolean flag (true if any field is based on LLM output)
  - "human_action_required": Boolean (true if HITL approval is needed)
  - "human_action_type": String (e.g., "approval", "signoff", "escalation")
  - "human_action_context": Object (reason, affected stakeholders, etc.)
- Do not include any information outside the JSON object.

Respond ONLY with the JSON object as specified.
```
---
