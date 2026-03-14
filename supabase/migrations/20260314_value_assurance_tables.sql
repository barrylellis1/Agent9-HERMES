-- =============================================================================
-- Value Assurance Agent — Supabase persistence tables
-- Phase 7B migration (enable by setting supabase_enabled=True in agent config)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- value_assurance_solutions
-- One row per HITL-approved solution.
-- strategy_snapshot captures the strategic context at the moment of approval
-- so alignment drift can be computed later without relying on point-in-time
-- registry state.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS value_assurance_solutions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    situation_id            TEXT NOT NULL,
    kpi_id                  TEXT NOT NULL,
    principal_id            TEXT NOT NULL,
    approved_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    solution_description    TEXT NOT NULL,
    expected_impact_lower   FLOAT NOT NULL,
    expected_impact_upper   FLOAT NOT NULL,
    measurement_window_days INTEGER NOT NULL DEFAULT 30,
    status                  TEXT NOT NULL DEFAULT 'MEASURING'
                                CHECK (status IN ('MEASURING','VALIDATED','PARTIAL','FAILED')),
    -- JSONB blobs for complex nested types
    strategy_snapshot       JSONB,          -- StrategySnapshot at approval time
    da_is_not_dimensions    JSONB,          -- List[str] — control group source
    ma_market_signals       JSONB,          -- List[str] — market context at approval
    narrative               TEXT,           -- LLM-generated executive summary
    -- Audit
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- value_assurance_evaluations
-- One row per evaluation run.  A solution can be re-evaluated multiple times
-- (e.g. at 30 days, 60 days, 90 days); all runs are preserved for audit.
-- The latest evaluation determines the solution's current status.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS value_assurance_evaluations (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    solution_id                 UUID NOT NULL
                                    REFERENCES value_assurance_solutions(id)
                                    ON DELETE CASCADE,
    -- Raw KPI values
    baseline_kpi_value          FLOAT NOT NULL,
    current_kpi_value           FLOAT NOT NULL,
    -- Attribution breakdown (DiD)
    total_kpi_change            FLOAT NOT NULL,
    control_group_change        FLOAT NOT NULL DEFAULT 0,
    market_driven_recovery      FLOAT NOT NULL DEFAULT 0,
    seasonal_component          FLOAT NOT NULL DEFAULT 0,
    attributable_impact         FLOAT NOT NULL,
    expected_impact_lower       FLOAT NOT NULL,
    expected_impact_upper       FLOAT NOT NULL,
    -- Verdict
    verdict                     TEXT NOT NULL
                                    CHECK (verdict IN ('VALIDATED','PARTIAL','FAILED','MEASURING')),
    confidence                  TEXT NOT NULL
                                    CHECK (confidence IN ('HIGH','MODERATE','LOW')),
    confidence_rationale        TEXT,
    attribution_method          TEXT NOT NULL,
    control_group_description   TEXT,
    market_context_summary      TEXT,
    -- Strategy alignment and composite verdict as JSONB
    strategy_alignment          JSONB,      -- StrategyAlignmentCheck
    composite_verdict           JSONB,      -- CompositeVerdict
    include_in_roi              BOOLEAN NOT NULL DEFAULT FALSE,
    -- Timestamps
    evaluated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_va_solutions_kpi_id
    ON value_assurance_solutions(kpi_id);

CREATE INDEX IF NOT EXISTS idx_va_solutions_principal_id
    ON value_assurance_solutions(principal_id);

CREATE INDEX IF NOT EXISTS idx_va_solutions_status
    ON value_assurance_solutions(status);

CREATE INDEX IF NOT EXISTS idx_va_solutions_approved_at
    ON value_assurance_solutions(approved_at DESC);

CREATE INDEX IF NOT EXISTS idx_va_evaluations_solution_id
    ON value_assurance_evaluations(solution_id);

CREATE INDEX IF NOT EXISTS idx_va_evaluations_evaluated_at
    ON value_assurance_evaluations(evaluated_at DESC);

-- ---------------------------------------------------------------------------
-- updated_at trigger (auto-maintain on UPDATE)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_va_solutions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_va_solutions_updated_at ON value_assurance_solutions;
CREATE TRIGGER trg_va_solutions_updated_at
    BEFORE UPDATE ON value_assurance_solutions
    FOR EACH ROW EXECUTE FUNCTION update_va_solutions_updated_at();
