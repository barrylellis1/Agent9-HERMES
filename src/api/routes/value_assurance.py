"""
API routes for Value Assurance — Initiative Tracking / Proven ROI (Pillar 5).

Endpoints:
  POST   /api/v1/value-assurance/solutions              — record a newly approved solution
  GET    /api/v1/value-assurance/solutions              — list all solutions (filterable)
  GET    /api/v1/value-assurance/solutions/{id}         — retrieve one solution
  PATCH  /api/v1/value-assurance/solutions/{id}         — update status / actual_impact / notes
  POST   /api/v1/value-assurance/solutions/{id}/check   — run a value assurance check

Storage: in-memory dict (keyed by UUID) for MVP.  Supabase persistence is Phase 2.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from src.agents.models.value_assurance_models import (
    AcceptedSolution,
    CreateAcceptedSolutionRequest,
    ListAcceptedSolutionsResponse,
    SolutionStatus,
    UpdateAcceptedSolutionRequest,
    ValueAssuranceCheckRequest,
    ValueAssuranceCheckResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/value-assurance",
    tags=["value-assurance"],
)

# ---------------------------------------------------------------------------
# In-memory store (MVP).  Replace with DB calls in Phase 2.
# ---------------------------------------------------------------------------
_solutions_store: dict[str, AcceptedSolution] = {}


# ---------------------------------------------------------------------------
# POST /solutions  — create
# ---------------------------------------------------------------------------
@router.post("/solutions", response_model=AcceptedSolution, status_code=201)
async def create_accepted_solution(request: CreateAcceptedSolutionRequest) -> AcceptedSolution:
    """Record a newly HITL-approved solution recommendation."""
    solution_id = str(uuid.uuid4())
    solution = AcceptedSolution(
        id=solution_id,
        session_id=request.session_id,
        principal_id=request.principal_id,
        kpi_name=request.kpi_name,
        option_title=request.option_title,
        option_description=request.option_description,
        expected_impact=request.expected_impact,
        expected_impact_lower=request.expected_impact_lower,
        expected_impact_upper=request.expected_impact_upper,
        notes=request.notes,
        status=SolutionStatus.ACCEPTED,
        accepted_at=datetime.utcnow().isoformat(),
    )
    _solutions_store[solution_id] = solution
    logger.info(
        "AcceptedSolution created: id=%s principal=%s kpi=%s",
        solution_id,
        request.principal_id,
        request.kpi_name,
    )
    return solution


# ---------------------------------------------------------------------------
# GET /solutions  — list (optional filters: principal_id, status)
# ---------------------------------------------------------------------------
@router.get("/solutions", response_model=ListAcceptedSolutionsResponse)
async def list_accepted_solutions(
    principal_id: Optional[str] = None,
    status: Optional[SolutionStatus] = None,
) -> ListAcceptedSolutionsResponse:
    """List all accepted solutions, optionally filtered by principal_id and/or status."""
    solutions = list(_solutions_store.values())

    if principal_id is not None:
        solutions = [s for s in solutions if s.principal_id == principal_id]

    if status is not None:
        solutions = [s for s in solutions if s.status == status]

    return ListAcceptedSolutionsResponse(solutions=solutions, total=len(solutions))


# ---------------------------------------------------------------------------
# GET /solutions/{id}  — retrieve one
# ---------------------------------------------------------------------------
@router.get("/solutions/{solution_id}", response_model=AcceptedSolution)
async def get_accepted_solution(solution_id: str) -> AcceptedSolution:
    """Retrieve a single accepted solution by ID."""
    solution = _solutions_store.get(solution_id)
    if solution is None:
        raise HTTPException(
            status_code=404,
            detail=f"Accepted solution '{solution_id}' not found",
        )
    return solution


# ---------------------------------------------------------------------------
# PATCH /solutions/{id}  — update mutable fields
# ---------------------------------------------------------------------------
@router.patch("/solutions/{solution_id}", response_model=AcceptedSolution)
async def update_accepted_solution(
    solution_id: str,
    request: UpdateAcceptedSolutionRequest,
) -> AcceptedSolution:
    """Update status, actual_impact, notes, or implementation/measurement timestamps."""
    solution = _solutions_store.get(solution_id)
    if solution is None:
        raise HTTPException(
            status_code=404,
            detail=f"Accepted solution '{solution_id}' not found",
        )

    # Apply only the fields that were explicitly provided (non-None)
    update_data = request.model_dump(exclude_none=True)
    updated = solution.model_copy(update=update_data)
    _solutions_store[solution_id] = updated

    logger.info(
        "AcceptedSolution updated: id=%s fields=%s",
        solution_id,
        list(update_data.keys()),
    )
    return updated


# ---------------------------------------------------------------------------
# POST /solutions/{id}/check  — run value assurance check
# ---------------------------------------------------------------------------
@router.post("/solutions/{solution_id}/check", response_model=ValueAssuranceCheckResponse)
async def check_value_assurance(
    solution_id: str,
    request: ValueAssuranceCheckRequest,
) -> ValueAssuranceCheckResponse:
    """
    Compare actual KPI movement against the expected impact range.

    - actual_delta = current_kpi_value - baseline_kpi_value
    - If both bounds are set: within_expected_range = lower <= actual_delta <= upper
    - If bounds are absent: within_expected_range defaults to True (no target to miss)
    - Updates the solution status to VALIDATED or FAILED and records actual_impact.
    """
    if request.accepted_solution_id != solution_id:
        raise HTTPException(
            status_code=400,
            detail="Path solution_id and body accepted_solution_id must match",
        )

    solution = _solutions_store.get(solution_id)
    if solution is None:
        raise HTTPException(
            status_code=404,
            detail=f"Accepted solution '{solution_id}' not found",
        )

    actual_delta = request.current_kpi_value - request.baseline_kpi_value

    lower = solution.expected_impact_lower
    upper = solution.expected_impact_upper

    if lower is not None and upper is not None:
        within_expected_range = lower <= actual_delta <= upper
    else:
        within_expected_range = True

    new_status = SolutionStatus.VALIDATED if within_expected_range else SolutionStatus.FAILED

    message = (
        f"Actual delta {actual_delta:+.4f} is within the expected range "
        f"[{lower}, {upper}]. Solution VALIDATED."
        if within_expected_range
        else f"Actual delta {actual_delta:+.4f} is outside the expected range "
        f"[{lower}, {upper}]. Solution FAILED."
    )

    # Persist the outcome back to the store
    updated_solution = solution.model_copy(
        update={
            "status": new_status,
            "actual_impact": actual_delta,
            "resolved_at": request.measurement_date,
        }
    )
    _solutions_store[solution_id] = updated_solution

    logger.info(
        "ValueAssuranceCheck: id=%s delta=%.4f within_range=%s new_status=%s",
        solution_id,
        actual_delta,
        within_expected_range,
        new_status,
    )

    return ValueAssuranceCheckResponse(
        accepted_solution_id=solution_id,
        kpi_name=solution.kpi_name,
        expected_impact_lower=lower,
        expected_impact_upper=upper,
        actual_delta=actual_delta,
        within_expected_range=within_expected_range,
        status=new_status,
        message=message,
    )
