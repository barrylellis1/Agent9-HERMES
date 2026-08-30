"""
Additivity validator -- DEVELOPMENT_PLAN.md Phase 17, T1 (second half:
`additive_across_dimensions`). docs/architecture/kpi_semantic_contract.md §3.

Checks whether a claimed ENTERPRISE-scope figure for a KPI is consistent with
that KPI's declared additivity. Distinct from measure_semantics_validator.py's
negation check: that inspects a KPI's own SQL text against a data-product-level
sign fact (Phase 16 step 2, already live). There is no SQL to parse here --
additivity is a property of how MULTIPLE values of the same KPI (across a
dimension) may be combined, not of how any single one is computed, so the
defect this catches lives in a downstream CLAIM (an SF option's
impact_estimate, a narrative claim), never in a KPI's own query.

This is exactly the bug class documented at the top of
src/analysis/groundedness.py: an option claimed a 26-47pp enterprise move,
built by summing unweighted segment-level pp deltas (43.24 + 16.76 + 15.18 =
75.18) against a KPI whose actual enterprise move was -1.67pp -- gross_margin_pct
is a weighted average across segments, not a sum, and nothing checked that
before this KPI declared additive_across_dimensions=false.

Upgrades groundedness.py's existing `cross_segment_summation` signal
(magnitude-ratio based -- only computed once G3's plausibility ceiling has
ALREADY failed, so a correctly-computed wrong sum that still happens to look
plausible in magnitude sails through undetected) with a check that also
catches that case: compares distance-to-segment-sum against
distance-to-observed-enterprise-move and flags whichever is closer.
Deliberately a heuristic distance comparison, not a proof -- consistent with
every other validator in this codebase being documented as approximate rather
than silently assumed precise (see measure_semantics_validator.py's own scope
note).
"""
from __future__ import annotations

from typing import Optional

from src.registry.models.kpi import KPI


def check_scope_claim_additivity(
    kpi: Optional[KPI],
    scope: Optional[str],
    claimed_value: Optional[float],
    segment_sum: Optional[float],
    enterprise_delta: Optional[float],
) -> Optional[str]:
    """Return a human-readable violation string, or None when there's nothing to flag.

    Fires only when all of the following hold:
    - `scope` is 'enterprise' (a segment-scoped claim isn't a rollup at all,
      nothing to check)
    - `kpi.additive_across_dimensions is False` EXPLICITLY -- None (not yet
      declared for this KPI) is a documented no-op, never treated as either
      True or False, matching measure_semantics_validator.py's own
      "None is a no-op" convention for undeclared facts
    - `segment_sum` is available to compare against (no segment data, nothing
      to compare the claim to)
    - the claim sits closer to `segment_sum` than to `enterprise_delta` (or
      no `enterprise_delta` is available at all, in which case proximity to
      the segment sum alone is sufficient to raise the flag)
    """
    if (
        kpi is None
        or scope != "enterprise"
        or kpi.additive_across_dimensions is not False
        or not isinstance(claimed_value, (int, float))
        or not segment_sum
    ):
        return None

    dist_to_sum = abs(abs(float(claimed_value)) - segment_sum)
    dist_to_enterprise: Optional[float] = (
        abs(abs(float(claimed_value)) - enterprise_delta)
        if enterprise_delta is not None
        else None
    )
    if dist_to_enterprise is not None and dist_to_enterprise <= dist_to_sum:
        # Closer to (or equidistant from) the real enterprise move than to the
        # segment sum -- not the summation defect this check exists to catch.
        return None

    method_note = (
        f", aggregation_method should be '{kpi.aggregation_method}'"
        if kpi.aggregation_method
        else ""
    )
    return (
        f"'{kpi.id}' is declared additive_across_dimensions=false -- claim {claimed_value:g} sits "
        f"closer to the unweighted segment sum ({segment_sum:g}) than to the observed enterprise "
        f"move{method_note}."
    )
