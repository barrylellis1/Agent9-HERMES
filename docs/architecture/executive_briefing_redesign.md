# Executive Briefing Redesign — one document, two default disclosure states

**Created:** 2026-08-22
**Status:** Built. Stages 1-9 shipped Aug 2026; the composition pass that made move #1 real
landed 2026-08-27. See "Build state" below.
**Updated:** 2026-08-27
**Mockup:** https://claude.ai/code/artifact/2a1b0c69-654a-4592-8ae4-0ce0c3c6f3bb
**Evidence:** a full live SF pipeline run executed 2026-08-22 (EBITDA / Base Oil & Additives,
lubricants, CFO principal). Raw payload and screenshots:
`decision-studio-ui/scratchpad/sf_run2/`.

---

## 1. Why this exists

Raised directly: the briefing has to serve two people at once, and currently serves neither
cleanly.

- The **Business Analyst / FP&A decision framer** needs confidence in the details — the evidence
  chain, the checks, what was tested and what wasn't.
- The **decision maker** needs a much cleaner view of the decision ask, rationale and stakes —
  something readable in two minutes or presentable in a meeting.

Today `ExecutiveBriefing.tsx` (1848 lines) renders **ten accordion sections** plus a persistent
Decision Workspace chat. Three open by default (`options`, `recommendation`, `roadmap`;
`ExecutiveBriefing.tsx:314-315`); seven are collapsed — including the two that carry the caveats.
The split is roughly along the two personas already, but not by design: `Stage 1: Independent
Proposals`, `Stage 2: Cross-Review` and `Moderator Verdicts` are **process transparency** — exactly
what the framer needs and the decision maker does not.

---

## 2. What the live run actually showed

This section is evidence, not impression. Every item below was observed on screen or in the
captured payload on 2026-08-22.

### 2.1 The real decision was buried at the bottom

The run's own `unresolved_tensions[0]` reads:

> "opt_1 assumes the Base Oil & Additives problem is primarily a pricing-execution gap, while
> opt_2 assumes it is primarily a structural input-cost problem — **both cannot be the dominant
> driver**, and resourcing both simultaneously risks diluting either effort."
> *Requires:* VP Finance to complete a cost-vs-price attribution analysis on the $5.55M delta,
> separating input-cost inflation from unrealized pricing, before Week 3.

That is the decision. Not "choose one of three options" but *"we cannot yet tell which hypothesis
is true, and the recommended first action is the one that finds out."* It rendered inside a
collapsed `Considerations & Blind Spots` / `Unresolved Tensions` region at the very bottom of the
page.

**This is the single highest-value change in the redesign:** the contradiction becomes the
headline, and the three options are presented underneath it as consequences of an unresolved fork.

### 2.2 Two of the three options were modelled identically

| Option | Recovery range | Time to value | Reversibility | Cost |
|---|---|---|---|---|
| opt_1 Rapid Cost-to-Price Realignment | **$3.8M–$5.2M** | 0–90 days | high | 0.45 |
| opt_2 Integrated Full-Potential Program | **$3.8M–$5.2M** | 12+ months | low | 0.60 |
| opt_3 Structural Supply Chain Reset | $3.2M–$4.8M | 3–12 months | medium | 0.50 |

opt_2 is **strictly dominated** — identical modelled upside to opt_1, but slower, costlier and hard
to undo. Rendered as equal rows in the Strategic Options table, that asymmetry is invisible; a
reader scanning the impact column sees two equally attractive paths.

The redesign keeps opt_2 on the page **dimmed and explicitly flagged**, rather than dropping it.
Removing it would conceal a real signal: the model failed to differentiate two of its own options.

### 2.3 Internal option IDs leaked into executive prose

The decision ask rendered on screen as:

> "Approve immediate launch of the 30-day Base Oil & Additives cost-and-pricing diagnostic
> **under opt_1**."

Not isolated — `immediate_actions[*].why_it_matters` also carries "the 30-day pricing diagnostic in
**opt_1**", "**opt_2**'s structural cost hypothesis", "**opt_3**'s regional pricing thesis". This is
LLM output hygiene, not a rendering bug (see §5 — filed to SF, not to the UI).

### 2.4 Cost of Inaction leads with the wrong number

The block renders `In 30 days: $-74.0M ($-618K)`. The large figure is a projected EBITDA *level*;
the parenthetical is the actual 30-day erosion. They are an order of magnitude apart, and this is
the most visually prominent element on the page — the only light-coloured panel in a dark layout.
"What does waiting cost?" is answered by the small number.

### 2.5 The situation opened with an 86-word sentence

One sentence, six figures, two clauses of interpretation, unbroken. Measured directly from
`briefing-text.txt`.

### 2.6 The page cannot be captured or printed whole

`ExecutiveBriefing` renders inside a fixed-height inner scroll pane. A Playwright `fullPage: true`
screenshot returns only the fold. This matters because the meeting artifact is assumed to be the
Print / Export / View Report path — **that assumption is untested and should be verified before
anyone relies on it in a room.**

---

## 3. The two-persona model

**One document, two default disclosure states.** Not two documents, and not different content.

| | Decision maker | Decision framer (FP&A / analyst) |
|---|---|---|
| The ask, owner, deadline, approval type | Open | Open |
| Why now / cost of waiting | Open | Open |
| The unresolved fork (§2.1) | Open | Open |
| The three paths, with scope + dominance flags | Open | Open |
| Before you approve (blind spots, blocking conditions) | Open | Open |
| Verification ledger, council record, per-option assumptions, prerequisites, evidence chain | **Collapsed** | **Open** |

This satisfies the **M1 invariant** rather than fighting it. M1 is stated in three independent
places — `src/registry/models/principal.py:79-84`, `DecisionAskBlock.tsx:19-20`, and
`DEVELOPMENT_PLAN.md` Phase 13 — and says role adaptation controls *entry point and depth only,
never the facts or the recommendation*. A disclosure-state difference is precisely that; a
content difference would violate it.

### The framer's layer is already a trust ledger, not prose

`moderator_grades` (present and populated in the live payload) carries per option:

- `constraint_survival`: pass / fail, plus `violated_constraints`
- `causal_grounding`: e.g. `cogs -> gross_margin_pct (confirmed, correlational, ~1-month lag)`
- `arithmetic_consistency`: pass / fail, plus `arithmetic_note`
- `grade_rationale`: an audit paragraph

That is exactly "confidence in the details," and it needs **no new backend fields** — only promotion
out of a bottom accordion into a compact, scannable ledger. The mockup renders it as three
pass/fail rows with the mechanism underneath.

---

## Build state (2026-08-27)

Stages 1-9 shipped the components. A design critique of the assembled page then scored it
**19/40 — Poor**, with 7 of 8 cognitive-load checks failing, because several moves were built and
then defeated by composition. What changed on 2026-08-27:

| Move | State | Note |
|---|---|---|
| 1. Contradiction becomes the headline | **Done** | Shipped in Stage 8 but rendered *fifth*, below two statements of the answer — one full scroll under the fold. `ContradictionBanner` now has a `headline` variant, leads the page, and carries the document's only `<h1>`. |
| 2. Dominated option labelled, not hidden | Built, unverified live | `dominated_by` is `null` on all three options in the verified payload, so the flag has never been seen firing on real data. |
| 3. Scope travels with every number | Built | Scope chip present; still renders at 9px. |
| 4. Cost of inaction leads with incremental loss | **Done** | The number was fixed earlier; the *panel* was not — it was `bg-amber-50` on a slate-950 page, making it the brightest object in the first viewport. Now dark-first, with `print:` variants for paper. |
| 5. Option titles a person would say aloud | Not done | Titles are still the generated ones, truncated in the workspace selector. |
| 6. Ten accordions become one page and one toggle | **Done** | Shipped as ten accordions *plus* one toggle. Four (Market Intelligence, Stage 1, Stage 2, Moderator Verdicts) and the Implementation Roadmap now live on `/report/:situationId` and `/debate/:situationId`, which already rendered them from the same payload. `ANALYSIS_SECTION_IDS` went from seven ids to three. |

Deliberately still open, and **not** silently assumed done: the accessibility layer (0 `aria-*`,
no focus trap on `OptionDetailDrawer`), the 107 hardcoded semantic colours vs 0 `severity-*`
tokens, two-step approve confirmation, and load-bearing meaning in `title=` tooltips.

Open question §6 ("three overlapping output surfaces") is now **answered**: the briefing decides,
the report explains. Print and Export were also collapsed — Export survives at narrow widths.

---

## 4. The six design moves

1. **The contradiction becomes the headline** (§2.1).
2. **A dominated option is labelled, not hidden** (§2.2).
3. **Scope travels with every number.** Every impact estimate in the live run is `scope: "segment"`
   with `scope_label: "Base Oil & Additives"` — none are enterprise. `DecisionAskBlock.tsx:92-94`
   already carries a code comment warning that stripping the scope qualifier is "how a segment
   figure gets read as an enterprise one, an order of magnitude apart"; the options table does not
   honour it. Hatched range bars plus an explicit scope chip.
4. **Cost of inaction leads with the incremental loss**, not the projected level (§2.4).
5. **Option titles a person would say aloud**, with the generated title retained underneath so
   nothing is silently rewritten.
6. **Ten accordions become one page and one toggle** (§3).

---

## 5. What this redesign does NOT fix — filed to other owners

These surfaced in the same run but are **not** UI problems. Presenting them better would be
lipstick; they need fixes in the agents that produce them. Cross-referenced here, owned in
`DEVELOPMENT_PLAN.md`.

| Finding | Real owner |
|---|---|
| Council converges (three near-verbatim hypotheses, all "High conviction") but is presented as three independent opinions | A9_Solution_Finder_Agent / persona design |
| Two options modelled at an identical recovery range | A9_Solution_Finder_Agent synthesis quality |
| `opt_1`/`opt_2`/`opt_3` in executive-facing prose | A9_Solution_Finder_Agent prompt / output hygiene |
| Real firm names (`MCKINSEY`/`BCG`/`BAIN`) still rendered on the Council Debate page | Phase 18 Category C (already scoped, not done) |

**Open question, deliberately not resolved here:** when the council genuinely converges, should the
UI *say so* rather than render three columns implying independent agreement? Three agreeing experts
read as corroboration; one model answering three times is not corroboration. This is a content and
positioning decision, not a layout one. `persona_council_experiments.md` already found that "topic
selection converges under every configuration" — this run is that finding rendered on screen.

---

## 6. Open questions

1. **Council convergence presentation** (§5) — needs a product call.
2. **Does the meeting artifact stay this page, or `WhitePaperReport`?** There are already three
   overlapping output surfaces: `/debate/:id` (process + trade-off), `/briefing/:id` (this page),
   and `/report/:id` (`WhitePaperReport.tsx`, 435 lines, serif, white, 9-section consulting arc:
   Executive Summary → Situation & Context → Root Cause → Market Context → Options Evaluated →
   Recommendation & Rationale → Implementation Roadmap → Risks & Mitigations → Appendix). The
   redesigned brief overlaps all three. Consolidating is likely right; which one survives is not
   settled here.
3. **Does the disclosure default key off the new `workflow_role` field** proposed in
   `decision_framer_and_decision_maker_personas_design.md`, or off `communication.detail_level`
   which already exists? The former is cleaner; the latter ships sooner.
4. **Print/Export fidelity** (§2.6) — verify before relying on it.

---

## 7. Related documents

- `decision_framer_and_decision_maker_personas_design.md` — the principal-model side of the same
  split; this document is its briefing-surface consequence
- `ui_refinement_plan.md` §8 — the wider empirical UI findings from the same session
- `persona_council_experiments.md` — the convergence finding this run reproduced live
- `hitl_decision_philosophy.md` — Gate 2 (Solution Decision) is the moment this page serves
- `DEVELOPMENT_PLAN.md` Phase 13 — M1 invariant, and Cat 4's deferred "role-adaptive collapse
  depth" item, which this document supersedes with a concrete design
