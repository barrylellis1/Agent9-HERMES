-- Prevent duplicate solution rows for the same KPI breach.
-- One active solution per (kpi_id, situation_id) pair.
-- Re-approving the same situation upserts the existing row rather than inserting a new one.
-- Genuinely new breaches produce distinct situation_ids, so they still get their own rows.

-- Wipe all existing rows. Pre-migration rows have UUID-format IDs; post-migration rows
-- use deterministic sha256 IDs derived from (kpi_id, situation_id). If any UUID-ID row
-- survived, a new sha256-ID approval for the same (kpi_id, situation_id) pair would hit
-- the unique constraint and fail. Clean slate avoids that conflict entirely.
-- Re-seed demo data after deployment via: python scripts/seed_va_demo_data.py
DELETE FROM value_assurance_solutions;

-- Also wipe evaluations — they reference solution IDs that will no longer exist.
DELETE FROM value_assurance_evaluations;

ALTER TABLE value_assurance_solutions
  ADD CONSTRAINT uq_solution_kpi_situation UNIQUE (kpi_id, situation_id);
