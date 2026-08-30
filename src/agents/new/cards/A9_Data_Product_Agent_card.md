# A9_Data_Product_Agent Card

Status: Active (contract-driven SQL generation; BigQuery + SQL Server + DuckDB + Snowflake backends; DGA mandatory; `_get_view_name_from_kpi` preserves KPI metadata fallback even when DGA throws; SF-DIAG-ENV log dumps all SF_ env vars at connection time for Railway diagnostics)

## Overview
The `A9_Data_Product_Agent` is responsible for contract-driven SQL orchestration **and** the automated onboarding “data factory” pipeline. It reads from database-backed registry metadata plus YAML contracts to understand schema, KPIs, and column mappings, and it now profiles upstream platforms (BigQuery, Snowflake, Databricks, Datasphere) via pluggable adapters.

## Protocol Entrypoints
- Query execution:
  - `generate_sql_for_kpi(kpi_definition, timeframe, filters, topn, breakdown, override_group_by) -> Dict`
  - `execute_sql(sql, parameters=None, principal_context=None, data_product_id=None) -> Dict`  — routes to BigQuery, SQL Server (bracket-quoted T-SQL detection), Snowflake, or DuckDB. **Infra B3 (Jul 2026):** when principal_context carries a client_id AND data_product_id is given, DGA `validate_data_access` gates execution before routing — cross-client access returns `success: False` with an "Access denied by Data Governance" message; a scoped principal with `data_governance_agent=None` is denied fail-closed.
  - `register_tables_from_contract(contract_path) -> Dict`
  - `create_view_from_contract(contract_path, view_name) -> Dict`
- Data factory onboarding:
  - `inspect_source_schema(DataProductSchemaInspectionRequest) -> DataProductSchemaInspectionResponse`
  - `generate_contract_yaml(DataProductContractGenerationRequest) -> DataProductContractGenerationResponse`
  - `register_data_product(DataProductRegistrationRequest) -> DataProductRegistrationResponse` — as of Phase 12G (Jul 2026), when `request.schema_summary` (profiled `TableProfile[]` from `inspect_source_schema`) is supplied, this also synthesizes and persists `tables`/`views`/`time_dimensions` on the `DataProduct` row instead of registering an empty shell. See `_synthesize_time_dimensions`/`_derive_tables_and_views`/`_detect_time_dimension_for_table` — pure heuristics over profiled columns, no LLM call. Detection priority: fiscal_year+fiscal_period column pair > fiscal_year alone > best single date/timestamp column (business-date names like `transaction_date` ranked above audit timestamps like `created_at`). Logs a warning (not silent) when no time dimension can be synthesized, since `_resolve_time_spec` falls back to a hardcoded `transaction_date` guess that fails at query execution against real schemas.
  - `sync_related_business_processes(DataProductBusinessProcessSyncRequest) -> DataProductBusinessProcessSyncResponse` — unions a set of business-process IDs into a `DataProduct.related_business_processes`. Called by `A9_KPI_Assistant_Agent.finalize_kpis` after KPIs are registered (KPIs are the only place `business_process_ids` gets set today). Fails loud on client_id mismatch; best-effort/non-fatal from the caller's side.
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
- (Feb 2026) Multi-tenant architecture changes; client_id propagation through registry and seed scripts

## Phase 10B-DGA: Data Governance Wiring (Apr 2026)
- Removed broken DGA acquisition from `_async_init()` and `connect()` — both methods were failing silently and falling back to local resolution
- `data_governance_agent` now initialized to `None` in `__init__` and wired post-bootstrap by A9_Orchestrator via `runtime._wire_governance_dependencies()`
- Fixes Data Governance agent circular dependency: DPA no longer tries to instantiate DGA during its own initialization
- DPA continues to cache DGA reference after post-bootstrap wiring; all KPI/data-product queries use the injected agent
- Removed 2 remaining `if self.data_governance_agent:` guards — DGA calls are now always attempted:
  - `_get_view_name_from_kpi()` (line ~2871): DGA is primary path, KPI metadata fallback still available
  - `_lookup_kpi_by_name()` (line ~3752): KPI mapping enrichment via DGA, silently skipped on failure

- May 2026: Bug fixes — NaN normalization, multi-tenant kpi_registry collision fix, comparison value extraction
- May 2026 (Infra A4-a): Per-request data product registry refresh — new `_refresh_data_product_registry()` helper calls `data_product_provider.load()` inside `get_data_product` and `generate_sql_for_kpi`. Non-fatal; falls back to cached state on provider error.
- May 2026 (Infra A4-d): New public `test_connection(data_product_id)` method — routes to the correct backend via `_resolve_source_system()` and runs `SELECT 1` (or equivalent). Returns `{"status", "source_system", "latency_ms", "error"}`. Called by `AgentRuntime.probe_connection_health()` for the Connection Health Dashboard admin endpoint.
- May 2026: Time dimension SQL aliasing — `_build_bq_dimensional_sql` and `_build_sf_dimensional_sql` now alias SQL expressions (e.g. `CONCAT(...)`) as `_td_period` in CTE inner queries so outer CTE can reference the alias by name.

## Phase 10F — Uniform Time Dimension Layer (May 2026)
- `_build_bq_dimensional_sql`, `_build_sf_dimensional_sql`, `_build_ss_dimensional_sql` all replaced with `TimeFilter`-based implementations — no hardcoded `transaction_date` fallback.
- New `_build_databricks_dimensional_sql`: standard ANSI SQL (no backticks/brackets), `LIMIT n` for TopN. Routed via `source_system='databricks'` in `generate_sql_for_kpi`.
- `_resolve_time_spec(data_product_id)`: looks up primary `TimeDimensionSpec` from registry, returns plain dict for `TimeFilter`. Falls back to `{"type": "date", "column": "transaction_date"}`.
- `generate_sql_for_kpi` routes by `_resolve_source_system()` (Tier 1), regex fallback (Tier 2): bigquery → BQ builder, sqlserver/mssql → SS builder, snowflake → SF builder, databricks → DB builder, else → DuckDB path.
- `TimeDimensionSpec.fiscal_year_start_month` (int, default 1): non-January FY support — `TimeFilter` converts calendar month to fiscal period/year using this offset.

## Infra A2: Registry write persistence fix (Jul 2026)
- `_load_registry()`'s data-product creation loop and `register_data_product()` now `await self.data_product_provider.register()` / `.upsert()` — `DatabaseRegistryProvider.register/upsert/delete` were sync methods returning an unawaited coroutine, so every write silently never reached Supabase (cache-only, lost on restart). Now genuinely async everywhere. See `src/registry/providers/database_provider.py` and `src/api/routes/registry.py` for the full fix (also corrected: wrong `ON CONFLICT` key_fields for bootstrap-shared providers, and a JSON-blob serialization column that doesn't exist on any of the 5 registry tables).
- Known follow-up (not fixed): `register_data_product()` passes a plain `dict` to `upsert()` where a Pydantic model is expected — a separate, pre-existing bug in the data-factory onboarding path that predates this fix and wasn't reachable/testable in this pass.

## Categorical value sampling (Jul 2026)
- `TableColumnProfile.sample_values` (field existed, never populated) is now filled in by `_populate_categorical_sample_values`, called once from the shared `_profile_table` dispatcher after any backend's column metadata comes back — not duplicated per backend. `_is_categorical_candidate` selects text-typed columns that aren't primary/foreign keys or already tagged time/measure; `_sample_distinct_values` runs `SELECT DISTINCT ... LIMIT N` against the live source, with a small per-backend branch (identifier quoting, qualified table name, `LIMIT`/`TOP N` syntax) rather than a new duplicated profiling method per backend.
- Rationale: without real sample values, KPI SQL generation only ever saw a column's name+type and had to guess WHERE-filter literals (e.g. `account_category = 'COGS'`) — a guess that doesn't match any real row doesn't error, it silently returns a NULL aggregate that still passes Query Validation as "success" (found live 2026-07-24 onboarding Brookshire Brothers, reusing Apex Lubricants' Snowflake schema — real convention is `account_type = 'COGS'`). `A9_KPI_Assistant_Agent._build_suggestion_user_prompt` now lists real sampled values per dimension and instructs the LLM to only use one of those literals.
- Defense in depth: `_validate_single_kpi_query` now also flags a KPI whose `value` column is NULL across every returned row as `warning_message` (status stays `"success"` — a true zero-match result is plausible too) instead of a silent green checkmark. Rendered as an amber banner in `DataProductOnboardingNew.tsx`'s Query Validation step.

## `include_total` → `GROUP BY ROLLUP` (Aug 2026)

`generate_sql_for_kpi(..., include_total=True)` appends `GROUP BY ROLLUP(<dims>)` on the breakdown path, adding one row with a NULL dimension that carries the aggregate over all rows.

**Why the DPA owns this.** A caller cannot get a dimension's total by adding the member rows. For a ratio KPI that is not merely imprecise — summing per-product gross margin gave **452.95%** against a true **29.43%**, and summing the pp deltas gave **-53pp** against an enterprise move of about **-5pp**. The total has to be re-aggregated from the underlying components (`SUM(gp)/SUM(rev)`), which only the query can do, and the KPI's registered expression is already the definition of that calculation. Doing it here keeps the arithmetic inside the curated data product instead of reimplementing it in an agent, and means a KPI nobody configured still yields a correct total.

**Off by default** — purely additive, so no existing caller changes shape.

**Never applied on the topn branch.** That path ends in `ORDER BY ... LIMIT n`; a LIMIT either clips the total row or keeps it and drops a real member, and the total sorts unpredictably against the members, so which is lost is not even stable.

Backends: `ROLLUP` is standard across BigQuery, Snowflake, SQL Server, Postgres and DuckDB. Currently wired on the BigQuery builder (`_build_bq_dimensional_sql`); add the same one-line grouping switch to the other builders when a client needs it.

Tests: `tests/unit/test_rollup_total_sql.py`.

## `comparison_period` Was Ignored on the Non-Breakdown Path (Aug 2026)

`_build_bq_dimensional_sql` hardcoded `TimeFilter.current_condition` in its non-breakdown early return, so a caller requesting the PRIOR scalar value silently received the CURRENT one. Found by a live run: an overall gross margin logged `current=29.94 previous=29.94 delta=0.0`, which would have rendered a confident "0.00pp" movement on a KPI that had actually moved -4.49pp.

The breakdown branch had always honoured the flag. Only the scalar path did not, and nothing exercised it until Deep Analysis began fetching a path-independent overall figure. A parameter that is silently dropped is worse than one that errors — the caller gets a plausible number and no signal.

**All four backends, not just BigQuery (Aug 2026).** The `comparison_period` defect above was originally fixed only in `_build_bq_dimensional_sql`. The identical bug was present in the Snowflake, SQL Server and Databricks builders — which are what Apex and Hess actually run on, so those tenants would have received a confident "0.00pp" overall movement. All four now honour the flag, with a parametrised regression test across every builder (`TestComparisonPeriodHonouredOnEveryBackend`). Fixing one backend and leaving three is how a bug returns wearing a different client's name.

`include_total` / ROLLUP remains wired on the BigQuery builder only. That is deliberate and currently harmless: the parameter is not threaded to the other builders, so they ignore it, and the overall total on every backend comes from Deep Analysis's path-independent scalar pair rather than from a ROLLUP row. Add the one-line grouping switch to a given builder only when there is a way to verify it against that warehouse.

## `generate_monthly_series_sql` — SQL generation belongs here, not in a calling agent (Aug 2026)

**Found live, mid-build, from a direct question: "isn't all SQL supposed to go through the DPA?"**
`A9_Deep_Analysis_Agent`'s new Phase 20 causal-neighbourhood trend chart (see that agent's own card)
needed a monthly time-series query for KPIs other than its own. Its first implementation built that SQL
directly in DA via regex on the KPI's raw `sql_query`, then only handed DPA the finished string to
`execute_sql` — DPA ran it, but never generated it. That's exactly the split CLAUDE.md's SQL Backend
Routing rule (§9) and this card's own Overview line ("responsible for contract-driven SQL
orchestration") exist to prevent.

**It gets worse before it gets better.** The pattern DA copied — build monthly-series SQL via regex
directly in the calling agent — wasn't invented for this feature. `A9_Situation_Awareness_Agent` already
had an identical method, `_bq_monthly_series_sql`, doing the same thing for its own KPI-tile trend
sparklines. And this project's own Phase 10C architectural decision (`docs/architecture/` — MCP-first
connectivity) had **already named that exact SA method as dead code to be removed**, years before this
session, not a pattern to extend. DA's new method copied a violation the codebase had already flagged
and never cleaned up. Two independent instances of the same class of bug is why this got a same-day fix
rather than a backlog item.

**The fix**: `generate_monthly_series_sql(kpi_definition, num_months=9) -> Dict[str, Any]` (sync — no I/O
of its own, matches the sync convention of this agent's other internal SQL builders like
`_build_bq_dimensional_sql`) and its helper `_build_bq_monthly_series_sql(base_sql, date_col,
num_months)` now live here, as the one place this SQL text gets generated for any caller. Same
`{"success", "sql", ...}` return shape as `generate_sql_for_kpi`. Uses the same Tier-1 (`_resolve_source_system`
registry lookup) / Tier-2 (backtick-table regex fallback) routing convention already established in
`generate_sql_for_kpi` immediately above. **BigQuery-backed KPIs only in this pass** — not a new
limitation, the scope this feature was built and live-verified against; a non-BigQuery KPI gets
`{"success": False}`, never a wrong-dialect query attempt or a raised exception.

**Deliberately NOT fixed in this pass**: `A9_Situation_Awareness_Agent._bq_monthly_series_sql` (and its
SQL Server/Snowflake siblings `_ss_monthly_series_sql`/`_sf_monthly_series_sql`) are left exactly where
they were — pre-existing, already-flagged-for-removal (Phase 10C), but genuinely live and feeding the
dashboard's KPI-tile trend sparklines. Refactoring SA to call this new DPA method instead is the correct
next step, but it touches a currently-stable, demo-relied-upon path and was deliberately deferred rather
than rushed the night before a demo. Tracked, not forgotten.

Tests: `tests/unit/test_data_product_agent_kpi_methods.py::TestGenerateMonthlySeriesSql` (BigQuery
detection via both Tier 1 and Tier 2, non-BigQuery/no-SQL/unparseable-SQL all fail gracefully rather than
raise, custom `date_column` from KPI metadata honoured, non-date `WHERE` conditions preserved).

## `_resolve_attribute_name` bypassed the registry factory entirely for glossary lookups (Aug 2026)
- Found auditing for other instances of the `A9_Principal_Context_Agent` startup-race bug shape: this method never called `registry_factory.get_provider("business_glossary")` at all — every call constructed a fresh `BusinessGlossaryProvider()`, which loads directly from `src/registry/data/business_glossary.yaml` (a `yaml.safe_load()` in an agent file — the exact pattern rule 6 in root `CLAUDE.md` prohibits). This ran regardless of whether `RegistryBootstrap` had already hydrated and registered a Supabase-backed instance into the shared factory.
- Fixed: now checks `self.registry_factory.get_provider("business_glossary")` first — same pattern `A9_Data_Governance_Agent.connect()` already uses — and only falls back to the raw YAML-backed instance if the factory has none registered.
- Business glossary terms are intentionally shared across all clients by design (`client_id=None` at Supabase hydration, per-client override supported via `client_id`/`get_by_client()` for terms that need it) — this fix does not change that; it only stops silently maintaining a second, always-stale, never-Supabase-synced copy alongside the real one.

## `_get_contract_column_aliases` is registry-first as of Phase 16 step 4 (Aug 2026)
- `DataProduct.column_aliases` is a new field (sibling of `dimension_semantics`/`measure_semantics`); the method tries the registry record first, only scanning the legacy YAML contract when the registry field is empty. Same posture as `A9_Deep_Analysis_Agent._dims_from_contract` (step 1).
- Only genuinely live for one client: this method is `_generate_sql_for_kpi`'s last-resort fallback inside `generate_sql_for_kpi`, reached only when `_resolve_source_system` and the backtick/bracket regex both fail to identify a backend — none of the seeded BigQuery/Snowflake/SQL Server clients ever reach it. It exists for bicycle (`source_system=duckdb`), and is likely moot even there since all of bicycle's KPIs already carry a literal `sql_query`.
- **Found and fixed a real cross-tenant bug while migrating it**: the method took `data_product_id` as a parameter but its YAML fallback called `self._contract_path()` with no argument — silently dropping it and always resolving to the bicycle default contract (`fi_star_schema.yaml`) regardless of which data product was actually being asked about. Same shape as the cross-tenant contamination already fixed once for `_dims_from_contract` (Jul 2026 per that agent's card / Phase 16's own finding). Fixed here by threading `data_product_id` through all 5 call sites inside `_generate_sql_for_kpi` (`getattr(kpi_definition, 'data_product_id', None)`) and passing it to `_contract_path` in the fallback branch.
- `business_terms`, `supported_business_processes`, and `connection` — the other three sections in the same YAML files — were investigated in the same pass and found to have ZERO live readers anywhere in `src/agents/**` (confirmed by grep, not assumed). No schema change was made for them: `business_terms`' actual content gap was backfilled as `business_glossary_terms` seed data (an existing, already-Supabase-backed mechanism); `supported_business_processes` is redundant with the existing `DataProduct.related_business_processes` field; `connection` is dead AND carries a plaintext local-dev password, superseded by the proper `connection_profiles` mechanism — recommended for deletion, not migration, when the YAML files are removed (Phase 16 step 5). See `DEVELOPMENT_PLAN.md`'s Phase 16 step 4 write-up for the full audit.
- Tests: `tests/unit/test_dpa_column_aliases_registry.py` — registry-wins-when-populated, empty-dict-treated-as-not-migrated, `data_product_id` genuinely reaches `_contract_path` (pins the bug fix), non-fatal degradation on missing registry factory / provider exception / missing or malformed YAML.
