"""Tests for src/analysis/decomposition.py (Phase 17 T2).

Pure functions, no DB -- exercised against the REAL lubricants shape
(gross_profit = net_revenue - cogs; gross_margin_pct = ratio(gross_profit,
net_revenue)) so this proves the tree this stage actually seeds reconciles,
not just a synthetic fixture.
"""
from __future__ import annotations

import pytest

from src.analysis.decomposition import check_tree_reconciles, roll_up_scope
from src.registry.models.kpi_decomposition import KPIDecompositionEdge


class TestRollUpScope:
    def test_translates_segment_delta_by_weight_share(self):
        # 2.8pp on Engine Oils (32% of revenue) -> ~0.9pp enterprise --
        # DEVELOPMENT_PLAN.md Phase 17's own worked example.
        result = roll_up_scope(segment_delta=2.8, segment_weight=32.0, enterprise_weight=100.0)
        assert result == pytest.approx(0.896)

    def test_zero_enterprise_weight_yields_none_not_zero(self):
        """An undefined share must never be conflated with a zero effect."""
        assert roll_up_scope(segment_delta=2.8, segment_weight=10.0, enterprise_weight=0.0) is None

    def test_full_share_returns_the_segment_delta_unchanged(self):
        assert roll_up_scope(segment_delta=5.0, segment_weight=100.0, enterprise_weight=100.0) == pytest.approx(5.0)


class TestCheckTreeReconcilesLinear:
    def _gross_profit_edges(self):
        return [
            KPIDecompositionEdge(parent_kpi_id="gross_profit", child_kpi_id="net_revenue",
                                  client_id="lubricants", operation="linear", sign=1),
            KPIDecompositionEdge(parent_kpi_id="gross_profit", child_kpi_id="cogs",
                                  client_id="lubricants", operation="linear", sign=-1),
        ]

    def test_real_lubricants_values_reconcile(self):
        """net_revenue - cogs = gross_profit, using magnitudes representative
        of the actual seeded lubricants dataset (cogs KPI reports a positive
        cost magnitude, per its own sign_convention)."""
        current = {"gross_profit": 100.0, "net_revenue": 393.8, "cogs": 293.8}
        assert check_tree_reconciles("gross_profit", self._gross_profit_edges(), current) is None

    def test_wrong_cogs_value_is_caught(self):
        """The actual failure mode this exists to catch: a stale or wrong
        child value that no longer sums to its parent."""
        current = {"gross_profit": 100.0, "net_revenue": 393.8, "cogs": 250.0}
        result = check_tree_reconciles("gross_profit", self._gross_profit_edges(), current)
        assert result is not None
        assert "does not reconcile" in result

    def test_missing_child_value_is_a_no_op_not_a_failure(self):
        current = {"gross_profit": 100.0, "net_revenue": 393.8}  # cogs missing
        assert check_tree_reconciles("gross_profit", self._gross_profit_edges(), current) is None

    def test_missing_parent_value_is_a_no_op(self):
        current = {"net_revenue": 393.8, "cogs": 293.8}
        assert check_tree_reconciles("gross_profit", self._gross_profit_edges(), current) is None

    def test_no_edges_is_a_no_op(self):
        assert check_tree_reconciles("gross_profit", [], {"gross_profit": 100.0}) is None


class TestCheckTreeReconcilesRatio:
    def _margin_edge(self):
        return [
            KPIDecompositionEdge(parent_kpi_id="gross_margin_pct", child_kpi_id="gross_profit",
                                  client_id="lubricants", operation="ratio", weight_kpi_id="net_revenue"),
        ]

    def test_real_lubricants_values_reconcile_percent_scaled(self):
        """gross_margin_pct is stored percent-scaled (100 * gross_profit /
        net_revenue), per every seeded KPI's own sql_query -- parent_unit_class
        must be passed to get the right scaling."""
        current = {"gross_margin_pct": 25.4, "gross_profit": 100.0, "net_revenue": 393.8}
        result = check_tree_reconciles(
            "gross_margin_pct", self._margin_edge(), current, parent_unit_class="ratio",
        )
        assert result is None

    def test_without_unit_class_hint_checked_as_a_fraction_and_flagged(self):
        """Confirms the scaling hint actually matters -- omitting it checks
        against the wrong scale and (correctly) flags a mismatch."""
        current = {"gross_margin_pct": 25.4, "gross_profit": 100.0, "net_revenue": 393.8}
        result = check_tree_reconciles("gross_margin_pct", self._margin_edge(), current)
        assert result is not None

    def test_multiple_ratio_edges_is_flagged_as_malformed(self):
        edges = self._margin_edge() * 2
        current = {"gross_margin_pct": 25.4, "gross_profit": 100.0, "net_revenue": 393.8}
        result = check_tree_reconciles("gross_margin_pct", edges, current, parent_unit_class="ratio")
        assert result is not None
        assert "exactly one" in result

    def test_zero_weight_is_a_no_op_not_a_division_error(self):
        current = {"gross_margin_pct": 25.4, "gross_profit": 100.0, "net_revenue": 0.0}
        assert check_tree_reconciles(
            "gross_margin_pct", self._margin_edge(), current, parent_unit_class="ratio",
        ) is None


class TestInconsistentOperations:
    def test_mixed_operations_under_one_parent_is_flagged(self):
        edges = [
            KPIDecompositionEdge(parent_kpi_id="x", child_kpi_id="a", client_id="c",
                                  operation="linear", sign=1),
            KPIDecompositionEdge(parent_kpi_id="x", child_kpi_id="b", client_id="c",
                                  operation="ratio", weight_kpi_id="d"),
        ]
        result = check_tree_reconciles("x", edges, {"x": 10.0, "a": 5.0, "b": 5.0, "d": 1.0})
        assert result is not None
        assert "inconsistent operations" in result
