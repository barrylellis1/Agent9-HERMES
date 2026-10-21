"""A cost is over budget when its amount is larger than budgeted, whichever sign the data uses.

Found 2026-10-21 in the owner's card review and verified against each warehouse's raw amounts:
lubricants and Apex report Cost of Goods Sold as a positive amount (their SQL negates the raw
debits); Hess reports its costs as the raw negative amounts. The budget check assumed negative
costs, so lubricants COGS, 9.8% under budget, was carded as above plan, and Apex COGS, 117.6% over,
as below. The comparison with last year already handled both (it flips only a negative value).
"""
import pytest

from src.agents.new.a9_situation_awareness_agent import _budget_breach_level, _over_budget


@pytest.mark.parametrize("actual, budget, expected", [
    (82_541_368, 91_553_176, False),      # lubricants COGS, positive amounts: 9.8% under budget
    (79_517_475, 36_549_786, True),       # Apex COGS, positive amounts: 117.6% over budget
    (-139_110_152, -144_180_607, False),  # Hess SG&A, negative amounts: 3.5% under budget
    (-150_000_000, -144_180_607, True),   # Hess SG&A, negative amounts, over budget
])
def test_a_cost_is_over_budget_when_its_amount_is_larger(actual, budget, expected):
    assert _over_budget(actual, budget, lower_is_better=True) is expected


@pytest.mark.parametrize("actual, budget, expected", [
    (117_837_622, 140_576_100, True),     # lubricants Net Revenue: 16.2% short of budget
    (150_000_000, 140_576_100, False),
])
def test_revenue_is_short_when_below_budget(actual, budget, expected):
    assert _over_budget(actual, budget, lower_is_better=False) is expected


def test_the_projection_level_for_each_convention():
    # a cost reported as a positive amount breaches by rising above budget plus the tolerance
    assert _budget_breach_level(10_000_000, 0.05, lower_is_better=True) == (10_500_000, True)
    # a cost stored as a negative amount breaches by falling below (more negative than) budget
    assert _budget_breach_level(-10_000_000, 0.05, lower_is_better=True) == (-10_500_000, False)
    # revenue breaches by falling below budget less the tolerance
    assert _budget_breach_level(10_000_000, 0.05, lower_is_better=False) == (9_500_000, False)


def test_a_rising_positive_cost_is_projected_to_breach_and_a_falling_one_is_not():
    import logging
    from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent as SA
    sa = SA.__new__(SA)
    sa.logger = logging.getLogger("t")
    level, rising = _budget_breach_level(100.0, 0.05, lower_is_better=True)
    up = [{"period": f"2026-{m:02d}", "value": 95.0 + 2 * m} for m in range(1, 7)]
    down = [{"period": f"2026-{m:02d}", "value": 110.0 - 2 * m} for m in range(1, 7)]
    assert sa._project_trend(up, {"red": level}, inverse_logic=rising) is not None
    assert sa._project_trend(down, {"red": level}, inverse_logic=rising) is None
