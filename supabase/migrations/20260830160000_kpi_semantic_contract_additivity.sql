-- DEVELOPMENT_PLAN.md Phase 17, T1 (second half): the KPI Semantic Contract's
-- §3 fields (docs/architecture/kpi_semantic_contract.md) -- additivity and
-- aggregation, a property of the KPI ALONE. Distinct from §4's
-- not_sliceable_by (kpis.not_sliceable_by, added 20260815/20260816): that is
-- a KPI x dimension property (is this cut meaningful at all?); this is a
-- KPI-only property (may this KPI's own segment values be summed to a
-- total?). The two do not collapse into one field -- see §4.1's own worked
-- example (net_revenue is additive AND sliceable by customer; gross_margin_pct
-- is not additive yet was sliceable by product on the same dataset where it
-- wasn't sliceable by customer).
--
-- additive_across_dimensions has NO DEFAULT (nullable, defaults to NULL) --
-- deliberately, not TRUE. §6 "Honest limitations": assuming additive-by-
-- default would silently re-authorise the exact defect this contract exists
-- to close (the Aug 6 bug: 43.24+16.76+15.18 summed as an enterprise move on
-- a KPI whose real enterprise move was -1.67pp). NULL means "not yet
-- declared for this KPI" -- application code must never treat NULL as TRUE.

-- Postgres has no `ADD CONSTRAINT IF NOT EXISTS` -- CHECK constraints are
-- declared inline on ADD COLUMN instead (which DOES support IF NOT EXISTS),
-- so this migration stays safely re-runnable like every other one here.
ALTER TABLE kpis
    ADD COLUMN IF NOT EXISTS unit_class TEXT
        CHECK (unit_class IS NULL OR unit_class IN ('currency', 'ratio', 'count', 'duration')),
    ADD COLUMN IF NOT EXISTS additive_across_dimensions BOOLEAN,
    ADD COLUMN IF NOT EXISTS aggregation_method TEXT
        CHECK (aggregation_method IS NULL OR aggregation_method IN ('sum', 'weighted_avg', 'ratio_of_sums')),
    ADD COLUMN IF NOT EXISTS weight_column TEXT,
    ADD COLUMN IF NOT EXISTS sign_convention TEXT
        CHECK (sign_convention IS NULL OR sign_convention IN ('natural', 'negative_stored')),
    ADD COLUMN IF NOT EXISTS inverse_logic BOOLEAN,
    ADD COLUMN IF NOT EXISTS scope_eligible TEXT
        CHECK (scope_eligible IS NULL OR scope_eligible IN ('enterprise', 'segment', 'both'));

COMMENT ON COLUMN kpis.additive_across_dimensions IS
    'Whether this KPI''s own segment-level values may be validly summed to a total (e.g. net_revenue: true; gross_margin_pct: false -- percentages don''t add). NULL means not yet declared -- application code must never treat NULL as TRUE. docs/architecture/kpi_semantic_contract.md §3.';

COMMENT ON COLUMN kpis.aggregation_method IS
    'How to roll segment values up when additive_across_dimensions is false: sum | weighted_avg | ratio_of_sums. Required (by convention, not a DB constraint) when additive_across_dimensions=false.';

COMMENT ON COLUMN kpis.weight_column IS
    'KPI id (or column) supplying the weight for aggregation_method=weighted_avg, e.g. net_revenue weighting gross_margin_pct.';

COMMENT ON COLUMN kpis.sign_convention IS
    'KPI-LEVEL sign convention -- distinct from data_products.measure_semantics (data-product-level, Phase 16 step 2, already live). negative_stored means this KPI''s own values arrive as negative debits (e.g. cogs).';

COMMENT ON COLUMN kpis.inverse_logic IS
    'Whether a rise in this KPI is bad. Proposed KPI-level source of truth per §3 -- additive to, not a migration of, the existing per-comparison inverse_logic already carried on kpi_thresholds rows.';

COMMENT ON COLUMN kpis.scope_eligible IS
    'Whether this KPI can legitimately be claimed at enterprise level, only at segment level, or both. Leaned on by the Phase 17 T2 KPI decomposition model.';

COMMENT ON COLUMN kpis.unit_class IS
    'How to format this KPI''s values, and whether a delta is expressed in pp or %.';
