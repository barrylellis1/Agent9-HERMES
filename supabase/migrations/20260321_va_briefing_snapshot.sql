-- Add briefing_snapshot JSONB column to value_assurance_solutions
ALTER TABLE value_assurance_solutions
ADD COLUMN IF NOT EXISTS briefing_snapshot JSONB;

COMMENT ON COLUMN value_assurance_solutions.briefing_snapshot IS 'Full Executive Briefing payload captured at approval time — enables replay without re-running agents';
