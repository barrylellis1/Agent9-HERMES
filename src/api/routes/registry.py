from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.api.auth_middleware import AuthUser, get_optional_user
from src.registry.factory import RegistryFactory
from src.registry.models.business_process import BusinessProcess
from src.registry.models.data_product import DataProduct
from src.registry.models.kpi import KPI
from src.registry.models.principal import PrincipalProfile
from src.registry.providers.business_glossary_provider import BusinessGlossaryProvider, BusinessTerm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/registry", tags=["registry"])


class Envelope(BaseModel):
    status: str = Field("ok")
    data: Any


def error_response(code: str, message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return {
        "status": "error",
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }


async def get_registry_factory() -> RegistryFactory:
    """Return the shared, properly-bootstrapped RegistryFactory.

    Routes through RegistryBootstrap.initialize() — idempotent and self-healing
    (it re-verifies principal_profile/business_glossary/data_product/kpi providers
    and only re-runs what's actually missing) — rather than RegistryFactory's own
    plain .initialize(), which only LOADS DATA for providers already registered
    and does nothing if none are. Every registry CRUD route was implicitly relying
    on RegistryBootstrap having already run via the app's startup sequence before
    any request arrived; this makes that guarantee explicit instead of assumed.
    Found live, Aug 2026, tracing the same startup-ordering gap that let
    A9_Principal_Context_Agent register a non-tenant-aware fallback provider —
    see that agent's connect() and its card for the full finding.
    """
    from src.registry.bootstrap import RegistryBootstrap
    await RegistryBootstrap.initialize()
    return RegistryFactory()


def serialize(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, list):
        return [serialize(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    return value


def wrap(data: Any) -> Envelope:
    return Envelope(data=serialize(data))


# ---------------------------------------------------------------------------
# Infra A2: server-derived client_id for tenant-scoped writes
#
# Registry models default client_id from a static ACTIVE_CLIENT_ID server env
# var (src/registry/models/kpi.py etc.) — a body-omitted client_id would
# silently stamp records with whatever tenant the process happens to be
# configured for, not the client actually being onboarded. These helpers make
# every create/replace/update route resolve client_id authoritatively
# server-side instead: a valid JWT wins; without one (demo/admin mode) an
# explicit client_id query param is required and validated against
# business_contexts. Fails closed — never falls through to a default tenant.
# ---------------------------------------------------------------------------


async def _client_exists(bc_provider: Any, client_id: str) -> bool:
    """Check a client_id names a real business_contexts row.

    Deliberately checks list_contexts() (raw dicts) rather than get_context()
    (which hydrates a strict A9_PS_BusinessContext model and returns None on
    ANY validation error — e.g. a legitimate client's business_contexts row
    with more than the model's max strategic_priorities would silently look
    "unknown" here otherwise).
    """
    if bc_provider is None:
        return False
    rows = await bc_provider.list_contexts()
    return any(row.get("id") == client_id for row in rows)


async def _resolve_create_client_id(
    client_id_qp: Optional[str],
    user: Optional[AuthUser],
    factory: RegistryFactory,
) -> str:
    if user is not None:
        if client_id_qp and client_id_qp != user.client_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                error_response(
                    "client_mismatch",
                    f"Authenticated for client '{user.client_id}', cannot write to '{client_id_qp}'",
                ),
            )
        return user.client_id

    if not client_id_qp:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            error_response("client_id_required", "client_id query parameter is required when not authenticated"),
        )

    bc_provider = factory.get_business_context_provider()
    known = await _client_exists(bc_provider, client_id_qp)
    if not known:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_response("unknown_client", f"No such client '{client_id_qp}'"),
        )
    return client_id_qp


def _enforce_write_ownership(
    existing_client_id: Optional[str],
    client_id_qp: Optional[str],
    user: Optional[AuthUser],
) -> str:
    """Verify the caller may modify a record with an existing client_id.

    Returns the caller's resolved client_id — callers must persist this,
    never the request body's client_id, so an update can never re-parent a
    record to a different tenant.
    """
    caller_client_id = user.client_id if user is not None else client_id_qp
    if not caller_client_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            error_response("client_id_required", "client_id query parameter is required when not authenticated"),
        )
    if existing_client_id and caller_client_id != existing_client_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            error_response("forbidden", f"Record belongs to client '{existing_client_id}', not '{caller_client_id}'"),
        )
    return caller_client_id


async def _fetch_principal_from_supabase(principal_id: str) -> Optional[PrincipalProfile]:
    """Fetch a single principal directly from Supabase by ID.

    Used as a fallback when the in-memory provider (scoped to ACTIVE_CLIENT_ID)
    doesn't contain the requested principal — e.g. a different client's principal.
    """
    try:
        import httpx as _httpx
        supabase_url = os.getenv("SUPABASE_URL")
        service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not supabase_url or not service_key:
            return None
        async with _httpx.AsyncClient(timeout=10.0) as http:
            resp = await http.get(
                f"{supabase_url.rstrip('/')}/rest/v1/principal_profiles",
                headers={
                    "apikey": service_key,
                    "Authorization": f"Bearer {service_key}",
                    "Accept": "application/json",
                },
                params={"id": f"eq.{principal_id}", "select": "*"},
            )
            resp.raise_for_status()
            rows = json.loads(resp.text)
            if rows:
                return PrincipalProfile.model_validate(rows[0])
    except Exception as e:
        logger.warning("Supabase principal lookup failed for %s: %s", principal_id, e)
    return None


# ---------------------------------------------------------------------------
# KPI Registry
# ---------------------------------------------------------------------------


@router.get("/kpis", response_model=Envelope)
async def list_kpis(
    domain: Optional[str] = Query(None),
    owner_role: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_kpi_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "KPI provider unavailable"))

    items: List[KPI] = provider.get_by_client(client_id) if client_id else provider.get_all()
    if domain:
        items = [kpi for kpi in items if kpi.domain == domain]
    if owner_role:
        items = [kpi for kpi in items if kpi.owner_role == owner_role]
    if tag:
        items = [kpi for kpi in items if tag in getattr(kpi, "tags", [])]

    return wrap(items)


@router.get("/kpis/{kpi_id}", response_model=Envelope)
async def get_kpi(
    kpi_id: str,
    client_id: Optional[str] = Query(None, description="Tenant client ID for ownership verification"),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_kpi_provider()
    kpi = provider.get(kpi_id, client_id=client_id) if provider else None
    if kpi is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"KPI '{kpi_id}' not found"))
    # Defense in depth: provider.get() already scopes by client_id when given,
    # but re-check explicitly in case a future provider swap doesn't honor it.
    if client_id and getattr(kpi, "client_id", None) != client_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"KPI '{kpi_id}' not found"))
    return wrap(kpi)


@router.post("/kpis", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_kpi(
    payload: KPI,
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_kpi_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "KPI provider unavailable"))
    resolved_client_id = await _resolve_create_client_id(client_id, user, factory)
    # Duplicate check must be scoped to this tenant — an unscoped bare-id
    # lookup would wrongly reject a new client's KPI as "already exists"
    # whenever another tenant happens to use the same generic id (e.g. every
    # client's "net_income").
    if provider.get(payload.id, client_id=resolved_client_id):
        raise HTTPException(status.HTTP_409_CONFLICT, error_response("duplicate", f"KPI '{payload.id}' exists"))
    payload = payload.model_copy(update={"client_id": resolved_client_id})
    await provider.register(payload)
    return wrap(payload)


@router.put("/kpis/{kpi_id}", response_model=Envelope)
async def replace_kpi(
    kpi_id: str,
    payload: KPI,
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_kpi_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "KPI provider unavailable"))
    existing = provider.get(kpi_id, client_id=user.client_id if user else client_id)
    if existing is not None:
        owner_client_id = _enforce_write_ownership(getattr(existing, "client_id", None), client_id, user)
    else:
        owner_client_id = await _resolve_create_client_id(client_id, user, factory)
    replacement = payload.model_copy(update={"id": kpi_id, "client_id": owner_client_id})
    await provider.upsert(replacement)
    return wrap(replacement)


@router.patch("/kpis/{kpi_id}", response_model=Envelope)
async def update_kpi(
    kpi_id: str,
    payload: Dict[str, Any],
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_kpi_provider()
    kpi = provider.get(kpi_id, client_id=user.client_id if user else client_id) if provider else None
    if kpi is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"KPI '{kpi_id}' not found"))
    _enforce_write_ownership(getattr(kpi, "client_id", None), client_id, user)
    payload = {k: v for k, v in payload.items() if k != "client_id"}
    updated = kpi.model_copy(update=payload)
    await provider.upsert(updated)
    return wrap(updated)


@router.delete("/kpis/{kpi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kpi(
    kpi_id: str,
    client_id: Optional[str] = Query(None),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_kpi_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"KPI '{kpi_id}' not found"))

    # Fetch KPI to validate ownership if client_id provided
    kpi = provider.get(kpi_id, client_id=client_id)
    if kpi is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"KPI '{kpi_id}' not found"))

    kpi_client = getattr(kpi, "client_id", None)
    if client_id and kpi_client != client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, error_response("forbidden", f"KPI belongs to client '{kpi_client}', not '{client_id}'"))

    # Delete keys on the provider's composite cache key (client_id:id) — the
    # record's own client_id, not just the id, or the delete never matches.
    delete_key = f"{kpi_client}:{kpi_id}" if kpi_client else kpi_id
    if not await provider.delete(delete_key):
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"KPI '{kpi_id}' not found"))


# ---------------------------------------------------------------------------
# Principal Profiles
# ---------------------------------------------------------------------------


@router.get("/principals", response_model=Envelope)
async def list_principals(
    client_id: Optional[str] = Query(None, description="Filter principals by client/tenant ID"),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    # If a client_id is specified, query Supabase directly so we always return
    # that client's principals — even if the in-memory provider was bootstrapped
    # for a different tenant.
    if client_id:
        try:
            import httpx as _httpx
            supabase_url = os.getenv("SUPABASE_URL")
            service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            if supabase_url and service_key:
                async with _httpx.AsyncClient(timeout=10.0) as http:
                    resp = await http.get(
                        f"{supabase_url.rstrip('/')}/rest/v1/principal_profiles",
                        headers={
                            "apikey": service_key,
                            "Authorization": f"Bearer {service_key}",
                            "Accept": "application/json",
                        },
                        params={"client_id": f"eq.{client_id}", "select": "*"},
                    )
                    resp.raise_for_status()
                    rows = json.loads(resp.text)
                    if rows:
                        items = [PrincipalProfile.model_validate(r) for r in rows]
                        return wrap(items)
        except Exception as e:
            logger.warning("Direct Supabase principal lookup failed for client_id=%s: %s", client_id, e)
        # Fall through to in-memory provider if Supabase query fails

    provider = factory.get_principal_profile_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Principal provider unavailable"))
    items: List[PrincipalProfile] = (
        provider.get_by_client(client_id) if client_id else provider.get_all()
    )
    return wrap(items)


@router.get("/principals/{principal_id}", response_model=Envelope)
async def get_principal(
    principal_id: str,
    client_id: Optional[str] = Query(None, description="Tenant client ID for ownership verification"),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_principal_profile_provider()
    profile = provider.get(principal_id, client_id=client_id) if provider else None
    # Fallback: query Supabase directly if not in the in-memory provider
    if profile is None:
        profile = await _fetch_principal_from_supabase(principal_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Principal '{principal_id}' not found"))
    # Enforce tenant isolation when caller supplies client_id
    if client_id and getattr(profile, "client_id", None) != client_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Principal '{principal_id}' not found"))
    return wrap(profile)


@router.post("/principals", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_principal(
    payload: PrincipalProfile,
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_principal_profile_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Principal provider unavailable"))
    resolved_client_id = await _resolve_create_client_id(client_id, user, factory)
    if provider.get(payload.id, client_id=resolved_client_id):
        raise HTTPException(status.HTTP_409_CONFLICT, error_response("duplicate", f"Principal '{payload.id}' exists"))
    payload = payload.model_copy(update={"client_id": resolved_client_id})
    await provider.register(payload)
    return wrap(payload)


@router.put("/principals/{principal_id}", response_model=Envelope)
async def replace_principal(
    principal_id: str,
    payload: PrincipalProfile,
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_principal_profile_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Principal provider unavailable"))
    existing = provider.get(principal_id, client_id=user.client_id if user else client_id)
    if existing is not None:
        owner_client_id = _enforce_write_ownership(getattr(existing, "client_id", None), client_id, user)
    else:
        owner_client_id = await _resolve_create_client_id(client_id, user, factory)
    replacement = payload.model_copy(update={"id": principal_id, "client_id": owner_client_id})
    await provider.upsert(replacement)
    return wrap(replacement)


@router.patch("/principals/{principal_id}", response_model=Envelope)
async def update_principal(
    principal_id: str,
    payload: Dict[str, Any],
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_principal_profile_provider()
    profile = provider.get(principal_id, client_id=user.client_id if user else client_id) if provider else None
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Principal '{principal_id}' not found"))
    _enforce_write_ownership(getattr(profile, "client_id", None), client_id, user)
    payload = {k: v for k, v in payload.items() if k != "client_id"}
    updated = profile.model_copy(update=payload)
    await provider.upsert(updated)
    return wrap(updated)


@router.delete("/principals/{principal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_principal(
    principal_id: str,
    client_id: Optional[str] = Query(None),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_principal_profile_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Principal '{principal_id}' not found"))

    profile = provider.get(principal_id, client_id=client_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Principal '{principal_id}' not found"))

    profile_client = getattr(profile, "client_id", None)
    if client_id and profile_client != client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, error_response("forbidden", f"Principal belongs to client '{profile_client}', not '{client_id}'"))

    delete_key = f"{profile_client}:{principal_id}" if profile_client else principal_id
    if not await provider.delete(delete_key):
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Principal '{principal_id}' not found"))


# ---------------------------------------------------------------------------
# Data Products
# ---------------------------------------------------------------------------


@router.get("/data-products", response_model=Envelope)
async def list_data_products(
    domain: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    business_process_id: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_data_product_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Data product provider unavailable"))

    items: List[DataProduct] = provider.get_by_client(client_id) if client_id else provider.get_all()

    if domain:
        items = [dp for dp in items if dp.domain == domain]
    if tag:
        items = [dp for dp in items if tag in getattr(dp, "tags", [])]
    if business_process_id:
        items = [
            dp
            for dp in items
            if business_process_id in getattr(dp, "related_business_processes", [])
            or business_process_id in dp.metadata.get("business_process_ids", [])
        ]

    return wrap(items)


@router.get("/data-products/{data_product_id}", response_model=Envelope)
async def get_data_product(
    data_product_id: str,
    client_id: Optional[str] = Query(None, description="Tenant client ID for ownership verification"),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_data_product_provider()
    data_product = provider.get(data_product_id, client_id=client_id) if provider else None
    if data_product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Data product '{data_product_id}' not found"))
    # Defense in depth: provider.get() already scopes by client_id when given,
    # but re-check explicitly in case a future provider swap doesn't honor it.
    # 404 (not 403) so an unauthorized caller can't distinguish "wrong tenant"
    # from "doesn't exist".
    if client_id and getattr(data_product, "client_id", None) != client_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Data product '{data_product_id}' not found"))
    return wrap(data_product)


@router.post("/data-products", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_data_product(
    payload: DataProduct,
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_data_product_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Data product provider unavailable"))
    resolved_client_id = await _resolve_create_client_id(client_id, user, factory)
    if provider.get(payload.id, client_id=resolved_client_id):
        raise HTTPException(status.HTTP_409_CONFLICT, error_response("duplicate", f"Data product '{payload.id}' exists"))
    payload = payload.model_copy(update={"client_id": resolved_client_id})
    await provider.register(payload)
    return wrap(payload)


@router.put("/data-products/{data_product_id}", response_model=Envelope)
async def replace_data_product(
    data_product_id: str,
    payload: DataProduct,
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_data_product_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Data product provider unavailable"))
    existing = provider.get(data_product_id, client_id=user.client_id if user else client_id)
    if existing is not None:
        owner_client_id = _enforce_write_ownership(getattr(existing, "client_id", None), client_id, user)
    else:
        owner_client_id = await _resolve_create_client_id(client_id, user, factory)
    replacement = payload.model_copy(update={"id": data_product_id, "client_id": owner_client_id})
    await provider.upsert(replacement)
    return wrap(replacement)


@router.patch("/data-products/{data_product_id}", response_model=Envelope)
async def update_data_product(
    data_product_id: str,
    payload: Dict[str, Any],
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_data_product_provider()
    data_product = provider.get(data_product_id, client_id=user.client_id if user else client_id) if provider else None
    if data_product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Data product '{data_product_id}' not found"))
    _enforce_write_ownership(getattr(data_product, "client_id", None), client_id, user)
    payload = {k: v for k, v in payload.items() if k != "client_id"}
    updated = data_product.model_copy(update=payload)
    await provider.upsert(updated)
    return wrap(updated)


@router.delete("/data-products/{data_product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_product(
    data_product_id: str,
    client_id: Optional[str] = Query(None),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_data_product_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Data product '{data_product_id}' not found"))

    # Fetch data product to validate ownership if client_id provided
    dp = provider.get(data_product_id, client_id=client_id)
    if dp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Data product '{data_product_id}' not found"))

    dp_client = getattr(dp, "client_id", None)
    if client_id and dp_client != client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, error_response("forbidden", f"Data product belongs to client '{dp_client}', not '{client_id}'"))

    delete_key = f"{dp_client}:{data_product_id}" if dp_client else data_product_id
    if not await provider.delete(delete_key):
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Data product '{data_product_id}' not found"))


# ---------------------------------------------------------------------------
# Business Processes
# ---------------------------------------------------------------------------


@router.get("/business-processes", response_model=Envelope)
async def list_business_processes(
    domain: Optional[str] = Query(None),
    owner_role: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_business_process_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Business process provider unavailable"))

    items: List[BusinessProcess] = provider.get_by_client(client_id) if client_id else provider.get_all()
    if domain:
        items = [bp for bp in items if bp.domain == domain]
    if owner_role:
        items = [bp for bp in items if bp.owner_role == owner_role]
    if tag:
        items = [bp for bp in items if tag in getattr(bp, "tags", [])]

    return wrap(items)


@router.get("/business-processes/{process_id}", response_model=Envelope)
async def get_business_process(
    process_id: str,
    client_id: Optional[str] = Query(None, description="Tenant client ID for ownership verification"),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_business_process_provider()
    process = provider.get(process_id, client_id=client_id) if provider else None
    if process is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Business process '{process_id}' not found"))
    if client_id and getattr(process, "client_id", None) != client_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Business process '{process_id}' not found"))
    return wrap(process)


@router.post("/business-processes", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_business_process(
    payload: BusinessProcess,
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_business_process_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Business process provider unavailable"))
    resolved_client_id = await _resolve_create_client_id(client_id, user, factory)
    if provider.get(payload.id, client_id=resolved_client_id):
        raise HTTPException(status.HTTP_409_CONFLICT, error_response("duplicate", f"Business process '{payload.id}' exists"))
    payload = payload.model_copy(update={"client_id": resolved_client_id})
    await provider.register(payload)
    return wrap(payload)


@router.put("/business-processes/{process_id}", response_model=Envelope)
async def replace_business_process(
    process_id: str,
    payload: BusinessProcess,
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_business_process_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Business process provider unavailable"))
    existing = provider.get(process_id, client_id=user.client_id if user else client_id)
    if existing is not None:
        owner_client_id = _enforce_write_ownership(getattr(existing, "client_id", None), client_id, user)
    else:
        owner_client_id = await _resolve_create_client_id(client_id, user, factory)
    replacement = payload.model_copy(update={"id": process_id, "client_id": owner_client_id})
    await provider.upsert(replacement)
    return wrap(replacement)


@router.patch("/business-processes/{process_id}", response_model=Envelope)
async def update_business_process(
    process_id: str,
    payload: Dict[str, Any],
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_business_process_provider()
    process = provider.get(process_id, client_id=user.client_id if user else client_id) if provider else None
    if process is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Business process '{process_id}' not found"))
    _enforce_write_ownership(getattr(process, "client_id", None), client_id, user)
    payload.pop("client_id", None)
    updated = process.model_copy(update=payload)
    await provider.upsert(updated)
    return wrap(updated)


@router.delete("/business-processes/{process_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business_process(
    process_id: str,
    client_id: Optional[str] = Query(None),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_business_process_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Business process '{process_id}' not found"))

    # Fetch business process to validate ownership if client_id provided
    bp = provider.get(process_id, client_id=client_id)
    if bp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Business process '{process_id}' not found"))

    bp_client = getattr(bp, "client_id", None)
    if client_id and bp_client != client_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, error_response("forbidden", f"Business process belongs to client '{bp_client}', not '{client_id}'"))

    delete_key = f"{bp_client}:{process_id}" if bp_client else process_id
    if not await provider.delete(delete_key):
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Business process '{process_id}' not found"))


# ---------------------------------------------------------------------------
# Business Glossary
# ---------------------------------------------------------------------------


def _get_glossary_provider(factory: RegistryFactory) -> BusinessGlossaryProvider:
    provider = factory.get_provider("business_glossary")
    if not isinstance(provider, BusinessGlossaryProvider):
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Business glossary provider unavailable"))
    return provider


@router.get("/glossary", response_model=Envelope)
async def list_terms(
    client_id: Optional[str] = Query(None, description="Filter glossary terms by client/tenant ID"),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = _get_glossary_provider(factory)
    items = provider.get_by_client(client_id) if client_id else provider.get_all()
    return wrap(items)


@router.get("/glossary/{term_name}", response_model=Envelope)
async def get_term(term_name: str, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = _get_glossary_provider(factory)
    term = provider.get_term(term_name)
    if term is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Term '{term_name}' not found"))
    return wrap(term)


@router.post("/glossary", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_term(
    payload: BusinessTerm,
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = _get_glossary_provider(factory)
    resolved_client_id = await _resolve_create_client_id(client_id, user, factory)
    payload = payload.model_copy(update={"client_id": resolved_client_id})
    provider.add_term(payload)
    return wrap(payload)


@router.put("/glossary/{term_name}", response_model=Envelope)
async def replace_term(
    term_name: str,
    payload: BusinessTerm,
    client_id: Optional[str] = Query(None, description="Required when not authenticated"),
    user: Optional[AuthUser] = Depends(get_optional_user),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = _get_glossary_provider(factory)
    existing = provider.get_term(term_name)
    if existing is not None:
        owner_client_id = _enforce_write_ownership(getattr(existing, "client_id", None), client_id, user)
    else:
        owner_client_id = await _resolve_create_client_id(client_id, user, factory)
    replacement = payload.model_copy(update={"name": term_name, "client_id": owner_client_id})
    provider.upsert_term(replacement)
    return wrap(replacement)


@router.delete("/glossary/{term_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_term(term_name: str, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = _get_glossary_provider(factory)
    if not provider.delete_term(term_name):
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Term '{term_name}' not found"))


# ---------------------------------------------------------------------------
# KPI Relationships (Phase 11I-B)
# ---------------------------------------------------------------------------


@router.get("/kpi-relationships", response_model=Envelope)
async def list_kpi_relationships(
    client_id: Optional[str] = Query(None),
    kpi_id: Optional[str] = Query(None),
):
    """List KPI relationships. Optionally filter by client_id and/or kpi_id."""
    from src.registry.providers.kpi_relationship_provider import KPIRelationshipProvider
    provider = KPIRelationshipProvider()
    try:
        if kpi_id and client_id:
            items = await provider.get_relationships_for_kpi(kpi_id, client_id)
        elif client_id:
            items = await provider.get_all(client_id)
        else:
            return Envelope(status="error", data=error_response("missing_param", "client_id is required"))
        return Envelope(data=[i.model_dump() for i in items])
    except Exception as e:
        return Envelope(status="error", data=error_response("server_error", str(e)))


@router.post("/kpi-relationships", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_kpi_relationship(body: Dict[str, Any]):
    """Create or update a KPI relationship."""
    from src.registry.providers.kpi_relationship_provider import KPIRelationshipProvider
    from src.registry.models.kpi_relationship import KPIRelationship
    provider = KPIRelationshipProvider()
    try:
        item = KPIRelationship(**body)
        result = await provider.upsert(item)
        return Envelope(data=result.model_dump())
    except Exception as e:
        return Envelope(status="error", data=error_response("server_error", str(e)))


@router.delete("/kpi-relationships/{kpi_id}/{related_kpi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kpi_relationship(
    kpi_id: str,
    related_kpi_id: str,
    client_id: str = Query(...),
):
    """Delete a KPI relationship by composite key."""
    from src.registry.providers.kpi_relationship_provider import KPIRelationshipProvider
    provider = KPIRelationshipProvider()
    try:
        await provider.delete(kpi_id, related_kpi_id, client_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Assumptions (Phase 15 Stage D — theory layer assumption/constraint/explanation records)
# ---------------------------------------------------------------------------


@router.get("/assumptions", response_model=Envelope)
async def list_assumptions(
    client_id: str = Query(...),
):
    """List all assumption/constraint/explanation records for a client."""
    from src.registry.providers.assumption_provider import AssumptionProvider
    provider = AssumptionProvider()
    try:
        items = await provider.get_all(client_id)
        return Envelope(data=[i.model_dump() for i in items])
    except Exception as e:
        return Envelope(status="error", data=error_response("server_error", str(e)))


@router.post("/assumptions", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_assumption(body: Dict[str, Any]):
    """Create or update an assumption/constraint/explanation record."""
    from src.registry.providers.assumption_provider import AssumptionProvider
    from src.registry.models.assumption import Assumption
    provider = AssumptionProvider()
    try:
        item = Assumption(**body)
        result = await provider.upsert(item)
        return Envelope(data=result.model_dump())
    except Exception as e:
        return Envelope(status="error", data=error_response("server_error", str(e)))


@router.delete("/assumptions/{assumption_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assumption(
    assumption_id: str,
    client_id: str = Query(...),
):
    """Delete an assumption/constraint/explanation record by id."""
    from src.registry.providers.assumption_provider import AssumptionProvider
    provider = AssumptionProvider()
    try:
        await provider.delete(assumption_id, client_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Clients (multi-tenant)
# ---------------------------------------------------------------------------

# Fallback list used when Supabase business_contexts is unavailable.
# Production clients only — bicycle/hess are local-only demo contexts and were
# removed from production business_contexts; keep this list in sync so a
# transient Supabase read failure can't reintroduce them on the login screen.
_FALLBACK_CLIENTS = [
    {
        "id": "apex_lubricants",
        "name": "Apex Lubricants",
        "industry": "Specialty Chemicals & Automotive Aftermarket",
        "data_product_ids": ["dp_lubricants_snowflake"],
    },
    {
        "id": "lubricants",
        "name": "Lubricants Business",
        "industry": "Oil & Gas / Specialty Chemicals",
        "data_product_ids": ["dp_lubricants_financials"],
    },
]


@router.get("/clients", response_model=Envelope)
async def list_clients():
    """Return available client/tenant configurations from Supabase business_contexts.

    Reads live from the business_contexts table so newly onboarded clients appear
    immediately without a code deployment. Falls back to the hardcoded list if
    Supabase is unavailable.
    """
    try:
        factory = RegistryFactory()
        provider = factory.get_business_context_provider()
        if provider is not None:
            rows = await provider.list_contexts()
            if rows:
                clients = [
                    {
                        "id": row.get("id"),
                        "name": row.get("name") or row.get("id"),
                        "industry": row.get("industry", ""),
                        "data_product_ids": row.get("data_product_ids") or [],
                    }
                    for row in rows
                    if row.get("id")
                ]
                if clients:
                    return wrap(clients)
    except Exception:
        pass  # fall through to hardcoded fallback

    return wrap(_FALLBACK_CLIENTS)


@router.post("/clients", response_model=Envelope)
async def create_client(payload: dict):
    """Upsert a client/tenant in business_contexts.

    Used by the System Admin onboarding flow to create a new client workspace
    before seeding KPIs, principals, etc.  Idempotent — re-posting the same
    id updates name/industry without duplicating the row.
    """
    client_id = (payload.get("id") or "").strip().lower().replace(" ", "_")
    if not client_id:
        raise HTTPException(status_code=422, detail="id is required")

    row = {
        "id": client_id,
        "name": payload.get("name") or client_id,
        "industry": payload.get("industry") or "",
        "data_product_ids": payload.get("data_product_ids") or [],
    }

    try:
        factory = RegistryFactory()
        provider = factory.get_business_context_provider()
        if provider is not None:
            await provider.upsert_context(row)
            return wrap(row)
    except Exception as exc:
        logger.warning("business_contexts upsert failed: %s", exc)
        # Fall through — return the row optimistically so the UI can proceed
        # even if persistence fails (e.g. provider missing method)

    return wrap(row)


# ---------------------------------------------------------------------------
# Theory layer exhibit (Phase 17) — assembled Spine / Causal Edges / Ports
# ---------------------------------------------------------------------------


def _epistemic_summary(causal_edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Count what is CERTAIN vs ASSERTED vs ASSUMED, from recorded fields only.

    The exhibit's whole thesis is "what we know versus what we assumed"
    (DEVELOPMENT_PLAN.md Phase 17), so these counts come from `basis` /
    `causal_rung` / `provenance` — all recorded fields, never inferred.

    Identities are counted SEPARATELY from causal claims and never fold into a
    "confirmed" total: an accounting identity is arithmetic, not verified
    theory, and letting it inflate the confirmed count would manufacture
    exactly the impression the density gate exists to prevent.
    """
    identities = [e for e in causal_edges if e.get("basis") == "accounting_identity"]
    claims = [e for e in causal_edges if e.get("basis") != "accounting_identity"]
    tested = [e for e in claims if e.get("causal_rung") == "intervention_tested"]
    template = [e for e in claims if e.get("provenance") == "template"]
    asserted = [e for e in claims if e not in tested and e not in template]
    return {
        "identities": len(identities),
        "causal_claims": len(claims),
        "tested": len(tested),
        "asserted": len(asserted),
        "template": len(template),
        # DEVELOPMENT_PLAN.md Phase 17's stated bar: confirmed
        # (intervention_tested) edges outnumber template/unconfirmed ones.
        # Reported as a fact; the caller decides what to do with a False.
        "density_gate_passed": len(tested) > (len(claims) - len(tested)),
    }


@router.get("/theory-layer/{kpi_id}", response_model=Envelope)
async def get_theory_layer(
    kpi_id: str,
    client_id: str = Query(...),
    include_values: bool = Query(False, description="Execute each spine KPI's SQL for live values (costs real warehouse queries)"),
    timeframe: str = Query("year_to_date", description="Timeframe for the current period; the prior period is the SAME SPAN shifted back one period (comparison_period=True), never a full-prior-period token"),
):
    """Assemble the theory-layer exhibit for one KPI: Spine, Causal Edges, Ports.

    Structure follows docs/architecture/kpi_relationship_basis_design.md §5:
    each section is CONDITIONAL (present only with real content) rather than a
    fixed four-quadrant grid, because a grid reserving space for all four
    concepts recreates Phase 17's own delivery-rule failure one level down.
    Assumptions is deliberately NOT a section — a held/falsified verdict is a
    marker on an edge, so verdicts ride along on each causal edge instead.

    `include_values=False` by default: structure and provenance are free, but
    real KPI values cost live warehouse queries. Values are strictly optional —
    a spine with no numbers is honest; a spine with WRONG numbers is the exact
    failure Phase 17's T1 gate exists to prevent.
    """
    from src.registry.providers.kpi_decomposition_provider import KPIDecompositionProvider
    from src.registry.providers.kpi_relationship_provider import KPIRelationshipProvider
    from src.registry.providers.port_provider import PortProvider

    notes: List[str] = []
    try:
        factory = RegistryFactory()
        kpi_provider = factory.get_provider("kpi")

        def _kpi(kid: str):
            return kpi_provider.get(kid, client_id=client_id) if kpi_provider else None

        primary = _kpi(kpi_id)

        # --- Spine: arithmetic parentage (Phase 17 T2) ---------------------
        decomp = await KPIDecompositionProvider().get_full_tree(kpi_id, client_id)
        node_ids: List[str] = []
        for e in decomp:
            for nid in (e.parent_kpi_id, e.child_kpi_id, e.weight_kpi_id):
                if nid and nid not in node_ids:
                    node_ids.append(nid)

        # Current AND prior period. The prior half is not optional garnish: the
        # Spine's chart is a VARIANCE bridge, not a composition bridge
        # (kpi_relationship_basis_design.md §4 — "the framing question is 'why
        # did this move'... A composition bridge doesn't answer that at all"),
        # and a variance bridge is uncomputable without both periods.
        # generate_sql_for_kpi(comparison_period=...) is the same proven pattern
        # A9_Deep_Analysis_Agent._fetch_neighbour_snapshot already uses, so DPA's
        # own backend routing is reused rather than reimplemented.
        values: Dict[str, float] = {}
        prior_values: Dict[str, float] = {}
        if include_values and node_ids:
            try:
                # get_orchestrator is a METHOD on an async-acquired AgentRuntime,
                # not a module function — the first attempt called it as
                # `runtime.get_orchestrator()` and this block's own non-fatal
                # note is what surfaced the mistake, rather than silently
                # rendering an empty spine.
                from src.api.runtime import get_agent_runtime
                _rt = await get_agent_runtime()
                orchestrator = _rt.get_orchestrator()
                dpa = await orchestrator.get_agent("A9_Data_Product_Agent")

                # A timeframe is REQUIRED, not optional garnish: with none, both
                # calls return the same all-time rollup and the bridge reports a
                # flat 0.00pp move that closes perfectly — a wrong answer wearing
                # the costume of a right one. Found live: prior == current on
                # every node. `comparison_period=True` shifts THIS span back one
                # period (TimeFilter.previous_period_name's docstring warns at
                # length against the full-prior-period alternative — a real
                # production briefing carried two baselines and understated a
                # decline by ~40% that way).
                async def _val(k, comparison: bool) -> Optional[float]:
                    gen = await dpa.generate_sql_for_kpi(k, timeframe=timeframe, comparison_period=comparison)
                    if not gen.get("success"):
                        return None
                    res = await dpa.execute_sql(gen.get("sql"), data_product_id=getattr(k, "data_product_id", None))
                    rows = (res or {}).get("rows") or []
                    if not rows:
                        return None
                    first = rows[0]
                    v = list(first.values())[0] if isinstance(first, dict) else first[0]
                    return float(v) if isinstance(v, (int, float)) else None

                for nid in node_ids:
                    k = _kpi(nid)
                    if k is None:
                        continue
                    cur = await _val(k, False)
                    prev = await _val(k, True)
                    if cur is not None:
                        values[nid] = cur
                    if prev is not None:
                        prior_values[nid] = prev
            except Exception as exc:
                notes.append(f"Live values unavailable ({exc}) - spine renders structure only.")

        spine_nodes = []
        for nid in node_ids:
            k = _kpi(nid)
            spine_nodes.append({
                "kpi_id": nid,
                "name": getattr(k, "name", nid) if k else nid,
                "unit": getattr(k, "unit", None) if k else None,
                "unit_class": getattr(k, "unit_class", None) if k else None,
                "additive_across_dimensions": getattr(k, "additive_across_dimensions", None) if k else None,
                "aggregation_method": getattr(k, "aggregation_method", None) if k else None,
                "scope_eligible": getattr(k, "scope_eligible", None) if k else None,
                "value": values.get(nid),
                "prior_value": prior_values.get(nid),
            })

        # Reconciliation is the spine's own integrity check — a derived tree
        # that does not reproduce its parent is a wrong number in a diagram,
        # which Phase 17 calls harder to challenge than a wrong number in a
        # table. Only computable when values were actually fetched.
        reconciliation = None
        bridge = None
        if values:
            from src.analysis.decomposition import check_tree_reconciles, variance_bridge
            direct = [e for e in decomp if e.parent_kpi_id == kpi_id]
            violation = check_tree_reconciles(
                kpi_id, direct, values,
                parent_unit_class=getattr(primary, "unit_class", None) if primary else None,
            )
            reconciliation = {"ok": violation is None, "detail": violation}

            # The variance bridge — the Spine's actual chart per §4. Computed
            # generically from the recorded decomposition operations, not from
            # a hardcoded margin formula: §4 left "which arithmetic" as an open
            # gap, and T2's operation/sign fields close it for any tree.
            unit_classes = {n["kpi_id"]: n["unit_class"] for n in spine_nodes if n["unit_class"]}
            bridge = variance_bridge(
                kpi_id, decomp, values, prior_values, unit_classes=unit_classes,
            )
            if bridge is None and prior_values:
                notes.append(
                    "Variance bridge unavailable — prior-period values missing for one or more "
                    "spine inputs, so the move cannot be decomposed exactly."
                )

        # --- Causal edges (Phase 15 D/E + basis, §2) -----------------------
        neighbourhood = await KPIRelationshipProvider().get_causal_neighbourhood(kpi_id, client_id)
        causal_edges = []
        for rel, hops in neighbourhood:
            d = rel.model_dump()
            d["hops"] = hops
            # Assumptions ride along as a marker per §5, never as a section.
            # No graded verdict attaches to an EDGE today — T3 grades
            # assumptions per SOLUTION — so this is explicitly pending rather
            # than silently absent.
            d["verdict"] = None
            causal_edges.append(d)

        # --- Ports (Phase 17 T4) -------------------------------------------
        port_rows = await PortProvider().get_all(client_id)
        # Scope = the spine PLUS the causal neighbourhood, not the spine alone.
        # theory_layer_design.md §7 describes ports as "off-tree nodes docking
        # into tree nodes" — and the anchor case proves the point: the Base Oil
        # port docks into base_oil_cost, which reaches gross_margin_pct through
        # CAUSAL edges (base_oil_cost -> cogs -> gross_margin_pct, 2 hops), not
        # through the arithmetic decomposition. Scoping to the spine alone
        # silently dropped the one port that exists — and it is precisely the
        # 11F anchor scenario §2.3 says this exhibit should render literally.
        reachable = set(node_ids) | {kpi_id}
        for e in causal_edges:
            reachable.add(e["kpi_id"])
            reachable.add(e["related_kpi_id"])
        ports = [p.model_dump() for p in port_rows if p.linked_kpi_id in reachable]

        summary = _epistemic_summary(causal_edges)
        if not summary["density_gate_passed"]:
            notes.append(
                f"Causal Edges density gate NOT passed: {summary['tested']} tested vs "
                f"{summary['causal_claims'] - summary['tested']} unconfirmed claim(s). "
                "Per DEVELOPMENT_PLAN.md Phase 17 this bar is cleared by real accretion "
                "(VA verdicts), never by seeding."
            )

        return Envelope(data={
            "kpi_id": kpi_id,
            "kpi_name": getattr(primary, "name", kpi_id) if primary else kpi_id,
            "client_id": client_id,
            "spine": {
                "nodes": spine_nodes,
                "edges": [e.model_dump() for e in decomp],
                "reconciliation": reconciliation,
                "variance_bridge": bridge,
            },
            "causal_edges": causal_edges,
            "ports": ports,
            "epistemic_summary": summary,
            "values_included": bool(values),
            "notes": notes,
        })
    except Exception as e:
        logger.warning("theory-layer assembly failed for %s/%s: %s", client_id, kpi_id, e)
        return Envelope(status="error", data=error_response("server_error", str(e)))
