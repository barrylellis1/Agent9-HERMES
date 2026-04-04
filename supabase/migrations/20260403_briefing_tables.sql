-- Phase 9D: Principal Intelligence Briefing (PIB) tables
-- briefing_runs: one row per PIB email sent
-- briefing_tokens: secure one-click action + deep link tokens

-- ---------------------------------------------------------------------------
-- briefing_runs
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS briefing_runs (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id            TEXT        NOT NULL,
    client_id               TEXT        NOT NULL,
    assessment_run_id       UUID        REFERENCES assessment_runs(id) ON DELETE SET NULL,
    sent_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    new_situation_count     INTEGER     NOT NULL DEFAULT 0,
    format                  TEXT        NOT NULL DEFAULT 'detailed'
                                CHECK (format IN ('detailed', 'digest')),
    email_to                TEXT        NOT NULL,
    status                  TEXT        NOT NULL DEFAULT 'pending'
                                CHECK (status IN ('pending', 'sent', 'failed')),
    error_message           TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_briefing_runs_principal_id
    ON briefing_runs(principal_id);

CREATE INDEX IF NOT EXISTS idx_briefing_runs_principal_client
    ON briefing_runs(principal_id, client_id);

CREATE INDEX IF NOT EXISTS idx_briefing_runs_sent_at
    ON briefing_runs(sent_at DESC);

-- ---------------------------------------------------------------------------
-- briefing_tokens
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS briefing_tokens (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    token               UUID        UNIQUE NOT NULL DEFAULT gen_random_uuid(),
    token_type          TEXT        NOT NULL
                            CHECK (token_type IN ('deep_link', 'snooze', 'delegate', 'request_info', 'approve')),
    principal_id        TEXT        NOT NULL,
    situation_id        TEXT        NOT NULL,
    kpi_assessment_id   UUID        REFERENCES kpi_assessments(id) ON DELETE SET NULL,
    briefing_run_id     UUID        REFERENCES briefing_runs(id) ON DELETE CASCADE,
    expires_at          TIMESTAMPTZ NOT NULL,
    used_at             TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_briefing_tokens_token
    ON briefing_tokens(token);

CREATE INDEX IF NOT EXISTS idx_briefing_tokens_principal_id
    ON briefing_tokens(principal_id);

CREATE INDEX IF NOT EXISTS idx_briefing_tokens_situation_id
    ON briefing_tokens(situation_id);

CREATE INDEX IF NOT EXISTS idx_briefing_tokens_expires_at
    ON briefing_tokens(expires_at);
