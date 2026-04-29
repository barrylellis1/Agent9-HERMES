from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

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
    factory = RegistryFactory()
    if not factory.is_initialized:
        await factory.initialize()
    return factory


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
            rows = resp.json()
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

    items: List[KPI] = provider.get_all()
    if domain:
        items = [kpi for kpi in items if kpi.domain == domain]
    if owner_role:
        items = [kpi for kpi in items if kpi.owner_role == owner_role]
    if tag:
        items = [kpi for kpi in items if tag in getattr(kpi, "tags", [])]
    if client_id:
        items = [kpi for kpi in items if getattr(kpi, "client_id", None) == client_id]

    return wrap(items)


@router.get("/kpis/{kpi_id}", response_model=Envelope)
async def get_kpi(kpi_id: str, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_kpi_provider()
    kpi = provider.get(kpi_id) if provider else None
    if kpi is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"KPI '{kpi_id}' not found"))
    return wrap(kpi)


@router.post("/kpis", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_kpi(payload: KPI, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_kpi_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "KPI provider unavailable"))
    if provider.get(payload.id):
        raise HTTPException(status.HTTP_409_CONFLICT, error_response("duplicate", f"KPI '{payload.id}' exists"))
    provider.register(payload)
    return wrap(payload)


@router.put("/kpis/{kpi_id}", response_model=Envelope)
async def replace_kpi(kpi_id: str, payload: KPI, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_kpi_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "KPI provider unavailable"))
    replacement = payload.model_copy(update={"id": kpi_id})
    provider.upsert(replacement)
    return wrap(replacement)


@router.patch("/kpis/{kpi_id}", response_model=Envelope)
async def update_kpi(
    kpi_id: str,
    payload: Dict[str, Any],
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_kpi_provider()
    kpi = provider.get(kpi_id) if provider else None
    if kpi is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"KPI '{kpi_id}' not found"))
    updated = kpi.model_copy(update=payload)
    provider.upsert(updated)
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
    kpi = provider.get(kpi_id)
    if kpi is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"KPI '{kpi_id}' not found"))

    if client_id:
        kpi_client = getattr(kpi, "client_id", None)
        if kpi_client != client_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, error_response("forbidden", f"KPI belongs to client '{kpi_client}', not '{client_id}'"))

    if not provider.delete(kpi_id):
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
                    rows = resp.json()
                    if rows:
                        items = [PrincipalProfile.model_validate(r) for r in rows]
                        return wrap(items)
        except Exception as e:
            logger.warning("Direct Supabase principal lookup failed for client_id=%s: %s", client_id, e)
        # Fall through to in-memory provider if Supabase query fails

    provider = factory.get_principal_profile_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Principal provider unavailable"))
    items: List[PrincipalProfile] = provider.get_all()
    if client_id:
        items = [p for p in items if getattr(p, "client_id", None) == client_id]
    return wrap(items)


@router.get("/principals/{principal_id}", response_model=Envelope)
async def get_principal(principal_id: str, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_principal_profile_provider()
    profile = provider.get(principal_id) if provider else None
    # Fallback: query Supabase directly if not in the in-memory provider
    if profile is None:
        profile = await _fetch_principal_from_supabase(principal_id)
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Principal '{principal_id}' not found"))
    return wrap(profile)


@router.post("/principals", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_principal(payload: PrincipalProfile, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_principal_profile_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Principal provider unavailable"))
    if provider.get(payload.id):
        raise HTTPException(status.HTTP_409_CONFLICT, error_response("duplicate", f"Principal '{payload.id}' exists"))
    provider.register(payload)
    return wrap(payload)


@router.put("/principals/{principal_id}", response_model=Envelope)
async def replace_principal(principal_id: str, payload: PrincipalProfile, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_principal_profile_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Principal provider unavailable"))
    replacement = payload.model_copy(update={"id": principal_id})
    provider.upsert(replacement)
    return wrap(replacement)


@router.patch("/principals/{principal_id}", response_model=Envelope)
async def update_principal(principal_id: str, payload: Dict[str, Any], factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_principal_profile_provider()
    profile = provider.get(principal_id) if provider else None
    if profile is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Principal '{principal_id}' not found"))
    updated = profile.model_copy(update=payload)
    provider.upsert(updated)
    return wrap(updated)


@router.delete("/principals/{principal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_principal(principal_id: str, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_principal_profile_provider()
    if provider is None or not provider.delete(principal_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Principal '{principal_id}' not found"))


# ---------------------------------------------------------------------------
# Data Products
# ---------------------------------------------------------------------------


@router.get("/data-products", response_model=Envelope)
async def list_data_products(
    domain: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    business_process_id: Optional[str] = Query(None),
    include_staging: bool = Query(True, description="Include staging products"),
    client_id: Optional[str] = Query(None),
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_data_product_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Data product provider unavailable"))

    items: List[DataProduct] = provider.get_all()
    
    # Include staging products if requested
    if include_staging:
        import os
        import yaml
        staging_dir = "src/registry_references/data_product_registry/staging"
        if os.path.exists(staging_dir):
            for filename in os.listdir(staging_dir):
                if filename.endswith('.yaml') and filename != 'README.md':
                    try:
                        filepath = os.path.join(staging_dir, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            contract_data = yaml.safe_load(f)
                            if contract_data:
                                product_id = os.path.splitext(filename)[0]
                                staging_product = DataProduct.from_yaml_contract(contract_data, product_id)
                                # Mark as staging in metadata
                                staging_product.metadata['staging'] = True
                                
                                # Replace existing product with staging version if it exists
                                existing_idx = next((i for i, dp in enumerate(items) if dp.id == product_id), None)
                                if existing_idx is not None:
                                    items[existing_idx] = staging_product
                                else:
                                    items.append(staging_product)
                    except Exception as e:
                        # Skip invalid staging files
                        pass
    
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
    if client_id:
        items = [dp for dp in items if getattr(dp, "client_id", None) == client_id]

    return wrap(items)


@router.get("/data-products/{data_product_id}", response_model=Envelope)
async def get_data_product(data_product_id: str, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_data_product_provider()
    
    # First check staging directory for this product
    import os
    import yaml
    staging_dir = "src/registry_references/data_product_registry/staging"
    staging_file = os.path.join(staging_dir, f"{data_product_id}.yaml")
    
    if os.path.exists(staging_file):
        try:
            with open(staging_file, 'r', encoding='utf-8') as f:
                contract_data = yaml.safe_load(f)
                if contract_data:
                    data_product = DataProduct.from_yaml_contract(contract_data, data_product_id)
                    data_product.metadata['staging'] = True
                    return wrap(data_product)
        except Exception as e:
            # Fall through to registry lookup if staging file is invalid
            pass
    
    # Fall back to registry provider
    data_product = provider.get(data_product_id) if provider else None
    if data_product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Data product '{data_product_id}' not found"))
    return wrap(data_product)


@router.post("/data-products", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_data_product(payload: DataProduct, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_data_product_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Data product provider unavailable"))
    if provider.get(payload.id):
        raise HTTPException(status.HTTP_409_CONFLICT, error_response("duplicate", f"Data product '{payload.id}' exists"))
    provider.register(payload)
    return wrap(payload)


@router.put("/data-products/{data_product_id}", response_model=Envelope)
async def replace_data_product(data_product_id: str, payload: DataProduct, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_data_product_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Data product provider unavailable"))
    replacement = payload.model_copy(update={"id": data_product_id})
    provider.upsert(replacement)
    return wrap(replacement)


@router.patch("/data-products/{data_product_id}", response_model=Envelope)
async def update_data_product(
    data_product_id: str,
    payload: Dict[str, Any],
    factory: RegistryFactory = Depends(get_registry_factory),
):
    provider = factory.get_data_product_provider()
    data_product = provider.get(data_product_id) if provider else None
    if data_product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Data product '{data_product_id}' not found"))
    updated = data_product.model_copy(update=payload)
    provider.upsert(updated)
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
    dp = provider.get(data_product_id)
    if dp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Data product '{data_product_id}' not found"))

    if client_id:
        dp_client = getattr(dp, "client_id", None)
        if dp_client != client_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, error_response("forbidden", f"Data product belongs to client '{dp_client}', not '{client_id}'"))

    if not provider.delete(data_product_id):
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

    items: List[BusinessProcess] = provider.get_all()
    if domain:
        items = [bp for bp in items if bp.domain == domain]
    if owner_role:
        items = [bp for bp in items if bp.owner_role == owner_role]
    if tag:
        items = [bp for bp in items if tag in getattr(bp, "tags", [])]
    if client_id:
        items = [bp for bp in items if getattr(bp, "client_id", None) == client_id]

    return wrap(items)


@router.get("/business-processes/{process_id}", response_model=Envelope)
async def get_business_process(process_id: str, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_business_process_provider()
    process = provider.get(process_id) if provider else None
    if process is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Business process '{process_id}' not found"))
    return wrap(process)


@router.post("/business-processes", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_business_process(payload: BusinessProcess, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_business_process_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Business process provider unavailable"))
    if provider.get(payload.id):
        raise HTTPException(status.HTTP_409_CONFLICT, error_response("duplicate", f"Business process '{payload.id}' exists"))
    provider.register(payload)
    return wrap(payload)


@router.put("/business-processes/{process_id}", response_model=Envelope)
async def replace_business_process(process_id: str, payload: BusinessProcess, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_business_process_provider()
    if provider is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("provider_missing", "Business process provider unavailable"))
    replacement = payload.model_copy(update={"id": process_id})
    provider.upsert(replacement)
    return wrap(replacement)


@router.patch("/business-processes/{process_id}", response_model=Envelope)
async def update_business_process(process_id: str, payload: Dict[str, Any], factory: RegistryFactory = Depends(get_registry_factory)):
    provider = factory.get_business_process_provider()
    process = provider.get(process_id) if provider else None
    if process is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Business process '{process_id}' not found"))
    updated = process.model_copy(update=payload)
    provider.upsert(updated)
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
    bp = provider.get(process_id)
    if bp is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Business process '{process_id}' not found"))

    if client_id:
        bp_client = getattr(bp, "client_id", None)
        if bp_client != client_id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, error_response("forbidden", f"Business process belongs to client '{bp_client}', not '{client_id}'"))

    if not provider.delete(process_id):
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
async def list_terms(factory: RegistryFactory = Depends(get_registry_factory)):
    provider = _get_glossary_provider(factory)
    return wrap(provider.get_all())


@router.get("/glossary/{term_name}", response_model=Envelope)
async def get_term(term_name: str, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = _get_glossary_provider(factory)
    term = provider.get_term(term_name)
    if term is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Term '{term_name}' not found"))
    return wrap(term)


@router.post("/glossary", response_model=Envelope, status_code=status.HTTP_201_CREATED)
async def create_term(payload: BusinessTerm, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = _get_glossary_provider(factory)
    provider.add_term(payload)
    return wrap(payload)


@router.put("/glossary/{term_name}", response_model=Envelope)
async def replace_term(term_name: str, payload: BusinessTerm, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = _get_glossary_provider(factory)
    replacement = payload.model_copy(update={"name": term_name})
    provider.upsert_term(replacement)
    return wrap(replacement)


@router.delete("/glossary/{term_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_term(term_name: str, factory: RegistryFactory = Depends(get_registry_factory)):
    provider = _get_glossary_provider(factory)
    if not provider.delete_term(term_name):
        raise HTTPException(status.HTTP_404_NOT_FOUND, error_response("not_found", f"Term '{term_name}' not found"))


# ---------------------------------------------------------------------------
# Clients (multi-tenant)
# ---------------------------------------------------------------------------

# Fallback list used when Supabase business_contexts is unavailable.
_FALLBACK_CLIENTS = [
    {
        "id": "lubricants",
        "name": "Lubricants Business",
        "industry": "Oil & Gas / Specialty Chemicals",
        "data_product_ids": ["dp_lubricants_financials"],
    },
    {
        "id": "bicycle",
        "name": "Global Bike Inc.",
        "industry": "Retail & Manufacturing",
        "data_product_ids": ["fi_star_schema"],
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
