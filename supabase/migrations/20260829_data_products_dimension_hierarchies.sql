-- DEVELOPMENT_PLAN.md Phase 16, step 5: dimension_hierarchies is a THIRD
-- YAML-only, live section of views[].llm_profile that the original Phase 16
-- finding table (step 0's audit) did not catalogue -- found while auditing
-- every yaml.safe_load call site in src/agents/** before attempting to
-- delete any of the 12 contract files, per that step's own precondition
-- ("only safe once nothing reads them").
--
-- Genuinely live, with real behavioural impact: A9_Deep_Analysis_Agent's
-- execute_deep_analysis reads this via _hierarchies_from_contract() and, when
-- non-empty, takes the HIERARCHICAL DRILL analysis path instead of flat
-- dimension ranking -- a behavioural fork, not an ordering hint. Only
-- hess_financials.yaml and fi_star_schema.yaml (bicycle) declare this
-- section; lubricants_star_schema.yaml and lubricants_snowflake.yaml (apex)
-- never did, so those two clients are unaffected either way -- nothing lost
-- for them by this column being empty.
--
-- Same "one contract fact, one place" pattern as dimension_semantics;
-- DatabaseRegistryProvider's serialize/deserialize path is fully generic.

ALTER TABLE data_products
    ADD COLUMN IF NOT EXISTS dimension_hierarchies JSONB;

COMMENT ON COLUMN data_products.dimension_hierarchies IS
    'Named drill paths for hierarchical Deep Analysis (e.g. {"geography": ["country","basin_name","asset_name"]}) -- distinct from dimension_semantics (a flat ranked list). When non-empty, A9_Deep_Analysis_Agent takes the hierarchical-drill path instead of flat dimension ranking. NULL/empty means not yet migrated for this data product (or genuinely never declared, for clients whose YAML never had this section). See docs -- DEVELOPMENT_PLAN.md Phase 16 step 5.';
