import logging
import os

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.api.runtime import AgentRuntime, get_agent_runtime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

_ADMIN_KEY_ENV = "ADMIN_API_KEY"


def _require_admin_key(x_admin_key: str = Header(default="")) -> None:
    """Validate the X-Admin-Key header against the ADMIN_API_KEY env var.

    If ADMIN_API_KEY is not configured the endpoint is disabled — returning
    503 rather than 403 so ops can distinguish "not set up" from "wrong key".
    """
    configured_key = os.getenv(_ADMIN_KEY_ENV, "").strip()
    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API key not configured on this server (set ADMIN_API_KEY env var).",
        )
    if x_admin_key != configured_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin key.",
        )


@router.post(
    "/registry/reload",
    summary="Force registry refresh on SA, PCA, and DPA agents",
    description=(
        "Triggers an immediate in-memory registry refresh on the three agents that "
        "cache registry data (Situation Awareness, Principal Context, Data Product). "
        "Use after seeding a new client or updating KPIs/principals in Supabase when "
        "you need the change visible immediately without a Railway restart. "
        "Requires the X-Admin-Key header."
    ),
)
async def reload_registry(
    _: None = Depends(_require_admin_key),
    runtime: AgentRuntime = Depends(get_agent_runtime),
):
    logger.info("Admin registry reload triggered")
    result = await runtime.reload_registry()
    logger.info("Admin registry reload complete: %s", result)
    return {"status": result["status"], "data": result}
