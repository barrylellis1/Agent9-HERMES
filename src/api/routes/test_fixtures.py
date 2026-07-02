"""
Test fixture injection endpoint — only mounted when APP_ENV=test.

Allows Playwright and integration tests to pre-seed workflow results into the
in-memory workflow store without running the real agent pipeline. The existing
status endpoints (/workflows/*/status) return these results transparently.

NEVER import or mount this router in production code — it bypasses all agent logic.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Re-use the shared store and helpers from the workflows module
from src.api.routes.workflows import (
    WorkflowRecord,
    Envelope,
    wrap,
    _workflow_store,
    _store_lock,
)

router = APIRouter(prefix="/test", tags=["test-fixtures"])

_ALLOWED_WORKFLOW_TYPES = {"situations", "deep_analysis", "solutions"}


class InjectWorkflowResultRequest(BaseModel):
    request_id: str = Field(..., description="The fake request_id the UI will poll against")
    workflow_type: str = Field(..., description="'situations' | 'deep_analysis' | 'solutions'")
    result: Dict[str, Any] = Field(..., description="Pre-canned result payload stored under record.result")
    state: str = Field("completed", description="Workflow terminal state — almost always 'completed'")
    error: Optional[str] = Field(None, description="Error message if state='failed'")


@router.post("/inject-workflow-result", response_model=Envelope)
async def inject_workflow_result(body: InjectWorkflowResultRequest) -> Envelope:
    """
    Inject a pre-canned workflow result into the in-memory store.

    After calling this endpoint, any poll to /api/v1/workflows/{type}/{request_id}/status
    will return the injected result immediately with state=completed.
    """
    if body.workflow_type not in _ALLOWED_WORKFLOW_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"workflow_type must be one of {sorted(_ALLOWED_WORKFLOW_TYPES)}",
        )

    now = datetime.utcnow().isoformat()
    record = WorkflowRecord(
        request_id=body.request_id,
        workflow_type=body.workflow_type,
        state=body.state,
        payload={},
        created_at=now,
        updated_at=now,
        result=body.result,
        error=body.error,
    )
    async with _store_lock:
        _workflow_store[body.request_id] = record

    return wrap({"request_id": body.request_id, "state": body.state, "injected": True})


@router.delete("/clear-workflow-result/{request_id}", response_model=Envelope)
async def clear_injected_result(request_id: str) -> Envelope:
    """Remove an injected workflow result from the store (test teardown)."""
    async with _store_lock:
        removed = _workflow_store.pop(request_id, None)
    return wrap({"request_id": request_id, "removed": removed is not None})


@router.delete("/clear-all-workflow-results", response_model=Envelope)
async def clear_all_results() -> Envelope:
    """Wipe the entire in-memory workflow store (full test reset)."""
    async with _store_lock:
        count = len(_workflow_store)
        _workflow_store.clear()
    return wrap({"cleared": count})
