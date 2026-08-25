-- Phase 20 (Decision Framer/Decision Maker split): sf_pending_decisions
--
-- Nothing in this codebase persisted "awaiting a decision" before this.
-- SolutionFinderResponse.human_action_required was set on completion
-- (a9_solution_finder_agent.py) but only ever lived in workflows.py's
-- in-memory _workflow_store, keyed by request_id -- no endpoint listed it
-- by principal. This table is that durable record.
--
-- Design note: summary (the recommended option's title) is deliberately
-- denormalized onto this row rather than requiring a join back to the
-- workflow record -- the Decision Maker landing view renders its queue
-- from one query, per docs/architecture/decision_framer_and_decision_maker_personas_design.md.

CREATE TABLE IF NOT EXISTS sf_pending_decisions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id            TEXT NOT NULL,
    client_id             TEXT NOT NULL,
    principal_id          TEXT NOT NULL,
    situation_id          TEXT,
    kpi_id                TEXT,
    human_action_type     TEXT,
    summary               TEXT,
    human_action_context  JSONB,
    resolved              BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_action       TEXT,
    resolved_at           TIMESTAMPTZ,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_sf_pending_decisions_request_id
    ON sf_pending_decisions (request_id);

CREATE INDEX IF NOT EXISTS idx_sf_pending_decisions_principal_unresolved
    ON sf_pending_decisions (principal_id, client_id, resolved)
    WHERE resolved = FALSE;

COMMENT ON TABLE sf_pending_decisions IS
    'Durable record of a completed Solution Finder run awaiting a decision-maker sign-off (human_action_required=True). Written by PendingDecisionsStore from src/api/routes/workflows.py on SF completion; resolved when the approve/request-changes/iterate action fires.';
COMMENT ON COLUMN sf_pending_decisions.request_id IS
    'Links back to the SF workflow record (workflows.py _workflow_store key). Unique -- a re-run of the same request_id replaces via upsert, never duplicates.';
COMMENT ON COLUMN sf_pending_decisions.summary IS
    'Denormalized: the recommended option''s title at completion time, so the landing view queue renders from a single query with no join back to the workflow record.';
COMMENT ON COLUMN sf_pending_decisions.resolved IS
    'FALSE until the principal takes an action (approve/request-changes/iterate) on this request_id. The landing view queries WHERE resolved = FALSE.';

-- ---------------------------------------------------------------------------
-- RLS (Infra B3 -- mandatory for any new client_id table)
-- ---------------------------------------------------------------------------

GRANT SELECT ON sf_pending_decisions TO a9_tenant_scope;
ALTER TABLE sf_pending_decisions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON sf_pending_decisions;
CREATE POLICY client_isolation ON sf_pending_decisions FOR SELECT TO a9_tenant_scope
    USING (client_id = current_setting('app.client_id', true));

-- Remember: also add 'sf_pending_decisions' to _RLS_TABLES in
-- scripts/verify_prod_registry.py (done in this same change).
