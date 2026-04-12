"""
API routes for Value Assurance — Initiative Tracking / Proven ROI (Pillar 5).

Legacy endpoints (unchanged — backwards-compatible):
  POST   /api/v1/value-assurance/solutions              — record a newly approved solution
  GET    /api/v1/value-assurance/solutions              — list all solutions (filterable)
  GET    /api/v1/value-assurance/solutions/{id}         — retrieve one solution
  PATCH  /api/v1/value-assurance/solutions/{id}         — update status / actual_impact / notes
  POST   /api/v1/value-assurance/solutions/{id}/check   — run a value assurance check

Phase 7A endpoints (delegate to A9_Value_Assurance_Agent via AgentRegistry):
  POST   /api/v1/value-assurance/register                       — register solution (DiD tracking)
  POST   /api/v1/value-assurance/solutions/{id}/evaluate        — DiD attribution
  GET    /api/v1/value-assurance/portfolio/{principal_id}       — portfolio summary
  POST   /api/v1/value-assurance/inaction-cost                  — project inaction cost

Storage: legacy routes use in-memory dict (MVP).
         Phase 7A routes delegate to the agent's own in-memory store.
         Supabase persistence is Phase 7B.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from src.agents.models.value_assurance_models import (
    LegacyAcceptedSolution as AcceptedSolution,
    CreateAcceptedSolutionRequest,
    EvaluateSolutionRequest,
    EvaluateSolutionResponse,
    ListAcceptedSolutionsResponse,
    PortfolioSummaryRequest,
    ProjectInactionCostRequest,
    ProjectInactionCostResponse,
    RecordKPIMeasurementRequest,
    RecordKPIMeasurementResponse,
    RegisterSolutionRequest,
    RegisterSolutionResponse,
    SolutionPhase,
    SolutionStatus,
    UpdateSolutionPhaseRequest,
    UpdateSolutionPhaseResponse,
    StrategyAwarePortfolio,
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
# In-memory store for legacy endpoints (MVP).  Replace with DB calls in Phase 2.
# ---------------------------------------------------------------------------
_solutions_store: dict[str, AcceptedSolution] = {}


# ---------------------------------------------------------------------------
# Internal helper — acquire VA Agent (singleton via AgentRegistry)
# ---------------------------------------------------------------------------

async def _get_va_agent():
    """
    Get (or lazily create) the Value Assurance Agent.

    Tries the AgentRegistry first so the agent is reused across requests.
    Falls back to direct instantiation when the registry is unavailable.

    Raises HTTPException(503) when the agent cannot be obtained.
    """
    try:
        from src.agents.new.a9_orchestrator_agent import AgentRegistry
        agent = await AgentRegistry.get_agent("A9_Value_Assurance_Agent")
        if agent is not None:
            return agent
    except Exception as exc:
        logger.warning("VA agent registry lookup failed, falling back to direct create: %s", exc)

    # Fallback: create directly (connects without an orchestrator)
    try:
        from src.agents.new.a9_value_assurance_agent import A9_Value_Assurance_Agent
        from src.agents.agent_config_models import A9ValueAssuranceAgentConfig
        config = A9ValueAssuranceAgentConfig()
        agent = await A9_Value_Assurance_Agent.create_from_registry(config)
        # Cache in registry so subsequent requests reuse the same instance
        try:
            from src.agents.new.a9_orchestrator_agent import AgentRegistry as _AR
            _AR.register_agent("A9_Value_Assurance_Agent", agent)
        except Exception:
            pass
        return agent
    except Exception as exc:
        logger.error("VA agent fallback creation failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Value Assurance Agent is unavailable. Please retry later.",
        ) from exc


# ---------------------------------------------------------------------------
# Legacy POST /solutions  — create
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
# Legacy GET /solutions  — list (optional filters: principal_id, status)
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
# Legacy GET /solutions/{id}  — retrieve one
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
# Legacy PATCH /solutions/{id}  — update mutable fields
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
# Legacy POST /solutions/{id}/check  — run value assurance check
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


# ---------------------------------------------------------------------------
# Phase 7A POST /register  — register solution for DiD tracking
# ---------------------------------------------------------------------------
@router.post("/register", response_model=RegisterSolutionResponse, status_code=201)
async def register_solution(request: RegisterSolutionRequest) -> RegisterSolutionResponse:
    """
    Register a HITL-approved solution with the Value Assurance Agent for measurement.

    The agent captures a strategy snapshot (principal priorities, KPI threshold,
    data product) and begins tracking the solution in its measurement window.
    """
    # If benchmark segments not provided, try to retrieve from Supabase situation record
    if not request.benchmark_segments or not request.strategy_snapshot:
        try:
            from src.database.situations_store import SituationsStore
            _store = SituationsStore()
            if _store.enabled and request.situation_id:
                situation_data = await _store.get_situation(request.situation_id)
                if situation_data:
                    payload = situation_data.get("full_payload", {})
                    if not request.benchmark_segments:
                        benchmarks = payload.get("benchmark_segments", [])
                        if benchmarks:
                            request = request.model_copy(update={
                                "benchmark_segments": benchmarks,
                                "control_group_segments": [
                                    s for s in benchmarks
                                    if s.get("benchmark_type") == "control_group"
                                ] or None,
                            })
        except Exception as e:
            logger.warning("Situation lookup failed (non-fatal): %s", e)

    agent = await _get_va_agent()
    try:
        response: RegisterSolutionResponse = await agent.register_solution(request)
        logger.info(
            "VA register_solution: solution_id=%s principal=%s kpi=%s",
            response.solution_id,
            request.principal_id,
            request.kpi_id,
        )
        return response
    except Exception as exc:
        logger.error("VA register_solution failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Phase 7A POST /solutions/{solution_id}/evaluate  — DiD attribution
# ---------------------------------------------------------------------------
@router.post("/solutions/{solution_id}/evaluate", response_model=EvaluateSolutionResponse)
async def evaluate_solution(
    solution_id: str,
    request: EvaluateSolutionRequest,
) -> EvaluateSolutionResponse:
    """
    Run Difference-in-Differences attribution and determine the solution verdict.

    Requires the solution to have been previously registered via POST /register.
    """
    if request.solution_id != solution_id:
        raise HTTPException(
            status_code=400,
            detail="Path solution_id and body solution_id must match",
        )

    agent = await _get_va_agent()
    try:
        response: EvaluateSolutionResponse = await agent.evaluate_solution_impact(request)
        logger.info(
            "VA evaluate_solution_impact: solution_id=%s verdict=%s",
            solution_id,
            response.evaluation.verdict,
        )
        return response
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("VA evaluate_solution_impact failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Phase 7A GET /portfolio/{principal_id}  — portfolio summary
# ---------------------------------------------------------------------------
@router.get("/portfolio/{principal_id}", response_model=StrategyAwarePortfolio)
async def get_portfolio(
    principal_id: str,
    include_superseded: bool = False,
) -> StrategyAwarePortfolio:
    """
    Aggregate all tracked solutions into a strategy-aware portfolio summary for a principal.

    When include_superseded=False (default), solutions whose strategy alignment is
    SUPERSEDED are excluded from ROI totals but still appear in the solutions list.
    """
    portfolio_req = PortfolioSummaryRequest(
        request_id=str(uuid.uuid4()),
        principal_id=principal_id,
        include_superseded=include_superseded,
    )
    agent = await _get_va_agent()
    try:
        portfolio: StrategyAwarePortfolio = await agent.get_portfolio_summary(portfolio_req)
        return portfolio
    except Exception as exc:
        logger.error("VA get_portfolio_summary failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Phase 7A POST /inaction-cost  — project inaction cost
# ---------------------------------------------------------------------------
@router.post("/inaction-cost", response_model=ProjectInactionCostResponse)
async def project_inaction_cost(
    request: ProjectInactionCostRequest,
) -> ProjectInactionCostResponse:
    """
    Fit a linear trend to historical KPI values and project forward 30 and 90 days.

    Revenue impact is a heuristic (0.5% revenue per 1% KPI change, LOW confidence).
    Requires at least one value in historical_trend.
    """
    agent = await _get_va_agent()
    try:
        response: ProjectInactionCostResponse = await agent.project_inaction_cost(request)
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("VA project_inaction_cost failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Phase 7C POST /solutions/{solution_id}/measure  — record KPI measurement
# ---------------------------------------------------------------------------
@router.post(
    "/solutions/{solution_id}/measure",
    response_model=RecordKPIMeasurementResponse,
)
async def record_kpi_measurement(
    solution_id: str,
    kpi_value: float,
    principal_id: str = "",
) -> RecordKPIMeasurementResponse:
    """
    Append a monthly KPI measurement to the solution's actual_trend.

    Called manually from the Portfolio UI or automatically by the Enterprise
    Assessment Pipeline (Phase 9).
    """
    agent = await _get_va_agent()
    req = RecordKPIMeasurementRequest(
        request_id=str(uuid.uuid4()),
        principal_id=principal_id,
        solution_id=solution_id,
        kpi_value=kpi_value,
    )
    try:
        response: RecordKPIMeasurementResponse = await agent.record_kpi_measurement(req)
        logger.info(
            "VA record_kpi_measurement: solution_id=%s points=%d",
            solution_id,
            len(response.actual_trend),
        )
        return response
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("VA record_kpi_measurement failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# PATCH /solutions/{solution_id}/phase  — lifecycle phase transition
# ---------------------------------------------------------------------------
from pydantic import BaseModel as _BaseModel

class _PhaseTransitionBody(_BaseModel):
    new_phase: SolutionPhase
    notes: Optional[str] = None

@router.patch(
    "/solutions/{solution_id}/phase",
    response_model=UpdateSolutionPhaseResponse,
)
async def update_solution_phase(
    solution_id: str,
    body: _PhaseTransitionBody,
    principal_id: str = "",
) -> UpdateSolutionPhaseResponse:
    """
    Advance a solution through its lifecycle phases.

    Valid forward transitions: APPROVED → IMPLEMENTING → LIVE → MEASURING → COMPLETE.
    """
    agent = await _get_va_agent()
    req = UpdateSolutionPhaseRequest(
        request_id=str(uuid.uuid4()),
        principal_id=principal_id,
        solution_id=solution_id,
        new_phase=body.new_phase,
        notes=body.notes,
    )
    try:
        response: UpdateSolutionPhaseResponse = await agent.update_solution_phase(req)
        logger.info(
            "VA update_solution_phase: solution_id=%s → %s",
            solution_id, body.new_phase.value,
        )
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("VA update_solution_phase failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# PUT /solutions/{solution_id}/briefing  — store briefing snapshot
# ---------------------------------------------------------------------------
@router.put("/solutions/{solution_id}/briefing")
async def store_briefing_snapshot(solution_id: str, request: Request):
    """Store the Executive Briefing snapshot for a VA solution."""
    try:
        from src.database.va_solutions_store import VASolutionsStore
        store = VASolutionsStore()
        if not store.enabled:
            raise HTTPException(status_code=503, detail="Supabase not configured")

        import json as _json
        body_bytes = await request.body()
        snapshot = _json.loads(body_bytes)
        success = await store.store_briefing_snapshot(solution_id, snapshot)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to store briefing snapshot")
        return {"status": "ok", "solution_id": solution_id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("store_briefing_snapshot failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# GET /solutions/{solution_id}/briefing  — retrieve briefing snapshot
# ---------------------------------------------------------------------------
@router.get("/solutions/{solution_id}/briefing")
async def get_briefing_snapshot(solution_id: str):
    """Retrieve the stored Executive Briefing snapshot for a VA solution."""
    try:
        from src.database.va_solutions_store import VASolutionsStore
        store = VASolutionsStore()
        if not store.enabled:
            raise HTTPException(status_code=503, detail="Supabase not configured")

        snapshot = await store.get_briefing_snapshot(solution_id)
        if snapshot is None:
            raise HTTPException(
                status_code=404, detail="No briefing snapshot found for this solution"
            )
        return snapshot
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("get_briefing_snapshot failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
