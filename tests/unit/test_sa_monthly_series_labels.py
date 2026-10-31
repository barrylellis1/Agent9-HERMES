# arch-allow-direct-agent-construction
"""Monthly series labels name the month, whatever type the period column is.

Found live 2026-10-13 on Hess (SQL Server): fiscal_period is text ('001'..'012'); cutting it
to two characters labelled every month '2026-00', so no month could be told from another and
no baseline could be recorded when a solution was approved.
"""
# The builders moved from the scan to the Data Product Agent on 2026-10-31.
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent as DPA

SS = "SELECT SUM([amount]) AS value FROM [dbo].[HessStarSchemaView] WHERE [account_type] = 'Revenue' AND [version] = 'Actual'"
SF = "SELECT SUM(amount) AS value FROM AGENT9_DEMO.LUBRICANTS.STAR_VIEW WHERE account_type = 'Revenue' AND version = 'Actual'"


def _agent():
    a = DPA.__new__(DPA)
    a.logger = __import__("logging").getLogger("t")
    return a


def _series(sql, dialect):
    from src.database.time_filter import TimeFilter
    fyp = {"type": "fiscal_year_period", "year_column": "fiscal_year", "period_column": "fiscal_period"}
    return _agent()._build_monthly_series_sql(sql, TimeFilter.period_key_expr(fyp, dialect), 9,
                                              ["fiscal_year", "fiscal_period"], dialect)


def test_sql_server_reads_the_period_as_a_number_before_padding():
    sql = _series(SS, "sqlserver")
    assert "CAST(CAST(fiscal_period AS INT) AS VARCHAR(2))" in sql
    assert "CAST(fiscal_period AS VARCHAR(2))" not in sql.replace("CAST(CAST(fiscal_period AS INT)", "")  # the cut that produced '00'
    assert "[version] = 'Actual'" in sql and "TOP 9" in sql


def test_snowflake_reads_the_period_as_a_number_before_padding():
    sql = _series(SF, "snowflake")
    assert "TO_VARCHAR(CAST(fiscal_period AS INTEGER))" in sql
    assert "LPAD(CAST(fiscal_period AS VARCHAR), 2, '0')" not in sql
    assert "LIMIT 9" in sql
