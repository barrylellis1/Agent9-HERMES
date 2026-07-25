"""API routes for onboarding wizard progress aggregation.

Computes 6-step onboarding wizard completion for a client by calling
existing provider/agent accessors directly (no HTTP self-calls), so each
sub-check inherits whatever tenant-isolation mechanism that accessor already
has (RLS-wrapped via tenant_scope() for accountability, or application-layer
strict-match filtering for the KPI/principal/data-product registries — the
same mechanism src/api/routes/registry.py's list endpoints already use).

Full wizard design: docs/architecture/onboarding_wizard_redesign.md

Prefix: /api/v1/onboarding/
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from fastapi import APIRouter, Query

from src.api.routes.admin import get_connection_health
from src.api.routes.assessments import _assessment_runs
from src.api.routes.company_profile import get_company_profile
from src.api.routes.kpi_accountability import _get_interview_agent
from src.api.runtime import get_agent_runtime
from src.registry.factory import RegistryFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])

_STEP_ORDER = [
    "workspace_setup",
    "principals",
    "kpi_library",
    "ownership",
    "connect_data",
    "validate_launch",
]


async def _get_registry_factory() -> RegistryFactory:
    factory = RegistryFactory()
    if not factory.is_initialized:
        await factory.initialize()
    return factory


async def _check_workspace_setup(client_id: str) -> Dict[str, Any]:
    profile = await get_company_profile(client_id=client_id)
    complete = bool(profile) and bool(profile.get("industry"))
    return {"complete": complete}


async def _check_principals(factory: RegistryFactory, client_id: str) -> Dict[str, Any]:
    provider = factory.get_principal_profile_provider()
    principals = provider.get_by_client(client_id) if provider else []
    count = len(principals)
    with_email = sum(1 for p in principals if getattr(p, "email", None))
    return {
        "complete": count >= 1 and with_email == count,
        "count": count,
        "with_email": with_email,
    }


async def _check_kpi_library(factory: RegistryFactory, client_id: str) -> Dict[str, Any]:
    provider = factory.get_kpi_provider()
    kpis = provider.get_by_client(client_id) if provider else []
    count = len(kpis)

    # Informational only — deliberately not folded into `complete`. Business
    # processes were retrofitted onto the wizard after many clients already
    # onboarded without them (Phase 12F); gating step 3 on this would mark
    # every already-complete client "incomplete" with no backfill path.
    bp_provider = factory.get_business_process_provider()
    business_processes_count = len(bp_provider.get_by_client(client_id)) if bp_provider else 0

    return {
        "complete": count >= 1,
        "count": count,
        "business_processes_count": business_processes_count,
    }


async def _check_ownership(client_id: str) -> Dict[str, Any]:
    agent = await _get_interview_agent()
    coverage = await agent.get_coverage(client_id)
    total = coverage.get("total_kpis", 0)
    assigned = coverage.get("covered_kpis", 0)
    return {"complete": total > 0 and assigned == total, "assigned": assigned, "total": total}


async def _check_connect_data(factory: RegistryFactory, client_id: str) -> Dict[str, Any]:
    provider = factory.get_data_product_provider()
    data_products = provider.get_by_client(client_id) if provider else []
    count = len(data_products)

    # A data product row alone only means the Day-5 sub-wizard *started* —
    # register_data_product fires as early as the Metadata Analysis step,
    # long before KPI Definition / Query Validation / Review & Register
    # finish. Reading that as "step 5 complete" makes OnboardingResume jump
    # an admin straight past in-progress, unsaved KPI Definition work to
    # Day 6 (found live 2026-07-24: brookshire_brothers had a registered
    # data product with zero KPIs, and the 5 KPIs pending "Accept All" were
    # lost when resume bounced past Day 5). KPI sql_query validation itself
    # still isn't persisted (see onboarding_wizard_redesign.md §4), but
    # "at least one KPI actually finalized against one of this client's real
    # data products" is a persisted signal that only exists once
    # finalize_kpis (Review & Register) has actually run — use that instead.
    kpi_provider = factory.get_kpi_provider()
    kpis = kpi_provider.get_by_client(client_id) if kpi_provider else []
    data_product_ids = {dp.id for dp in data_products}
    kpis_connected = sum(1 for k in kpis if getattr(k, "data_product_id", None) in data_product_ids)

    return {
        "complete": count >= 1 and kpis_connected >= 1,
        "data_products": count,
        "kpis_connected": kpis_connected,
    }


async def _check_validate_launch(client_id: str) -> Dict[str, Any]:
    runtime = await get_agent_runtime()
    health = await get_connection_health(client_id=client_id, runtime=runtime)
    # get_connection_health's top-level "status" is the GLOBAL status of the
    # last probe across every tenant's data products — it is not re-derived
    # per client_id, only `data.results` is filtered. Recompute a per-tenant
    # status from the already-filtered results instead of trusting the
    # unscoped field (avoids one tenant's probe result leaking into another's
    # onboarding gate). Fail-closed when there are no results yet (never
    # probed for this client) rather than vacuously reporting healthy.
    results = health.get("data", {}).get("results", [])
    connection_ok = bool(results) and all(r.get("status") == "ok" for r in results)
    # Known limitation: _assessment_runs is in-memory only and resets on
    # every backend redeploy — see onboarding_wizard_redesign.md §4.
    assessment_runs = [r for r in _assessment_runs.values() if r.client_id == client_id]
    return {
        "complete": connection_ok and len(assessment_runs) >= 1,
        "connection_ok": connection_ok,
        "assessment_runs": len(assessment_runs),
    }


async def _safe_check(step_key: str, coro) -> Dict[str, Any]:
    """Run one sub-check, degrading to incomplete-with-error instead of
    letting one failing accessor 500 the whole aggregator endpoint."""
    try:
        return await coro
    except Exception as exc:  # noqa: BLE001 - deliberately broad, see docstring
        logger.error("onboarding progress check '%s' failed: %s", step_key, exc)
        return {"complete": False, "error": str(exc)}


@router.get("/progress")
async def get_onboarding_progress(client_id: str = Query(...)) -> Dict[str, Any]:
    """Return per-step completion for the 6-step onboarding wizard."""
    factory = await _get_registry_factory()

    (
        workspace_setup,
        principals,
        kpi_library,
        ownership,
        connect_data,
        validate_launch,
    ) = await asyncio.gather(
        _safe_check("workspace_setup", _check_workspace_setup(client_id)),
        _safe_check("principals", _check_principals(factory, client_id)),
        _safe_check("kpi_library", _check_kpi_library(factory, client_id)),
        _safe_check("ownership", _check_ownership(client_id)),
        _safe_check("connect_data", _check_connect_data(factory, client_id)),
        _safe_check("validate_launch", _check_validate_launch(client_id)),
    )

    steps = {
        "workspace_setup": workspace_setup,
        "principals": principals,
        "kpi_library": kpi_library,
        "ownership": ownership,
        "connect_data": connect_data,
        "validate_launch": validate_launch,
    }

    first_incomplete_step = 7
    for i, key in enumerate(_STEP_ORDER, start=1):
        if not steps[key]["complete"]:
            first_incomplete_step = i
            break

    return {
        "client_id": client_id,
        "steps": steps,
        "first_incomplete_step": first_incomplete_step,
    }
