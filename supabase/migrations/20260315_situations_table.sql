-- Situations and Opportunities registry
-- Persists SA-detected cards so they survive restarts and can be
-- retrieved by downstream agents (DA, SF, VA).

CREATE TABLE IF NOT EXISTS situations (
    id                  TEXT PRIMARY KEY,        -- UUID from SA agent (situation_id / opportunity_id)
    card_type           TEXT NOT NULL            -- 'problem' | 'opportunity'
                            CHECK (card_type IN ('problem', 'opportunity')),
    kpi_id              TEXT NOT NULL,
    kpi_name            TEXT,
    principal_id        TEXT,
    severity            TEXT,                    -- critical / high / medium / low / information
    title               TEXT NOT NULL,
    description         TEXT,
    kpi_value           FLOAT,
    threshold           FLOAT,
    deviation_pct       FLOAT,
    opportunity_type    TEXT,                    -- outperformance / recovery / trend_reversal (NULL for problems)
    status              TEXT NOT NULL DEFAULT 'OPEN'
                            CHECK (status IN ('OPEN','ANALYZING','SOLUTION_APPROVED','RESOLVED','DISMISSED')),
    detected_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at         TIMESTAMPTZ,
    -- Downstream linkage (populated as pipeline progresses)
    da_request_id       TEXT,                    -- workflow request_id for the DA run
    solution_id         TEXT,                    -- VA solution_id after HITL approval
    -- Full payload for downstream retrieval
    full_payload        JSONB,                   -- complete Situation or OpportunitySignal as JSON
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_situations_kpi_id ON situations(kpi_id);
CREATE INDEX IF NOT EXISTS idx_situations_principal_id ON situations(principal_id);
CREATE INDEX IF NOT EXISTS idx_situations_status ON situations(status);
CREATE INDEX IF NOT EXISTS idx_situations_card_type ON situations(card_type);
CREATE INDEX IF NOT EXISTS idx_situations_detected_at ON situations(detected_at DESC);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_situations_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_situations_updated_at ON situations;
CREATE TRIGGER trg_situations_updated_at
    BEFORE UPDATE ON situations
    FOR EACH ROW EXECUTE FUNCTION update_situations_updated_at();
