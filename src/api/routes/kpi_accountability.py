"""API routes for KPI Accountability.

Provides CRUD operations for the kpi_accountability registry table, plus the
LLM-driven accountability interview endpoints (start, chat, confirm, coverage).
All endpoints are scoped by client_id — strict match, no cross-tenant leakage.

Prefix: /api/v1/accountability/
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import List, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from src.registry.models.kpi_accountability import AccountabilityRole, KPIAccountability
from src.registry.providers.accountability_provider import KPIAccountabilityProvider
from src.agents.new.a9_accountability_interview_agent import (
    A9_Accountability_Interview_Agent,
    AccountabilityInterviewRequest,
    AccountabilityInterviewResponse,
    ProposedAssignment,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/accountability", tags=["kpi-accountability"])


# ---------------------------------------------------------------------------
# DB dependency — reuses the shared pool from RegistryBootstrap
# (identical pattern to src/api/routes/connection_profiles.py)
# ---------------------------------------------------------------------------

async def _get_pool() -> asyncpg.Pool:
    from src.registry.bootstrap import RegistryBootstrap
    from src.api.runtime import agent_runtime

    await agent_runtime.initialize()

    db_manager = RegistryBootstrap._db_manager
    if db_manager is None or getattr(db_manager, "pool", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available — registry not initialized.",
        )
    return db_manager.pool


# ---------------------------------------------------------------------------
# Pydantic I/O models
# ---------------------------------------------------------------------------

class KPIAccountabilityOut(BaseModel):
    id: str
    client_id: str
    kpi_id: str
    principal_id: str
    scope_dimension: Optional[str] = None
    scope_value: Optional[str] = None
    role: str
    notes: Optional[str] = None
    created_by: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class KPIAccountabilityCreate(BaseModel):
    client_id: str
    kpi_id: str
    principal_id: str
    scope_dimension: Optional[str] = None
    scope_value: Optional[str] = None
    role: AccountabilityRole = AccountabilityRole.ACCOUNTABLE
    notes: Optional[str] = None
    created_by: str = "system"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _model_to_out(item: KPIAccountability) -> KPIAccountabilityOut:
    def _iso(val) -> Optional[str]:
        if val is None:
            return None
        if isinstance(val, datetime):
            return val.isoformat()
        return str(val)

    return KPIAccountabilityOut(
        id=item.id,
        client_id=item.client_id,
        kpi_id=item.kpi_id,
        principal_id=item.principal_id,
        scope_dimension=item.scope_dimension,
        scope_value=item.scope_value,
        role=item.role.value,
        notes=item.notes,
        created_by=item.created_by,
        created_at=_iso(item.created_at),
        updated_at=_iso(item.updated_at),
    )


# ---------------------------------------------------------------------------
# Provider dependency
# ---------------------------------------------------------------------------

def _get_provider() -> KPIAccountabilityProvider:
    return KPIAccountabilityProvider()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_model=List[KPIAccountabilityOut])
async def list_accountability(
    client_id: str = Query(..., description="Tenant client ID — strict match"),
    pool: asyncpg.Pool = Depends(_get_pool),  # noqa: ARG001  (ensures pool is ready)
    provider: KPIAccountabilityProvider = Depends(_get_provider),
):
    """List all KPI accountability records for a client."""
    records = await provider.get_all(client_id)
    return [_model_to_out(r) for r in records]


@router.get("/principal/{principal_id}", response_model=List[KPIAccountabilityOut])
async def list_accountability_for_principal(
    principal_id: str,
    client_id: str = Query(..., description="Tenant client ID — strict match"),
    pool: asyncpg.Pool = Depends(_get_pool),
    provider: KPIAccountabilityProvider = Depends(_get_provider),
):
    """List KPI accountability records for a specific principal."""
    records = await provider.get_for_principal(client_id, principal_id)
    return [_model_to_out(r) for r in records]


@router.get("/kpi/{kpi_id}", response_model=List[KPIAccountabilityOut])
async def list_accountability_for_kpi(
    kpi_id: str,
    client_id: str = Query(..., description="Tenant client ID — strict match"),
    pool: asyncpg.Pool = Depends(_get_pool),
    provider: KPIAccountabilityProvider = Depends(_get_provider),
):
    """List accountability records for a specific KPI."""
    records = await provider.get_for_kpi(client_id, kpi_id)
    return [_model_to_out(r) for r in records]


@router.post("/", response_model=KPIAccountabilityOut, status_code=status.HTTP_201_CREATED)
async def create_accountability(
    request: KPIAccountabilityCreate,
    pool: asyncpg.Pool = Depends(_get_pool),
    provider: KPIAccountabilityProvider = Depends(_get_provider),
):
    """Create a KPI accountability record.

    The unique constraint on (client_id, kpi_id, scope_dimension, scope_value) is
    enforced at the database level — attempting to add a second accountable principal
    to the same scope will raise a 409 Conflict.
    """
    new_id = str(uuid.uuid4())[:8]  # short but unique within a session
    # Use a deterministic prefix so IDs are meaningful in seed data
    record_id = f"acc_{new_id}"

    item = KPIAccountability(
        id=record_id,
        client_id=request.client_id,
        kpi_id=request.kpi_id,
        principal_id=request.principal_id,
        scope_dimension=request.scope_dimension,
        scope_value=request.scope_value,
        role=request.role,
        notes=request.notes,
        created_by=request.created_by,
    )

    try:
        created = await provider.upsert(item)
    except asyncpg.UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"An accountability record already exists for KPI '{request.kpi_id}' "
                f"with scope ({request.scope_dimension}, {request.scope_value}) "
                f"for client '{request.client_id}'."
            ),
        )

    logger.info(
        "Created accountability record for kpi=%s principal=%s client=%s",
        request.kpi_id,
        request.principal_id,
        request.client_id,
    )
    return _model_to_out(created)


# ---------------------------------------------------------------------------
# Interview — lazy singleton agent (sessions are in-memory)
# ---------------------------------------------------------------------------

_interview_agent: Optional[A9_Accountability_Interview_Agent] = None


async def _get_interview_agent() -> A9_Accountability_Interview_Agent:
    global _interview_agent
    if _interview_agent is None:
        _interview_agent = await A9_Accountability_Interview_Agent.create()
    return _interview_agent


# ---------------------------------------------------------------------------
# Interview request/response wrappers
# ---------------------------------------------------------------------------

class InterviewStartRequest(BaseModel):
    client_id: str
    principal_id: Optional[str] = None


class InterviewChatRequest(BaseModel):
    session_id: str
    client_id: str
    message: str


class InterviewConfirmRequest(BaseModel):
    client_id: str
    approved: List[ProposedAssignment]


class InterviewConfirmResponse(BaseModel):
    rows_written: int


# ---------------------------------------------------------------------------
# Interview routes
# ---------------------------------------------------------------------------

@router.post("/interview/start", response_model=AccountabilityInterviewResponse)
async def start_interview(
    request: InterviewStartRequest,
    pool: asyncpg.Pool = Depends(_get_pool),  # noqa: ARG001
):
    """Start a new accountability interview session.

    Returns an opening agent message and a session_id to use for subsequent /chat calls.
    """
    agent = await _get_interview_agent()
    interview_request = AccountabilityInterviewRequest(
        client_id=request.client_id,
        principal_id=request.principal_id,
    )
    return await agent.interview(interview_request)


@router.post("/interview/chat", response_model=AccountabilityInterviewResponse)
async def chat_interview(
    request: InterviewChatRequest,
    pool: asyncpg.Pool = Depends(_get_pool),  # noqa: ARG001
):
    """Continue an accountability interview with the admin's response.

    Returns the agent's next message plus updated proposed assignments.
    """
    agent = await _get_interview_agent()
    interview_request = AccountabilityInterviewRequest(
        session_id=request.session_id,
        client_id=request.client_id,
        user_message=request.message,
    )
    return await agent.interview(interview_request)


@router.post("/interview/confirm", response_model=InterviewConfirmResponse)
async def confirm_interview(
    request: InterviewConfirmRequest,
    pool: asyncpg.Pool = Depends(_get_pool),  # noqa: ARG001
    provider: KPIAccountabilityProvider = Depends(_get_provider),
):
    """Write approved ProposedAssignment rows to kpi_accountability.

    Only assignments with status='confirmed' or 'modified' are written.
    Rejected assignments are silently discarded.
    """
    rows_written = 0
    for assignment in request.approved:
        if assignment.status not in ("confirmed", "modified"):
            continue
        record_id = f"acc_{uuid.uuid4().hex[:8]}"
        item = KPIAccountability(
            id=record_id,
            client_id=request.client_id,
            kpi_id=assignment.kpi_id,
            principal_id=assignment.principal_id,
            scope_dimension=assignment.scope_dimension,
            scope_value=assignment.scope_value,
            role=AccountabilityRole(assignment.role),
            notes=f"Set via accountability interview — {assignment.suggestion_source}",
            created_by="interview",
        )
        try:
            await provider.upsert(item)
            rows_written += 1
        except Exception as exc:
            logger.error(
                "Failed to write accountability row kpi=%s principal=%s: %s",
                assignment.kpi_id,
                assignment.principal_id,
                exc,
            )

    logger.info(
        "Interview confirm: wrote %d rows for client '%s'",
        rows_written,
        request.client_id,
    )
    return InterviewConfirmResponse(rows_written=rows_written)


@router.get("/coverage/{client_id}")
async def get_coverage(
    client_id: str,
    pool: asyncpg.Pool = Depends(_get_pool),  # noqa: ARG001
):
    """Return KPI accountability coverage for a client.

    Counts KPIs with at least one accountable principal, lists unassigned KPIs,
    principals without assignments, and scope-level conflicts.
    """
    agent = await _get_interview_agent()
    return await agent.get_coverage(client_id)


# ---------------------------------------------------------------------------
# Delete (existing route kept below)
# ---------------------------------------------------------------------------

@router.delete("/{record_id}", status_code=status.HTTP_200_OK)
async def delete_accountability(
    record_id: str,
    client_id: str = Query(..., description="Tenant client ID for ownership verification"),
    pool: asyncpg.Pool = Depends(_get_pool),
    provider: KPIAccountabilityProvider = Depends(_get_provider),
):
    """Delete a KPI accountability record. Verifies client_id ownership before deleting."""
    deleted = await provider.delete(client_id, record_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Accountability record '{record_id}' not found for client '{client_id}'.",
        )
    return {"message": f"Accountability record '{record_id}' deleted."}
