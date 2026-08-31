"""Tests for _confirm_causal_edge_from_verdict (Phase 17 density-gate
write-back infrastructure).

Mocks KPIRelationshipProvider directly -- dispatch/mapping logic, mirrors
test_va_assumption_grading.py's own pattern for the same reason (this is
verdict-gating and edge-matching, not a DB round-trip test).
"""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.models.value_assurance_models import SolutionVerdict
from src.agents.new.a9_value_assurance_agent import _confirm_causal_edge_from_verdict


def _edge(**overrides):
    from src.registry.models.kpi_relationship import KPIRelationship
    base = dict(
        kpi_id="base_oil_cost", related_kpi_id="cogs", client_id="lubricants",
        relationship_type="custom", conflict_direction="converging",
        provenance="confirmed",
    )
    base.update(overrides)
    return KPIRelationship(**base)


@pytest.fixture
def logger_():
    return logging.getLogger("test")


class TestOnlyValidatedConfirms:
    @pytest.mark.asyncio
    async def test_validated_with_a_real_matching_edge_confirms_it(self, logger_):
        with patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_all = AsyncMock(return_value=[_edge()])
            instance.upsert = AsyncMock()
            await _confirm_causal_edge_from_verdict(
                "lubricants", "base_oil_cost<->cogs", SolutionVerdict.VALIDATED, logger_,
            )
            instance.upsert.assert_awaited_once()
            confirmed = instance.upsert.await_args.args[0]
            assert confirmed.causal_rung == "intervention_tested"
            assert confirmed.provenance == "va_validated"

    @pytest.mark.asyncio
    async def test_partial_never_confirms(self, logger_):
        with patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_all = AsyncMock(return_value=[_edge()])
            instance.upsert = AsyncMock()
            await _confirm_causal_edge_from_verdict(
                "lubricants", "base_oil_cost<->cogs", SolutionVerdict.PARTIAL, logger_,
            )
            instance.upsert.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_failed_never_confirms(self, logger_):
        with patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_all = AsyncMock(return_value=[_edge()])
            instance.upsert = AsyncMock()
            await _confirm_causal_edge_from_verdict(
                "lubricants", "base_oil_cost<->cogs", SolutionVerdict.FAILED, logger_,
            )
            instance.upsert.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_measuring_never_confirms(self, logger_):
        with patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_all = AsyncMock(return_value=[_edge()])
            instance.upsert = AsyncMock()
            await _confirm_causal_edge_from_verdict(
                "lubricants", "base_oil_cost<->cogs", SolutionVerdict.MEASURING, logger_,
            )
            instance.upsert.assert_not_awaited()


class TestNoSpeculativeConfirmation:
    """The core guarantee: never fires without a REAL, traceable edge."""

    @pytest.mark.asyncio
    async def test_no_claimed_edge_does_not_confirm(self, logger_):
        with patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_all = AsyncMock(return_value=[_edge()])
            instance.upsert = AsyncMock()
            await _confirm_causal_edge_from_verdict("lubricants", None, SolutionVerdict.VALIDATED, logger_)
            instance.upsert.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_ungrounded_does_not_confirm(self, logger_):
        with patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_all = AsyncMock(return_value=[_edge()])
            instance.upsert = AsyncMock()
            await _confirm_causal_edge_from_verdict("lubricants", "ungrounded", SolutionVerdict.VALIDATED, logger_)
            instance.upsert.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_insufficient_data_does_not_confirm(self, logger_):
        with patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_all = AsyncMock(return_value=[_edge()])
            instance.upsert = AsyncMock()
            await _confirm_causal_edge_from_verdict(
                "lubricants", "insufficient_data", SolutionVerdict.VALIDATED, logger_,
            )
            instance.upsert.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_client_id_does_not_confirm(self, logger_):
        with patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_all = AsyncMock(return_value=[_edge()])
            instance.upsert = AsyncMock()
            await _confirm_causal_edge_from_verdict(None, "base_oil_cost<->cogs", SolutionVerdict.VALIDATED, logger_)
            instance.upsert.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_claimed_edge_with_no_matching_registered_row_does_not_confirm(self, logger_):
        """An edge cited in prose that was never actually registered confirms nothing."""
        with patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_all = AsyncMock(return_value=[_edge()])  # base_oil_cost<->cogs only
            instance.upsert = AsyncMock()
            await _confirm_causal_edge_from_verdict(
                "lubricants", "net_revenue<->some_unregistered_kpi", SolutionVerdict.VALIDATED, logger_,
            )
            instance.upsert.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_edge_matches_regardless_of_kpi_order(self, logger_):
        """Undirected match -- 'a<->b' and 'b<->a' name the same edge."""
        with patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_all = AsyncMock(return_value=[_edge(kpi_id="cogs", related_kpi_id="base_oil_cost")])
            instance.upsert = AsyncMock()
            await _confirm_causal_edge_from_verdict(
                "lubricants", "base_oil_cost<->cogs", SolutionVerdict.VALIDATED, logger_,
            )
            instance.upsert.assert_awaited_once()


class TestAlreadyConfirmedIsANoOp:
    @pytest.mark.asyncio
    async def test_already_intervention_tested_and_va_validated_skips_upsert(self, logger_):
        with patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_all = AsyncMock(return_value=[
                _edge(causal_rung="intervention_tested", provenance="va_validated"),
            ])
            instance.upsert = AsyncMock()
            await _confirm_causal_edge_from_verdict(
                "lubricants", "base_oil_cost<->cogs", SolutionVerdict.VALIDATED, logger_,
            )
            instance.upsert.assert_not_awaited()


class TestNonFatal:
    @pytest.mark.asyncio
    async def test_provider_exception_does_not_propagate(self, logger_):
        with patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_all = AsyncMock(side_effect=RuntimeError("pool not initialized"))
            await _confirm_causal_edge_from_verdict(
                "lubricants", "base_oil_cost<->cogs", SolutionVerdict.VALIDATED, logger_,
            )
