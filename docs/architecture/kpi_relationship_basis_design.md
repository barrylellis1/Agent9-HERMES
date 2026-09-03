# KPI Relationship `basis` — Separating Accounting Identity from Causal Estimate

**Created:** 2026-08-21
**Status:** **§2 (`basis`), §4 (variance bridge) and §5 (panel structure) BUILT 2026-08-30**
(Phase 17 Stage 6). §3 (the Port-model gap) built the same day as Phase 17 T4 — see
`src/registry/models/port.py`. This note is now a record of decisions that shipped, not a
proposal; per-section status is stated in §6.
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
| `base_oil_cost → cogs` (`causal_rung: correlational`, `confidence: high`, `provenance: confirmed`), `distribution_cost → cogs` (`causal_rung: correlational`, `confidence: moderate`, `provenance: template`) | mechanism cites "inventory-buffered lag," "trucking spot rates" | **Both accounting identities, confirmed by their own SQL.** `base_oil_cost` is `SUM(amount) WHERE account_category = 'Raw Materials'`; `distribution_cost` is `SUM(amount) WHERE account_category = 'Distribution'` — both are `account_category` sub-slices *within* `cogs`'s own `account_type = 'COGS'` bucket. COGS literally equals the sum of its `account_category` components. The lag/pass-through story in each mechanism is real, but it describes something these edges don't actually encode: an *external* commodity or logistics-market driver moving a ledger line's dollar value, not the ledger line summing into its own parent total. |

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

## 4. The Spine mechanism, corrected: a variance bridge, not a composition bridge

The first mockup rendered Spine as a *composition* bridge — Net Revenue − COGS ÷ = Gross Margin
%, decomposing the current period's value into its inputs. Caught in conversation as the wrong
chart: the framing question is "why did this move, and is this the right KPI to be looking at" —
inherently about the *delta* between periods, not the current value's arithmetic. A composition
bridge doesn't answer that at all.

**The data already needed for the right chart is already fetched.** `NeighbourSnapshot`
(`deep_analysis_models.py:383-404`) carries `value` (current) *and* `comparison_value` (prior
period) for every neighbour, and the primary KPI's own `primary_snapshot` in the same shape.
Nothing new needs to reach the framing gate.

**The bridge, exact for two identity inputs — not approximate:**

```
margin%(R, C) = (R − C) / R

Revenue effect = margin%(R₁, C₀) − margin%(R₀, C₀)   -- swap revenue to current, COGS held at prior
COGS effect    = margin%(R₁, C₁) − margin%(R₁, C₀)   -- now swap COGS to current

Revenue effect + COGS effect = Current margin% − Prior margin%,  exactly -- no residual term
```

Illustrative numbers (not live — the mockup states this): R₀=100, C₀=65 → prior margin 35.0%;
R₁=110, C₁=77 → current margin 30.0%. Revenue effect = +5.9pp, COGS effect = −10.9pp, and they
sum to exactly the observed −5.0pp move. That closure is the property worth protecting: it holds
for exactly two identity inputs via sequential substitution. It stops holding automatically the
moment a third identity input joins the same bridge (splitting COGS into Raw Materials and
Distribution, say) — order of substitution then affects the split, and either a disclosed
convention or an order-independent method (Shapley) is needed. Not a problem today; a tripwire
for later.

**A gap this surfaces that `basis` alone doesn't close:** `accounting_identity` says an edge is
exact arithmetic, not *which* arithmetic — add, subtract, divide, in what order. Gross Margin %'s
formula is simple enough to hardcode as a first cut; a general mechanism needs the relationship
(or the KPI's own `sql_query`) to express the actual operation. Left as a known gap, not solved
here.

**Why `premium_mix_pct` cannot join this same numeric bridge.** It isn't a third input to the
margin% formula — it's a claim about *why* revenue or COGS moved, which would need an elasticity
Phase 17 already names as missing (§"What a MATURE decomposition model does for Solution
Finding": *"cannot say lag... elasticity... how much"*). Folding it into the same bar sequence
would fabricate precision for a genuinely uncertain edge, the exact conflation this whole note
exists to prevent. It stays in Edges, rendered qualitatively, never merged into the numeric
Spine.

---

## 5. Panel structure — Spine, Edges, and Ports as conditional sections; Assumptions as a marker, not a section

Resolved in conversation 2026-08-21, after the waterfall question above: the Framing Evidence
Map isn't a fixed four-box layout mirroring the four Value Driver Tree concepts one-for-one. Two
findings changed the shape:

**A fixed four-quadrant grid would violate Phase 17's own delivery rule one level down.** That
rule exists because a partial four-panel layout — three empty boxes beside one populated one —
"reads as a product that does not work." A rigid grid reserving space for all four concepts on
every KPI recreates exactly that failure at the panel level: **Spine** only exists for a primary
with surviving `accounting_identity` neighbours (an FI-anchored KPI like Gross Margin %, not a
pure Operational KPI like `units_sold`, which has nothing above it in a ledger). **Ports** only
exists when Market Analysis's conflict detection actually fires that period — most periods, for
most KPIs, it won't. Reserving a quadrant for either produces a routinely-half-empty layout for
most real KPI/period combinations.

**Assumptions was never a fourth section to begin with.** Phase 17's own text says it plainly and
this design missed it on first pass: *"the spine is the skeleton; sections 2–4 are the
annotation."* A holding/breaking verdict is a marker *on* an edge or *on* a framing decision, not
independent content with its own chart. It attaches at two points once a graded-verdict field
exists (Phase 17 T3, still gated on VA outcome data): the `prior_frame` block already rendered in
`FramingGateCard`, and individual `causal_estimate` edge/port cards. Until T3 ships, the honest
default is a small per-card "verdict pending" note where the badge will eventually sit — not a
panel-wide muted strip parallel to the real sections, which overstates it into looking like a
fourth missing feature rather than a badge with nothing to show yet.

**Resolved structure:** Spine, Edges, and Ports render only when they have real content for the
specific KPI being framed, stacked full-width in priority order (Spine → Edges → Ports) — never
boxed into reserved space. Assumptions never occupies a section; it decorates whichever
`causal_estimate` cards exist, once gradeable.

**A KPI-specific edge case worth naming, because it's sharper than "FI-schema ⇒ has a Spine":**
Net Revenue *does* sit on the FI ledger, but its only identity neighbour (`gross_margin_pct`) is
correctly excluded from its own framing alternatives by this session's earlier hop-1
confirmed-downstream-effect filter — margin % is a derived ratio, not a legitimate root-cause
candidate when analysing revenue itself (see the `causal_direction` comment in
`scripts/clients/lubricants.py:768-779`). So Net Revenue's Spine section is empty not because it
lacks identity neighbours in the schema sense, but because the one it has doesn't survive the
same path-validity filter already governing Edges. One rule — "does a neighbour survive the
path-validity filter" — decides whether *any* section renders, Spine included; there is no
separate carve-out needed for "is this KPI FI-schema."

**Illustrative per-KPI outcomes, not hypothetical:**

| Primary KPI | Spine | Edges | Ports (this period) |
|---|---|---|---|
| Gross Margin % | `net_revenue`, `cogs` (both identity, 1 hop) | `premium_mix_pct` (estimate) | absent unless MA's conflict fires |
| `units_sold` | never — no ledger ancestor | whatever registered edges exist | possible |
| Net Revenue | empty — its one identity neighbour is filtered out by the hop-1 rule above | `units_sold`/`sales_order_count`/`average_order_value` (estimate) | possible |

---

## 6. Built vs. not built

**Done (2026-08-22):** the four misclassified edges' `confidence`/`causal_rung` fields dropped to
`None` and `provenance` normalized to `confirmed` in `scripts/clients/lubricants.py`, using only
fields that already exist on `KPIRelationship` — no schema change. `gross_margin_pct→cogs`,
`base_oil_cost→cogs`, and `distribution_cost→cogs` also had their `mechanism` text corrected from
the one-hop-removed external-causal story to an accurate description of the actual identity
relationship (§1's finding #2); `distribution_cost→cogs`'s `provenance` was upgraded from
`template` to `confirmed` in the same pass, since an identity doesn't need to graduate through the
evidence ladder — it's true by construction from day one. `lag_periods` dropped from the two COGS
component edges (an identity sums same-period, no lag applies). Deliberately **not yet synced to
production** — per the registry data-sync protocol (root `CLAUDE.md`), this seed-file change needs
`onboard_client.py --client lubricants --env production` run explicitly before it reaches the live
framing gate; local/dev only until then. All 1345 unit tests pass unchanged.

**Built 2026-08-30 (Phase 17 Stage 6)** — everything the "Not built" paragraph below originally
listed. Superseded text kept as the record of what was outstanding at the time:

> ~~**Not built:** the `basis` field itself (§2) — today's fix corrects the *values* on the four
> known edges by hand; it doesn't add the field that would let a validator catch the next
> misclassified edge automatically, or drive the Framing Evidence Map's chart choice
> programmatically. The variance-bridge computation (§4), the panel restructuring (§5), and the
> Port-model gap (§3) all remain design-only, explicitly deferred as lower priority than
> validating the framing gate itself first (conversation 2026-08-21/22).~~

| § | What shipped | Where |
|---|---|---|
| **2** | `basis` (`accounting_identity` \| `causal_estimate`), NOT NULL DEFAULT `causal_estimate` so no edge silently becomes "certain". Model + provider mapping + migration; the four identity edges marked in the lubricants seed | `src/registry/models/kpi_relationship.py`, `supabase/migrations/20260830190000_kpi_relationship_basis.sql` |
| **3** | The Port model — the home for the external base-oil story this note evicted from `base_oil_cost→cogs` and flagged as having "no KPI to attach to yet" | `src/registry/models/port.py`, `ports` table (Phase 17 T4) |
| **4** | `variance_bridge()` — sequential substitution, closes with no residual; §4's tripwire implemented as `exact=False` + a stated reason rather than a silent split (corrected 2026-09-02 — see below: the real trigger is a ratio/product operation ANYWHERE in the tree, not leaf count) | `src/analysis/decomposition.py` |
| **5** | Conditional Spine→Edges→Ports stack; Assumptions as a per-card marker, never a section | `decision-studio-ui/src/components/theory/TheoryLayerExhibit.tsx` |

**Why `basis` had to be a recorded field, confirmed empirically rather than assumed.** The
build first considered deriving identity-ness from the absence of `causal_rung`/`confidence` —
the signature the 2026-08-22 pass left behind. That would have been **wrong on live data**:
`product_sales_revenue↔cogs` carries `causal_rung=NULL` **and** `confidence=NULL` exactly like
the four identity edges, yet is not an identity (its own seed comment calls it "a co-movement,
not a recorded cause"). A heuristic reading those NULLs misclassifies it. The counter-example is
now documented inline in the seed so the reasoning survives.

**§4's "which arithmetic" gap is closed, not carried forward.** §4 noted that
`accounting_identity` says an edge is exact arithmetic but not *which* arithmetic, and suggested
hardcoding Gross Margin %'s formula as a first cut. That proved unnecessary: Phase 17 T2's
`kpi_decompositions` records the operation (`linear`/`ratio`) and per-edge `sign` explicitly, so
`variance_bridge()` is generic over any tree the decomposition model covers.

**Verified against this note's own worked example** (§4: R₀=100, C₀=65 → 35.0%; R₁=110, C₁=77 →
30.0%): revenue effect **+5.91pp**, COGS effect **−10.91pp**, summing to exactly **−5.0pp**,
residual 0. Also verified live against BigQuery for lubricants YTD: 34.43% → 29.94%, a −4.48pp
move decomposing to net_revenue **+1.95pp** / cogs **−6.43pp**, residual exactly 0.

**Still not synced to production.** The `basis` values are seed-file data — per the registry
data-sync protocol (root `CLAUDE.md`) they need
`onboard_client.py --client lubricants --env production` before reaching the live framing gate.
Local/dev only until then, same caveat the 2026-08-22 pass carried.

**Correction, 2026-09-02 — the tripwire's real trigger, found while extending the Core Spine
across data products.** This section's own table above (and `docs/CLAUDE.md`'s index entry)
described the tripwire as ">2 inputs ⇒ order-dependent". That was wrong, caught while adding a
`product` operation for `net_revenue = sales_order_count * average_order_value`
(`dp_lubricants_sales → dp_lubricants_financials`, live-verified as an exact identity:
24,961 × $17,639.6622 = $440,303,607.89 = `SUM(net_amount)` exactly).

Sequential substitution's TOTAL always telescopes to the observed move exactly, for ANY function
— that was never actually in question, at any leaf count, linear or not. What genuinely varies is
whether the **individual per-leaf split** is order-independent, and that depends on the
**operation**, not the leaf count: a pure `linear` (sum-only) subtree has zero cross-derivatives
between leaves, so every substitution order gives identical individual effects, however many
leaves there are. A `ratio` or `product` node introduces a real cross term — and does so **even at
exactly two leaves**. Hand-verified on this very section's own worked numbers: swapping Revenue
before COGS gives +5.9pp / −10.9pp; swapping COGS first gives +7.0pp / −12.0pp for the *same*
−5.0pp total move. Two leaves, and still order-dependent — the opposite of what the original
`len(leaves) == 2 ⇒ exact` rule assumed.

`variance_bridge()`'s `exact` flag is now derived from the tree's operations (pure-linear ⇒ `True`
regardless of depth; any `ratio`/`product` anywhere ⇒ `False`), not leaf count. Live consequence:
`gross_margin_pct`'s own variance bridge — reported as `exact=True` in this section's earlier
verification — was **wrong under the old rule** (its tree includes a `ratio` node) and now
correctly reports `exact=False` with the order-dependence caveat surfaced in the UI. The pure-COGS
four-category bridge (all `linear`) correctly stays `exact=True` at four leaves.
