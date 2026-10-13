"""When the gap is everywhere, is an option still pinning it on a segment?

`deviation_scope` says when a deviation is general: every segment is off its own
comparison, so no segment is the cause. Solution Finder is told that in its
prompt, and an instruction is only a request. Three live runs on the same data
(2026-10-13, lubricants Net Revenue, all 75 segments 16.3% below plan) produced
three different option sets; in one, an option sized itself against "the four
largest-declining SKUs" as though the decline were located there.

Each option already declares, as data, what its impact figure covers
(`impact_estimate.scope` / `scope_label`). This module checks that declaration
against the segment figures. It counts and compares; it reads no prose.

Rules, for a general deviation only:
- The scope must be stated.
- A segment-scoped figure must say why it is scoped to a segment, and the reason
  must be one that is true when no segment is the cause: a pilot, or the largest
  exposure. `scope_reason` carries it.
- The named segment must be one the analysis measured, and the figure must not
  exceed that segment's own share of the gap.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

ALLOWED_SEGMENT_REASONS = ("pilot", "largest_exposure")

SCOPE_NOT_STATED = "scope_not_stated"
SEGMENT_WITHOUT_REASON = "segment_scope_without_reason"
SEGMENT_NOT_RECOGNISED = "segment_not_recognised"
IMPACT_EXCEEDS_SEGMENT_GAP = "impact_exceeds_segment_gap"

# What each finding means, in the reader's words.
EXPLANATIONS: Dict[str, str] = {
    SCOPE_NOT_STATED: "The option does not say whether its figure covers the whole business or one segment.",
    SEGMENT_WITHOUT_REASON: (
        "The gap is across the board, but the option is sized to one segment without saying "
        "whether that is a pilot or simply the largest exposure."
    ),
    SEGMENT_NOT_RECOGNISED: "The option names a segment the analysis did not measure, so its figure cannot be checked.",
    IMPACT_EXCEEDS_SEGMENT_GAP: "The option claims to recover more than the named segment's own share of the gap.",
}


def segment_gap(scope_label: Optional[str], change_points: Iterable[Any]) -> Optional[float]:
    """The size of the gap in the segment(s) a label names, or None if it names none
    the analysis measured.

    A label may name several members ("Engine Oils and Gear Oils"). Members of the
    SAME dimension are added. Across dimensions the largest total is taken, never
    the sum: "Retail Partners" (customer segment) and "Retail Products Division"
    (profit centre) can be the same dollars counted twice.
    """
    label = str(scope_label or "").lower()
    if not label.strip():
        return None
    by_dimension: Dict[str, float] = {}
    for cp in change_points or []:
        get = cp.get if isinstance(cp, dict) else (lambda k, _cp=cp: getattr(_cp, k, None))
        key = str(get("key") or "").strip().lower()
        delta = get("delta")
        if not key or len(key) < 3 or not isinstance(delta, (int, float)):
            continue
        if key in label:
            dim = str(get("dimension") or "")
            by_dimension[dim] = by_dimension.get(dim, 0.0) + abs(float(delta))
    return max(by_dimension.values()) if by_dimension else None


def check_impact_scope(impact_estimate: Any, change_points: Iterable[Any]) -> List[str]:
    """Findings for one option's impact estimate under a general deviation. [] = passes.

    `impact_estimate` is the raw dict the model wrote. An option with no impact
    estimate at all makes no sized claim and is not this check's concern.
    """
    if not isinstance(impact_estimate, dict):
        return []
    scope = impact_estimate.get("scope")
    if scope not in ("enterprise", "segment"):
        return [SCOPE_NOT_STATED]
    if scope == "enterprise":
        return []
    findings: List[str] = []
    if impact_estimate.get("scope_reason") not in ALLOWED_SEGMENT_REASONS:
        findings.append(SEGMENT_WITHOUT_REASON)
    gap = segment_gap(impact_estimate.get("scope_label"), list(change_points or []))
    if gap is None:
        findings.append(SEGMENT_NOT_RECOGNISED)
        return findings
    rr = impact_estimate.get("recovery_range")
    high = rr.get("high") if isinstance(rr, dict) else None
    if isinstance(high, (int, float)) and abs(float(high)) > gap * 1.0001:
        findings.append(IMPACT_EXCEEDS_SEGMENT_GAP)
    return findings


def explain(findings: Iterable[str]) -> List[str]:
    return [EXPLANATIONS[f] for f in findings if f in EXPLANATIONS]
