"""The recommendation follows the business's weights; the rationale follows the recommendation.

Found in a production briefing 2026-10-14: Option A was badged Recommended while the rationale
argued for Option B. The owner chose to keep the weights deciding (human approval stays in charge).
"""
from types import SimpleNamespace as NS

from src.agents.models.solution_finder_models import SolutionOption
from src.analysis.recommendation_choice import choose, disagreement_tension, fallback_rationale

AUDIT = NS(id="opt_1", title="COGS Component Audit", is_check=True)
ESCALATORS = NS(id="opt_2", title="Tiered Price Escalators", is_check=False)
DECOMP = NS(id="opt_3", title="Price-vs-Cost Decomposition", is_check=True)


def test_a_check_ranked_first_is_not_recommended_on_its_own():
    c = choose([AUDIT, ESCALATORS, DECOMP], model_pick_id="opt_2")
    assert c["recommended"] is ESCALATORS and c["skipped_checks"] == [AUDIT]
    assert c["disagrees"] is False and c["score_top"] is AUDIT


def test_the_live_case_audit_badged_rationale_for_escalators_cannot_recur():
    # before: badge = ranked[0] (the audit), rationale = the model's case for the escalators
    c = choose([AUDIT, ESCALATORS, DECOMP], model_pick_id="opt_2")
    assert c["recommended"].id == "opt_2"


def test_the_weights_decide_when_the_model_preferred_another_option():
    c = choose([ESCALATORS, NS(id="opt_4", title="Mix shift", is_check=False)], model_pick_id="opt_4")
    assert c["recommended"] is ESCALATORS and c["disagrees"] is True and c["model_pick"].id == "opt_4"


def test_when_every_option_is_a_check_the_first_stands():
    c = choose([AUDIT, DECOMP], model_pick_id=None)
    assert c["recommended"] is AUDIT and c["skipped_checks"] == []


def test_an_unknown_or_missing_pick_is_not_a_disagreement():
    assert choose([ESCALATORS], "opt_9")["disagrees"] is False
    assert choose([ESCALATORS], None)["disagrees"] is False
    assert choose([], "opt_1")["recommended"] is None


def test_the_disagreement_is_stated_for_the_reader_without_ids_in_the_prose():
    t = disagreement_tension(ESCALATORS, NS(id="opt_4", title="Mix shift"))
    assert "Mix shift" in t["tension"] and "Tiered Price Escalators" in t["tension"]
    assert "opt_" not in t["tension"] and "opt_" not in t["requires"]
    assert t["options_affected"] == ["opt_2", "opt_4"]


def test_the_fallback_never_argues_for_another_option():
    assert "Tiered Price Escalators" in fallback_rationale(ESCALATORS)


def test_options_carry_the_check_flag_default_false():
    o = SolutionOption(id="opt_1", title="t")
    assert o.is_check is False
    assert SolutionOption(id="opt_1", title="t", is_check=True).is_check is True
