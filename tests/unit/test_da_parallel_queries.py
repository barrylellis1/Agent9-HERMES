"""Deep Analysis runs its independent warehouse queries in parallel (owner, 2026-10-23).

Measured on four live cards: 12-55 s of a 32-77 s analysis was 17-66 queries issued one after
another. `_ParallelQueries` starts them together under a per-analysis cap, runs identical SQL once,
and raises a failed query where the sequential code raised it. A backend that runs one query at a
time (SQL Server, DuckDB) keeps the old pass-through.
"""
import asyncio

import pytest

from src.agents.new import a9_deep_analysis_agent as da
from src.agents.new.a9_deep_analysis_agent import _ParallelQueries


class Warehouse:
    def __init__(self, delay=0.05, fail=()):
        self.delay, self.fail = delay, set(fail)
        self.calls = []
        self.in_flight = 0
        self.peak = 0

    async def execute(self, sql):
        self.calls.append(sql)
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        try:
            await asyncio.sleep(self.delay)
            if sql in self.fail:
                raise RuntimeError(f"warehouse error on {sql}")
            return {"rows": [[sql]], "columns": ["value"]}
        finally:
            self.in_flight -= 1


@pytest.mark.asyncio
async def test_prefetched_queries_run_together_and_are_not_rerun():
    wh = Warehouse()
    q = _ParallelQueries(wh.execute, enabled=True)
    sqls = [f"q{i}" for i in range(6)]
    q.prefetch(sqls)
    results = [await q.run(s) for s in sqls]
    assert [r["rows"][0][0] for r in results] == sqls
    assert sorted(wh.calls) == sorted(sqls)  # each ran once
    assert wh.peak > 1  # and they overlapped
    assert q.stats() == {"queries": 6, "prefetched": 6, "unused": 0}


@pytest.mark.asyncio
async def test_identical_sql_runs_once_per_analysis():
    wh = Warehouse()
    q = _ParallelQueries(wh.execute, enabled=True)
    a, b = await q.run("same"), await q.run("same")
    assert a is b and wh.calls == ["same"]


@pytest.mark.asyncio
async def test_the_per_analysis_cap_holds():
    wh = Warehouse(delay=0.02)
    q = _ParallelQueries(wh.execute, enabled=True, limit=3)
    q.prefetch([f"q{i}" for i in range(12)])
    await asyncio.gather(*(q.run(f"q{i}") for i in range(12)))
    assert wh.peak == 3


@pytest.mark.asyncio
async def test_the_server_cap_holds_across_analyses(monkeypatch):
    from src.database import query_slots
    monkeypatch.setattr(query_slots, "QUERIES_PER_SERVER", 4)
    monkeypatch.setattr(query_slots, "_SERVER_SLOTS", {})
    wh = Warehouse(delay=0.02)
    runners = [_ParallelQueries(wh.execute, enabled=True, limit=8) for _ in range(3)]
    for i, r in enumerate(runners):
        r.prefetch([f"a{i}-{j}" for j in range(6)])
    await asyncio.gather(*(r.run(f"a{i}-{j}") for i, r in enumerate(runners) for j in range(6)))
    assert wh.peak == 4


@pytest.mark.asyncio
async def test_a_failed_query_raises_where_its_result_is_used():
    wh = Warehouse(fail={"bad"})
    q = _ParallelQueries(wh.execute, enabled=True)
    q.prefetch(["good", "bad"])  # prefetching does not raise
    assert (await q.run("good"))["rows"] == [["good"]]
    with pytest.raises(RuntimeError, match="warehouse error on bad"):
        await q.run("bad")


@pytest.mark.asyncio
async def test_a_one_query_at_a_time_backend_keeps_the_old_pass_through():
    wh = Warehouse()
    q = _ParallelQueries(wh.execute, enabled=False)
    q.prefetch(["x", "y"])  # does nothing
    assert wh.calls == []
    await q.run("x"); await q.run("x")
    assert wh.calls == ["x", "x"] and wh.peak == 1  # no cache, no overlap: exactly as before


def test_only_bigquery_and_snowflake_run_in_parallel():
    assert da._PARALLEL_SOURCES == ("bigquery", "snowflake")
