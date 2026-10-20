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
# Rolling (owner rulings 2026-10-17): the last 12 complete months against the 12 before. The
# operational default, and the financial fallback while the year so far holds too few months.
# "Complete" for every data product (ruling B3): a date-keyed product's current month is left out.
ROLLING = ("ltm_vs_prior_ltm",)
COMPARISONS = TO_DATE + COMPLETE + ROLLING

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
    "ltm_vs_prior_ltm": "Last 12 months vs the 12 before",
}

# Finance shorthand for tiles and cards (owner ruling B2, 2026-10-17). Quarter labels carry the
# quarter numbers, so they are built from the spans (short_label). Comparisons without a ruled
# shorthand fall back to their descriptive LABELS.
SHORT_LABELS: Dict[str, str] = {
    "ytd_vs_pytd": "YTD vs PYTD",
    "ltm_vs_prior_ltm": "LTM vs Prior LTM",
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
    "ltm_vs_prior_ltm": ("rolling12", 12),
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
    return spans_at(comparison, reference_day(today, period_keyed, latest_actual), period_keyed, fy_start)


def spans_at(comparison: str, ref: date, period_keyed: bool, fy_start: int = 1) -> ComparisonSpans:
    """The two spans, from a reference day already decided (by `reference_day`, or carried
    from an earlier reading so a later stage measures exactly the same spans)."""
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

    if grain == "rolling12":
        # The last 12 COMPLETE months: a reference day inside a month (date-keyed data) leaves
        # that month out.
        last = _idx(ref) if ref == _month_end(ref) else _idx(ref) - 1
        cur_start = last - 11
        current = Span(_month_start(cur_start), _month_end(last))
        previous = Span(_month_start(cur_start - 12), _month_end(last - 12))
        return ComparisonSpans(comparison, LABELS[comparison], ref, current, previous)

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


# ── a comparison as a timeframe token (Phase 26, step 3) ─────────────────────────────────
#
# Stages pass a period to the Data Product Agent as a "timeframe" string, through some thirty
# call sites in Deep Analysis alone. A comparison travels the same way: its name, optionally
# with the reference day it was read at ("ytd_vs_pytd@2026-07-31"), so a later stage measures
# the spans an earlier one did. src/database/time_filter.py resolves it through this module.

def token(comparison: str, ref: Optional[date] = None) -> str:
    if comparison not in COMPARISONS:
        raise ValueError(f"unknown comparison {comparison!r}")
    return f"{comparison}@{ref.isoformat()}" if ref else comparison


def parse_token(value: object) -> Optional[Tuple[str, Optional[date]]]:
    """(comparison, reference day or None) when `value` is a comparison token, else None.
    Only the ten names are tokens; old request words (year_to_date, yoy) are not."""
    s = str(getattr(value, "value", value) or "").strip().lower()
    name, _, day = s.partition("@")
    if name not in COMPARISONS:
        return None
    try:
        return name, (date.fromisoformat(day) if day else None)
    except ValueError:
        return None


_YEAR_REQUESTS = ("year_to_date", "current_year", "this_year")
_QUARTER_REQUESTS = ("current_quarter", "this_quarter", "quarter_to_date")
_MONTH_REQUESTS = ("current_month", "this_month", "month_to_date")


def from_request(timeframe: object, comparison_type: object = None, period_keyed: bool = False) -> str:
    """The comparison an old-style request (a timeframe word and a comparison type) asks for.

    The dashboard sends year_to_date with year_over_year: YTD vs previous year YTD, as every
    scan has read it. "The current quarter" is the quarter so far (Situation Awareness never
    read it as the whole quarter). A month-to-date request on period-keyed data is the last
    closed month, as complete_periods.closed_view answered it. A comparison type that is not a
    period shift (budget, target, benchmark) only says which version to compare; the period
    is then the timeframe's year-over-year reading.
    """
    if parse_token(timeframe):
        return parse_token(timeframe)[0]
    tf = str(getattr(timeframe, "value", timeframe) or "").strip().lower()
    ct = str(getattr(comparison_type, "value", comparison_type) or "year_over_year").strip().lower()
    sequential = ("quarter" in ct) or ("month" in ct)  # else a year back
    if tf in _YEAR_REQUESTS:
        return "ytd_vs_pytd"
    if tf in _QUARTER_REQUESTS:
        return "qtd_vs_prev_qtd" if sequential else "qtd_vs_py_qtd"
    if tf in _MONTH_REQUESTS:
        if period_keyed:
            return "month_vs_prev_month" if sequential else "month_vs_py_month"
        return "mtd_vs_prev_mtd" if sequential else "mtd_vs_py_mtd"
    if tf == "last_year":
        return "year_vs_prev_year"
    if tf == "last_month":
        return "month_vs_prev_month" if sequential else "month_vs_py_month"
    # last_quarter, and anything unrecognised (the old default was the last quarter)
    return "quarter_vs_prev_quarter" if sequential else "quarter_vs_py_quarter"


_LEGACY_WORD = {
    "ytd_vs_pytd": "year_to_date", "qtd_vs_prev_qtd": "quarter_to_date", "qtd_vs_py_qtd": "quarter_to_date",
    "mtd_vs_prev_mtd": "month_to_date", "mtd_vs_py_mtd": "month_to_date",
    "quarter_vs_prev_quarter": "last_quarter", "quarter_vs_py_quarter": "last_quarter",
    "month_vs_prev_month": "last_month", "month_vs_py_month": "last_month", "year_vs_prev_year": "last_year",
}


def legacy_word(value: object) -> object:
    """For a path that only knows the old words (the DuckDB SQL builder): the nearest one.
    Approximate: the old words cannot say "previous quarter to date". Anything that is not a
    comparison token is returned unchanged."""
    parsed = parse_token(value)
    return _LEGACY_WORD[parsed[0]] if parsed else value


def period_words(value: object) -> str:
    """A timeframe as a reader says it: a comparison token as its label and reference day
    ("YTD vs previous year YTD, as of 30 Sep 2026"); anything else as given."""
    parsed = parse_token(value)
    if not parsed:
        return str(getattr(value, "value", value) or "")
    name, ref = parsed
    return f"{LABELS[name]}, as of {ref.day} {ref:%b %Y}" if ref else LABELS[name]


def basis_key(comparison: str) -> str:
    """What the current span is set against, as the short key the agents' wording uses:
    "yoy" (the same span a year earlier), "qoq" (the previous quarter), "mom" (the previous month)."""
    _, back = _GRAIN[comparison]
    if back == 12:
        return "yoy"
    return "qoq" if back == 3 else "mom"


def short_label(sp: "ComparisonSpans", fy_start: int = 1) -> str:
    """The comparison in finance shorthand (owner ruling B2): "YTD vs PYTD", "LTM vs Prior LTM",
    "Q3 vs PY Q3", "Q3 vs Q2". Quarters are numbered within the fiscal year."""
    if sp.comparison in SHORT_LABELS:
        return SHORT_LABELS[sp.comparison]

    def q(d: date) -> int:
        return ((d.month - fy_start) % 12) // 3 + 1
    if sp.comparison == "quarter_vs_py_quarter":
        return f"Q{q(sp.current.start)} vs PY Q{q(sp.previous.start)}"
    if sp.comparison == "quarter_vs_prev_quarter":
        return f"Q{q(sp.current.start)} vs Q{q(sp.previous.start)}"
    return sp.label


def current_short(sp: "ComparisonSpans", fy_start: int = 1) -> str:
    """The current span alone in finance shorthand, for actuals set against a plan (owner ruling
    B2: "YTD Act vs Budget"): "YTD", "LTM", "Q3". QTD and MTD are the same convention; the
    complete month and year, which no data product reads yet, say "Month" and "Year"."""
    grain, _ = _GRAIN[sp.comparison]
    if sp.comparison == "ytd_vs_pytd":
        return "YTD"
    if grain == "rolling12":
        return "LTM"
    if sp.comparison.startswith("qtd"):
        return "QTD"
    if sp.comparison.startswith("mtd"):
        return "MTD"
    if grain == "quarter":
        return f"Q{((sp.current.start.month - fy_start) % 12) // 3 + 1}"
    return "Month" if grain == "month" else "Year"


def months_words(span: Span) -> str:
    """A span as a card's second line names it (owner ruling C, 2026-10-20): "Jan–Sep 2026",
    "Oct 2025–Sep 2026", "Sep 2026". A span ending part-way through a month keeps its days
    ("1 Jan–20 Oct 2026"), so a to-date reading on data booked by date is not overstated."""
    a, b = span.start, span.end
    if a.day == 1 and b == _month_end(b):
        if (a.year, a.month) == (b.year, b.month):
            return f"{a:%b %Y}"
        if a.year == b.year:
            return f"{a:%b}–{b:%b %Y}"
        return f"{a:%b %Y}–{b:%b %Y}"
    if a == b:
        return f"{a.day} {a:%b %Y}"
    if a.year == b.year:
        return f"{a.day} {a:%b}–{b.day} {b:%b %Y}"
    return f"{a.day} {a:%b %Y}–{b.day} {b:%b %Y}"


def months_line(sp: "ComparisonSpans") -> str:
    """The months a comparison set side by side: "Jan–Sep 2026 vs Jan–Sep 2025"."""
    return f"{months_words(sp.current)} vs {months_words(sp.previous)}"


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


def fiscal_year_period(d: date, fy_start: int = 1) -> Tuple[int, int]:
    """(fiscal_year, period) of a calendar day; a fiscal year is named by the year it starts in."""
    if d.month >= fy_start:
        return d.year, d.month - fy_start + 1
    return d.year - 1, d.month - fy_start + 13


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
