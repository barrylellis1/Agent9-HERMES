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

import logging
from typing import Any, Dict, Literal, Optional

import asyncpg

from src.registry.models.audit_event import AuditEvent

logger = logging.getLogger(__name__)


class AuditService:
    """Static write path -- no instance state, mirrors AssumptionProvider's shape."""

    @staticmethod
    def _pool() -> Optional[asyncpg.Pool]:
        from src.registry.bootstrap import RegistryBootstrap

        return getattr(RegistryBootstrap._db_manager, "pool", None)

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
            import json
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
