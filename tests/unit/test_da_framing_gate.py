# arch-allow-direct-agent-construction
"""
Phase 19, Slice 4 — the mandatory framing gate, wired into the interview
(2026-08-18).

Covers `_get_topic_sequence`'s FRAMING_TOPIC insertion and `_handle_framing_gate`
— the single entry point `refine_analysis` calls BEFORE every other branch
(early-exit, skip-command, max-turns, all-complete). That placement IS the
server-side bypass guard: these tests prove early-exit/skip/proceed commands
are silently ignored while framing is pending, not that three separate
methods each independently learned to reject them.

Same construction pattern as test_da_refinement_topic_routing.py (which this
file directly extends): `A9_Deep_Analysis_Agent(config)` via the real
constructor — no orchestrator/DPA/LLM wiring needed for these methods, and
`self.llm_service_agent` stays None, which `_generate_refinement_question`
already degrades gracefully from (`default_questions.get(...)`).
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.new.a9_deep_analysis_agent import (
    FRAMING_TOPIC,
    MAX_TOPICS_IN_SEQUENCE,
    PROTECTED_TOPICS,
    A9_Deep_Analysis_Agent,
)
from src.agents.models.deep_analysis_models import (
    ProblemRefinementInput,
    FramingPrompt,
    FramingAlternative,
    FramingDecision,
)
from src.registry.models.assumption import Assumption


def _agent(enable_framing_gate: bool = True) -> A9_Deep_Analysis_Agent:
    return A9_Deep_Analysis_Agent({"enable_framing_gate": enable_framing_gate})


def _da(
    *,
    change_points=None,
    where_is_not=None,
    analysis_mode="problem",
    compound_alert=False,
    market_conflict=False,
    benchmarks=None,
    kpi_name="gross_margin_pct",
    client_id="hess",
):
    """Same shape test_da_refinement_topic_routing.py's `_da()` builds."""
    execution = {
        "analysis_mode": analysis_mode,
        "change_points": change_points if change_points is not None else [],
        "kt_is_is_not": {
            "where_is_not": where_is_not if where_is_not is not None else [],
            "benchmark_segments": benchmarks or [],
        },
        "compound_alert": compound_alert,
        "market_conflict": market_conflict,
    }
    return {"plan": {"kpi_name": kpi_name, "client_id": client_id}, "execution": execution}


_CONCENTRATED = [{"delta": -43.24}, {"delta": -16.76}]
_DISTRIBUTED = [{"delta": -7.14}, {"delta": -6.61}, {"delta": -5.86}]
_CONTROL_GROUP = [{"key": "Chain B", "delta": 1.2}]


def _canned_prompt(alt_kpi_id="cogs"):
    return FramingPrompt(
        kpi_id="gross_margin_pct", kpi_name="Gross Margin %",
        stated_objective_text="Recovering Gross Margin %",
        question="Is recovering Gross Margin % the right objective?",
        alternatives=[FramingAlternative(source="causal_graph", kpi_id=alt_kpi_id, objective_text="x", hops=1)],
    )


def _decision(**overrides):
    base = dict(
        choice="confirm_stated", chosen_objective_text="Recovering Gross Margin %",
        falsification_criterion="If margin does not recover within 2 quarters, this was wrong.",
    )
    base.update(overrides)
    return FramingDecision(**base)


def _refinement_input(da_output, *, framing_decision=None, user_message=None,
                       topics_completed=None, turn_count=0, current_topic=None):
    return ProblemRefinementInput(
        deep_analysis_output=da_output,
        principal_context={"role": "CFO", "principal_id": "cfo_001", "decision_style": "analytical"},
        conversation_history=[],
        user_message=user_message,
        current_topic=current_topic,
        turn_count=turn_count,
        topics_completed=topics_completed or [],
        framing_decision=framing_decision,
    )


# ---------------------------------------------------------------------------
# _get_topic_sequence — FRAMING_TOPIC insertion
# ---------------------------------------------------------------------------

class TestTopicSequenceInsertion:
    def test_framing_at_position_zero_when_flag_on(self):
        agent = _agent(True)
        seq, _, rules = agent._get_topic_sequence(_da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP))
        assert seq[0] == FRAMING_TOPIC
        assert any("PHASE19" in r for r in rules)

    def test_framing_absent_when_flag_off(self):
        agent = _agent(False)
        seq, _, _ = agent._get_topic_sequence(_da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP))
        assert FRAMING_TOPIC not in seq

    def test_framing_present_even_when_classify_fails(self):
        """A profiling failure must not ALSO cost the principal the framing
        gate — both return paths in _get_topic_sequence insert it."""
        agent = _agent(True)
        with patch("src.analysis.problem_profile.classify", side_effect=ValueError("boom")):
            seq, profile, _ = agent._get_topic_sequence(_da())
        assert profile is None
        assert seq[0] == FRAMING_TOPIC

    def test_survives_a_seven_topic_routed_sequence_hitting_the_cap(self):
        """Same fixture as test_da_refinement_topic_routing.py's cap test
        (concentrated + no control group + compound_alert + opportunity +
        benchmarks -> hits MAX_TOPICS_IN_SEQUENCE=6 on its own), with the
        gate on top. Framing must survive the cap AND lead the sequence —
        inserted AFTER the cap runs, so it is never one of the topics
        eligible for trimming."""
        agent = _agent(True)
        seq, _, rules = agent._get_topic_sequence(_da(
            change_points=_CONCENTRATED, where_is_not=[], compound_alert=True,
            analysis_mode="opportunity", benchmarks=[{"benchmark_type": "internal_benchmark", "key": "Chain B"}],
        ))
        assert seq[0] == FRAMING_TOPIC
        assert len(seq) == MAX_TOPICS_IN_SEQUENCE + 1  # cap's 6 + framing, never trimmed itself
        for protected in PROTECTED_TOPICS:
            assert protected in seq, f"{protected} must survive truncation"
        assert any("CAP" in r for r in rules)
        assert any("PHASE19" in r for r in rules)


# ---------------------------------------------------------------------------
# refine_analysis / _handle_framing_gate — presentation turn
# ---------------------------------------------------------------------------

class TestPresentationTurn:
    @pytest.mark.asyncio
    async def test_presents_framing_prompt_on_first_turn(self, monkeypatch):
        agent = _agent(True)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=_canned_prompt()))
        result = await agent.refine_analysis(_refinement_input(_da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP)))
        assert result.framing_required is True
        assert result.framing_prompt is not None
        assert result.ready_for_solutions is False
        assert result.topics_completed == []

    @pytest.mark.asyncio
    async def test_build_framing_prompt_returning_none_still_blocks(self, monkeypatch):
        """_build_framing_prompt's own None means 'nothing to show' -- NOT
        permission to proceed. Fail closed."""
        agent = _agent(True)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=None))
        result = await agent.refine_analysis(_refinement_input(_da()))
        assert result.framing_required is True
        assert result.framing_prompt is None
        assert result.ready_for_solutions is False
        assert result.suggested_responses == []

    @pytest.mark.asyncio
    async def test_flag_off_never_shows_framing_prompt(self, monkeypatch):
        agent = _agent(False)
        build_mock = AsyncMock(return_value=_canned_prompt())
        monkeypatch.setattr(agent, "_build_framing_prompt", build_mock)
        result = await agent.refine_analysis(_refinement_input(_da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP)))
        assert result.framing_prompt is None
        assert result.framing_required is False
        build_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Server-side bypass guards — the UI gate is not the gate
# ---------------------------------------------------------------------------

class TestBypassGuards:
    @pytest.mark.asyncio
    async def test_proceed_to_solutions_does_not_finalize_during_pending_framing(self, monkeypatch):
        agent = _agent(True)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=_canned_prompt()))
        result = await agent.refine_analysis(_refinement_input(
            _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP),
            user_message="Proceed to solutions",
        ))
        assert result.ready_for_solutions is False
        assert result.framing_required is True
        assert result.framing_prompt is not None

    @pytest.mark.asyncio
    async def test_skip_command_does_not_skip_framing(self, monkeypatch):
        agent = _agent(True)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=_canned_prompt()))
        result = await agent.refine_analysis(_refinement_input(
            _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP),
            user_message="skip this topic",
        ))
        assert FRAMING_TOPIC not in result.topics_completed
        assert result.framing_required is True

    @pytest.mark.asyncio
    async def test_early_exit_does_not_finalize_during_pending_framing(self, monkeypatch):
        agent = _agent(True)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=_canned_prompt()))
        result = await agent.refine_analysis(_refinement_input(
            _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP),
            user_message="I'm done, let's move on",
        ))
        assert result.ready_for_solutions is False
        assert result.framing_required is True

    @pytest.mark.asyncio
    async def test_max_turns_does_not_finalize_during_pending_framing(self, monkeypatch):
        """No turn-budget escape valve for framing -- unlike a normal topic,
        running out the clock must not auto-finalize past it."""
        agent = _agent(True)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=_canned_prompt()))
        result = await agent.refine_analysis(_refinement_input(
            _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP), turn_count=999,
        ))
        assert result.ready_for_solutions is False
        assert result.framing_required is True

    @pytest.mark.asyncio
    async def test_extraction_pipeline_never_invoked_on_a_framing_turn(self, monkeypatch):
        """No user_message exists on a framing turn (present or submit) --
        the extraction pipeline must never be reached, not just usually
        skipped. Rigged to raise if called at all."""
        agent = _agent(True)

        async def _must_not_be_called(*a, **kw):
            raise AssertionError("_extract_refinements_from_response must not be invoked on a framing turn")

        monkeypatch.setattr(agent, "_extract_refinements_from_response", _must_not_be_called)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=_canned_prompt()))
        monkeypatch.setattr(agent, "generate_scqa_for_frame", AsyncMock(return_value="Frame (chosen by CFO): x\n\nSituation..."))

        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
            MockAP.return_value.get_active_framing = AsyncMock(return_value=None)
            MockAP.return_value.upsert = AsyncMock(return_value=Assumption(
                id="a1", client_id="hess", scope="gross_margin_pct", record_type="framing",
                text="x", source="da_hitl",
            ))
            with patch.object(agent, "_lookup_kpi_scoped", return_value=SimpleNamespace(
                id="gross_margin_pct", name="Gross Margin %", owner_role="CFO",
            )):
                # Presentation turn (no user_message ever set here either)
                await agent.refine_analysis(_refinement_input(_da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP)))
                # Submission turn
                await agent.refine_analysis(_refinement_input(
                    _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP),
                    framing_decision=_decision(),
                ))
        # No AssertionError raised -> the pipeline was genuinely never invoked.


# ---------------------------------------------------------------------------
# Submission validation
# ---------------------------------------------------------------------------

class TestSubmissionValidation:
    def test_missing_falsification_criterion_rejected_with_usable_error(self):
        with pytest.raises(Exception) as exc_info:
            ProblemRefinementInput(
                deep_analysis_output=_da(), principal_context={}, conversation_history=[],
                framing_decision={"choice": "confirm_stated", "chosen_objective_text": "x", "falsification_criterion": ""},
            )
        assert "falsification_criterion" in str(exc_info.value)

    def test_alternative_choice_missing_kpi_id_rejected_at_the_model_layer(self):
        with pytest.raises(Exception) as exc_info:
            ProblemRefinementInput(
                deep_analysis_output=_da(), principal_context={}, conversation_history=[],
                framing_decision={"choice": "alternative", "chosen_objective_text": "x", "falsification_criterion": "y"},
            )
        assert "chosen_kpi_id" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unoffered_kpi_id_rejected_and_gate_re_shown(self, monkeypatch):
        """Pydantic guarantees chosen_kpi_id is non-null for 'alternative' --
        it cannot know whether that id was ever actually OFFERED. This is the
        agent-level check: re-derive fresh alternatives, never trust a
        client-echoed offer list."""
        agent = _agent(True)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=_canned_prompt(alt_kpi_id="cogs")))
        result = await agent.refine_analysis(_refinement_input(
            _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP),
            framing_decision=_decision(choice="alternative", chosen_kpi_id="not_actually_offered"),
        ))
        assert result.framing_required is True
        assert result.framing_prompt is not None
        assert FRAMING_TOPIC not in result.topics_completed

    @pytest.mark.asyncio
    async def test_offered_kpi_id_accepted(self, monkeypatch):
        agent = _agent(True)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=_canned_prompt(alt_kpi_id="cogs")))
        monkeypatch.setattr(agent, "generate_scqa_for_frame", AsyncMock(return_value="Frame (chosen by CFO): x\n\nSituation..."))
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP, \
             patch.object(agent, "_lookup_kpi_scoped", return_value=SimpleNamespace(
                 id="gross_margin_pct", name="Gross Margin %", owner_role="CFO",
             )):
            MockAP.return_value.get_active_framing = AsyncMock(return_value=None)
            MockAP.return_value.upsert = AsyncMock(return_value=Assumption(
                id="a1", client_id="hess", scope="gross_margin_pct", record_type="framing",
                text="x", source="da_hitl",
            ))
            result = await agent.refine_analysis(_refinement_input(
                _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP),
                framing_decision=_decision(choice="alternative", chosen_kpi_id="cogs", chosen_objective_text="Addressing cogs"),
            ))
        assert FRAMING_TOPIC in result.topics_completed
        assert result.framing_required is False


# ---------------------------------------------------------------------------
# Valid submission — end to end through _handle_framing_gate
# ---------------------------------------------------------------------------

class TestValidSubmission:
    @pytest.mark.asyncio
    async def test_valid_submission_advances_with_scqa_and_next_question(self, monkeypatch):
        agent = _agent(True)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=_canned_prompt()))
        monkeypatch.setattr(
            agent, "generate_scqa_for_frame",
            AsyncMock(return_value="Frame (chosen by CFO): Recovering Gross Margin %\n\nSituation: ..."),
        )
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP, \
             patch.object(agent, "_lookup_kpi_scoped", return_value=SimpleNamespace(
                 id="gross_margin_pct", name="Gross Margin %", owner_role="CFO",
             )):
            MockAP.return_value.get_active_framing = AsyncMock(return_value=None)
            MockAP.return_value.upsert = AsyncMock(return_value=Assumption(
                id="a1", client_id="hess", scope="gross_margin_pct", record_type="framing",
                text="The objective is recovering Gross Margin %.", source="da_hitl",
                falsification_criterion="x", created_at="2026-08-18T00:00:00",
            ))
            result = await agent.refine_analysis(_refinement_input(
                _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP),
                framing_decision=_decision(),
            ))

        assert result.topics_completed == [FRAMING_TOPIC]
        assert result.scqa_summary is not None
        assert result.framing_required is False
        assert result.framing_record is not None
        assert result.framing_record.persisted is True
        # The interview did not stall -- a real next-topic question was generated
        # in the SAME response, current_topic advanced past framing.
        assert result.current_topic != FRAMING_TOPIC
        assert result.agent_message

    @pytest.mark.asyncio
    async def test_prior_active_framing_row_is_lifted_not_overwritten(self, monkeypatch):
        """Decision #9: lift-then-insert. A resubmission must mark the prior
        row 'lifted' (via its own upsert call) before inserting the new one."""
        agent = _agent(True)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=_canned_prompt()))
        monkeypatch.setattr(agent, "generate_scqa_for_frame", AsyncMock(return_value="Frame (chosen by CFO): x\n\ny"))
        prior_row = Assumption(
            id="prior-1", client_id="hess", scope="gross_margin_pct", record_type="framing",
            text="The objective is recovering Gross Margin %.", source="da_hitl",
            status="active", falsification_criterion="x",
        )
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP, \
             patch.object(agent, "_lookup_kpi_scoped", return_value=SimpleNamespace(
                 id="gross_margin_pct", name="Gross Margin %", owner_role="CFO",
             )):
            MockAP.return_value.get_active_framing = AsyncMock(return_value=prior_row)
            MockAP.return_value.upsert = AsyncMock(side_effect=lambda item: item if item.id == "prior-1" else Assumption(
                id="new-1", client_id="hess", scope="gross_margin_pct", record_type="framing",
                text="x", source="da_hitl",
            ))
            await agent.refine_analysis(_refinement_input(
                _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP),
                framing_decision=_decision(),
            ))
            upsert_calls = MockAP.return_value.upsert.call_args_list
        assert len(upsert_calls) == 2  # lift the prior row, then insert the new one
        lifted_arg = upsert_calls[0].args[0]
        assert lifted_arg.id == "prior-1"
        assert lifted_arg.status == "lifted"

    @pytest.mark.asyncio
    async def test_register_write_failure_still_proceeds(self, monkeypatch):
        """Losing the register write is a smaller failure than losing the
        chat -- persisted=False with a reason, but the interview advances."""
        agent = _agent(True)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=_canned_prompt()))
        monkeypatch.setattr(agent, "generate_scqa_for_frame", AsyncMock(return_value="Frame (chosen by CFO): x\n\ny"))
        with patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP, \
             patch.object(agent, "_lookup_kpi_scoped", return_value=SimpleNamespace(
                 id="gross_margin_pct", name="Gross Margin %", owner_role="CFO",
             )):
            MockAP.return_value.get_active_framing = AsyncMock(side_effect=RuntimeError("relation does not exist"))
            result = await agent.refine_analysis(_refinement_input(
                _da(change_points=_DISTRIBUTED, where_is_not=_CONTROL_GROUP),
                framing_decision=_decision(),
            ))

        assert result.framing_record is not None
        assert result.framing_record.persisted is False
        assert result.framing_record.persist_error
        # The chat itself is NOT a casualty -- framing_choice still recorded
        # in the response, next topic's question still generated.
        assert result.topics_completed == [FRAMING_TOPIC]
        assert result.current_topic != FRAMING_TOPIC
        assert result.scqa_summary is not None

    @pytest.mark.asyncio
    async def test_unresolvable_kpi_still_proceeds_without_persisting(self, monkeypatch):
        """client_id/kpi_id not resolvable at all -- still must not lose the
        chat, but obviously cannot write a scoped register row."""
        agent = _agent(True)
        monkeypatch.setattr(agent, "_build_framing_prompt", AsyncMock(return_value=None))
        monkeypatch.setattr(agent, "generate_scqa_for_frame", AsyncMock(return_value="Frame (chosen by cfo_001): x\n\ny"))
        with patch.object(agent, "_lookup_kpi_scoped", return_value=None):
            result = await agent.refine_analysis(_refinement_input(
                _da(kpi_name=None, client_id=None),
                framing_decision=_decision(),
            ))
        assert result.framing_record.persisted is False
        assert result.topics_completed == [FRAMING_TOPIC]
