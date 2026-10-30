"""Deep Analysis loads the data product registry once per run, not once per query (2026-10-30).

Each query the analysis built reloaded the data_products table: about 60 reloads a run,
~10 s against production Supabase (Railway log). Inside registry_snapshot() the reload
happens once; outside it every call still reloads, so a newly onboarded data product is
still visible without a restart.
"""
import asyncio
import logging
from types import SimpleNamespace

import pytest

from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent


class _Provider:
    def __init__(self):
        self.loads = 0

    async def load(self):
        self.loads += 1


def _dpa():
    dpa = A9_Data_Product_Agent.__new__(A9_Data_Product_Agent)
    dpa.data_product_provider = _Provider()
    dpa.logger = logging.getLogger("test_dpa_registry_snapshot")
    return dpa


@pytest.mark.asyncio
async def test_outside_a_run_every_request_still_reloads():
    dpa = _dpa()
    for _ in range(3):
        await dpa._refresh_data_product_registry()
    assert dpa.data_product_provider.loads == 3


@pytest.mark.asyncio
async def test_inside_a_run_the_registry_loads_once_including_parallel_queries():
    dpa = _dpa()
    async with dpa.registry_snapshot():
        await dpa._refresh_data_product_registry()
        # parallel queries run as tasks started inside the scope; they inherit it
        await asyncio.gather(*(dpa._refresh_data_product_registry() for _ in range(8)))
    assert dpa.data_product_provider.loads == 1
    await dpa._refresh_data_product_registry()  # the scope has ended: reloads again
    assert dpa.data_product_provider.loads == 2


@pytest.mark.asyncio
async def test_another_request_running_alongside_is_not_affected():
    dpa = _dpa()
    inside = asyncio.Event()
    release = asyncio.Event()

    async def analysis():
        async with dpa.registry_snapshot():
            inside.set()
            await release.wait()

    task = asyncio.create_task(analysis())
    await inside.wait()
    await dpa._refresh_data_product_registry()  # a scan or NL question at the same time
    release.set()
    await task
    assert dpa.data_product_provider.loads == 2


@pytest.mark.asyncio
async def test_an_error_inside_a_run_still_ends_the_scope():
    dpa = _dpa()
    with pytest.raises(RuntimeError):
        async with dpa.registry_snapshot():
            raise RuntimeError("analysis failed")
    await dpa._refresh_data_product_registry()
    assert dpa.data_product_provider.loads == 2


@pytest.mark.asyncio
async def test_execute_deep_analysis_runs_inside_one_registry_load():
    dpa = _dpa()
    da = A9_Deep_Analysis_Agent.__new__(A9_Deep_Analysis_Agent)
    da.data_product_agent = dpa

    async def body(plan):
        for _ in range(60):  # one reload attempt per query built
            await dpa._refresh_data_product_registry()
        return "response"

    da._execute_deep_analysis = body
    assert await da.execute_deep_analysis(SimpleNamespace()) == "response"
    assert dpa.data_product_provider.loads == 1


@pytest.mark.asyncio
async def test_execute_deep_analysis_without_a_real_data_agent_still_runs():
    da = A9_Deep_Analysis_Agent.__new__(A9_Deep_Analysis_Agent)
    da.data_product_agent = SimpleNamespace()  # e.g. a test double

    async def body(plan):
        return "response"

    da._execute_deep_analysis = body
    assert await da.execute_deep_analysis(SimpleNamespace()) == "response"
