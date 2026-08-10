"""GROUP BY ROLLUP — the SQL that makes the total the warehouse's job.

WHY
---
A dimension header showed the sum of its member rows. For a ratio KPI that is
meaningless: summing per-product gross margin gave 452.95% against a true
29.43%, and summing the pp deltas gave -53pp against an enterprise move of about
-5pp.

The total cannot be recovered from the member rows at all — it has to be
re-aggregated from the underlying components (SUM(gp)/SUM(rev)). Only the query
can do that, using the KPI's own registered expression, which is also where the
curated data product already defines the calculation. So the DPA appends
ROLLUP and the total arrives as data.

These tests drive the SQL builder directly: no warehouse, no network.
"""
from __future__ import annotations

import pytest

from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent


class _KPI:
    """Minimal KPI shape the BigQuery builder reads."""
    def __init__(self, sql: str):
        self.sql_query = sql
        self.calculation = sql
        self.name = "Gross Margin %"
        self.id = "gross_margin_pct"
        self.data_product_id = "dp_lubricants_financials"
        self.metadata = {}
        self.unit = "%"
        self.attributes = None


RATIO_SQL = (
    "SELECT ROUND(100.0 * SUM(CASE WHEN account_type IN ('Revenue', 'COGS') THEN amount ELSE 0 END) "
    "/ NULLIF(SUM(CASE WHEN account_type = 'Revenue' THEN amount ELSE 0 END), 0), 2) AS value "
    "FROM `p.d.v` WHERE version = 'Actual'"
)


@pytest.fixture
def agent():
    # The builder is a pure string transform; no lifecycle needed for it.
    return A9_Data_Product_Agent.__new__(A9_Data_Product_Agent)


def _build(agent, *, include_total: bool, topn=None):
    import logging
    agent.logger = logging.getLogger("test")
    return agent._build_bq_dimensional_sql(
        RATIO_SQL, _KPI(RATIO_SQL), "year_to_date", topn, True, ["product_name"],
        False, time_spec=None, include_total=include_total,
    )


class TestRollupIsOptIn:
    def test_off_by_default_produces_a_plain_group_by(self, agent):
        sql = _build(agent, include_total=False)
        assert sql, "builder returned nothing"
        assert "GROUP BY" in sql.upper()
        assert "ROLLUP" not in sql.upper(), "ROLLUP must not appear unless requested"

    def test_on_produces_group_by_rollup(self, agent):
        sql = _build(agent, include_total=True)
        assert sql, "builder returned nothing"
        assert "ROLLUP(" in sql.upper().replace(" (", "(")

    def test_the_kpi_expression_is_preserved_intact(self, agent):
        """The total must be computed from the KPI's OWN definition.

        Re-implementing the ratio here — or averaging the member values — is the
        class of arithmetic this change exists to remove from Agent9.
        """
        sql = _build(agent, include_total=True)
        assert "NULLIF" in sql.upper()
        assert "100.0" in sql
        # Both components of the ratio survive, so the warehouse re-aggregates
        # SUM(gp)/SUM(rev) rather than combining pre-divided values.
        assert sql.upper().count("SUM(") >= 2


class TestRollupIsNotAppliedWhereItWouldBreak:
    def test_topn_path_never_gets_rollup(self, agent):
        """That branch ends in ORDER BY ... LIMIT n.

        A LIMIT either clips the total row or keeps it and drops a real member —
        and the total sorts unpredictably against the members, so which one you
        lose is not even stable.
        """
        sql = _build(agent, include_total=True, topn={"n": 10})
        assert sql, "builder returned nothing"
        assert "LIMIT" in sql.upper()
        assert "ROLLUP" not in sql.upper()


class TestTotalRowIdentification:
    """The total row comes back with a NULL dimension.

    DA lifts it out by testing the raw value for None — not by comparing
    `str(key) == "None"`, which would misread a segment legitimately named
    "None" as the grand total.
    """

    def test_sentinel_cannot_collide_with_a_dimension_value(self):
        from src.agents.new.a9_deep_analysis_agent import _ROLLUP_TOTAL_KEY
        assert "\x00" in _ROLLUP_TOTAL_KEY, "sentinel must be unrepresentable as data"
        for realistic in ("None", "Total", "NULL", "", "All", "Unallocated"):
            assert realistic != _ROLLUP_TOTAL_KEY


class TestComparisonPeriodHonouredOnEveryBackend:
    """The scalar (non-breakdown) path ignored `comparison_period`.

    A caller asking for the PRIOR value silently received the CURRENT one, so a
    delta computed from the pair was 0.0 — a confident "no change" on a KPI that
    had moved -4.49pp. Found live on BigQuery; the identical defect was present in
    the Snowflake, SQL Server and Databricks builders, which are what Apex and
    Hess actually run on. Fixing one backend and leaving three is how a bug comes
    back wearing a different client's name.
    """

    BUILDERS = [
        ("_build_bq_dimensional_sql", "bigquery"),
        ("_build_sf_dimensional_sql", "snowflake"),
        ("_build_ss_dimensional_sql", "sqlserver"),
        ("_build_databricks_dimensional_sql", "databricks"),
    ]

    @pytest.mark.parametrize("method,dialect", BUILDERS)
    def test_prior_scalar_differs_from_current(self, agent, method, dialect):
        import logging
        agent.logger = logging.getLogger("test")
        build = getattr(agent, method)
        common = dict(raw_sql=RATIO_SQL, kpi_definition=_KPI(RATIO_SQL),
                      timeframe="year_to_date", topn=None, breakdown=False,
                      override_group_by=None, time_spec=None)
        cur = build(**common, comparison_period=False)
        prev = build(**common, comparison_period=True)
        assert cur and prev, f"{method} produced no SQL"
        assert cur != prev, (
            f"{dialect}: comparison_period is being dropped — the prior-period query "
            f"is byte-identical to the current one, so any delta computed from the "
            f"pair is 0.0"
        )

    @pytest.mark.parametrize("method,dialect", BUILDERS)
    def test_the_two_windows_are_equal_duration_and_shifted_one_year(self, agent, method, dialect):
        """Stronger than "the strings differ".

        Two queries can differ and still compare unequal spans — which is the
        original bug, where YTD was measured against a FULL prior year. This
        asserts the emitted predicates cover the same number of days, one year
        apart.

        Short of a live warehouse this is the strongest available check for
        Snowflake / SQL Server / Databricks, which no test executes against.
        """
        import datetime as _dt
        import logging
        import re
        agent.logger = logging.getLogger("test")
        build = getattr(agent, method)
        kw = dict(raw_sql=RATIO_SQL, kpi_definition=_KPI(RATIO_SQL), timeframe="year_to_date",
                  topn=None, breakdown=False, override_group_by=None, time_spec=None)
        cur, prev = build(**kw, comparison_period=False), build(**kw, comparison_period=True)

        def span(sql):
            d = re.findall(r"'(\d{4}-\d{2}-\d{2})'", sql or "")
            if len(d) < 2:
                pytest.skip(f"{dialect}: predicate is not a literal date range")
            a, b = _dt.date.fromisoformat(d[-2]), _dt.date.fromisoformat(d[-1])
            return a, b, (b - a).days

        c0, c1, cdays = span(cur)
        p0, p1, pdays = span(prev)
        assert cdays == pdays, (
            f"{dialect}: current window spans {cdays} days but the comparison spans "
            f"{pdays} — unequal durations are the original defect, not a variation of it")
        assert c0.year - p0.year == 1 and (c0.month, c0.day) == (p0.month, p0.day), (
            f"{dialect}: comparison window starts {p0}, expected exactly one year before {c0}")
