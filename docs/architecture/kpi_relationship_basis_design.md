# KPI Relationship `basis` — Separating Accounting Identity from Causal Estimate

**Created:** 2026-08-21
**Status:** Design note, not built
**Triggered by:** the waterfall-chart question on the Framing Evidence Map mockup
(`docs/architecture/ui_refinement_plan.md`'s sibling conversation) — whether a waterfall would
work for causal-graph alternatives. Answer: not for causal estimates, but for the subset of
`KPIRelationship` edges that are actually accounting identities, yes — and the model has no way
to say which is which today.

---

## 1. The finding

`KPIRelationship` treats every edge as the same kind of thing: a `causal_rung`
(`correlational`/`intervention_hypothesized`/`intervention_tested`), a `confidence` tier, a
`provenance` (`template`/`confirmed`/`hitl_proposed`/`va_validated`), a `mechanism` sentence.
That vocabulary is right for a genuinely uncertain claim about the world — COGS rising *because*
a commodity price moved is a claim that could be wrong. It is the wrong vocabulary for an edge
that is true by construction: Gross Margin % is *calculated from* Net Revenue and COGS. There is
no "confidence" in `(Revenue − COGS) / Revenue`; it is arithmetic, not evidence.

**This is already partially recognised in the codebase, not a new observation.** The
`net_revenue↔gross_margin_pct` edge's own comment (`scripts/clients/lubricants.py:768-779`,
corrected 2026-08-20) reasons through exactly this: *"Gross Margin % is CALCULATED FROM Net
Revenue and COGS... a derived ratio isn't an upstream cause of one of its own inputs."* And the
three Sales-KPI edges added the same day (`units_sold`/`sales_order_count`/`average_order_value`
→ `net_revenue`) carry a comment doing the opposite check correctly: *"NOT arithmetic in
disguise, despite Sales SUM(net_amount) reconciling to net_revenue exactly by construction...
each is ONE factor (volume, order frequency, price/mix), not the whole story."* Someone was
already asking the right question edge by edge. What's missing is a field that records the
answer, so every consumer of this table doesn't have to re-derive it from a comment.

### The operational test, already used informally — worth making explicit

The Sales-edge comment states the test without naming it: **does knowing the "causing" KPI's
value, together with whatever else is already known, fully determine the "caused" KPI's value —
or does it leave genuine uncertainty?** Gross Margin % is fully determined by Net Revenue and
COGS — nothing else can move it. `units_sold` rising does *not* by itself tell you `net_revenue`
rose — price or mix could move the other way. That is the real distinction, and it is sharper
than "which schema is this KPI in" (the practical proxy raised in conversation): schema
membership is a good heuristic — FI-schema KPIs sitting on a shared chart-of-accounts are usually
identities, Operational-schema KPIs are usually estimates — but the invariant underneath is
determinism, not the schema boundary itself. A future FI-schema KPI could still be an estimate
(a forecast ratio, say), and the test should be applied per edge, not inferred from which data
product either side lives in.

### Three edges misclassified today, found by applying that test

Checked directly against `scripts/clients/lubricants.py`, not asserted from memory:

| Edge | Current treatment | What it actually is |
|---|---|---|
| `net_revenue → gross_margin_pct` | `causal_rung: correlational`, `confidence: high`, `provenance: confirmed` | **Accounting identity.** `gross_margin_pct = (net_revenue − cogs) / net_revenue`. Direction is already correct (fixed 2026-08-20); the *epistemic category* is still wrong — this edge carries zero uncertainty, and labelling it "high confidence" alongside a genuinely uncertain edge like `premium_mix_pct → gross_margin_pct` (`provenance: template`, `confidence: moderate`) makes them look like the same kind of fact when they aren't. |
| `gross_margin_pct → cogs` | Same treatment; `mechanism` describes "base oil price volatility passes through to COGS with a lag" | **Also an identity** — COGS is the other direct input to the same formula. **Plus a second, distinct problem**: the mechanism text isn't describing the COGS→margin% arithmetic at all — it's describing a genuinely causal claim about an *external* commodity price affecting a ledger line, one hop removed from what this edge actually connects. |
| `base_oil_cost → cogs`, `distribution_cost → cogs` | `causal_rung: correlational`, `confidence: high`, `provenance: confirmed`, mechanism cites "inventory-buffered lag," "trucking spot rates" | **Both accounting identities, confirmed by their own SQL.** `base_oil_cost` is `SUM(amount) WHERE account_category = 'Raw Materials'`; `distribution_cost` is `SUM(amount) WHERE account_category = 'Distribution'` — both are `account_category` sub-slices *within* `cogs`'s own `account_type = 'COGS'` bucket. COGS literally equals the sum of its `account_category` components. The lag/pass-through story in each mechanism is real, but it describes something these edges don't actually encode: an *external* commodity or logistics-market driver moving a ledger line's dollar value, not the ledger line summing into its own parent total. |

**Correctly classified today, for contrast:** `units_sold`/`sales_order_count`/
`average_order_value` → `net_revenue`, and `premium_mix_pct → gross_margin_pct` — each is a real
factor that leaves genuine uncertainty even when known, `provenance` and `confidence` mean what
they say, and the mechanism text describes the actual edge, not a one-hop-removed one.

---

## 2. Proposed fix: a `basis` field on `KPIRelationship`

```python
basis: Literal["accounting_identity", "causal_estimate"] = Field(
    "causal_estimate",
    description=(
        "accounting_identity: the related KPI is an arithmetic input/component of this "
        "one (or vice versa) -- true by construction, no confidence applies. "
        "causal_estimate: a believed real-world mechanism -- confidence/mechanism/"
        "provenance are meaningful because the claim could be wrong."
    ),
)
```

Default `causal_estimate` so every existing edge that hasn't been explicitly reclassified keeps
its current meaning rather than silently downgrading to "certain."

**Consequences of the field, not just its presence:**

- **Rendering.** This is what should decide the Framing Evidence Map's chart choice, not schema
  membership: `accounting_identity` edges render as a waterfall/spine bar (exact, computed, no
  confidence badge — a fifth visual state distinct from the emerald/amber/red confidence tiers,
  since "certain" isn't a point on that scale, it's off it). `causal_estimate` edges keep the
  causal-graph node treatment already mocked up (hop distance, direction arrow, confidence,
  mechanism, provenance caveat).
- **Validation, not just display.** `confidence`/`provenance`/`causal_rung` should arguably become
  conditionally-required-absent for `accounting_identity` edges the same way
  `Assumption._explanation_requires_expiry` already conditionally validates fields by record
  shape — an identity edge that still carries `confidence: "high"` is a modelling error, not a
  legitimate data point, and a validator can catch it instead of relying on someone noticing the
  comment mismatch by eye, the way this note had to.
- **Phase 17's Core Spine readiness is better than its own audit says, for the FI subset.** That
  audit (`DEVELOPMENT_PLAN.md` Phase 17) says Core Spine is "NOT built... no `parent_kpi`/
  `contributes_to` model exists." True for a generic cross-KPI decomposition model. Not quite
  true for the FI-schema subset specifically: every FI KPI's `sql_query`/`filters` already
  encodes its `account_type`/`account_category` membership (`scripts/clients/lubricants.py`,
  confirmed live) — that *is* an informal decomposition model, already summing correctly in SQL,
  today, for every FI KPI. Formalising `basis: accounting_identity` on the edges that already sit
  inside that structure is a much narrower lift than Phase 17's T2 prerequisite as originally
  scoped — it's labelling an existing correct arithmetic relationship, not inventing a new one.
  This doesn't unblock all of Phase 17 (Assumptions grading and the Port model are untouched by
  this), but it makes the Core Spine section of that exhibit meaningfully closer for the
  FI-anchored KPIs specifically.

---

## 3. What this does *not* solve

The `gross_margin_pct → cogs` and `*_cost → cogs` mechanism-text mismatch is a second, related
but distinct problem this field doesn't fix by itself: the *real* causal story in those
mechanisms (commodity price → ledger line, with a lag) has no KPI to attach to today. Reassigning
those edges to `basis: accounting_identity` is correct, but it also means the genuinely causal
claim currently riding along in their `mechanism` text needs a new home — either a real external
"base oil spot price" driver KPI (if the warehouse ever carries one) or routing through the same
Market Analysis external-port channel the Framing Evidence Map already has a lane for (§2 of that
conversation's mockup). Not scoped further here; flagged so it isn't lost.

---

## 4. Not built

This is a design note only. Reclassifying live edges (`net_revenue↔gross_margin_pct`,
`gross_margin_pct↔cogs`, `base_oil_cost→cogs`, `distribution_cost→cogs`) changes what the
framing gate has been showing in production since 2026-08-20 — needs explicit confirmation
before touching the seed file, the model, or a migration, same as every other schema change this
session.
