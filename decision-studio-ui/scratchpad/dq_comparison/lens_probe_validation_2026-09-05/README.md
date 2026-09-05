# Phase 22 Stage D — lens-probe validation (two runs, corrected methodology)

**Captured 2026-09-05.** Measures whether Stage 22's Stages A–C (persona-keyed
refinement — one framework-anchored clarifying question per persona, replacing
a single persona-invariant refined-problem string) actually increases Stage 1
hypothesis diversity, using `scripts/run_lens_probe_validation.py`. Two
completed runs exist, under different simulated-answer information levels;
both are kept, not just the final one.

## v2 (current): complete DA output — near-neutral, not negative

`manifest_v2_complete_da_output.json`. The simulated executive answering the
lens-probe questions received the **complete DA execution output** — every
change point, every segment, every region, at full detail — not a recap of
any size.

| | baseline (no lens data) | with lens_refinement |
|---|---|---|
| distinct lever families (10 runs) | `[3,3,3,3,3,3,3,3,3,3]` | `[3,2,3,3,3,3,3,3,3,3]` |
| mean | **3.00** | **2.90** |
| runs above / tied / below the other arm | — | 0 above / 9 tied / 1 below |

Answers under this version are genuinely substantive — real cross-referenced
figures, not hedges:

> *"All six customer segments... and all six regions... show margin
> compression in the -4 to -5 point range, indicating the pressure is
> broadly structural across the customer base... suggesting this is
> category-wide pricing or cost pressure, not localized participation loss."*

**Baseline is already at ceiling.** All 10 baseline runs hit exactly 3 of 3
possible distinct families (this fixture's 3-persona lens council already
produces full diversity without any lens data, because each persona's
default framework lean is already distinct: commercial→pricing,
structural→portfolio exit, operational varying but distinct from both). That
leaves essentially no headroom for lens-probing to show as an *improvement*
on this specific metric, on this fixture — a ceiling effect, not evidence the
mechanism has no value, just evidence this measurement can't see one if it
exists here.

## v1 (superseded): 3-line recap — a genuine negative, later found confounded

`manifest_v1_underprovisioned_recap.json`. The first version of this script
gave the simulated executive only 3 generic lines
(`kt_is_is_not.what_is[:3]`) — missing 4 of this fixture's 5 segment-level
change points and the situation complication summary.

| | baseline (N=1, later found non-reproducible) | with lens_refinement (N=10) |
|---|---|---|
| distinct families | 3 | mean 2.60, range `[3,3,2,2,3,3,3,2,3,2]` |

Root cause, found in the manifest: every simulated answer hedged —
*"I don't have visibility yet...", "I'd need to confirm..."* — because the
lens-probe questions ask about segment/mix-level detail (*"has the mix
shifted toward lower-tier or value-segment SKUs"*) that this recap never gave
the simulator the material to answer. **This was a confound in the harness,
not evidence about lens-probing** — corrected in v2 by giving the simulator
everything DA produced instead of narrowing what it saw.

A middle attempt (recap matched to `a9_solution_finder_agent.py`'s own
`dataset_recap_lines`, i.e. what a real persona sees) was run but crashed
mid-sweep on an unretried transient LLM failure at run 7/10 — no usable
final number, not counted as a result. The retry logic added afterward
(3 attempts, backoff) is what let v2 complete cleanly.

## What this two-run arc establishes

- The sharp v1 negative result does not hold up once the harness gives the
  simulator complete information — it was substantially an artifact of
  under-provisioning, not a property of persona-keyed refinement.
- v2's near-null result does not confirm the hypothesis either. It's
  consistent with "no measurable effect on this fixture" and equally
  consistent with "a ceiling effect on this fixture hides a real effect" —
  this measurement cannot distinguish those.
- Stages A–C's plumbing is unaffected by either result: `ps_s1` is confirmed
  genuinely persona-keyed by direct unit test
  (`test_sf_lens_probe_persona_keying.py`), independent of what Stage D's
  simulated-executive proxy shows.

## Why this still isn't the real answer, and won't be from a harness

Both runs share the same irreducible limitation: **no live executive
answered these questions.** v2's simulator gives excellent, well-grounded
answers because it was told to use everything DA produced and forbidden from
inventing anything beyond it — a real executive might answer more
confidently, less confidently, or answer something the DA payload doesn't
even contain (institutional knowledge, a customer conversation, a
competitor's move). Whether that changes Stage 1's diversity, or the
resulting recommendation's actual quality, is not something any simulation
can settle.

## Recommendation (unchanged from the original finding)

Do not treat Phase 22 as validated by either run, in either direction.
Consistent with how this codebase already treats the theory-layer exhibit's
own density gate — clears only through accumulated VA verdicts over real
use, never by seeding — this mechanism's real test can only come from actual
executives answering actual questions through Stage C's shipped UI. Ship it,
watch what real answers look like, re-measure against real HITL/VA outcomes.
Do not run a third simulated-answer variant hoping for a clearer number —
both corrections above were made because a specific, identified
methodological flaw was found (under-provisioned information, then a crash),
not because the prior result was inconvenient. There is no flaw remaining to
correct; further variation now would be exactly the multiple-comparisons
trap `src/analysis/__init__.py`'s own design discipline exists to name and
avoid.

## Reproducing

```bash
python scripts/run_lens_probe_validation.py \
    --fixture decision-studio-ui/scratchpad/dq_comparison/lens_run \
    --n 10 --out <a fresh directory>
```

Cost: Haiku-tier only (Stage 1 + lens-probe generation + simulated-answer
generation), no synthesis calls. Each full run costs well under $1.
