# arch-allow-direct-agent-construction
"""
Infra A2: server-derived client_id stamping on registry writes.

Registry models (KPI/PrincipalProfile/DataProduct) default client_id from a
static ACTIVE_CLIENT_ID server env var — a body-omitted client_id would
silently stamp new records with whatever tenant the server process happens to
be configured for, not the client actually being onboarded. These tests
verify the fix in src/api/routes/registry.py: create/replace/update routes
resolve client_id authoritatively server-side (JWT when present, a validated
client_id query param otherwise) and fail closed rather than falling back to
a default tenant.
"""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.auth_middleware import AuthUser, get_optional_user
from src.api.routes.registry import get_registry_factory, router


def _make_app(kpi_provider=None, principal_provider=None, data_product_provider=None,
              bc_provider=None, user: AuthUser | None = None):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")

    async def _mock_factory():
        factory = MagicMock()
        factory.get_kpi_provider.return_value = kpi_provider
        factory.get_principal_profile_provider.return_value = principal_provider
        factory.get_data_product_provider.return_value = data_product_provider
        factory.get_business_context_provider.return_value = bc_provider
        return factory

    app.dependency_overrides[get_registry_factory] = _mock_factory
    app.dependency_overrides[get_optional_user] = lambda: user
    return TestClient(app, raise_server_exceptions=False)


def _mock_kpi_provider(existing=None):
    provider = MagicMock()
    provider.get.return_value = existing
    provider.register = AsyncMock()
    provider.upsert = AsyncMock()
    return provider


def _mock_bc_provider(known_clients: set[str]):
    provider = MagicMock()
    provider.list_contexts = AsyncMock(return_value=[{"id": cid} for cid in known_clients])
    return provider


KPI_BODY = {
    "id": "gross_revenue",
    "name": "Gross Revenue",
    "domain": "Finance",
    "data_product_id": "fi_star_schema",
}


# ---------------------------------------------------------------------------
# POST /kpis — create path
# ---------------------------------------------------------------------------

def test_create_kpi_no_auth_no_client_id_fails_closed():
    provider = _mock_kpi_provider()
    client = _make_app(kpi_provider=provider, bc_provider=_mock_bc_provider({"bicycle"}))
    resp = client.post("/api/v1/registry/kpis", json=KPI_BODY)
    assert resp.status_code == 400
    provider.register.assert_not_called()


def test_create_kpi_no_auth_unknown_client_id_rejected():
    provider = _mock_kpi_provider()
    client = _make_app(kpi_provider=provider, bc_provider=_mock_bc_provider({"bicycle"}))
    resp = client.post("/api/v1/registry/kpis?client_id=nonexistent", json=KPI_BODY)
    assert resp.status_code == 422
    provider.register.assert_not_called()


def test_create_kpi_no_auth_valid_client_id_survives_unrelated_model_validation_error():
    """A real client whose business_contexts row fails A9_PS_BusinessContext
    hydration for an unrelated reason (e.g. too many strategic_priorities)
    must still be recognized as existing — existence must not depend on full
    model deserialization. Regression test for a bug caught by live testing:
    _client_exists checks raw list_contexts() rows, not get_context()."""
    provider = _mock_kpi_provider()
    bc_provider = MagicMock()
    bc_provider.list_contexts = AsyncMock(return_value=[
        {"id": "apex_lubricants", "strategic_priorities": ["a", "b", "c", "d"]},  # would fail model validation
    ])
    bc_provider.get_context = AsyncMock(side_effect=Exception("should not be called"))
    client = _make_app(kpi_provider=provider, bc_provider=bc_provider)
    resp = client.post("/api/v1/registry/kpis?client_id=apex_lubricants", json=KPI_BODY)
    assert resp.status_code == 201
    persisted = provider.register.call_args.args[0]
    assert persisted.client_id == "apex_lubricants"


def test_create_kpi_no_auth_valid_client_id_stamps_from_query_param():
    provider = _mock_kpi_provider()
    client = _make_app(kpi_provider=provider, bc_provider=_mock_bc_provider({"bicycle"}))
    body = {**KPI_BODY, "client_id": "attacker_supplied"}
    resp = client.post("/api/v1/registry/kpis?client_id=bicycle", json=body)
    assert resp.status_code == 201
    persisted = provider.register.call_args.args[0]
    assert persisted.client_id == "bicycle", "body-supplied client_id must never be trusted"


def test_create_kpi_jwt_stamps_from_token_ignoring_body():
    provider = _mock_kpi_provider()
    user = AuthUser(sub="u1", email="cfo@lubricants.com", client_id="lubricants")
    client = _make_app(kpi_provider=provider, user=user)
    body = {**KPI_BODY, "client_id": "bicycle"}
    resp = client.post("/api/v1/registry/kpis", json=body)
    assert resp.status_code == 201
    persisted = provider.register.call_args.args[0]
    assert persisted.client_id == "lubricants"


def test_create_kpi_jwt_query_param_mismatch_rejected():
    provider = _mock_kpi_provider()
    user = AuthUser(sub="u1", email="cfo@lubricants.com", client_id="lubricants")
    client = _make_app(kpi_provider=provider, user=user)
    resp = client.post("/api/v1/registry/kpis?client_id=bicycle", json=KPI_BODY)
    assert resp.status_code == 403
    provider.register.assert_not_called()


# ---------------------------------------------------------------------------
# PUT /kpis/{id} — replace path
# ---------------------------------------------------------------------------

def test_replace_kpi_cross_client_rejected():
    existing = MagicMock(client_id="bicycle")
    provider = _mock_kpi_provider(existing=existing)
    user = AuthUser(sub="u1", email="cfo@lubricants.com", client_id="lubricants")
    client = _make_app(kpi_provider=provider, user=user)
    resp = client.put("/api/v1/registry/kpis/gross_revenue", json=KPI_BODY)
    assert resp.status_code == 403
    provider.upsert.assert_not_called()


def test_replace_kpi_same_client_preserves_client_id_even_if_body_differs():
    existing = MagicMock(client_id="bicycle")
    provider = _mock_kpi_provider(existing=existing)
    user = AuthUser(sub="u1", email="cfo@bicycle.com", client_id="bicycle")
    client = _make_app(kpi_provider=provider, user=user)
    body = {**KPI_BODY, "client_id": "lubricants"}  # attempted re-parent
    resp = client.put("/api/v1/registry/kpis/gross_revenue", json=body)
    assert resp.status_code == 200
    persisted = provider.upsert.call_args.args[0]
    assert persisted.client_id == "bicycle", "PUT must never re-parent a record to a different tenant"


def test_replace_kpi_no_existing_record_falls_back_to_create_resolution():
    provider = _mock_kpi_provider(existing=None)
    client = _make_app(kpi_provider=provider, bc_provider=_mock_bc_provider({"bicycle"}))
    resp = client.put("/api/v1/registry/kpis/gross_revenue?client_id=bicycle", json=KPI_BODY)
    assert resp.status_code == 200
    persisted = provider.upsert.call_args.args[0]
    assert persisted.client_id == "bicycle"


# ---------------------------------------------------------------------------
# PATCH /kpis/{id} — partial update path
# ---------------------------------------------------------------------------

def test_patch_kpi_cross_client_rejected():
    existing_model = MagicMock()
    existing_model.client_id = "bicycle"
    provider = _mock_kpi_provider(existing=existing_model)
    user = AuthUser(sub="u1", email="cfo@lubricants.com", client_id="lubricants")
    client = _make_app(kpi_provider=provider, user=user)
    resp = client.patch("/api/v1/registry/kpis/gross_revenue", json={"name": "Renamed"})
    assert resp.status_code == 403
    provider.upsert.assert_not_called()


def test_patch_kpi_strips_client_id_from_body():
    existing_model = MagicMock()
    existing_model.client_id = "bicycle"
    existing_model.model_copy.return_value = MagicMock(client_id="bicycle")
    provider = _mock_kpi_provider(existing=existing_model)
    user = AuthUser(sub="u1", email="cfo@bicycle.com", client_id="bicycle")
    client = _make_app(kpi_provider=provider, user=user)
    resp = client.patch("/api/v1/registry/kpis/gross_revenue", json={"name": "Renamed", "client_id": "lubricants"})
    assert resp.status_code == 200
    # model_copy must have been called WITHOUT client_id in the update dict
    update_arg = existing_model.model_copy.call_args.kwargs.get("update", {})
    assert "client_id" not in update_arg
    assert update_arg == {"name": "Renamed"}


# ---------------------------------------------------------------------------
# Confirm the same pattern was applied to Principals and Data Products
# ---------------------------------------------------------------------------

PRINCIPAL_BODY = {
    "id": "cfo_001",
    "name": "Test CFO",
    "title": "Chief Financial Officer",
}


def test_create_principal_no_auth_no_client_id_fails_closed():
    provider = MagicMock()
    provider.get.return_value = None
    client = _make_app(principal_provider=provider, bc_provider=_mock_bc_provider({"bicycle"}))
    resp = client.post("/api/v1/registry/principals", json=PRINCIPAL_BODY)
    assert resp.status_code == 400
    provider.register.assert_not_called()


def test_replace_principal_cross_client_rejected():
    existing = MagicMock(client_id="bicycle")
    provider = MagicMock()
    provider.get.return_value = existing
    user = AuthUser(sub="u1", email="cfo@lubricants.com", client_id="lubricants")
    client = _make_app(principal_provider=provider, user=user)
    resp = client.put("/api/v1/registry/principals/cfo_001", json=PRINCIPAL_BODY)
    assert resp.status_code == 403
    provider.upsert.assert_not_called()


DATA_PRODUCT_BODY = {
    "id": "fi_star_schema",
    "name": "FI Star Schema",
    "domain": "Finance",
    "owner": "Finance Team",
}


def test_create_data_product_no_auth_no_client_id_fails_closed():
    provider = MagicMock()
    provider.get.return_value = None
    client = _make_app(data_product_provider=provider, bc_provider=_mock_bc_provider({"bicycle"}))
    resp = client.post("/api/v1/registry/data-products", json=DATA_PRODUCT_BODY)
    assert resp.status_code == 400
    provider.register.assert_not_called()


def test_replace_data_product_cross_client_rejected():
    existing = MagicMock(client_id="bicycle")
    provider = MagicMock()
    provider.get.return_value = existing
    user = AuthUser(sub="u1", email="cfo@lubricants.com", client_id="lubricants")
    client = _make_app(data_product_provider=provider, user=user)
    resp = client.put("/api/v1/registry/data-products/fi_star_schema", json=DATA_PRODUCT_BODY)
    assert resp.status_code == 403
    provider.upsert.assert_not_called()
