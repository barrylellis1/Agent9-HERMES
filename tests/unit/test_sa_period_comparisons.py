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

    def __init__(self, last_month="2026-07", last_month_by_table=None):
        self.last_month = last_month
        self.last_month_by_table = last_month_by_table or {}  # a quieter KPI's own table
        self.sql = []

    async def execute_sql(self, sql, parameters=None, principal_context=None, data_product_id=None):
        self.sql.append(sql)
        if "LIMIT" in sql:  # the monthly series
            last = next((m for t, m in self.last_month_by_table.items() if t in sql), self.last_month)
            y, m = int(last[:4]), int(last[5:])
            months = [(y if k <= m else y - 1, k) for k in range(1, 13)]
            return {"rows": [{"period": f"{yy}-{mm:02d}", "value": 10.0} for yy, mm in months]}
        run = re.search(r"BETWEEN (\d{4})\d{2} AND (\d{4})\d{2}", sql)  # a span across fiscal years: its end year
        m = run and (None, run.group(2)) or re.search(r"BETWEEN '(\d{4})-", sql) or re.search(r"fiscal_year = (\d{4})", sql)
        year = run.group(2) if run else m.group(1)
        return {"rows": [[120.0 if year == "2026" else 100.0]]}


def _sa(warehouse, spec=FYP):
    sa = SA.__new__(SA)
    sa.logger = logging.getLogger("t")
    sa.data_product_agent = warehouse
    sa._last_sql_cache = {}
    sa._resolve_source_system = lambda dp: "bigquery"
    sa.kpi_registry = {"hess:Production Revenue": _kpi()}  # the product's KPIs, for its actuals cut-off

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
    # how a card names it (owner rulings B2, C): the months show where the actuals stop
    assert (ctx.period_short_label, ctx.period_months) == ("YTD vs PYTD", "Jan–Jul 2026 vs Jan–Jul 2025")
    assert (ctx.period_current_short, ctx.period_current_months) == ("YTD", "Jan–Jul 2026")
    assert SA._reading_label(v) == "YTD vs PYTD"


@pytest.mark.asyncio
async def test_a_current_feed_reads_to_the_last_closed_month_and_says_nothing_extra(today):
    wh = Warehouse("2026-12")  # the demo data holds later-dated rows
    v = await _sa(wh)._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    assert _span_filters(wh)[0] == ("2026-01-01", "2026-09-30")
    assert v.context.actuals_end is None
    assert v.context.period_months == "Jan–Sep 2026 vs Jan–Sep 2025"


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
async def test_a_february_scan_falls_back_to_the_last_12_months(february):
    """Owner ruling 2: a financial year to date holding one closed month is read on the last 12
    months, judged on its year-to-date targets, and may raise a card."""
    wh = Warehouse("2026-12")
    v = await _sa(wh)._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    c = v.context
    assert (c.period_comparison, c.fallback_from) == ("ltm_vs_prior_ltm", "ytd_vs_pytd")
    assert (c.window_start, c.window_end) == ("2025-02-01", "2026-01-31")
    assert c.card_hold_reason is None and c.plan_card_hold_reason is None
    # the card says what it read, not what it stands in for
    assert (c.period_short_label, c.period_months) == ("LTM vs Prior LTM", "Feb 2025–Jan 2026 vs Feb 2024–Jan 2025")


@pytest.mark.asyncio
async def test_a_quarter_reading_is_context_unless_the_client_turns_quarters_on(today):
    v = await _sa(Warehouse("2026-12"))._get_kpi_value(
        _kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {}, period_comparison="quarter_vs_py_quarter")
    assert v.context.card_hold_reason == "Quarter vs same quarter previous year is shown for context; it does not raise cards here."
    # the data product turns quarter cards on (no per-KPI exceptions, ruling 3)
    from src.analysis.period_settings import PeriodSettings
    sa = _sa(Warehouse("2026-12"))

    async def _with_quarters(dp_id, keyed):
        return PeriodSettings(card_comparisons=["ytd_vs_pytd", "quarter_vs_py_quarter"]), None
    sa._period_settings_cached = _with_quarters
    v = await sa._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {},
                                period_comparison="quarter_vs_py_quarter")
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
    # no covenant/regulatory exemption (owner ruling 5)
    assert [s.alert_type for s in kept] == ["projected_breach", "acceleration"]
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
    # asked for the product's cut-off and for the reading, read from the warehouse once
    assert asked and set(asked) == {13}
    assert wh.sql.count("SELECT period, value FROM (...) LIMIT 13") == 1


@pytest.mark.asyncio
async def test_no_series_rather_than_one_on_a_guessed_column(today):
    wh = Warehouse("2026-07")
    wh.generate_monthly_series_sql = lambda kpi, num_months=9: {"success": False, "sql": ""}
    v = await _sa(wh)._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    assert not any("LIMIT" in q for q in wh.sql)
    assert v.monthly_values is None and v.context.reference_day == "2026-09-30"  # calendar rule without a series



# ── Step 3f(2): the actuals cut-off is the data product's, across all its KPIs (decision 7) ──

@pytest.mark.asyncio
async def test_a_quiet_kpi_takes_its_data_products_cut_off(today):
    """A seasonal cost with nothing posted after July, in a product whose other KPIs run to
    September: read to September like its siblings, not as a stopped feed."""
    quiet = _kpi()
    quiet.name, quiet.calculation = "Exploration Expense", "SELECT SUM(amount) AS value FROM `p.d.QuietView` WHERE version = 'Actual'"
    quiet.sql_query = quiet.calculation
    busy = _kpi()
    wh = Warehouse("2026-09", last_month_by_table={"QuietView": "2026-07"})
    sa = _sa(wh)
    sa.kpi_registry = {"hess:Exploration Expense": quiet, "hess:Production Revenue": busy}
    v = await sa._get_kpi_value(quiet, TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    assert v.context.reference_day == "2026-09-30" and v.context.actuals_end is None
    assert _span_filters(wh)[0] == ("2026-01-01", "2026-09-30")


@pytest.mark.asyncio
async def test_a_stopped_feed_stops_the_whole_product(today):
    wh = Warehouse("2026-07")
    sa = _sa(wh)
    other = _kpi()
    other.name = "Total Revenue"
    sa.kpi_registry = {"hess:Production Revenue": _kpi(), "hess:Total Revenue": other}
    v = await sa._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {})
    assert (v.context.reference_day, v.context.actuals_end) == ("2026-07-31", "2026-07-31")


# ── Phase 26 step 3f(3): the dashboard reads each data product's comparison; cards name it ──

@pytest.mark.asyncio
async def test_the_dashboard_reads_the_data_products_own_comparison(today):
    """Owner ruling 8: asked for the product reading, an operational product reads the last 12
    months whatever the request words say; a financial one reads YTD."""
    from src.analysis.period_settings import PeriodSettings
    sa = _sa(Warehouse("2026-12"))

    async def _operational(dp_id, keyed):
        return PeriodSettings(kind="operational"), None
    sa._period_settings_cached = _operational
    v = await sa._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {},
                                product_reading=True)
    c = v.context
    assert (c.period_comparison, c.period_short_label) == ("ltm_vs_prior_ltm", "LTM vs Prior LTM")
    assert c.period_months == "Oct 2025–Sep 2026 vs Oct 2024–Sep 2025"

    v = await _sa(Warehouse("2026-12"))._get_kpi_value(_kpi(), TimeFrame.CURRENT_QUARTER, ComparisonType.YEAR_OVER_YEAR, {},
                                                        product_reading=True)
    assert v.context.period_comparison == "ytd_vs_pytd"  # financial, the default kind


@pytest.mark.asyncio
async def test_a_named_comparison_wins_over_the_product_reading(today):
    v = await _sa(Warehouse("2026-12"))._get_kpi_value(_kpi(), TimeFrame.YEAR_TO_DATE, ComparisonType.YEAR_OVER_YEAR, {},
                                                        period_comparison="quarter_vs_py_quarter", product_reading=True)
    assert (v.context.period_comparison, v.context.period_short_label) == ("quarter_vs_py_quarter", "Q3 vs PY Q3")


def test_cards_take_the_readings_label_unless_they_set_their_own():
    from src.agents.models.situation_awareness_models import KPIValue, Situation, SituationSeverity
    ctx = MeasurementContext(period_short_label="YTD vs PYTD", period_months="Jan–Sep 2026 vs Jan–Sep 2025")
    kv = KPIValue(kpi_name="Net Revenue", value=1.0, timeframe=TimeFrame.YEAR_TO_DATE, context=ctx)

    def card(**kw):
        return Situation(situation_id="x", kpi_name="Net Revenue", kpi_value=kv, severity=SituationSeverity.HIGH,
                         description="d", business_impact="b", **kw)
    breach, plan = card(), card(alert_type="plan_variance", comparison_label="YTD Act vs Budget", period_months="Jan–Sep 2026")
    SA._label_cards([breach, plan], kv)
    assert (breach.comparison_label, breach.period_months) == ("YTD vs PYTD", "Jan–Sep 2026 vs Jan–Sep 2025")
    assert (plan.comparison_label, plan.period_months) == ("YTD Act vs Budget", "Jan–Sep 2026")


def test_a_series_names_its_months():
    from src.agents.new.a9_situation_awareness_agent import _series_months
    series = [{"period": f"2026-{m:02d}", "value": 1.0} for m in range(1, 10)]
    assert _series_months(series) == "Jan–Sep 2026"
    assert _series_months(series[-6:]) == "Apr–Sep 2026"
    assert _series_months([]) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("body, product_reading, named", [
    ({}, True, None),                                            # the dashboard sends no period
    ({"timeframe": "current_quarter"}, False, None),             # an old caller keeps its words
    ({"period_comparison": "quarter_vs_py_quarter"}, False, "quarter_vs_py_quarter"),
])
async def test_the_route_asks_for_the_product_reading_when_no_period_is_given(monkeypatch, body, product_reading, named):
    """Owner ruling 8: with no period in the request each KPI is read on its data product's
    comparison; a caller naming a timeframe or a comparison keeps it."""
    from src.api.routes import workflows
    seen = {}

    class _Orch:
        async def execute_agent_method(self, agent, method, args):
            return {"context": {"principal_id": "cfo_001", "role": "CFO", "business_processes": ["finance"],
                                "default_filters": {}, "decision_style": "analytical",
                                "communication_style": "concise", "preferred_timeframes": ["year_to_date"]}}

        async def orchestrate_situation_detection(self, request):
            seen["request"] = request
            return {"status": "error", "message": "stop here"}

    async def _record(request_id, **updates):
        return None
    monkeypatch.setattr(workflows, "_update_record", _record)
    runtime = SimpleNamespace(get_orchestrator=lambda: _Orch())
    await workflows._run_situations_workflow(
        "r1", runtime, workflows.SituationWorkflowRequest(principal_id="cfo_001", client_id="lubricants", **body))
    r = seen["request"]
    assert (r.use_data_product_reading, r.period_comparison) == (product_reading, named)
