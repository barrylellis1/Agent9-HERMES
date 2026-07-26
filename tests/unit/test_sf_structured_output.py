# arch-allow-direct-agent-construction
"""
Phase 15 Stage A/B — schema-validation compliance tests (mocked; no live API calls).

Per the Phase 15 M2/M5 compliance gate: schema-shape and validation-rule
correctness are verified here with fixtures. The 20+ live-API synthetic-run
compliance check and the Sonnet-vs-current-prompt quality A/B are a SEPARATE,
manually-triggered step (see DEVELOPMENT_PLAN.md Phase 15) — never run live
Claude calls from this file.

Covers:
- SolutionAssumption / DecisionAsk / ImmediateAction / ImpactEstimate construction
  and validation (word-count + hedge-word rejection on DecisionAsk)
- StrategySnapshot legacy plain-string -> SolutionAssumption coercion
- SFSynthesisSchema tool-schema generation
- ClaudeService.generate_structured() forced tool-use plumbing (mocked Anthropic client)
- A9_LLM_Service_Agent.generate() routes to generate_structured when response_schema is set
- SF agent's defensive per-option parsing helpers (malformed/partial LLM output)
"""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from src.agents.models.solution_finder_models import (
    SolutionAssumption,
    DecisionAsk,
    ImmediateAction,
    ImpactEstimate,
    RecoveryRange,
    SFSynthesisSchema,
    SolutionOption,
)
from src.agents.models.value_assurance_models import StrategySnapshot
from src.agents.new.a9_solution_finder_agent import (
    _parse_key_assumptions,
    _parse_impact_estimate,
    _parse_decision_ask,
    _parse_immediate_actions,
)
from src.agents.new.a9_llm_service_agent import (
    A9_LLM_Service_Agent,
    A9_LLM_Request,
    A9_LLM_AnalysisRequest,
)
from src.agents.agent_config_models import A9_LLM_Service_Agent_Config


# ---------------------------------------------------------------------------
# SolutionAssumption
# ---------------------------------------------------------------------------

def test_solution_assumption_valid_construction():
    a = SolutionAssumption(assumption="Base oil price holds", validated_by="ma_query", confidence="moderate")
    assert a.grounded is False  # default
    assert a.confidence == "moderate"


def test_solution_assumption_rejects_missing_validated_by():
    with pytest.raises(ValidationError):
        SolutionAssumption(assumption="x")  # validated_by is required, no default


def test_solution_assumption_rejects_invalid_validated_by_enum():
    with pytest.raises(ValidationError):
        SolutionAssumption(assumption="x", validated_by="just_trust_me")


# ---------------------------------------------------------------------------
# DecisionAsk — Phase 13 M2 (word count + hedge words)
# ---------------------------------------------------------------------------

def test_decision_ask_valid():
    d = DecisionAsk(decision_text="Approve the Q3 pricing realignment for the DIY channel")
    assert d.decision_text


def test_decision_ask_rejects_over_25_words():
    with pytest.raises(ValidationError):
        DecisionAsk(decision_text=" ".join(["word"] * 26))


def test_decision_ask_accepts_exactly_25_words():
    DecisionAsk(decision_text=" ".join(["word"] * 25))  # should not raise


@pytest.mark.parametrize("hedge_phrase", ["might", "potentially", "could possibly", "may want to", "consider"])
def test_decision_ask_rejects_hedge_words(hedge_phrase):
    with pytest.raises(ValidationError):
        DecisionAsk(decision_text=f"You {hedge_phrase} raise prices in Q3")


# ---------------------------------------------------------------------------
# ImmediateAction / ImpactEstimate
# ---------------------------------------------------------------------------

def test_immediate_action_construction():
    a = ImmediateAction(action_text="Commission cost-to-serve analysis", owner="CFO", due_by_days=7)
    assert a.due_by_days == 7


def test_impact_estimate_typed_recovery_range():
    ie = ImpactEstimate(metric="Gross Margin", unit="%", recovery_range=RecoveryRange(low=1.2, high=2.8), basis="...")
    assert ie.recovery_range.low == 1.2
    dumped = ie.model_dump()
    # Must serialize to the same nested shape workflows.py already reads
    assert dumped["recovery_range"] == {"low": 1.2, "high": 2.8}


# ---------------------------------------------------------------------------
# StrategySnapshot legacy coercion (Phase 11J P1 requirement, absorbed into Phase 15 Stage B)
# ---------------------------------------------------------------------------

def _snapshot(key_assumptions):
    return StrategySnapshot(
        principal_priorities=["Gross Margin"],
        principal_role="CFO",
        business_process_domain="Finance",
        data_product_id="fi",
        kpi_threshold_at_approval=45.0,
        key_assumptions=key_assumptions,
        business_context_name="ctx",
        captured_at=datetime.utcnow().isoformat(),
    )


def test_strategy_snapshot_coerces_legacy_plain_strings():
    snap = _snapshot(["Control group is comparable cohort"])
    assert isinstance(snap.key_assumptions[0], SolutionAssumption)
    assert snap.key_assumptions[0].assumption == "Control group is comparable cohort"
    assert snap.key_assumptions[0].validated_by == "human_confirmation"


def test_strategy_snapshot_accepts_typed_dicts():
    snap = _snapshot([{"assumption": "Base oil holds", "validated_by": "sa_assessment"}])
    assert snap.key_assumptions[0].validated_by == "sa_assessment"


def test_strategy_snapshot_accepts_mixed_legacy_and_typed():
    snap = _snapshot(["legacy string", {"assumption": "typed", "validated_by": "ma_query"}])
    assert snap.key_assumptions[0].validated_by == "human_confirmation"
    assert snap.key_assumptions[1].validated_by == "ma_query"


# ---------------------------------------------------------------------------
# SF agent defensive parsing helpers (malformed/partial LLM output)
# ---------------------------------------------------------------------------

def test_parse_key_assumptions_handles_dicts_and_strings():
    result = _parse_key_assumptions([
        {"assumption": "a", "validated_by": "sa_assessment"},
        "plain string bet",
    ])
    assert len(result) == 2
    assert result[0].validated_by == "sa_assessment"
    assert result[1].validated_by == "human_confirmation"


def test_parse_key_assumptions_skips_malformed_entries():
    result = _parse_key_assumptions([{"assumption": "ok", "validated_by": "sa_assessment"}, 12345, None, ""])
    assert len(result) == 1


def test_parse_key_assumptions_handles_non_list_input():
    assert _parse_key_assumptions(None) == []
    assert _parse_key_assumptions("not a list") == []


def test_parse_impact_estimate_valid():
    ie = _parse_impact_estimate({"metric": "Gross Margin", "unit": "%", "recovery_range": {"low": 1.0, "high": 2.0}, "basis": "..."})
    assert ie.recovery_range.low == 1.0


def test_parse_impact_estimate_handles_missing_recovery_range():
    ie = _parse_impact_estimate({"metric": "Gross Margin"})
    assert ie.recovery_range is None


def test_parse_impact_estimate_handles_non_dict():
    assert _parse_impact_estimate(None) is None
    assert _parse_impact_estimate("garbage") is None


def test_parse_decision_ask_drops_invalid_without_raising():
    # Hedge word -> fails DecisionAsk validation -> parser must swallow, not raise
    assert _parse_decision_ask({"decision_text": "You might consider this"}) is None


def test_parse_decision_ask_valid():
    d = _parse_decision_ask({"decision_text": "Approve the pricing change for Q3"})
    assert d is not None


def test_parse_immediate_actions_skips_malformed():
    result = _parse_immediate_actions([{"action_text": "Do the thing"}, "not a dict", 42])
    assert len(result) == 1


# ---------------------------------------------------------------------------
# SFSynthesisSchema — tool-schema generation (Phase 15 Stage A)
# ---------------------------------------------------------------------------

def test_sf_synthesis_schema_generates_valid_json_schema():
    schema = SFSynthesisSchema.model_json_schema()
    assert "properties" in schema
    for key in ("problem_reframe", "options", "recommendation", "recommendation_rationale", "cross_review"):
        assert key in schema["properties"], f"missing {key} in generated schema"


def test_solution_option_round_trips_through_synthesis_schema():
    # A full option dict (as the LLM would emit it) validates against SolutionOption
    # standalone, confirming the schema-guaranteed shape matches the manual parser's
    # expectations.
    opt = SolutionOption(
        id="opt_1",
        title="Renegotiate supplier contracts",
        expected_impact=0.6,
        cost=0.4,
        risk=0.3,
        impact_estimate={"metric": "Gross Margin", "unit": "%", "recovery_range": {"low": 1.2, "high": 2.8}, "basis": "..."},
        key_assumptions=[{"assumption": "Supplier will renegotiate", "validated_by": "human_confirmation"}],
    )
    assert isinstance(opt.impact_estimate, ImpactEstimate)
    assert isinstance(opt.key_assumptions[0], SolutionAssumption)


# ---------------------------------------------------------------------------
# ClaudeService.generate_structured() — forced tool-use plumbing (mocked client)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_structured_extracts_tool_input(monkeypatch):
    from src.llm_services.claude_service import ClaudeService, ClaudeServiceConfig

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-not-real")
    service = ClaudeService(ClaudeServiceConfig(model_name="claude-sonnet-5"))

    tool_use_block = SimpleNamespace(type="tool_use", input={"options": [], "recommendation_rationale": "x"})
    fake_message = SimpleNamespace(
        stop_reason="tool_use",
        content=[tool_use_block],
        model="claude-sonnet-5",
        usage=SimpleNamespace(input_tokens=100, output_tokens=50),
    )
    service.client = MagicMock()
    service.client.messages.create = MagicMock(return_value=fake_message)

    result = await service.generate_structured(
        prompt="synthesize", tool_schema={"type": "object"}, tool_name="emit_sf_synthesis"
    )

    assert result["error"] is None if "error" in result and result["error"] is not None else True
    assert "response" in result
    import json as _json
    parsed = _json.loads(result["response"])
    assert parsed["recommendation_rationale"] == "x"
    assert result["usage"]["total_tokens"] == 150

    # tool_choice must force the exact tool (this is the actual guarantee mechanism)
    call_kwargs = service.client.messages.create.call_args.kwargs
    assert call_kwargs["tool_choice"] == {"type": "tool", "name": "emit_sf_synthesis"}
    assert call_kwargs["tools"][0]["name"] == "emit_sf_synthesis"


@pytest.mark.asyncio
async def test_generate_structured_handles_refusal(monkeypatch):
    from src.llm_services.claude_service import ClaudeService, ClaudeServiceConfig

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-not-real")
    service = ClaudeService(ClaudeServiceConfig(model_name="claude-sonnet-5"))

    fake_message = SimpleNamespace(
        stop_reason="refusal",
        stop_details=SimpleNamespace(category="policy"),
        content=[],
        model="claude-sonnet-5",
    )
    service.client = MagicMock()
    service.client.messages.create = MagicMock(return_value=fake_message)

    result = await service.generate_structured(prompt="x", tool_schema={"type": "object"})
    assert result["response"] is None
    assert "refusal" in result["error"]


@pytest.mark.asyncio
async def test_generate_structured_handles_missing_tool_use_block(monkeypatch):
    from src.llm_services.claude_service import ClaudeService, ClaudeServiceConfig

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-fake-not-real")
    service = ClaudeService(ClaudeServiceConfig(model_name="claude-sonnet-5"))

    fake_message = SimpleNamespace(
        stop_reason="end_turn",
        content=[SimpleNamespace(type="text", text="oops, no tool call")],
        model="claude-sonnet-5",
    )
    service.client = MagicMock()
    service.client.messages.create = MagicMock(return_value=fake_message)

    result = await service.generate_structured(prompt="x", tool_schema={"type": "object"})
    assert result["response"] is None
    assert "no tool_use block" in result["error"]


# ---------------------------------------------------------------------------
# A9_LLM_Service_Agent.generate() routing — response_schema present -> structured path
# ---------------------------------------------------------------------------

def _bare_llm_agent() -> A9_LLM_Service_Agent:
    """Construct an agent instance bypassing __init__ (no API key / guardrails
    loading needed) — isolates the routing branch added in Phase 15 Stage A."""
    agent = object.__new__(A9_LLM_Service_Agent)
    agent.config = A9_LLM_Service_Agent_Config(
        provider="anthropic", log_all_requests=False, system_prompt_override="test system prompt"
    )
    agent.llm_service = MagicMock()
    agent.llm_service.generate = AsyncMock(return_value={"response": "free text", "usage": {}})
    agent.llm_service.generate_structured = AsyncMock(return_value={"response": "{}", "usage": {}})
    return agent


@pytest.mark.asyncio
async def test_generate_routes_to_structured_when_schema_present():
    agent = _bare_llm_agent()
    request = A9_LLM_Request(request_id="r1", principal_id="p1", prompt="synthesize", response_schema={"type": "object"}, tool_name="emit_x")

    resp = await agent.generate(request)

    agent.llm_service.generate_structured.assert_awaited_once()
    agent.llm_service.generate.assert_not_awaited()
    assert resp.status == "success"


@pytest.mark.asyncio
async def test_generate_uses_free_text_path_when_no_schema():
    agent = _bare_llm_agent()
    request = A9_LLM_Request(request_id="r2", principal_id="p1", prompt="hello")

    resp = await agent.generate(request)

    agent.llm_service.generate.assert_awaited_once()
    agent.llm_service.generate_structured.assert_not_awaited()
    assert resp.status == "success"


@pytest.mark.asyncio
async def test_analyze_threads_response_schema_into_generate():
    agent = _bare_llm_agent()
    request = A9_LLM_AnalysisRequest(
        request_id="r3", principal_id="p1", content="data", analysis_type="custom",
        response_schema={"type": "object"}, tool_name="emit_y",
    )
    agent.llm_service.generate_structured = AsyncMock(
        return_value={"response": '{"foo": "bar"}', "usage": {}}
    )

    resp = await agent.analyze(request)

    agent.llm_service.generate_structured.assert_awaited_once()
    call_kwargs = agent.llm_service.generate_structured.call_args.kwargs
    assert call_kwargs["tool_schema"] == {"type": "object"}
    assert call_kwargs["tool_name"] == "emit_y"
    assert resp.analysis == {"foo": "bar"}
