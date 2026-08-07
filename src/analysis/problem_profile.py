"""
Deterministic problem-type classification from Deep Analysis output.

WHY THIS EXISTS
---------------
"Should this KPI use an MBB council or a diverse one? A debate or a collaborative
protocol?" is unanswerable while every experiment runs on one situation. Averaging
council effects across structurally different problems hides exactly the effect
we are trying to find — a council that helps on a distributed multi-segment
problem may do nothing on a single-segment one.

This module labels the problem so effects can be compared WITHIN type. Every
facet is read from data DA already emits; nothing here calls an LLM or guesses.

It also gives the first real test of DA's own council routing
(`a9_deep_analysis_agent.py::_recommend_diverse_council`), which selects partners
by keyword matching over refinement prose and principal role — never by the
structural facets below. Whether those are the facets that actually matter for
outcome quality is an open question this makes measurable.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

# A top segment at least 2x the next one is doing the work. Chosen over a
# share-of-total measure because DA truncates change_points to the top N, so any
# denominator built from that list is truncation-dependent; a ratio between the
# top two is stable regardless of how many are reported.
DOMINANCE_THRESHOLD = 2.0


@dataclass
class ProblemProfile:
    """Structural facets of a problem, all deterministically derived."""
    kpi_name: Optional[str] = None
    client_id: Optional[str] = None

    mode: Optional[str] = None                 # problem | opportunity | mixed
    mixed_framing: bool = False                # DA needed a HITL framing choice
    concentration: Optional[str] = None        # concentrated | distributed
    dominance_ratio: Optional[float] = None    # top segment delta / second
    segment_count: int = 0
    has_control_group: bool = False            # IS-NOT set non-empty
    compound_alert: bool = False
    market_conflict: bool = False
    cross_kpi: Optional[bool] = None           # needs registry; None = not checked

    notes: List[str] = field(default_factory=list)

    def cell_key(self) -> str:
        """Compact label for grouping experiment runs by problem type."""
        return "/".join([
            self.mode or "unknown",
            self.concentration or "unknown",
            "control" if self.has_control_group else "no-control",
            "compound" if self.compound_alert else "single",
        ])


def classify(
    da_result: Dict[str, Any],
    *,
    kpi_has_relationships: Optional[bool] = None,
) -> ProblemProfile:
    """Classify a DA result. `kpi_has_relationships` is optional registry input;
    left None it reports as not-checked rather than defaulting to False."""
    plan = da_result.get("plan") or {}
    execution = da_result.get("execution") or da_result

    p = ProblemProfile(
        kpi_name=plan.get("kpi_name") or execution.get("kpi_name"),
        client_id=plan.get("client_id"),
        mode=execution.get("analysis_mode") or plan.get("analysis_mode"),
        mixed_framing=bool(execution.get("mixed_framing")),
        cross_kpi=kpi_has_relationships,
    )

    # --- concentration: is one segment carrying the variance? ---------------
    deltas = sorted(
        (abs(float(cp["delta"])) for cp in (execution.get("change_points") or [])
         if isinstance(cp, dict) and isinstance(cp.get("delta"), (int, float))),
        reverse=True,
    )
    p.segment_count = len(deltas)
    if len(deltas) >= 2 and deltas[1] > 0:
        p.dominance_ratio = round(deltas[0] / deltas[1], 2)
        p.concentration = "concentrated" if p.dominance_ratio >= DOMINANCE_THRESHOLD else "distributed"
    elif len(deltas) == 1:
        p.concentration = "concentrated"
        p.notes.append("single change point reported")

    # --- control group: does the IS-NOT side have anything in it? -----------
    # Matters because KT diagnosis leans on contrast. A problem with an empty
    # IS-NOT set has no control group, so "why here and not there" cannot be
    # answered from the data — worth knowing before comparing protocols that
    # assume a contrast set exists.
    kt = execution.get("kt_is_is_not") or {}
    p.has_control_group = bool(kt.get("where_is_not"))
    if not p.has_control_group:
        p.notes.append("empty IS-NOT set — no contrast group available for diagnosis")

    # --- compound / market conflict ----------------------------------------
    p.compound_alert = bool(
        plan.get("compound_alert") or execution.get("compound_alert")
        or plan.get("merged_alert_types") or execution.get("merged_alert_types")
    )
    p.market_conflict = bool(da_result.get("market_conflict") or execution.get("market_conflict"))

    return p


def profiles_differ(a: ProblemProfile, b: ProblemProfile) -> Set[str]:
    """Which facets differ between two problems — used to confirm that a second
    experiment situation is genuinely structurally different from the first,
    rather than the same shape wearing a different KPI name."""
    out: Set[str] = set()
    for facet in ("mode", "concentration", "has_control_group", "compound_alert",
                  "market_conflict", "cross_kpi"):
        if getattr(a, facet) != getattr(b, facet):
            out.add(facet)
    return out
