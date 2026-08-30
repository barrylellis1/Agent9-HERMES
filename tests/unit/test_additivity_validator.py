"""
DEVELOPMENT_PLAN.md Phase 17, T1 (second half) -- the additivity check.

Pinned against the REAL live defect documented at the top of
src/analysis/groundedness.py: an option claimed a 26-47pp enterprise move on
gross_margin_pct, built by summing unweighted segment-level pp deltas
(43.24+16.76+15.18=75.18) against a KPI whose actual enterprise move was
-1.67pp. That case is already caught (test_sf_metrics.py's
test_g3_catches_the_live_enterprise_summation_case) because the claim was
also implausible in magnitude. This module's job is the case magnitude alone
cannot catch: a correctly-computed wrong sum that happens to still look
plausible.
"""
from src.registry.models.kpi import KPI
from src.registry.validators.additivity_validator import check_scope_claim_additivity


def _kpi(**overrides) -> KPI:
    base = dict(
        id="gross_margin_pct",
        client_id="lubricants",
        name="Gross Margin %",
        domain="Finance",
        data_product_id="dp_lubricants_financials",
    )
    base.update(overrides)
    return KPI(**base)


class TestUndeclaredIsANoOp:
    """None (not yet declared) must never be treated as either True or False."""

    def test_undeclared_additivity_yields_no_violation(self):
        kpi = _kpi(additive_across_dimensions=None)
        result = check_scope_claim_additivity(
            kpi=kpi, scope="enterprise", claimed_value=2.3, segment_sum=2.3, enterprise_delta=2.0,
        )
        assert result is None

    def test_no_kpi_supplied_yields_no_violation(self):
        result = check_scope_claim_additivity(
            kpi=None, scope="enterprise", claimed_value=2.3, segment_sum=2.3, enterprise_delta=2.0,
        )
        assert result is None

    def test_declared_true_yields_no_violation(self):
        """additive_across_dimensions=True (e.g. net_revenue, cogs) -- summing is legitimate."""
        kpi = _kpi(id="net_revenue", additive_across_dimensions=True)
        result = check_scope_claim_additivity(
            kpi=kpi, scope="enterprise", claimed_value=2.3, segment_sum=2.3, enterprise_delta=0.1,
        )
        assert result is None


class TestScopeGating:
    def test_segment_scope_never_checked(self):
        """A segment-scoped claim isn't a rollup at all -- nothing to check."""
        kpi = _kpi(additive_across_dimensions=False)
        result = check_scope_claim_additivity(
            kpi=kpi, scope="segment", claimed_value=2.3, segment_sum=2.3, enterprise_delta=2.0,
        )
        assert result is None

    def test_no_segment_sum_available_yields_no_violation(self):
        kpi = _kpi(additive_across_dimensions=False)
        result = check_scope_claim_additivity(
            kpi=kpi, scope="enterprise", claimed_value=2.3, segment_sum=None, enterprise_delta=2.0,
        )
        assert result is None


class TestClosesTheMagnitudePlausibleGap:
    """The actual defect this module exists to catch: a claim that would PASS
    the existing magnitude-ratio check (groundedness.py's G3/cross_segment_summation)
    because it happens to sit inside the plausibility ceiling, yet was still
    built by summing segment values on a KPI declared non-additive."""

    def test_claim_closer_to_segment_sum_than_enterprise_move_is_flagged(self):
        # Ceiling here (enterprise_delta * 1.2 = 2.4) would pass the OLD
        # magnitude-only check for a claim of 2.3 -- this is exactly the gap.
        kpi = _kpi(additive_across_dimensions=False, aggregation_method="weighted_avg", weight_column="net_revenue")
        result = check_scope_claim_additivity(
            kpi=kpi, scope="enterprise", claimed_value=2.3, segment_sum=2.3, enterprise_delta=2.0,
        )
        assert result is not None
        assert "additive_across_dimensions=false" in result
        assert "weighted_avg" in result

    def test_claim_closer_to_enterprise_move_than_segment_sum_is_not_flagged(self):
        kpi = _kpi(additive_across_dimensions=False)
        result = check_scope_claim_additivity(
            kpi=kpi, scope="enterprise", claimed_value=2.05, segment_sum=9.0, enterprise_delta=2.0,
        )
        assert result is None

    def test_no_enterprise_delta_available_still_flags_on_segment_sum_proximity(self):
        kpi = _kpi(additive_across_dimensions=False)
        result = check_scope_claim_additivity(
            kpi=kpi, scope="enterprise", claimed_value=5.0, segment_sum=5.0, enterprise_delta=None,
        )
        assert result is not None
