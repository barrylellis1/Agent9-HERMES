# arch-allow-direct-agent-construction
"""
Phase 16 step 5 (DEVELOPMENT_PLAN.md) -- exposed_columns moves registry-first,
then registry-ONLY (2026-08-30) once every real data product's
DataProduct.exposed_columns was confirmed populated in Supabase and the 8
legacy contract YAML files were deleted from disk (along with the
_contract_path helper their fallback alone used).

`A9_Data_Product_Agent._get_exposed_columns` is the label-first short-circuit
inside `_resolve_attribute_name`, itself the last-resort fallback inside
`_generate_sql_for_kpi` -- reached only when source_system routing (CLAUDE.md
rule 9) cannot resolve a backend for a data product. None of the seeded
BigQuery/Snowflake/SQL Server clients ever reach it; it exists for a
DuckDB-style client (bicycle) with no resolvable source_system.

Uses a bare `object.__new__` instance rather than the real constructor --
`A9_Data_Product_Agent.__init__` opens a real DuckDBManager, which is more
than this pure-branching-logic method needs.
"""

from unittest.mock import MagicMock
from types import SimpleNamespace

from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent


def _agent(registry_factory=None):
    agent = object.__new__(A9_Data_Product_Agent)
    agent.registry_factory = registry_factory
    agent._registry_data = None
    agent._view_exposed_columns_cache = {}
    return agent


def _dp(exposed_columns=None):
    return SimpleNamespace(exposed_columns=exposed_columns)


class TestRegistryOnly:
    def test_registry_exposed_columns_returned_when_populated(self):
        dp = _dp(exposed_columns={"hessstarschemaview": ["transaction_id", "fiscal_year", "amount"]})
        provider = MagicMock()
        provider.get.return_value = dp
        factory = MagicMock()
        factory.get_provider.return_value = provider

        agent = _agent(registry_factory=factory)
        result = agent._get_exposed_columns("HessStarSchemaView", "dp_hess_financials")

        assert result == {"transaction_id", "fiscal_year", "amount"}
        provider.get.assert_called_once_with("dp_hess_financials")

    def test_registry_lookup_is_case_insensitive_on_view_name(self):
        dp = _dp(exposed_columns={"lubricantsstarschemaview": ["amount", "version"]})
        provider = MagicMock()
        provider.get.return_value = dp
        factory = MagicMock()
        factory.get_provider.return_value = provider

        agent = _agent(registry_factory=factory)
        result = agent._get_exposed_columns("  LubricantsStarSchemaView  ", "dp_lubricants_financials")

        assert result == {"amount", "version"}

    def test_registry_view_not_present_returns_none(self):
        # Registry has entries, but not for THIS view.
        dp = _dp(exposed_columns={"someothereview": ["x"]})
        provider = MagicMock()
        provider.get.return_value = dp
        factory = MagicMock()
        factory.get_provider.return_value = provider

        agent = _agent(registry_factory=factory)
        assert agent._get_exposed_columns("FI_Star_View", "fi_star_schema") is None

    def test_registry_empty_dict_returns_none(self):
        dp = _dp(exposed_columns={})
        provider = MagicMock()
        provider.get.return_value = dp
        factory = MagicMock()
        factory.get_provider.return_value = provider

        agent = _agent(registry_factory=factory)
        assert agent._get_exposed_columns("FI_Star_View", "dp_x") is None


class TestCacheKeyedByDataProductAndView:
    """The bug this fix closes for exposed_columns specifically: a cache keyed
    by view name alone would let two data products with an identically-named
    view collide."""

    def test_two_data_products_same_view_name_do_not_collide(self):
        dp_a = _dp(exposed_columns={"starview": ["a_col"]})
        dp_b = _dp(exposed_columns={"starview": ["b_col"]})
        provider = MagicMock()
        provider.get.side_effect = lambda dpid: dp_a if dpid == "dp_a" else dp_b
        factory = MagicMock()
        factory.get_provider.return_value = provider

        agent = _agent(registry_factory=factory)
        result_a = agent._get_exposed_columns("StarView", "dp_a")
        result_b = agent._get_exposed_columns("StarView", "dp_b")

        assert result_a == {"a_col"}
        assert result_b == {"b_col"}


class TestNonFatalDegradation:
    def test_no_view_name_returns_none(self):
        agent = _agent(registry_factory=None)
        assert agent._get_exposed_columns(None, "dp_x") is None
        assert agent._get_exposed_columns("   ", "dp_x") is None

    def test_no_registry_factory_returns_none(self):
        agent = _agent(registry_factory=None)
        assert agent._get_exposed_columns("FI_Star_View", "dp_x") is None

    def test_provider_exception_returns_none_not_raise(self):
        factory = MagicMock()
        factory.get_provider.side_effect = RuntimeError("provider explosion")
        agent = _agent(registry_factory=factory)

        assert agent._get_exposed_columns("FI_Star_View", "dp_x") is None

    def test_no_data_product_id_returns_none(self):
        factory = MagicMock()
        agent = _agent(registry_factory=factory)

        result = agent._get_exposed_columns("FI_Star_View", None)
        assert result is None
        factory.get_provider.assert_not_called()

    def test_provider_returns_none_returns_none(self):
        provider = MagicMock()
        provider.get.return_value = None
        factory = MagicMock()
        factory.get_provider.return_value = provider

        agent = _agent(registry_factory=factory)
        assert agent._get_exposed_columns("FI_Star_View", "dp_x") is None
