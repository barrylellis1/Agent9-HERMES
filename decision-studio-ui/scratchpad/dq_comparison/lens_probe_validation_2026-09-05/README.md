# Phase 22 Stage D — lens-probe validation (negative result)

**Captured 2026-09-05.** Measures whether Stage 22's Stages A–C (persona-keyed
refinement, replacing the single persona-invariant refined-problem string with
one framework-anchored clarifying question per persona) actually increases
Stage 1 hypothesis diversity, using `scripts/run_lens_probe_validation.py`.

## Result: no — on this measurement, it made diversity worse

| | baseline (no lens data) | with lens_refinement |
|---|---|---|
| distinct lever families (10 runs) | `[3,3,3,3,3,3,3,3,3,3]` | `[3,3,2,2,3,3,3,2,3,2]` |
| mean | **3.00** | **2.60** |
| runs above the other arm's mean | — | 0/10 |
| runs below the other arm's mean | — | 4/10 |

Fixture: `lens_run`'s DA payload (Gross Margin %, lubricants). Council: lens
(commercial/operational/structural). Model: Anthropic (Haiku-tier, matching
Stage 1's own production model). Measured directly on Stage 1's three
`proposed_option` titles via `classify_lever` — no synthesis call needed.

## The mechanism, found in the data, not guessed

Every one of the 10 simulated executive answers hedges:

> *"Without detailed price, mix, and cost data by SKU, I cannot definitively
> isolate the driver..."*
> *"I don't have visibility yet into whether this is a cost-structure issue..."*
> *"I'd need to confirm whether raw material or procurement costs have
> shifted..."*

None state a fact the DA recap didn't already contain — correctly, since the
simulation prompt explicitly forbade inventing numbers not implied by the
facts. But handing all three personas the **same uncertain, non-committal
signal** appears to pull them toward a shared "insufficient data, probably
pricing/mix" read, rather than letting each fall back to its own framework's
default lean. In baseline (no lens data at all), each persona reasoned from
its own framework independently and consistently landed on a distinct family:
commercial → `pricing_corridor`, operational → varied but distinct,
structural → `portfolio_exit`, appearing in **every single one of the 10
baseline runs**. A hedge homogenized what independence had kept apart.

## Why this is not evidence against the Stage A–C architecture

The mechanism itself works exactly as built and tested — `ps_s1` is
genuinely persona-keyed, three different lens answers reliably produce three
different Stage 1 prompts (proven directly in
`tests/unit/test_sf_lens_probe_persona_keying.py`). What this measures is a
**downstream consequence of the *content* of the answers**, not a defect in
the plumbing that delivers them.

The real, load-bearing limitation is the one already named before this run
happened, in the harness's own module docstring and in this phase's design
discussion: **no live executive answered these questions.** A model asked to
simulate a cautious CFO, explicitly forbidden from inventing facts, will
hedge — correctly, for a simulation. Whether a real executive would hedge the
same way, or bring genuine private knowledge the DA recap doesn't contain, is
a live-usage question no harness can substitute for.

## What this does and does not settle

- **Does not** confirm lens-probing improves analysis quality on this
  fixture, with this council, under this simulation method.
- **Does** identify a concrete, actionable risk: uninformative or hedged
  lens-probe answers can homogenize rather than diversify Stage 1 reasoning,
  and a UI that lets an executive answer with an "I don't know" should expect
  this failure mode rather than be surprised by it.
- **Does not** invalidate Stages A–C's mechanism-level tests, which verify
  the plumbing does what it's supposed to do, correctly.

## Recommendation

Do not treat Phase 22 as validated by this measurement. Consistent with how
this codebase already treats the theory-layer exhibit's own density gate —
"clears only through accumulated VA verdicts over real use, never by
seeding" — this mechanism's real validation can only come from actual
executives answering actual questions in the live UI, not from a simulated
proxy. Ship Stage C, watch what real answers look like, and re-measure
against real HITL outcomes before drawing a conclusion either way.

## Reproducing

```bash
python scripts/run_lens_probe_validation.py \
    --fixture decision-studio-ui/scratchpad/dq_comparison/lens_run \
    --n 10 --out <this directory>
```

Cost: Haiku-tier only (Stage 1 + lens-probe generation + simulated-answer
generation), no synthesis calls. This run cost well under $1.
