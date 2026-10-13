"""The baseline an outcome is measured against is the KPI's actual value at approval.

Found live 2026-10-13: the baseline was `kpi_threshold_at_approval` (the KPI's
warning threshold, or 0 when it had none). It was never the KPI's value. Every
locally "measured" solution had a baseline of 0, so "total change" was simply the
number the caller supplied: a $35M revenue figure would have read as a +$35M change.
"""
from __future__ import annotations

import pytest
import pytest_asyncio

from src.agents.agent_config_models import A9ValueAssuranceAgentConfig
from src.agents.models.value_assurance_models import (
    EvaluateSolutionRequest,
    RegisterSolutionRequest,
    StrategySnapshot,
)
from src.agents.new.a9_value_assurance_agent import (
    A9_Value_Assurance_Agent,
    BaselineNotRecordedError,
)
from src.api.routes.workflows import _baseline_from_situation


def _snapshot(**over) -> StrategySnapshot:
    base = dict(
        principal_priorities=["margin"], principal_role="CFO", business_process_domain="finance",
        data_product_id="dp", kpi_threshold_at_approval=45.0, key_assumptions=[],
        business_context_name="Summit", captured_at="2026-10-04T00:00:00Z",
    )
    base.update(over)
    return StrategySnapshot(**base)


def _register(**over) -> RegisterSolutionRequest:
    base = dict(
        request_id="r1", principal_id="cfo_001", situation_id="sit1", kpi_id="net_revenue",
        solution_description="win-back", expected_impact_lower=2.0, expected_impact_upper=6.0,
        strategy_snapshot=_snapshot(),
    )
    base.update(over)
    return RegisterSolutionRequest(**base)


@pytest_asyncio.fixture
async def agent():
    a = await A9_Value_Assurance_Agent.create_from_registry(A9ValueAssuranceAgentConfig().model_dump())
    a.orchestrator = None
    a._va_store = None  # never touch live Supabase in unit tests
    return a


class TestEvaluationNeedsARecordedBaseline:
    @pytest.mark.asyncio
    async def test_no_recorded_value_refuses_instead_of_using_the_threshold(self, agent):
        reg = await agent.register_solution(_register())  # threshold 45.0, no KPI value
        with pytest.raises(BaselineNotRecordedError):
            await agent.evaluate_solution_impact(EvaluateSolutionRequest(
                request_id="e1", principal_id="cfo_001", solution_id=reg.solution_id,
                current_kpi_value=49.0,
            ))

    @pytest.mark.asyncio
    async def test_change_is_measured_from_the_recorded_value(self, agent):
        reg = await agent.register_solution(_register(baseline_kpi_value=40.0, baseline_period="2026-09"))
        stored = agent._solutions_store[reg.solution_id]
        assert stored.strategy_snapshot.kpi_value_at_approval == 40.0
        assert stored.strategy_snapshot.kpi_value_period == "2026-09"
        assert stored.strategy_snapshot.kpi_threshold_at_approval == 45.0  # untouched
        resp = await agent.evaluate_solution_impact(EvaluateSolutionRequest(
            request_id="e2", principal_id="cfo_001", solution_id=reg.solution_id,
            current_kpi_value=49.0,
        ))
        assert resp.evaluation.baseline_kpi_value == 40.0
        assert resp.evaluation.total_kpi_change == 9.0  # 49 - 40, not 49 - 45

    @pytest.mark.asyncio
    async def test_a_recorded_zero_is_a_real_baseline(self, agent):
        reg = await agent.register_solution(_register(baseline_kpi_value=0.0, baseline_period="2026-09"))
        resp = await agent.evaluate_solution_impact(EvaluateSolutionRequest(
            request_id="e3", principal_id="cfo_001", solution_id=reg.solution_id,
            current_kpi_value=3.0,
        ))
        assert resp.evaluation.total_kpi_change == 3.0

    @pytest.mark.asyncio
    async def test_projection_lines_start_from_the_recorded_value(self, agent):
        reg = await agent.register_solution(_register(baseline_kpi_value=40.0, baseline_period="2026-09"))
        stored = agent._solutions_store[reg.solution_id]
        assert stored.baseline_kpi_value == 40.0 and stored.actual_trend == [40.0]


SERIES = [
    {"period": "2026-08", "value": 14410757.27},
    {"period": "2026-09", "value": 13108162.82},
    {"period": "2026-10", "value": 12212459.56},   # the current, partial month
    {"period": "2026-11", "value": 11543734.37},   # later-dated rows (the demo data has them)
]


def _situation(kpi_id="net_revenue", series=SERIES) -> dict:
    return {"kpi_id": kpi_id, "kpi_value": {"value": 3131581.8, "monthly_values": series}}


class TestBaselineFromSituation:
    def test_last_complete_month_before_approval(self):
        assert _baseline_from_situation(_situation(), "net_revenue", today="2026-10-07") == (13108162.82, "2026-09")

    def test_current_and_later_months_are_never_the_baseline(self):
        value, period = _baseline_from_situation(_situation(), "net_revenue", today="2026-10-07")
        assert period < "2026-10" and value != 12212459.56

    def test_a_reframed_kpi_gets_no_baseline_from_another_kpis_series(self):
        assert _baseline_from_situation(_situation("gross_margin_pct"), "cogs", today="2026-10-07") == (None, None)

    @pytest.mark.parametrize("payload", [{}, {"kpi_id": "net_revenue"}, _situation(series=[]),
                                          _situation(series=[{"period": "2026-10", "value": 1.0}])])
    def test_nothing_usable_means_none_not_a_guess(self, payload):
        assert _baseline_from_situation(payload, "net_revenue", today="2026-10-07") == (None, None)

    def test_an_unparseable_value_is_skipped(self):
        series = [{"period": "2026-09", "value": "n/a"}, "junk", {"period": "2026-08", "value": 5.0}]
        assert _baseline_from_situation(_situation(series=series), "net_revenue", today="2026-10-07") == (5.0, "2026-08")

    def test_a_series_with_untrustworthy_month_labels_gives_no_baseline(self):
        """The Hess (SQL Server) series as returned live on 2026-10-13."""
        hess = [{"period": p, "value": v} for p, v in [
            ("2025-01", -17188774), ("2025-01", -17579428), ("2026-00", -23740041),
            ("2026-00", -23136480), ("2026-00", -21728173)]]
        assert _baseline_from_situation(_situation(series=hess), "net_revenue", today="2026-10-13") == (None, None)

    @pytest.mark.parametrize("bad", ["2026-00", "2026-13", "2026-9", "2026-Q3"])
    def test_one_bad_label_discredits_the_whole_series(self, bad):
        series = [{"period": "2026-08", "value": 5.0}, {"period": bad, "value": 6.0}]
        assert _baseline_from_situation(_situation(series=series), "net_revenue", today="2026-10-13") == (None, None)
