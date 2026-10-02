# arch-allow-direct-agent-construction
"""GET /api/v1/admin/audit-events (docs/architecture/audit_event_system_design.md,
section 4 "Read path") -- the smallest unlock toward anyone actually seeing
what the five reliability signals have written. AuditService.query() is
patched directly, same convention as test_admin_registry_reload.py patching
AgentRuntime.reload_registry.
"""
import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes.admin import router
from src.registry.models.audit_event import AuditEvent


def _app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def _event(**overrides) -> AuditEvent:
    defaults = dict(
        id="11111111-1111-1111-1111-111111111111",
        client_id="lubricants",
        event_type="reliability.rollup_check",
        severity="warning",
        outcome="fail",
        source_agent="A9_Deep_Analysis_Agent",
        resource_type="kpi",
        resource_id="gross_margin_pct",
        payload={"dimension": "customer_name"},
        created_at="2026-10-02T12:00:00+00:00",
    )
    defaults.update(overrides)
    return AuditEvent(**defaults)


def test_503_when_env_var_not_set(monkeypatch):
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)
    client = TestClient(_app(), raise_server_exceptions=False)
    resp = client.get("/api/v1/admin/audit-events", headers={"X-Admin-Key": "anything"})
    assert resp.status_code == 503


def test_403_when_wrong_key(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret123")
    client = TestClient(_app(), raise_server_exceptions=False)
    resp = client.get("/api/v1/admin/audit-events", headers={"X-Admin-Key": "wrong"})
    assert resp.status_code == 403


def test_403_when_no_key_header(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret123")
    client = TestClient(_app(), raise_server_exceptions=False)
    resp = client.get("/api/v1/admin/audit-events")
    assert resp.status_code == 403


def test_200_with_correct_key_returns_events(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret123")
    with patch("src.api.routes.admin.AuditService.pool_available", return_value=True), \
         patch("src.api.routes.admin.AuditService.query", new=AsyncMock(return_value=[_event()])):
        client = TestClient(_app(), raise_server_exceptions=False)
        resp = client.get("/api/v1/admin/audit-events", headers={"X-Admin-Key": "secret123"})

    assert resp.status_code == 200
    body = json.loads(resp.content)
    assert body["status"] == "ok"
    assert body["data"]["count"] == 1
    assert body["data"]["events"][0]["event_type"] == "reliability.rollup_check"


def test_empty_result_with_pool_available_is_ok_not_degraded(monkeypatch):
    """The pool answered and genuinely found nothing matching the filters --
    distinct from no pool at all (see the dedicated 'degraded' test below).
    Collapsing the two would make the panel silently going dark read
    identically to a clean bill of health (code-review finding, 2026-10-02)."""
    monkeypatch.setenv("ADMIN_API_KEY", "secret123")
    with patch("src.api.routes.admin.AuditService.pool_available", return_value=True), \
         patch("src.api.routes.admin.AuditService.query", new=AsyncMock(return_value=[])):
        client = TestClient(_app(), raise_server_exceptions=False)
        resp = client.get("/api/v1/admin/audit-events", headers={"X-Admin-Key": "secret123"})

    assert resp.status_code == 200
    body = json.loads(resp.content)
    assert body["status"] == "ok"
    assert body["data"]["count"] == 0
    assert body["data"]["events"] == []


def test_no_pool_is_degraded_not_ok(monkeypatch):
    """No database pool at all -- must read as 'degraded', never as 'ok' with
    an empty list, which would be indistinguishable from every reliability
    check having passed."""
    monkeypatch.setenv("ADMIN_API_KEY", "secret123")
    with patch("src.api.routes.admin.AuditService.pool_available", return_value=False), \
         patch("src.api.routes.admin.AuditService.query", new=AsyncMock(return_value=[])) as spy:
        client = TestClient(_app(), raise_server_exceptions=False)
        resp = client.get("/api/v1/admin/audit-events", headers={"X-Admin-Key": "secret123"})

    assert resp.status_code == 200
    body = json.loads(resp.content)
    assert body["status"] == "degraded"
    assert body["data"]["count"] == 0
    spy.assert_not_called()  # no pool -> never even attempts the query


def test_query_params_are_forwarded_to_audit_service(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "secret123")
    spy = AsyncMock(return_value=[])
    with patch("src.api.routes.admin.AuditService.pool_available", return_value=True), \
         patch("src.api.routes.admin.AuditService.query", new=spy):
        client = TestClient(_app(), raise_server_exceptions=False)
        resp = client.get(
            "/api/v1/admin/audit-events",
            headers={"X-Admin-Key": "secret123"},
            params={"client_id": "lubricants", "event_type": "reliability.slice_validity", "outcome": "fail", "limit": 50},
        )

    assert resp.status_code == 200
    spy.assert_awaited_once()
    kwargs = spy.call_args.kwargs
    assert kwargs["client_id"] == "lubricants"
    assert kwargs["event_type"] == "reliability.slice_validity"
    assert kwargs["outcome"] == "fail"
    assert kwargs["limit"] == 50
