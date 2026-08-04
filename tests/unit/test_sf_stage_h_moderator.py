"""
Phase 15 Stage H — theory-guided moderator tests (2026-08-04).

The moderator replaces the single-author simulated firm-vs-firm cross-review
with an adjudication duty graded against ground truth: constraint survival,
causal-edge grounding, impact arithmetic, and critic-finding response. It is
the NEW arm of the PM-2 A/B — the baseline (simulated cross-review) prompt
must remain byte-for-byte untouched while the A/B is open, so half these
tests are baseline-regression assertions, not feature assertions.

PM requirements under test here:
- PM-1: grades state their denominator (N constraints / N edges + provenance
  mix), and a zero register renders as counts of 0 — never silently omitted.
- PM-3: the active protocol/flag state is logged at run start.
- PM-7: an "enterprise" scope claim carrying a named segment label is a
  self-contradiction — parser resets scope to None, call site emits an
  impact_scope_contradiction audit event.
- PM-9: unknown moderator_protocol values fall back to 'judge', logged.

Uses the same direct-construction + capturing-stub-orchestrator pattern as
the Stage D/E test files (A9_Solution_Finder_Agent.create(), enable_hybrid_
council=True so Stage 1 actually runs).
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.models.solution_finder_models import SolutionFinderRequest, TradeOffCriterion
from src.agents.new.a9_solution_finder_agent import _parse_impact_estimate, _scope_contradiction
from src.registry.models.kpi_relationship import KPIRelationship
from src.registry.models.assumption import Assumption


def _kpi(kpi_id, client_id, name="Gross Margin %"):
    return SimpleNamespace(id=kpi_id, client_id=client_id, name=name)


def _relationship(**overrides):
    base = dict(
        kpi_id="base_oil_cost", related_kpi_id="gross_margin_pct", client_id="lubricants",
        relationship_type="cost_revenue", conflict_direction="diverging",
    )
    base.update(overrides)
    return KPIRelationship(**base)


def _constraint(**overrides):
    base = dict(client_id="lubricants", scope="gross_margin_pct", record_type="constraint",
                text="Cannot raise list prices on anchor accounts mid-quarter", source="manual")
    base.update(overrides)
    return Assumption(**base)


def _patched_provider_for_e2e():
    provider = MagicMock()
    provider.get_all.return_value = [_kpi("gross_margin_pct", "lubricants", name="Gross Margin %")]
    factory = MagicMock()
    factory.get_provider.return_value = provider
    return patch("src.registry.factory.RegistryFactory", return_value=factory)


class _CapturingOrchestrator:
    """Stub handling Stage 1 (_s1_), critic (_critic), and synthesis calls,
    capturing every prompt. The synthesis analysis payload is injectable so
    tests can drive moderator_grades / contradictory scopes through parsing."""

    def __init__(self, synthesis_analysis: dict | None = None):
        self.captured_prompts: list[str] = []
        self._synthesis_analysis = synthesis_analysis

    async def execute_agent_method(self, agent_name: str, method_name: str, params):
        if agent_name == "A9_LLM_Service_Agent" and method_name == "analyze":
            req = params.get("request")
            self.captured_prompts.append(getattr(req, "content", "") or "")
            req_id = getattr(req, "request_id", "")

            if "_critic" in req_id:
                return SimpleNamespace(
                    status="success", request_id=req_id,
                    analysis={"findings": [{"persona_id": "mckinsey",
                                            "concern": "Repricing may violate the anchor-account price lock",
                                            "affected_kpi": "gross_margin_pct", "severity": "high"}]},
                    model_used="mock-llm", usage={}, confidence=0.9,
                )
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
            analysis = self._synthesis_analysis or {
                "problem_reframe": {"situation": "s", "complication": "c", "question": "q",
                                    "key_assumptions": []},
                "options": [
                    {"id": "opt_1", "title": "Reprice at renewal", "expected_impact": 0.7,
                     "cost": 0.3, "risk": 0.2},
                ],
                "recommendation": {"id": "opt_1", "title": "Reprice at renewal"},
                "recommendation_rationale": "Renewal boundary avoids the mid-quarter price lock.",
                "unresolved_tensions": [], "blind_spots": [], "next_steps": [],
                "moderator_grades": {
                    "opt_1": {"constraint_survival": "pass",
                              "causal_grounding": "base_oil_cost -> gross_margin_pct",
                              "arithmetic_consistency": "pass",
                              "critic_findings_response": [
                                  {"finding": "price lock", "disposition": "answered"}],
                              "grade_rationale": "Survives the mid-quarter price-lock constraint."}
                },
            }
            return SimpleNamespace(status="success", request_id=req_id, analysis=analysis,
                                   model_used="mock-llm",
                                   usage={"prompt_tokens": 100, "completion_tokens": 50},
                                   confidence=0.9)
        raise AssertionError(f"Unexpected call: {agent_name}.{method_name}")


async def _build_sf(monkeypatch, *, theory_moderator: bool, causal_grounding: bool = True,
                    critic_pass: bool = False, moderator_protocol: str = "judge"):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    from src.agents.new.a9_solution_finder_agent import A9_Solution_Finder_Agent
    sf = await A9_Solution_Finder_Agent.create({
        "enable_llm_debate": True,
        "enable_hybrid_council": True,  # required for Stage 1 to run at all
        "enable_causal_grounding": causal_grounding,
        "enable_critic_pass": critic_pass,
        "enable_theory_moderator": theory_moderator,
        "moderator_protocol": moderator_protocol,
    })
    await sf.connect()
    return sf


def _sf_request(client_id: str = "lubricants") -> SolutionFinderRequest:
    return SolutionFinderRequest(
        request_id=str(uuid.uuid4()), principal_id="cfo_001",
        problem_statement="Gross margin declined vs prior year",
        deep_analysis_output={"plan": {"kpi_name": "Gross Margin %", "client_id": client_id}},
        client_id=client_id,
        evaluation_criteria=[TradeOffCriterion(name="impact", weight=0.5),
                             TradeOffCriterion(name="cost", weight=0.3),
                             TradeOffCriterion(name="risk", weight=0.2)],
    )


def _synthesis_prompt(stub) -> str:
    return next(p for p in stub.captured_prompts if "## INPUT DATA" in p)


def _providers(relationships, constraints):
    kr = patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider")
    ap = patch("src.registry.providers.assumption_provider.AssumptionProvider")
    return kr, ap, relationships, constraints


async def _run(sf, stub, relationships, constraints):
    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_relationships_for_kpi = AsyncMock(return_value=relationships)
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=constraints)
        return await sf.recommend_actions(_sf_request())


# ---------------------------------------------------------------------------
# Baseline-arm regression (PM-2: the A/B baseline must not drift)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_flag_off_keeps_simulated_cross_review_baseline(monkeypatch):
    sf = await _build_sf(monkeypatch, theory_moderator=False)
    stub = _CapturingOrchestrator()
    sf.orchestrator = stub
    resp = await _run(sf, stub, [_relationship()], [_constraint()])
    prompt = _synthesis_prompt(stub)
    assert resp.status == "success"
    assert "STAGE 2 - CROSS-REVIEW" in prompt          # simulated duty intact
    assert '"cross_review": {' in prompt                # template asks for it
    assert "MODERATOR DUTY" not in prompt
    assert "moderator_grades" not in prompt
    assert resp.moderator_grades is None


@pytest.mark.asyncio
async def test_flag_on_without_causal_grounding_stays_on_baseline(monkeypatch):
    # Same dependency rule as the critic: no register, nothing to grade against.
    sf = await _build_sf(monkeypatch, theory_moderator=True, causal_grounding=False)
    stub = _CapturingOrchestrator()
    sf.orchestrator = stub
    resp = await _run(sf, stub, [], [])
    prompt = _synthesis_prompt(stub)
    assert resp.status == "success"
    assert "MODERATOR DUTY" not in prompt
    assert "STAGE 2 - CROSS-REVIEW" in prompt


# ---------------------------------------------------------------------------
# Moderator arm
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_moderator_prompt_carries_duty_denominator_and_scope(monkeypatch):
    sf = await _build_sf(monkeypatch, theory_moderator=True, critic_pass=True)
    stub = _CapturingOrchestrator()
    sf.orchestrator = stub
    resp = await _run(sf, stub, [_relationship(provenance="va_validated")], [_constraint()])
    prompt = _synthesis_prompt(stub)
    assert resp.status == "success"
    # Duty replaces simulation
    assert "MODERATOR DUTY" in prompt
    assert "STAGE 2 - CROSS-REVIEW" not in prompt
    assert "Do NOT include a 'cross_review' field" in prompt
    # PM-1: the denominator is stated, with provenance mix
    assert "Active constraints: 1" in prompt
    assert "Causal edges: 1" in prompt
    assert "va_validated: 1" in prompt
    # Grades schema requested
    assert '"moderator_grades"' in prompt
    assert "constraint_survival" in prompt
    # Scope elicitation lives in this arm only
    assert "IMPACT SCOPE (required in this mode)" in prompt
    # Calibration guardrail (theory §4)
    assert "never 'proved'" in prompt.lower() or "never ‘proved’" in prompt.lower() \
        or "never 'proved'".replace("'", "") in prompt.lower().replace("'", "")


@pytest.mark.asyncio
async def test_moderator_zero_register_states_zero_counts_not_silence(monkeypatch):
    # PM-1: a thin register must be visible as 0s with the insufficient_data
    # rule in force — never confident grades over nothing.
    sf = await _build_sf(monkeypatch, theory_moderator=True)
    stub = _CapturingOrchestrator()
    sf.orchestrator = stub
    resp = await _run(sf, stub, [], [])
    prompt = _synthesis_prompt(stub)
    assert resp.status == "success"
    assert "Active constraints: 0" in prompt
    assert "Causal edges: 0 (by provenance: none)" in prompt
    assert "NEVER 'pass'" in prompt
    assert "insufficient_data" in prompt


@pytest.mark.asyncio
async def test_moderator_grades_parsed_into_response_and_ledger_labeled(monkeypatch):
    sf = await _build_sf(monkeypatch, theory_moderator=True)
    stub = _CapturingOrchestrator()
    sf.orchestrator = stub
    resp = await _run(sf, stub, [_relationship()], [_constraint()])
    assert resp.status == "success"
    assert resp.moderator_grades is not None
    assert resp.moderator_grades["opt_1"]["constraint_survival"] == "pass"
    assert resp.cross_review is None or resp.cross_review == {}
    # Ledger label distinguishes the arm that paid (stub supplies usage on the
    # synthesis response only, so exactly one ledger row exists).
    tu = [e for e in (resp.audit_log or []) if e.get("event") == "token_usage"]
    assert tu, "token_usage event missing"
    assert [r["call"] for r in tu[0]["by_call"]] == ["moderator"]


@pytest.mark.asyncio
async def test_unknown_protocol_falls_back_to_judge(monkeypatch):
    # PM-9: 'integrator' is designed but gated; a typo must not change behavior.
    sf = await _build_sf(monkeypatch, theory_moderator=True, moderator_protocol="integrator")
    stub = _CapturingOrchestrator()
    sf.orchestrator = stub
    resp = await _run(sf, stub, [_relationship()], [_constraint()])
    assert resp.status == "success"
    assert "MODERATOR DUTY" in _synthesis_prompt(stub)


@pytest.mark.asyncio
async def test_contradictory_scope_resets_to_none_and_audits(monkeypatch):
    # PM-7 end-to-end: "enterprise" + a named segment label is self-contradictory.
    synthesis_analysis = {
        "options": [
            {"id": "opt_1", "title": "t", "expected_impact": 0.7, "cost": 0.3, "risk": 0.2,
             "impact_estimate": {"metric": "Gross Margin %", "unit": "pp",
                                 "recovery_range": {"low": 18.5, "high": 32.0},
                                 "basis": "sized from Chain A's -43.24pp change point",
                                 "scope": "enterprise",
                                 "scope_label": "National Auto Parts Chain A"}},
        ],
        "recommendation": {"id": "opt_1", "title": "t"},
        "recommendation_rationale": "r",
        "unresolved_tensions": [], "blind_spots": [], "next_steps": [],
        "moderator_grades": {"opt_1": {"constraint_survival": "pass"}},
    }
    sf = await _build_sf(monkeypatch, theory_moderator=True)
    stub = _CapturingOrchestrator(synthesis_analysis=synthesis_analysis)
    sf.orchestrator = stub
    resp = await _run(sf, stub, [_relationship()], [_constraint()])
    assert resp.status == "success"
    opt = resp.options_ranked[0]
    assert opt.impact_estimate is not None
    assert opt.impact_estimate.scope is None                     # claim withdrawn
    assert opt.impact_estimate.scope_label == "National Auto Parts Chain A"  # info kept
    events = [e for e in (resp.audit_log or []) if e.get("event") == "impact_scope_contradiction"]
    assert len(events) == 1
    assert events[0]["option_id"] == "opt_1"


# ---------------------------------------------------------------------------
# PM-7 pure-function truth table
# ---------------------------------------------------------------------------

def test_scope_contradiction_truth_table():
    assert _scope_contradiction({"scope": "enterprise", "scope_label": "Chain A"}) is True
    assert _scope_contradiction({"scope": "enterprise", "scope_label": None}) is False
    assert _scope_contradiction({"scope": "segment", "scope_label": "Chain A"}) is False
    assert _scope_contradiction({"scope": "segment", "scope_label": None}) is False
    assert _scope_contradiction(None) is False
    assert _scope_contradiction("enterprise") is False


def test_parser_normalises_contradiction_but_keeps_label():
    ie = _parse_impact_estimate({"metric": "GM%", "unit": "pp",
                                 "recovery_range": {"low": 1.0, "high": 2.0},
                                 "scope": "enterprise", "scope_label": "Chain A"})
    assert ie is not None
    assert ie.scope is None
    assert ie.scope_label == "Chain A"


def test_parser_keeps_consistent_scopes():
    seg = _parse_impact_estimate({"metric": "GM%", "unit": "pp",
                                  "recovery_range": {"low": 1.0, "high": 2.0},
                                  "scope": "segment", "scope_label": "Chain A"})
    assert seg is not None and seg.scope == "segment"
    ent = _parse_impact_estimate({"metric": "GM%", "unit": "pp",
                                  "recovery_range": {"low": 1.0, "high": 2.0},
                                  "scope": "enterprise", "scope_label": None})
    assert ent is not None and ent.scope == "enterprise"
