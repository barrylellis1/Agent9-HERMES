# The Theory Layer — Design Sketch

**Status:** Design direction (July 2026). Not scheduled. P0 items are candidates for near-term scheduling; everything else is gated (see §10).
**Companion docs:** `principal_lens_weighting_design.md` (five lenses, role weighting, Value Driver Tree V1), `analytical_methodology_positioning.md` (KT/MBB framing), DEVELOPMENT_PLAN.md Phase 12 (12A–12E).
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

### 5.2 SF HITL — rejections are worth more than approvals

- **Rejection/modification rationale → constraint records** ("can't touch pricing on the anchor account, contract to 2028"). Fed into SF Stage 1 prompts for that client permanently. The visible learning loop — SF demonstrably stops proposing known-impossible things — is the calibration behavior executives read as competence. ⚠️ Per-client prompt injection widens the cross-tenant contamination surface previously hit in SF — isolation tests required.
- **Approval → "this option bets on:" assumption list**, emitted by synthesis, confirmed at approval, passed to VA in the registration payload. Rides the same wiring as the open SF→VA HITL TODO (kpi_id + impact bounds) — implement together.

### 5.3 VA HITL — the richest and currently thinnest touchpoint

VA is the only agent observing **tested** causality:

- **Outcome adjudication** at validation checkpoints: "KPI recovered — solution, market, or other?" **Structural bias rule: never pre-fill the flattering answer.** Show DiD evidence and ask cold, or ask the counterfactual ("would this have recovered anyway?"). Anchored self-adjudication converts the theory into institutional self-justification (§9.4).
- **Assumption verdicts** at closeout: each "bets on" assumption → held/broke.
- **Lag capture for free**: VA measures actual time-to-impact; write it onto the lever edge. Lags are what humans estimate worst and VA observes automatically.
- CoI notes during implementation → same extraction as SA comments.

### 5.4 Review governance — no standing queue

Proposals are confirmed inside an **existing ritual** (monthly assessment-run review) with a named owner, or not generated at all. A standing proposal queue with no owner becomes a dead-letter queue (§9.3).

### 5.5 Schema deltas (deliberately minimal)

- `kpi_relationships` + `lag_periods`, `mechanism`, `provenance`, `confidence`.
- New `assumptions` table: `{client_id, scope, text, status, source, expiry, linked situation/solution ids}` (or JSONB on monitoring-profile thresholds for P0).
- Both are tenant tables → **Infra B3 RLS checklist applies** (grant + enable RLS + client_isolation policy + `_RLS_TABLES` in `verify_prod_registry.py`).
- Conflict semantics needed for contradictory edges (open question §12).

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

**Spine** = Value Driver Tree per `principal_lens_weighting_design.md` §7: objective (12C) → apex metric per principal → decomposition branches → KPIs; node color = worst attached situation severity; node weight = value-at-stake. Deterministic layout, DuPont-familiar.

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
| **P2** | SF rejection→constraint extraction + prompt injection | Tenant-isolation tests pass; ≥1 pilot with real SF usage |
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
