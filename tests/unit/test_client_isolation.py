"""
Phase 10B-DGA: Client isolation regression tests.

Verifies that tenant boundaries are enforced — a principal from one client
(e.g., lubricants) must never see KPIs belonging to another client (e.g., bicycle).
"""

import os
import sys
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.agents.models.situation_awareness_models import PrincipalContext, KPIDefinition
from src.agents.models.data_governance_models import (
    DataAccessValidationRequest,
    KPIDataProductMappingRequest,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_kpi(name: str, client_id: str, bps: list[str] | None = None) -> KPIDefinition:
    return KPIDefinition(
        name=name,
        description=f"Test KPI: {name}",
        client_id=client_id,
        data_product_id=f"{client_id}_star_schema",
        business_processes=bps or ["Finance: Revenue Analysis"],
        positive_trend_is_good=True,
    )


def _make_principal(principal_id: str, client_id: str | None, bps: list[str] | None = None) -> PrincipalContext:
    return PrincipalContext(
        role="CFO",
        principal_id=principal_id,
        client_id=client_id,
        business_processes=bps or ["Finance"],
        default_filters={},
        decision_style="analytical",
        communication_style="executive",
        preferred_timeframes=[],
    )


BICYCLE_KPIS = {
    "Gross Revenue": _make_kpi("Gross Revenue", "bicycle"),
    "Net Revenue": _make_kpi("Net Revenue", "bicycle"),
    "COGS": _make_kpi("COGS", "bicycle"),
}

LUBRICANTS_KPIS = {
    "Lubricant Sales": _make_kpi("Lubricant Sales", "lubricants"),
    "Production Cost": _make_kpi("Production Cost", "lubricants"),
}

ALL_KPIS = {**BICYCLE_KPIS, **LUBRICANTS_KPIS}


async def _get_sa_agent():
    """Create an SA agent with a mixed-client KPI registry."""
    from src.agents.new.a9_orchestrator_agent import (
        A9_Orchestrator_Agent,
        initialize_agent_registry,
    )
    from src.registry.factory import RegistryFactory

    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()
    rf = RegistryFactory()

    sa_agent = await orchestrator.create_agent_with_dependencies(
        "A9_Situation_Awareness_Agent",
        {"orchestrator": orchestrator, "registry_factory": rf},
    )
    # Inject the mixed-client KPI registry directly
    sa_agent.kpi_registry = dict(ALL_KPIS)
    return sa_agent


# ---------------------------------------------------------------------------
# SA Agent: _get_relevant_kpis — client isolation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_bicycle_principal_sees_only_bicycle_kpis():
    sa = await _get_sa_agent()
    ctx = _make_principal("cfo_001", "bicycle")
    result = sa._get_relevant_kpis(ctx, business_processes=["Finance"])
    names = set(result.keys())
    assert names == {"Gross Revenue", "Net Revenue", "COGS"}, f"Expected bicycle KPIs only, got {names}"


@pytest.mark.asyncio
async def test_lubricants_principal_sees_only_lubricants_kpis():
    sa = await _get_sa_agent()
    ctx = _make_principal("cfo_002", "lubricants")
    result = sa._get_relevant_kpis(ctx, business_processes=["Finance"])
    names = set(result.keys())
    assert names == {"Lubricant Sales", "Production Cost"}, f"Expected lubricants KPIs only, got {names}"


@pytest.mark.asyncio
async def test_unscoped_principal_sees_all_kpis():
    """Admin/unscoped context: principal with no client_id sees all KPIs.

    This is the system/admin context only. Normal principals always have a client_id.
    """
    sa = await _get_sa_agent()
    ctx = _make_principal("admin_001", None)
    result = sa._get_relevant_kpis(ctx, business_processes=["Finance"])
    names = set(result.keys())
    assert names == set(ALL_KPIS.keys()), f"Expected all KPIs, got {names}"


@pytest.mark.asyncio
async def test_client_id_from_principal_context_used_when_not_explicit():
    """client_id on PrincipalContext should be extracted even when not passed explicitly."""
    sa = await _get_sa_agent()
    ctx = _make_principal("cfo_001", "bicycle")
    # Do NOT pass client_id kwarg — should pick it up from ctx.client_id
    result = sa._get_relevant_kpis(ctx, business_processes=["Finance"], client_id=None)
    names = set(result.keys())
    assert "Lubricant Sales" not in names
    assert "Gross Revenue" in names


@pytest.mark.asyncio
async def test_kpi_without_client_id_excluded_when_principal_has_client():
    """A KPI with client_id=None must NOT appear in a client-scoped scan.

    When a principal has a client_id, the filter is strict: only KPIs with exactly
    matching client_id are included. KPIs with client_id=None are unscoped and must
    be excluded to prevent cross-tenant contamination.
    """
    sa = await _get_sa_agent()
    # Add a shared KPI with no client_id (simulating contract-loaded or legacy data)
    sa.kpi_registry["Shared Metric"] = KPIDefinition(
        name="Shared Metric",
        description="Cross-client metric",
        client_id=None,
        data_product_id="shared_schema",
        business_processes=["Finance: Revenue Analysis"],
        positive_trend_is_good=True,
    )
    ctx = _make_principal("cfo_001", "bicycle")
    result = sa._get_relevant_kpis(ctx, business_processes=["Finance"])
    names = set(result.keys())
    # Only bicycle-scoped KPIs should be included — no unscoped metrics
    assert "Shared Metric" not in names, "Unscoped KPI (client_id=None) must be excluded"
    assert "Gross Revenue" in names
    # Lubricants still excluded (cross-client)
    assert "Lubricant Sales" not in names


# ---------------------------------------------------------------------------
# DGA: validate_data_access — tenant boundary enforcement
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dga_allows_same_client_access():
    from src.agents.new.a9_orchestrator_agent import (
        A9_Orchestrator_Agent,
        initialize_agent_registry,
    )
    from src.registry.factory import RegistryFactory

    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()
    rf = RegistryFactory()

    dga = await orchestrator.create_agent_with_dependencies(
        "A9_Data_Governance_Agent",
        {"orchestrator": orchestrator, "registry_factory": rf},
    )

    req = DataAccessValidationRequest(
        principal_id="cfo_001",
        data_product_id="bicycle_star_schema",
        client_id="bicycle",
    )
    resp = await dga.validate_data_access(req)
    assert resp.allowed is True


@pytest.mark.asyncio
async def test_dga_denies_cross_client_access():
    from src.agents.new.a9_orchestrator_agent import (
        A9_Orchestrator_Agent,
        initialize_agent_registry,
    )
    from src.registry.factory import RegistryFactory

    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()
    rf = RegistryFactory()

    dga = await orchestrator.create_agent_with_dependencies(
        "A9_Data_Governance_Agent",
        {"orchestrator": orchestrator, "registry_factory": rf},
    )

    # Inject a mock KPI provider that returns a data product with client_id="bicycle"
    mock_kpi_provider = MagicMock()
    mock_kpi = SimpleNamespace(
        name="Gross Revenue",
        client_id="bicycle",
        data_product_id="bicycle_star_schema",
    )
    mock_kpi_provider.get_all.return_value = [mock_kpi]
    dga.kpi_provider = mock_kpi_provider

    req = DataAccessValidationRequest(
        principal_id="cfo_002",
        data_product_id="bicycle_star_schema",
        client_id="lubricants",  # Lubricants principal trying to access bicycle data
    )
    resp = await dga.validate_data_access(req)
    assert resp.allowed is False, "Cross-client access should be denied"


@pytest.mark.asyncio
async def test_dga_allows_when_principal_is_unscoped():
    """Admin/unscoped context: principal with no client_id can access any data product.

    When a principal has no client_id (system/admin context), access is allowed
    regardless of the data product's client_id. Normal principals always have
    a client_id and are subject to strict tenant isolation.
    """
    from src.agents.new.a9_orchestrator_agent import (
        A9_Orchestrator_Agent,
        initialize_agent_registry,
    )
    from src.registry.factory import RegistryFactory

    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()
    rf = RegistryFactory()

    dga = await orchestrator.create_agent_with_dependencies(
        "A9_Data_Governance_Agent",
        {"orchestrator": orchestrator, "registry_factory": rf},
    )

    req = DataAccessValidationRequest(
        principal_id="cfo_001",
        data_product_id="bicycle_star_schema",
        # No client_id → backward compat
    )
    resp = await dga.validate_data_access(req)
    assert resp.allowed is True


# ---------------------------------------------------------------------------
# DGA: map_kpis_to_data_products — client-scoped mapping
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dga_mapping_filters_by_client():
    from src.agents.new.a9_orchestrator_agent import (
        A9_Orchestrator_Agent,
        initialize_agent_registry,
    )
    from src.registry.factory import RegistryFactory

    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()
    rf = RegistryFactory()

    dga = await orchestrator.create_agent_with_dependencies(
        "A9_Data_Governance_Agent",
        {"orchestrator": orchestrator, "registry_factory": rf},
    )

    # Inject a mock KPI provider with mixed-client KPIs
    mock_kpi_provider = MagicMock()
    bicycle_kpi = SimpleNamespace(
        name="Gross Revenue", client_id="bicycle", data_product_id="bicycle_star_schema",
        business_processes=["Finance"], metadata={},
    )
    lubricants_kpi = SimpleNamespace(
        name="Lubricant Sales", client_id="lubricants", data_product_id="lubricants_star_schema",
        business_processes=["Finance"], metadata={},
    )
    mock_kpi_provider.get_all.return_value = [bicycle_kpi, lubricants_kpi]
    mock_kpi_provider.get_by_client.return_value = [bicycle_kpi]
    dga.kpi_provider = mock_kpi_provider

    req = KPIDataProductMappingRequest(
        kpi_names=["Gross Revenue", "Lubricant Sales"],
        client_id="bicycle",
    )
    resp = await dga.map_kpis_to_data_products(req)

    mapped_names = [m.kpi_name for m in resp.mappings]
    assert "Gross Revenue" in mapped_names
    # Lubricant Sales should NOT appear — it belongs to a different client
    assert "Lubricant Sales" not in mapped_names or "Lubricant Sales" in resp.unmapped_kpis
