# arch-allow-direct-agent-construction
"""
Unit tests for A9_Value_Assurance_Agent (Phase 7A).

Covers all 6 entrypoints:
  1. register_solution        — registration and default snapshot building
  2. evaluate_solution_impact — DiD attribution logic and verdict derivation
  3. check_strategy_alignment — drift detection and alignment verdicts
  4. project_inaction_cost    — trend fitting and cost projection
  5. get_portfolio_summary    — aggregation across solutions
  6. generate_narrative       — LLM-routed narrative generation with fallback

Also tests the 9-entry composite verdict lookup matrix exhaustively.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.agents.new.a9_value_assurance_agent import (
    A9_Value_Assurance_Agent,
    _build_composite_verdict,
)
from src.agents.models.value_assurance_models import (
    AcceptedSolution,
    CheckStrategyAlignmentRequest,
    CompositeVerdict,
    ConfidenceLevel,
    EvaluateSolutionRequest,
    GenerateNarrativeRequest,
    ImpactEvaluation,
    PortfolioSummaryRequest,
    ProjectInactionCostRequest,
    RegisterSolutionRequest,
    SolutionVerdict,
    StrategyAlignment,
    StrategyAlignmentCheck,
    StrategySnapshot,
)
from src.agents.agent_config_models import A9ValueAssuranceAgentConfig


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def config():
    """Standard config for all tests."""
    return A9ValueAssuranceAgentConfig(log_all_requests=False)


@pytest_asyncio.fixture
async def agent(config):
    """Bare agent with no orchestrator (pure-logic tests)."""
    a = await A9_Value_Assurance_Agent.create_from_registry(config.model_dump())
    a.orchestrator = None  # Disable orchestrator for isolation
    return a


@pytest.fixture
def strategy_snapshot() -> StrategySnapshot:
    """Reusable snapshot for test solutions."""
    return StrategySnapshot(
        principal_priorities=["Gross Margin", "Revenue Growth"],
        principal_role="CFO",
        business_process_domain="Finance",
        data_product_id="lubricants_fi",
        kpi_threshold_at_approval=45.0,
        key_assumptions=["Control group represents same cohort"],
        business_context_name="Q1 2026 margin recovery",
        captured_at=datetime.utcnow().isoformat() + "Z",
    )


@pytest.fixture
def register_request(strategy_snapshot) -> RegisterSolutionRequest:
    """Reusable registration request."""
    return RegisterSolutionRequest(
        request_id="req-001",
        principal_id="cfo_001",
        situation_id="sit-001",
        kpi_id="lub_gross_margin_pct",
        solution_description="Renegotiate supplier contracts to reduce COGS",
        expected_impact_lower=2.0,
        expected_impact_upper=4.5,
        measurement_window_days=30,
        benchmark_segments=[{"dimension": "product_line", "key": "lubricants", "delta": -2.1, "delta_pct": -4.5, "benchmark_type": "control_group"}],
        ma_market_signals=[
            "Global oil prices dropped 12% in Feb 2026",
            "Competitor margin expansion signals supply-side weakness",
        ],
        strategy_snapshot=strategy_snapshot,
    )


# ---------------------------------------------------------------------------
# Test: Composite Verdict Matrix (9 cells tested)
# ---------------------------------------------------------------------------


def test_composite_verdict_validated_aligned():
    """VALIDATED + ALIGNED → Full success, include_in_roi, no exec attention."""
    verdict = _build_composite_verdict(
        SolutionVerdict.VALIDATED, StrategyAlignment.ALIGNED
    )
    assert verdict.composite_label == "Full success"
    assert verdict.include_in_roi_totals is True
    assert verdict.executive_attention_required is False


def test_composite_verdict_validated_drifted():
    """VALIDATED + DRIFTED → Misdirected win, include_in_roi, exec attention."""
    verdict = _build_composite_verdict(
        SolutionVerdict.VALIDATED, StrategyAlignment.DRIFTED
    )
    assert verdict.composite_label == "Misdirected win"
    assert verdict.include_in_roi_totals is True
    assert verdict.executive_attention_required is True


def test_composite_verdict_validated_superseded():
    """VALIDATED + SUPERSEDED → Obsolete win, exclude_from_roi, no exec attention."""
    verdict = _build_composite_verdict(
        SolutionVerdict.VALIDATED, StrategyAlignment.SUPERSEDED
    )
    assert verdict.composite_label == "Obsolete win"
    assert verdict.include_in_roi_totals is False
    assert verdict.executive_attention_required is False


def test_composite_verdict_partial_aligned():
    """PARTIAL + ALIGNED → Work in progress, include_in_roi, no exec attention."""
    verdict = _build_composite_verdict(
        SolutionVerdict.PARTIAL, StrategyAlignment.ALIGNED
    )
    assert verdict.composite_label == "Work in progress"
    assert verdict.include_in_roi_totals is True
    assert verdict.executive_attention_required is False


def test_composite_verdict_partial_drifted():
    """PARTIAL + DRIFTED → Partial misdirection, exclude_from_roi, exec attention."""
    verdict = _build_composite_verdict(
        SolutionVerdict.PARTIAL, StrategyAlignment.DRIFTED
    )
    assert verdict.composite_label == "Partial misdirection"
    assert verdict.include_in_roi_totals is False
    assert verdict.executive_attention_required is True


def test_composite_verdict_partial_superseded():
    """PARTIAL + SUPERSEDED → Acceptable loss, exclude_from_roi, no exec attention."""
    verdict = _build_composite_verdict(
        SolutionVerdict.PARTIAL, StrategyAlignment.SUPERSEDED
    )
    assert verdict.composite_label == "Acceptable loss"
    assert verdict.include_in_roi_totals is False
    assert verdict.executive_attention_required is False


def test_composite_verdict_failed_aligned():
    """FAILED + ALIGNED → Failure, exclude_from_roi, exec attention."""
    verdict = _build_composite_verdict(
        SolutionVerdict.FAILED, StrategyAlignment.ALIGNED
    )
    assert verdict.composite_label == "Failure"
    assert verdict.include_in_roi_totals is False
    assert verdict.executive_attention_required is True


def test_composite_verdict_failed_drifted():
    """FAILED + DRIFTED → Strategic waste, exclude_from_roi, exec attention."""
    verdict = _build_composite_verdict(
        SolutionVerdict.FAILED, StrategyAlignment.DRIFTED
    )
    assert verdict.composite_label == "Strategic waste"
    assert verdict.include_in_roi_totals is False
    assert verdict.executive_attention_required is True


def test_composite_verdict_failed_superseded():
    """FAILED + SUPERSEDED → Irrelevant failure, exclude_from_roi, no exec attention."""
    verdict = _build_composite_verdict(
        SolutionVerdict.FAILED, StrategyAlignment.SUPERSEDED
    )
    assert verdict.composite_label == "Irrelevant failure"
    assert verdict.include_in_roi_totals is False
    assert verdict.executive_attention_required is False


# ---------------------------------------------------------------------------
# Test: Entrypoint 1 — register_solution
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_solution_happy_path(agent, register_request):
    """Happy path: registers solution and returns MEASURING status with UUID."""
    resp = await agent.register_solution(register_request)

    assert resp.solution_id is not None
    assert len(resp.solution_id) > 0
    assert resp.status == SolutionVerdict.MEASURING
    assert "measurement" in resp.message.lower()


@pytest.mark.asyncio
async def test_register_solution_stored_and_retrievable(agent, register_request):
    """Registered solution is stored and retrievable from internal store."""
    resp = await agent.register_solution(register_request)
    solution_id = resp.solution_id

    # Verify it's in the store
    assert solution_id in agent._solutions_store
    stored = agent._solutions_store[solution_id]
    assert stored.kpi_id == register_request.kpi_id
    assert stored.principal_id == register_request.principal_id
    assert stored.status == SolutionVerdict.MEASURING


@pytest.mark.asyncio
async def test_register_solution_auto_snapshot_when_none_provided(agent, register_request):
    """When no strategy_snapshot supplied, agent builds a minimal default."""
    # Remove snapshot
    register_request.strategy_snapshot = None

    resp = await agent.register_solution(register_request)
    stored = agent._solutions_store[resp.solution_id]

    # Verify snapshot was auto-built
    assert stored.strategy_snapshot is not None
    assert stored.strategy_snapshot.data_product_id is not None
    assert stored.strategy_snapshot.kpi_threshold_at_approval is not None


@pytest.mark.asyncio
async def test_register_solution_preserves_input_fields(agent, register_request):
    """All input fields are preserved in the AcceptedSolution record."""
    resp = await agent.register_solution(register_request)
    stored = agent._solutions_store[resp.solution_id]

    assert stored.situation_id == register_request.situation_id
    assert stored.solution_description == register_request.solution_description
    assert stored.expected_impact_lower == register_request.expected_impact_lower
    assert stored.expected_impact_upper == register_request.expected_impact_upper
    assert stored.benchmark_segments == register_request.benchmark_segments
    assert stored.ma_market_signals == register_request.ma_market_signals


# ---------------------------------------------------------------------------
# Test: Entrypoint 2 — evaluate_solution_impact (DiD Attribution)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_solution_validated_verdict(agent, register_request):
    """
    VALIDATED verdict when:
      current_kpi > baseline AND attributable >= expected_lower AND attributable > 0
    """
    # Register first
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    # Evaluate: baseline=45, current=49 (total +4)
    # No control/market → attributable = 4.0
    # expected_lower=2.0 → 4.0 >= 2.0 → VALIDATED
    eval_req = EvaluateSolutionRequest(
        request_id="eval-001",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=49.0,
    )
    resp = await agent.evaluate_solution_impact(eval_req)

    assert resp.evaluation.verdict == SolutionVerdict.VALIDATED
    assert resp.evaluation.attributable_impact == 4.0
    assert resp.evaluation.confidence == ConfidenceLevel.LOW  # No control/market


@pytest.mark.asyncio
async def test_evaluate_solution_partial_verdict(agent, register_request):
    """
    PARTIAL verdict when:
      attributable > 0 but < expected_lower
    """
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    # Baseline=45, current=46 (total +1), expected_lower=2.0
    # 1.0 > 0 but < 2.0 → PARTIAL
    eval_req = EvaluateSolutionRequest(
        request_id="eval-002",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=46.0,
    )
    resp = await agent.evaluate_solution_impact(eval_req)

    assert resp.evaluation.verdict == SolutionVerdict.PARTIAL
    assert resp.evaluation.attributable_impact == 1.0


@pytest.mark.asyncio
async def test_evaluate_solution_failed_verdict(agent, register_request):
    """
    FAILED verdict when:
      attributable <= 0
    """
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    # Baseline=45, current=43 (total -2) → attributable <= 0 → FAILED
    eval_req = EvaluateSolutionRequest(
        request_id="eval-003",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=43.0,
    )
    resp = await agent.evaluate_solution_impact(eval_req)

    assert resp.evaluation.verdict == SolutionVerdict.FAILED
    assert resp.evaluation.attributable_impact == -2.0


@pytest.mark.asyncio
async def test_evaluate_solution_control_group_adjustment(agent, register_request):
    """
    DiD with control group: attributable = total_change - control_change - market - seasonal
    """
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    # Baseline=45, current=50 (total +5)
    # Control group mean = 1.0
    # attributable = 5.0 - 1.0 = 4.0 → VALIDATED (>= expected_lower=2.0)
    eval_req = EvaluateSolutionRequest(
        request_id="eval-004",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=50.0,
        control_group_kpi_values=[0.5, 1.0, 1.5],
    )
    resp = await agent.evaluate_solution_impact(eval_req)

    assert resp.evaluation.control_group_change == 1.0
    assert resp.evaluation.attributable_impact == 4.0
    assert resp.evaluation.verdict == SolutionVerdict.VALIDATED


@pytest.mark.asyncio
async def test_evaluate_solution_market_recovery_adjustment(agent, register_request):
    """
    DiD with market recovery estimate deducted from attributable impact.
    """
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    # Baseline=45, current=50 (total +5)
    # Market recovery = 2.0
    # attributable = 5.0 - 2.0 = 3.0 → VALIDATED (>= expected_lower=2.0)
    eval_req = EvaluateSolutionRequest(
        request_id="eval-005",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=50.0,
        market_recovery_estimate=2.0,
    )
    resp = await agent.evaluate_solution_impact(eval_req)

    assert resp.evaluation.market_driven_recovery == 2.0
    assert resp.evaluation.attributable_impact == 3.0


@pytest.mark.asyncio
async def test_evaluate_solution_confidence_high(agent, register_request):
    """
    Confidence=HIGH when all 3 signals provided:
      control group + market recovery + seasonal
    """
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    eval_req = EvaluateSolutionRequest(
        request_id="eval-006",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=50.0,
        control_group_kpi_values=[0.5, 1.0],
        market_recovery_estimate=1.0,
        seasonal_estimate=0.5,
    )
    resp = await agent.evaluate_solution_impact(eval_req)

    assert resp.evaluation.confidence == ConfidenceLevel.HIGH
    assert "Control group, market recovery, and seasonal" in resp.evaluation.confidence_rationale


@pytest.mark.asyncio
async def test_evaluate_solution_confidence_moderate(agent, register_request):
    """
    Confidence=MODERATE when 1–2 signals provided.
    """
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    eval_req = EvaluateSolutionRequest(
        request_id="eval-007",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=50.0,
        control_group_kpi_values=[0.5, 1.0],
    )
    resp = await agent.evaluate_solution_impact(eval_req)

    assert resp.evaluation.confidence == ConfidenceLevel.MODERATE
    assert "1/3" in resp.evaluation.confidence_rationale or "some confounders" in resp.evaluation.confidence_rationale.lower()


@pytest.mark.asyncio
async def test_evaluate_solution_confidence_low_no_controls(agent, register_request):
    """
    Confidence=LOW when no control, market, or seasonal data.
    """
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    eval_req = EvaluateSolutionRequest(
        request_id="eval-008",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=50.0,
    )
    resp = await agent.evaluate_solution_impact(eval_req)

    assert resp.evaluation.confidence == ConfidenceLevel.LOW
    assert "No control group" in resp.evaluation.confidence_rationale


@pytest.mark.asyncio
async def test_evaluate_solution_updates_status(agent, register_request):
    """Solution status is updated to the evaluated verdict."""
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    # Start as MEASURING
    assert agent._solutions_store[solution_id].status == SolutionVerdict.MEASURING

    # Evaluate
    eval_req = EvaluateSolutionRequest(
        request_id="eval-009",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=49.0,
    )
    await agent.evaluate_solution_impact(eval_req)

    # Now VALIDATED
    assert agent._solutions_store[solution_id].status == SolutionVerdict.VALIDATED


@pytest.mark.asyncio
async def test_evaluate_solution_nonexistent_raises(agent):
    """Evaluating a non-existent solution raises ValueError."""
    eval_req = EvaluateSolutionRequest(
        request_id="eval-bad",
        principal_id="cfo_001",
        solution_id="nonexistent-id",
        current_kpi_value=50.0,
    )
    with pytest.raises(ValueError, match="not found"):
        await agent.evaluate_solution_impact(eval_req)


# ---------------------------------------------------------------------------
# Test: Entrypoint 3 — check_strategy_alignment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_check_strategy_alignment_aligned_default(agent, register_request):
    """When no drift factors, verdict is ALIGNED."""
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    align_req = CheckStrategyAlignmentRequest(
        request_id="align-001",
        principal_id="cfo_001",
        solution_id=solution_id,
    )
    resp = await agent.check_strategy_alignment(align_req)

    # No PC Agent or Registry available in bare test → fallback to ALIGNED
    assert resp.alignment.alignment_verdict == StrategyAlignment.ALIGNED
    assert resp.alignment.priority_drift is False


@pytest.mark.asyncio
async def test_check_strategy_alignment_nonexistent_raises(agent):
    """Checking alignment for non-existent solution raises ValueError."""
    align_req = CheckStrategyAlignmentRequest(
        request_id="align-bad",
        principal_id="cfo_001",
        solution_id="nonexistent-id",
    )
    with pytest.raises(ValueError, match="not found"):
        await agent.check_strategy_alignment(align_req)


@pytest.mark.asyncio
async def test_check_strategy_alignment_priority_overlap_full_match(agent, register_request):
    """Priority overlap is calculated correctly when priorities match."""
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    # Without PC Agent, current_priorities defaults to original_priorities
    # so overlap should be 1.0 and priority_drift should be False.
    align_req = CheckStrategyAlignmentRequest(
        request_id="align-002",
        principal_id="cfo_001",
        solution_id=solution_id,
    )
    resp = await agent.check_strategy_alignment(align_req)

    # When priorities match exactly, overlap = 1.0 → no drift
    assert resp.alignment.priority_overlap == 1.0
    assert resp.alignment.priority_drift is False
    assert resp.alignment.alignment_verdict == StrategyAlignment.ALIGNED


# ---------------------------------------------------------------------------
# Test: Entrypoint 4 — project_inaction_cost
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_project_inaction_cost_stable_trend(agent):
    """Flat historical trend → slope ≈ 0 → trend_direction="stable"."""
    proj_req = ProjectInactionCostRequest(
        request_id="proj-001",
        principal_id="cfo_001",
        situation_id="sit-001",
        kpi_id="lub_gross_margin_pct",
        current_kpi_value=45.0,
        historical_trend=[45.0, 45.2, 44.8, 45.1, 45.0],
    )
    resp = await agent.project_inaction_cost(proj_req)

    assert resp.projection.trend_direction == "stable"
    assert resp.projection.current_kpi_value == 45.0


@pytest.mark.asyncio
async def test_project_inaction_cost_deteriorating_trend(agent):
    """Declining historical trend → negative slope → trend_direction="deteriorating"."""
    proj_req = ProjectInactionCostRequest(
        request_id="proj-002",
        principal_id="cfo_001",
        situation_id="sit-001",
        kpi_id="lub_gross_margin_pct",
        current_kpi_value=45.0,
        historical_trend=[50.0, 48.0, 46.0, 45.0],
    )
    resp = await agent.project_inaction_cost(proj_req)

    assert resp.projection.trend_direction == "deteriorating"
    assert resp.projection.projected_kpi_value_30d < resp.projection.current_kpi_value


@pytest.mark.asyncio
async def test_project_inaction_cost_single_observation(agent):
    """Single data point → no trend → slope=0 → stable, LOW confidence."""
    proj_req = ProjectInactionCostRequest(
        request_id="proj-003",
        principal_id="cfo_001",
        situation_id="sit-001",
        kpi_id="lub_gross_margin_pct",
        current_kpi_value=45.0,
        historical_trend=[45.0],
    )
    resp = await agent.project_inaction_cost(proj_req)

    assert resp.projection.trend_direction == "stable"
    assert resp.projection.trend_confidence == ConfidenceLevel.LOW
    assert "No trend data" in resp.projection.projection_method


@pytest.mark.asyncio
async def test_project_inaction_cost_empty_trend_raises(agent):
    """Empty trend list raises ValueError."""
    proj_req = ProjectInactionCostRequest(
        request_id="proj-bad",
        principal_id="cfo_001",
        situation_id="sit-001",
        kpi_id="lub_gross_margin_pct",
        current_kpi_value=45.0,
        historical_trend=[],
    )
    with pytest.raises(ValueError, match="at least one"):
        await agent.project_inaction_cost(proj_req)


# ---------------------------------------------------------------------------
# Test: Entrypoint 5 — get_portfolio_summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_portfolio_summary_empty_store(agent):
    """Empty solution store returns zeros."""
    summary_req = PortfolioSummaryRequest(
        request_id="port-001",
        principal_id="cfo_001",
        include_superseded=False,
    )
    resp = await agent.get_portfolio_summary(summary_req)

    assert resp.total_solutions == 0
    assert resp.validated_count == 0
    assert resp.partial_count == 0
    assert resp.failed_count == 0
    assert resp.measuring_count == 0
    assert resp.total_attributable_impact == 0.0


@pytest.mark.asyncio
async def test_get_portfolio_summary_counts_solutions(agent, register_request):
    """Portfolio counts solutions correctly after registrations."""
    # Register 2 solutions
    resp1 = await agent.register_solution(register_request)

    register_request.kpi_id = "lub_revenue"
    resp2 = await agent.register_solution(register_request)

    summary_req = PortfolioSummaryRequest(
        request_id="port-002",
        principal_id="cfo_001",
        include_superseded=False,
    )
    resp = await agent.get_portfolio_summary(summary_req)

    assert resp.total_solutions == 2
    assert resp.measuring_count == 2  # Both still in MEASURING


@pytest.mark.asyncio
async def test_get_portfolio_summary_aggregates_roi(agent, register_request):
    """Portfolio aggregates attributable impact only for ROI-eligible solutions."""
    # Register and evaluate first solution as VALIDATED + ALIGNED
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    eval_req = EvaluateSolutionRequest(
        request_id="eval-101",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=49.0,  # +4 attributable → VALIDATED
    )
    await agent.evaluate_solution_impact(eval_req)

    summary_req = PortfolioSummaryRequest(
        request_id="port-003",
        principal_id="cfo_001",
        include_superseded=False,
    )
    resp = await agent.get_portfolio_summary(summary_req)

    # One VALIDATED solution → validated_count=1, total_attributable=4.0
    assert resp.validated_count == 1
    assert resp.total_attributable_impact == 4.0
    assert resp.roi_eligible_solutions == 1


@pytest.mark.asyncio
async def test_get_portfolio_summary_executive_attention_flag(agent, register_request):
    """Portfolio flags solutions requiring executive attention."""
    # Register and evaluate as FAILED + ALIGNED (requires attention)
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    eval_req = EvaluateSolutionRequest(
        request_id="eval-102",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=43.0,  # -2 attributable → FAILED
    )
    await agent.evaluate_solution_impact(eval_req)

    summary_req = PortfolioSummaryRequest(
        request_id="port-004",
        principal_id="cfo_001",
        include_superseded=False,
    )
    resp = await agent.get_portfolio_summary(summary_req)

    # FAILED + ALIGNED → composite requires exec attention
    assert len(resp.executive_attention_required) == 1
    assert resp.executive_attention_required[0] == solution_id


# ---------------------------------------------------------------------------
# Test: Entrypoint 6 — generate_narrative
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_narrative_llm_unavailable_fallback(agent, register_request):
    """When LLM unavailable, graceful fallback to static message."""
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    # No LLM service injected → fallback path
    assert agent._llm_service is None

    narr_req = GenerateNarrativeRequest(
        request_id="narr-001",
        principal_id="cfo_001",
        solution_id=solution_id,
    )
    resp = await agent.generate_narrative(narr_req)

    # Should return fallback message
    assert "unavailable" in resp.narrative.lower() or "LLM" in resp.narrative


@pytest.mark.asyncio
async def test_generate_narrative_with_llm_mock(agent, register_request):
    """When LLM is available, narrative is generated and persisted."""
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    # Mock LLM service
    mock_llm = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.analysis = {"content": "Executive summary of the solution outcome."}
    mock_llm.analyze = AsyncMock(return_value=mock_resp)
    agent._llm_service = mock_llm

    narr_req = GenerateNarrativeRequest(
        request_id="narr-002",
        principal_id="cfo_001",
        solution_id=solution_id,
    )
    resp = await agent.generate_narrative(narr_req)

    # Narrative should be from LLM
    assert "Executive summary" in resp.narrative

    # Verify it was persisted
    updated_solution = agent._solutions_store[solution_id]
    assert updated_solution.narrative == resp.narrative


@pytest.mark.asyncio
async def test_generate_narrative_nonexistent_raises(agent):
    """Generating narrative for non-existent solution raises ValueError."""
    narr_req = GenerateNarrativeRequest(
        request_id="narr-bad",
        principal_id="cfo_001",
        solution_id="nonexistent-id",
    )
    with pytest.raises(ValueError, match="not found"):
        await agent.generate_narrative(narr_req)


@pytest.mark.asyncio
async def test_generate_narrative_with_evaluated_solution(agent, register_request):
    """Narrative generation includes evaluation details when available."""
    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    # Evaluate first
    eval_req = EvaluateSolutionRequest(
        request_id="eval-103",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=49.0,
    )
    await agent.evaluate_solution_impact(eval_req)

    # Mock LLM and capture the prompt
    mock_llm = AsyncMock()
    captured_prompt = None

    async def capture_analyze(req):
        nonlocal captured_prompt
        captured_prompt = req.content
        resp = MagicMock()
        resp.analysis = {"content": "Generated narrative."}
        return resp

    mock_llm.analyze = AsyncMock(side_effect=capture_analyze)
    agent._llm_service = mock_llm

    narr_req = GenerateNarrativeRequest(
        request_id="narr-003",
        principal_id="cfo_001",
        solution_id=solution_id,
    )
    await agent.generate_narrative(narr_req)

    # Verify evaluation details in prompt
    assert captured_prompt is not None
    assert "VALIDATED" in captured_prompt


# ---------------------------------------------------------------------------
# Test: Lifecycle methods
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agent_create_from_registry():
    """Agent can be created via create_from_registry classmethod."""
    config = A9ValueAssuranceAgentConfig()
    agent = await A9_Value_Assurance_Agent.create_from_registry(config.model_dump())

    assert agent.name == "A9_Value_Assurance_Agent"
    assert agent.version == "1.0.0"
    assert agent._solutions_store == {}


@pytest.mark.asyncio
async def test_agent_disconnect():
    """Disconnect method completes without error."""
    config = A9ValueAssuranceAgentConfig()
    agent = await A9_Value_Assurance_Agent.create_from_registry(config.model_dump())

    await agent.disconnect()  # Should not raise


# ---------------------------------------------------------------------------
# Test: Edge cases and error conditions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_evaluate_solution_with_zero_baseline(agent, register_request, strategy_snapshot):
    """Evaluation handles zero baseline gracefully."""
    # Set baseline to 0
    strategy_snapshot.kpi_threshold_at_approval = 0.0
    register_request.strategy_snapshot = strategy_snapshot

    reg_resp = await agent.register_solution(register_request)
    solution_id = reg_resp.solution_id

    eval_req = EvaluateSolutionRequest(
        request_id="eval-edge-1",
        principal_id="cfo_001",
        solution_id=solution_id,
        current_kpi_value=5.0,
    )
    resp = await agent.evaluate_solution_impact(eval_req)

    # Should handle without division error
    assert resp.evaluation.total_kpi_change == 5.0


@pytest.mark.asyncio
async def test_project_inaction_cost_with_zero_current_value(agent):
    """Projection handles zero current_kpi_value gracefully."""
    proj_req = ProjectInactionCostRequest(
        request_id="proj-edge-1",
        principal_id="cfo_001",
        situation_id="sit-001",
        kpi_id="lub_gross_margin_pct",
        current_kpi_value=0.0,
        historical_trend=[1.0, 0.5, 0.0],
    )
    resp = await agent.project_inaction_cost(proj_req)

    # Should not raise; revenue impact will be None or 0
    assert resp.projection.current_kpi_value == 0.0
