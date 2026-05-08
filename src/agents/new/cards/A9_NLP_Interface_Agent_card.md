# A9_NLP_Interface_Agent Card

**Last Updated:** 2026-05-08  
**Status:** MVP Planning

## Overview
The `A9_NLP_Interface_Agent` provides a protocol-compliant interface for natural language parsing in Agent9. It extracts business-level intent from user questions and defers:
- Business-to-technical translation to the Data Governance Agent (DGA)
- SQL generation and timeframe enforcement to the Data Product Agent (DPA)

It is orchestrator-driven, registry-integrated, and HITL-enabled per the NLP PRD.

## Protocol Entrypoints

| Method | Signature | Returns |
|--------|-----------|---------|
| `parse_business_query` | `async def parse_business_query(input_model: NLPBusinessQueryInput, context: Optional[Dict[str, Any]]) -> NLPBusinessQueryResult` | matched_views + filters + topn + HITL fields |
| `entity_extraction` | `async def entity_extraction(input_model: EntityExtractionInput, context: Optional[Dict[str, Any]]) -> EntityExtractionResult` | extracted_entities + unmapped + HITL escalation |

**Deterministic (No LLM):** Both methods use regex and registry lookups only; no generative calls.

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

## Request/Response Models

### NLPBusinessQueryInput
```python
query: Optional[str]                # Natural language question (e.g., "top 5 regions by revenue")
business_terms: Optional[List[str]] # Tokenized form of request
principal_context: Optional[Dict]   # Principal defaults {filters, typical_timeframes}
kpi_hints: Optional[List[str]]      # KPI candidates to bias resolution
hitl_enabled: bool = False          # Enable HITL escalation
```

### NLPBusinessQueryResult
```python
matched_views: List[MatchedView]    # Candidate interpretations (0–N)
unmapped_terms: List[str]           # Terms that could not be parsed
filters: Dict[str, Any]             # Business-level filters for DGA translation
topn: Optional[TopNSpec]            # Top/Bottom N intent
principal_context: Dict[str, Any]   # Context used during parsing
human_action_required: bool         # HITL escalation flag
human_action_type: Optional[str]    # "clarification", "ambiguity", etc.
human_action_context: Optional[Dict] # Context for HITL prompt
```

### MatchedView (in NLPBusinessQueryResult)
```python
kpi_name: str                       # Business-level KPI name (registry-resolved)
data_product_id: Optional[str]      # Resolved data product (if identified)
view_name: Optional[str]            # Resolved view name (if identified)
groupings: List[str]                # Business-level grouping dimensions
time_filter: Optional[TimeFilterSpec] # Timeframe intent (e.g., "current", "ytd")
filters: Dict[str, Any]             # Business-level filters (DGA will translate)
```

### EntityExtractionInput
```python
text: str                           # Input text to extract entities from
entity_types: Optional[List[str]]   # Types to extract (e.g., ["date", "dimension"])
principal_context: Optional[Dict]   # Context for disambiguation
```

### EntityExtractionResult
```python
extracted_entities: List[ExtractedEntity] # Parsed entities
unmapped_terms: List[str]           # Terms that could not be matched
human_action_required: bool         # HITL escalation flag
human_action_type: Optional[str]    # "ambiguity", "clarification"
human_action_context: Optional[Dict] # Disambiguation choices for user
```

## Error Behaviour

| Scenario | parse_business_query | entity_extraction |
|----------|---------------------|-------------------|
| Empty query + empty business_terms | human_action_required=True, type="clarification" | human_action_required=True |
| KPI not found in registry | unmapped_terms includes KPI name | unmapped_terms includes entity |
| Ambiguous dimension (multiple matches) | matched_views contains all candidates; HITL if hitl_enabled=True | human_action_required=True |
| Registry unavailable | matched_views=[], unmapped_terms=[all terms] | unmapped_terms=[all terms] |
| Malformed principal_context | Ignored gracefully; uses empty dict | Ignored gracefully |

**HITL Escalation:** When ambiguity exists and `hitl_enabled=True`, response includes `human_action_context` with disambiguation choices. When `hitl_enabled=False`, agent picks the highest-confidence match silently.

## Compliance Checklist (Agent9 Standards)
- A2A protocol: All entrypoints use Pydantic models
- No LLM calls; deterministic regex + registry lookups only
- Registry Factory integration for glossary/KPI lookups
- HITL fields always present (escalation is opt-in per config)
- Business-to-technical translation deferred to DGA
- SQL generation deferred to DPA
- Graceful degradation when registry unavailable
