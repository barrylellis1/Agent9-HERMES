"""
Phase 22 Stage A — deterministic override of moderator_grades.arithmetic_consistency.

VerificationLedger.tsx renders this field as a green PASS / red FAIL chip in
the compact executive briefing — the one component that literally claims
verification happened. Before this override it was the moderator's OWN
self-report: a separate LLM call grading an option against its own claimed
inputs, never against the data. src.analysis.groundedness's own docstring
records the live failure this produced (2026-08-06): `pass` on an option
claiming 26-47pp impact built by summing unweighted segment deltas, against a
KPI whose actual enterprise move was -1.67pp.

These tests recreate that failure shape against a real captured DA fixture's
extraction path (not synthetic regex-matching text) and assert the override:
- downgrades a self-reported "pass" that the data contradicts, to "flag"
- upgrades a self-reported "flag" the data actually supports, to "pass"
- never lets an unverifiable claim show as a bare self-reported "pass" —
  degrades to "insufficient_data" instead, one of the moderator's own three
  valid values, rather than trusting the self-report when nothing can be
  checked.

Uses the same direct-construction + capturing-stub-orchestrator pattern as
test_sf_stage_h_moderator.py (that file predates this one; not imported from
here — no tests/unit/__init__.py, and no existing precedent for cross-test-
file imports in this repo — so the small harness is reproduced locally,
trimmed to just what this override needs).
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.models.solution_finder_models import SolutionFinderRequest, TradeOffCriterion
from src.agents.new.a9_solution_finder_agent import A9_Solution_Finder_Agent
from src.registry.models.kpi_relationship import KPIRelationship
from src.registry.models.assumption import Assumption


def _kpi(kpi_id, client_id, name="Gross Margin %"):
    return SimpleNamespace(id=kpi_id, client_id=client_id, name=name)


def _patched_provider_for_e2e():
    provider = MagicMock()
    provider.get_all.return_value = [_kpi("gross_margin_pct", "lubricants")]
    factory = MagicMock()
    factory.get_provider.return_value = provider
    return patch("src.registry.factory.RegistryFactory", return_value=factory)


class _CapturingOrchestrator:
    """Handles Stage 1 and synthesis calls; the synthesis analysis payload is
    injectable so each test can drive a specific moderator_grades shape
    through parsing without needing a real LLM."""

    def __init__(self, synthesis_analysis: dict):
        self.captured_prompts: list[str] = []
        self._synthesis_analysis = synthesis_analysis

    async def execute_agent_method(self, agent_name: str, method_name: str, params):
        assert agent_name == "A9_LLM_Service_Agent" and method_name == "analyze"
        req = params.get("request")
        self.captured_prompts.append(getattr(req, "content", "") or "")
        req_id = getattr(req, "request_id", "")

        if "_s1_" in req_id:
            analysis = {
                "persona_id": "mckinsey", "framework": "MECE", "hypothesis": "h",
                "key_evidence": ["e1", "e2", "e3"], "recommended_focus": "Chain A",
                "conviction": "High",
                "proposed_option": {
                    "title": "Reprice anchor accounts",
                    "mechanism": "Margin recovery via price realignment",
                    "description": "d", "time_horizon": "0-90 days",
                    "impact_estimate": {"metric": "Gross Margin", "unit": "%",
                                        "recovery_range": {"low": 1.0, "high": 2.0}, "basis": "..."},
                    "cost_signal": "Medium", "risk_signal": "Low",
                },
            }
            return SimpleNamespace(status="success", request_id=req_id, analysis=analysis,
                                   model_used="mock-llm", usage={}, confidence=0.9)

        # Synthesis / moderator
        return SimpleNamespace(status="success", request_id=req_id,
                               analysis=self._synthesis_analysis,
                               model_used="mock-llm",
                               usage={"prompt_tokens": 100, "completion_tokens": 50},
                               confidence=0.9)


async def _build_sf(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    sf = await A9_Solution_Finder_Agent.create({
        "enable_llm_debate": True,
        "enable_hybrid_council": True,  # required for Stage 1 to run at all
        "enable_causal_grounding": True,
        "enable_theory_moderator": True,
    })
    await sf.connect()
    return sf


def _synthesis(option_impact_estimate: dict, self_reported: str) -> dict:
    return {
        "problem_reframe": {"situation": "s", "complication": "c", "question": "q",
                            "key_assumptions": []},
        "options": [
            {"id": "opt_1", "title": "Reprice at renewal", "expected_impact": 0.7,
             "cost": 0.3, "risk": 0.2, "impact_estimate": option_impact_estimate},
        ],
        "recommendation": {"id": "opt_1", "title": "Reprice at renewal"},
        "recommendation_rationale": "Renewal boundary avoids the mid-quarter price lock.",
        "unresolved_tensions": [], "blind_spots": [], "next_steps": [],
        "moderator_grades": {
            "opt_1": {
                "constraint_survival": "pass",
                "causal_grounding": "base_oil_cost -> gross_margin_pct",
                "arithmetic_consistency": self_reported,  # the model's own claim
                "arithmetic_note": None,
                "critic_findings_response": [],
                "grade_rationale": "Self-reported by the moderator prompt.",
            }
        },
    }


def _sf_request(deep_analysis_output: dict) -> SolutionFinderRequest:
    return SolutionFinderRequest(
        request_id=str(uuid.uuid4()), principal_id="cfo_001",
        problem_statement="Gross margin declined vs prior year",
        deep_analysis_output=deep_analysis_output,
        client_id="lubricants",
        evaluation_criteria=[TradeOffCriterion(name="impact", weight=0.5),
                             TradeOffCriterion(name="cost", weight=0.3),
                             TradeOffCriterion(name="risk", weight=0.2)],
    )


# A DA fixture whose enterprise move is small and real, in the exact
# narrative shape extract_da_facts's regex reads (`[Δ<number>]` inside a
# what_is line) — not a synthetic string picked to make the regex happy, the
# same shape verified against decision-studio-ui/scratchpad/dq_comparison/
# lens_run/da-payload.json during this fix's own development.
_DA_WITH_REAL_ENTERPRISE_DELTA = {
    "plan": {"kpi_name": "Gross Margin %", "client_id": "lubricants"},
    "execution": {
        "kt_is_is_not": {
            "what_is": [
                {"text": "Gross Margin % is underperforming plan [Δ4.49] at the enterprise level."},
            ]
        },
        "change_points": [],
    },
}

_DA_WITH_NO_ENTERPRISE_DELTA = {
    "plan": {"kpi_name": "Gross Margin %", "client_id": "lubricants"},
}


async def _run(sf, stub):
    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_causal_neighbourhood = AsyncMock(return_value=[])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[])
        return await sf.recommend_actions(stub._request)


@pytest.mark.asyncio
async def test_self_reported_pass_is_downgraded_when_data_contradicts_it(monkeypatch):
    """The exact documented failure shape: moderator self-reports 'pass' on an
    enterprise claim the real DA data cannot support (47pp vs an actual 4.49pp
    move — the same order-of-magnitude gap as the live 2026-08-06 incident)."""
    sf = await _build_sf(monkeypatch)
    synthesis = _synthesis(
        option_impact_estimate={"scope": "enterprise", "recovery_range": {"high": 47}},
        self_reported="pass",
    )
    stub = _CapturingOrchestrator(synthesis)
    stub._request = _sf_request(_DA_WITH_REAL_ENTERPRISE_DELTA)
    sf.orchestrator = stub
    sf.llm_service_agent = None

    resp = await _run(sf, stub)

    assert resp.moderator_grades["opt_1"]["arithmetic_consistency"] == "flag", (
        "a self-reported 'pass' the real data contradicts must not reach the "
        "briefing unchanged"
    )
    assert "4.49" in (resp.moderator_grades["opt_1"]["arithmetic_note"] or "")


@pytest.mark.asyncio
async def test_self_reported_flag_is_upgraded_when_data_actually_supports_it(monkeypatch):
    """The moderator can be wrong in the other direction too: a plausible claim
    it flagged unnecessarily must not stay flagged."""
    sf = await _build_sf(monkeypatch)
    synthesis = _synthesis(
        option_impact_estimate={"scope": "enterprise", "recovery_range": {"high": 3.5}},
        self_reported="flag",
    )
    stub = _CapturingOrchestrator(synthesis)
    stub._request = _sf_request(_DA_WITH_REAL_ENTERPRISE_DELTA)
    sf.orchestrator = stub
    sf.llm_service_agent = None

    resp = await _run(sf, stub)

    assert resp.moderator_grades["opt_1"]["arithmetic_consistency"] == "pass"
    assert resp.moderator_grades["opt_1"]["arithmetic_note"] is None


@pytest.mark.asyncio
async def test_unverifiable_claim_never_shows_as_a_bare_self_reported_pass(monkeypatch):
    """No enterprise/segment baseline to check against -> insufficient_data,
    never a pass-through of whatever the moderator claimed. A self-report is
    not a check; when the deterministic read cannot run, the chip must say so
    rather than imply one happened."""
    sf = await _build_sf(monkeypatch)
    synthesis = _synthesis(
        option_impact_estimate={"scope": "enterprise", "recovery_range": {"high": 5}},
        self_reported="pass",
    )
    stub = _CapturingOrchestrator(synthesis)
    stub._request = _sf_request(_DA_WITH_NO_ENTERPRISE_DELTA)
    sf.orchestrator = stub
    sf.llm_service_agent = None

    resp = await _run(sf, stub)

    assert resp.moderator_grades["opt_1"]["arithmetic_consistency"] == "insufficient_data"


@pytest.mark.asyncio
async def test_override_never_breaks_generation_on_malformed_impact_estimate(monkeypatch):
    """Observation must never break generation — same discipline the
    constraint-union assembly right above this block already follows.

    A malformed impact_estimate ("not a dict") is caught by SolutionOption's
    own Pydantic validation before this override ever sees it, so score_option
    sees no impact_estimate at all and correctly reports g3 as not-checkable —
    the SAME insufficient_data path as the missing-baseline case above, not a
    crash and NOT a silent pass-through of the self-reported "pass". Belt and
    braces either way: whether the malformation is caught upstream by Pydantic
    or reaches score_option directly, the run must complete and the self-
    report must never survive unexamined.
    """
    sf = await _build_sf(monkeypatch)
    synthesis = _synthesis(
        option_impact_estimate="not a dict",  # malformed on purpose
        self_reported="pass",
    )
    stub = _CapturingOrchestrator(synthesis)
    stub._request = _sf_request(_DA_WITH_REAL_ENTERPRISE_DELTA)
    sf.orchestrator = stub
    sf.llm_service_agent = None

    resp = await _run(sf, stub)

    assert resp.status == "success"
    assert resp.moderator_grades["opt_1"]["arithmetic_consistency"] == "insufficient_data", (
        "malformed impact_estimate must never leave an unverified self-reported "
        "'pass' standing"
    )
