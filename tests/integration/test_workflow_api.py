import asyncio
import json
import sys
from pathlib import Path

import pytest
from httpx import AsyncClient


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.main import app  # noqa: E402
from src.api.runtime import get_agent_runtime  # noqa: E402
from src.agents.models.data_product_onboarding_models import (  # noqa: E402
    DataProductOnboardingWorkflowResponse,
    WorkflowStepSummary,
)

pytestmark = pytest.mark.anyio("asyncio")


class _StubOrchestrator:
    async def execute_agent_method(self, agent_name: str, method_name: str, params):
        if agent_name == "A9_Principal_Context_Agent" and method_name == "get_principal_context_by_id":
            principal_id = params.get("principal_id")
            return {
                "context": {
                    "principal_id": principal_id,
                    "role": "CFO",
                    "business_processes": ["Finance: Profitability Analysis"],
                    "default_filters": {},
                    "decision_style": "Analytical",
                    "communication_style": "Concise",
                    "preferred_timeframes": ["current_quarter"],
                }
            }
        if agent_name == "A9_Deep_Analysis_Agent" and method_name == "plan_deep_analysis":
            request = params["request"]
            return {
                "plan": {
                    "kpi_name": request.kpi_name,
                    "dimensions": ["Customer"],
                    "steps": [],
                    "notes": "stub",
                },
                "request_id": request.request_id,
            }
        if agent_name == "A9_Deep_Analysis_Agent" and method_name == "execute_deep_analysis":
            return {
                "summary": "Analysis complete",
                "change_points": [],
            }
        if agent_name == "A9_Solution_Finder_Agent" and method_name == "recommend_actions":
            return {
                "recommendations": [
                    {
                        "solution_id": "stub-solution",
                        "title": "Improve margin",
                        "confidence": 0.9,
                    }
                ]
            }
        raise NotImplementedError(f"Unhandled agent call {agent_name}.{method_name}")

    async def detect_situations_batch(self, request):
        return {
            "situations": [
                {
                    "situation_id": "stub-situation",
                    "kpi_id": "Gross Margin",
                    "status": "warning",
                }
            ]
        }

    async def orchestrate_data_product_onboarding(self, request):
        response = DataProductOnboardingWorkflowResponse.success(
            request_id=request.request_id,
            data_product_id=request.data_product_id,
            steps=[
                WorkflowStepSummary(
                    name="inspect_source_schema",
                    status="success",
                    details={},
                ),
                WorkflowStepSummary(
                    name="generate_contract_yaml",
                    status="success",
                    details={"contract_path": "src/registry/data_product/new_contract.yaml"},
                ),
            ],
            contract_paths=["src/registry/data_product/new_contract.yaml"],
            governance_status="success",
            principal_owner={"owner_principal_id": "finance_manager"},
            qa_report={"overall_status": "pass"},
            activation_context={"status": "completed"},
        )
        return response


class _StubRuntime:
    def __init__(self):
        self._orchestrator = _StubOrchestrator()

    async def initialize(self):
        return True

    def get_orchestrator(self):
        return self._orchestrator


@pytest.fixture(autouse=True)
def override_runtime_dependency():
    stub_runtime = _StubRuntime()

    async def _override():
        return stub_runtime

    app.dependency_overrides[get_agent_runtime] = _override
    yield
    app.dependency_overrides.pop(get_agent_runtime, None)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac


async def _wait_for_finished(client: AsyncClient, request_id: str, kind: str, timeout: float = 5.0):
    route = f"/api/v1/workflows/{kind}/{request_id}/status"
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        response = await client.get(route)
        response.raise_for_status()
        payload = json.loads(response.content)
        data = payload["data"]
        if data["state"] in {"completed", "failed"}:
            return data
        await asyncio.sleep(0.1)
    raise TimeoutError(f"Workflow {request_id} did not finish")


@pytest.mark.anyio
async def test_run_situations_workflow(client: AsyncClient):
    payload = {
        "principal_id": "cfo_001",
        "business_processes": ["Finance: Profitability Analysis"],
    }
    response = await client.post("/api/v1/workflows/situations/run", json=payload)
    assert response.status_code == 202
    data = json.loads(response.content)["data"]
    request_id = data["request_id"]
    status_payload = await _wait_for_finished(client, request_id, "situations")
    assert status_payload["state"] == "completed"
    assert "situations" in status_payload["result"]


@pytest.mark.anyio
async def test_run_deep_analysis_workflow(client: AsyncClient):
    payload = {
        "principal_id": "cfo_001",
        "scope": {"kpi_id": "Gross Margin"},
    }
    response = await client.post("/api/v1/workflows/deep-analysis/run", json=payload)
    assert response.status_code == 202
    request_id = json.loads(response.content)["data"]["request_id"]
    status_payload = await _wait_for_finished(client, request_id, "deep-analysis")
    assert status_payload["state"] == "completed"
    assert "plan" in status_payload["result"]


@pytest.mark.anyio
async def test_run_solution_workflow(client: AsyncClient):
    payload = {
        "principal_id": "cfo_001",
        "problem_statement": "Improve margin",
    }
    response = await client.post("/api/v1/workflows/solutions/run", json=payload)
    assert response.status_code == 202
    request_id = json.loads(response.content)["data"]["request_id"]
    status_payload = await _wait_for_finished(client, request_id, "solutions")
    assert status_payload["state"] == "completed"
    assert "solutions" in status_payload["result"]


@pytest.mark.anyio
async def test_run_data_product_onboarding_workflow(client: AsyncClient):
    payload = {
        "principal_id": "data_foundation_lead",
        "data_product_id": "dp_test_001",
        "source_system": "duckdb",
        "schema": "main",
        "tables": ["financial_transactions"],
        "qa_enabled": True,
        "kpi_entries": [
            {
                "kpi_id": "gross_margin",
                "name": "Gross Margin",
            }
        ],
        "business_process_mappings": [
            {
                "process_id": "finance_profitability_analysis",
                "kpi_ids": ["gross_margin"],
            }
        ],
    }

    response = await client.post(
        "/api/v1/workflows/data-product-onboarding/run",
        json=payload,
    )
    assert response.status_code == 202
    request_id = json.loads(response.content)["data"]["request_id"]

    status_payload = await _wait_for_finished(
        client,
        request_id,
        "data-product-onboarding",
    )
    assert status_payload["state"] == "completed"
    result = status_payload["result"]
    assert result["status"] == "success"
    assert result["data_product_id"] == "dp_test_001"
