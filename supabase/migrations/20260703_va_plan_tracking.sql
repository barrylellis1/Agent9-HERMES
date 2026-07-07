-- Phase 11I-C: VA plan/budget trajectory tracking
-- Captures the KPI's budget/plan value at solution approval and the vs-plan
-- verdict computed at evaluation time (mirrors SA's 11I-A plan_variance pattern
-- but as a fourth VA trajectory rather than a detection alert).

ALTER TABLE value_assurance_solutions
  ADD COLUMN IF NOT EXISTS plan_value_at_approval NUMERIC;

ALTER TABLE value_assurance_evaluations
  ADD COLUMN IF NOT EXISTS vs_plan_verdict TEXT
    CHECK (vs_plan_verdict IN ('ahead_of_plan', 'on_plan', 'behind_plan', 'no_plan_data')),
  ADD COLUMN IF NOT EXISTS vs_plan_pct NUMERIC;
