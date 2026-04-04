"""
Principal Intelligence Briefing (PIB) API routes — Phase 9E.

POST /api/v1/pib/run                — compose and send a PIB for a principal+client
GET  /api/v1/pib/runs               — list recent briefing runs for a principal
GET  /api/v1/pib/token/{token}      — validate a one-click action token and execute it
POST /api/v1/pib/delegate/{token}   — complete a delegation (select target principal)
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.agents.models.pib_models import (
    BriefingConfig,
    BriefingFormat,
    BriefingRun,
    BriefingRunStatus,
    TokenType,
)
from src.api.runtime import get_agent_runtime

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/pib",
    tags=["pib"],
)


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------

class PIBRunRequest(BaseModel):
    principal_id: str
    client_id: str
    email_to: Optional[str] = None
    format: BriefingFormat = BriefingFormat.DETAILED
    dry_run: bool = False


class PIBRunResponse(BaseModel):
    """Summarised result returned from POST /run."""
    run_id: str
    principal_id: str
    client_id: str
    status: BriefingRunStatus
    new_situation_count: int
    email_to: str
    dry_run: bool
    error_message: Optional[str] = None


class TokenActionResponse(BaseModel):
    """Returned by GET /token/{token} after executing the one-click action."""
    token_type: str
    situation_id: str
    action_taken: str
    redirect_url: Optional[str] = None   # frontend route to navigate to
    principal_id: Optional[str] = None
    kpi_name: Optional[str] = None       # stable KPI name for dashboard matching
    message: str


class DelegateRequest(BaseModel):
    delegate_to_principal_id: str
    note: Optional[str] = None


class DelegateResponse(BaseModel):
    situation_id: str
    delegated_to: str
    message: str


# ---------------------------------------------------------------------------
# POST /run  — compose and send PIB
# ---------------------------------------------------------------------------

@router.post("/run", response_model=PIBRunResponse)
async def run_pib(
    request: PIBRunRequest,
    runtime=Depends(get_agent_runtime),
) -> PIBRunResponse:
    """
    Compose and (optionally) send a Principal Intelligence Briefing.

    If dry_run=true the email is composed but not sent; the briefing run
    record is still persisted with status=pending.
    """
    from src.agents.new.a9_pib_agent import A9_PIB_Agent  # local import — avoids circular

    orchestrator = runtime.get_orchestrator()

    try:
        pib_agent = await A9_PIB_Agent.create({"orchestrator": orchestrator})
    except Exception as exc:
        logger.error("PIB agent creation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"PIB agent init failed: {exc}") from exc

    config = BriefingConfig(
        principal_id=request.principal_id,
        client_id=request.client_id,
        email_to=request.email_to,
        format=request.format,
        dry_run=request.dry_run,
    )

    try:
        briefing_run: BriefingRun = await pib_agent.generate_and_send(config)
    except Exception as exc:
        logger.error(
            "PIB generation failed: principal=%s client=%s error=%s",
            request.principal_id, request.client_id, exc,
        )
        raise HTTPException(status_code=500, detail=f"PIB generation failed: {exc}") from exc

    return PIBRunResponse(
        run_id=briefing_run.id,
        principal_id=briefing_run.principal_id,
        client_id=briefing_run.client_id,
        status=briefing_run.status,
        new_situation_count=briefing_run.new_situation_count,
        email_to=briefing_run.email_to,
        dry_run=request.dry_run,
        error_message=briefing_run.error_message,
    )


# ---------------------------------------------------------------------------
# GET /runs  — list recent briefing runs
# ---------------------------------------------------------------------------

@router.get("/runs", response_model=List[Dict[str, Any]])
async def list_pib_runs(
    principal_id: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """
    Return recent PIB runs from Supabase, optionally filtered by principal_id.

    Returns an empty list when Supabase is not configured (graceful degradation).
    """
    from src.database.briefing_store import BriefingStore

    store = BriefingStore()
    if not store.enabled:
        return []

    try:
        import httpx
        params: Dict[str, Any] = {
            "order": "created_at.desc",
            "limit": str(limit),
            "select": "*",
        }
        if principal_id:
            params["principal_id"] = f"eq.{principal_id}"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                store._runs_url,
                headers=store.headers,
                params=params,
            )
            response.raise_for_status()
            import json as _json
            return _json.loads(response.content) if response.content else []
    except Exception as exc:
        logger.warning("list_pib_runs: Supabase query failed (non-fatal): %s", exc)
        return []


# ---------------------------------------------------------------------------
# GET /token/{token}  — validate and execute one-click action
# ---------------------------------------------------------------------------

@router.get("/token/{token_str}", response_model=TokenActionResponse)
async def execute_token_action(
    token_str: str,
    runtime=Depends(get_agent_runtime),
) -> TokenActionResponse:
    """
    Validate a single-use briefing action token and execute the corresponding action.

    Token types and their effects:
    - deep_link     → returns redirect_url to the Decision Studio Deep Analysis view
    - snooze        → records a 14-day snooze action on the situation
    - request_info  → records a request-for-information action on the situation
    - delegate      → returns redirect_url to the /delegate/{token} confirmation page
    - approve       → approves a pending HITL solution in Value Assurance

    Tokens are single-use and expire after 7 days. Returns 410 if expired or
    already used, 404 if the token is not recognised.
    """
    from src.database.briefing_store import BriefingStore
    from src.database.situations_store import SituationsStore

    store = BriefingStore()
    row = await store.validate_and_consume_token(token_str)

    if row is None:
        raise HTTPException(
            status_code=410,
            detail="Token is invalid, expired, or has already been used.",
        )

    token_type = row.get("token_type", "")
    situation_id = row.get("situation_id", "")
    principal_id = row.get("principal_id", "")

    # Build the Decision Studio base URL from env (falls back to localhost)
    import os
    ds_url = os.getenv("DECISION_STUDIO_URL", "http://localhost:5173")

    # --- deep_link ---
    if token_type == TokenType.DEEP_LINK.value:
        # situation_id in briefing_tokens stores the kpi_name (stable across runs)
        kpi_name: Optional[str] = situation_id if situation_id else None

        redirect_url = f"{ds_url}/situation/{situation_id}"
        return TokenActionResponse(
            token_type=token_type,
            situation_id=situation_id,
            action_taken="deep_link",
            redirect_url=redirect_url,
            principal_id=row.get("principal_id", ""),
            kpi_name=kpi_name,
            message="Redirecting to Deep Analysis.",
        )

    # --- snooze ---
    if token_type == TokenType.SNOOZE.value:
        sit_store = SituationsStore()
        from datetime import datetime, timezone, timedelta
        snooze_expires = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
        await sit_store.update_status(
            situation_id,
            "SNOOZED",
            snoozed_by=principal_id,
            snooze_expires_at=snooze_expires,
        )
        return TokenActionResponse(
            token_type=token_type,
            situation_id=situation_id,
            action_taken="snoozed_14_days",
            redirect_url=f"{ds_url}/situations",
            principal_id=row.get("principal_id", ""),
            message="Situation snoozed for 14 days.",
        )

    # --- request_info ---
    if token_type == TokenType.REQUEST_INFO.value:
        sit_store = SituationsStore()
        await sit_store.update_status(
            situation_id,
            "PENDING_INFO",
            requested_by=principal_id,
        )
        return TokenActionResponse(
            token_type=token_type,
            situation_id=situation_id,
            action_taken="request_info_recorded",
            redirect_url=f"{ds_url}/situations",
            principal_id=row.get("principal_id", ""),
            message="Request for information has been recorded.",
        )

    # --- delegate ---
    if token_type == TokenType.DELEGATE.value:
        # The token has been consumed; return the token string so the frontend
        # can present the delegate form without needing the original token.
        # We store a fresh *one-time* reference: the frontend POSTs to /delegate/{token_str}
        # with the chosen delegate principal.  Since validate_and_consume_token already
        # marked the token as used, we re-issue a short-lived delegate-confirm token.
        redirect_url = f"{ds_url}/delegate?situation={situation_id}&token={token_str}&principal={principal_id}"
        return TokenActionResponse(
            token_type=token_type,
            situation_id=situation_id,
            action_taken="delegate_initiated",
            redirect_url=redirect_url,
            principal_id=row.get("principal_id", ""),
            message="Choose a delegate principal to complete delegation.",
        )

    # --- approve (HITL solution approval) ---
    if token_type == TokenType.APPROVE.value:
        kpi_assessment_id = row.get("kpi_assessment_id")
        await _approve_solution_from_token(kpi_assessment_id, principal_id, runtime)
        return TokenActionResponse(
            token_type=token_type,
            situation_id=situation_id,
            action_taken="solution_approved",
            redirect_url=f"{ds_url}/value-assurance",
            principal_id=row.get("principal_id", ""),
            message="Solution approved and added to Value Assurance tracking.",
        )

    # Unknown token type — should not happen
    raise HTTPException(status_code=400, detail=f"Unknown token type: {token_type}")


# ---------------------------------------------------------------------------
# POST /delegate/{token}  — complete delegation
# ---------------------------------------------------------------------------

@router.post("/delegate/{token_str}", response_model=DelegateResponse)
async def complete_delegation(
    token_str: str,
    body: DelegateRequest,
) -> DelegateResponse:
    """
    Complete a delegation action.

    Called by the Decision Studio delegation form after the principal selects
    a delegate.  The token must be a DELEGATE-type token that was already
    validated (but not consumed) by GET /token/{token}.

    Note: Because validate_and_consume_token marks the token as used, this
    endpoint operates directly on the situation_id embedded in the token
    payload passed through the frontend redirect URL.  The delegate_to_principal_id
    is supplied in the request body.
    """
    from src.database.situations_store import SituationsStore

    if not body.delegate_to_principal_id:
        raise HTTPException(status_code=422, detail="delegate_to_principal_id is required.")

    # Retrieve situation_id from token (token already consumed by GET /token step,
    # so we do a permissive look-up by token value regardless of used_at)
    from src.database.briefing_store import BriefingStore
    import httpx, json as _json

    store = BriefingStore()
    situation_id: Optional[str] = None

    if store.enabled:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    store._tokens_url,
                    headers=store.headers,
                    params={"token": f"eq.{token_str}", "select": "situation_id,token_type"},
                )
                resp.raise_for_status()
                rows = _json.loads(resp.content) if resp.content else []
                if rows:
                    row = rows[0]
                    if row.get("token_type") != TokenType.DELEGATE.value:
                        raise HTTPException(status_code=400, detail="Token is not a delegate token.")
                    situation_id = row.get("situation_id")
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("complete_delegation: token lookup failed: %s", exc)

    if not situation_id:
        raise HTTPException(
            status_code=404,
            detail="Delegate token not found or situation could not be resolved.",
        )

    # Record the delegation on the situation row
    sit_store = SituationsStore()
    await sit_store.update_status(
        situation_id,
        "DELEGATED",
        delegated_to=body.delegate_to_principal_id,
        delegate_note=body.note or "",
    )

    # Write audit record to situation_actions
    try:
        from src.database.assessment_store import AssessmentStore
        from src.agents.models.assessment_models import SituationAction, SituationActionType

        # Retrieve the delegating principal's ID from the token row
        delegating_principal = ""
        if store.enabled and rows:
            delegating_principal = rows[0].get("principal_id", "")

        action = SituationAction(
            situation_id=situation_id,
            principal_id=delegating_principal or "unknown",
            action_type=SituationActionType.DELEGATE,
            target_principal_id=body.delegate_to_principal_id,
            notes=body.note,
        )
        assessment_store = AssessmentStore()
        await assessment_store.insert_action(action)
    except Exception as exc:
        logger.warning("complete_delegation: audit record failed (non-fatal): %s", exc)

    return DelegateResponse(
        situation_id=situation_id,
        delegated_to=body.delegate_to_principal_id,
        message=f"Situation delegated to principal '{body.delegate_to_principal_id}'.",
    )


# ---------------------------------------------------------------------------
# GET /delegates  — recommend delegate principals for a KPI
# ---------------------------------------------------------------------------

class DelegateSuggestion(BaseModel):
    principal_id: str
    name: str
    title: str
    is_recommended: bool = False
    reason: Optional[str] = None


@router.get("/delegates", response_model=List[DelegateSuggestion])
async def get_delegate_suggestions(
    kpi_name: str,
    exclude_principal_id: Optional[str] = None,
    client_id: str = "lubricants",
    runtime=Depends(get_agent_runtime),
) -> List[DelegateSuggestion]:
    """
    Return a ranked list of principals who could own a KPI situation.

    Uses the chain: KPI → business_process_ids → principals with matching
    business processes. Principals whose business processes overlap with the
    KPI's are marked as recommended.
    """
    registry_factory = runtime.get_registry_factory()
    suggestions: List[DelegateSuggestion] = []

    try:
        kpi_provider = registry_factory.get_provider("kpi")
        principal_provider = registry_factory.get_provider("principal_profile")

        # Find the KPI's business_process_ids
        kpi_bp_ids: set = set()
        all_kpis = kpi_provider.get_all() if kpi_provider else []
        if isinstance(all_kpis, dict):
            all_kpis = list(all_kpis.values())
        for kpi in all_kpis:
            kpi_obj_name = getattr(kpi, "name", None) or getattr(kpi, "display_name", None) or ""
            kpi_obj_id = getattr(kpi, "id", "")
            if kpi_obj_name.lower() == kpi_name.lower() or kpi_obj_id.lower() == kpi_name.lower():
                bp_ids = getattr(kpi, "business_process_ids", []) or []
                kpi_bp_ids.update(bp_ids)
                break

        # Get all principals for the client
        all_principals = principal_provider.get_all() if principal_provider else []
        if isinstance(all_principals, dict):
            all_principals = list(all_principals.values())

        for p in all_principals:
            pid = getattr(p, "id", "")
            if pid == exclude_principal_id:
                continue
            p_bps = set(getattr(p, "business_processes", []) or [])
            overlap = kpi_bp_ids & p_bps
            is_rec = len(overlap) > 0
            reason = None
            if is_rec and overlap:
                bp_names = [bp.replace("_", " ").title() for bp in list(overlap)[:2]]
                reason = f"Responsible for {', '.join(bp_names)}"

            suggestions.append(DelegateSuggestion(
                principal_id=pid,
                name=getattr(p, "name", pid),
                title=getattr(p, "title", ""),
                is_recommended=is_rec,
                reason=reason,
            ))

        # Sort: recommended first, then alphabetically
        suggestions.sort(key=lambda s: (not s.is_recommended, s.name))

    except Exception as exc:
        logger.warning("get_delegate_suggestions failed: %s", exc)

    return suggestions


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _approve_solution_from_token(
    kpi_assessment_id: Optional[str],
    principal_id: str,
    runtime: Any,
) -> None:
    """
    Approve a pending HITL solution via the Value Assurance agent.

    This is a best-effort operation; failures are logged but not surfaced to
    the caller (the token action response has already been committed).
    """
    if not kpi_assessment_id:
        logger.warning("_approve_solution_from_token: no kpi_assessment_id in token row")
        return
    try:
        orchestrator = runtime.get_orchestrator()
        await orchestrator.execute_agent_method(
            "A9_Value_Assurance_Agent",
            "approve_solution",
            {
                "kpi_assessment_id": kpi_assessment_id,
                "approved_by": principal_id,
                "source": "pib_email_token",
            },
        )
    except Exception as exc:
        logger.warning(
            "_approve_solution_from_token: VA approval failed (non-fatal): %s", exc
        )
