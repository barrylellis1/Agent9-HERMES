# Causal Edge Direction and Magnitude

**Status: Design note, not built.** Extends the causal-edge model
`theory_layer_design.md` already ships (`KPIRelationship`,
`supabase/migrations/20260723_theory_layer_causal_schema.sql`) and its
already-scheduled P1 write-back plan (VA adjudication HITL + assumption
verdicts + **lag** write-back) — this note is about the two things that plan
does not yet cover: direction and magnitude.

## Found live, Aug 20 2026 — the incoherent chain that started this

Walking the framing gate for a Net Revenue variance, "Cost of Goods Sold"
appeared as a candidate alternative objective. It shouldn't have: Net Revenue
(top-line, volume/mix-driven) and COGS (input cost) have no real relationship
to each other. Traced precisely:

- The only path from `net_revenue` to `cogs` in the graph is two hops, through
  `gross_margin_pct`: `net_revenue —(volume_margin)→ gross_margin_pct
  —(custom)→ cogs`.
- `get_causal_neighbourhood` treats edges as **undirected** for traversal (by
  design, for SA's compound-alert detection, which genuinely doesn't care
  which KPI is upstream). `_build_framing_prompt` inherits that
  undirectedness with no filter of its own.
- The `gross_margin_pct↔cogs` edge's own `mechanism` text says COGS (via base
  oil) drives margin — i.e. the real direction is `cogs → gross_margin_pct`.
  Walking from `gross_margin_pct` to `cogs` at hop 2 walks that edge
  **backward** (effect → cause), not forward.
- `net_revenue → gross_margin_pct` is a *different* mechanism (volume/mix)
  than `gross_margin_pct → cogs` (input cost). Chaining two unrelated
  mechanisms through a ratio node that combines both of their underlying
  drivers doesn't compose into a real inference about the original KPI — unlike
  the design's own justifying example, `base_oil_cost → cogs →
  gross_margin_pct`, which is one coherent cost-flow story all the way
  through.
- The mechanism text shown for the COGS alternative, if surfaced, would be
  `gross_margin_pct↔cogs`'s own mechanism ("base oil... margin absorbs the
  difference") — a true statement about a *different* KPI pair, presented as
  if it justified the Net-Revenue alternative. `_build_framing_prompt`
  (`a9_deep_analysis_agent.py:3500`) takes `mechanism = getattr(edge,
  "mechanism", None)` from the edge that introduced the neighbour, with no
  path-level synthesis.

## Gap 1 — no field encodes which KPI causes which

Checked `KPIRelationship`'s full field set: `kpi_id`, `related_kpi_id`,
`relationship_type`, `conflict_direction`, `mechanism`, `lag_periods`,
`causal_rung`, `provenance`, `confidence`. None of these say which KPI is the
cause. `conflict_direction` (diverging/converging) says whether the two move
together or apart — not which one drives the other.

The seed data confirms `kpi_id`/`related_kpi_id` carry no causal ordering
convention today — they're just "whichever KPI the author listed first":

```python
# base_oil_cost is the CAUSE here, and IS stored as kpi_id:
{"kpi_id": "base_oil_cost", "related_kpi_id": "cogs", ...}

# cogs is the CAUSE here (per its own mechanism text), but is stored as
# related_kpi_id -- the OPPOSITE convention:
{"kpi_id": "gross_margin_pct", "related_kpi_id": "cogs",
 "mechanism": "Base oil (largest COGS input) price volatility passes through
               to COGS with a lag; margin absorbs the difference..."}
```

**Proposed field:**

```python
causal_direction: Literal["kpi_causes_related", "related_causes_kpi", "bidirectional", "unknown"] = Field(
    "unknown", description="Which end of the edge is upstream. 'unknown' preserves today's behavior."
)
```

Default `"unknown"` so this is additive — an edge that hasn't been reviewed
doesn't silently become wrong, it just doesn't participate in
direction-filtered consumption until someone (or an LLM draft, human-reviewed,
same posture as `strategic_causal_graph_design.md`) sets it.

**Where to filter, and where not to.** `get_causal_neighbourhood`'s BFS itself
should **stay undirected** — SA's compound-alert detection is right that two
KPIs breaching together are worth flagging regardless of which one is
upstream. The fix belongs in `_build_framing_prompt` specifically: when
building a `FramingAlternative` from a 2+-hop edge, only accept it if the walk
from the *previous* node to the *new* neighbour matches that edge's
`causal_direction` (i.e. only walk cause → effect, never effect → cause). A
1-hop alternative reached directly from the analysed KPI can stay
direction-agnostic if `causal_direction="unknown"` — the framing gate already
shows an explicit "no causal mechanism recorded" caveat for that case; a
multi-hop alternative walking *backward* through a known direction is a
sharper, correctable error, not just weak evidence.

## Gap 2 — no field for magnitude, and "confirmed" doesn't mean quantified

`causal_rung="intervention_tested"` is enforced (DB constraint + Pydantic
validator) to require `provenance="va_validated"` — real discipline, already
built. But the *only* quantitative field that rung is meant to populate is
`lag_periods` (per `theory_layer_design.md`'s P1 plan: "assumption verdicts +
lag write-back"). There's no field for **how much** — a coefficient, an
elasticity, a pass-through rate — anywhere on the model.

Checked what's actually implemented, not just referenced: VA's DiD attribution
(`evaluate_solution_impact`) is real, working code and does produce a
quantified `attributable` effect size — but it measures a *solution's* impact
on its *own target* KPI (before/after vs. control group), not general
cross-KPI elasticity between two related KPIs. Granger causality — the tool
that would naturally produce a lead-lag coefficient *between two KPI time
series*, which is what `intervention_tested` on a `KPIRelationship` edge
actually implies — is named in the docstrings and in
`theory_layer_design.md`'s own research citation (Pearl, AIOps causality
graphs, DiD/Granger) as the intended mechanism, but no Granger implementation
exists anywhere in this codebase today.

**Proposed field**, deliberately not a bare float — mirrors `confidence`'s
existing "categorical, deliberately not a float" discipline
(`kpi_relationship.py:53-55`), for the same reason: a precise-looking number
from an LLM estimate or a template manufactures confidence the evidence
doesn't support.

```python
magnitude_category: Optional[Literal["large", "moderate", "small"]] = Field(
    None, description="Estimated size of the effect, categorical like confidence -- not a coefficient unless va_validated."
)
magnitude_coefficient: Optional[float] = Field(
    None, description="A real regression/elasticity coefficient. Requires provenance='va_validated' (Granger-derived) -- same guardrail pattern as intervention_tested."
)
```

Same enforced pairing as `causal_rung`/`provenance`: `magnitude_coefficient`
set requires `provenance="va_validated"`, exactly mirroring
`_intervention_tested_requires_va_validated`. `magnitude_category` has no such
requirement — it's available at any provenance tier, explicitly including
`template`/`hitl_proposed` estimates, because an *estimated* factor is still
useful (see below) as long as it's never dressed up as a validated one.

## Why an estimated factor is worth having before validation (the point that closed this)

An LLM-drafted or template-seeded `magnitude_category`, reviewed by a human
the same way `strategic_causal_graph_design.md`'s onboarding-time drafting
works, changes what the framing gate can do *today*, without waiting on a
Granger implementation that doesn't exist yet:

- **Ranking.** `_build_framing_prompt` currently builds one
  `FramingAlternative` per distinct neighbour with no ordering by strength — a
  1-hop edge with no recorded mechanism at all sits in the same list, with the
  same visual weight, as a 1-hop edge carrying a detailed, high-confidence
  mechanism. A `magnitude_category` gives the gate something to sort on: large
  estimated effects first.
- **Filtering.** A directionally-valid but negligible relationship (large hop
  count, thin mechanism, small estimated magnitude) is technically not wrong
  to show, but it's not a serious reframing candidate either. Today there's no
  signal to suppress it; the DQ L1 check just sees "an alternative was
  offered" as binary, regardless of how thin the evidence behind it is.
- **L1 itself.** This is the concrete link to the standing DQ problem this
  session has been chasing since the strategic-causal-graph work: L1 currently
  grades on vocabulary matching against synthesized prose. A magnitude signal
  attached to the *offered* alternative — not the LLM's retelling of it — is a
  data-driven input L1 could eventually weigh directly, the same way
  `theory_layer` tagging was proposed as a structural signal in
  `strategic_causal_graph_design.md`.

## Explicitly out of scope — curves / non-linearity

Not recommended for this pass. Neither VA's existing DiD code nor a
hypothetical Granger implementation (standard Granger causality is VAR-based —
linear) would produce a non-linear relationship without a materially
different method (threshold Granger, spline/nonlinear regression). Nothing in
this codebase or its design docs has a concrete use case that needs that yet.
Flagged so a future "why isn't the curve captured" question has an answer on
record, not silence.

## Recommended sequencing

| Piece | Cost | Recommendation |
|---|---|---|
| `causal_direction` field + backfill existing edges | Small — one field, a handful of edges per client to re-read and classify from their own mechanism text | Near-term |
| Direction filter in `_build_framing_prompt` (not the shared BFS) | Small — one consumption-site check, doesn't touch SA's undirected use | Near-term, same change as above |
| `magnitude_category` (estimated, LLM-assisted, human-reviewed) | Small–moderate — one field + reuse of the onboarding-time drafting pattern already proposed for strategic candidates | Near-term |
| `magnitude_coefficient` (va_validated only) | Blocked — needs a real Granger implementation that doesn't exist | Deferred, not scheduled |
| Non-linear / curve treatment | Not justified by any concrete case yet | Explicitly out of scope |

## Falsifiable prediction

If the direction filter is built and re-run against the Net Revenue situation
that motivated this note, COGS should no longer appear as a candidate
alternative for Net Revenue at all (the only path to it walks the
`gross_margin_pct↔cogs` edge backward) — while Gross Margin % itself, COGS's
own framing gate, and the legitimate `base_oil_cost → cogs → gross_margin_pct`
chain should be unaffected. If COGS still appears, the direction backfill was
wrong for that edge, not the filter logic — worth checking which, not
assuming the fix failed.
