# arch-allow-direct-agent-construction
"""
Phase 16 step 4 (DEVELOPMENT_PLAN.md) -- column_aliases moves registry-first.

`A9_Data_Product_Agent._get_contract_column_aliases` is the last-resort
fallback inside `_generate_sql_for_kpi`, reached only when source_system
routing (CLAUDE.md rule 9) cannot resolve a backend for a data product --
none of the seeded BigQuery/Snowflake/SQL Server clients ever reach it; it
exists for a DuckDB-style client (bicycle) with no resolvable source_system.

Before this fix, the YAML fallback ALWAYS ignored the `data_product_id`
argument it was given (called `self._contract_path()` with no argument),
silently resolving to the bicycle default contract regardless of which data
product was actually asked for -- the same cross-tenant-contamination shape
already fixed once for DA's `_dims_from_contract` (Phase 16 step 1). This
file pins the fix: registry wins when populated, `data_product_id` is
actually threaded through the YAML fallback, and the method degrades
non-fatally on any provider failure.

Uses a bare `object.__new__` instance rather than the real constructor --
`A9_Data_Product_Agent.__init__` opens a real DuckDBManager, which is more
than this pure-branching-logic method needs.
"""

from unittest.mock import MagicMock
from types import SimpleNamespace

import pytest

from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent


def _agent(registry_factory=None):
    agent = object.__new__(A9_Data_Product_Agent)
    agent.registry_factory = registry_factory
    agent._registry_data = None
    return agent


def _dp(column_aliases=None):
    return SimpleNamespace(column_aliases=column_aliases)


class TestRegistryWinsOverYaml:
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

    def test_registry_none_falls_back_to_yaml_scan(self, monkeypatch, tmp_path):
        dp = _dp(column_aliases=None)  # not yet migrated
        provider = MagicMock()
        provider.get.return_value = dp
        factory = MagicMock()
        factory.get_provider.return_value = provider

        contract = tmp_path / "contract.yaml"
        contract.write_text("column_aliases:\n  measure: amount\n  date: transaction_date\n", encoding="utf-8")

        agent = _agent(registry_factory=factory)
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: str(contract))

        result = agent._get_contract_column_aliases("dp_hess_financials")
        assert result == {"measure": "amount", "date": "transaction_date"}

    def test_registry_empty_dict_falls_back_to_yaml_scan(self, monkeypatch, tmp_path):
        # {} is falsy -- must be treated the same as None, not returned as-is.
        dp = _dp(column_aliases={})
        provider = MagicMock()
        provider.get.return_value = dp
        factory = MagicMock()
        factory.get_provider.return_value = provider

        contract = tmp_path / "contract.yaml"
        contract.write_text("column_aliases:\n  measure: amount\n", encoding="utf-8")

        agent = _agent(registry_factory=factory)
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: str(contract))

        assert agent._get_contract_column_aliases("dp_x") == {"measure": "amount"}


class TestDataProductIdThreadedThrough:
    """The bug this fix closes: data_product_id used to be silently dropped."""

    def test_data_product_id_passed_to_contract_path(self, monkeypatch):
        agent = _agent(registry_factory=None)  # no registry -> straight to YAML path
        seen = {}

        def fake_contract_path(data_product_id=None):
            seen["data_product_id"] = data_product_id
            return "/nonexistent/path.yaml"

        monkeypatch.setattr(agent, "_contract_path", fake_contract_path)
        agent._get_contract_column_aliases("dp_hess_financials")

        assert seen["data_product_id"] == "dp_hess_financials", (
            "data_product_id must reach _contract_path -- prior to this fix it was "
            "silently dropped, always resolving to the bicycle default contract "
            "regardless of which data product was actually asked for."
        )


class TestNonFatalDegradation:
    def test_no_registry_factory_falls_back_cleanly(self, monkeypatch, tmp_path):
        agent = _agent(registry_factory=None)
        contract = tmp_path / "contract.yaml"
        contract.write_text("column_aliases:\n  measure: amount\n", encoding="utf-8")
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: str(contract))

        assert agent._get_contract_column_aliases("dp_x") == {"measure": "amount"}

    def test_provider_exception_falls_back_to_yaml_not_raise(self, monkeypatch, tmp_path):
        factory = MagicMock()
        factory.get_provider.side_effect = RuntimeError("provider explosion")
        agent = _agent(registry_factory=factory)

        contract = tmp_path / "contract.yaml"
        contract.write_text("column_aliases:\n  measure: amount\n", encoding="utf-8")
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: str(contract))

        assert agent._get_contract_column_aliases("dp_x") == {"measure": "amount"}

    def test_no_data_product_id_skips_registry_goes_to_yaml(self, monkeypatch, tmp_path):
        factory = MagicMock()
        agent = _agent(registry_factory=factory)
        contract = tmp_path / "contract.yaml"
        contract.write_text("column_aliases:\n  measure: amount\n", encoding="utf-8")
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: str(contract))

        result = agent._get_contract_column_aliases(None)
        assert result == {"measure": "amount"}
        factory.get_provider.assert_not_called()

    def test_missing_yaml_file_returns_empty_dict_not_raise(self, monkeypatch):
        agent = _agent(registry_factory=None)
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: "/does/not/exist.yaml")
        assert agent._get_contract_column_aliases("dp_x") == {}

    def test_malformed_yaml_column_aliases_returns_empty_dict(self, monkeypatch, tmp_path):
        agent = _agent(registry_factory=None)
        contract = tmp_path / "contract.yaml"
        contract.write_text("column_aliases: not_a_dict\n", encoding="utf-8")
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: str(contract))
        assert agent._get_contract_column_aliases("dp_x") == {}
