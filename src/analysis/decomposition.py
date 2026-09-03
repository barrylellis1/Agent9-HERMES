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

from typing import Any, Dict, List, Optional

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


def evaluate_tree(
    kpi_id: str,
    edges: List[KPIDecompositionEdge],
    values: Dict[str, float],
    *,
    unit_classes: Optional[Dict[str, str]] = None,
    _depth: int = 0,
) -> Optional[float]:
    """Compute `kpi_id`'s value from its LEAF inputs, through the tree.

    A leaf (no outgoing decomposition edges) returns its own value. A parent is
    computed from its children -- signed sum for 'linear', child/weight for
    'ratio' (percent-scaled when the parent's unit_class is 'ratio', matching
    every seeded KPI's own sql_query).

    Returns None whenever any needed input is missing -- never a partial or
    zero-filled result, same documented no-op posture as check_tree_reconciles.

    This is what makes a variance bridge computable GENERICALLY rather than by
    hardcoding one KPI's formula: kpi_relationship_basis_design.md §4 named
    that as an open gap ("`accounting_identity` says an edge is exact
    arithmetic, not WHICH arithmetic"), and the Phase 17 T2 decomposition model
    records the operation explicitly, which closes it for any tree it covers.
    """
    if _depth > 6:
        return None
    children = [e for e in edges if e.parent_kpi_id == kpi_id]
    if not children:
        return values.get(kpi_id)

    ops = {e.operation for e in children}
    if len(ops) > 1:
        return None
    op = ops.pop()

    if op == "linear":
        total = 0.0
        for e in children:
            v = evaluate_tree(e.child_kpi_id, edges, values, unit_classes=unit_classes, _depth=_depth + 1)
            if v is None:
                return None
            total += e.sign * v
        return total

    if op == "ratio":
        if len(children) != 1:
            return None
        e = children[0]
        num = evaluate_tree(e.child_kpi_id, edges, values, unit_classes=unit_classes, _depth=_depth + 1)
        den = evaluate_tree(e.weight_kpi_id, edges, values, unit_classes=unit_classes, _depth=_depth + 1) if e.weight_kpi_id else None
        if num is None or not den:
            return None
        scale = 100.0 if (unit_classes or {}).get(kpi_id) == "ratio" else 1.0
        return scale * num / den

    return None


def leaf_inputs(kpi_id: str, edges: List[KPIDecompositionEdge]) -> List[str]:
    """The independent inputs at the bottom of `kpi_id`'s tree, in stable order.

    A KPI appearing both as an intermediate parent and as a leaf elsewhere
    (net_revenue is both gross_profit's child AND gross_margin_pct's ratio
    denominator) is counted ONCE -- it is one independent quantity, and
    double-counting it would fabricate a third bar in a two-input bridge.
    """
    out: List[str] = []
    seen: set = set()

    def walk(kid: str, depth: int = 0) -> None:
        if depth > 6 or kid in seen:
            return
        children = [e for e in edges if e.parent_kpi_id == kid]
        if not children:
            if kid not in out:
                out.append(kid)
            return
        seen.add(kid)
        for e in children:
            walk(e.child_kpi_id, depth + 1)
            if e.weight_kpi_id:
                walk(e.weight_kpi_id, depth + 1)

    walk(kpi_id)
    return out


def variance_bridge(
    kpi_id: str,
    edges: List[KPIDecompositionEdge],
    current: Dict[str, float],
    prior: Dict[str, float],
    *,
    unit_classes: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """Decompose a KPI's MOVE between two periods into per-input effects.

    docs/architecture/kpi_relationship_basis_design.md §4 — the composition
    bridge (decomposing the CURRENT value into its inputs) was explicitly
    rejected as the wrong chart: "the framing question is 'why did this move'
    — inherently about the DELTA between periods, not the current value's
    arithmetic." This is the variance bridge it specified instead.

    Method: sequential substitution. Starting from all-prior, swap one input to
    its current value at a time; each swap's effect on the parent is that
    input's contribution. The effects then sum to the observed move EXACTLY,
    with no residual term — the property §4 calls "worth protecting".

    THE TRIPWIRE, implemented rather than just noted: that exact closure holds
    for exactly TWO inputs. §4 — "It stops holding automatically the moment a
    third identity input joins the same bridge... order of substitution then
    affects the split, and either a disclosed convention or an order-
    independent method (Shapley) is needed." So a tree with anything other
    than two leaf inputs returns `exact=False` and a stated reason rather than
    silently emitting an order-dependent split as though it were exact.

    Returns None when the bridge cannot be computed at all (missing values).
    """
    leaves = leaf_inputs(kpi_id, edges)
    if len(leaves) < 2:
        return None
    if not all(k in current and k in prior for k in leaves):
        return None

    start = evaluate_tree(kpi_id, edges, prior, unit_classes=unit_classes)
    end = evaluate_tree(kpi_id, edges, current, unit_classes=unit_classes)
    if start is None or end is None:
        return None

    working = dict(prior)
    effects: List[Dict[str, Any]] = []
    running = start
    for leaf in leaves:
        working[leaf] = current[leaf]
        after = evaluate_tree(kpi_id, edges, working, unit_classes=unit_classes)
        if after is None:
            return None
        effects.append({"kpi_id": leaf, "effect": after - running})
        running = after

    total = end - start
    residual = total - sum(e["effect"] for e in effects)
    exact = len(leaves) == 2
    return {
        "prior_value": start,
        "current_value": end,
        "total_move": total,
        "effects": effects,
        "residual": residual,
        "exact": exact,
        "note": None if exact else (
            f"{len(leaves)} inputs — sequential substitution is order-dependent beyond two "
            "inputs, so this split is one convention among several, not the exact "
            "decomposition (kpi_relationship_basis_design.md §4)."
        ),
    }


def compute_lever_impact(
    headline_kpi_id: str,
    edges: List[KPIDecompositionEdge],
    current_values: Dict[str, float],
    leaf_kpi_id: str,
    delta_low_pct: float,
    delta_high_pct: float,
    *,
    unit_classes: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """Phase 17 D2: compute a headline KPI's impact range from an OPERATIONAL
    lever, instead of an LLM asserting the resulting number directly.

    The LLM proposes the lever (which input, roughly what magnitude — a
    business judgement it is well-placed to make); this computes what that
    lever does to `headline_kpi_id` through the real decomposition tree — an
    arithmetic question it should not be trusted to answer freestanding. Two
    real, documented briefing errors this session traced (a segment number
    promoted to the headline KPI; three cited figures summing to 140.4pp
    instead of 75.18) both originated in exactly this gap: SF's
    `recovery_range` has no Python arithmetic behind it anywhere.

    `leaf_kpi_id` must be a genuine leaf of `headline_kpi_id`'s tree
    (`leaf_inputs`) — a lever aimed at an intermediate node or an unrelated
    KPI is not computable and returns None, never a fabricated number.
    `delta_low_pct`/`delta_high_pct` perturb `leaf_kpi_id` ITSELF (e.g. a
    price lever assumed to move net_revenue +3% to +5%); the corresponding
    headline-KPI effect is what this function derives, via `evaluate_tree`.

    Returns None whenever the lever isn't computable or a needed current
    value is missing — never a partial or best-guess result. On success,
    returns a dict carrying both bounds plus the leaf-level assumption that
    produced them, so a caller can register that assumption for later VA
    grading (the same falsifiable-bet discipline `_grade_assumptions_from_verdict`
    already applies) rather than treating the computed number as free of its
    own uncertainty.
    """
    if leaf_kpi_id not in leaf_inputs(headline_kpi_id, edges):
        return None
    leaf_value = current_values.get(leaf_kpi_id)
    if leaf_value is None:
        return None
    baseline = evaluate_tree(headline_kpi_id, edges, current_values, unit_classes=unit_classes)
    if baseline is None:
        return None

    bounds = []
    for delta_pct in (delta_low_pct, delta_high_pct):
        perturbed = dict(current_values)
        perturbed[leaf_kpi_id] = leaf_value * (1.0 + delta_pct / 100.0)
        effect_value = evaluate_tree(headline_kpi_id, edges, perturbed, unit_classes=unit_classes)
        if effect_value is None:
            return None
        bounds.append(effect_value - baseline)

    return {
        "baseline_value": baseline,
        "effect_low": min(bounds),
        "effect_high": max(bounds),
        "leaf_kpi_id": leaf_kpi_id,
        "leaf_current_value": leaf_value,
        "leaf_delta_low_pct": delta_low_pct,
        "leaf_delta_high_pct": delta_high_pct,
    }


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
