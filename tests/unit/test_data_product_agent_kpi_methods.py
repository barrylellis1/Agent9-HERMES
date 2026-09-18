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


@pytest.fixture
def agent_with_fiscal_spec(data_product_agent):
    """DPA whose data product declares a fiscal_year_period time dimension and
    no date column at all -- the shape of dp_lubricants_sales."""
    data_product_agent._resolve_time_spec = lambda dp_id, kpi_definition=None: {
        "type": "fiscal_year_period",
        "year_column": "fiscal_year",
        "period_column": "fiscal_period",
        "period_column_type": "string",
    }
    return data_product_agent


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
        # Phase 25 step 1 changed the EXPRESSION (LEFT(col,7) ->
        # FORMAT_DATE('%Y-%m', ...)) but not the guarantee this test exists to
        # pin: an explicit per-KPI date_column still wins over the data
        # product's declared spec.
        assert "fiscal_date" in result["sql"]
        assert "FORMAT_DATE('%Y-%m'" in result["sql"]
        assert "transaction_date" not in result["sql"]

    # ── Phase 25 step 1 — canonical period key ──────────────────────────────

    def test_fiscal_year_period_product_uses_normalized_key_not_display_expr(self, agent_with_fiscal_spec):
        """The bug this phase exists for.

        A sales-style product keyed on fiscal_year + fiscal_period has NO date
        column. Before this change the builder emitted SQL against a
        hardcoded `transaction_date`, which does not exist on that view: the
        query failed, the fetch swallowed it, and the trend line vanished with
        no error. It must now key off the declared fiscal columns.
        """
        agent = agent_with_fiscal_spec
        kpi = _bq_kpi_def("SELECT COUNT(DISTINCT sales_order_id) AS value FROM `proj.dataset.sales`")
        result = agent.generate_monthly_series_sql(kpi)
        assert result["success"] is True
        assert "transaction_date" not in result["sql"]
        assert "fiscal_year" in result["sql"] and "fiscal_period" in result["sql"]

    def test_fiscal_period_padding_is_normalized_to_two_digits(self, agent_with_fiscal_spec):
        """Both lubricants generators write fiscal_period as f"{m:03d}" -- a
        3-digit string. The product's own `display_expr` would therefore yield
        "2026-005" while the date path yields "2026-05", producing two disjoint
        axes and no error anywhere. The key must CAST to INT and re-pad to 2.
        """
        agent = agent_with_fiscal_spec
        kpi = _bq_kpi_def("SELECT SUM(net_amount) AS value FROM `proj.dataset.sales`")
        sql = agent.generate_monthly_series_sql(kpi)["sql"]
        assert "AS INT64" in sql, "period must be cast to INT to normalize '005' -> 5"
        assert "LPAD(" in sql and ", 2, '0')" in sql, "period must be re-padded to 2 digits"

    def test_date_and_fiscal_products_agree_on_key_shape(self, data_product_agent, agent_with_fiscal_spec):
        """Cross-product alignment is the whole point: a date-keyed product and
        a fiscal-keyed one must emit the same YYYY-MM shape, or a causal edge
        between their KPIs cannot be affirmed.
        """
        from src.database.time_filter import TimeFilter

        date_key = TimeFilter.period_key_expr({"type": "date", "column": "transaction_date"}, "bigquery")
        fiscal_key = TimeFilter.period_key_expr(
            {"type": "fiscal_year_period", "year_column": "fiscal_year", "period_column": "fiscal_period"},
            "bigquery",
        )
        assert date_key and fiscal_key and date_key != fiscal_key
        assert TimeFilter.period_key_grain({"type": "date"}) == "month"
        assert TimeFilter.period_key_grain({"type": "fiscal_year_period"}) == "month"
        # fiscal_year products are annual -- comparing one against a monthly
        # series is a grain mismatch a caller must refuse, not silently plot.
        assert TimeFilter.period_key_grain({"type": "fiscal_year"}) == "year"

    def test_unusable_time_spec_fails_gracefully(self, data_product_agent, monkeypatch):
        agent = data_product_agent
        monkeypatch.setattr(agent, "_resolve_time_spec", lambda dp_id, kpi_definition=None: {"type": "date", "column": ""})
        kpi = _bq_kpi_def("SELECT SUM(amount) AS value FROM `proj.dataset.financials`")
        result = agent.generate_monthly_series_sql(kpi)
        assert result["success"] is False
        assert "time dimension" in result["message"].lower()

    def test_non_date_where_conditions_preserved(self, data_product_agent):
        agent = data_product_agent
        kpi = _bq_kpi_def(
            "SELECT SUM(amount) AS value FROM `proj.dataset.financials` "
            "WHERE transaction_date BETWEEN '2026-01-01' AND '2026-08-31' AND account_type = 'COGS'"
        )
        result = agent.generate_monthly_series_sql(kpi)
        assert result["success"] is True
        assert "account_type = 'COGS'" in result["sql"]
