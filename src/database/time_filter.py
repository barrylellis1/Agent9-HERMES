"""TimeFilter — uniform time-dimension SQL condition generator.

Replaces the four fragmented time-filtering mechanisms in DPA:
  - _get_timeframe_condition       (uses table alias 't', breaks without time_dim JOIN)
  - _get_previous_timeframe_condition
  - _build_bq_dimensional_sql._append_date  (defaults to 'transaction_date')
  - _build_sf_dimensional_sql._append_date  (same)

All logic is pure Python — no I/O, no async.  Date arithmetic runs at call time
and produces concrete integer / date-string literals, so the emitted SQL is
readable and backend-agnostic for fiscal types.

Supported spec types (set ``type`` key in the TimeDimensionSpec dict):
  date               — single DATE/TIMESTAMP column; emits BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
  fiscal_year_period — two integer columns (year + period); emits fiscal_year=Y AND fiscal_period=P
  fiscal_year        — one integer column; emits fiscal_year=Y
"""

import calendar
from datetime import date, timedelta
from typing import Optional, Tuple


class TimeFilter:
    """Pure-logic time filter.  All public methods are @staticmethod / @classmethod."""

    # ── Internal helpers ────────────────────────────────────────────────────

    @staticmethod
    def _today() -> date:
        return date.today()

    @staticmethod
    def _normalize(timeframe) -> str:
        if hasattr(timeframe, "value"):
            return str(timeframe.value).strip().lower()
        return str(timeframe or "").strip().lower()

    @staticmethod
    def _quarter_of(month: int) -> int:
        return (month - 1) // 3 + 1

    @staticmethod
    def _quarter_months(q: int) -> Tuple[int, int]:
        """Return (start_month, end_month) for calendar quarter 1-4."""
        return (q - 1) * 3 + 1, q * 3

    @staticmethod
    def _month_end(year: int, month: int) -> int:
        return calendar.monthrange(year, month)[1]

    @staticmethod
    def _prev_quarter(year: int, quarter: int) -> Tuple[int, int]:
        """Return (prev_year, prev_quarter)."""
        if quarter == 1:
            return year - 1, 4
        return year, quarter - 1

    @staticmethod
    def _prev_month(year: int, month: int) -> Tuple[int, int]:
        if month == 1:
            return year - 1, 12
        return year, month - 1

    @staticmethod
    def _calendar_to_fiscal(cal_year: int, cal_month: int, fy_start: int) -> Tuple[int, int]:
        """Convert calendar year+month to (fiscal_year, fiscal_period).

        fiscal_year is labeled by the calendar year in which the FY starts.
        E.g. fy_start=4 (April): May 2026 → FY 2026 period 2; Jan 2026 → FY 2025 period 10.
        fy_start=1 (default): fiscal_year=calendar_year, fiscal_period=calendar_month (no change).
        """
        if cal_month >= fy_start:
            return cal_year, cal_month - fy_start + 1
        return cal_year - 1, cal_month - fy_start + 1 + 12

    # ── fiscal_year_period: current ─────────────────────────────────────────

    @classmethod
    def _fyp_current(cls, year_col: str, period_col: str, tf: str, today: date, fy_start: int = 1) -> Optional[str]:
        y, m = today.year, today.month
        fy, fp = cls._calendar_to_fiscal(y, m, fy_start)
        fq = cls._quarter_of(fp)
        fqs, fqe = cls._quarter_months(fq)

        if tf in ("current_quarter", "this_quarter"):
            return f"{year_col} = {fy} AND {period_col} BETWEEN {fqs} AND {fqe}"
        if tf == "quarter_to_date":
            return f"{year_col} = {fy} AND {period_col} BETWEEN {fqs} AND {fp}"
        if tf in ("current_year", "this_year"):
            return f"{year_col} = {fy}"
        if tf == "year_to_date":
            return f"{year_col} = {fy} AND {period_col} <= {fp}"
        if tf in ("current_month", "this_month", "month_to_date"):
            return f"{year_col} = {fy} AND {period_col} = {fp}"
        if tf == "last_quarter":
            # _prev_quarter / _prev_month work identically in fiscal space
            py, pq = cls._prev_quarter(fy, fq)
            ps, pe = cls._quarter_months(pq)
            return f"{year_col} = {py} AND {period_col} BETWEEN {ps} AND {pe}"
        if tf == "last_year":
            return f"{year_col} = {fy - 1}"
        if tf == "last_month":
            py, pm = cls._prev_month(fy, fp)
            return f"{year_col} = {py} AND {period_col} = {pm}"
        return None

    # ── fiscal_year_period: previous ────────────────────────────────────────

    @classmethod
    def _fyp_previous(cls, year_col: str, period_col: str, tf: str, today: date, fy_start: int = 1) -> Optional[str]:
        y, m = today.year, today.month
        fy, fp = cls._calendar_to_fiscal(y, m, fy_start)
        fq = cls._quarter_of(fp)

        # current/this → previous = last equivalent
        if tf in ("current_quarter", "this_quarter", "quarter_to_date"):
            return cls._fyp_current(year_col, period_col, "last_quarter", today, fy_start)
        if tf in ("current_year", "this_year", "year_to_date"):
            return cls._fyp_current(year_col, period_col, "last_year", today, fy_start)
        if tf in ("current_month", "this_month", "month_to_date"):
            return cls._fyp_current(year_col, period_col, "last_month", today, fy_start)

        # last_* → two periods back (in fiscal space)
        if tf == "last_quarter":
            py, pq = cls._prev_quarter(fy, fq)
            py2, pq2 = cls._prev_quarter(py, pq)
            ps, pe = cls._quarter_months(pq2)
            return f"{year_col} = {py2} AND {period_col} BETWEEN {ps} AND {pe}"
        if tf == "last_year":
            return f"{year_col} = {fy - 2}"
        if tf == "last_month":
            py, pm = cls._prev_month(fy, fp)
            py2, pm2 = cls._prev_month(py, pm)
            return f"{year_col} = {py2} AND {period_col} = {pm2}"

        return None

    # ── fiscal_year: current ────────────────────────────────────────────────

    @classmethod
    def _fy_current(cls, year_col: str, tf: str, today: date) -> Optional[str]:
        y, m = today.year, today.month
        q = cls._quarter_of(m)

        if tf in ("current_year", "this_year", "year_to_date",
                  "current_quarter", "this_quarter", "quarter_to_date",
                  "current_month", "this_month", "month_to_date"):
            return f"{year_col} = {y}"
        if tf == "last_year":
            return f"{year_col} = {y - 1}"
        if tf == "last_quarter":
            # if we're in Q1, last_quarter was Q4 of prev year
            return f"{year_col} = {y - 1 if q == 1 else y}"
        if tf == "last_month":
            py, _ = cls._prev_month(y, m)
            return f"{year_col} = {py}"
        return None

    # ── fiscal_year: previous ───────────────────────────────────────────────

    @classmethod
    def _fy_previous(cls, year_col: str, tf: str, today: date) -> Optional[str]:
        y, m = today.year, today.month
        q = cls._quarter_of(m)

        if tf in ("current_year", "this_year", "year_to_date",
                  "current_quarter", "this_quarter", "quarter_to_date",
                  "current_month", "this_month", "month_to_date"):
            return f"{year_col} = {y - 1}"
        if tf == "last_year":
            return f"{year_col} = {y - 2}"
        if tf == "last_quarter":
            # two quarters back — might wrap to prev year
            py, pq = cls._prev_quarter(y, q)
            py2, _ = cls._prev_quarter(py, pq)
            return f"{year_col} = {py2}"
        if tf == "last_month":
            py, pm = cls._prev_month(y, m)
            py2, _ = cls._prev_month(py, pm)
            return f"{year_col} = {py2}"
        return None

    # ── date type: ranges ───────────────────────────────────────────────────

    @classmethod
    def _date_range(cls, tf: str, today: date) -> Tuple[Optional[str], Optional[str]]:
        y, m = today.year, today.month
        q = cls._quarter_of(m)

        def qrange(year: int, qtr: int) -> Tuple[str, str]:
            qs, qe = cls._quarter_months(qtr)
            return str(date(year, qs, 1)), str(date(year, qe, cls._month_end(year, qe)))

        if tf in ("current_quarter", "this_quarter"):
            return qrange(y, q)
        if tf == "quarter_to_date":
            qs, _ = cls._quarter_months(q)
            return str(date(y, qs, 1)), str(today)
        if tf in ("current_year", "this_year"):
            return str(date(y, 1, 1)), str(date(y, 12, 31))
        if tf == "year_to_date":
            return str(date(y, 1, 1)), str(today)
        if tf in ("current_month", "this_month"):
            return str(date(y, m, 1)), str(date(y, m, cls._month_end(y, m)))
        if tf == "month_to_date":
            return str(date(y, m, 1)), str(today)
        if tf == "last_quarter":
            py, pq = cls._prev_quarter(y, q)
            return qrange(py, pq)
        if tf == "last_year":
            return str(date(y - 1, 1, 1)), str(date(y - 1, 12, 31))
        if tf == "last_month":
            py, pm = cls._prev_month(y, m)
            return str(date(py, pm, 1)), str(date(py, pm, cls._month_end(py, pm)))
        if tf == "last_7_days":
            return str(today - timedelta(days=7)), str(today)
        if tf == "last_30_days":
            return str(today - timedelta(days=30)), str(today)
        if tf == "last_90_days":
            return str(today - timedelta(days=90)), str(today)
        return None, None

    @classmethod
    def _date_current(cls, col: str, tf: str, today: date, dialect: str) -> Optional[str]:
        start, end = cls._date_range(tf, today)
        if start is None:
            return None
        quoted = f"`{col}`" if dialect == "bigquery" else col
        return f"{quoted} BETWEEN '{start}' AND '{end}'"

    @classmethod
    def _date_previous(cls, col: str, tf: str, today: date, dialect: str) -> Optional[str]:
        prev_map = {
            "current_quarter": "last_quarter",
            "this_quarter": "last_quarter",
            "quarter_to_date": "last_quarter",
            "current_year": "last_year",
            "this_year": "last_year",
            "year_to_date": "last_year",
            "current_month": "last_month",
            "this_month": "last_month",
            "month_to_date": "last_month",
        }
        if tf in prev_map:
            return cls._date_current(col, prev_map[tf], today, dialect)

        # For last_* → go one more period back
        y, m = today.year, today.month
        q = cls._quarter_of(m)

        if tf == "last_quarter":
            py, pq = cls._prev_quarter(y, q)
            py2, pq2 = cls._prev_quarter(py, pq)
            qs, qe = cls._quarter_months(pq2)
            start = str(date(py2, qs, 1))
            end = str(date(py2, qe, cls._month_end(py2, qe)))
        elif tf == "last_year":
            start, end = str(date(y - 2, 1, 1)), str(date(y - 2, 12, 31))
        elif tf == "last_month":
            py, pm = cls._prev_month(y, m)
            py2, pm2 = cls._prev_month(py, pm)
            start = str(date(py2, pm2, 1))
            end = str(date(py2, pm2, cls._month_end(py2, pm2)))
        else:
            return None

        quoted = f"`{col}`" if dialect == "bigquery" else col
        return f"{quoted} BETWEEN '{start}' AND '{end}'"

    # ── Public API ──────────────────────────────────────────────────────────

    @classmethod
    def current_condition(cls, spec: dict, timeframe, dialect: str = "bigquery") -> Optional[str]:
        """Return a SQL WHERE fragment (no WHERE keyword) for the current period.

        Args:
            spec:      TimeDimensionSpec as a plain dict (use .model_dump() if needed).
            timeframe: Timeframe string or enum-like with .value.
            dialect:   'bigquery' | 'snowflake' | 'sqlserver' | 'duckdb'.
                       Only affects column quoting for date type.
        """
        tf = cls._normalize(timeframe)
        today = cls._today()
        spec_type = (spec.get("type") or "date").lower()

        if spec_type == "fiscal_year_period":
            return cls._fyp_current(
                spec.get("year_column", "fiscal_year"),
                spec.get("period_column", "fiscal_period"),
                tf, today,
                fy_start=spec.get("fiscal_year_start_month", 1),
            )
        if spec_type == "fiscal_year":
            return cls._fy_current(spec.get("year_column", "fiscal_year"), tf, today)

        # date type
        return cls._date_current(spec.get("column", "transaction_date"), tf, today, dialect)

    @classmethod
    def previous_condition(cls, spec: dict, timeframe, dialect: str = "bigquery") -> Optional[str]:
        """Return a SQL WHERE fragment for the prior comparison period."""
        tf = cls._normalize(timeframe)
        today = cls._today()
        spec_type = (spec.get("type") or "date").lower()

        if spec_type == "fiscal_year_period":
            return cls._fyp_previous(
                spec.get("year_column", "fiscal_year"),
                spec.get("period_column", "fiscal_period"),
                tf, today,
                fy_start=spec.get("fiscal_year_start_month", 1),
            )
        if spec_type == "fiscal_year":
            return cls._fy_previous(spec.get("year_column", "fiscal_year"), tf, today)

        return cls._date_previous(spec.get("column", "transaction_date"), tf, today, dialect)

    @classmethod
    def date_range(
        cls, spec: dict, timeframe, previous: bool = False
    ) -> Tuple[Optional[str], Optional[str]]:
        """Return (start_str, end_str) for date-type specs only.

        Returns (None, None) for fiscal types — callers should use
        current_condition / previous_condition instead.
        """
        spec_type = (spec.get("type") or "date").lower()
        if spec_type != "date":
            return None, None

        tf = cls._normalize(timeframe)
        today = cls._today()

        if not previous:
            return cls._date_range(tf, today)

        prev_map = {
            "current_quarter": "last_quarter",
            "this_quarter": "last_quarter",
            "quarter_to_date": "last_quarter",
            "current_year": "last_year",
            "this_year": "last_year",
            "year_to_date": "last_year",
            "current_month": "last_month",
            "this_month": "last_month",
            "month_to_date": "last_month",
        }
        prev_tf = prev_map.get(tf, tf)
        return cls._date_range(prev_tf, today)

    @classmethod
    def previous_period_name(cls, timeframe) -> Optional[str]:
        """Return the canonical previous-period timeframe string, for DA _prev_timeframe."""
        tf = cls._normalize(timeframe)
        prev_map = {
            "current_quarter": "last_quarter",
            "this_quarter": "last_quarter",
            "quarter_to_date": "last_quarter",
            "current_year": "last_year",
            "this_year": "last_year",
            "year_to_date": "last_year",
            "current_month": "last_month",
            "this_month": "last_month",
            "month_to_date": "last_month",
            "last_quarter": "last_quarter",   # already previous — keep for DA compatibility
            "last_year": "last_year",
            "last_month": "last_month",
        }
        return prev_map.get(tf)

    @classmethod
    def append_condition(cls, sql: str, condition: Optional[str]) -> str:
        """Append a WHERE condition to a SQL string (handles existing WHERE clause)."""
        if not condition:
            return sql
        import re
        if re.search(r"\bWHERE\b", sql, re.IGNORECASE):
            return sql + f" AND {condition}"
        return sql + f" WHERE {condition}"
