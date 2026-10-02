-- Audit events — persisted diagnostics for monitoring, error review, and the
-- stage-wise reliability panel. Design: docs/architecture/audit_event_system_design.md
--
-- Three event families share this one table, distinguished by event_type prefix
-- and by their write path's call site, never by a schema difference:
--   - SF narrative/debug events (pilot scope, section 4 of the design note):
--     'heuristic_stub_fallback', 'llm_debate_completed', 'token_usage', ...
--     These carry no outcome (NULL) — they are not checks, they have no verdict.
--   - Infra C's access/action trail (SOC 2): 'auth.login', 'solution.approved',
--     'registry.record_deleted', ... — outcome 'pass'/'fail' maps 1:1 from the
--     prior success/failure draft (section 4's schema-note on reconciliation).
--   - The stage-wise reliability panel (2026-10-02 scope extension): SA
--     detection confidence, DA's [ROLLUP-CHECK], check_tree_reconciles,
--     check_slice_validity, KPI coverage — each a check with a real verdict.
--
-- severity and outcome are independent axes (design note section 4): a `fail`
-- can be low-severity (DA's ROLLUP-CHECK overshoot logs as 'warning', non-fatal
-- by design — "a bad decomposition must not take down a good analysis"), and
-- an `abstain` can be entirely routine. Collapsing them into one column would
-- lose exactly the distinction src/analysis's True/False/None convention exists
-- to preserve.
--
-- Retention (design note section 4, resolved 2026-10-02, revised same day after
-- wiring a second signal) is tiered by outcome, not by event_type: 'pass' AND
-- 'abstain' rows get a 90-day scheduled sweep after being rolled into an
-- aggregate (the sweep job is a follow-up migration, not this one — this
-- migration only creates the table the sweep will read). Only 'fail' rows get
-- Infra C1's 2-year SOC 2 horizon with no scheduled delete — 'abstain' was
-- moved out of that bucket once SA's confidence-floor signal showed abstain
-- can be the COMMON case for a borderline KPI, not a rare incident the way a
-- ROLLUP-CHECK overshoot is.

CREATE TABLE IF NOT EXISTS audit_events (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id    TEXT NOT NULL,
    event_type   TEXT NOT NULL,
    severity     TEXT NOT NULL
        CHECK (severity IN ('info', 'warning', 'error')),
    outcome      TEXT
        CHECK (outcome IN ('pass', 'fail', 'abstain')),
    source_agent TEXT NOT NULL,
    request_id   TEXT,
    resource_type TEXT,
    resource_id   TEXT,
    payload      JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_events_client_type_created
    ON audit_events (client_id, event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_events_outcome_created
    ON audit_events (outcome, created_at)
    WHERE outcome IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_audit_events_resource
    ON audit_events (client_id, resource_type, resource_id)
    WHERE resource_type IS NOT NULL;

COMMENT ON TABLE audit_events IS
    'Shared sink for three event families (SF pilot narrative events, Infra C SOC 2 access/action trail, the stage-wise reliability panel) — distinguished by event_type prefix, not by schema. docs/architecture/audit_event_system_design.md.';
COMMENT ON COLUMN audit_events.severity IS
    'How urgent this is to a human reader: info | warning | error. Independent of outcome — a fail can be warning-severity when non-fatal by design.';
COMMENT ON COLUMN audit_events.outcome IS
    'What a check concluded: pass | fail | abstain | NULL. NULL means this event_type is not a check (no verdict to render) — e.g. SF''s narrative events. Mirrors src/analysis''s True/False/None convention: abstain/NULL is excluded from both numerator and denominator wherever this is aggregated, never treated as pass.';
COMMENT ON COLUMN audit_events.resource_type IS
    'What the event is about, e.g. ''kpi'', ''dimension'', ''decomposition_edge''. Nullable — not every event concerns one addressable resource.';

-- ---------------------------------------------------------------------------
-- RLS (Infra B3 -- mandatory for any new client_id table)
-- ---------------------------------------------------------------------------

GRANT SELECT ON audit_events TO a9_tenant_scope;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON audit_events;
CREATE POLICY client_isolation ON audit_events FOR SELECT TO a9_tenant_scope
    USING (client_id = current_setting('app.client_id', true));

-- Remember: also add 'audit_events' to _RLS_TABLES in
-- scripts/verify_prod_registry.py (done in this same change).
