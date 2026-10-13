"""Complete periods only, for data that is keyed by period.

A data product declares how it keys time in `time_dimensions[0].type`:
`fiscal_year_period` (a year column and a period column: finance postings), or
`date` (a transaction date). The declaration decides what "the current period"
can mean.

For period-keyed data the current period is not finished until it closes, and
postings inside it are neither complete nor evenly dated. So every "current" or
"to date" request is answered as of the LAST CLOSED PERIOD: on 13 October,
"year to date" is January to September, "this quarter" is July to September, and
"this month" is September, each against the same periods a year earlier.

Date-keyed data is left to the day: the period so far against the same days a
year earlier.

Found live 2026-10-13 on lubricants (period-keyed): the situation card sliced the
data to the day (1-13 Oct against 1-13 Oct), Deep Analysis worked in whole periods
(all October, including rows dated after today), and for Premium Product Mix % the
card said it fell while the analysis said it rose.

Both stages now ask this module what date to treat as "today".
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Optional

PERIOD_KEYED_TYPES = ("fiscal_year_period", "fiscal_year")

# Requests that mean "the period we are in". `last_*` requests already name a closed period.
OPEN_PERIOD_TOKENS = {
    "current_month": "month_to_date", "this_month": "month_to_date", "month_to_date": "month_to_date",
    "current_quarter": "quarter_to_date", "this_quarter": "quarter_to_date", "quarter_to_date": "quarter_to_date",
    "current_year": "year_to_date", "this_year": "year_to_date", "year_to_date": "year_to_date",
}


def _get(spec: Any, key: str) -> Any:
    return spec.get(key) if isinstance(spec, dict) else getattr(spec, key, None)


def is_period_keyed(spec: Any) -> bool:
    """True when the data product keys time by period, not by transaction date."""
    if not spec:
        return False
    spec_type = str(_get(spec, "type") or "date").lower()
    if spec_type in PERIOD_KEYED_TYPES:
        return True
    # a "date" spec with no date column but a year column is period-keyed in practice
    return spec_type == "date" and not _get(spec, "column") and bool(_get(spec, "year_column"))


def last_closed_day(today: Optional[date] = None) -> date:
    """The last day of the last closed month."""
    today = today or date.today()
    return today.replace(day=1) - timedelta(days=1)


def as_of(spec: Any, today: Optional[date] = None) -> Optional[date]:
    """The date to treat as "today" when resolving an open-period request.

    The last closed day for period-keyed data; None (meaning: the real today) for
    date-keyed data.
    """
    return last_closed_day(today) if is_period_keyed(spec) else None


def closed_view(token: Any, today: date) -> tuple:
    """(token, today) to resolve a period-keyed request with.

    An open-period request becomes its to-date form as of the last closed day, so it
    covers closed periods only and is compared with the same periods a year earlier.
    Any other request is returned unchanged.
    """
    key = str(getattr(token, "value", token) or "").strip().lower()
    if key in OPEN_PERIOD_TOKENS:
        return OPEN_PERIOD_TOKENS[key], last_closed_day(today)
    return token, today
