# arch-allow-direct-agent-construction
"""`get_kpi_definition` must not resolve another tenant's KPI.

Found live 2026-10-01. Three clients register a KPI named "Cost of Goods Sold":

    apex_lubricants / cogs               -> dp_lubricants_snowflake
    bicycle         / cost_of_goods_sold -> fi_star_schema           (DuckDB)
    lubricants      / cogs               -> dp_lubricants_financials (BigQuery)

An unscoped lubricants lookup resolved the BICYCLE definition, so
`generate_sql_for_kpi` routed to that KPI's DuckDB source_system, emitted an
unqualified `FROM LubricantsStarSchemaView`, and returned 0 rows. Every
component behaved correctly on the wrong record, which is why nothing errored.

RLS cannot catch this: the lookup never resolves a tenant, so there is no
scoped query for a policy to constrain.
"""
import logging
from types import SimpleNamespace

import pytest

from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent


def _kpi(client_id, kpi_id, name, dp):
    return SimpleNamespace(id=kpi_id, name=name, client_id=client_id, data_product_id=dp, metadata={})


# The real production collision.
COGS = [
    _kpi("apex_lubricants", "cogs", "Cost of Goods Sold", "dp_lubricants_snowflake"),
    _kpi("bicycle", "cost_of_goods_sold", "Cost of Goods Sold", "fi_star_schema"),
    _kpi("lubricants", "cogs", "Cost of Goods Sold", "dp_lubricants_financials"),
]
UNIQUE = _kpi("lubricants", "premium_mix_pct", "Premium Mix %", "dp_lubricants_financials")


class _Provider:
    """Mimics DatabaseRegistryProvider.get's documented scoping contract."""

    def __init__(self, items):
        self._items = items

    def get(self, id_or_name, client_id=None):
        # The real DatabaseRegistryProvider.get matches on ID only -- composite
        # key, then bare id, then a scan comparing `item.id`. Name lookups fall
        # through to get_kpi_definition's own get_all scan. Mirroring that
        # exactly matters: a double that also matched names would hide which
        # code path the tenant guard actually runs in.
        for it in self._items:
            if it.id == id_or_name:
                if client_id and it.client_id != client_id:
                    continue
                return it
        return None

    def get_all(self):
        return list(self._items)


def _agent(items):
    a = object.__new__(A9_Data_Product_Agent)
    a.logger = logging.getLogger("test.kpi_scoping")
    a.kpi_provider = _Provider(items)
    a.registry_factory = SimpleNamespace(get_provider=lambda n: a.kpi_provider)
    return a


class TestTenantScoping:
    @pytest.mark.asyncio
    async def test_scoped_lookup_returns_the_right_tenants_kpi(self):
        agent = _agent(COGS)
        got = await agent.get_kpi_definition("Cost of Goods Sold", client_id="lubricants")
        assert got is not None
        assert got.client_id == "lubricants"
        assert got.data_product_id == "dp_lubricants_financials", (
            "must not return bicycle's fi_star_schema -- that is the live bug"
        )

    @pytest.mark.asyncio
    async def test_each_tenant_gets_its_own(self):
        agent = _agent(COGS)
        for cid, dp in [
            ("bicycle", "fi_star_schema"),
            ("apex_lubricants", "dp_lubricants_snowflake"),
            ("lubricants", "dp_lubricants_financials"),
        ]:
            got = await agent.get_kpi_definition("Cost of Goods Sold", client_id=cid)
            assert got.client_id == cid and got.data_product_id == dp

    @pytest.mark.asyncio
    async def test_scoped_lookup_for_a_tenant_without_that_kpi_returns_none(self):
        """Fail closed. Falling back to another tenant's record is the defect."""
        agent = _agent(COGS)
        assert await agent.get_kpi_definition("Cost of Goods Sold", client_id="hess") is None

    @pytest.mark.asyncio
    async def test_ambiguous_name_without_client_id_fails_closed_and_logs(self, caplog):
        """No client_id + multiple tenants matching => None, not an arbitrary pick."""
        agent = _agent(COGS)
        # Name-only match forces the get_all scan (ids differ per tenant).
        agent.kpi_provider = _Provider([
            _kpi("apex_lubricants", "a_cogs", "Cost of Goods Sold", "dp_a"),
            _kpi("bicycle", "b_cogs", "Cost of Goods Sold", "dp_b"),
        ])
        with caplog.at_level(logging.ERROR):
            got = await agent.get_kpi_definition("Cost of Goods Sold")
        assert got is None
        assert any("ambiguous" in r.getMessage().lower() for r in caplog.records), \
            "the collision must be named in the log, not silently swallowed"

    @pytest.mark.asyncio
    async def test_unambiguous_name_without_client_id_still_resolves(self):
        """Single-tenant installs and genuinely shared records keep working."""
        agent = _agent([UNIQUE])
        got = await agent.get_kpi_definition("Premium Mix %")
        assert got is not None and got.id == "premium_mix_pct"

    @pytest.mark.asyncio
    async def test_cross_tenant_record_is_discarded_even_if_provider_returns_it(self):
        """Defence in depth: a provider that ignores client_id must not leak."""
        class _LeakyProvider(_Provider):
            def get(self, id_or_name, client_id=None):
                return COGS[1]  # always bicycle

        agent = _agent(COGS)
        agent.kpi_provider = _LeakyProvider(COGS)
        assert await agent.get_kpi_definition("Cost of Goods Sold", client_id="lubricants") is None
