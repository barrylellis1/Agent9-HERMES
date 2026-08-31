-- DEVELOPMENT_PLAN.md Phase 17, T4: external-world port model.
-- docs/architecture/theory_layer_design.md §2.3: external forces enter a
-- business through a small enumerable set of ports -- input costs, demand
-- volume, price realization, capital cost, talent supply, regulatory
-- constraint -- each with a characteristic lag and buffer.
--
-- This is the model gap the design doc names explicitly for the Lubricants
-- anchor scenario (Base Oil rising while COGS declines): "The genuinely
-- causal base-oil-price story... has no KPI to attach to yet." Base oil
-- SPOT PRICE is not itself a registered KPI -- linked_kpi_id is the
-- INTERNAL side only (the KPI this port enters at); the external fact
-- lives in current_signal, in plain language.

CREATE TABLE IF NOT EXISTS ports (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           TEXT NOT NULL,
    name                TEXT NOT NULL,
    port_type           TEXT NOT NULL
        CHECK (port_type IN ('input_costs', 'demand_volume', 'price_realization',
                              'capital_cost', 'talent_supply', 'regulatory_constraint')),
    linked_kpi_id       TEXT NOT NULL,
    lag_periods         INTEGER,
    buffer_description  TEXT,
    current_signal      TEXT,
    source              TEXT NOT NULL DEFAULT 'manual'
        CHECK (source IN ('ma_query', 'manual')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ports_unique_per_kpi_type UNIQUE (client_id, linked_kpi_id, port_type)
);

CREATE INDEX IF NOT EXISTS idx_ports_client_kpi ON ports (client_id, linked_kpi_id);

COMMENT ON TABLE ports IS
    'External-world entry points (theory_layer_design.md §2.3) -- input costs, demand volume, price realization, capital cost, talent supply, regulatory constraint -- each with a lag and buffer. DEVELOPMENT_PLAN.md Phase 17 T4.';
COMMENT ON COLUMN ports.linked_kpi_id IS
    'The INTERNAL KPI this external force enters at (e.g. base_oil_cost) -- not the external field itself, which is not a registered KPI.';
COMMENT ON COLUMN ports.lag_periods IS
    'Months between the external move and the linked KPI''s own move.';
COMMENT ON COLUMN ports.buffer_description IS
    'What absorbs the shock before it reaches the ledger -- inventory layers, hedges, contracts, backlog.';
COMMENT ON COLUMN ports.current_signal IS
    'The actual observed external-world fact, in plain language. Human/LLM-authored today (source=manual); a live MA-agent write path (source=ma_query) is a follow-up, not built.';

-- ---------------------------------------------------------------------------
-- RLS (Infra B3 -- mandatory for any new client_id table)
-- ---------------------------------------------------------------------------

GRANT SELECT ON ports TO a9_tenant_scope;
ALTER TABLE ports ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON ports;
CREATE POLICY client_isolation ON ports FOR SELECT TO a9_tenant_scope
    USING (client_id = current_setting('app.client_id', true));

-- Remember: also add 'ports' to _RLS_TABLES in scripts/verify_prod_registry.py
-- (done in this same change).
