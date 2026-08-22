# DQ Link 1: Reading the Recorded Frame Instead of Guessing From Prose

**Status: Design note, not built. Deliberately not built yet — see "Why this isn't ready to ship" below.**

## What prompted this

Running `score_dq_run.py` against a live lens-council run (CFO, framed against `units_sold` instead of
`net_revenue`, Aug 21 2026) scored **6/6, chain verdict PASS** — the first full pass across this
session's entire DQ testing history. Every prior run failed L1.

Tracing why: `score_run()`'s signature is `score_run(solutions, *, da_result=None, run_id="?")`. It has
**no access to the framing decision at all**. L1 currently infers "was an appropriate frame examined"
by scanning the SF synthesis text for `FRAME_WIDENING_PATTERNS` vocabulary (exit/divest/deprioritize/
reallocate-capital/etc.) — a guess at something the system already knows with certainty: the framing
gate (Phase 19) persists the actual decision to the registry as an `Assumption` with
`record_type="framing"`, `framing_choice: "confirm_stated" | "alternative" | "other"`,
`decided_by_role`, a timestamp. `score_run()` never reads it.

Checked both failure directions on real data this session, not hypothetically:
- **False negative**: my own hand-written `strategic_causal_graph_design.md` examples (a COGS reframe,
  a price-lock-covenant reframe) were genuine frame-widening candidates and did not trip
  `FRAME_WIDENING_PATTERNS`.
- **False positive risk**: already documented in the rubric (71%), and this run itself had a borderline
  case — "deprioritizing" matched, but the sentence described *customer* behavior ("buyers and reps
  deprioritizing a compressed-margin SKU"), not a company decision. The pass held up on inspection
  because a genuinely separate strategic option (National Auto Parts Chain B exit/de-emphasis) also
  used qualifying language — but that was one option out of three, and the match itself was partly
  coincidental about *which* words happened to land where.

## Why the obvious fix is not simply correct

The first version of this proposal was: replace the vocabulary scan with
`framing_choice != "confirm_stated"`. That's wrong, or at least incomplete, and worth being precise
about why rather than shipping it on the strength of one good-looking run.

**L1's own stated definition** (`decision_quality.py`'s docstring): *"Does the decision ever consider a
response other than recovering this KPI within its existing structure?"* — this is a claim about the
**solutions considered**, not about which KPI was selected as the objective. Those are related but
genuinely different facts:

- The framing gate measures whether the **objective** was examined before generating solutions — was
  Net Revenue's own recovery the target, or was units_sold (a different, causally upstream KPI)
  substituted in instead.
- L1 as documented measures whether the **solution set**, once generated, ever proposes something
  structurally different from operating the existing setup better — exit, divest, reallocate capital,
  not just tune a lever.

Today's run happened to have both: the CFO picked a different objective, *and* the lens council
separately proposed a genuine customer-portfolio-exit option. But those aren't guaranteed to co-occur.
A run where the CFO picks `units_sold` and all three resulting solutions turn out to be purely
operational volume-recovery tactics (no exit, no reallocation, nothing structural) would, under the
naive `framing_choice != "confirm_stated"` rule, **still score L1 PASS** — because an alternative
objective was picked, not because anything structurally wider was ever actually considered. That is not
what L1 claims to measure, and shipping it would very likely raise the apparent pass rate without making
the score more accurate — just differently wrong, and biased toward "PASS whenever the framing gate was
engaged with," which is a much lower bar than the link's own name implies.

## The self-referential risk, named directly

This session spent several hours building the exact machinery — `causal_direction`, the hop-1 and hop-2+
path-validity filters, the three Sales KPI causal edges — that made today's `units_sold` framing possible
at all. That work is separately justified and already verified correct on its own terms (live-tested,
regression-tested, committed). But changing the **scoring mechanism itself**, in the same sitting, on the
strength of the one run that machinery just enabled, is exactly the failure mode
`theory_layer_design.md`'s own guardrail section warns about for a different case ("HITL confirmation is
not scientific validation" — agreement with a narrative one just helped construct is not the same as an
independent test of it). The fact that a fix I built moments ago produced a good-looking score on the
next thing I built moments after that is not evidence the *scoring* is more correct — it's exactly the
pattern that should raise suspicion, not lower it.

## What's actually defensible: report both, collapse neither

Rather than replacing the L1 verdict with a new single inference, report the two facts side by side, each
verified independently:

- **`objective_examined`** — read directly from the persisted framing record:
  `framing_choice != "confirm_stated"` (was a different objective genuinely chosen, on the record,
  attributed to a named role). This is a hard fact, not an inference, and needs no vocabulary matching at
  all. Threading it in is mechanically simple: `score_run()` gains an optional `framing_record` parameter.
- **`solutions_widened`** — the existing L1 check, unchanged: does the *solution set* propose something
  structurally different (vocabulary scan + `STRUCTURAL_FAMILIES` classification).

Neither one alone is "L1." Report both, let a human (or a future weighting decision, made deliberately,
not defaulted into) decide how they combine — the same posture `causal_rung`/`provenance` already take
for the causal graph (two axes, never silently conflated into one score).

## Falsifiable prediction — corrected 2026-08-22, the original plan wasn't executable

The first version of this plan said: score the existing 13/33-option corpus
(`tools/ab_harness/scope_arm_*.json`, referenced in `decision_quality_rubric.md`) with
`objective_examined` and `solutions_widened` computed side by side. Checked directly before running
it: **that corpus cannot supply `objective_examined` at all.** It was added 2026-08-15 — each file is
a raw SF workflow-record dump from the Stage I evidence-scope A/B harness (`tools/ab_harness/`), a
scripted test path that never touches the framing gate or persists an `Assumption` with
`record_type="framing"`. This predates Phase 19 by weeks. `objective_examined` isn't missing a field
for these runs — there is no fact for it to read. Scoring the corpus with both signals "side by side"
would silently produce `objective_examined = None` for all 13, every time — not a divergence result,
a vacuous one. The prediction as written could not have been tested against the corpus it named.

**The two questions this note bundled together have different preconditions and had to be split:**

- **`solutions_widened` alone needs no framing record** — pure SF-output text analysis, already
  computable for any corpus, including this one. Run 2026-08-22 against all 13 files: **13/13 scored
  cleanly, 2 PASS (`scope_arm_D1`: "delist, discontinu[e]"; `scope_arm_E2`: "exit"), 11 FAIL** (*"every
  option recovers the breached KPI within its existing structure"*). This is a real result for the
  existing signal on its own — consistent with the broader pattern already on record elsewhere in this
  project (a large majority of runs never propose anything structurally wider), though it should not be
  read as confirming the specific "71%" figure quoted in `strategic_causal_graph_design.md`, which
  measured something adjacent, not identical. The two PASS cases carry the same false-positive caution
  already named above in this note (a vocabulary match can land on the wrong subject) and were not
  manually re-adjudicated here.
- **`objective_examined` needs real framing-gate runs**, and the independence bar had to be corrected
  too: "predating this session entirely" is no longer achievable by construction — the framing gate
  *is* this session's own work, so every run with a real framing record was necessarily produced by it.
  The honest bar is narrower: runs whose *specific framing decision* wasn't shaped by the identity-
  reclassification work done today (`kpi_relationship_basis_design.md`). **That bar still isn't met.**
  Every framing-gate run that currently exists — `gross_margin_reframe_run`, `ecommerce_confirm_run`
  (both 2026-08-22), and the Aug 21 `units_sold` run this whole note was originally written about — was
  generated by this session testing its own machinery. Using any of them as "the validation" repeats
  exactly the self-referential pattern this note exists to guard against.

**So the real requirement for the `objective_examined` half is accumulation, not a build step.** Genuine
framing-gate usage this session had no hand in — future demos, sessions run by someone else, or simply
more calendar time between building the feature and testing it against it — has to happen before an
honest divergence test is possible. No amount of code written today closes that gap; it isn't a
plumbing problem.

## Why this isn't ready to ship

- **Half the held-out validation is done, half is structurally blocked.** `solutions_widened` scored
  clean against the old 13-run corpus (2026-08-22, above). `objective_examined`'s divergence test cannot
  run yet — not unexecuted, *blocked*, on a real independent-run corpus that doesn't exist. This is a
  different, harder kind of "not ready" than the note originally described.
- `score_run()`'s signature change is small, but nothing consumes a `framing_record` today; the plumbing
  from the framing gate (`ProblemRefinementResult.framing_record`) through to wherever DQ scoring is
  invoked doesn't exist yet either.
- Whether `objective_examined`/`solutions_widened` should stay two separate advisory signals forever, or
  whether one of them should eventually become a hard gate, is a real decision this note deliberately
  does not make.

## Recommended sequencing

| Piece | Recommendation |
|---|---|
| ~~Run the held-out validation~~ `solutions_widened` on the old corpus | ✅ Done 2026-08-22 — 13/13 scored, 2 PASS / 11 FAIL |
| Accumulate real framing-gate runs this session had no hand in | **Blocking, not scheduled** — needs real usage over time, not a task this session can complete by writing more code |
| Once accumulated: score `objective_examined` vs `solutions_widened` on that independent set | Only after the above — this is the actual falsifiable test |
| Thread `framing_record` into `score_run()`, report `objective_examined` alongside the existing L1 (`solutions_widened`), not instead of it | Only after validation supports it |
| Decide whether either becomes a hard gate instead of advisory | Explicitly deferred — a product decision, not a scoring-mechanics one |
