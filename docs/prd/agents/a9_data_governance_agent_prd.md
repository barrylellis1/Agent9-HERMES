# A9_Data_Governance_Agent PRD

<!--
CANONICAL PRD DOCUMENT
Last updated: 2026-04-12
Rewritten to reflect actual implementation state and multi-tenant requirements.
-->

## Overview

**Purpose:** The Data Governance Agent (DGA) is the single authority for tenant-scoped data access in Agent9-HERMES. Its core job: *given a principal, return only the KPIs, data products, and views that principal is authorized to see.* It also provides business-to-technical term translation, KPI-to-data-product mapping, and view name resolution.

**Agent Type:** Core Agent
**Version:** 2.0
**Status:** Active — multi-tenant access control shipping in Phase 10B-DGA

**Key files:**
- Implementation: `src/agents/new/a9_data_governance_agent.py`
- Models: `src/agents/models/data_governance_models.py`
- Card: `src/agents/new/cards/A9_Data_Governance_Agent_card.md`
- Config: `src/agents/agent_config_models.py`

---

## 1. Multi-Tenant Access Control

**This is the DGA's primary responsibility.** Without it, principals from one client can see KPIs and data belonging to another client. This has been confirmed as a real data leak between bicycle and lubricants tenants.

### 1.1 Tenant Isolation Model

- **`client_id`** is the tenant isolation key. Every KPI, data product, and principal profile carries a `client_id` field.
- The DGA enforces: a principal may only access KPIs and data products where `principal.client_id == resource.client_id`.
- When `client_id` is `None` (legacy/test data), access is allowed for backward compatibility but logged as a warning.

### 1.2 validate_data_access()

```python
async def validate_data_access(request: DataAccessValidationRequest) -> DataAccessValidationResponse
```

**Current state:** MVP stub — always returns `allowed=True`.
**Target state (Phase 10B-DGA):**
1. Look up principal's `client_id` from principal profile
2. Look up data product's `client_id` from data product registry
3. Allow only if they match (or if either is `None` for backward compat)
4. Log denied access attempts at WARNING level with principal_id, data_product_id, and both client_ids
5. Return `allowed=False` with reason when client_ids mismatch

### 1.3 Client-Scoped KPI Mapping

`map_kpis_to_data_products()` currently calls `kpi_provider.get_all()` with no filtering. When `client_id` is provided in the request context, it MUST filter KPIs by client before mapping.

### 1.4 Integration Points for Access Control

| Agent | Where client_id is enforced | Mechanism |
|-------|---------------------------|-----------|
| SA Agent | `_get_relevant_kpis()` | Calls `kpi_provider.get_by_client(client_id)` instead of `get_all()` |
| SA Agent | `detect_situations()` | Calls `dga.validate_data_access()` before processing each KPI |
| DPA | `_resolve_view_name_for_kpi()` | DGA resolves view, DPA executes query — no cross-client views |
| DA Agent | `plan_deep_analysis()` | Dimensions come from DGA-mapped data products, already client-scoped |

### 1.5 Data Flow for Tenant Isolation

```
Principal logs in → PrincipalContext (includes client_id)
    → SA Agent receives detect_situations request
    → SA extracts client_id from PrincipalContext
    → SA calls kpi_provider.get_by_client(client_id)  [only this client's KPIs]
    → For each KPI: DGA.validate_data_access(principal_id, data_product_id)
    → Only authorized KPIs proceed to monitoring
    → Downstream agents (DA, SF, VA) inherit the scoped dataset
```

---

## 2. Business Term Translation

**Status:** Implemented with real logic.

```python
async def translate_business_terms(request: BusinessTermTranslationRequest) -> BusinessTermTranslationResponse
```

- Translates business terms (e.g., "revenue", "gross margin") to technical attribute names using the Business Glossary Provider
- Returns `resolved_terms` (business → technical mapping) and `unmapped_terms`
- Sets `human_action_required=True` with `human_action_type="clarification"` when terms cannot be mapped
- Delegates to `business_glossary_provider.translate_business_terms()`

### HITL Escalation for Unmapped Terms

When business terms remain unmapped after glossary resolution:
```json
{
  "resolved_terms": {"revenue": "TOTAL_REVENUE"},
  "unmapped_terms": ["sales velocity"],
  "human_action_required": true,
  "human_action_type": "clarification",
  "human_action_context": {
    "unmapped_terms": ["sales velocity"],
    "message": "Please clarify or map these terms before proceeding."
  }
}
```

---

## 3. KPI-to-Data-Product Mapping

**Status:** Implemented with real logic.

### 3.1 map_kpis_to_data_products()

```python
async def map_kpis_to_data_products(request: KPIDataProductMappingRequest) -> KPIDataProductMappingResponse
```

- Maps KPI names to their underlying data products by querying the KPI Provider registry
- For each matched KPI: extracts `data_product_id`, `technical_name`, dimensions, thresholds, business processes
- Returns `unmapped_kpis` list and sets `human_action_required` when KPIs can't be resolved
- Uses `kpi_provider.get_all()` (to be scoped by `client_id` in Phase 10B)

### 3.2 get_view_name_for_kpi()

```python
async def get_view_name_for_kpi(request: KPIViewNameRequest) -> KPIViewNameResponse
```

3-tier resolution strategy:
1. **Direct lookup** — KPI name as-is in provider
2. **Normalized ID** — `"Gross Revenue"` → `"gross_revenue"` → provider lookup
3. **Scan** — case-insensitive match across all KPIs by display name

View name derivation (per KPI):
1. Explicit `view_name` attribute on KPI object
2. Metadata-defined `view_name`
3. Hardcoded fallback: FI_Star_Schema → `"FI_Star_View"` (legacy, to be removed)
4. Returns `"unknown"` if no resolution (no synthetic fallbacks per PRD)

### 3.3 register_kpi_metadata()

```python
async def register_kpi_metadata(request: KPIRegistryUpdateRequest) -> KPIRegistryUpdateResponse
```

Upserts KPI definitions into the governance registry. Used during data product onboarding.

### 3.4 map_business_process()

```python
async def map_business_process(request: BusinessProcessMappingRequest) -> BusinessProcessMappingResponse
```

Associates KPIs with business processes and persists to the Business Process Provider.

---

## 4. KPI Strategic Metadata Tags

KPIs carry strategic metadata tags that drive principal-driven analysis, consulting persona selection, and situation prioritization.

### Required Tags

| Tag | Values | Purpose |
|-----|--------|---------|
| `metadata.line` | `top_line`, `middle_line`, `bottom_line` | P&L classification |
| `metadata.altitude` | `strategic`, `tactical`, `operational` | Decision-making level |
| `metadata.profit_driver_type` | `revenue`, `expense`, `efficiency`, `risk` | P&L impact type |
| `metadata.lens_affinity` | `bcg`, `bain`, `mckinsey`, `mbb_council`, etc. | Consulting persona mapping |

### Validation Rules

1. All four tags MUST be present on every KPI
2. Each tag MUST contain only allowed enumerated values
3. Tag combinations MUST be logically consistent (e.g., `top_line` + `revenue` is consistent; `top_line` + `expense` should warn)
4. Multiple `lens_affinity` values are comma-separated with no spaces
5. Strategic altitude should align with C-suite owner roles

### Tag Assignment Examples

**Revenue KPI:** `line: top_line, altitude: strategic, profit_driver_type: revenue, lens_affinity: bcg,mckinsey`
**Efficiency KPI:** `line: middle_line, altitude: tactical, profit_driver_type: efficiency, lens_affinity: bain`
**Cost Control KPI:** `line: bottom_line, altitude: operational, profit_driver_type: expense, lens_affinity: bain`

### API Methods (planned)

- `validate_kpi_metadata(kpi) -> ValidationResult` — validates all required tags
- `suggest_kpi_metadata(kpi_characteristics) -> MetadataSuggestion` — suggests tags based on KPI name/description
- `enrich_kpi_metadata(kpi, context) -> KPI` — fills missing tags with defaults

---

## 5. Bootstrap Wiring

### The Problem (Pre-Phase 10B)

The DGA is created during bootstrap but never successfully wired into consuming agents due to a lifecycle timing bug:

1. `create()` calls `_async_init()` — agents try to find DGA here
2. `connect(orchestrator)` runs later — this is when the orchestrator reference becomes available
3. Result: every agent's `_async_init()` hits `self.orchestrator is None`, sets `self.data_governance_agent = None`
4. All `if self.data_governance_agent:` guards skip DGA calls, falling back to local resolution

### The Fix (Phase 10B)

A post-connect wiring phase in `src/api/runtime.py`:

```python
async def _wire_governance_dependencies(self):
    """Wire DGA into consuming agents after all agents are created and connected."""
    dga = await self._orchestrator.get_agent("A9_Data_Governance_Agent")
    for agent_name in ["A9_Situation_Awareness_Agent", "A9_Data_Product_Agent", "A9_Deep_Analysis_Agent"]:
        agent = await self._orchestrator.get_agent(agent_name)
        if agent:
            agent.data_governance_agent = dga
```

This runs after all agents are created and connected, guaranteeing DGA availability.

---

## 6. Dependencies

| Agent | Role |
|-------|------|
| `A9_Principal_Context_Agent` | Source of principal profiles with `client_id` |
| `A9_Data_Product_Agent` | Data product registry, SQL execution, view management |
| `A9_Situation_Awareness_Agent` | Primary consumer — KPI monitoring uses DGA for scoped KPI resolution |
| `A9_Deep_Analysis_Agent` | Uses DGA for dimension resolution |

### Registry Providers Used

| Provider | Purpose |
|----------|---------|
| `BusinessGlossaryProvider` | Business-to-technical term translation |
| `KPIProvider` | KPI definitions, metadata, data product mappings |
| `BusinessProcessProvider` | KPI-to-business-process associations |

---

## 7. Configuration

```python
class A9DataGovernanceAgentConfig(BaseModel):
    agent_name: str = "A9_Data_Governance_Agent"
```

Minimal configuration. The DGA's behavior is driven by registry data, not config parameters.

---

## 8. Pydantic Models

All defined in `src/agents/models/data_governance_models.py`:

| Model | Used By |
|-------|---------|
| `BusinessTermTranslationRequest/Response` | `translate_business_terms()` |
| `DataAccessValidationRequest/Response` | `validate_data_access()` |
| `KPIDataProductMappingRequest/Response` | `map_kpis_to_data_products()` |
| `KPIViewNameRequest/Response` | `get_view_name_for_kpi()` |
| `DataLineageRequest/Response` | `get_data_lineage()` (stub) |
| `DataQualityCheckRequest/Response` | `check_data_quality()` (stub) |
| `DataAssetPathRequest/Response` | Asset path resolution (stub) |

---

## 9. Not Yet Implemented

These capabilities are defined in the models but return stubs:

| Method | Current State | When Needed |
|--------|--------------|-------------|
| `get_data_lineage()` | Returns empty nodes/edges | When audit trail is a customer requirement |
| `check_data_quality()` | Returns hardcoded metrics (0.98/0.95/1.0) | When data quality monitoring is a feature |
| `validate_semantic_query()` | Not implemented | When NLP-driven analytics needs governance |
| LLM-assisted synonym harvesting | Not implemented | When glossary coverage is insufficient |
| Dynamic Data Asset Discovery | Not implemented | When multiple asset stores need resolution |

---

## 10. Compliance

- A2A Pydantic I/O for all requests/responses — no raw dicts
- Lifecycle: `create()` → `connect()` → entrypoints → `disconnect()`
- All registry access through Registry Factory providers
- No direct `anthropic` / `openai` imports
- No local registry caching — always reads from providers
- Standard error handling: ConfigurationError, ProcessingError, ValidationError

---

## 11. Future Roadmap

| Capability | Trigger |
|-----------|---------|
| Real `validate_data_access()` with client_id matching | Phase 10B-DGA (in progress) |
| Client-scoped `map_kpis_to_data_products()` | Phase 10B-DGA (in progress) |
| Query dialect layer for new connectors | Phase 10C (after DGA wiring) |
| Data lineage tracking | Customer requirement |
| Data quality monitoring | Customer requirement |
| LLM-assisted synonym harvesting | When glossary coverage gaps appear in production |
| RAG pattern for glossary lookups | When glossary exceeds manual maintenance scale |
