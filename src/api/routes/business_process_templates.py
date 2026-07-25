"""API routes for Phase 12F — Business Process Template Generator.

Two endpoints:
  - POST /api/v1/templates/research-business-processes → MA agent selects the
    relevant subset of the canonical business-process taxonomy for a client,
    plus proposes a few industry-specific extras.
  - POST /api/v1/templates/commit-business-processes    → writes accepted
    processes directly to the business_processes registry. Unlike KPIs there
    is no template/active lifecycle — a committed business process is
    immediately valid.

Ownership: unlike kpi_templates.py's /commit (which trusts the request
body's client_id outright), these endpoints resolve the authoritative
client_id server-side via _resolve_create_client_id (an authenticated user's
own client_id, or a client_id query param validated against
business_contexts) — never the request body. This matches the stricter
tenant-isolation pattern the rest of registry.py already enforces.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.agents.models.business_process_template_models import (
    AcceptedTemplateBusinessProcess,
    BusinessProcessResearchRequest,
    BusinessProcessResearchResponse,
    CommitBusinessProcessTemplatesRequest,
    CommitBusinessProcessTemplatesResponse,
    CommittedBusinessProcessSummary,
)
from src.agents.new.a9_market_analysis_agent import A9_Market_Analysis_Agent
from src.api.auth_middleware import AuthUser, get_optional_user
from src.api.routes.registry import _resolve_create_client_id
from src.registry.factory import RegistryFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/templates", tags=["business-process-templates"])


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

async def _get_pool() -> asyncpg.Pool:
    from src.api.runtime import agent_runtime
    from src.registry.bootstrap import RegistryBootstrap

    await agent_runtime.initialize()

    db_manager = RegistryBootstrap._db_manager
    if db_manager is None or getattr(db_manager, "pool", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available — registry not initialized.",
        )
    return db_manager.pool


async def _get_ma_agent() -> A9_Market_Analysis_Agent:
    """Resolve the MA agent from the orchestrator registry."""
    from src.api.runtime import agent_runtime
    from src.agents.new.a9_orchestrator_agent import AgentRegistry

    await agent_runtime.initialize()

    try:
        agent = await AgentRegistry.get_agent("A9_Market_Analysis_Agent")
    except Exception as exc:
        logger.error("MA agent not available: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Market Analysis agent is not available — please retry.",
        )
    return agent


async def _get_registry_factory() -> RegistryFactory:
    factory = RegistryFactory()
    if not factory.is_initialized:
        await factory.initialize()
    return factory


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/research-business-processes",
    response_model=BusinessProcessResearchResponse,
    status_code=status.HTTP_200_OK,
)
async def research_business_processes(
    request: BusinessProcessResearchRequest,
    client_id: Optional[str] = Query(
        None, description="Required when not authenticated; ignored (auth wins) otherwise"
    ),
    user: Optional[AuthUser] = Depends(get_optional_user),
    ma_agent: A9_Market_Analysis_Agent = Depends(_get_ma_agent),
    factory: RegistryFactory = Depends(_get_registry_factory),
) -> BusinessProcessResearchResponse:
    """Select relevant canonical business processes + extras for a client.

    The request body's own client_id is ignored — the caller's tenant is
    always resolved server-side (authenticated user, or a validated
    client_id query param) so a body value can never claim a different
    tenant's onboarding session.
    """
    resolved_client_id = await _resolve_create_client_id(client_id, user, factory)
    resolved_request = request.model_copy(update={"client_id": resolved_client_id})

    try:
        profile = await ma_agent.research_company_business_processes(resolved_request)
    except Exception as exc:
        logger.error(
            "MA research_company_business_processes failed for client=%s: %s",
            resolved_client_id,
            exc,
        )
        return BusinessProcessResearchResponse(
            status="error",
            profile=None,
            error=f"Research failed: {exc}",
        )

    response_status: str = "degraded" if profile.degraded else "success"
    logger.info(
        "BP research complete — client=%s status=%s selected=%d",
        resolved_client_id,
        response_status,
        len(profile.selected),
    )
    return BusinessProcessResearchResponse(
        status=response_status,  # type: ignore[arg-type]
        profile=profile,
    )


# ---------------------------------------------------------------------------
# Commit helpers
# ---------------------------------------------------------------------------

_BP_ID_RE = re.compile(r"[^a-z0-9_]+")


def _slugify_bp_id(domain: str, name: str) -> str:
    """Generate a natural {domain}_{name} snake_case ID, matching the
    canonical taxonomy's own convention (e.g. finance_expense_management)."""
    base = f"{domain}_{name}".lower().strip()
    base = _BP_ID_RE.sub("_", base)
    base = re.sub(r"_+", "_", base).strip("_")
    return base or "business_process"


async def _insert_template_bp(
    conn: asyncpg.Connection,
    client_id: str,
    bp: AcceptedTemplateBusinessProcess,
    created_by: str,
    live_provider: Optional[Any] = None,
) -> CommittedBusinessProcessSummary:
    """Write one accepted business process to public.business_processes.

    Returns a per-row summary indicating written / skipped_duplicate / error.
    No status/lifecycle field is set — unlike KPIs, a committed business
    process is immediately valid, there's no "pending data connection" concept.

    `live_provider`, when supplied, is the actual registered
    business_process provider instance (a DatabaseRegistryProvider — an
    in-memory cache populated once at bootstrap, not a live query). This raw
    SQL insert bypasses that cache entirely, so a newly-written row would
    otherwise be invisible to every registry.py list endpoint (and anything
    reading them, like Context Explorer or the accountability interview)
    until the process restarts. On a genuinely NEW row we mirror it into the
    cache directly via `_cache_item`. Deliberately skipped on
    skipped_duplicate — the existing DB row may have been hand-edited since
    creation, and blindly overwriting the cache with this commit's payload
    could put the cache out of sync with the DB in the other direction.
    """
    bp_id = bp.id or _slugify_bp_id(bp.domain, bp.name)
    display_name = f"{bp.domain}: {bp.name}"
    now = datetime.now(timezone.utc)

    # BusinessProcess.metadata is typed Dict[str, str] — same constraint as
    # KPI.metadata; every value must be stringified before storage or it
    # fails Pydantic validation on read and silently vanishes from caches.
    metadata: dict[str, str] = {
        "source": bp.source,
        "confidence": str(bp.confidence),
        "created_by": created_by,
    }

    try:
        result = await conn.execute(
            """
            INSERT INTO business_processes (
                id, client_id, name, domain, description, display_name,
                owner_role, stakeholder_roles, tags, metadata, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $11)
            ON CONFLICT (client_id, id) DO NOTHING
            """,
            bp_id,
            client_id,
            bp.name,
            bp.domain,
            bp.description,
            display_name,
            bp.owner_role,
            bp.stakeholder_roles,
            bp.tags,
            metadata,
            now,
        )
    except Exception as exc:
        logger.error(
            "Insert failed for template business process '%s' (client=%s): %s",
            bp_id,
            client_id,
            exc,
        )
        return CommittedBusinessProcessSummary(
            id=bp_id, name=bp.name, status="error", error=str(exc)
        )

    # asyncpg returns "INSERT 0 N" — N is the actual row count
    inserted = result.endswith(" 1")
    if not inserted:
        return CommittedBusinessProcessSummary(id=bp_id, name=bp.name, status="skipped_duplicate")

    if live_provider is not None:
        try:
            from src.registry.models.business_process import BusinessProcess

            live_provider._cache_item(
                BusinessProcess(
                    id=bp_id,
                    client_id=client_id,
                    name=bp.name,
                    domain=bp.domain,
                    description=bp.description,
                    tags=bp.tags,
                    owner_role=bp.owner_role,
                    stakeholder_roles=bp.stakeholder_roles,
                    display_name=display_name,
                    metadata=metadata,
                )
            )
        except Exception as exc:
            # Cache mirroring is best-effort — the DB write already succeeded;
            # a cache-sync failure here must not fail the whole commit.
            logger.warning("Failed to mirror '%s' into the live provider cache: %s", bp_id, exc)

    return CommittedBusinessProcessSummary(id=bp_id, name=bp.name, status="written")


@router.post(
    "/commit-business-processes",
    response_model=CommitBusinessProcessTemplatesResponse,
    status_code=status.HTTP_200_OK,
)
async def commit_business_processes(
    request: CommitBusinessProcessTemplatesRequest,
    client_id: Optional[str] = Query(
        None, description="Required when not authenticated; ignored (auth wins) otherwise"
    ),
    user: Optional[AuthUser] = Depends(get_optional_user),
    pool: asyncpg.Pool = Depends(_get_pool),
    factory: RegistryFactory = Depends(_get_registry_factory),
) -> CommitBusinessProcessTemplatesResponse:
    """Write accepted business processes to the registry.

    Idempotent: existing rows with the same (client_id, id) are reported as
    skipped_duplicate rather than overwritten. Failures on individual rows
    do not abort the batch — every row is attempted and reported per-row.
    """
    if not request.accepted_processes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one business process must be accepted before commit.",
        )

    resolved_client_id = await _resolve_create_client_id(client_id, user, factory)
    live_provider = factory.get_business_process_provider()

    results: list[CommittedBusinessProcessSummary] = []
    async with pool.acquire() as conn:
        for bp in request.accepted_processes:
            summary = await _insert_template_bp(
                conn, resolved_client_id, bp, request.created_by, live_provider
            )
            results.append(summary)

    rows_written = sum(1 for r in results if r.status == "written")
    rows_skipped = sum(1 for r in results if r.status == "skipped_duplicate")
    rows_failed = sum(1 for r in results if r.status == "error")

    logger.info(
        "Commit business process templates: client=%s written=%d skipped=%d failed=%d",
        resolved_client_id,
        rows_written,
        rows_skipped,
        rows_failed,
    )

    return CommitBusinessProcessTemplatesResponse(
        rows_written=rows_written,
        rows_skipped=rows_skipped,
        rows_failed=rows_failed,
        results=results,
    )
