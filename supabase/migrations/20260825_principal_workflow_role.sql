-- Phase 20 (Decision Framer / Decision Maker split): workflow_role
-- Date: 2026-08-25
-- Purpose: First-class workflow-stage axis on principal_profiles, replacing
--          the "everyone runs the identical pipeline" default. Mirrors the
--          20260604_principal_template_status.sql pattern exactly (add
--          column with a safe default + CHECK constraint + supporting index).
--
-- Scope decisions (from docs/architecture/decision_framer_and_decision_maker_personas_design.md):
--   - Two values only: 'framer' (stewards SA->DA->SF, runs refinement/reframing)
--     and 'decision_maker' (consumes a distilled brief, approves). Default
--     'framer' keeps every existing principal's behavior unchanged --
--     additive, non-breaking.
--   - This is a WORKFLOW-STAGE axis, never a content axis: it controls
--     default landing view and briefing disclosure depth, never which
--     option a Solution Finder run recommends (see PrincipalProfile's own
--     M1 comment a few lines above where this field lives).
--   - No RLS trio needed here -- principal_profiles is already a tenant
--     table under 20260713_rls_client_isolation.sql; this is a column add
--     on an existing, already-RLS-enabled table, not a new table.
--
-- ============================================================
-- 1. Add workflow_role column with backwards-compatible default
-- ============================================================
ALTER TABLE public.principal_profiles
    ADD COLUMN IF NOT EXISTS workflow_role TEXT NOT NULL DEFAULT 'framer';

-- Constrain valid values
ALTER TABLE public.principal_profiles
    DROP CONSTRAINT IF EXISTS principal_profiles_workflow_role_check;

ALTER TABLE public.principal_profiles
    ADD CONSTRAINT principal_profiles_workflow_role_check
    CHECK (workflow_role IN ('framer', 'decision_maker'));

-- ============================================================
-- 2. Index for downstream filters (default-view routing, briefing disclosure)
-- ============================================================
CREATE INDEX IF NOT EXISTS principal_profiles_client_workflow_role_idx
    ON public.principal_profiles (client_id, workflow_role);

-- ============================================================
-- 3. Column documentation
-- ============================================================
COMMENT ON COLUMN public.principal_profiles.workflow_role IS
    'Workflow-stage axis, not a content axis: sets the DEFAULT landing view (framer = situations dashboard, decision_maker = pending-decisions queue) and Executive Briefing disclosure depth. Never gates which option a Solution Finder run recommends, and never a permission -- every principal can always reach the full pipeline via the escape-hatch toggle.';
