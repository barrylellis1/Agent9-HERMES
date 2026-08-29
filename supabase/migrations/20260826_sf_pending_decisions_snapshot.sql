-- Phase 20 (Decision Framer/Decision Maker split) follow-up: briefing_snapshot
--
-- User-caught, live: clicking a pending decision in the Decision Maker
-- landing view re-ran Deep Analysis for real (against BigQuery) instead of
-- showing what was already produced. The pending-decisions queue must be a
-- snapshot of the completed recommendation, the same way
-- value_assurance_solutions.briefing_snapshot captures it AFTER approval
-- for Portfolio replay (VASolutionsStore.store_briefing_snapshot /
-- get_briefing_snapshot, src/api/routes/value_assurance.py's
-- PUT/GET /solutions/{id}/briefing) -- this mirrors that exact pattern for
-- the PRE-approval case, so a Decision Maker reviews the actual completed
-- analysis, never triggers new agent work.

ALTER TABLE sf_pending_decisions
    ADD COLUMN IF NOT EXISTS briefing_snapshot JSONB;

COMMENT ON COLUMN sf_pending_decisions.briefing_snapshot IS
    'The fully-transformed Executive Briefing payload (buildExecutiveBriefing output, not the raw SF response) at the moment synthesis completed. Written client-side by CouncilDebatePage.tsx right after it computes the same payload for its own localStorage cache -- same data, same shape, just also persisted so a Decision Maker can review it without re-running DA/SF, and so it survives beyond one browser session.';
