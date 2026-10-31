"""Fiscal years that do not start in January (Phase 28 B, 2026-10-31).

A data product declares its fiscal start month and how it names a fiscal year (by the year it
starts or ends in); Agent9 translates, and refuses what is undeclared or unsupported. Chart labels
become calendar months so every reader (closed months, actuals cut-off, Value Assurance, the
screens) reads them correctly. A January year is unchanged.
"""
from __future__ import annotations

from datetime import date

import pytest

from src.database.time_filter import TimeFilter as TF

FYP = {"type": "fiscal_year_period", "year_column": "fiscal_year", "period_column": "fiscal_period"}
APRIL_END = dict(FYP, fiscal_year_start_month=4, fiscal_year_named_by="end")
APRIL_START = dict(FYP, fiscal_year_start_month=4, fiscal_year_named_by="start")


def test_january_needs_no_declaration():
    assert TF.fiscal_naming(FYP) == (1, 0)


def test_an_undeclared_non_january_year_is_refused():
    with pytest.raises(ValueError, match="fiscal_year_named_by"):
        TF.fiscal_naming(dict(FYP, fiscal_year_start_month=4))


def test_naming_by_the_end_year_adds_one():
    assert TF.fiscal_naming(APRIL_END) == (4, 1)
    assert TF.fiscal_naming(APRIL_START) == (4, 0)


@pytest.mark.parametrize("spec", [dict(FYP, calendar="4-4-5"), {"type": "date", "column": "d", "calendar": "52_53_week"}])
def test_a_calendar_other_than_months_is_refused(spec):
    with pytest.raises(ValueError, match="not supported"):
        TF.current_condition(spec, "ytd_vs_pytd@2026-01-31", dialect="snowflake")


def test_the_filter_uses_the_declared_name():
    # YTD to 31 Jan 2026 on an April year is fiscal periods 1-10: FY2026 when named by the end
    # year, FY2025 when named by the start year.
    end = TF.current_condition(APRIL_END, "ytd_vs_pytd@2026-01-31", dialect="snowflake")
    start = TF.current_condition(APRIL_START, "ytd_vs_pytd@2026-01-31", dialect="snowflake")
    assert "fiscal_year = 2026" in end and "BETWEEN 1 AND 10" in end
    assert "fiscal_year = 2025" in start and "BETWEEN 1 AND 10" in start
    prev = TF.previous_condition(APRIL_END, "ytd_vs_pytd@2026-01-31", dialect="snowflake")
    assert "fiscal_year = 2025" in prev


def test_the_legacy_words_use_the_declared_name_too(monkeypatch):
    monkeypatch.setattr(TF, "_today", staticmethod(lambda: date(2026, 1, 20)))
    assert "fiscal_year = 2026" in TF.current_condition(APRIL_END, "year_to_date", dialect="snowflake")


def test_january_labels_are_unchanged():
    assert TF.period_key_expr(FYP, "snowflake") == (
        "TO_VARCHAR(fiscal_year) || '-' || LPAD(TO_VARCHAR(CAST(fiscal_period AS INTEGER)), 2, '0')"
    )


def _labels(spec, year, periods):
    duckdb = pytest.importorskip("duckdb")
    con = duckdb.connect()
    con.execute("CREATE TABLE t (fiscal_year INTEGER, fiscal_period VARCHAR)")
    con.executemany("INSERT INTO t VALUES (?, ?)", [(year, f"{p:03d}") for p in periods])  # '001' text, as Hess
    expr = TF.period_key_expr(spec, "duckdb")
    return [r[0] for r in con.execute(f"SELECT {expr} FROM t ORDER BY CAST(fiscal_period AS INTEGER)").fetchall()]


def test_labels_become_calendar_months_named_by_the_end_year():
    labels = _labels(APRIL_END, 2026, range(1, 14))
    assert labels[:12] == ["2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09",
                           "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"]
    assert labels[12] is None  # period 13 is not a month (owner rule on year-end periods pending)


def test_labels_become_calendar_months_named_by_the_start_year():
    assert _labels(APRIL_START, 2026, [1, 9, 10, 12]) == ["2026-04", "2026-12", "2027-01", "2027-03"]


@pytest.mark.parametrize("start", range(2, 13))
def test_every_start_month_round_trips_with_the_filter(start):
    # The label of the period the filter computes for a calendar month is that calendar month.
    from src.analysis.period_comparisons import fiscal_year_period
    spec = dict(FYP, fiscal_year_start_month=start, fiscal_year_named_by="end")
    for month in range(1, 13):
        fy, p = fiscal_year_period(date(2026, month, 1), start)
        assert _labels(spec, fy + 1, [p]) == [f"2026-{month:02d}"]


def test_an_undeclared_year_reads_nothing_through_the_data_product_agent():
    from types import SimpleNamespace
    from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent as DPA
    agent = DPA.__new__(DPA)
    kpi = SimpleNamespace(name="Revenue", calculation=None, data_product_id="dp", metadata={},
                          sql_query="SELECT SUM(amount) AS value FROM V WHERE version = 'Actual'")
    out = agent.generate_period_sql(kpi, "ytd_vs_pytd@2026-01-31", time_spec=dict(FYP, fiscal_year_start_month=4),
                                    dialect="snowflake")
    assert out["success"] is False and "fiscal_year_named_by" in out["error"]
