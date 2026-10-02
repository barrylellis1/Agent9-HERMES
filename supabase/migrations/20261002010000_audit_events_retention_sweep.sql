-- audit_events retention sweep (design note: docs/architecture/audit_event_system_design.md
-- section 4, retention table, resolved 2026-10-02). Follow-up to
-- 20261002000000_audit_events.sql, which created the table and deliberately left this
-- for its own migration.
--
-- WHAT GETS SWEPT, AND WHAT DOESN'T. Only outcome IN ('pass', 'abstain') rows older than
-- the cutoff (90 days, the design note's resolved number) are summarized and deleted.
-- outcome = 'fail' rows are NEVER swept by this function -- they keep Infra C1's 2-year
-- SOC 2 horizon with no scheduled deletion, per the design note's own retention table
-- (a `fail` is a rare incident record, not routine volume). outcome IS NULL rows (SF's
-- narrative/debug events, which aren't checks) are also never touched here -- out of
-- scope for this resolution, same as the design note states.
--
-- WHY fail HAS NO ROLLUP TABLE ENTRY. pass/abstain rows are deleted, so their only
-- surviving record of "this happened" is the rollup row this function writes before
-- deleting them. fail rows are never deleted, so they remain directly queryable from
-- audit_events itself forever -- a second, parallel fail_count bookkeeping column here
-- would just be a cache that could drift from the source of truth it is meant to
-- summarize, for no benefit this design currently needs.
--
-- SAFE TO RE-RUN. The upsert accumulates onto any existing rollup row for the same
-- (client_id, event_type, day) rather than overwriting it, so calling this twice (a
-- retried admin trigger, an overlapping scheduled run) adds counts rather than losing
-- or double-counting a day that was already partly swept. created_at is fixed at insert
-- time, so a row can never retroactively become old enough to match a prior sweep's
-- cutoff after the fact -- the two statements inside the function see a stable set.
--
-- WHO CALLS THIS -- deliberately open as of this migration. There is no pg_cron
-- extension enabled on this Supabase project today, and no existing scheduled-job
-- mechanism anywhere in this codebase (no Railway cron, no app-level scheduler) to
-- hang an automatic trigger on. This migration ships the sweep LOGIC and a manual
-- admin-triggered call path (POST /api/v1/admin/audit-events/sweep); wiring it to run
-- unattended on a schedule is a separate, deliberate infrastructure decision --
-- enabling pg_cron, a Railway cron job, or an external scheduler hitting the admin
-- endpoint are all live options, not decided here.

CREATE TABLE IF NOT EXISTS audit_events_daily_rollup (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id     TEXT NOT NULL,
    event_type    TEXT NOT NULL,
    day           DATE NOT NULL,
    pass_count    INTEGER NOT NULL DEFAULT 0,
    abstain_count INTEGER NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT audit_events_daily_rollup_pk UNIQUE (client_id, event_type, day)
);

CREATE INDEX IF NOT EXISTS idx_audit_events_daily_rollup_client_type
    ON audit_events_daily_rollup (client_id, event_type, day DESC);

COMMENT ON TABLE audit_events_daily_rollup IS
    'Permanent per-day pass/abstain counts for audit_events rows the retention sweep has deleted. No fail_count column -- fail rows are never swept, so they stay directly queryable from audit_events itself. docs/architecture/audit_event_system_design.md.';

GRANT SELECT ON audit_events_daily_rollup TO a9_tenant_scope;
ALTER TABLE audit_events_daily_rollup ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON audit_events_daily_rollup;
CREATE POLICY client_isolation ON audit_events_daily_rollup FOR SELECT TO a9_tenant_scope
    USING (client_id = current_setting('app.client_id', true));

-- Remember: also add 'audit_events_daily_rollup' to _RLS_TABLES in
-- scripts/verify_prod_registry.py (done in this same change).

CREATE OR REPLACE FUNCTION sweep_audit_events_retention(cutoff_days INTEGER DEFAULT 90)
RETURNS TABLE(rolled_up_groups INTEGER, rows_deleted INTEGER) AS $$
DECLARE
    _cutoff TIMESTAMPTZ := NOW() - (cutoff_days || ' days')::INTERVAL;
    _groups INTEGER;
    _deleted INTEGER;
BEGIN
    WITH to_sweep AS (
        SELECT client_id, event_type, (created_at AT TIME ZONE 'UTC')::date AS day, outcome
        FROM audit_events
        WHERE outcome IN ('pass', 'abstain') AND created_at < _cutoff
    ),
    grouped AS (
        SELECT client_id, event_type, day,
               COUNT(*) FILTER (WHERE outcome = 'pass')    AS pass_count,
               COUNT(*) FILTER (WHERE outcome = 'abstain') AS abstain_count
        FROM to_sweep
        GROUP BY client_id, event_type, day
    ),
    upserted AS (
        INSERT INTO audit_events_daily_rollup (client_id, event_type, day, pass_count, abstain_count)
        SELECT client_id, event_type, day, pass_count, abstain_count FROM grouped
        ON CONFLICT (client_id, event_type, day) DO UPDATE SET
            pass_count    = audit_events_daily_rollup.pass_count + EXCLUDED.pass_count,
            abstain_count = audit_events_daily_rollup.abstain_count + EXCLUDED.abstain_count,
            updated_at    = NOW()
        RETURNING 1
    )
    SELECT COUNT(*) INTO _groups FROM upserted;

    DELETE FROM audit_events
    WHERE outcome IN ('pass', 'abstain') AND created_at < _cutoff;
    GET DIAGNOSTICS _deleted = ROW_COUNT;

    RETURN QUERY SELECT COALESCE(_groups, 0), COALESCE(_deleted, 0);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION sweep_audit_events_retention IS
    'Rolls up and deletes audit_events rows with outcome pass/abstain older than cutoff_days (default 90). fail and NULL-outcome rows are never touched. Safe to re-run -- see this migration''s own header comment.';
