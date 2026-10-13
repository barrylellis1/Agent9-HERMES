"""src/analysis/monthly_series.py and the No Action slope taken from it at approval.

Found live 2026-10-13: the No Action line was always flat. Its slope was read from
deep_analysis_output["aggregates"], a field Deep Analysis has never returned. Gross
Profit had fallen 4.92M -> 4.54M -> 3.94M over the three months before approval and
the stored line was 3.94M for every month.
"""
from __future__ import annotations

import pytest
import pytest_asyncio

from src.agents.agent_config_models import A9ValueAssuranceAgentConfig
from src.agents.models.deep_analysis_models import DeepAnalysisResponse
from src.agents.models.value_assurance_models import RegisterSolutionRequest, StrategySnapshot
from src.agents.new.a9_value_assurance_agent import A9_Value_Assurance_Agent
from src.analysis.monthly_series import (
    complete_months_before,
    complete_months_between,
    trend_slope_per_month,
    trusted_months,
)
from src.api.routes.workflows import _trend_slope_from_situation

GROSS_PROFIT = [  # as returned live for lubricants on 2026-10-13
    {"period": "2026-04", "value": 3697310}, {"period": "2026-05", "value": 4274060},
    {"period": "2026-06", "value": 4778482}, {"period": "2026-07", "value": 4915051},
    {"period": "2026-08", "value": 4537714}, {"period": "2026-09", "value": 3936089},
    {"period": "2026-10", "value": 3479447}, {"period": "2026-11", "value": 3155406},
]


class TestTrustedMonths:
    def test_sorted_pairs(self):
        assert trusted_months([{"period": "2026-09", "value": 2}, {"period": "2026-08", "value": 1}]) == [
            ("2026-08", 1.0), ("2026-09", 2.0)]

    @pytest.mark.parametrize("series", [
        None, [], "x",
        [{"period": "2026-00", "value": 1}, {"period": "2026-09", "value": 2}],   # not a month
        [{"period": "2026-09", "value": 1}, {"period": "2026-09", "value": 2}],   # repeated
        [{"period": "2026-9", "value": 1}],
    ])
    def test_untrustworthy_series_is_none(self, series):
        assert trusted_months(series) is None

    def test_a_bad_value_drops_that_point_only(self):
        assert trusted_months([{"period": "2026-08", "value": "n/a"}, {"period": "2026-09", "value": 2}]) == [("2026-09", 2.0)]


class TestWindows:
    def test_before_excludes_the_named_month_and_later(self):
        assert [p for p, _ in complete_months_before(GROSS_PROFIT, "2026-10")][-1] == "2026-09"

    def test_between_is_exclusive_at_both_ends(self):
        assert [p for p, _ in complete_months_between(GROSS_PROFIT, "2026-08", "2026-11")] == ["2026-09", "2026-10"]


class TestTrendSlope:
    def test_a_steady_decline(self):
        months = [("2026-07", 300.0), ("2026-08", 200.0), ("2026-09", 100.0)]
        assert trend_slope_per_month(months) == pytest.approx(-100.0)

    def test_fewer_than_three_months_is_not_a_trend(self):
        assert trend_slope_per_month([("2026-08", 200.0), ("2026-09", 100.0)]) is None

    def test_a_gap_between_months_is_measured_on_the_calendar(self):
        # 300 in June, 100 in August: two months apart, so -100 a month, not -200.
        months = [("2026-06", 300.0), ("2026-08", 100.0), ("2026-09", 0.0)]
        assert trend_slope_per_month(months) == pytest.approx(-100.0, rel=0.05)

    def test_only_the_last_six_months_count(self):
        old = [(f"2025-{m:02d}", 1000.0 * m) for m in range(1, 7)]           # rising long ago
        recent = [(f"2026-{m:02d}", 500.0 - 10.0 * m) for m in range(1, 7)]  # falling now
        assert trend_slope_per_month(old + recent) == pytest.approx(-10.0)


class TestSlopeAtApproval:
    def test_the_field_the_old_code_read_does_not_exist(self):
        assert "aggregates" not in DeepAnalysisResponse.model_fields

    def test_slope_comes_from_the_months_before_approval(self):
        payload = {"kpi_id": "gross_profit", "kpi_value": {"monthly_values": GROSS_PROFIT}}
        slope = _trend_slope_from_situation(payload, "gross_profit", today="2026-10-13")
        # Apr..Sep only: October and November are not before approval.
        assert slope == pytest.approx(trend_slope_per_month(
            [(p["period"], float(p["value"])) for p in GROSS_PROFIT[:6]]))

    def test_a_reframed_kpi_or_untrusted_series_gives_no_slope(self):
        payload = {"kpi_id": "gross_profit", "kpi_value": {"monthly_values": GROSS_PROFIT}}
        assert _trend_slope_from_situation(payload, "cogs", today="2026-10-13") is None
        bad = {"kpi_id": "x", "kpi_value": {"monthly_values": [{"period": "2026-00", "value": 1}] * 4}}
        assert _trend_slope_from_situation(bad, "x", today="2026-10-13") is None


@pytest_asyncio.fixture
async def agent():
    a = await A9_Value_Assurance_Agent.create_from_registry(A9ValueAssuranceAgentConfig().model_dump())
    a.orchestrator = None
    a._va_store = None
    a._registry_factory = None
    return a


def _register(**over) -> RegisterSolutionRequest:
    base = dict(
        request_id="r", principal_id="cfo_001", situation_id="s", kpi_id="gross_profit",
        solution_description="x", expected_impact_lower=50.0, expected_impact_upper=150.0,
        measurement_window_days=90, baseline_kpi_value=1000.0, baseline_period="2026-09",
        strategy_snapshot=StrategySnapshot(
            principal_priorities=[], principal_role="CFO", business_process_domain="f",
            data_product_id="dp", kpi_threshold_at_approval=0.0, key_assumptions=[],
            business_context_name="x", captured_at="2026-10-13T00:00:00Z"),
    )
    base.update(over)
    return RegisterSolutionRequest(**base)


class TestNoActionLine:
    @pytest.mark.asyncio
    async def test_the_line_continues_the_measured_trend(self, agent):
        r = await agent.register_solution(_register(pre_approval_monthly_slope=-100.0))
        sol = agent._solutions_store[r.solution_id]
        assert sol.inaction_trend[:4] == [1000.0, 900.0, 800.0, 700.0]
        assert sol.pre_approval_slope == -100.0

    @pytest.mark.asyncio
    async def test_no_measured_trend_means_a_flat_line(self, agent):
        r = await agent.register_solution(_register())
        assert set(agent._solutions_store[r.solution_id].inaction_trend) == {1000.0}

    @pytest.mark.asyncio
    async def test_an_opportunity_stays_flat_whatever_the_trend(self, agent):
        r = await agent.register_solution(_register(pre_approval_monthly_slope=80.0, analysis_mode="opportunity"))
        assert set(agent._solutions_store[r.solution_id].inaction_trend) == {1000.0}
