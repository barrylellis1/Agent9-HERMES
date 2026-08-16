"""
Stage J — enterprise lens weights reach Solution Finder's option ranking.

The weighting belongs to the COMPANY's strategy, not to whoever is reading the
briefing. An earlier cut of this stage hung `tradeoff_weights` off `PrincipalProfile`
and was reverted: ranking weights change which option wins (measurably — 4 of 11
saved arms flip across plausible CEO/COO/CFO weightings), which breaks the M1
invariant already stated in the synthesis prompt — *role adaptation controls
entry point and depth only; the conclusion is identical for every role*.

Pure functions and model construction — no LLM, no network, no DB.
"""
from __future__ import annotations

import pytest

from src.agents.models.solution_finder_models import TradeOffCriterion, TradeOffMatrix
from src.agents.new.a9_solution_finder_agent import _tradeoff_weights_to_criteria
from src.agents.shared.a9_debate_protocol_models import A9_PS_BusinessContext, TradeoffWeights
from src.analysis.decision_quality import DEFAULT_CRITERIA_WEIGHTS, score_run
from src.registry.models.principal import PrincipalProfile


def _bc(**kw) -> A9_PS_BusinessContext:
    # A9_PS_BusinessContext is a Pydantic MODEL, not an agent. The architecture
    # lint matches the `A9_*(` prefix, which models share with agent classes;
    # constructing a model is not the lifecycle bypass that rule exists to
    # prevent. Token must sit on the matching line — the check is per-line.
    return A9_PS_BusinessContext(  # arch-allow-agent-ctor
        enterprise_name="Lubricants Business", industry="Oil & Gas", **kw
    )


class TestTradeoffWeightsModel:
    def test_all_three_weights_are_required(self):
        """A partially-specified weighting is not a weighting. Silently filling
        the rest from a default would smuggle the system's preferences back in
        wearing the customer's name."""
        with pytest.raises(Exception):
            TradeoffWeights(impact=0.6)

    def test_negative_weight_rejected(self):
        with pytest.raises(Exception):
            TradeoffWeights(impact=-0.1, cost=0.2, risk=0.2)

    def test_renders_as_evaluation_criteria_shape(self):
        assert TradeoffWeights(impact=0.6, cost=0.2, risk=0.2).to_criteria() == [
            {"name": "impact", "weight": 0.6},
            {"name": "cost", "weight": 0.2},
            {"name": "risk", "weight": 0.2},
        ]


class TestWhereWeightsLive:
    def test_business_context_holds_them_and_defaults_to_none(self):
        """None means 'never configured', which stays visible. A default_factory
        would manufacture consent — every client appearing to have chosen weights
        nobody set."""
        c = _bc()
        assert c.tradeoff_weights is None
        assert c.strategic_posture is None

    def test_posture_carries_the_justification(self):
        c = _bc(strategic_posture="margin defense",
                tradeoff_weights=TradeoffWeights(impact=0.4, cost=0.3, risk=0.3))
        assert c.strategic_posture == "margin defense"
        assert c.tradeoff_weights.impact == 0.4

    def test_principal_profile_does_not_carry_ranking_weights(self):
        """REGRESSION / invariant. Re-adding this would silently reintroduce the
        M1 violation: two executives receiving different recommendations for the
        same situation, with nothing on the output explaining why."""
        p = PrincipalProfile(id="cfo_001", name="CFO", title="Chief Financial Officer")
        assert not hasattr(p, "tradeoff_weights")
        assert "tradeoff_weights" not in PrincipalProfile.model_fields


class TestResolver:
    def test_no_context_yields_none(self):
        assert _tradeoff_weights_to_criteria(None) is None

    def test_context_without_weights_yields_none(self):
        assert _tradeoff_weights_to_criteria({"industry": "Oil & Gas"}) is None
        assert _tradeoff_weights_to_criteria(_bc()) is None

    def test_returns_none_rather_than_the_default_vector(self):
        """Handing SF the numbers it would have used anyway makes 'nobody chose
        this' and 'this client chose the house numbers' indistinguishable
        downstream — the exact ambiguity Stage J removes."""
        assert _tradeoff_weights_to_criteria({"tradeoff_weights": None}) is None

    def test_dict_form_resolves(self):
        assert _tradeoff_weights_to_criteria(
            {"tradeoff_weights": {"impact": 0.7, "cost": 0.2, "risk": 0.1}}
        ) == [
            {"name": "impact", "weight": 0.7},
            {"name": "cost", "weight": 0.2},
            {"name": "risk", "weight": 0.1},
        ]

    def test_pydantic_form_resolves(self):
        out = _tradeoff_weights_to_criteria(
            _bc(tradeoff_weights=TradeoffWeights(impact=0.5, cost=0.3, risk=0.2))
        )
        assert out[0] == {"name": "impact", "weight": 0.5}
        assert len(out) == 3

    def test_partial_weighting_falls_back_wholesale(self):
        assert _tradeoff_weights_to_criteria({"tradeoff_weights": {"impact": 0.7, "cost": 0.2}}) is None

    def test_non_numeric_weight_falls_back(self):
        assert _tradeoff_weights_to_criteria(
            {"tradeoff_weights": {"impact": "high", "cost": 0.2, "risk": 0.1}}
        ) is None

    def test_bool_is_not_a_weight(self):
        """`isinstance(True, int)` is True in Python — without an explicit guard
        a JSON `true` would silently become a weight of 1.0."""
        assert _tradeoff_weights_to_criteria(
            {"tradeoff_weights": {"impact": True, "cost": 0.2, "risk": 0.1}}
        ) is None


class TestProviderRoundTrip:
    """`business_contexts` needs NO migration — both fields ride the existing
    `metadata` JSONB, which the provider already round-trips explicitly."""

    def _provider(self):
        from src.registry.business_context.business_context_provider import (
            SupabaseBusinessContextProvider,
        )
        return SupabaseBusinessContextProvider(
            supabase_url="http://localhost", supabase_service_key="test-key"
        )

    def test_weights_and_posture_survive_a_round_trip(self):
        p = self._provider()
        row = p._model_to_row(
            _bc(strategic_posture="growth capture",
                tradeoff_weights=TradeoffWeights(impact=0.7, cost=0.15, risk=0.15))
        )
        assert row["metadata"]["strategic_posture"] == "growth capture"
        assert row["metadata"]["tradeoff_weights"] == {"impact": 0.7, "cost": 0.15, "risk": 0.15}

        back = p._row_to_model(row)
        assert back.strategic_posture == "growth capture"
        assert back.tradeoff_weights.impact == 0.7
        assert _tradeoff_weights_to_criteria(back)[0]["weight"] == 0.7

    def test_absent_weights_round_trip_as_none(self):
        p = self._provider()
        back = p._row_to_model(p._model_to_row(_bc()))
        assert back.tradeoff_weights is None
        assert back.strategic_posture is None


class TestLink4ReadsProvenance:
    def _run(self, matrix):
        return score_run({"options_ranked": [{"id": "o1", "title": "Indexed Pricing Clause"}],
                          "tradeoff_matrix": matrix})

    def test_business_context_source_passes_even_at_the_default_vector(self):
        """REGRESSION for the false positive a value-based check produces: a
        client whose declared posture happens to match the house numbers DID
        choose them, and link 4 must credit that."""
        s = self._run({
            "criteria": [{"name": n, "weight": w} for n, w in DEFAULT_CRITERIA_WEIGHTS],
            "criteria_source": "business_context",
        })
        assert s.criteria_defaulted is False
        assert s.l4_tradeoffs.passed is True

    def test_config_default_source_fails_even_at_an_unusual_vector(self):
        s = self._run({
            "criteria": [{"name": "impact", "weight": 0.9},
                         {"name": "cost", "weight": 0.05},
                         {"name": "risk", "weight": 0.05}],
            "criteria_source": "config_default",
        })
        assert s.criteria_defaulted is True
        assert s.l4_tradeoffs.passed is False

    def test_legacy_payload_without_source_falls_back_to_value_comparison(self):
        """All 11 baseline arms predate `criteria_source` and must stay
        scoreable, or the recorded §8 result becomes unreproducible."""
        s = self._run({"criteria": [{"name": n, "weight": w} for n, w in DEFAULT_CRITERIA_WEIGHTS]})
        assert s.criteria_defaulted is True
        assert s.l4_tradeoffs.passed is False
        assert "legacy payload" in s.l4_tradeoffs.detail


class TestWeightsAreWithheldFromThePrompt:
    """Text drives generation, numbers drive selection — only the numbers are
    withheld. If the model can read the weighting it is about to be scored
    under, it can tilt its own impact/cost/risk scalars toward it and
    `_rank_options` applies the same weighting again to tilted inputs."""

    def _ctx(self):
        from src.agents.new.a9_solution_finder_agent import _business_context_for_prompt
        return _business_context_for_prompt(
            _bc(strategic_posture="margin defense",
                risk_posture="low",
                tradeoff_weights=TradeoffWeights(impact=0.4, cost=0.3, risk=0.3))
        )

    def test_tradeoff_weights_never_reach_the_prompt(self):
        assert "tradeoff_weights" not in self._ctx()

    def test_strategic_posture_does_reach_the_prompt(self):
        """The half the model SHOULD see — prose it can reason with when
        proposing options."""
        assert self._ctx()["strategic_posture"] == "margin defense"

    def test_other_context_is_untouched(self):
        ctx = self._ctx()
        assert ctx["risk_posture"] == "low"
        assert ctx["industry"] == "Oil & Gas"

    def test_none_context_stays_none(self):
        from src.agents.new.a9_solution_finder_agent import _business_context_for_prompt
        assert _business_context_for_prompt(None) is None

    def test_dict_form_is_stripped_too(self):
        from src.agents.new.a9_solution_finder_agent import _business_context_for_prompt
        out = _business_context_for_prompt(
            {"industry": "Oil & Gas", "tradeoff_weights": {"impact": 0.4, "cost": 0.3, "risk": 0.3}}
        )
        assert "tradeoff_weights" not in out
        assert out["industry"] == "Oil & Gas"

    def test_ranking_still_sees_the_weights(self):
        """Withheld from the prompt, NOT from the ranker — the resolver reads the
        unstripped context."""
        ctx = _bc(tradeoff_weights=TradeoffWeights(impact=0.4, cost=0.3, risk=0.3))
        assert _tradeoff_weights_to_criteria(ctx)[0] == {"name": "impact", "weight": 0.4}


class TestProvenanceMarker:
    def test_matrix_carries_source(self):
        m = TradeOffMatrix(criteria=[TradeOffCriterion(name="impact", weight=0.6)],
                           criteria_source="business_context")
        assert m.criteria_source == "business_context"

    def test_source_is_optional_for_legacy_payloads(self):
        assert TradeOffMatrix().criteria_source is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
