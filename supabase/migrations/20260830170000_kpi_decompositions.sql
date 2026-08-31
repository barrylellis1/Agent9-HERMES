-- DEVELOPMENT_PLAN.md Phase 17, T2: KPI decomposition / arithmetic-parentage
-- model ("solution finder input").
--
-- Distinct from kpi_relationships: that models CAUSAL claims between KPIs
-- (uncertain, gradeable, carrying confidence/provenance/causal_rung). This
-- models ARITHMETIC parentage -- true by construction from the KPI's own
-- formula. DEVELOPMENT_PLAN.md's "RESOLVED: derive the structure, author
-- the presentation": the GRAPH here is derived and required; LAYOUT
-- (collapse/order/emphasis for the Core Spine exhibit) is a separate,
-- optional, presentation-only concern this table deliberately does not
-- hold, so a restated fact can never drift from the KPI it restates.
--
-- Only 'linear' and 'ratio' operations -- see kpi_decomposition.py's module
-- docstring for why a bare 'difference' literal was dropped in favour of a
-- per-edge signed 'linear' sum (each KPI's own reported value already
-- carries its intended sign via KPI.sign_convention, so "gross_profit
-- decomposes into net_revenue and cogs" is net_revenue - cogs, not a plain
-- addition of both KPI values).

CREATE TABLE IF NOT EXISTS kpi_decompositions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       TEXT NOT NULL,
    parent_kpi_id   TEXT NOT NULL,
    child_kpi_id    TEXT NOT NULL,
    operation       TEXT NOT NULL
        CHECK (operation IN ('linear', 'ratio')),
    sign            SMALLINT NOT NULL DEFAULT 1
        CHECK (sign IN (1, -1)),
    weight_kpi_id   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT kpi_decompositions_pk UNIQUE (client_id, parent_kpi_id, child_kpi_id),
    CONSTRAINT kpi_decompositions_no_self_loop CHECK (parent_kpi_id <> child_kpi_id),
    CONSTRAINT kpi_decompositions_ratio_requires_weight
        CHECK (operation <> 'ratio' OR weight_kpi_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_kpi_decompositions_client_parent
    ON kpi_decompositions (client_id, parent_kpi_id);
CREATE INDEX IF NOT EXISTS idx_kpi_decompositions_client_child
    ON kpi_decompositions (client_id, child_kpi_id);

COMMENT ON TABLE kpi_decompositions IS
    'Arithmetic parentage between KPIs -- parent_kpi_id decomposes (in part) into child_kpi_id. True by construction from the KPI''s own formula, distinct from kpi_relationships'' causal claims. DEVELOPMENT_PLAN.md Phase 17 T2.';
COMMENT ON COLUMN kpi_decompositions.operation IS
    'linear: this child contributes sign * child_value to a signed sum producing the parent. ratio: child_kpi_id / weight_kpi_id = parent (weight_kpi_id required, exactly one ratio edge per parent).';
COMMENT ON COLUMN kpi_decompositions.sign IS
    'For operation=linear only: +1 if this child ADDS to the parent, -1 if it SUBTRACTS (using each KPI''s own already-sign-converted reported value). Ignored for ratio.';
COMMENT ON COLUMN kpi_decompositions.weight_kpi_id IS
    'Required when operation=ratio: the denominator KPI id (e.g. gross_margin_pct''s edge names net_revenue here).';

-- ---------------------------------------------------------------------------
-- RLS (Infra B3 -- mandatory for any new client_id table)
-- ---------------------------------------------------------------------------

GRANT SELECT ON kpi_decompositions TO a9_tenant_scope;
ALTER TABLE kpi_decompositions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON kpi_decompositions;
CREATE POLICY client_isolation ON kpi_decompositions FOR SELECT TO a9_tenant_scope
    USING (client_id = current_setting('app.client_id', true));

-- Remember: also add 'kpi_decompositions' to _RLS_TABLES in
-- scripts/verify_prod_registry.py (done in this same change).
