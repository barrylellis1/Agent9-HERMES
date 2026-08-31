"""Tests for _grade_assumptions_from_verdict (Phase 17 T3, "VA feedback").

Mocks AssumptionProvider directly -- this is dispatch/mapping logic
(verdict -> status, skip-if-already-graded), not a DB round-trip; the real
round-trip is AssumptionProvider's own concern (mirrors this file's sibling
test_a9_value_assurance_agent_unit.py's own _FakeVAStore pattern for the
same reason).
"""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock, patch

import pytest

from src.agents.models.value_assurance_models import SolutionVerdict
from src.agents.new.a9_value_assurance_agent import _grade_assumptions_from_verdict


def _assumption(status="active", **overrides):
    from src.registry.models.assumption import Assumption
    base = dict(
        id="a1", client_id="lubricants", scope="gross_margin_pct",
        record_type="assumption", text="Base oil holds under $85",
        status=status, source="sf_hitl_approval", linked_solution_id="sol_1",
    )
    base.update(overrides)
    return Assumption(**base)


@pytest.fixture
def logger_():
    return logging.getLogger("test")


class TestVerdictMapping:
    @pytest.mark.asyncio
    async def test_validated_grades_held(self, logger_):
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_for_solution = AsyncMock(return_value=[_assumption()])
            instance.upsert = AsyncMock()
            await _grade_assumptions_from_verdict("sol_1", "lubricants", SolutionVerdict.VALIDATED, logger_)
            instance.upsert.assert_awaited_once()
            graded = instance.upsert.await_args.args[0]
            assert graded.status == "held"

    @pytest.mark.asyncio
    async def test_failed_grades_falsified(self, logger_):
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_for_solution = AsyncMock(return_value=[_assumption()])
            instance.upsert = AsyncMock()
            await _grade_assumptions_from_verdict("sol_1", "lubricants", SolutionVerdict.FAILED, logger_)
            graded = instance.upsert.await_args.args[0]
            assert graded.status == "falsified"

    @pytest.mark.asyncio
    async def test_partial_leaves_active_untouched(self, logger_):
        """Insufficient signal to grade which assumption held vs. broke."""
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_for_solution = AsyncMock(return_value=[_assumption()])
            instance.upsert = AsyncMock()
            await _grade_assumptions_from_verdict("sol_1", "lubricants", SolutionVerdict.PARTIAL, logger_)
            instance.upsert.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_measuring_leaves_active_untouched(self, logger_):
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_for_solution = AsyncMock(return_value=[_assumption()])
            instance.upsert = AsyncMock()
            await _grade_assumptions_from_verdict("sol_1", "lubricants", SolutionVerdict.MEASURING, logger_)
            instance.upsert.assert_not_awaited()


class TestNonClobberGuard:
    @pytest.mark.asyncio
    async def test_already_held_is_never_regraded(self, logger_):
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_for_solution = AsyncMock(return_value=[_assumption(status="held")])
            instance.upsert = AsyncMock()
            await _grade_assumptions_from_verdict("sol_1", "lubricants", SolutionVerdict.FAILED, logger_)
            instance.upsert.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_already_falsified_is_never_regraded(self, logger_):
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_for_solution = AsyncMock(return_value=[_assumption(status="falsified")])
            instance.upsert = AsyncMock()
            await _grade_assumptions_from_verdict("sol_1", "lubricants", SolutionVerdict.VALIDATED, logger_)
            instance.upsert.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_mixed_batch_only_grades_active_rows(self, logger_):
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_for_solution = AsyncMock(return_value=[
                _assumption(id="a1", status="active"),
                _assumption(id="a2", status="held"),
                _assumption(id="a3", status="active"),
            ])
            instance.upsert = AsyncMock()
            await _grade_assumptions_from_verdict("sol_1", "lubricants", SolutionVerdict.VALIDATED, logger_)
            assert instance.upsert.await_count == 2
            graded_ids = {call.args[0].id for call in instance.upsert.await_args_list}
            assert graded_ids == {"a1", "a3"}


class TestNonFatal:
    @pytest.mark.asyncio
    async def test_missing_client_id_does_not_raise(self, logger_):
        await _grade_assumptions_from_verdict("sol_1", None, SolutionVerdict.VALIDATED, logger_)

    @pytest.mark.asyncio
    async def test_provider_exception_does_not_propagate(self, logger_):
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_for_solution = AsyncMock(side_effect=RuntimeError("pool not initialized"))
            await _grade_assumptions_from_verdict("sol_1", "lubricants", SolutionVerdict.VALIDATED, logger_)

    @pytest.mark.asyncio
    async def test_no_assumptions_for_solution_is_a_no_op(self, logger_):
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockProvider:
            instance = MockProvider.return_value
            instance.get_for_solution = AsyncMock(return_value=[])
            instance.upsert = AsyncMock()
            await _grade_assumptions_from_verdict("sol_1", "lubricants", SolutionVerdict.VALIDATED, logger_)
            instance.upsert.assert_not_awaited()
