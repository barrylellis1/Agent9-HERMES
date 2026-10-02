-- Schedules the audit_events retention sweep (supabase/migrations/
-- 20261002010000_audit_events_retention_sweep.sql) to run weekly, resolving
-- the open question that migration explicitly left: there was no `pg_cron`
-- extension enabled on this project, and no other scheduled-job mechanism
-- anywhere in this codebase (no Railway cron, no app-level scheduler).
--
-- WHY pg_cron OVER THE ALTERNATIVES (Railway cron hitting the admin
-- endpoint, or an external scheduler doing the same). This runs inside
-- Postgres itself: no dependency on the app server being up, no need to
-- expose or rotate an admin key for an automated caller, and it keeps
-- scheduling logic co-located with the function and the data it acts on --
-- consistent with Supabase already being the sole backend everywhere else
-- in this codebase (root CLAUDE.md). The manual trigger, POST
-- /api/v1/admin/audit-events/sweep, is untouched and still useful for an
-- ad hoc run or a cutoff_days other than the default 90.
--
-- WHY WEEKLY. The cutoff is 90 days; a row crossing that threshold sits for
-- at most a few extra days before the next scheduled sweep picks it up --
-- immaterial at current volume (hundreds to low thousands of rows/day per
-- the design note), and not worth a tighter schedule for a maintenance task
-- that is not latency-sensitive.
--
-- Sunday 03:00 UTC -- an arbitrary but conventional low-traffic maintenance
-- window; change the schedule string below if a different time is wanted.
-- Standard cron syntax: minute hour day-of-month month day-of-week.
--
-- IDEMPOTENT: unschedules any prior job of the same name before
-- (re-)scheduling, so re-running this migration (or a future migration that
-- changes the schedule) does not collide with an already-registered job.

CREATE EXTENSION IF NOT EXISTS pg_cron;

DO $$
BEGIN
    PERFORM cron.unschedule('audit-events-retention-sweep');
EXCEPTION WHEN OTHERS THEN
    -- No prior job with this name -- nothing to unschedule, not an error.
    NULL;
END
$$;

SELECT cron.schedule(
    'audit-events-retention-sweep',
    '0 3 * * 0',  -- weekly, Sunday 03:00 UTC
    $$SELECT sweep_audit_events_retention();$$
);

COMMENT ON EXTENSION pg_cron IS
    'Enables scheduled SQL jobs inside Postgres. First (and, as of this migration, only) user: the audit_events retention sweep. docs/architecture/audit_event_system_design.md.';
