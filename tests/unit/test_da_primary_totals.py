"""The totals belong to the primary basis.

Found live 2026-10-13 on lubricants Gross Profit, a card that fired against prior year AND
against plan: the segments were measured against prior year (summing to 14.80M) while the
total beside them read 17.76M, which was the plan. The second-basis pass had recorded its
own totals over the primary ones.
"""
from src.agents.new.a9_deep_analysis_agent import _keep_primary_totals, _restore_primary_totals


def test_totals_recorded_by_the_second_pass_are_dropped():
    totals = {"region": {"previous": 14.80}}
    kept = _keep_primary_totals(totals)
    totals["region"] = {"previous": 17.76}          # second basis overwrote it
    totals["product"] = {"previous": 17.76}         # and added one the primary pass never had
    _restore_primary_totals(totals, kept)
    assert totals == {"region": {"previous": 14.80}}


def test_no_primary_totals_stays_empty_so_they_are_asked_for_on_the_primary_basis():
    totals: dict = {}
    kept = _keep_primary_totals(totals)
    totals["region"] = {"previous": 17.76}
    _restore_primary_totals(totals, kept)
    assert totals == {}


def test_the_same_dict_object_is_restored_in_place():
    totals = {"region": 1}
    alias = totals
    kept = _keep_primary_totals(totals)
    totals["x"] = 2
    _restore_primary_totals(totals, kept)
    assert alias is totals and alias == {"region": 1}
