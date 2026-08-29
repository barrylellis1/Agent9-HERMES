"""Regression/coverage tests for the workflow_role field on PrincipalProfile
(2026-08-25, Decision Framer / Decision Maker split).

Additive, non-breaking field: defaults to FRAMER so every pre-existing
principal's behavior is unchanged. Two values only -- this is a
WORKFLOW-STAGE axis (default landing view, briefing disclosure depth),
never a content axis (never gates which option a Solution Finder run
recommends). See docs/architecture/decision_framer_and_decision_maker_personas_design.md
"""
import pytest
from pydantic import ValidationError

from src.registry.models.principal import PrincipalProfile, WorkflowRole


def _profile(**overrides) -> PrincipalProfile:
    base = dict(id="test_principal", client_id="test_client", name="Test", title="Test Title")
    base.update(overrides)
    return PrincipalProfile(**base)


class TestWorkflowRoleDefault:
    def test_defaults_to_framer_when_absent(self):
        """A principal dict with no workflow_role key at all -- the shape every
        pre-existing production row has today -- must resolve to FRAMER, not
        error and not silently drop to some other value."""
        profile = _profile()
        assert profile.workflow_role == WorkflowRole.FRAMER

    def test_default_is_non_breaking_for_existing_seed_shape(self):
        """Mirrors a real pre-migration seed dict (no workflow_role key) --
        this must construct cleanly, the same precondition the migration's
        own DEFAULT 'framer' guarantees at the database layer."""
        legacy_shape = {
            "id": "cfo_001",
            "client_id": "lubricants",
            "name": "Sarah Chen",
            "title": "Chief Financial Officer",
        }
        profile = PrincipalProfile(**legacy_shape)
        assert profile.workflow_role == WorkflowRole.FRAMER


class TestWorkflowRoleExplicitValues:
    def test_accepts_framer(self):
        assert _profile(workflow_role="framer").workflow_role == WorkflowRole.FRAMER

    def test_accepts_decision_maker(self):
        assert _profile(workflow_role="decision_maker").workflow_role == WorkflowRole.DECISION_MAKER

    def test_rejects_invalid_value(self):
        """Must fail closed, matching the DB-level CHECK constraint added in
        the same migration -- an invalid string should never silently
        coerce to a valid enum member."""
        with pytest.raises(ValidationError):
            _profile(workflow_role="executive")


class TestWorkflowRoleNeverGatesContent:
    """This field must control entry point / disclosure depth only -- never
    which option a Solution Finder run recommends (the M1 invariant, stated
    independently in this same model's option-ranking-weights comment,
    DecisionAskBlock.tsx, and DEVELOPMENT_PLAN.md Phase 13)."""

    def test_workflow_role_is_not_read_by_option_ranking(self):
        """option_dominance.py / option ranking must never import or branch
        on WorkflowRole -- confirms the field stays confined to its intended
        axis rather than leaking into recommendation logic."""
        import inspect
        from src.analysis import option_dominance

        source = inspect.getsource(option_dominance)
        assert "workflow_role" not in source
        assert "WorkflowRole" not in source
