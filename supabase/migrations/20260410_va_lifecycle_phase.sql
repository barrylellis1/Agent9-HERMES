-- Add lifecycle phase tracking to value_assurance_solutions
-- Phase is independent of verdict (status): phase tracks where in the lifecycle,
-- status tracks the evaluation result.

ALTER TABLE value_assurance_solutions
  ADD COLUMN IF NOT EXISTS phase TEXT DEFAULT 'APPROVED'
    CHECK (phase IN ('APPROVED','IMPLEMENTING','LIVE','MEASURING','COMPLETE')),
  ADD COLUMN IF NOT EXISTS go_live_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- Backfill existing solutions based on their verdict status
UPDATE value_assurance_solutions SET phase = 'COMPLETE' WHERE status IN ('VALIDATED','PARTIAL','FAILED');
UPDATE value_assurance_solutions SET phase = 'LIVE' WHERE status = 'MEASURING';
