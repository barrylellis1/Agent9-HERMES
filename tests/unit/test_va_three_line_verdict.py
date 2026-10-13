"""The verdict is read from the three lines, at the close of the measurement window.

Settled design: Solution (projected if it works), No Action (the trend at acceptance,
continued), Actual (measured since acceptance).

Found by a regression check on 2026-10-13:
- two solutions both held at 1,000; one had been falling 100 a month, so holding
  avoided a 300 loss, the other was flat. Both were judged "did not hold".
- a solution with a 90-day window, evaluated the instant after approval, came back
  "held up" and was marked complete.
"""
from __future__ import annotations

import pytest
import pytest_asyncio

from src.agents.agent_config_models import A9ValueAssuranceAgentConfig
from src.agents.models.value_assurance_models import (
    EvaluateSolutionRequest,
    RegisterSolutionRequest,
    SolutionPhase,
    SolutionVerdict,
    StrategySnapshot,
)
from src.agents.new.a9_value_assurance_agent import (
    A9_Value_Assurance_Agent,
    MeasurementWindowOpenError,
    _verdict_from_three_lines,
)

V, P, F = SolutionVerdict.VALIDATED, SolutionVerdict.PARTIAL, SolutionVerdict.FAILED


class TestVerdictRule:
    def _judge(self, actual, no_action, lower_is_better=False, adjustment=0.0, baseline=1000.0, expected_lower=50.0):
        return _verdict_from_three_lines(actual, baseline, no_action, expected_lower, adjustment, lower_is_better)

    def test_reaching_the_solution_line_holds_up(self):
        assert self._judge(actual=1060.0, no_action=1000.0)[0] == V

    def test_beating_no_action_without_reaching_the_solution_line_is_partial(self):
        """The case the old code got wrong: held at 1,000 against a decline to 700."""
        verdict, total, credited = self._judge(actual=1000.0, no_action=700.0)
        assert verdict == P and total == 0.0 and credited == 300.0

    def test_holding_level_when_nothing_was_falling_did_not_hold(self):
        assert self._judge(actual=1000.0, no_action=1000.0)[0] == F

    def test_doing_worse_than_no_action_did_not_hold(self):
        assert self._judge(actual=650.0, no_action=700.0)[0] == F

    def test_movement_explained_by_something_else_is_not_credited(self):
        # +60 since acceptance, but untouched segments rose 40 too: only 20 is left.
        verdict, total, credited = self._judge(actual=1060.0, no_action=1000.0, adjustment=40.0)
        assert verdict == P and total == 60.0 and credited == 20.0

    def test_for_a_cost_lower_is_better(self):
        # Expected to cut 50. Fell from 1000 to 940: held up.
        assert self._judge(actual=940.0, no_action=1000.0, lower_is_better=True)[0] == V
        # Rose to 1040, but No Action would have reached 1100: beat doing nothing.
        assert self._judge(actual=1040.0, no_action=1100.0, lower_is_better=True)[0] == P
        # Rose to 1040 when nothing was rising: did not hold.
        assert self._judge(actual=1040.0, no_action=1000.0, lower_is_better=True)[0] == F


def _register(**over) -> RegisterSolutionRequest:
    base = dict(
        request_id="r", principal_id="cfo_001", situation_id="s", kpi_id="net_revenue",
        solution_description="x", expected_impact_lower=50.0, expected_impact_upper=150.0,
        measurement_window_days=90, baseline_kpi_value=1000.0, baseline_period="2026-06",
        strategy_snapshot=StrategySnapshot(
            principal_priorities=[], principal_role="CFO", business_process_domain="f",
            data_product_id="dp", kpi_threshold_at_approval=0.0, key_assumptions=[],
            business_context_name="x", captured_at="2026-07-02T00:00:00Z"),
    )
    base.update(over)
    return RegisterSolutionRequest(**base)


@pytest_asyncio.fixture
async def agent():
    a = await A9_Value_Assurance_Agent.create_from_registry(A9ValueAssuranceAgentConfig().model_dump())
    a.orchestrator = None
    a._va_store = None
    a._registry_factory = None
    return a


async def _evaluate(agent, solution_id, **kw):
    return await agent.evaluate_solution_impact(EvaluateSolutionRequest(
        request_id="e", principal_id="cfo_001", solution_id=solution_id, **kw))


def _set(agent, solution_id, **updates):
    agent._solutions_store[solution_id] = agent._solutions_store[solution_id].model_copy(update=updates)


class TestWindow:
    @pytest.mark.asyncio
    async def test_no_verdict_before_the_window_closes(self, agent):
        r = await agent.register_solution(_register())
        with pytest.raises(MeasurementWindowOpenError):
            await _evaluate(agent, r.solution_id, current_kpi_value=1060.0)
        sol = agent._solutions_store[r.solution_id]
        assert sol.status == SolutionVerdict.MEASURING and sol.phase == SolutionPhase.APPROVED
        assert sol.impact_evaluation is None

    @pytest.mark.asyncio
    async def test_two_of_three_months_measured_is_still_open(self, agent):
        r = await agent.register_solution(_register())
        _set(agent, r.solution_id, actual_trend=[1000.0, 1010.0, 1020.0], actual_trend_dates=["2026-06", "2026-07", "2026-08"])
        with pytest.raises(MeasurementWindowOpenError):
            await _evaluate(agent, r.solution_id)

    @pytest.mark.asyncio
    async def test_the_actual_line_is_used_at_the_closing_month(self, agent):
        r = await agent.register_solution(_register())
        _set(agent, r.solution_id, actual_trend=[1000.0, 1020.0, 1040.0, 1070.0, 1300.0],
             actual_trend_dates=["2026-06", "2026-07", "2026-08", "2026-09", "2026-10"])
        resp = await _evaluate(agent, r.solution_id, current_kpi_value=5.0)   # the supplied number is ignored
        assert resp.evaluation.current_kpi_value == 1070.0                    # month 3, not the latest month
        assert resp.evaluation.total_kpi_change == 70.0
        assert resp.evaluation.verdict == V

    @pytest.mark.asyncio
    async def test_a_supplied_reading_is_used_once_the_calendar_window_has_closed(self, agent):
        r = await agent.register_solution(_register())
        _set(agent, r.solution_id, approved_at="2026-01-01T00:00:00Z")
        resp = await _evaluate(agent, r.solution_id, current_kpi_value=1060.0)
        assert resp.evaluation.verdict == V

    @pytest.mark.asyncio
    async def test_a_closed_window_with_no_reading_at_all_is_still_open(self, agent):
        r = await agent.register_solution(_register())
        _set(agent, r.solution_id, approved_at="2026-01-01T00:00:00Z")
        with pytest.raises(MeasurementWindowOpenError):
            await _evaluate(agent, r.solution_id)


class TestAgainstTheNoActionLine:
    @pytest.mark.asyncio
    async def test_holding_against_a_decline_is_credited(self, agent):
        """The regression case, end to end through the agent."""
        falling = await agent.register_solution(_register(situation_id="falling", pre_approval_monthly_slope=-100.0))
        flat = await agent.register_solution(_register(situation_id="flat"))
        for sid in (falling.solution_id, flat.solution_id):
            _set(agent, sid, actual_trend=[1000.0, 1000.0, 1000.0, 1000.0],
                 actual_trend_dates=["2026-06", "2026-07", "2026-08", "2026-09"])
        e_falling = (await _evaluate(agent, falling.solution_id)).evaluation
        e_flat = (await _evaluate(agent, flat.solution_id)).evaluation
        assert e_falling.verdict == P and e_falling.attributable_impact == 300.0
        assert e_flat.verdict == F and e_flat.attributable_impact == 0.0


class TestSolutionLineDirection:
    @pytest.mark.asyncio
    async def test_for_a_cost_the_solution_line_points_down(self, agent):
        r = await agent.register_solution(_register(kpi_id="sga_expense", kpi_lower_is_better=True))
        sol = agent._solutions_store[r.solution_id]
        assert sol.strategy_snapshot.kpi_lower_is_better is True
        assert sol.expected_trend[0] == 1000.0 and sol.expected_trend[-1] == 900.0   # midpoint cut of 100

    @pytest.mark.asyncio
    async def test_otherwise_it_points_up(self, agent):
        r = await agent.register_solution(_register())
        assert agent._solutions_store[r.solution_id].expected_trend[-1] == 1100.0
