# A9_NLP_Interface_Agent Card

Status: MVP Planning

## Overview
The `A9_NLP_Interface_Agent` provides a protocol-compliant interface for natural language parsing in Agent9. It extracts business-level intent from user questions and defers:
- Business-to-technical translation to the Data Governance Agent (DGA)
- SQL generation and timeframe enforcement to the Data Product Agent (DPA)

It is orchestrator-driven, registry-integrated, and HITL-enabled per the NLP PRD.

## Capabilities (Protocol Entrypoints)
- `parse_business_query(input: NLPBusinessQueryInput, context: dict) -> NLPBusinessQueryResult`
  - Extract KPI, groupings, filters (business-level), timeframe hints, and Top/Bottom N.
  - Uses `yaml_contract_text` from `context` when present.
  - Delegates glossary/KPI resolution to registry via DGA.
- `entity_extraction(input: EntityExtractionInput, context: dict) -> EntityExtractionResult`
  - Deterministic entity extraction with BusinessGlossaryProvider for validation.
  - HITL escalation for ambiguous/unmapped entities.

## Configuration Schema
Defined in `src/agents/agent_config_models.py`:

```python
class A9_NLP_Interface_Agent_Config(BaseModel):
    model_config = ConfigDict(extra="allow")
    # Core behavior
    hitl_enabled: bool = Field(False)
    llm_parsing_enabled: bool = Field(False)
    # Orchestration & logging
    require_orchestrator: bool = Field(True)
    log_all_requests: bool = Field(True)
    # Parsing defaults
    default_topn_n: int = Field(10)
```

## Protocol Models
Defined in `src/agents/models/nlp_models.py`:
- `NLPBusinessQueryInput` / `NLPBusinessQueryResult`
- `EntityExtractionInput` / `EntityExtractionResult`
- Supporting: `MatchedView`, `TimeFilterSpec`, `TopNSpec`, `ExtractedEntity`

Compliance reference map (for documentation/tests):
```python
NLP_PROTOCOL_MODELS = {
  "parse_business_query": {"input": NLPBusinessQueryInput, "output": NLPBusinessQueryResult},
  "entity_extraction": {"input": EntityExtractionInput, "output": EntityExtractionResult},
}
```

## Orchestrator & Registry Integration
- Uses `RegistryFactory` to access BusinessGlossaryProvider and KPI registry.
- Reads `yaml_contract_text` from `context` (no local caching of registry data).
- Orchestrator injects `principal_context` (filters, typical_timeframes), enabling defaults such as “Show my current Margin”.

## Deterministic Governance Path
- NLP returns business-level keys/values only.
- DGA translates to technical columns/codes using the glossary and FI view code↔description pairs.
- DPA generates/executes SQL and applies timeframe via `time_dim`.

## HITL and Explainability
- Outputs include `human_action_required`, `human_action_type`, `human_action_context`.
- Logs are structured and async; escalations are user-actionable.

## Usage (Orchestrator-Driven)
```python
from src.agents.new.A9_NLP_Interface_Agent import A9_NLP_Interface_Agent
from src.agents.models.nlp_models import NLPBusinessQueryInput

agent = await A9_NLP_Interface_Agent.create(config)
input_model = NLPBusinessQueryInput(
    query="Show my current Margin",
    principal_context={
        "filters": {"Profit Center Name": ["Production"], "Parent Customer Hierarchy ID": ["Z2","Z3"]},
        "typical_timeframes": ["Monthly","Quarterly"],
    },
)
result = await agent.parse_business_query(input_model, context={"yaml_contract_text": yaml_contract})
# Pass result to DGA for translation, then to DPA for SQL/execute
```

## Compliance Checklist (Agent9 Standards)
- A2A protocol: All entrypoints use Pydantic models
- Orchestrator-only invocation; no self-registration
- Registry Factory integration for glossary/KPI
- HITL fields enforced
- No business-to-technical translation in NLP; no SQL in NLP
- `yaml_contract_text` accessed via `context` param
