"""The ten named period comparisons (Phase 26, step 1): src/analysis/period_comparisons.py."""
from datetime import date

import pytest

from src.analysis.period_comparisons import (
    COMPARISONS, ComparisonNotAvailable, Span, available, fiscal_periods, reference_day, spans,
)

TODAY = date(2026, 10, 15)


def s(c, today=TODAY, keyed=False, latest=None, fy=1):
    r = spans(c, today, keyed, latest, fy)
    return (r.current.start, r.current.end), (r.previous.start, r.previous.end)


class TestReferenceDay:
    def test_date_keyed_is_today(self):
        assert reference_day(TODAY, period_keyed=False) == TODAY

    def test_period_keyed_is_the_last_closed_day(self):
        assert reference_day(TODAY, period_keyed=True) == date(2026, 9, 30)

    def test_a_period_with_no_actuals_is_not_finished(self):
        # Hess: actuals stop at July 2026
        assert reference_day(TODAY, True, latest_actual=date(2026, 7, 1)) == date(2026, 7, 31)
        assert reference_day(TODAY, False, latest_actual=date(2026, 10, 9)) == date(2026, 10, 9)

    def test_actuals_dated_in_the_future_do_not_move_today(self):
        assert reference_day(TODAY, True, latest_actual=date(2026, 12, 1)) == date(2026, 9, 30)


class TestToDateOnDateKeyedData:
    def test_mtd(self):
        assert s("mtd_vs_prev_mtd") == ((date(2026, 10, 1), TODAY), (date(2026, 9, 1), date(2026, 9, 15)))
        assert s("mtd_vs_py_mtd") == ((date(2026, 10, 1), TODAY), (date(2025, 10, 1), date(2025, 10, 15)))

    def test_qtd(self):
        assert s("qtd_vs_prev_qtd") == ((date(2026, 10, 1), TODAY), (date(2026, 7, 1), date(2026, 7, 15)))
        assert s("qtd_vs_py_qtd") == ((date(2026, 10, 1), TODAY), (date(2025, 10, 1), date(2025, 10, 15)))

    def test_qtd_in_the_second_month_keeps_the_same_month_offset(self):
        assert s("qtd_vs_prev_qtd", today=date(2026, 11, 13)) == \
            ((date(2026, 10, 1), date(2026, 11, 13)), (date(2026, 7, 1), date(2026, 8, 13)))

    def test_ytd(self):
        assert s("ytd_vs_pytd") == ((date(2026, 1, 1), TODAY), (date(2025, 1, 1), date(2025, 10, 15)))

    def test_the_same_point_is_clamped_to_a_shorter_month(self):
        assert s("mtd_vs_prev_mtd", today=date(2026, 3, 30)) == \
            ((date(2026, 3, 1), date(2026, 3, 30)), (date(2026, 2, 1), date(2026, 2, 28)))

    def test_a_leap_day_maps_to_the_28th(self):
        assert s("mtd_vs_py_mtd", today=date(2028, 2, 29)) == \
            ((date(2028, 2, 1), date(2028, 2, 29)), (date(2027, 2, 1), date(2027, 2, 28)))


class TestToDateOnPeriodKeyedData:
    def test_month_to_date_is_not_available(self):
        for c in ("mtd_vs_prev_mtd", "mtd_vs_py_mtd"):
            with pytest.raises(ComparisonNotAvailable):
                spans(c, TODAY, period_keyed=True)
        assert "mtd_vs_prev_mtd" not in available(True) and len(available(True)) == len(COMPARISONS) - 2
        assert available(False) == COMPARISONS

    def test_qtd_as_of_a_quarter_end_is_the_whole_quarter(self):
        assert s("qtd_vs_prev_qtd", keyed=True) == \
            ((date(2026, 7, 1), date(2026, 9, 30)), (date(2026, 4, 1), date(2026, 6, 30)))
        assert s("qtd_vs_py_qtd", keyed=True) == \
            ((date(2026, 7, 1), date(2026, 9, 30)), (date(2025, 7, 1), date(2025, 9, 30)))

    def test_qtd_one_month_in(self):
        assert s("qtd_vs_prev_qtd", today=date(2026, 11, 13), keyed=True) == \
            ((date(2026, 10, 1), date(2026, 10, 31)), (date(2026, 7, 1), date(2026, 7, 31)))

    def test_ytd_stops_at_the_last_closed_month(self):
        assert s("ytd_vs_pytd", keyed=True) == \
            ((date(2026, 1, 1), date(2026, 9, 30)), (date(2025, 1, 1), date(2025, 9, 30)))

    def test_hess_ytd_stops_at_the_last_month_with_actuals(self):
        assert s("ytd_vs_pytd", keyed=True, latest=date(2026, 7, 1)) == \
            ((date(2026, 1, 1), date(2026, 7, 31)), (date(2025, 1, 1), date(2025, 7, 31)))


class TestCompletePeriods:
    def test_month(self):
        assert s("month_vs_prev_month") == ((date(2026, 9, 1), date(2026, 9, 30)), (date(2026, 8, 1), date(2026, 8, 31)))
        assert s("month_vs_py_month") == ((date(2026, 9, 1), date(2026, 9, 30)), (date(2025, 9, 1), date(2025, 9, 30)))

    def test_quarter(self):
        assert s("quarter_vs_prev_quarter") == ((date(2026, 7, 1), date(2026, 9, 30)), (date(2026, 4, 1), date(2026, 6, 30)))
        assert s("quarter_vs_py_quarter") == ((date(2026, 7, 1), date(2026, 9, 30)), (date(2025, 7, 1), date(2025, 9, 30)))

    def test_year(self):
        assert s("year_vs_prev_year") == ((date(2025, 1, 1), date(2025, 12, 31)), (date(2024, 1, 1), date(2024, 12, 31)))

    def test_on_the_last_day_of_a_period_that_period_is_finished(self):
        assert s("quarter_vs_prev_quarter", today=date(2026, 9, 30)) == \
            ((date(2026, 7, 1), date(2026, 9, 30)), (date(2026, 4, 1), date(2026, 6, 30)))
        assert s("year_vs_prev_year", today=date(2026, 12, 31)) == \
            ((date(2026, 1, 1), date(2026, 12, 31)), (date(2025, 1, 1), date(2025, 12, 31)))

    def test_hess_quarter_is_the_last_quarter_with_all_its_actuals(self):
        # actuals through July: Q3 has one month of three, so the last finished quarter is Q2
        assert s("quarter_vs_prev_quarter", keyed=True, latest=date(2026, 7, 1)) == \
            ((date(2026, 4, 1), date(2026, 6, 30)), (date(2026, 1, 1), date(2026, 3, 31)))
        assert s("month_vs_py_month", keyed=True, latest=date(2026, 7, 1)) == \
            ((date(2026, 7, 1), date(2026, 7, 31)), (date(2025, 7, 1), date(2025, 7, 31)))

    def test_period_keyed_month_is_the_last_closed_month(self):
        assert s("month_vs_prev_month", keyed=True) == ((date(2026, 9, 1), date(2026, 9, 30)), (date(2026, 8, 1), date(2026, 8, 31)))


class TestFiscalYearStartingInApril:
    def test_quarters_follow_the_fiscal_year(self):
        # FY starts in April: Oct-Dec is fiscal Q3; the last finished quarter on 15 Oct is Jul-Sep (Q2)
        assert s("quarter_vs_prev_quarter", fy=4) == ((date(2026, 7, 1), date(2026, 9, 30)), (date(2026, 4, 1), date(2026, 6, 30)))
        assert s("qtd_vs_prev_qtd", fy=4) == ((date(2026, 10, 1), TODAY), (date(2026, 7, 1), date(2026, 7, 15)))

    def test_years_follow_the_fiscal_year(self):
        assert s("ytd_vs_pytd", fy=4) == ((date(2026, 4, 1), TODAY), (date(2025, 4, 1), date(2025, 10, 15)))
        assert s("year_vs_prev_year", fy=4) == ((date(2025, 4, 1), date(2026, 3, 31)), (date(2024, 4, 1), date(2025, 3, 31)))

    def test_fiscal_periods_for_period_keyed_queries(self):
        assert fiscal_periods(Span(date(2026, 4, 1), date(2026, 6, 30)), fy_start=4) == (2026, 1, 3)
        assert fiscal_periods(Span(date(2026, 1, 1), date(2026, 3, 31)), fy_start=4) == (2025, 10, 12)
        assert fiscal_periods(Span(date(2026, 1, 1), date(2026, 9, 30))) == (2026, 1, 9)
        with pytest.raises(ValueError):
            fiscal_periods(Span(date(2026, 3, 1), date(2026, 4, 30)), fy_start=4)


class TestEveryComparisonIsWellFormed:
    @pytest.mark.parametrize("c", COMPARISONS)
    @pytest.mark.parametrize("today", [date(2026, 1, 1), date(2026, 2, 28), date(2026, 3, 31), date(2026, 10, 15), date(2026, 12, 31)])
    @pytest.mark.parametrize("fy", [1, 4, 7, 10])
    def test_date_keyed_spans_are_ordered_equal_in_shape_and_not_in_the_future(self, c, today, fy):
        r = spans(c, today, False, None, fy)
        months = lambda sp: (sp.end.year * 12 + sp.end.month) - (sp.start.year * 12 + sp.start.month)
        assert r.current.start <= r.current.end <= today
        assert r.previous.start <= r.previous.end < r.current.start     # entirely before the current span
        assert months(r.previous) == months(r.current)                  # same shape, month for month
        assert r.current.start.day == 1 and r.previous.start.day == 1

    # The rolling 12 months deliberately cross a fiscal year (TimeFilter keys them on one running
    # year*100+period number); every other comparison stays inside one.
    @pytest.mark.parametrize("c", [c for c in COMPARISONS if not c.startswith("mtd") and c != "ltm_vs_prior_ltm"])
    @pytest.mark.parametrize("fy", [1, 4])
    def test_period_keyed_spans_are_whole_months_inside_one_fiscal_year(self, c, fy):
        r = spans(c, TODAY, True, None, fy)
        for span in (r.current, r.previous):
            assert span.start.day == 1 and span.end.day == __import__("calendar").monthrange(span.end.year, span.end.month)[1]
            fiscal_periods(span, fy)  # raises if it crossed a fiscal year
        assert r.current.end <= date(2026, 9, 30)

    def test_an_unknown_comparison_is_refused(self):
        with pytest.raises(ValueError):
            spans("yoy", TODAY, False)


def test_describe_reads_as_a_person_would_say_it():
    r = spans("quarter_vs_py_quarter", TODAY, True)
    assert r.describe() == "Quarter vs same quarter previous year: Jul 2026 – Sep 2026 vs Jul 2025 – Sep 2025"


class TestCompleteMonths:
    def test_whole_months_only(self):
        from src.analysis.period_comparisons import complete_months
        assert complete_months(Span(date(2026, 1, 1), date(2026, 9, 30))) == 9
        assert complete_months(Span(date(2026, 10, 1), date(2026, 10, 15))) == 0
        assert complete_months(Span(date(2026, 1, 1), date(2026, 2, 27))) == 1
        assert complete_months(Span(date(2026, 1, 1), date(2026, 2, 28))) == 2
        assert complete_months(Span(date(2026, 1, 15), date(2026, 3, 31))) == 2
