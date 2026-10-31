# arch-allow-direct-agent-construction
"""Top-N share KPIs (2026-10-31, owner): "Top 3 Customer Revenue Share" for Apex.

The share cannot be one SELECT with the period condition appended: customers have to be ranked
after the period is chosen. The KPI stores the plain total (B2B revenue) and declares
metadata.top_n / metadata.rank_by; the Data Product Agent wraps the period-filtered query.
"""
from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent as DPA
from src.database.time_filter import TimeFilter

RAW = ("SELECT SUM(amount) AS value FROM LubricantsStarSchemaView WHERE channel_name = 'B2B Direct Sales' "
       "AND account_type = 'Revenue' AND version = 'Actual'")
FYP = {"type": "fiscal_year_period", "year_column": "fiscal_year", "period_column": "fiscal_period"}
TOKEN = "ytd_vs_pytd@2026-09-30"


def _kpi(md=None, sql=RAW):
    return SimpleNamespace(name="Top 3 Customer Revenue Share", calculation=None, sql_query=sql, data_product_id="dp",
                           metadata={"top_n": "3", "rank_by": "customer_name"} if md is None else md)


def _dpa(source="snowflake"):
    agent = DPA.__new__(DPA)
    agent.logger = logging.getLogger("t")
    agent._resolve_source_system = lambda dp: source
    agent._resolve_time_spec = lambda dp, kpi=None: FYP
    return agent


def test_a_declared_top_n_share_is_recognised():
    assert DPA.top_n_share(_kpi()) == ("customer_name", 3)
    assert DPA.top_n_share(_kpi(md={"line": "top"})) is None


@pytest.mark.parametrize("md", [{"top_n": "3"}, {"rank_by": "customer_name"}, {"top_n": "three", "rank_by": "c"},
                                {"top_n": "3", "rank_by": "customer_name; DROP TABLE x"}, {"top_n": "0", "rank_by": "c"}])
def test_a_half_or_bad_declaration_is_an_error_not_a_plain_total(md):
    with pytest.raises(ValueError):
        DPA.top_n_share(_kpi(md=md))


def test_the_period_is_chosen_before_customers_are_ranked():
    out = _dpa().generate_period_sql(_kpi(), TOKEN, time_spec=FYP, dialect="snowflake")
    cond = TimeFilter.current_condition(FYP, TOKEN, dialect="snowflake")
    assert out["success"]
    sql = out["sql"]
    inner = sql[: sql.index("), ranked AS")]
    assert cond in inner and "GROUP BY customer_name" in inner  # the period filter is inside the first step
    assert "ROW_NUMBER() OVER (ORDER BY value DESC)" in sql and "rn <= 3" in sql
    assert sql.rstrip().endswith("FROM ranked")


def test_the_previous_period_uses_the_previous_condition():
    out = _dpa().generate_period_sql(_kpi(), TOKEN, previous=True, time_spec=FYP, dialect="snowflake")
    assert TimeFilter.previous_condition(FYP, TOKEN, dialect="snowflake") in out["sql"]


def test_a_bad_declaration_reads_nothing():
    out = _dpa().generate_period_sql(_kpi(md={"top_n": "3"}), TOKEN, time_spec=FYP, dialect="snowflake")
    assert out["success"] is False and out["sql"] == ""


def test_a_multi_step_stored_query_cannot_be_wrapped():
    out = _dpa().generate_period_sql(_kpi(sql="WITH a AS (SELECT 1) SELECT x AS value FROM a"), TOKEN,
                                     time_spec=FYP, dialect="snowflake")
    assert out["success"] is False


@pytest.mark.parametrize("dialect,latest", [("snowflake", "LIMIT 9"), ("bigquery", "LIMIT 9"), ("sqlserver", "TOP 9")])
def test_the_monthly_series_ranks_within_each_month(dialect, latest):
    out = _dpa(source=dialect).generate_monthly_series_sql(_kpi(), num_months=9, time_spec=FYP, dialect=dialect)
    sql = out["sql"]
    assert out["success"] and latest in sql
    assert "PARTITION BY period ORDER BY value DESC" in sql
    assert f"GROUP BY {TimeFilter.period_key_expr(FYP, dialect)}, customer_name" in sql


def test_the_series_without_a_dialect_resolves_it():
    out = _dpa(source="snowflake").generate_monthly_series_sql(_kpi(), num_months=9)
    assert out["success"] and out["source_system"] == "snowflake"


@pytest.mark.asyncio
async def test_deep_analysis_gets_the_share_overall_and_no_breakdown():
    agent = _dpa()

    async def _noop():
        return None
    agent._refresh_data_product_registry = _noop
    overall = await agent.generate_sql_for_kpi(_kpi(), timeframe=TOKEN)
    split = await agent.generate_sql_for_kpi(_kpi(), timeframe=TOKEN, breakdown=True, override_group_by=["product_line"])
    assert overall["success"] and "rn <= 3" in overall["sql"]
    assert split["success"] is False and "not broken down" in split["message"]


# ── Deep Analysis says no segment was read (2026-10-31) ──

def _da():
    from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
    da = object.__new__(A9_Deep_Analysis_Agent)
    da.logger = logging.getLogger("t")
    return da


@pytest.mark.parametrize("mode", ["opportunity", "problem"])
def test_no_segments_means_no_invented_segments(mode):
    from src.agents.models.deep_analysis_models import DeepAnalysisPlan, KTIsIsNot
    from src.agents.new.a9_deep_analysis_agent import _NO_SEGMENTS_SENTENCE
    text = _da()._build_situation_complication_facts(
        plan=DeepAnalysisPlan(kpi_name="Top 3 Customer Revenue Share", client_id="apex_lubricants", timeframe="ytd_vs_pytd"),
        kt=KTIsIsNot(where_is=[], where_is_not=[]), change_points=[],
        spec={"comparison_type": "yoy", "inverse_logic": True}, analysis_mode=mode,
    )
    assert _NO_SEGMENTS_SENTENCE in text
    for filler in ("leading segments", "remaining segments", "key contributors identified", "concentrated in"):
        assert filler not in text
