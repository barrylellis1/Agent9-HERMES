# Strategic Causal Graph — Design Note (Not Built)

**Status: Design note, not built.** Opening design pass, written same-night as the finding that
motivated it — not yet adjudicated across multiple runs or reviewed the way `problem_framing_design.md`
was before its build started. Treat every decision below as a draft to be locked, not a settled one.

## Context — the finding that motivates this

Three live runs on 2026-08-19 (2 MBB, 1 lens council), each a different persona configuration, each
independently synthesizing options for the same chosen frame ("Addressing Cost of Goods Sold instead
of Gross Margin % directly"), all scored against the Stanford SDG Decision Quality rubric
(`decision_quality_rubric.md`, `src/analysis/decision_quality.py`). **L1 (appropriate frame) failed in
all three, with identical reasoning every time**: "every option recovers the breached KPI within its
existing structure." This is not the first time L1 has failed — `problem_framing_design.md` itself was
built because the *same* link failed a 13-run corpus and a second problem shape (§10-11 of that doc).
Phase 19/20 fixed *whether the frame is examined*; it did not fix *what frame the system is even capable
of offering*.

The root cause, traced live: the causal graph `KPIRelationshipProvider.get_causal_neighbourhood()`
draws framing alternatives from contains **only operational/financial KPI-to-KPI edges** — for
`gross_margin_pct` on the lubricants client: COGS, Net Revenue, Premium Product Mix %, Raw Materials
Cost, Distribution Cost, Product Sales Revenue. None of these represent a portfolio-participation or
strategic-posture question. So a principal at the mandatory framing gate cannot choose a strategic
reframe — it was never offered — and nothing downstream in Solution Finder has occasion to consider one
either. Three independent syntheses correctly and faithfully explored the small operational solution
space the chosen frame permitted (hedge the input, reprice the output, adjust cost/mix structure) — the
system did its job correctly against too narrow a frame, which is a different and more fundamental
problem than a synthesis-quality issue.

**Why this matters beyond one DQ link**: if Decision Quality is presented to users as a real measure of
decision quality — the confidence-building instrument this session's testing was aimed at — a pipeline
that structurally cannot surface a strategic alternative is measuring operational-response quality, not
decision quality, no matter how well synthesis performs within that narrower scope.

## The problem, precisely

Every alternative offered at the framing gate today is anchored to an existing `KPIDefinition` — the
`FramingAlternative`/`KPIRelationship` shape assumes "the other end of this edge is a KPI with a current
value and a trend." A strategic alternative ("should we reduce participation in commodity-exposed
grades") is not a KPI in that sense — it doesn't have a period-over-period value, it has a *posture*.

## Why this is a real initiative, not a registry seed

Checked directly before writing this: `KPIRelationship.related_kpi_id` is a plain `str`, no FK
enforcement — a relationship *could* point at a non-KPI id today without a schema migration, and
`_lookup_kpi_scoped` returning `None` already degrades gracefully (falls back to the raw id as the
display name, no crash). So the floor is lower than it might look. But three things make "just add a
row" the wrong instinct:

1. **The provenance ladder doesn't fit.** `template → confirmed → hitl_proposed → va_validated`
   (`kpi_relationship.py`) was built for *empirical* claims — `base_oil_cost ↔ COGS` can be checked
   against real data, and `va_validated` specifically means VA ran a DiD/Granger test on it. "Should we
   reduce commodity-grade participation" is a strategic judgment about competitive position and risk
   appetite — there is no query that confirms it, and no version of VA's DiD methodology tests it.
   Forcing it into the existing ladder either mislabels a judgment as `confirmed` (over-claiming
   certainty the empirical ladder was built to prevent) or leaves it permanently at `template`
   (under-representing a principal's actual considered judgment). It needs its own trust vocabulary,
   not a borrowed slot in this one.
2. **Not templatable across clients.** Operational KPI relationships can often be inferred from a shared
   chart-of-accounts shape (this is most of why `provenance="template"` exists at all). A strategic node
   is about *this specific client's* competitive position, portfolio, and market — Hess's version of
   this looks nothing like Apex's or Lubricants'. This is a bespoke, per-client curation step, which
   means it becomes a new item in the New Client Onboarding Checklist (root `CLAUDE.md`), not a
   registry-seed script.
3. **Different revalidation cadence.** An empirical cost relationship is stable until the underlying
   process changes and mostly self-evidences in the data. A strategic judgment ages with competitive
   dynamics and board risk appetite — it likely needs a human to actively re-confirm it on a cadence,
   not sit as a static row that's "true until someone notices it's stale."

## Concrete example

Today's graph for `gross_margin_pct` has only operational nodes. A strategic node looks structurally
different:

```
kpi_id: "gross_margin_pct"
related_kpi_id: "commodity_grade_portfolio_participation"   # not a KPI — a portfolio construct
relationship_type: "structural_exposure"                     # new type; none of the existing four fit
mechanism: "Commodity-exposed grades (Synthetic Blend, Conventional Engine Oil, Compressor Oil,
  Hydraulic Oil, Manual Gear Oil) carry base-oil-cost pass-through risk with no differentiation
  premium to absorb volatility. Sustained participation at current mix caps margin recovery to
  whatever cost-management levers alone can achieve — a ceiling on the OPERATIONAL fix, not a claim
  that hedging or repricing doesn't work."
causal_rung: null            # not an empirical claim in Pearl's sense — see provenance below
provenance: "strategic_judgment"   # NEW value, not reusing the empirical ladder — open question below
confidence: null              # confidence-in-a-fact doesn't apply; conviction-in-a-judgment might, TBD
```

At the framing gate this becomes a visibly different KIND of alternative: not *"Addressing Cost of
Goods Sold instead of Gross Margin % directly"* but something like *"Addressing commodity-grade
portfolio participation instead of Gross Margin % directly — a structural exposure question, not a
cost-management one."*

## Open decisions — not locked, listed so the next pass doesn't re-derive them from zero

1. **New node type, or overload `KPIRelationship`?** The string-id escape hatch means a minimal version
   needs no migration. A clean version probably wants a distinct `StrategicAlternative` model (own
   provenance vocabulary, no `causal_rung`, no snapshot-fetch expectation) rather than stretching a
   model built for empirical KPI pairs. Leaning toward the distinct model — same reasoning
   `problem_framing_design.md` used for `FramingAlternative`'s `source`-discriminated shape (market
   signal vs. causal graph) rather than forcing one schema to mean two things.
2. **Provenance vocabulary for strategic edges.** `strategic_judgment` above is a placeholder, not a
   decision. Does it need levels (e.g. `principal_proposed` vs. `board_ratified`)? Does "confidence" even
   make sense here, or is the honest field something more like "who owns this judgment and when did they
   last affirm it"?
3. **Who curates these, and when.** Onboarding-time only (client's strategy team names 1-3 strategic
   postures per major KPI cluster), or can a principal add one ad hoc at a framing gate ("actually, is
   exiting this segment on the table?") the way HITL-accreted assumptions already work elsewhere in the
   theory layer? The latter is more aligned with this project's existing accretion pattern
   (`theory_layer_design.md`) but is a bigger interaction-design lift.
4. **UI treatment.** No snapshot, no trend chart — `_fetch_neighbour_snapshot`/`_fetch_neighbour_monthly_trend`
   (Phase 20) should skip strategic alternatives outright rather than attempt a fetch that can't
   succeed. `CausalNeighbourhoodEvidence.tsx` needs a visibly different card treatment (no "+X% this
   period" stat — there's nothing to compute it from) so a principal doesn't read "no data" as "nothing
   is happening" when the honest state is "this isn't the kind of thing that has a period-over-period
   value."
5. **Does this change the DQ scorer itself?** L1 today is a pure text-screen on the *offered options*
   (71% false-positive rate, documented in `decision_quality.py`). If a genuine structural alternative
   is offered at the framing gate and a principal explicitly accepts or rejects it (same structured-submit
   discipline `FramingDecision` already uses — Decision #4 of the Phase 19 plan: a click, not a guess),
   L1 could stop being a term-match on synthesis output and become a real check: **was a structural
   alternative offered, and was it given an explicit verdict** — data, not vocabulary-matching. That
   would also close the false-positive gap the current screen carries. This is the single highest-value
   consequence of building this, and probably the actual design center of the next pass, not an
   afterthought.

## Explicitly out of scope for this note

- The exact schema/migration for a `StrategicAlternative` model — decision 1 above needs to be locked
  first.
- Whether an LLM can be trusted to *propose* candidate strategic alternatives for human review (cheaper
  to scale, but importing exactly the "computed weight vector, nobody chose it" failure mode
  `problem_framing_design.md` §"Compute the frame from the causal graph" already rejected for the
  operational case) versus pure human curation at onboarding.
- Any change to `decision_quality.py`'s `score_run()` — decision 5 above is a real design direction, not
  a build plan.
- A revised onboarding checklist entry — follows once decisions 2-3 are locked.

## Falsifiable prediction, before any build (per `persona_council_experiments.md`'s own transferable
method: predict before running, one variable at a time)

If a genuine strategic alternative is added to the lubricants `gross_margin_pct` graph and offered at
the framing gate, the prediction is: **a majority of principals will still confirm the stated
(operational) objective rather than choose the strategic reframe** — margin recovery is usually the
correct near-term answer, and offering the alternative is about making that a considered choice, not
expecting principals to flip to portfolio exit. The value being tested is not "principals should choose
differently," it's "L1 should measure whether the choice was actually available and actually made" — the
same falsifiable-decision-quality standard `problem_framing_design.md`'s own stated falsifier already
applies to the operational reframe question. If principals confirm the stated objective in nearly every
run even once the strategic option exists, that is itself the honest finding to report, not a result to
argue away.

## Recommended sequencing

Not started. Recommended as the next real initiative after the current demo cycle, sequenced through the
same discipline `problem_framing_design.md` used: lock the open decisions above (ideally after
adjudicating a few more live DQ runs so L1's failure rate is confirmed beyond n=3, not assumed), write
the slice-by-slice build plan, then implement.
