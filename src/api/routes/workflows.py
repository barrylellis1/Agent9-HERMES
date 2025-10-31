from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.runtime import AgentRuntime, get_agent_runtime
from src.agents.models.deep_analysis_models import DeepAnalysisPlan, DeepAnalysisRequest
from src.agents.models.solution_finder_models import SolutionFinderRequest
from src.agents.models.situation_awareness_models import ComparisonType, TimeFrame


router = APIRouter(prefix="/workflows", tags=["workflows"])


class Envelope(BaseModel):
    status: str = Field("ok")
    data: Any


def serialize(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return {key: serialize(val) for key, val in value.items()}
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def wrap(data: Any) -> Envelope:
    return Envelope(data=serialize(data))


@dataclass
class WorkflowRecord:
    request_id: str
    workflow_type: str
    state: str
    payload: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    annotations: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "workflow_type": self.workflow_type,
            "state": self.state,
            "payload": serialize(self.payload),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": serialize(self.result) if self.result is not None else None,
            "error": self.error,
            "annotations": serialize(self.annotations),
            "actions": serialize(self.actions),
        }


_workflow_store: Dict[str, WorkflowRecord] = {}
_store_lock = asyncio.Lock()


def _generate_request_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex}"


async def _create_record(request_id: str, workflow_type: str, payload: Dict[str, Any]) -> WorkflowRecord:
    record = WorkflowRecord(request_id=request_id, workflow_type=workflow_type, state="pending", payload=payload)
    async with _store_lock:
        _workflow_store[request_id] = record
    return record


async def _get_record(request_id: str) -> Optional[WorkflowRecord]:
    async with _store_lock:
        return _workflow_store.get(request_id)


async def _update_record(request_id: str, **updates: Any) -> Optional[WorkflowRecord]:
    async with _store_lock:
        record = _workflow_store.get(request_id)
        if record is None:
            return None
        for key, value in updates.items():
            setattr(record, key, value)
        record.updated_at = datetime.utcnow().isoformat()
        return record


async def _ensure_record(request_id: str, expected_type: str) -> WorkflowRecord:
    record = await _get_record(request_id)
    if record is None or record.workflow_type != expected_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow request not found")
    return record


class SituationWorkflowRequest(BaseModel):
    principal_id: str = Field(..., description="ID of the principal requesting the workflow")
    business_processes: Optional[List[str]] = Field(None, description="Specific business processes to analyze")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters for KPI evaluation")
    comparison_type: Optional[str] = Field(None, description="Override comparison type")
    timeframe: Optional[str] = Field(None, description="Requested timeframe token")
    kpi_ids: Optional[List[str]] = Field(None, description="Explicit KPI identifiers to evaluate")
    include_annotations: bool = Field(False, description="Whether to capture annotations in the workflow")


class DeepAnalysisScope(BaseModel):
    kpi_id: str = Field(..., description="Target KPI identifier")
    time_range: Optional[Dict[str, Any]] = Field(None, description="Custom time range with start/end")


class DeepAnalysisWorkflowRequest(BaseModel):
    principal_id: str = Field(..., description="ID of the requesting principal")
    situation_id: Optional[str] = Field(None, description="Related situation identifier")
    scope: DeepAnalysisScope = Field(..., description="Scope for the deep analysis")
    hypotheses: Optional[List[str]] = Field(None, description="Optional hypotheses to evaluate")
    include_supporting_evidence: bool = Field(True, description="Whether to compute supporting evidence artifacts")


class SolutionWorkflowRequest(BaseModel):
    principal_id: str = Field(..., description="ID of the requesting principal")
    analysis_request_id: Optional[str] = Field(None, description="Prior deep-analysis request to build upon")
    problem_statement: Optional[str] = Field(None, description="Problem statement to solve")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Constraints such as budget or timeline")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Additional preferences for recommendations")


class AnnotationRequest(BaseModel):
    note: str = Field(..., description="Annotation text")


class ActionRequest(BaseModel):
    action: str = Field(..., description="Action identifier")
    comment: Optional[str] = Field(None, description="Additional action context")
    payload: Optional[Dict[str, Any]] = Field(None, description="Optional payload for the action")


@router.post("/situations/run", response_model=Envelope, status_code=status.HTTP_202_ACCEPTED)
async def run_situations_workflow(
    request: SituationWorkflowRequest,
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> Envelope:
    request_id = _generate_request_id("situation")
    await _create_record(request_id, "situations", request.model_dump())
    asyncio.create_task(_run_situations_workflow(request_id, runtime, request))
    return wrap({"request_id": request_id, "state": "pending"})


@router.get("/situations/{request_id}/status", response_model=Envelope)
async def get_situations_status(request_id: str) -> Envelope:
    record = await _ensure_record(request_id, "situations")
    return wrap(record.to_dict())


@router.post("/deep-analysis/run", response_model=Envelope, status_code=status.HTTP_202_ACCEPTED)
async def run_deep_analysis_workflow(
    request: DeepAnalysisWorkflowRequest,
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> Envelope:
    request_id = _generate_request_id("deep_analysis")
    await _create_record(request_id, "deep_analysis", request.model_dump())
    asyncio.create_task(_run_deep_analysis_workflow(request_id, runtime, request))
    return wrap({"request_id": request_id, "state": "pending"})


@router.get("/deep-analysis/{request_id}/status", response_model=Envelope)
async def get_deep_analysis_status(request_id: str) -> Envelope:
    record = await _ensure_record(request_id, "deep_analysis")
    return wrap(record.to_dict())


@router.post("/solutions/run", response_model=Envelope, status_code=status.HTTP_202_ACCEPTED)
async def run_solution_workflow(
    request: SolutionWorkflowRequest,
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> Envelope:
    request_id = _generate_request_id("solution")
    await _create_record(request_id, "solutions", request.model_dump())
    asyncio.create_task(_run_solution_workflow(request_id, runtime, request))
    return wrap({"request_id": request_id, "state": "pending"})


@router.get("/solutions/{request_id}/status", response_model=Envelope)
async def get_solution_status(request_id: str) -> Envelope:
    record = await _ensure_record(request_id, "solutions")
    return wrap(record.to_dict())


@router.post("/situations/{request_id}/annotations", response_model=Envelope)
async def annotate_situation(request_id: str, request: AnnotationRequest) -> Envelope:
    record = await _ensure_record(request_id, "situations")
    record.annotations.append({
        "note": request.note,
        "timestamp": datetime.utcnow().isoformat(),
    })
    await _update_record(request_id, annotations=record.annotations)
    return wrap({"request_id": request_id, "annotations": record.annotations})


@router.post("/deep-analysis/{request_id}/actions/request-revision", response_model=Envelope)
async def deep_analysis_request_revision(request_id: str, request: ActionRequest) -> Envelope:
    record = await _ensure_record(request_id, "deep_analysis")
    action_entry = {
        "action": request.action,
        "comment": request.comment,
        "payload": serialize(request.payload) if request.payload else None,
        "timestamp": datetime.utcnow().isoformat(),
    }
    record.actions.append(action_entry)
    await _update_record(request_id, actions=record.actions)
    return wrap({"request_id": request_id, "actions": record.actions})


@router.post("/solutions/{request_id}/actions/approve", response_model=Envelope)
async def approve_solution(request_id: str, request: ActionRequest) -> Envelope:
    return await _record_solution_action(request_id, "approve", request)


@router.post("/solutions/{request_id}/actions/request-changes", response_model=Envelope)
async def request_solution_changes(request_id: str, request: ActionRequest) -> Envelope:
    return await _record_solution_action(request_id, "request-changes", request)


@router.post("/solutions/{request_id}/actions/iterate", response_model=Envelope)
async def iterate_solution(request_id: str, request: ActionRequest) -> Envelope:
    return await _record_solution_action(request_id, "iterate", request)


async def _record_solution_action(request_id: str, action_type: str, request: ActionRequest) -> Envelope:
    record = await _ensure_record(request_id, "solutions")
    entry = {
        "action": action_type,
        "comment": request.comment,
        "payload": serialize(request.payload) if request.payload else None,
        "timestamp": datetime.utcnow().isoformat(),
    }
    record.actions.append(entry)
    await _update_record(request_id, actions=record.actions)
    return wrap({"request_id": request_id, "actions": record.actions})


async def _run_situations_workflow(request_id: str, runtime: AgentRuntime, request: SituationWorkflowRequest) -> None:
    try:
        orchestrator = runtime.get_orchestrator()
        principal_resp = await orchestrator.execute_agent_method(
            "A9_Principal_Context_Agent",
            "get_principal_context_by_id",
            {"principal_id": request.principal_id},
        )

        principal_context = None
        if isinstance(principal_resp, dict):
            principal_context = principal_resp.get("context") or principal_resp.get("principal_context") or principal_resp
        elif hasattr(principal_resp, "context"):
            principal_context = serialize(principal_resp.context)
        if principal_context is None:
            raise ValueError("Unable to resolve principal context")

        business_processes = request.business_processes or principal_context.get("business_processes") or []
        timeframe = request.timeframe or TimeFrame.CURRENT_QUARTER.value
        comparison_type = request.comparison_type or ComparisonType.YEAR_OVER_YEAR.value

        detection_request = {
            "request_id": request_id,
            "principal_context": principal_context,
            "business_processes": business_processes,
            "timeframe": timeframe,
            "comparison_type": comparison_type,
            "filters": request.filters or {},
        }
        if request.kpi_ids:
            detection_request["kpi_ids"] = request.kpi_ids

        response = await orchestrator.detect_situations_batch(detection_request)
        await _update_record(
            request_id,
            state="completed",
            result={"situations": serialize(response)},
        )
    except Exception as exc:  # pragma: no cover - defensive
        await _update_record(request_id, state="failed", error=str(exc))


async def _run_deep_analysis_workflow(request_id: str, runtime: AgentRuntime, request: DeepAnalysisWorkflowRequest) -> None:
    try:
        orchestrator = runtime.get_orchestrator()
        principal_resp = await orchestrator.execute_agent_method(
            "A9_Principal_Context_Agent",
            "get_principal_context_by_id",
            {"principal_id": request.principal_id},
        )
        principal_context = None
        if isinstance(principal_resp, dict):
            principal_context = principal_resp.get("context") or principal_resp.get("principal_context") or principal_resp
        elif hasattr(principal_resp, "context"):
            principal_context = serialize(principal_resp.context)

        deep_request_payload: Dict[str, Any] = {
            "request_id": request_id,
            "principal_id": request.principal_id,
            "kpi_name": request.scope.kpi_id,
            "filters": {},
        }
        if principal_context is not None:
            deep_request_payload["principal_context"] = principal_context
        if request.scope.time_range:
            deep_request_payload["filters"] = {"time_range": request.scope.time_range}
        if request.hypotheses:
            deep_request_payload["extra"] = {"hypotheses": request.hypotheses}
        deep_request = DeepAnalysisRequest(**deep_request_payload)

        plan_resp = await orchestrator.execute_agent_method(
            "A9_Deep_Analysis_Agent",
            "plan_deep_analysis",
            {"request": deep_request},
        )
        plan_serialized = serialize(plan_resp)
        plan_data = None
        if isinstance(plan_resp, dict):
            plan_data = plan_resp.get("plan")
        elif hasattr(plan_resp, "plan"):
            plan_data = serialize(plan_resp.plan)
        if plan_data is None:
            plan_data = plan_serialized.get("plan") if isinstance(plan_serialized, dict) else None
        if plan_data is None:
            raise ValueError("Deep analysis plan not available")
        plan_object = DeepAnalysisPlan(**plan_data) if not hasattr(plan_data, "model_dump") else plan_data

        execution_resp = await orchestrator.execute_agent_method(
            "A9_Deep_Analysis_Agent",
            "execute_deep_analysis",
            {"plan": plan_object},
        )
        result_payload = {
            "plan": plan_serialized,
            "execution": serialize(execution_resp),
        }
        await _update_record(request_id, state="completed", result=result_payload)
    except Exception as exc:  # pragma: no cover - defensive
        await _update_record(request_id, state="failed", error=str(exc))


async def _run_solution_workflow(request_id: str, runtime: AgentRuntime, request: SolutionWorkflowRequest) -> None:
    try:
        orchestrator = runtime.get_orchestrator()
        deep_output: Optional[Dict[str, Any]] = None
        if request.analysis_request_id:
            related_record = await _get_record(request.analysis_request_id)
            if related_record and related_record.result:
                deep_output = related_record.result.get("execution") or related_record.result

        solution_request_payload: Dict[str, Any] = {
            "request_id": request_id,
            "principal_id": request.principal_id,
            "problem_statement": request.problem_statement or "",
            "deep_analysis_output": deep_output,
            "constraints": request.constraints or {},
            "preferences": request.preferences or {},
        }
        solution_request = SolutionFinderRequest(**solution_request_payload)

        response = await orchestrator.execute_agent_method(
            "A9_Solution_Finder_Agent",
            "recommend_actions",
            {"request": solution_request},
        )
        await _update_record(request_id, state="completed", result={"solutions": serialize(response)})
    except Exception as exc:  # pragma: no cover - defensive
        await _update_record(request_id, state="failed", error=str(exc))
