"""Tests for Phase 17 D2 -- computing impact_estimate from a lever instead of
the LLM asserting it directly.

Two things under test: _parse_impact_estimate's new optional `lever` field
(pure parsing, no DB), and _compute_impact_from_lever's dispatch/fetch logic
(mocked provider/orchestrator -- dispatch logic, mirrors
test_va_causal_edge_confirmation.py's own pattern for the same reason).
"""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.new.a9_solution_finder_agent import (
    _compute_impact_from_lever,
    _parse_impact_estimate,
)
from src.agents.models.solution_finder_models import ImpactLever


@pytest.fixture
def logger_():
    return logging.getLogger("test")


class TestParseImpactEstimateLever:
    def test_valid_lever_is_parsed(self):
        raw = {
            "metric": "gross_margin_pct", "unit": "%",
            "recovery_range": {"low": 1.0, "high": 2.0},
            "lever": {"leaf_kpi_id": "net_revenue", "delta_low_pct": 3.0, "delta_high_pct": 5.0},
        }
        ie = _parse_impact_estimate(raw)
        assert ie is not None
        assert ie.lever is not None
        assert ie.lever.leaf_kpi_id == "net_revenue"
        assert ie.lever.delta_low_pct == 3.0
        assert ie.source == "llm_estimated"  # parsing alone never marks it computed

    def test_absent_lever_is_none_not_an_error(self):
        raw = {"metric": "gross_margin_pct", "unit": "%", "recovery_range": {"low": 1.0, "high": 2.0}}
        ie = _parse_impact_estimate(raw)
        assert ie is not None
        assert ie.lever is None

    def test_malformed_lever_degrades_to_none(self):
        """A lever object that fails validation must not break the whole
        impact_estimate parse -- same defensive posture as recovery_range."""
        raw = {
            "metric": "gross_margin_pct", "unit": "%",
            "lever": "not-a-dict",
        }
        ie = _parse_impact_estimate(raw)
        assert ie is not None
        assert ie.lever is None

    def test_source_defaults_to_llm_estimated(self):
        ie = _parse_impact_estimate({"metric": "x", "unit": "%"})
        assert ie.source == "llm_estimated"


class TestComputeImpactFromLever:
    @pytest.mark.asyncio
    async def test_no_lever_is_a_no_op(self, logger_):
        result = await _compute_impact_from_lever("gross_margin_pct", "lubricants", None, MagicMock(), logger_)
        assert result is None

    @pytest.mark.asyncio
    async def test_lever_missing_deltas_is_a_no_op(self, logger_):
        lever = ImpactLever(leaf_kpi_id="net_revenue")  # deltas unset
        result = await _compute_impact_from_lever("gross_margin_pct", "lubricants", lever, MagicMock(), logger_)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_decomposition_tree_is_a_no_op(self, logger_):
        lever = ImpactLever(leaf_kpi_id="net_revenue", delta_low_pct=3.0, delta_high_pct=5.0)
        with patch("src.registry.providers.kpi_decomposition_provider.KPIDecompositionProvider") as MockProvider:
            MockProvider.return_value.get_full_tree = AsyncMock(return_value=[])
            result = await _compute_impact_from_lever(
                "gross_margin_pct", "lubricants", lever, MagicMock(), logger_,
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_no_orchestrator_is_a_no_op(self, logger_):
        from src.registry.models.kpi_decomposition import KPIDecompositionEdge
        lever = ImpactLever(leaf_kpi_id="net_revenue", delta_low_pct=3.0, delta_high_pct=5.0)
        edges = [
            KPIDecompositionEdge(parent_kpi_id="gross_profit", child_kpi_id="net_revenue",
                                  client_id="lubricants", operation="linear", sign=1),
        ]
        with patch("src.registry.providers.kpi_decomposition_provider.KPIDecompositionProvider") as MockProvider:
            MockProvider.return_value.get_full_tree = AsyncMock(return_value=edges)
            result = await _compute_impact_from_lever(
                "gross_profit", "lubricants", lever, None, logger_,
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_provider_exception_does_not_propagate(self, logger_):
        lever = ImpactLever(leaf_kpi_id="net_revenue", delta_low_pct=3.0, delta_high_pct=5.0)
        with patch("src.registry.providers.kpi_decomposition_provider.KPIDecompositionProvider") as MockProvider:
            MockProvider.return_value.get_full_tree = AsyncMock(side_effect=RuntimeError("pool not initialized"))
            result = await _compute_impact_from_lever(
                "gross_margin_pct", "lubricants", lever, MagicMock(), logger_,
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_end_to_end_with_mocked_dpa_and_registry(self, logger_):
        """Full path: real decomposition edges (mocked provider), mocked DPA
        returning fixed current values, mocked KPI registry for unit_class --
        confirms the wiring reaches compute_lever_impact and returns a real
        computed bound, not just that it doesn't crash."""
        from src.registry.models.kpi_decomposition import KPIDecompositionEdge

        edges = [
            KPIDecompositionEdge(parent_kpi_id="gross_margin_pct", child_kpi_id="gross_profit",
                                  client_id="lubricants", operation="ratio", weight_kpi_id="net_revenue"),
            KPIDecompositionEdge(parent_kpi_id="gross_profit", child_kpi_id="net_revenue",
                                  client_id="lubricants", operation="linear", sign=1),
            KPIDecompositionEdge(parent_kpi_id="gross_profit", child_kpi_id="cogs",
                                  client_id="lubricants", operation="linear", sign=-1),
        ]
        lever = ImpactLever(leaf_kpi_id="net_revenue", delta_low_pct=3.0, delta_high_pct=5.0)

        def _fake_kpi(kpi_id, unit_class=None, value=None):
            k = MagicMock()
            k.unit_class = unit_class
            k.data_product_id = "dp1"
            k.sql_query = f"SELECT {value} AS value" if value is not None else None
            return k

        values = {"gross_margin_pct": 32.16, "net_revenue": 440245582.78, "cogs": 298679848.02}
        kpis = {
            "gross_margin_pct": _fake_kpi("gross_margin_pct", unit_class="ratio", value=values["gross_margin_pct"]),
            "net_revenue": _fake_kpi("net_revenue", value=values["net_revenue"]),
            "cogs": _fake_kpi("cogs", value=values["cogs"]),
        }
        kpi_provider = MagicMock()
        kpi_provider.get.side_effect = lambda nid, client_id=None: kpis.get(nid)

        dpa = MagicMock()
        async def _execute_sql(sql, data_product_id=None):
            v = float(sql.split("SELECT ")[1].split(" AS")[0])
            return {"rows": [{"value": v}]}
        dpa.execute_sql = AsyncMock(side_effect=_execute_sql)

        orchestrator = MagicMock()
        orchestrator.get_agent = AsyncMock(return_value=dpa)

        with patch("src.registry.providers.kpi_decomposition_provider.KPIDecompositionProvider") as MockProvider, \
             patch("src.registry.factory.RegistryFactory") as MockFactory:
            MockProvider.return_value.get_full_tree = AsyncMock(return_value=edges)
            MockFactory.return_value.get_provider.return_value = kpi_provider

            result = await _compute_impact_from_lever(
                "gross_margin_pct", "lubricants", lever, orchestrator, logger_,
            )

        assert result is not None
        assert result["leaf_kpi_id"] == "net_revenue"
        assert result["effect_low"] > 0
        assert result["effect_high"] > result["effect_low"]
