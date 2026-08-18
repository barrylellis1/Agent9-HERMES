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
    record_type: Literal["assumption", "constraint", "explanation", "framing"] = Field(
        "assumption",
        description=(
            "assumption = a belief that might be wrong. constraint = a stated prohibition "
            "(from SF-rejection HITL). explanation = why a situation is suppressed -- requires expiry. "
            "framing = a human-chosen problem objective (Phase 19) -- event-scoped via expiry_event, "
            "not date-scoped via expiry."
        ),
    )
    text: str = Field(..., description="The claim itself, in plain language")
    status: Literal["active", "held", "falsified", "lifted"] = Field(
        "active",
        description="assumption/explanation use active|held|falsified; constraint uses active|lifted",
    )
    source: Literal["sa_hitl", "sf_hitl_rejection", "sf_hitl_approval", "va_hitl", "manual", "da_hitl"] = Field(
        ..., description="Which HITL surface produced this record"
    )
    provenance: Literal["template", "confirmed", "hitl_proposed", "va_validated"] = Field(
        "hitl_proposed", description="Same provenance ladder as KPIRelationship -- how this was captured"
    )
    confidence: Optional[Literal["high", "moderate", "low"]] = None
    validated_by: Optional[Literal["sa_assessment", "ma_query", "human_confirmation"]] = Field(
        None,
        description=(
            "Who/what can render a verdict on this claim, carried over from "
            "SolutionAssumption.validated_by. This is the routing key for grading: "
            "'sa_assessment' and 'ma_query' are machine-checkable from KPI data / an MA "
            "re-query, so only 'human_confirmation' rows need to reach a person. Without "
            "that split every solution puts its full assumption list in front of an "
            "executive and adjudication quietly stops happening (theory doc §9 pre-mortem #3)."
        ),
    )
    falsification_criterion: Optional[str] = Field(
        None,
        description=(
            "What observation would confirm or falsify this claim, in plain language. "
            "Carried over from SolutionAssumption.provenance -- deliberately NOT named "
            "`provenance` here, because that name is already taken above by the capture "
            "ladder and the two mean entirely different things. Language capped at "
            "'consistent with', never 'proved' (theory doc §4)."
        ),
    )
    expiry: Optional[str] = Field(
        None,
        description=(
            "ISO datetime. MANDATORY for record_type='explanation' -- self-falsification, "
            "never indefinite suppression (theory doc §5.1, §9 pre-mortem #5). Enforced here "
            "AND at the DB layer (CHECK constraint) so no write path can skip it. Stays None "
            "for record_type='framing' -- that record's expiry is event-based, see expiry_event."
        ),
    )
    expiry_event: Optional[Literal["va_verdict_on_linked_solution"]] = Field(
        None,
        description=(
            "Event-based expiry trigger for record_type='framing' (problem_framing_design.md §8 "
            "item 3): the frame expires when Value Assurance resolves the bet on the solution it "
            "governed -- validated OR failed, either outcome is a genuine re-examination trigger. "
            "Deliberately NOT a date -- `expiry` is typed as an ISO datetime and cannot express "
            "'when VA renders a verdict', which is why this is a separate field rather than an "
            "overload of `expiry`. A frame whose solution is never approved never expires via this "
            "mechanism -- the un-backstopped case named in the design doc, carried forward not "
            "solved here."
        ),
    )
    linked_situation_id: Optional[str] = None
    linked_solution_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    # --- record_type='framing' attribution (Phase 19) ---------------------
    # Discovered mid-implementation (Slice 2, 2026-08-18): building the
    # framing-gate's PriorFrameRecord re-presentation ("show a prior frame
    # WITH its reasoning, never pre-ticked") needs to know WHICH kind of
    # choice was made and WHO made it relative to KPI ownership — neither is
    # recoverable from the fields above without parsing `text` as prose,
    # which this codebase's discipline treats as unacceptable (never infer
    # what should be recorded explicitly). Generic field names, not
    # framing-specific ones, in case a future HITL surface wants the same
    # "who decided, and were they the owner" attribution.
    framing_choice: Optional[Literal["confirm_stated", "alternative", "other"]] = Field(
        None,
        description=(
            "Which kind of framing decision this was — mirrors FramingDecision.choice. "
            "Only populated for record_type='framing'. Needed so a prior frame can be "
            "re-presented accurately rather than re-derived by comparing text strings."
        ),
    )
    decided_by_role: Optional[str] = Field(
        None, description="The role that submitted this decision — server-computed from principal_context, never client-claimed"
    )
    decided_by_is_owner: Optional[bool] = Field(
        None, description="Whether decided_by_role matched the KPI's owner_role at submission time (Decision #5: non-owners may submit, with attribution)"
    )

    @model_validator(mode="after")
    def _explanation_requires_expiry(self) -> "Assumption":
        if self.record_type == "explanation" and not self.expiry:
            raise ValueError(
                "explanation records must carry an expiry — indefinite suppression without "
                "self-falsification is 'snooze with better paperwork' (theory doc §5.1/§9 pre-mortem #5)"
            )
        return self
