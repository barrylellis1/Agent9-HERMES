-- DEVELOPMENT_PLAN.md Phase 16, step 4: column_aliases is the ONE of the four
-- remaining YAML contract sections (business_terms, column_aliases,
-- supported_business_processes, connection) that has a genuine live reader --
-- A9_Data_Product_Agent._get_contract_column_aliases, called from
-- _generate_sql_for_kpi's LAST-RESORT fallback branch (only reached when
-- source_system routing, CLAUDE.md rule 9, cannot resolve a backend). None of
-- the seeded BigQuery/Snowflake/SQL Server clients ever reach this branch;
-- it exists for a DuckDB-style client with no resolvable source_system.
--
-- The other three sections were audited as part of this step and found to
-- have ZERO live readers anywhere in src/agents/** (confirmed by search, not
-- assumed) -- see the Phase 16 step 4 write-up for what happened to each:
-- business_terms/supported_business_processes have already-migrated,
-- already-Supabase-backed equivalents (business_glossary_terms,
-- DataProduct.related_business_processes); connection is dead AND carries a
-- plaintext password, superseded by the proper connection_profiles
-- mechanism -- recommended for deletion (not migration) when the YAML files
-- are removed in step 5.
--
-- Same "one contract fact, one place" pattern as dimension_semantics/
-- measure_semantics; DatabaseRegistryProvider's serialize/deserialize path
-- is fully generic, no provider-code change needed.

ALTER TABLE data_products
    ADD COLUMN IF NOT EXISTS column_aliases JSONB;

COMMENT ON COLUMN data_products.column_aliases IS
    'Business-name-to-technical-column aliases: {measure, date, version, default_version_value}. Consumed by A9_Data_Product_Agent._get_contract_column_aliases as the last-resort fallback inside _generate_sql_for_kpi, reached only when source_system routing cannot resolve a backend. NULL means not yet migrated off the legacy YAML contract; the method falls back to the YAML scan in that case. See docs -- DEVELOPMENT_PLAN.md Phase 16 step 4.';
