# A9_Data_Product_Agent Card

Status: MVP (contract-driven SQL generation)

## Overview
The `A9_Data_Product_Agent` is responsible for contract-driven SQL orchestration **and** the automated onboarding “data factory” pipeline. It reads from Supabase-backed registry metadata plus YAML contracts to understand schema, KPIs, and column mappings, and it now profiles upstream platforms (BigQuery, Snowflake, Databricks, Datasphere) via pluggable adapters.

## Protocol Entrypoints
- Query execution:
  - `generate_sql_for_kpi(kpi_definition, timeframe, filters, topn, breakdown, override_group_by) -> Dict`
  - `execute_sql(sql) -> Dict`
  - `register_tables_from_contract(contract_path) -> Dict`
  - `create_view_from_contract(contract_path, view_name) -> Dict`
- Data factory onboarding:
  - `inspect_source_schema(DataProductSchemaInspectionRequest) -> DataProductSchemaInspectionResponse`
  - `generate_contract_yaml(DataProductContractGenerationRequest) -> DataProductContractGenerationResponse`
  - `register_data_product(DataProductRegistrationRequest) -> DataProductRegistrationResponse`
  - `validate_kpi_queries(KPIQueryValidationRequest) -> KPIQueryValidationResponse`

## Configuration Schema
Defined in `src/agents/agent_config_models.py`:

```python
class A9_Data_Product_Agent_Config(BaseModel):
    model_config = ConfigDict(extra="allow")
    database_type: str = "duckdb"
    database_path: str = "data/agent9-hermes-api.duckdb"
    enable_llm_sql: bool = False
    force_llm_sql: bool = False
```

## Dependencies
- `A9_Data_Governance_Agent` (business term resolution, KPI mappings)
- `A9_LLM_Service_Agent` (optional, for NL->SQL generation)
- `connection_profiles` module for secure credential routing
- Vendor SDK adapters (`google-cloud-bigquery`, Snowflake connector, Databricks SQL connector, SAP Datasphere Open SQL/OData) – loaded dynamically via the onboarding workflow.

## Contract Path Resolution
Uses `_contract_path()` method to resolve contract files from registry:
- Primary: Registry's `yaml_contract_path` from `data_product_registry.yaml`
- Canonical location: `src/registry_references/data_product_registry/data_products/fi_star_schema.yaml`

## SQL Generation Features
- **Timeframe filtering**: Joins with `time_dim` table for fiscal year/quarter filtering
- **Delta calculation**: CTE-based queries with `delta_prev` metric for current vs previous comparison
- **Column aliases**: Reads `column_aliases` from contract for measure, date, version columns
- **TopN ranking**: Supports `top`/`bottom` N by various metrics including `delta_prev`
- **View resolution**: Relies solely on governance metadata/contract hints; aborts loud if a view cannot be resolved instead of fabricating `view_*` aliases.
- **Time dimension bootstrap**: Recreates `time_dim` with an expanded 2021–2030 range on each run to guarantee consistent ISO date casting.

## Data Factory Features (NEW 2026)
- **Dynamic backend selection**: `inspect_source_schema` uses `_resolve_inspection_settings` to merge metadata from the request, registry entry, and connection profile, determining the `source_system` (DuckDB or BigQuery), schema/dataset, project, and connection parameters. The method then calls `_prepare_inspection_manager` to instantiate the correct `DatabaseManager` via `DatabaseManagerFactory`—reusing the existing DuckDB connection or creating a new BigQuery manager with scoped credentials.
- **Backend-specific profiling**: `_discover_tables_for_inspection` queries the appropriate INFORMATION_SCHEMA to enumerate tables/views, and `_profile_table` dispatches to `_profile_table_duckdb` or `_profile_table_bigquery` for metadata extraction (columns, types, row counts, samples, semantic tags). Each backend adapter enforces SELECT-only profiling with rate/cost limits.
- **Workflow automation**: Orchestrator invokes `inspect_source_schema → generate_contract_yaml → register_data_product`, then governance + ownership mapping. Outputs include `activation_context` so Decision Studio immediately surfaces new products.
- **Registry sync**: Supabase `data_products` rows now store multi-source connection descriptors, refresh cadence, yaml contract path, and provenance fields so Situation Awareness and embedded SAC cards display trustworthy metadata.
- **Security**: Credentials stay in git-ignored `secrets*/` folders or external vaults; adapters accept per-request overrides. Logging redacts secrets and tags events with `source_platform`.
- **Implementation status**: DuckDB and BigQuery backends are fully implemented and tested. Snowflake/Databricks/Datasphere adapters follow the same pattern and will be added as needed.

## Recent Updates (Dec 2025)
- Contract path consolidated to single source of truth in `registry_references`
- Added CTE-based `delta_prev` SQL generation for timeframe comparisons
- Fixed column alias resolution from contract `column_aliases` section
- Added debug logging for topn and timeframe parameters
- (Jan 2026) Added data factory onboarding entrypoints, adapter abstraction, and Supabase metadata sync requirements.
