-- Phase 9C: Situation State Model
-- Adds situation_actions table and extends assessment_runs with client scope + delta tracking.

-- ---------------------------------------------------------------------------
-- Extend assessment_runs
-- ---------------------------------------------------------------------------

ALTER TABLE assessment_runs
    ADD COLUMN IF NOT EXISTS client_id          TEXT,
    ADD COLUMN IF NOT EXISTS new_situation_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS previous_run_id    UUID REFERENCES assessment_runs(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_assessment_runs_client_id
    ON assessment_runs(client_id);

CREATE INDEX IF NOT EXISTS idx_assessment_runs_principal_client
    ON assessment_runs((config->>'principal_id'), client_id);

-- ---------------------------------------------------------------------------
-- situation_actions — records principal actions on detected situations
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS situation_actions (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    situation_id        TEXT        NOT NULL,           -- SA situation_id or kpi_name used as key
    kpi_assessment_id   UUID        REFERENCES kpi_assessments(id) ON DELETE SET NULL,
    run_id              UUID        NOT NULL REFERENCES assessment_runs(id) ON DELETE CASCADE,
    principal_id        TEXT        NOT NULL,
    action_type         TEXT        NOT NULL
                            CHECK (action_type IN ('snooze', 'delegate', 'request_info', 'acknowledge')),
    target_principal_id TEXT,                           -- populated for delegate actions
    snooze_expires_at   TIMESTAMPTZ,                    -- populated for snooze actions
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Snooze lookups by situation
CREATE INDEX IF NOT EXISTS idx_situation_actions_active_snooze
    ON situation_actions(situation_id, snooze_expires_at)
    WHERE action_type = 'snooze';

CREATE INDEX IF NOT EXISTS idx_situation_actions_situation_id
    ON situation_actions(situation_id);

CREATE INDEX IF NOT EXISTS idx_situation_actions_principal_id
    ON situation_actions(principal_id);

CREATE INDEX IF NOT EXISTS idx_situation_actions_action_type
    ON situation_actions(action_type);

CREATE INDEX IF NOT EXISTS idx_situation_actions_run_id
    ON situation_actions(run_id);
