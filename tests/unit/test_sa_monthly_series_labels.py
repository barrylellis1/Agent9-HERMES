# arch-allow-direct-agent-construction
"""Monthly series labels name the month, whatever type the period column is.

Found live 2026-10-13 on Hess (SQL Server): fiscal_period is text ('001'..'012'); cutting it
to two characters labelled every month '2026-00', so no month could be told from another and
no baseline could be recorded when a solution was approved.
"""
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent as SA

SS = "SELECT SUM([amount]) AS value FROM [dbo].[HessStarSchemaView] WHERE [account_type] = 'Revenue' AND [version] = 'Actual'"
SF = "SELECT SUM(amount) AS value FROM AGENT9_DEMO.LUBRICANTS.STAR_VIEW WHERE account_type = 'Revenue' AND version = 'Actual'"


def _agent():
    a = SA.__new__(SA)
    a.logger = __import__("logging").getLogger("t")
    return a


def test_sql_server_reads_the_period_as_a_number_before_padding():
    sql = _agent()._ss_monthly_series_sql(SS)
    assert "TRY_CAST([fiscal_period] AS INT)" in sql
    assert "CAST([fiscal_period] AS VARCHAR(2))" not in sql      # the cut that produced '00'
    assert "GROUP BY [fiscal_year], [fiscal_period]" in sql and "[version] = 'Actual'" in sql


def test_snowflake_reads_the_period_as_a_number_before_padding():
    sql = _agent()._sf_monthly_series_sql(SF)
    assert "TRY_TO_NUMBER(CAST(fiscal_period AS VARCHAR))" in sql
    assert "LPAD(CAST(fiscal_period AS VARCHAR), 2, '0')" not in sql
