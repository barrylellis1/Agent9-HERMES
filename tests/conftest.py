"""Pytest fixtures and configuration for Agent9 test suite."""

import asyncio
import os
import sys
from typing import AsyncIterator, Iterator

import pytest
import pytest_asyncio

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.registry.bootstrap import RegistryBootstrap
from src.registry.factory import RegistryFactory
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent, create_and_connect_agents


pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session", autouse=True)
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Provide a session-scoped event loop for tests needing asyncio."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        yield loop
    finally:
        asyncio.set_event_loop(None)
        loop.close()


@pytest.fixture(scope="session")
def registry_bootstrap(event_loop: asyncio.AbstractEventLoop) -> RegistryFactory:
    """Ensure registry providers are initialized once per test session."""
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
    event_loop.run_until_complete(RegistryBootstrap.initialize({"base_path": base_path}))
    factory = RegistryFactory()
    # Ensure required providers are registered (initialize() may skip if already set up)
    if factory.get_provider("data_product") is None:
        factory.get_data_product_provider()
    if factory.get_provider("kpi") is None:
        factory.get_kpi_provider()

    # Ensure providers have loaded data where supported
    data_provider = factory.get_provider("data_product")
    if data_provider and hasattr(data_provider, "load"):
        try:
            event_loop.run_until_complete(data_provider.load())
        except TypeError:
            data_provider.load()

    kpi_provider = factory.get_provider("kpi")
    if kpi_provider and hasattr(kpi_provider, "load"):
        try:
            event_loop.run_until_complete(kpi_provider.load())
        except TypeError:
            kpi_provider.load()
    return factory


@pytest.fixture(scope="session")
def data_product_agent(event_loop: asyncio.AbstractEventLoop, registry_bootstrap: RegistryFactory) -> Iterator[A9_Data_Product_Agent]:
    """Provide a connected Data Product Agent backed by real registry data."""
    db_path = os.path.join("data", "agent9-hermes.duckdb")
    config = {
        "data_directory": os.path.dirname(db_path) or "data",
        "database": {"type": "duckdb", "path": db_path},
        "registry_factory": registry_bootstrap,
        "bypass_mcp": True,
    }
    agent = event_loop.run_until_complete(A9_Data_Product_Agent.create(config))
    event_loop.run_until_complete(agent.db_manager.connect({"database_path": agent.db_path}))
    try:
        yield agent
    finally:
        event_loop.run_until_complete(agent.disconnect())


@pytest_asyncio.fixture(scope="function")
async def orchestrator(registry_bootstrap: RegistryFactory) -> AsyncIterator[A9_Orchestrator_Agent]:
    orchestrator = await A9_Orchestrator_Agent.create({"registry_factory": registry_bootstrap})
    await orchestrator.connect()
    await create_and_connect_agents(orchestrator, registry_bootstrap)
    try:
        yield orchestrator
    finally:
        await orchestrator.disconnect()
