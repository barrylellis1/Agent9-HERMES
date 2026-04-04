-- =============================================================================
-- Enterprise Assessment Pipeline — Phase 9A
-- assessment_runs: one row per batch run
-- kpi_assessments: one row per KPI per run with SA severity + DA results
-- =============================================================================

-- ---------------------------------------------------------------------------
-- assessment_runs
-- One row per batch assessment execution.  Status progresses from 'running'
-- to 'complete' (or 'error' on failure).  Counter columns are updated
-- incrementally as each KPI is processed so progress can be polled in real
-- time without aggregating kpi_assessments.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS assessment_runs (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at            TIMESTAMPTZ,
    status                  TEXT NOT NULL DEFAULT 'running'
                                CHECK (status IN ('running', 'complete', 'error')),
    kpi_count               INTEGER NOT NULL DEFAULT 0,
    kpis_escalated          INTEGER NOT NULL DEFAULT 0,
    kpis_monitored          INTEGER NOT NULL DEFAULT 0,
    kpis_below_threshold    INTEGER NOT NULL DEFAULT 0,
    kpis_errored            INTEGER NOT NULL DEFAULT 0,
    config                  JSONB,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- kpi_assessments
-- One row per KPI per run.  Captures the raw SA signal (severity, confidence,
-- status) and the DA result when the KPI was escalated.  benchmark_segments
-- stores the IS/IS NOT dimensional breakdown as a JSONB array so it can be
-- queried without a separate table.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS kpi_assessments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id              UUID NOT NULL REFERENCES assessment_runs(id) ON DELETE CASCADE,
    kpi_id              TEXT NOT NULL,
    kpi_name            TEXT,
    kpi_value           FLOAT,
    comparison_value    FLOAT,
    severity            FLOAT,
    confidence          FLOAT,
    status              TEXT NOT NULL CHECK (status IN ('detected','monitoring','below_threshold','error')),
    escalated_to_da     BOOLEAN NOT NULL DEFAULT FALSE,
    da_result           JSONB,
    benchmark_segments  JSONB,
    error_message       TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_kpi_assessment_per_run UNIQUE (run_id, kpi_id)
);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_assessment_runs_status
    ON assessment_runs(status);

CREATE INDEX IF NOT EXISTS idx_assessment_runs_started_at
    ON assessment_runs(started_at DESC);

CREATE INDEX IF NOT EXISTS idx_kpi_assessments_run_id
    ON kpi_assessments(run_id);

CREATE INDEX IF NOT EXISTS idx_kpi_assessments_kpi_id
    ON kpi_assessments(kpi_id);

CREATE INDEX IF NOT EXISTS idx_kpi_assessments_status
    ON kpi_assessments(status);

CREATE INDEX IF NOT EXISTS idx_kpi_assessments_escalated
    ON kpi_assessments(escalated_to_da) WHERE escalated_to_da = TRUE;

-- ---------------------------------------------------------------------------
-- updated_at trigger (auto-maintain on UPDATE)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_assessment_runs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_assessment_runs_updated_at ON assessment_runs;
CREATE TRIGGER trg_assessment_runs_updated_at
    BEFORE UPDATE ON assessment_runs
    FOR EACH ROW EXECUTE FUNCTION update_assessment_runs_updated_at();
