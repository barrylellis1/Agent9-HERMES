"""Unit tests for PendingDecisionsStore's env-gating and safe-degradation
behavior (2026-08-25, Decision Framer/Decision Maker split, Stage 3).

Deliberately does NOT mock httpx round-trips against a fake Supabase --
this codebase's own convention (see feedback_unit_test_mocking_debt) treats
heavy mocking of store classes as tech debt, and no sibling store
(SituationsStore, VASolutionsStore) has such a test either. The real
round-trip is verified live in Stage 4/5 against a running local Supabase
via a real SA->DA->SF pipeline run. What IS unit-testable and load-bearing
on its own: the store must never raise and must degrade safely when
Supabase env vars are absent -- local dev without Supabase configured must
keep working, and a persistence failure must never propagate up into the
SF workflow response that triggered it.
"""
import pytest

from src.database.pending_decisions_store import PendingDecisionsStore


@pytest.fixture
def disabled_store(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    return PendingDecisionsStore()


class TestPendingDecisionsStoreDisabledGracefully:
    def test_disabled_when_env_vars_absent(self, disabled_store):
        assert disabled_store.enabled is False

    @pytest.mark.asyncio
    async def test_create_pending_returns_false_not_raises(self, disabled_store):
        result = await disabled_store.create_pending(
            request_id="req_1", client_id="lubricants", principal_id="cfo_001",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_resolve_returns_false_not_raises(self, disabled_store):
        result = await disabled_store.resolve("req_1", "approve")
        assert result is False

    @pytest.mark.asyncio
    async def test_list_unresolved_returns_empty_list_not_raises(self, disabled_store):
        result = await disabled_store.list_unresolved("cfo_001", "lubricants")
        assert result == []


class TestPendingDecisionsStoreEnabled:
    def test_enabled_when_env_vars_present(self, monkeypatch):
        monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
        monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-key")
        store = PendingDecisionsStore()
        assert store.enabled is True
        assert store.endpoint.endswith("/rest/v1/sf_pending_decisions")
