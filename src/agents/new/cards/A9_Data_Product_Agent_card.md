# A9_Data_Product_Agent Card

Status: MVP (contract-driven SQL generation)

## Overview
The `A9_Data_Product_Agent` is responsible for all SQL generation and execution against data products. It reads from contract YAML files to understand schema, KPIs, and column mappings.

## Protocol Entrypoints
- `generate_sql_for_kpi(kpi_definition, timeframe, filters, topn, breakdown, override_group_by) -> Dict`
- `execute_sql(sql) -> Dict`
- `register_tables_from_contract(contract_path) -> Dict`
- `create_view_from_contract(contract_path, view_name) -> Dict`

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

## Contract Path Resolution
Uses `_contract_path()` method to resolve contract files from registry:
- Primary: Registry's `yaml_contract_path` from `data_product_registry.yaml`
- Canonical location: `src/registry_references/data_product_registry/data_products/fi_star_schema.yaml`

## SQL Generation Features
- **Timeframe filtering**: Joins with `time_dim` table for fiscal year/quarter filtering
- **Delta calculation**: CTE-based queries with `delta_prev` metric for current vs previous comparison
- **Column aliases**: Reads `column_aliases` from contract for measure, date, version columns
- **TopN ranking**: Supports `top`/`bottom` N by various metrics including `delta_prev`

## Recent Updates (Dec 2025)
- Contract path consolidated to single source of truth in `registry_references`
- Added CTE-based `delta_prev` SQL generation for timeframe comparisons
- Fixed column alias resolution from contract `column_aliases` section
- Added debug logging for topn and timeframe parameters
