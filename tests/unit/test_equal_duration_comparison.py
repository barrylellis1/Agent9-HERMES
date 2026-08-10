"""ACTUALS are compared like-for-like: YTD vs prior YTD, never YTD vs full prior year.

THE RULE
--------
A comparison between two Actual periods is only meaningful when the periods are
the SAME LENGTH. Year-to-date against a full prior year compares eight months of
trading with twelve and calls the difference performance.

WHAT WENT WRONG
---------------
`_compute_overall_summary` asked the DPA for `timeframe=prev_tf`, and `prev_tf`
for `year_to_date` is `"last_year"` — a full year. Every dimensional query in the
same method used `cur_tf` with `comparison_period=True`, i.e. prior year-to-date.
One production briefing therefore carried both:

    headline    29.94 vs 32.63  (FY-2025)   -2.69pp / -8.2%
    segments    29.94 vs 34.43  (YTD-2025)  -4.49pp / -13.1%

Confirmed against BigQuery: YTD-2025 = 34.43%, FY-2025 = 32.63%. The 32.63
figure was not wrong — it was the right number for a question nobody asked.

Version comparisons (budget/plan) are a DIFFERENT case and deliberately not
covered by this rule: those hold the window fixed and vary the version, which is
`comparison_basis="version"` in MeasurementContext.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

DA_SOURCE = Path(__file__).resolve().parents[2] / "src" / "agents" / "new" / "a9_deep_analysis_agent.py"


class TestNoCallPassesAPreviousTimeframeToken:
    """Structural guard: the shape of the bug must be unrepresentable in DA.

    An equality assertion on one call site would not have caught this — the wrong
    call was one of several, and the others were correct. What matters is that NO
    query is built from a separate previous-timeframe token.
    """

    @pytest.fixture(scope="class")
    def source(self) -> str:
        return DA_SOURCE.read_text(encoding="utf-8")

    def test_generate_sql_is_never_given_prev_tf_as_its_timeframe(self, source):
        # `timeframe=prev_tf` is the exact defect. The comparison period must be
        # requested with comparison_period=True on the CURRENT timeframe, so the
        # window is the same span shifted back rather than a different span.
        offenders = re.findall(r"timeframe\s*=\s*prev_tf\w*", source)
        assert not offenders, (
            f"{len(offenders)} call(s) build a query from a separate previous-timeframe "
            f"token. For Actuals the comparison must be the SAME timeframe shifted back "
            f"(comparison_period=True), or durations will not match: {offenders}"
        )

    def test_prev_tf_survives_only_as_an_availability_guard(self, source):
        """`if prev_tf:` is legitimate — it asks whether a prior period exists at
        all. Using its VALUE to build a query is not."""
        assert "prev_tf" in source, "guard removed entirely — availability is still worth checking"
        for m in re.finditer(r"prev_tf\w*", source):
            line = source[source.rfind("\n", 0, m.start()) + 1: source.find("\n", m.end())]
            if "timeframe=" in line and "comparison_period" not in line:
                pytest.fail(f"prev_tf used to build a query: {line.strip()}")


class TestLabelsNameTheWindowActuallyMeasured:
    """A label naming a different period than the number is how this hid.

    The headline was labelled "last_year" while measuring prior year-to-date. Both
    the label and the figure looked reasonable; only together were they wrong.
    """

    @pytest.fixture(scope="class")
    def source(self) -> str:
        return DA_SOURCE.read_text(encoding="utf-8")

    def test_timeframe_mapping_derives_previous_from_current(self, source):
        assert '"previous": f"prior {cur_tf_val}"' in source, (
            "timeframe_mapping must describe the comparison as the same timeframe "
            "shifted back, not as a differently-named period"
        )

    def test_comparator_label_derives_from_current_timeframe(self, source):
        assert 'f"prior {cur_tf}"' in source, (
            "comparator_label must name the window measured; it previously said "
            "'last_year' while the query measured prior year-to-date"
        )


class TestTheArithmeticThatMadeItVisible:
    """The two baselines, kept as literals so the gap stays concrete."""

    YTD_2026, YTD_2025, FY_2025 = 29.94, 34.43, 32.63

    def test_equal_duration_comparison_is_the_larger_decline(self):
        like_for_like = self.YTD_2026 - self.YTD_2025
        mismatched = self.YTD_2026 - self.FY_2025
        assert like_for_like == pytest.approx(-4.49, abs=0.01)
        assert mismatched == pytest.approx(-2.69, abs=0.01)
        # The mismatched pair understates the decline by about 40%, which is the
        # difference between a briefing that acts and one that watches.
        assert abs(mismatched) < abs(like_for_like)

    def test_the_percentages_the_two_bases_produce(self):
        assert (self.YTD_2026 - self.YTD_2025) / self.YTD_2025 == pytest.approx(-0.131, abs=0.002)
        assert (self.YTD_2026 - self.FY_2025) / self.FY_2025 == pytest.approx(-0.082, abs=0.002)
