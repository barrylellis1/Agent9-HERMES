"""AuditService write path (docs/architecture/audit_event_system_design.md).

No live DB here, same convention as test_assumption_pre_registration.py: model
validation and the no-pool-available path are unit-testable; the actual INSERT
against local Supabase is verified against the live pool, not here. The
mocked-pool test below proves the SQL/parameter wiring is self-consistent
without asserting anything about a real database.
"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from src.registry.models.audit_event import AuditEvent
from src.services.audit_service import AuditService


class _FakeAcquireCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *exc):
        return False


class _FakePool:
    """Minimal asyncpg.Pool stand-in: .acquire() is an async context manager."""

    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _FakeAcquireCtx(self._conn)


def test_audit_event_rejects_invalid_outcome():
    with pytest.raises(ValidationError):
        AuditEvent(
            client_id="lubricants",
            event_type="reliability.rollup_check",
            severity="warning",
            outcome="partial",  # not a valid Literal
            source_agent="A9_Deep_Analysis_Agent",
        )


def test_audit_event_outcome_defaults_to_none_for_narrative_events():
    # SF's narrative/debug events have no verdict -- outcome stays None, never
    # defaulted to something that would read as a pass in an aggregate.
    event = AuditEvent(
        client_id="lubricants",
        event_type="llm_debate_completed",
        severity="info",
        source_agent="A9_Solution_Finder_Agent",
    )
    assert event.outcome is None


@pytest.mark.asyncio
async def test_log_returns_false_without_raising_when_pool_unavailable(monkeypatch):
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: None))
    ok = await AuditService.log(
        client_id="lubricants",
        event_type="reliability.rollup_check",
        severity="warning",
        source_agent="A9_Deep_Analysis_Agent",
        outcome="fail",
    )
    assert ok is False


@pytest.mark.asyncio
async def test_log_writes_expected_columns_when_pool_available(monkeypatch):
    conn = AsyncMock()
    pool = _FakePool(conn)
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: pool))

    ok = await AuditService.log(
        client_id="lubricants",
        event_type="reliability.rollup_check",
        severity="warning",
        outcome="fail",
        source_agent="A9_Deep_Analysis_Agent",
        resource_type="kpi",
        resource_id="gross_margin_pct",
        payload={"dimension": "customer_name", "contributions_sum": -53.0, "warehouse_delta": -5.0},
    )

    assert ok is True
    conn.execute.assert_awaited_once()
    args, _ = conn.execute.call_args
    sql = args[0]
    assert "INSERT INTO audit_events" in sql
    # positional params: client_id, event_type, severity, outcome, source_agent,
    # request_id, resource_type, resource_id, payload(json)
    params = args[1:]
    assert params[0] == "lubricants"
    assert params[1] == "reliability.rollup_check"
    assert params[2] == "warning"
    assert params[3] == "fail"
    assert params[4] == "A9_Deep_Analysis_Agent"
    assert params[6] == "kpi"
    assert params[7] == "gross_margin_pct"
    assert json.loads(params[8])["dimension"] == "customer_name"


@pytest.mark.asyncio
async def test_log_never_raises_when_write_fails(monkeypatch):
    conn = AsyncMock()
    conn.execute.side_effect = RuntimeError("connection reset")
    pool = _FakePool(conn)
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: pool))

    ok = await AuditService.log(
        client_id="lubricants",
        event_type="reliability.rollup_check",
        severity="warning",
        outcome="fail",
        source_agent="A9_Deep_Analysis_Agent",
    )
    assert ok is False
