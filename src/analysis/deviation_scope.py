"""Is the deviation somewhere, or everywhere?

Kepner-Tregoe tests each segment against its own "should". A segment that is off
it is IS; a comparable segment that could be off but is not is IS NOT. The IS NOT
exists to find a distinction: what is different about where the problem is.

Sometimes there is no IS NOT. Every segment that could be off, is. That is a real
result with a specific meaning: nothing distinguishes the affected segments, so the
cause is common to all of them. The two candidates are a shift outside the business
(the market moved) and a "should" that is itself wrong (a plan set too high).

Found live 2026-10-13 on lubricants Net Revenue against plan: all 60 segments in all
ten dimensions were exactly 16.3% below budget. Deep Analysis reported "the budget
gap is driven by Synthetic Blend Engine Oil, Automatic Transmission Fluid, ...". Those
were not drivers. They were the largest products, each 16.3% short like every other,
and Solution Finder built options around them.

This module only counts. It never decides that a deviation is general from a
truncated list: `member_stats` is given every member of a dimension.
"""
from __future__ import annotations

from statistics import median
from typing import Any, Dict, Iterable, Optional, Tuple

# Segments whose proportional gaps all sit within this many percentage points of each
# other are "the same size of gap". Wider than that and the extent genuinely differs.
UNIFORM_TOLERANCE_PTS = 2.0

Diff = Tuple[Any, float, float, float]  # (key, current, previous, delta)


def member_stats(diffs: Iterable[Diff], trend_positive: bool) -> Dict[str, Any]:
    """Count one dimension's members by which way each moved against its own comparison.

    Members with no comparison value are left out: there is no "should" to be off.
    `gap_pcts` are the signed proportional gaps of the ADVERSE members; `gain_pcts`
    those of the favourable ones.
    """
    adverse_pcts, favourable_pcts = [], []
    for _key, _current, previous, delta in diffs:
        if not previous:
            continue
        pct = 100.0 * delta / abs(previous)
        is_adverse = (delta < 0) if trend_positive else (delta > 0)
        (adverse_pcts if is_adverse else favourable_pcts).append(pct)
    return {
        "members": len(adverse_pcts) + len(favourable_pcts),
        "adverse": len(adverse_pcts),
        "favourable": len(favourable_pcts),
        "gap_pcts": adverse_pcts,
        "gain_pcts": favourable_pcts,
    }


def assess(stats_by_dimension: Optional[Dict[str, Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    """-> {"kind", "direction", ...counts and gap range...}, or None when nothing was counted.

    kind:
    - "localised":       some members moved one way and some the other. There is an IS NOT.
    - "general_uniform": every member moved the same way, by about the same proportion.
    - "general_uneven":  every member moved the same way, by differing proportions.
    direction: "adverse" or "favourable" (which way everything moved), None when localised.
    """
    dims = {d: s for d, s in (stats_by_dimension or {}).items() if s and s.get("members")}
    if not dims:
        return None
    members = sum(s["members"] for s in dims.values())
    adverse = sum(s["adverse"] for s in dims.values())
    favourable = sum(s["favourable"] for s in dims.values())
    base = {
        "dimensions_checked": len(dims),
        "members_checked": members,
        "adverse_members": adverse,
        "favourable_members": favourable,
    }
    if adverse and favourable:
        return {"kind": "localised", "direction": None, **base}
    direction = "adverse" if adverse else "favourable"
    pcts = [p for s in dims.values() for p in (s["gap_pcts"] if adverse else s["gain_pcts"])]
    if not pcts:
        return None
    low, high = min(pcts), max(pcts)
    uniform = (high - low) <= UNIFORM_TOLERANCE_PTS
    return {
        "kind": "general_uniform" if uniform else "general_uneven",
        "direction": direction,
        "gap_pct_typical": round(median(pcts), 1),
        "gap_pct_min": round(low, 1),
        "gap_pct_max": round(high, 1),
        **base,
    }


def is_general(scope: Optional[Dict[str, Any]]) -> bool:
    return bool(scope) and str(scope.get("kind", "")).startswith("general") and scope.get("direction") == "adverse"


def describe(scope: Optional[Dict[str, Any]], against_plan: bool) -> Optional[str]:
    """One or two plain sentences for the reader, or None when the deviation is not
    general. States the count it rests on, and the two candidate causes."""
    if not is_general(scope):
        return None
    n, dims = scope["members_checked"], scope["dimensions_checked"]
    typical = scope["gap_pct_typical"]
    side = "below" if typical < 0 else "above"
    reference = "plan" if against_plan else "the comparison period"
    if scope["kind"] == "general_uniform":
        extent = (
            f"The gap is across the board: all {n} segments checked, in {dims} dimension"
            f"{'' if dims == 1 else 's'}, are about {abs(typical):.1f}% {side} {reference}. "
            "No segment stands out."
        )
    else:
        lo, hi = sorted((abs(scope["gap_pct_min"]), abs(scope["gap_pct_max"])))
        extent = (
            f"The gap is across the board: all {n} segments checked, in {dims} dimension"
            f"{'' if dims == 1 else 's'}, are {side} {reference}, by {lo:.1f}% to {hi:.1f}%. "
            "The size differs, but no segment is unaffected."
        )
    second = "a plan that was set too high" if against_plan else "a change that applied to the whole business"
    return (
        f"{extent} A gap that is everywhere points to a cause common to the whole business: "
        f"a shift in the market, or {second}."
    )
