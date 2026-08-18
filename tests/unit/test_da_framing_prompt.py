"""
Phase 19, Slice 2 — framing prompt builder tests (2026-08-18).

`_build_framing_prompt` is unwired at this point in the plan — nothing calls
it yet (that's Slice 4). This file exercises it directly, the same isolated-
method style as test_da_scqa_failure_no_fallback.py (lightweight
object.__new__ stub, no orchestrator/DPA/LLM infrastructure) and
test_sf_stage_d_causal_grounding.py (RegistryFactory / KPIRelationshipProvider
/ AssumptionProvider mocking pattern).

ONE outer try/except, deliberately, mirroring SF's causal-grounding block —
see the method's own docstring. That means a provider exception ANYWHERE in
the body returns None for the WHOLE prompt, not a partially-populated one.
"""
from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
from src.registry.models.kpi_relationship import KPIRelationship
from src.registry.models.assumption import Assumption

_LOGGER = logging.getLogger("test.framing_prompt")


def _make_da_stub() -> A9_Deep_Analysis_Agent:
    stub = object.__new__(A9_Deep_Analysis_Agent)
    stub.logger = _LOGGER
    return stub


def _kpi(kpi_id, client_id, name=None, owner_role=None):
    return SimpleNamespace(id=kpi_id, client_id=client_id, name=name or kpi_id, owner_role=owner_role)


def _da_output(kpi_name="gross_margin_pct", client_id="hess", market_conflict=None):
    out = {"plan": {"kpi_name": kpi_name, "client_id": client_id}}
    if market_conflict is not None:
        out["market_conflict"] = market_conflict
    return out


def _relationship(**overrides):
    base = dict(
        kpi_id="gross_margin_pct", related_kpi_id="cogs", client_id="hess",
        relationship_type="cost_revenue", conflict_direction="diverging",
    )
    base.update(overrides)
    return KPIRelationship(**base)


def _registry_patch(records):
    provider = MagicMock()
    provider.get_all.return_value = records
    factory = MagicMock()
    factory.get_provider.return_value = provider
    return patch("src.registry.factory.RegistryFactory", return_value=factory)


class _DualPatch:
    """Small helper so tests can `with _providers(...) as (MockKR, MockAP):`
    without repeating the two-patch dance every time."""
    def __init__(self, **kwargs):
        self._kr_patch = patch("src.registry.providers.kpi_relationship_provider.KPIRelationshipProvider")
        self._ap_patch = patch("src.registry.providers.assumption_provider.AssumptionProvider")
        self._neighbourhood = kwargs.get("neighbourhood", [])
        self._neighbourhood_side_effect = kwargs.get("neighbourhood_side_effect")
        self._constraints = kwargs.get("constraints", [])
        self._prior_framing = kwargs.get("prior_framing", None)

    def __enter__(self):
        MockKR = self._kr_patch.start()
        MockAP = self._ap_patch.start()
        if self._neighbourhood_side_effect is not None:
            MockKR.return_value.get_causal_neighbourhood = AsyncMock(side_effect=self._neighbourhood_side_effect)
        else:
            MockKR.return_value.get_causal_neighbourhood = AsyncMock(return_value=self._neighbourhood)
        MockAP.return_value.get_active_constraints = AsyncMock(return_value=self._constraints)
        MockAP.return_value.get_active_framing = AsyncMock(return_value=self._prior_framing)
        return MockKR, MockAP

    def __exit__(self, *exc):
        self._kr_patch.stop()
        self._ap_patch.stop()


def _providers(**kwargs) -> _DualPatch:
    return _DualPatch(**kwargs)


# ---------------------------------------------------------------------------
# Missing inputs — must return None, never raise
# ---------------------------------------------------------------------------

class TestMissingInputs:
    @pytest.mark.asyncio
    async def test_no_client_id_returns_none(self):
        da = _make_da_stub()
        result = await da._build_framing_prompt({"plan": {"kpi_name": "x"}}, {})
        assert result is None

    @pytest.mark.asyncio
    async def test_no_kpi_ref_returns_none(self):
        da = _make_da_stub()
        result = await da._build_framing_prompt({"plan": {"client_id": "hess"}}, {})
        assert result is None

    @pytest.mark.asyncio
    async def test_cross_tenant_kpi_returns_none(self):
        # KPI exists, but only for a different client_id — _lookup_kpi_scoped
        # must refuse the cross-tenant fallback, and the whole prompt is None.
        da = _make_da_stub()
        with _registry_patch([_kpi("gross_margin_pct", "apex_lubricants")]):
            result = await da._build_framing_prompt(_da_output(client_id="hess"), {})
        assert result is None


# ---------------------------------------------------------------------------
# Causal-graph alternatives
# ---------------------------------------------------------------------------

class TestCausalGraphAlternatives:
    @pytest.mark.asyncio
    async def test_empty_graph_produces_empty_alternatives_never_fabricated(self):
        da = _make_da_stub()
        with _registry_patch([_kpi("gross_margin_pct", "hess")]), _providers(neighbourhood=[]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        assert result.alternatives == []

    @pytest.mark.asyncio
    async def test_provider_exception_returns_none_for_whole_prompt(self):
        """Deliberate: ONE outer try/except, no partial degradation — see the
        method's own docstring. A provider exception anywhere aborts the
        whole build, it does not silently drop just the causal alternatives."""
        da = _make_da_stub()
        with _registry_patch([_kpi("gross_margin_pct", "hess")]), \
             _providers(neighbourhood_side_effect=RuntimeError("relation does not exist")):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is None

    @pytest.mark.asyncio
    async def test_mechanism_none_sets_direction_unconfirmed_and_caveat(self):
        da = _make_da_stub()
        edge = _relationship(mechanism=None, provenance="template")
        with _registry_patch([_kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess")]), \
             _providers(neighbourhood=[(edge, 1)]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        assert len(result.alternatives) == 1
        alt = result.alternatives[0]
        assert alt.direction_confirmed is False
        assert alt.mechanism is None
        assert any("mechanism" in c.lower() for c in alt.evidence_caveats)

    @pytest.mark.asyncio
    async def test_two_hop_edge_preserves_hop_distance_not_flattened(self):
        da = _make_da_stub()
        # base_oil_cost -> cogs (hop 1, already visited via kpi_id="cogs")
        # cogs -> gross_margin_pct would be hop... construct directly as a
        # 2-hop return from the provider (mirrors what get_causal_neighbourhood
        # itself would produce for a 2-hop BFS).
        hop1 = _relationship(kpi_id="gross_margin_pct", related_kpi_id="cogs", provenance="confirmed")
        hop2 = _relationship(kpi_id="cogs", related_kpi_id="base_oil_cost", provenance="template", mechanism="cost pass-through")
        with _registry_patch([
            _kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess"), _kpi("base_oil_cost", "hess"),
        ]), _providers(neighbourhood=[(hop1, 1), (hop2, 2)]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        by_kpi = {a.kpi_id: a for a in result.alternatives}
        assert by_kpi["cogs"].hops == 1
        assert by_kpi["base_oil_cost"].hops == 2  # NOT flattened to 1

    @pytest.mark.asyncio
    async def test_cross_link_edge_introduces_no_new_alternative(self):
        """An edge connecting two ALREADY-visited nodes is real evidence but
        not a distinct candidate objective — must not raise, must not add a
        phantom alternative with kpi_id=None."""
        da = _make_da_stub()
        hop1 = _relationship(kpi_id="gross_margin_pct", related_kpi_id="cogs")
        cross_link = _relationship(kpi_id="gross_margin_pct", related_kpi_id="cogs", relationship_type="custom")
        with _registry_patch([_kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess")]), \
             _providers(neighbourhood=[(hop1, 1), (cross_link, 1)]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        assert len(result.alternatives) == 1  # de-duplicated, not two

    @pytest.mark.asyncio
    async def test_every_provenance_value_maps_to_nonempty_human_copy(self):
        da = _make_da_stub()
        for provenance in ("template", "confirmed", "hitl_proposed", "va_validated"):
            edge = _relationship(provenance=provenance)
            with _registry_patch([_kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess")]), \
                 _providers(neighbourhood=[(edge, 1)]):
                result = await da._build_framing_prompt(_da_output(), {})
            assert result is not None
            assert result.alternatives[0].provenance_caveat, f"no caveat text for provenance={provenance}"

    @pytest.mark.asyncio
    async def test_no_string_from_sf_provenance_caveat_appears_in_output(self):
        """Pins new-copy-not-old: this must be NEW human-facing text, not
        a9_solution_finder_agent.py's _PROVENANCE_CAVEAT (LLM-instruction
        language, e.g. 'do not assert as fact')."""
        from src.agents.new.a9_solution_finder_agent import _PROVENANCE_CAVEAT as SF_CAVEAT
        da = _make_da_stub()
        edge = _relationship(provenance="template")
        with _registry_patch([_kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess")]), \
             _providers(neighbourhood=[(edge, 1)]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        caveat = result.alternatives[0].provenance_caveat
        assert caveat != SF_CAVEAT["template"]
        assert "do not assert as fact" not in caveat


# ---------------------------------------------------------------------------
# Market-signal alternative (Decision #12)
# ---------------------------------------------------------------------------

class TestMarketSignalAlternative:
    @pytest.mark.asyncio
    async def test_detected_conflict_with_summary_appends_market_alternative(self):
        da = _make_da_stub()
        conflict = {"detected": True, "type": "tailwind_vs_problem", "confidence": 0.72,
                    "summary": "Base oil spot prices have fallen 8% this quarter, contrary to the internal COGS increase."}
        with _registry_patch([_kpi("gross_margin_pct", "hess")]), _providers(neighbourhood=[]):
            result = await da._build_framing_prompt(_da_output(market_conflict=conflict), {})
        assert result is not None
        market_alts = [a for a in result.alternatives if a.source == "market_signal"]
        assert len(market_alts) == 1
        assert market_alts[0].objective_text == conflict["summary"]
        assert market_alts[0].confidence == "72%"
        assert market_alts[0].kpi_id is None
        assert market_alts[0].mechanism is None

    @pytest.mark.asyncio
    async def test_causal_and_market_alternatives_coexist_undeduplicated(self):
        da = _make_da_stub()
        edge = _relationship(provenance="confirmed")
        conflict = {"detected": True, "summary": "External signal contradicts the internal read."}
        with _registry_patch([_kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess")]), \
             _providers(neighbourhood=[(edge, 1)]):
            result = await da._build_framing_prompt(_da_output(market_conflict=conflict), {})
        assert result is not None
        sources = sorted(a.source for a in result.alternatives)
        assert sources == ["causal_graph", "market_signal"]

    @pytest.mark.asyncio
    async def test_conflict_absent_produces_zero_market_alternatives(self):
        da = _make_da_stub()
        with _registry_patch([_kpi("gross_margin_pct", "hess")]), _providers(neighbourhood=[]):
            result = await da._build_framing_prompt(_da_output(market_conflict=None), {})
        assert result is not None
        assert [a for a in result.alternatives if a.source == "market_signal"] == []

    @pytest.mark.asyncio
    async def test_conflict_detected_false_produces_zero_market_alternatives(self):
        da = _make_da_stub()
        conflict = {"detected": False, "summary": "should be ignored"}
        with _registry_patch([_kpi("gross_margin_pct", "hess")]), _providers(neighbourhood=[]):
            result = await da._build_framing_prompt(_da_output(market_conflict=conflict), {})
        assert result is not None
        assert [a for a in result.alternatives if a.source == "market_signal"] == []

    @pytest.mark.asyncio
    async def test_malformed_conflict_detected_true_but_no_summary_is_skipped_not_fabricated(self):
        da = _make_da_stub()
        conflict = {"detected": True, "summary": ""}  # malformed — detected=True but nothing to say
        with _registry_patch([_kpi("gross_margin_pct", "hess")]), _providers(neighbourhood=[]):
            result = await da._build_framing_prompt(_da_output(market_conflict=conflict), {})
        assert result is not None
        assert [a for a in result.alternatives if a.source == "market_signal"] == []

    @pytest.mark.asyncio
    async def test_conflict_not_a_dict_does_not_raise(self):
        da = _make_da_stub()
        with _registry_patch([_kpi("gross_margin_pct", "hess")]), _providers(neighbourhood=[]):
            result = await da._build_framing_prompt(_da_output(market_conflict="not a dict"), {})
        assert result is not None
        assert [a for a in result.alternatives if a.source == "market_signal"] == []


# ---------------------------------------------------------------------------
# Constraints, prior frame, owner attribution
# ---------------------------------------------------------------------------

class TestConstraintsAndPriorFrame:
    @pytest.mark.asyncio
    async def test_active_constraints_carried_through_as_constraint_items(self):
        da = _make_da_stub()
        constraint = Assumption(
            client_id="hess", scope="gross_margin_pct", record_type="constraint",
            text="Cannot touch pricing on the anchor account", source="sf_hitl_rejection",
        )
        with _registry_patch([_kpi("gross_margin_pct", "hess")]), \
             _providers(neighbourhood=[], constraints=[constraint]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        assert len(result.active_constraints) == 1
        assert result.active_constraints[0].source == "assumption_register"
        assert result.active_constraints[0].text == "Cannot touch pricing on the anchor account"

    @pytest.mark.asyncio
    async def test_prior_frame_present_and_never_marked_as_current_choice(self):
        da = _make_da_stub()
        prior = Assumption(
            client_id="hess", scope="gross_margin_pct", record_type="framing",
            text="Addressing base_oil_cost instead of gross_margin_pct directly",
            source="da_hitl", framing_choice="alternative",
            falsification_criterion="If base oil prices stabilize and margin does not recover, this was wrong.",
            decided_by_role="Finance Manager", decided_by_is_owner=True,
        )
        with _registry_patch([_kpi("gross_margin_pct", "hess")]), \
             _providers(neighbourhood=[], prior_framing=prior):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        assert result.prior_frame is not None
        assert result.prior_frame.choice == "alternative"
        assert result.prior_frame.chosen_objective_text == prior.text
        assert result.prior_frame.decided_by_role == "Finance Manager"

    @pytest.mark.asyncio
    async def test_no_prior_frame_leaves_field_none(self):
        da = _make_da_stub()
        with _registry_patch([_kpi("gross_margin_pct", "hess")]), _providers(neighbourhood=[], prior_framing=None):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        assert result.prior_frame is None

    @pytest.mark.asyncio
    async def test_owner_attribution_computed_server_side(self):
        da = _make_da_stub()
        with _registry_patch([_kpi("gross_margin_pct", "hess", owner_role="CFO")]), \
             _providers(neighbourhood=[]):
            result = await da._build_framing_prompt(_da_output(), {"role": "CFO"})
        assert result is not None
        assert result.owner_role == "CFO"
        assert result.viewer_role == "CFO"
        assert result.viewer_is_owner is True

    @pytest.mark.asyncio
    async def test_non_owner_viewer_is_flagged(self):
        da = _make_da_stub()
        with _registry_patch([_kpi("gross_margin_pct", "hess", owner_role="CFO")]), \
             _providers(neighbourhood=[]):
            result = await da._build_framing_prompt(_da_output(), {"role": "Finance Manager"})
        assert result is not None
        assert result.viewer_is_owner is False

    @pytest.mark.asyncio
    async def test_owner_attribution_tolerates_full_title_vs_short_code(self):
        """Found live 2026-08-18: useDecisionStudio.ts sends
        principal_context.role as the principal's full TITLE
        ('Chief Financial Officer'), but KPI.owner_role in the registry is a
        short code ('CFO'). The original test above used 'CFO' for BOTH
        sides, which is why it passed while the real bug shipped — this
        reproduces the actual live shape."""
        da = _make_da_stub()
        with _registry_patch([_kpi("gross_margin_pct", "hess", owner_role="CFO")]), \
             _providers(neighbourhood=[]):
            result = await da._build_framing_prompt(_da_output(), {"role": "Chief Financial Officer"})
        assert result is not None
        assert result.viewer_is_owner is True

    @pytest.mark.asyncio
    async def test_requires_falsification_criterion_always_true(self):
        da = _make_da_stub()
        with _registry_patch([_kpi("gross_margin_pct", "hess")]), _providers(neighbourhood=[]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result.requires_falsification_criterion is True


# ---------------------------------------------------------------------------
# _roles_match — the abbreviation-vs-full-title normalization
# ---------------------------------------------------------------------------

class TestRolesMatch:
    def test_exact_match(self):
        from src.agents.new.a9_deep_analysis_agent import _roles_match
        assert _roles_match("CFO", "CFO") is True
        assert _roles_match("Finance Manager", "Finance Manager") is True

    def test_case_and_whitespace_insensitive(self):
        from src.agents.new.a9_deep_analysis_agent import _roles_match
        assert _roles_match("  CFO ", "cfo") is True

    def test_abbreviation_matches_full_title(self):
        from src.agents.new.a9_deep_analysis_agent import _roles_match
        assert _roles_match("CFO", "Chief Financial Officer") is True
        assert _roles_match("Chief Financial Officer", "CFO") is True
        assert _roles_match("CEO", "Chief Executive Officer") is True
        assert _roles_match("COO", "Chief Operating Officer") is True

    def test_genuinely_different_roles_do_not_match(self):
        from src.agents.new.a9_deep_analysis_agent import _roles_match
        assert _roles_match("CFO", "Finance Manager") is False
        assert _roles_match("CFO", "Chief Operating Officer") is False

    def test_blank_or_none_never_matches(self):
        from src.agents.new.a9_deep_analysis_agent import _roles_match
        assert _roles_match(None, "CFO") is False
        assert _roles_match("CFO", None) is False
        assert _roles_match("", "") is False
        assert _roles_match(None, None) is False
