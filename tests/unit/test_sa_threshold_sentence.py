"""A KPI that moved the right way but fell short of its target says so.

Found live 2026-10-13: "B2B Revenue increased by 3.1% vs prior year" under a problem card.
The KPI is higher-is-better and its target is 5% growth; the card was right and its sentence
gave no reason.
"""
from src.agents.new.a9_situation_awareness_agent import _threshold_sentence as s


def test_growth_short_of_the_growth_target():
    assert s("B2B Revenue", 3.1, False, 5.0, " (Q3)") == \
        "B2B Revenue grew 3.1% vs prior year (Q3), short of the 5.0% growth target"


def test_a_fall_in_a_higher_is_better_kpi_reads_as_before():
    assert s("Gross Profit", -9.5, False, 5.0) == "Gross Profit decreased by 9.5% vs prior year"


def test_a_cost_that_fell_but_not_by_enough():
    assert s("SG&A Expense", -1.0, True, -3.0) == \
        "SG&A Expense fell 1.0% vs prior year, short of the 3.0% reduction target"


def test_a_cost_that_rose_past_its_limit():
    assert s("SG&A Expense", 6.0, True, 2.0) == "SG&A Expense increased by 6.0% vs prior year, above the 2.0% limit"


def test_with_no_target_recorded_the_sentence_is_unchanged():
    assert s("B2B Revenue", 3.1, False, None) == "B2B Revenue increased by 3.1% vs prior year"
    assert s("B2B Revenue", 3.1, False, "n/a") == "B2B Revenue increased by 3.1% vs prior year"
