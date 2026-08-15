# arch-allow-direct-agent-construction
"""GET/POST /api/v1/admin/slice-validity — docs/architecture/kpi_semantic_contract.md §4.

Mirrors tests/unit/test_admin_registry_reload.py's structure. Two layers:
route-level (FastAPI TestClient against a mocked runtime) and
AgentRuntime.get_cached_slice_validity()/run_slice_validity_check() directly
(mocked registry/agents).

THE ONE DELIBERATE DIFFERENCE FROM connection-health's GET
------------------------------------------------------------
GET /connection-health reads an in-memory cache (_last_health_probe) because
connection probes have no natural persisted home. GET /slice-validity reads
the KPI record itself — slice-validity results ARE durably stored — so this
must be correct after a process restart with no probe having run in THIS
process. test_get_reads_the_database_not_process_memory pins that.
"""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Route-level — FastAPI TestClient, mocked runtime
# ---------------------------------------------------------------------------


def _make_app(*, get_result=None, test_result=None):
    from fastapi import FastAPI
    from src.api.routes.admin import router
    from src.api.runtime import get_agent_runtime

    app = FastAPI()
    app.include_router(router)

    async def _mock_runtime():
        rt = MagicMock()
        rt.get_cached_slice_validity = MagicMock(return_value=get_result or {})
        rt.run_slice_validity_check = AsyncMock(return_value=test_result or {})
        return rt

    app.dependency_overrides[get_agent_runtime] = _mock_runtime
    return app


def test_get_requires_kpi_id_and_client_id():
    app = _make_app()
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/v1/admin/slice-validity")
    assert resp.status_code == 422  # FastAPI query validation, not a 500


def test_get_returns_not_probed_when_never_checked():
    result = {
        "status": "not_probed", "kpi_id": "gross_margin_pct", "client_id": "lubricants",
        "results": [], "not_sliceable_by": [], "checked_at": None,
    }
    app = _make_app(get_result=result)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/v1/admin/slice-validity?kpi_id=gross_margin_pct&client_id=lubricants")
    assert resp.status_code == 200
    body = json.loads(resp.content)
    assert body["status"] == "not_probed"
    assert body["data"]["not_sliceable_by"] == []


def test_get_surfaces_a_persisted_invalid_verdict():
    result = {
        "status": "checked", "kpi_id": "gross_margin_pct", "client_id": "lubricants",
        "results": [{"dimension": "customer_name", "verdict": "INVALID", "coverage": 0.05,
                      "counts": {"Revenue": 20, "COGS": 1}}],
        "not_sliceable_by": ["customer_name"],
        "checked_at": "2026-08-15T00:00:00+00:00",
    }
    app = _make_app(get_result=result)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/v1/admin/slice-validity?kpi_id=gross_margin_pct&client_id=lubricants")
    body = json.loads(resp.content)
    assert body["data"]["not_sliceable_by"] == ["customer_name"]
    assert body["data"]["checked_at"] is not None


def test_post_triggers_a_fresh_check_and_returns_its_result():
    result = {
        "status": "success", "kpi_id": "gross_margin_pct", "client_id": "lubricants",
        "results": [], "not_sliceable_by": [], "checked_at": "2026-08-15T00:00:00+00:00",
    }
    app = _make_app(test_result=result)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/v1/admin/slice-validity/test?kpi_id=gross_margin_pct&client_id=lubricants")
    assert resp.status_code == 200
    body = json.loads(resp.content)
    assert body["status"] == "success"


def test_post_no_auth_required():
    """Matches connection-health's current MVP posture — flagged as a
    conscious tradeoff in the plan's premortem, not an oversight."""
    app = _make_app(test_result={"status": "success"})
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/v1/admin/slice-validity/test?kpi_id=x&client_id=y")
    assert resp.status_code != 403 and resp.status_code != 503


def test_post_forwards_dimensions_to_the_runtime_call():
    from fastapi import FastAPI
    from src.api.routes.admin import router
    from src.api.runtime import get_agent_runtime

    app = FastAPI()
    app.include_router(router)
    mock_rt = MagicMock()
    mock_rt.run_slice_validity_check = AsyncMock(return_value={"status": "success"})

    async def _mock_runtime():
        return mock_rt

    app.dependency_overrides[get_agent_runtime] = _mock_runtime
    client = TestClient(app, raise_server_exceptions=False)

    client.post(
        "/api/v1/admin/slice-validity/test"
        "?kpi_id=gross_margin_pct&client_id=lubricants&dimensions=customer_name&dimensions=product_name"
    )

    mock_rt.run_slice_validity_check.assert_awaited_once()
    _, kwargs = mock_rt.run_slice_validity_check.call_args
    assert kwargs["kpi_id"] == "gross_margin_pct"
    assert kwargs["client_id"] == "lubricants"
    assert kwargs["dimensions"] == ["customer_name", "product_name"]


# ---------------------------------------------------------------------------
# AgentRuntime.get_cached_slice_validity() — database read, not process cache
# ---------------------------------------------------------------------------


def _kpi_stub(**overrides):
    defaults = dict(
        client_id="lubricants",
        not_sliceable_by=[],
        slice_validity_details=None,
        slice_validity_checked_at=None,
    )
    defaults.update(overrides)
    stub = MagicMock()
    for k, v in defaults.items():
        setattr(stub, k, v)
    return stub


def test_get_reads_the_database_not_process_memory():
    """No _last_health_probe-style attribute involved at all — a fresh
    AgentRuntime() with zero prior activity in THIS process must still
    return a real result if the registry has one."""
    from src.api.runtime import AgentRuntime

    rt = AgentRuntime()
    kpi = _kpi_stub(
        not_sliceable_by=["customer_name"],
        slice_validity_details={"customer_name": {"verdict": "INVALID", "coverage": 0.05, "counts": {}}},
        slice_validity_checked_at=MagicMock(isoformat=lambda: "2026-08-15T00:00:00+00:00"),
    )
    provider = MagicMock()
    provider.get.return_value = kpi
    rt._registry_factory = MagicMock()
    rt._registry_factory.get_provider.return_value = provider

    result = rt.get_cached_slice_validity(kpi_id="gross_margin_pct", client_id="lubricants")

    assert result["status"] == "checked"
    assert result["not_sliceable_by"] == ["customer_name"]
    assert result["checked_at"] == "2026-08-15T00:00:00+00:00"


def test_get_returns_not_probed_for_a_kpi_that_was_never_checked():
    from src.api.runtime import AgentRuntime

    rt = AgentRuntime()
    provider = MagicMock()
    provider.get.return_value = _kpi_stub()  # never checked — all None/empty defaults
    rt._registry_factory = MagicMock()
    rt._registry_factory.get_provider.return_value = provider

    result = rt.get_cached_slice_validity(kpi_id="gross_margin_pct", client_id="lubricants")

    assert result["status"] == "not_probed"
    assert result["checked_at"] is None


def test_get_cross_tenant_kpi_is_treated_as_not_probed_not_leaked():
    from src.api.runtime import AgentRuntime

    rt = AgentRuntime()
    provider = MagicMock()
    provider.get.return_value = _kpi_stub(
        client_id="hess",  # wrong tenant
        not_sliceable_by=["customer_name"],
        slice_validity_checked_at=MagicMock(isoformat=lambda: "2026-08-15T00:00:00+00:00"),
    )
    rt._registry_factory = MagicMock()
    rt._registry_factory.get_provider.return_value = provider

    result = rt.get_cached_slice_validity(kpi_id="gross_margin_pct", client_id="lubricants")

    assert result["status"] == "not_probed"
    assert result["not_sliceable_by"] == []  # the other tenant's data must not leak through


def test_get_handles_missing_registry_gracefully():
    from src.api.runtime import AgentRuntime

    rt = AgentRuntime()
    rt._registry_factory = None

    result = rt.get_cached_slice_validity(kpi_id="x", client_id="y")

    assert result["status"] == "not_probed"


# ---------------------------------------------------------------------------
# AgentRuntime.run_slice_validity_check()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_check_handles_missing_dga_gracefully():
    from src.api.runtime import AgentRuntime

    rt = AgentRuntime()
    rt._agents = {}

    result = await rt.run_slice_validity_check(kpi_id="x", client_id="y")

    assert result["status"] == "error"
    assert "Data Governance Agent" in result["error_message"]


@pytest.mark.asyncio
async def test_run_check_delegates_to_dga_and_returns_its_response():
    from src.api.runtime import AgentRuntime
    from src.agents.models.data_governance_models import SliceValidityCheckResponse

    rt = AgentRuntime()
    dga = MagicMock()
    dga.check_slice_validity = AsyncMock(return_value=SliceValidityCheckResponse(
        kpi_id="gross_margin_pct", client_id="lubricants", status="success",
        not_sliceable_by=["customer_name"],
    ))
    rt._agents = {"A9_Data_Governance_Agent": dga}

    result = await rt.run_slice_validity_check(kpi_id="gross_margin_pct", client_id="lubricants")

    dga.check_slice_validity.assert_awaited_once()
    assert result["status"] == "success"
    assert result["not_sliceable_by"] == ["customer_name"]
