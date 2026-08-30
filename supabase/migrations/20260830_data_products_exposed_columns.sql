-- DEVELOPMENT_PLAN.md Phase 16, step 5: exposed_columns is the last of the
-- three genuinely-live views[].llm_profile sections found during the step-5
-- yaml.safe_load audit (dimension_semantics and dimension_hierarchies were
-- migrated first). Named at the time as "the clearest concrete next unit of
-- step 5 work" and deliberately deferred as low-value/low-risk: its only
-- call path (A9_Data_Product_Agent._resolve_attribute_name's label-first
-- short-circuit) is the same last-resort fallback column_aliases uses,
-- unreachable for lubricants/apex_lubricants/hess because their
-- source_system routes explicitly before ever reaching it (CLAUDE.md rule
-- 9) -- real-world reachability today is bicycle only. Migrated anyway so
-- the registry becomes a complete substitute for the YAML contracts before
-- they are deleted, same reasoning already applied to column_aliases.
--
-- Keyed by lowercased view name (Dict[str, List[str]]), not a flat list,
-- because the pre-existing YAML-scan code (_get_exposed_columns) already
-- looks up by view name with a fallback to FI_Star_View -- every seeded
-- contract today declares exactly one view, but the shape stays faithful
-- to what the code has always supported rather than flattening it away.
--
-- Same "one contract fact, one place" pattern as dimension_semantics /
-- dimension_hierarchies / column_aliases; DatabaseRegistryProvider's
-- serialize/deserialize path is fully generic, no provider changes needed.

ALTER TABLE data_products
    ADD COLUMN IF NOT EXISTS exposed_columns JSONB;

COMMENT ON COLUMN data_products.exposed_columns IS
    'Per-view allow-list of column labels exposed to KPI SQL generation, keyed by lowercased view name (e.g. {"hessstarschemaview": ["transaction_id", "fiscal_year", ...]}). Consumed by A9_Data_Product_Agent._get_exposed_columns as the LAST-RESORT fallback inside _resolve_attribute_name/_generate_sql_for_kpi -- reachable in practice only for source_system values with no explicit Tier-1 routing branch (e.g. duckdb). NULL/empty means not yet migrated off the legacy YAML contract for this data product. See docs -- DEVELOPMENT_PLAN.md Phase 16 step 5.';
