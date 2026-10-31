# arch-allow-direct-agent-construction
"""Period and plan SQL are built by the Data Product Agent only (2026-10-31).

The scan used to add the period condition to a warehouse KPI's SQL itself, and the Budget variant
of a KPI's SQL was written twice (the scan and Deep Analysis). Both now live in the Data Product
Agent; the scan asks for them. Live check at the move: 146 queries across Lubricants (BigQuery),
Apex (Snowflake) and Hess (SQL Server) were identical before and after.
"""
from __future__ import annotations

import inspect
from types import SimpleNamespace

from src.agents.new import a9_deep_analysis_agent as da_mod
from src.agents.new import a9_situation_awareness_agent as sa_mod
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent as DPA
from src.database.time_filter import TimeFilter

RAW = "SELECT SUM(amount) AS value FROM View WHERE version = 'Actual'"
FYP = {"type": "fiscal_year_period", "year_column": "fiscal_year", "period_column": "fiscal_period"}


def _kpi(sql=RAW, dp="dp_x"):
    return SimpleNamespace(name="Net Revenue", calculation=sql, sql_query=sql, data_product_id=dp)


def _dpa(source="snowflake", spec=FYP):
    agent = DPA.__new__(DPA)
    agent._resolve_source_system = lambda dp: source
    agent._resolve_time_spec = lambda dp, kpi=None: spec
    return agent


def test_the_current_period_is_the_kpi_sql_with_its_period_condition():
    out = _dpa().generate_period_sql(_kpi(), "ytd_vs_pytd@2026-09-30", time_spec=FYP, dialect="snowflake")
    cond = TimeFilter.current_condition(FYP, "ytd_vs_pytd@2026-09-30", dialect="snowflake")
    assert out == {"success": True, "sql": TimeFilter.append_condition(RAW, cond)}


def test_the_previous_period_uses_the_previous_condition():
    out = _dpa().generate_period_sql(_kpi(), "ytd_vs_pytd@2026-09-30", previous=True, time_spec=FYP, dialect="snowflake")
    cond = TimeFilter.previous_condition(FYP, "ytd_vs_pytd@2026-09-30", dialect="snowflake")
    assert out["sql"] == TimeFilter.append_condition(RAW, cond)


def test_spec_and_dialect_are_resolved_when_not_given():
    given = _dpa(source="sqlserver").generate_period_sql(_kpi(), "ytd_vs_pytd@2026-09-30", time_spec=FYP, dialect="sqlserver")
    resolved = _dpa(source="sqlserver").generate_period_sql(_kpi(), "ytd_vs_pytd@2026-09-30")
    assert given == resolved


def test_a_kpi_without_sql_gets_no_query():
    out = _dpa().generate_period_sql(_kpi(sql=""), "ytd_vs_pytd@2026-09-30", time_spec=FYP, dialect="snowflake")
    assert out["success"] is False and out["sql"] == ""


def test_never_a_query_without_a_period_filter(monkeypatch):
    monkeypatch.setattr(TimeFilter, "current_condition", classmethod(lambda cls, *a, **k: None))
    out = _dpa().generate_period_sql(_kpi(), "ytd_vs_pytd@2026-09-30", time_spec=FYP, dialect="snowflake")
    assert out["success"] is False and out["sql"] == ""


def test_the_plan_variant_swaps_actual_for_the_plan_version():
    assert DPA.derive_plan_sql(RAW, "Budget") == RAW.replace("'Actual'", "'Budget'")
    assert DPA.derive_plan_sql("SELECT 1", "Budget") is None


def test_the_scan_and_deep_analysis_no_longer_build_this_sql():
    sa_src, da_src = inspect.getsource(sa_mod), inspect.getsource(da_mod)
    for needle in ("append_condition(", "current_condition(", "previous_condition(", "def _derive_plan_sql"):
        assert needle not in sa_src, needle
    assert "def _derive_budget_sql" not in da_src


# ── Step 2 (2026-10-31): the monthly-series builders moved too ──

def test_the_scan_contains_no_sql_at_all():
    src = inspect.getsource(sa_mod)
    for needle in ("def _bq_monthly_series_sql", "def _ss_monthly_series_sql", "def _sf_monthly_series_sql",
                   "SELECT ", "GROUP BY", "ORDER BY"):
        assert needle not in src, needle


def _series_dpa(spec):
    import logging
    agent = DPA.__new__(DPA)
    agent.logger = logging.getLogger("t")
    agent._resolve_time_spec = lambda dp, kpi=None: spec
    return agent


SF_RAW = "SELECT SUM(amount) AS value FROM STAR_VIEW WHERE account_type = 'Revenue' AND version = 'Actual'"
SS_RAW = "SELECT SUM([amount]) AS value FROM [dbo].[HessView] WHERE [version] = 'Actual'"


def test_snowflake_and_sql_server_series_use_the_fiscal_period_builders():
    sf = _series_dpa(FYP).generate_monthly_series_sql(_kpi(SF_RAW), num_months=9, time_spec=FYP, dialect="snowflake")
    ss = _series_dpa(FYP).generate_monthly_series_sql(_kpi(SS_RAW), num_months=9, time_spec=FYP, dialect="sqlserver")
    assert sf["success"] and sf["sql"] == _series_dpa(FYP)._build_sf_monthly_series_sql(SF_RAW, num_months=9)
    assert ss["success"] and ss["sql"] == _series_dpa(FYP)._build_ss_monthly_series_sql(SS_RAW, num_months=9)


def test_a_date_keyed_warehouse_series_groups_on_the_date_column():
    spec = {"type": "date", "column": "transaction_date"}
    out = _series_dpa(spec).generate_monthly_series_sql(_kpi(SF_RAW), num_months=9, time_spec=spec, dialect="snowflake")
    assert out["sql"] == _series_dpa(spec)._build_date_monthly_series_sql(SF_RAW, date_col="transaction_date", num_months=9)


def test_a_series_around_generated_sql():
    out = _series_dpa(FYP).generate_monthly_series_from_sql(SF_RAW, date_col="transaction_date", num_months=9)
    assert out["success"] and "LIMIT 9" in out["sql"]
