-- DEVELOPMENT_PLAN.md Phase 16, step 1: dimension_semantics is the ONE live
-- contract read (_dims_from_contract, a9_deep_analysis_agent.py) and it comes
-- from YAML only today -- confirmed live against lubricants 2026-08-29, not
-- just the Hess fixture: GET /registry/data-products?client_id=lubricants
-- returns a `views` field shaped {name, description, sql_definition,
-- depends_on}, structurally incapable of holding dimension_semantics even if
-- the code tried to read it from there.
--
-- Mirrors the time_dimensions column (20260724_data_products_time_dimensions_
-- column.sql) -- same "one contract fact, one place" pattern, now mature
-- rather than the transitional metadata-only phase time_dimensions started in.
-- DatabaseRegistryProvider's serialize/deserialize path is fully generic
-- (introspects information_schema.columns at runtime, no hand-maintained
-- field list to update) -- this column is the only change needed on the
-- persistence side.
--
-- fallback_group_by_dimensions is NOT given a column here -- its one real
-- consumer (A9_Data_Product_Agent._collect_group_by_items, tier 4) already
-- reads it from the existing metadata JSONB column
-- (DataProduct.metadata['fallback_group_by_dimensions']), so the fix for that
-- field is a seed-data addition, not a schema change.

ALTER TABLE data_products
    ADD COLUMN IF NOT EXISTS dimension_semantics JSONB;

COMMENT ON COLUMN data_products.dimension_semantics IS
    'Ordered list of dimension column names this data product declares as analysis-worthy -- the client''s own statement of what matters, honoured verbatim by A9_Deep_Analysis_Agent._dims_from_contract (no re-ranking). NULL/empty means not yet migrated off the legacy YAML contract for this data product; _dims_from_contract falls back to the YAML scan in that case. See docs -- DEVELOPMENT_PLAN.md Phase 16 step 1.';
