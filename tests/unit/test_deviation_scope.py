"""Somewhere, or everywhere? (src/analysis/deviation_scope.py and its use in Deep Analysis)

Found live 2026-10-13 on lubricants Net Revenue against plan: all 60 segments in all
ten dimensions were exactly 16.3% below budget, there was no IS NOT, and the analysis
said "the budget gap is driven by Synthetic Blend Engine Oil, Automatic Transmission
Fluid, ...". They were the largest products, not the cause.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.agents.models.deep_analysis_models import ChangePoint, DeepAnalysisResponse
from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
from src.analysis.deviation_scope import assess, describe, is_general, member_stats, shortlist_is_complete


def _diffs(pairs):
    """[(previous, current)] -> diffs rows"""
    return [(f"seg{i}", cur, prev, cur - prev) for i, (prev, cur) in enumerate(pairs)]


UNIFORM = _diffs([(100.0, 83.7), (200.0, 167.4), (50.0, 41.85), (400.0, 334.8)])   # all -16.3%
UNEVEN = _diffs([(100.0, 95.0), (200.0, 150.0), (50.0, 45.0)])                       # -5%, -25%, -10%
MIXED = _diffs([(100.0, 80.0), (200.0, 230.0), (50.0, 40.0)])                        # one up


class TestMemberStats:
    def test_every_member_is_counted_by_direction(self):
        s = member_stats(MIXED, trend_positive=True)
        assert (s["members"], s["adverse"], s["favourable"]) == (3, 2, 1)

    def test_for_a_cost_a_rise_is_the_adverse_direction(self):
        s = member_stats(MIXED, trend_positive=False)
        assert (s["adverse"], s["favourable"]) == (1, 2)

    def test_a_member_with_no_comparison_value_is_left_out(self):
        s = member_stats([("new", 10.0, 0.0, 10.0)] + UNIFORM, trend_positive=True)
        assert s["members"] == 4


class TestAssess:
    def test_the_live_case_is_general_and_uniform(self):
        scope = assess({"product": member_stats(UNIFORM, True), "region": member_stats(UNIFORM[:2], True)})
        assert scope["kind"] == "general_uniform" and scope["direction"] == "adverse"
        assert scope["members_checked"] == 6 and scope["dimensions_checked"] == 2
        assert scope["gap_pct_typical"] == -16.3 and scope["favourable_members"] == 0
        assert is_general(scope)

    def test_everything_down_by_different_amounts_is_general_but_uneven(self):
        scope = assess({"product": member_stats(UNEVEN, True)})
        assert scope["kind"] == "general_uneven"
        assert (scope["gap_pct_min"], scope["gap_pct_max"]) == (-25.0, -5.0)

    def test_one_member_moving_the_other_way_makes_it_localised(self):
        scope = assess({"product": member_stats(UNIFORM, True), "region": member_stats(MIXED, True)})
        assert scope["kind"] == "localised" and not is_general(scope)

    def test_nothing_counted_is_none_not_a_verdict(self):
        assert assess({}) is None and assess(None) is None and assess({"product": {}}) is None

    def test_everywhere_is_not_claimed_while_any_dimension_went_uncounted(self):
        # live: Premium Product Mix %, 5 members counted in 3 dimensions, 7 dimensions Top-N only
        assert assess({"product": member_stats(UNIFORM, True)}, dimensions_not_counted=7) is None

    def test_a_localised_result_stands_on_a_partial_count(self):
        scope = assess({"region": member_stats(MIXED, True)}, dimensions_not_counted=7)
        assert scope["kind"] == "localised" and scope["dimensions_not_counted"] == 7

    def test_everything_up_is_general_in_the_favourable_direction(self):
        up = _diffs([(100.0, 110.0), (200.0, 221.0)])
        scope = assess({"product": member_stats(up, True)})
        assert scope["direction"] == "favourable" and not is_general(scope)   # not a problem to explain


class TestDescribe:
    def test_uniform_against_plan(self):
        text = describe(assess({"product": member_stats(UNIFORM, True)}), against_plan=True)
        assert "all 4 segments checked" in text and "16.3% below plan" in text
        assert "No segment stands out" in text
        assert "a shift in the market, or a plan that was set too high" in text

    def test_against_a_prior_period_the_second_candidate_is_not_the_plan(self):
        text = describe(assess({"product": member_stats(UNIFORM, True)}), against_plan=False)
        assert "below the comparison period" in text and "plan" not in text

    def test_uneven_states_the_range(self):
        text = describe(assess({"product": member_stats(UNEVEN, True)}), against_plan=True)
        assert "by 5.0% to 25.0%" in text and "no segment is unaffected" in text

    def test_localised_or_absent_says_nothing(self):
        assert describe(assess({"product": member_stats(MIXED, True)}), against_plan=True) is None
        assert describe(None, against_plan=True) is None


def _agent() -> A9_Deep_Analysis_Agent:
    a = A9_Deep_Analysis_Agent.__new__(A9_Deep_Analysis_Agent)
    a.logger = __import__("logging").getLogger("t")
    return a


class TestDeepAnalysisUsesIt:
    def test_the_count_covers_members_beyond_the_display_cap(self):
        many = _diffs([(100.0, 84.0)] * 25)
        stats: dict = {}
        shown, healthy = _agent()._select_variance_items(many, max_items=10, trend_positive=True, stats_out=stats)
        assert len(shown) == 10 and healthy == []
        assert stats["members"] == 25 and stats["adverse"] == 25

    def _facts(self, scope, **kw):
        plan = SimpleNamespace(kpi_name="Net Revenue", timeframe="current_quarter")
        kt = SimpleNamespace(where_is=[{"key": "Synthetic Blend Engine Oil"}, {"key": "Automatic Transmission Fluid"}],
                             where_is_not=[])
        cps = [ChangePoint(dimension="customer_region", key="North America", delta=-5735814.9)]
        return _agent()._build_situation_complication_facts(
            plan=plan, kt=kt, change_points=cps, spec={"comparison_type": "budget", "inverse_logic": False},
            analysis_mode="problem", alert_type="plan_variance", deviation_scope=scope, **kw)

    def test_a_general_gap_is_stated_and_no_segment_is_called_a_driver(self):
        scope = assess({"product_name": member_stats(UNIFORM, True)})
        text = self._facts(scope)
        assert "The gap is across the board" in text and "No segment stands out" in text
        assert "a shift in the market, or a plan that was set too high" in text
        assert "driven by" not in text and "Key drivers" not in text
        assert "Largest segments by size (extent, not cause): Customer Region: North America (-5.7M)" in text
        assert "Question:" not in text and "Answer:" not in text      # still facts only

    def test_a_localised_gap_reads_as_before(self):
        text = self._facts(assess({"product_name": member_stats(MIXED, True)}))
        assert "the budget gap driven by" in text and "Key drivers:" in text

    def test_with_nothing_counted_the_text_is_unchanged(self):
        assert self._facts(None) == self._facts(assess({}))
        assert "Key drivers:" in self._facts(None)

    def test_the_response_carries_the_assessment(self):
        assert "deviation_scope" in DeepAnalysisResponse.model_fields


class TestShortlistIsComplete:
    """A "top 50 movers" result that came back short of 50 is the whole dimension."""

    def test_fewer_rows_than_asked_for_is_the_whole_dimension(self):
        assert shortlist_is_complete(16, 50, 0, trend_positive=True)

    def test_a_full_page_may_have_been_cut_off(self):
        assert not shortlist_is_complete(50, 50, 0, trend_positive=True)

    def test_a_dropped_row_is_a_member_not_seen(self):
        assert not shortlist_is_complete(16, 50, 1, trend_positive=True)

    def test_no_rows_is_nothing_to_count(self):
        assert not shortlist_is_complete(0, 50, 0, trend_positive=True)

    def test_a_cost_is_never_counted_from_a_shortlist(self):
        # a member with a value last period and none now is missing from the query;
        # for a cost that member improved, and leaving it out could fake "everywhere"
        assert not shortlist_is_complete(16, 50, 0, trend_positive=False)

    def test_the_live_case_now_reads_localised(self):
        # Premium Product Mix %: Fleet Customer C down, Independent Service Centers up
        customers = [("Independent Service Centers", 14.03, 7.71, 6.32), ("Fleet Customer C", 17.81, 23.23, -5.42)]
        scope = assess({"customer_name": member_stats(customers, True)}, dimensions_not_counted=0)
        assert scope["kind"] == "localised"
