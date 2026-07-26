-- Phase 15 Stage D/E: Theory layer causal schema
--
-- Extends kpi_relationships with causal typing and adds the
-- assumption/constraint/explanation register (theory_layer_design.md §4, §5.5).
--
-- Design note: causal_rung and provenance are deliberately SEPARATE axes, not
-- one field. provenance answers "how was this captured" (the existing ladder:
-- template/confirmed/hitl_proposed/va_validated). causal_rung answers "which
-- rung of Pearl's ladder of causation was actually established" (correlational/
-- intervention_hypothesized/intervention_tested) -- a va_validated edge is not
-- automatically intervention_tested unless VA specifically ran DiD on THIS
-- relationship. Conflating these was the design gap surfaced when researching
-- causal-graph best practices (2026-07-23) before writing this migration.
--
-- confidence is deliberately categorical (high/moderate/low), matching
-- SolutionAssumption.confidence -- not a float. Business data from a single
-- client rarely supports probabilistic precision; a float would encode false
-- precision the categorical scale doesn't pretend to have.

-- ---------------------------------------------------------------------------
-- 1. kpi_relationships: causal typing columns
-- ---------------------------------------------------------------------------

ALTER TABLE kpi_relationships
    ADD COLUMN IF NOT EXISTS mechanism TEXT,
    ADD COLUMN IF NOT EXISTS lag_periods INTEGER,
    ADD COLUMN IF NOT EXISTS causal_rung VARCHAR(32),
    ADD COLUMN IF NOT EXISTS provenance VARCHAR(32) NOT NULL DEFAULT 'template',
    ADD COLUMN IF NOT EXISTS confidence VARCHAR(16);

ALTER TABLE kpi_relationships
    ADD CONSTRAINT kpi_relationships_causal_rung_check
        CHECK (causal_rung IS NULL OR causal_rung IN ('correlational', 'intervention_hypothesized', 'intervention_tested')),
    ADD CONSTRAINT kpi_relationships_provenance_check
        CHECK (provenance IN ('template', 'confirmed', 'hitl_proposed', 'va_validated')),
    ADD CONSTRAINT kpi_relationships_confidence_check
        CHECK (confidence IS NULL OR confidence IN ('high', 'moderate', 'low')),
    -- Epistemic guardrail (added 2026-07-26, discussion: does HITL confirmation
    -- risk masquerading as scientific proof?): human confirmation is agreement
    -- with a narrative, not a statistical test. 'confirmed' provenance must
    -- never be able to claim the intervention_tested rung -- only VA actually
    -- running DiD/Granger causality on THIS edge earns that rung. Enforced at
    -- the DB layer, not just documentation, so no write path can quietly
    -- upgrade a human sign-off into a scientific claim.
    ADD CONSTRAINT kpi_relationships_tested_requires_va_validated
        CHECK (causal_rung != 'intervention_tested' OR provenance = 'va_validated');

COMMENT ON COLUMN kpi_relationships.mechanism IS
    'Free-text causal pathway (e.g. "input cost pass-through, inventory-buffered"). Human/LLM-authored; nothing writes theory autonomously (theory doc §5).';
COMMENT ON COLUMN kpi_relationships.lag_periods IS
    'Lag in months between cause and effect. Prefer Granger-causality-derived values on va_validated edges over guessed values on template/hitl_proposed edges (theory doc §5.3 "lag capture for free").';
COMMENT ON COLUMN kpi_relationships.causal_rung IS
    'Pearl ladder-of-causation rung actually established: correlational (association only, SA/DA-detected) | intervention_hypothesized (SF proposed, untested) | intervention_tested (VA ran DiD/counterfactual on this specific edge). Orthogonal to provenance.';
COMMENT ON COLUMN kpi_relationships.provenance IS
    'How this edge was captured: template (MA industry research, unconfirmed) | confirmed (exec/admin blessed) | hitl_proposed (extracted from usage, awaiting confirmation) | va_validated (VA-tested). Consumption rule: SF must caveat or ignore template edges; language on va_validated edges capped at "consistent with" -- never "proved".';
COMMENT ON COLUMN kpi_relationships.confidence IS
    'Categorical confidence (high/moderate/low), matching SolutionAssumption.confidence.';

-- NOTE (data, not schema): existing 11I-B seeded rows (e.g. Hess) will backfill
-- to provenance='template' via the column default. They were hand-declared by
-- the admin/dev team, not MA-researched, so 'confirmed' may be more accurate --
-- a manual data review decision, not made here.

-- ---------------------------------------------------------------------------
-- 2. assumptions: assumption / constraint / explanation register
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS assumptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(64) NOT NULL,
    scope VARCHAR(128) NOT NULL,
    record_type VARCHAR(16) NOT NULL DEFAULT 'assumption',
    text TEXT NOT NULL,
    status VARCHAR(16) NOT NULL DEFAULT 'active',
    source VARCHAR(32) NOT NULL,
    provenance VARCHAR(32) NOT NULL DEFAULT 'hitl_proposed',
    confidence VARCHAR(16),
    expiry TIMESTAMPTZ,
    linked_situation_id VARCHAR(128),
    linked_solution_id VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT assumptions_record_type_check CHECK (record_type IN ('assumption', 'constraint', 'explanation')),
    CONSTRAINT assumptions_status_check CHECK (status IN ('active', 'held', 'falsified', 'lifted')),
    CONSTRAINT assumptions_source_check CHECK (source IN ('sa_hitl', 'sf_hitl_rejection', 'sf_hitl_approval', 'va_hitl', 'manual')),
    CONSTRAINT assumptions_provenance_check CHECK (provenance IN ('template', 'confirmed', 'hitl_proposed', 'va_validated')),
    CONSTRAINT assumptions_confidence_check CHECK (confidence IS NULL OR confidence IN ('high', 'moderate', 'low')),
    -- Mandatory self-falsification (theory doc §5.1, §9 pre-mortem #5): an
    -- explanation record with no expiry is indefinite suppression with better
    -- paperwork, which the accountability model already rejected. Enforced at
    -- the DB layer, not just the application layer, so no write path can skip it.
    CONSTRAINT assumptions_explanation_requires_expiry
        CHECK (record_type != 'explanation' OR expiry IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_assumptions_client_scope ON assumptions (client_id, scope);
CREATE INDEX IF NOT EXISTS idx_assumptions_client_record_type ON assumptions (client_id, record_type);
CREATE INDEX IF NOT EXISTS idx_assumptions_expiry ON assumptions (expiry) WHERE expiry IS NOT NULL;

COMMENT ON TABLE assumptions IS
    'Theory layer assumption/constraint/explanation register (theory_layer_design.md §5.5). One table, not three -- record_type discriminates, matching the Stage B SolutionAssumption unification pattern (Phase 15).';
COMMENT ON COLUMN assumptions.record_type IS
    'assumption = a belief that might be wrong (e.g. "base oil holds under $85"), status lifecycle active|held|falsified. constraint = a stated prohibition from SF-rejection HITL (e.g. "cannot touch pricing on anchor account"), status lifecycle active|lifted. explanation = why a situation is suppressed; MUST carry expiry (see CHECK constraint).';
COMMENT ON COLUMN assumptions.scope IS
    'What this attaches to -- typically a kpi_id or a monitoring-profile threshold identifier. Free text, not a foreign key: it references different tables depending on record_type.';
COMMENT ON COLUMN assumptions.source IS
    'Which HITL surface produced this record -- sa_hitl (situation comment extraction) | sf_hitl_rejection (constraint) | sf_hitl_approval ("bets on" assumption) | va_hitl (outcome adjudication) | manual (admin-entered).';

-- ---------------------------------------------------------------------------
-- 3. RLS (Infra B3 -- mandatory for any new client_id table)
-- ---------------------------------------------------------------------------

GRANT SELECT ON assumptions TO a9_tenant_scope;
ALTER TABLE assumptions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON assumptions;
CREATE POLICY client_isolation ON assumptions FOR SELECT TO a9_tenant_scope
    USING (client_id = current_setting('app.client_id', true));

-- Remember: also add 'assumptions' to _RLS_TABLES in scripts/verify_prod_registry.py
-- (done in this same change -- see that file's diff).
