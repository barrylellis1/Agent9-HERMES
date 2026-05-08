# A9_Data_Governance_Agent Card

**Last Updated:** 2026-05-08  
**Status:** MVP

## Overview
The `A9_Data_Governance_Agent` handles business term resolution, KPI-to-data-product mapping, and data access validation.

## Protocol Entrypoints

| Method | Signature | Returns |
|--------|-----------|---------|
| `map_kpis_to_data_products` | `async def map_kpis_to_data_products(request: KPIDataProductMappingRequest) -> KPIDataProductMappingResponse` | mappings[] + unmapped_kpis[] (client-scoped) |
| `translate_business_terms` | `async def translate_business_terms(request: BusinessTermTranslationRequest) -> BusinessTermTranslationResponse` | resolved_terms dict + unmapped_terms[] |
| `validate_data_access` | `async def validate_data_access(request: DataAccessValidationRequest) -> DataAccessValidationResponse` | allowed: bool + reason + policy_id |
| `get_view_name_for_kpi` | `async def get_view_name_for_kpi(request: KPIViewNameRequest) -> KPIViewNameResponse` | view_name (or "unknown" if not found) |
| `map_business_process` | `async def map_business_process(request: BusinessProcessMappingRequest) -> BusinessProcessMappingResponse` | mapped process + ownership + KPIs |

**All methods are async. All returns use Pydantic models.**

## Dependencies
- RegistryFactory + providers: KPI, Business Glossary, Data Product, Business Process

## Contract Path Resolution
Uses `_contract_path()` method to resolve contract files:
- Canonical location: `src/registry_references/data_product_registry/data_products/fi_star_schema.yaml`

## KPI Lookup & View Resolution
- Normalizes KPI identifiers (e.g., `Gross Revenue` → `gross_revenue`) and exhaustively scans registry entries to tolerate naming drift before failing.
- Defers view-name decisions to upstream registry data; if a view cannot be found, returns `"unknown"` rather than synthesizing a `view_*` alias.

## Recent Updates (Dec 2025)
- Contract path consolidated to single source of truth in `registry_references`

## Request/Response Models

### KPIDataProductMappingRequest
```python
kpi_names: List[str]                # KPI identifiers to map
client_id: Optional[str]            # Tenant filter (when provided, results scoped to this client)
context: Optional[Dict]             # Additional context (principal context, etc.)
```

### KPIDataProductMappingResponse
```python
mappings: List[KPIDataProductMapping]  # Mapped KPI → data_product_id entries
unmapped_kpis: List[str]            # KPI names not found in registry
```

### BusinessTermTranslationRequest
```python
business_terms: List[str]           # Terms to translate (e.g., ["Gross Margin", "Profit Center"])
system: Optional[str] = "duckdb"    # Backend context for mapping
context: Optional[Dict]             # Principal context, etc.
```

### BusinessTermTranslationResponse
```python
resolved_terms: Dict[str, str]      # {business_term: technical_column_name}
unmapped_terms: List[str]           # Terms not found in glossary
human_action_required: bool         # Escalation flag for ambiguous terms
human_action_type: Optional[str]    # "clarification" or "ambiguity"
human_action_context: Optional[Dict] # Disambiguation choices
```

### DataAccessValidationRequest
```python
principal_id: str                   # Principal requesting access
data_product_id: str                # Data product to access
access_type: str = "read"           # "read" | "write" | "execute"
client_id: Optional[str]            # Tenant filter (principal's client_id)
```

### DataAccessValidationResponse
```python
allowed: bool                       # Access granted/denied
reason: Optional[str]               # Reason for decision
policy_id: Optional[str]            # Governance policy applied
```

### KPIViewNameRequest
```python
kpi_id: str                         # KPI identifier
client_id: Optional[str]            # Tenant context
```

### KPIViewNameResponse
```python
view_name: str                      # Resolved view name or "unknown"
kpi_id: str
data_product_id: Optional[str]      # Source data product
```

## Error Behaviour

| Scenario | Returns | Notes |
|----------|---------|-------|
| KPI not found | mappings=[], unmapped_kpis=[kpi_name] | Non-fatal; caller handles empty mappings |
| Registry unavailable | Empty mappings/resolved_terms, all input terms → unmapped | Graceful fallback; no exception raised |
| client_id mismatch | Filters out non-matching KPIs; unmapped_kpis increases | Strict isolation: never leaks cross-client KPIs |
| Business term ambiguous | human_action_required=True + human_action_context with choices | NLP agent must escalate to HITL for clarification |
| Data access denied | allowed=False + reason (e.g., "Principal not authorized for this product") | No exception; caller sees denied status |
| View not found for KPI | view_name="unknown" | No exception; indicates incomplete registry mapping |
| Invalid business_terms input | unmapped_terms=[all terms], resolved_terms={} | Tolerates empty input gracefully |

## Caching & Glossary Structure

**No caching:** All lookups are live against RegistryFactory providers (Supabase). No in-memory glossary cache.

**Glossary structure** (BusinessGlossaryProvider):
```
Glossary entries map business terms to technical columns:
  Business Term: "Gross Margin"
  Technical Name: "gross_margin_pct"
  Description: "Gross profit divided by revenue"
  Source System: "FI_Star_View"
```

On ambiguity (e.g., "Margin" could be gross_margin or net_margin), `human_action_required=True` and `human_action_context` lists candidates.

## Phase 10B-DGA: Data Governance Wiring (Apr 2026)
- `validate_data_access()` enforces real client_id filtering — no longer returns allow-all
- `map_kpis_to_data_products()` filters mapped results by client_id, preventing cross-client KPI visibility
- Post-bootstrap DGA wiring: A9_Orchestrator calls `runtime._wire_governance_dependencies()` after all agents connect, injecting DGA into Data Product and Deep Analysis agents
- Client isolation hardened: all governance queries scoped to PrincipalContext.client_id
- DGA is a required dependency of Data Product Agent — wiring enforced at bootstrap (raises RuntimeError if DGA unavailable)
