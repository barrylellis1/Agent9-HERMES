"""Deterministic helpers over a KPI's monthly series: [{"period": "YYYY-MM", "value": float}, ...].

Used by Value Assurance for the three lines it compares (settled design):
the KPI's value at acceptance, the "No Action" line (the trend at acceptance,
continued), and the "Actual" line (measured months since acceptance).

Two rules run through every function here:

1. A series is used only when EVERY label is a distinct calendar month. Found
   live on a SQL Server client: the series came back labelled
   ['2025-01', '2025-01', '2026-00', '2026-00', ...] because 3-digit fiscal
   periods were truncated when the label was built. Picking "the latest month"
   out of that produced a baseline for period "2026-00". A series whose labels
   cannot be trusted yields nothing at all.
2. Only COMPLETE months count. The current month is partial, and a warehouse
   may hold later-dated rows (the demo data does).

No function here guesses. Absent or unusable input returns None or an empty list.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, List, Optional, Sequence, Tuple

Month = Tuple[str, float]

_CALENDAR_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def month_index(period: str) -> int:
    """'2026-09' -> a running month number, so gaps between months are measurable."""
    return int(period[:4]) * 12 + int(period[5:7])


def current_month(today: Optional[str] = None) -> str:
    return (today or datetime.utcnow().strftime("%Y-%m-%d"))[:7]


def trusted_months(series: Any) -> Optional[List[Month]]:
    """The series as sorted (period, value) pairs, or None when it cannot be trusted.

    None when it is empty, any label is not a calendar month, or labels repeat.
    A point with an unparseable value is dropped; that does not discredit the rest.
    """
    if not isinstance(series, (list, tuple)) or not series:
        return None
    points = [p for p in series if isinstance(p, dict)]
    labels = [str(p.get("period") or "") for p in points]
    if not labels or len(set(labels)) != len(labels):
        return None
    if not all(_CALENDAR_MONTH.match(label) for label in labels):
        return None
    out: List[Month] = []
    for point, label in zip(points, labels):
        try:
            out.append((label, float(point.get("value"))))
        except (TypeError, ValueError):
            continue
    return sorted(out) or None


def complete_months_before(series: Any, month: str) -> List[Month]:
    """Trusted months strictly earlier than `month` ("YYYY-MM"), oldest first."""
    months = trusted_months(series)
    return [m for m in (months or []) if m[0] < month]


def complete_months_between(series: Any, after: str, before: str) -> List[Month]:
    """Trusted months strictly after `after` and strictly before `before`, oldest first."""
    months = trusted_months(series)
    return [m for m in (months or []) if after < m[0] < before]


def trend_slope_per_month(
    months: Sequence[Month], lookback: int = 6, min_points: int = 3
) -> Optional[float]:
    """Least-squares change per month over the last `lookback` months.

    None when fewer than `min_points` months are available: two points always
    make a line, and a "trend" read from them is noise. Gaps between months are
    respected (the x axis is the calendar, not the row number).
    """
    recent = list(months)[-lookback:]
    if len(recent) < min_points:
        return None
    xs = [float(month_index(period)) for period, _ in recent]
    ys = [value for _, value in recent]
    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return None
    return sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys)) / denom
