"""A KPI that moved the right way but fell short of its target says so.

Found live 2026-10-13: "B2B Revenue increased by 3.1% vs prior year" under a problem card.
The KPI is higher-is-better and its target is 5% growth; the card was right and its sentence
gave no reason.

The sentence ends with the comparison in finance shorthand (owner ruling C, 2026-10-20); it
used to say "vs prior year" and raw dates whatever the comparison was.
"""
from src.agents.new.a9_situation_awareness_agent import _threshold_sentence as s


def test_growth_short_of_the_growth_target():
    assert s("B2B Revenue", 3.1, False, 5.0, "YTD vs PYTD") == \
        "B2B Revenue grew 3.1%, short of the 5.0% growth target, YTD vs PYTD"


def test_a_fall_in_a_higher_is_better_kpi():
    assert s("Gross Profit", -9.5, False, 5.0, "YTD vs PYTD") == "Gross Profit decreased by 9.5%, YTD vs PYTD"


def test_a_cost_that_fell_but_not_by_enough():
    assert s("SG&A Expense", -1.0, True, -3.0, "YTD vs PYTD") == \
        "SG&A Expense fell 1.0%, short of the 3.0% reduction target, YTD vs PYTD"


def test_a_cost_that_rose_past_its_limit():
    assert s("SG&A Expense", 6.0, True, 2.0, "LTM vs Prior LTM") == \
        "SG&A Expense increased by 6.0%, above the 2.0% limit, LTM vs Prior LTM"


def test_with_no_target_recorded_the_sentence_is_unchanged():
    assert s("B2B Revenue", 3.1, False, None, "YTD vs PYTD") == "B2B Revenue increased by 3.1%, YTD vs PYTD"
    assert s("B2B Revenue", 3.1, False, "n/a", "YTD vs PYTD") == "B2B Revenue increased by 3.1%, YTD vs PYTD"


def test_an_unstamped_reading_gains_no_invented_comparison():
    assert s("B2B Revenue", 3.1, False, None) == "B2B Revenue increased by 3.1%"


def test_a_percentage_kpi_states_its_change_in_points():
    # live 2026-10-14: "Gross Margin % decreased by 13.0%" for a fall of 4.48 points
    assert s("Gross Margin %", -13.0, False, 1.0, "YTD vs PYTD", points=-4.48) == \
        "Gross Margin % decreased by 4.5 points (13.0%), YTD vs PYTD"
    assert s("Gross Margin %", 1.2, False, 5.0, "YTD vs PYTD", points=0.4) == \
        "Gross Margin % grew 0.4 points (1.2%), short of the 5.0% growth target, YTD vs PYTD"


def test_points_are_found_only_for_percentage_kpis():
    from types import SimpleNamespace as NS
    from src.agents.new.a9_situation_awareness_agent import _point_change
    gm = NS(name="Gross Margin %", unit="%")
    assert round(_point_change(gm, NS(value=29.95, comparison_value=34.43)), 2) == -4.48
    assert _point_change(NS(name="Net Revenue", unit="$"), NS(value=2.0, comparison_value=1.0)) is None
    assert _point_change(NS(name="Premium Product Mix %", unit=None), NS(value=12.75, comparison_value=13.11, unit=None)) is not None
    assert _point_change(gm, NS(value=29.95, comparison_value=None)) is None


def test_a_tiny_point_change_never_reads_as_zero():
    # live: Premium Product Mix % moved 0.03 points and the card said "0.0 points"
    assert s("Premium Product Mix %", -0.2, False, 1.0, "YTD vs PYTD", points=-0.03) == \
        "Premium Product Mix % decreased by 0.03 points (0.2%), YTD vs PYTD"
