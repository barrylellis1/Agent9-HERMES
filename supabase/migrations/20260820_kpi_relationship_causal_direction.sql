-- causal_edge_direction_and_magnitude_design.md: direction piece.
--
-- kpi_id / related_kpi_id carry no causal ordering convention today -- found
-- live 2026-08-20 walking the framing gate for a Net Revenue variance, which
-- offered COGS as a candidate alternative objective. COGS has no real
-- relationship to Net Revenue; the only path to it is two hops through
-- gross_margin_pct, and the second edge on that path (gross_margin_pct <->
-- cogs) was walked BACKWARD -- its own mechanism text says COGS causes
-- margin, not the reverse. The seed data itself is inconsistent about which
-- slot holds the cause (base_oil_cost, the cause, is stored as kpi_id in one
-- edge; cogs, the cause per its mechanism, is stored as related_kpi_id in
-- another) -- confirming kpi_id/related_kpi_id order carries no directional
-- meaning and never did.
--
-- get_causal_neighbourhood's BFS stays undirected on purpose (SA's
-- compound-alert detection is right that two KPIs breaching together are
-- worth flagging regardless of which is upstream). This column is consumed
-- only by A9_Deep_Analysis_Agent._build_framing_prompt's path-validity check:
-- a multi-hop framing alternative is only offered if every edge on the path
-- back to the analysed KPI, read toward the origin, is a confirmed
-- cause-of relationship. Default 'unknown' means an edge nobody has
-- reviewed yet simply can't be used as a stepping stone -- it doesn't
-- silently become wrong, and it doesn't block that edge's own 1-hop
-- alternative from showing (1-hop stays direction-agnostic, matching the
-- framing gate's original decision #3: shown unfiltered by direction).

ALTER TABLE kpi_relationships
    ADD COLUMN IF NOT EXISTS causal_direction VARCHAR(32) NOT NULL DEFAULT 'unknown';

ALTER TABLE kpi_relationships
    ADD CONSTRAINT kpi_relationships_causal_direction_check
        CHECK (causal_direction IN ('kpi_causes_related', 'related_causes_kpi', 'bidirectional', 'unknown'));

COMMENT ON COLUMN kpi_relationships.causal_direction IS
    'Which end of the edge is upstream: kpi_causes_related | related_causes_kpi | bidirectional | unknown (default -- preserves undirected behavior for edges not yet reviewed). Consumed only by the framing-gate multi-hop path-validity check, not get_causal_neighbourhood''s BFS, which stays undirected for SA''s compound-alert detection.';
