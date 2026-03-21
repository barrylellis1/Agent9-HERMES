-- =============================================================================
-- Value Assurance Agent — Phase 7C trajectory tracking + benchmark segments
-- Adds three-trajectory model columns (inaction / expected / actual) and
-- structured benchmark segment storage to value_assurance_solutions.
-- Drops da_is_not_dimensions (replaced by control_group_segments /
-- benchmark_segments which carry full BenchmarkSegment objects).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- Three-trajectory model columns
-- inaction_trend    — projected values if no action had been taken
-- expected_trend    — model-predicted values given the approved solution
-- actual_trend      — observed KPI values as they are collected over time
-- actual_trend_dates— ISO-8601 date strings paired 1:1 with actual_trend
-- ---------------------------------------------------------------------------
ALTER TABLE value_assurance_solutions ADD COLUMN IF NOT EXISTS inaction_trend        JSONB;
ALTER TABLE value_assurance_solutions ADD COLUMN IF NOT EXISTS expected_trend        JSONB;
ALTER TABLE value_assurance_solutions ADD COLUMN IF NOT EXISTS actual_trend          JSONB    DEFAULT '[]'::jsonb;
ALTER TABLE value_assurance_solutions ADD COLUMN IF NOT EXISTS actual_trend_dates    JSONB    DEFAULT '[]'::jsonb;

-- ---------------------------------------------------------------------------
-- Pre-approval KPI state — anchors all trajectory calculations
-- baseline_kpi_value    — KPI value at the moment the solution was approved
-- pre_approval_slope    — linear trend slope (units/day) over look-back window
-- inaction_horizon_months — how far into the future the inaction projection runs
-- ---------------------------------------------------------------------------
ALTER TABLE value_assurance_solutions ADD COLUMN IF NOT EXISTS baseline_kpi_value       FLOAT;
ALTER TABLE value_assurance_solutions ADD COLUMN IF NOT EXISTS pre_approval_slope        FLOAT;
ALTER TABLE value_assurance_solutions ADD COLUMN IF NOT EXISTS inaction_horizon_months   INTEGER;

-- ---------------------------------------------------------------------------
-- Structured segment storage (replaces flat da_is_not_dimensions list)
-- control_group_segments — List[BenchmarkSegment] used for DiD control group
-- benchmark_segments     — List[BenchmarkSegment] identified as replication targets
-- ---------------------------------------------------------------------------
ALTER TABLE value_assurance_solutions ADD COLUMN IF NOT EXISTS control_group_segments    JSONB;
ALTER TABLE value_assurance_solutions ADD COLUMN IF NOT EXISTS benchmark_segments        JSONB;

-- ---------------------------------------------------------------------------
-- Drop superseded column
-- da_is_not_dimensions was a flat List[str]; control_group_segments replaces it
-- ---------------------------------------------------------------------------
ALTER TABLE value_assurance_solutions DROP COLUMN IF EXISTS da_is_not_dimensions;
