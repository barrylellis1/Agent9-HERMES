"""Phase 26 step 3a: a comparison passed as a timeframe token, and TimeFilter resolving it.

src/analysis/period_comparisons.py (token, parse_token, from_request, legacy_word, basis_key,
spans_at) and src/database/time_filter.py.
"""
from __future__ import annotations

from datetime import date

import pytest

from src.analysis.period_comparisons import (
    COMPARISONS, ComparisonNotAvailable, basis_key, from_request, legacy_word, parse_token, spans,
    spans_at, token,
)
from src.database.time_filter import TimeFilter

FYP = {"type": "fiscal_year_period", "year_column": "fiscal_year", "period_column": "fiscal_period"}
DATE = {"type": "date", "column": "transaction_date"}


class TestToken:
    def test_round_trip(self):
        assert token("ytd_vs_pytd") == "ytd_vs_pytd"
        assert token("ytd_vs_pytd", date(2026, 7, 31)) == "ytd_vs_pytd@2026-07-31"
        assert parse_token("ytd_vs_pytd@2026-07-31") == ("ytd_vs_pytd", date(2026, 7, 31))
        assert parse_token("QTD_VS_PY_QTD") == ("qtd_vs_py_qtd", None)

    @pytest.mark.parametrize("value", ["year_to_date", "yoy", "current_quarter", "", None, "ytd_vs_pytd@not-a-day"])
    def test_old_words_are_not_tokens(self, value):
        assert parse_token(value) is None

    def test_an_unknown_comparison_cannot_be_made_a_token(self):
        with pytest.raises(ValueError):
            token("rolling_90")


class TestOldRequests:
    @pytest.mark.parametrize("tf, ct, keyed, expected", [
        ("year_to_date", "year_over_year", True, "ytd_vs_pytd"),     # what the dashboard sends
        ("year_to_date", None, False, "ytd_vs_pytd"),
        ("current_year", "year_over_year", True, "ytd_vs_pytd"),
        ("current_quarter", "year_over_year", True, "qtd_vs_py_qtd"),  # the route's default
        ("quarter_to_date", "quarter_over_quarter", False, "qtd_vs_prev_qtd"),
        ("current_month", "year_over_year", False, "mtd_vs_py_mtd"),
        ("current_month", "month_over_month", False, "mtd_vs_prev_mtd"),
        ("current_month", "year_over_year", True, "month_vs_py_month"),  # closed month
        ("month_to_date", "month_over_month", True, "month_vs_prev_month"),
        ("last_quarter", "year_over_year", True, "quarter_vs_py_quarter"),
        ("last_quarter", "quarter_over_quarter", True, "quarter_vs_prev_quarter"),
        ("last_month", "month_over_month", True, "month_vs_prev_month"),
        ("last_year", "year_over_year", True, "year_vs_prev_year"),
        ("year_to_date", "budget_vs_actual", True, "ytd_vs_pytd"),    # the version differs, not the period
        ("custom", "year_over_year", True, "quarter_vs_py_quarter"),  # the old default, last quarter
        ("ytd_vs_pytd@2026-07-31", "quarter_over_quarter", True, "ytd_vs_pytd"),  # a token is kept
    ])
    def test_each_maps_to_the_comparison_it_was_read_as(self, tf, ct, keyed, expected):
        assert from_request(tf, ct, keyed) == expected

    def test_the_old_qtd_window_is_the_new_one(self):
        # SA read current_quarter on period-keyed data on 15 Oct as Jul 1 - Sep 30 vs a year earlier
        r = spans(from_request("current_quarter", "year_over_year", True), date(2026, 10, 15), True)
        assert (r.current.start, r.current.end) == (date(2026, 7, 1), date(2026, 9, 30))
        assert (r.previous.start, r.previous.end) == (date(2025, 7, 1), date(2025, 9, 30))

    @pytest.mark.parametrize("c, word", [
        ("ytd_vs_pytd", "year_to_date"), ("qtd_vs_py_qtd", "quarter_to_date"),
        ("quarter_vs_py_quarter", "last_quarter"), ("year_vs_prev_year", "last_year"),
    ])
    def test_legacy_word_for_the_duckdb_builder(self, c, word):
        assert legacy_word(token(c, date(2026, 9, 30))) == word
        assert legacy_word("year_to_date") == "year_to_date"

    def test_basis_key(self):
        assert {c: basis_key(c) for c in COMPARISONS} == {
            "mtd_vs_prev_mtd": "mom", "mtd_vs_py_mtd": "yoy", "qtd_vs_prev_qtd": "qoq", "qtd_vs_py_qtd": "yoy",
            "ytd_vs_pytd": "yoy", "month_vs_prev_month": "mom", "month_vs_py_month": "yoy",
            "quarter_vs_prev_quarter": "qoq", "quarter_vs_py_quarter": "yoy", "year_vs_prev_year": "yoy",
        }


class TestSpansAt:
    def test_matches_spans_when_given_the_same_reference_day(self):
        for c in COMPARISONS:
            if c.startswith("mtd"):
                continue
            a = spans(c, date(2026, 10, 15), True, date(2026, 7, 1))
            assert spans_at(c, a.reference_day, True) == a

    def test_month_to_date_still_refused_on_period_keyed_data(self):
        with pytest.raises(ComparisonNotAvailable):
            spans_at("mtd_vs_py_mtd", date(2026, 9, 30), True)


class TestTimeFilter:
    def test_period_keyed_ytd_matches_the_old_condition(self):
        assert TimeFilter.current_condition(FYP, "ytd_vs_pytd@2026-09-30") == \
            "fiscal_year = 2026 AND fiscal_period BETWEEN 1 AND 9"
        assert TimeFilter.previous_condition(FYP, "ytd_vs_pytd@2026-09-30") == \
            "fiscal_year = 2025 AND fiscal_period BETWEEN 1 AND 9"

    def test_hess_reads_to_the_last_month_with_actuals(self):
        assert TimeFilter.current_condition(FYP, "ytd_vs_pytd@2026-07-31") == \
            "fiscal_year = 2026 AND fiscal_period BETWEEN 1 AND 7"
        assert TimeFilter.current_condition(FYP, "quarter_vs_py_quarter@2026-07-31") == \
            "fiscal_year = 2026 AND fiscal_period BETWEEN 4 AND 6"

    def test_previous_quarter_to_date_can_now_be_expressed(self):
        assert TimeFilter.previous_condition(FYP, "qtd_vs_prev_qtd@2026-08-31") == \
            "fiscal_year = 2026 AND fiscal_period BETWEEN 4 AND 5"

    def test_string_period_columns_are_cast(self):
        spec = dict(FYP, period_column_type="string")
        assert TimeFilter.current_condition(spec, "ytd_vs_pytd@2026-09-30", dialect="sqlserver") == \
            "fiscal_year = 2026 AND CAST(fiscal_period AS INT) BETWEEN 1 AND 9"

    def test_april_fiscal_year(self):
        spec = dict(FYP, fiscal_year_start_month=4)
        assert TimeFilter.current_condition(spec, "ytd_vs_pytd@2026-09-30") == \
            "fiscal_year = 2026 AND fiscal_period BETWEEN 1 AND 6"

    def test_date_keyed(self):
        assert TimeFilter.current_condition(DATE, "ytd_vs_pytd@2026-10-15") == \
            "`transaction_date` BETWEEN '2026-01-01' AND '2026-10-15'"
        assert TimeFilter.previous_condition(DATE, "ytd_vs_pytd@2026-10-15", dialect="snowflake") == \
            "transaction_date BETWEEN '2025-01-01' AND '2025-10-15'"

    def test_annual_data_answers_years_only(self):
        spec = {"type": "fiscal_year", "year_column": "fy"}
        assert TimeFilter.current_condition(spec, "ytd_vs_pytd@2026-09-30") == "fy = 2026"
        assert TimeFilter.previous_condition(spec, "year_vs_prev_year@2026-09-30") == "fy = 2024"
        assert TimeFilter.current_condition(spec, "quarter_vs_py_quarter@2026-09-30") is None

    def test_without_a_reference_day_today_decides(self, monkeypatch):
        monkeypatch.setattr(TimeFilter, "_today", staticmethod(lambda: date(2026, 10, 15)))
        assert TimeFilter.current_condition(FYP, "ytd_vs_pytd") == "fiscal_year = 2026 AND fiscal_period BETWEEN 1 AND 9"
        assert TimeFilter.current_condition(DATE, "ytd_vs_pytd", dialect="duckdb") == \
            "transaction_date BETWEEN '2026-01-01' AND '2026-10-15'"

    def test_month_to_date_on_period_keyed_data_is_refused_not_unfiltered(self):
        with pytest.raises(ComparisonNotAvailable):
            TimeFilter.current_condition(FYP, "mtd_vs_py_mtd@2026-09-30")

    def test_a_token_always_has_a_previous_period(self):
        assert TimeFilter.previous_period_name("ytd_vs_pytd@2026-09-30")
        assert TimeFilter.previous_period_name("year_to_date") == "last_year"

    def test_old_words_are_answered_as_before(self, monkeypatch):
        monkeypatch.setattr(TimeFilter, "_today", staticmethod(lambda: date(2026, 10, 15)))
        assert TimeFilter.current_condition(FYP, "year_to_date") == "fiscal_year = 2026 AND fiscal_period <= 9"
