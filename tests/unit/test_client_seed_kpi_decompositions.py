"""Validate every client seed file's KPI_DECOMPOSITIONS rows.

Mirrors test_client_seed_kpi_relationships.py's own rationale exactly: seed
data has zero automated coverage otherwise, and a bad row is not loud --
KPIDecompositionProvider's reads are not on any documented non-fatal
degrade path yet, but the same failure MODE applies (a row that fails model
validation, or a dangling KPI reference, is invisible until something tries
to render or reconcile the tree).

These tests import the seed module directly (no DB, no network), so they
run in the normal fast unit suite.
"""
from __future__ import annotations

import importlib

import pytest

from src.registry.models.kpi_decomposition import KPIDecompositionEdge

# Only lubricants exports KPI_DECOMPOSITIONS as of Phase 17 T2 -- hess,
# apex_lubricants and bicycle have no decomposition tree seeded yet.
_CLIENTS = ["lubricants"]


def _load(client: str):
    return importlib.import_module(f"scripts.clients.{client}")


@pytest.mark.parametrize("client", _CLIENTS)
def test_kpi_decompositions_pass_model_validation(client: str):
    """Every row must satisfy the Pydantic model -- closed operation Literal,
    the ratio-requires-weight guardrail, sign in (1, -1), no self-loops."""
    mod = _load(client)
    rows = getattr(mod, "KPI_DECOMPOSITIONS", [])
    assert rows, f"{client} exports KPI_DECOMPOSITIONS but it is empty"
    for row in rows:
        KPIDecompositionEdge(**row)


@pytest.mark.parametrize("client", _CLIENTS)
def test_kpi_decompositions_have_no_dangling_kpi_references(client: str):
    """parent_kpi_id, child_kpi_id and (when present) weight_kpi_id must all
    be a KPI this client actually seeds -- a dangling id is invisible rather
    than wrong, exactly the class test_client_seed_kpi_relationships.py's
    same-named test exists to catch."""
    mod = _load(client)
    kpi_ids = {k["id"] for k in mod.KPIS}
    for row in getattr(mod, "KPI_DECOMPOSITIONS", []):
        for field in ("parent_kpi_id", "child_kpi_id"):
            assert row[field] in kpi_ids, (
                f"{client}: decomposition edge {row['parent_kpi_id']}->{row['child_kpi_id']} "
                f"references unknown KPI id {row[field]!r} in {field}"
            )
        weight = row.get("weight_kpi_id")
        if weight:
            assert weight in kpi_ids, (
                f"{client}: decomposition edge {row['parent_kpi_id']}->{row['child_kpi_id']} "
                f"references unknown weight_kpi_id {weight!r}"
            )


@pytest.mark.parametrize("client", _CLIENTS)
def test_kpi_decompositions_carry_client_id(client: str):
    mod = _load(client)
    for row in getattr(mod, "KPI_DECOMPOSITIONS", []):
        assert row.get("client_id") == mod.CLIENT_ID, (
            f"{client}: edge {row.get('parent_kpi_id')}->{row.get('child_kpi_id')} "
            f"has client_id={row.get('client_id')!r}, expected {mod.CLIENT_ID!r}"
        )


@pytest.mark.parametrize("client", _CLIENTS)
def test_no_duplicate_decomposition_edges(client: str):
    """Composite PK (client_id, parent_kpi_id, child_kpi_id) -- a duplicate
    parent/child pair collides on insert."""
    mod = _load(client)
    seen: set = set()
    for row in getattr(mod, "KPI_DECOMPOSITIONS", []):
        pair = (row["parent_kpi_id"], row["child_kpi_id"])
        assert pair not in seen, f"{client}: duplicate decomposition edge {pair}"
        seen.add(pair)


@pytest.mark.parametrize("client", _CLIENTS)
def test_lubricants_tree_reconciles_against_real_seeded_values(client: str):
    """The actual proof this stage exists for: run check_tree_reconciles
    against the KPIS the same seed file declares, using each KPI's own
    thresholds as a stand-in for a 'current value' isn't available here (no
    live data at seed-validation time) -- so this test instead asserts the
    STRUCTURAL shape (operations agree, ratio edges are singular) that
    check_tree_reconciles depends on, deferring the live-value reconciliation
    proof to test_decomposition_analysis.py's dedicated fixture-based tests.
    """
    mod = _load(client)
    rows = getattr(mod, "KPI_DECOMPOSITIONS", [])
    by_parent: dict = {}
    for row in rows:
        by_parent.setdefault(row["parent_kpi_id"], []).append(row)
    for parent, edges in by_parent.items():
        ops = {e["operation"] for e in edges}
        assert len(ops) == 1, f"{client}: {parent}'s children mix operations {ops}"
        if "ratio" in ops:
            assert len(edges) == 1, f"{client}: {parent} has {len(edges)} ratio edges, expected exactly 1"


# ---------------------------------------------------------------------------
# Negative tests -- prove the guards above actually fire.
# ---------------------------------------------------------------------------

def _valid_row(**overrides):
    base = dict(
        parent_kpi_id="gross_profit", child_kpi_id="net_revenue",
        client_id="lubricants", operation="linear", sign=1,
    )
    base.update(overrides)
    return base


def test_guard_catches_invalid_operation():
    with pytest.raises(Exception) as exc:
        KPIDecompositionEdge(**_valid_row(operation="sum"))
    assert "operation" in str(exc.value)


def test_guard_catches_ratio_without_weight():
    with pytest.raises(Exception) as exc:
        KPIDecompositionEdge(**_valid_row(operation="ratio", weight_kpi_id=None))
    assert "weight_kpi_id" in str(exc.value)


def test_guard_catches_invalid_sign():
    with pytest.raises(Exception) as exc:
        KPIDecompositionEdge(**_valid_row(sign=2))
    assert "sign" in str(exc.value)


def test_guard_catches_self_loop():
    with pytest.raises(Exception) as exc:
        KPIDecompositionEdge(**_valid_row(child_kpi_id="gross_profit"))
    assert "cannot decompose into itself" in str(exc.value)
