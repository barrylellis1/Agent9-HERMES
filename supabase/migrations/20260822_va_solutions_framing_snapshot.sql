-- reframe_relaunch_and_lineage_design.md / kpi_relationship_basis_design.md's
-- pending VA-capture follow-up.
--
-- Found live 2026-08-22: value_assurance_solutions.kpi_id was always the
-- SITUATION's original KPI, never the framing decision's chosen one -- if a
-- principal reframed (e.g. Gross Margin % -> COGS, today's own live test),
-- VA registered and would go on to measure gross_margin_pct, silently
-- mistracking the thing the human actually decided to act on. The application-
-- layer fix (workflows.py's kpi_id resolution) needs somewhere durable to
-- record what was actually believed at approval time, both KPIs -- not just
-- whichever one won -- so the decision is auditable and VA's eventual
-- "confirm or modify theory layer components" grading has something real to
-- grade against.

ALTER TABLE value_assurance_solutions
    ADD COLUMN IF NOT EXISTS framing_snapshot JSONB,
    ADD COLUMN IF NOT EXISTS target_metric TEXT;

COMMENT ON COLUMN value_assurance_solutions.framing_snapshot IS
    'FramingSnapshot (choice, chosen_kpi_id, chosen_objective_text, falsification_criterion, stated_kpi_id) -- what was believed true about the objective at approval time. NULL for solutions approved before this column existed, or where no framing gate ran. Does not yet capture alternatives_considered or the framing record''s own decided_by_role/assumption_id -- those need frontend threading beyond framing_decision, see the design note.';

COMMENT ON COLUMN value_assurance_solutions.target_metric IS
    'The approved option''s own impact_estimate.metric -- which KPI its impact is measured against. Empirically validated 2026-08-21/22 as a clean discriminator of frame-widening (dq_l1_framing_signal_design.md), unlike raw KPI-name mentions in solution text.';
