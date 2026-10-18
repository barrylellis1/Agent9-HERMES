# arch-allow-direct-agent-construction
"""Phase 26 step 3b: Situation Awareness reads a KPI on a named comparison.

A stand-in warehouse shaped like Hess: actuals through July 2026, so a scan on 16 October must
read YTD as January to July, not to September (rule 2: a period with no actuals is not finished).
"""
from __future__ import annotations

import logging
import re
from datetime import date
from types import SimpleNamespace

import pytest

from src.agents.models.situation_awareness_models import ComparisonType, MeasurementContext, TimeFrame
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent as SA
from src.agents.new.a9_situation_awareness_agent import _latest_month_end

RAW_SQL = "SELECT SUM(amount) AS value FROM `p.d.HessView` WHERE version = 'Actual'"
FYP = {"type": "fiscal_year_period", "year_column": "fiscal_year", "period_column": "fiscal_period"}


class Warehouse:
    """Answers the monthly series with months through `last_month`, and a total per span."""

    def __init__(self, last_month="2026-07"):
        self.last_month = last_month
        self.sql = []

    async def execute_sql(self, sql, parameters=None, principal_context=None, data_product_id=None):
        self.sql.append(sql)
        if "LIMIT" in sql:  # the monthly series
            y, m = int(self.last_month[:4]), int(self.last_month[5:])
            months = [(y if k <= m else y - 1, k) for k in range(1, 13)]
            return {"rows": [{"period": f"{yy}-{mm:02d}", "value": 10.0} for yy, mm in months]}
        m = re.search(r"BETWEEN '(\d{4})-", sql) or re.search(r"fiscal_year = (\d{4})", sql)
        return {"rows": [[120.0 if m.group(1) == "2026" else 100.0]]}


def _sa(warehouse, spec=FYP):
    sa = SA.__new__(SA)
    sa.logger = logging.getLogger("t")
    sa.data_product_agent = warehouse
    sa._last_sql_cache = {}
    sa._resolve_source_system = lambda dp: "bigquery"

    async def _spec(dp):
        return spec
    sa._resolve_time_spec_sa = _spec
    return sa


def _kpi():
    return SimpleNamespace(name="Production Revenue", calculation=RAW_SQL, sql_query=RAW_SQL,
                           data_product_id="dp_hess", metadata={}, unit="$", thresholds=[],
                           plan_version_value=None)


def _span_filters(warehouse):
    """The (start, end) each period-filtered query read, as dates, whether it filtered a date
    column or fiscal year and period (period-keyed data, owner ruling B4)."""
    import calendar
    out = []
    for q in warehouse.sql:
        if "LIMIT" in q:
            continue
        d = re.search(r"BETWEEN '([\d-]+)' AND '([\d-]+)'", q)
        f = re.search(r"fiscal_year = (\d{4}) AND \S+ BETWEEN (\d+) AND (\d+)", q)
        if d:
            out.append(d.groups())
        elif f:
            y, p1, p2 = int(f.group(1)), int(f.group(2)), int(f.group(3))
            out.append((f"{y}-{p1:02d}-01", f"{y}-{p2:02d}-{calendar.monthrange(y, p2)[1]:02d}"))
    return out


@pytest.fixture
def today(monkeypatch):
    """Pin date.today() as the agent sees it."""
    import datetime as _dt

    class _D(_dt.date):
        @classmethod
        def today(cls):
            return cls(2026, 10, 16)
    monkeypatch.setattr(_dt, "date", _D)
    return _D(2026, 10, 16)


@pytest.mark.asyncio
async def test_ytd_stops_at_the_last_month_with_actuals(today):
    wh = Warehouse("2026-07")
    v = await _sa(wh)._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    assert "LIMIT" in wh.sql[0], "the series runs first, so the spans know where actuals end"
    assert _span_filters(wh) == [("2026-01-01", "2026-07-31"), ("2025-01-01", "2025-07-31")]
    assert v.value == 120.0 and v.comparison_value == 100.0 and round(v.percent_change, 1) == 20.0
    ctx = v.context
    assert (ctx.period_comparison, ctx.reference_day, ctx.actuals_end) == ("ytd_vs_pytd", "2026-07-31", "2026-07-31")
    assert ctx.period_label == "YTD vs previous year YTD"
    assert (ctx.window_start, ctx.window_end) == ("2026-01-01", "2026-07-31")
    assert SA._window_suffix(v).endswith("; actuals end Jul 2026)")


@pytest.mark.asyncio
async def test_a_current_feed_reads_to_the_last_closed_month_and_says_nothing_extra(today):
    wh = Warehouse("2026-12")  # the demo data holds later-dated rows
    v = await _sa(wh)._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    assert _span_filters(wh)[0] == ("2026-01-01", "2026-09-30")
    assert v.context.actuals_end is None
    assert "actuals end" not in SA._window_suffix(v)


@pytest.mark.asyncio
async def test_the_quarter_so_far_on_hess_is_july(today):
    wh = Warehouse("2026-07")
    v = await _sa(wh)._get_kpi_value(_kpi(), TimeFrame.CURRENT_QUARTER, ComparisonType.YEAR_OVER_YEAR, {})
    assert v.context.period_comparison == "qtd_vs_py_qtd"
    assert _span_filters(wh) == [("2026-07-01", "2026-07-31"), ("2025-07-01", "2025-07-31")]


@pytest.mark.asyncio
async def test_the_plan_is_read_over_the_actuals_span_not_its_own(today):
    # plan rows run to December; the actual reading passes its token on
    wh = Warehouse("2026-12")
    sa = _sa(wh)
    v = await sa._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, None, {}, period_comparison="ytd_vs_pytd@2026-07-31")
    assert not any("LIMIT" in q for q in wh.sql[:1]), "a fixed reference day needs no series first"
    assert _span_filters(wh) == [("2026-01-01", "2026-07-31")]
    assert v.context.reference_day == "2026-07-31"


@pytest.mark.asyncio
async def test_a_request_can_name_the_comparison(today):
    wh = Warehouse("2026-09")
    v = await _sa(wh)._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {},
                                     period_comparison="quarter_vs_py_quarter")
    assert v.context.period_comparison == "quarter_vs_py_quarter"
    assert _span_filters(wh) == [("2026-07-01", "2026-09-30"), ("2025-07-01", "2025-09-30")]


@pytest.mark.asyncio
async def test_a_comparison_the_data_cannot_answer_is_unread_not_unfiltered(today):
    wh = Warehouse("2026-09")
    v = await _sa(wh)._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {},
                                     period_comparison="mtd_vs_py_mtd")
    assert v is None
    assert not any("BETWEEN" in q or "fiscal_year =" in q for q in wh.sql if "LIMIT" not in q)
    assert await _sa(Warehouse())._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, None, {}, period_comparison="rolling_90") is None


@pytest.mark.asyncio
async def test_date_keyed_data_reads_to_the_day(today):
    wh = Warehouse("2026-10")
    v = await _sa(wh, {"type": "date", "column": "transaction_date"})._get_kpi_value(
        _kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    assert _span_filters(wh) == [("2026-01-01", "2026-10-16"), ("2025-01-01", "2025-10-16")]
    assert v.context.actuals_end is None


def test_latest_month_end():
    assert _latest_month_end([{"period": "2026-06", "value": 1}, {"period": "2026-07", "value": 2}]) == date(2026, 7, 31)
    assert _latest_month_end([{"period": "2026-00", "value": 1}]) is None  # untrusted labels
    assert _latest_month_end([]) is None


def test_period_token_carries_the_reading_on():
    v = SimpleNamespace(context=MeasurementContext(period_comparison="ytd_vs_pytd", reference_day="2026-07-31"))
    assert SA._period_token(v) == "ytd_vs_pytd@2026-07-31"
    assert SA._period_token(SimpleNamespace(context=None)) is None


# ── Phase 26 step 3c: the period settings decide which readings may raise a card ──

@pytest.fixture
def february(monkeypatch):
    import datetime as _dt

    class _D(_dt.date):
        @classmethod
        def today(cls):
            return cls(2026, 2, 20)
    monkeypatch.setattr(_dt, "date", _D)


@pytest.mark.asyncio
async def test_in_october_a_ytd_breach_may_raise_a_card(today):
    v = await _sa(Warehouse("2026-12"))._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    assert v.context.card_hold_reason is None and v.context.plan_card_hold_reason is None


@pytest.mark.asyncio
async def test_a_february_scan_holds_ytd_on_one_closed_month(february):
    v = await _sa(Warehouse("2026-12"))._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    assert v.context.card_hold_reason == "YTD vs previous year YTD holds 1 complete month (Jan 2026); a card needs 2."
    assert v.context.plan_card_hold_reason.startswith("Actual vs plan holds 1 complete month")


@pytest.mark.asyncio
async def test_a_quarter_reading_is_context_unless_the_client_turns_quarters_on(today):
    v = await _sa(Warehouse("2026-12"))._get_kpi_value(
        _kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {}, period_comparison="quarter_vs_py_quarter")
    assert v.context.card_hold_reason == "Quarter vs same quarter previous year is shown for context; it does not raise cards here."
    # the threshold row for that comparison opts in
    kpi = _kpi()
    kpi.metadata = {"variance_thresholds": {"quarter_vs_py_quarter": {"green": 5.0, "raises_card": True}}}
    v = await _sa(Warehouse("2026-12"))._get_kpi_value(
        kpi, TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {}, period_comparison="quarter_vs_py_quarter")
    assert v.context.card_hold_reason is None


@pytest.mark.asyncio
async def test_the_plan_reading_carries_no_card_decision(today):
    v = await _sa(Warehouse("2026-12"))._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, None, {},
                                                        period_comparison="ytd_vs_pytd@2026-07-31")
    assert v.context.card_hold_reason is None  # decided on the actual reading, not the plan's


def test_held_cards_are_listed_with_the_reason_and_others_pass():
    ctx = MeasurementContext(card_hold_reason="YTD holds 1 complete month (Jan 2026); a card needs 2.",
                             plan_card_hold_reason="Actual vs plan holds 1 complete month (Jan 2026); a card needs 2.")
    v = SimpleNamespace(context=ctx)
    sits = [SimpleNamespace(kpi_name="EBITDA", alert_type=a) for a in
            ("threshold_breach", None, "plan_variance", "covenant", "projected_breach", "acceleration")]
    kept, held = SA._apply_card_settings(sits, v)
    assert [s.alert_type for s in kept] == ["covenant", "projected_breach", "acceleration"]
    assert held == ["EBITDA: YTD holds 1 complete month (Jan 2026); a card needs 2.",
                    "EBITDA: Actual vs plan holds 1 complete month (Jan 2026); a card needs 2."]


def test_nothing_is_held_without_a_reason():
    sits = [SimpleNamespace(kpi_name="EBITDA", alert_type="threshold_breach")]
    assert SA._apply_card_settings(sits, SimpleNamespace(context=None)) == (sits, [])


def test_the_response_and_orchestrator_carry_the_held_readings():
    from src.agents.models.situation_awareness_models import SituationDetectionResponse
    r = SituationDetectionResponse(request_id="r", status="success", situations=[])
    assert r.readings_held == []


# ── Owner ruling B4: read on the KPI's declared time dimension ──

@pytest.mark.asyncio
async def test_period_keyed_data_is_filtered_on_fiscal_year_and_period(today):
    wh = Warehouse("2026-07")
    await _sa(wh)._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    reads = [q for q in wh.sql if "LIMIT" not in q]
    assert reads[0].endswith("AND fiscal_year = 2026 AND fiscal_period BETWEEN 1 AND 7")
    assert reads[1].endswith("AND fiscal_year = 2025 AND fiscal_period BETWEEN 1 AND 7")
    assert not any("transaction_date" in q for q in reads)


@pytest.mark.asyncio
async def test_a_kpi_dated_by_another_event_uses_that_dimension(today):
    """As Deep Analysis does: the Data Product Agent's resolver picks the KPI's declared dimension."""
    wh = Warehouse("2026-12")
    wh._resolve_time_spec = lambda dp_id, kpi: {"type": "date", "column": "delivery_date"}
    v = await _sa(wh)._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    reads = [q for q in wh.sql if "LIMIT" not in q]
    assert "`delivery_date` BETWEEN '2026-01-01' AND '2026-09-30'" in reads[0]   # the product's closed months
    assert v.context.window_end == "2026-09-30"


@pytest.mark.asyncio
async def test_bigquery_series_comes_from_the_data_product_agent(today):
    wh = Warehouse("2026-07")
    asked = []

    def _series(kpi, num_months=9):
        asked.append(num_months)
        return {"success": True, "sql": "SELECT period, value FROM (...) LIMIT 13"}
    wh.generate_monthly_series_sql = _series
    await _sa(wh)._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    assert asked == [13] and wh.sql[0] == "SELECT period, value FROM (...) LIMIT 13"


@pytest.mark.asyncio
async def test_no_series_rather_than_one_on_a_guessed_column(today):
    wh = Warehouse("2026-07")
    wh.generate_monthly_series_sql = lambda kpi, num_months=9: {"success": False, "sql": ""}
    v = await _sa(wh)._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    assert not any("LIMIT" in q for q in wh.sql)
    assert v.monthly_values is None and v.context.reference_day == "2026-09-30"  # calendar rule without a series
