"""Integration test for the pending-decisions persistence round-trip
(2026-08-25, Decision Framer/Decision Maker split, Stages 3-5).

Exercises the REAL PendingDecisionsStore against a REAL local Supabase
instance -- not mocked -- proving the create/list/resolve round-trip that
workflows.py's new write path (SF completion) and resolve path (approve/
request-changes/iterate) both depend on. Deliberately does not run a full
SA->DA->SF LLM pipeline: the human_action_required flag itself is
pre-existing, already-tested logic (a9_solution_finder_agent.py); the only
NEW thing this stage adds is durably PERSISTING it, which is exactly what
this test proves, at a fraction of the cost of a real LLM run.

Requires local Supabase running (`supabase start` / restart_decision_studio_ui.ps1)
with the 20260825120000_sf_pending_decisions.sql migration applied. Skips
cleanly if SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY point elsewhere or are
unset, rather than risk writing test rows into production.
"""
import os
import uuid

import pytest
import pytest_asyncio

from src.database.pending_decisions_store import PendingDecisionsStore

# Local-only guard: this test writes and deletes real rows. Never run it
# against a URL that isn't the local Docker instance.
_LOCAL_SUPABASE_URL = "http://127.0.0.1:54321"


def _is_local_supabase() -> bool:
    return os.environ.get("SUPABASE_URL", "").rstrip("/") == _LOCAL_SUPABASE_URL


pytestmark = pytest.mark.skipif(
    not _is_local_supabase(),
    reason="Requires SUPABASE_URL=http://127.0.0.1:54321 (local Docker Supabase) -- "
    "never runs this against production.",
)


@pytest_asyncio.fixture
async def cleanup_request_id():
    request_id = f"test_pending_{uuid.uuid4().hex[:12]}"
    yield request_id
    # Best-effort cleanup regardless of test outcome.
    import httpx

    url = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    async with httpx.AsyncClient() as client:
        await client.delete(
            f"{url}/rest/v1/sf_pending_decisions",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            params={"request_id": f"eq.{request_id}"},
        )


class TestPendingDecisionsRoundtrip:
    @pytest.mark.asyncio
    async def test_create_then_list_then_resolve(self, cleanup_request_id):
        request_id = cleanup_request_id
        store = PendingDecisionsStore()
        assert store.enabled, "PendingDecisionsStore must be enabled against local Supabase"

        created = await store.create_pending(
            request_id=request_id,
            client_id="lubricants",
            principal_id="test_principal_pending",
            situation_id="sit_test_001",
            human_action_type="approval",
            summary="Test recommended option title",
            human_action_context={"note": "integration test row"},
        )
        assert created is True

        pending = await store.list_unresolved("test_principal_pending", "lubricants")
        matching = [r for r in pending if r["request_id"] == request_id]
        assert len(matching) == 1
        assert matching[0]["resolved"] is False
        assert matching[0]["summary"] == "Test recommended option title"

        resolved = await store.resolve(request_id, "approve")
        assert resolved is True

        pending_after = await store.list_unresolved("test_principal_pending", "lubricants")
        matching_after = [r for r in pending_after if r["request_id"] == request_id]
        assert len(matching_after) == 0, "resolved row must not appear in list_unresolved"

    @pytest.mark.asyncio
    async def test_create_is_idempotent_on_request_id(self, cleanup_request_id):
        request_id = cleanup_request_id
        store = PendingDecisionsStore()

        first = await store.create_pending(
            request_id=request_id, client_id="lubricants", principal_id="test_principal_pending",
            summary="First summary",
        )
        second = await store.create_pending(
            request_id=request_id, client_id="lubricants", principal_id="test_principal_pending",
            summary="Second summary (should replace, not duplicate)",
        )
        assert first is True
        assert second is True

        pending = await store.list_unresolved("test_principal_pending", "lubricants")
        matching = [r for r in pending if r["request_id"] == request_id]
        assert len(matching) == 1, "upsert on request_id must not create a duplicate row"
        assert matching[0]["summary"] == "Second summary (should replace, not duplicate)"
