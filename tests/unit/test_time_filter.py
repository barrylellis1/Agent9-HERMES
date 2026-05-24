"""Unit tests for TimeFilter — Phase 10F Uniform Time Dimension Layer.

Tests cover all three spec types × all relevant timeframes × all SQL dialects.
TimeFilter._today() is monkeypatched to a fixed date (2026-05-15, a Friday in Q2).
"""

from datetime import date
from unittest.mock import patch
import pytest

from src.database.time_filter import TimeFilter

# Fixed reference date: 2026-05-15 (Q2: April–June, month 5)
_TODAY = date(2026, 5, 15)
_PATCH = "src.database.time_filter.TimeFilter._today"


# ── Helpers ──────────────────────────────────────────────────────────────────

def cur(spec, tf, dialect="bigquery"):
    with patch(_PATCH, return_value=_TODAY):
        return TimeFilter.current_condition(spec, tf, dialect=dialect)


def prev(spec, tf, dialect="bigquery"):
    with patch(_PATCH, return_value=_TODAY):
        return TimeFilter.previous_condition(spec, tf, dialect=dialect)


# ── fiscal_year_period specs ──────────────────────────────────────────────────

FYP = {"type": "fiscal_year_period", "year_column": "fiscal_year", "period_column": "fiscal_period"}


class TestFiscalYearPeriodCurrent:
    def test_current_quarter(self):
        # Q2 2026 = periods 4-6
        assert cur(FYP, "current_quarter") == "fiscal_year = 2026 AND fiscal_period BETWEEN 4 AND 6"

    def test_this_quarter_alias(self):
        assert cur(FYP, "this_quarter") == cur(FYP, "current_quarter")

    def test_quarter_to_date(self):
        # Q2 starts at period 4; today is period 5
        assert cur(FYP, "quarter_to_date") == "fiscal_year = 2026 AND fiscal_period BETWEEN 4 AND 5"

    def test_current_year(self):
        assert cur(FYP, "current_year") == "fiscal_year = 2026"

    def test_this_year_alias(self):
        assert cur(FYP, "this_year") == "fiscal_year = 2026"

    def test_year_to_date(self):
        # Up to period 5 (May)
        assert cur(FYP, "year_to_date") == "fiscal_year = 2026 AND fiscal_period <= 5"

    def test_current_month(self):
        assert cur(FYP, "current_month") == "fiscal_year = 2026 AND fiscal_period = 5"

    def test_this_month_alias(self):
        assert cur(FYP, "this_month") == cur(FYP, "current_month")

    def test_month_to_date(self):
        assert cur(FYP, "month_to_date") == "fiscal_year = 2026 AND fiscal_period = 5"

    def test_last_quarter(self):
        # Q1 2026 = periods 1-3
        assert cur(FYP, "last_quarter") == "fiscal_year = 2026 AND fiscal_period BETWEEN 1 AND 3"

    def test_last_year(self):
        assert cur(FYP, "last_year") == "fiscal_year = 2025"

    def test_last_month(self):
        # April 2026 = period 4
        assert cur(FYP, "last_month") == "fiscal_year = 2026 AND fiscal_period = 4"

    def test_unknown_returns_none(self):
        assert cur(FYP, "last_90_days") is None

    def test_custom_column_names(self):
        spec = {"type": "fiscal_year_period", "year_column": "gjahr", "period_column": "monat"}
        assert cur(spec, "current_year") == "gjahr = 2026"
        assert cur(spec, "current_quarter") == "gjahr = 2026 AND monat BETWEEN 4 AND 6"


class TestFiscalYearPeriodPrevious:
    def test_prev_current_quarter(self):
        # previous of Q2 = Q1 2026
        assert prev(FYP, "current_quarter") == "fiscal_year = 2026 AND fiscal_period BETWEEN 1 AND 3"

    def test_prev_quarter_to_date(self):
        # same as prev of current_quarter
        assert prev(FYP, "quarter_to_date") == "fiscal_year = 2026 AND fiscal_period BETWEEN 1 AND 3"

    def test_prev_current_year(self):
        assert prev(FYP, "current_year") == "fiscal_year = 2025"

    def test_prev_year_to_date(self):
        assert prev(FYP, "year_to_date") == "fiscal_year = 2025"

    def test_prev_current_month(self):
        # previous of May = April
        assert prev(FYP, "current_month") == "fiscal_year = 2026 AND fiscal_period = 4"

    def test_prev_last_quarter(self):
        # two quarters back from Q2 = Q4 2025
        assert prev(FYP, "last_quarter") == "fiscal_year = 2025 AND fiscal_period BETWEEN 10 AND 12"

    def test_prev_last_year(self):
        assert prev(FYP, "last_year") == "fiscal_year = 2024"

    def test_prev_last_month(self):
        # two months back from May = March
        assert prev(FYP, "last_month") == "fiscal_year = 2026 AND fiscal_period = 3"


class TestFiscalYearPeriodQ1Wraparound:
    """Test quarter wraparound when today falls in Q1."""

    _Q1_TODAY = date(2026, 2, 15)

    def test_prev_last_quarter_from_q1(self):
        # today is Q1 2026; last_quarter = Q4 2025; two-back = Q3 2025
        with patch(_PATCH, return_value=self._Q1_TODAY):
            result = TimeFilter.previous_condition(FYP, "last_quarter")
        assert result == "fiscal_year = 2025 AND fiscal_period BETWEEN 7 AND 9"

    def test_last_quarter_from_q1(self):
        # last_quarter from Q1 2026 = Q4 2025
        with patch(_PATCH, return_value=self._Q1_TODAY):
            result = TimeFilter.current_condition(FYP, "last_quarter")
        assert result == "fiscal_year = 2025 AND fiscal_period BETWEEN 10 AND 12"


# ── fiscal_year specs ─────────────────────────────────────────────────────────

FY = {"type": "fiscal_year", "year_column": "fiscal_year"}


class TestFiscalYearCurrent:
    def test_current_year(self):
        assert cur(FY, "current_year") == "fiscal_year = 2026"

    def test_year_to_date(self):
        assert cur(FY, "year_to_date") == "fiscal_year = 2026"

    def test_current_quarter(self):
        # best approximation for fiscal_year type
        assert cur(FY, "current_quarter") == "fiscal_year = 2026"

    def test_last_year(self):
        assert cur(FY, "last_year") == "fiscal_year = 2025"

    def test_last_quarter_q2(self):
        # last quarter from Q2 stays in same year
        assert cur(FY, "last_quarter") == "fiscal_year = 2026"

    def test_last_quarter_q1(self):
        # last quarter from Q1 wraps to previous year
        with patch(_PATCH, return_value=date(2026, 2, 15)):
            result = TimeFilter.current_condition(FY, "last_quarter")
        assert result == "fiscal_year = 2025"


class TestFiscalYearPrevious:
    def test_prev_current_year(self):
        assert prev(FY, "current_year") == "fiscal_year = 2025"

    def test_prev_last_year(self):
        assert prev(FY, "last_year") == "fiscal_year = 2024"


# ── date type specs ───────────────────────────────────────────────────────────

DATE_BQ = {"type": "date", "column": "posting_date"}
DATE_SF = {"type": "date", "column": "posting_date"}


class TestDateTypeCurrent:
    def test_current_quarter_bigquery(self):
        result = cur(DATE_BQ, "current_quarter", dialect="bigquery")
        assert result == "`posting_date` BETWEEN '2026-04-01' AND '2026-06-30'"

    def test_current_quarter_snowflake(self):
        result = cur(DATE_SF, "current_quarter", dialect="snowflake")
        assert result == "posting_date BETWEEN '2026-04-01' AND '2026-06-30'"

    def test_last_quarter(self):
        # Q1 2026 = Jan 1 – Mar 31
        result = cur(DATE_BQ, "last_quarter")
        assert result == "`posting_date` BETWEEN '2026-01-01' AND '2026-03-31'"

    def test_current_year(self):
        result = cur(DATE_BQ, "current_year")
        assert result == "`posting_date` BETWEEN '2026-01-01' AND '2026-12-31'"

    def test_last_year(self):
        result = cur(DATE_BQ, "last_year")
        assert result == "`posting_date` BETWEEN '2025-01-01' AND '2025-12-31'"

    def test_year_to_date(self):
        result = cur(DATE_BQ, "year_to_date")
        assert result == "`posting_date` BETWEEN '2026-01-01' AND '2026-05-15'"

    def test_current_month(self):
        result = cur(DATE_BQ, "current_month")
        assert result == "`posting_date` BETWEEN '2026-05-01' AND '2026-05-31'"

    def test_last_month(self):
        result = cur(DATE_BQ, "last_month")
        assert result == "`posting_date` BETWEEN '2026-04-01' AND '2026-04-30'"

    def test_unknown_returns_none(self):
        result = cur(DATE_BQ, "all_time")
        assert result is None


class TestDateTypePrevious:
    def test_prev_current_quarter(self):
        # prev of Q2 = Q1
        result = prev(DATE_BQ, "current_quarter")
        assert result == "`posting_date` BETWEEN '2026-01-01' AND '2026-03-31'"

    def test_prev_current_year(self):
        result = prev(DATE_BQ, "current_year")
        assert result == "`posting_date` BETWEEN '2025-01-01' AND '2025-12-31'"

    def test_prev_last_quarter(self):
        # two quarters back from Q2 = Q4 2025
        result = prev(DATE_BQ, "last_quarter")
        assert result == "`posting_date` BETWEEN '2025-10-01' AND '2025-12-31'"

    def test_prev_last_year(self):
        result = prev(DATE_BQ, "last_year")
        assert result == "`posting_date` BETWEEN '2024-01-01' AND '2024-12-31'"

    def test_prev_current_month(self):
        # prev of May = April
        result = prev(DATE_BQ, "current_month")
        assert result == "`posting_date` BETWEEN '2026-04-01' AND '2026-04-30'"

    def test_prev_last_month(self):
        # prev of April = March
        result = prev(DATE_BQ, "last_month")
        assert result == "`posting_date` BETWEEN '2026-03-01' AND '2026-03-31'"


# ── date_range helper ─────────────────────────────────────────────────────────

class TestDateRange:
    def test_current(self):
        with patch(_PATCH, return_value=_TODAY):
            s, e = TimeFilter.date_range(DATE_BQ, "current_quarter")
        assert s == "2026-04-01" and e == "2026-06-30"

    def test_previous(self):
        with patch(_PATCH, return_value=_TODAY):
            s, e = TimeFilter.date_range(DATE_BQ, "current_quarter", previous=True)
        assert s == "2026-01-01" and e == "2026-03-31"

    def test_fiscal_type_returns_none(self):
        with patch(_PATCH, return_value=_TODAY):
            s, e = TimeFilter.date_range(FYP, "current_quarter")
        assert s is None and e is None


# ── append_condition helper ───────────────────────────────────────────────────

class TestAppendCondition:
    def test_no_existing_where(self):
        sql = "SELECT SUM(revenue) AS value FROM `tbl`"
        result = TimeFilter.append_condition(sql, "fiscal_year = 2026")
        assert result.endswith(" WHERE fiscal_year = 2026")

    def test_existing_where(self):
        sql = "SELECT SUM(revenue) AS value FROM `tbl` WHERE client = 'X'"
        result = TimeFilter.append_condition(sql, "fiscal_year = 2026")
        assert "AND fiscal_year = 2026" in result

    def test_none_condition(self):
        sql = "SELECT 1"
        assert TimeFilter.append_condition(sql, None) == sql


# ── previous_period_name (DA integration) ────────────────────────────────────

class TestPreviousPeriodName:
    def test_current_quarter(self):
        assert TimeFilter.previous_period_name("current_quarter") == "last_quarter"

    def test_this_quarter(self):
        assert TimeFilter.previous_period_name("this_quarter") == "last_quarter"

    def test_current_year(self):
        assert TimeFilter.previous_period_name("current_year") == "last_year"

    def test_year_to_date(self):
        assert TimeFilter.previous_period_name("year_to_date") == "last_year"

    def test_current_month(self):
        assert TimeFilter.previous_period_name("current_month") == "last_month"

    def test_last_quarter_passthrough(self):
        assert TimeFilter.previous_period_name("last_quarter") == "last_quarter"

    def test_unknown_returns_none(self):
        assert TimeFilter.previous_period_name("all_time") is None


# ── Non-January fiscal year (fiscal_year_start_month=4, April) ───────────────
# Reference date: 2026-05-15 → FY 2026, fiscal period 2 (May = month 2 of April-start FY)
# Fiscal Q1 = periods 1-3 (April/May/June)

FYP_APR = {
    "type": "fiscal_year_period",
    "year_column": "fiscal_year",
    "period_column": "fiscal_period",
    "fiscal_year_start_month": 4,
}


class TestAprilFiscalYearCurrent:
    def test_current_quarter_is_fiscal_q1(self):
        # Calendar May → FY 2026 Q1 = periods 1-3
        assert cur(FYP_APR, "current_quarter") == "fiscal_year = 2026 AND fiscal_period BETWEEN 1 AND 3"

    def test_quarter_to_date(self):
        # Q1 start = period 1; today = period 2
        assert cur(FYP_APR, "quarter_to_date") == "fiscal_year = 2026 AND fiscal_period BETWEEN 1 AND 2"

    def test_current_year(self):
        assert cur(FYP_APR, "current_year") == "fiscal_year = 2026"

    def test_year_to_date(self):
        # Up to fiscal period 2 (May)
        assert cur(FYP_APR, "year_to_date") == "fiscal_year = 2026 AND fiscal_period <= 2"

    def test_current_month(self):
        # May = fiscal period 2
        assert cur(FYP_APR, "current_month") == "fiscal_year = 2026 AND fiscal_period = 2"

    def test_last_quarter(self):
        # fiscal Q4 of FY 2025 = periods 10-12 (Jan/Feb/Mar 2026)
        assert cur(FYP_APR, "last_quarter") == "fiscal_year = 2025 AND fiscal_period BETWEEN 10 AND 12"

    def test_last_year(self):
        assert cur(FYP_APR, "last_year") == "fiscal_year = 2025"

    def test_last_month(self):
        # fiscal period 1 = April 2026
        assert cur(FYP_APR, "last_month") == "fiscal_year = 2026 AND fiscal_period = 1"


class TestAprilFiscalYearPrevious:
    def test_prev_current_quarter(self):
        # prev of fiscal Q1 = fiscal Q4 of FY 2025
        assert prev(FYP_APR, "current_quarter") == "fiscal_year = 2025 AND fiscal_period BETWEEN 10 AND 12"

    def test_prev_year_to_date(self):
        assert prev(FYP_APR, "year_to_date") == "fiscal_year = 2025"

    def test_prev_current_month(self):
        # prev of fiscal period 2 = fiscal period 1
        assert prev(FYP_APR, "current_month") == "fiscal_year = 2026 AND fiscal_period = 1"

    def test_prev_last_year(self):
        assert prev(FYP_APR, "last_year") == "fiscal_year = 2024"


class TestAprilFiscalYearJanuary:
    """January in an April-start FY falls in the PREVIOUS fiscal year (FY 2025, period 10)."""

    _JAN = date(2026, 1, 15)

    def test_current_month_jan_in_prev_fy(self):
        with patch(_PATCH, return_value=self._JAN):
            result = TimeFilter.current_condition(FYP_APR, "current_month")
        assert result == "fiscal_year = 2025 AND fiscal_period = 10"

    def test_current_quarter_jan_is_fiscal_q4(self):
        # Jan 2026 = FY 2025 Q4 = periods 10-12
        with patch(_PATCH, return_value=self._JAN):
            result = TimeFilter.current_condition(FYP_APR, "current_quarter")
        assert result == "fiscal_year = 2025 AND fiscal_period BETWEEN 10 AND 12"


# ── Databricks dialect ────────────────────────────────────────────────────────

DATE_DB = {"type": "date", "column": "posting_date"}


class TestDatabricksDialect:
    def test_date_no_backticks(self):
        # Databricks uses standard SQL — column must NOT be backtick-quoted
        result = cur(DATE_DB, "current_quarter", dialect="databricks")
        assert "`" not in result
        assert "posting_date BETWEEN" in result

    def test_date_current_quarter(self):
        # Q2 2026 = April 1 – June 30
        result = cur(DATE_DB, "current_quarter", dialect="databricks")
        assert result == "posting_date BETWEEN '2026-04-01' AND '2026-06-30'"

    def test_fyp_dialect_ignored(self):
        # fiscal_year_period is pure integer arithmetic — dialect has no effect
        result_db = cur(FYP, "year_to_date", dialect="databricks")
        result_bq = cur(FYP, "year_to_date", dialect="bigquery")
        assert result_db == result_bq == "fiscal_year = 2026 AND fiscal_period <= 5"

    def test_prev_date_no_backticks(self):
        result = prev(DATE_DB, "current_quarter", dialect="databricks")
        assert "`" not in result
        assert "posting_date BETWEEN" in result
