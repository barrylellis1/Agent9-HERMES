"""Validate every client seed file's PORTS rows (Phase 17 T4).

Mirrors test_client_seed_kpi_decompositions.py's own rationale: seed data
has zero automated coverage otherwise. Imports the seed module directly (no
DB, no network), so it runs in the normal fast unit suite.
"""
from __future__ import annotations

import importlib

import pytest

from src.registry.models.port import Port

# Only lubricants exports PORTS as of Phase 17 T4.
_CLIENTS = ["lubricants"]


def _load(client: str):
    return importlib.import_module(f"scripts.clients.{client}")


@pytest.mark.parametrize("client", _CLIENTS)
def test_ports_pass_model_validation(client: str):
    mod = _load(client)
    rows = getattr(mod, "PORTS", [])
    assert rows, f"{client} exports PORTS but it is empty"
    for row in rows:
        Port(**row)


@pytest.mark.parametrize("client", _CLIENTS)
def test_ports_have_no_dangling_kpi_references(client: str):
    """linked_kpi_id must be a KPI this client actually seeds -- a dangling
    id is invisible rather than wrong."""
    mod = _load(client)
    kpi_ids = {k["id"] for k in mod.KPIS}
    for row in getattr(mod, "PORTS", []):
        assert row["linked_kpi_id"] in kpi_ids, (
            f"{client}: port {row['name']!r} references unknown KPI id {row['linked_kpi_id']!r}"
        )


@pytest.mark.parametrize("client", _CLIENTS)
def test_ports_carry_client_id(client: str):
    mod = _load(client)
    for row in getattr(mod, "PORTS", []):
        assert row.get("client_id") == mod.CLIENT_ID, (
            f"{client}: port {row.get('name')} has client_id={row.get('client_id')!r}, "
            f"expected {mod.CLIENT_ID!r}"
        )


@pytest.mark.parametrize("client", _CLIENTS)
def test_no_duplicate_port_per_kpi_and_type(client: str):
    """Composite uniqueness (client_id, linked_kpi_id, port_type) -- a duplicate collides on insert."""
    mod = _load(client)
    seen: set = set()
    for row in getattr(mod, "PORTS", []):
        key = (row["linked_kpi_id"], row["port_type"])
        assert key not in seen, f"{client}: duplicate port {key}"
        seen.add(key)


# ---------------------------------------------------------------------------
# Negative tests -- prove the guards above actually fire.
# ---------------------------------------------------------------------------

def _valid_row(**overrides):
    base = dict(
        client_id="lubricants", name="Base Oil Price", port_type="input_costs",
        linked_kpi_id="base_oil_cost",
    )
    base.update(overrides)
    return base


def test_guard_catches_invalid_port_type():
    with pytest.raises(Exception) as exc:
        Port(**_valid_row(port_type="commodity_price"))
    assert "port_type" in str(exc.value)


def test_guard_catches_invalid_source():
    with pytest.raises(Exception) as exc:
        Port(**_valid_row(source="llm_guess"))
    assert "source" in str(exc.value)


def test_all_six_port_types_are_valid():
    for pt in ("input_costs", "demand_volume", "price_realization",
               "capital_cost", "talent_supply", "regulatory_constraint"):
        assert Port(**_valid_row(port_type=pt)).port_type == pt
