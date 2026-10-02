# arch-allow-direct-agent-construction
"""reliability.kpi_coverage -- the fifth and final pilot signal for the
stage-wise reliability panel (docs/architecture/audit_event_system_design.md,
2026-10-02 scope extension), and the only one of the five that did not
already compute anything.

Two things under test:
1. `_get_relevant_kpis(..., coverage_out=...)` populates registered/evaluated
   correctly -- including a genuine Brookshire Brothers-shaped fixture
   (business_processes assigned on both sides, zero overlap) reproduced with
   TODAY's code, as a regression anchor for what this signal would have
   caught live on 2026-07-25.
2. `_kpi_coverage_outcome()` -- the pure decision function -- maps those
   counts to pass/fail/None correctly, including the registered==0 skip and
   the known false-positive case (a legitimately zero-overlap principal also
   reads as `fail`, disclosed rather than hidden -- see the call site's own
   comment in a9_situation_awareness_agent.py).

Reuses test_kpi_accountability_wiring.py's fixtures (_sa_agent, _kpi_def)
rather than re-deriving them.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.agents.new.a9_situation_awareness_agent import (
    A9_Situation_Awareness_Agent,
    _kpi_coverage_outcome,
)
from src.agents.models.situation_awareness_models import PrincipalContext


def _sa_agent() -> A9_Situation_Awareness_Agent:
    agent = A9_Situation_Awareness_Agent(config={})
    agent.data_governance_agent = MagicMock()
    agent.kpi_registry = {}
    agent.data_product_agent = None
    agent.principal_profiles = {}
    return agent


def _kpi_def(kpi_id: str, client_id: str = "lubricants", business_processes=None) -> MagicMock:
    kpi = MagicMock()
    kpi.id = kpi_id
    kpi.name = kpi_id
    kpi.client_id = client_id
    kpi.business_processes = business_processes if business_processes is not None else []
    kpi.business_process_ids = None
    return kpi


def _principal_context(business_processes, principal_id="cfo_001") -> MagicMock:
    ctx = MagicMock(spec=PrincipalContext)
    ctx.principal_id = principal_id
    ctx.role = "CFO"
    ctx.business_processes = business_processes
    return ctx


class TestKpiCoverageOutcome:
    """The pure decision function -- no agent needed."""

    def test_nothing_registered_skips_entirely(self):
        assert _kpi_coverage_outcome(registered=0, evaluated=0) is None

    def test_full_dropout_is_fail(self):
        assert _kpi_coverage_outcome(registered=5, evaluated=0) == "fail"

    def test_any_nonzero_evaluated_is_pass(self):
        assert _kpi_coverage_outcome(registered=5, evaluated=1) == "pass"
        assert _kpi_coverage_outcome(registered=5, evaluated=5) == "pass"


class TestGetRelevantKpisCoverageOut:
    """_get_relevant_kpis(coverage_out=...) -- the side-channel the async
    caller reads to decide whether to emit."""

    def test_coverage_out_counts_registered_and_evaluated(self):
        agent = _sa_agent()
        agent.kpi_registry = {
            "lubricants:gross_margin_pct": _kpi_def("gross_margin_pct"),
            "lubricants:net_revenue": _kpi_def("net_revenue"),
        }
        ctx = _principal_context(business_processes=[])  # fail-open shortcut -- matches all
        coverage = {}

        with patch.object(agent, "_apply_principal_kpi_preferences", side_effect=lambda _c, kpis: kpis):
            result = agent._get_relevant_kpis(ctx, client_id="lubricants", coverage_out=coverage)

        assert coverage == {"registered": 2, "evaluated": 2}
        assert set(result.keys()) == {"gross_margin_pct", "net_revenue"}

    def test_brookshire_brothers_shape_reproduced_with_todays_code(self):
        """The live 2026-07-25 incident was principals with business_processes=[]
        (the fail-open shortcut above) zeroing out real KPIs -- already fixed.
        A genuine, non-bug zero-overlap case still exists today when BOTH sides
        declare real, non-matching business processes -- this is what the
        coverage signal's known false-positive is about (see the call site's
        comment), reproduced here to prove it really does read registered>0,
        evaluated=0 on legitimate input, not just on a contrived empty dict."""
        agent = _sa_agent()
        agent.kpi_registry = {
            "lubricants:gross_margin_pct": _kpi_def("gross_margin_pct", business_processes=["Finance: Profitability"]),
            "lubricants:net_revenue": _kpi_def("net_revenue", business_processes=["Finance: Profitability"]),
        }
        ctx = _principal_context(business_processes=["HR: Recruiting"])
        coverage = {}

        with patch.object(agent, "_apply_principal_kpi_preferences", side_effect=lambda _c, kpis: kpis):
            result = agent._get_relevant_kpis(ctx, client_id="lubricants", coverage_out=coverage)

        assert coverage == {"registered": 2, "evaluated": 0}
        assert result == {}
        assert _kpi_coverage_outcome(**coverage) == "fail"

    def test_no_coverage_out_does_not_break_existing_callers(self):
        """coverage_out is optional -- every pre-existing call site that
        doesn't pass it must keep working unchanged."""
        agent = _sa_agent()
        agent.kpi_registry = {"lubricants:net_revenue": _kpi_def("net_revenue")}
        ctx = _principal_context(business_processes=[])

        with patch.object(agent, "_apply_principal_kpi_preferences", side_effect=lambda _c, kpis: kpis):
            result = agent._get_relevant_kpis(ctx, client_id="lubricants")

        assert "net_revenue" in result
