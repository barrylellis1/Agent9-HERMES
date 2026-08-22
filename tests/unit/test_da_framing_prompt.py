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
    async def test_identity_edge_with_no_confidence_flows_through_cleanly(self):
        """An accounting-identity edge (kpi_relationship_basis_design.md) carries
        confidence=None and causal_rung=None -- neither applies to arithmetic
        that's true by construction. Verified live 2026-08-22 against the real
        provider for the four reclassified lubricants edges
        (net_revenue<->gross_margin_pct, gross_margin_pct<->cogs,
        base_oil_cost->cogs, distribution_cost->cogs); this pins the same
        behavior through _build_framing_prompt end-to-end so a future refactor
        can't silently start fabricating a confidence value or raising on None."""
        da = _make_da_stub()
        edge = _relationship(
            confidence=None, causal_rung=None, provenance="confirmed",
            mechanism="Gross Margin % is calculated from Net Revenue and COGS; "
                      "COGS movements directly move the ratio (Revenue held constant), not the reverse.",
        )
        with _registry_patch([_kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess")]), \
             _providers(neighbourhood=[(edge, 1)]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        assert len(result.alternatives) == 1
        alt = result.alternatives[0]
        assert alt.confidence is None
        assert alt.causal_rung is None
        assert alt.mechanism is not None  # identity edges keep their (accurate) mechanism text

    @pytest.mark.asyncio
    async def test_two_hop_edge_preserves_hop_distance_not_flattened(self):
        da = _make_da_stub()
        # base_oil_cost -> cogs (hop 1, already visited via kpi_id="cogs")
        # cogs -> gross_margin_pct would be hop... construct directly as a
        # 2-hop return from the provider (mirrors what get_causal_neighbourhood
        # itself would produce for a 2-hop BFS).
        # causal_direction="related_causes_kpi" on both: cogs causes
        # gross_margin_pct, and base_oil_cost causes cogs -- a valid path
        # back to the origin, required since Aug 2026 for a hop-2 alternative
        # to be offered at all (causal_edge_direction_and_magnitude_design.md).
        hop1 = _relationship(kpi_id="gross_margin_pct", related_kpi_id="cogs", provenance="confirmed", causal_direction="related_causes_kpi")
        hop2 = _relationship(kpi_id="cogs", related_kpi_id="base_oil_cost", provenance="template", mechanism="cost pass-through", causal_direction="related_causes_kpi")
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
# Causal direction filtering (causal_edge_direction_and_magnitude_design.md,
# Aug 2026) — found live: a Net Revenue framing gate offered COGS as an
# alternative objective via a 2-hop path through gross_margin_pct, even
# though the connecting edge's own mechanism says the direction runs the
# other way (COGS causes margin, not the reverse). hop 1 stays unfiltered by
# design (decision #3); these tests cover hop 2+ path validity.
# ---------------------------------------------------------------------------

class TestCausalDirectionFiltering:
    @pytest.mark.asyncio
    async def test_hop_two_excluded_when_connecting_edge_direction_unknown(self):
        """The exact real-world case: net_revenue -> gross_margin_pct (no
        recorded mechanism, causal_direction defaults to 'unknown') ->
        cogs. Nothing establishes gross_margin_pct as upstream of
        net_revenue, so cogs must not be offered as a 2-hop alternative."""
        da = _make_da_stub()
        hop1 = _relationship(kpi_id="net_revenue", related_kpi_id="gross_margin_pct")  # causal_direction defaults to "unknown"
        hop2 = _relationship(kpi_id="gross_margin_pct", related_kpi_id="cogs", causal_direction="related_causes_kpi")
        with _registry_patch([
            _kpi("net_revenue", "hess"), _kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess"),
        ]), _providers(neighbourhood=[(hop1, 1), (hop2, 2)]):
            result = await da._build_framing_prompt(_da_output(kpi_name="net_revenue"), {})
        assert result is not None
        kpi_ids = {a.kpi_id for a in result.alternatives}
        assert kpi_ids == {"gross_margin_pct"}  # hop-1 still shown, unfiltered
        assert "cogs" not in kpi_ids

    @pytest.mark.asyncio
    async def test_hop_two_excluded_when_second_edge_walked_backward(self):
        """Both edges individually well-directed is not sufficient -- the
        SECOND edge must point the right way too, even when hop 1 is a
        validly-upstream neighbour (cogs causes gross_margin_pct, correctly
        shown). The hop-2 edge here says cogs causes base_oil_cost -- the
        wrong direction (really base_oil_cost causes cogs) -- so walking
        from cogs TO base_oil_cost at hop 2 must be excluded even though
        hop 1 is fine."""
        da = _make_da_stub()
        hop1 = _relationship(kpi_id="gross_margin_pct", related_kpi_id="cogs", causal_direction="related_causes_kpi")  # cogs causes margin -- valid, cogs shown
        hop2 = _relationship(kpi_id="cogs", related_kpi_id="base_oil_cost", causal_direction="kpi_causes_related")  # says cogs causes base_oil_cost -- backward
        with _registry_patch([
            _kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess"), _kpi("base_oil_cost", "hess"),
        ]), _providers(neighbourhood=[(hop1, 1), (hop2, 2)]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        kpi_ids = {a.kpi_id for a in result.alternatives}
        assert kpi_ids == {"cogs"}
        assert "base_oil_cost" not in kpi_ids

    @pytest.mark.asyncio
    async def test_hop_one_excluded_when_neighbour_is_confirmed_effect(self):
        """Even at hop 1: once a direction is confirmed, a neighbour the
        edge confirms is the EFFECT (not the cause) of the analysed KPI must
        be excluded -- not just left unfiltered like the 'unknown' case.
        Real example: Gross Margin % is calculated FROM Net Revenue, so
        Net Revenue is a legitimate root-cause candidate for Gross Margin %,
        but Gross Margin % is never a legitimate root-cause candidate for
        Net Revenue -- a derived ratio isn't upstream of one of its own
        inputs."""
        da = _make_da_stub()
        edge = _relationship(kpi_id="net_revenue", related_kpi_id="gross_margin_pct", causal_direction="kpi_causes_related")
        with _registry_patch([_kpi("net_revenue", "hess"), _kpi("gross_margin_pct", "hess")]), \
             _providers(neighbourhood=[(edge, 1)]):
            # Analysing net_revenue: gross_margin_pct is a confirmed EFFECT -- excluded.
            result_from_revenue = await da._build_framing_prompt(_da_output(kpi_name="net_revenue"), {})
        assert result_from_revenue is not None
        assert result_from_revenue.alternatives == []

        with _registry_patch([_kpi("net_revenue", "hess"), _kpi("gross_margin_pct", "hess")]), \
             _providers(neighbourhood=[(edge, 1)]):
            # Analysing gross_margin_pct: net_revenue is a confirmed CAUSE -- included.
            result_from_margin = await da._build_framing_prompt(_da_output(kpi_name="gross_margin_pct"), {})
        assert result_from_margin is not None
        assert {a.kpi_id for a in result_from_margin.alternatives} == {"net_revenue"}

    @pytest.mark.asyncio
    async def test_hop_two_included_when_full_chain_confirmed(self):
        """The 11F anchor scenario this design was built to preserve:
        base_oil_cost -> cogs -> gross_margin_pct, both edges confirmed in
        the direction that makes base_oil_cost a valid 2-hop upstream cause
        of gross_margin_pct."""
        da = _make_da_stub()
        hop1 = _relationship(kpi_id="gross_margin_pct", related_kpi_id="cogs", causal_direction="related_causes_kpi")
        hop2 = _relationship(kpi_id="base_oil_cost", related_kpi_id="cogs", causal_direction="kpi_causes_related")
        with _registry_patch([
            _kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess"), _kpi("base_oil_cost", "hess"),
        ]), _providers(neighbourhood=[(hop1, 1), (hop2, 2)]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        kpi_ids = {a.kpi_id for a in result.alternatives}
        assert kpi_ids == {"cogs", "base_oil_cost"}

    @pytest.mark.asyncio
    async def test_hop_one_unfiltered_regardless_of_direction(self):
        """Decision #3, unchanged: a direct (hop-1) neighbour is shown
        regardless of its own edge's causal_direction -- filtering only
        gates whether it may be used as a stepping stone for hop 2+."""
        da = _make_da_stub()
        edge = _relationship(kpi_id="gross_margin_pct", related_kpi_id="cogs")  # "unknown"
        with _registry_patch([_kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess")]), \
             _providers(neighbourhood=[(edge, 1)]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        assert {a.kpi_id for a in result.alternatives} == {"cogs"}

    @pytest.mark.asyncio
    async def test_bidirectional_direction_confirms_either_walk(self):
        """A 'bidirectional' edge is a real claim (both directions hold),
        not a placeholder for ignorance -- it must confirm extension in
        either direction, unlike 'unknown'."""
        da = _make_da_stub()
        hop1 = _relationship(kpi_id="gross_margin_pct", related_kpi_id="cogs", causal_direction="bidirectional")
        hop2 = _relationship(kpi_id="cogs", related_kpi_id="base_oil_cost", causal_direction="bidirectional")
        with _registry_patch([
            _kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess"), _kpi("base_oil_cost", "hess"),
        ]), _providers(neighbourhood=[(hop1, 1), (hop2, 2)]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        assert {a.kpi_id for a in result.alternatives} == {"cogs", "base_oil_cost"}


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


# ---------------------------------------------------------------------------
# Phase 20 — _first_numeric_value (module-level scalar parser)
# ---------------------------------------------------------------------------

class TestFirstNumericValue:
    def test_dict_row_takes_last_column(self):
        from src.agents.new.a9_deep_analysis_agent import _first_numeric_value
        result = {"columns": ["value"], "rows": [{"value": 42.5}]}
        assert _first_numeric_value(result) == 42.5

    def test_list_row_takes_last_column(self):
        from src.agents.new.a9_deep_analysis_agent import _first_numeric_value
        result = {"columns": ["value"], "rows": [[42.5]]}
        assert _first_numeric_value(result) == 42.5

    def test_no_rows_returns_none(self):
        from src.agents.new.a9_deep_analysis_agent import _first_numeric_value
        assert _first_numeric_value({"columns": ["value"], "rows": []}) is None

    def test_not_a_dict_returns_none(self):
        from src.agents.new.a9_deep_analysis_agent import _first_numeric_value
        assert _first_numeric_value(None) is None
        assert _first_numeric_value("not a dict") is None

    def test_unparseable_value_returns_none_not_raise(self):
        from src.agents.new.a9_deep_analysis_agent import _first_numeric_value
        result = {"columns": ["value"], "rows": [{"value": "not-a-number"}]}
        assert _first_numeric_value(result) is None

    def test_null_value_returns_none(self):
        from src.agents.new.a9_deep_analysis_agent import _first_numeric_value
        result = {"columns": ["value"], "rows": [{"value": None}]}
        assert _first_numeric_value(result) is None


# ---------------------------------------------------------------------------
# Phase 20 — _fetch_neighbour_snapshot (the lightweight rollup fetch)
# ---------------------------------------------------------------------------

def _dpa_stub(cur_val=None, prev_val=None, gen_success=True, exec_side_effect=None):
    """A minimal data_product_agent double: generate_sql_for_kpi always
    'succeeds' with a distinguishable SQL string per comparison_period, and
    execute_sql returns cur_val/prev_val keyed off which SQL was requested —
    same call-shape DA's own dimensional queries already use."""
    dpa = MagicMock()

    async def _gen(kpi_definition, timeframe=None, filters=None, comparison_period=False, **kw):
        if not gen_success:
            return {"success": False}
        return {"success": True, "sql": "PREV_SQL" if comparison_period else "CUR_SQL"}

    async def _exec(sql, data_product_id=None, **kw):
        if exec_side_effect is not None:
            return exec_side_effect(sql)
        val = prev_val if sql == "PREV_SQL" else cur_val
        if val is None:
            return {"columns": ["value"], "rows": []}
        return {"columns": ["value"], "rows": [{"value": val}]}

    dpa.generate_sql_for_kpi = AsyncMock(side_effect=_gen)
    dpa.execute_sql = AsyncMock(side_effect=_exec)
    return dpa


class TestFetchNeighbourSnapshot:
    @pytest.mark.asyncio
    async def test_no_data_product_agent_returns_none(self):
        da = _make_da_stub()
        da.data_product_agent = None
        result = await da._fetch_neighbour_snapshot(_kpi("cogs", "hess"))
        assert result is None

    @pytest.mark.asyncio
    async def test_success_computes_percent_change(self):
        da = _make_da_stub()
        da.data_product_agent = _dpa_stub(cur_val=110.0, prev_val=100.0)
        result = await da._fetch_neighbour_snapshot(_kpi("cogs", "hess"))
        assert result is not None
        assert result.value == 110.0
        assert result.comparison_value == 100.0
        assert result.percent_change == pytest.approx(10.0)

    @pytest.mark.asyncio
    async def test_zero_comparison_value_does_not_divide_by_zero(self):
        da = _make_da_stub()
        da.data_product_agent = _dpa_stub(cur_val=50.0, prev_val=0.0)
        result = await da._fetch_neighbour_snapshot(_kpi("cogs", "hess"))
        assert result is not None
        assert result.percent_change is None  # never raises ZeroDivisionError

    @pytest.mark.asyncio
    async def test_generate_sql_failure_returns_none(self):
        da = _make_da_stub()
        da.data_product_agent = _dpa_stub(gen_success=False)
        result = await da._fetch_neighbour_snapshot(_kpi("cogs", "hess"))
        assert result is None

    @pytest.mark.asyncio
    async def test_unparseable_execution_result_returns_none_not_raise(self):
        da = _make_da_stub()
        da.data_product_agent = _dpa_stub(exec_side_effect=lambda sql: {"columns": [], "rows": []})
        result = await da._fetch_neighbour_snapshot(_kpi("cogs", "hess"))
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_sql_raises_returns_none_not_propagate(self):
        da = _make_da_stub()
        dpa = MagicMock()
        dpa.generate_sql_for_kpi = AsyncMock(return_value={"success": True, "sql": "X"})
        dpa.execute_sql = AsyncMock(side_effect=RuntimeError("BigQuery timeout"))
        da.data_product_agent = dpa
        result = await da._fetch_neighbour_snapshot(_kpi("cogs", "hess"))
        assert result is None


# ---------------------------------------------------------------------------
# Phase 20 — _fetch_neighbour_monthly_trend (BigQuery-only trend series)
# ---------------------------------------------------------------------------

def _bq_kpi(kpi_id="cogs", client_id="hess"):
    return SimpleNamespace(
        id=kpi_id, client_id=client_id, name=kpi_id,
        sql_query="SELECT SUM(amount) AS value FROM `proj.dataset.financials` WHERE transaction_date BETWEEN '2026-01-01' AND '2026-08-31'",
        calculation=None,
        data_product_id="dp_lubricants_financials",
        metadata={"date_column": "transaction_date"},
    )


def _dpa_monthly_stub(gen_success=True, gen_sql="SELECT period, value FROM (...)", exec_result=None, exec_side_effect=None):
    """DA no longer builds monthly-series SQL itself (Phase 20 cleanup,
    2026-08-19) — it calls DPA's (synchronous) generate_monthly_series_sql
    then (async) execute_sql. Mock both steps explicitly rather than one
    bare MagicMock, which silently swallowed the real behavior into an
    unrelated exception path before this fix."""
    dpa = MagicMock()
    dpa.generate_monthly_series_sql = MagicMock(return_value={"success": gen_success, "sql": gen_sql if gen_success else ""})
    if exec_side_effect is not None:
        dpa.execute_sql = AsyncMock(side_effect=exec_side_effect)
    else:
        dpa.execute_sql = AsyncMock(return_value=exec_result if exec_result is not None else {"columns": ["period", "value"], "rows": []})
    return dpa


class TestFetchNeighbourMonthlyTrend:
    @pytest.mark.asyncio
    async def test_dpa_reports_non_bigquery_returns_none_without_calling_execute(self):
        """DPA is the one deciding backend eligibility now — DA just relays
        that decision, it never re-derives it. execute_sql must not even be
        attempted when DPA couldn't generate anything."""
        da = _make_da_stub()
        da.data_product_agent = _dpa_monthly_stub(gen_success=False)
        result = await da._fetch_neighbour_monthly_trend(_bq_kpi())
        assert result is None
        da.data_product_agent.execute_sql.assert_not_called()

    @pytest.mark.asyncio
    async def test_success_parses_period_value_rows(self):
        da = _make_da_stub()
        da.data_product_agent = _dpa_monthly_stub(exec_result={
            "columns": ["period", "value"],
            "rows": [{"period": "2026-06", "value": 100.0}, {"period": "2026-07", "value": 110.0}],
        })
        result = await da._fetch_neighbour_monthly_trend(_bq_kpi())
        assert result == [{"period": "2026-06", "value": 100.0}, {"period": "2026-07", "value": 110.0}]

    @pytest.mark.asyncio
    async def test_malformed_row_skipped_not_raised(self):
        da = _make_da_stub()
        da.data_product_agent = _dpa_monthly_stub(exec_result={
            "columns": ["period", "value"],
            "rows": [{"period": "2026-06", "value": "not-a-number"}, {"period": "2026-07", "value": 110.0}],
        })
        result = await da._fetch_neighbour_monthly_trend(_bq_kpi())
        assert result == [{"period": "2026-07", "value": 110.0}]

    @pytest.mark.asyncio
    async def test_no_rows_returns_none(self):
        da = _make_da_stub()
        da.data_product_agent = _dpa_monthly_stub(exec_result={"columns": ["period", "value"], "rows": []})
        result = await da._fetch_neighbour_monthly_trend(_bq_kpi())
        assert result is None

    @pytest.mark.asyncio
    async def test_execute_sql_raises_returns_none_not_propagate(self):
        da = _make_da_stub()
        da.data_product_agent = _dpa_monthly_stub(exec_side_effect=RuntimeError("BigQuery timeout"))
        result = await da._fetch_neighbour_monthly_trend(_bq_kpi())
        assert result is None

    @pytest.mark.asyncio
    async def test_no_data_product_agent_returns_none(self):
        da = _make_da_stub()
        da.data_product_agent = None
        result = await da._fetch_neighbour_monthly_trend(_bq_kpi())
        assert result is None


# ---------------------------------------------------------------------------
# Phase 20 — ranking, cap, disclosure, primary_snapshot (integration through
# _build_framing_prompt)
# ---------------------------------------------------------------------------

class TestFramingPromptRankingAndSnapshots:
    @pytest.mark.asyncio
    async def test_snapshot_attached_to_each_alternative_and_primary(self):
        da = _make_da_stub()
        da.data_product_agent = _dpa_stub(cur_val=110.0, prev_val=100.0)
        edge = _relationship()
        with _registry_patch([_kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess")]), \
             _providers(neighbourhood=[(edge, 1)]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        assert len(result.alternatives) == 1
        assert result.alternatives[0].neighbour_snapshot is not None
        assert result.alternatives[0].neighbour_snapshot.percent_change == pytest.approx(10.0)
        assert result.primary_snapshot is not None

    @pytest.mark.asyncio
    async def test_a_failed_snapshot_never_drops_the_alternative(self):
        da = _make_da_stub()
        da.data_product_agent = None  # every fetch fails
        edge = _relationship()
        with _registry_patch([_kpi("gross_margin_pct", "hess"), _kpi("cogs", "hess")]), \
             _providers(neighbourhood=[(edge, 1)]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        assert len(result.alternatives) == 1  # still present
        assert result.alternatives[0].neighbour_snapshot is None  # just no context
        assert result.primary_snapshot is None

    @pytest.mark.asyncio
    async def test_ranking_hop_tier_first_then_magnitude(self):
        """Two hop-1 candidates (one moving a lot, one flat) and one hop-2
        candidate moving a lot: hop-1 slots fill before hop-2 regardless of
        magnitude, and within hop-1 the mover ranks above the flat one."""
        da = _make_da_stub()

        async def _exec(sql, data_product_id=None, **kw):
            # kpi encoded in the generated SQL string via a stub gen below
            return {"columns": ["value"], "rows": [{"value": 0.0}]}

        # Distinguish per-KPI current/comparison values by kpi_definition.id
        vals = {
            "cogs_mover": (150.0, 100.0),      # hop 1, +50%
            "premium_mix_flat": (100.0, 100.0),  # hop 1, 0%
            "base_oil_mover": (200.0, 100.0),   # hop 2, +100%
        }

        async def _gen(kpi_definition, timeframe=None, filters=None, comparison_period=False, **kw):
            kid = getattr(kpi_definition, "id", None)
            return {"success": True, "sql": f"{kid}|{'prev' if comparison_period else 'cur'}"}

        async def _exec2(sql, data_product_id=None, **kw):
            kid, which = sql.split("|")
            cur, prev = vals[kid]
            v = prev if which == "prev" else cur
            return {"columns": ["value"], "rows": [{"value": v}]}

        dpa = MagicMock()
        dpa.generate_sql_for_kpi = AsyncMock(side_effect=_gen)
        dpa.execute_sql = AsyncMock(side_effect=_exec2)
        da.data_product_agent = dpa

        edge_mover_1hop = _relationship(kpi_id="gross_margin_pct", related_kpi_id="cogs_mover")
        # related_causes_kpi on the flat 1-hop edge and the 2-hop edge:
        # premium_mix_flat causes gross_margin_pct, base_oil_mover causes
        # premium_mix_flat -- a valid path, required for base_oil_mover's
        # hop-2 alternative to be offered at all (see hop-1 test above).
        edge_flat_1hop = _relationship(kpi_id="gross_margin_pct", related_kpi_id="premium_mix_flat", causal_direction="related_causes_kpi")
        edge_mover_2hop_a = _relationship(kpi_id="gross_margin_pct", related_kpi_id="premium_mix_flat", causal_direction="related_causes_kpi")
        edge_mover_2hop_b = _relationship(kpi_id="premium_mix_flat", related_kpi_id="base_oil_mover", causal_direction="related_causes_kpi")

        with _registry_patch([
            _kpi("gross_margin_pct", "hess"), _kpi("cogs_mover", "hess"),
            _kpi("premium_mix_flat", "hess"), _kpi("base_oil_mover", "hess"),
        ]), _providers(neighbourhood=[
            (edge_mover_1hop, 1), (edge_flat_1hop, 1), (edge_mover_2hop_b, 2),
        ]):
            result = await da._build_framing_prompt(_da_output(), {})

        assert result is not None
        order = [a.kpi_id for a in result.alternatives]
        # Both hop-1 candidates rank ahead of the hop-2 one, regardless of
        # the hop-2 candidate's much larger magnitude.
        assert order.index("cogs_mover") < order.index("base_oil_mover")
        assert order.index("premium_mix_flat") < order.index("base_oil_mover")
        # Within hop-1, the mover ranks ahead of the flat one.
        assert order.index("cogs_mover") < order.index("premium_mix_flat")

    @pytest.mark.asyncio
    async def test_cap_and_disclosure_count(self):
        """More than the list cap's worth of causal alternatives — the extras
        are disclosed via additional_causal_measures_count, never silently
        dropped with no trace."""
        da = _make_da_stub()
        da.data_product_agent = None  # snapshots irrelevant to this test
        edges = [
            _relationship(kpi_id="gross_margin_pct", related_kpi_id=f"neighbour_{i}")
            for i in range(7)
        ]
        kpis = [_kpi("gross_margin_pct", "hess")] + [_kpi(f"neighbour_{i}", "hess") for i in range(7)]
        with _registry_patch(kpis), _providers(neighbourhood=[(e, 1) for e in edges]):
            result = await da._build_framing_prompt(_da_output(), {})
        assert result is not None
        assert len(result.alternatives) == da._FRAMING_ALTERNATIVES_LIST_CAP
        assert result.additional_causal_measures_count == 7 - da._FRAMING_ALTERNATIVES_LIST_CAP

    @pytest.mark.asyncio
    async def test_market_signal_alternative_never_counted_against_the_cap(self):
        """The market-signal alternative is a separate category (Decision #12)
        — it must survive the causal-graph cap untouched, appended after."""
        da = _make_da_stub()
        da.data_product_agent = None
        edges = [
            _relationship(kpi_id="gross_margin_pct", related_kpi_id=f"neighbour_{i}")
            for i in range(7)
        ]
        kpis = [_kpi("gross_margin_pct", "hess")] + [_kpi(f"neighbour_{i}", "hess") for i in range(7)]
        conflict = {"detected": True, "confidence": 0.6, "summary": "Market signals diverge from the internal read."}
        with _registry_patch(kpis), _providers(neighbourhood=[(e, 1) for e in edges]):
            result = await da._build_framing_prompt(_da_output(market_conflict=conflict), {})
        assert result is not None
        assert len(result.alternatives) == da._FRAMING_ALTERNATIVES_LIST_CAP + 1
        assert result.alternatives[-1].source == "market_signal"
