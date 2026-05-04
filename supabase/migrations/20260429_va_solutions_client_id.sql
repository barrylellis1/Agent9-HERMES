-- Migration: add client_id to value_assurance_solutions for multi-tenant isolation
-- Date: 2026-04-29

ALTER TABLE value_assurance_solutions
    ADD COLUMN IF NOT EXISTS client_id TEXT;

-- Index for fast per-client portfolio queries
CREATE INDEX IF NOT EXISTS idx_va_solutions_client_id
    ON value_assurance_solutions (client_id);

-- Composite index for the common query pattern: solutions for a principal within a client
CREATE INDEX IF NOT EXISTS idx_va_solutions_principal_client
    ON value_assurance_solutions (principal_id, client_id);
