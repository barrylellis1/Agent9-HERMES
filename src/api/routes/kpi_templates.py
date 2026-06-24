"""API routes for Phase 12A — Company Intelligence-Driven KPI Template Generator.

Two endpoints:
  - POST /api/v1/templates/research-company  → MA agent researches a company,
    returns a CompanyKPIProfile with benchmark-anchored template KPIs.
  - POST /api/v1/templates/commit            → writes accepted templates to the
    KPI registry with status='template' (SA agent skips these in detection).

All endpoints are strictly scoped by client_id. Template KPIs use
data_product_id='pending' as a sentinel until the admin connects data and
promotes the row to status='active' via a future onboarding step.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.agents.models.kpi_template_models import (
    AcceptedTemplateKPI,
    CommittedKPISummary,
    CommitTemplatesRequest,
    CommitTemplatesResponse,
    CompanyResearchRequest,
    CompanyResearchResponse,
)
from src.agents.new.a9_market_analysis_agent import A9_Market_Analysis_Agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/templates", tags=["kpi-templates"])


# ---------------------------------------------------------------------------
# DB dependency — reuses the shared pool from RegistryBootstrap
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


# ---------------------------------------------------------------------------
# MA agent dependency — resolved via orchestrator at request time
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/research-company",
    response_model=CompanyResearchResponse,
    status_code=status.HTTP_200_OK,
)
async def research_company(
    request: CompanyResearchRequest,
    ma_agent: A9_Market_Analysis_Agent = Depends(_get_ma_agent),
) -> CompanyResearchResponse:
    """Run the MA agent's Phase 12A research pipeline.

    Returns a CompanyKPIProfile with benchmark-anchored KPI templates the
    admin can review, edit, accept, or reject. When Perplexity is unavailable
    the agent falls back to LLM-only mode (status='degraded'); the profile is
    still usable but every benchmark_source is 'inferred'.
    """
    try:
        profile = await ma_agent.research_company_kpi_profile(request)
    except Exception as exc:
        logger.error(
            "MA research_company_kpi_profile failed for company=%s client=%s: %s",
            request.company_name,
            request.client_id,
            exc,
        )
        return CompanyResearchResponse(
            status="error",
            profile=None,
            error=f"Research failed: {exc}",
        )

    response_status: str = "degraded" if profile.degraded else "success"
    logger.info(
        "Research complete — company=%s client=%s status=%s kpis=%d",
        request.company_name,
        request.client_id,
        response_status,
        len(profile.template_kpis),
    )
    return CompanyResearchResponse(
        status=response_status,  # type: ignore[arg-type]
        profile=profile,
    )


# ---------------------------------------------------------------------------
# Commit helpers
# ---------------------------------------------------------------------------

_KPI_ID_RE = re.compile(r"[^a-z0-9_]+")
TEMPLATE_DATA_PRODUCT_SENTINEL = "pending"


def _slugify_kpi_id(name: str) -> str:
    """Generate a natural snake_case ID from a KPI name."""
    base = name.lower().strip()
    base = _KPI_ID_RE.sub("_", base)
    base = re.sub(r"_+", "_", base).strip("_")
    return base or "kpi"


async def _insert_template_kpi(
    conn: asyncpg.Connection,
    client_id: str,
    kpi: AcceptedTemplateKPI,
    created_by: str,
) -> CommittedKPISummary:
    """Write one accepted template KPI to public.kpis with status='template'.

    Returns a per-KPI summary indicating written / skipped_duplicate / error.
    """
    kpi_id = kpi.kpi_id or _slugify_kpi_id(kpi.name)
    bp_ids: list[str] = [kpi.business_process_id] if kpi.business_process_id else []
    now = datetime.now(timezone.utc)

    try:
        result = await conn.execute(
            """
            INSERT INTO kpis (
                id, client_id, name, domain, description, unit,
                data_product_id, business_process_ids,
                status, benchmark_range, benchmark_source,
                metadata, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'template', $9, $10, $11, $12, $12)
            ON CONFLICT (client_id, id) DO NOTHING
            """,
            kpi_id,
            client_id,
            kpi.name,
            kpi.domain or "General",
            kpi.definition,
            kpi.unit,
            TEMPLATE_DATA_PRODUCT_SENTINEL,
            bp_ids,
            kpi.benchmark_range,
            kpi.benchmark_source,
            {
                "confidence": kpi.confidence,
                "benchmark_low": kpi.benchmark_low,
                "benchmark_high": kpi.benchmark_high,
                "created_by": created_by,
            },
            now,
        )
    except Exception as exc:
        logger.error(
            "Insert failed for template KPI '%s' (client=%s): %s",
            kpi_id,
            client_id,
            exc,
        )
        return CommittedKPISummary(
            kpi_id=kpi_id, name=kpi.name, status="error", error=str(exc)
        )

    # asyncpg returns "INSERT 0 N" — N is the actual row count
    inserted = result.endswith(" 1")
    if inserted:
        return CommittedKPISummary(kpi_id=kpi_id, name=kpi.name, status="written")
    return CommittedKPISummary(
        kpi_id=kpi_id, name=kpi.name, status="skipped_duplicate"
    )


@router.post(
    "/commit",
    response_model=CommitTemplatesResponse,
    status_code=status.HTTP_200_OK,
)
async def commit_templates(
    request: CommitTemplatesRequest,
    pool: asyncpg.Pool = Depends(_get_pool),
) -> CommitTemplatesResponse:
    """Write accepted template KPIs to the registry with status='template'.

    Idempotent: existing rows with the same (client_id, id) are reported as
    skipped_duplicate rather than overwritten. Failures on individual KPIs do
    not abort the batch — every row is attempted and reported per-row.
    """
    if not request.accepted_kpis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one KPI must be accepted before commit.",
        )

    results: list[CommittedKPISummary] = []
    async with pool.acquire() as conn:
        for kpi in request.accepted_kpis:
            summary = await _insert_template_kpi(
                conn, request.client_id, kpi, request.created_by
            )
            results.append(summary)

    rows_written = sum(1 for r in results if r.status == "written")
    rows_skipped = sum(1 for r in results if r.status == "skipped_duplicate")
    rows_failed = sum(1 for r in results if r.status == "error")

    logger.info(
        "Commit templates: client=%s written=%d skipped=%d failed=%d",
        request.client_id,
        rows_written,
        rows_skipped,
        rows_failed,
    )

    return CommitTemplatesResponse(
        rows_written=rows_written,
        rows_skipped=rows_skipped,
        rows_failed=rows_failed,
        results=results,
    )
