# Persona Council Experiments — Record, Method, and Test Design

**Status:** Exploration complete, no build authorised. Seven arms run 2026-08-12, ~$1.20 total.
**Harness:** `tools/ab_harness/b3_question_divergence.py`, `tools/ab_harness/b3_discovery_round.py`
**Origin:** Phase 15 Stage I B-3 gate — see `DEVELOPMENT_PLAN.md` → Phase 15 → Stage I.

---

## 1. What was under test

Stage I's premise: three MBB personas produce "one analysis in three costumes" because every point at
which they could diverge is removed before they are invoked. The proposed fix (B-4) was a shared
question queue with per-persona constraint sets. The gate asked the cheap prior question:

> **Would the personas actually ask different questions?**

If not, a shared queue of three gets one questioner's worth of enquiry in three voices, and the
expensive build is settled without doing it.

---

## 2. The record

Every arm ran against one fixed Deep Analysis result (lubricants `gross_margin_pct`, YTD, 5 product
lines declining 6–7pp). Effort held at `medium` throughout. No LLM judge anywhere.

| # | roster | model | prompt | n | tags/persona | topic J | null | vs null | lexical J |
|---|---|---|---|---|---|---|---|---|---|
| 1 | MBB | sonnet-5 | registry | 3 | 6 of 9 | 0.667 | 0.512 | **above 95th** | 0.20 |
| 2 | MBB | fable-5 | registry | 3 | 6 of 9 | **0.810** | 0.512 | **far above** | 0.26 |
| 3 | diverse council | sonnet-5 | registry | 4 | 6 of 9 | 0.604 | 0.512 | at 95th edge | 0.16 |
| 4 | famous four | sonnet-5 | authored | 4 | 6 of 9 | 0.540 | 0.512 | **at null** | 0.13 |
| 5 | 20 methods | sonnet-5 | authored | 20 | 2 of 9 | 0.405 | 0.157 | far above | 0.080 |
| 6 | 20 methods | fable-5 | authored | 20 | 2 of 9 | 0.311 | 0.157 | far above | 0.058 |
| 7 | 20 methods | fable-5 | **name only** | 20 | 2 of 9 | **0.261** | 0.157 | above | 0.085 |

Nulls are simulated random taggers at the same picks-from-vocabulary shape (fixed seed, 8–20k trials).

### Clean single-variable comparisons

Only these three change exactly one thing and are therefore interpretable:

| comparison | variable | result |
|---|---|---|
| arm 1 → 2 | model | 0.667 → 0.810 — **more convergent** |
| arm 5 → 6 | model | 0.405 → 0.311 — **more divergent** |
| arm 6 → 7 | prompt richness | 0.311 → 0.261 — **more divergent** |

Arms 1/3/4/5 differ in several variables at once (roster, size, prompt source, tags per persona) and
support only ordinal reading, not attribution.

---

## 3. What we now believe

**High confidence:**

1. **Topic selection converges under every configuration tested.** All seven arms sit above their
   null; only arm 4 reached it. The problem constrains what is worth asking about a diagnosed margin
   decline — there is a finite set of useful questions, and every council finds most of it. *This is a
   finding, not an instrument failure.*
2. **Content within topics differentiates with persona differentiation.** Lexical Jaccard orders
   monotonically with roster differentiation (0.26 → 0.20 → 0.16 → 0.13 → 0.080 → 0.058), and the
   unique-term lists are sharply method-specific.
3. **The convergence is a property of the roster, not the pipeline.** A more capable model pushes
   weakly-differentiated personas *together* (MBB 0.667 → 0.810, McKinsey and BCG identical on both
   models) and genuinely-differentiated personas *apart* (0.405 → 0.311). One model change, two
   opposite directions, decided by who was in the council.
4. **The differentiation is not authored.** Stripping the profiles entirely and prompting with the
   name alone *increased* divergence (0.311 → 0.261), and produced concepts absent from any profile
   text: Ohno → *gemba*; Levitt → *electric*, *drivetrains*, *commoditization*; Drucker →
   *abandonment*; Sloan → *divisional*, *absorption*; Munger → *invert*. It lives in the models'
   knowledge of these people.

**Consequential observation:** two of twenty minds (Carnegie, Deming) independently proposed that the
margin decline might be an **accounting artefact** — under-absorption from volume shortfall, or a
costing-methodology change — rather than anything commercial. *Zero of the six consulting personas
did.* The Aug 9 incident in this codebase was exactly that failure: COGS pinned to one customer
produced a −457% margin that SA, DA, three MBB personas and a briefing all treated as a business
problem.

**Not established:**

- Any of it at n > 1. Every arm is a single draw.
- Any of it on a second problem, KPI, client, or `cell_key()`.
- **That divergence is desirable.** See §5.

---

## 4. Methodology lessons

The transferable part. Each was learned by getting it wrong first.

| Lesson | What it cost |
|---|---|
| **Compute the null before setting a threshold.** A flat "Jaccard ≤ 0.70 ⇒ diverge" rule sat *below* the 0.512 random baseline — it would have called chance divergence, and did, twice. | Two wrong verdicts, reported before being caught. |
| **One variable per run.** Held throughout, and it is the only reason arms 1→2 and 5→6 can be read against each other at all. | — (held; the discipline is what made the result interpretable) |
| **State the prediction before running.** The Fable arm was informative *because* a direction was predicted and the result went the other way, killing one hypothesis. Run without a prediction, it would have been a number. | — |
| **A coarse instrument hides real effects.** Topic-tag Jaccard could not distinguish four people asking about blending tanks, volume retention, target mechanisms and approval authority — all tag `hypothesis_validation`. Lexical Jaccard, which was dismissed as "measuring phrasing," tracked the true ordering. | Nearly closed the exploration on the wrong reading. |
| **Test for authored circularity by stripping the authoring.** Profiles written by the person analysing the results make "differentiation found" partly "differentiation supplied." | — (caught before it mattered) |
| **A stacked test proves nothing.** The shared-queue design ("here is what has been asked, add what is missing") would have produced a beautifully diverse queue and measured instruction-following, not perspective. | Avoided. |
| **Verify the expensive path cheaply first.** One-call probes for API credit and for Fable availability (model access, 30-day retention, fallbacks form) before committing 20-call runs. | — |
| **Optimising a proxy is not optimising the objective.** Everything here measures divergence. Divergence was never the goal. | Unresolved — see §5. |

---

## 5. Why an outcome measure must precede optimisation

The obvious next move is a factorial sweep to find the combination that maximises divergence. **That
would be optimising the wrong thing.**

Divergence is a proxy chosen because it was measurable, not because it is the objective. The objective
is constraints that change the recommendation. And the dev plan's own load-bearing risk runs the
*other* way:

> A persona that never asks about a real constraint does not produce a differently-valid answer — it
> produces a **wrong** one, and its option scores *better* precisely because it never learned what
> would kill it.

A council optimised for divergence could be a council optimised for mutual ignorance. Until "better"
has a referent, every additional arm refines a number nobody should act on.

### 🏁 Phase 0 RUN (2026-08-12) — no council reliably catches it. Roster is not the fix.

Scored all seven saved arms with `tools/ab_harness/b3_artefact_score.py`. No new API calls.
**Question: does any persona challenge HOW COST WAS ASSIGNED before diagnosing a commercial cause?**

| arm | screened by terms | **genuine** | of | rate |
|---|---|---|---|---|
| MBB · sonnet-5 | 1 | **0** | 3 | 0% |
| MBB · fable-5 | 0 | **0** | 3 | 0% |
| diverse council · sonnet-5 | 1 | **0** | 4 | 0% |
| famous four · sonnet-5 | 0 | **0** | 4 | 0% |
| 20 methods · sonnet-5 | 4 | **2** | 20 | 10% |
| 20 methods · fable-5 | 3 | **1** | 20 | 5% |
| 20 methods · fable-5 · name only | 5 | **1** | 20 | 5% |

**Consulting and famous councils: 0 of 14 persona-slots. Method councils: 4 of 60 (~7%).**

The genuine hits, in full:

- **Carnegie** — *"Were any of these five lines running below their standard cost absorption rate due to volume falling short of the base plant output used to set overhead allocation this year?"*
- **Deming** — *"a supplier cost change, **a costing methodology shift**, or a pricing policy — not five independent product problems."*
- **Ohno** — *"Before we accept these margin numbers as a diagnosis… what did they see change in the actual work — materials, changeovers, rework, scrap — at that moment, **not in the ledger**?"*
- **Deming (name-only)** — *"what changed in the system itself — a supplier, a pricing policy, a sales incentive, a spec, **a cost allocation method**?"*

**What this settles.** The roster thesis is directionally supported — 0% versus ~7% is a real difference, and it is the same two or three methods (cost accounting, statistical process control, shop-floor diagnosis) doing all the work. But **~7% is not a solution to a correctness problem.** Selecting 4–6 from a 20-library gives roughly a coin-flip chance of including Carnegie or Deming. A defect that silently produced a −457% margin and reached a briefing cannot be defended by a persona lottery.

**Therefore: do not solve this with personas.** The artefact question must be asked *deterministically, every run*. The check already exists — `scripts/check_slice_validity.py`, run by hand and wired to nothing — and the governed version is designed in `kpi_semantic_contract.md` §4 (sliceability). **Wiring that check is worth more than any council change**, and it is the recommendation Phase 0 produces.

**Instrument caveat, and a second methodology lesson.** The term screen produced 14 candidates of which **4 survived adjudication — a 71% false-positive rate.** The dominant failure is `absorb` in the commercial sense (*"we absorbed the cost increase"* ≠ absorption costing); second is `allocation` meaning capital or resource allocation. A keyword screen for a semantic property is a **screen, not a verdict** — which is why the adjudication is recorded as data next to it rather than folded into a cleverer regex.

And the first version of that adjudication silently failed: an off-by-one in the lookup key turned every verdict into `unreviewed`, which then displayed as **0 genuine across all seven arms**. A not-checked masquerading as a fail — the exact conflation `src/analysis` exists to prevent. It was caught only because a uniform zero looked wrong.

**Limitation.** All arms saw the **post-fix (clean)** data, so this measures whether the method asks the artefact question *as standard practice* — arguably the property you want, since the check must fire before anyone suspects a problem. It does not measure whether a council would react to visibly absurd numbers (−457% / exactly 100.00%). That is the v1b test: re-run against the frozen pre-fix profile.

### Outcome measure v1 — artefact detection (cheap, objective, pre-existing)

`tests/fixtures/lubricants_uneven_granularity_profile.json` freezes the **pre-fix** BigQuery profile
from the Aug 9 slice-validity incident — COGS allocated to one customer while revenue spanned twenty,
producing −457.71% for one account and exactly 100.00% for nineteen. The correct diagnostic response
is known, and the failure is one this project actually suffered.

**Score:** does any persona in the council ask a question that would surface the artefact before
diagnosing a commercial cause? Binary per persona, count per council. No LLM judge — the question is
either about allocation/absorption/costing method or it is not, and that can be keyed on a small
term list plus a read.

This converts "did the council diverge" into "did the council catch the thing that fooled the last
one," which is worth optimising.

### Outcome measure v2 — held-out constraint recall

A curated ground-truth list of what actually bounds this problem (contract terms from the assumption
register, the anchor-account price lock, base-oil index formulas, capacity). Score each council on
recall. More work, more general, and it maps directly onto B-2's `constraint_items`.

---

## 6. The variable space

| # | variable | levels tested | levels available |
|---|---|---|---|
| V1 | roster composition | consulting firms · famous operators · 20 methods | + sourced-from-writing personas |
| V2 | council size | 3 · 4 · 20 | 6 · 8 · 12 |
| V3 | model | sonnet-5 · fable-5 | opus-5 · haiku-4-5 |
| V4 | effort | medium only | low · high · xhigh · max |
| V5 | prompt richness | authored profile · name only | sourced excerpts |
| V6 | utterances per persona | 6 · 1+1 | 1 · 3 |
| V7 | visibility | blind only | shared queue (stacked — see §4) |
| V8 | evidence base | shared DA only | per-persona cuts (**rejected** — weakens moderator G3) |
| V9 | problem shape | one `cell_key()` | concentrated · distributed · no-control · compound |
| V10 | replicates | n=1 | n≥5 |

**V4 (effort) is the most obvious untested lever** and the cheapest to sweep. **V10 (n) is not
optional** — no current number carries an error bar.

---

## 7. Proposed sequence

A full factorial is 4 × 4 × 4 × 3 × 2 × 4 ≈ 1,500 cells. Screening first.

| Phase | What | Status |
|---|---|---|
| **0** | Outcome measure v1, scored retrospectively on the saved payloads | ✅ **RUN — see §5. Stop rule fired.** |
| **1** | Replicate baseline at **n=5** | ⏸ Deferred |
| **2** | One-at-a-time screening across V2–V6, ~25 runs | ⏸ Deferred |
| **3** | Sweep the variables that screened in, ≥2 problem shapes | ⏸ Deferred |
| **4** | Re-ask B-4 with the winning configuration | ⏸ Deferred |

**The stop rule fired.** It read: *if phase 0 shows no council catches the artefact, roster
composition is not the lever and the whole line closes.* The literal result is not quite zero —
method councils reach ~7% against consulting councils' 0% — but ~7% does not defend a correctness
property, and phases 1–3 would be spending to optimise a lever that tops out well below useful.

**Revised priority.** Wire the deterministic slice-validity check (`kpi_semantic_contract.md` §4)
ahead of any further council work. Phases 1–4 remain a sound design and should be resumed only if
persona composition is pursued for a *different* objective than correctness — e.g. option diversity
in Solution Finder, where the failure mode is blandness rather than a wrong number.

This is the intended outcome of running phase 0 first: **~$0 of new spend closed a line of work that
phases 1–3 would have spent real money refining.**

---

## 7b. Evidence-scope experiment (2026-08-14) — six real Solution Finder runs

A separate question from roster composition, run on the same fixed lubricants `gross_margin_pct` DA
result. Solution Finder reasons over the *dimensional decomposition* of one KPI — which answers WHERE
a KPI moved, never WHY. Two channels were supposed to reach the cause, and until 2026-08-14 neither
arrived: causal context was fetched single-hop (so `base_oil_cost → cogs → gross_margin_pct` was
invisible), and `market_signals` was never read by SF at all. Both were fixed. **Does the fix change
what the options act on?**

Measure: **cause vs symptom** — not divergence. Does the option act on the input cost (indexation,
hedging, sourcing, reformulation) or on the price of the affected lines (repricing, mix, negotiation)?

| arm | hops | edges (direct/indirect) | MA signals | refinement | options |
|---|---|---|---|---|---|
| A | 1 | 3 / 0 | no | yes | 3 |
| B | 2 | 3 / 3 | no | yes | 3 |
| C | 2 | 3 / 3 | **4** | yes | 3 |
| A0 | 1 | 3 / 0 | no | **no** | 3 |
| B0 | 2 | 3 / 3 | no | **no** | 3 |
| A0C | 1 | 3 / 0 | no | no, **+`market_conflict` stripped** | 3 |

Every arm confirmed from its own `causal_context` audit event, never from the shell env. No
`heuristic_stub_fallback` in any arm. ~50k tokens/arm, 230–265s each.

### Result: no measurable effect of traversal depth. One real effect from market signals.

**Cause-vs-symptom did not discriminate at all** — the term screen returned 3-of-3 "cause" in every
arm, and reading the options confirms it: *all six arms already act on the cause*, proposing indexed
pricing or surcharge mechanisms tied to base oil. Across 5 arms and 15 options, procurement-side
actions (hedging, forward contracting, sourcing) appeared in 1/6 of `hops=1` options and 2/9 of
`hops=2` options. That is noise.

**Why — and this is the finding.** It took three attempts to build a control, because base oil
reaches the model through four channels, and I closed them one at a time instead of enumerating them
first:

| # | channel | closed in |
|---|---|---|
| 1 | `refinement_result.validated_hypotheses` — *"Base oil costs jumped 18% in Q2 and we could not pass it through"*: the entire causal story, volunteered by the CFO | A0/B0 |
| 2 | `deep_analysis_output.market_signals` — 4 signals naming base oil, Group II/III, crude | A0/B0 |
| 3 | `deep_analysis_output.market_conflict.summary` — restates the signals in prose under a **second key**, so popping `market_signals` alone leaves the cause in the payload | A0C |
| 4 | **the mechanism prose on the *direct* edge** — `gross_margin_pct → cogs` reads *"Base oil (largest COGS input) price volatility passes through to COGS with a lag; margin absorbs the difference before pricing catches up"* | **cannot be closed** |

Channel 4 is the answer. **The one-hop edge already narrates what the two-hop node would contribute.**
`base_oil_cost → cogs` adds precision (~50–60% of COGS, one-month inventory-buffered lag) but not the
concept. A0C — no refinement, no signals, no market conflict, one hop — still produced eight mentions
of base oil, because a direct edge told it.

> **Graph depth and mechanism prose are substitutes.** Traversal buys most where near edges are
> sparse. Three of the six lubricants edges have `mechanism: null` (all `template` provenance); on a
> KPI whose neighbourhood is mostly those, `max_hops=2` would carry far more weight than it did here.
> This experiment picked the KPI where traversal had the *least* to add.

### The one checkable quality difference: market signals fixed a wrong benchmark

| arm | index proposed for the base-oil surcharge |
|---|---|
| A | *"a transparent base oil benchmark (e.g., **WTI** or industry index)"* |
| B | *"base-oil-indexed pricing mechanism"* (unspecified) |
| **C** | *"indexed to **Group I/II spot pricing, 30-day lookback**"* |

WTI is *crude*, not base oil. Indexing a base-oil surcharge to WTI systematically mis-recovers,
because the crude-to-base-oil spread moves independently — which is exactly the exposure being
hedged. Group I/II is the correct grade, and it traces to the signal *"Group II/III base oil supply
tightness."* One variable, one checkable correction, in the detail that decides whether the contract
clause works.

**The graph encodes the mechanism; the signals encode the current fact.** The graph knows base oil
drives COGS with a lag. It does not know *which grade is tight this quarter* — and that is what the
clause has to name. This is the clearest argument yet for MA routing, and it is a groundedness
argument, not a scope one: A0C asserted *"citing documented base oil cost inflation"* when nothing in
its context documented any inflation. The mechanism was grounded; the event was not, and the two read
identically.

### Additional methodology lessons

| Lesson | What it cost |
|---|---|
| **Enumerate every channel carrying the variable before running, not after each failure.** Three successive "clean" controls each leaked through a channel I had not thought to list. | 6 runs where 2 would have done. |
| **A second key can restate the first.** `market_conflict` prose duplicated `market_signals` content, so stripping one key left the variable in the payload. Grep the *rendered payload* for the concept, not for the field name. | One wholly confounded pair (A0/B0). |
| **Do not edit files under the reload watcher while a run is in flight.** Editing `scope_arm.py` mid-run hot-reloaded the backend and destroyed in-memory workflow state — two runs lost to `404` on the status endpoint. | 2 discarded runs. |
| **The screen was flat and the finding was real.** A 3/3 term-screen tie invited "no difference"; the difference (WTI vs Group I/II) was inside one clause of one option, invisible to any count. | — (caught by reading) |

### What this authorises

- **Keep both changes.** Traversal is unproven *here* but sound and cheap; the null is explained by
  edge-authoring, not by the feature. Market-signal routing is supported by a concrete correction.
- **Mechanism prose is load-bearing.** A `template` edge with `mechanism: null` contributes almost
  nothing. Populating mechanism text on near edges may beat increasing `max_hops`.
- **Retest traversal on a KPI with sparse near edges** — the condition under which it should pay.
  Not urgent, and not on `gross_margin_pct`.
- **Do not read this as "the causal graph does not help."** It was never isolated. It was always
  present at one hop, and it is where the base-oil concept came from in every arm.

---

## 7c. Two false zeros found while re-baselining, then the frame-challenge test (2026-08-14/15)

Before any further arm could be trusted, two context defects needed fixing — both would have
confounded a task-statement comparison, and both were **false zeros**: an instrument reporting "0"
because it hadn't looked yet, not because the true value was zero.

**Fix 1 — `_build_kt_summary` unit rendering.** The WHERE-IS block hardcoded `$` and `:,.0f` onto
every driver delta regardless of the KPI's actual unit:

```
- Synthetic Blend Engine Oil: $-7 (0.0% of variance)
- Conventional Engine Oil: $-7 (0.0% of variance)
```

This is the context every Stage 1 persona reads. Three faults in one line: (a) a percentage KPI
rendered as currency — `gross_margin_pct` fell 7.14 **percentage points**, not $7; (b) `:,.0f`
collapsed -7.14 and -6.61 onto the identical `$-7`, destroying the ranking the block exists to
convey; (c) `percent_of_total` is not computed on the flat dimension path — the key is **absent**
from every entry — so `.get(key, 0)` printed `(0.0% of variance)` against every driver, asserting
that the top driver explains none of the problem. Fixed: unit resolved from the KPI registry via the
existing `_lookup_kpi_scoped` helper, `pp`-suffixed with two-decimal precision, and the variance
clause omitted rather than asserted-false when the field is genuinely absent (kept when a real 0.0 is
measured). All 27 prior evidence-scope options were generated over the broken string.

**Fix 2 — the `causal_context` audit read `_cg_constraints` before it was fetched.** The variable was
initialised to `[]`, the audit-log append ran, *then* the register was queried — so `constraints: 0`
appeared in every arm regardless of what the register held. It was not a data gap: the lubricants
register holds one active constraint scoped to `gross_margin_pct` (the anchor-account price-lock),
and it **was** reaching Stage 1 correctly the whole time via a separate code path — only the audit
instrument was blind. Fixed by moving the append after the fetch. Both false zeros are now pinned by
regression tests (`test_da_kt_summary_units.py`, the ordering assertion in
`test_sf_constraint_exposure.py`).

**Re-baseline (arm C1)**, identical config to arm C, run after both fixes: `constraints: 1` now
appears correctly. Options: still 3/3 `indexation`-cluster.

### Step 1 — does permission to challenge the frame change anything?

New flag `stage1_allow_frame_challenge` (`agent_config_models.py`, env `SF_STAGE1_ALLOW_FRAME_CHALLENGE`,
default `False`). The production task text *requires* every option to name the "primary driver of
THIS KPI situation" with `recovery_range` "proportional to the observed variance" — a wording that
cannot express a portfolio or exit move. The flag adds a fifth, explicitly optional task item
permitting a portfolio-level response when "genuinely warranted by the evidence." It does not remove
items 1–4 and does not require anything; an option that still recovers the KPI remains fully valid.
The off-branch is verified byte-identical to the pre-existing text
(`test_default_task_text_is_byte_identical_to_baseline`).

Two independent runs (arms D1, D2), same config as C1, flag on:

| arm | options | lever families |
|---|---|---|
| C1 (control) | 3 | indexation × 3 |
| D1 | 3 | indexation × 2, pricing_corridor × 1 |
| D2 | 3 | pricing_corridor × 3 |

**Result: a genuine null, at n=2, not a confounded one.** Zero of six treatment options exercised the
permission — not "chose a worse structural option," simply never touched it. Combined with the 21
options in the original 7-arm roster record, **0 of 27 real-run options across this entire
investigation have ever proposed a portfolio, exit, or category-level response**, including the six
that were explicitly invited to.

🔴 **CORRECTION (2026-08-15) — the `0 of 27` is wrong as stated.** Retrospective DQ scoring of all 11
saved arms (`docs/architecture/decision_quality_rubric.md` §8) found that **D1 opt_2, "Immediate SKU
Rationalization + Staged Q3 Contract Reset", proposes discontinuing and delisting SKUs** — acting on
portfolio composition rather than on the price or cost of the existing portfolio. D1 is one of the six
treatment options counted as `0/6` here. Arm E2 opt_3 ("SKU exit/de-emphasis", volume reallocated
elsewhere) is a second instance. The null above was adjudicated at *category/portfolio-exit*
granularity and SKU rationalisation was not counted — a defensible line that was **never written
down**, so the headline number is doing work the adjudication does not support. The direction survives
(2 of 33 is still near the floor) but **do not quote `0 of 27` again without a stated criterion.**

With that correction applied, this *sharpens* the original roster hypothesis rather than undermining it. Before this test, "the
council never proposes structural options" was consistent with two different explanations: the task
wording forecloses it, or MBB-style reasoning doesn't reach for it regardless of what's asked. This
test isolated wording as the variable and found no effect — which is evidence for the second
explanation, not the first. The single unclassified-by-title but closest-to-structural option found
anywhere in the record remains arm C1's sibling from the earlier baseline: *"Strategic Channel
Portfolio Shift: De-Risk Anchor Concentration"* — and even that pairs the diversification with an
indexed price increase and classifies as `indexation` on its description fallback (no lever pattern
matches its title at all). It is a channel-mix move, not a portfolio-exit one.

**Caveat, stated plainly:** n=2 is thin for a stochastic generator, and the schema has no way to
record "the model considered the alternative frame and declined it" versus "never engaged with item
5 at all" — those read identically from the outside. A third run would cost about $0.20 and is not
ruled out, but the practical signal (0/6, explicit invitation, twice) is strong enough to proceed
rather than spend further here.

### Authorises

- **Step 1 is closed.** Task-statement permission alone does not move the option space. Do not spend
  further on wording variants.
- **Proceed to step 2 (lens swap)** — Commercial / Operational / Structural roster, replacing
  McKinsey/BCG/Bain, compared against arm C1 using unchanged task text
  (`stage1_allow_frame_challenge=False`, the config default) so the lens swap is the only variable
  against a now-clean baseline.
- Flip `SF_STAGE1_ALLOW_FRAME_CHALLENGE` back to unset/`false` before running step 2 — it is a
  standing env line in `.env` and must not silently ride along as a second variable.

### Step 2 — lens swap (Commercial / Operational / Structural)

New method-defined roster in `consulting_personas_registry.yaml` (`commercial`, `operational`,
`structural`), replacing McKinsey/BCG/Bain via `preferences.consulting_personas` — no code path
change, since `req_personas` already resolves any id in the YAML and bypasses the MBB default
entirely. Motivated by a real, live finding while building this: `to_prompt_context()` renders
`## Consulting Advisor: McKinsey & Company` — the actual protected firm name and mark — directly into
the LLM prompt today, for all eight personas in the existing registry. The lens roster is
method-branded specifically to remove that exposure, independent of what the experiment below finds.

Two independent runs (E1, E2), config identical to C1 (task text unchanged, flag off), only the roster
differs. `stage1_calls_complete` confirms `["commercial","operational","structural"]` ran with zero
drops in both.

**Still 0/6 portfolio or category-participation options — the null holds even with a persona
explicitly built and briefed for that lens.** The Structural persona's `typical_recommendations`
name "portfolio reallocation," "test of whether continued participation is worth defending" almost
verbatim, and it still did not surface either. Its methodology (question the frame, name what would
need to be true) *did* transfer — but applied inward, to an existing option's assumption ("this rests
on an unconfirmed premium-mix-to-margin relationship... first validate from actual product-level
margin data"), not outward to the category-participation question it was written to reach for. That
is a real behavioral signature, and it is not the one predicted.

**One directional, small-n signal:** input-cost hedging appeared as a **title-level thesis** (not a
buried clause) in 2 of 6 lens options, vs 2 of 27 MBB options — checked by regex over titles only, not
impression. 33% vs 7%, but 2 vs 2 in absolute count; this is a direction to retest with a larger n, not
a finding to act on. The Operational lens's "skeptical of the measured number" brief plausibly
explains it, but the counterfactual (does that phrase alone move it, independent of the rest of the
persona) hasn't been isolated.

**One near-miss ruled out before being reported.** `blind_spots`/`unresolved_tensions` counts looked
qualitatively richer in E1 on first read — checked against C1 (`4/3` vs `5/3`) and E2 (`4/3`) before
writing anything, and they're statistically indistinguishable. That self-critique behaviour is a
standing property of the synthesis step, not a lens effect. Recorded here specifically so it isn't
re-discovered and mis-attributed later.

### What steps 1+2 together establish

Two independent variables — task-statement permission, and roster composition including a persona
purpose-built for exactly this gap — both tested at n=2, neither produced a single portfolio-level
option across the whole 33-option record. That is a much stronger statement than either result alone:
**it is not the wording, and it is not (solely) that the wrong personas were asking.** The candidate
explanations still standing: the shared evidence base (DA output, refinement, market signals) may not
contain the ingredients a portfolio call would need to be well-grounded rather than speculative — SF
sees a KPI, not a category; or the recovery_range/quantification machinery downstream of Stage 1
structurally pulls the synthesis back toward a recoverable number regardless of what Stage 1 proposed.
Neither is tested. This is now the natural next question if the portfolio gap is worth closing, rather
than a fourth roster or wording variant.

### Authorises (step 2)

- **Keep the lens roster** as an available `council_preset` (`lens_council`) — it closes the live
  trademark exposure, is a data-only change, and is at least as differentiated as MBB by the one clean
  signal available (hedge-in-title rate) while costing nothing extra to run.
- **Do not present it as solving the portfolio-blindness problem** — it doesn't, at n=2.
- **Do not spend on a step-3 wording variant or a fourth roster.** Two clean single-variable tests
  agreeing is the signal to change *what kind* of question is being asked, not to keep varying who's
  asking it.

---

## 8. Known gaps in the current record

- **No null for lexical Jaccard.** The topic-tag null is simulated; the lexical one is not, so the
  lexical ordering is relative-only and its absolute values mean nothing.
- **The saturation curve measures vocabulary, not ideas.** It cannot distinguish a new concept from a
  new synonym, and did not saturate by persona 20 in any arm. It should not be read as "20 is not
  enough."
- **The unique-contribution reading is qualitative**, performed by the same person who wrote the
  profiles and designed the instrument.
- **Topic tags are self-assigned by the model under test.** Structured output, not adjudication — but
  a persona that mis-tags its own question distorts the topic measure.
- **Arms 1/3/4/5 vary several things at once** and cannot support attribution.
- **`_build_kt_summary` formats percentage-point deltas as dollars** (`$-7 (0.0% of variance)`) in the
  context every persona received. Identical across arms so it did not bias any comparison, but it
  misinforms production refinement too — see Known Issues.
