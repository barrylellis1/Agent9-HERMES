# A9_Data_Governance_Agent Card

Status: MVP

## Overview
The `A9_Data_Governance_Agent` handles business term resolution, KPI-to-data-product mapping, and data access validation.

## Protocol Entrypoints
- `map_kpis_to_data_products(request: KPIDataProductMappingRequest) -> KPIDataProductMappingResponse`
- `resolve_business_term(term: str) -> Dict`
- `validate_data_access(principal_id: str, data_product_id: str) -> bool`

## Dependencies
- Registry providers (KPI, Business Glossary, Data Product)

## Contract Path Resolution
Uses `_contract_path()` method to resolve contract files:
- Canonical location: `src/registry_references/data_product_registry/data_products/fi_star_schema.yaml`

## KPI Lookup & View Resolution
- Normalizes KPI identifiers (e.g., `Gross Revenue` → `gross_revenue`) and exhaustively scans registry entries to tolerate naming drift before failing.
- Defers view-name decisions to upstream registry data; if a view cannot be found, returns `"unknown"` rather than synthesizing a `view_*` alias.

## Recent Updates (Dec 2025)
- Contract path consolidated to single source of truth in `registry_references`

## Phase 10B-DGA: Data Governance Wiring (Apr 2026)
- `validate_data_access()` now enforces real client_id filtering — no longer returns allow-all
- `map_kpis_to_data_products()` filters mapped results by client_id, preventing cross-client KPI visibility
- Post-bootstrap DGA wiring: A9_Orchestrator calls `runtime._wire_governance_dependencies()` after all agents connect, injecting DGA into Data Product and Deep Analysis agents
- Client isolation hardened: all governance queries scoped to PrincipalContext.client_id
