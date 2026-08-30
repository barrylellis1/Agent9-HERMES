# arch-allow-direct-agent-construction
"""
Phase 16, O3 follow-up (DEVELOPMENT_PLAN.md): discovery_only skips
registration entirely.

Every "Schema Discovery" step in the onboarding wizard calls
orchestrate_data_product_onboarding purely to preview tables
(data_product_id='temp_discovery', no display_name/domain/description) --
but every prior version of this method registered that placeholder anyway,
planting a junk 'temp_discovery' row into the real data_products table for
whichever client was targeted. Found live 2026-08-30 (two stray rows, one
from 2026-07-24, cleaned up directly in Supabase).
"""

from unittest.mock import AsyncMock

import pytest

from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent
from src.agents.models.data_product_onboarding_models import (
    DataProductOnboardingWorkflowRequest,
    DataProductSchemaInspectionResponse,
    DataProductRegistrationResponse,
)


def _orchestrator():
    return A9_Orchestrator_Agent({})


def _inspection_response():
    return DataProductSchemaInspectionResponse.success(
        request_id="req1",
        environment="dev",
        tables=[],
        inferred_kpis=[],
    )


def _base_request(**overrides) -> DataProductOnboardingWorkflowRequest:
    fields = dict(
        request_id="req1",
        principal_id="admin_user",
        client_id="hess",
        data_product_id="temp_discovery",
        source_system="sqlserver",
    )
    fields.update(overrides)
    return DataProductOnboardingWorkflowRequest(**fields)


class TestDiscoveryOnlySkipsRegistration:
    @pytest.mark.asyncio
    async def test_discovery_only_never_calls_register_data_product(self):
        orch = _orchestrator()
        orch.execute_agent_method = AsyncMock(return_value=_inspection_response())

        request = _base_request(discovery_only=True)
        response = await orch.orchestrate_data_product_onboarding(request)

        assert response.status == "success"
        called_methods = [c.args[1] for c in orch.execute_agent_method.call_args_list]
        assert called_methods == ["inspect_source_schema"], (
            f"discovery_only=True must call ONLY inspect_source_schema, got: {called_methods}"
        )

    @pytest.mark.asyncio
    async def test_non_discovery_call_still_registers_by_default(self):
        """Regression guard the other direction: a REAL registration call
        (discovery_only defaults to False) must still register -- this bug
        fix must not silently disable registration for everyone."""
        orch = _orchestrator()

        async def fake_call(agent_name, method_name, payload):
            if method_name == "inspect_source_schema":
                return _inspection_response()
            if method_name == "register_data_product":
                return DataProductRegistrationResponse.success(
                    request_id="req1", registry_entry={"id": "dp_test"},
                    was_created=True, registry_path=None,
                )
            raise AssertionError(f"unexpected call: {method_name}")

        orch.execute_agent_method = AsyncMock(side_effect=fake_call)

        request = _base_request(
            data_product_id="dp_test",
            data_product_name="Test Product",
            data_product_domain="Finance",
        )
        response = await orch.orchestrate_data_product_onboarding(request)

        assert response.status == "success"
        called_methods = [c.args[1] for c in orch.execute_agent_method.call_args_list]
        assert "register_data_product" in called_methods

    @pytest.mark.asyncio
    async def test_discovery_only_response_still_carries_inspection_result(self):
        """The UI reads steps.find(s => s.name === 'inspect_source_schema')
        from this response during discovery -- confirm that keeps working
        with registration skipped."""
        orch = _orchestrator()
        orch.execute_agent_method = AsyncMock(return_value=_inspection_response())

        request = _base_request(discovery_only=True)
        response = await orch.orchestrate_data_product_onboarding(request)

        step_names = [s.name for s in response.steps]
        assert step_names == ["inspect_source_schema"]
        assert response.steps[0].status == "success"

    @pytest.mark.asyncio
    async def test_discovery_only_default_is_false(self):
        """discovery_only must default to False -- an omitted field on any
        existing caller must not silently start skipping registration."""
        request = _base_request()
        assert request.discovery_only is False
