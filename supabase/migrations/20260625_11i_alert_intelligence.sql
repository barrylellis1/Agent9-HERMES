-- Phase 11I-A: Advanced Alert Intelligence
-- Add plan_version_value and kpi_type to kpis table

ALTER TABLE kpis
  ADD COLUMN IF NOT EXISTS plan_version_value TEXT,
  ADD COLUMN IF NOT EXISTS kpi_type VARCHAR(32) NOT NULL DEFAULT 'operational';

COMMENT ON COLUMN kpis.plan_version_value IS 'Version filter value for plan/budget SQL (e.g. ''Budget'', ''Plan''). NULL = skip plan variance detection.';
COMMENT ON COLUMN kpis.kpi_type IS 'KPI classification: operational | concentration | covenant | regulatory';
