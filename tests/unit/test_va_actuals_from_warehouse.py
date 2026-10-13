"""The Actual line is filled from the warehouse's monthly values.

Found live 2026-10-13: the only source of actual values was the manual entry box
on the Portfolio page. Nothing read the months since acceptance from the data.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from src.agents.agent_config_models import A9ValueAssuranceAgentConfig
from src.agents.models.value_assurance_models import RegisterSolutionRequest, StrategySnapshot
from src.agents.new.a9_value_assurance_agent import (
    A9_Value_Assurance_Agent,
    _actuals_are_stale,
    _actuals_since_acceptance,
)

SERIES = [
    {"period": "2026-08", "value": 110.0}, {"period": "2026-09", "value": 100.0},   # baseline month
    {"period": "2026-10", "value": 104.0}, {"period": "2026-11", "value": 109.0},
    {"period": "2026-12", "value": 111.0},                                            # partial / later
]


class TestActualsSinceAcceptance:
    def test_baseline_then_each_complete_month_since(self):
        assert _actuals_since_acceptance(100.0, "2026-09", SERIES, today="2026-12-05") == (
            [100.0, 104.0, 109.0], ["2026-09", "2026-10", "2026-11"])

    def test_nothing_complete_yet_is_just_the_baseline(self):
        assert _actuals_since_acceptance(100.0, "2026-09", SERIES, today="2026-10-13") == ([100.0], ["2026-09"])

    def test_untrusted_series_is_none(self):
        bad = [{"period": "2026-00", "value": 1.0}, {"period": "2026-00", "value": 2.0}]
        assert _actuals_since_acceptance(100.0, "2026-09", bad, today="2026-12-05") is None
        assert _actuals_since_acceptance(100.0, "2026-09", None, today="2026-12-05") is None


def _register(**over) -> RegisterSolutionRequest:
    base = dict(
        request_id="r", principal_id="cfo_001", situation_id="s", kpi_id="gross_profit",
        client_id="lubricants", solution_description="x",
        expected_impact_lower=5.0, expected_impact_upper=15.0, measurement_window_days=60,
        baseline_kpi_value=100.0, baseline_period="2026-09",
        strategy_snapshot=StrategySnapshot(
            principal_priorities=[], principal_role="CFO", business_process_domain="f",
            data_product_id="dp", kpi_threshold_at_approval=0.0, key_assumptions=[],
            business_context_name="x", captured_at="2026-10-13T00:00:00Z"),
    )
    base.update(over)
    return RegisterSolutionRequest(**base)


def _orchestrator(rows, success=True):
    dpa = MagicMock()
    dpa.get_kpi_definition = AsyncMock(return_value=MagicMock(data_product_id="dp"))
    dpa.generate_monthly_series_sql = MagicMock(return_value={"success": success, "sql": "SELECT 1"})
    dpa.execute_sql = AsyncMock(return_value={"rows": rows})
    orch = MagicMock()
    orch.get_agent = AsyncMock(return_value=dpa)
    return orch, dpa


@pytest_asyncio.fixture
async def agent():
    a = await A9_Value_Assurance_Agent.create_from_registry(A9ValueAssuranceAgentConfig().model_dump())
    a.orchestrator = None
    a._va_store = None
    a._registry_factory = None
    return a


class TestStaleness:
    @pytest.mark.asyncio
    async def test_no_new_complete_month_means_no_query(self, agent):
        r = await agent.register_solution(_register())
        sol = agent._solutions_store[r.solution_id]
        assert _actuals_are_stale(sol, today="2026-10-13") is False   # September is the baseline
        assert _actuals_are_stale(sol, today="2026-11-02") is True    # October has closed

    @pytest.mark.asyncio
    async def test_no_recorded_baseline_is_never_stale(self, agent):
        r = await agent.register_solution(_register(baseline_kpi_value=None, baseline_period=None))
        assert _actuals_are_stale(agent._solutions_store[r.solution_id], today="2027-01-01") is False


class TestRefresh:
    @pytest.mark.asyncio
    async def test_actual_line_is_filled_from_the_warehouse(self, agent):
        r = await agent.register_solution(_register())
        agent.orchestrator, dpa = _orchestrator([[p["period"], p["value"]] for p in SERIES])
        updated = await agent._refresh_actuals(agent._solutions_store[r.solution_id], today="2026-12-05")
        assert updated.actual_trend == [100.0, 104.0, 109.0]
        assert updated.actual_trend_dates == ["2026-09", "2026-10", "2026-11"]
        dpa.get_kpi_definition.assert_awaited_once_with("gross_profit", client_id="lubricants")  # tenant-scoped
        assert agent._solutions_store[r.solution_id].actual_trend == [100.0, 104.0, 109.0]

    @pytest.mark.asyncio
    async def test_dict_rows_work_too(self, agent):
        r = await agent.register_solution(_register())
        agent.orchestrator, _ = _orchestrator([{"PERIOD": p["period"], "VALUE": p["value"]} for p in SERIES])
        updated = await agent._refresh_actuals(agent._solutions_store[r.solution_id], today="2026-11-05")
        assert updated.actual_trend == [100.0, 104.0]

    @pytest.mark.asyncio
    async def test_once_current_it_does_not_query_again(self, agent):
        r = await agent.register_solution(_register())
        agent.orchestrator, dpa = _orchestrator([[p["period"], p["value"]] for p in SERIES])
        first = await agent._refresh_actuals(agent._solutions_store[r.solution_id], today="2026-12-05")
        await agent._refresh_actuals(first, today="2026-12-20")
        assert dpa.execute_sql.await_count == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize("rows,success", [
        ([], True),                                   # warehouse returned nothing
        ([["2026-00", 1.0], ["2026-00", 2.0]], True), # labels cannot be trusted
        ([["2026-10", 104.0]], False),                # no series for this backend
    ])
    async def test_nothing_usable_leaves_the_line_alone(self, agent, rows, success):
        r = await agent.register_solution(_register())
        before = agent._solutions_store[r.solution_id]
        agent.orchestrator, _ = _orchestrator(rows, success=success)
        after = await agent._refresh_actuals(before, today="2026-12-05")
        assert after.actual_trend == before.actual_trend == [100.0]

    @pytest.mark.asyncio
    async def test_a_warehouse_error_is_not_fatal(self, agent):
        r = await agent.register_solution(_register())
        orch = MagicMock()
        orch.get_agent = AsyncMock(side_effect=RuntimeError("boom"))
        agent.orchestrator = orch
        after = await agent._refresh_actuals(agent._solutions_store[r.solution_id], today="2026-12-05")
        assert after.actual_trend == [100.0]
