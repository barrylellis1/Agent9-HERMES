# Problem Framing — examining the frame instead of inheriting it

**Status:** Design note, **not built**. **Phase 19** (assigned 2026-08-16). Written 2026-08-16.
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
written by DA and then treated as given** by the interview, the council, the moderator and HITL.

**Consequence for §4's gate — this is a placement constraint, not just an ordering preference.**
Unbundling the gate from the interview (§4) solves *optionality* but not *position*: a mandatory gate
that fires after `execute_deep_analysis()` still arrives too late, because SCQA — and DA's
recommendation — are already written and shipped downstream.

### ✅ DECIDED (2026-08-16) — SCQA is the OUTPUT of framing, not an input to it

`_generate_scqa_summary()` and DA's recommendation move to **after** the framing gate and are produced
*against the chosen frame*. The rejected alternative was letting the gate rewrite an
already-generated SCQA, which keeps a discarded frame in the payload and in the reader's head.

This is the correct reading of what SCQA *is*. Situation–Complication–**Question**–Answer is a framing
device whose Q is the frame; generating it before the frame is chosen means the framing device is
doing the framing. Once the order is right, SCQA becomes the artefact that *records* the chosen frame,
and its Q is the answer to the gate rather than a substitute for it.

### 1c. 🔴 The display is itself premature framing — and the hierarchy is inverted

Moving generation is necessary but not sufficient. **The DA console currently anchors the reader on
the frame before anything asks them to choose one**, and it does so in the strongest possible way.

`DeepFocusView.tsx` renders `ScqaBlock` at the top of the Analysis panel, and inside it:

| SCQA element | treatment | line |
|---|---|---|
| **A** (answer) | **shown FIRST**, labelled **"Recommendation"**, `text-lg font-medium text-white` in a highlighted card | `:78-83` |
| S (situation) | body text, `text-slate-300` | `:97-101` |
| C (complication) | body text, `text-slate-300` | `:103-106` |
| **Q** (the frame) | **shown LAST**, `text-slate-500 italic text-xs` — the least prominent element on screen | `:107-109` |

**The visual hierarchy exactly inverts the epistemic order.** The reader sees a confident
recommendation in large white type before they see the question it answers, and the question — the
frame, the thing the gate exists to put in play — is styled as a footnote.

By the time a framing gate asks *"is recovering this KPI the objective?"*, a user who has read this
panel has already been given the answer to a question they were never asked. Their "yes" is an
anchored confirmation, not a choice — **which reproduces the rubber-stamp failure the gate exists to
prevent**, and would do so invisibly, because the gate would report `frame_examined: true`.

**Therefore the console must not render SCQA or DA's recommendation before the gate.** What it *can*
show pre-gate is the evidence, which carries no frame: KT Is/Is-Not, change points, dimensions
analysed, and the §4.5 deny-list exclusions. Facts first, frame chosen, then narrative and
recommendation generated against it.

**This is the first thing to settle**, because it determines where the gate physically sits, what
moves with it, and what the console shows in the meantime.

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

## 4. Proposal — a mandatory one-question framing gate, unbundled from the interview

> **Revised 2026-08-16.** The first draft proposed a tenth *topic inside* the refinement interview.
> That inherits the interview's optionality — arms A0/B0 ran with no refinement at all — so link 1
> would have passed only sometimes. **Unbundle it.** The refinement interview is 5–10 turns and making
> that mandatory is a real imposition on a user; the frame is **one question**. A single mandatory gate
> is a far smaller ask than a mandatory interview, and it closes the gap properly.

```python
"problem_framing":
    "Establish whether recovering this KPI is the objective, or whether the KPI is a "
    "symptom of an exposure the principal would rather act on directly."
```

**Mandatory, and independent of whether the full interview runs.** The gate fires on every situation
that reaches Solution Finding. The interview remains optional and unchanged.

**Why a human answers it.** The frame is *chosen*, not computed — the system asks, it does not decide.
Same division that made `strategic_posture` work: the interface elicits, the customer authors.

**The question must offer concrete alternatives or it will always get "yes."** A bare *"is this the
right problem?"* is rhetorical. The material for a real question already exists in the theory layer:

> Gross margin is down 7.14pp, concentrated in Synthetic Blend. The causal model says margin is
> downstream of COGS, which is downstream of base-oil cost, and the register shows an active
> price-lock on the anchor account. **Is the objective recovering margin, or reducing base-oil
> exposure?** They imply different work.

That is buildable today from `kpi_relationships` (already traversed at 2 hops by Stage D) plus the
assumption register (already fetched for constraint exposure). No new data.

### 4b. The burden falls over time — and the store already exists

A mandatory gate sounds like a permanent tax. It is not, because **a frame decision is an assumption**,
and the assumption register already models exactly this:

| `Assumption` field | carries |
|---|---|
| `text` | *"We are treating margin recovery as the objective, not base-oil exposure reduction."* |
| `provenance` | `template` → `hitl_proposed` → `confirmed` → `va_validated` — the accretion ladder |
| `validated_by` | `human_confirmation` for a chosen frame |
| `falsification_criterion` | 🔴 **what would make this frame wrong** |
| `expiry` | 🔴 **frames go stale, and this says when** |
| `linked_situation_id` / `linked_solution_id` | ties the frame to the run it governed |
| `client_id` | tenant-scoped, so accretion never crosses a client boundary |

So the first framing conversation for a client is elicitation; later ones are **confirmation against
recorded evidence**, which is cheaper without being emptier.

🔴 **The failure mode this must avoid, and the two fields that prevent it.** The obvious risk of
accretion is that a remembered frame becomes **the new unexamined default** — the system offers "same
frame as last time?", the user clicks yes, and precedent hardens into assumption. That is precisely
the defect closed twice already today: the tradeoff-weights constant nobody authored, and the
rubber-stamped LLM-proposed posture. A remembered frame accepted without examination is the same
disease wearing a longer history.

`falsification_criterion` and `expiry` are what make the difference. The second conversation is **not**
*"is this still the frame?"* — it is:

> You framed this as margin recovery on 14 June, because base-oil elevation looked cyclical. The
> falsification criterion you set was elevation persisting past Q4. **It has.** Does the frame still
> hold?

Confirmation against evidence, not a rubber stamp. This is the same machinery as **11J's
market-condition drift re-query** (re-querying MA for `validated_by="ma_query"` assumptions to check
they still hold), pointed at frames instead of solution assumptions.

**Already half-designed elsewhere:** the Structural lens's stated recommendations include *"flag an
assumption (continued category participation) for the record rather than silently accepting it"* —
that is a frame assumption written to this register. The intent is connected; nothing has wired it.

### 4c. On recording past interviews — split by purpose

| purpose | what to keep | why |
|---|---|---|
| **Accretion, same client** | the **typed decision** in the register | queryable, gradeable, expirable. A transcript is a weaker form of the same thing that nothing downstream can act on |
| **Cross-client learning** | transcripts — but as a **research asset**, not a product feature | genuinely useful for improving the system, and it crosses the tenant boundary that the RLS and client-isolation work exists to defend. Keep per-tenant and out of any shared corpus unless that is a separate, deliberate decision |

## 5. Surfaces that would change

| surface | change |
|---|---|
| **framing gate** | new, **mandatory**, fires before SF regardless of whether the interview runs. NOT a `REFINEMENT_TOPIC_SEQUENCE` entry — unbundling means `PROTECTED_TOPICS` and `MAX_TOPICS_IN_SEQUENCE` are untouched, and the Stage I B-1 routed topics keep their slots |
| `_generate_scqa_summary()` + DA recommendation | **move to after the gate**, generated against the chosen frame (§1b decision) |
| `DeepFocusView.tsx` — `ScqaBlock` | 🔴 **must not render pre-gate.** Today it shows the answer first as "Recommendation" in `text-lg text-white` and the Q last in `text-slate-500 italic text-xs`, anchoring the reader on a frame nobody chose. Pre-gate the panel shows evidence only: KT Is/Is-Not, change points, dimensions analysed, §4.5 exclusions |
| `Assumption` register | the frame decision is written here with `falsification_criterion` + `expiry` (§4b). No new model needed |
| `RefinementResult` | carries the frame decision + whether it was changed, when the interview does run |
| SF synthesis task text | must *accept* a reframed objective — today it requires every option to name "the primary driver of THIS KPI situation" with `recovery_range` "proportional to the observed variance", wording that cannot express a non-KPI objective |
| `decision_quality.py` link 1 | grade the recorded decision, not a term screen |

That fourth row is the one most likely to be skipped and the one that would silently neuter the whole
change: a frame decision that Solution Finder's task statement cannot express is a frame decision with
nowhere to go.

## 6. Risks — all but two now resolved by design

| risk | status |
|---|---|
| **Refinement is optional** | ✅ **Resolved by unbundling (§4).** The gate fires independently of the interview. This was the one unhandled risk in the first draft |
| Turn starvation / sequence cap | ✅ **Moot.** Unbundling leaves `REFINEMENT_TOPIC_SEQUENCE`, `PROTECTED_TOPICS` and `MAX_TOPICS_IN_SEQUENCE` untouched — the Stage I B-1 routed topics keep their slots |
| A mandatory gate is a permanent user tax | ✅ **Falls over time (§4b).** First conversation elicits; later ones confirm against a recorded falsification criterion |
| 🔴 **Accreted frame hardens into the new unexamined default** | **The real risk, mitigated not eliminated.** `falsification_criterion` + `expiry` turn re-confirmation into a check against evidence — but only if the UI actually *shows* the prior reasoning rather than offering a pre-ticked "same as last time" |
| Naive question gets "yes" | Mitigated by §4's concrete-alternatives construction; needs live validation |
| Frame examined but SF cannot act on it | §5 — the synthesis task text must land with it |

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

## 8. Open decisions — ✅ all settled 2026-08-16 (owner); build prerequisites remain in §9

1. ~~**Does `problem_framing` join `PROTECTED_TOPICS`?**~~ ✅ **Closed by unbundling (§4).** It is not
   a sequence entry at all, so the cap and the protected set are untouched and the Stage I B-1 routed
   topics keep their slots.
2. ✅ **DECIDED (owner, 2026-08-16) — the frame is a "Framing Statement" attached to the Situation
   Card for that KPI.** It becomes a named, attributable artefact the reader sees as a frame, rather
   than a frame absorbed implicitly through SCQA prose. This also does part of §1c's work: the
   hierarchy stops being inverted when the frame is the labelled thing at the top.
   > ⚠️ **Guardrail this needs, or it will be violated within a phase.** SA is a *sensor* — facts
   > only; DA owns interpretation. A Framing Statement is an interpretation, so the card **carries**
   > a human-authored statement, it never *generates* one. If a later change has SA compose the
   > Framing Statement, the frame is authored by machine again and this whole note is undone.
3. ✅ **DECIDED — the frame expires when Value Assurance resolves the bet: a solution it governed is
   validated OR fails.** Event-based, not calendar-based, and better than the date `expiry` this doc
   originally assumed. Both outcomes are genuine re-examination triggers: a failure makes the frame
   suspect, and a success means the problem it named is solved, so the next breach deserves a fresh
   look rather than inheriting a frame that has already done its job.
   > 🔴 **Two consequences to handle.** (a) `Assumption.expiry` is typed as an **ISO datetime string**;
   > an event trigger needs either a new field or VA writing the resolution back to the record. The
   > model does not support this today. (b) **A frame whose solution is never accepted never
   > expires** — the commonest case in a low-adoption pilot. Needs a backstop trigger (no approved
   > solution within N assessment cycles, or re-detection on materially changed evidence), or the
   > accretion ladder quietly becomes the permanent default it was designed to prevent.
4. ✅ **DECIDED — a changed frame starts a NEW Situation Card carrying the corrected frame.** This is
   the stronger answer and it dissolves the mismatch this entry worried about, rather than
   documenting it: SF never reasons about base-oil exposure using a gross-margin decomposition,
   because the decomposition is redone under the chosen frame.
   > 🔴 **The new card must link back to the one it reframed.** Without that link the audit trail
   > shows two unrelated cards and **the evidence that the frame was examined is lost** — which is
   > precisely what link 1 scores. The reframe is the finding; an unlinked pair hides it.
   > ⚠️ **Open mechanical question:** a reframed card may target a KPI that never breached a
   > threshold (base-oil exposure when gross margin is what tripped). Today a card exists *because* a
   > threshold breached. SA needs a legitimate provenance for a card created by reframe.
5. ✅ **DECIDED — yes, the frame decision reaches VA.** A solution accepted under a reframed objective
   is measured against *that* objective, not the original KPI. Note this closes the loop with #3: VA
   is both the consumer of the frame and the trigger for its expiry.
6. ✅ **DECIDED — a "no, the frame is right" answer is recorded.** Examined-and-confirmed passes link
   1; unexamined does not; the two are indistinguishable unless the confirmation is written down.
   The `not-checked is never pass` rule, applied to the frame.
7. ✅ **DECIDED — the frame is owned by the KPI OWNER.** This settles the whose-frame question and
   removes the shard-divergence risk `theory_layer_design.md:97` warns about: one owner per KPI, one
   frame, so two principals cannot drive two different objectives from the same situation. Consistent
   with the dimensional KPI-accountability model.
   > **Implementable today** — `KPI.owner_role` exists (`src/registry/models/kpi.py:143`) and is
   > populated on all 15 lubricants KPIs with real variation (CFO on `ecommerce_revenue`, Finance
   > Manager on `base_oil_cost`), so this is not a new registry field.
   > ⚠️ Two follow-ons. (a) It is a **role**, not a principal id, so owner resolution runs through the
   > role→principal path already logged as tech debt in CLAUDE.md ("Principal ID vs Role-Based
   > Lookup"). (b) A non-owner viewing the KPI sees the owner's frame and cannot change it — correct
   > for consistency, but it needs a **"request reframe"** path, or non-owners will work around it
   > and divergence returns through the back door.

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

---

## 10. The adjudication ran (2026-08-17) — first prerequisite closed, second still open

§9 called for reading the corpus before building anything. That happened — all 13
`tools/ab_harness/scope_arm_*.json` runs read verbatim (`situation`/`complication`/`question`
fields), plus 4 fresh live e2e runs this session (MBB control, MBB+refinement, and the first-ever
live `lens_council` run). 17 runs total, 0 showing evidence the frame was ever offered as a choice.

**Verdict: right call, essentially never examined — not wrong call.** Every one of the 17 assumed
recovering `gross_margin_pct` as the objective and varied only *how*. But the case for that objective
being correct is genuinely strong on this data: a single confirmed external cost shock (an 18% Q2
base-oil spike), a hard contractual constraint (the anchor-account price-lock), no serious ambiguity
about whether something real happened. This is not a corpus of bad calls that examination would have
caught. It is a corpus where a real, specific, non-hypothetical alternative — *"is the objective
recovering margin, or reducing base-oil exposure?"*, exactly §4's worked example — sat in every
situation block's own stated root cause and was never once raised for the KPI owner to accept or
reject. One arm (C1) came closest: an *option* proposed de-risking anchor-account concentration, but
nested as a tactic serving the same unexamined objective, not offered as an alternate frame.

**This sharpens the falsifier in §9, not just satisfies it.** §9's stated falsifier was "examined and
confirmed unchanged in nearly every run." What actually happened is thinner than that — not
*confirmed* unchanged, *never asked*. That is the stronger case for building the gate, not the weaker
one: there is a real question sitting unexamined, not a rubber stamp waiting to happen.

**Caution for whoever builds this next, surfaced in the same conversation that ran the adjudication:**
none of "requested the DA," "read the rendered `ScqaBlock`," "completed the (optional) refinement
interview," or "selected a council" can be read as evidence of examination, and this was checked
empirically, not just argued. The refinement-interview arm ran a genuine 9-turn conversation and
captured two real constraints — and still failed the frame link identically to the arm that skipped
refinement outright. Council selection happens *after* the frame is already fixed (DA generates SCQA
before SF ever sees a persona/council choice), so it cannot carry information about the frame by
construction. This is why §8 decision 6 (a confirmed "frame is right" answer must be *recorded*) is
load-bearing rather than a nice-to-have: every available behavioral proxy for examination was tested
against this corpus and produced zero variance. An inferred signal cannot substitute for an explicit
one here — the two are observationally identical (a principal who skimmed and one who read carefully
both simply proceed), so no amount of instrumenting the surrounding flow can recover the distinction.
Only asking directly can.

**Second prerequisite — a second problem shape — still has not moved.** All 13 corpus runs and all 4
live runs this session are the same recurring situation: one dominant segment, one confirmed external
mechanism, no healthy segment anywhere in the dataset. That last detail is not incidental — see the
VA finding immediately below, which was found by checking it directly rather than assumed.

**Side finding, worth its own paragraph because it wasn't anticipated: this situation shape may not
have a control group for VA either.** Checked directly against a live captured DA payload for this
exact recurring situation: `kt_is_is_not.where_is_not` and `.benchmark_segments` both empty (count 0).
`workflows.py` derives VA's `control_group_segments` straight from that field
(`kt.get("benchmark_segments")`, filtered to `benchmark_type == "control_group"`) — independently of
DA's own `has_control_group` routing signal, which is never read outside `_route_refinement_topics`
and was confirmed to have no other consumer. So on this recurring situation, any solution VA evaluates
would register with `control_group_segments=None`. **Checked how VA handles that, and it degrades
correctly rather than overclaiming** — `evaluate_solution_impact` (`a9_value_assurance_agent.py`)
counts `signals_present` across control group / market recovery / seasonal estimate, and with zero
present, confidence explicitly drops to LOW with the rationale stated in the record itself: *"No
control group or external estimates provided; attributable impact equals total KPI change."* This is
not a bug in VA — it is VA correctly reporting a limitation of the data it was handed. But it does
mean: (a) nothing approved against this exact situation could ever produce a HIGH-confidence DiD
verdict, and (b) the field-test plan discussed for lens-vs-MBB ("let VA's real outcome decide") needs
a situation with a genuine control group to mean anything — a gap in addition to the missing
council-provenance field already flagged for that plan. Whether this is a structural property of this
one situation or a broader pattern in the KPI/registry data is unchecked — worth resolving alongside
the second-problem-shape search, since a shape search that also turns up a genuine control group would
close two open items at once.

**Where this leaves the build:** first prerequisite (adjudicate before building) — done, and the
result argues FOR building the gate. Second prerequisite (a second problem shape) — still open, and is
now doing double duty: it also determines whether the VA control-group gap is a one-situation artifact
or a real limitation on how the eventual field signal can work.

---

## 11. Second problem shape scored (2026-08-17) — both prerequisites now closed

Targeted deliberately, not incidentally: a fresh SA scan surfaced 11 cards, most plausibly downstream
of the same base-oil shock (EBITDA, Gross Profit, Premium Product Mix % all likely reflect the same
root cause via different P&L rollups). **Net Revenue** — *"$20.2M (-16.2%) below budget"* — was chosen
specifically because it runs a different comparator mechanism (`plan_variance`/`budget`, not
`threshold_breach`/prior-period) with an unknown concentration pattern, since Revenue and Margin are
driven by different segment structures. Council left at the MBB default deliberately, to isolate
problem shape as the one variable under test rather than conflate it with the lens_council question.

**Confirmed genuinely different on two independent axes**, computed directly from `kt_is_is_not` (the
same method used for the shape-1 VA finding, since `concentration`/`has_control_group` are DA-internal
routing signals never persisted into the response):

| | shape 1 (gross margin) | shape 2 (net revenue) |
|---|---|---|
| alert_type / comparator | `threshold_breach` / prior-period | `plan_variance` / **budget** |
| segments analyzed (`where_is`) | single digits | **60** |
| dominance ratio (top two deltas) | one dominant driver | **1.76** — below DA's own 2.0 "concentrated" threshold |
| concentration | concentrated | **distributed** |
| `where_is_not` (control group) | 0 | **0** |

**DQ result: same cap, for the same underlying reason.** L1 fails on adjudication (not just the raw
screen — the QUESTION field asks *how to sequence* the response, never *whether* recovering Net
Revenue is the right objective). L2–L6 all pass. 5/6, capped by frame — identical shape to every prior
run this session.

**What's genuinely different: the frame's own reasoning quality, not whether the objective got
examined.** This run's `COMPLICATION` explicitly separates real problems from budget artifacts —
*"the five largest absolute-dollar shortfalls... are adverse only versus budget, not versus prior
year, indicating likely budget-setting or timing artifacts rather than true deterioration"* — versus
segments *"confirmed... adverse on BOTH bases."* Its `key_assumptions` state their own uncertainty
plainly (*"inferred... but not yet segment-verified"*) rather than asserting the root cause as settled
fact, which every shape-1 run did. That is real epistemic work, on a different axis than L1 entirely —
sharper reasoning *inside* an unexamined objective, not examination of the objective itself. This
shape's own analogous unexamined alternative: *is the objective recovering the revenue number, or
fixing a budget-setting process that appears to be generating part of the "shortfall" itself?* Never
asked, structurally the same gap as shape 1's base-oil-exposure question, just a different specific
candidate.

**The VA control-group finding generalizes — 2 for 2, not 1.** `where_is_not` empty on both a
concentrated shape and a distributed one. Shifts the likely explanation: less "this one recurring
situation happens to lack a comparison group," more a broader property of this dataset or a gap in how
`benchmark_segments` gets computed generally. Still n=2 — worth its own dedicated check — but no longer
a single-shape curiosity, and the shape search did NOT turn up a genuine control group as hoped.

**Both build prerequisites are now closed.** Adjudicate before building (§10) — done, argues for the
gate. Score a second shape before concluding "one right frame" — done: the framing gap holds across a
concentrated/threshold-breach/prior-period shape and a distributed/plan-variance/budget shape alike.
The gate can now be built on a basis broader than one recurring situation. The VA control-group
question is a separate, still-open thread — worth its own investigation (structural data fact vs.
pipeline gap), not a blocker on the framing build.

---

## 12. VA control-group investigation, closed (2026-08-18) — mode-specific, not dataset-wide

Checked directly rather than left as an open thread. Traced `_benchmark_source`'s selection logic in
`a9_deep_analysis_agent.py` (~line 2340): the field VA actually reads (`benchmark_segments`) is derived
differently per DA's effective analysis mode — `problem` mode sources it from `where_is_not`;
`opportunity` mode from `where_is`; `mixed` mode from `where_is` items tagged
`segment_type="opportunity"`, specifically *because* mixed mode deliberately empties `where_is_not`
(merges it into `where_is`) earlier in the same method. **`where_is_not` is not VA's signal — it is a
`problem`-mode-only intermediate that the §10/§11 findings mistook for a general one.**

**Verified live:** dispatched DA directly (API only, no SF needed) on `ecommerce_revenue` — an
`opportunity`-adjacent card unrelated to the base-oil shock, resolving to `analysis_mode="mixed"`.
Result: `where_is_not=0` (as expected for mixed mode — confirms the mechanism, not a new gap) but
`benchmark_segments=17`, of which **10 are genuinely `control_group`-tagged**, with real segment names
and deltas (`National Auto Parts Chain A`, `Chemicals & Additives`, `Synthetic Blend Engine Oil`...).
This is exactly what `workflows.py` filters into VA's `control_group_segments` at registration.

**Corrected conclusion.** §10/§11's "2/2 shapes lack a control group, shifting toward a broader dataset
property" was premature — both tested shapes happened to be `problem` mode, and the absence is a
property of that mode's data model (a genuine uniform-cost-shock read on those two specific KPIs), not
the client's data generally. The VA field-test plan's control-group gap is real **only** for
`problem`-mode runs on KPIs downstream of the shared base-oil shock (gross margin, net revenue, and
presumably EBITDA/gross profit/operating income/premium mix — the other cards likely riding the same
mechanism). Any `opportunity`- or `mixed`-mode KPI, verified against `ecommerce_revenue`, has real
control-group segments available. **No code change indicated** — the mechanism is correct and
mode-appropriate; the gap was in reading `where_is_not` as VA's signal when `benchmark_segments` always
was.

**Practical takeaway for the field-test plan:** point it at an opportunity/mixed-mode situation, not a
problem-mode one downstream of the cost shock, and VA's DiD attribution has a genuine counterfactual to
work with.
