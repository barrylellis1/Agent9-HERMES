-- Prevent duplicate solution rows for the same KPI breach.
-- One active solution per (kpi_id, situation_id) pair.
-- Re-approving the same situation upserts the existing row rather than inserting a new one.
-- Genuinely new breaches produce distinct situation_ids, so they still get their own rows.

-- Clear dev/test duplicates before adding the constraint.
-- Keeps the most recently approved row for each (kpi_id, situation_id) pair.
DELETE FROM value_assurance_solutions
WHERE id NOT IN (
    SELECT DISTINCT ON (kpi_id, situation_id) id
    FROM value_assurance_solutions
    ORDER BY kpi_id, situation_id, approved_at DESC NULLS LAST
);

ALTER TABLE value_assurance_solutions
  ADD CONSTRAINT uq_solution_kpi_situation UNIQUE (kpi_id, situation_id);
