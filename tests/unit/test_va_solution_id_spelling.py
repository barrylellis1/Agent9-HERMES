"""A solution has one id spelling from the moment it is created.

Found live 2026-10-13: approval answered with 32 bare hex characters, the portfolio listed
the same solution as a dashed uuid, and a caller matching the two by equality did not find it.
"""
import uuid

from src.agents.new.a9_value_assurance_agent import _SolutionStore, _solution_id_from

HEX = "5df7a3cd4f3a91496331bdd9afd8bbee"


def test_a_new_id_is_spelled_the_way_the_database_returns_it():
    assert _solution_id_from(HEX) == "5df7a3cd-4f3a-9149-6331-bdd9afd8bbee"
    assert _solution_id_from(HEX) == str(uuid.UUID(HEX))


def test_the_same_inputs_still_give_the_same_solution():
    assert _solution_id_from(HEX).replace("-", "") == HEX


def test_either_spelling_still_finds_the_solution_in_memory():
    store = _SolutionStore()
    store[_solution_id_from(HEX)] = "s"
    assert store[HEX] == "s" and HEX in store and len(store) == 1
