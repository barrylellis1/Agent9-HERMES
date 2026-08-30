# arch-allow-direct-agent-construction
"""
Phase 16 step 5 (DEVELOPMENT_PLAN.md) -- dimension_hierarchies registry-first.

Found while auditing every yaml.safe_load call site in a9_deep_analysis_agent.py
before attempting to delete any of the 12 legacy contract YAML files -- a THIRD
YAML-only section (alongside dimension_semantics and fallback_group_by_dimensions,
step 1) that the original Phase 16 finding table never catalogued.

Genuinely live with real behavioural impact, unlike column_aliases (step 4):
execute_deep_analysis's `_hierarchies_from_contract()` closure drives whether DA
takes the hierarchical-drill analysis path or the flat dimension-ranking path --
`if hmap: used_hierarchical = True`. Only hess (via hess_financials.yaml) and
bicycle (fi_star_schema.yaml) declare this section among the seeded clients;
lubricants/apex_lubricants never did, so they are unaffected by it being empty
for them -- that is "genuinely has none", not "not yet migrated", and both must
read as empty without the tests conflating them.

These tests cover `_hierarchies_from_registry` directly, mirroring
test_da_dimension_ranking.py's `_dims_from_registry` tests exactly -- the
`_hierarchies_from_contract` closure itself is nested inside
`execute_deep_analysis` and not independently unit-testable without invoking
the whole method; the registry-vs-YAML decision this step is actually about
lives in `_hierarchies_from_registry`.
"""

from types import SimpleNamespace
from unittest.mock import patch

from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent


def _agent(**config):
    return A9_Deep_Analysis_Agent(config or {})


class TestHierarchiesFromRegistry:
    def test_returns_populated_hierarchies_from_data_product(self):
        agent = _agent()
        fake_kpi = SimpleNamespace(data_product_id="dp_hess_financials")
        fake_dp = SimpleNamespace(dimension_hierarchies={
            "geography": ["country", "basin_name", "asset_name"],
            "segment": ["segment_name", "business_unit"],
        })
        with patch.object(agent, "_lookup_kpi_scoped", return_value=fake_kpi), \
             patch("src.registry.factory.RegistryFactory") as MockFactory:
            MockFactory.return_value.get_provider.return_value.get.return_value = fake_dp
            result = agent._hierarchies_from_registry(kpi_name="gross_margin_pct", client_id="hess")

        assert result == {
            "geography": ["country", "basin_name", "asset_name"],
            "segment": ["segment_name", "business_unit"],
        }

    def test_non_list_values_in_hierarchy_dict_are_dropped_not_raised(self):
        agent = _agent()
        fake_kpi = SimpleNamespace(data_product_id="dp_x")
        fake_dp = SimpleNamespace(dimension_hierarchies={
            "geography": ["country"],
            "bad_entry": "not-a-list",
        })
        with patch.object(agent, "_lookup_kpi_scoped", return_value=fake_kpi), \
             patch("src.registry.factory.RegistryFactory") as MockFactory:
            MockFactory.return_value.get_provider.return_value.get.return_value = fake_dp
            result = agent._hierarchies_from_registry(kpi_name="k", client_id="c")

        assert result == {"geography": ["country"]}

    def test_empty_dict_reads_as_empty_not_an_error(self):
        """lubricants/apex_lubricants genuinely never declared this section --
        must read as {} cleanly, not be distinguishable from a lookup failure
        by anything downstream (both correctly fall through to the YAML path,
        which is also empty for these two clients)."""
        agent = _agent()
        fake_kpi = SimpleNamespace(data_product_id="dp_lubricants_financials")
        fake_dp = SimpleNamespace(dimension_hierarchies={})
        with patch.object(agent, "_lookup_kpi_scoped", return_value=fake_kpi), \
             patch("src.registry.factory.RegistryFactory") as MockFactory:
            MockFactory.return_value.get_provider.return_value.get.return_value = fake_dp
            assert agent._hierarchies_from_registry(kpi_name="k", client_id="lubricants") == {}

    def test_returns_empty_when_kpi_unresolvable(self):
        agent = _agent()
        with patch.object(agent, "_lookup_kpi_scoped", return_value=None):
            assert agent._hierarchies_from_registry(kpi_name="nonexistent", client_id="hess") == {}

    def test_returns_empty_when_data_product_provider_missing(self):
        agent = _agent()
        fake_kpi = SimpleNamespace(data_product_id="dp_x")
        with patch.object(agent, "_lookup_kpi_scoped", return_value=fake_kpi), \
             patch("src.registry.factory.RegistryFactory") as MockFactory:
            MockFactory.return_value.get_provider.return_value = None
            assert agent._hierarchies_from_registry(kpi_name="k", client_id="c") == {}

    def test_never_raises_on_provider_exception(self):
        agent = _agent()
        fake_kpi = SimpleNamespace(data_product_id="dp_x")
        with patch.object(agent, "_lookup_kpi_scoped", return_value=fake_kpi), \
             patch("src.registry.factory.RegistryFactory") as MockFactory:
            MockFactory.return_value.get_provider.return_value.get.side_effect = RuntimeError("boom")
            assert agent._hierarchies_from_registry(kpi_name="k", client_id="c") == {}

    def test_no_kpi_name_returns_empty(self):
        agent = _agent()
        assert agent._hierarchies_from_registry(kpi_name=None, client_id="hess") == {}
