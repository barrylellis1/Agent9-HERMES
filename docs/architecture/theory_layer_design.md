# The Theory Layer — Design Sketch

**Status:** Design direction (July 2026). Not scheduled. P0 items are candidates for near-term scheduling; everything else is gated (see §10).
**Companion docs:** `principal_perspective_weighting_design.md` (five lenses, role weighting, Value Driver Tree V1), `analytical_methodology_positioning.md` (KT/MBB framing), DEVELOPMENT_PLAN.md Phase 12 (12A–12E).
**Part of the unified SF build spine — DEVELOPMENT_PLAN.md Phase 15:** this doc's §5.2 / §8 / §10 are **Stages D–F** (grounding + constraint input, critic pass, "bets on" → VA). The SF prompt/schema half — **Stages A–C** — is `llm_prompt_redesign_da_sf.md`. The unified `SolutionAssumption` (Stage B) also absorbs Phase 11J P1.

---

## 1. Purpose

Agent9 today is a **perception-and-response** system: SA senses, DA diagnoses, SF proposes, VA verifies. What none of the agents read from or write to is the thing an executive actually runs the business on: a causal **theory of the business** — the assumption register plus the causal map of how internal processes and external forces generate value.

This document defines that missing layer, how it gets populated without consulting-style elicitation (accretion + template seeding), how it is kept honest (provenance ladder, self-falsification), how it is visualized (layered Value Driver Tree), and why it is the long-term moat (an accumulated, reality-tested causal model of the client's business that a competitor — or a consulting firm — cannot cold-start).

It deliberately includes the **pre-mortem** (§9). The failure modes are as load-bearing as the design.

---

## 2. Conceptual Foundation — How Executives Actually Model a Business

Distilled from first-principles discussion (July 2026); this is the theory the product design must serve.

### 2.1 The mental object is a theory, not a scoreboard

Executives carry Drucker's "theory of the business": *we make money because X; that holds while Y stays true; Z could kill us.* KPIs are evidence for or against the theory, not the object itself. Consequence: executives track **surprise, not deviation**. Explained variance is noise regardless of magnitude; unexplained variance is signal regardless of magnitude. A system that re-alerts on explained variance is measuring deviation when the user cares about surprise.

### 2.2 The internal machine has three layers

| Layer | Contents | Role |
|---|---|---|
| Physical/operational | Capacity, throughput, people, pipeline, inventory, customer trust — stocks and flows | Where causes live |
| Economic | Price, mix, cost structure, working capital | Where causes get measured (arithmetic over layer 1) |
| Commitment | Plan, budget, guidance, covenants, contracts | Why causes matter (promises about layer 2) |

Cause lives in layer 1, is measured in layer 2, matters because of layer 3. Almost all reporting shows only layer 2. A **plan is a causal forecast with embedded assumptions**; a variance is a falsified assumption, and one dead assumption often explains several red cells at once — and silently invalidates plan lines that have not gone red yet.

Two structural facts: **levers act on layer 1 with real lags but are judged in layer 2 at fiscal cadence** (source of classic misjudgments), and **the org chart is a partition drawn over the causal graph** — causes routinely cross box boundaries, so "whose lever is it" is a causal-map question.

### 2.3 The external world: actors vs fields, entering through ports

- **Actors with intent** (competitors, customers, suppliers, regulators, capital markets, labor) respond to what you do — reasoning about them is game-theoretic.
- **Fields/conditions** (rates, commodity cycles, FX, technology) do not respond — you position and hedge.

External forces enter through a small enumerable set of **ports** (input costs, demand volume, price realization, capital cost, talent supply, regulatory constraint), each with a characteristic **lag** and **buffer** (inventory buffers commodity moves; backlog buffers demand; contracts buffer price). The Lubricants anchor scenario (Base Oil rising while COGS declines) is a port question: an external cause that *should* have transmitted and hasn't — the interesting object is whatever is in the chain (inventory layers, hedges, repricing lag, mix).

### 2.4 Properties of real cause-and-effect

Delayed (cross-period), mediated (chains, not pairs — diagnosis names the broken link), looped (reinforcing/balancing feedback), confounded (shared upstream causes), asymmetric (one-way doors: lost customers, departed talent — triage on irreversibility, not magnitude).

**Arithmetic decomposition ≠ causal explanation.** A DuPont/P×V×M bridge locates variance ("price fell in North"); the cause is usually steps upstream and often outside the ledger (a competitor's inventory position). Every driver tree bottoms out in accounting atoms; causality keeps going. This is the known limitation of the Value Driver Tree as an arithmetic skeleton — the theory layer is what annotates it into a causal object.

### 2.5 Executive maps exist but are flawed in predictable ways

Successful CEOs demonstrably hold causal maps (dominant logic literature; Bezos flywheel; Dalio's machine; Danaher DBS), but: compressed and uneven (3–5 dominant loops, resolution biased toward their functional background), systematically bad at delays/feedback/accumulation (Sterman), and **maintained socially** — each exec holds a shard; the leadership meeting is a model-synchronization ritual; reports are the prompt, not the product. Maps also go stale while the numbers stay explainable (Kodak, Nokia). The differentiator is **map maintenance, not map possession**.

**Product consequence:** do not give executives a causal map (presumptuous; rejected). Help with the three things they demonstrably struggle with: **externalizing** the implicit map, **testing** it against reality (especially in delay/feedback territory), and **synchronizing** shards across the team.

---

## 3. The Trust Model — When Do Executives Trust Proposed Solutions?

### 3.1 Calibration, not completeness

Executives trust a recommender whose causal model **reproduces things they already know to be true** and extends one step beyond. Checked against: verifiable anchors (did it get right what I can check?), **binding constraints** (a solution violating a known constraint retroactively destroys trust in the diagnosis), and probe survival ("have you considered X?"). Advice-taking research: discounting collapses once the advisor demonstrates independently verifiable knowledge.

### 3.2 Diagnosis and solutions have different trust thresholds

A diagnosis is checkable against data — DA output earns trust cheaply. A solution embeds a **counterfactual** that cannot be checked in advance; its trust must be borrowed from the verified diagnosis it rides on, from explicit inspectable assumptions, or from track record. SF is therefore the agent most exposed by a missing theory layer. Threshold scales with irreversibility: SF should target the **material-but-reversible band**; one-way-door decisions require human shared accountability no system provides.

### 3.3 Trust is temporal — VA is the trust engine

Trust accrues from a track record of being right about checkable things. Every VA-validated outcome is a calibration proof for the causal model. Ship solutions **explicitly subordinated to the verified diagnosis** ("conditional on this cause, which you can check, here are options and the assumptions each bets on") and let VA convert usage time into trust. Theory and trust accrete through the same mechanism.

### 3.4 What consulting engagements actually buy (positioning honesty)

The MBB diagnostic phase purchases four things: (1) a client-specific causal model — rebuilt from scratch every engagement, decaying on departure; (2) shard harvesting via interviews; (3) pre-socialization (recommendations land as co-created); (4) blame insurance. Agent9 can beat (1) and partially do (2); it **cannot** do (3) or (4) — those are social products, and they cap SF's realistic ambition.

**Agent9 is not positioned to "take over MBB."** Its real competitor is **Excel plus the monthly variance meeting** in the mid-market/enterprise segment MBB structurally cannot serve at its cost. Defensible claims, descending: (a) in installed accounts, the recurring "what's going on with margin" question becomes a product feature, removing the reason some diagnostic engagements get commissioned; (b) the accreted VA-validated model makes any consultant who shows up faster/cheaper — firms are plausible channel partners or acquirers, not victims; (c) top pricing tier prices like one engagement and delivers standing coverage. MBB appears in the deck only as the price anchor.

---

## 4. The Theory Layer — Definition

A per-client, persistent artifact with two components and one integrity mechanism:

1. **Assumption register** — the assumptions embedded in plans and thresholds, made explicit and testable. States: `active | held | falsified`. A threshold breach upgrades from "number crossed line" to "this assumption died — and these other plan lines depend on it."
2. **Causal graph** — extends `kpi_relationships` (11I-B) rather than introducing a new registry. Nodes: KPIs, objectives (12C), external ports. Edges: direction, `mechanism`, `lag_periods`, buffer notes.
3. **Provenance ladder** (the integrity mechanism and the startup↔accretion bridge):

| Provenance | Meaning | Visual | Consumption rule |
|---|---|---|---|
| `template` | Industry prior, seeded by MA research | dotted | Never asserted; SF must caveat or ignore |
| `confirmed` | Executive/admin blessed at onboarding or review | dashed | Usable by SF with attribution |
| `hitl_proposed` | Extracted from usage, awaiting confirmation | dotted+badge | Not consumed until confirmed |
| `va_validated` | Outcome-tested by VA (DiD + human adjudication) | solid | Highest rank; language capped at "consistent with" — never "proved" |

**Shard alignment warning:** per-principal personalization (PIB, lens weighting) *institutionalizes shard divergence* unless it becomes role-weighted **views over one shared model**. DA findings update the shared graph; the system flags when two principals' explanations of the same upstream cause contradict.

**Definition of "situation" (target state):** an assumption in the client's causal model was falsified — not merely "threshold crossed." This framing dissolves alert noise structurally: explained variance stops being a situation while its explanation holds (and only while it holds — §5.1).

---

## 5. Accretion — Capturing Theory During Normal Use

Principle: **executives will never fill in causal metadata forms.** The only viable capture is LLM extraction from what humans already do, landing as `status='proposed'` records for confirmation — the shipped 12A/12E "confirm rather than create" pattern. All extraction runs through the LLM Service Agent. Nothing writes theory autonomously.

### 5.1 SA HITL — mine the comment field (P0)

`HITLRequest` today: `decision` + free-text `comment` that dies in the audit log (`situation_awareness_models.py`). Add an extraction pass proposing:

- **Explanation records** `{kpi_id, dimensional scope, cause, expected-to-hold-until}` → powers explained-variance suppression. **MANDATORY: every explanation carries a hard expiry AND a self-falsification check** — the alert returns automatically and loudly the moment the predicted condition fails (e.g., "recovers in August" and August recovery doesn't materialize). Explanation-based suppression without self-falsification is snooze with better paperwork, which the accountability model already rejected. No indefinite suppression, ever.
- **Assumption records** — attach to the threshold row they explain.
- **Relationship candidates** — proposed `kpi_relationships` rows with mechanism/lag.

### 5.2 Constraint capture — two points, one register (designed 2026-08-12)

- **Approval → "this option bets on:" assumption list**, emitted by synthesis, confirmed at approval, passed to VA in the registration payload. Rides the same wiring as the open SF→VA HITL TODO (kpi_id + impact bounds) — implement together. **Shipped Aug 2026** (`workflows.py` HITL-approve handler → `AssumptionProvider.upsert`).
- **Rejection/modification rationale → constraint records** ("can't touch pricing on the anchor account, contract to 2028"). The visible learning loop — SF demonstrably stops proposing known-impossible things — is the calibration behavior executives read as competence. ⚠️ Per-client prompt injection widens the cross-tenant contamination surface previously hit in SF — isolation tests required.

The rest of this section is the design that fell out of working through that second bullet. **Not built.**

#### 5.2.1 There are two capture points, and they are complementary

Constraints are stated at two different moments, and the original sketch only saw one:

| | **Problem refinement** (DA) | **Solution rejection** (SF) |
|---|---|---|
| Prompt | direct question — "what levers are off the table?" | reaction to a concrete proposal |
| Cost to state | cheap; no decision attached | **costly** — overriding a recommendation |
| Recall quality | memory-limited — nobody lists the union agreement unprompted | triggered; far better |
| Generality | stated categorically | stated about *this* option |
| Rationalization risk | low | real — the reason given may not be the reason |

Neither dominates. Rejection is stronger on **assertion** (§4's own logic: vetoes are asymmetrically less bias-prone than confirmations — rejecting requires overriding, agreeing requires only inertia). Refinement is stronger on **generality**. A single ladder position cannot hold both, which is the same collision §5.5 already resolved for causal edges by splitting `causal_rung` from `provenance`.

**Resolution: same rung, different default reach.** Both are *directly elicited*, so both enter `confirmed` and active — see 5.2.2. They differ only in what they bind by default (5.2.4).

`ConstraintItem.source` gains `solution_rejection` alongside `refinement`, so the capture point survives into the register.

#### 5.2.2 Trust on capture — the ladder's caution does not apply here

`hitl_proposed` ("not consumed until confirmed") was built for **mined** material — the SA comment field, where a human never asserted anything and inference is doing the work. A direct question answered directly is a different epistemic event, and §5.5's guardrail already carves it out as the legitimate HITL contribution: *"domain facts an algorithm can't know (a supplier change, a contract event)."*

**Rule: if an executive answers a direct question, we trust it until it is proven wrong.** Refinement and rejection constraints enter `active` and are consumed immediately. This also disposes of the confirmation-lag problem — there is no queue to bypass (§5.4).

The boundary of that rule matters: it covers what the executive **asserted**, not what a model **inferred they meant**. See 5.2.4.

#### 5.2.3 VA cannot falsify a constraint — this is structural, not a gap in wiring

VA falsifies **assumptions** cleanly: an option bet on base oil normalising, VA observes the outcome, held or broke.

Constraints are not symmetric with this. A constraint's job is to stop certain options being generated — so **if a constraint is wrong, the evidence that would reveal it is never created.** The option was never proposed, never approved, never measured. VA sees nothing, because there is nothing to see.

"Can't raise prices on the anchor account" persists past the Q3 renewal. SF stops proposing price moves. No solution fails, no assumption breaks, VA stays silent, and the register looks healthy while quietly narrowing what the system can imagine. **This is the same failure §5.1 forbade outright for explanations — absence of evidence manufactured by the suppression itself** — and it is worse here, because a stale constraint is invisible: the failure is an *absence* of options, and nobody notices what was never proposed.

**Therefore constraints need a falsifier that is not outcome data.** It is the confirmation beat (5.2.5). This also catches rationalization: asking *"is this still true?"* at a later situation, outside the heat of rejecting a specific option, is exactly the test a real constraint survives and a constructed reason tends not to. No one has to distrust the executive in the moment.

#### 5.2.4 Reach — business process, not KPI

**Constraints bound decisions. KPIs are measurement instruments. Business processes are where decisions get made.**

"Can't raise prices on the anchor account" is not a fact about `gross_margin_pct`. It is a fact about revenue management, and it should bind whether the trigger was margin, net revenue or product sales revenue. Keying it to whichever metric happened to breach is an accident of which threshold fired first.

| Field | Role |
|---|---|
| `client_id` | hard tenant boundary — RLS-enforced, non-negotiable |
| `business_process_ids[]` | what it **binds** |
| `kpi_id`, `situation_id`, captured-at | where it **came from** — searchable tags, never gates |

Many-to-many is required, not optional: "headcount is frozen" bounds Finance *and* Operations. The current `assumptions.scope` single string (`scope = $2 OR scope = 'client'`) cannot express this.

**Default reach is deterministic:** the `business_process_ids` already attached to the KPI under analysis. That is a fact about our own registry, so it inherits the executive's trust and applies immediately.

**Inferred widening is held until confirmed.** When extraction concludes a constraint reaches further than the analysed KPI's processes ("this applies to anything touching the anchor account"), that is the *model* reasoning about what the executive meant — precisely the class 5.2.2's trust rule does not cover. Propose it, show it at the confirmation beat, apply it only when accepted.

**No promotion ladder.** An earlier sketch had reach earned by repetition (situation → KPI → client). That is wrong, not merely unnecessary: if a constraint is a fact, it is true everywhere it is relevant on day one, and a promotion mechanism means deliberately withholding a known fact until someone repeats themselves — the system being artificially stupid, plus machinery whose only job is to undo a restriction we imposed on ourselves.

⚠️ **Prerequisite.** Business process ids are currently inconsistent across registries (mixed snake_case, display names and ids — see root `CLAUDE.md` known issues). That is tolerable when BPs drive dimension hints; it is **not** when they gate whether a prohibition applies. A fuzzy match either leaks a prohibition onto unrelated work or silently fails to apply one, and the second is invisible. Constraint retrieval must be strict-match and must **log loudly when a constraint's BP ids do not resolve** — an unresolvable constraint should never fail silently, because its whole job is to stop something happening. Domain-level BPs (`"Finance"`) are too coarse to be usable here.

#### 5.2.5 The confirmation beat — inside the solution HITL

Not a standing queue (§5.4), not a separate ritual. At solution review the principal is already deciding; the beat is *"these N constraints are being applied to this problem — confirm."*

It does three jobs at once:
1. Confirms relevance — the situation→register mapping will not always be clean, so this is where LLM inference gets a human check rather than being trusted silently.
2. Falsifies stale constraints (5.2.3) at exactly the moment they would bind.
3. Accepts or rejects inferred widening (5.2.4).

Where the principal stated a review date — *"before the contract renews in Q3"* — carry it as a marker so the beat can say *"stated as holding until Q3, and it is now October"* rather than presenting the constraint flat. Not a hard expiry that silently deletes; a prompt that makes staleness visible.

#### 5.2.6 Late capture requires re-running Solution Finding

A constraint captured at solution review arrives **after** the options were generated. Those options were conceived without it. So the principal must be able to re-run Solution Finding with the augmented constraint set — a different option could emerge, and usually should.

This upgrades the learning loop from *next time* to *now*. Deferred learning is invisible; nobody notices an option that was not proposed weeks later. Immediate re-generation is the demonstration.

- **Full re-run, not partial reuse.** Constraints bind at Stage 1 (`refinement_compact_s1` feeds the persona prompts). Reusing Stage 1 hypotheses would produce options *conceived* under the old bounds and merely re-described under the new ones.
- **Replaces the briefing.** Round 1 remains retrievable under its own `request_id` and can be printed for comparison.
- **Supersession must be recorded** — run 2 links to run 1 with the constraint that caused it, so the briefing can say *"these options changed because you added this constraint."* That sentence is the value.
- **The over-constrained terminal state must be sayable.** Enough cycles and the feasible set empties. *"Everything that would work, you have ruled out"* is a legitimate and valuable answer — but today it would surface as generic stub options, indistinguishable from the known defect where a total LLM outage renders as a successful briefing. It needs its own explicit outcome.
- **Cycle count visible, not capped.** An executive on their fourth re-run is telling you something about the problem; cutting them off mid-thought is worse than letting it run.

⚠️ **This is the risk that decides whether the loop is worth building.** If the principal rejects an option saying "we can't touch the anchor account" and the re-run proposes something else that touches it, that is not a neutral failure — it is the system visibly not listening, seconds after being told, in front of the person whose trust the loop exists to earn. Deferred learning fails quietly; this fails loudly. The capture-and-apply path must be verified end-to-end on a real rejection before it goes near a demo.

#### 5.2.7 Schema deltas required

- `assumptions.business_process_ids` (array) — replaces single-string `scope` for constraint binding; `scope` degrades to a provenance tag.
- `assumptions.review_date` (nullable) — the principal's stated validity horizon, for 5.2.5.
- `ConstraintItem.source` += `solution_rejection`.
- Retrieval changes from `get_active_constraints(client_id, scope=kpi_id)` to a BP-set match resolved from the analysed KPI's `business_process_ids`.
- Supersession link on the solution workflow record (5.2.6).

### 5.3 VA HITL — the richest and currently thinnest touchpoint

VA is the only agent observing **tested** causality:

- **Outcome adjudication** at validation checkpoints: "KPI recovered — solution, market, or other?" **Structural bias rule: never pre-fill the flattering answer.** Show DiD evidence and ask cold, or ask the counterfactual ("would this have recovered anyway?"). Anchored self-adjudication converts the theory into institutional self-justification (§9.4).
- **Assumption verdicts** at closeout: each "bets on" assumption → held/broke.
- **Lag capture for free**: VA measures actual time-to-impact; write it onto the lever edge. Lags are what humans estimate worst and VA observes automatically.
- CoI notes during implementation → same extraction as SA comments.

### 5.4 Review governance — no standing queue

Proposals are confirmed inside an **existing ritual** (monthly assessment-run review) with a named owner, or not generated at all. A standing proposal queue with no owner becomes a dead-letter queue (§9.3).

### 5.5 Schema deltas — DESIGNED 2026-07-23, not yet applied

Migration: `supabase/migrations/20260723_theory_layer_causal_schema.sql`. Models: `src/registry/models/kpi_relationship.py` (extended), `src/registry/models/assumption.py` (new). Designed after researching causal-graph modeling practices (Pearl's ladder of causation, AIOps causality graphs, DiD/Granger causality) — see DEVELOPMENT_PLAN.md Phase 15 Stage D notes for the full research synthesis.

- **`kpi_relationships` +** `mechanism` (free text), `lag_periods` (months; prefer Granger-derived over guessed), `causal_rung`, `provenance`, `confidence`.
- **`causal_rung` and `provenance` are separate axes — the refinement over the original one-field sketch.** `provenance` = *how captured* (the ladder above). `causal_rung` = *which rung of Pearl's ladder was actually established*: `correlational` (SA/DA association only) | `intervention_hypothesized` (SF proposed, untested) | `intervention_tested` (VA ran DiD/counterfactual on *this* edge). A `va_validated` edge is not automatically `intervention_tested` unless VA specifically tested that relationship — conflating the two axes was the gap the research surfaced.
- **Guardrail added 2026-07-26 — HITL confirmation is not scientific validation.** Splitting the axes stops "how captured" from being read as "how rigorously established," but nothing originally *enforced* that separation: a record could be `provenance='confirmed'` (a human agreed) and `causal_rung='intervention_tested'` (a scientific claim) at the same time — exactly the "principal confirmation bias dressed up as proof" risk raised in discussion. Human agreement with a plausible-sounding narrative is not a statistical test; it's confirmation bias, and it's the same cognitive failure mode (Sterman's finding on human causal reasoning) the theory layer exists to correct, not re-encode. **Enforced now, not just documented:** `causal_rung='intervention_tested'` requires `provenance='va_validated'`, at both the DB layer (`kpi_relationships_tested_requires_va_validated` CHECK constraint) and the Pydantic model (`KPIRelationship._intervention_tested_requires_va_validated`). Only VA actually running DiD or Granger causality on a specific edge may claim the tested rung — no write path, human or automated, can bypass this. This also reframes what HITL confirmation of a causal edge should legitimately contribute: domain facts an algorithm can't know (a supplier change, a contract event) and vetoes (asymmetrically less bias-prone than confirmations — rejecting a claim requires overriding it, agreeing requires only inertia), never a causal verdict.
- **`confidence` is categorical** (`high|moderate|low`), matching `SolutionAssumption.confidence` — deliberately not a float; single-client business data rarely supports probabilistic precision, and a float would encode false precision.
- **New `assumptions` table folds constraints in via a `record_type` discriminator** (`assumption | constraint | explanation`) rather than a separate constraints table — same unification pattern as Stage B's single `SolutionAssumption` object. `record_type='explanation'` rows have a **DB-enforced mandatory `expiry`** (CHECK constraint, not just application logic) — directly encodes the §5.1/§9 pre-mortem #5 rule that indefinite suppression without self-falsification is forbidden.
- Both are tenant tables → **Infra B3 RLS checklist applied**: `kpi_relationships` already had RLS (11I-B); `assumptions` is new and gets full GRANT/ENABLE/POLICY, added to `_RLS_TABLES` in `scripts/verify_prod_registry.py`.
- **Status: schema designed and unit-tested (`tests/unit/test_theory_layer_causal_schema.py`), migration file written, NOT applied to any database (local or production).** Held uncommitted per explicit instruction — apply only when there's a concrete producer (accretion pipeline) or consumer (SF Stage D input contract) ready to use it, not ahead of either.
- Conflict semantics needed for contradictory edges (open question §12) — still open, not addressed by this schema pass.

---

## 6. Cold-Start Hybrid — Template Seeding Before Accretion

The flywheel (usage → theory → sharper output → trust → usage) fails at zero clients: accretion has no fuel. The fix is the consulting move: arrive with an **industry prior** and calibrate — confirming a mostly-right draft is 10× cheaper than eliciting from blank.

**Seed sources requiring zero usage:**

1. **Industry causal templates via MA** — third instance of the shipped 12A/12E pattern: MA researches company/industry → proposes driver tree, external ports, typical lags as `provenance='template'`. Generic industry causality (base oil → COGS, inventory-buffered, ~1–2 period lag) is exactly what LLM research does well — it's what the first-year consultant brings.
2. **The plan itself** — monitoring-profile thresholds + comparison types already encode assumptions; an onboarding LLM pass drafts the assumption text behind each for confirmation.
3. **What onboarding already declares** — 12C objective→driver weights and seeded `kpi_relationships` are causal edges lacking only provenance labels.
4. **One hour of executive correction, not weeks of elicitation** — present the templated tree: "drawn for a generic lubricants business — what's wrong for yours?" Correcting a wrong draft is easy and engaging where blank-page articulation fails. Double payoff: this **is** the calibration ritual (§3.1) — the exec watches the system understand their industry before data flows. Hunt **deviations** from template (their hedging policy, their anchor contract) — that's where client-specific value lives.

**Two flywheels, same schema:**
- **Template flywheel (portfolio-level, works at low per-client usage):** each client's confirmed corrections sharpen the industry template — *structure only, never data* (hard confidentiality line). Each onboarding gets faster and more impressive. This is MBB's cross-engagement pattern library, accumulating in the product instead of partners' heads.
- **Accretion flywheel (per-client, needs usage):** starts warm — usage *upgrades* edges (dotted→solid) rather than building from empty. Day one the tree is complete-but-dotted ("your theory, awaiting confirmation"), never sparse.

---

## 7. Visualization — Layered Value Driver Tree

Avoid two failure modes: the force-directed causal hairball (executives reject on sight) and the pure financial driver tree (arithmetic, not causal). Use one as the skeleton of the other:

**Spine** = Value Driver Tree per `principal_perspective_weighting_design.md` §7: objective (12C) → apex metric per principal → decomposition branches → KPIs; node color = worst attached situation severity; node weight = value-at-stake. Deterministic layout, DuPont-familiar.

**Toggleable overlays:**
1. **External ports** — off-tree nodes (Base Oil, rates, competitor capacity) docking into tree nodes, edges badged with lag + buffer. Renders the Lubricants anchor scenario literally.
2. **Cross-branch causal edges** from `kpi_relationships` — thin arcs, **drawn only when active in a current situation** (the anti-hairball rule).
3. **Assumption state** — markers on nodes with active assumptions; falsified = broken-link glyph on the edge it invalidated.
4. **Provenance encoding** — solid/dashed/dotted per §4 ladder. The tree visibly hardens with use: "every solid line is something the system verified about your business" (renewal-meeting slide; language stays "validated/consistent with," never "proved").

**Reframe:** the tree is the **browsing and adjudication UI for the theory layer** — proposed edges get confirmed/disputed on it; shard conflicts surface on it — not just a reporting view.

**Build honesty:** needs custom SVG + DAG layout (dagre/elkjs); Recharts won't do it. **Static exhibit first** (one non-interactive rendering in DeepFocusView or PIB, spine + external ports only) — earn the interactive version only if pilots actually look at it (spider-chart lesson). Not blocked on DA's structured L5 contract: the spine renders from 12C driver weights + monitoring profiles today; L5 deepens branches later.

---

## 8. Agent Impact Analysis

| Agent | Impact | When PRD/card updates |
|---|---|---|
| SA | HITL comment extraction; explanation-based suppression with self-falsification; situation-as-falsified-assumption framing | P0 build |
| SF | Constraint records into Stage 1 prompts; "bets on" assumption list at synthesis/approval; provenance-gated edge consumption | P2 build (assumption list: with SF→VA wiring TODO) |
| VA | Outcome adjudication HITL (no pre-fill); assumption verdicts; lag write-back | P1 build |
| MA | Industry causal template generator (12A pattern, third instance) | Template-seeding phase |
| PC | Serves principal views over the shared model; shard-conflict surfacing | Deferred (after graph density exists) |
| DA | Structured L5 decomposition contract deepens tree branches (existing lens-weighting dependency) | Unchanged by this doc |
| Orchestrator | Extraction pass routing via LLM Service | P0 build |

PRDs and agent cards are updated **when the touching phase is scheduled**, not now — this document is canonical until then.

---

## 9. Pre-Mortem Register (July 2026)

Kept as first-class design content. "It's July 2027 and the theory layer failed":

| # | Obituary | Mitigation baked into design |
|---|---|---|
| 1 | **Flywheel never spun** — zero clients, no HITL volume; sparse dotted graph demos worse than nothing | Template seeding (§6) makes day-one tree complete; usage *upgrades* rather than builds. Build gate: no extraction machinery until a pilot generates ~8+ substantive HITL comments/month |
| 2 | **Comments were garbage** ("known issue", "ok", empty) and captured analyst shards, not exec shards | Extraction proposes only when content exists; template+interview carry the exec shard; measure comment substance as the gate metric |
| 3 | **Proposal queue = dead-letter queue** — reviewing is nobody's job; rubber-stamped or ignored | No standing queue: confirmation attached to monthly assessment-run review with named owner (§5.4) |
| 4 | **Politically convenient causality** — attribution bias + pre-filled DiD drafts = self-justification with provenance badges; one publicly wrong "solid line" kills the moat story | Never pre-fill adjudication; counterfactual question; DiD language capped at "consistent with"; provenance-gated consumption |
| 5 | **Suppression silenced a real signal** — explanation held while something else compounded | Mandatory expiry + self-falsification on every explanation record; re-alerts loudly on failed prediction; no indefinite suppression (§5.1) |
| 6 | **Tree = the new spider chart** — weeks of custom SVG executives glance at once | Static exhibit first; interactive version must be earned by observed pilot usage (§7) |
| 7 | **Death by scope while core stayed soft** — months of theory scaffolding while VA persistence in-memory, SF→VA TODO open, alert noise unpolished | P0 limited to two items that improve the current product standalone (§10); everything else gated |
| 8 | **Cross-tenant contamination** via per-client prompt injection (previously burned in SF) | Isolation tests required before constraint injection ships; RLS checklist on new tables |

---

## 10. Phasing & Gates

| Phase | Content | Gate to proceed |
|---|---|---|
| **P0** | Assumption text on threshold rows; explanation records with mandatory expiry + self-falsification (alert-noise hardening win, zero flywheel dependency) | None — standalone value; schedule against Phase 12 priorities |
| **P1** | VA adjudication HITL (cold-ask, no pre-fill) + assumption verdicts + lag write-back — dock to SF→VA wiring TODO | SF→VA wiring scheduled |
| **P2** | Constraint capture at both HITL points + BP-scoped reach + confirmation beat + SF re-run loop (**§5.2 — designed 2026-08-12**) | Tenant-isolation tests pass; **business-process id normalisation** (§5.2.4 prerequisite — fuzzy BP matching silently fails to apply a prohibition); ≥1 pilot with real SF usage. Informed by Phase 15 Stage I B-3: if the personas do not diverge on what they ask, per-persona constraint sets matter much less and this reduces to a single shared set |
| **Template seeding** | MA causal template generator + onboarding correction interview + provenance ladder in schema | Scheduled with a real new-client onboarding (12-series slot) |
| **P3** | Static tree exhibit (spine + external ports) | 12C shipped (objectives/driver weights) |
| **P4** | Interactive tree as adjudication UI; shard-conflict surfacing | Observed pilot engagement with static exhibit; graph density from real usage |
| **Kill criteria** | If after 2 quarters of pilot usage: HITL comments avg < ~2 extractable facts/month or proposal confirmation rate < ~50% → stop extraction investment; keep P0 (it stands alone) | — |

**Explicit non-goals now:** building the full layer ahead of usage volume; autonomous theory writes; "proved" language anywhere; interactive tree before static validation; any elicitation workshop in onboarding beyond the one-hour correction interview.

---

## 11. Commercial Framing (for deck/narrative use)

- The theory layer is the **NRR/expansion story, not the demo story**. The wedge stays: faster variance diagnosis, fewer/smarter alerts.
- Moat: an accumulated, VA-tested causal model of *their* business — impossible to rip out, impossible for a competitor (or consultant) to cold-start, and it appreciates with use while a consulting deliverable depreciates from day one.
- Deepest product identity: not "detect situations" but **"keep the executive team's theory of the business honest"** — externalize, test, synchronize.

## 12. Open Questions

1. Conflict semantics when two edges (or two principals' explanations) contradict — who adjudicates, how is disagreement stored/displayed?
2. Assumption granularity — per threshold row, per KPI, or per plan line? (P0 forces a first answer: per threshold row.)
3. Template confidentiality boundary — what exactly counts as "structure not data" when client corrections improve industry templates? Needs a written rule before the second client in an industry.
4. Does the explanation-expiry check run in SA scan or as a scheduled job? (SA scan preferred — no new runtime.)
5. Where does the correction interview live in the 5-day onboarding plan without extending it?
6. Provenance display in PIB emails — do briefings cite edge provenance, or is that UI-only?
