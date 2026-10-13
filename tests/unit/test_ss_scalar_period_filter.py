# arch-allow-direct-agent-construction
"""SQL Server: an un-grouped total is filtered to its period.

Found live 2026-10-13 on Hess: the analysis's overall total was the all-time figure for both
the current and the prior period (1,996.9M vs 1,996.9M) because an un-grouped SQL Server
request skipped the builder and got the stored SQL back unfiltered.
"""
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent

RAW = "SELECT SUM([amount]) AS value FROM [dbo].[HessStarSchemaView] WHERE [account_type] = 'Revenue' AND [version] = 'Actual'"
SPEC = {"type": "fiscal_year_period", "year_column": "fiscal_year", "period_column": "fiscal_period"}


def _agent():
    a = A9_Data_Product_Agent.__new__(A9_Data_Product_Agent)
    a.logger = __import__("logging").getLogger("t")
    a.data_product_provider = None
    a.config = SimpleNamespace()
    a._resolve_source_system = lambda dp_id: "sqlserver"
    a._resolve_time_spec = lambda dp_id, kpi_definition=None: SPEC
    return a


def _kpi():
    return SimpleNamespace(id="production_revenue", name="Production Revenue", sql_query=RAW, calculation=RAW,
                           data_product_id="dp_hess", metadata={}, unit="$", dimensions=[], filters={})


@pytest.mark.asyncio
async def test_the_current_and_prior_totals_carry_different_period_filters():
    a = _agent()
    with patch("src.database.time_filter.TimeFilter._today", return_value=date(2026, 10, 13)):
        cur = await a.generate_sql_for_kpi(_kpi(), timeframe="quarter_to_date")
        prev = await a.generate_sql_for_kpi(_kpi(), timeframe="quarter_to_date", comparison_period=True)
    assert cur["success"] and prev["success"]
    assert "fiscal_year = 2026" in cur["sql"] and "BETWEEN 7 AND 9" in cur["sql"]
    assert "fiscal_year = 2025" in prev["sql"] and "BETWEEN 7 AND 9" in prev["sql"]
    assert cur["sql"] != prev["sql"] and cur["sql"].startswith(RAW)


@pytest.mark.asyncio
async def test_with_no_timeframe_the_stored_sql_is_returned_as_it_is():
    out = await _agent().generate_sql_for_kpi(_kpi(), timeframe=None)
    assert out["success"] and out["sql"].strip() == RAW
