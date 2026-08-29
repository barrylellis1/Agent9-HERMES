"""Deterministic Pareto-dominance check across a synthesis run's ranked options.

Same discipline as narrative_claims.py and option_id_leak.py in this package:
checkable without an LLM, so checked without one. `_rank_options` in
a9_solution_finder_agent.py already orders options by a weighted score, but
ordering alone doesn't SURFACE dominance — two options can render as equal
peers in a trade-off table even when one is strictly worse on every axis.

Found live 2026-08-24 (real synthesis run, lubricants EBITDA/Base Oil &
Additives): opt_1 and opt_2 were both modelled at an identical $3.8M-$5.2M
EBITDA recovery, but opt_2 took 12+ months against opt_1's 0-90 days, cost
more (0.60 vs 0.45), and carried more risk (0.55 vs 0.40). Nothing marked
opt_2 as dominated; it read as an independent, equally-attractive choice in
the trade-off matrix.

Only `impact_estimate.recovery_range`, `cost`, and `risk` are compared —
`time_to_value`/`reversibility` are free text (e.g. "0-90 days" vs "12+
months") and deliberately NOT parsed into an ordinal scale here: a fragile
text-to-number heuristic risks false positives, which are worse than no flag
(same "flags that cry wolf get ignored" lesson already learned in
narrative_claims.py). An option is never compared across a different
`impact_estimate.scope`/`scope_label` — that would be exactly the
segment-vs-enterprise order-of-magnitude trap ImpactEstimate's own docstring
warns about.
"""
from typing import Any, Dict, List, Optional, Tuple


def _recovery_bounds(option: Any) -> Optional[Tuple[float, float]]:
    ie = getattr(option, "impact_estimate", None)
    if ie is None:
        return None
    rr = getattr(ie, "recovery_range", None)
    if rr is None:
        return None
    low, high = getattr(rr, "low", None), getattr(rr, "high", None)
    if low is None or high is None:
        return None
    return (float(low), float(high))


def _scope_key(option: Any) -> Optional[str]:
    ie = getattr(option, "impact_estimate", None)
    if ie is None:
        return None
    scope = getattr(ie, "scope", None)
    if scope is None:
        return None  # unstated scope is unverified — never treated as comparable
    return f"{scope}:{getattr(ie, 'scope_label', None)}"


def find_dominated_options(options: List[Any]) -> List[Dict[str, Any]]:
    """Returns one entry per dominated option:
    {"dominated_id", "dominated_by_id", "reason"}.

    Empty when no genuine comparison is possible (impact_estimate/cost/risk
    missing, or every pair spans a different scope) — absence here means
    "could not determine," not "confirmed not dominated."
    """
    findings: List[Dict[str, Any]] = []
    for a in options:
        a_bounds = _recovery_bounds(a)
        if a_bounds is None or a.cost is None or a.risk is None:
            continue
        a_scope = _scope_key(a)
        if a_scope is None:
            continue

        for b in options:
            if a is b:
                continue
            b_bounds = _recovery_bounds(b)
            if b_bounds is None or b.cost is None or b.risk is None:
                continue
            if _scope_key(b) != a_scope:
                continue

            impact_ge = a_bounds[0] >= b_bounds[0] and a_bounds[1] >= b_bounds[1]
            cost_le = a.cost <= b.cost
            risk_le = a.risk <= b.risk
            strictly_better_somewhere = (
                a_bounds[0] > b_bounds[0] or a_bounds[1] > b_bounds[1]
                or a.cost < b.cost or a.risk < b.risk
            )
            if impact_ge and cost_le and risk_le and strictly_better_somewhere:
                findings.append({
                    "dominated_id": b.id,
                    "dominated_by_id": a.id,
                    "reason": (
                        f"{a.id} matches or exceeds {b.id} on modelled recovery "
                        f"({a_bounds[0]}-{a_bounds[1]} vs {b_bounds[0]}-{b_bounds[1]}) "
                        f"while costing no more ({a.cost} vs {b.cost}) and risking "
                        f"no more ({a.risk} vs {b.risk})."
                    ),
                })
    return findings


def apply_dominance_flags(options: List[Any]) -> List[Dict[str, Any]]:
    """Mutates `option.dominated_by` on each dominated option in place
    (first dominator found wins if more than one exists) and returns the
    raw findings for audit logging. Call after options are fully parsed,
    before the response is returned."""
    findings = find_dominated_options(options)
    by_id = {o.id: o for o in options}
    for finding in findings:
        opt = by_id.get(finding["dominated_id"])
        if opt is not None and getattr(opt, "dominated_by", None) is None:
            opt.dominated_by = finding["dominated_by_id"]
    return findings


def as_audit_event(findings: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Absent when clean, same convention as the other analysis/ checks."""
    if not findings:
        return None
    return {"event": "dominated_option", "findings": findings}
