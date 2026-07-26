"""
Phase 15 Stage D — grounding + constraint input contract tests (2026-07-23).

Three tiers:
1. _lookup_kpi_scoped — tenant-safe KPI resolution, mirrors
   test_da_kpi_scoped_lookup.py's fixtures/pattern exactly (same underlying
   risk: multiple tenants share KPI ids under the composite PK).
2. _build_causal_context_section — provenance-aware formatting, pure function.
3. End-to-end prompt injection via the stub-orchestrator pattern (same as
   test_sf_stage_c_context_contract.py): flag off/on, data present/absent,
   provider failure (simulating an unmigrated schema) — all must degrade
   safely, never crash solution generation.
"""
from __future__ import annotations

import logging
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.new.a9_solution_finder_agent import _lookup_kpi_scoped, _build_causal_context_section
from src.agents.models.solution_finder_models import SolutionFinderRequest, TradeOffCriterion
from src.registry.models.kpi_relationship import KPIRelationship
from src.registry.models.assumption import Assumption

_LOGGER = logging.getLogger("test")


# ---------------------------------------------------------------------------
# Tier 1 — tenant-safe KPI resolution (mirrors test_da_kpi_scoped_lookup.py)
# ---------------------------------------------------------------------------

def _kpi(kpi_id, client_id, name="Gross Margin %"):
    return SimpleNamespace(id=kpi_id, client_id=client_id, name=name)


_REGISTRY = [
    _kpi("gross_margin_pct", "lubricants"),
    _kpi("gross_margin_pct", "apex_lubricants"),
    _kpi("gross_margin_pct", "hess"),
    _kpi("net_revenue", "lubricants", name="Net Revenue"),
]


def _patched_provider():
    provider = MagicMock()
    provider.get_all.return_value = _REGISTRY
    factory = MagicMock()
    factory.get_provider.return_value = provider
    return patch("src.registry.factory.RegistryFactory", return_value=factory)


def test_lookup_kpi_scoped_resolves_by_name_within_tenant():
    with _patched_provider():
        result = _lookup_kpi_scoped("Gross Margin %", "hess", _LOGGER)
    assert result is not None
    assert result.client_id == "hess"


def test_lookup_kpi_scoped_refuses_cross_tenant_fallback():
    with _patched_provider():
        # A client with no gross_margin_pct record must NOT get another
        # tenant's same-id KPI back.
        result = _lookup_kpi_scoped("Gross Margin %", "some_other_client", _LOGGER)
    assert result is None


def test_lookup_kpi_scoped_no_client_id_returns_first_candidate():
    with _patched_provider():
        result = _lookup_kpi_scoped("Net Revenue", None, _LOGGER)
    assert result is not None
    assert result.id == "net_revenue"


def test_lookup_kpi_scoped_none_ref_returns_none():
    assert _lookup_kpi_scoped(None, "hess", _LOGGER) is None


def test_lookup_kpi_scoped_handles_registry_failure_gracefully():
    with patch("src.registry.factory.RegistryFactory", side_effect=Exception("registry down")):
        assert _lookup_kpi_scoped("Gross Margin %", "hess", _LOGGER) is None


# ---------------------------------------------------------------------------
# Tier 2 — _build_causal_context_section formatting
# ---------------------------------------------------------------------------

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


def test_empty_inputs_produce_empty_section():
    assert _build_causal_context_section([], []) == ""


def test_template_edge_gets_unconfirmed_caveat():
    section = _build_causal_context_section([_relationship(provenance="template")], [])
    assert "UNCONFIRMED" in section
    assert "do not assert as fact" in section


def test_va_validated_edge_gets_consistent_with_language_never_proved():
    section = _build_causal_context_section([_relationship(provenance="va_validated")], [])
    assert "consistent with" in section
    assert "proved" not in section.lower() or "NEVER 'proved'" in section


def test_mechanism_and_lag_periods_included_when_present():
    section = _build_causal_context_section(
        [_relationship(mechanism="input cost pass-through", lag_periods=2)], []
    )
    assert "input cost pass-through" in section
    assert "~2 months" in section


def test_constraints_section_has_do_not_violate_instruction():
    section = _build_causal_context_section([], [_constraint()])
    assert "KNOWN CONSTRAINTS" in section
    assert "do not propose options that violate these" in section
    assert "Cannot touch pricing on the anchor account" in section


# ---------------------------------------------------------------------------
# Tier 3 — end-to-end prompt injection (stub orchestrator, no live DB/LLM)
# ---------------------------------------------------------------------------

class _CapturingOrchestrator:
    def __init__(self):
        self.captured_prompts: list[str] = []

    async def execute_agent_method(self, agent_name: str, method_name: str, params):
        if agent_name == "A9_LLM_Service_Agent" and method_name == "analyze":
            req = params.get("request")
            self.captured_prompts.append(getattr(req, "content", "") or "")
            return SimpleNamespace(
                status="success", request_id=getattr(req, "request_id", "test"),
                analysis={
                    "options": [{"id": "opt_1", "title": "Renegotiate supplier contracts",
                                 "expected_impact": 0.7, "cost": 0.3, "risk": 0.2}],
                    "recommendation": {"id": "opt_1", "title": "Renegotiate supplier contracts"},
                    "recommendation_rationale": "Because margin pressure is concentrated in one relationship.",
                    "problem_reframe": {"situation": "s", "complication": "c", "question": "q", "key_assumptions": []},
                    "unresolved_tensions": [], "blind_spots": [], "next_steps": [], "cross_review": {},
                },
                model_used="mock-llm", usage={}, confidence=0.9,
            )
        raise AssertionError(f"Unexpected call: {agent_name}.{method_name}")


async def _build_sf(monkeypatch, *, enable_causal_grounding: bool):
    """Construct a fresh, unshared SF agent directly via the classmethod
    (bypasses orchestrator.create_agent_with_dependencies entirely).

    The shared agent-registry singleton can return a CACHED agent instance
    across tests in the same process/session — this bit twice in this file
    alone (a config field varying test-to-test picked up stale state from an
    unrelated prior test). A9_Solution_Finder_Agent.create() always does
    cls(config) with no caching, so this is the actually-robust fix, not just
    a workaround for this file's own internal ordering."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_1234567890")
    from src.agents.new.a9_solution_finder_agent import A9_Solution_Finder_Agent
    sf = await A9_Solution_Finder_Agent.create({
        "enable_llm_debate": True,
        # enable_hybrid_council is required for the Stage 1 parallel-persona
        # path to run at all (see using_hybrid_council gate in
        # recommend_actions) — without it, _run_stage1 never fires and the
        # Stage 1 injection this fix adds is never exercised.
        "enable_hybrid_council": True,
        "enable_causal_grounding": enable_causal_grounding,
    })
    await sf.connect()  # orchestrator=None — deep_analysis_agent/llm_service_agent stay None
    stub = _CapturingOrchestrator()
    sf.orchestrator = stub  # set directly, same pattern as the other SF test files
    return sf, stub


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


async def _run_sf(monkeypatch, *, enable_causal_grounding: bool, client_id: str = "hess"):
    """Convenience wrapper for tests that don't need to mock the registry
    (e.g. the flag-off case, where the lookup path never runs)."""
    sf, stub = await _build_sf(monkeypatch, enable_causal_grounding=enable_causal_grounding)
    resp = await sf.recommend_actions(_sf_request(client_id))
    assert getattr(resp, "status", "error") == "success", getattr(resp, "error_message", None)
    return stub


def _synthesis_prompt(stub) -> str:
    return next(p for p in stub.captured_prompts if "## INPUT DATA" in p)


def _stage1_prompts(stub) -> list[str]:
    return [p for p in stub.captured_prompts if "## PERSONA\n" in p]


@pytest.mark.asyncio
async def test_flag_off_never_injects_causal_context(monkeypatch):
    # Even if the KPI/registry lookups would succeed, the flag gates everything.
    stub = await _run_sf(monkeypatch, enable_causal_grounding=False)
    synth = _synthesis_prompt(stub)
    assert "CAUSAL CONTEXT" not in synth
    assert "KNOWN CONSTRAINTS" not in synth


@pytest.mark.asyncio
async def test_flag_on_but_kpi_unresolvable_degrades_safely(monkeypatch):
    # No registry data seeded for "Gross Margin %" -> _lookup_kpi_scoped returns
    # None -> must proceed without crashing and without fabricating context.
    sf, stub = await _build_sf(monkeypatch, enable_causal_grounding=True)
    with patch("src.registry.factory.RegistryFactory") as mock_factory_cls:
        mock_factory_cls.return_value.get_provider.return_value = None
        resp = await sf.recommend_actions(_sf_request())
    assert resp.status == "success"
    assert "CAUSAL CONTEXT" not in _synthesis_prompt(stub)


@pytest.mark.asyncio
async def test_flag_on_with_provider_exception_degrades_safely(monkeypatch):
    # Simulates the schema not being migrated yet -- the provider call raises,
    # and solution generation must still complete.
    sf, stub = await _build_sf(monkeypatch, enable_causal_grounding=True)
    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR:
        MockKR.return_value.get_relationships_for_kpi = AsyncMock(side_effect=RuntimeError("relation does not exist"))
        resp = await sf.recommend_actions(_sf_request())
    assert resp.status == "success"
    assert "CAUSAL CONTEXT" not in _synthesis_prompt(stub)  # degraded, not crashed


@pytest.mark.asyncio
async def test_flag_on_with_data_injects_provenance_aware_context(monkeypatch):
    sf, stub = await _build_sf(monkeypatch, enable_causal_grounding=True)
    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_relationships_for_kpi = AsyncMock(return_value=[
            _relationship(provenance="va_validated", mechanism="pricing pass-through", lag_periods=1)
        ])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[_constraint()])
        resp = await sf.recommend_actions(_sf_request())
    assert resp.status == "success"

    synth = _synthesis_prompt(stub)
    assert "CAUSAL CONTEXT" in synth
    assert "consistent with" in synth
    assert "KNOWN CONSTRAINTS" in synth
    assert "Cannot touch pricing on the anchor account" in synth


@pytest.mark.asyncio
async def test_stage1_personas_also_receive_causal_context_and_constraints(monkeypatch):
    """The actual regression this fix addresses: causal_context_section was
    originally built AFTER Stage 1 already ran (asyncio.gather completes
    before the section existed), so personas formed hypotheses with zero
    knowledge of known mechanisms or active constraints — synthesis had to
    silently override or contradict them after the fact. Constraints now
    merge into the existing PRINCIPAL CONSTRAINTS mechanism (refinement_
    compact_s1["constraints"]); the causal chain gets its own section."""
    sf, stub = await _build_sf(monkeypatch, enable_causal_grounding=True)
    with _patched_provider_for_e2e(), \
         patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider") as MockKR, \
         patch("src.registry.providers.assumption_provider.AssumptionProvider") as MockAP:
        MockKR.return_value.get_relationships_for_kpi = AsyncMock(return_value=[
            _relationship(provenance="va_validated", mechanism="pricing pass-through", lag_periods=1)
        ])
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=[_constraint()])
        resp = await sf.recommend_actions(_sf_request())
    assert resp.status == "success"

    stage1_prompts = _stage1_prompts(stub)
    assert stage1_prompts, "Stage 1 never ran — enable_hybrid_council gate not satisfied"
    for p in stage1_prompts:
        # Causal chain: its own section, same provenance-aware caveating as synthesis
        assert "pricing pass-through" in p
        assert "consistent with" in p
        # Constraint: merged into the EXISTING PRINCIPAL CONSTRAINTS mechanism,
        # not a second, separately-instructed section
        assert "PRINCIPAL CONSTRAINTS" in p
        assert "Cannot touch pricing on the anchor account" in p


def _patched_provider_for_e2e():
    provider = MagicMock()
    provider.get_all.return_value = [_kpi("gross_margin_pct", "hess", name="Gross Margin %")]
    factory = MagicMock()
    factory.get_provider.return_value = provider
    return patch("src.registry.factory.RegistryFactory", return_value=factory)
