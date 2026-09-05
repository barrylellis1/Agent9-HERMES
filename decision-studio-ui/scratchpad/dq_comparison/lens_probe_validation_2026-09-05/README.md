# Phase 22 Stage D — lens-probe validation (three runs, corrected methodology)

**Captured 2026-09-05.** Measures whether Stage 22's Stages A–C (persona-keyed
refinement — one framework-anchored clarifying question per persona, replacing
a single persona-invariant refined-problem string) actually increases Stage 1
hypothesis diversity, using `scripts/run_lens_probe_validation.py`. Three
completed runs exist, under different simulated-answer designs; all three are
kept, not just the final one.

**A note on why there's a v3 at all**, given v2's own recommendation said not
to run a third simulated-answer variant: that recommendation was about
re-running the *same* design hoping for a friendlier number — the
multiple-comparisons trap. v3 is not that. It was explicitly requested to
close a different, real gap: v1 and v2 both let "how hedged or confident the
simulated answer happens to be" fall out of uncontrolled temperature=0.8
sampling rather than testing it as its own variable. v3 controls it directly
and is a legitimate widening of the test design, not a re-roll of the same one.

## v3 (current): three prescribed postures, hedging excluded by enforcement — still no improvement, and the "ceiling" turned out to be a baseline-noise artifact

`manifest_v3_prescribed_postures.json`. Same fixture, same lens council, same
complete-DA-output simulator as v2, but the simulated answer is now generated
under one of three explicitly prescribed **postures** —
**conservative** (favor the more risk-averse reading of ambiguous evidence),
**assertive** (commit to the single most likely reading with full confidence),
**middle-of-the-road** (acknowledge the competing reading, still commit to one
working conclusion) — instead of one uncontrolled default stance. All three
share one **enforced, not just requested**, rule: no hedge, no non-answer.
`generate_simulated_answers()` regex-scans every returned answer for hedge
language ("I don't know", "I'd need more data", "unclear", "can't confirm",
etc.) and forces a regeneration if any persona's answer hedges, on the same
retry budget already used for transient API failures. Across all 30 with-lens
calls in this run, **zero regenerations were needed** — every simulated
answer passed the check on the first attempt, confirming the instruction
itself was already being followed, not just backstopped by the check.

| | baseline | conservative | assertive | middle |
|---|---|---|---|---|
| distinct lever families (10 runs) | `[3,2,3,3,3,3,2,2,3,2]` | `[3,3,2,3,1,3,3,2,2,3]` | `[3,3,3,2,3,2,2,2,3,2]` | `[3,2,2,2,2,3,3,3,2,2]` |
| mean | **2.60** | **2.50** | **2.50** | **2.40** |
| runs above / below the baseline mean | — | 6 above / 4 below | 5 above / 5 below | 4 above / 6 below |

All three postures sit at or slightly below baseline, not above — no posture
shows an improvement. Sample answers (conservative vs. assertive, same
question) show the postures are genuinely distinct in stance, not a relabeled
identical answer:

> **Conservative** (commercial): *"...indicates that lower-margin SKUs have
> gained share within the engine oils segment"* — attributes the effect to
> the more cautious, structural-mix explanation.
>
> **Assertive** (commercial): *"...is driven by a combination of both pricing
> pressure and unfavorable mix, with the Value product category showing the
> steepest decline"* — states a firmer, more specific compound claim.

**The "ceiling effect" from v2 does not hold up as a general property of this
fixture.** v2's baseline hit exactly 3-of-3 on all 10 runs; this run's fresh
baseline draw — same fixture, same personas, same code — came back
`[3,2,3,3,3,3,2,2,3,2]`, mean 2.60, not at ceiling at all. The two baseline
distributions disagree with each other more than any with-lens arm disagrees
with either baseline. That reframes what "ceiling effect" meant in v2: it was
this specific draw's outcome, not a structural property of the fixture that
explains away the null result — the real story is that **Stage 1's own
temperature=0 noise floor, run to run, is large enough to rival the effect
size this experiment is trying to detect.** This was already flagged in this
script's own module docstring (temperature=0 "does not guarantee bit-identical
output in practice") but v3 is the first run where it visibly swallows the
between-arm comparison, not just the within-arm one.

## v2 (superseded characterization, files retained as-is): complete DA output — near-neutral, not negative

`manifest_v2_complete_da_output.json`. The simulated executive answering the
lens-probe questions received the **complete DA execution output** — every
change point, every segment, every region, at full detail — not a recap of
any size, with no posture control (temperature=0.8 default stance only).

| | baseline (no lens data) | with lens_refinement |
|---|---|---|
| distinct lever families (10 runs) | `[3,3,3,3,3,3,3,3,3,3]` | `[3,2,3,3,3,3,3,3,3,3]` |
| mean | **3.00** | **2.90** |
| runs above / tied / below the other arm | — | 0 above / 9 tied / 1 below |

Its own write-up (below, unedited) attributed the near-null result to a
ceiling effect specific to this fixture. v3's fresh baseline draw shows that
explanation doesn't generalize — see above.

> Answers under this version are genuinely substantive — real cross-referenced
> figures, not hedges:
>
> *"All six customer segments... and all six regions... show margin
> compression in the -4 to -5 point range, indicating the pressure is
> broadly structural across the customer base... suggesting this is
> category-wide pricing or cost pressure, not localized participation loss."*

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
everything DA produced instead of narrowing what it saw, and corrected further
in v3 by making non-hedging an enforced property of every arm, not just a
side-effect of enough information being present.

A middle attempt (recap matched to `a9_solution_finder_agent.py`'s own
`dataset_recap_lines`, i.e. what a real persona sees) was run but crashed
mid-sweep on an unretried transient LLM failure at run 7/10 — no usable
final number, not counted as a result. The retry logic added afterward
(3 attempts, backoff) is what let v2 and v3 complete cleanly.

## What this three-run arc establishes

- The sharp v1 negative result does not hold up once the harness gives the
  simulator complete information — it was substantially an artifact of
  under-provisioning, not a property of persona-keyed refinement.
- v2's near-null result does not confirm the hypothesis either, and its own
  "ceiling effect" explanation for the null does not replicate in v3's fresh
  baseline draw.
- v3, with hedging excluded by enforcement and posture treated as a
  controlled factor rather than an accident of sampling, still shows no
  posture outperforming baseline — but the gap between any posture and
  baseline (≤0.20 of a family) is smaller than the gap between v2's baseline
  draw (3.00) and v3's baseline draw (2.60) of the *same* no-lens condition.
  **The measurement's own run-to-run noise floor is at least as large as any
  effect it is trying to detect on this fixture.**
- Stages A–C's plumbing is unaffected by any of the three results: `ps_s1` is
  confirmed genuinely persona-keyed by direct unit test
  (`test_sf_lens_probe_persona_keying.py`), independent of what Stage D's
  simulated-executive proxy shows.

## Why this still isn't the real answer, and won't be from a harness

All three runs share the same irreducible limitation: **no live executive
answered these questions.** v3 additionally shows this harness-based
measurement approach itself — `classify_lever` distinct-family count, over a
single fixture, driven by a temperature=0 Stage 1 call whose own
run-to-run variance rivals the effect size sought — may simply be too coarse
and too noisy to resolve what Stage C's real UI is meant to test, independent
of whether lens-probing helps. A real executive might also answer more
confidently, less confidently, or say something the DA payload doesn't even
contain (institutional knowledge, a customer conversation, a competitor's
move) — none of which any simulation, prescribed-posture or not, can
substitute for.

## Recommendation

Do not treat Phase 22 as validated by any of the three runs, in either
direction. Consistent with how this codebase already treats the theory-layer
exhibit's own density gate — clears only through accumulated VA verdicts over
real use, never by seeding — this mechanism's real test can only come from
actual executives answering actual questions through Stage C's shipped UI.
Ship it, watch what real answers look like, re-measure against real HITL/VA
outcomes. Do not run a fourth simulated-answer variant on this same fixture
hoping for a clearer number: three independent, methodologically-distinct
attempts (under-provisioned, fully-provisioned, fully-provisioned +
prescribed posture + enforced non-hedging) now agree that no signal clears
this measurement's own noise floor. A fourth attempt at the same measurement
would be the multiple-comparisons trap `src/analysis/__init__.py`'s own
design discipline exists to name and avoid — the next legitimate move is a
different, larger-N or multi-fixture measurement design, or real usage data,
not another single-fixture N=10 simulated-answer sweep.

## Reproducing

```bash
python scripts/run_lens_probe_validation.py \
    --fixture decision-studio-ui/scratchpad/dq_comparison/lens_run \
    --n 10 --out <a fresh directory> \
    --postures conservative,assertive,middle
```

Cost: Haiku-tier only (Stage 1 + lens-probe generation + simulated-answer
generation), no synthesis calls. Each full run (baseline + 3 postures)
costs well under $1.
