from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.runtime import AgentRuntime, get_agent_runtime
from src.agents.models.deep_analysis_models import (
    DeepAnalysisPlan,
    DeepAnalysisRequest,
    ProblemRefinementInput,
    ProblemRefinementResult,
)
from src.agents.models.solution_finder_models import SolutionFinderRequest
from src.agents.models.situation_awareness_models import ComparisonType, TimeFrame, SituationDetectionRequest
from src.agents.models.data_product_onboarding_models import (
    DataProductOnboardingWorkflowRequest,
    WorkflowStepSummary,
    KPIRegistryEntry,
    BusinessProcessMapping,
    ValidateKPIQueriesRequest,
    ValidateKPIQueriesResponse,
    KPIDefinition,
)


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
    analysis_request_id: Optional[str] = Field(None, description="Prior deep-analysis request ID (deprecated, prefer deep_analysis_output)")
    deep_analysis_output: Optional[Dict[str, Any]] = Field(None, description="Full Deep Analysis result for direct agent-to-agent data exchange")
    problem_statement: Optional[str] = Field(None, description="Problem statement to solve")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Constraints such as budget or timeline")
    preferences: Optional[Dict[str, Any]] = Field(None, description="Additional preferences for recommendations")
    principal_context: Optional[Dict[str, Any]] = Field(None, description="Principal context with decision_style for Principal-driven approach")
    refinement_result: Optional[Dict[str, Any]] = Field(None, description="Problem refinement chat result with exclusions, constraints, and council routing")


class ProblemRefinementRequest(BaseModel):
    """API request for problem refinement chat turn."""
    principal_id: str = Field(..., description="ID of the requesting principal")
    deep_analysis_output: Dict[str, Any] = Field(..., description="KT IS/IS-NOT results from Deep Analysis")
    principal_context: Dict[str, Any] = Field(..., description="Principal profile with role, decision_style, filters")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Multi-turn chat history")
    user_message: Optional[str] = Field(None, description="Latest principal response (None for first turn)")
    current_topic: Optional[str] = Field(None, description="Current topic in sequence (auto-managed)")
    turn_count: int = Field(0, description="Current turn number")


class AnnotationRequest(BaseModel):
    note: str = Field(..., description="Annotation text")


class ActionRequest(BaseModel):
    action: str = Field(..., description="Action identifier")
    comment: Optional[str] = Field(None, description="Additional action context")
    payload: Optional[Dict[str, Any]] = Field(None, description="Optional payload for the action")


class DataProductOnboardingWorkflowApiRequest(BaseModel):
    principal_id: str = Field(..., description="Principal initiating onboarding")
    data_product_id: str = Field(..., description="Identifier for the new data product")
    source_system: str = Field(..., description="Source system identifier (duckdb, bigquery, etc.)")
    database: Optional[str] = Field(None, description="Database or catalog")
    schema: Optional[str] = Field(None, description="Schema or dataset")
    tables: Optional[List[str]] = Field(None, description="Specific tables to profile")
    inspection_depth: str = Field("standard", description="Profiling depth (basic/standard/extended)")
    include_samples: bool = Field(False, description="Whether to include sample values during profiling")
    environment: str = Field("dev", description="Target environment (dev/test/prod)")
    connection_overrides: Optional[Dict[str, Any]] = Field(None, description="Per-environment connection overrides")
    contract_output_path: Optional[str] = Field(None, description="Filesystem path for generated contract")
    data_product_name: Optional[str] = Field(None, description="Human friendly name")
    data_product_domain: Optional[str] = Field(None, description="Business domain")
    data_product_description: Optional[str] = Field(None, description="Narrative description")
    data_product_tags: List[str] = Field(default_factory=list, description="Registry tags")
    contract_overrides: Dict[str, Any] = Field(default_factory=dict, description="Contract override payload")
    additional_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional registry metadata")
    owner_metadata: Dict[str, Any] = Field(default_factory=dict, description="Owner metadata to persist")
    kpi_entries: List[KPIRegistryEntry] = Field(default_factory=list, description="KPI definitions to register")
    overwrite_existing_kpis: bool = Field(False, description="Whether to overwrite existing KPI entries")
    business_process_mappings: List[BusinessProcessMapping] = Field(
        default_factory=list,
        description="Business process mappings to register",
    )
    overwrite_existing_mappings: bool = Field(
        False, description="Whether to overwrite existing business process mappings"
    )
    candidate_owner_ids: List[str] = Field(
        default_factory=list,
        description="Preferred principal IDs to evaluate for ownership",
    )
    fallback_roles: List[str] = Field(
        default_factory=list,
        description="Role escalation chain for ownership resolution",
    )
    business_process_context: List[str] = Field(
        default_factory=list,
        description="Business process context for ownership resolution",
    )
    qa_enabled: bool = Field(False, description="Whether to execute optional QA helper")
    qa_checks: List[str] = Field(default_factory=list, description="Explicit QA checks to run")
    qa_additional_context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context forwarded to QA"
    )


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


@router.post("/deep-analysis/refine", response_model=Envelope)
async def refine_deep_analysis(
    request: ProblemRefinementRequest,
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> Envelope:
    """
    Problem Refinement Chat endpoint - MBB-style principal engagement.
    
    This is a synchronous endpoint that processes one turn of the refinement
    conversation and returns the next question or final result.
    
    The conversation is stateless on the server - the client maintains
    conversation_history and passes it back each turn.
    """
    try:
        orchestrator = runtime.get_orchestrator()
        
        # Build the input model for the agent
        refinement_input = ProblemRefinementInput(
            deep_analysis_output=request.deep_analysis_output,
            principal_context=request.principal_context,
            conversation_history=request.conversation_history,
            user_message=request.user_message,
            current_topic=request.current_topic,
            turn_count=request.turn_count,
        )
        
        # Call the Deep Analysis Agent's refine_analysis method
        result = await orchestrator.execute_agent_method(
            "A9_Deep_Analysis_Agent",
            "refine_analysis",
            {"input_model": refinement_input}
        )
        
        # Handle response - could be dict or ProblemRefinementResult
        if hasattr(result, "model_dump"):
            result_data = result.model_dump()
        elif isinstance(result, dict):
            result_data = result
        else:
            result_data = serialize(result)
        
        return wrap(result_data)
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Problem refinement error: {e}")
        # Return a graceful error that allows the chat to continue
        return wrap({
            "agent_message": f"I encountered an issue: {str(e)[:200]}. Let's continue.",
            "suggested_responses": ["Continue", "Skip this topic", "Proceed to solutions"],
            "current_topic": request.current_topic or "hypothesis_validation",
            "topic_complete": False,
            "topics_completed": [],
            "ready_for_solutions": False,
            "turn_count": request.turn_count + 1,
            "conversation_history": request.conversation_history,
            "exclusions": [],
            "external_context": [],
            "constraints": [],
            "validated_hypotheses": [],
            "invalidated_hypotheses": [],
        })


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


@router.post("/data-product-onboarding/run", response_model=Envelope, status_code=status.HTTP_202_ACCEPTED)
async def run_data_product_onboarding_workflow(
    request: DataProductOnboardingWorkflowApiRequest,
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> Envelope:
    request_id = _generate_request_id("data_product_onboarding")
    await _create_record(request_id, "data_product_onboarding", request.model_dump())
    asyncio.create_task(_run_data_product_onboarding_workflow(request_id, runtime, request))
    return wrap({"request_id": request_id, "state": "pending"})


@router.get("/data-product-onboarding/{request_id}/status", response_model=Envelope)
async def get_data_product_onboarding_status(request_id: str) -> Envelope:
    record = await _ensure_record(request_id, "data_product_onboarding")
    return wrap(record.to_dict())


@router.post("/data-product-onboarding/validate-kpi-queries", response_model=Envelope)
async def validate_kpi_queries(
    request: ValidateKPIQueriesRequest,
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> Envelope:
    """
    Validate KPI queries by executing them against the data source.
    
    This endpoint executes each KPI query and returns:
    - Success/failure status
    - First 5 rows of results (if successful)
    - Error messages and categorization (if failed)
    - Execution time metrics
    
    Phase 2: Query Testing implementation.
    """
    try:
        orchestrator = runtime.get_orchestrator()
        
        # Execute validation via Data Product Agent
        response: ValidateKPIQueriesResponse = await orchestrator.execute_agent_method(
            "A9_Data_Product_Agent",
            "validate_kpi_queries",
            request
        )
        
        return wrap(response.model_dump())
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"KPI query validation failed: {str(e)}"
        )


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

        detection_request_payload = {
            "request_id": request_id,
            "principal_context": principal_context,
            "business_processes": business_processes,
            "timeframe": timeframe,
            "comparison_type": comparison_type,
            "filters": request.filters or {},
        }
        if request.kpi_ids:
            detection_request_payload["kpi_ids"] = request.kpi_ids

        detection_request = SituationDetectionRequest(**detection_request_payload)
        response = await orchestrator.orchestrate_situation_detection(detection_request)
        
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
            # Merge principal's default_filters into the request filters
            if isinstance(principal_context, dict) and principal_context.get("default_filters"):
                deep_request_payload["filters"].update(principal_context["default_filters"])
        if request.scope.time_range:
            deep_request_payload["filters"]["time_range"] = request.scope.time_range
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
        # PRD-compliant: Prefer direct deep_analysis_output passed by frontend (agent-to-agent data exchange)
        # Fall back to workflow store lookup only if deep_analysis_output not provided
        deep_output: Optional[Dict[str, Any]] = request.deep_analysis_output
        if not deep_output and request.analysis_request_id:
            related_record = await _get_record(request.analysis_request_id)
            if related_record and related_record.result:
                deep_output = related_record.result

        solution_request_payload: Dict[str, Any] = {
            "request_id": request_id,
            "principal_id": request.principal_id,
            "problem_statement": request.problem_statement or "",
            "deep_analysis_output": deep_output,
            "constraints": request.constraints or {},
            "preferences": request.preferences or {},
        }
        # Add principal_context if provided (for Principal-driven approach with decision_style)
        if request.principal_context:
            solution_request_payload["principal_context"] = request.principal_context
        solution_request = SolutionFinderRequest(**solution_request_payload)

        response = await orchestrator.execute_agent_method(
            "A9_Solution_Finder_Agent",
            "recommend_actions",
            {"request": solution_request},
        )
        await _update_record(request_id, state="completed", result={"solutions": serialize(response)})
    except Exception as exc:  # pragma: no cover - defensive
        await _update_record(request_id, state="failed", error=str(exc))


async def _run_data_product_onboarding_workflow(
    request_id: str,
    runtime: AgentRuntime,
    request: DataProductOnboardingWorkflowApiRequest,
) -> None:
    try:
        orchestrator = runtime.get_orchestrator()
        workflow_request = DataProductOnboardingWorkflowRequest(
            request_id=request_id,
            principal_id=request.principal_id,
            data_product_id=request.data_product_id,
            source_system=request.source_system,
            database=request.database,
            schema=request.schema,
            tables=request.tables,
            inspection_depth=request.inspection_depth,
            include_samples=request.include_samples,
            environment=request.environment,
            connection_overrides=request.connection_overrides,
            contract_output_path=request.contract_output_path,
            data_product_name=request.data_product_name,
            data_product_domain=request.data_product_domain,
            data_product_description=request.data_product_description,
            data_product_tags=request.data_product_tags,
            contract_overrides=request.contract_overrides,
            additional_metadata=request.additional_metadata,
            owner_metadata=request.owner_metadata,
            kpi_entries=request.kpi_entries,
            overwrite_existing_kpis=request.overwrite_existing_kpis,
            business_process_mappings=request.business_process_mappings,
            overwrite_existing_mappings=request.overwrite_existing_mappings,
            candidate_owner_ids=request.candidate_owner_ids,
            fallback_roles=request.fallback_roles,
            business_process_context=request.business_process_context,
            qa_enabled=request.qa_enabled,
            qa_checks=request.qa_checks,
            qa_additional_context=request.qa_additional_context,
        )

        response = await orchestrator.orchestrate_data_product_onboarding(workflow_request)
        response_payload = serialize(response)
        status = response_payload.get("status", "success")

        if status == "success":
            state = "completed"
        elif status == "pending":
            state = "pending"
        else:
            state = "failed"

        await _update_record(
            request_id,
            state=state,
            result=response_payload,
        )
    except Exception as exc:  # pragma: no cover - defensive
        await _update_record(request_id, state="failed", error=str(exc))
