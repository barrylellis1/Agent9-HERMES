-- kpi_relationship_basis_design.md §2 (designed 2026-08-21, built 2026-08-30 for
-- Phase 17's theory-layer exhibit).
--
-- kpi_relationships treats every edge with the same vocabulary
-- (confidence/provenance/mechanism) whether it's a genuinely uncertain causal
-- claim or an accounting identity true by construction. The 2026-08-22 data
-- pass correctly dropped confidence/causal_rung from the four identity edges
-- (there is no "confidence" in arithmetic) -- but that ABSENCE was then the
-- only thing distinguishing them, and it collides with a real causal edge that
-- simply hasn't been graded yet. Live proof in the lubricants seed:
-- product_sales_revenue<->cogs carries causal_rung=NULL + confidence=NULL and
-- is NOT an identity (its own seed comment calls it "a co-movement, not a
-- recorded cause"). Any heuristic reading NULLs as "identity" misclassifies it.
--
-- The theory-layer exhibit's central claim is "what we know vs. what we
-- assumed". Deriving that distinction from missing fields would undermine the
-- one thing the exhibit exists to show, so it is recorded explicitly here --
-- consistent with this codebase's standing rule against inferring what should
-- be recorded (see src/registry/models/assumption.py's framing_choice comment).
--
-- DEFAULT 'causal_estimate' deliberately: no existing edge may silently
-- upgrade itself to "certain" by virtue of this column appearing.

ALTER TABLE kpi_relationships
    ADD COLUMN IF NOT EXISTS basis TEXT NOT NULL DEFAULT 'causal_estimate'
        CHECK (basis IN ('accounting_identity', 'causal_estimate'));

COMMENT ON COLUMN kpi_relationships.basis IS
    'accounting_identity = true by construction (the KPI is calculated from, or sums into, the other -- no confidence applies to arithmetic). causal_estimate = a genuinely uncertain empirical claim. Defaults to causal_estimate so nothing silently becomes "certain". See docs/architecture/kpi_relationship_basis_design.md §2.';
