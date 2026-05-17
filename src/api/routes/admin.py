import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

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


@router.get(
    "/connection-health",
    summary="Return cached connection health for all data products",
    description=(
        "Returns the most recent connection health probe results without re-testing. "
        "If no probe has run yet, returns an empty result. "
        "Use POST /connection-health/test to trigger a fresh probe. "
        "No auth required (read-only cached data). Will move to Supabase session auth in Infra B."
    ),
)
async def get_connection_health(
    client_id: Optional[str] = Query(None, description="Filter results by client/tenant ID"),
    runtime: AgentRuntime = Depends(get_agent_runtime),
):
    cached = runtime._last_health_probe
    if not cached:
        return {"status": "not_probed", "data": {"probed_at": None, "results": []}}
    results = cached.get("results", [])
    if client_id:
        results = [r for r in results if r.get("client_id") == client_id]
    return {"status": cached.get("status", "unknown"), "data": {**cached, "results": results}}


@router.post(
    "/connection-health/test",
    summary="Probe all data product connections and return health status",
    description=(
        "Triggers a fresh connection probe for every data product in the registry. "
        "Runs SELECT 1 (or equivalent) against each backend. Results are cached and "
        "also returned by GET /connection-health. "
        "No auth required for MVP. Will move to Supabase session auth in Infra B."
    ),
)
async def test_connection_health(
    client_id: Optional[str] = Query(None, description="Restrict probe to one client/tenant"),
    runtime: AgentRuntime = Depends(get_agent_runtime),
):
    logger.info("Connection health probe triggered (client_id=%s)", client_id)
    result = await runtime.probe_connection_health(client_id=client_id)
    logger.info("Connection health probe complete: status=%s, %d data products", result.get("status"), len(result.get("results", [])))
    return {"status": result["status"], "data": result}
