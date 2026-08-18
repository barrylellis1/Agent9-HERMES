"""
Phase 19 — framing record model tests (2026-08-18).

Covers Slice 1 of the framing implementation plan (see
docs/architecture/problem_framing_design.md and the plan file referenced from
DEVELOPMENT_PLAN.md Phase 19): the Assumption model's new record_type='framing'
value, new source='da_hitl' value, and the new expiry_event field.

No DB/provider integration here — same posture as
test_theory_layer_causal_schema.py, which this file directly extends. The
migration section reads the .sql text and asserts the constraint strings
rather than requiring a live Supabase connection.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from src.registry.models.assumption import Assumption


def _assumption(**overrides):
    base = dict(client_id="lubricants", scope="net_revenue", text="x", source="da_hitl")
    base.update(overrides)
    return Assumption(**base)


# ---------------------------------------------------------------------------
# record_type='framing'
# ---------------------------------------------------------------------------

def test_record_type_framing_is_accepted():
    a = _assumption(record_type="framing")
    assert a.record_type == "framing"


def test_framing_record_does_not_require_expiry():
    """Proves the explanation-only validator doesn't over-reach: adding a
    fourth record_type value must not accidentally trip
    _explanation_requires_expiry, which checks record_type == 'explanation'
    specifically. Framing records are event-scoped via expiry_event, not
    date-scoped via expiry — see expiry_event's docstring."""
    a = _assumption(record_type="framing")
    assert a.expiry is None


def test_framing_record_with_expiry_event_round_trips():
    a = _assumption(record_type="framing", expiry_event="va_verdict_on_linked_solution")
    assert a.expiry_event == "va_verdict_on_linked_solution"
    assert a.expiry is None


def test_expiry_event_rejects_invalid_value():
    with pytest.raises(ValidationError):
        _assumption(record_type="framing", expiry_event="whenever_someone_gets_around_to_it")


def test_expiry_event_defaults_to_none_for_every_record_type():
    # A non-framing record must not silently pick up an expiry_event value —
    # the field only has one legal value and is opt-in everywhere.
    for record_type in ("assumption", "constraint", "framing"):
        assert _assumption(record_type=record_type).expiry_event is None


# ---------------------------------------------------------------------------
# source='da_hitl'
# ---------------------------------------------------------------------------

def test_source_da_hitl_is_accepted():
    a = _assumption(source="da_hitl", record_type="framing")
    assert a.source == "da_hitl"


def test_da_hitl_source_still_rejected_for_unrelated_invalid_values():
    # Sanity check the enum extension didn't accidentally widen validation.
    with pytest.raises(ValidationError):
        _assumption(source="framing_gate")


# ---------------------------------------------------------------------------
# Migration text — read the .sql, assert the constraint strings, no live DB
# needed. Same pattern as test_theory_layer_causal_schema.py's coverage of
# 20260723_theory_layer_causal_schema.sql (that file has no dedicated test of
# its own text; this establishes the pattern for the framing migration since
# it is new and additive rather than baseline schema).
# ---------------------------------------------------------------------------

_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2]
    / "supabase" / "migrations" / "20260818_framing_records.sql"
)


def test_migration_file_exists():
    assert _MIGRATION_PATH.exists(), f"expected migration at {_MIGRATION_PATH}"


def test_migration_adds_expiry_event_column():
    text = _MIGRATION_PATH.read_text(encoding="utf-8")
    assert "ADD COLUMN IF NOT EXISTS expiry_event" in text


def test_migration_extends_record_type_check_to_include_framing():
    text = _MIGRATION_PATH.read_text(encoding="utf-8")
    assert "'assumption', 'constraint', 'explanation', 'framing'" in text


def test_migration_extends_source_check_to_include_da_hitl():
    text = _MIGRATION_PATH.read_text(encoding="utf-8")
    assert (
        "'sa_hitl', 'sf_hitl_rejection', 'sf_hitl_approval', 'va_hitl', 'manual', 'da_hitl'"
        in text
    )


def test_migration_constrains_expiry_event_to_the_one_known_value():
    text = _MIGRATION_PATH.read_text(encoding="utf-8")
    assert "expiry_event IS NULL OR expiry_event IN ('va_verdict_on_linked_solution')" in text


def test_migration_adds_framing_scope_index():
    text = _MIGRATION_PATH.read_text(encoding="utf-8")
    assert "idx_assumptions_framing_scope" in text
    assert "WHERE record_type = 'framing'" in text


def test_migration_documents_the_unbackstopped_expiry_gap():
    # The un-backstopped case (a frame whose solution is never approved never
    # expires) must be named in the migration, not just in the design doc —
    # this is the kind of thing that gets silently forgotten a phase later.
    text = _MIGRATION_PATH.read_text(encoding="utf-8")
    assert "never expires" in text
