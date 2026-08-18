-- ---------------------------------------------------------------------------
-- Framing decision attribution fields (Phase 19, Slice 2 — 2026-08-18)
--
-- Discovered mid-implementation: building the framing gate's "re-present a
-- prior frame with its reasoning, never pre-ticked" behavior needs to know
-- WHICH kind of decision was made (confirm the stated objective / pick a
-- named alternative / free-text other) and WHO made it relative to the KPI's
-- ownership — neither is recoverable from 20260818_framing_records.sql's
-- fields without parsing `text` as prose, which this codebase treats as
-- unacceptable (never infer what should be recorded explicitly).
--
-- Separate migration from 20260818_framing_records.sql (applied together,
-- but kept as two files) so each is independently reviewable against the
-- decision it corresponds to — the first migration is "this table can now
-- hold a framing record at all"; this one is "and here is what a framing
-- record specifically needs to carry".
-- ---------------------------------------------------------------------------

ALTER TABLE assumptions
    ADD COLUMN IF NOT EXISTS framing_choice VARCHAR(32),
    ADD COLUMN IF NOT EXISTS decided_by_role VARCHAR(64),
    ADD COLUMN IF NOT EXISTS decided_by_is_owner BOOLEAN;

ALTER TABLE assumptions
    DROP CONSTRAINT IF EXISTS assumptions_framing_choice_check;
ALTER TABLE assumptions
    ADD CONSTRAINT assumptions_framing_choice_check
        CHECK (framing_choice IS NULL OR framing_choice IN ('confirm_stated', 'alternative', 'other'));

COMMENT ON COLUMN assumptions.framing_choice IS
    'Which kind of framing decision this was -- mirrors FramingDecision.choice (Phase 19). Only populated for record_type=''framing''. Needed so a prior frame can be re-presented accurately rather than re-derived by comparing text strings.';
COMMENT ON COLUMN assumptions.decided_by_role IS
    'The role that submitted this decision -- server-computed from principal_context at submission time, never client-claimed.';
COMMENT ON COLUMN assumptions.decided_by_is_owner IS
    'Whether decided_by_role matched the KPI''s owner_role at submission time (problem_framing_design.md §8 item 7 / Decision #5: non-owners may submit, with attribution).';
