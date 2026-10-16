"""The ten named period comparisons (Phase 26, step 1).

Given the day, how a data product keys time, its fiscal year start, and the latest period
it holds actuals for, return the two spans a comparison sets side by side. Step 3 routes every
stage through it. Until then only `canonical()` is in use: Situation Awareness and Deep Analysis
match threshold rows through it, so an old name and its new one find the same row.

Two families, as the owner defined them (2026-10-13/14):

  To date: two partial spans of equal elapsed length.
    mtd_vs_prev_mtd     this month so far        vs last month to the same point
    mtd_vs_py_mtd       this month so far        vs the same month last year to the same point
    qtd_vs_prev_qtd     this quarter so far      vs last quarter to the same point
    qtd_vs_py_qtd       this quarter so far      vs the same quarter last year to the same point
    ytd_vs_pytd         this year so far         vs last year to the same point

  Complete period: two finished periods of equal length.
    month_vs_prev_month       last finished month    vs the month before
    month_vs_py_month         last finished month    vs that month a year earlier
    quarter_vs_prev_quarter   last finished quarter  vs the quarter before
    quarter_vs_py_quarter     last finished quarter  vs that quarter a year earlier
    year_vs_prev_year         last finished year     vs the year before

"Today" is the reference day, and two rules decide it:

  1. Period-keyed data is read as of the last closed month (src/analysis/complete_periods.py).
     The two month-to-date comparisons then mean nothing (a closed month is a whole month),
     so they are not available for period-keyed data.
  2. A period with no actuals is not finished, whatever the calendar says: the reference day
     is never later than the end of the latest month (period-keyed) or day (date-keyed) that
     holds actuals. Found live on Hess, whose actuals stop at July 2026.

"To the same point" is the same number of months into the period and the same day of the
month (clamped to the month's length; a month end maps to a month end). Quarters and years
follow the data product's fiscal year start month; a fiscal year is named by the calendar
year it starts in, as src/database/time_filter.py does.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Optional, Tuple

TO_DATE = ("mtd_vs_prev_mtd", "mtd_vs_py_mtd", "qtd_vs_prev_qtd", "qtd_vs_py_qtd", "ytd_vs_pytd")
COMPLETE = ("month_vs_prev_month", "month_vs_py_month", "quarter_vs_prev_quarter",
            "quarter_vs_py_quarter", "year_vs_prev_year")
COMPARISONS = TO_DATE + COMPLETE

LABELS: Dict[str, str] = {
    "mtd_vs_prev_mtd": "MTD vs previous MTD",
    "mtd_vs_py_mtd": "MTD vs previous year MTD",
    "qtd_vs_prev_qtd": "QTD vs previous QTD",
    "qtd_vs_py_qtd": "QTD vs previous year QTD",
    "ytd_vs_pytd": "YTD vs previous year YTD",
    "month_vs_prev_month": "Month vs previous month",
    "month_vs_py_month": "Month vs same month previous year",
    "quarter_vs_prev_quarter": "Quarter vs previous quarter",
    "quarter_vs_py_quarter": "Quarter vs same quarter previous year",
    "year_vs_prev_year": "Year vs previous year",
}

# Names in use before Phase 26, and what each has always meant in practice (step 2, 2026-10-15).
# "yoy" thresholds were only ever evaluated against YTD vs previous year YTD: the screen sends
# year_to_date and the offline assessment defaults to it. "qoq" and "mom" were never evaluated,
# so they take their literal reading. The request spellings (year_over_year…) map the same way.
LEGACY: Dict[str, str] = {
    "yoy": "ytd_vs_pytd", "year_over_year": "ytd_vs_pytd", "year-over-year": "ytd_vs_pytd",
    "qoq": "quarter_vs_prev_quarter", "quarter_over_quarter": "quarter_vs_prev_quarter",
    "quarter-over-quarter": "quarter_vs_prev_quarter",
    "mom": "month_vs_prev_month", "month_over_month": "month_vs_prev_month",
    "month-over-month": "month_vs_prev_month",
}


def canonical(name: object) -> str:
    """A comparison name as one of the ten, when it is an old spelling of one. Anything else
    (budget, plan_variance, projected_breach…) comes back lower-cased and otherwise unchanged."""
    n = str(getattr(name, "value", name) or "").strip().lower()
    return LEGACY.get(n, n)


# The period each comparison works in, and how far back its comparison span starts (months).
_GRAIN: Dict[str, Tuple[str, int]] = {
    "mtd_vs_prev_mtd": ("month", 1), "mtd_vs_py_mtd": ("month", 12),
    "qtd_vs_prev_qtd": ("quarter", 3), "qtd_vs_py_qtd": ("quarter", 12),
    "ytd_vs_pytd": ("year", 12),
    "month_vs_prev_month": ("month", 1), "month_vs_py_month": ("month", 12),
    "quarter_vs_prev_quarter": ("quarter", 3), "quarter_vs_py_quarter": ("quarter", 12),
    "year_vs_prev_year": ("year", 12),
}


class ComparisonNotAvailable(ValueError):
    """The comparison has no meaning for this data product (e.g. MTD on period-keyed data)."""


@dataclass(frozen=True)
class Span:
    start: date
    end: date  # inclusive

    def describe(self) -> str:
        if self.start.day == 1 and self.end == _month_end(self.end):
            first, last = self.start.strftime("%b %Y"), self.end.strftime("%b %Y")
            return first if first == last else f"{first} – {last}"
        return f"{self.start:%d %b %Y} – {self.end:%d %b %Y}"


@dataclass(frozen=True)
class ComparisonSpans:
    comparison: str
    label: str
    reference_day: date
    current: Span
    previous: Span

    def describe(self) -> str:
        return f"{self.label}: {self.current.describe()} vs {self.previous.describe()}"


# ── calendar arithmetic ─────────────────────────────────────────────────────────────────

def _idx(d: date) -> int:
    return d.year * 12 + (d.month - 1)


def _from_idx(i: int) -> Tuple[int, int]:
    return i // 12, i % 12 + 1


def _month_start(i: int) -> date:
    y, m = _from_idx(i)
    return date(y, m, 1)


def _month_end(d_or_idx) -> date:
    y, m = (d_or_idx.year, d_or_idx.month) if isinstance(d_or_idx, date) else _from_idx(d_or_idx)
    return date(y, m, calendar.monthrange(y, m)[1])


def _period_start_idx(i: int, grain: str, fy_start: int) -> int:
    """Month index at which the month / fiscal quarter / fiscal year containing month i starts."""
    if grain == "month":
        return i
    fiscal_month = ((i % 12 + 1) - fy_start) % 12  # 0-based month within the fiscal year
    return i - (fiscal_month % 3 if grain == "quarter" else fiscal_month)


def _period_len(grain: str) -> int:
    return {"month": 1, "quarter": 3, "year": 12}[grain]


def _same_point(day: date, from_start: int, to_start: int) -> date:
    """`day`, which lies in the period starting at month index from_start, moved to the same
    number of months into the period starting at to_start, on the same day of the month."""
    target = to_start + (_idx(day) - from_start)
    if day == _month_end(day):
        return _month_end(target)
    y, m = _from_idx(target)
    return date(y, m, min(day.day, calendar.monthrange(y, m)[1]))


# ── the reference day ───────────────────────────────────────────────────────────────────

def reference_day(today: date, period_keyed: bool, latest_actual: Optional[date] = None) -> date:
    """The day the comparison is taken as of (rules 1 and 2 in the module docstring)."""
    if period_keyed:
        ref = today.replace(day=1) - timedelta(days=1)  # last closed day
        if latest_actual is not None:
            ref = min(ref, _month_end(latest_actual))
        return ref
    ref = today
    if latest_actual is not None:
        ref = min(ref, latest_actual)
    return ref


# ── the spans ───────────────────────────────────────────────────────────────────────────

def spans(
    comparison: str,
    today: date,
    period_keyed: bool,
    latest_actual: Optional[date] = None,
    fy_start: int = 1,
) -> ComparisonSpans:
    """The two spans `comparison` sets side by side, as of `today` for this data product."""
    if comparison not in COMPARISONS:
        raise ValueError(f"unknown comparison {comparison!r}; expected one of {', '.join(COMPARISONS)}")
    if period_keyed and comparison in ("mtd_vs_prev_mtd", "mtd_vs_py_mtd"):
        raise ComparisonNotAvailable(
            "Month to date has no meaning for data keyed by period: it is read as of the last closed "
            "month, which is a whole month. Use month vs previous month, or vs the same month last year."
        )
    if not 1 <= int(fy_start) <= 12:
        raise ValueError("fy_start must be a month number, 1 to 12")

    grain, back = _GRAIN[comparison]
    ref = reference_day(today, period_keyed, latest_actual)
    length = _period_len(grain)

    if comparison in TO_DATE:
        cur_start = _period_start_idx(_idx(ref), grain, fy_start)
        prev_start = cur_start - back
        current = Span(_month_start(cur_start), ref)
        previous = Span(_month_start(prev_start), _same_point(ref, cur_start, prev_start))
    else:
        containing = _period_start_idx(_idx(ref), grain, fy_start)
        finished = ref == _month_end(containing + length - 1)
        cur_start = containing if finished else containing - length
        prev_start = cur_start - back
        current = Span(_month_start(cur_start), _month_end(cur_start + length - 1))
        previous = Span(_month_start(prev_start), _month_end(prev_start + length - 1))

    return ComparisonSpans(comparison, LABELS[comparison], ref, current, previous)


def available(period_keyed: bool) -> Tuple[str, ...]:
    """The comparisons that mean something for this kind of data product."""
    if period_keyed:
        return tuple(c for c in COMPARISONS if c not in ("mtd_vs_prev_mtd", "mtd_vs_py_mtd"))
    return COMPARISONS


def complete_months(span: Span) -> int:
    """Whole calendar months inside a span. A to-date span on date-keyed data ends part-way
    through a month, which does not count; every span on period-keyed data is whole months."""
    first = _idx(span.start) if span.start.day == 1 else _idx(span.start) + 1
    last = _idx(span.end) if span.end == _month_end(span.end) else _idx(span.end) - 1
    return max(0, last - first + 1)


def fiscal_periods(span: Span, fy_start: int = 1) -> Tuple[int, int, int]:
    """A month-aligned span as (fiscal_year, first_period, last_period), for period-keyed data.
    Every span this module returns lies inside one fiscal year."""
    def fiscal(d: date) -> Tuple[int, int]:
        if d.month >= fy_start:
            return d.year, d.month - fy_start + 1
        return d.year - 1, d.month - fy_start + 13
    (fy1, p1), (fy2, p2) = fiscal(span.start), fiscal(span.end)
    if fy1 != fy2:
        raise ValueError(f"span {span.describe()} crosses a fiscal year")
    return fy1, p1, p2
