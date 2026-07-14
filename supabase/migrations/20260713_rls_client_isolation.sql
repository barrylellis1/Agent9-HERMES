-- Infra B3: Database-level multi-tenant isolation (Row-Level Security)
--
-- Design note (why this differs from the original sketch):
-- The application's asyncpg pool connects as the `postgres` role, which has
-- BYPASSRLS in Supabase (local and hosted). Plain `ENABLE ROW LEVEL SECURITY`
-- would therefore be silently bypassed by every app query. Instead we create a
-- dedicated NOLOGIN role `a9_tenant_scope` (no BYPASSRLS, not table owner) and
-- the app switches to it per-transaction for tenant-scoped reads:
--
--     BEGIN;
--     SET LOCAL ROLE a9_tenant_scope;
--     SELECT set_config('app.client_id', $client_id, true);
--     SELECT ...;            -- RLS enforced: only $client_id rows visible
--     COMMIT;                -- role + GUC reset automatically
--
-- The policy is fail-closed: if app.client_id is not set, current_setting()
-- returns NULL and the policy matches zero rows. Bootstrap, admin paths, and
-- seeding scripts continue to run as postgres/service_role (RLS-exempt).
--
-- Tables WITHOUT a client_id column (situations, kpi_assessments,
-- situation_actions, value_assurance_evaluations, briefing_tokens) are not
-- covered here — their isolation is indirect via parent records. Tracked as
-- a known gap in DEVELOPMENT_PLAN.md (Infra B3 follow-up).

-- 1. Tenant-scoped role (idempotent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'a9_tenant_scope') THEN
        CREATE ROLE a9_tenant_scope NOLOGIN;
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO a9_tenant_scope;
-- The app's pool role must be able to SET ROLE to the tenant role
GRANT a9_tenant_scope TO postgres;

-- 2. RLS on every table with a client_id column
DO $$
DECLARE
    t text;
    tenant_tables text[] := ARRAY[
        'kpis',
        'principal_profiles',
        'data_products',
        'business_processes',
        'business_glossary_terms',
        'value_assurance_solutions',
        'kpi_accountability',
        'kpi_relationships',
        'connection_profiles',
        'briefing_runs',
        'assessment_runs'
    ];
BEGIN
    FOREACH t IN ARRAY tenant_tables LOOP
        EXECUTE format('GRANT SELECT ON %I TO a9_tenant_scope', t);
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        EXECUTE format('DROP POLICY IF EXISTS client_isolation ON %I', t);
        EXECUTE format(
            'CREATE POLICY client_isolation ON %I FOR SELECT TO a9_tenant_scope
             USING (client_id = current_setting(''app.client_id'', true))', t);
    END LOOP;
END
$$;

-- 3. business_contexts: the row id IS the client anchor (no client_id column)
GRANT SELECT ON business_contexts TO a9_tenant_scope;
ALTER TABLE business_contexts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON business_contexts;
CREATE POLICY client_isolation ON business_contexts FOR SELECT TO a9_tenant_scope
    USING (id = current_setting('app.client_id', true));
