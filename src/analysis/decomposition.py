"""
Pure functions over the KPI decomposition tree (Phase 17 T2).

No DB, no LLM -- same design commitment as groundedness.py and
narrative_claims.py: a stochastic ruler cannot measure a stochastic process,
and neither can a validator that itself depends on one.

Two capabilities, given the tree (kpi_decompositions rows) plus current KPI
values the caller already has (from a live DA run, or a test fixture):

1. `roll_up_scope` -- segment-level delta -> enterprise-level effect. The
   checkable version of "scope translation comes free"
   (DEVELOPMENT_PLAN.md Phase 17): "+2.8pp on Engine Oils" becomes "+0.9pp
   enterprise at 32% revenue share" by arithmetic, not by an LLM restating
   it (or a production briefing having to flag the ambiguity in its own
   risk register, which is what happened before this existed).

2. `check_tree_reconciles` -- verifies a parent's declared children
   actually combine (via `linear`'s signed sum, or `ratio`) to reproduce
   the parent's OWN current value. DEVELOPMENT_PLAN.md Phase 17, "RESOLVED:
   derive the structure, author the presentation": "Derived structure is
   testable. Assert that children reconcile to their parent -- if
   gross_profit's children do not sum to gross_profit, either the tree or
   the KPI is wrong, and it surfaces at build time rather than in front of
   a CFO."
"""
from __future__ import annotations

from typing import Dict, List, Optional

from src.registry.models.kpi_decomposition import KPIDecompositionEdge


def roll_up_scope(
    segment_delta: float,
    segment_weight: float,
    enterprise_weight: float,
) -> Optional[float]:
    """Translate a segment-level delta into its enterprise-level effect.

    `segment_delta`: the observed move within one segment (e.g. Engine Oils'
    gross_margin_pct rose 2.8pp).
    `segment_weight` / `enterprise_weight`: the KPI's declared weight_column
    value (net_revenue) for that segment vs. the enterprise total.

    Returns `segment_delta * (segment_weight / enterprise_weight)` -- e.g.
    2.8 * (engine_oils_revenue / total_revenue). Returns None (not zero) when
    `enterprise_weight` is falsy: an undefined share is not the same claim as
    a zero effect, and the two must never be conflated.
    """
    if not enterprise_weight:
        return None
    return segment_delta * (segment_weight / enterprise_weight)


def check_tree_reconciles(
    parent_kpi_id: str,
    edges: List[KPIDecompositionEdge],
    current_values: Dict[str, float],
    *,
    parent_unit_class: Optional[str] = None,
    tolerance: float = 0.01,
) -> Optional[str]:
    """Verify `parent_kpi_id`'s declared direct children reproduce its own
    current value.

    `edges`: the parent's direct children only (KPIDecompositionProvider.
    get_children's return shape) -- not the full recursive tree.
    `current_values`: kpi_id -> its current value, from whatever source the
    caller has (a live DA run, VA's snapshot, a test fixture).
    `parent_unit_class`: disambiguates ratio scaling -- 'ratio' KPIs in this
    codebase are stored percent-scaled (gross_margin_pct = 100 * gross_profit
    / net_revenue, per every seeded KPI's own sql_query), so a 'ratio' edge
    is checked against `100 * child / weight` when the parent's unit_class
    is 'ratio'; any other unit_class (or None) is checked as a plain
    fraction (`child / weight`).

    Returns a violation string, or None when the tree reconciles -- or when
    there is nothing to check (a value is missing). Missing data is a
    documented no-op, never a silent pass or a silent fail.

    `tolerance` is a fraction of the parent's own magnitude (default 1%) --
    generous enough for rounding, tight enough to catch a genuinely wrong or
    stale edge.
    """
    if not edges:
        return None
    parent_value = current_values.get(parent_kpi_id)
    if parent_value is None:
        return None

    operations = {e.operation for e in edges}
    if len(operations) > 1:
        return (
            f"'{parent_kpi_id}' has children declared under inconsistent operations "
            f"({sorted(operations)}) -- a parent's direct children must share one operation."
        )
    operation = operations.pop()

    if operation == "linear":
        contributions = []
        for e in edges:
            v = current_values.get(e.child_kpi_id)
            if v is None:
                return None
            contributions.append(e.sign * v)
        computed = sum(contributions)
    elif operation == "ratio":
        if len(edges) != 1:
            return f"'{parent_kpi_id}' has {len(edges)} 'ratio' edges -- exactly one is expected."
        edge = edges[0]
        child_value = current_values.get(edge.child_kpi_id)
        weight_value = current_values.get(edge.weight_kpi_id) if edge.weight_kpi_id else None
        if child_value is None or not weight_value:
            return None
        computed = (100.0 if parent_unit_class == "ratio" else 1.0) * child_value / weight_value
    else:
        # Unknown operation -- nothing to check yet, matching every other
        # not-checkable case above.
        return None

    allowed = max(abs(parent_value) * tolerance, 0.01)
    if abs(computed - parent_value) <= allowed:
        return None

    return (
        f"'{parent_kpi_id}' does not reconcile with its declared children: computed {computed:g} "
        f"via {operation}, but the parent's own current value is {parent_value:g} "
        f"(off by {abs(computed - parent_value):g}) -- either the tree or the KPI definition is wrong."
    )
