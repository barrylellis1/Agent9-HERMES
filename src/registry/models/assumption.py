"""Theory layer assumption/constraint/explanation register (Phase 15 Stage D/E).

One table, one model, not three -- record_type discriminates. This mirrors the
Stage B unification of SolutionAssumption (11J P1's typed assumption and SF's
"bets on" list are the same object) applied one level up: an assumption, a
constraint, and an explanation are all "a claim about this client, sourced
somehow, with a lifecycle" -- they differ in what the lifecycle states mean,
not in shape. See docs/architecture/theory_layer_design.md §5.5.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class Assumption(BaseModel):
    id: Optional[str] = Field(None, description="UUID, server-generated on insert")
    client_id: str = Field(..., description="Client/tenant this record belongs to")
    scope: str = Field(
        ..., description="What this attaches to -- typically a kpi_id or a monitoring-profile threshold identifier"
    )
    record_type: Literal["assumption", "constraint", "explanation"] = Field(
        "assumption",
        description=(
            "assumption = a belief that might be wrong. constraint = a stated prohibition "
            "(from SF-rejection HITL). explanation = why a situation is suppressed -- requires expiry."
        ),
    )
    text: str = Field(..., description="The claim itself, in plain language")
    status: Literal["active", "held", "falsified", "lifted"] = Field(
        "active",
        description="assumption/explanation use active|held|falsified; constraint uses active|lifted",
    )
    source: Literal["sa_hitl", "sf_hitl_rejection", "sf_hitl_approval", "va_hitl", "manual"] = Field(
        ..., description="Which HITL surface produced this record"
    )
    provenance: Literal["template", "confirmed", "hitl_proposed", "va_validated"] = Field(
        "hitl_proposed", description="Same provenance ladder as KPIRelationship -- how this was captured"
    )
    confidence: Optional[Literal["high", "moderate", "low"]] = None
    expiry: Optional[str] = Field(
        None,
        description=(
            "ISO datetime. MANDATORY for record_type='explanation' -- self-falsification, "
            "never indefinite suppression (theory doc §5.1, §9 pre-mortem #5). Enforced here "
            "AND at the DB layer (CHECK constraint) so no write path can skip it."
        ),
    )
    linked_situation_id: Optional[str] = None
    linked_solution_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @model_validator(mode="after")
    def _explanation_requires_expiry(self) -> "Assumption":
        if self.record_type == "explanation" and not self.expiry:
            raise ValueError(
                "explanation records must carry an expiry — indefinite suppression without "
                "self-falsification is 'snooze with better paperwork' (theory doc §5.1/§9 pre-mortem #5)"
            )
        return self
