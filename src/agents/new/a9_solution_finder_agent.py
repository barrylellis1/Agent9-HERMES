"""
A9 Solution Finder Agent (MVP with optional LLM debate)
- Implements SolutionFinderProtocol
- Generates/evaluates solution options, builds trade-off matrix
- Emits a single HITL event per cycle (per PRD)
- Optional: persona debate via A9_LLM_Service_Agent when enabled in config
"""
from __future__ import annotations

import logging
import uuid
from typing import Dict, Any, Optional, List

from src.agents.agent_config_models import A9_Solution_Finder_Agent_Config
from src.agents.protocols.solution_finder_protocol import SolutionFinderProtocol
from src.agents.models.solution_finder_models import (
    SolutionFinderRequest,
    SolutionFinderResponse,
    SolutionOption,
    TradeOffCriterion,
    TradeOffMatrix,
)
from src.agents.a9_llm_service_agent import (
    A9_LLM_AnalysisRequest,
    A9_LLM_AnalysisResponse,
)


logger = logging.getLogger(__name__)

def _safe01(v: Any) -> Optional[float]:
    """Clamp to [0,1] if numeric; return None if not parseable."""
    try:
        if v is None:
            return None
        f = float(v)
        # reject NaN or infinities
        if f != f or f == float('inf') or f == float('-inf'):
            return None
        return max(0.0, min(1.0, f))
    except Exception:
        return None


class A9_Solution_Finder_Agent(SolutionFinderProtocol):
    """Solution Finder Agent MVP implementation (skeleton)."""

    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> "A9_Solution_Finder_Agent":
        inst = cls(config or {})
        await inst.connect()
        return inst

    def __init__(self, config: Dict[str, Any]):
        self.name = "A9_Solution_Finder_Agent"
        self.version = "0.1.0"
        self.config = A9_Solution_Finder_Agent_Config(**(config or {}))
        self.logger = logging.getLogger(self.__class__.__name__)
        self.deep_analysis_agent = None
        self.llm_service_agent = None
        self.orchestrator = None

    async def connect(self, orchestrator=None) -> bool:
        try:
            self.orchestrator = orchestrator
            if orchestrator is not None:
                try:
                    self.deep_analysis_agent = await orchestrator.get_agent("A9_Deep_Analysis_Agent")
                except Exception:
                    self.deep_analysis_agent = None
                try:
                    self.llm_service_agent = await orchestrator.get_agent("A9_LLM_Service_Agent")
                except Exception:
                    self.llm_service_agent = None
            self.logger.info("Solution Finder Agent connected")
            return True
        except Exception as e:
            self.logger.warning(f"Solution Finder Agent connect error: {e}")
            return False

    async def recommend_actions(self, request: SolutionFinderRequest) -> SolutionFinderResponse:
        req_id = request.request_id
        try:
            audit_log: List[Dict[str, Any]] = []

            # Decide path: LLM persona debate vs heuristic fallback
            # Try LLM when explicitly enabled OR orchestrator is present (safe fallback on failure)
            use_llm = bool(self.config.enable_llm_debate or (self.orchestrator is not None))
            options: List[SolutionOption] = []
            rationale = ""

            if use_llm and (self.orchestrator or self.llm_service_agent):
                try:
                    # Build compact debate prompt content using provided context
                    da_ctx = request.deep_analysis_output or {}
                    # Derive a robust problem statement
                    ps_raw = (getattr(request, "problem_statement", None) or "").strip()
                    ps = ps_raw
                    if not ps:
                        # Prefer SCQA summary from Deep Analysis
                        try:
                            scqa = None
                            if hasattr(da_ctx, "scqa_summary"):
                                scqa = getattr(da_ctx, "scqa_summary", None)
                            elif isinstance(da_ctx, dict):
                                scqa = da_ctx.get("scqa_summary")
                            if isinstance(scqa, str) and scqa.strip():
                                ps = scqa.strip()
                        except Exception:
                            pass
                    if not ps:
                        # Fallback to KPI name from plan if available
                        try:
                            plan = None
                            if hasattr(da_ctx, "plan"):
                                plan = getattr(da_ctx, "plan", None)
                            elif isinstance(da_ctx, dict):
                                plan = da_ctx.get("plan")
                            kpi_name = None
                            if plan is not None:
                                if isinstance(plan, dict):
                                    kpi_name = plan.get("kpi_name")
                                else:
                                    kpi_name = getattr(plan, "kpi_name", None)
                            if kpi_name:
                                ps = f"KPI: {kpi_name} — generate actionable solution options."
                        except Exception:
                            pass
                    if not ps:
                        ps = "Problem statement not provided"

                    # Align with active situation context to avoid KPI mismatch
                    try:
                        sctx = getattr(request, "situation_context", None)
                        sctx_desc = sctx.get("description") if isinstance(sctx, dict) else getattr(sctx, "description", None)
                        sctx_kpi = sctx.get("kpi_name") if isinstance(sctx, dict) else getattr(sctx, "kpi_name", None)
                        if isinstance(sctx_desc, str) and sctx_desc.strip():
                            ps = sctx_desc.strip()
                        elif (not ps_raw) and sctx_kpi:
                            ps = f"KPI: {sctx_kpi} — generate actionable solution options."
                    except Exception:
                        pass
                    # Allow per-request persona override via preferences
                    try:
                        prefs = getattr(request, "preferences", None) or {}
                    except Exception:
                        prefs = {}
                    personas_override: List[str] = []
                    try:
                        cand = prefs.get("personas") if isinstance(prefs, dict) else None
                        if isinstance(cand, list):
                            personas_override = [str(p) for p in cand if p]
                    except Exception:
                        personas_override = []
                    personas_list = personas_override or (self.config.expert_personas or [])
                    personas = ", ".join(personas_list)

                    debate_spec = (
                        "You are a panel of expert personas (" + personas + ") debating solutions.\n"
                        "Given the problem and data context, propose 2-3 concrete solution options with normalized metrics (0-1).\n"
                        "Return STRICT JSON with keys: options (array of {id,title,description,expected_impact,cost,risk,rationale}),\n"
                        "consensus_rationale (string), transcript (array of {persona,opinion}), and transcript_detailed (array).\n"
                        "Each item in transcript_detailed should include: {persona, claim, reasoning_outline (array of bullet points),\n"
                        "counters (array), concession (string|nullable), revised_position (string|nullable), vote (0-1 or yes/no)}.\n"
                    )
                    # Optional user-supplied context to guide the debate
                    try:
                        user_ctx = prefs.get("user_context") if isinstance(prefs, dict) else None
                    except Exception:
                        user_ctx = None

                    content = {
                        "problem": ps,
                        "deep_analysis_context": da_ctx,
                        "debate_spec": debate_spec,
                        "user_context": user_ctx,
                    }
                    import json as _json
                    analysis_payload = _json.dumps(content)

                    analysis_req = A9_LLM_AnalysisRequest(
                        request_id=req_id,
                        principal_id=getattr(request, "principal_id", None),
                        timestamp=getattr(request, "timestamp", None),
                        principal_context=getattr(request, "principal_context", None),
                        situation_context=getattr(request, "situation_context", None),
                        business_context=getattr(request, "business_context", None),
                        content=analysis_payload,
                        analysis_type="custom",
                        context="Respond ONLY with valid JSON matching the required keys and numeric fields in [0,1].",
                    )

                    # Record the analysis request components in audit for UI/debug
                    try:
                        def _to_obj(x):
                            try:
                                if hasattr(x, "model_dump"):
                                    return x.model_dump()
                                if hasattr(x, "__dict__"):
                                    return dict(x.__dict__)
                            except Exception:
                                return x
                            return x
                        audit_log.append({
                            "event": "llm_debate_analysis_req",
                            "principal_context": _to_obj(getattr(analysis_req, "principal_context", None)),
                            "situation_context": _to_obj(getattr(analysis_req, "situation_context", None)),
                            "business_context": _to_obj(getattr(analysis_req, "business_context", None)),
                            # Use parsed content dict for readability
                            "content": content,
                        })
                    except Exception:
                        pass

                    # Prefer orchestrator routing per LLM PRD; fallback to direct agent if missing
                    if self.orchestrator is not None:
                        llm_resp = await self.orchestrator.execute_agent_method(
                            "A9_LLM_Service_Agent", "analyze", {"request": analysis_req}
                        )
                    else:
                        llm_resp = await self.llm_service_agent.analyze(analysis_req)  # type: ignore

                    # Extract options and rationale safely
                    llm_ok = getattr(llm_resp, "status", "error") == "success"
                    model_used = getattr(llm_resp, "model_used", None)
                    audit_log.append({
                        "event": "llm_debate_completed",
                        "status": getattr(llm_resp, "status", None),
                        "model_used": model_used,
                    })

                    parsed = getattr(llm_resp, "analysis", None) if llm_ok else None
                    # Fallback if non-JSON returned
                    if isinstance(parsed, dict) and parsed.get("options"):
                        for idx, o in enumerate(parsed.get("options", []) or []):
                            try:
                                options.append(
                                    SolutionOption(
                                        id=str(o.get("id") or f"opt{idx+1}"),
                                        title=str(o.get("title") or f"Option {idx+1}"),
                                        description=o.get("description"),
                                        expected_impact=_safe01(o.get("expected_impact")),
                                        cost=_safe01(o.get("cost")),
                                        risk=_safe01(o.get("risk")),
                                        rationale=o.get("rationale"),
                                    )
                                )
                            except Exception:
                                continue
                        rationale = str(parsed.get("consensus_rationale") or "LLM consensus rationale")
                        # Add transcript snippet to audit (limit size)
                        if parsed.get("transcript"):
                            audit_log.append({
                                "event": "llm_debate_transcript",
                                "sample": (parsed.get("transcript") or [])[:3],
                            })
                            # Include a truncated full transcript for UI rendering
                            try:
                                _full_t = parsed.get("transcript") or []
                                if isinstance(_full_t, list) and _full_t:
                                    audit_log.append({
                                        "event": "llm_debate_transcript_full",
                                        "transcript": _full_t[:20],
                                    })
                            except Exception:
                                pass
                        # Record detailed transcript if provided
                        try:
                            _det = parsed.get("transcript_detailed")
                            if isinstance(_det, list) and _det:
                                audit_log.append({
                                    "event": "llm_debate_transcript_detailed",
                                    "transcript_detailed": _det[:20],
                                })
                        except Exception:
                            pass

                except Exception as le:
                    # LLM path failed; fall back to heuristic
                    self.logger.info(f"LLM debate path failed, falling back to heuristic: {le}")
                    audit_log.append({"event": "llm_debate_error", "error": str(le)})

            # Heuristic fallback or augmentation if LLM didn't yield options
            if not options:
                options = [
                    SolutionOption(id="opt1", title="Tighten spend controls", expected_impact=0.6, cost=0.3, risk=0.3),
                    SolutionOption(id="opt2", title="Optimize pricing", expected_impact=0.7, cost=0.5, risk=0.4),
                ]
                if not rationale:
                    rationale = "MVP heuristic ranking by weighted impact/cost/risk."

            criteria = request.evaluation_criteria or [
                TradeOffCriterion(name="impact", weight=self.config.weight_impact),
                TradeOffCriterion(name="cost", weight=self.config.weight_cost),
                TradeOffCriterion(name="risk", weight=self.config.weight_risk),
            ]
            ranked = self._rank_options(options, criteria)
            recommendation = ranked[0] if ranked else None

            # Normalize nested models to plain dict payloads to avoid cross-module identity issues
            try:
                criteria_payload = [
                    (c.model_dump() if hasattr(c, "model_dump") else {"name": getattr(c, "name", None), "weight": getattr(c, "weight", None)})
                    for c in (criteria or [])
                ]
            except Exception:
                criteria_payload = [
                    {"name": "impact", "weight": float(self.config.weight_impact)},
                    {"name": "cost", "weight": float(self.config.weight_cost)},
                    {"name": "risk", "weight": float(self.config.weight_risk)},
                ]
            try:
                options_payload = [
                    (o.model_dump() if hasattr(o, "model_dump") else {
                        "id": getattr(o, "id", None),
                        "title": getattr(o, "title", None),
                        "description": getattr(o, "description", None),
                        "expected_impact": getattr(o, "expected_impact", None),
                        "cost": getattr(o, "cost", None),
                        "risk": getattr(o, "risk", None),
                        "rationale": getattr(o, "rationale", None),
                    })
                    for o in (ranked or [])
                ]
            except Exception:
                options_payload = []
            try:
                recommendation_payload = recommendation.model_dump() if (recommendation is not None and hasattr(recommendation, "model_dump")) else (recommendation if isinstance(recommendation, dict) else None)
            except Exception:
                recommendation_payload = None
            matrix_payload = {"criteria": criteria_payload, "options": options_payload}

            # Single HITL event required per PRD
            return SolutionFinderResponse.success(
                request_id=req_id,
                options_ranked=options_payload,
                tradeoff_matrix=matrix_payload,
                recommendation=recommendation_payload,
                recommendation_rationale=rationale,
                human_action_required=True,
                human_action_type="approval",
                human_action_context={
                    "summary": "Review ranked options and approve or select an alternative.",
                },
                audit_log=[{"event": "ranked_options", "count": len(options_payload)}] + audit_log,
            )
        except Exception as e:
            return SolutionFinderResponse.error(request_id=req_id, error_message=str(e))

    async def evaluate_options(self, request: SolutionFinderRequest) -> SolutionFinderResponse:
        req_id = request.request_id
        try:
            options = request.extra.get("options", []) if request.extra else []
            # Convert dicts to model instances if necessary
            normalized: List[SolutionOption] = []
            for o in options:
                if isinstance(o, SolutionOption):
                    normalized.append(o)
                elif isinstance(o, dict):
                    normalized.append(SolutionOption(**o))
            criteria = request.evaluation_criteria or [
                TradeOffCriterion(name="impact", weight=self.config.weight_impact),
                TradeOffCriterion(name="cost", weight=self.config.weight_cost),
                TradeOffCriterion(name="risk", weight=self.config.weight_risk),
            ]
            ranked = self._rank_options(normalized, criteria)
            matrix = TradeOffMatrix(criteria=criteria, options=ranked)
            recommendation = ranked[0] if ranked else None
            return SolutionFinderResponse.success(
                request_id=req_id,
                options_ranked=ranked,
                tradeoff_matrix=matrix,
                recommendation=recommendation,
                recommendation_rationale="Heuristic ranking applied.",
                human_action_required=True,
                human_action_type="approval",
                human_action_context={"summary": "Approve or override the recommended option."},
            )
        except Exception as e:
            return SolutionFinderResponse.error(request_id=req_id, error_message=str(e))

    def _rank_options(self, options: List[SolutionOption], criteria: List[TradeOffCriterion]) -> List[SolutionOption]:
        # Simple weighted score: impact positive, cost and risk negative
        def score(o: SolutionOption) -> float:
            imp = o.expected_impact or 0.0
            cost = o.cost or 0.0
            risk = o.risk or 0.0
            w = {c.name: c.weight for c in criteria}
            return (w.get("impact", 0.0) * imp) - (w.get("cost", 0.0) * cost) - (w.get("risk", 0.0) * risk)

        return sorted(options, key=score, reverse=True)


async def create_solution_finder_agent(config: Dict[str, Any] = None) -> A9_Solution_Finder_Agent:
    return await A9_Solution_Finder_Agent.create(config or {})
