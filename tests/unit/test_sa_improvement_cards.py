# arch-allow-direct-agent-construction
"""Improvement cards follow the problem cards' logic and wording (owner, 2026-10-20).

Found live 2026-10-20: improvement cards read the first threshold row listed, whatever its
comparison, so lubricants Net Revenue (+3.1% year to date against a 5.0% target) showed "above
3.0% target", its quarter-on-quarter target; and because an improvement card shared the
threshold-breach dedupe key, it replaced the problem card "grew 3.1%, short of the 5.0% growth
target" on the same KPI.
"""
from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from src.agents.models.situation_awareness_models import (
    KPIValue, MeasurementContext, OpportunitySignal, Situation, SituationSeverity, TimeFrame,
)
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent as SA
from src.agents.new.a9_situation_awareness_agent import _improvement_sentence as s

YTD = MeasurementContext(period_comparison="ytd_vs_pytd", period_short_label="YTD vs PYTD")


class TestSentence:
    def test_growth_above_its_target(self):
        assert s("Midstream Revenue", 5.81, False, 5.0, "YTD vs PYTD") == \
            "Midstream Revenue grew 5.8%, above the 5.0% growth target, YTD vs PYTD"

    def test_a_fall_beyond_a_reduction_target(self):
        assert s("SG&A Expense", -3.92, True, -2.0, "YTD vs PYTD") == \
            "SG&A Expense fell 3.9%, beyond the 2.0% reduction target, YTD vs PYTD"

    def test_a_fall_within_a_limit_on_increases(self):
        assert s("Order Cancellation Rate", -3.61, True, 5.0, "YTD vs PYTD") == \
            "Order Cancellation Rate decreased by 3.6%, YTD vs PYTD"

    def test_growth_where_the_target_only_rules_out_a_decline(self):
        assert s("Average Transaction Value", 2.59, False, 0.0, "YTD vs PYTD") == \
            "Average Transaction Value increased by 2.6%, YTD vs PYTD"

    def test_a_percentage_kpi_states_points(self):
        assert s("Gross Margin %", 3.0, False, 1.0, "YTD vs PYTD", points=1.0) == \
            "Gross Margin % grew 1.0 points (3.0%), above the 1.0% growth target, YTD vs PYTD"


def _sa():
    sa = SA.__new__(SA)
    sa.logger = logging.getLogger("t")
    sa._opportunity_threshold_multiplier = 1.5
    sa._opportunity_recovery_min_delta_pct = 5.0
    return sa


def _kpi(rows, name="Net Revenue", unit="$"):
    # the KPI's own direction flag mirrors its rows' inverse_logic, as the registry seeds it
    lower_is_better = any(r.get("inverse_logic") for r in rows.values())
    return SimpleNamespace(name=name, unit=unit, thresholds={}, positive_trend_is_good=not lower_is_better,
                           metadata={"variance_thresholds": rows})


def _value(pct, name="Net Revenue", ctx=YTD):
    return KPIValue(kpi_name=name, value=100 + pct, comparison_value=100.0, percent_change=pct,
                    timeframe=TimeFrame.YEAR_TO_DATE, context=ctx)


NET_REVENUE = {"ytd_vs_pytd": {"green": 5.0, "inverse_logic": False},
               "quarter_vs_prev_quarter": {"green": 3.0, "inverse_logic": False}}


class TestWhichTarget:
    def test_short_of_the_ytd_target_is_no_improvement_whatever_the_quarter_target(self):
        assert _sa()._detect_opportunities(_kpi(NET_REVENUE), _value(3.1)) == []

    def test_above_the_ytd_target(self):
        [sig] = _sa()._detect_opportunities(_kpi(NET_REVENUE), _value(5.8))
        assert sig.headline == "Net Revenue grew 5.8%, above the 5.0% growth target, YTD vs PYTD"

    def test_no_row_for_the_comparison_read_means_no_improvement(self):
        rows = {"quarter_vs_prev_quarter": {"green": 0.0, "inverse_logic": False}}
        assert _sa()._detect_opportunities(_kpi(rows, "Average Transaction Value"), _value(2.6, "Average Transaction Value")) == []

    def test_a_lower_is_better_kpi_must_meet_its_reduction_target(self):
        rows = {"ytd_vs_pytd": {"green": -2.0, "inverse_logic": True}}
        assert _sa()._detect_opportunities(_kpi(rows, "SG&A Expense"), _value(-1.0, "SG&A Expense")) == []
        [sig] = _sa()._detect_opportunities(_kpi(rows, "SG&A Expense"), _value(-3.92, "SG&A Expense"))
        assert sig.headline == "SG&A Expense fell 3.9%, beyond the 2.0% reduction target, YTD vs PYTD"

    def test_a_rise_within_a_limit_is_not_an_improvement(self):
        rows = {"ytd_vs_pytd": {"green": 5.0, "inverse_logic": True}}
        assert _sa()._detect_opportunities(_kpi(rows, "Order Cancellation Rate"), _value(2.0, "Order Cancellation Rate")) == []

    def test_the_february_fallback_is_judged_on_its_ytd_row(self):
        ctx = MeasurementContext(period_comparison="ltm_vs_prior_ltm", fallback_from="ytd_vs_pytd",
                                 period_short_label="LTM vs Prior LTM")
        [sig] = _sa()._detect_opportunities(_kpi(NET_REVENUE), _value(5.8, ctx=ctx))
        assert sig.headline.endswith("above the 5.0% growth target, LTM vs Prior LTM")


def _card(card_type, severity, alert_type=None):
    kv = _value(3.1)
    return Situation(situation_id=f"{card_type}-{severity.value}", kpi_name="Net Revenue", kpi_value=kv,
                     severity=severity, card_type=card_type, alert_type=alert_type,
                     description="d", business_impact="b")


def test_an_improvement_card_never_replaces_a_problem_card():
    problem = _card("problem", SituationSeverity.MEDIUM, "threshold_breach")
    improvement = _card("opportunity", SituationSeverity.HIGH)
    kept = SA._deduplicate_situations([problem, improvement])
    assert {(c.card_type, c.severity) for c in kept} == {("problem", SituationSeverity.MEDIUM),
                                                         ("opportunity", SituationSeverity.HIGH)}


def test_the_most_severe_card_of_one_pattern_is_kept():
    kept = SA._deduplicate_situations([_card("problem", SituationSeverity.MEDIUM, "threshold_breach"),
                                       _card("problem", SituationSeverity.HIGH, "threshold_breach")])
    assert [c.severity for c in kept] == [SituationSeverity.HIGH]


@pytest.mark.parametrize("pct, expected", [
    (-3.92, "SG&A Expense fell 3.9%, YTD vs PYTD. Deep analysis can identify what drove this "
            "and whether it can be sustained or replicated."),
    (5.81, "SG&A Expense grew 5.8%, YTD vs PYTD, ahead of its target. Deep analysis can identify "
           "the key drivers and determine where to accelerate."),
])
def test_why_it_matters_names_the_comparison_and_no_cost(pct, expected):
    sig = OpportunitySignal(kpi_name="SG&A Expense", kpi_display_name="SG&A Expense", current_value=1.0,
                            baseline_value=1.0, delta_pct=abs(pct), opportunity_type="outperformance",
                            headline="h", confidence=0.75)
    card = Situation.from_opportunity_signal(sig, _value(pct, "SG&A Expense"))
    assert card.business_impact == expected


# ── Problem cards' "Why it matters" names the comparison (owner, 2026-10-20) ──

def _impact(severity, value, comparison, pct, unit="$", name="Net Revenue"):
    from src.agents.models.situation_awareness_models import PrincipalContext
    kv = KPIValue(kpi_name=name, value=value, comparison_value=comparison, percent_change=pct, unit=unit,
                  timeframe=TimeFrame.YEAR_TO_DATE, context=YTD)
    kd = SimpleNamespace(name=name, id="x", diagnostic_questions=None)
    pc = SimpleNamespace(role="CFO")
    return _sa()._create_threshold_situation(kd, kv, severity, "d", pc).business_impact


def test_last_years_figure_is_not_called_the_target():
    text = _impact(SituationSeverity.MEDIUM, 117_800_000, 114_300_000, 3.1)
    assert text == ("Monitor closely: Net Revenue is $117.8M vs $114.3M (+3.1%), YTD vs PYTD, "
                    "showing notable variation from expected values.")
    assert "target $" not in _impact(SituationSeverity.HIGH, 117_800_000, 114_300_000, 3.1)


def test_only_a_currency_kpi_reads_in_dollars():
    text = _impact(SituationSeverity.HIGH, 18_400, 19_900, -7.5, unit="orders", name="Sales Order Count")
    assert text.startswith("Attention needed: Sales Order Count is 18K orders vs 20K orders (-7.5%), YTD vs PYTD")
