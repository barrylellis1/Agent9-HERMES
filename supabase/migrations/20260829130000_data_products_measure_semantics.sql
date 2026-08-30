-- DEVELOPMENT_PLAN.md Phase 16, step 2: sign convention is a fact about the
-- data (which account types are stored negative), declared once on the data
-- product record -- a sibling of dimension_semantics/time_dimensions, same
-- "one contract fact, one place" pattern.
--
-- Shape: {"type_column": "account_type", "amount_column": "amount",
--          "stored_sign": {"Revenue": "positive", "COGS": "negative", ...}}
--
-- Consumed by src/registry/validators/measure_semantics_validator.py to catch
-- a KPI's sql_query re-negating a measure the contract already states is
-- negative -- the bug class that produced Hess's gross_margin_pct=165.57%
-- (true value 34.43%): COGS is stored negative in HessStarSchemaView, and
-- three seeded KPIs negate it again (`WHEN 'COGS' THEN -[amount]`), which
-- ADDS cost to revenue instead of subtracting it.
--
-- NULL means not yet declared for this data product -- the validator is a
-- no-op in that case (opt-in per client, same posture as dimension_semantics
-- being empty for an unmigrated client), not a validation failure.
--
-- NAMING NOTE (see DataProduct.measure_semantics docstring for the full
-- version): this is UNRELATED to `llm_profile.measure_semantics` inside the
-- legacy contract_yaml text consumed by the ad-hoc NL-to-SQL path
-- (a9_data_product_agent.py / a9_llm_service_agent.py) -- that shape is
-- {default_measure, default_aggregation} and lives at a different attribute
-- path, never colocated with this column. Flagged deliberately rather than
-- repeated silently, since the same key recurring with a different shape is
-- exactly the anti-pattern Phase 16 exists to close (see the `views` shape
-- collision documented in the Phase 16 finding).

ALTER TABLE data_products
    ADD COLUMN IF NOT EXISTS measure_semantics JSONB;

COMMENT ON COLUMN data_products.measure_semantics IS
    'Declared sign convention for this data product''s measure column: {type_column, amount_column, stored_sign: {account_type: "positive"|"negative"}}. Consumed by src/registry/validators/measure_semantics_validator.py to catch a KPI SQL re-negating an already-negative measure. NULL means not yet declared -- the validator no-ops. See docs -- DEVELOPMENT_PLAN.md Phase 16 step 2.';
