"""Write path for the audit_events table (design note:
docs/architecture/audit_event_system_design.md).

Formalizes what was previously ad-hoc per-agent logging (SF's in-memory
`audit_log` list, DA's `[ROLLUP-CHECK]` log line) into one typed, persisted
sink shared by three event families -- see `AuditEvent`'s own docstring for
what distinguishes them.

NON-BLOCKING BY DESIGN. `log()` never raises. A failure to persist an audit
event must never take down the analysis that produced it -- the same
"logged, not raised" discipline DA's ROLLUP-CHECK already uses for the
decomposition cross-check itself. Callers `await` it (it is one INSERT, not
truly fire-and-forget via a background task -- that trades a small amount of
latency for not having to reason about dangling tasks at event-loop
shutdown) but can never be broken by it.

Uses the shared asyncpg pool from RegistryBootstrap -- same lazy pool
pattern as AssumptionProvider (`src/registry/providers/assumption_provider.py`).
Writes go through the pool's normal role, not `tenant_scope()`: the caller
always supplies a trusted `client_id` at write time (this is an internal
agent writing about its own run, not a tenant-supplied query), so there is
no RLS-bypass concern to guard against on INSERT -- RLS on this table (per
its migration) governs SELECT only, same as every other client_id table in
this codebase.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

import asyncpg

from src.registry.models.audit_event import AuditEvent

logger = logging.getLogger(__name__)

_MAX_QUERY_LIMIT = 500  # hard ceiling regardless of what a caller asks for


class AuditService:
    """Static write path -- no instance state, mirrors AssumptionProvider's shape."""

    @staticmethod
    def _pool() -> Optional[asyncpg.Pool]:
        from src.registry.bootstrap import RegistryBootstrap

        return getattr(RegistryBootstrap._db_manager, "pool", None)

    @staticmethod
    def pool_available() -> bool:
        """Is there a database pool to read or write through at all?

        Code-review finding (2026-10-02): `query()` returning `[]` when the
        pool is unavailable is indistinguishable, at the admin endpoint, from
        "every reliability check passed" -- a monitoring blind spot in the
        monitoring system itself. `_pool()` is `None` not only for an
        unusual backend (a DuckDB-backed `_db_manager`, which has no `.pool`
        attribute at all) but, more routinely, whenever `RegistryBootstrap`
        has not finished initializing yet, or a pool that failed to connect.
        `GET /api/v1/admin/audit-events` uses this to report `status:
        "degraded"` rather than `"ok"` on an empty result caused by no pool,
        so an empty page reads as "this signal never ran here" rather than
        "clean bill of health".
        """
        return AuditService._pool() is not None

    @staticmethod
    async def log(
        client_id: str,
        event_type: str,
        severity: Literal["info", "warning", "error"],
        source_agent: str,
        outcome: Optional[Literal["pass", "fail", "abstain"]] = None,
        request_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Persist one audit event. Returns True on success, False otherwise --
        never raises, so a call site never needs a try/except around this.

        `outcome=None` for event types that are not checks (no verdict to
        render). Where it IS populated, `abstain` must never be written as a
        stand-in for `pass` -- that is precisely the not-checked-is-not-pass
        failure mode `src/analysis` exists to prevent, now extended to this
        table's own aggregation.
        """
        pool = AuditService._pool()
        if pool is None:
            logger.warning(
                "AuditService.log: no database pool available (event_type=%s, client=%s) -- "
                "event dropped, not queued for retry",
                event_type, client_id,
            )
            return False
        try:
            event = AuditEvent(
                client_id=client_id,
                event_type=event_type,
                severity=severity,
                outcome=outcome,
                source_agent=source_agent,
                request_id=request_id,
                resource_type=resource_type,
                resource_id=resource_id,
                payload=payload or {},
            )
        except Exception as e:
            logger.warning("AuditService.log: invalid event dropped (event_type=%s): %s", event_type, e)
            return False

        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_events
                        (client_id, event_type, severity, outcome, source_agent,
                         request_id, resource_type, resource_id, payload)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)
                    """,
                    event.client_id, event.event_type, event.severity, event.outcome,
                    event.source_agent, event.request_id, event.resource_type,
                    event.resource_id, json.dumps(event.payload),
                )
            return True
        except Exception as e:
            # Never propagate -- an audit-logging failure must not surface as an
            # analysis failure. Logged at warning so it is visible without being
            # mistaken for the thing it was trying to record.
            logger.warning(
                "AuditService.log: write failed, event dropped (event_type=%s, client=%s): %s",
                event_type, client_id, e,
            )
            return False

    @staticmethod
    async def query(
        client_id: Optional[str] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        outcome: Optional[str] = None,
        request_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Read back audit events for the admin diagnostics endpoint
        (`GET /api/v1/admin/audit-events`, design note section 4 "Read path").

        Every filter is optional and ANDed together; omitting all of them
        returns the most recent events across every client -- appropriate
        for an endpoint already gated by `X-Admin-Key`, not for a tenant-
        facing surface (there is no `tenant_scope()` here deliberately: an
        admin diagnostics read spans clients by design).

        `limit` is clamped to `_MAX_QUERY_LIMIT` regardless of what is asked
        for, so a careless caller cannot pull the whole table. Returns an
        empty list on no pool or a query failure -- never raises, same
        discipline as `log()` -- a broken diagnostics read must not take the
        diagnostics endpoint down with a 500; it reports what it found
        (nothing) and the caller sees the gap in the response, not a crash.
        """
        pool = AuditService._pool()
        if pool is None:
            logger.warning("AuditService.query: no database pool available -- returning empty result")
            return []

        conditions: List[str] = []
        params: List[Any] = []

        def _add(column: str, value: Any) -> None:
            if value is None:
                return
            params.append(value)
            conditions.append(f"{column} = ${len(params)}")

        _add("client_id", client_id)
        _add("event_type", event_type)
        _add("severity", severity)
        _add("outcome", outcome)
        _add("request_id", request_id)
        if since is not None:
            params.append(since)
            conditions.append(f"created_at >= ${len(params)}")
        if until is not None:
            params.append(until)
            conditions.append(f"created_at <= ${len(params)}")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        safe_limit = max(1, min(int(limit), _MAX_QUERY_LIMIT))
        params.append(safe_limit)

        sql = f"""
            SELECT id, client_id, event_type, severity, outcome, source_agent,
                   request_id, resource_type, resource_id, payload, created_at
            FROM audit_events
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${len(params)}
        """

        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(sql, *params)
        except Exception as e:
            logger.warning("AuditService.query: read failed, returning empty result: %s", e)
            return []

        events: List[AuditEvent] = []
        for row in rows:
            try:
                payload = row["payload"]
                if isinstance(payload, str):
                    payload = json.loads(payload)
                events.append(AuditEvent(
                    id=str(row["id"]),
                    client_id=row["client_id"],
                    event_type=row["event_type"],
                    severity=row["severity"],
                    outcome=row["outcome"],
                    source_agent=row["source_agent"],
                    request_id=row["request_id"],
                    resource_type=row["resource_type"],
                    resource_id=row["resource_id"],
                    payload=payload or {},
                    created_at=row["created_at"].isoformat() if row["created_at"] else None,
                ))
            except Exception as e:
                # One malformed row must not drop the rest of the page.
                logger.warning("AuditService.query: skipping unparseable row: %s", e)
        return events

    @staticmethod
    async def run_retention_sweep(cutoff_days: int = 90) -> Optional[Dict[str, int]]:
        """Run the retention sweep (migration `20261002010000_audit_events_retention_sweep.sql`):
        roll up and delete `pass`/`abstain` rows older than `cutoff_days`, leaving
        `fail` and `NULL`-outcome rows untouched.

        Manually triggered today via `POST /api/v1/admin/audit-events/sweep` --
        there is no automatic schedule yet. No `pg_cron` extension is enabled
        on this Supabase project and no other scheduled-job mechanism exists
        anywhere in this codebase; wiring this to run unattended (`pg_cron`, a
        Railway cron job, or an external scheduler hitting the admin endpoint)
        is a deliberate infrastructure decision this method does not make.

        Returns `{"rolled_up_groups": N, "rows_deleted": M}`, or `None` on no
        pool or a failure -- never raises, same discipline as `log()`/`query()`.
        Safe to call repeatedly: the underlying SQL function's upsert
        accumulates rather than overwrites, so a retried or overlapping call
        cannot lose or double-count a day already partly swept.
        """
        pool = AuditService._pool()
        if pool is None:
            logger.warning("AuditService.run_retention_sweep: no database pool available -- sweep skipped")
            return None
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM sweep_audit_events_retention($1)", cutoff_days,
                )
            if row is None:
                return None
            result = {"rolled_up_groups": row["rolled_up_groups"], "rows_deleted": row["rows_deleted"]}
            logger.info("AuditService.run_retention_sweep: %s", result)
            return result
        except Exception as e:
            logger.warning("AuditService.run_retention_sweep: sweep failed: %s", e)
            return None
