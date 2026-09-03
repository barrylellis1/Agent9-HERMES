-- Adds 'product' to kpi_decompositions.operation (2026-09-02 -- "strengthen the
-- Core Spine", cross-data-product example): net_revenue = sales_order_count *
-- average_order_value (dp_lubricants_sales -> dp_lubricants_financials).
-- See src/registry/models/kpi_decomposition.py's module docstring for why this
-- was added (and why a bare 'difference' literal stays dropped).
--
-- Postgres has no ALTER CHECK CONSTRAINT; drop and recreate is the standard
-- idiom. Column-level default/nullability are untouched.

ALTER TABLE kpi_decompositions DROP CONSTRAINT IF EXISTS kpi_decompositions_operation_check;
ALTER TABLE kpi_decompositions ADD CONSTRAINT kpi_decompositions_operation_check
    CHECK (operation IN ('linear', 'ratio', 'product'));

COMMENT ON COLUMN kpi_decompositions.operation IS
    'linear: this child contributes sign * child_value to a signed sum producing the parent. ratio: child_kpi_id / weight_kpi_id = parent (weight_kpi_id required, exactly one ratio edge per parent). product: all of the parent''s product children multiply together to produce the parent.';
