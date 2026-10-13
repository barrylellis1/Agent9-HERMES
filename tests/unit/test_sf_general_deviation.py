"""Solution Finder is told when the gap is everywhere.

Found live 2026-10-13: all 60 lubricants segments were 16.3% below plan, and the
approved option targeted "the Retail Partners decline", one of the larger segments.
"""
from __future__ import annotations

from src.agents.new.a9_solution_finder_agent import (
    _GENERAL_DEVIATION_RULE,
    _extract_deep_analysis_summary,
    _general_deviation_note,
)

GENERAL = {
    "kind": "general_uniform", "direction": "adverse", "dimensions_checked": 10,
    "members_checked": 60, "adverse_members": 60, "favourable_members": 0,
    "gap_pct_typical": -16.3, "gap_pct_min": -16.3, "gap_pct_max": -16.3,
}
LOCALISED = {"kind": "localised", "direction": None, "dimensions_checked": 3,
             "members_checked": 20, "adverse_members": 12, "favourable_members": 8}


def _da(scope, comparator="budget"):
    execution = {
        "status": "success", "comparator": comparator, "deviation_scope": scope,
        "kt_is_is_not": {"where_is": [{"dimension": "product_name", "key": "Synthetic Blend Engine Oil",
                                       "delta": -892525.19, "text": "product_name: Synthetic Blend Engine Oil"}],
                         "where_is_not": []},
        "change_points": [],
    }
    return {"plan": {"kpi_name": "net_revenue", "client_id": "lubricants"}, "execution": execution}


def test_a_general_gap_reaches_the_summary_in_the_readers_words():
    note = _extract_deep_analysis_summary(_da(GENERAL)).get("deviation_is_general")
    assert note and "all 60 segments checked" in note and "16.3% below plan" in note
    assert "a shift in the market, or a plan that was set too high" in note


def test_against_a_prior_period_the_plan_is_not_a_candidate():
    note = _extract_deep_analysis_summary(_da(GENERAL, comparator="previous")).get("deviation_is_general")
    assert note and "plan" not in note


def test_a_localised_or_uncounted_gap_adds_nothing():
    assert "deviation_is_general" not in _extract_deep_analysis_summary(_da(LOCALISED))
    assert "deviation_is_general" not in _extract_deep_analysis_summary(_da(None))


def test_execution_passed_on_its_own_works_too():
    assert _general_deviation_note(_da(GENERAL)["execution"], None)


def test_the_instruction_says_what_matters():
    rule = _GENERAL_DEVIATION_RULE
    assert "NO SEGMENT IS ITS CAUSE" in rule
    assert "extent" in rule and "cause common to the whole business" in rule
    assert "CHECK" in rule and "market" in rule and "plan set too high" in rule


def test_the_rule_is_wired_into_both_prompt_stages():
    """Guards the wiring: the note and the rule must reach Stage 1 and synthesis."""
    import inspect
    import src.agents.new.a9_solution_finder_agent as sf
    src = inspect.getsource(sf)
    assert 'da_compact_s1["how_to_read_the_segments"] = _GENERAL_DEVIATION_RULE' in src
    assert "dataset_recap_lines.append(_GENERAL_DEVIATION_RULE)" in src
    assert "Largest segments by size (extent, not cause)" in src


class TestMarketShiftLine:
    def test_not_asked_says_nothing(self):
        from src.agents.new.a9_solution_finder_agent import _market_shift_line
        assert _market_shift_line({}) is None and _market_shift_line({"market_shift": None}) is None
        assert _market_shift_line("text") is None

    def test_an_unsourced_answer_is_passed_on_as_unsettled(self):
        from src.agents.new.a9_solution_finder_agent import _market_shift_line
        line = _market_shift_line({"market_shift": {
            "assessment": "insufficient", "grounded": False, "summary": "No sourced market evidence was available.",
            "unsourced_assessment": "supported", "unsourced_summary": "Demand fell."}})
        assert "NOT SETTLED" in line and "No sourced market evidence" in line
        assert "supported" not in line and "Demand fell" not in line

    def test_a_sourced_answer_is_passed_on_as_given(self):
        from src.agents.new.a9_solution_finder_agent import _market_shift_line
        line = _market_shift_line({"market_shift": {
            "assessment": "not_supported", "grounded": True, "summary": "Industry volumes were steady."}})
        assert "not_supported, on cited sources. Industry volumes were steady." in line
