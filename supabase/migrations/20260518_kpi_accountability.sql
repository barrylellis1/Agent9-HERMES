-- Phase 11A: KPI Accountability Registry
-- Tracks which principals are accountable or responsible for each KPI,
-- optionally scoped to a dimension (e.g. "Region = APAC").

CREATE TABLE IF NOT EXISTS public.kpi_accountability (
    id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    kpi_id TEXT NOT NULL,
    principal_id TEXT NOT NULL,
    scope_dimension TEXT,         -- null = enterprise-wide
    scope_value TEXT,             -- null = all values in this dimension
    role TEXT NOT NULL DEFAULT 'accountable',  -- 'accountable' | 'responsible'
    notes TEXT,
    created_by TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_kpi_accountability PRIMARY KEY (client_id, id),
    -- Max 1 accountable principal per (kpi_id, scope_dimension, scope_value)
    CONSTRAINT uq_kpi_accountability_scope UNIQUE (client_id, kpi_id, scope_dimension, scope_value)
);

CREATE INDEX IF NOT EXISTS idx_kpi_accountability_client ON public.kpi_accountability (client_id);
CREATE INDEX IF NOT EXISTS idx_kpi_accountability_principal ON public.kpi_accountability (client_id, principal_id);
CREATE INDEX IF NOT EXISTS idx_kpi_accountability_kpi ON public.kpi_accountability (client_id, kpi_id);
