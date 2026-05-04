"""
Company Profile API routes.

Provides a singleton company/business-context profile endpoint for the deployment.
The profile is persisted in Supabase. The row id IS the client_id for all registry tables.

Endpoints:
    GET    /api/v1/company-profile                — load profile + client_id
    POST   /api/v1/company-profile                — first-time create (assigns client_id)
    PUT    /api/v1/company-profile                — full replace
    PATCH  /api/v1/company-profile                — partial update
    POST   /api/v1/company-profile/industry-research — industry benchmarks via Market Analysis Agent
"""
from __future__ import annotations

import logging
import os
import re
import uuid
from typing import Any, Dict, List, Optional
import json as _json_module

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.agents.shared.a9_debate_protocol_models import A9_PS_BusinessContext
from src.registry.factory import RegistryFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/company-profile", tags=["company-profile"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _slugify(name: str) -> str:
    """Derive a client_id slug from an enterprise name.

    Examples:
        "Valvoline Inc."     → "valvoline"
        "Global Bike Inc."   → "global-bike"
        "Acme Corp Ltd."     → "acme-corp"
    """
    # Strip common legal suffixes
    cleaned = re.sub(
        r'\b(inc|corp|ltd|llc|plc|gmbh|co|company|group|holdings?)\b\.?',
        '',
        name,
        flags=re.IGNORECASE,
    )
    # Lowercase, replace runs of non-alphanumeric chars with hyphens, trim
    slug = re.sub(r'[^a-z0-9]+', '-', cleaned.lower()).strip('-')
    return slug[:40] or 'company'


def _get_provider():
    """Return the SupabaseBusinessContextProvider or None."""
    factory = RegistryFactory()
    return factory.get_business_context_provider()


async def _find_active_client_id(provider) -> Optional[str]:
    """Resolve the active client_id for this deployment.

    Resolution order:
    1. ``CLIENT_ID`` environment variable (set by Railway/Vercel for each customer)
    2. First non-demo, non-default row in business_contexts
    3. None (no profile saved yet)
    """
    env_id = os.getenv('CLIENT_ID')
    if env_id:
        return env_id

    rows = await provider.list_contexts(is_demo=False)
    for row in rows:
        row_id = row.get('id') or ''
        if row_id not in ('default', 'lubricants', 'bicycle', ''):
            return row_id

    return None


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class CompanyProfileCreateRequest(A9_PS_BusinessContext):
    """Extends A9_PS_BusinessContext with an optional client_id for the POST body.

    If ``client_id`` is omitted the server will derive it from ``enterprise_name``.
    Once created the client_id is immutable — it is the composite PK anchor for
    all registry tables (kpis, principals, data_products, etc.).
    """
    client_id: Optional[str] = Field(
        None,
        description="Unique client identifier (auto-derived from enterprise_name if not supplied). "
                    "Immutable after creation. Used as composite PK across all registry tables.",
        pattern=r'^[a-z0-9][a-z0-9\-]{0,38}[a-z0-9]$|^[a-z0-9]$',
    )


class IndustryResearchRequest(BaseModel):
    """Request body for the industry-research endpoint."""
    industry: str
    subindustry: Optional[str] = None


class IndustryResearchResponse(BaseModel):
    """Response from the industry-research endpoint."""
    synthesis: str                              # Plain narrative text (paragraphs joined)
    signals: list
    confidence: float
    benchmarks: Optional[Dict[str, Any]] = None  # key_quantitative_benchmarks_summary if present
    themes: Optional[List[str]] = None           # Paragraph themes as bullet headings


# ---------------------------------------------------------------------------
# GET  /api/v1/company-profile
# ---------------------------------------------------------------------------

@router.get("", response_model=Dict[str, Any])
async def get_company_profile(client_id: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Load the company profile for the given client, or the active singleton if unscoped.

    When ``client_id`` is provided (set by the frontend from the active login session)
    the profile for that specific client is returned. This enforces tenant isolation in
    multi-client deployments. Falls back to ``_find_active_client_id()`` for
    single-tenant or env-var scoped deployments.

    Returns the profile dict including ``client_id``, or ``{}`` if no profile
    has been saved yet (HTTP 200 in both cases).
    """
    provider = _get_provider()
    if provider is None:
        logger.warning("Business context provider unavailable; returning empty profile")
        return {}

    # Use the provided client_id (from logged-in session) or fall back to singleton resolution
    active_client_id = client_id or await _find_active_client_id(provider)
    if not active_client_id:
        return {}

    context = await provider.get_context(active_client_id)
    if context is None:
        return {}

    result = context.model_dump(exclude_none=True)
    result['client_id'] = active_client_id   # always surface the client_id to the frontend
    return result


# ---------------------------------------------------------------------------
# POST  /api/v1/company-profile
# ---------------------------------------------------------------------------

@router.post("", response_model=Dict[str, Any])
async def create_company_profile(request: CompanyProfileCreateRequest) -> Dict[str, Any]:
    """Create the company profile and assign the client_id (first-time setup).

    The ``client_id`` is derived from ``enterprise_name`` if not supplied.
    Raises 409 when a profile already exists (use PUT to replace).
    Raises 503 when Supabase is unavailable.
    """
    provider = _get_provider()
    if provider is None:
        raise HTTPException(
            status_code=503,
            detail="Business context provider unavailable (check SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)",
        )

    # Resolve client_id
    client_id = (request.client_id or '').strip()
    if not client_id:
        client_id = _slugify(request.enterprise_name)

    # Guard: reject collision with reserved IDs
    if client_id in ('default', 'lubricants', 'bicycle'):
        raise HTTPException(
            status_code=400,
            detail=f"'{client_id}' is a reserved client ID. Choose a different value.",
        )

    # Guard: already exists
    existing = await provider.get_context(client_id)
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"A profile with client_id='{client_id}' already exists. Use PUT to replace.",
        )

    # Strip client_id from the business context payload before persisting
    context = A9_PS_BusinessContext(**request.model_dump(exclude={'client_id'}))
    success = await provider.create_context(client_id, context)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create company profile")

    result = context.model_dump(exclude_none=True)
    result['client_id'] = client_id
    logger.info(f"Company profile created: client_id='{client_id}', name='{context.enterprise_name}'")
    return result


# ---------------------------------------------------------------------------
# PUT  /api/v1/company-profile
# ---------------------------------------------------------------------------

@router.put("", response_model=Dict[str, Any])
async def replace_company_profile(context: A9_PS_BusinessContext) -> Dict[str, Any]:
    """Full replace of the company profile (upsert).

    Uses the existing client_id from the active profile. Creates a new profile
    under a derived client_id if none exists yet.
    """
    provider = _get_provider()
    if provider is None:
        raise HTTPException(status_code=503, detail="Business context provider unavailable")

    client_id = await _find_active_client_id(provider)

    if client_id is None:
        # No existing profile — create with derived ID
        client_id = _slugify(context.enterprise_name)
        success = await provider.create_context(client_id, context)
    else:
        success = await provider.update_context(client_id, context)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to save company profile")

    result = context.model_dump(exclude_none=True)
    result['client_id'] = client_id
    return result


# ---------------------------------------------------------------------------
# PATCH  /api/v1/company-profile
# ---------------------------------------------------------------------------

@router.patch("", response_model=Dict[str, Any])
async def patch_company_profile(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Partial update of the company profile.

    Merges the supplied fields into the existing profile and validates the
    result against A9_PS_BusinessContext before persisting.
    The ``client_id`` field in the payload is ignored (immutable after creation).

    Raises 404 if no profile exists yet (use POST to create first).
    """
    provider = _get_provider()
    if provider is None:
        raise HTTPException(status_code=503, detail="Business context provider unavailable")

    client_id = await _find_active_client_id(provider)
    if client_id is None:
        raise HTTPException(
            status_code=404,
            detail="No company profile found. Use POST to create one first.",
        )

    existing = await provider.get_context(client_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Company profile not found")

    # client_id is immutable — ignore it in patch payloads
    updates.pop('client_id', None)

    current_data = existing.model_dump(exclude_none=True)
    current_data.update(updates)

    try:
        merged = A9_PS_BusinessContext(**current_data)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid profile data after merge: {exc}")

    success = await provider.update_context(client_id, merged)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update company profile")

    result = merged.model_dump(exclude_none=True)
    result['client_id'] = client_id
    return result


# ---------------------------------------------------------------------------
# POST  /api/v1/company-profile/industry-research
# ---------------------------------------------------------------------------

@router.post("/industry-research", response_model=IndustryResearchResponse)
async def industry_research(request: IndustryResearchRequest) -> IndustryResearchResponse:
    """Return industry benchmarks and signals via the Market Analysis Agent.

    The agent uses Perplexity (when configured) for live web search and falls
    back to LLM-only synthesis when the key is absent.
    """
    try:
        from src.agents.new.a9_market_analysis_agent import A9_Market_Analysis_Agent
        from src.agents.models.market_analysis_models import MarketAnalysisRequest
        from src.agents.agent_config_models import A9_Market_Analysis_Agent_Config

        config = A9_Market_Analysis_Agent_Config()
        agent = await A9_Market_Analysis_Agent.create(config.model_dump())
        await agent.connect()

        industry_label = request.industry
        if request.subindustry:
            industry_label = f"{request.industry} / {request.subindustry}"

        ma_request = MarketAnalysisRequest(
            session_id=str(uuid.uuid4()),
            kpi_name="industry benchmarks",
            kpi_context=(
                f"Provide industry benchmarks, key performance indicators, and strategic "
                f"context for the {industry_label} sector."
            ),
            industry=industry_label,
        )

        response = await agent.analyze_market(ma_request)
        await agent.disconnect()

        signals_list = [
            {"title": s.title, "summary": s.summary, "url": s.url}
            for s in response.signals
        ]

        # Parse synthesis — the LLM may return a structured dict/JSON or plain text.
        synthesis_text = response.synthesis
        benchmarks: Optional[Dict[str, Any]] = None
        themes: Optional[List[str]] = None

        parsed: Optional[Dict[str, Any]] = None
        if isinstance(synthesis_text, dict):
            parsed = synthesis_text
        else:
            import json as _json
            try:
                candidate = str(synthesis_text).strip()
                # Handle Python-style dicts (single quotes) by trying ast.literal_eval first
                import ast as _ast
                try:
                    parsed = _ast.literal_eval(candidate)
                except Exception:
                    parsed = _json.loads(candidate)
            except Exception:
                pass  # synthesis is already plain text

        if parsed and isinstance(parsed, dict):
            eb = parsed.get("executive_briefing", {})
            paragraphs = eb.get("paragraphs", [])
            if paragraphs:
                synthesis_text = "\n\n".join(
                    p.get("content", "") for p in paragraphs if p.get("content")
                )
                themes = [p.get("theme", "") for p in paragraphs if p.get("theme")]
            benchmarks = eb.get("key_quantitative_benchmarks_summary") or parsed.get(
                "key_quantitative_benchmarks_summary"
            )

        return IndustryResearchResponse(
            synthesis=synthesis_text if isinstance(synthesis_text, str) else str(synthesis_text),
            signals=signals_list,
            confidence=response.confidence,
            benchmarks=benchmarks,
            themes=themes,
        )

    except Exception as exc:
        logger.error("industry_research failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
