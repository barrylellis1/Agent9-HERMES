 # arch-allow-direct-agent-construction
from types import SimpleNamespace
import pytest


@pytest.mark.asyncio
async def test_get_kpi_data_happy_path(data_product_agent, monkeypatch):
    agent = data_product_agent

    # Mock SQL generation
    async def mock_generate_sql_for_kpi(kpi_definition, timeframe=None, filters=None):
        return {"success": True, "sql": "SELECT 42 AS value"}

    # Mock SQL execution returning a dict row
    async def mock_execute_sql(sql, principal_context=None):
        return {
            "success": True,
            "columns": ["value"],
            "rows": [{"value": 123.45}],
            "execution_time": 0.01,
        }

    monkeypatch.setattr(agent, "generate_sql_for_kpi", mock_generate_sql_for_kpi)
    monkeypatch.setattr(agent, "execute_sql", mock_execute_sql)

    kpi_def = SimpleNamespace(name="Gross Revenue")
    resp = await agent.get_kpi_data(kpi_definition=kpi_def, timeframe=None, filters={})

    assert resp["status"] == "success"
    assert isinstance(resp["kpi_value"], (int, float))
    assert resp["kpi_value"] == 123.45


@pytest.mark.asyncio
async def test_get_kpi_data_no_rows(data_product_agent, monkeypatch):
    agent = data_product_agent

    async def mock_generate_sql_for_kpi(kpi_definition, timeframe=None, filters=None):
        return {"success": True, "sql": "SELECT 1"}

    async def mock_execute_sql(sql, principal_context=None):
        return {
            "success": True,
            "columns": ["value"],
            "rows": [],
            "execution_time": 0.01,
        }

    monkeypatch.setattr(agent, "generate_sql_for_kpi", mock_generate_sql_for_kpi)
    monkeypatch.setattr(agent, "execute_sql", mock_execute_sql)

    kpi_def = SimpleNamespace(name="Gross Revenue")
    resp = await agent.get_kpi_data(kpi_definition=kpi_def, timeframe=None, filters={})

    assert resp["status"] == "error"
    assert "No data" in resp["message"]


@pytest.mark.asyncio
async def test_get_kpi_comparison_data_happy_path(data_product_agent, monkeypatch):
    agent = data_product_agent

    async def mock_generate_sql_for_kpi_comparison(kpi_definition, timeframe=None, comparison_type="previous_period", filters=None):
        return {"success": True, "sql": "SELECT 84 AS value"}

    async def mock_execute_sql(sql, principal_context=None):
        return {
            "success": True,
            "columns": ["value"],
            "rows": [[456.78]],
            "execution_time": 0.02,
        }

    monkeypatch.setattr(agent, "generate_sql_for_kpi_comparison", mock_generate_sql_for_kpi_comparison)
    monkeypatch.setattr(agent, "execute_sql", mock_execute_sql)

    kpi_def = SimpleNamespace(name="Gross Revenue")
    resp = await agent.get_kpi_comparison_data(kpi_definition=kpi_def, timeframe=None, comparison_type="previous_period", filters={})

    assert resp["status"] == "success"
    assert resp["comparison_value"] == 456.78


# ---------------------------------------------------------------------------
# Phase 20 cleanup (2026-08-19) — generate_monthly_series_sql /
# _build_bq_monthly_series_sql, moved here from A9_Deep_Analysis_Agent where
# they were originally (wrongly) built directly in the calling agent,
# bypassing DPA entirely. See A9_Data_Product_Agent_card.md's Phase 20 entry
# and CLAUDE.md's SQL Backend Routing rule (§9). This is now the ONE place
# this SQL text gets generated for any DPA caller.
# ---------------------------------------------------------------------------

def _bq_kpi_def(sql_query, dp_id="nonexistent_dp_for_regex_fallback_test", metadata=None):
    return SimpleNamespace(id="cogs", name="cogs", sql_query=sql_query, calculation=None, data_product_id=dp_id, metadata=metadata or {})


class TestGenerateMonthlySeriesSql:
    def test_bigquery_kpi_generates_sql(self, data_product_agent):
        agent = data_product_agent
        kpi = _bq_kpi_def("SELECT SUM(amount) AS value FROM `proj.dataset.financials` WHERE transaction_date BETWEEN '2026-01-01' AND '2026-08-31'")
        result = agent.generate_monthly_series_sql(kpi, num_months=9)
        assert result["success"] is True
        assert "GROUP BY period" in result["sql"]
        assert "LIMIT 9" in result["sql"]
        # The hard date-range filter must be stripped — recency comes from LIMIT, not a fixed window.
        assert "BETWEEN" not in result["sql"]

    def test_non_bigquery_kpi_fails_gracefully(self):
        # No registry bootstrap needed — Tier-2 regex detection alone decides
        # this isn't BigQuery, so _resolve_source_system's registry lookup
        # (which would need a real data product) never has to resolve anything.
        from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
        agent = object.__new__(A9_Data_Product_Agent)
        import logging
        agent.logger = logging.getLogger("test.dpa_monthly_series")
        agent.registry_factory = None
        kpi = _bq_kpi_def("SELECT SUM([Amount]) AS value FROM [dbo].[Financials]", dp_id=None)
        result = agent.generate_monthly_series_sql(kpi)
        assert result["success"] is False
        assert result["sql"] == ""

    def test_no_stored_sql_fails_gracefully(self):
        from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
        agent = object.__new__(A9_Data_Product_Agent)
        import logging
        agent.logger = logging.getLogger("test.dpa_monthly_series")
        agent.registry_factory = None
        kpi = SimpleNamespace(id="cogs", name="cogs", sql_query=None, calculation=None, data_product_id=None, metadata={})
        result = agent.generate_monthly_series_sql(kpi)
        assert result["success"] is False

    def test_unparseable_sql_fails_gracefully_not_raise(self):
        from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
        agent = object.__new__(A9_Data_Product_Agent)
        import logging
        agent.logger = logging.getLogger("test.dpa_monthly_series")
        agent.registry_factory = None
        kpi = _bq_kpi_def("not valid sql at all but has a `proj.dataset.table` reference")
        result = agent.generate_monthly_series_sql(kpi)
        assert result["success"] is False
        assert result["sql"] == ""

    def test_custom_date_column_from_metadata_used(self, data_product_agent):
        agent = data_product_agent
        kpi = _bq_kpi_def(
            "SELECT SUM(amount) AS value FROM `proj.dataset.financials` WHERE fiscal_date BETWEEN '2026-01-01' AND '2026-08-31'",
            metadata={"date_column": "fiscal_date"},
        )
        result = agent.generate_monthly_series_sql(kpi)
        assert result["success"] is True
        assert "LEFT(fiscal_date, 7)" in result["sql"]

    def test_non_date_where_conditions_preserved(self, data_product_agent):
        agent = data_product_agent
        kpi = _bq_kpi_def(
            "SELECT SUM(amount) AS value FROM `proj.dataset.financials` "
            "WHERE transaction_date BETWEEN '2026-01-01' AND '2026-08-31' AND account_type = 'COGS'"
        )
        result = agent.generate_monthly_series_sql(kpi)
        assert result["success"] is True
        assert "account_type = 'COGS'" in result["sql"]
