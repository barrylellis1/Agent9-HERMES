# arch-allow-direct-agent-construction
"""
Infra A4-a: Registry Live-Reload regression tests.

Validates that SA, PC, and DP agents refresh their registry state per request,
so that registry changes (new client seeded, new KPI added, new data product
registered) become visible without a service restart.

Background:
  Before this fix, all three agents loaded registry data once at connect() time
  into instance state (self.kpi_registry / self.principal_profiles / data product
  provider cache) and never refreshed it. Seeding a new client mid-runtime
  produced empty results until Railway restarted. This is the bug discovered
  during the Hess client onboarding attempt.

Contract under test (Approach A — pragmatic refresh-before-read):
  1. SA.detect_situations() calls _load_kpi_registry() before processing
  2. SA.process_nl_query() calls _load_kpi_registry() before processing
  3. SA.get_kpi_definitions() calls _load_kpi_registry() before processing
  4. PC.get_principal_context_by_id() calls _principal_provider.load() before lookup
  5. PC.get_principal_context() calls _principal_provider.load() before lookup
  6. DP.get_data_product() calls _refresh_data_product_registry() before lookup
  7. DP.generate_sql_for_kpi() calls _refresh_data_product_registry() before lookup
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.new.a9_principal_context_agent import A9_Principal_Context_Agent
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.models.situation_awareness_models import (
    NLQueryRequest,
    PrincipalContext,
    SituationDetectionRequest,
    BusinessProcess,
    TimeFrame,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _principal_context() -> PrincipalContext:
    return PrincipalContext(
        role="CFO",
        principal_id="cfo_001",
        client_id="lubricants",
        business_processes=["Finance"],
        default_filters={},
        decision_style="analytical",
        communication_style="direct",
        preferred_timeframes=[],
    )


def _sa_agent_with_spy() -> tuple[A9_Situation_Awareness_Agent, AsyncMock]:
    """SA agent with _load_kpi_registry replaced by an AsyncMock spy."""
    agent = A9_Situation_Awareness_Agent(config={})
    agent.kpi_registry = {}
    agent.principal_profiles = {}
    agent.data_product_agent = None
    agent.data_governance_agent = MagicMock()
    spy = AsyncMock(return_value=None)
    agent._load_kpi_registry = spy
    return agent, spy


def _pc_agent_with_spy() -> tuple[A9_Principal_Context_Agent, AsyncMock]:
    """PC agent with _principal_provider mocked; spy on provider.load()."""
    agent = A9_Principal_Context_Agent(config={})
    mock_provider = MagicMock()
    load_spy = AsyncMock(return_value=None)
    mock_provider.load = load_spy
    mock_provider._items = {}
    mock_provider.get = MagicMock(return_value=None)
    mock_provider.get_all = MagicMock(return_value={})
    agent._principal_provider = mock_provider
    agent._business_process_provider = None
    agent.principal_profiles = {}
    agent.logger = MagicMock()
    return agent, load_spy


def _dp_agent_with_spy() -> tuple[A9_Data_Product_Agent, AsyncMock]:
    """DP agent with _refresh_data_product_registry replaced by an AsyncMock spy."""
    agent = A9_Data_Product_Agent(config={})
    spy = AsyncMock(return_value=None)
    agent._refresh_data_product_registry = spy
    return agent, spy


# ---------------------------------------------------------------------------
# 1. SA.detect_situations refreshes KPI registry per request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sa_detect_situations_refreshes_kpi_registry():
    """detect_situations must call _load_kpi_registry per request so new KPIs
    seeded mid-runtime are visible without restart."""
    agent, spy = _sa_agent_with_spy()

    request = SituationDetectionRequest(
        request_id="test-a4a-001",
        principal_context=_principal_context(),
        business_processes=[],
        timeframe=TimeFrame.YEAR_TO_DATE,
    )

    # We don't care if the rest of the method succeeds; only that the refresh
    # was triggered before downstream processing.
    try:
        await agent.detect_situations(request)
    except Exception:
        pass

    spy.assert_called()


# ---------------------------------------------------------------------------
# 2. SA.process_nl_query refreshes KPI registry per request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sa_process_nl_query_refreshes_kpi_registry():
    agent, spy = _sa_agent_with_spy()
    # DGA mocked enough to get past the wiring guard
    agent.data_governance_agent.translate_business_terms = AsyncMock(
        side_effect=RuntimeError("stop here — refresh already fired")
    )

    request = NLQueryRequest(
        request_id="test-a4a-002",
        query="What is net revenue this quarter?",
        principal_context=_principal_context(),
    )

    try:
        await agent.process_nl_query(request)
    except Exception:
        pass

    spy.assert_called()


# ---------------------------------------------------------------------------
# 3. SA.get_kpi_definitions refreshes KPI registry per request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sa_get_kpi_definitions_refreshes_kpi_registry():
    agent, spy = _sa_agent_with_spy()

    try:
        await agent.get_kpi_definitions(_principal_context(), business_process=None)
    except Exception:
        pass

    spy.assert_called()


# ---------------------------------------------------------------------------
# 4. PC.get_principal_context_by_id refreshes provider per request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pc_get_principal_context_by_id_refreshes_provider():
    """Per-request principal provider refresh — so a newly seeded principal
    (e.g. when onboarding a new client) is visible without service restart."""
    agent, load_spy = _pc_agent_with_spy()

    try:
        await agent.get_principal_context_by_id("cfo_001", client_id="lubricants")
    except Exception:
        pass

    load_spy.assert_called()


# ---------------------------------------------------------------------------
# 5. PC.get_principal_context refreshes provider per request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pc_get_principal_context_refreshes_provider():
    agent, load_spy = _pc_agent_with_spy()

    try:
        await agent.get_principal_context("CFO")
    except Exception:
        pass

    load_spy.assert_called()


# ---------------------------------------------------------------------------
# 6. DP.get_data_product refreshes registry per request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dp_get_data_product_refreshes_registry():
    agent, spy = _dp_agent_with_spy()

    try:
        await agent.get_data_product("dp_lubricants_financials")
    except Exception:
        pass

    spy.assert_called()


# ---------------------------------------------------------------------------
# 7. DP.generate_sql_for_kpi refreshes registry per request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dp_generate_sql_for_kpi_refreshes_registry():
    agent, spy = _dp_agent_with_spy()

    fake_kpi = MagicMock()
    fake_kpi.name = "net_revenue"
    fake_kpi.sql_query = "SELECT 1"
    fake_kpi.calculation = ""
    fake_kpi.data_product_id = "dp_lubricants_financials"

    try:
        await agent.generate_sql_for_kpi(fake_kpi)
    except Exception:
        pass

    spy.assert_called()
