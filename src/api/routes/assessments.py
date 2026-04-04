"""
Assessment Pipeline API routes — Phase 9C.

GET  /api/v1/assessments/latest          — most recent completed assessment run with all KPI results
GET  /api/v1/assessments/{run_id}        — full detail for a specific run
POST /api/v1/assessments/run             — trigger an on-demand assessment (calls run_enterprise_assessment logic inline)
GET  /api/v1/assessments/runs            — list recent runs (latest 10 by default)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from src.agents.models.assessment_models import (
    AssessmentConfig,
    AssessmentRun,
    AssessmentStatus,
    AssessmentSummary,
    KPIAssessment,
)
from src.api.runtime import get_agent_runtime

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/assessments",
    tags=["assessments"],
)

# ---------------------------------------------------------------------------
# In-memory store (MVP — Supabase in Phase 9C full)
# ---------------------------------------------------------------------------
# TODO: Replace with Supabase reads in Phase 9C full implementation
_assessment_runs: dict[str, AssessmentRun] = {}
_kpi_assessments: dict[str, list[KPIAssessment]] = {}  # keyed by run_id


# ---------------------------------------------------------------------------
# GET /latest  — most recent completed assessment run
# ---------------------------------------------------------------------------
@router.get("/latest", response_model=AssessmentSummary)
async def get_latest_assessment(
    principal_id: Optional[str] = None,
) -> AssessmentSummary:
    """
    Return the most recent completed assessment run together with all of its
    per-KPI results.

    When principal_id is provided it is noted but filtering is not yet applied
    (TODO: filter by principal once Supabase persistence lands in Phase 9C full).
    """
    # TODO: when principal_id is set, filter KPIs owned by / relevant to that principal
    completed = [
        run for run in _assessment_runs.values()
        if run.status == AssessmentStatus.COMPLETE
    ]
    if not completed:
        raise HTTPException(
            status_code=404,
            detail="No completed assessment runs found",
        )

    latest = max(completed, key=lambda r: r.started_at)
    return AssessmentSummary(
        run=latest,
        assessments=_kpi_assessments.get(latest.id, []),
    )


# ---------------------------------------------------------------------------
# GET /runs  — list recent runs
# ---------------------------------------------------------------------------
@router.get("/runs", response_model=list[AssessmentRun])
async def list_assessment_runs(limit: int = 10) -> list[AssessmentRun]:
    """Return the most recent `limit` assessment runs sorted by started_at descending."""
    sorted_runs = sorted(
        _assessment_runs.values(),
        key=lambda r: r.started_at,
        reverse=True,
    )
    return sorted_runs[:limit]


# ---------------------------------------------------------------------------
# GET /{run_id}  — full detail for a specific run
# ---------------------------------------------------------------------------
@router.get("/{run_id}", response_model=AssessmentSummary)
async def get_assessment(run_id: str) -> AssessmentSummary:
    """Return the AssessmentRun and all KPIAssessment records for a given run_id."""
    run = _assessment_runs.get(run_id)
    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Assessment run '{run_id}' not found",
        )
    return AssessmentSummary(
        run=run,
        assessments=_kpi_assessments.get(run_id, []),
    )


# ---------------------------------------------------------------------------
# POST /run  — trigger an on-demand assessment
# ---------------------------------------------------------------------------
@router.post("/run", response_model=AssessmentRun)
async def trigger_assessment(
    principal_id: Optional[str] = None,
    dry_run: bool = False,
    runtime=Depends(get_agent_runtime),
) -> AssessmentRun:
    """
    Trigger an on-demand enterprise assessment.

    Creates an AssessmentRun record with status RUNNING, delegates to
    EnterpriseAssessmentEngine, stores the completed run and its per-KPI
    results, then returns the finished AssessmentRun.
    """
    config = AssessmentConfig(principal_id=principal_id, dry_run=dry_run)

    run_id = str(uuid.uuid4())
    run = AssessmentRun(
        id=run_id,
        started_at=datetime.now(timezone.utc),
        status=AssessmentStatus.RUNNING,
        config=config,
    )
    _assessment_runs[run_id] = run

    try:
        # Function-level import to avoid circular import at module load time
        from run_enterprise_assessment import EnterpriseAssessmentEngine  # type: ignore[import]

        engine = EnterpriseAssessmentEngine(
            runtime.get_orchestrator(),
            runtime.get_registry_factory(),
            config,
        )
        completed_run: AssessmentRun = await engine.run()
        _assessment_runs[completed_run.id] = completed_run
        _kpi_assessments[completed_run.id] = getattr(engine, "kpi_assessments", [])
        logger.info(
            "Assessment run completed: id=%s kpi_count=%d escalated=%d",
            completed_run.id,
            completed_run.kpi_count,
            completed_run.kpis_escalated,
        )
        return completed_run

    except Exception as exc:
        logger.error("Assessment run failed: run_id=%s error=%s", run_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Assessment run failed: {exc}",
        ) from exc
