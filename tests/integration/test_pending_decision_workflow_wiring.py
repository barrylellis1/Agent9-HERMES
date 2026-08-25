"""Integration test: the FastAPI workflow routes actually wire into
PendingDecisionsStore (2026-08-25, Decision Framer/Decision Maker split,
Stages 4-5).

Complements test_pending_decisions_roundtrip.py (which proves the store
class itself works) by proving workflows.py's NEW code -- the write on SF
completion and the resolve on approve/request-changes/iterate -- actually
fires through the real route handlers, not just in isolation. Stubs the
orchestrator (same pattern as test_workflow_api.py) so this costs zero LLM
spend; the only thing under test is the NEW persistence wiring, not SF's
own synthesis logic (already covered elsewhere).

Requires local Supabase (see test_pending_decisions_roundtrip.py's guard);
skips cleanly rather than risk writing test rows into production.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

import pytest
from httpx import AsyncClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.api.main import app  # noqa: E402
from src.api.runtime import get_agent_runtime  # noqa: E402

pytestmark = [
    pytest.mark.anyio("asyncio"),
    pytest.mark.skipif(
        os.environ.get("SUPABASE_URL", "").rstrip("/") != "http://127.0.0.1:54321",
        reason="Requires SUPABASE_URL=http://127.0.0.1:54321 (local Docker Supabase) -- "
        "never runs this against production.",
    ),
]

_TEST_PRINCIPAL = "test_principal_pending_wiring"
_TEST_CLIENT = "lubricants"


class _HitlStubOrchestrator:
    """Returns an SF response with human_action_required=True, as a real
    completed run would when a recommendation needs sign-off."""

    async def orchestrate_solution_finding(self, request):
        from src.agents.models.solution_finder_models import SolutionFinderResponse, SolutionOption

        option = SolutionOption(id="opt_1", title="Renegotiate base oil supply contracts")
        return SolutionFinderResponse(
            status="success",
            request_id=getattr(request, "request_id", "stub"),
            options_ranked=[option],
            recommendation=option,
            human_action_required=True,
            human_action_type="approval",
            human_action_context={"stub": True},
        )


class _HitlStubRuntime:
    def __init__(self):
        self._orchestrator = _HitlStubOrchestrator()

    async def initialize(self):
        return True

    def get_orchestrator(self):
        return self._orchestrator


@pytest.fixture(autouse=True)
def override_runtime_dependency():
    stub_runtime = _HitlStubRuntime()

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
    # Best-effort cleanup of any row this test created.
    import httpx

    url = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    async with httpx.AsyncClient() as cleanup_client:
        await cleanup_client.delete(
            f"{url}/rest/v1/sf_pending_decisions",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            params={"principal_id": f"eq.{_TEST_PRINCIPAL}"},
        )


async def _wait_for_finished(client: AsyncClient, request_id: str, timeout: float = 5.0):
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        response = await client.get(f"/api/v1/workflows/solutions/{request_id}/status")
        response.raise_for_status()
        data = json.loads(response.content)["data"]
        if data["state"] in {"completed", "failed"}:
            return data
        await asyncio.sleep(0.1)
    raise TimeoutError(f"Workflow {request_id} did not finish")


@pytest.mark.anyio
async def test_sf_completion_persists_and_approve_resolves(client: AsyncClient):
    payload = {
        "principal_id": _TEST_PRINCIPAL,
        "client_id": _TEST_CLIENT,
        "situation_id": "sit_wiring_test",
        "problem_statement": "Improve margin",
    }
    response = await client.post("/api/v1/workflows/solutions/run", json=payload)
    assert response.status_code == 202
    request_id = json.loads(response.content)["data"]["request_id"]

    status_payload = await _wait_for_finished(client, request_id)
    assert status_payload["state"] == "completed"

    # The write path (Stage 4): completion with human_action_required=True
    # must have persisted a row, visible via the new endpoint (Stage 5).
    pending_response = await client.get(
        "/api/v1/workflows/solutions/pending",
        params={"principal_id": _TEST_PRINCIPAL, "client_id": _TEST_CLIENT},
    )
    assert pending_response.status_code == 200
    pending_rows = json.loads(pending_response.content)["data"]
    matching = [r for r in pending_rows if r["request_id"] == request_id]
    assert len(matching) == 1, "SF completion with human_action_required=True must persist a pending row"
    assert matching[0]["summary"] == "Renegotiate base oil supply contracts"

    # The resolve path (Stage 5): approving must remove it from the queue.
    approve_response = await client.post(
        f"/api/v1/workflows/solutions/{request_id}/actions/approve",
        json={"action": "approve", "comment": "approved in test"},
    )
    assert approve_response.status_code == 200

    pending_after = await client.get(
        "/api/v1/workflows/solutions/pending",
        params={"principal_id": _TEST_PRINCIPAL, "client_id": _TEST_CLIENT},
    )
    rows_after = json.loads(pending_after.content)["data"]
    matching_after = [r for r in rows_after if r["request_id"] == request_id]
    assert len(matching_after) == 0, "approved decision must no longer appear in the pending queue"
