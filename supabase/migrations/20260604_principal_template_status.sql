-- Phase 12E: Principal Template Status
-- Date: 2026-06-04
-- Purpose: Add status lifecycle (template | active) to principal_profiles to
--          support the Company Intelligence-Driven Principal Template Generator.
--          Template principals are research artifacts pending email entry and
--          admin confirmation — never appear in login, SA, or PIB.
--
-- Scope decisions adopted (from DEVELOPMENT_PLAN.md Phase 12E):
--   - No decision_style or communication_style inference (Decision 1)
--   - email may be NULL at commit (Decision 2) — already nullable per
--     20260404_add_email_to_principals.sql, no change required here
--   - Research metadata (sources, confidence) stored in existing metadata JSONB
--
-- ============================================================
-- 1. Add status column with backwards-compatible default
-- ============================================================
ALTER TABLE public.principal_profiles
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active';

-- Constrain valid values
ALTER TABLE public.principal_profiles
    DROP CONSTRAINT IF EXISTS principal_profiles_status_check;

ALTER TABLE public.principal_profiles
    ADD CONSTRAINT principal_profiles_status_check
    CHECK (status IN ('template', 'active'));

-- ============================================================
-- 2. Index for downstream guard filters (login, PIB, SA all filter active)
-- ============================================================
CREATE INDEX IF NOT EXISTS principal_profiles_client_status_idx
    ON public.principal_profiles (client_id, status);

-- ============================================================
-- 3. Column documentation
-- ============================================================
COMMENT ON COLUMN public.principal_profiles.status IS
    'Principal lifecycle: ''template'' = research artifact pending email entry and admin confirmation (login/PIB/SA exclude); ''active'' = production-ready';
