"""Multi-hop causal traversal — reaching the upstream cause (Aug 2026).

THE DEFECT THIS FIXES
---------------------
`get_relationships_for_kpi` returns only edges that TOUCH the KPI. Measured on the
lubricants seed, three of its six edges touch `gross_margin_pct`; the invisible
three include `base_oil_cost -> cogs`, labelled in the seed file as "the 11F
anchor scenario" and carrying that client's single most important causal fact —
base oil is ~41% of COGS and passes through with a one-month lag.

The real chain is `base_oil_cost -> cogs -> gross_margin_pct`. Two hops. Solution
Finder saw one, so a margin analysis could never reach the cause of its own margin
problem. A dimensional breakdown answers WHERE a KPI moved; the causal graph is
the only thing that answers WHY, and it was being read one hop too shallow.

Single-hop behaviour is deliberately preserved for SA's compound-alert detection
and the registry API — both genuinely want direct edges only.
"""

import pytest

from src.registry.models.kpi_relationship import KPIRelationship
from src.registry.providers.kpi_relationship_provider import KPIRelationshipProvider


def _edge(a: str, b: str, provenance: str = "confirmed", rtype: str = "custom") -> KPIRelationship:
    return KPIRelationship(
        kpi_id=a,
        related_kpi_id=b,
        client_id="lubricants",
        relationship_type=rtype,
        conflict_direction="converging",
        description=f"{a} -> {b}",
        provenance=provenance,
    )


# Mirrors the six edges seeded in scripts/clients/lubricants.py.
LUBRICANTS_EDGES = [
    _edge("net_revenue", "gross_margin_pct"),
    _edge("product_sales_revenue", "cogs"),
    _edge("gross_margin_pct", "cogs"),
    _edge("base_oil_cost", "cogs"),          # the 11F anchor — 2 hops from margin
    _edge("premium_mix_pct", "gross_margin_pct"),
    _edge("distribution_cost", "cogs"),
]


class _Provider(KPIRelationshipProvider):
    """Provider with get_all stubbed — traversal is pure logic over the edge set."""

    def __init__(self, edges):
        self._edges = edges

    async def get_all(self, client_id: str):
        return list(self._edges)


@pytest.mark.asyncio
async def test_reaches_the_upstream_cause_the_single_hop_view_hides():
    """The regression. base_oil_cost must be reachable from gross_margin_pct."""
    got = await _Provider(LUBRICANTS_EDGES).get_causal_neighbourhood(
        "gross_margin_pct", "lubricants", max_hops=2
    )
    reached = {r.kpi_id for r, _h in got} | {r.related_kpi_id for r, _h in got}

    assert "base_oil_cost" in reached, (
        "base_oil_cost -> cogs -> gross_margin_pct is the documented anchor scenario; "
        "at max_hops=2 it must be reachable"
    )
    assert "distribution_cost" in reached


@pytest.mark.asyncio
async def test_one_hop_matches_the_old_behaviour():
    """max_hops=1 must return exactly the edges that touch the KPI.

    Pins that the traversal is a superset, not a different answer — SA and the
    registry API still depend on single-hop semantics.
    """
    got = await _Provider(LUBRICANTS_EDGES).get_causal_neighbourhood(
        "gross_margin_pct", "lubricants", max_hops=1
    )
    pairs = {(r.kpi_id, r.related_kpi_id) for r, _h in got}

    assert pairs == {
        ("net_revenue", "gross_margin_pct"),
        ("gross_margin_pct", "cogs"),
        ("premium_mix_pct", "gross_margin_pct"),
    }
    assert all(h == 1 for _r, h in got)


@pytest.mark.asyncio
async def test_hop_distance_is_reported_not_flattened():
    """A 2-hop inference is weaker evidence and must stay distinguishable."""
    got = await _Provider(LUBRICANTS_EDGES).get_causal_neighbourhood(
        "gross_margin_pct", "lubricants", max_hops=2
    )
    by_pair = {(r.kpi_id, r.related_kpi_id): h for r, h in got}

    assert by_pair[("gross_margin_pct", "cogs")] == 1
    assert by_pair[("base_oil_cost", "cogs")] == 2
    assert by_pair[("distribution_cost", "cogs")] == 2


@pytest.mark.asyncio
async def test_each_edge_appears_once_at_its_shortest_distance():
    got = await _Provider(LUBRICANTS_EDGES).get_causal_neighbourhood(
        "gross_margin_pct", "lubricants", max_hops=3
    )
    pairs = [(r.kpi_id, r.related_kpi_id) for r, _h in got]
    assert len(pairs) == len(set(pairs)), "an edge was emitted twice"


@pytest.mark.asyncio
async def test_cycles_terminate():
    """A -> B -> C -> A must not loop."""
    cyc = [_edge("a", "b"), _edge("b", "c"), _edge("c", "a")]
    got = await _Provider(cyc).get_causal_neighbourhood("a", "lubricants", max_hops=10)
    assert len(got) == 3


@pytest.mark.asyncio
async def test_max_edges_bounds_a_dense_graph():
    """A prompt must not be floodable by graph density."""
    dense = [_edge("hub", f"leaf_{i}") for i in range(50)]
    got = await _Provider(dense).get_causal_neighbourhood(
        "hub", "lubricants", max_hops=3, max_edges=10
    )
    assert len(got) == 10


@pytest.mark.asyncio
async def test_empty_graph_returns_empty_not_error():
    """An unseeded client must degrade silently, never fabricate."""
    assert await _Provider([]).get_causal_neighbourhood("x", "c") == []


@pytest.mark.asyncio
async def test_isolated_kpi_returns_nothing():
    got = await _Provider(LUBRICANTS_EDGES).get_causal_neighbourhood(
        "unrelated_kpi", "lubricants", max_hops=3
    )
    assert got == []


# ---------------------------------------------------------------------------
# Prompt rendering
# ---------------------------------------------------------------------------


def test_prompt_labels_indirect_edges_and_warns_about_the_chain():
    from src.agents.new.a9_solution_finder_agent import _build_causal_context_section

    section = _build_causal_context_section(
        [(_edge("gross_margin_pct", "cogs"), 1), (_edge("base_oil_cost", "cogs"), 2)],
        [],
    )
    assert "[DIRECT]" in section
    assert "[INDIRECT via 2 hops]" in section
    # The caveat must appear, or a 2-hop chain reads as an established fact.
    assert "hypothesis to test" in section


def test_prompt_omits_the_indirect_caveat_when_everything_is_direct():
    from src.agents.new.a9_solution_finder_agent import _build_causal_context_section

    section = _build_causal_context_section([(_edge("a", "b"), 1)], [])
    assert "[DIRECT]" in section
    assert "INDIRECT" not in section


def test_prompt_still_accepts_bare_relationships():
    """Backward compatibility: callers that pass un-tupled edges still render."""
    from src.agents.new.a9_solution_finder_agent import _build_causal_context_section

    section = _build_causal_context_section([_edge("a", "b")], [])
    assert "[DIRECT]" in section
    assert "a <-> b" in section
