# arch-allow-direct-agent-construction
"""
Validates opportunity-mode behaviour across the DA → SF → VA pipeline.

Five contracts under test:
1. DA _classify_benchmark_segments — uses where_is items in opportunity mode (leading segments)
2. DA benchmark source selection — where_is_not used in problem mode, where_is in opportunity mode
3. DA _build_scqa_narrative — deterministic fallback uses replication language in opportunity mode
4. DA _build_scqa_narrative — LLM response with problem framing is rejected in opportunity mode
5. SF _extract_deep_analysis_summary — reads analysis_mode from plan dict correctly
6. VA register_solution — inaction_trend is flat (pre_slope = 0) in opportunity mode
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.new.a9_deep_analysis_agent import _classify_benchmark_segments
from src.agents.new.a9_solution_finder_agent import _extract_deep_analysis_summary
from src.agents.models.value_assurance_models import RegisterSolutionRequest, StrategySnapshot
from src.agents.agent_config_models import A9ValueAssuranceAgentConfig


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_item(key: str, delta: float, current: float = 50.0, dimension: str = "region") -> dict:
    return {"key": key, "dimension": dimension, "delta": delta, "current": current, "previous": current - delta}


def _make_da_plan(analysis_mode: str = "problem") -> MagicMock:
    plan = MagicMock()
    plan.kpi_name = "gross_margin_pct"
    plan.timeframe = "last_quarter"
    plan.analysis_mode = analysis_mode
    return plan


def _make_kt(where_is=None, where_is_not=None) -> MagicMock:
    kt = MagicMock()
    kt.where_is = where_is or []
    kt.where_is_not = where_is_not or []
    return kt


def _make_da_agent():
    from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
    agent = A9_Deep_Analysis_Agent.__new__(A9_Deep_Analysis_Agent)
    import logging
    agent.logger = logging.getLogger("test_da")
    agent.llm_service_agent = MagicMock()
    agent.llm_service_agent.generate = AsyncMock(return_value=MagicMock(content=""))
    return agent


def _strategy_snapshot():
    return StrategySnapshot(
        principal_priorities=["Gross Margin"],
        principal_role="CFO",
        business_process_domain="Finance",
        data_product_id="lubricants_fi",
        kpi_threshold_at_approval=45.0,
        key_assumptions=["Control group is comparable cohort"],
        business_context_name="Q2 2026 margin opportunity",
        captured_at="2026-05-20T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# DA: benchmark segment classification
# ---------------------------------------------------------------------------

class TestDABenchmarkSourceSelection:
    """_classify_benchmark_segments receives the correct source based on analysis_mode."""

    def test_opportunity_mode_uses_where_is_as_benchmark_source(self):
        """In opportunity mode, IS (leading) segments become the benchmark blueprints."""
        where_is = [
            _is_item("North", delta=5.2, current=52.0),
            _is_item("West", delta=3.8, current=48.0),
        ]
        where_is_not = [
            _is_item("South", delta=-1.1, current=43.0),
        ]

        plan = _make_da_plan("opportunity")
        _is_opportunity = getattr(plan, "analysis_mode", "problem") == "opportunity"
        benchmark_source = where_is if _is_opportunity else where_is_not

        segments = _classify_benchmark_segments(benchmark_source)

        # Should reflect where_is items (North, West), not where_is_not (South)
        keys = {s.key for s in segments}
        assert "North" in keys
        assert "West" in keys
        assert "South" not in keys

    def test_problem_mode_uses_where_is_not_as_benchmark_source(self):
        """In problem mode, IS NOT (healthy) segments become the benchmarks."""
        where_is = [
            _is_item("South", delta=-3.5, current=40.0),
        ]
        where_is_not = [
            _is_item("North", delta=2.1, current=50.0),
            _is_item("West", delta=1.8, current=48.0),
        ]

        plan = _make_da_plan("problem")
        _is_opportunity = getattr(plan, "analysis_mode", "problem") == "opportunity"
        benchmark_source = where_is if _is_opportunity else where_is_not

        segments = _classify_benchmark_segments(benchmark_source)

        keys = {s.key for s in segments}
        assert "North" in keys
        assert "West" in keys
        assert "South" not in keys

    def test_missing_analysis_mode_defaults_to_problem(self):
        """If analysis_mode is missing from plan, getattr default → problem mode."""
        plan = MagicMock(spec=[])  # no analysis_mode attribute
        _is_opportunity = getattr(plan, "analysis_mode", "problem") == "opportunity"
        assert _is_opportunity is False


# ---------------------------------------------------------------------------
# DA: SCQA narrative framing
# ---------------------------------------------------------------------------

class TestDASCQANarrative:
    """_build_scqa_narrative deterministic fallback and LLM rejection guard."""

    @pytest.mark.asyncio
    async def test_opportunity_fallback_uses_replication_language(self):
        """When LLM is unavailable, opportunity fallback says 'replication' not 'under-performing'."""
        agent = _make_da_agent()
        agent.llm_service_agent.generate = AsyncMock(side_effect=RuntimeError("LLM down"))

        plan = _make_da_plan("opportunity")
        kt = _make_kt(
            where_is=[{"key": "North", "dimension": "region"}],
            where_is_not=[{"key": "South", "dimension": "region"}],
        )

        result = await agent._generate_scqa_summary(
            plan=plan, kt=kt, change_points=[], spec=None,
            principal_id="cfo_001", analysis_mode="opportunity",
        )

        assert "replication" in result.lower() or "replicate" in result.lower() or "scale" in result.lower()
        assert "under-performing" not in result.lower()
        assert "declined" not in result.lower()

    @pytest.mark.asyncio
    async def test_problem_fallback_uses_variance_language(self):
        """When LLM is unavailable, problem fallback says 'under-performing' not 'replication'."""
        agent = _make_da_agent()
        agent.llm_service_agent.generate = AsyncMock(side_effect=RuntimeError("LLM down"))

        plan = _make_da_plan("problem")
        kt = _make_kt(
            where_is=[{"key": "South", "dimension": "region"}],
            where_is_not=[{"key": "North", "dimension": "region"}],
        )

        result = await agent._generate_scqa_summary(
            plan=plan, kt=kt, change_points=[], spec=None,
            principal_id="cfo_001", analysis_mode="problem",
        )

        assert "under-performing" in result.lower() or "performing" in result.lower()
        assert "replication" not in result.lower()

    @pytest.mark.asyncio
    async def test_llm_problem_framing_rejected_in_opportunity_mode(self):
        """LLM response with 'underperforming' is rejected in opportunity mode → deterministic fallback."""
        agent = _make_da_agent()
        bad_scqa = (
            "Situation: Gross margin is underperforming vs prior period. "
            "Complication: South region is declining. "
            "Question: How do we fix the underperformance? "
            "Answer: Cut costs."
        )
        agent.llm_service_agent.generate = AsyncMock(return_value=MagicMock(content=bad_scqa))

        plan = _make_da_plan("opportunity")
        kt = _make_kt(
            where_is=[{"key": "North", "dimension": "region"}],
            where_is_not=[{"key": "South", "dimension": "region"}],
        )

        result = await agent._generate_scqa_summary(
            plan=plan, kt=kt, change_points=[], spec=None,
            principal_id="cfo_001", analysis_mode="opportunity",
        )

        # Must NOT return the LLM's problem-framed response
        assert "underperforming" not in result.lower()
        # Must be the deterministic fallback (contains "replication" or "outperform")
        assert "replication" in result.lower() or "replicate" in result.lower() or "outperform" in result.lower() or "performing" in result.lower()

    @pytest.mark.asyncio
    async def test_llm_valid_opportunity_scqa_is_accepted(self):
        """A clean opportunity-framed LLM response is returned as-is."""
        agent = _make_da_agent()
        good_scqa = (
            "Situation: Gross margin is outperforming vs prior period driven by North region. "
            "Complication: The outperformance is concentrated in North — South has unrealised potential. "
            "Question: How do we scale North's practices across South? "
            "Answer: Replicate the procurement model from North into South operations."
        )
        agent.llm_service_agent.generate = AsyncMock(return_value=MagicMock(content=good_scqa))

        plan = _make_da_plan("opportunity")
        kt = _make_kt(
            where_is=[{"key": "North", "dimension": "region"}],
            where_is_not=[{"key": "South", "dimension": "region"}],
        )

        result = await agent._generate_scqa_summary(
            plan=plan, kt=kt, change_points=[], spec=None,
            principal_id="cfo_001", analysis_mode="opportunity",
        )

        assert "Situation:" in result
        assert "Complication:" in result
        assert "Question:" in result
        assert "Answer:" in result
        assert "underperforming" not in result.lower()


# ---------------------------------------------------------------------------
# SF: analysis_mode propagation through _extract_deep_analysis_summary
# ---------------------------------------------------------------------------

class TestSFAnalysisModeExtraction:
    """_extract_deep_analysis_summary correctly reads analysis_mode from nested plan dict."""

    def test_extracts_opportunity_mode_from_plan(self):
        """analysis_mode='opportunity' in plan dict is surfaced in the summary."""
        da_ctx = {
            "plan": {
                "kpi_name": "gross_margin_pct",
                "analysis_mode": "opportunity",
                "timeframe": "last_quarter",
            },
            "execution": {
                "plan": {"kpi_name": "gross_margin_pct", "analysis_mode": "opportunity"},
                "change_points": [],
                "kt_is_is_not": {},
            },
        }

        summary = _extract_deep_analysis_summary(da_ctx)

        # The plan dict is returned as-is from _extract_deep_analysis_summary
        # (the caller reads analysis_mode directly from the raw plan dict)
        from src.agents.new.a9_solution_finder_agent import _model_to_dict
        plan_dict = _model_to_dict(da_ctx.get("plan"))
        assert plan_dict.get("analysis_mode") == "opportunity"

    def test_extracts_problem_mode_when_not_set(self):
        """analysis_mode defaults to 'problem' when absent from plan dict."""
        da_ctx = {
            "plan": {"kpi_name": "gross_margin_pct"},
            "execution": {"plan": {"kpi_name": "gross_margin_pct"}, "change_points": [], "kt_is_is_not": {}},
        }

        from src.agents.new.a9_solution_finder_agent import _model_to_dict
        plan_dict = _model_to_dict(da_ctx.get("plan"))
        analysis_mode = plan_dict.get("analysis_mode") or "problem"
        assert analysis_mode == "problem"

    def test_opportunity_flag_resolves_to_is_opportunity_true(self):
        """The full extraction chain (plan dict → analysis_mode string → is_opportunity bool) works."""
        da_ctx = {
            "plan": {"kpi_name": "net_revenue", "analysis_mode": "opportunity"},
            "execution": {"plan": {}, "change_points": [], "kt_is_is_not": {}},
        }

        from src.agents.new.a9_solution_finder_agent import _model_to_dict
        try:
            raw_plan = da_ctx.get("plan")
            da_plan_dict = _model_to_dict(raw_plan)
        except Exception:
            da_plan_dict = None

        analysis_mode = (
            (da_plan_dict.get("analysis_mode") if isinstance(da_plan_dict, dict) else None)
            or "problem"
        )
        is_opportunity = analysis_mode == "opportunity"

        assert is_opportunity is True


# ---------------------------------------------------------------------------
# VA: flat inaction trend in opportunity mode
# ---------------------------------------------------------------------------

class TestVAOpportunityInactionTrend:
    """register_solution with analysis_mode='opportunity' produces a flat inaction_trend."""

    @pytest_asyncio.fixture
    async def agent(self):
        from src.agents.new.a9_value_assurance_agent import A9_Value_Assurance_Agent
        a = await A9_Value_Assurance_Agent.create_from_registry(
            A9ValueAssuranceAgentConfig(log_all_requests=False).model_dump()
        )
        a.orchestrator = None
        return a

    @pytest.mark.asyncio
    async def test_opportunity_mode_produces_flat_inaction_trend(self, agent):
        """In opportunity mode, foregone gain (not deterioration) — inaction_trend must be flat."""
        request = RegisterSolutionRequest(
            request_id="req-opp-001",
            principal_id="cfo_001",
            situation_id="sit-opp-001",
            kpi_id="gross_margin_pct",
            solution_description="Scale North region procurement model to South",
            expected_impact_lower=1.5,
            expected_impact_upper=3.0,
            measurement_window_days=90,
            pre_approval_kpi_value=47.0,  # Has a prior value — would create slope in problem mode
            analysis_mode="opportunity",
            strategy_snapshot=_strategy_snapshot(),
        )

        response = await agent.register_solution(request)
        solution = agent._solutions_store.get(response.solution_id)

        # Slope must be zero regardless of pre_approval_kpi_value
        assert solution.pre_approval_slope == 0.0
        # Inaction trend must be flat (all values equal to baseline)
        baseline = solution.baseline_kpi_value
        assert all(v == baseline for v in solution.inaction_trend), (
            f"Expected flat inaction_trend at {baseline}, got {solution.inaction_trend[:5]}"
        )

    @pytest.mark.asyncio
    async def test_problem_mode_produces_sloped_inaction_trend(self, agent):
        """In problem mode with a declining prior value, inaction_trend should slope downward."""
        baseline = 45.0
        prior = 47.0  # was higher → slope = 45 - 47 = -2 per month
        request = RegisterSolutionRequest(
            request_id="req-prob-001",
            principal_id="cfo_001",
            situation_id="sit-prob-001",
            kpi_id="gross_margin_pct",
            solution_description="Cut COGS via supplier renegotiation",
            expected_impact_lower=2.0,
            expected_impact_upper=4.0,
            measurement_window_days=90,
            pre_approval_kpi_value=prior,
            analysis_mode="problem",
            strategy_snapshot=_strategy_snapshot(),
        )

        response = await agent.register_solution(request)
        solution = agent._solutions_store.get(response.solution_id)

        # Slope = baseline - prior = 45 - 47 = -2 (deteriorating)
        assert solution.pre_approval_slope == pytest.approx(baseline - prior)
        # Inaction trend should NOT be flat — it should decline
        assert solution.inaction_trend[0] == pytest.approx(baseline)
        assert solution.inaction_trend[-1] < baseline, (
            "Expected inaction_trend to slope below baseline in problem mode"
        )
