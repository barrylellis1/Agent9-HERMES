# Decision Quality Rubric — outcome measure for Stage H/I

**Status:** 🏁 **BUILT AND RUN (2026-08-15).** `src/analysis/decision_quality.py`,
`tools/ab_harness/dq_score.py`, 19 tests in `tests/unit/test_decision_quality.py`.
All 11 saved arms scored. **$0 of new API spend.** Results in §8.
**Purpose:** supply the missing referent that `persona_council_experiments.md` §5 names —
*"until 'better' has a referent, every additional arm refines a number nobody should act on."*
**Corpus:** the 11 `tools/ab_harness/scope_arm_*.json` payloads already on disk. No new API spend.

---

## 1. Why a rubric rather than another arm

Every instrument built so far measures a **proxy**: divergence (`b3_question_divergence`), lever-family
stability (`mechanism.py`), citation hygiene (`groundedness.py`). Each was chosen because it was
measurable. None of them is the objective, and two experiments have now returned nulls that the
proxies could not explain:

| experiment | varied | result |
|---|---|---|
| B-3 roster (7 arms) | council composition | topics converge everywhere; ~7% artefact catch |
| Step 1 frame-challenge (D1/D2) | task-statement permission | 0 of 6 options took the invitation |

Both nulls are consistent with the binding constraint sitting **upstream of the council entirely**.
A rubric that scores the decision rather than the council can distinguish that from a council defect;
divergence cannot.

## 2. The standard being adopted

**Decision Quality (Stanford SDG — Spetzler, Matheson & Howard).** Six requirements, evaluated as a
chain: overall quality is the **weakest link**, not the average. Chosen over the alternatives because:

- It is a **standard, not a procedure.** It scores an artefact and asks nothing of the customer's
  meeting structure, forum, or decision rights — the property that keeps Agent9 a software purchase
  rather than a change-management engagement.
- It is already native to capital-allocation organisations in process industries (Chevron, Eli Lilly),
  which is the launch ICP.
- Its first link is **frame**, which is exactly the thing neither prior experiment could vary.

Related work deliberately **not** adopted as the rubric, and why:

| framework | why not the rubric |
|---|---|
| Kahneman/Sibony **MAP** + 12-question checklist | Adopted as a *structural* prescription for Stage I (independent assessments of *different* dimensions, holistic verdict last), not as the score. Complements DQ; does not replace it. |
| **Vroom-Yetton-Jago** | Prescribes how much consultation a decision needs — governance, not deliberation quality. Belongs in onboarding config, not in a grader. |
| **KT Decision Analysis** (MUST/WANT) | Compatible and recognisable to process-industry buyers; folds into link 4 rather than standing alone. |
| **AHP** | Rank reversal; weight elicitation is gameable. Sophisticated buyers know this. |

## 3. The six links, mapped to fields that already exist

Scoring must obey the `src/analysis` house rule: **True / False / None, where None means not-checked
and is excluded from both numerator and denominator.** Not-checked is never pass.

| # | DQ link | Checkable from | Existing instrument |
|---|---|---|---|
| 1 | **Appropriate frame** | `problem_reframe`; whether any option's lever family or `impact_estimate.scope` reaches outside the single breached KPI | `mechanism.py` lever families — new check |
| 2 | **Creative alternatives** | count of **distinct lever families** per run, not option count. 3 options all `indexation` is one alternative presented three ways | `mechanism.py` fingerprint — reuse as-is |
| 3 | **Reliable information** | citation hygiene, cross-segment summation, the cost-allocation artefact question | `groundedness.py` G1–G5 + `check_slice_validity.py` |
| 4 | **Clear values & tradeoffs** | `tradeoff_matrix`, `expected_impact`/`cost`/`risk` scalars — **and whether the criteria producing them are ever stated** | new check |
| 5 | **Sound reasoning** | `moderator_grades.arithmetic_consistency`, narrative claim arithmetic | `narrative_claims.py` + moderator grades |
| 6 | **Commitment to action** | `decision_ask`, `immediate_actions`, `next_steps`, `human_action_required` | new check (structural presence) |

Note `unresolved_tensions` and `blind_spots` are already populated and are honest inputs to links 1
and 3 — the payload is richer against this rubric than against any proxy measured so far.

## 4. Prediction, recorded before scoring

Per the §4 methodology rule (*state the prediction before running*), and recorded here rather than in
a conversation so it cannot be reconstructed after the fact:

> Links **1 (frame)** and **2 (alternatives)** fail broadly. Links **3, 5, 6** mostly pass. Link **4**
> is partial — the scalars are present, the criteria behind them are not stated.
> **And: the moderator's existing grades correlate with links 3 and 5 — the ones already passing.**

If that last clause holds, the moderator is grading the strong links and is silent on the weak ones,
which would relocate Stage H's next increment from rubric-tuning to frame.

Falsifier: if links 1 and 2 pass on the post-fix stratum, the frame hypothesis is wrong and the
`0 of 27` structural-option finding needs a different explanation.

## 5. Corpus and its limits

11 arms × 3 options = **33 options**. Stratify — do not pool:

| stratum | arms | n | note |
|---|---|---|---|
| pre-fix | A, A0, A0C, B, B0, C | 18 | generated over the broken `_build_kt_summary` unit string (§7c) |
| post-fix | C1, D1, D2, E1, E2 | 15 | clean context; C1 is the control, E1/E2 the lens swap |

- The PM-2 A/B `ab_raw` payloads are **gone** — scratchpad-only, not recoverable. The 27-option figure
  quoted in `persona_council_experiments.md` §7c cannot be fully re-scored; 33 is what survives.
- 🔴 **All 33 options are one problem** (lubricants `gross_margin_pct`, one frozen DA result). A
  uniform failure on link 1 is therefore consistent with *"this problem has one right frame"* as well
  as *"the pipeline forecloses the frame."* The rubric cannot separate those on this corpus. A second
  `cell_key()` — ideally a `distributed` or `no-control` problem shape (V9) — is required before any
  frame conclusion is load-bearing.
- Term screens remain **screens, not verdicts** (§5, 71% false-positive rate on the artefact screen).
  Links 1 and 4 are semantic and will need adjudication recorded as data beside the screen.

## 6. Open, for decision before the scorer is written

1. **Is link 1 scored per-run or per-option?** Frame is a property of the run; the other five are
   per-option. Mixing granularities in a weakest-link chain needs an explicit rule.
2. **Does a failed link 1 cap the chain?** Strict DQ says yes — weakest link governs. That would score
   every run to date as low quality regardless of links 2–6, which is either the correct and useful
   result or an instrument that says one thing forever.
3. **E1/E2 provenance.** `scope_arm.py` was modified at 09:42, between the E1 (09:41) and E2 (09:47)
   runs. Roster, `max_hops` and the input payload stamp are identical across both, so they are
   comparable on config — but §7b's own lesson (*do not edit under the reload watcher*) means E2
   should not be treated as a clean replicate of E1 until that edit is identified.

## 7. Where this lands: a module, not an agent

`src/analysis/` is a **deterministic, LLM-free checking library serving two consumers** — the offline
harness and the live agents. It is not a dev-time-only package, and half of it has already graduated:

| module | runtime consumer |
|---|---|
| `problem_profile.py` | `a9_deep_analysis_agent.py:2785` — live |
| `narrative_claims.py` | `a9_solution_finder_agent.py:2805` — live |
| `mechanism.py` | tests + harness only |
| `groundedness.py` | tests + harness only |

`decision_quality.py` joins as a fifth module and follows the **precedented** path, not an invented
one: score saved payloads first, graduate only if the checks discriminate. `narrative_claims` walked
exactly this route, and the reason it graduated is recorded in the plan — *"detection that reaches
only an audit payload is a smoke alarm wired to a notepad."*

**It is not a new agent, at any stage.** A new agent costs a registry entry, a card, a PRD, lifecycle
methods and orchestrator wiring, in exchange for wrapping a pure function over a payload that is
already in memory. The component that would consume DQ verdicts already exists: the Stage H moderator.
Graduation is an edit to `moderator_section` in the SF agent, nothing more.

**Compute the links deterministically; do not ask the moderator to self-grade against them.** The PM-2
readout established that moderator grades are **stochastic on identical input** (`arithmetic_flags`
went 0→3→0→1→n/a across five runs of the same payload). A DQ completeness score inherits that wobble
if the LLM produces it — and a quality score shown to an executive that moves when nothing moved is
worse than no score. This is the same reasoning that created `src/analysis` in the first place: *a
model-based judge would wobble run-to-run and make process noise indistinguishable from measurement
noise.* Links 2, 3, 5 and 6 are computable without a model. Links 1 and 4 are semantic and stay
advisory until proven otherwise.

**Customer-facing DQ scoring is destination three, and is gated on destination two being stable.**
Do not render a link count in the HITL gate or a briefing until repeat runs on fixed input produce the
same count.

---

## 8. 🏁 RESULT (2026-08-15) — 11 arms, 33 options, $0 new spend

| link | post-fix (5) | pre-fix (6) | all 11 |
|---|---|---|---|
| 1 frame *(advisory)* | 2/5 | 0/6 | **2/11** |
| 2 alternatives | 4/5 | 6/6 | 10/11 |
| 3 information | 5/5 | 6/6 | **11/11** |
| 4 tradeoffs *(advisory)* | 0/5 | 0/6 | **0/11** |
| 5 reasoning | 5/5 | 5/6 | 10/11 |
| 6 commitment | 5/5 | 6/6 | **11/11** |

**Chain capped by:** frame ×9, tradeoffs ×11, alternatives ×1, reasoning ×1. **No run holds the chain.**

*(Link 2 figures are post-taxonomy-extension — see §9. Before `mix_shift` and `hedging` existed it read
8/10 with one undetermined, which is why the extension was made before anything was concluded.)*

### Prediction scorecard (§4, recorded before running)

| # | predicted | outcome |
|---|---|---|
| 1 | frame + alternatives fail broadly | **frame ✅** (9/11 fail). **alternatives ❌** — 8/10 pass |
| 2 | links 3, 5, 6 mostly pass | ✅ 11/11, 10/11, 11/11 |
| 3 | link 4 partial — scalars present, criteria unstated | ❌ **worse than predicted**: criteria *are* stated and weighted, and fail 11/11 for a different reason (below) |
| 4 | moderator grades the links already passing | ✅ **confirmed by inspection** |

Two of four wrong. Recording that plainly, because the value of a pre-registered prediction is
entirely in being allowed to lose.

### Finding 1 — link 4 fails 11/11, and it is a product defect, not a measurement artefact

Every run's tradeoff matrix carries **the identical vector**: `impact=0.5, cost=0.25, risk=0.25`.
That is `A9_Solution_Finder_Agent_Config.weight_*`, reached through

```python
criteria = request.evaluation_criteria or [TradeOffCriterion(name="impact", weight=self.config.weight_impact), ...]
```

`request.evaluation_criteria` is **never populated by anything**. So every decision Agent9 has ever
produced was ranked against a system constant, and it renders as a fully-populated weighted matrix
that passes any presence check — which is why nobody caught it. DQ's fourth link asks whether *this
decision maker's* values were made explicit; the answer has always been no.

This is the finding with a design already waiting for it: `principal_lens_weighting_design.md`
specifies role-based lens weighting per principal. The intent exists; the wiring does not.

### Finding 2 — the moderator is structurally blind to every failing link

Union of `moderator_grades` keys across all 11 arms:

`constraint_survival` · `causal_grounding` · `arithmetic_consistency` · `critic_findings_response`

Those map to links **3 and 5** — the two scoring 11/11 and 10/11. There is **no rubric item for
frame, alternatives, or values**, the three links that actually fail. The moderator grades the strong
links and cannot see the weak ones. Prediction 4 confirmed, and it relocates Stage H's next increment
from rubric-tuning to rubric-*coverage*.

### Finding 3 — 🔴 the "0 of 27 structural options" claim in `persona_council_experiments.md` §7c is wrong as stated

Arm **D1 opt_2, "Immediate SKU Rationalization + Staged Q3 Contract Reset"**, proposes discontinuing
and delisting SKUs — acting on portfolio composition rather than on the price or cost of the existing
portfolio. D1 is one of the six frame-challenge *treatment* options the §7c entry reports as `0/6`.
Arm **E2 opt_3** likewise proposes "SKU exit/de-emphasis" with volume reallocated elsewhere.

The §7c null was read at *category/portfolio-exit* granularity; SKU rationalisation was not counted.
That may be a defensible line, but it was never stated, and the headline `0 of 27` is doing work the
adjudication does not support. **Re-adjudicate with a written criterion before that number is quoted
again.** It does not overturn the direction of the finding — 2 of 33 is still close to the floor.

### Instrument defects found and fixed BEFORE any number above was reported

Both were caught by adjudicating screen hits rather than trusting them, per §5's 71%-FPR lesson.

| defect | effect | fix |
|---|---|---|
| `unclassified` counted as a lever family | Arm E2 (1 real family + 2 unnameable options) scored a confident **PASS** on link 2 | Unclassified never counts; when it would decide the verdict, link 2 returns **None** |
| `volume_for_margin` auto-passed link 1 | Its `full[-\s]potential` pattern matched Bain vocabulary on arm A's ordinary recovery plan — a **false positive** | Auto-pass removed. Mechanism taxonomy classifies *mechanism*, never *frame* |

Both are regression-tested. Frame-screen adjudications (2 genuine, 1 rejected) are recorded as data
in `dq_score.py`, next to the screen, not folded into the regex.

### Secondary finding — the lever taxonomy has two gaps

`unclassified` appears in **6 of 11 arms**. Reading the titles, two recurring levers have no family:
**mix-shift** ("Phased Mix Shift Toward Compressor Oil", "Reallocate Anchor Retail Mix Toward
Premium") and **hedging** ("Base Oil Feedstock Hedging", "Forward-Buy Hedge"). `mechanism.py`'s
taxonomy was derived from 13 payloads in Aug 2026 and has not been revisited since. Until it is,
link 2 is unreliable wherever unclassified appears — which is why it now abstains rather than guesses.

### What this authorises

1. **Wire `evaluation_criteria` from the principal** — highest value, smallest change, and it closes a
   defect that has silently affected every ranking the product has ever produced.
2. **Extend the moderator rubric to the links it cannot currently see**, or accept that frame and
   alternatives are not gradeable at synthesis time and handle them upstream. Do not tune the four
   existing rubric items; they grade what already passes.
3. **Add `mix_shift` and `hedging` to `mechanism.LEVER_PATTERNS`**, then re-run — link 2's numbers are
   provisional until then.
4. **Re-adjudicate §7c's `0/27`** with a written criterion for what counts as a structural response.
5. **Still required before any frame conclusion is load-bearing:** a second problem shape. All 33
   options are one KPI on one DA result, so "frame fails 9/11" remains consistent with *this problem
   has one right frame*. Nothing above changes that limit.

---

## 9. 🔴 The lens-swap comparison cannot currently be read (2026-08-15)

Extending the taxonomy with `mix_shift` and `hedging` (§8, authorisation 3) made link 2 readable for
the first time. The result is not the one the lens hypothesis wanted.

| arm | roster | distinct lever families |
|---|---|---|
| A | MBB (pre-fix) | **3/3** |
| A0 | MBB (pre-fix) | **3/3** |
| A0C | MBB (pre-fix) | **3/3** |
| B | MBB (pre-fix) | **3/3** |
| B0 | MBB (pre-fix) | 2/3 |
| C | MBB (pre-fix) | **3/3** |
| **C1** | **MBB (post-fix) — THE CONTROL** | **1/3** |
| D1 | MBB + frame flag | 2/3 |
| D2 | MBB + frame flag | 2/3 |
| E1 | lens | **3/3** |
| E2 | lens | **3/3** |

**3/3 is not a lens property.** MBB reached it in 5 of 6 pre-fix runs. The lens arms match that
ceiling; they do not exceed it.

**And C1 — the control the entire lens swap is measured against — is the single worst run in the
corpus.** Two lens runs are being compared against one control draw that is an outlier in the
direction that flatters the treatment. That is `feedback_one_observation_is_not_a_baseline` again, at
n=1, on the control side this time.

### The pattern that actually wants explaining

Every post-fix MBB run (C1=1, D1=2, D2=2) scores **below every pre-fix MBB run but one** (3,3,3,3,2,3).
The build changed between them: the `_build_kt_summary` unit fix (§7c) replaced `$-7 (0.0% of
variance)` on every driver with correctly-ranked `pp` values.

Hypothesis worth testing, not asserting: **a correctly-specified problem invites a narrower answer.**
Before the fix, personas saw an undifferentiated smear and had to invent breadth; after it, they see
one dominant driver (Synthetic Blend, −7.14pp) and converge on it. If that holds it is a genuine and
uncomfortable finding — the data-quality fix was unambiguously correct, and may have cost option
diversity. It is equally consistent with noise at these sample sizes.

### What Stage I needs before the lens result means anything

1. **Replicate C1 to n≥3.** Cheapest possible unblock (~$0.20/run), and it is the *control*, so
   nothing can be read without it. Do this before any further lens arm.
2. Only then compare lens vs MBB on the post-fix build, with link 2 and link 1 as the measures.
3. **Do not wire `evaluation_criteria` (§8 authorisation 1) until this closes.** It changes
   `_rank_options`, i.e. *which option is recommended* — a second variable inside a running experiment
   about *which options are generated*. PM-4 applies.

The taxonomy extension itself is safe to land mid-experiment: `mechanism.py` is imported by tests and
the harness only, never by an agent, so it changes measurement and not generation.

---

## 10. 🏁 Stage J scored (2026-08-16) — link 4 passes for the first time

Two new arms, identical but for whether `business_contexts.metadata` carries a posture. Scored as a
**third stratum** — they ran on a later build than either group above and are not poolable with them.

| link | P0 control | P1 posture |
|---|---|---|
| 1 frame *(advisory)* | FAIL | FAIL |
| 2 alternatives | PASS | PASS |
| 3 information | PASS | PASS |
| 4 tradeoffs *(advisory)* | **FAIL** — agent config default | **PASS** — weights from declared posture |
| 5 reasoning | PASS | PASS |
| 6 commitment | PASS | PASS |
| **chain** | capped, 4/6 | capped, **5/6** |

**The pair differ on exactly one link.** That is the result: a well-scoped change moved the link it
was aimed at and nothing else. P1 is the highest-scoring run in the corpus.

### Corpus now 13 runs, 39 options

| link | pass rate | change |
|---|---|---|
| 1 frame *(advisory)* | 2/13 | — |
| 2 alternatives | 12/13 | — |
| 3 information | 13/13 | — |
| 4 tradeoffs *(advisory)* | **1/13** | **was 0/11 — first pass ever** |
| 5 reasoning | 12/13 | — |
| 6 commitment | 13/13 | — |

**Capped by:** frame ×11 · tradeoffs ×12 · alternatives ×1 · reasoning ×1.

### What this changes about the plan

**One of the two systematic caps is now closable on demand.** Link 4 failed 11/11 because nothing
could supply enterprise values; it now passes whenever a client has a posture. That is a
configuration state, not a code gap — every client that gets a posture gets the link.

**Frame is the sole remaining systematic failure**, and it is the one that sits *outside* Phase 15 by
the phase's own goal statement (see DEVELOPMENT_PLAN → Phase 15 → Stage J scope finding). The chain
now reads: everything Solution Finder controls passes; the thing it does not control does not. A run
scoring 5/6 capped only by a link decided three stages upstream is a sharper argument for the frame
work than any of the roster or wording experiments produced.

**Caveat that has not moved.** Links 1 and 4 remain advisory screens, and all 39 options are still one
KPI on one Deep Analysis result. "Frame fails 11 of 13" stays consistent with *this problem has one
right frame* until a second problem shape is scored.
