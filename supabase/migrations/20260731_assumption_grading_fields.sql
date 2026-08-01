-- ---------------------------------------------------------------------------
-- Assumption grading fields (Phase 15 / theory layer §5.3)
--
-- Adds the two fields needed to carry an SF "bets on" assumption through to a
-- verdict at VA evaluation. Both come from SolutionAssumption
-- (src/agents/models/solution_finder_models.py) and had no home on the registry
-- model, so pre-registering an approved option's bets lost exactly the two
-- pieces of information that make grading them possible later.
--
-- Separate migration rather than an edit to 20260723_theory_layer_causal_schema
-- because that one is already applied; editing an applied migration in place
-- produces a checksum mismatch and silently skips the change for anyone who
-- already ran it.
-- ---------------------------------------------------------------------------

ALTER TABLE assumptions
    ADD COLUMN IF NOT EXISTS validated_by VARCHAR(32),
    ADD COLUMN IF NOT EXISTS falsification_criterion TEXT;

-- Routing key for grading. Machine-checkable claims must not be put in front of
-- a person: if every solution sends its full assumption list to an executive,
-- adjudication becomes nobody's job and the queue rots (theory doc §9 pre-mortem #3).
ALTER TABLE assumptions
    DROP CONSTRAINT IF EXISTS assumptions_validated_by_check;
ALTER TABLE assumptions
    ADD CONSTRAINT assumptions_validated_by_check
        CHECK (validated_by IS NULL OR validated_by IN ('sa_assessment', 'ma_query', 'human_confirmation'));

COMMENT ON COLUMN assumptions.validated_by IS
    'Who/what can render a verdict: sa_assessment and ma_query are machine-checkable (KPI data / MA re-query and auto-gradeable); human_confirmation is the only value that needs a person. Carried from SolutionAssumption.validated_by.';

-- NOTE the deliberate name. SolutionAssumption calls this field `provenance`,
-- but `assumptions.provenance` already exists above and means something else
-- entirely -- the capture ladder (template|confirmed|hitl_proposed|va_validated).
-- Copying one into the other would fail the ladder's CHECK constraint at best and
-- corrupt provenance semantics at worst, so the falsification criterion gets its
-- own explicitly-named column.
COMMENT ON COLUMN assumptions.falsification_criterion IS
    'What observation would confirm or falsify this claim, in plain language. Carried from SolutionAssumption.provenance -- NOT the same concept as assumptions.provenance (the capture ladder). Language capped at "consistent with", never "proved" (theory doc §4).';

-- Partial unique index: one row per (solution, claim). Approving the same
-- solution twice must not double-register its bets, which would double-count at
-- grading time and inflate whatever evidence later accrues to a causal edge.
-- Partial because linked_solution_id is nullable -- manually-entered assumptions
-- and SA-derived ones legitimately have no solution attached.
--
-- Indexed on md5(text) rather than text itself. A btree index entry must fit in
-- ~2704 bytes, and `text` here is LLM-generated prose of unbounded length --
-- verified: 2700 chars of low-entropy text already fails with "index row size
-- 2728 exceeds btree version 4 maximum 2704". Because the INSERT happens inside
-- a deliberately non-fatal handler, that failure would not surface as an error;
-- the assumption would just silently never be registered. md5 is a fixed 32
-- bytes, so the ceiling disappears entirely. (Used as a dedup key, not for
-- security.)
CREATE UNIQUE INDEX IF NOT EXISTS uq_assumptions_solution_text
    ON assumptions (linked_solution_id, md5(text))
    WHERE linked_solution_id IS NOT NULL;

-- Grading lookup: "which active bets belong to this solution?"
CREATE INDEX IF NOT EXISTS idx_assumptions_linked_solution
    ON assumptions (linked_solution_id)
    WHERE linked_solution_id IS NOT NULL;
