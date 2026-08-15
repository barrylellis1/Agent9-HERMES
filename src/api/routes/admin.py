import logging
import os
from typing import List, Optional

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


@router.get(
    "/slice-validity",
    summary="Return a KPI's last slice-validity check, straight off the KPI record",
    description=(
        "docs/architecture/kpi_semantic_contract.md §4. Returns the persisted "
        "not_sliceable_by / per-dimension coverage / last-checked timestamp for "
        "one KPI — this is a database read, not a cache, so it is correct across "
        "restarts and multiple server instances. If the KPI has never been "
        "checked, returns status='not_probed' with empty results. "
        "Use POST /slice-validity/test to run a fresh check. "
        "Advisory only — nothing reads not_sliceable_by to gate any workflow. "
        "No auth required (read-only). Will move to Supabase session auth in Infra B."
    ),
)
async def get_slice_validity(
    kpi_id: str = Query(..., description="KPI to look up"),
    client_id: str = Query(..., description="Tenant — strict scope, required"),
    runtime: AgentRuntime = Depends(get_agent_runtime),
):
    result = runtime.get_cached_slice_validity(kpi_id=kpi_id, client_id=client_id)
    return {"status": result["status"], "data": result}


@router.post(
    "/slice-validity/test",
    summary="Run the slice-validity check for one KPI",
    description=(
        "docs/architecture/kpi_semantic_contract.md §4. Counts, per dimension, "
        "how many distinct values each component measure (default Revenue/COGS) "
        "reaches — a dimension only one component reaches produces a confident, "
        "plausible, wrong ratio when sliced by it. Result is persisted onto the "
        "KPI record (not_sliceable_by / slice_validity_details / "
        "slice_validity_checked_at) and also returned here. "
        "Scoped to one caller-chosen KPI, not a scan of every KPI in the "
        "registry — this is a human-triggered diagnostic, run it again after a "
        "client's data model changes, not an automatic batch job. "
        "Advisory only — nothing reads the result to gate any workflow; "
        "enforcement was designed and explicitly rejected as scope creep at "
        "demo stage (DEVELOPMENT_PLAN.md -> Phase 15 -> Stage I). "
        "No auth required for MVP. Will move to Supabase session auth in Infra B."
    ),
)
async def test_slice_validity(
    kpi_id: str = Query(..., description="KPI to check"),
    client_id: str = Query(..., description="Tenant — strict scope, required"),
    dimensions: Optional[List[str]] = Query(
        None, description="Dimensions to check; defaults to the KPI's own declared dimensions"
    ),
    runtime: AgentRuntime = Depends(get_agent_runtime),
):
    logger.info("Slice-validity check triggered (kpi_id=%s, client_id=%s)", kpi_id, client_id)
    result = await runtime.run_slice_validity_check(kpi_id=kpi_id, client_id=client_id, dimensions=dimensions)
    logger.info(
        "Slice-validity check complete: status=%s, not_sliceable_by=%s",
        result.get("status"), result.get("not_sliceable_by"),
    )
    return {"status": result["status"], "data": result}
