# Data Product Time Dimension Planning

**Status: Design note, not built.** Interim mitigation shipped Aug 2026 on `dp_lubricants_sales`
(see below); the general mechanism this note proposes is not.

## The problem, found live, not hypothetical

`dp_lubricants_sales` (added Aug 2026, see `strategic_causal_graph_design.md`'s companion commit)
carries three genuinely distinct dates on the same fact table, because that is what a real SAP SD
order-to-cash cycle looks like: order date, delivery date, and (not even modeled yet) billing
date. Its `SALES_DATA_PRODUCT.time_dimensions` was originally wired with `delivery_date` as the
sole, `primary` time dimension.

That was wrong, and material, not cosmetic. Checked live against the actual data:

- **90.2%** of Sales Order Item rows (55,584 of 61,654) have `delivery_date` in a *different*
  fiscal month than the `fiscal_year`/`fiscal_month` their revenue was actually recognized in.
  The generator adds a 15–60 day shipping lag from order date to delivery date for realism; that
  routinely crosses a month boundary.
- The effect on a real query is not a rounding footnote. Filtering `SUM(net_amount)` by
  `delivery_date BETWEEN ...` vs. the correct `fiscal_year = Y AND fiscal_period = P` for the
  same nominal window:
  - `current_month`: $15,247,394 (delivery-date-based) vs. $14,401,703 (recognition-period-based)
    — a 5.5% gap.
  - `year_to_date`: $95,345,750 vs. $104,667,369 — an 8.9% gap.

Whole-history totals still reconcile exactly to Finance (proven when the data product was built —
$440,303,607.89 both sides, to the cent), because a total ignores period boundaries entirely. Any
*period-sliced* Sales KPI — which is most of what Situation Awareness and Deep Analysis actually
run — was silently wrong.

## Why this will recur, not a one-off

This is not a quirk of one synthetic dataset. Any real SAP SD-shaped data product has this same
shape: order create date, goods-issue/delivery date, and billing date are different business
events, and revenue recognition is keyed to whichever the client's actual accounting treatment
uses — not necessarily any single one of the three. A data product onboarded from real SAP
Datasphere content (the sample this session's Sales work started from, and the eventual real-MM
connector `strategic_causal_graph_design.md` defers) will carry the same ambiguity by default,
every time.

## Current mechanism, confirmed against code

`A9_Data_Product_Agent._resolve_time_spec(data_product_id)` (`a9_data_product_agent.py:4385`)
picks exactly one time dimension **per data product**:

```python
tds = getattr(dp, "time_dimensions", None) or []
primary = next((t for t in tds if getattr(t, "primary", False)), tds[0] if tds else None)
```

`time_dimensions` is already a *list* — the schema has room for multiple entries — but nothing
downstream ever consults any entry except the primary one. There is no `time_dimension` field
anywhere on the `KPI` model (`src/registry/models/kpi.py`), and no call site threads a KPI-level
override into `_resolve_time_spec`. So today, every KPI on a data product is filtered by the same
single date column regardless of what the KPI is actually about — a fulfillment KPI that should
key off delivery, and a revenue-recognition KPI that should key off billing/recognition period,
are forced onto whichever one column won the `primary` flag.

## Interim mitigation shipped now

`SALES_DATA_PRODUCT.time_dimensions` (`scripts/clients/lubricants.py`) was changed to:

1. `fiscal_year_period` (year_column=`fiscal_year`, period_column=`fiscal_period`, zero-padded
   string — same shape and same `fiscal_year_start_month=1` default as
   `dp_lubricants_financials`) as **primary** — correct for 4 of the 5 Sales KPIs (order count,
   units sold, average order value), which are volume/value metrics that must reconcile to
   Finance's own recognition period.
2. `order_date` and `delivery_date` retained as **non-primary** entries in the same list —
   captured, not discarded, for the day per-KPI selection exists.

This is a real fix for the KPIs it fixes, and an **honest, tracked gap** for the two it doesn't:
`order_fulfillment_rate` and `order_cancellation_rate` are conceptually about delivery/lifecycle
status, not revenue recognition, and are *still* filtered by `fiscal_year_period` today because
that's the only primary available. They are not silently wrong in the same way delivery-date was
wrong for value KPIs (status codes don't have a "recognition period" to disagree with), but a
period-sliced fulfillment-rate query is answering "what fraction of orders *recognized* this
month were eventually fulfilled," not "what fraction of orders *due* this month were fulfilled" —
a real, if smaller, mismatch of the same kind.

## Proposed general mechanism (not built)

1. Give each `time_dimensions` list entry a stable `key` (short slug, e.g. `"recognition"`,
   `"order"`, `"delivery"`) distinct from `label` (human-facing prose) — `label` should not double
   as an identifier a KPI references.
2. Add an optional `KPI.time_dimension_ref: Optional[str] = None` field naming that key.
3. Extend `_resolve_time_spec(data_product_id, kpi: Optional[KPI] = None)`: when
   `kpi.time_dimension_ref` is set, look it up by `key` in the data product's `time_dimensions`
   list first; fall back to `primary` exactly as today when unset or unresolvable (so every
   existing KPI, which never sets this field, is byte-identical in behavior — the same
   backward-compatibility posture `sales_lines` used in `generate_transactions()`).
4. Thread the KPI object (already resolved earlier in the same call path, e.g.
   `_lookup_kpi_scoped`) into the `_resolve_time_spec` call sites (`a9_data_product_agent.py`
   lines ~5152 onward) — a signature change, not a new lookup.

## Scope check — is this worth building now?

No, deliberately not — recommend fast-follow, not pre-demo. Unlike the SAP MM/Layer-1 causal
graph gap (`strategic_causal_graph_design.md`), this is genuinely narrow and cheap: one new
optional model field, one function signature extension, a handful of call sites, entirely
additive and backward-compatible by construction. But `_resolve_time_spec` and
`_build_bq_dimensional_sql`/`_build_sf_dimensional_sql`/etc. sit on the core DPA SQL-generation
path every workflow depends on (`CLAUDE.md`'s "Critical Areas" list) — not a place to touch on
the same day as a demo. The interim mitigation above already closes the material, measured gap
(the two value KPIs that were off by 5.5–8.9%); the remaining gap (fulfillment/cancellation rate
using the wrong-but-plausible period) is real but smaller and already documented in code comments
at the point of decision, not silently accepted.

## Falsifiable prediction

If this is built, `order_fulfillment_rate` filtered by `delivery_date` for a given month should
diverge from the same KPI filtered by `fiscal_year_period` by a comparable order of magnitude to
the 5.5–8.9% found above for value KPIs — if it doesn't move materially, the mechanism was built
for a problem that wasn't actually there for *that* KPI, worth knowing before investing further.
