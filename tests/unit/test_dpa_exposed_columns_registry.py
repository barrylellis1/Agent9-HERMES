# arch-allow-direct-agent-construction
"""
Phase 16 step 5 (DEVELOPMENT_PLAN.md) -- exposed_columns moves registry-first.

`A9_Data_Product_Agent._get_exposed_columns` is the label-first short-circuit
inside `_resolve_attribute_name`, itself the last-resort fallback inside
`_generate_sql_for_kpi` -- reached only when source_system routing (CLAUDE.md
rule 9) cannot resolve a backend for a data product. None of the seeded
BigQuery/Snowflake/SQL Server clients ever reach it; it exists for a
DuckDB-style client (bicycle) with no resolvable source_system.

Same shape as the column_aliases fix (step 4, test_dpa_column_aliases_
registry.py): before this change the YAML fallback ignored the
`data_product_id` it was given (called `self._contract_path()` with no
argument), silently resolving to the bicycle default contract regardless of
which data product was actually asked about. This file pins the fix:
registry wins when populated for the requested view, the cache key is
(data_product_id, view_name) so two data products never collide on an
identically-named view, `data_product_id` is actually threaded through the
YAML fallback, and the method degrades non-fatally on any provider failure.

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


class TestRegistryWinsOverYaml:
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

    def test_registry_view_not_present_falls_back_to_yaml_scan(self, monkeypatch, tmp_path):
        # Registry has entries, but not for THIS view -- must fall back, not return empty.
        dp = _dp(exposed_columns={"someothereview": ["x"]})
        provider = MagicMock()
        provider.get.return_value = dp
        factory = MagicMock()
        factory.get_provider.return_value = provider

        contract = tmp_path / "contract.yaml"
        contract.write_text(
            "views:\n  - name: FI_Star_View\n    llm_profile:\n      exposed_columns:\n        - \"Version\"\n",
            encoding="utf-8",
        )
        agent = _agent(registry_factory=factory)
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: str(contract))

        result = agent._get_exposed_columns("FI_Star_View", "fi_star_schema")
        assert result == {"Version"}

    def test_registry_empty_dict_falls_back_to_yaml_scan(self, monkeypatch, tmp_path):
        # {} is falsy -- must be treated the same as None, not returned as-is.
        dp = _dp(exposed_columns={})
        provider = MagicMock()
        provider.get.return_value = dp
        factory = MagicMock()
        factory.get_provider.return_value = provider

        contract = tmp_path / "contract.yaml"
        contract.write_text(
            "views:\n  - name: FI_Star_View\n    llm_profile:\n      exposed_columns:\n        - \"Version\"\n",
            encoding="utf-8",
        )
        agent = _agent(registry_factory=factory)
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: str(contract))

        assert agent._get_exposed_columns("FI_Star_View", "dp_x") == {"Version"}


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


class TestDataProductIdThreadedThrough:
    """The bug this fix closes: data_product_id used to be silently dropped
    from the YAML fallback (self._contract_path() called with no argument)."""

    def test_data_product_id_passed_to_contract_path(self, monkeypatch):
        agent = _agent(registry_factory=None)  # no registry -> straight to YAML path
        seen = {}

        def fake_contract_path(data_product_id=None):
            seen["data_product_id"] = data_product_id
            return "/nonexistent/path.yaml"

        monkeypatch.setattr(agent, "_contract_path", fake_contract_path)
        agent._get_exposed_columns("HessStarSchemaView", "dp_hess_financials")

        assert seen["data_product_id"] == "dp_hess_financials", (
            "data_product_id must reach _contract_path -- prior to this fix it was "
            "silently dropped, always resolving to the bicycle default contract "
            "regardless of which data product was actually asked about."
        )


class TestNonFatalDegradation:
    def test_no_view_name_returns_none(self):
        agent = _agent(registry_factory=None)
        assert agent._get_exposed_columns(None, "dp_x") is None
        assert agent._get_exposed_columns("   ", "dp_x") is None

    def test_no_registry_factory_falls_back_cleanly(self, monkeypatch, tmp_path):
        agent = _agent(registry_factory=None)
        contract = tmp_path / "contract.yaml"
        contract.write_text(
            "views:\n  - name: FI_Star_View\n    llm_profile:\n      exposed_columns:\n        - \"Version\"\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: str(contract))

        assert agent._get_exposed_columns("FI_Star_View", "dp_x") == {"Version"}

    def test_provider_exception_falls_back_to_yaml_not_raise(self, monkeypatch, tmp_path):
        factory = MagicMock()
        factory.get_provider.side_effect = RuntimeError("provider explosion")
        agent = _agent(registry_factory=factory)

        contract = tmp_path / "contract.yaml"
        contract.write_text(
            "views:\n  - name: FI_Star_View\n    llm_profile:\n      exposed_columns:\n        - \"Version\"\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: str(contract))

        assert agent._get_exposed_columns("FI_Star_View", "dp_x") == {"Version"}

    def test_no_data_product_id_skips_registry_goes_to_yaml(self, monkeypatch, tmp_path):
        factory = MagicMock()
        agent = _agent(registry_factory=factory)
        contract = tmp_path / "contract.yaml"
        contract.write_text(
            "views:\n  - name: FI_Star_View\n    llm_profile:\n      exposed_columns:\n        - \"Version\"\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: str(contract))

        result = agent._get_exposed_columns("FI_Star_View", None)
        assert result == {"Version"}
        factory.get_provider.assert_not_called()

    def test_missing_yaml_file_returns_none_not_raise(self, monkeypatch):
        agent = _agent(registry_factory=None)
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: "/does/not/exist.yaml")
        assert agent._get_exposed_columns("FI_Star_View", "dp_x") is None

    def test_view_not_found_falls_back_to_fi_star_view(self, monkeypatch, tmp_path):
        # Pre-existing behaviour, unchanged by this fix: unknown view name
        # falls back to whichever view is literally named FI_Star_View.
        agent = _agent(registry_factory=None)
        contract = tmp_path / "contract.yaml"
        contract.write_text(
            "views:\n  - name: FI_Star_View\n    llm_profile:\n      exposed_columns:\n        - \"Version\"\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(agent, "_contract_path", lambda data_product_id=None: str(contract))

        assert agent._get_exposed_columns("SomeUnknownView", "dp_x") == {"Version"}
