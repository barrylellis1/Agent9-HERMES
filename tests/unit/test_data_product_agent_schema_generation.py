# arch-allow-direct-agent-construction
"""
Phase 12G — Quality Schema Generation unit tests.

Covers:
  - _infer_semantic_tags: fiscal_year/fiscal_period columns tag as "time", not "measure"
  - _detect_time_dimension_for_table / _synthesize_time_dimensions: fiscal pair,
    fiscal-year-only, single date column (business-date vs audit-timestamp ranking),
    no candidates, primary=True selection across multiple tables
  - _derive_tables_and_views: view vs. physical-table branching
  - register_data_product: schema_summary wiring end-to-end
  - sync_related_business_processes: union/dedup + client_id-mismatch rejection
  - _build_connection_config_for_source: snowflake/sqlserver config building
    (validate_kpi_queries previously only handled duckdb/bigquery here,
    silently connecting with an empty config for other backends)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.models.data_product_onboarding_models import (
    DataProductBusinessProcessSyncRequest,
    DataProductRegistrationRequest,
    ForeignKeyRelationship,
    TableColumnProfile,
    TableProfile,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def agent():
    config = {
        "agent_id": "test_dpa",
        "database": {"type": "duckdb", "path": ":memory:"},
        "bypass_mcp": True,
        "registry_factory": MagicMock(),
    }
    return A9_Data_Product_Agent(config=config)  # arch-allow-agent-ctor


def _col(name: str, data_type: str, semantic_tags) -> TableColumnProfile:
    return TableColumnProfile(name=name, data_type=data_type, semantic_tags=semantic_tags)


# ---------------------------------------------------------------------------
# _infer_semantic_tags — fiscal_year/fiscal_period bugfix
# ---------------------------------------------------------------------------

def test_fiscal_year_period_columns_tag_as_time_not_measure(agent):
    assert agent._infer_semantic_tags("fiscal_year", "INTEGER") == ["time"]
    assert agent._infer_semantic_tags("fiscal_period", "INTEGER") == ["time"]
    assert agent._infer_semantic_tags("FISCAL_QTR", "NUMBER") == ["time"]


def test_bare_year_period_quarter_tokens_do_not_false_positive(agent):
    """Compound tokens only — bare 'year'/'period'/'quarter' must not hijack
    legitimate measure/dimension columns."""
    assert agent._infer_semantic_tags("warranty_years", "INTEGER") == ["measure"]
    assert agent._infer_semantic_tags("trial_period_days", "INTEGER") == ["measure"]
    assert agent._infer_semantic_tags("model_year", "VARCHAR") == ["dimension"]


# ---------------------------------------------------------------------------
# _detect_time_dimension_for_table
# ---------------------------------------------------------------------------

def test_detects_fiscal_year_period_pair(agent):
    table = TableProfile(
        name="LubricantsStarSchemaView",
        columns=[
            _col("fiscal_year", "INTEGER", ["time"]),
            _col("fiscal_period", "INTEGER", ["time"]),
            _col("amount", "NUMBER", ["measure"]),
        ],
    )
    spec = agent._detect_time_dimension_for_table(table)
    assert spec["type"] == "fiscal_year_period"
    assert spec["year_column"] == "fiscal_year"
    assert spec["period_column"] == "fiscal_period"
    assert spec["period_type"] == "month"
    assert spec["period_column_type"] == "integer"
    assert spec["display_expr"] == "CONCAT(CAST(fiscal_year AS VARCHAR), '-', fiscal_period)"
    assert spec["sort_expr"] == "fiscal_year * 100 + CAST(fiscal_period AS INTEGER)"


def test_detects_fiscal_quarter_as_quarter_granularity_and_string_type(agent):
    table = TableProfile(
        name="t",
        columns=[
            _col("fiscal_year", "INTEGER", ["time"]),
            _col("fiscal_qtr", "VARCHAR", ["time"]),
        ],
    )
    spec = agent._detect_time_dimension_for_table(table)
    assert spec["type"] == "fiscal_year_period"
    assert spec["period_type"] == "quarter"
    assert spec["period_column_type"] == "string"


def test_detects_fiscal_year_alone(agent):
    table = TableProfile(
        name="t",
        columns=[_col("fiscal_year", "INTEGER", ["time"])],
    )
    spec = agent._detect_time_dimension_for_table(table)
    assert spec == {"type": "fiscal_year", "year_column": "fiscal_year", "granularity": "year", "label": "Fiscal Year"}


def test_detects_single_date_column(agent):
    table = TableProfile(
        name="t",
        columns=[_col("transaction_date", "DATE", ["time"])],
    )
    spec = agent._detect_time_dimension_for_table(table)
    assert spec == {
        "type": "date", "column": "transaction_date", "granularity": "day", "label": "Transaction Date",
    }


def test_business_date_ranked_above_audit_timestamp(agent):
    """When both a business date and an audit timestamp exist, prefer the business one."""
    table = TableProfile(
        name="t",
        columns=[
            _col("created_at", "TIMESTAMP", ["time"]),
            _col("order_date", "DATE", ["time"]),
            _col("updated_at", "TIMESTAMP", ["time"]),
        ],
    )
    spec = agent._detect_time_dimension_for_table(table)
    assert spec["type"] == "date"
    assert spec["column"] == "order_date"


def test_no_time_columns_returns_none(agent):
    table = TableProfile(
        name="t",
        columns=[_col("amount", "NUMBER", ["measure"]), _col("product_id", "VARCHAR", ["identifier"])],
    )
    assert agent._detect_time_dimension_for_table(table) is None


# ---------------------------------------------------------------------------
# _synthesize_time_dimensions — primary selection across tables
# ---------------------------------------------------------------------------

def test_synthesize_empty_when_nothing_found(agent):
    tables = [TableProfile(name="t", columns=[_col("amount", "NUMBER", ["measure"])])]
    assert agent._synthesize_time_dimensions(tables) == []


def test_synthesize_prefers_fact_table_as_primary(agent):
    dim_table = TableProfile(
        name="dim_date", table_role="DIMENSION",
        columns=[_col("effective_date", "DATE", ["time"])],
    )
    fact_table = TableProfile(
        name="fact_sales", table_role="FACT",
        columns=[_col("transaction_date", "DATE", ["time"])],
    )
    result = agent._synthesize_time_dimensions([dim_table, fact_table])
    assert len(result) == 2
    primaries = [r for r in result if r["primary"]]
    assert len(primaries) == 1
    assert primaries[0]["column"] == "transaction_date"


def test_synthesize_falls_back_to_first_when_no_fact_table(agent):
    t1 = TableProfile(name="t1", columns=[_col("order_date", "DATE", ["time"])])
    t2 = TableProfile(name="t2", columns=[_col("posting_date", "DATE", ["time"])])
    result = agent._synthesize_time_dimensions([t1, t2])
    primaries = [r for r in result if r["primary"]]
    assert len(primaries) == 1
    assert primaries[0]["column"] == "order_date"


# ---------------------------------------------------------------------------
# _derive_tables_and_views
# ---------------------------------------------------------------------------

def test_derive_tables_and_views_splits_by_view_definition(agent):
    view = TableProfile(name="MyView", view_definition="SELECT * FROM base_table")
    table = TableProfile(
        name="base_table",
        columns=[_col("id", "INTEGER", ["identifier"]), _col("amount", "NUMBER", ["measure"])],
        primary_keys=["id"],
        foreign_keys=[
            ForeignKeyRelationship(
                source_table="base_table", source_column="customer_id",
                target_table="customers", target_column="id",
            )
        ],
    )
    tables_out, views_out = agent._derive_tables_and_views([view, table])

    assert "MyView" in views_out
    assert views_out["MyView"]["sql_definition"] == "SELECT * FROM base_table"

    assert "base_table" in tables_out
    assert tables_out["base_table"]["column_schema"] == {"id": "INTEGER", "amount": "NUMBER"}
    assert tables_out["base_table"]["primary_keys"] == ["id"]
    assert tables_out["base_table"]["foreign_keys"] == {"customer_id": "customers.id"}
    assert tables_out["base_table"]["data_source_type"] == "database"


# ---------------------------------------------------------------------------
# register_data_product — schema_summary wiring end-to-end
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_data_product_populates_tables_views_time_dimensions(agent):
    agent.data_product_provider = MagicMock()
    agent.data_product_provider.get.return_value = None
    agent.data_product_provider.upsert = AsyncMock(return_value=True)
    agent.data_product_provider.source_path = None

    schema_summary = [
        TableProfile(
            name="LubricantsStarSchemaView",
            view_definition="SELECT * FROM base",
            columns=[
                _col("fiscal_year", "INTEGER", ["time"]),
                _col("fiscal_period", "INTEGER", ["time"]),
                _col("amount", "NUMBER", ["measure"]),
            ],
            table_role="FACT",
        )
    ]

    request = DataProductRegistrationRequest(
        request_id="req1", principal_id="admin_user", data_product_id="dp_test",
        client_id="brookshire_brothers", source_system="snowflake",
        display_name="Test", domain="Finance",
        schema_summary=schema_summary,
    )

    response = await agent.register_data_product(request)

    assert response.status == "success"
    entry = response.registry_entry
    assert "LubricantsStarSchemaView" in entry["views"]
    assert entry["time_dimensions"][0]["type"] == "fiscal_year_period"
    assert entry["time_dimensions"][0]["primary"] is True


# ---------------------------------------------------------------------------
# sync_related_business_processes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sync_unions_and_dedupes_business_processes(agent):
    existing = MagicMock()
    existing.client_id = "brookshire_brothers"
    existing.related_business_processes = ["finance_expense_management"]

    agent.data_product_provider = MagicMock()
    agent.data_product_provider.get.return_value = existing
    agent.data_product_provider.upsert = AsyncMock(return_value=True)

    request = DataProductBusinessProcessSyncRequest(
        request_id="req1", principal_id="system", data_product_id="dp_test",
        client_id="brookshire_brothers",
        business_process_ids=["finance_expense_management", "finance_revenue_growth_analysis"],
    )

    response = await agent.sync_related_business_processes(request)

    assert response.status == "success"
    assert response.related_business_processes == [
        "finance_expense_management", "finance_revenue_growth_analysis",
    ]
    assert existing.related_business_processes == [
        "finance_expense_management", "finance_revenue_growth_analysis",
    ]


@pytest.mark.asyncio
async def test_sync_rejects_client_id_mismatch(agent):
    existing = MagicMock()
    existing.client_id = "apex_lubricants"

    agent.data_product_provider = MagicMock()
    agent.data_product_provider.get.return_value = existing
    agent.data_product_provider.upsert = AsyncMock(return_value=True)

    request = DataProductBusinessProcessSyncRequest(
        request_id="req1", principal_id="system", data_product_id="dp_test",
        client_id="brookshire_brothers", business_process_ids=["finance_expense_management"],
    )

    response = await agent.sync_related_business_processes(request)

    assert response.status == "error"
    assert "brookshire_brothers" in response.error_message
    agent.data_product_provider.upsert.assert_not_called()


# ---------------------------------------------------------------------------
# _build_connection_config_for_source
# ---------------------------------------------------------------------------

def test_connection_config_snowflake_uses_overrides_not_empty(agent, monkeypatch):
    """Regression test: validate_kpi_queries previously had no snowflake
    branch at all, silently connecting with connection_config={} and failing
    with a confusing 'password or private_key must be provided' error even
    when the caller supplied full connection_overrides."""
    # Force the password branch regardless of this machine's local .env —
    # SF_PRIVATE_KEY_PATH/SF_PRIVATE_KEY being set would otherwise route
    # through key-pair auth instead, and the test only cares that overrides
    # (not empty/ambient config) drive the result either way.
    monkeypatch.delenv("SF_PRIVATE_KEY_PATH", raising=False)
    monkeypatch.delenv("SF_PRIVATE_KEY", raising=False)

    overrides = {
        "account": "VSGHWKW-SI38932", "warehouse": "AGENT9_WH", "database": "AGENT9_DEMO",
        "schema": "LUBRICANTS", "role": "ACCOUNTADMIN", "username": "BARRYLELLIS1", "password": "secret",
    }
    config, params = agent._build_connection_config_for_source("snowflake", None, None, overrides)

    assert config["account"] == "VSGHWKW-SI38932"
    assert config["warehouse"] == "AGENT9_WH"
    assert config["database"] == "AGENT9_DEMO"
    assert config["schema"] == "LUBRICANTS"
    assert params["user"] == "BARRYLELLIS1"
    assert params["password"] == "secret"


def test_connection_config_sqlserver_uses_overrides(agent):
    overrides = {"host": "sql.example.com", "database": "agent9_hess", "username": "svc", "password": "pw"}
    config, params = agent._build_connection_config_for_source("sqlserver", None, None, overrides)

    assert config["type"] == "sqlserver"
    assert config["host"] == "sql.example.com"
    assert config["database"] == "agent9_hess"
    assert config["username"] == "svc"
    assert config["password"] == "pw"


def test_connection_config_unknown_source_returns_empty_not_raises(agent):
    config, params = agent._build_connection_config_for_source("unknown_backend", None, None, {})
    assert config == {}
    assert params == {}


# ---------------------------------------------------------------------------
# Categorical value sampling — closes the gap where KPI SQL generation only
# ever saw a column's name+type and had to guess WHERE-filter literals
# ---------------------------------------------------------------------------

def test_is_categorical_candidate_selects_text_excludes_ids_and_tagged_columns(agent):
    text_col = _col("ACCOUNT_CATEGORY", "TEXT", ["dimension"])
    id_col = _col("GL_ACCOUNT_ID", "TEXT", ["identifier"])
    time_col = _col("TRANSACTION_DATE", "DATE", ["time"])
    measure_col = _col("AMOUNT", "NUMBER", ["measure"])

    assert agent._is_categorical_candidate(text_col, primary_keys=[], fk_source_columns=set())
    assert not agent._is_categorical_candidate(id_col, primary_keys=["GL_ACCOUNT_ID"], fk_source_columns=set())
    assert not agent._is_categorical_candidate(time_col, primary_keys=[], fk_source_columns=set())
    assert not agent._is_categorical_candidate(measure_col, primary_keys=[], fk_source_columns=set())
    # FK source column excluded even without a matching primary_keys entry
    assert not agent._is_categorical_candidate(text_col, primary_keys=[], fk_source_columns={"ACCOUNT_CATEGORY"})


@pytest.mark.asyncio
async def test_sample_distinct_values_snowflake_builds_correct_query(agent):
    manager = AsyncMock()
    manager.execute_query.return_value = {"rows": [{"sample_value": "Product Sales"}, {"sample_value": "Raw Materials"}]}

    values = await agent._sample_distinct_values(
        manager, "snowflake", "FINANCIALTRANSACTIONS", "ACCOUNT_CATEGORY",
        {"schema": "LUBRICANTS", "project": "AGENT9_DEMO"},
    )

    assert values == ["Product Sales", "Raw Materials"]
    query = manager.execute_query.call_args[0][0]
    assert 'DISTINCT "ACCOUNT_CATEGORY"' in query
    assert '"LUBRICANTS"."FINANCIALTRANSACTIONS"' in query
    assert "LIMIT" in query


@pytest.mark.asyncio
async def test_sample_distinct_values_sqlserver_uses_top_not_limit(agent):
    manager = AsyncMock()
    manager.execute_query.return_value = {"rows": [{"sample_value": "Revenue"}]}

    values = await agent._sample_distinct_values(
        manager, "sqlserver", "HessStarSchemaView", "account_type", {"schema": "dbo"},
    )

    assert values == ["Revenue"]
    query = manager.execute_query.call_args[0][0]
    assert "TOP" in query
    assert "[dbo].[HessStarSchemaView]" in query


@pytest.mark.asyncio
async def test_sample_distinct_values_filters_none_and_caps_at_limit(agent):
    manager = AsyncMock()
    manager.execute_query.return_value = {
        "rows": [{"sample_value": v} for v in ["A", None, "B", "C"]]
    }

    values = await agent._sample_distinct_values(
        manager, "snowflake", "T", "COL", {}, limit=2,
    )

    assert values == ["A", "B"]


@pytest.mark.asyncio
async def test_sample_distinct_values_unknown_backend_returns_empty(agent):
    manager = AsyncMock()
    values = await agent._sample_distinct_values(manager, "duckdb_variant_x", "T", "COL", {})
    assert values == []
    manager.execute_query.assert_not_called()


@pytest.mark.asyncio
async def test_sample_distinct_values_swallows_query_errors(agent):
    manager = AsyncMock()
    manager.execute_query.side_effect = RuntimeError("permission denied")

    values = await agent._sample_distinct_values(manager, "snowflake", "T", "COL", {})

    assert values == []


@pytest.mark.asyncio
async def test_populate_categorical_sample_values_only_touches_categorical_columns(agent, monkeypatch):
    profile = TableProfile(
        name="FINANCIALTRANSACTIONS",
        columns=[
            _col("ACCOUNT_CATEGORY", "TEXT", ["dimension"]),
            _col("TRANSACTION_ID", "TEXT", ["identifier"]),
            _col("AMOUNT", "NUMBER", ["measure"]),
        ],
        primary_keys=["TRANSACTION_ID"],
        foreign_keys=[],
    )
    sampled = AsyncMock(return_value=["Product Sales", "Raw Materials"])
    monkeypatch.setattr(agent, "_sample_distinct_values", sampled)

    await agent._populate_categorical_sample_values(AsyncMock(), "snowflake", profile, {})

    assert sampled.await_count == 1
    by_name = {c.name: c for c in profile.columns}
    assert by_name["ACCOUNT_CATEGORY"].sample_values == ["Product Sales", "Raw Materials"]
    assert by_name["TRANSACTION_ID"].sample_values == []
    assert by_name["AMOUNT"].sample_values == []


# ---------------------------------------------------------------------------
# Null-aggregate validation warning — a guessed filter literal that matches no
# real row doesn't error, it silently returns NULL; must not pass as a plain
# green checkmark.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_single_kpi_query_flags_null_aggregate_as_warning(agent):
    kpi = MagicMock(id="cogs", sql_query="SELECT SUM(amount) AS value FROM t WHERE account_category = 'COGS'")
    kpi.name = "COGS"  # MagicMock(name=...) sets the mock's repr, not the .name attribute
    manager = AsyncMock()
    manager.execute_query.return_value = {"rows": [{"value": None}], "success": True}

    result = await agent._validate_single_kpi_query(kpi, manager, timeout_seconds=10, request_id="req1")

    assert result.status == "success"
    assert result.warning_message is not None
    assert "NULL" in result.warning_message


@pytest.mark.asyncio
async def test_validate_single_kpi_query_no_warning_for_real_value(agent):
    kpi = MagicMock(id="revenue", sql_query="SELECT SUM(amount) AS value FROM t")
    kpi.name = "Revenue"
    manager = AsyncMock()
    manager.execute_query.return_value = {"rows": [{"value": 12345.0}], "success": True}

    result = await agent._validate_single_kpi_query(kpi, manager, timeout_seconds=10, request_id="req1")

    assert result.status == "success"
    assert result.warning_message is None
