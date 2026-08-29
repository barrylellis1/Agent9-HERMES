"""Tests for BusinessGlossaryProvider.get_by_technical_name() and
A9_Data_Governance_Agent.resolve_dimension_label() — the reverse lookup
(technical field name -> governed display term) added 2026-08-24 so DA's
Variance Breakdown exhibit can show a governed label instead of the raw
contract dimension_semantics identifier or an ungoverned client-side
mechanical transform.
"""
import pytest
from unittest.mock import AsyncMock

from src.registry.providers.business_glossary_provider import BusinessGlossaryProvider, BusinessTerm


def _provider_with(*terms: BusinessTerm) -> BusinessGlossaryProvider:
    p = BusinessGlossaryProvider(auto_load=False)
    for t in terms:
        p.terms[t.name.lower()] = t
    return p


class TestGetByTechnicalName:
    def test_finds_term_by_technical_mapping_value(self):
        provider = _provider_with(
            BusinessTerm(
                id="dim_customer_region", client_id="lubricants", name="Customer Region",
                technical_mappings={"bigquery": "customer_region"},
            )
        )
        term = provider.get_by_technical_name("customer_region", client_id="lubricants")
        assert term is not None
        assert term.name == "Customer Region"

    def test_case_insensitive(self):
        provider = _provider_with(
            BusinessTerm(id="dim_product_line", client_id="lubricants", name="Product Line",
                         technical_mappings={"bigquery": "product_line"})
        )
        assert provider.get_by_technical_name("PRODUCT_LINE", client_id="lubricants") is not None

    def test_unmapped_field_returns_none(self):
        provider = _provider_with(
            BusinessTerm(id="dim_product_line", client_id="lubricants", name="Product Line",
                         technical_mappings={"bigquery": "product_line"})
        )
        assert provider.get_by_technical_name("nonexistent_field", client_id="lubricants") is None

    def test_empty_or_none_field_name_returns_none(self):
        provider = _provider_with()
        assert provider.get_by_technical_name("", client_id="lubricants") is None
        assert provider.get_by_technical_name(None, client_id="lubricants") is None

    def test_scoped_to_client_id_does_not_leak_across_tenants(self):
        """Same technical field name, different clients — must not cross-match."""
        provider = _provider_with(
            BusinessTerm(id="dim_region_a", client_id="client_a", name="Region (A's meaning)",
                         technical_mappings={"bigquery": "region"}),
        )
        # client_b never seeded this term — must not find client_a's.
        assert provider.get_by_technical_name("region", client_id="client_b") is None
        assert provider.get_by_technical_name("region", client_id="client_a") is not None

    def test_unscoped_search_when_no_client_id_given(self):
        """Matches the pattern get_by_client() already uses elsewhere: no
        client_id given searches everything (used by callers that already
        know they're operating in a single-client context)."""
        provider = _provider_with(
            BusinessTerm(id="dim_region", client_id="lubricants", name="Region",
                         technical_mappings={"bigquery": "region"}),
        )
        assert provider.get_by_technical_name("region") is not None


class TestDGAResolveDimensionLabel:
    @pytest.mark.asyncio
    async def test_resolves_via_glossary_provider(self):
        from src.agents.new.a9_data_governance_agent import A9_Data_Governance_Agent
        agent = A9_Data_Governance_Agent.__new__(A9_Data_Governance_Agent)
        import logging
        agent.logger = logging.getLogger("test_dga")
        agent.business_glossary_provider = _provider_with(
            BusinessTerm(id="dim_customer_region", client_id="lubricants", name="Customer Region",
                         technical_mappings={"bigquery": "customer_region"})
        )

        result = await agent.resolve_dimension_label("customer_region", client_id="lubricants")
        assert result == "Customer Region"

    @pytest.mark.asyncio
    async def test_returns_none_when_unmapped_not_raises(self):
        """Enrichment, not a gate — an unmapped field degrades to None so the
        caller can fall back to a mechanical transform, never an exception."""
        from src.agents.new.a9_data_governance_agent import A9_Data_Governance_Agent
        agent = A9_Data_Governance_Agent.__new__(A9_Data_Governance_Agent)
        import logging
        agent.logger = logging.getLogger("test_dga")
        agent.business_glossary_provider = _provider_with()

        result = await agent.resolve_dimension_label("nonexistent_field", client_id="lubricants")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_provider_unavailable(self):
        from src.agents.new.a9_data_governance_agent import A9_Data_Governance_Agent
        agent = A9_Data_Governance_Agent.__new__(A9_Data_Governance_Agent)
        import logging
        agent.logger = logging.getLogger("test_dga")
        agent.business_glossary_provider = None

        result = await agent.resolve_dimension_label("customer_region", client_id="lubricants")
        assert result is None

    @pytest.mark.asyncio
    async def test_provider_exception_is_swallowed_not_raised(self):
        from src.agents.new.a9_data_governance_agent import A9_Data_Governance_Agent
        agent = A9_Data_Governance_Agent.__new__(A9_Data_Governance_Agent)
        import logging
        agent.logger = logging.getLogger("test_dga")

        class _Boom:
            def get_by_technical_name(self, *a, **kw):
                raise RuntimeError("provider blew up")
        agent.business_glossary_provider = _Boom()

        result = await agent.resolve_dimension_label("customer_region", client_id="lubricants")
        assert result is None
