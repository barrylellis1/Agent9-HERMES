"""
Regression tests: no registry write may persist a record without a resolved
client_id — as a category, not as isolated fixes per endpoint.

Context: the data-product-onboarding registration path and the KPI Assistant
finalize path both constructed registry records (DataProduct, KPI) with no
client_id threaded through the request chain at all, silently falling back to
DataProduct/KPI's env-var default (effectively misattributing every write to
whichever client that default happened to be, regardless of which client was
actually being onboarded). RLS (Infra B3) does not catch this class of bug —
it enforces that a *claimed* tenant identity cannot read another tenant's
rows; it has no way to know the application claimed the *wrong* identity in
the first place. These tests lock in the fix at the two most severe, directly
wizard-reachable call sites, plus the shared helper functions
(_resolve_create_client_id / _enforce_write_ownership) that every
registry.py CRUD endpoint (kpis, principals, data-products, business-processes,
glossary) now depends on for the same guarantee.
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.api.auth_middleware import AuthUser


# ---------------------------------------------------------------------------
# Shared helpers used by every registry.py CRUD endpoint
# ---------------------------------------------------------------------------

class TestEnforceWriteOwnership:
    def test_raises_when_no_client_id_and_no_auth(self):
        from src.api.routes.registry import _enforce_write_ownership

        with pytest.raises(HTTPException) as exc_info:
            _enforce_write_ownership(existing_client_id=None, client_id_qp=None, user=None)
        assert exc_info.value.status_code == 400

    def test_raises_when_caller_does_not_own_existing_record(self):
        from src.api.routes.registry import _enforce_write_ownership

        with pytest.raises(HTTPException) as exc_info:
            _enforce_write_ownership(existing_client_id="acme_corp", client_id_qp="other_client", user=None)
        assert exc_info.value.status_code == 403

    def test_authenticated_user_identity_used_regardless_of_query_param(self):
        from src.api.routes.registry import _enforce_write_ownership

        # For ownership checks the authenticated user's own client_id is what's
        # trusted — a query param can't override it (mismatch-vs-request-intent
        # is _resolve_create_client_id's job, tested separately below).
        user = AuthUser(sub="u1", email="cfo@acme.com", client_id="acme_corp")
        resolved = _enforce_write_ownership(existing_client_id="acme_corp", client_id_qp="ignored", user=user)
        assert resolved == "acme_corp"

    def test_succeeds_and_returns_caller_client_id_when_owned(self):
        from src.api.routes.registry import _enforce_write_ownership

        resolved = _enforce_write_ownership(existing_client_id="acme_corp", client_id_qp="acme_corp", user=None)
        assert resolved == "acme_corp"


class TestResolveCreateClientId:
    @pytest.mark.asyncio
    async def test_raises_when_unauthenticated_and_no_client_id(self):
        from src.api.routes.registry import _resolve_create_client_id

        factory = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await _resolve_create_client_id(client_id_qp=None, user=None, factory=factory)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_authenticated_user_forbidden_from_writing_to_other_client(self):
        from src.api.routes.registry import _resolve_create_client_id

        factory = MagicMock()
        user = AuthUser(sub="u1", email="cfo@acme.com", client_id="acme_corp")
        with pytest.raises(HTTPException) as exc_info:
            await _resolve_create_client_id(client_id_qp="other_client", user=user, factory=factory)
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# register_data_product — the data-product-onboarding registration path
# ---------------------------------------------------------------------------

class TestRegisterDataProductRequiresClientId:
    @pytest.mark.asyncio
    async def test_missing_client_id_fails_closed_not_silent_default(self):
        from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
        from src.agents.models.data_product_onboarding_models import DataProductRegistrationRequest

        agent = A9_Data_Product_Agent.__new__(A9_Data_Product_Agent)
        agent.data_product_provider = MagicMock()
        agent.logger = MagicMock()

        request = DataProductRegistrationRequest(
            request_id="req1",
            principal_id="admin_user",
            data_product_id="dp_test",
            client_id=None,  # never threaded through — the original bug
        )

        response = await agent.register_data_product(request)

        assert response.status == "error"
        assert "client_id" in (response.error_message or "").lower()
        agent.data_product_provider.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_provided_client_id_is_stamped_onto_the_registered_record(self):
        from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
        from src.agents.models.data_product_onboarding_models import DataProductRegistrationRequest

        agent = A9_Data_Product_Agent.__new__(A9_Data_Product_Agent)
        agent.data_product_provider = MagicMock()
        agent.data_product_provider.get.return_value = None
        agent.data_product_provider.upsert = AsyncMock(return_value=True)
        agent.data_product_provider.source_path = None
        agent.logger = MagicMock()

        request = DataProductRegistrationRequest(
            request_id="req2",
            principal_id="admin_user",
            data_product_id="dp_test",
            client_id="brookshire_brothers",
            source_system="snowflake",
            display_name="Test Data Product",
            domain="Finance",
        )

        response = await agent.register_data_product(request)

        assert response.status == "success"
        assert response.registry_entry["client_id"] == "brookshire_brothers"
        assert response.registry_entry["source_system"] == "snowflake"
        persisted = agent.data_product_provider.upsert.call_args[0][0]
        assert persisted.client_id == "brookshire_brothers"


# ---------------------------------------------------------------------------
# KPI Assistant finalize — the "Register Data Product" button's KPI write path
# ---------------------------------------------------------------------------

class TestKpiFinalizeRequiresClientId:
    @pytest.mark.asyncio
    async def test_missing_client_id_fails_closed_not_silent_default(self):
        from src.agents.new.a9_kpi_assistant_agent import A9_KPI_Assistant_Agent

        agent = A9_KPI_Assistant_Agent.__new__(A9_KPI_Assistant_Agent)
        agent.logger = MagicMock()

        results = await agent._trigger_registry_updates(
            data_product_id="dp_test",
            kpis=[{"id": "kpi1", "name": "Test KPI", "domain": "Finance", "unit": "USD"}],
            client_id=None,  # never threaded through — the original bug
        )

        assert results["success"] == []
        assert len(results["failed"]) == 1
        assert "client_id" in results["failed"][0]["error"].lower()

    @pytest.mark.asyncio
    async def test_provided_client_id_is_stamped_onto_every_kpi(self):
        from src.agents.new.a9_kpi_assistant_agent import A9_KPI_Assistant_Agent

        agent = A9_KPI_Assistant_Agent.__new__(A9_KPI_Assistant_Agent)
        agent.logger = MagicMock()

        captured_kpis = []

        def fake_register(kpi):
            captured_kpis.append(kpi)
            return True

        mock_provider = MagicMock()
        mock_provider.register = fake_register

        mock_factory = MagicMock()
        mock_factory.is_initialized = True
        mock_factory.get_kpi_provider.return_value = mock_provider

        import src.registry.factory as factory_module
        original_factory_cls = factory_module.RegistryFactory
        factory_module.RegistryFactory = lambda: mock_factory
        try:
            results = await agent._trigger_registry_updates(
                data_product_id="dp_test",
                kpis=[
                    {"id": "kpi1", "name": "KPI One", "domain": "Finance", "unit": "USD"},
                    {"id": "kpi2", "name": "KPI Two", "domain": "Finance", "unit": "%"},
                ],
                client_id="brookshire_brothers",
            )
        finally:
            factory_module.RegistryFactory = original_factory_cls

        assert results["failed"] == []
        assert set(results["success"]) == {"kpi1", "kpi2"}
        assert all(kpi.client_id == "brookshire_brothers" for kpi in captured_kpis)
