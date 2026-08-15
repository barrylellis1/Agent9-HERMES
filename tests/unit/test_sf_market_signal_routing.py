"""Market signals reach Solution Finder under their own label and budget (Aug 2026).

THREE DEFECTS FIXED
-------------------
1. `market_signals` was never read by the Solution Finder at all. The only path in
   was `refinement_result["external_context"]`, populated by turn-0 seeding of the
   refinement chat — so a principal who SKIPPED refinement got no market signals,
   even though the Market Analysis agent had run and attached them to the DA output.
   Only the `market_conflict` flag survived that path.
2. When refinement did run, MA signals were rendered as "PRINCIPAL-PROVIDED
   CONTEXT (from refinement)" — market research attributed to the executive.
3. Signals and the principal's own statements shared one `[:3]` budget, so seeded
   signals crowded out what the executive actually said. Same failure shape as the
   refinement/register constraint budgets.
"""

from src.agents.new.a9_solution_finder_agent import (
    _MAX_MARKET_SIGNALS,
    _format_market_signals,
    _split_external_context,
)


def _signal(title, summary, source="Reuters", relevance=0.9):
    return {"title": title, "summary": summary, "source": source, "relevance_score": relevance}


# ---------------------------------------------------------------------------
# Reading from the DA output — the path that did not exist
# ---------------------------------------------------------------------------


def test_signals_arrive_without_a_refinement_chat():
    """The regression. Skipping refinement must not silently drop market signals."""
    da_ctx = {"market_signals": [_signal("Base oil up 18%", "Crude and additive costs rose in Q2")]}

    block = _format_market_signals(da_ctx, refinement_result=None)

    assert "Base oil up 18%" in block
    assert "Crude and additive costs rose" in block


def test_block_is_labelled_as_external_not_as_the_principal():
    da_ctx = {"market_signals": [_signal("Competitor price cut", "Rival dropped Value tier 6%")]}
    block = _format_market_signals(da_ctx, None)

    assert "EXTERNAL MARKET SIGNALS" in block
    assert "not the principal's own words" in block
    assert "PRINCIPAL-PROVIDED" not in block


def test_source_and_relevance_survive():
    """MA returns structured signals; flattening to a bare string discards the
    provenance a persona needs to weigh them."""
    da_ctx = {"market_signals": [_signal("Base oil up 18%", "…", source="ICIS", relevance=0.83)]}
    block = _format_market_signals(da_ctx, None)

    assert "source: ICIS" in block
    assert "relevance: 0.83" in block


def test_signal_count_is_bounded():
    da_ctx = {"market_signals": [_signal(f"Signal {i}", "body") for i in range(20)]}
    block = _format_market_signals(da_ctx, None)

    assert block.count(" | source:") <= _MAX_MARKET_SIGNALS


def test_no_signals_yields_no_block_rather_than_an_empty_heading():
    assert _format_market_signals({}, None) == ""
    assert _format_market_signals({"market_signals": []}, None) == ""
    assert _format_market_signals(None, None) == ""


def test_malformed_signals_are_skipped_not_crashed():
    da_ctx = {"market_signals": [None, "a bare string", {}, {"title": "Real one", "summary": "body"}]}
    block = _format_market_signals(da_ctx, None)

    assert "Real one" in block


# ---------------------------------------------------------------------------
# Separating MA-seeded items from what the principal actually said
# ---------------------------------------------------------------------------


def test_split_recovers_the_principals_own_words():
    principal, ma = _split_external_context([
        "Market signal: Base oil up 18% — crude rose",
        "We lost the Chain A tender in June",
        "Market signal: Competitor cut Value pricing — rival dropped 6%",
        "Our new plant comes online in Q4",
    ])

    assert principal == ["We lost the Chain A tender in June", "Our new plant comes online in Q4"]
    assert len(ma) == 2


def test_seeded_signals_are_not_double_counted_when_da_already_carries_them():
    """Both paths can supply the same signal; it must appear once."""
    da_ctx = {"market_signals": [_signal("Base oil up 18%", "crude rose")]}
    refinement = {"external_context": ["Market signal: Base oil up 18% — crude rose"]}

    block = _format_market_signals(da_ctx, refinement)

    assert block.count("Base oil up 18%") == 1


def test_legacy_payloads_still_work_through_the_refinement_fallback():
    """DA outputs predating market_signals still deliver via the seeded path."""
    refinement = {"external_context": ["Market signal: Supply disruption — port strike"]}
    block = _format_market_signals({}, refinement)

    assert "Supply disruption" in block
    assert "EXTERNAL MARKET SIGNALS" in block


def test_the_principals_own_context_is_preserved_not_removed():
    """The split protects principal context; it does not drop it.

    Guards against reading the MA fix as 'principal context was removed'. Both
    the dataset recap and Stage 1's `principal_context` key still carry what the
    executive said — the split only stops market research being filed under it.
    """
    external = [
        "Market signal: Base oil up 18% — crude rose",
        "We lost the Chain A tender in June",
    ]
    principal, ma = _split_external_context(external)

    assert principal == ["We lost the Chain A tender in June"]
    assert ma, "the signal must still be carried — under its own label"


def test_split_applied_at_both_consumption_sites():
    """Fixing one site and not the other renders the same data two ways.

    The dataset recap was fixed first; Stage 1's refinement_compact_s1
    ["principal_context"] was missed on the first pass and still passed the
    unsplit list.
    """
    import inspect

    from src.agents.new import a9_solution_finder_agent as sf

    src = inspect.getsource(sf)
    assert src.count("_split_external_context(refinement_result") >= 2, (
        "both the dataset recap and the Stage 1 compact must split external_context"
    )
    assert 'refinement_compact_s1["principal_context"] = refinement_result["external_context"][:3]' not in src


def test_principal_context_budget_is_not_consumed_by_signals():
    """Three principal statements must all survive alongside five signals."""
    external = [f"Market signal: S{i} — body" for i in range(5)] + [
        "Union agreement runs to Q3",
        "We cannot touch the anchor account",
        "New plant online in Q4",
    ]
    principal, ma = _split_external_context(external)

    assert len(principal) == 3, "the principal's own statements were crowded out by seeded signals"
    assert len(ma) == 5
