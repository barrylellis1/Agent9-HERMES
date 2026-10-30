"""SA writes card text (observations + trend note) for several cards at once (2026-10-30).

The two model calls per card ran one after another inside the KPI loop: 23 calls, ~20 s of a
65 s Lubricants scan, with each KPI's queries waiting behind the previous KPI's text.
"""
import asyncio
import inspect
import logging
import time
from types import SimpleNamespace

import pytest

from src.agents.new import a9_situation_awareness_agent as sa_mod
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent


def _agent(delay=0.1, fail_on=None):
    sa = A9_Situation_Awareness_Agent.__new__(A9_Situation_Awareness_Agent)
    sa.logger = logging.getLogger("test_sa_enrich_cards_parallel")
    state = {"in_flight": 0, "peak": 0}

    async def _call(kind, kd, sit):
        state["in_flight"] += 1
        state["peak"] = max(state["peak"], state["in_flight"])
        try:
            await asyncio.sleep(delay)
            if fail_on == (kind, sit.kpi_name):
                raise RuntimeError("model call failed")
            return [f"obs {sit.kpi_name}"] if kind == "obs" else f"note {sit.kpi_name}"
        finally:
            state["in_flight"] -= 1

    async def obs(kd, kv, sit):
        return await _call("obs", kd, sit)

    async def note(kd, kv, sit):
        return await _call("note", kd, sit)

    sa._generate_key_observations = obs
    sa._generate_trend_note = note
    return sa, state


def _cards(n):
    return [(SimpleNamespace(name=f"K{i}"), None,
             SimpleNamespace(kpi_name=f"K{i}", alert_type="plan_variance", key_observations=None, trend_note=None))
            for i in range(n)]


@pytest.mark.asyncio
async def test_cards_are_written_at_once_and_every_card_gets_its_text():
    sa, state = _agent(delay=0.1)
    items = _cards(8)
    t0 = time.perf_counter()
    await sa._enrich_cards(items)
    took = time.perf_counter() - t0
    # one after another: 8 cards x 2 calls x 0.1 s = 1.6 s; 4 cards at once, both calls together: ~0.2 s
    assert took < 0.6
    for _, _, sit in items:
        assert sit.key_observations == [f"obs {sit.kpi_name}"]
        assert sit.trend_note == f"note {sit.kpi_name}"


@pytest.mark.asyncio
async def test_no_more_than_the_cap_of_model_calls_run_at_once():
    sa, state = _agent(delay=0.05)
    await sa._enrich_cards(_cards(12))
    assert state["peak"] == 2 * sa_mod._ENRICH_CARDS_AT_ONCE


@pytest.mark.asyncio
async def test_one_failed_call_leaves_the_rest_of_the_cards_untouched():
    sa, _ = _agent(delay=0.01, fail_on=("note", "K1"))
    items = _cards(3)
    await sa._enrich_cards(items)  # does not raise
    by_name = {sit.kpi_name: sit for _, _, sit in items}
    assert by_name["K1"].key_observations == ["obs K1"]  # its other call still lands
    assert by_name["K1"].trend_note is None
    assert by_name["K0"].trend_note == "note K0" and by_name["K2"].trend_note == "note K2"


@pytest.mark.asyncio
async def test_no_cards_makes_no_calls():
    sa, state = _agent()
    await sa._enrich_cards([])
    assert state["peak"] == 0


def test_the_kpi_loop_no_longer_waits_on_card_text():
    src = inspect.getsource(A9_Situation_Awareness_Agent.detect_situations)
    assert "await self._generate_key_observations" not in src
    assert "await self._enrich_cards(" in src
    # the text is written before the merge, which folds key_observations
    assert src.index("await self._enrich_cards(") < src.index("self._merge_compound_kpi_situations(situations)")
