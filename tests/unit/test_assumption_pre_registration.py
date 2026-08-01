"""Pre-registration of SF "bets on" assumptions at HITL approval (theory §5.3).

Writing these at APPROVAL time rather than at verdict time is the design point:
it is the record that the claims were committed to before the outcome was known.
Without it, the later discipline of grading assumptions *before* revealing DiD
attribution is a formality — nothing would prove the bet predated the result.

These tests cover the mapping only (no DB): the provider round-trip, idempotency,
and verdict-preservation-on-re-approval were verified against local Supabase and
depend on a live pool, so they are not unit-testable here.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.api.routes.workflows import _assumption_from_bet
from src.registry.models.assumption import Assumption


def _bet(**overrides):
    """A SolutionAssumption as it arrives from SF (already model_dump()'d)."""
    base = {
        "assumption": "Base oil holds under $85/bbl through Q3",
        "validated_by": "sa_assessment",
        "validated_at": None,
        "revalidation_days": 30,
        "grounded": True,
        "confidence": "moderate",
        # NOTE: on SolutionAssumption this field is free-text "what would
        # falsify this" — NOT the capture ladder. That collision is the whole
        # reason the mapping needs its own tests.
        "provenance": "base_oil_cost exceeds 85 for two consecutive periods",
    }
    base.update(overrides)
    return base


def _map(bet, **kw):
    args = dict(client_id="lubricants", kpi_id="gross_margin_pct",
                situation_id="sit_1", solution_id="sol_1")
    args.update(kw)
    return _assumption_from_bet(bet, **args)


# ---------------------------------------------------------------------------
# The collision — the rule most likely to be "simplified" back into a bug
# ---------------------------------------------------------------------------

def test_solution_assumption_provenance_is_not_copied_into_the_ladder():
    """SolutionAssumption.provenance is a falsification criterion;
    Assumption.provenance is the capture ladder. Copying across would fail the
    DB CHECK constraint at best and corrupt ladder semantics at worst."""
    rec = _map(_bet())
    assert rec.provenance == "hitl_proposed"
    assert rec.provenance != _bet()["provenance"]


def test_falsification_criterion_carries_the_free_text():
    """The criterion is the most useful field for honest grading later — it must
    survive the hop rather than being dropped on the floor."""
    rec = _map(_bet())
    assert rec.falsification_criterion == (
        "base_oil_cost exceeds 85 for two consecutive periods"
    )


def test_approval_is_a_proposal_not_a_confirmation():
    """Even when SF marked the assumption grounded+high confidence, a human
    approving a solution that BETS ON a claim has proposed it, not confirmed
    it. Anything above hitl_proposed here would be unearned ladder inflation."""
    rec = _map(_bet(grounded=True, confidence="high"))
    assert rec.provenance == "hitl_proposed"


# ---------------------------------------------------------------------------
# Grading routing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("who", ["sa_assessment", "ma_query", "human_confirmation"])
def test_validated_by_survives_as_the_grading_routing_key(who):
    """Lose this and step 2 cannot tell machine-checkable claims from ones
    needing a person, so every solution puts its full list in front of an
    executive and adjudication rots (theory §9 pre-mortem #3)."""
    assert _map(_bet(validated_by=who)).validated_by == who


def test_missing_validated_by_is_tolerated():
    """Older SF payloads predate the field; a missing routing key must not
    block pre-registration."""
    bet = _bet()
    del bet["validated_by"]
    assert _map(bet).validated_by is None


def test_invalid_validated_by_is_rejected_by_the_model():
    with pytest.raises(ValidationError):
        Assumption(
            client_id="lubricants", scope="k", record_type="assumption",
            text="t", source="sf_hitl_approval", validated_by="vibes",
        )


# ---------------------------------------------------------------------------
# Fixed fields + skip behaviour
# ---------------------------------------------------------------------------

def test_maps_fixed_fields_for_grading_and_join():
    rec = _map(_bet())
    assert rec.text == "Base oil holds under $85/bbl through Q3"
    assert rec.record_type == "assumption"
    assert rec.status == "active"          # -> held | falsified at evaluation
    assert rec.source == "sf_hitl_approval"
    assert rec.confidence == "moderate"
    assert rec.scope == "gross_margin_pct"
    assert rec.linked_solution_id == "sol_1"
    assert rec.linked_situation_id == "sit_1"


def test_scope_falls_back_to_client_when_kpi_unknown():
    """scope is NOT NULL; a solution without a resolved kpi_id must still
    pre-register rather than throwing inside the approve handler."""
    assert _map(_bet(), kpi_id=None).scope == "client"


@pytest.mark.parametrize("bad", [None, "a string", 42, [], {}, {"assumption": "   "}])
def test_unusable_entries_are_skipped_not_raised(bad):
    """The approve handler must never fail because SF emitted a malformed
    assumption — the approval itself is the user's action and matters more."""
    assert _map(bad) is None


def test_blank_text_is_skipped():
    assert _map(_bet(assumption="")) is None
    assert _map(_bet(assumption=None)) is None
