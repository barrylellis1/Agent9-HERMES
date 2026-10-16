"""Deep Analysis analyses the period the situation card was measured over.

Found live 2026-10-13: the B2B Revenue card said "up 1.8% vs prior year" (2026-10-01..13
against 2025-10-01..13) and Deep Analysis, asked about that card with the same token,
compared the whole quarter with the whole previous quarter and found every segment down.
"""
from __future__ import annotations

from datetime import date

import pytest

from src.agents.new.a9_deep_analysis_agent import _situation_period
from src.analysis.period_comparisons import from_request, spans
from src.database.time_filter import TimeFilter

SPEC = {"type": "date", "column": "d"}


@pytest.mark.parametrize("token", ["current_quarter", "current_month", "current_year", "year_to_date", "last_quarter"])
def test_both_stages_measure_the_same_two_windows(token):
    r = spans(from_request(token, "year_over_year", False), date.today(), False)
    cur_start, cur_end = r.current.start.isoformat(), r.current.end.isoformat()
    prev_start, prev_end = r.previous.start.isoformat(), r.previous.end.isoformat()
    aligned = _situation_period(token)
    current = TimeFilter.current_condition(SPEC, aligned, dialect="snowflake")
    previous = TimeFilter.previous_condition(SPEC, aligned, dialect="snowflake")
    assert current == f"d BETWEEN '{cur_start}' AND '{cur_end}'"
    if token != "last_quarter":
        assert previous == f"d BETWEEN '{prev_start}' AND '{prev_end}'"


def test_the_untranslated_token_was_a_different_period():
    # the defect: same token, two readings
    if date.today() == TimeFilter._date_range("current_quarter", date.today())[1]:
        pytest.skip("last day of the quarter: to-date and whole quarter coincide")
    assert TimeFilter.previous_condition(SPEC, "current_quarter") != TimeFilter.previous_condition(SPEC, "quarter_to_date")


def test_tokens_that_already_agree_are_left_alone():
    for token in ("year_to_date", "quarter_to_date", "last_quarter", "last_month", "last_year", None):
        assert _situation_period(token) == token


def test_an_enum_token_is_translated_too():
    from src.agents.models.situation_awareness_models import TimeFrame
    assert _situation_period(TimeFrame.CURRENT_QUARTER) == "quarter_to_date"
