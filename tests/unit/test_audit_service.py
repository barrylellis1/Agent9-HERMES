"""AuditService write path (docs/architecture/audit_event_system_design.md).

No live DB here, same convention as test_assumption_pre_registration.py: model
validation and the no-pool-available path are unit-testable; the actual INSERT
against local Supabase is verified against the live pool, not here. The
mocked-pool test below proves the SQL/parameter wiring is self-consistent
without asserting anything about a real database.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from src.registry.models.audit_event import AuditEvent
from src.services.audit_service import AuditService, _MAX_QUERY_LIMIT


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


# ---------------------------------------------------------------------------
# query() -- the read path behind GET /api/v1/admin/audit-events
# ---------------------------------------------------------------------------

def _fake_row(**overrides) -> dict:
    row = {
        "id": "11111111-1111-1111-1111-111111111111",
        "client_id": "lubricants",
        "event_type": "reliability.rollup_check",
        "severity": "warning",
        "outcome": "fail",
        "source_agent": "A9_Deep_Analysis_Agent",
        "request_id": None,
        "resource_type": "kpi",
        "resource_id": "gross_margin_pct",
        "payload": json.dumps({"dimension": "customer_name"}),
        "created_at": datetime(2026, 10, 2, 12, 0, 0, tzinfo=timezone.utc),
    }
    row.update(overrides)
    return row


@pytest.mark.asyncio
async def test_query_returns_empty_list_without_raising_when_pool_unavailable(monkeypatch):
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: None))
    events = await AuditService.query(client_id="lubricants")
    assert events == []


@pytest.mark.asyncio
async def test_query_with_no_filters_returns_most_recent_across_all_clients(monkeypatch):
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[_fake_row()])
    pool = _FakePool(conn)
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: pool))

    events = await AuditService.query()

    assert len(events) == 1
    assert events[0].client_id == "lubricants"
    assert events[0].outcome == "fail"
    assert events[0].payload == {"dimension": "customer_name"}
    sql, params = conn.fetch.call_args[0][0], conn.fetch.call_args[0][1:]
    assert "WHERE" not in sql  # no filters supplied -> no WHERE clause at all
    assert params == (100,)  # just the default limit


@pytest.mark.asyncio
async def test_query_filters_are_anded_and_parameterized(monkeypatch):
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    pool = _FakePool(conn)
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: pool))

    await AuditService.query(client_id="lubricants", event_type="reliability.rollup_check", outcome="fail")

    sql, params = conn.fetch.call_args[0][0], conn.fetch.call_args[0][1:]
    assert "client_id = $1" in sql
    assert "event_type = $2" in sql
    assert "outcome = $3" in sql
    assert " AND " in sql
    assert params == ("lubricants", "reliability.rollup_check", "fail", 100)


@pytest.mark.asyncio
async def test_query_limit_is_clamped_to_the_ceiling(monkeypatch):
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    pool = _FakePool(conn)
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: pool))

    await AuditService.query(limit=999999)

    params = conn.fetch.call_args[0][1:]
    assert params[-1] == _MAX_QUERY_LIMIT  # never the raw 999999 asked for


@pytest.mark.asyncio
async def test_query_returns_empty_list_without_raising_when_read_fails(monkeypatch):
    conn = AsyncMock()
    conn.fetch = AsyncMock(side_effect=RuntimeError("connection reset"))
    pool = _FakePool(conn)
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: pool))

    events = await AuditService.query(client_id="lubricants")
    assert events == []


@pytest.mark.asyncio
async def test_query_skips_one_unparseable_row_without_dropping_the_rest(monkeypatch):
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[
        _fake_row(severity="not-a-valid-severity"),  # fails AuditEvent validation
        _fake_row(resource_id="net_revenue"),  # valid
    ])
    pool = _FakePool(conn)
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: pool))

    events = await AuditService.query()

    assert len(events) == 1
    assert events[0].resource_id == "net_revenue"


# ---------------------------------------------------------------------------
# pool_available() -- lets the admin endpoint distinguish "no pool" from
# "pool answered, nothing matched" (code-review finding, 2026-10-02)
# ---------------------------------------------------------------------------

def test_pool_available_false_when_no_pool(monkeypatch):
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: None))
    assert AuditService.pool_available() is False


def test_pool_available_true_when_pool_present(monkeypatch):
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: _FakePool(AsyncMock())))
    assert AuditService.pool_available() is True


# ---------------------------------------------------------------------------
# run_retention_sweep() -- manual trigger for the pass/abstain rollup-and-delete
# (migration 20261002010000_audit_events_retention_sweep.sql)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sweep_returns_none_without_raising_when_pool_unavailable(monkeypatch):
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: None))
    result = await AuditService.run_retention_sweep()
    assert result is None


@pytest.mark.asyncio
async def test_sweep_calls_the_sql_function_with_cutoff_and_returns_counts(monkeypatch):
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value={"rolled_up_groups": 3, "rows_deleted": 42})
    pool = _FakePool(conn)
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: pool))

    result = await AuditService.run_retention_sweep(cutoff_days=60)

    assert result == {"rolled_up_groups": 3, "rows_deleted": 42}
    conn.fetchrow.assert_awaited_once()
    sql, params = conn.fetchrow.call_args[0][0], conn.fetchrow.call_args[0][1:]
    assert "sweep_audit_events_retention" in sql
    assert params == (60,)


@pytest.mark.asyncio
async def test_sweep_defaults_to_90_days(monkeypatch):
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(return_value={"rolled_up_groups": 0, "rows_deleted": 0})
    pool = _FakePool(conn)
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: pool))

    await AuditService.run_retention_sweep()

    params = conn.fetchrow.call_args[0][1:]
    assert params == (90,)


@pytest.mark.asyncio
async def test_sweep_returns_none_without_raising_when_it_fails(monkeypatch):
    conn = AsyncMock()
    conn.fetchrow = AsyncMock(side_effect=RuntimeError("connection reset"))
    pool = _FakePool(conn)
    monkeypatch.setattr(AuditService, "_pool", staticmethod(lambda: pool))

    result = await AuditService.run_retention_sweep()
    assert result is None
