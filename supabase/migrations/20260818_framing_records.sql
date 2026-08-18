-- ---------------------------------------------------------------------------
-- Framing records (Phase 19 — problem_framing_design.md, implementation plan
-- 2026-08-18)
--
-- Extends the theory-layer assumptions table (20260723_theory_layer_causal_schema)
-- with what the mandatory framing gate needs: a new record_type='framing' value,
-- a new source='da_hitl' value (the refinement interview is the HITL surface that
-- produces these, distinct from every existing source which names a different
-- agent's HITL surface), and an event-based expiry trigger.
--
-- Separate migration rather than an edit to an applied one, same reasoning as
-- 20260731_assumption_grading_fields.sql: editing an applied migration in place
-- produces a checksum mismatch and silently skips the change for anyone who
-- already ran it.
-- ---------------------------------------------------------------------------

ALTER TABLE assumptions
    ADD COLUMN IF NOT EXISTS expiry_event VARCHAR(64);

-- record_type gains 'framing': a human-chosen problem objective, recorded at
-- the mandatory first topic of the Problem Refinement interview.
ALTER TABLE assumptions
    DROP CONSTRAINT IF EXISTS assumptions_record_type_check;
ALTER TABLE assumptions
    ADD CONSTRAINT assumptions_record_type_check
        CHECK (record_type IN ('assumption', 'constraint', 'explanation', 'framing'));

-- source gains 'da_hitl': the framing gate is a Deep Analysis / Problem
-- Refinement surface, not any of the existing SA/SF/VA HITL sources.
ALTER TABLE assumptions
    DROP CONSTRAINT IF EXISTS assumptions_source_check;
ALTER TABLE assumptions
    ADD CONSTRAINT assumptions_source_check
        CHECK (source IN ('sa_hitl', 'sf_hitl_rejection', 'sf_hitl_approval', 'va_hitl', 'manual', 'da_hitl'));

-- expiry_event: the only value today is 'va_verdict_on_linked_solution' — the
-- frame expires when Value Assurance resolves the bet on the solution it
-- governed (validated OR failed; both outcomes are genuine re-examination
-- triggers). `expiry` is typed as an ISO datetime and cannot express an
-- event-based trigger, hence a separate, deliberately narrow column rather
-- than overloading `expiry`'s meaning.
ALTER TABLE assumptions
    DROP CONSTRAINT IF EXISTS assumptions_expiry_event_check;
ALTER TABLE assumptions
    ADD CONSTRAINT assumptions_expiry_event_check
        CHECK (expiry_event IS NULL OR expiry_event IN ('va_verdict_on_linked_solution'));

COMMENT ON COLUMN assumptions.expiry_event IS
    'Event-based expiry trigger for record_type=''framing'' -- see problem_framing_design.md §8 item 3. '
    'Framing records deliberately leave `expiry` NULL: their trigger is a VA verdict on the solution the '
    'frame governed, not a calendar date. KNOWN GAP, carried forward not solved here: a frame whose '
    'solution is never approved has no expiry_event to fire and never expires -- the common case in a '
    'low-adoption pilot, and exactly the accretion-ladder risk the provenance ladder was built to '
    'prevent if left unbackstopped. A future migration should add a calendar-based backstop (e.g. no '
    'approved solution within N assessment cycles) once real pilot usage shows how common the gap is.';

-- Active-framing lookup: "what is the current frame for this KPI?" — the read
-- path AssumptionProvider.get_active_framing() uses on every refinement turn
-- once the gate has fired once for a given scope.
CREATE INDEX IF NOT EXISTS idx_assumptions_framing_scope
    ON assumptions (client_id, scope)
    WHERE record_type = 'framing';
