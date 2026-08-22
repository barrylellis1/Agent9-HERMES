"""
Regression test: VA registration's kpi_id was ALWAYS the situation's original
KPI, never the framing decision's chosen one -- found live 2026-08-22 in
today's own Gross Margin % -> COGS reframe test. A reframed, human-approved
solution would have been registered and measured against the wrong KPI,
silently, with no error anywhere in the chain.

See docs/architecture/reframe_relaunch_and_lineage_design.md and
kpi_relationship_basis_design.md's pending VA-capture follow-up.
"""

from src.api.routes.workflows import _resolve_va_kpi_id_and_framing
from src.agents.models.value_assurance_models import FramingSnapshot


def _wf_payload(framing_decision=None):
    payload = {"preferences": {}}
    if framing_decision is not None:
        payload["preferences"]["refinement_result"] = {"framing_decision": framing_decision}
    return payload


def test_reframed_choice_registers_the_chosen_kpi_not_the_stated_one():
    """The exact scenario from today's live test: CFO reframes Gross Margin %
    onto COGS -- kpi_id must be 'cogs', not 'gross_margin_pct'."""
    payload = _wf_payload({
        "choice": "alternative",
        "chosen_kpi_id": "cogs",
        "chosen_objective_text": "Addressing Cost of Goods Sold instead of Gross Margin % directly",
        "falsification_criterion": "If COGS does not fall within two cycles, this frame was wrong.",
    })

    kpi_id, snapshot = _resolve_va_kpi_id_and_framing(payload, stated_kpi_id="gross_margin_pct")

    assert kpi_id == "cogs"
    assert isinstance(snapshot, FramingSnapshot)
    assert snapshot.choice == "alternative"
    assert snapshot.chosen_kpi_id == "cogs"
    assert snapshot.stated_kpi_id == "gross_margin_pct"


def test_confirmed_choice_keeps_the_stated_kpi():
    payload = _wf_payload({
        "choice": "confirm_stated",
        "chosen_kpi_id": None,
        "chosen_objective_text": "Recovering Gross Margin %",
        "falsification_criterion": "If margin does not recover, this frame was wrong.",
    })

    kpi_id, snapshot = _resolve_va_kpi_id_and_framing(payload, stated_kpi_id="gross_margin_pct")

    assert kpi_id == "gross_margin_pct"
    assert snapshot.choice == "confirm_stated"
    assert snapshot.chosen_kpi_id is None


def test_no_framing_gate_ran_falls_back_cleanly():
    """Older payloads, or a KPI the framing gate flag was off for -- no
    preferences.refinement_result.framing_decision at all."""
    kpi_id, snapshot = _resolve_va_kpi_id_and_framing({}, stated_kpi_id="net_revenue")

    assert kpi_id == "net_revenue"
    assert snapshot is None


def test_alternative_choice_with_no_chosen_kpi_id_falls_back_to_stated():
    """A malformed/incomplete alternative decision must not register kpi_id=''
    or None -- degrade to the known-good stated KPI instead."""
    payload = _wf_payload({
        "choice": "alternative",
        "chosen_kpi_id": None,
        "chosen_objective_text": "Something else",
        "falsification_criterion": "x",
    })

    kpi_id, snapshot = _resolve_va_kpi_id_and_framing(payload, stated_kpi_id="gross_margin_pct")

    assert kpi_id == "gross_margin_pct"


def test_other_choice_also_uses_chosen_kpi_id_when_present():
    """'other' (free-text reframe) still routes through chosen_kpi_id when the
    caller populated one -- choice matters, not the literal string 'alternative'."""
    payload = _wf_payload({
        "choice": "other",
        "chosen_kpi_id": "distribution_cost",
        "chosen_objective_text": "Addressing distribution cost overruns",
        "falsification_criterion": "x",
        "other_text": "Addressing distribution cost overruns",
    })

    kpi_id, snapshot = _resolve_va_kpi_id_and_framing(payload, stated_kpi_id="cogs")

    assert kpi_id == "distribution_cost"
    assert snapshot.choice == "other"


def test_malformed_framing_decision_does_not_raise():
    """A framing_decision missing required FramingSnapshot fields must degrade
    to no snapshot, never propagate a validation error into HITL approval."""
    payload = _wf_payload({"choice": "alternative"})  # missing chosen_objective_text, falsification_criterion

    kpi_id, snapshot = _resolve_va_kpi_id_and_framing(payload, stated_kpi_id="net_revenue")

    # chosen_kpi_id absent -> falls back to stated even though choice != confirm_stated
    assert kpi_id == "net_revenue"
    # FramingSnapshot tolerates missing text fields via explicit "" defaults in
    # the caller, so this constructs successfully rather than raising -- pin that.
    assert snapshot is not None
    assert snapshot.chosen_objective_text == ""
