"""The SA scan reads several KPIs at once on BigQuery/Snowflake, inside shared query limits (2026-10-30).

A Lubricants scan spent ~45 s of 65 s reading 13 KPIs one after another. KPIs now run together
when every data product is BigQuery or Snowflake; the scan keeps at most QUERIES_PER_RUN queries
in flight, inside the server-wide QUERIES_PER_SERVER shared with Deep Analysis. Results are
combined in KPI order, so the cards match a one-at-a-time scan.
"""
import asyncio
import logging
from types import SimpleNamespace

import pytest

from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.database import query_slots


class _Warehouse:
    def __init__(self, delay=0.02):
        self.delay, self.in_flight, self.peak, self.calls = delay, 0, 0, 0

    async def execute_sql(self, sql, parameters=None, principal_context=None, data_product_id=None):
        self.calls += 1
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        try:
            await asyncio.sleep(self.delay)
            return {"rows": [{"value": 1}]}
        finally:
            self.in_flight -= 1


def _agent(sources):
    sa = A9_Situation_Awareness_Agent.__new__(A9_Situation_Awareness_Agent)
    sa.logger = logging.getLogger("test_sa_parallel_kpi_scan")
    sa.data_product_agent = _Warehouse()
    sa._resolve_source_system = lambda dp: sources.get(dp)
    return sa


def _kpis(dps):
    return {f"K{i}": SimpleNamespace(name=f"K{i}", data_product_id=dp) for i, dp in enumerate(dps)}


@pytest.fixture(autouse=True)
def _fresh_server_slots(monkeypatch):
    monkeypatch.setattr(query_slots, "_SERVER_SLOTS", {})


@pytest.mark.asyncio
async def test_bigquery_kpis_run_together_and_come_back_in_kpi_order():
    sa = _agent({"dp_bq": "bigquery"})
    running, peak = 0, 0

    async def scan_one(name, definition):
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.05 if name == "K0" else 0.01)  # the first KPI finishes last
        running -= 1
        return name

    out = await sa._run_kpi_scans(scan_one, _kpis(["dp_bq"] * 5))
    assert out == ["K0", "K1", "K2", "K3", "K4"]
    assert peak == 5


@pytest.mark.asyncio
@pytest.mark.parametrize("sources", [["sqlserver"], ["bigquery", "sqlserver"], ["duckdb"], [None]])
async def test_any_one_at_a_time_backend_keeps_the_whole_scan_sequential(sources):
    mapping = {f"dp{i}": s for i, s in enumerate(sources)}
    sa = _agent(mapping)
    running, peak = 0, 0

    async def scan_one(name, definition):
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.01)
        running -= 1
        return name

    dps = [f"dp{i % len(sources)}" for i in range(4)]
    assert await sa._run_kpi_scans(scan_one, _kpis(dps)) == ["K0", "K1", "K2", "K3"]
    assert peak == 1


@pytest.mark.asyncio
async def test_a_parallel_scan_keeps_at_most_the_run_cap_of_queries_in_flight():
    sa = _agent({"dp_bq": "bigquery"})

    async def scan_one(name, definition):
        # each KPI sends four queries, two of them together, as _get_kpi_value does
        await sa._execute_sql("base", None, "dp_bq")
        await asyncio.gather(sa._execute_sql("monthly", None, "dp_bq"), sa._execute_sql("comp", None, "dp_bq"))
        await sa._execute_sql("plan", None, "dp_bq")
        return name

    await sa._run_kpi_scans(scan_one, _kpis(["dp_bq"] * 13))
    assert sa.data_product_agent.calls == 52
    assert sa.data_product_agent.peak == query_slots.QUERIES_PER_RUN


@pytest.mark.asyncio
async def test_overlapping_scans_share_the_server_cap(monkeypatch):
    monkeypatch.setattr(query_slots, "QUERIES_PER_SERVER", 5)
    warehouse = _Warehouse()
    scans = [_agent({"dp_bq": "bigquery"}) for _ in range(3)]
    for sa in scans:
        sa.data_product_agent = warehouse

    def scanner(sa):
        async def scan_one(name, definition):
            await asyncio.gather(*(sa._execute_sql(f"{name}-{j}", None, "dp_bq") for j in range(3)))
            return name
        return scan_one

    await asyncio.gather(*(sa._run_kpi_scans(scanner(sa), _kpis(["dp_bq"] * 6)) for sa in scans))
    assert warehouse.peak == 5


@pytest.mark.asyncio
async def test_a_sql_server_query_takes_no_slot():
    sa = _agent({"dp_ss": "sqlserver"})
    await asyncio.gather(*(sa._execute_sql(f"q{i}", None, "dp_ss") for i in range(20)))
    assert sa.data_product_agent.peak == 20  # unchanged: the scan itself keeps SQL Server sequential
    assert not query_slots._SERVER_SLOTS  # never touched the server cap


@pytest.mark.asyncio
async def test_kpis_asking_for_the_same_work_at_once_share_one_run():
    sa = _agent({})
    runs = 0

    async def work():
        nonlocal runs
        runs += 1
        await asyncio.sleep(0.02)
        return "latest month"

    results = await asyncio.gather(*(sa._once(("actuals_end", "dp"), work) for _ in range(13)))
    assert results == ["latest month"] * 13 and runs == 1
    assert await sa._once(("actuals_end", "dp"), work) == "latest month" and runs == 2  # finished: not held


@pytest.mark.asyncio
async def test_a_failure_in_shared_work_reaches_every_caller_and_is_not_kept():
    sa = _agent({})

    async def broken():
        await asyncio.sleep(0.01)
        raise RuntimeError("warehouse unreachable")

    results = await asyncio.gather(*(sa._once("k", broken) for _ in range(3)), return_exceptions=True)
    assert all(isinstance(r, RuntimeError) for r in results)
    assert not sa.__dict__.get("_inflight")
