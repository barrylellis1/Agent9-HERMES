"""External-world port model (Phase 17 T4). docs/architecture/theory_layer_design.md §2.3.

External forces enter a business through a small, enumerable set of ports --
input costs, demand volume, price realization, capital cost, talent supply,
regulatory constraint -- each with a characteristic LAG (how long before the
attached KPI actually moves) and BUFFER (what absorbs the shock before it
reaches the ledger: inventory buffers a commodity move, backlog buffers a
demand move, contracts buffer a price move).

This is the model gap the design doc names explicitly for the Lubricants
anchor scenario: "The genuinely causal base-oil-price story... has no KPI to
attach to yet." Base oil SPOT PRICE is not itself a registered KPI (it's an
external field, not a measured internal metric) -- `linked_kpi_id` is the
INTERNAL side only (the KPI this port enters at, e.g. `base_oil_cost`); the
external fact itself lives in `current_signal`, in plain language, same
posture as `KPIRelationship.mechanism`.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class Port(BaseModel):
    id: Optional[str] = Field(None, description="UUID, server-generated on insert")
    client_id: str = Field(..., description="Client/tenant this port belongs to")
    name: str = Field(..., description="Human-readable name, e.g. 'Base Oil Price'")
    port_type: Literal[
        "input_costs", "demand_volume", "price_realization",
        "capital_cost", "talent_supply", "regulatory_constraint",
    ] = Field(..., description="Which of the six enumerable port types this is (theory_layer_design.md §2.3)")
    linked_kpi_id: str = Field(
        ..., description="The INTERNAL KPI this external force enters at (e.g. base_oil_cost) -- not the external field itself, which is not a registered KPI"
    )
    lag_periods: Optional[int] = Field(
        None, description="Months between the external move and the linked KPI's own move"
    )
    buffer_description: Optional[str] = Field(
        None, description="What absorbs the shock before it reaches the ledger -- inventory layers, hedges, contracts, backlog"
    )
    current_signal: Optional[str] = Field(
        None,
        description=(
            "The actual observed external-world fact, in plain language -- same posture as "
            "KPIRelationship.mechanism (human/LLM-authored, nothing writes theory autonomously). "
            "Populated by a human/seed today; a live MA-agent write path is a follow-up, not built."
        ),
    )
    source: Literal["ma_query", "manual"] = Field(
        "manual", description="'ma_query' = a live Market Analysis re-query populated this (not wired yet); 'manual' = hand-entered/seeded"
    )
