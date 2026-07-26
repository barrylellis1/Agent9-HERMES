"""
Phase 15 Stage D/E — theory layer causal schema tests (2026-07-23).

Covers the two new/extended models designed after researching causal-graph
best practices: KPIRelationship's causal typing (mechanism/lag_periods/
causal_rung/provenance/confidence) and the new Assumption
(assumption/constraint/explanation) register.

No DB/provider integration here — those need a live Supabase connection and
are exercised via the existing regression suite pattern once Stage D/E
actually wires consumption. This file locks in the model-level contracts:
defaults, validation, and the mandatory-expiry rule for explanation records.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.registry.models.kpi_relationship import KPIRelationship
from src.registry.models.assumption import Assumption


# ---------------------------------------------------------------------------
# KPIRelationship — causal typing
# ---------------------------------------------------------------------------

def _relationship(**overrides):
    base = dict(
        kpi_id="net_revenue", related_kpi_id="cogs", client_id="hess",
        relationship_type="cost_revenue", conflict_direction="diverging",
    )
    base.update(overrides)
    return KPIRelationship(**base)


def test_provenance_defaults_to_template():
    # Conservative default per "no invented defaults" — unreviewed edges must
    # not silently read as confirmed.
    assert _relationship().provenance == "template"


def test_causal_rung_and_provenance_are_independent_fields():
    # Independent axes, but NOT unconstrained combinations — see the
    # intervention_tested guardrail tests below for the one enforced link.
    r = _relationship(causal_rung="intervention_hypothesized", provenance="hitl_proposed")
    assert r.causal_rung == "intervention_hypothesized"
    assert r.provenance == "hitl_proposed"


def test_intervention_tested_requires_va_validated_provenance():
    """Epistemic guardrail (2026-07-26): HITL confirmation is agreement with
    a narrative, not a statistical test. Only VA actually running DiD/Granger
    causality on this specific edge may claim the intervention_tested rung —
    'confirmed' (a human said yes) must never be able to masquerade as it."""
    with pytest.raises(ValidationError, match="intervention_tested"):
        _relationship(causal_rung="intervention_tested", provenance="confirmed")
    with pytest.raises(ValidationError, match="intervention_tested"):
        _relationship(causal_rung="intervention_tested", provenance="hitl_proposed")
    with pytest.raises(ValidationError, match="intervention_tested"):
        _relationship(causal_rung="intervention_tested", provenance="template")


def test_intervention_tested_accepted_with_va_validated_provenance():
    r = _relationship(causal_rung="intervention_tested", provenance="va_validated")
    assert r.causal_rung == "intervention_tested"
    assert r.provenance == "va_validated"


def test_non_tested_rungs_unaffected_by_the_guardrail():
    # The constraint targets ONLY intervention_tested — correlational and
    # intervention_hypothesized may pair with any provenance value.
    for rung in ("correlational", "intervention_hypothesized", None):
        for prov in ("template", "confirmed", "hitl_proposed", "va_validated"):
            _relationship(causal_rung=rung, provenance=prov)  # must not raise


def test_causal_rung_rejects_invalid_value():
    with pytest.raises(ValidationError):
        _relationship(causal_rung="definitely_true")


def test_confidence_is_categorical_not_numeric():
    with pytest.raises(ValidationError):
        _relationship(confidence=0.85)  # must be high/moderate/low, not a float score


def test_mechanism_and_lag_periods_optional_and_unset_by_default():
    r = _relationship()
    assert r.mechanism is None
    assert r.lag_periods is None


# ---------------------------------------------------------------------------
# Assumption — record_type discriminator + mandatory expiry for explanations
# ---------------------------------------------------------------------------

def _assumption(**overrides):
    base = dict(client_id="hess", scope="net_revenue", text="x", source="sa_hitl")
    base.update(overrides)
    return Assumption(**base)


def test_record_type_defaults_to_assumption():
    assert _assumption().record_type == "assumption"


def test_explanation_without_expiry_is_rejected():
    """The core enforcement: theory doc §5.1/§9 pre-mortem #5 — indefinite
    suppression without self-falsification is 'snooze with better paperwork'.
    Must fail at construction time, not silently pass through."""
    with pytest.raises(ValidationError, match="explanation records must carry an expiry"):
        _assumption(record_type="explanation")


def test_explanation_with_expiry_is_accepted():
    a = _assumption(record_type="explanation", expiry="2026-08-01T00:00:00")
    assert a.expiry == "2026-08-01T00:00:00"


def test_constraint_does_not_require_expiry():
    # Constraints are permanent prohibitions, not time-bound explanations —
    # the expiry requirement is specific to record_type='explanation'.
    a = _assumption(record_type="constraint", source="sf_hitl_rejection")
    assert a.expiry is None


def test_assumption_does_not_require_expiry():
    a = _assumption(record_type="assumption")
    assert a.expiry is None


def test_invalid_record_type_rejected():
    with pytest.raises(ValidationError):
        _assumption(record_type="belief")


def test_invalid_source_rejected():
    with pytest.raises(ValidationError):
        _assumption(source="someone_said_so")


def test_provenance_defaults_to_hitl_proposed():
    # Assumptions are accreted from usage by default — distinct from
    # KPIRelationship's 'template' default, which is seeded/researched.
    assert _assumption().provenance == "hitl_proposed"
