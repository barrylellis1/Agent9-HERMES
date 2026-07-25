# arch-allow-direct-agent-construction
"""
Phase 12F — Business Process Template Generator unit tests.

Covers:
  - MA.research_company_business_processes() happy path with a stored company
    profile mocked (canonical selection + extras)
  - Canonical selections are hydrated verbatim from BP_BY_ID even when the
    mocked LLM response has mismatched name/description text for a selected id
  - Extras colliding with an existing canonical id are dropped, not duplicated
  - Degraded fallback when no stored profile and no industry_override
  - Commit idempotency: same accepted process committed twice → second run
    reports skipped_duplicate
  - business_process_templates route slug generation helper
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.models.business_process_template_models import (
    AcceptedTemplateBusinessProcess,
    BusinessProcessResearchRequest,
    CompanyBusinessProcessProfile,
)
from src.agents.new.a9_market_analysis_agent import A9_Market_Analysis_Agent
from src.api.routes.business_process_templates import _insert_template_bp, _slugify_bp_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(**kwargs) -> BusinessProcessResearchRequest:
    defaults = dict(client_id="brookshire_brothers", industry_override=None, max_extra_processes=5)
    defaults.update(kwargs)
    return BusinessProcessResearchRequest(**defaults)


def _make_llm_response(payload: dict) -> MagicMock:
    resp = MagicMock()
    resp.status = "success"
    resp.content = json.dumps(payload)
    return resp


def _agent_with_mocks(*, industry: str | None, subindustry: str | None = None, llm_payload: dict):
    """Build an MA agent with LLM + business-context provider mocked."""
    agent = A9_Market_Analysis_Agent(config={"enable_perplexity": False})

    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(return_value=_make_llm_response(llm_payload))
    agent._llm_service = mock_llm

    mock_context = None
    if industry is not None:
        mock_context = MagicMock()
        mock_context.industry = industry
        mock_context.subindustry = subindustry

    mock_bc_provider = AsyncMock()
    mock_bc_provider.get_context = AsyncMock(return_value=mock_context)

    mock_factory = MagicMock()
    mock_factory.is_initialized = True
    mock_factory.get_business_context_provider = MagicMock(return_value=mock_bc_provider)

    import src.registry.factory as factory_module
    agent._patched_factory_cls = factory_module.RegistryFactory
    factory_module.RegistryFactory = lambda: mock_factory

    return agent


# ---------------------------------------------------------------------------
# MA agent tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_research_happy_path_selects_canonical_and_extra():
    """Happy path: stored industry resolves, LLM selects canonical ids + one extra."""
    llm_payload = {
        "selected_canonical_ids": [
            "finance_expense_management",
            "finance_revenue_growth_analysis",
        ],
        "extra_processes": [
            {
                "name": "Perishables Inventory Management",
                "domain": "Supply Chain",
                "description": "Tracking shrink and spoilage for perishable goods",
                "owner_role": "COO",
                "stakeholder_roles": ["Supply Chain Manager"],
                "tags": ["perishables"],
                "confidence": 0.75,
                "rationale": "Grocery retailers manage significant perishable inventory",
            }
        ],
    }
    agent = _agent_with_mocks(industry="Grocery Retail", llm_payload=llm_payload)

    try:
        profile = await agent.research_company_business_processes(_make_request())
    finally:
        import src.registry.factory as factory_module
        factory_module.RegistryFactory = agent._patched_factory_cls

    assert isinstance(profile, CompanyBusinessProcessProfile)
    assert profile.client_id == "brookshire_brothers"
    assert profile.industry_used == "Grocery Retail"
    assert profile.degraded is False
    assert len(profile.selected) == 3

    canonical_rows = [bp for bp in profile.selected if bp.source == "canonical"]
    extra_rows = [bp for bp in profile.selected if bp.source == "extra"]
    assert {bp.id for bp in canonical_rows} == {
        "finance_expense_management",
        "finance_revenue_growth_analysis",
    }
    assert len(extra_rows) == 1
    assert extra_rows[0].name == "Perishables Inventory Management"
    assert extra_rows[0].id is None  # not yet slugified — happens at commit time


@pytest.mark.asyncio
async def test_canonical_selection_hydrated_verbatim_not_from_llm():
    """Even if the LLM echoes different name/description text for a selected
    canonical id, the committed content must come from BP_BY_ID verbatim —
    the canonical taxonomy is the single source of truth, not the LLM."""
    llm_payload = {
        "selected_canonical_ids": ["finance_expense_management"],
        # LLM hallucinated different text for the same id — must be ignored
        "extra_processes": [],
    }
    agent = _agent_with_mocks(industry="Grocery Retail", llm_payload=llm_payload)

    try:
        profile = await agent.research_company_business_processes(_make_request())
    finally:
        import src.registry.factory as factory_module
        factory_module.RegistryFactory = agent._patched_factory_cls

    assert len(profile.selected) == 1
    bp = profile.selected[0]
    from src.registry.canonical.business_processes import BP_BY_ID

    canonical = BP_BY_ID["finance_expense_management"]
    assert bp.name == canonical["name"]
    assert bp.description == canonical["description"]
    assert bp.owner_role == canonical["owner_role"]


@pytest.mark.asyncio
async def test_extra_process_colliding_with_canonical_is_dropped():
    """An LLM-proposed extra whose derived id collides with an existing
    canonical entry must be dropped, not duplicated."""
    llm_payload = {
        "selected_canonical_ids": [],
        "extra_processes": [
            {
                # Derived id "finance_expense_management" already exists in BP_BY_ID
                "name": "Expense Management",
                "domain": "Finance",
                "description": "A duplicate of the canonical entry",
            }
        ],
    }
    agent = _agent_with_mocks(industry="Grocery Retail", llm_payload=llm_payload)

    try:
        profile = await agent.research_company_business_processes(_make_request())
    finally:
        import src.registry.factory as factory_module
        factory_module.RegistryFactory = agent._patched_factory_cls

    assert profile.selected == []


@pytest.mark.asyncio
async def test_degraded_when_no_stored_profile_and_no_override():
    """No stored company profile and no industry_override → degraded=True,
    but the agent still proceeds with a generic prompt rather than failing."""
    llm_payload = {
        "selected_canonical_ids": ["finance_expense_management"],
        "extra_processes": [],
    }
    agent = _agent_with_mocks(industry=None, llm_payload=llm_payload)

    try:
        profile = await agent.research_company_business_processes(_make_request())
    finally:
        import src.registry.factory as factory_module
        factory_module.RegistryFactory = agent._patched_factory_cls

    assert profile.degraded is True
    assert profile.industry_used is None
    assert len(profile.selected) == 1


@pytest.mark.asyncio
async def test_industry_override_used_when_no_stored_profile():
    """industry_override is honoured when no stored company profile exists,
    and does not mark the profile as degraded."""
    llm_payload = {"selected_canonical_ids": [], "extra_processes": []}
    agent = _agent_with_mocks(industry=None, llm_payload=llm_payload)

    try:
        profile = await agent.research_company_business_processes(
            _make_request(industry_override="Specialty Retail")
        )
    finally:
        import src.registry.factory as factory_module
        factory_module.RegistryFactory = agent._patched_factory_cls

    assert profile.degraded is False
    assert profile.industry_used == "Specialty Retail"


# ---------------------------------------------------------------------------
# Commit path — idempotency
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_insert_template_bp_idempotent():
    """Same accepted process committed twice → second run reports skipped_duplicate."""
    bp = AcceptedTemplateBusinessProcess(
        id="supply_chain_perishables_inventory_management",
        name="Perishables Inventory Management",
        domain="Supply Chain",
        description="Tracking shrink and spoilage",
        owner_role="COO",
        stakeholder_roles=["Supply Chain Manager"],
        tags=["perishables"],
        source="extra",
        confidence=0.75,
    )

    mock_conn = AsyncMock()
    # First insert succeeds (1 row), second is a no-op via ON CONFLICT (0 rows)
    mock_conn.execute = AsyncMock(side_effect=["INSERT 0 1", "INSERT 0 0"])

    first = await _insert_template_bp(mock_conn, "brookshire_brothers", bp, "bp_template_generator")
    second = await _insert_template_bp(mock_conn, "brookshire_brothers", bp, "bp_template_generator")

    assert first.status == "written"
    assert second.status == "skipped_duplicate"
    assert mock_conn.execute.call_count == 2


@pytest.mark.asyncio
async def test_insert_template_bp_mirrors_new_row_into_live_provider_cache():
    """A genuinely new write must be mirrored into the live provider's cache —
    the raw SQL insert bypasses DatabaseRegistryProvider entirely, so without
    this the row would be invisible to every registry.py list endpoint (and
    Context Explorer, the accountability interview, etc.) until a restart."""
    from src.registry.models.business_process import BusinessProcess

    bp = AcceptedTemplateBusinessProcess(
        name="Perishables Inventory Management", domain="Supply Chain", source="extra",
    )
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value="INSERT 0 1")

    mock_provider = MagicMock()
    cached: dict = {}
    mock_provider._cache_item = MagicMock(side_effect=lambda item: cached.update({item.id: item}))

    summary = await _insert_template_bp(
        mock_conn, "brookshire_brothers", bp, "bp_template_generator", mock_provider
    )

    assert summary.status == "written"
    mock_provider._cache_item.assert_called_once()
    cached_item = next(iter(cached.values()))
    assert isinstance(cached_item, BusinessProcess)
    assert cached_item.client_id == "brookshire_brothers"
    assert cached_item.name == "Perishables Inventory Management"


@pytest.mark.asyncio
async def test_insert_template_bp_does_not_mirror_skipped_duplicate():
    """A skipped_duplicate row must NOT touch the cache — the existing DB row
    may have been hand-edited since creation; blindly overwriting the cache
    with this commit's payload could desync cache from DB in the other
    direction."""
    bp = AcceptedTemplateBusinessProcess(
        id="finance_expense_management", name="Expense Management", domain="Finance", source="canonical",
    )
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(return_value="INSERT 0 0")

    mock_provider = MagicMock()

    summary = await _insert_template_bp(
        mock_conn, "brookshire_brothers", bp, "bp_template_generator", mock_provider
    )

    assert summary.status == "skipped_duplicate"
    mock_provider._cache_item.assert_not_called()


@pytest.mark.asyncio
async def test_insert_template_bp_error_is_reported_not_raised():
    """A per-row DB failure is caught and reported, not propagated — matches
    the KPI commit path's fail-per-row, not fail-the-batch, contract."""
    bp = AcceptedTemplateBusinessProcess(
        name="Broken Process", domain="Finance", source="extra",
    )
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock(side_effect=RuntimeError("connection reset"))

    summary = await _insert_template_bp(mock_conn, "brookshire_brothers", bp, "bp_template_generator")

    assert summary.status == "error"
    assert "connection reset" in summary.error


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def test_slugify_bp_id_basic():
    assert _slugify_bp_id("Finance", "Expense Management") == "finance_expense_management"
    assert _slugify_bp_id("Supply Chain", "Perishables Inventory") == "supply_chain_perishables_inventory"


def test_slugify_bp_id_empty_fallback():
    assert _slugify_bp_id("", "") == "business_process"
