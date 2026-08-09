# KPI Semantic Contract — Governing What a Number *Means*

**Status:** Design note. Not built. Parked behind the Phase 15 Stage H A/B (PM-4: one variable per live run).
**Date:** 2026-08-09
**Related:** `theory_layer_design.md` (what is *causally true*), this doc (what a number *means*),
`DEVELOPMENT_PLAN.md` Phase 15 Stage H, `src/analysis/` (the deterministic scorers that would consume it)

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

The recurring shape: **prose or UI re-deriving what a typed model already carried correctly**, or
computing something the registry never said was valid to compute.

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

cogs:
  unit_class: currency
  additive_across_dimensions: true
  sign_convention: negative_stored      # stored as negative debits
  inverse_logic: true                   # a rise is bad
```

---

## 4. Division of responsibility (deliberate)

**The DGA declares. The scorers enforce. The agents obey.**

```
DGA        declares the semantic contract per KPI          (authoritative, static)
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

That last row matters most: an LLM that sums three segment percentages *correctly* currently passes
every check we have. Only a declared additivity property catches it.

---

## 5. Honest limitations

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

---

## 6. Sequencing

Pairs naturally with **token substitution** (see Phase 15 Stage H notes): a basis-aware token
vocabulary and an additivity declaration are the same idea — *the registry states what this number
means, and consumers reference rather than re-derive*. Both are parked behind the Stage H A/B and
should land together rather than separately.

Suggested order when unparked:

1. **Schema + seed for one client** (lubricants), `unknown` defaults everywhere else
2. **Scorers consume it** — `groundedness` and `narrative_claims` prefer the declared fact over their
   heuristic, falling back to the heuristic when `unknown`
3. **SF prompt is told it** — one line per KPI in the synthesis context
4. **DGA exposes it** via a `get_kpi_semantics(kpi_id, client_id)` entrypoint, and
   `validate_registry_integrity` gains a check for KPIs missing a semantic contract
5. **Backfill remaining clients**, then flip `unknown` from tolerated to a registry-integrity warning

Also worth doing independently of the above: **either implement `check_data_quality` or delete it.**
It currently returns hardcoded confident metrics, which is actively misleading.
