"""Ratio KPI deltas are not additive — the arithmetic, and the flag that gates it.

WHY THIS FILE EXISTS
--------------------
The Variance Breakdown panel summed every segment's delta to produce a dimension
header. For Gross Margin % that printed **-53pp** for products and **-50pp** for
customers, against an enterprise move of roughly **-5pp**. Summing the margin
LEVELS the same way gives **452.95%** against a true **29.43%** — overstated
15.4x, measured on the live BigQuery dataset 2026-08-09.

The cause was not the chart. Deep Analysis has a correct ratio path (the
"bridge"): it fetches numerator and denominator SEPARATELY per segment, computes
each segment's rate, and reports `delta` as a revenue-WEIGHTED contribution.
Weighted contributions do sum to the overall change. But that path only runs when
the KPI carries `kpi_type='ratio'` plus bridge SQL in its metadata, and the
Lubricants Gross Margin % KPI carried neither — so DA fell through to raw
per-segment deltas and the UI added them up anyway.

Two independent things are pinned here:
  1. the arithmetic itself, so nobody "simplifies" the weighting away;
  2. `deltas_are_contributions`, which must default False so an unmarked payload
     is never summed by accident.
"""
from __future__ import annotations

import pytest

from src.agents.models.deep_analysis_models import KTIsIsNot

# Gross Margin % by product, 2026, from BigQuery (GROUP BY ROLLUP).
# (segment, margin_pct, revenue_millions)
PRODUCT_MARGINS_2026 = [
    ("Conventional Engine Oil", 18.52, 16.3),
    ("Synthetic Blend Engine Oil", 20.04, 20.2),
    ("Manual Gear Oil", 21.26, 5.1),
    ("Hydraulic Oil", 25.22, 6.1),
    ("Compressor Oil", 27.45, 6.1),
    ("Automatic Transmission Fluid", 27.81, 15.9),
    ("Heavy-Duty Coolant", 27.84, 6.2),
    ("Extended Life Coolant", 29.86, 9.1),
    ("Turbine Oil", 31.19, 4.1),
    ("High Mileage Engine Oil", 32.48, 9.8),
    ("Multi-Purpose Grease", 34.76, 14.4),
    ("Full Synthetic Engine Oil", 35.33, 15.9),
    ("High-Temp Bearing Grease", 38.12, 3.9),
    ("Oil Treatment Additive", 41.00, 8.4),
    ("Fuel System Cleaner", 42.07, 11.1),
]
TRUE_ENTERPRISE_MARGIN_2026 = 29.43   # ratio of the summed components


class TestTheSummationFallacy:
    def test_summing_member_percentages_is_wildly_wrong(self):
        """The exact number the header printed, preserved."""
        naive = sum(m for _, m, _ in PRODUCT_MARGINS_2026)
        assert naive == pytest.approx(452.95, abs=0.01)
        assert naive / TRUE_ENTERPRISE_MARGIN_2026 == pytest.approx(15.4, abs=0.1)

    def test_revenue_weighting_recovers_the_true_enterprise_margin(self):
        """The correct aggregation, from the same per-segment numbers.

        This is what the bridge path does: weight each segment's rate by its share
        of the denominator. It is equivalent to SUM(gp)/SUM(rev) and lands on the
        real figure, which is why weighted contributions may be summed and raw
        rates may not.
        """
        total_rev = sum(r for _, _, r in PRODUCT_MARGINS_2026)
        weighted = sum(m * (r / total_rev) for _, m, r in PRODUCT_MARGINS_2026)
        assert weighted == pytest.approx(TRUE_ENTERPRISE_MARGIN_2026, abs=0.15)

    def test_weighted_contributions_sum_to_the_overall_change(self):
        """Deltas, not levels — the case the chart header actually renders.

        Segment rate changes are weighted by revenue share, exactly as
        `_contrib = _rev_share * _rate` does in the DA bridge path.
        """
        # (rate_change_pp, revenue_share)
        segments = [(-7.86, 0.35), (-7.33, 0.25), (-6.77, 0.15), (-4.18, 0.25)]
        raw_sum = sum(rate for rate, _ in segments)
        weighted_sum = sum(rate * share for rate, share in segments)

        assert sum(share for _, share in segments) == pytest.approx(1.0)
        # The raw sum is the bug: it roughly quadruples the real movement.
        assert raw_sum == pytest.approx(-26.14, abs=0.01)
        assert weighted_sum == pytest.approx(-6.644, abs=0.01)
        assert abs(raw_sum) > abs(weighted_sum) * 3


class TestAdditivityFlagFailsSafe:
    def test_defaults_to_false(self):
        """An unmarked payload must never be summed.

        Every older DA response, and every path where the bridge did not run,
        arrives without this field. Defaulting True would silently restore the bug
        for exactly those cases.
        """
        assert KTIsIsNot().deltas_are_contributions is False

    def test_can_be_set_when_the_bridge_ran(self):
        assert KTIsIsNot(deltas_are_contributions=True).deltas_are_contributions is True

    def test_flag_is_independent_of_having_items(self):
        # An empty IS list with the flag set must not imply a meaningful total;
        # that judgement belongs to the consumer, but the flag must round-trip.
        kt = KTIsIsNot(where_is=[], deltas_are_contributions=True)
        assert kt.deltas_are_contributions is True
        assert kt.where_is == []


class TestBridgeMetadataIsPresentOnTheSeed:
    """The bridge only runs when the KPI declares it. It silently did not."""

    @pytest.fixture(scope="class")
    def gross_margin_kpi(self):
        from scripts.clients.lubricants import KPIS  # noqa: PLC0415
        for k in KPIS:
            if k.get("id") == "gross_margin_pct":
                return k
        pytest.fail("gross_margin_pct not found in the lubricants seed")

    def test_declares_ratio_type(self, gross_margin_kpi):
        assert gross_margin_kpi["metadata"].get("kpi_type") == "ratio"

    def test_carries_both_bridge_queries(self, gross_margin_kpi):
        md = gross_margin_kpi["metadata"]
        assert md.get("bridge_numerator_sql"), "no numerator SQL — bridge cannot run"
        assert md.get("bridge_denominator_sql"), "no denominator SQL — bridge cannot run"

    def test_bridge_queries_are_full_select_statements(self, gross_margin_kpi):
        """The DPA lifts the expression between SELECT and FROM, so a bare
        aggregate expression would silently produce no usable SQL."""
        md = gross_margin_kpi["metadata"]
        for key in ("bridge_numerator_sql", "bridge_denominator_sql"):
            sql = md[key].upper()
            assert sql.strip().startswith("SELECT"), f"{key} must be a full SELECT"
            assert " FROM " in sql, f"{key} must have a FROM clause"
            assert "GROUP BY" not in sql, (
                f"{key} must NOT group — the DPA adds its own GROUP BY, and an "
                "existing one makes the expression unusable as a scalar measure"
            )

    def test_numerator_is_gross_profit_and_denominator_is_revenue(self, gross_margin_kpi):
        md = gross_margin_kpi["metadata"]
        num = md["bridge_numerator_sql"]
        den = md["bridge_denominator_sql"]
        # Numerator is the SIGNED sum of Revenue+COGS (COGS is stored negative).
        assert "'Revenue', 'COGS'" in num or "'Revenue','COGS'" in num
        # Denominator is revenue alone — the weighting base.
        assert "COGS" not in den, "denominator must be revenue only"
        assert "Revenue" in den
