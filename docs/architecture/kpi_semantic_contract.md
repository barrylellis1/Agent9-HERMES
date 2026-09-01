# KPI Semantic Contract — Governing What a Number *Means*

**Status:** **§3 BUILT 2026-08-30** (Phase 17 Stage 1 — it was T1's remaining half, the hard
prerequisite for the theory-layer exhibit). All seven fields are live on `KPI`
(`src/registry/models/kpi.py`) with `supabase/migrations/20260830160000_kpi_semantic_contract_additivity.sql`,
seeded for lubricants' four core FI KPIs, and enforced by
`src/registry/validators/additivity_validator.py` — a declared field with no enforcement was
explicitly not considered done, matching how Phase 16 step 2 shipped `measure_semantics`
(field + negation validator together). `additive_across_dimensions` defaults to **None, never
True**, per §6's own warning that an additive-by-default assumption "would silently re-authorise
the exact defect". Still open for §3: threading these facts into the SF *prompt* — today they are
checked on SF's OUTPUT (`groundedness.py`, `narrative_claims.py::check_additive_claim`), not
supplied as generation-time input, so the model still writes an invalid cross-segment sum and is
caught afterward rather than prevented. Not yet synced to production (seed data — see the
registry data-sync protocol). **§4 (sliceability) — this "Status" line was
stale for three weeks: it IS built.** `KPI.not_sliceable_by` is real, computed by
`A9_Data_Governance_Agent.check_slice_validity()`, enforced in `A9_Deep_Analysis_Agent`
(excluded from `dims_to_process`, recorded on `dimensions_excluded`), and backfilled for all
three real clients since **2026-08-15** — four days after this doc was written, never reflected
back into this header. Found only by checking code directly on 2026-08-30, not by reading this
doc or the DA/DGA PRDs (neither mentions it either). Not yet built for §4: automatic onboarding
trigger (still admin-only), scorer consumption, SF prompt wiring, the DGA `get_kpi_semantics`
entrypoint, and `validate_registry_integrity` surfacing `pipeline_gap` entries.
**Date:** 2026-08-09 · **§4 sliceability added 2026-08-11, built 2026-08-15, header corrected 2026-08-30**
· **§3 built 2026-08-30 (Phase 17 Stage 1)**

> **Note on this header, twice over.** §4's status line sat stale for three weeks while the
> feature was live. §3's said "genuinely not built anywhere" and was accurate for about six hours
> before Stage 1 built it. A status line is only true on the day it is written — check the code.
> That lesson recurred three times in the 2026-08-30 session alone: this header, the
> `20260723_theory_layer_causal_schema.sql` migration documented as "held, not applied" that had
> in fact been applied, and a stale local `master` ref read as "Phase 16 was never deployed" when
> `origin/master` showed it had been.
**Related:** `theory_layer_design.md` (what is *causally true*), this doc (what a number *means*),
`DEVELOPMENT_PLAN.md` Phase 15 Stage H / Stage I, `src/analysis/` (the deterministic scorers that
would consume it), `scripts/check_slice_validity.py` (the profiler that would populate §4)

---

## 1. The problem, stated from evidence

Every number defect found in the 2026-08-04 → 08-09 review traces to a **semantic property of a KPI
that nothing authoritative records**. Not one was a plumbing failure; the A2A models held throughout.

| Defect (all observed live) | Missing property |
|---|---|
| `"140.4pp of combined drag"` — the three segments it cited sum to **75.18** | **additivity** — are these deltas summable? |
| `26–47pp` claimed as *enterprise* impact by summing segment deltas (43.24 + 16.76 + 15.18) on a KPI whose enterprise move was **−1.67pp** | **additivity** (same root, different surface) |
| A segment's `−43.24` presented as *"the headline KPI move"* (true headline: 30.29%) | **scope discipline** — which values may stand for the whole |
| `"Trend: Recovering"` printed above `−$58.3M → −$59.5M` | **sign convention** for negative-stored measures |
| `KPIValue.unit` never populated system-wide → fake `$` on percentage points (fixed Jul 2026) | **unit**, declared but never enforced |
| `%` vs `pp` confusion in briefing formatting | **unit semantics**, not just the symbol |
| Gross margin by customer read **−457.71%** for one account and **exactly 100.00%** for nineteen others; the briefing recommended renegotiating a contract to correct an ETL defect | **sliceability** — is a cut along *this* dimension meaningful for *this* KPI? (§4) |

The recurring shape: **prose or UI re-deriving what a typed model already carried correctly**, or
computing something the registry never said was valid to compute.

The last row is the odd one out and is worth stating precisely, because it is the reason §4 exists.
Its *root cause* was a plumbing failure — COGS rows pinned to one `cust_id` in the generator — unlike
every other row here. But its *escape* was semantic: SA raised a breach, DA found the "concentration",
three MBB personas diagnosed a base-oil pass-through, and the briefing recommended action, because
**no layer anywhere asked whether the slice was meaningful before reasoning on top of it**. The
enterprise figure (33.25%) was correct throughout, which is exactly why it survived. A data bug is
someone else's to fix; not noticing is ours.

The sharpest single example: **Revenue in dollars genuinely sums across segments. Gross Margin %
does not — it requires revenue-weighting.** That distinction caused two separate defects, and today
it exists *nowhere in the system*. `src/analysis/groundedness.py` infers it heuristically
(`cross_segment_summation`); the LLM guessed wrong twice.

---

## 2. What the DGA governs today

`translate_business_terms` · `validate_data_access` (tenant gate, Infra B3) ·
`map_kpis_to_data_products` · `get_view_name_for_kpi` · `validate_registry_integrity` ·
`compute_and_persist_top_dimensions`

All of this governs **structure and access**: does this KPI resolve to a data product, does this
dimension exist in the contract, may this principal read it.

Two observations:

- **Nothing governs meaning.** No agent owns "may these values be added together", "is a rise good",
  "what unit does the SQL actually return".
- **`check_data_quality` returns hardcoded values** (`completeness: 0.98, accuracy: 0.95,
  timeliness: 1.0`) with an empty issues list. The one method whose name implies quality assurance
  currently asserts nothing. It should either be implemented or removed — a stub that returns
  confident metrics is the same failure class this whole document is about.

---

## 3. Proposed: the KPI Semantic Contract

New governed fields on the KPI registry record, owned by the DGA, consumed by everything downstream.

| Field | Values | Governs |
|---|---|---|
| `unit_class` | `currency` \| `ratio` \| `count` \| `duration` | How to format; whether `pp` or `%` is correct for a delta |
| `additive_across_dimensions` | `true` \| `false` | Whether segment values may be summed |
| `aggregation_method` | `sum` \| `weighted_avg` \| `ratio_of_sums` | *How* to roll up when not additive; names the weight column |
| `weight_column` | e.g. `revenue` | Required when `aggregation_method = weighted_avg` |
| `sign_convention` | `natural` \| `negative_stored` | Whether costs arrive as negative debits |
| `inverse_logic` | `true` \| `false` | Whether a rise is bad (already on `KPIValue`; belongs in the registry as the source of truth) |
| `scope_eligible` | `enterprise` \| `segment` \| `both` | Whether this KPI can legitimately be claimed at enterprise level |
| `not_sliceable_by` | list of `{dimension, reason_class, note, source}` | Which dimensions this KPI must **not** be cut by. Different shape from the rest — see §4 |

Every field above is a property of the KPI **alone**. `not_sliceable_by` is the one exception: it is a
property of the KPI **× dimension** pair, and it is derived rather than declared. §4 covers why.

### Worked example

```yaml
net_revenue:
  unit_class: currency
  additive_across_dimensions: true      # $ across segments genuinely sums
  aggregation_method: sum
  sign_convention: natural
  inverse_logic: false

gross_margin_pct:
  unit_class: ratio
  additive_across_dimensions: false     # <-- the property that was missing
  aggregation_method: weighted_avg
  weight_column: net_revenue
  sign_convention: natural
  inverse_logic: false
  not_sliceable_by:                     # <-- §4; empty today, populated by profiling
    - dimension: customer_name
      reason_class: pipeline_gap        # should carry customer; the load drops it
      note: "COGS coverage 1/20 vs revenue 20/20 (profiled 2026-08-09, since fixed)"
      source: derived

cogs:
  unit_class: currency
  additive_across_dimensions: true
  sign_convention: negative_stored      # stored as negative debits
  inverse_logic: true                   # a rise is bad
```

### 3a. This generalizes beyond finance — worked example for an operational client

Every worked example above is a P&L KPI, and that's worth correcting for explicitly: nothing about
`unit_class`/`additive_across_dimensions`/`aggregation_method` is finance-specific. `sign_convention`
and `scope_eligible` are the only two fields with a genuinely accounting-flavored shape (a signed
ledger; an enterprise P&L rollup) — the rest apply unchanged to an operational key-figure model with
no `account_type` column anywhere in it (a manufacturing OEE/throughput schema, a logistics
on-time-delivery model, a support-ticket SLA model):

```yaml
units_produced:
  unit_class: count
  additive_across_dimensions: true       # a flow/count genuinely sums across lines, shifts, plants
  aggregation_method: sum
  sign_convention: natural               # not accounting data -- always positive, nothing to declare
  inverse_logic: false

oee_pct:                                 # Overall Equipment Effectiveness
  unit_class: ratio
  additive_across_dimensions: false      # <-- exactly the same trap as gross_margin_pct
  aggregation_method: weighted_avg
  weight_column: planned_production_time # OEE weighted by the time base it was computed over
  sign_convention: natural
  inverse_logic: false                   # higher OEE is better

on_time_delivery_rate:
  unit_class: ratio
  additive_across_dimensions: false
  aggregation_method: weighted_avg
  weight_column: order_count
  sign_convention: natural
  inverse_logic: false

avg_cycle_time_hours:
  unit_class: duration
  additive_across_dimensions: false      # an average of averages is not the average
  aggregation_method: weighted_avg
  weight_column: order_count
  sign_convention: natural
  inverse_logic: true                    # lower cycle time is better

inventory_on_hand:
  unit_class: count
  additive_across_dimensions: false      # a STOCK, not a flow -- summing across time periods is
  aggregation_method: weighted_avg       # meaningless (it's not "how much moved", it's "how much
  weight_column: null                    # existed at a point in time"); summing across LOCATIONS at
  sign_convention: natural                # the SAME instant is fine, but that's a different dimension
  inverse_logic: false                    # than time, and this field doesn't distinguish the two yet
                                           # (see the flow-vs-stock note under Phase 21's honest gaps)
```

The failure mode is identical to `gross_margin_pct`'s: `oee_pct` for three production lines at
82%, 74%, and 91% cannot be added to produce "the plant's OEE" any more than three margin
percentages can be added to produce the enterprise margin — and nothing downstream today
(`groundedness.cross_segment_summation`, same heuristic either domain) reliably catches a
*correctly-computed* wrong sum in either case. The `inventory_on_hand` case additionally shows a
real gap this contract doesn't fully close yet: additivity can differ **by dimension** for the
same KPI (sums fine across locations at one instant, never across time) — see Phase 21's honest
gaps in `DEVELOPMENT_PLAN.md`.

---

## 4. Sliceability — the KPI × dimension axis

### 4.1 It is a different property from additivity, and only one of them was designed

These get conflated constantly, so state them side by side:

| | Additivity (§3) | Sliceability (§4) |
|---|---|---|
| Scope | the KPI | the KPI **×** dimension pair |
| Question | may segment values be **summed**? | is a cut along this dimension **meaningful at all**? |
| Governs | arithmetic *between* segments | whether the segment values were ever worth computing |
| Catches | `43.24 + 16.76 + 15.18` claimed as an enterprise move | `−457.71%` for one customer |

`additive_across_dimensions: false` on `gross_margin_pct` correctly forbids summing its segments. It
says **nothing** about whether any individual segment value was real. On the same KPI, the same day,
the Aug 9 briefing failed the second test while passing the first.

The reverse also holds, which is what makes this a genuinely separate axis rather than a special case:
`net_revenue` is perfectly additive *and* was perfectly sliceable by customer in the same dataset that
made `gross_margin_pct` unsliceable by customer. Additivity is about the measure; sliceability is
about whether the measure's **components** reach that grain.

### 4.2 Why it belongs on the KPI and not the data product

Validity follows the KPI's components, not the view. On the *same* `LubricantsStarSchemaView`:

| KPI | by product | by customer (pre-fix data) |
|---|---|---|
| `net_revenue` | valid | valid — revenue carries `cust_id` |
| `gross_margin_pct` | valid — both components carry product | **invalid** — COGS did not |

One data product, one view, two different answers. That is a KPI-level property by construction.

This matters beyond correctness. `KPI.dimensions` exists today and is supposed to be the per-KPI
declaration of what to analyse — but it is an **allow list that decayed into a per-client constant**:
all four client seeds define one module-level `_DIMS`/`_DIMENSIONS` and paste it onto every KPI (67
KPI records across 4 files reference exactly 4 distinct lists; `bicycle.py` has 2 entries). It is
strictly worse than the contract it duplicates — for `lubricants` it is 5 entries against the
contract's 16, two of which (`channel`, `region`) are not columns at all. Sliceability is the job that
actually belongs at that level.

### 4.3 Deny list, not allow list

The decay above is structural, not sloppiness, and it is the argument for the shape:

- An **allow list** must be maintained as the contract grows. Add a column to the view and the allow
  list silently omits it. You lose analysis coverage with **zero signal** — nobody discovers that a
  good analysis never happened.
- A **deny list** defaults to *analyse*. New dimensions are picked up automatically; an entry is
  needed only where something is known-broken.

The failure modes are asymmetric in the direction we want:

| | decay produces | visibility |
|---|---|---|
| allow list | a good analysis silently never happens | **invisible** |
| deny list | you analyse something you shouldn't, and get a strange number | **loud** |

Prefer loud. This is the same reasoning as `DimensionTotal.source` being a `Literal` in which `"sum"`
is not representable: make the bad state hard to reach and the remaining failure noisy.

### 4.4 Derive it; do not ask for it

The strongest version is not hand-authored. `scripts/check_slice_validity.py` **already computes**
per-component dimensional coverage and reports which dimensions a ratio KPI can legitimately be cut
by. It is run by hand, wired to nothing, and gates no workflow.

Proposal: run it at onboarding, write the result onto the KPI record, and let humans add what the data
cannot reveal. Each entry carries `source`:

| `source` | Meaning |
|---|---|
| `derived` | produced by coverage profiling — reproducible, re-runnable, dated |
| `declared` | a human asserted it; the data did not show it |

This is the provenance ladder from `theory_layer_design.md`, applied to measurement rather than
causation. It also answers the obvious objection — *who would know?* — for the common case: **the data
knows.** Coverage profiling would have caught Aug 9 outright (COGS 1-of-20 against revenue 20-of-20)
without anyone needing prior knowledge of the ETL defect.

`"ok"` must require **full** coverage. 19 of 20 means one slice is fabricated, and partial coverage is
the case most likely to be believed.

### 4.5 What DA does with it, and the one rule that must not be broken

Exclude the dimension from `dims_to_process` — analysing a cut you have declared meaningless burns a
query slot and risks the number reaching a reader.

**But record every exclusion.** `DeepAnalysisResponse.dimensions_excluded: [{dimension, reason_class,
source}]`, alongside the `dimensions_analyzed` field added in Stage I Part A. A deny list that quietly
shrinks the investigation is the `preferred`-literal defect wearing better clothes — Part A was spent
removing one invisible narrowing of the dimension set, and this must not install another.

Useful interaction: excluding known-invalid cuts **frees slots** under `max_dimensions` (10 since Part
A), so the search reaches deeper into valid dimensions. The check partly pays for its own cost.

### 4.6 The trap: a deny list is a place to hide bugs

Someone sees `−457.71%`, adds `customer_name` to `not_sliceable_by`, the symptom disappears, and the
ETL defect lives forever behind something that looks like governance. `reason_class` exists to prevent
exactly this:

| `reason_class` | Meaning | Disposition |
|---|---|---|
| `structural` | the component genuinely is not captured at that grain (COGS is booked at product level; that is how the business works) | a **fact** — permanent, correct to declare |
| `pipeline_gap` | it should be captured at that grain and is not | a **bug** — needs a ticket, not a declaration |

`pipeline_gap` entries should be surfaced by `validate_registry_integrity` as open defects rather than
sitting silently. A deny list with no `structural`/`pipeline_gap` split becomes a graveyard of unfixed
ETL problems, and the graveyard will look like diligence.

---

## 5. Division of responsibility (deliberate)

**The DGA declares. The scorers enforce. The agents obey.**

```
DGA        declares the semantic contract per KPI          (authoritative, static)
           §4 sliceability is the exception: DERIVED by
           profiling, re-runnable, dated — not static
   |
   v
SA / DA    read it when computing and stamping values      (MeasurementContext)
   |
   v
SF prompt  is TOLD it: "Gross Margin % is not additive;
           do not sum segment deltas to an enterprise figure"
   |
   v
Scorers    enforce it deterministically                    (src/analysis/)
```

**Explicit non-goal: the DGA should NOT validate rendered presentation.** Checking briefing output is
what `src/analysis/groundedness.py` and `narrative_claims.py` already do, deterministically and
without an LLM. Routing that through an agent adds an orchestration hop without adding truth. The
DGA's contribution is *upstream* — supplying the facts those checks currently have to infer.

### What this converts from heuristic to fact

| Today | With the contract |
|---|---|
| `groundedness.cross_segment_summation` — inferred: "the claim is implausible vs the enterprise move but fits the sum of segments, so it was *probably* summed" | "this KPI is declared **non-additive**; summing its segment deltas is invalid, full stop" |
| `narrative_claims` sum check — self-contained: only catches a total contradicting components *cited in the same sentence* | Also catches a total that is arithmetically consistent but **semantically invalid** (correctly summed, wrong to sum at all) |
| `_parse_impact_estimate` scope guard — rejects `enterprise` + a segment label | Also rejects an `enterprise` claim on a KPI declared `scope_eligible: segment` |
| **Nothing.** No layer asks whether a slice is meaningful before reasoning on it — the −457% / 100.00% margins passed SA, DA, three MBB personas and a briefing intact | `not_sliceable_by` excludes the cut, and `dimensions_excluded` records that it was excluded and why (§4.5) |

Two rows matter most. An LLM that sums three segment percentages *correctly* currently passes every
check we have — only a declared additivity property catches it. And the last row is not an upgrade
from heuristic to fact but from **nothing to something**: the other checks all verify arithmetic
*inside* the pipeline, and no amount of downstream rigour substitutes for asking whether the input
was meaningful.

---

## 6. Honest limitations

1. **This is prevention-adjacent, not prevention.** Declaring non-additivity does not stop an LLM
   summing anyway. It makes the violation *deterministically detectable* rather than heuristically
   suspected — the same posture as everything else built this week.
2. **It is a registry schema change.** New fields on KPI records, seeded per client via
   `scripts/clients/<id>.py`, plus a migration. `CLAUDE.md` flags registry migrations as
   handle-with-care, and every existing client needs backfilling. Heavier than it looks.
3. **Defaults are dangerous.** An unset `additive_across_dimensions` must NOT default to `true` —
   that silently re-authorises the exact defect. Unset means *unknown*, and unknown must read as
   "cannot verify this claim", consistent with the not-checked ≠ pass discipline in `src/analysis/`.
4. **It does not help un-onboarded KPIs.** A client whose KPIs predate the contract gets `unknown`
   everywhere until backfilled — which is honest, but means the checks stay heuristic in the interim.
5. **Sliceability catches known and detectable invalidity — not unknown invalidity.** Coverage
   profiling closes most of the gap, but it measures **presence, not provenance**. A fully-allocated
   COGS column looks perfect to it. The genuinely dangerous case it cannot see is cost that reached
   the customer by **allocation rather than observation**: someone re-weights an allocation driver and
   an account goes from profitable to catastrophic with nothing having happened commercially. Unlike
   100%-margin rows, that is invisible to inspection. It needs a real CO-PA / PaPM feed where the
   cycles exist and is correctly deferred to pilot — raise it in pilot scoping, never as a demo slide.
6. **Its value is concentrated outside the enterprise ICP.** In a mature SAP CO-PA / S4 Margin
   Analysis landscape, standard COGS *does* carry customer and product from the sales document, so the
   coverage check often will not fire. Its value concentrates in mid-market and in warehouse layers
   that dropped characteristics — a segment not yet validated.

---

## 7. Sequencing

Pairs naturally with **token substitution** (see Phase 15 Stage H notes): a basis-aware token
vocabulary and an additivity declaration are the same idea — *the registry states what this number
means, and consumers reference rather than re-derive*. They should land together rather than
separately. (The Stage H A/B these were parked behind **closed 2026-08-09**; nothing gates them now
except priority.)

**§4 sliceability update (2026-08-30): this section was overtaken by events and left uncorrected
for three weeks.** Everything below was written on 2026-08-09/08-11 assuming neither §3 nor §4
existed yet. In fact §4 shipped separately, on its own, on **2026-08-15** — not "with §3," and not
per the order suggested below. §3 remains genuinely unbuilt (confirmed 2026-08-30). The claim
that sliceability "has no cover at all — no layer anywhere currently asks the question" was true
on 2026-08-11 and has been false since 2026-08-15; nobody updated this paragraph when it shipped,
which is exactly the case study for the out-of-sync-docs risk this needs to be read alongside
(`DEVELOPMENT_PLAN.md`, 2026-08-30 session). The suggested order below is preserved for reference
but should NOT be treated as the real step-by-step status — check the per-step notes instead,
verified live 2026-08-30:

1. ✅ **Schema + seed for one client** — done, and further than "one client": `not_sliceable_by`/
   `slice_validity_details`/`slice_validity_checked_at` exist on `KPI` (`src/registry/models/kpi.py`)
   and are populated for all three real clients (lubricants, apex_lubricants, hess), not just
   lubricants.
2. 🟡 **`check_slice_validity` exists and is callable** (`A9_Data_Governance_Agent
   .check_slice_validity()`, `src/api/routes/admin.py` → `src/api/runtime.py`) but is **admin-
   triggered, not wired into onboarding automatically** — the "populated by profiling rather than
   authored" property holds (a human never hand-types a `not_sliceable_by` entry), but "wired into
   onboarding" does not yet.
3. ❌ **Scorers do not consume it** — confirmed by direct search: zero references to
   `not_sliceable_by`/`dimensions_excluded` in `src/analysis/groundedness.py` or
   `src/analysis/narrative_claims.py`.
4. ✅ **DA consumes `not_sliceable_by`** — confirmed by reading `a9_deep_analysis_agent.py`
   directly: excluded from `dims_to_process` before the `max_dimensions` cut, every exclusion
   recorded on `dimensions_excluded`, never silent, exactly as designed.
5. ❌ **SF prompt is not told it** — zero references in `a9_solution_finder_agent.py`.
6. ❌ **No DGA `get_kpi_semantics` entrypoint exists**; `validate_registry_integrity` does not
   surface `pipeline_gap` entries.
7. 🟡 **Backfilled for all three real clients already** (see step 1) — the "remaining clients" this
   line meant (given it assumed step 1 covered only one) don't exist; what's actually missing is
   re-running the check as client data changes, and bicycle (the fourth, DuckDB client) was not
   checked in this pass.

Also true and unaffected by the above: **§3 (additivity itself) has zero cover of any kind** —
no schema field, no detection, no scorer awareness. The design doc's own §3a now has an
operational (non-financial) worked example.

Note the ordering constraint in step 4: it depends on Stage I Part A having landed
`dimensions_analyzed`, since `dimensions_excluded` is meaningless without a record of what *was*
analysed. That is already in place.

Also worth doing independently of the above: **either implement `check_data_quality` or delete it.**
It currently returns hardcoded confident metrics, which is actively misleading.
