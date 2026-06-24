-- Phase 12A: KPI Template Status + Benchmark Columns
-- Date: 2026-06-02
-- Purpose: Add status lifecycle (template | active) and benchmark provenance
--          columns to support the Company Intelligence-Driven KPI Template
--          Generator. SA agent only evaluates status='active' KPIs; template
--          KPIs are research artifacts pending data connection.
--
-- Pre-mortem mitigations addressed:
--   M1 (benchmark trust): benchmark_source records provenance for every range.
--   M2 (dead KPI registry): status='template' isolated from SA evaluation.
--
-- ============================================================
-- 1. Add status column with backwards-compatible default
-- ============================================================
ALTER TABLE public.kpis
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';

-- Constrain valid values
ALTER TABLE public.kpis
    DROP CONSTRAINT IF EXISTS kpis_status_check;

ALTER TABLE public.kpis
    ADD CONSTRAINT kpis_status_check
    CHECK (status IN ('template', 'active'));

-- ============================================================
-- 2. Add benchmark columns
-- ============================================================
ALTER TABLE public.kpis
    ADD COLUMN IF NOT EXISTS benchmark_range TEXT;

ALTER TABLE public.kpis
    ADD COLUMN IF NOT EXISTS benchmark_source TEXT;

-- Constrain benchmark_source values (nullable when no benchmark provided)
ALTER TABLE public.kpis
    DROP CONSTRAINT IF EXISTS kpis_benchmark_source_check;

ALTER TABLE public.kpis
    ADD CONSTRAINT kpis_benchmark_source_check
    CHECK (benchmark_source IS NULL OR benchmark_source IN ('filing', 'peer', 'inferred'));

-- ============================================================
-- 3. Index for SA guard filter (only active KPIs reach detection)
-- ============================================================
CREATE INDEX IF NOT EXISTS kpis_client_status_idx
    ON public.kpis (client_id, status);

-- ============================================================
-- 4. Column documentation
-- ============================================================
COMMENT ON COLUMN public.kpis.status IS
    'KPI lifecycle: ''template'' = research artifact pending data connection, ''active'' = monitored by SA';
COMMENT ON COLUMN public.kpis.benchmark_range IS
    'Display-friendly industry benchmark range (e.g. "12-18%") populated by Phase 12A template generator';
COMMENT ON COLUMN public.kpis.benchmark_source IS
    'Provenance of benchmark_range: ''filing'' = company-reported, ''peer'' = industry peer report, ''inferred'' = LLM-derived';
