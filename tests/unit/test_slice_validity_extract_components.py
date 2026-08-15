"""extract_components() — src/analysis/slice_validity.py.

Every case below is a REAL sql_query string read live off a KPI record
during this session (2026-08-15/16), across all three real backends —
not synthesized, so a passing test here means the function works on the
actual data it will run against, not an idealized shape.

Returns (measure_column, components) — account_type tried first (the
discriminator for every ratio/composite KPI in this codebase), falling back
to account_category for the real subset of single-component KPIs
(product_sales_revenue, service_revenue, base_oil_cost, distribution_cost)
that filter on it instead and have no account_type reference at all —
found live running this against every KPI across all three clients, not
assumed in advance.
"""
from src.analysis.slice_validity import extract_components


def test_single_bare_equality():
    """lubricants/net_revenue, hess/total_revenue, apex_lubricants/net_revenue."""
    sql = "SELECT SUM(amount) AS value FROM `x` WHERE account_type = 'Revenue' AND version = 'Actual'"
    assert extract_components(sql) == ("account_type", ["Revenue"])


def test_in_list():
    """lubricants/gross_profit, lubricants/operating_income, lubricants/ebitda."""
    sql = "SELECT SUM(amount) AS value FROM `x` WHERE account_type IN ('Revenue', 'COGS', 'SGA') AND version = 'Actual'"
    assert extract_components(sql) == ("account_type", ["Revenue", "COGS", "SGA"])


def test_case_when_multiple_matches():
    """hess/gross_profit (SQL Server, bracket-quoted, CASE WHEN shape)."""
    sql = (
        "SELECT SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] "
        "WHEN [account_type] = 'COGS' THEN -[amount] ELSE 0 END) AS value "
        "FROM [dbo].[HessStarSchemaView] WHERE [version] = 'Actual'"
    )
    assert extract_components(sql) == ("account_type", ["Revenue", "COGS"])


def test_bracket_quoted_in_list():
    """hess/ebitda, hess/operating_income (SQL Server)."""
    sql = (
        "SELECT SUM(CASE WHEN [account_type] IN ('Revenue', 'COGS', 'SGA') THEN [amount] "
        "ELSE -[amount] END) AS value FROM [dbo].[HessStarSchemaView] "
        "WHERE [account_type] IN ('Revenue', 'COGS', 'SGA') AND [version] = 'Actual'"
    )
    assert extract_components(sql) == ("account_type", ["Revenue", "COGS", "SGA"])


def test_mixed_equality_and_in_within_one_query():
    """hess/ebitda's real full query — combines an IN(...) with a bare = for
    the D&A add-back leg ("Other"), inside a parenthesized OR."""
    sql = (
        "SELECT SUM(CASE WHEN [account_type] = 'Revenue' THEN [amount] ELSE -[amount] END) "
        "AS value FROM [dbo].[HessStarSchemaView] "
        "WHERE ([account_type] IN ('Revenue', 'COGS', 'SGA') "
        "OR ([account_type] = 'Other' AND [account_category] = 'D&A')) "
        "AND [version] = 'Actual'"
    )
    column, components = extract_components(sql)
    assert column == "account_type"
    assert set(components) == {"Revenue", "COGS", "SGA", "Other"}
    assert components[0] == "Revenue"  # Revenue always first when present


def test_snowflake_unquoted_case_when():
    """apex_lubricants/gross_profit (Snowflake — no bracket quoting at all)."""
    sql = (
        "SELECT SUM(CASE WHEN account_type = 'Revenue' THEN amount "
        "WHEN account_type = 'COGS' THEN amount ELSE 0 END) AS value "
        "FROM LubricantsStarSchemaView WHERE version = 'Actual'"
    )
    assert extract_components(sql) == ("account_type", ["Revenue", "COGS"])


def test_account_category_column_is_not_confused_with_account_type_when_both_present():
    """When account_type DOES match, it wins — account_category is only a
    fallback for when account_type matches nothing at all, not a second
    source to merge in."""
    sql = "SELECT 1 WHERE account_type = 'Revenue' AND account_category = 'D&A'"
    assert extract_components(sql) == ("account_type", ["Revenue"])


def test_account_category_fallback_when_no_account_type_filter_exists():
    """Real, live-found KPIs: lubricants/product_sales_revenue,
    apex_lubricants/base_oil_cost — no account_type filter anywhere, only
    account_category. Failed with "could not determine components" before
    this fallback was added — confirmed by running the check against every
    KPI across all three clients, not a synthesized edge case."""
    sql = "SELECT SUM(amount) AS value FROM `x` WHERE account_category = 'Product Sales' AND version = 'Actual'"
    assert extract_components(sql) == ("account_category", ["Product Sales"])


def test_account_category_fallback_with_negated_sum():
    """lubricants/base_oil_cost, lubricants/distribution_cost — SUM(-amount),
    still just a single-component filter on account_category."""
    sql = "SELECT -SUM(amount) AS value FROM `x` WHERE account_category = 'Raw Materials' AND version = 'Actual'"
    assert extract_components(sql) == ("account_category", ["Raw Materials"])


def test_no_filter_at_all_returns_account_type_with_empty_components():
    """account_type is the reported column even on a total miss — it's the
    more common case, not a real signal either way when nothing matched."""
    assert extract_components("SELECT SUM(amount) AS value FROM x") == ("account_type", [])


def test_none_and_empty_input_are_handled():
    assert extract_components(None) == ("account_type", [])
    assert extract_components("") == ("account_type", [])


def test_revenue_first_alphabetical_after():
    sql = "SELECT 1 WHERE account_type IN ('SGA', 'COGS', 'Revenue')"
    assert extract_components(sql) == ("account_type", ["Revenue", "COGS", "SGA"])
