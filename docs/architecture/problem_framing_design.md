# Problem Framing — examining the frame instead of inheriting it

**Status:** Design note, **not built**, no phase assigned. Written 2026-08-16.
**Motivation:** DQ link 1 (appropriate frame) fails **11 of 13** scored runs and is now the *only*
systematic cap left on the chain — see `decision_quality_rubric.md` §8–10.
**Related:** `hitl_decision_philosophy.md` · `theory_layer_design.md` · `persona_council_experiments.md`

---

## 1. The frame is set once, upstream, and never questioned again

Situation Awareness emits a card named after one breached KPI. Everything downstream inherits
*"recover this KPI"* as an axiom:

```
SA card: gross_margin_pct breached
      -> DA refinement interview  — refines HOW to attack it
      -> SF personas              — argue WHICH option attacks it best
      -> moderator                — grades options against constraints and arithmetic
      -> HITL                     — approves one of them
```

**No stage asks whether recovering that KPI is the right objective.** This is verifiable rather than
inferred — here is the full topic vocabulary of the one interview that exists
(`REFINEMENT_TOPIC_SEQUENCE` / `TOPIC_OBJECTIVES`, `a9_deep_analysis_agent.py`):

| topic | asks | inside the frame? |
|---|---|---|
| `hypothesis_validation` | which KT drivers are real | yes |
| `scope_boundaries` | which segments/periods to include | yes |
| `external_context` | factors not visible in the data | yes |
| `constraints` | which levers are off-limits | yes |
| `success_criteria` | what "solved" looks like *for this problem* | yes |
| `replication_potential` | can a benchmark segment be copied | yes |
| `tradeoff_tolerance` | which KPI to give ground on when two are in tension | **closest — still within** |
| `segment_specific_causation` | why this segment specifically | yes |
| `comparison_baseline` | what to compare against absent a control group | yes |

Nine topics, none of them the frame. `tradeoff_tolerance` comes nearest and still presumes the KPI set
is the right set to trade within.

### 1b. 🔴 Worse than inherited — DA *authors* the frame, in SCQA, before any human is engaged

SCQA is a framing device. Its **Q is the frame**, and its A presupposes that Q. So the question is not
only *when* the frame gets examined but *who wrote it*, and the answer is: an LLM call inside Deep
Analysis, before the interview exists.

Ordering, verified in `a9_deep_analysis_agent.py`:

```
execute_deep_analysis()            (:857)
    └── _generate_scqa_summary()   (:2270)  ← the frame is authored HERE
    └── returns scqa_summary       (:2466)  ← and propagates to SF's context
_generate_refinement_question()    (:3628)  ← the interview runs AFTER, and has
                                              no topic that can revisit it
```

And on the fallback path the frame is not merely early, it is **hardcoded**:

```python
scqa_summary = (f"Situation: Reviewing {kpi_name}. Complication: Variance detected vs target. "
                f"Question: Which segments drive the change?")
```

*"Which segments drive the change?"* is a dimensional-attribution question — a frame, asserted as a
constant, whenever SCQA generation fails. Every downstream stage then answers it faithfully. The DA
**recommendation** carries the same problem: it is produced against a frame nobody chose.

This tightens §1's claim. The frame is not passively inherited from the SA card; it is **actively
written by DA and then treated as given** by the interview, the council, the moderator and HITL. Any
framing intervention must therefore sit *before or at* SCQA generation — a `problem_framing` interview
topic placed after `execute_deep_analysis()` refines a frame that has already been committed to prose
and shipped downstream.

**Consequence for §4's proposal:** either the interview must be able to *rewrite* the SCQA Q (and DA's
recommendation with it), or SCQA generation must move to after the framing topic. The second is
cleaner and is the larger change. This is now the first open decision, ahead of those in §8.

## 2. This explains both prior nulls

Two experiments tried to move the option space and both returned nulls:

| experiment | varied | result |
|---|---|---|
| B-3 roster (7 arms) | who is in the council | topics converge under every roster |
| Step 1 frame-challenge (D1/D2) | task-statement *permission* | 0 of 6 options took the invitation |

Both varied things **inside** a frame decided three stages earlier. A council cannot reach outside a
frame it was handed, and permission to leave a frame is not a reason to leave it.

🔴 **This re-reads the D-arm null, and the re-reading matters.** That test established *permission
alone does not move the option space*. It did **not** establish that permission plus an upstream frame
decision fails — that combination has never been run. The flag gave the model licence to propose a
portfolio move while every other input still described a margin-recovery problem. Declining was the
coherent response.

## 3. "The perfect frame" is the wrong target

The instinct is to compute the right frame and feed it in. That reproduces, one layer up and with far
higher stakes, exactly the defect Stage J just closed: **a frame nobody chose.** The tradeoff-weights
lesson generalises — the defect was never that `0.5/0.25/0.25` was the wrong vector, it was that no
human authored it. A computed "optimal frame" is the same failure wearing machinery.

Decision Quality's first link does not ask for a *correct* frame. It asks whether the frame was
**examined**. And the empirical literature points the same way: Nutt's tracked-decision work found the
dominant failure is premature closure on the first framing — roughly two-thirds of managers never
search past their first alternative. Agent9 currently *institutionalises* that failure by handing the
council a frame and asking only for options within it.

**So the objective is not a better frame. It is that the frame is chosen rather than inherited.**

## 4. Proposal — a `problem_framing` topic, asked first

Add a tenth topic and route it to the front of the sequence.

```python
"problem_framing":
    "Establish whether recovering this KPI is the objective, or whether the KPI is a "
    "symptom of an exposure the principal would rather act on directly."
```

**Why the refinement interview is the right home.** It is the only point where a human is engaged
before Solution Finder runs; it is upstream of SF, where the frame actually lives; and the human
answers, so the frame is *chosen*. The system asks — it does not decide. Same division that made
`strategic_posture` work: the interface elicits, the customer authors.

**The question must offer concrete alternatives or it will always get "yes."** A bare *"is this the
right problem?"* is rhetorical. The material for a real question already exists in the theory layer:

> Gross margin is down 7.14pp, concentrated in Synthetic Blend. The causal model says margin is
> downstream of COGS, which is downstream of base-oil cost, and the register shows an active
> price-lock on the anchor account. **Is the objective recovering margin, or reducing base-oil
> exposure?** They imply different work.

That is buildable today from `kpi_relationships` (already traversed at 2 hops by Stage D) plus the
assumption register (already fetched for constraint exposure). No new data.

## 5. Surfaces that would change

| surface | change |
|---|---|
| `TOPIC_OBJECTIVES` / `REFINEMENT_TOPIC_SEQUENCE` | new topic, routed first |
| `PROTECTED_TOPICS` | **decision required** — see §8 |
| `RefinementResult` | new typed field carrying the frame decision + whether it was changed |
| SF synthesis task text | must *accept* a reframed objective — today it requires every option to name "the primary driver of THIS KPI situation" with `recovery_range` "proportional to the observed variance", wording that cannot express a non-KPI objective |
| `decision_quality.py` link 1 | grade the recorded decision, not a term screen |

That fourth row is the one most likely to be skipped and the one that would silently neuter the whole
change: a frame decision that Solution Finder's task statement cannot express is a frame decision with
nowhere to go.

## 6. Risks — and the two that turn out to be already handled

| risk | status |
|---|---|
| Turn starvation from a longer sequence | **Already handled.** `effective_turn_budget()` scales as `max(MAX_TOTAL_TURNS, TURNS_PER_TOPIC_BUDGET * len(sequence))` — added 2026-08-11 after a live 6-topic run reached topic 2 of 6 by turn 5 |
| Sequence length cap | **Already handled** — routing exists; `MAX_TOPICS_IN_SEQUENCE = 6`, so a tenth topic *competes for a slot* rather than extending the interview |
| **Refinement is optional** | 🔴 **Not handled.** Arms A0/B0 ran with no refinement at all. A frame topic only fires when the interview runs, so link 1 would pass *sometimes* — better than never, not a fix |
| Naive question gets "yes" | Mitigated by §4's concrete-alternatives construction; needs live validation |
| Frame examined but SF cannot act on it | §5 row 4 — must land together |

## 7. Alternatives considered and rejected

**Generate N candidate frames and run SF on each, then rank.** Expensive (N× a ~$0.20, ~280s run) and
it converts a judgment into a ranking problem — which the Stage J measurement showed is a *tiebreaker*
that only acts on near-ties. The frame is exactly the decision that should not be settled by a
weighted sum.

**Compute the frame from the causal graph.** Same defect as a computed weight vector: nobody chose it.
Also fragile — three of the six lubricants edges carry `mechanism: null`.

**Grade the frame in the moderator rubric and change nothing else.** Cheap and honest, and worth doing
regardless, but it only *reports* a frame that is still inherited. Detection without a remedy is the
"smoke alarm wired to a notepad" pattern.

**Widen the SA situation card to name the causal neighbourhood.** Real, and complementary rather than
competing — but it changes what SA emits for every card in the system, which is a much larger blast
radius than one interview topic. Worth revisiting if the interview route proves insufficient.

## 8. Open decisions — settle before any code

1. **Does `problem_framing` join `PROTECTED_TOPICS`?** It is link 1 of the chain, which argues yes.
   But protected topics survive truncation, and with a 6-topic cap a fourth protected entry squeezes
   the problem-shape-routed topics (`tradeoff_tolerance`, `segment_specific_causation`,
   `comparison_baseline`) that Stage I B-1 added for good reasons.
2. **What happens when the frame IS changed?** Does DA re-run against a different KPI? Does SF receive
   the original decomposition with a reframed objective? The cheap version — carry the decision as
   context and let SF act on it — is probably right, but it means SF reasons about base-oil exposure
   using a gross-margin decomposition, and that mismatch should be stated rather than discovered.
3. **Does the frame decision reach VA?** A solution accepted under a reframed objective must be
   measured against *that* objective, not the original KPI.
4. **Is a "no, the frame is right" answer recorded?** It must be. An examined-and-confirmed frame
   passes link 1; an unexamined one does not, and the two are indistinguishable unless the confirmation
   is written down. This is the `not-checked is never pass` rule applied to the frame.

## 9. How it would be measured, and what would falsify it

**Measure:** DQ link 1 across matched runs, refinement-on, before and after. Link 1 becomes a check of
the *recorded decision* rather than the current term screen — which also retires a screen with a known
71% false-positive rate on this class of property.

**Falsifier, stated in advance:** if the frame is examined and confirmed unchanged in nearly every run,
this is an expensive way to write `frame_examined: true` into a payload, and the honest conclusion is
that the frame really is determined by the KPI that breached. That result would be worth knowing and
should not be argued away.

**Prerequisite that has not moved:** all 39 scored options are one KPI on one Deep Analysis result.
Frame conclusions stay provisional until a second problem shape is scored — ideally `distributed` or
`no-control`, where the right frame is genuinely less obvious than it is on a single dominant driver.
