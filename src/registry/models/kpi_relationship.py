"""KPI relationship model for compound alert detection (Phase 11I-B)
and causal-graph typing (Phase 15 Stage D/E)."""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class KPIRelationship(BaseModel):
    """Declared relationship between two KPIs for compound alert detection,
    extended with causal typing for the theory layer (Phase 15 Stage D/E).

    causal_rung and provenance are separate axes -- see
    docs/architecture/theory_layer_design.md §4 and the migration
    20260723_theory_layer_causal_schema.sql for the full rationale.
    """
    kpi_id: str = Field(..., description="Primary KPI identifier")
    related_kpi_id: str = Field(..., description="Related KPI identifier")
    client_id: str = Field(..., description="Client/tenant this relationship belongs to")
    relationship_type: Literal["volume_margin", "receivables_revenue", "cost_revenue", "custom"] = Field(
        ..., description="Class of relationship"
    )
    conflict_direction: Literal["diverging", "converging"] = Field(
        ...,
        description=(
            "'diverging' = opposite movements signal a problem (revenue UP / margin DOWN); "
            "'converging' = same-direction movements signal a problem (receivables UP / revenue UP)"
        )
    )
    description: Optional[str] = Field(None, description="Human-readable description of the relationship")

    # --- Phase 15 Stage D/E: causal-graph typing ---
    mechanism: Optional[str] = Field(
        None, description="Free-text causal pathway, e.g. 'input cost pass-through, inventory-buffered'"
    )
    lag_periods: Optional[int] = Field(
        None, description="Lag in months between cause and effect. Prefer Granger-derived values on va_validated edges over guesses."
    )
    causal_rung: Optional[Literal["correlational", "intervention_hypothesized", "intervention_tested"]] = Field(
        None,
        description=(
            "Pearl ladder-of-causation rung actually established: correlational (SA/DA association) | "
            "intervention_hypothesized (SF proposed, untested) | intervention_tested (VA ran DiD on this edge)."
        ),
    )
    provenance: Literal["template", "confirmed", "hitl_proposed", "va_validated"] = Field(
        "template",
        description=(
            "How this edge was captured. Consumption rule: SF must caveat or ignore 'template' edges; "
            "language on 'va_validated' edges capped at 'consistent with' -- never 'proved'."
        ),
    )
    confidence: Optional[Literal["high", "moderate", "low"]] = Field(
        None, description="Categorical, matching SolutionAssumption.confidence -- deliberately not a float."
    )

    # --- kpi_relationship_basis_design.md §2 (designed 2026-08-21, built 2026-08-30) ---
    basis: Literal["accounting_identity", "causal_estimate"] = Field(
        "causal_estimate",
        description=(
            "Whether this edge is TRUE BY CONSTRUCTION (accounting_identity -- e.g. "
            "gross_margin_pct is calculated FROM cogs; base_oil_cost is an "
            "account_category component summing INTO cogs) or a genuinely uncertain "
            "empirical claim (causal_estimate). There is no 'confidence' in "
            "arithmetic, which is why the identity edges correctly carry "
            "confidence=None/causal_rung=None -- but that ABSENCE was the only "
            "signal distinguishing them, and it collides with a real causal edge "
            "that simply hasn't been graded yet (product_sales_revenue<->cogs, live "
            "in the lubricants seed, is exactly that case). Defaults to "
            "causal_estimate so no existing edge silently upgrades itself to "
            "'certain'. Consumed by the theory-layer exhibit to separate what is "
            "certain from what is asserted -- the distinction that exhibit exists "
            "to show, so it must be a RECORDED fact, never inferred from the "
            "absence of other fields."
        ),
    )

    # --- causal_edge_direction_and_magnitude_design.md (Aug 2026) ---
    causal_direction: Literal["kpi_causes_related", "related_causes_kpi", "bidirectional", "unknown"] = Field(
        "unknown",
        description=(
            "Which end of the edge is upstream. Default 'unknown' preserves pre-existing "
            "undirected behavior for any edge not yet reviewed -- an edge that hasn't been "
            "classified doesn't silently become wrong, it just can't be used as a stepping "
            "stone for a multi-hop framing-gate alternative (see "
            "A9_Deep_Analysis_Agent._build_framing_prompt). get_causal_neighbourhood's BFS "
            "itself stays undirected -- SA's compound-alert detection is right that two KPIs "
            "breaching together are worth flagging regardless of which is upstream; this field "
            "is consumed only by the framing-gate-specific path-validity check."
        ),
    )

    @model_validator(mode="after")
    def _intervention_tested_requires_va_validated(self) -> "KPIRelationship":
        """Epistemic guardrail (2026-07-26): human confirmation is agreement
        with a narrative, not a statistical test. 'confirmed' provenance must
        never be able to claim the intervention_tested rung -- only VA
        actually running DiD/Granger causality on THIS edge earns it. Mirrors
        the DB CHECK constraint (kpi_relationships_tested_requires_va_validated)
        -- enforced here too so this can never be silently bypassed by code
        that constructs the model without going through the DB write path."""
        if self.causal_rung == "intervention_tested" and self.provenance != "va_validated":
            raise ValueError(
                "causal_rung='intervention_tested' requires provenance='va_validated' — "
                "HITL confirmation alone can never establish a tested causal claim"
            )
        return self
