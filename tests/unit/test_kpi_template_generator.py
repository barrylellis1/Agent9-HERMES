# arch-allow-direct-agent-construction
"""
Phase 12A — Company Intelligence KPI Template Generator unit tests.

Covers:
  - MA.research_company_kpi_profile() happy path with Perplexity mocked
  - MA fallback when Perplexity is disabled (degraded=True, all 'inferred')
  - MA fallback when all 4 parallel searches return empty/error
  - SA agent guard skips KPIs with status='template' during registry load
  - kpi_templates route slug generation helper
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.agents.models.kpi_template_models import (
    CompanyKPIProfile,
    CompanyResearchRequest,
)
from src.agents.new.a9_market_analysis_agent import A9_Market_Analysis_Agent
from src.api.routes.kpi_templates import _slugify_kpi_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(**kwargs) -> CompanyResearchRequest:
    defaults = dict(
        company_name="Valvoline Inc.",
        client_id="lubricants",
        industry_hint="Specialty Chemicals",
        sub_sector="Industrial Lubricants",
        business_description="B2B distributor of industrial lubricants.",
        max_kpis=10,
    )
    defaults.update(kwargs)
    return CompanyResearchRequest(**defaults)


def _make_llm_response(payload: dict) -> MagicMock:
    """Build a mock LLM response carrying a JSON payload."""
    resp = MagicMock()
    resp.status = "success"
    resp.content = json.dumps(payload)
    return resp


def _fixture_profile_payload() -> dict:
    """A realistic synthesized profile the LLM might return."""
    return {
        "industry_inferred": "Specialty Chemicals — Industrial Lubricants",
        "is_public": True,
        "research_sources": [
            "Company annual reports 2024",
            "Specialty chemicals analyst reports 2024",
        ],
        "template_kpis": [
            {
                "name": "Gross Margin",
                "definition": "Revenue minus COGS, as a % of revenue",
                "unit": "%",
                "benchmark_low": 28.0,
                "benchmark_high": 35.0,
                "benchmark_range": "28-35%",
                "benchmark_source": "filing",
                "confidence": 0.85,
                "domain": "Finance",
                "business_process_id": None,
            },
            {
                "name": "Order-to-Delivery Lead Time",
                "definition": "Average days from order receipt to shipment",
                "unit": "days",
                "benchmark_low": 3.0,
                "benchmark_high": 5.0,
                "benchmark_range": "3-5 days",
                "benchmark_source": "peer",
                "confidence": 0.7,
                "domain": "Operations",
                "business_process_id": None,
            },
            {
                "name": "Inventory Turns",
                "definition": "COGS divided by average inventory",
                "unit": "x",
                "benchmark_low": 6.0,
                "benchmark_high": 9.0,
                "benchmark_range": "6-9x",
                "benchmark_source": "inferred",
                "confidence": 0.55,
                "domain": "Supply Chain",
                "business_process_id": None,
            },
        ],
    }


def _agent_with_mocks(*, enable_perplexity: bool, perplexity_answers: list[str] | None = None):
    """Build an agent with LLM mocked and (optionally) Perplexity mocked.

    perplexity_answers: list of 4 answer strings to return from each search
    in sequence. None means Perplexity is not mocked (used for disabled mode).
    """
    agent = A9_Market_Analysis_Agent(config={"enable_perplexity": enable_perplexity})

    # Mock LLM: respond to JSON calls with the fixture profile payload
    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(return_value=_make_llm_response(_fixture_profile_payload()))
    agent._llm_service = mock_llm

    if enable_perplexity and perplexity_answers is not None:
        mock_perp = MagicMock()
        mock_perp.api_key = "fake_key"
        side_effects = [
            {"answer": ans, "citations": []} for ans in perplexity_answers
        ]
        mock_perp.search = AsyncMock(side_effect=side_effects)
        agent._perplexity = mock_perp

    return agent


# ---------------------------------------------------------------------------
# MA agent tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_research_happy_path_with_perplexity():
    """Happy path: 4 Perplexity searches return content, LLM synthesises JSON profile."""
    agent = _agent_with_mocks(
        enable_perplexity=True,
        perplexity_answers=[
            "10-K disclosed gross margin range 28-35%",
            "Operating segments: industrial, automotive",
            "Specialty chemicals peers report 28-32% gross margin",
            "CEO investor day: focus on margin expansion",
        ],
    )

    profile = await agent.research_company_kpi_profile(_make_request())

    assert isinstance(profile, CompanyKPIProfile)
    assert profile.company_name == "Valvoline Inc."
    assert profile.degraded is False
    assert profile.is_public is True
    assert len(profile.template_kpis) == 3
    # Source diversity preserved
    sources = {k.benchmark_source for k in profile.template_kpis}
    assert sources == {"filing", "peer", "inferred"}
    # 4 parallel searches executed
    assert agent._perplexity.search.call_count == 4


@pytest.mark.asyncio
async def test_research_fallback_when_perplexity_disabled():
    """Perplexity disabled → degraded=True and all benchmark_source forced to 'inferred'."""
    agent = _agent_with_mocks(enable_perplexity=False)

    profile = await agent.research_company_kpi_profile(_make_request())

    assert profile.degraded is True
    assert len(profile.template_kpis) == 3
    # M4: every benchmark_source forced to 'inferred' in degraded mode,
    # regardless of what the LLM payload originally claimed.
    for kpi in profile.template_kpis:
        assert kpi.benchmark_source == "inferred"


@pytest.mark.asyncio
async def test_research_fallback_when_all_searches_empty():
    """All 4 Perplexity searches return empty answers → falls back to LLM-only."""
    agent = _agent_with_mocks(
        enable_perplexity=True,
        perplexity_answers=["", "", "", ""],
    )

    profile = await agent.research_company_kpi_profile(_make_request())

    # Degraded because no usable search payload survived the filter
    assert profile.degraded is True
    for kpi in profile.template_kpis:
        assert kpi.benchmark_source == "inferred"


@pytest.mark.asyncio
async def test_build_company_search_queries_count_and_specificity():
    """4 queries are built, each touching a distinct angle and including company name."""
    agent = A9_Market_Analysis_Agent(config={"enable_perplexity": True})
    queries = agent._build_company_search_queries(_make_request())

    assert len(queries) == 4
    # Each query targets a distinct facet
    joined = " | ".join(queries).lower()
    assert "10-k" in joined
    assert "business segments" in joined
    assert "benchmark" in joined
    assert "investor day" in joined
    # Company name appears in at least the filing/segments queries
    assert "valvoline" in queries[0].lower()
    assert "valvoline" in queries[3].lower()


# ---------------------------------------------------------------------------
# SA agent guard test — confirms template KPIs are excluded
# ---------------------------------------------------------------------------

class _FakeKPI:
    """Minimal stand-in for the registry KPI object used by SA._load_kpi_registry."""

    def __init__(self, kpi_id: str, name: str, status: str, domain: str = "Finance"):
        self.id = kpi_id
        self.name = name
        self.status = status
        self.domain = domain
        self.client_id = "lubricants"
        # Fields touched by _convert_to_kpi_definition / _kpi_matches_domains:
        self.data_product_id = "dp_fi"
        self.business_process_ids = []
        self.business_processes = []
        self.thresholds = []
        self.dimensions = []
        self.metadata = {}
        self.unit = "%"
        self.description = "test KPI"
        self.sql_query = "SELECT 1"
        self.filters = None
        self.view_name = None
        self.monitoring_profile = None
        self.benchmark_range = None
        self.benchmark_source = None


@pytest.mark.asyncio
async def test_sa_loader_skips_template_kpis():
    """`_load_kpi_registry` must skip KPIs with status='template'."""
    from src.agents.models.situation_awareness_models import KPIDefinition
    from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent

    active = _FakeKPI("net_revenue", "Net Revenue", status="active")
    template = _FakeKPI("gross_margin", "Gross Margin", status="template")

    mock_provider = MagicMock()
    mock_provider.get_all = MagicMock(return_value=[active, template])
    mock_provider.load = AsyncMock(return_value=None)

    mock_factory = MagicMock()
    mock_factory.get_kpi_provider = MagicMock(return_value=mock_provider)
    mock_factory.get_provider = MagicMock(return_value=mock_provider)
    mock_factory.is_initialized = True

    # Build agent without going through async create() — we're testing the loader directly
    agent = A9_Situation_Awareness_Agent.__new__(A9_Situation_Awareness_Agent)
    agent.config = {
        "target_domains": ["Finance"],
        "registry_factory": mock_factory,
    }
    agent.kpi_registry = {}

    # Bypass the heavyweight domain/conversion methods — we want to verify the
    # status filter is the gate, not the conversion logic.
    agent._kpi_matches_domains = MagicMock(return_value=True)
    agent._convert_to_kpi_definition = MagicMock(
        side_effect=lambda kpi: KPIDefinition(
            id=kpi.id,
            name=kpi.name,
            description=kpi.description,
            data_product_id=kpi.data_product_id,
            client_id=kpi.client_id,
        )
    )

    await agent._load_kpi_registry()

    # Only the 'active' KPI should land in the registry
    assert "Net Revenue" in agent.kpi_registry
    assert "Gross Margin" not in agent.kpi_registry
    # Conversion was attempted only for the active KPI
    assert agent._convert_to_kpi_definition.call_count == 1


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------

def test_slugify_kpi_id_basic():
    assert _slugify_kpi_id("Gross Margin") == "gross_margin"
    assert _slugify_kpi_id("Order-to-Delivery Lead Time") == "order_to_delivery_lead_time"
    assert _slugify_kpi_id("EBITDA %") == "ebitda"
    assert _slugify_kpi_id("  Net  Revenue  ") == "net_revenue"


def test_slugify_kpi_id_empty_fallback():
    assert _slugify_kpi_id("") == "kpi"
    assert _slugify_kpi_id("---") == "kpi"
