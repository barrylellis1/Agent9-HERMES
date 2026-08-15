"""check_completeness() — src/analysis/slice_validity.py.

WHY THIS IS A SEPARATE CHECK FROM profile()
---------------------------------------------
profile() answers "do two-or-more components disagree with each other's
dimensional reach" — it needs 2+ components and says nothing about a
single-component KPI. A user correctly pointed out that this left every
plain-sum KPI (net_revenue, cogs, sga_expense — 26 of 42 KPIs across the
three seeded clients) completely unchecked: a single-component KPI can
still be wrong when sliced if some of its rows have no value for the
dimension at all (a Revenue row with NULL customer_name silently drops out
of "revenue by customer" rather than corrupting one customer's number).
check_completeness() answers that question, and applies to every KPI
regardless of component count.
"""
import pytest

from src.analysis.slice_validity import check_completeness


def _rows(total, complete):
    return [{"total_rows": total, "complete_rows": complete}]


@pytest.mark.asyncio
async def test_full_coverage_is_ok():
    def run_query(sql):
        return _rows(100, 100)

    verdicts = await check_completeness(
        run_query, "v", "account_type", ["Revenue"], ["customer_name"],
    )

    assert verdicts[0].verdict == "ok"
    assert verdicts[0].coverage == 1.0


@pytest.mark.asyncio
async def test_applies_to_a_single_component_kpi():
    """The whole point: net_revenue-shaped KPIs (one account_type value) are
    now checkable, where profile() had nothing to compare them against."""
    def run_query(sql):
        assert "account_type IN ('Revenue')" in sql
        return _rows(50, 45)

    verdicts = await check_completeness(
        run_query, "v", "account_type", ["Revenue"], ["customer_name"],
    )

    assert verdicts[0].coverage == 0.9
    assert verdicts[0].verdict == "degraded"


@pytest.mark.asyncio
async def test_some_null_dimension_rows_is_invalid_below_threshold():
    def run_query(sql):
        return _rows(100, 10)  # 90% of rows have no value for this dimension

    verdicts = await check_completeness(
        run_query, "v", "account_type", ["Revenue"], ["customer_name"],
    )

    assert verdicts[0].verdict == "INVALID"


@pytest.mark.asyncio
async def test_zero_rows_is_unknown_not_a_division_error():
    def run_query(sql):
        return _rows(0, 0)

    verdicts = await check_completeness(
        run_query, "v", "account_type", ["Revenue"], ["customer_name"],
    )

    assert verdicts[0].verdict == "unknown"
    assert verdicts[0].coverage == 0.0


@pytest.mark.asyncio
async def test_uppercase_row_keys_handled_case_insensitively():
    """Same Snowflake finding as profile() — must not regress independently
    in the sibling check."""
    def run_query(sql):
        return [{"TOTAL_ROWS": 20, "COMPLETE_ROWS": 20}]

    verdicts = await check_completeness(
        run_query, "v", "account_type", ["Revenue"], ["customer_name"], source_system="snowflake",
    )

    assert verdicts[0].verdict == "ok"


@pytest.mark.asyncio
async def test_a_row_shape_surprise_on_one_dimension_does_not_kill_the_whole_check():
    def run_query(sql):
        if "customer_name" in sql:
            return [{"unexpected": "shape"}]
        return _rows(10, 10)

    verdicts = await check_completeness(
        run_query, "v", "account_type", ["Revenue"], ["customer_name", "product_name"],
    )

    assert len(verdicts) == 1
    assert verdicts[0].dimension == "product_name"


@pytest.mark.asyncio
async def test_query_filters_to_the_kpis_own_components_and_version():
    seen = {}

    def run_query(sql):
        seen["sql"] = sql
        return _rows(10, 10)

    await check_completeness(
        run_query, "proj.dataset.view", "account_type", ["Revenue", "COGS", "SGA"],
        ["basin_name"], version_filter="Actual", source_system="bigquery",
    )

    assert "account_type IN ('Revenue', 'COGS', 'SGA')" in seen["sql"]
    assert "version = 'Actual'" in seen["sql"]
    assert "COUNT(*) AS total_rows" in seen["sql"]
    assert "COUNT(basin_name) AS complete_rows" in seen["sql"]
    assert "FROM `proj.dataset.view`" in seen["sql"]


@pytest.mark.asyncio
async def test_no_group_by_alias_risk_here_at_all():
    """check_completeness() never groups by anything, so it can't regress
    the T-SQL GROUP BY-alias bug profile() had — pinned so a future edit
    that adds grouping doesn't reintroduce it silently."""
    seen = {}

    def run_query(sql):
        seen["sql"] = sql
        return _rows(5, 5)

    await check_completeness(
        run_query, "dbo.HessStarSchemaView", "account_type", ["Revenue"],
        ["segment_name"], source_system="sqlserver",
    )

    assert "GROUP BY" not in seen["sql"]
    assert "FROM [dbo].[HessStarSchemaView]" in seen["sql"]
