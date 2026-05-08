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
    client_id: Optional[str] = Field(None, description="Client/tenant ID — limits KPI evaluation to this client's KPIs")


class DeepAnalysisScope(BaseModel):
    kpi_id: str = Field(..., description="Target KPI identifier")
    time_range: Optional[Dict[str, Any]] = Field(None, description="Custom time range with start/end")
    timeframe: Optional[str] = Field(None, description="Timeframe token matching SA selection (e.g., 'year_to_date', 'current_quarter')")


class DeepAnalysisWorkflowRequest(BaseModel):
    principal_id: str = Field(..., description="ID of the requesting principal")
    situation_id: Optional[str] = Field(None, description="Related situation identifier")
    scope: DeepAnalysisScope = Field(..., description="Scope for the deep analysis")
    hypotheses: Optional[List[str]] = Field(None, description="Optional hypotheses to evaluate")
    include_supporting_evidence: bool = Field(True, description="Whether to compute supporting evidence artifacts")
    analysis_mode: Optional[str] = Field(default="problem", description="Analysis framing: 'problem' or 'opportunity'")


class SolutionWorkflowRequest(BaseModel):
    principal_id: str = Field(..., description="ID of the requesting principal")
    situation_id: Optional[str] = Field(None, description="Situation ID from SA — forwarded to VA on approval")
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
    contract_output_path: Optional[str] = Field(None, description="Deprecated — Supabase is canonical registry backend")
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
    record = await _get_record(request_id)
    if record is None or record.workflow_type != "situations":
        return wrap({"request_id": request_id, "state": "not_found", "error": "Workflow request not found"})
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
        
        # --- On turn 0: run Market Analysis in parallel to seed external_context ---
        initial_external_context: List[str] = []
        pending_signals: Optional[List[Dict]] = None

        if request.turn_count == 0:
            # Read market signals from DA output (MA already ran at end of DA workflow)
            _da_out = request.deep_analysis_output or {}
            _raw_signals = _da_out.get("market_signals") or []
            if _raw_signals:
                initial_external_context = [
                    f"Market signal: {s.get('title', '')} — {s.get('summary', '')}"
                    for s in _raw_signals
                ]
                pending_signals = _raw_signals

            refinement_input = ProblemRefinementInput(
                deep_analysis_output=request.deep_analysis_output,
                principal_context=request.principal_context,
                conversation_history=request.conversation_history,
                user_message=request.user_message,
                current_topic=request.current_topic,
                turn_count=request.turn_count,
                initial_external_context=initial_external_context,
            )
        else:
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

        # Attach market_signals on turn 0 (overrides model default of None)
        if pending_signals:
            result_data["market_signals"] = pending_signals

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
async def approve_solution(
    request_id: str, request: ActionRequest,
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> Envelope:
    return await _record_solution_action(request_id, "approve", request, runtime)


@router.post("/solutions/{request_id}/actions/request-changes", response_model=Envelope)
async def request_solution_changes(request_id: str, request: ActionRequest) -> Envelope:
    return await _record_solution_action(request_id, "request-changes", request)


@router.post("/solutions/{request_id}/actions/iterate", response_model=Envelope)
async def iterate_solution(request_id: str, request: ActionRequest) -> Envelope:
    return await _record_solution_action(request_id, "iterate", request)


# ---------------------------------------------------------------------------
# Briefing Q&A
# ---------------------------------------------------------------------------

class BriefingQARequest(BaseModel):
    question: str = Field(..., description="Question about the decision briefing")
    principal_id: str = Field(..., description="ID of the principal asking the question")
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Prior Q&A turns as [{role, content}]",
    )


class BriefingQAResponse(BaseModel):
    answer: str
    transparency_tier: int = Field(..., description="1=direct data, 2=calculated, 3=inferred, 4=opinion")
    tier_label: str
    sources: List[str] = Field(default_factory=list)
    suggested_followups: List[str] = Field(default_factory=list)


def _detect_transparency_tier(question: str):
    q = question.lower()
    if any(kw in q for kw in ["recommend", "should we", "what would you", "your opinion", "best option", "advise"]):
        return 4, "Opinion / Recommendation"
    if any(kw in q for kw in ["why", "implication", "impact of", "what does it mean", "suggest about", "indicate", "tell us"]):
        return 3, "Inferred from analysis"
    if any(kw in q for kw in ["compare", "difference", "higher", "lower", "rank", "how much", "how many", "percentage", "ratio"]):
        return 2, "Calculated from analysis data"
    return 1, "Direct from analysis data"


def _build_briefing_context(record: WorkflowRecord) -> str:
    result = record.result or {}
    solutions = result.get("solutions") or {}
    payload = record.payload or {}
    sections: List[str] = []

    problem = (
        payload.get("problem_statement")
        or (payload.get("deep_analysis_output") or {}).get("scqa_summary")
        or "Not available"
    )
    sections.append(f"## Problem Statement\n{problem}")

    da = payload.get("deep_analysis_output") or {}
    exec_da = da.get("execution", da)
    kpi = exec_da.get("kpi_name") or da.get("kpi_id") or ""
    if kpi:
        sections.append(f"## KPI Under Analysis\n{kpi}")
    scqa = exec_da.get("scqa_summary") or ""
    if scqa:
        sections.append(f"## SCQA Summary\n{scqa}")
    kt = exec_da.get("kt_is_is_not") or {}
    where_is = (kt.get("where_is") or [])[:5]
    if where_is:
        driver_lines = [f"- {d.get('key','?')}: delta {d.get('delta',0):+.0f}" if isinstance(d, dict) else f"- {d}" for d in where_is]
        sections.append("## Key Drivers (Where IS)\n" + "\n".join(driver_lines))
    benchmarks = (kt.get("benchmark_segments") or [])[:3]
    if benchmarks:
        bench_lines = [f"- {b.get('dimension','')}: {b.get('key','')} (replication potential: {b.get('replication_potential','?')})" if isinstance(b, dict) else f"- {b}" for b in benchmarks]
        sections.append("## Internal Benchmarks\n" + "\n".join(bench_lines))

    stage1 = solutions.get("stage_1_persona_hypotheses") or solutions.get("stage_1_hypotheses") or {}
    if stage1:
        hyp_lines = []
        for persona, hyp in stage1.items():
            if isinstance(hyp, dict):
                h = hyp.get("hypothesis") or hyp.get("proposed_option", {}).get("title", "")
                if h:
                    hyp_lines.append(f"- [{persona}] {h}")
        if hyp_lines:
            sections.append("## Stage 1 Hypotheses\n" + "\n".join(hyp_lines))

    options = solutions.get("options_ranked") or solutions.get("options") or []
    if options:
        opt_lines = []
        for opt in options:
            if not isinstance(opt, dict):
                continue
            title = opt.get("title", "Unnamed option")
            desc = opt.get("description") or opt.get("rationale") or ""
            impact_est = opt.get("impact_estimate") or {}
            rng = impact_est.get("recovery_range") or {} if isinstance(impact_est, dict) else {}
            low, high = rng.get("low") if isinstance(rng, dict) else None, rng.get("high") if isinstance(rng, dict) else None
            unit = impact_est.get("unit", "") if isinstance(impact_est, dict) else ""
            impact = f" | Impact: {low}–{high} {unit}".strip() if (low is not None and high is not None) else ""
            opt_lines.append(f"### {title}{impact}\n{desc}")
        if opt_lines:
            sections.append("## Solution Options\n\n" + "\n\n".join(opt_lines))

    blind_spots = solutions.get("blind_spots") or []
    if blind_spots:
        sections.append("## Blind Spots\n" + "\n".join(f"- {b}" for b in blind_spots))

    tensions = solutions.get("unresolved_tensions") or []
    if tensions:
        t_lines = [f"- {t.get('tension', str(t))}" if isinstance(t, dict) else f"- {t}" for t in tensions]
        sections.append("## Unresolved Tensions\n" + "\n".join(t_lines))

    return "\n\n".join(sections) if sections else "No briefing context available."


@router.post("/solutions/{request_id}/qa", response_model=Envelope)
async def briefing_qa(
    request_id: str,
    request: BriefingQARequest,
    runtime: AgentRuntime = Depends(get_agent_runtime),
) -> Envelope:
    """Interactive Q&A for the Decision Briefing — answers questions about analysis, options, recommendation."""
    import logging as _lg
    _log = _lg.getLogger("workflows.solutions.qa")

    record = await _get_record(request_id)
    if record is None or record.workflow_type != "solutions":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solutions workflow '{request_id}' not found.",
        )

    tier, tier_label = _detect_transparency_tier(request.question)
    briefing_context = _build_briefing_context(record)

    history_block = ""
    if request.conversation_history:
        history_lines = [
            f"{turn.get('role', 'user').capitalize()}: {turn.get('content', '')}"
            for turn in request.conversation_history[-6:]
        ]
        history_block = "\n\n### Previous Q&A\n" + "\n".join(history_lines)

    from src.llm_services.claude_service import get_claude_model_for_task, ClaudeTaskType
    model = get_claude_model_for_task(ClaudeTaskType.NLP_PARSING if tier <= 2 else ClaudeTaskType.BRIEFING)

    prompt = (
        "You are an executive briefing analyst. Answer the principal's question based ONLY "
        "on the briefing context below. Be concise and direct.\n\n"
        f"### Briefing Context\n{briefing_context}"
        f"{history_block}\n\n"
        f"### Principal's Question\n{request.question}\n\n"
        "### Instructions\n"
        "- Answer in 2–4 sentences.\n"
        "- After the answer, on a new line starting with 'SOURCES:', list 1–3 labels from: "
        "'Deep Analysis', 'Stage 1 hypotheses', 'Solution options', 'Recommendation', 'Blind spots', 'Unresolved tensions'.\n"
        "- After sources, on a new line starting with 'FOLLOWUPS:', list 3 suggested follow-up questions separated by ' | '.\n"
        "- If the answer is not in the briefing context, say 'This information is not available in the current briefing.'"
    )

    try:
        orchestrator = runtime.get_orchestrator()
        from src.agents.new.a9_llm_service_agent import A9_LLM_Request

        llm_req = A9_LLM_Request(
            request_id=str(uuid.uuid4()),
            principal_id=request.principal_id,
            prompt=prompt,
            model=model,
            max_tokens=800,
            operation="generate",
        )
        llm_resp = await orchestrator.execute_agent_method(
            "A9_LLM_Service_Agent", "generate", {"request": llm_req}
        )

        raw = (getattr(llm_resp, "content", None) or (llm_resp.get("content") if isinstance(llm_resp, dict) else None) or str(llm_resp))
        answer_text = raw
        sources: List[str] = []
        followups: List[str] = []

        if "SOURCES:" in raw:
            a_part, rest = raw.split("SOURCES:", 1)
            answer_text = a_part.strip()
            if "FOLLOWUPS:" in rest:
                s_part, f_part = rest.split("FOLLOWUPS:", 1)
                sources = [s.strip() for s in s_part.strip().split(",") if s.strip()]
                followups = [f.strip() for f in f_part.strip().split("|") if f.strip()]
            else:
                sources = [s.strip() for s in rest.strip().split(",") if s.strip()]
        elif "FOLLOWUPS:" in raw:
            a_part, f_part = raw.split("FOLLOWUPS:", 1)
            answer_text = a_part.strip()
            followups = [f.strip() for f in f_part.strip().split("|") if f.strip()]

        if not followups:
            followups = ["What are the key drivers?", "Which option has the lowest risk?", "What blind spots should we watch?"]

        return wrap(BriefingQAResponse(
            answer=answer_text, transparency_tier=tier, tier_label=tier_label,
            sources=sources, suggested_followups=followups[:3],
        ).model_dump())

    except Exception as exc:
        _log.warning("Briefing Q&A LLM call failed, returning fallback: %s", exc)
        return wrap(BriefingQAResponse(
            answer=f"Q&A service temporarily unavailable. Context: {briefing_context[:500]}",
            transparency_tier=tier, tier_label=tier_label,
            sources=["Briefing data (fallback)"],
            suggested_followups=["What are the key drivers?", "Which option is recommended?", "What are the main risks?"],
        ).model_dump())


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


async def _record_solution_action(
    request_id: str, action_type: str, request: ActionRequest,
    runtime: Optional["AgentRuntime"] = None,
) -> Envelope:
    record = await _ensure_record(request_id, "solutions")
    entry = {
        "action": action_type,
        "comment": request.comment,
        "payload": serialize(request.payload) if request.payload else None,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # VA registration on approve — reconstruct from workflow record
    if action_type == "approve" and runtime is not None:
        try:
            import logging as _lg
            _va_log = _lg.getLogger("workflows.solutions.approve")
            orchestrator = runtime.get_orchestrator()

            action_payload = request.payload or {}
            solution_option_id = action_payload.get("solution_option_id")

            # Resolve the approved option from the SF result
            result_solutions = (record.result or {}).get("solutions") or {}
            options = result_solutions.get("options_ranked") or []
            matched = next(
                (o for o in options if o.get("id") == solution_option_id),
                options[0] if options else {},
            )

            # Build description
            sol_desc = matched.get("title", "Approved solution")
            if matched.get("description"):
                sol_desc = f"{sol_desc}: {matched['description']}"

            # Extract impact bounds
            impact_est = matched.get("impact_estimate") or {}
            recovery = impact_est.get("recovery_range") or {}
            impact_lower = float(recovery.get("low") or matched.get("expected_impact") or 0.0)
            impact_upper = float(recovery.get("high") or matched.get("expected_impact") or 0.0)

            # Extract upstream context from workflow payload
            wf_payload = record.payload or {}
            situation_id = wf_payload.get("situation_id") or action_payload.get("situation_id") or ""
            da_output = wf_payload.get("deep_analysis_output") or {}
            kpi_id = da_output.get("kpi_name") or ""

            # DA benchmark segments for DiD control group (Phase 7C)
            kt = da_output.get("kt_is_is_not") or {}
            all_benchmarks = kt.get("benchmark_segments") or []
            control_segments = [s for s in all_benchmarks if s.get("benchmark_type") == "control_group"] or None
            benchmark_segments = all_benchmarks or None

            # Pre-approval KPI value for slope calculation
            aggregates = da_output.get("aggregates") or {}
            pre_approval_kpi_value = aggregates.get("comparison_value") or aggregates.get("previous_value")

            # Market signals from SF result
            mkt_intel = result_solutions.get("market_intelligence")
            ma_signals = None
            if isinstance(mkt_intel, list):
                ma_signals = [
                    s.get("summary") or s.get("title") or str(s)
                    for s in mkt_intel if s
                ] or None
            elif isinstance(mkt_intel, dict):
                signals_list = mkt_intel.get("signals") or mkt_intel.get("market_signals") or []
                ma_signals = [
                    s.get("summary") or s.get("title") or str(s)
                    for s in signals_list if s
                ] or None

            from src.agents.models.value_assurance_models import RegisterSolutionRequest

            va_req = RegisterSolutionRequest(
                request_id=str(uuid.uuid4()),
                principal_id=wf_payload.get("principal_id", ""),
                situation_id=situation_id,
                kpi_id=kpi_id,
                solution_description=sol_desc,
                expected_impact_lower=impact_lower,
                expected_impact_upper=impact_upper,
                control_group_segments=control_segments,
                benchmark_segments=benchmark_segments,
                pre_approval_kpi_value=pre_approval_kpi_value,
                ma_market_signals=ma_signals,
            )

            va_resp = await orchestrator.execute_agent_method(
                "A9_Value_Assurance_Agent",
                "register_solution",
                {"request": va_req},
            )
            va_solution_id = getattr(va_resp, "solution_id", None)
            _va_log.info("VA registered: solution_id=%s kpi=%s", va_solution_id, kpi_id)

            # Append VA solution_id to the action entry for audit trail
            entry["va_solution_id"] = va_solution_id

        except Exception as _va_exc:
            import logging as _lg
            _lg.getLogger("workflows.solutions.approve").warning(
                "VA register_solution failed (non-fatal): %s", _va_exc,
            )

    record.actions.append(entry)
    await _update_record(request_id, actions=record.actions)
    return wrap({"request_id": request_id, "actions": record.actions})


async def _run_situations_workflow(request_id: str, runtime: AgentRuntime, request: SituationWorkflowRequest) -> None:
    try:
        orchestrator = runtime.get_orchestrator()
        pc_lookup_args: dict = {"principal_id": request.principal_id}
        if request.client_id:
            pc_lookup_args["client_id"] = request.client_id
        principal_resp = await orchestrator.execute_agent_method(
            "A9_Principal_Context_Agent",
            "get_principal_context_by_id",
            pc_lookup_args,
        )

        principal_context = None
        if isinstance(principal_resp, dict):
            principal_context = principal_resp.get("context") or principal_resp.get("principal_context") or principal_resp
        elif hasattr(principal_resp, "context"):
            principal_context = serialize(principal_resp.context)
        if principal_context is None:
            raise ValueError("Unable to resolve principal context")

        business_processes = (
            request.business_processes
            or principal_context.get("business_processes")
            or principal_context.get("business_process_ids")  # fallback for Supabase column name
            or []
        )
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
        if request.client_id:
            detection_request_payload["client_id"] = request.client_id

        detection_request = SituationDetectionRequest(**detection_request_payload)
        response = await orchestrator.orchestrate_situation_detection(detection_request)
        
        await _update_record(
            request_id,
            state="completed",
            result={"situations": serialize(response)},
        )

        # Persist situations and opportunities to Supabase (non-blocking)
        try:
            from src.database.situations_store import SituationsStore
            import logging as _lg
            _situations_logger = _lg.getLogger("workflows.situations")
            store = SituationsStore()
            if store.enabled:
                _situations = response.situations if hasattr(response, "situations") else (response.get("situations") or [])
                _opportunities = response.opportunities if hasattr(response, "opportunities") else (response.get("opportunities") or [])
                for situation in _situations:
                    await store.upsert_situation(situation)
                for opportunity in _opportunities:
                    await store.upsert_opportunity(opportunity)
                _situations_logger.info(
                    "Persisted %d situations and %d opportunities to Supabase",
                    len(_situations),
                    len(_opportunities),
                )
        except Exception as e:
            import logging as _lg
            _lg.getLogger("workflows.situations").warning(
                "Supabase situation persistence failed (non-fatal): %s", e
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
            "timeframe": request.scope.timeframe or "current_quarter",
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
        deep_request_payload["analysis_mode"] = request.analysis_mode or "problem"
        deep_request = DeepAnalysisRequest(**deep_request_payload)

        # Use Orchestrator to run the full Deep Analysis workflow (Plan + Execute)
        response = await orchestrator.orchestrate_deep_analysis(deep_request)

        # Run Market Analysis to enrich DA results with external market context
        market_signals = None
        try:
            from src.agents.models.market_analysis_models import MarketAnalysisRequest
            _kpi_name = request.scope.kpi_id or "KPI"
            _scqa = getattr(response, "scqa_summary", None) or str(_kpi_name)
            _industry = None
            if principal_context and isinstance(principal_context, dict):
                _industry = principal_context.get("industry")
            _ma_req = MarketAnalysisRequest(
                session_id=f"da-{request_id}",
                kpi_name=str(_kpi_name),
                kpi_context=str(_scqa)[:500],
                industry=_industry,
                principal_id=request.principal_id,
                max_signals=4,
            )
            _ma_resp = await orchestrator.execute_agent_method(
                "A9_Market_Analysis_Agent",
                "analyze_market",
                {"request": _ma_req},
            )
            if _ma_resp and hasattr(_ma_resp, "signals") and _ma_resp.signals:
                market_signals = [s.model_dump() for s in _ma_resp.signals]
        except Exception as _mae:
            import logging as _lg
            import traceback as _tb
            _lg.getLogger("workflows.deep_analysis").warning("[DA] MA enrichment skipped: %s\n%s", _mae, _tb.format_exc())

        # Maintain backward compatibility with UI result structure
        # UI expects { "plan": ..., "execution": ... }
        # The orchestrator response (DeepAnalysisResponse) contains the plan
        plan_serialized = serialize(response.plan) if response.plan else None
        execution_serialized = serialize(response)

        result_payload = {
            "plan": plan_serialized,
            "execution": execution_serialized,
            "market_signals": market_signals,
        }
        
        status = "failed" if response.status == "error" else "completed"
        error_msg = response.error_message if response.status == "error" else None
        
        if status == "failed":
             await _update_record(request_id, state="failed", error=error_msg)
        else:
             await _update_record(request_id, state="completed", result=result_payload)

        # Update situation status to ANALYZING when DA completes (non-blocking)
        try:
            from src.database.situations_store import SituationsStore
            _store = SituationsStore()
            if _store.enabled and request.situation_id:
                await _store.update_status(
                    request.situation_id,
                    "ANALYZING",
                    da_request_id=request_id,
                )
        except Exception as _se:
            import logging as _lg
            _lg.getLogger("workflows.deep_analysis").warning(
                "Supabase status update failed (non-fatal): %s", _se
            )

    except Exception as exc:  # pragma: no cover - defensive
        import traceback as _tb
        import logging as _lg
        _lg.getLogger("workflows.deep_analysis").error("TRACEBACK:\n%s", _tb.format_exc())
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

        # Use Orchestrator to run the Solution Finding workflow
        response = await orchestrator.orchestrate_solution_finding(solution_request)
        
        status = "failed" if response.status == "error" else "completed"
        error_msg = response.message if response.status == "error" else None
        
        if status == "failed":
            await _update_record(request_id, state="failed", error=error_msg)
        else:
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
