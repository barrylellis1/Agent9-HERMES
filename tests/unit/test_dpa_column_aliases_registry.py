# arch-allow-direct-agent-construction
"""
Phase 16 step 4 (DEVELOPMENT_PLAN.md) -- column_aliases moves registry-first.
Phase 16 step 5 (2026-08-30) -- registry-ONLY: the YAML-contract fallback (and
the _contract_path helper it alone used) was deleted once every real data
product's DataProduct.column_aliases was confirmed populated in Supabase, and
the 8 legacy contract YAML files themselves were deleted from disk.

`A9_Data_Product_Agent._get_contract_column_aliases` is the last-resort
fallback inside `_generate_sql_for_kpi`, reached only when source_system
routing (CLAUDE.md rule 9) cannot resolve a backend for a data product --
none of the seeded BigQuery/Snowflake/SQL Server clients ever reach it; it
exists for a DuckDB-style client (bicycle) with no resolvable source_system.

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
    return agent


def _dp(column_aliases=None):
    return SimpleNamespace(column_aliases=column_aliases)


class TestRegistryOnly:
    def test_registry_column_aliases_returned_when_populated(self):
        dp = _dp(column_aliases={"measure": "amount", "date": "transaction_date",
                                  "version": "version", "default_version_value": "Actual"})
        provider = MagicMock()
        provider.get.return_value = dp
        factory = MagicMock()
        factory.get_provider.return_value = provider

        agent = _agent(registry_factory=factory)
        result = agent._get_contract_column_aliases("dp_lubricants_financials")

        assert result == dp.column_aliases
        provider.get.assert_called_once_with("dp_lubricants_financials")

    def test_registry_none_returns_empty_dict(self):
        dp = _dp(column_aliases=None)  # not yet migrated
        provider = MagicMock()
        provider.get.return_value = dp
        factory = MagicMock()
        factory.get_provider.return_value = provider

        agent = _agent(registry_factory=factory)
        assert agent._get_contract_column_aliases("dp_hess_financials") == {}

    def test_registry_empty_dict_returns_empty_dict(self):
        dp = _dp(column_aliases={})
        provider = MagicMock()
        provider.get.return_value = dp
        factory = MagicMock()
        factory.get_provider.return_value = provider

        agent = _agent(registry_factory=factory)
        assert agent._get_contract_column_aliases("dp_x") == {}


class TestNonFatalDegradation:
    def test_no_registry_factory_returns_empty_dict(self):
        agent = _agent(registry_factory=None)
        assert agent._get_contract_column_aliases("dp_x") == {}

    def test_provider_exception_returns_empty_dict_not_raise(self):
        factory = MagicMock()
        factory.get_provider.side_effect = RuntimeError("provider explosion")
        agent = _agent(registry_factory=factory)

        assert agent._get_contract_column_aliases("dp_x") == {}

    def test_no_data_product_id_returns_empty_dict(self):
        factory = MagicMock()
        agent = _agent(registry_factory=factory)

        result = agent._get_contract_column_aliases(None)
        assert result == {}
        factory.get_provider.assert_not_called()

    def test_provider_returns_none_returns_empty_dict(self):
        provider = MagicMock()
        provider.get.return_value = None
        factory = MagicMock()
        factory.get_provider.return_value = provider

        agent = _agent(registry_factory=factory)
        assert agent._get_contract_column_aliases("dp_x") == {}
