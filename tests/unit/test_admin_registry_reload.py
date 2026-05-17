# arch-allow-direct-agent-construction
"""
Infra A4-c: Admin registry reload endpoint tests.

Validates that POST /api/v1/admin/registry/reload:
  1. Returns 503 when ADMIN_API_KEY env var is not set
  2. Returns 403 when the wrong key is supplied
  3. Returns 200 with per-agent status when the correct key is supplied
  4. Reports partial status when one agent reload fails
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app(reload_result: dict):
    """Build a minimal FastAPI app with the admin router and a mocked runtime."""
    from fastapi import FastAPI
    from src.api.routes.admin import router
    from src.api.runtime import get_agent_runtime

    app = FastAPI()
    app.include_router(router)

    async def _mock_runtime():
        rt = MagicMock()
        rt.reload_registry = AsyncMock(return_value=reload_result)
        return rt

    app.dependency_overrides[get_agent_runtime] = _mock_runtime
    return app


_GOOD_RESULT = {
    "status": "ok",
    "agents": {
        "A9_Situation_Awareness_Agent": "ok",
        "A9_Principal_Context_Agent": "ok",
        "A9_Data_Product_Agent": "ok",
    },
    "timestamp": "2026-05-17T00:00:00+00:00",
}

_PARTIAL_RESULT = {
    "status": "partial",
    "agents": {
        "A9_Situation_Awareness_Agent": "ok",
        "A9_Principal_Context_Agent": "error: provider unavailable",
        "A9_Data_Product_Agent": "ok",
    },
    "timestamp": "2026-05-17T00:00:00+00:00",
}


# ---------------------------------------------------------------------------
# Auth tests
# ---------------------------------------------------------------------------

def test_503_when_env_var_not_set(monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    app = _make_app(_GOOD_RESULT)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/v1/admin/registry/reload", headers={"X-Admin-Key": "anything"})
    assert resp.status_code == 503


def test_403_when_wrong_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret123")
    app = _make_app(_GOOD_RESULT)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/v1/admin/registry/reload", headers={"X-Admin-Key": "wrong"})
    assert resp.status_code == 403


def test_403_when_no_key_header(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret123")
    app = _make_app(_GOOD_RESULT)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/v1/admin/registry/reload")
    assert resp.status_code == 403


def test_200_with_correct_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret123")
    app = _make_app(_GOOD_RESULT)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/v1/admin/registry/reload", headers={"X-Admin-Key": "secret123"})
    assert resp.status_code == 200
    body = json.loads(resp.content)
    assert body["status"] == "ok"
    assert body["data"]["agents"]["A9_Situation_Awareness_Agent"] == "ok"


def test_partial_status_propagated(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret123")
    app = _make_app(_PARTIAL_RESULT)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.post("/api/v1/admin/registry/reload", headers={"X-Admin-Key": "secret123"})
    assert resp.status_code == 200
    body = json.loads(resp.content)
    assert body["status"] == "partial"
    assert "error" in body["data"]["agents"]["A9_Principal_Context_Agent"]


# ---------------------------------------------------------------------------
# AgentRuntime.reload_registry() unit tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_reload_calls_all_agent_methods():
    from src.api.runtime import AgentRuntime

    rt = AgentRuntime()
    sa = MagicMock()
    sa._load_kpi_registry = AsyncMock()
    pca = MagicMock()
    pca._principal_provider = MagicMock()
    pca._principal_provider.load = AsyncMock()
    pca._load_principal_profiles = AsyncMock()
    dpa = MagicMock()
    dpa._refresh_data_product_registry = AsyncMock()

    rt._agents = {
        "A9_Situation_Awareness_Agent": sa,
        "A9_Principal_Context_Agent": pca,
        "A9_Data_Product_Agent": dpa,
    }

    result = await rt.reload_registry()

    sa._load_kpi_registry.assert_awaited_once()
    pca._principal_provider.load.assert_awaited_once()
    pca._load_principal_profiles.assert_awaited_once()
    dpa._refresh_data_product_registry.assert_awaited_once()
    assert result["status"] == "ok"
    assert all(v == "ok" for v in result["agents"].values())


@pytest.mark.asyncio
async def test_reload_partial_on_error():
    from src.api.runtime import AgentRuntime

    rt = AgentRuntime()
    sa = MagicMock()
    sa._load_kpi_registry = AsyncMock(side_effect=RuntimeError("boom"))
    pca = MagicMock()
    pca._principal_provider = MagicMock()
    pca._principal_provider.load = AsyncMock()
    pca._load_principal_profiles = AsyncMock()
    dpa = MagicMock()
    dpa._refresh_data_product_registry = AsyncMock()

    rt._agents = {
        "A9_Situation_Awareness_Agent": sa,
        "A9_Principal_Context_Agent": pca,
        "A9_Data_Product_Agent": dpa,
    }

    result = await rt.reload_registry()
    assert result["status"] == "partial"
    assert "error" in result["agents"]["A9_Situation_Awareness_Agent"]
    assert result["agents"]["A9_Data_Product_Agent"] == "ok"


@pytest.mark.asyncio
async def test_reload_handles_missing_agents():
    from src.api.runtime import AgentRuntime

    rt = AgentRuntime()
    rt._agents = {}

    result = await rt.reload_registry()
    assert result["status"] == "partial"
    assert all(v == "not_loaded" for v in result["agents"].values())
