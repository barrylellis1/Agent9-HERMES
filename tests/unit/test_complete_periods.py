"""Complete periods only, for data keyed by period (src/analysis/complete_periods.py).

Found live 2026-10-13 on lubricants: the situation card sliced period-keyed data to the
day (1-13 Oct against 1-13 Oct), Deep Analysis worked in whole periods, and for Premium
Product Mix % one said it fell and the other said it rose.
"""
from __future__ import annotations

from datetime import date
from unittest.mock import patch

from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent as SA
from src.analysis.complete_periods import as_of, closed_view, is_period_keyed, last_closed_day
from src.database.time_filter import TimeFilter

TODAY = date(2026, 10, 13)
PERIOD = {"type": "fiscal_year_period", "year_column": "fiscal_year", "period_column": "fiscal_period", "column": ""}
DATED = {"type": "date", "column": "transaction_date"}


class TestWhichKind:
    def test_the_declared_type_decides(self):
        assert is_period_keyed(PERIOD) and is_period_keyed({"type": "fiscal_year", "year_column": "fy"})
        assert not is_period_keyed(DATED) and not is_period_keyed(None) and not is_period_keyed({})

    def test_a_date_spec_with_only_a_year_column_is_period_keyed(self):
        assert is_period_keyed({"type": "date", "column": "", "year_column": "fiscal_year"})

    def test_as_of_is_the_last_closed_day_or_the_real_today(self):
        assert as_of(PERIOD, TODAY) == date(2026, 9, 30)
        assert as_of(DATED, TODAY) is None

    def test_january_closes_back_into_december(self):
        assert last_closed_day(date(2027, 1, 5)) == date(2026, 12, 31)


class TestClosedView:
    def test_an_open_period_request_is_read_as_of_the_last_closed_day(self):
        assert closed_view("current_quarter", TODAY) == ("quarter_to_date", date(2026, 9, 30))
        assert closed_view("year_to_date", TODAY) == ("year_to_date", date(2026, 9, 30))
        assert closed_view("this_month", TODAY) == ("month_to_date", date(2026, 9, 30))

    def test_a_request_that_names_a_closed_period_is_unchanged(self):
        assert closed_view("last_quarter", TODAY) == ("last_quarter", TODAY)
        assert closed_view("last_month", TODAY) == ("last_month", TODAY)


class TestBothStagesOnPeriodKeyedData:
    """The card (dates) and the analysis (year + period) name the same closed periods."""

    def _analysis(self, token):
        with patch("src.database.time_filter.TimeFilter._today", return_value=TODAY):
            return TimeFilter.current_condition(PERIOD, token), TimeFilter.previous_condition(PERIOD, token)

    def _card(self, token):
        a = as_of(PERIOD, TODAY)
        return SA._bq_get_period_dates(token, as_of=a), SA._bq_get_period_dates(token, True, "year_over_year", as_of=a)

    def test_this_quarter_is_the_last_closed_quarter_when_no_month_of_it_has_closed(self):
        assert self._card("current_quarter") == (("2026-07-01", "2026-09-30"), ("2025-07-01", "2025-09-30"))
        assert self._analysis("current_quarter") == (
            "fiscal_year = 2026 AND fiscal_period BETWEEN 7 AND 9",
            "fiscal_year = 2025 AND fiscal_period BETWEEN 7 AND 9",
        )

    def test_year_to_date_stops_at_the_last_closed_month(self):
        assert self._card("year_to_date") == (("2026-01-01", "2026-09-30"), ("2025-01-01", "2025-09-30"))
        assert self._analysis("year_to_date") == (
            "fiscal_year = 2026 AND fiscal_period <= 9", "fiscal_year = 2025 AND fiscal_period <= 9",
        )

    def test_this_month_is_the_last_closed_month(self):
        assert self._card("current_month") == (("2026-09-01", "2026-09-30"), ("2025-09-01", "2025-09-30"))
        assert self._analysis("current_month") == (
            "fiscal_year = 2026 AND fiscal_period = 9", "fiscal_year = 2025 AND fiscal_period = 9",
        )

    def test_once_a_month_of_the_quarter_has_closed_the_quarter_is_that_month(self):
        nov = date(2026, 11, 13)
        a = as_of(PERIOD, nov)
        assert SA._bq_get_period_dates("current_quarter", as_of=a) == ("2026-10-01", "2026-10-31")
        with patch("src.database.time_filter.TimeFilter._today", return_value=nov):
            assert TimeFilter.current_condition(PERIOD, "current_quarter") == "fiscal_year = 2026 AND fiscal_period BETWEEN 10 AND 10"

    def test_month_over_month_now_compares_two_whole_months(self):
        a = as_of(PERIOD, TODAY)
        assert SA._bq_get_period_dates("current_month", True, "month_over_month", as_of=a) == ("2026-08-01", "2026-08-31")


class TestDateKeyedDataIsStillToTheDay:
    def test_the_card_reads_to_today(self):
        cur = SA._bq_get_period_dates("current_quarter", as_of=date(2026, 10, 13))
        assert cur == ("2026-10-01", "2026-10-13")

    def test_the_shared_helper_does_not_shift_a_dated_product(self):
        with patch("src.database.time_filter.TimeFilter._today", return_value=TODAY):
            assert TimeFilter.current_condition(DATED, "quarter_to_date", dialect="snowflake") == \
                "transaction_date BETWEEN '2026-10-01' AND '2026-10-13'"


def test_the_29th_of_february_compares_with_the_28th():
    assert SA._bq_get_period_dates("current_month", True, "year_over_year", as_of=date(2028, 2, 29)) == ("2027-02-01", "2027-02-28")
