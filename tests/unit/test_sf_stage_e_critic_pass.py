"""
Phase 15 Stage E — critic pass tests (2026-07-26).

generate -> critique-against-theory -> synthesize: after Stage 1 completes,
a critic call traces each persona's proposed lever through the causal graph
(kpi_relationships + assumptions, same data Stage D fetches) and flags
grounded side-effects/violated constraints BEFORE synthesis runs, so
synthesis can address them at the source instead of silently overriding a
persona's proposal after the fact — same principle as the Stage D
constraint-timing fix.

Gated on BOTH enable_critic_pass and enable_causal_grounding (a critic with
no causal graph has nothing to critique), and on there actually being causal
data to critique against. Uses the same direct-construction pattern as the
Stage D test file (A9_Solution_Finder_Agent.create()) to avoid the shared
agent-registry singleton returning a cached instance across tests.
"""
from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.models.solution_finder_models import SolutionFinderRequest, TradeOffCriterion
from src.registry.models.kpi_relationship import KPIRelationship
from src.registry.models.assumption import Assumption


def _kpi(kpi_id, client_id, name="Gross Margin %"):
    return SimpleNamespace(id=kpi_id, client_id=client_id, name=name)


def _relationship(**overrides):
    base = dict(
        kpi_id="net_revenue", related_kpi_id="cogs", client_id="hess",
        relationship_type="cost_revenue", conflict_direction="diverging",
    )
    base.update(overrides)
    return KPIRelationship(**base)


def _constraint(**overrides):
    base = dict(client_id="hess", scope="net_revenue", record_type="constraint",
                text="Cannot touch pricing on the anchor account", source="sf_hitl_rejection")
    base.update(overrides)
    return Assumption(**base)


def _patched_provider_for_e2e():
    provider = MagicMock()
    provider.get_all.return_value = [_kpi("gross_margin_pct", "hess", name="Gross Margin %")]
    factory = MagicMock()
    factory.get_provider.return_value = provider
    return patch("src.registry.factory.RegistryFactory", return_value=factory)


class _CapturingOrchestrator:
    """Stub orchestrator handling Stage 1 (_s1_), critic (_critic), and
    synthesis calls distinctly, capturing every prompt sent."""

    def __init__(self, critic_findings: list | None = None):
        self.captured_prompts: list[str] = []
        self._critic_findings = critic_findings if critic_findings is not None else []

    async def execute_agent_method(self, agent_name: str, method_name: str, params):
        if agent_name == "A9_LLM_Service_Agent" and method_name == "analyze":
            req = params.get("request")
            self.captured_prompts.append(getattr(req, "content", "") or "")
            req_id = getattr(req, "request_id", "")

            if "_critic" in req_id:
                return SimpleNamespace(
                    status="success", request_id=req_id,
                    analysis={"findings": self._critic_findings},
                    model_used="mock-llm", usage={}, confidence=0.9,
                )
            if "_s1_" in req_id:
                analysis = {
                    "persona_id": "mckinsey", "framework": "MECE", "hypothesis": "h",
                    "key_evidence": ["e1", "e2", "e3"], "recommended_focus": "North Region",
                    "conviction": "High",
                    "proposed_option": {
                        "title": "Renegotiate supplier contracts",
                        "mechanism": "Direct cost reduction via supplier renegotiation",
                        "description": "d", "time_horizon": "0-90 days",
                        "impact_estimate": {"metric": "Gross Margin", "unit": "%",
                                             "recovery_range": {"low": 1.0, "high": 2.0}, "basis": "..."},
                        "cost_signal": "Medium", "risk_signal": "Low",
                    },
                }
                return SimpleNamespace(status="success", request_id=req_id, analysis=analysis,
                                        model_used="mock-llm", usage={}, confidence=0.9)
            # Synthesis
            analysis = {
                "problem_reframe": {"situation": "s", "complication": "c", "question": "q", "key_assumptions": []},
                "options": [
                    {"id": "opt_1", "title": "Renegotiate supplier contracts", "expected_impact": 0.7,
                     "cost": 0.3, "risk": 0.2, "flagged_side_effects": ["May strain the same supplier relationship a separate delivery-reliability KPI depends on"]},
                ],
                "recommendation": {"id": "opt_1", "title": "Renegotiate supplier contracts"},
                "recommendation_rationale": "Because margin pressure is concentrated in one relationship.",
                "unresolved_tensions": [], "blind_spots": [], "next_steps": [], "cross_review": {},
            }
            return SimpleNamespace(status="success", request_id=req_id, analysis=analysis,
                                    model_used="mock-llm", usage={}, confidence=0.9)
        raise AssertionError(f"Unexpected call: {agent_name}.{method_name}")


async def _build_sf(monkeypatch, *, enable_critic_pass: bool, enable_causal_grounding: bool = True):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    from src.agents.new.a9_solution_finder_agent import A9_Solution_Finder_Agent
    sf = await A9_Solution_Finder_Agent.create({
        "enable_llm_debate": True,
        "enable_hybrid_council": True,  # required for Stage 1 to run at all
        "enable_causal_grounding": enable_causal_grounding,
        "enable_critic_pass": enable_critic_pass,
    })
    await sf.connect()
    return sf


def _sf_request(client_id: str = "hess") -> SolutionFinderRequest:
    return SolutionFinderRequest(
        request_id=str(uuid.uuid4()), principal_id="cfo_001",
        problem_statement="Gross margin declined vs plan",
        deep_analysis_output={"plan": {"kpi_name": "Gross Margin %", "client_id": client_id}},
        client_id=client_id,
        evaluation_criteria=[TradeOffCriterion(name="impact", weight=0.5),
                              TradeOffCriterion(name="cost", weight=0.3),
                              TradeOffCriterion(name="risk", weight=0.2)],
    )


def _synthesis_prompt(stub) -> str:
    return next(p for p in stub.captured_prompts if "## INPUT DATA" in p)


def _critic_prompt_sent(stub) -> bool:
    return any("PROPOSED OPTIONS (from persona hypotheses)" in p for p in stub.captured_prompts)


@pytest.mark.asyncio
async def test_critic_pass_off_never_calls_critic_even_with_data(monkeypatch):
    sf = await _build_sf(monkeypatch, enable_critic_pass=False)
    stub = _CapturingOrchestrator(critic_findings=[{"persona_id": "mckinsey", "concern": "x"}])
    sf.orchestrator = stub
    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_relationships_for_kpi = AsyncMock(return_value=[_relationship(provenance="va_validated")])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[])
        resp = await sf.recommend_actions(_sf_request())
    assert resp.status == "success"
    assert not _critic_prompt_sent(stub)
    assert "CRITIC FINDINGS" not in _synthesis_prompt(stub)


@pytest.mark.asyncio
async def test_critic_pass_on_but_causal_grounding_off_never_calls_critic(monkeypatch):
    # Dependency check: critic pass requires enable_causal_grounding too.
    sf = await _build_sf(monkeypatch, enable_critic_pass=True, enable_causal_grounding=False)
    stub = _CapturingOrchestrator(critic_findings=[{"persona_id": "mckinsey", "concern": "x"}])
    sf.orchestrator = stub
    resp = await sf.recommend_actions(_sf_request())
    assert resp.status == "success"
    assert not _critic_prompt_sent(stub)


@pytest.mark.asyncio
async def test_critic_pass_skipped_when_no_causal_data_to_critique(monkeypatch):
    # Both flags on, but the graph is empty -- nothing to critique against.
    sf = await _build_sf(monkeypatch, enable_critic_pass=True, enable_causal_grounding=True)
    stub = _CapturingOrchestrator(critic_findings=[{"persona_id": "mckinsey", "concern": "x"}])
    sf.orchestrator = stub
    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_relationships_for_kpi = AsyncMock(return_value=[])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[])
        resp = await sf.recommend_actions(_sf_request())
    assert resp.status == "success"
    assert not _critic_prompt_sent(stub)


@pytest.mark.asyncio
async def test_critic_pass_fires_and_findings_reach_synthesis(monkeypatch):
    sf = await _build_sf(monkeypatch, enable_critic_pass=True, enable_causal_grounding=True)
    stub = _CapturingOrchestrator(critic_findings=[{
        "persona_id": "mckinsey",
        "concern": "Renegotiating this supplier may damage on-time delivery performance",
        "affected_kpi": "otd_pct",
        "severity": "moderate",
    }])
    sf.orchestrator = stub
    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_relationships_for_kpi = AsyncMock(return_value=[
            _relationship(provenance="va_validated", mechanism="supplier lead time", causal_rung="intervention_tested")
        ])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[_constraint()])
        resp = await sf.recommend_actions(_sf_request())
    assert resp.status == "success"

    assert _critic_prompt_sent(stub), "critic call never fired"
    critic_prompt = next(p for p in stub.captured_prompts if "PROPOSED OPTIONS" in p)
    # Critic sees the persona's actual proposal and the causal/constraint context
    assert "Renegotiate supplier contracts" in critic_prompt
    assert "supplier lead time" in critic_prompt
    assert "Cannot touch pricing on the anchor account" in critic_prompt

    synth = _synthesis_prompt(stub)
    assert "CRITIC FINDINGS" in synth
    assert "damage on-time delivery performance" in synth
    assert "otd_pct" in synth
    assert "flagged_side_effects" in synth  # instruction to populate the field, not drop the finding

    # And the final option genuinely carries the side effect (from the mocked synthesis response)
    assert resp.options_ranked[0].flagged_side_effects


@pytest.mark.asyncio
async def test_critic_pass_finds_nothing_produces_no_section(monkeypatch):
    # A critic call that legitimately finds no concern must not fabricate one.
    sf = await _build_sf(monkeypatch, enable_critic_pass=True, enable_causal_grounding=True)
    stub = _CapturingOrchestrator(critic_findings=[])
    sf.orchestrator = stub
    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_relationships_for_kpi = AsyncMock(return_value=[_relationship(provenance="va_validated")])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[])
        resp = await sf.recommend_actions(_sf_request())
    assert resp.status == "success"
    assert _critic_prompt_sent(stub)  # it DID run
    assert "CRITIC FINDINGS" not in _synthesis_prompt(stub)  # but found nothing worth flagging


@pytest.mark.asyncio
async def test_critic_pass_call_failure_degrades_safely(monkeypatch):
    class _FailingOrchestrator(_CapturingOrchestrator):
        async def execute_agent_method(self, agent_name, method_name, params):
            req = params.get("request")
            if "_critic" in getattr(req, "request_id", ""):
                raise RuntimeError("LLM service unavailable")
            return await super().execute_agent_method(agent_name, method_name, params)

    sf = await _build_sf(monkeypatch, enable_critic_pass=True, enable_causal_grounding=True)
    stub = _FailingOrchestrator()
    sf.orchestrator = stub
    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_relationships_for_kpi = AsyncMock(return_value=[_relationship(provenance="va_validated")])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[])
        resp = await sf.recommend_actions(_sf_request())
    # Must still complete successfully -- a critic failure must never break solution generation
    assert resp.status == "success"
    assert "CRITIC FINDINGS" not in _synthesis_prompt(stub)
