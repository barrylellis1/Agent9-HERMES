"""KPI decomposition model -- arithmetic parentage (Phase 17 T2).

DEVELOPMENT_PLAN.md Phase 17, "RESOLVED: derive the structure, author the
presentation": the Core Spine's GRAPH -- what decomposes into what -- is
DERIVED from this model; its LAYOUT (collapse/order/emphasis) is a separate,
optional presentation layer this model deliberately does NOT hold, so a
restated fact can never drift from the KPI definition it restates (the
"stale diagram" failure mode the same design section names).

Distinct from KPIRelationship (the kpi_relationships table): that models
CAUSAL claims between KPIs -- uncertain, gradeable, carrying
confidence/provenance/causal_rung. This models ARITHMETIC parentage -- true
by construction from the KPI's own formula, not a claim that could be wrong
in the causal sense. This table IS the "accounting_identity" concept
docs/architecture/kpi_relationship_basis_design.md proposes splitting out of
kpi_relationships (that edge type is conflated there today); a formal home
for it here is what that design note was arguing kpi_relationships needed.

'linear', 'ratio', and 'product' are modelled -- deliberately, not a general
expression tree. A KPI's OWN reported value already carries its intended
sign (e.g. the `cogs` KPI negates its raw signed amount to report a positive
cost magnitude, per KPI.sign_convention) -- so "gross_profit decomposes into
net_revenue and cogs" is not a plain sum of KPI values, it's
`net_revenue - cogs`. `sign` on each edge carries exactly that: whether this
child ADDS to or SUBTRACTS from the parent, using each KPI's own reported
(already-sign-converted) value. A bare 'difference' literal was considered
and dropped -- 'linear' (a signed sum, which subsumes plain addition and
subtraction alike via `sign`) covers every FI decomposition this stage
seeds, and does not need an arbitrary "first child minus the rest" ordering
convention the way a bare 'difference' literal would.

'product' was added 2026-09-02 for the first genuinely cross-data-product
decomposition: `net_revenue = sales_order_count * average_order_value`
(dp_lubricants_sales -> dp_lubricants_financials), verified live as an exact
identity on the Sales side (average_order_value is DEFINED as
SAFE_DIVIDE(SUM(net_amount), COUNT(DISTINCT sales_order_id)), so the product
is tautological, not estimated). Multiplication itself needs no ordering
convention (it's commutative, unlike a bare 'difference'), but see
src/analysis/decomposition.py's `variance_bridge` docstring for a real,
separate finding this addition surfaced: attributing a MOVE between two
periods to each factor of a product (or a ratio) is order-dependent even
though the multiplication/division itself is not -- a distinct concern from
this model's own shape.
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator


class KPIDecompositionEdge(BaseModel):
    """One parent/child arithmetic edge: `parent_kpi_id` decomposes (in
    part) into `child_kpi_id`.

    'linear': the parent is the signed sum of its direct children's OWN
    reported values -- `parent = sum(sign_i * child_value_i)`. E.g.
    gross_profit's two edges: net_revenue (sign=+1), cogs (sign=-1) ->
    gross_profit = net_revenue - cogs (cogs's own KPI value is already a
    positive cost magnitude, per its sign_convention).

    'ratio': the parent is one child divided by a weight KPI -- a parent
    has exactly one 'ratio' edge, carrying the denominator's kpi_id in
    `weight_kpi_id`. E.g. gross_margin_pct's ratio edge names gross_profit
    as child_kpi_id and net_revenue as weight_kpi_id
    (gross_margin_pct = 100 * gross_profit / net_revenue -- the 100x
    percent-scaling is a display convention, checked via KPI.unit_class by
    src/analysis/decomposition.py, not stored on the edge itself).

    'product': the parent is the product of ALL its direct children's own
    reported values -- `parent = child_1 * child_2 * ...`. E.g.
    net_revenue's two edges: sales_order_count and average_order_value ->
    net_revenue = sales_order_count * average_order_value. `sign` is
    ignored for 'product', same as for 'ratio'.
    """
    parent_kpi_id: str = Field(..., description="The KPI being decomposed")
    child_kpi_id: str = Field(..., description="One component of the parent")
    client_id: str = Field(..., description="Client/tenant this edge belongs to")
    operation: Literal["linear", "ratio", "product"] = Field(
        ...,
        description=(
            "'linear': this child contributes sign * child_value to a signed sum "
            "that produces the parent. 'ratio': child_kpi_id / weight_kpi_id = "
            "parent (weight_kpi_id required; a parent has exactly one such edge). "
            "'product': all of the parent's 'product' children multiply together "
            "to produce the parent."
        ),
    )
    sign: int = Field(
        1,
        description="For operation='linear' only: +1 if this child ADDS to the parent, -1 if it SUBTRACTS. Ignored for 'ratio'.",
    )
    weight_kpi_id: Optional[str] = Field(
        None,
        description="Required when operation='ratio': the denominator KPI id.",
    )

    @model_validator(mode="after")
    def _validate_shape(self) -> "KPIDecompositionEdge":
        if self.operation == "ratio" and not self.weight_kpi_id:
            raise ValueError(
                "operation='ratio' requires weight_kpi_id (the denominator KPI) -- "
                "a ratio edge is meaningless without it"
            )
        if self.sign not in (1, -1):
            raise ValueError("sign must be 1 or -1")
        if self.parent_kpi_id == self.child_kpi_id:
            raise ValueError("parent_kpi_id and child_kpi_id must differ -- a KPI cannot decompose into itself")
        return self
