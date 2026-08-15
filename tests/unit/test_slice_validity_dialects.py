"""src/analysis/slice_validity.py's backend-aware identifier quoting.

THE DEFECT THIS PINS
----------------------
`profile()`'s query template originally hardcoded BigQuery's backtick
quoting directly into the SQL text. Routing the query to the right database
connection (via A9_Data_Product_Agent.execute_sql()) does NOT fix this — a
backtick-quoted FROM clause is a syntax error on SQL Server or Snowflake
regardless of which connection runs it. Connection routing and query dialect
are two separate problems; this file is the test that would have caught the
first draft of this design, which only fixed the first one.

Each quoting convention below is empirically confirmed from real code
elsewhere in this repo, not invented:
  - BigQuery:   scripts/check_slice_validity.py's original template + the
                a9_data_product_agent.py BQ-reference regex
  - SQL Server: scripts/clients/hess.py's `_SS_PREFIX = "[dbo].[HessStarSchemaView]"`
  - Snowflake:  scripts/clients/apex_lubricants.py's bare `_VIEW` usage
  - DuckDB:     scripts/clients/bicycle.py's bare `FROM {_VIEW}` usage
"""
import pytest

from src.analysis.slice_validity import DimensionVerdict, _quote_view, assess, profile


# ---------------------------------------------------------------------------
# _quote_view — one assertion per source_system
# ---------------------------------------------------------------------------


def test_bigquery_backtick_wraps_the_whole_fully_qualified_name():
    assert _quote_view("proj.dataset.view", "bigquery") == "`proj.dataset.view`"


@pytest.mark.parametrize("alias", ["sqlserver", "sql_server", "mssql"])
def test_sqlserver_brackets_each_segment_individually(alias):
    """NOT a single bracket around the whole string — that's the BigQuery
    mistake ported to a different character. Each dot-separated segment gets
    its own brackets, matching scripts/clients/hess.py's `_SS_PREFIX` literal."""
    assert _quote_view("dbo.HessStarSchemaView", alias) == "[dbo].[HessStarSchemaView]"


def test_sqlserver_single_segment_view_still_quotes_correctly():
    """The actual live shape: KPI.view_name for Hess is the bare
    "HessStarSchemaView", no schema prefix — confirmed by reading
    scripts/clients/hess.py directly, not assumed."""
    assert _quote_view("HessStarSchemaView", "sqlserver") == "[HessStarSchemaView]"


def test_snowflake_is_unquoted():
    assert _quote_view("LubricantsStarSchemaView", "snowflake") == "LubricantsStarSchemaView"


def test_duckdb_is_unquoted():
    assert _quote_view("bicycle_view", "duckdb") == "bicycle_view"


def test_unrecognised_source_system_falls_back_to_bigquery_convention():
    """Refusing to run on an unfamiliar source_system is less useful than
    running with the most common convention and surfacing a syntax error
    loudly if it's wrong — still louder than never running at all."""
    assert _quote_view("some.view", "made_up_backend") == "`some.view`"


def test_default_source_system_is_bigquery():
    """profile()'s own default — unchanged behaviour for the original CLI caller."""
    assert _quote_view("proj.dataset.view", "") == "`proj.dataset.view`"
    assert _quote_view("proj.dataset.view", None) == "`proj.dataset.view`"


# ---------------------------------------------------------------------------
# profile() — the FROM clause actually reaching run_query per backend
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_profile_emits_bracket_quoted_sql_for_sqlserver():
    seen_sql = {}

    def run_query(sql):
        seen_sql["sql"] = sql
        return [{"component": "Revenue", "n": 5}, {"component": "COGS", "n": 5}]

    await profile(
        run_query, "dbo.HessStarSchemaView", "account_type",
        ["Revenue", "COGS"], ["customer_name"], "Actual", "sqlserver",
    )

    assert "FROM [dbo].[HessStarSchemaView]" in seen_sql["sql"]
    assert "`" not in seen_sql["sql"]


def test_group_by_uses_the_expression_not_the_select_alias():
    """Regression for a real bug found live (2026-08-15) against Hess.

    `GROUP BY component` (the SELECT-list alias) is accepted by BigQuery,
    Snowflake, DuckDB and Postgres, but T-SQL (SQL Server) rejects it —
    "Invalid column name 'component'" — because it doesn't resolve aliases
    inside GROUP BY. Every dimension query silently failed and was skipped
    by profile()'s per-dimension error handling, so the check "succeeded"
    with zero results and no visible error. Grouping by the underlying
    expression is valid on every backend, so this is one universal fix, not
    a per-dialect branch — checked for all four source_system values.
    """
    import asyncio

    for source_system in ("bigquery", "sqlserver", "snowflake", "duckdb"):
        seen = {}

        def run_query(sql, _seen=seen):
            _seen["sql"] = sql
            return [{"component": "Revenue", "n": 5}, {"component": "COGS", "n": 5}]

        asyncio.run(profile(
            run_query, "v", "account_type", ["Revenue", "COGS"], ["d"], "Actual", source_system,
        ))

        assert "GROUP BY account_type" in seen["sql"], source_system
        assert "GROUP BY component" not in seen["sql"], source_system


@pytest.mark.asyncio
async def test_profile_emits_backtick_quoted_sql_for_bigquery():
    seen_sql = {}

    def run_query(sql):
        seen_sql["sql"] = sql
        return [{"component": "Revenue", "n": 5}, {"component": "COGS", "n": 5}]

    await profile(
        run_query, "proj.dataset.view", "account_type",
        ["Revenue", "COGS"], ["customer_name"], "Actual", "bigquery",
    )

    assert "FROM `proj.dataset.view`" in seen_sql["sql"]


@pytest.mark.asyncio
async def test_profile_accepts_a_sync_or_async_run_query():
    """A9_Data_Governance_Agent's closure around execute_sql is async; the
    CLI's _bigquery_executor is sync. Both must work without profile()
    branching on caller type."""

    async def async_run_query(sql):
        return [{"component": "Revenue", "n": 3}, {"component": "COGS", "n": 3}]

    def sync_run_query(sql):
        return [{"component": "Revenue", "n": 3}, {"component": "COGS", "n": 3}]

    async_result = await profile(
        async_run_query, "v", "account_type", ["Revenue", "COGS"], ["d"], "Actual", "duckdb",
    )
    sync_result = await profile(
        sync_run_query, "v", "account_type", ["Revenue", "COGS"], ["d"], "Actual", "duckdb",
    )

    assert async_result[0].verdict == sync_result[0].verdict == "ok"
