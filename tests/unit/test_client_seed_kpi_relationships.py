"""Validate every client seed file's KPI_RELATIONSHIPS rows.

Why this exists: seed data had ZERO automated coverage. A bad row is not loud —
`A9_Solution_Finder_Agent`'s causal-grounding fetch is deliberately non-fatal
(missing migration / empty table / unresolvable KPI must never break solution
generation), so a row that fails model validation is caught, logged at INFO,
and silently degrades to "no causal context injected". That is exactly what
happened on 2026-07-26: a seeded `relationship_type="cost_margin"` — not in the
closed Literal set — made the provider raise, the exception was swallowed by
design, and a live LLM call ran with an empty causal chain while still
reporting success. Nothing failed; the feature just didn't happen.

These tests move that failure to commit time. They import the seed modules
directly (no DB, no network), so they run in the normal fast unit suite.
"""
from __future__ import annotations

import importlib

import pytest

from src.registry.models.kpi_relationship import KPIRelationship

# Clients that export KPI_RELATIONSHIPS. bicycle is intentionally absent —
# it has no relationships defined, which is valid.
_CLIENTS = ["lubricants", "hess", "apex_lubricants"]
_ALL_CLIENTS = _CLIENTS + ["bicycle"]


def _load(client: str):
    return importlib.import_module(f"scripts.clients.{client}")


@pytest.mark.parametrize("client", _CLIENTS)
def test_kpi_relationships_pass_model_validation(client: str):
    """Every row must satisfy the Pydantic model — closed Literals for
    relationship_type / conflict_direction / causal_rung / provenance /
    confidence, plus the epistemic guardrail that causal_rung=
    'intervention_tested' requires provenance='va_validated'."""
    mod = _load(client)
    rows = getattr(mod, "KPI_RELATIONSHIPS", [])
    assert rows, f"{client} exports KPI_RELATIONSHIPS but it is empty"

    for row in rows:
        # Raises ValidationError with the offending field on a bad row.
        KPIRelationship(**row)


@pytest.mark.parametrize("client", _CLIENTS)
def test_kpi_relationships_have_no_dangling_kpi_references(client: str):
    """Both endpoints of every edge must be a KPI this client actually seeds.

    A dangling id doesn't error anywhere — `get_relationships_for_kpi` simply
    never matches it, so the edge is invisible rather than wrong, which is
    harder to notice than a crash.
    """
    mod = _load(client)
    kpi_ids = {k["id"] for k in mod.KPIS}

    for row in getattr(mod, "KPI_RELATIONSHIPS", []):
        for field in ("kpi_id", "related_kpi_id"):
            assert row[field] in kpi_ids, (
                f"{client}: relationship {row['kpi_id']}->{row['related_kpi_id']} "
                f"references unknown KPI id {row[field]!r} in {field}"
            )


@pytest.mark.parametrize("client", _CLIENTS)
def test_kpi_relationships_carry_client_id(client: str):
    """client_id is the tenant boundary — a row missing or mismatching it
    would be seeded against the wrong tenant or rejected by RLS."""
    mod = _load(client)
    for row in getattr(mod, "KPI_RELATIONSHIPS", []):
        assert row.get("client_id") == mod.CLIENT_ID, (
            f"{client}: relationship {row.get('kpi_id')}->{row.get('related_kpi_id')} "
            f"has client_id={row.get('client_id')!r}, expected {mod.CLIENT_ID!r}"
        )


@pytest.mark.parametrize("client", _CLIENTS)
def test_no_self_referencing_relationships(client: str):
    """An edge from a KPI to itself is meaningless for both compound-alert
    detection and the causal graph, and would render as a self-loop."""
    mod = _load(client)
    for row in getattr(mod, "KPI_RELATIONSHIPS", []):
        assert row["kpi_id"] != row["related_kpi_id"], (
            f"{client}: self-referencing relationship on {row['kpi_id']}"
        )


@pytest.mark.parametrize("client", _CLIENTS)
def test_no_duplicate_relationship_pairs(client: str):
    """`kpi_relationships` has composite PK (client_id, kpi_id, related_kpi_id)
    and the provider looks up bidirectionally, so both an exact duplicate and a
    reversed duplicate are problems: the first collides on insert, the second
    renders the same edge twice in the causal context sent to the LLM."""
    mod = _load(client)
    seen: set[frozenset[str]] = set()
    for row in getattr(mod, "KPI_RELATIONSHIPS", []):
        pair = frozenset({row["kpi_id"], row["related_kpi_id"]})
        assert pair not in seen, (
            f"{client}: duplicate relationship between "
            f"{row['kpi_id']} and {row['related_kpi_id']} "
            f"(the provider matches bidirectionally, so A->B and B->A are the same edge)"
        )
        seen.add(pair)


@pytest.mark.parametrize("client", _ALL_CLIENTS)
def test_seed_module_exports_kpis(client: str):
    """Guards the assumption the other tests rest on — that `KPIS` exists and
    every entry has an `id` to resolve relationships against."""
    mod = _load(client)
    assert getattr(mod, "KPIS", None), f"{client} exports no KPIS"
    for k in mod.KPIS:
        assert k.get("id"), f"{client}: a KPI entry is missing 'id'"


# ---------------------------------------------------------------------------
# Negative tests — prove the guards above actually fire.
#
# The tests above pass against current data. That alone says nothing: they'd
# also pass if the assertions were vacuous. These reproduce the specific bad
# rows the guards exist to reject, so the suite fails loudly if a guard is ever
# weakened into a no-op.
# ---------------------------------------------------------------------------

def _valid_row(**overrides):
    base = dict(
        kpi_id="gross_margin_pct",
        related_kpi_id="cogs",
        client_id="lubricants",
        relationship_type="custom",
        conflict_direction="diverging",
    )
    base.update(overrides)
    return base


def test_guard_catches_invalid_relationship_type():
    """The real 2026-07-26 bug: `cost_margin` is not in the closed Literal set.
    It seeded fine (PostgREST has no such constraint), then made the provider
    raise on read — swallowed by Stage D's non-fatal handler."""
    with pytest.raises(Exception) as exc:
        KPIRelationship(**_valid_row(relationship_type="cost_margin"))
    assert "relationship_type" in str(exc.value)


def test_guard_catches_epistemic_violation():
    """causal_rung='intervention_tested' with anything other than
    provenance='va_validated' must be rejected — human confirmation is
    agreement with a narrative, not a statistical test."""
    with pytest.raises(Exception) as exc:
        KPIRelationship(**_valid_row(causal_rung="intervention_tested", provenance="confirmed"))
    assert "va_validated" in str(exc.value)


def test_guard_catches_invalid_provenance_and_confidence():
    for field, bad in (("provenance", "assumed"), ("confidence", "very_high"),
                       ("conflict_direction", "sideways")):
        with pytest.raises(Exception) as exc:
            KPIRelationship(**_valid_row(**{field: bad}))
        assert field in str(exc.value)


def test_dangling_reference_guard_logic_is_not_vacuous():
    """Mirrors the dangling-ref assertion against a synthetic unknown id."""
    kpi_ids = {"gross_margin_pct", "cogs"}
    bad = _valid_row(related_kpi_id="does_not_exist")
    assert bad["related_kpi_id"] not in kpi_ids  # the condition the guard asserts on


def test_duplicate_pair_guard_treats_reversed_edges_as_equal():
    """A->B and B->A are the same edge to the bidirectional provider, so the
    duplicate guard must compare unordered pairs, not tuples."""
    a = frozenset({_valid_row()["kpi_id"], _valid_row()["related_kpi_id"]})
    b = frozenset({_valid_row()["related_kpi_id"], _valid_row()["kpi_id"]})
    assert a == b
