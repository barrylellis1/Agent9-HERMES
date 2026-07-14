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
    # Inject the mixed-client KPI registry using the same dual-key format the SA agent
    # uses when loading from Supabase: plain name key + client-qualified key per KPI.
    registry = {}
    for name, kpi in ALL_KPIS.items():
        registry[name] = kpi
        if kpi.client_id:
            registry[f"{kpi.client_id}:{name}"] = kpi
    sa_agent.kpi_registry = registry
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

    # Inject mock data product provider so the DGA can resolve dp_client="bicycle"
    mock_dp_provider = MagicMock()
    mock_dp = SimpleNamespace(client_id="bicycle", id="bicycle_star_schema")
    mock_dp_provider.get.return_value = mock_dp
    dga.data_product_provider = mock_dp_provider

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
        # No client_id → admin/system context, access allowed regardless of DP client
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


# ---------------------------------------------------------------------------
# Infra B3 Layer 2: provider get_by_client — correct-by-construction accessor
# ---------------------------------------------------------------------------

def _make_db_provider(key_fields=None):
    from src.registry.providers.database_provider import DatabaseRegistryProvider
    from src.agents.models.situation_awareness_models import KPIDefinition

    db_manager = MagicMock()
    provider = DatabaseRegistryProvider(
        db_manager=db_manager,
        table_name="kpis",
        model_class=KPIDefinition,
        key_fields=key_fields,
    )
    return provider, db_manager


def test_get_by_client_returns_only_matching_tenant():
    provider, _ = _make_db_provider()
    for kpi in ALL_KPIS.values():
        provider._cache_item(kpi.model_copy(update={"id": kpi.name.lower().replace(" ", "_")}))
    result = provider.get_by_client("bicycle")
    assert {k.name for k in result} == set(BICYCLE_KPIS.keys())


def test_get_by_client_excludes_unscoped_items():
    """Items with client_id=None must never leak into a tenant-scoped read."""
    provider, _ = _make_db_provider()
    unscoped = _make_kpi("Shared Metric", "bicycle").model_copy(
        update={"client_id": None, "id": "shared_metric"}
    )
    provider._cache_item(unscoped)
    scoped = _make_kpi("Gross Revenue", "bicycle").model_copy(update={"id": "gross_revenue"})
    provider._cache_item(scoped)
    result = provider.get_by_client("bicycle")
    assert {k.name for k in result} == {"Gross Revenue"}


def test_get_by_client_empty_client_id_returns_nothing():
    """Fail-closed: no tenant context → no rows, never all rows."""
    provider, _ = _make_db_provider()
    provider._cache_item(_make_kpi("Gross Revenue", "bicycle").model_copy(update={"id": "gross_revenue"}))
    assert provider.get_by_client("") == []
    assert provider.get_by_client(None) == []


# ---------------------------------------------------------------------------
# Infra B3: composite-key delete must match ALL key fields (cross-tenant guard)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_composite_delete_targets_single_tenant_row():
    """Deleting 'bicycle:net_revenue' must never touch lubricants' net_revenue."""
    provider, db_manager = _make_db_provider(key_fields=["client_id", "id"])
    db_manager.delete_record_multi = AsyncMock(return_value=True)
    db_manager.delete_record = AsyncMock(return_value=True)

    result = await provider._delete_async("bicycle:net_revenue")

    assert result is True
    db_manager.delete_record_multi.assert_awaited_once_with(
        "kpis", {"client_id": "bicycle", "id": "net_revenue"}
    )
    db_manager.delete_record.assert_not_awaited()


# ---------------------------------------------------------------------------
# Infra B3 Layer 1: tenant_scope — fail-closed without a client_id
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tenant_scope_rejects_empty_client_id():
    from src.database.tenant_scope import tenant_scope

    pool = MagicMock()
    with pytest.raises(ValueError):
        async with tenant_scope(pool, ""):
            pass
    pool.acquire.assert_not_called()


# ---------------------------------------------------------------------------
# Infra B3 Layer 3: DPA execute_sql — DGA gate on tenant-scoped SQL
# ---------------------------------------------------------------------------

async def _get_dpa_agent():
    from src.agents.new.a9_orchestrator_agent import (
        A9_Orchestrator_Agent,
        initialize_agent_registry,
    )
    from src.registry.factory import RegistryFactory

    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()
    rf = RegistryFactory()

    dpa = await orchestrator.create_agent_with_dependencies(
        "A9_Data_Product_Agent",
        {"orchestrator": orchestrator, "registry_factory": rf},
    )
    return dpa


@pytest.mark.asyncio
async def test_dpa_execute_sql_denies_on_dga_rejection():
    dpa = await _get_dpa_agent()
    mock_dga = MagicMock()
    mock_dga.validate_data_access = AsyncMock(
        return_value=SimpleNamespace(allowed=False, reason="Client mismatch", policy_id=None)
    )
    dpa.data_governance_agent = mock_dga

    ctx = _make_principal("cfo_002", "lubricants")
    result = await dpa.execute_sql(
        "SELECT 1", principal_context=ctx, data_product_id="bicycle_star_schema"
    )

    assert result["success"] is False
    assert "Access denied by Data Governance" in result["message"]
    assert result["rows"] == []
    req = mock_dga.validate_data_access.await_args.args[0]
    assert req.principal_id == "cfo_002"
    assert req.client_id == "lubricants"
    assert req.data_product_id == "bicycle_star_schema"


@pytest.mark.asyncio
async def test_dpa_execute_sql_fails_closed_without_dga():
    """A tenant-scoped principal with no DGA wired must be denied, not allowed through."""
    dpa = await _get_dpa_agent()
    dpa.data_governance_agent = None

    ctx = _make_principal("cfo_002", "lubricants")
    result = await dpa.execute_sql(
        "SELECT 1", principal_context=ctx, data_product_id="bicycle_star_schema"
    )

    assert result["success"] is False
    assert "fail-closed" in result["message"]


@pytest.mark.asyncio
async def test_dpa_execute_sql_skips_gate_for_unscoped_principal():
    """System/admin context (no client_id) is not gated — DGA must not be consulted."""
    dpa = await _get_dpa_agent()
    mock_dga = MagicMock()
    mock_dga.validate_data_access = AsyncMock()
    dpa.data_governance_agent = mock_dga

    ctx = _make_principal("admin_001", None)
    await dpa.execute_sql(
        "SELECT 1", principal_context=ctx, data_product_id="bicycle_star_schema"
    )

    mock_dga.validate_data_access.assert_not_awaited()
