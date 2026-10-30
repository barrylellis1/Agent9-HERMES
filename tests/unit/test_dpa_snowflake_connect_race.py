"""Snowflake queries starting together share one connection attempt (2026-10-30).

A parallel SA scan's first Snowflake queries each built a SnowflakeManager and replaced the shared
one while another was still connecting; queries in between hit "Snowflake connection not
established" and an Apex scan lost every monthly series.
"""
import asyncio
import logging

import pytest

from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent


class _SlowManager:
    created = 0

    def __init__(self, config, logger=None):
        _SlowManager.created += 1
        self.conn = None

    async def connect(self, params):
        await asyncio.sleep(0.05)
        self.conn = object()
        return True


class _FailingManager(_SlowManager):
    async def connect(self, params):
        await asyncio.sleep(0.01)
        return False


def _dpa():
    dpa = A9_Data_Product_Agent.__new__(A9_Data_Product_Agent)
    dpa.logger = logging.getLogger("test_dpa_snowflake_connect_race")
    dpa._sf_manager = None
    dpa.registry_factory = None
    return dpa


@pytest.mark.asyncio
async def test_queries_starting_together_connect_once_and_all_see_a_connected_manager(monkeypatch):
    from src.database.backends import snowflake_manager

    monkeypatch.setenv("SF_ACCOUNT", "acct")
    monkeypatch.setattr(snowflake_manager, "SnowflakeManager", _SlowManager)
    _SlowManager.created = 0
    dpa = _dpa()
    seen = []

    async def query():
        ok = await dpa._ensure_snowflake_connected("dp_apex")
        seen.append(ok and dpa._sf_manager is not None and dpa._sf_manager.conn is not None)

    await asyncio.gather(*(query() for _ in range(8)))
    assert _SlowManager.created == 1
    assert seen == [True] * 8


@pytest.mark.asyncio
async def test_a_failed_connect_leaves_no_half_open_manager_behind(monkeypatch):
    from src.database.backends import snowflake_manager

    monkeypatch.setenv("SF_ACCOUNT", "acct")
    monkeypatch.setattr(snowflake_manager, "SnowflakeManager", _FailingManager)
    dpa = _dpa()
    assert await dpa._ensure_snowflake_connected("dp_apex") is False
    assert dpa._sf_manager is None
