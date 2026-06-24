# Decision Studio — Strategic Horizon

**Created:** 2026-06-01
**Version:** 1.0
**Status:** Long-horizon strategy — the layer above the roadmap
**Relationship to other docs:**
- `docs/strategy/roadmap.md` — tactical agent build sequencing and milestone dates (execution layer)
- `DEVELOPMENT_PLAN.md` — phase-level engineering specs (near-term tactical)
- `docs/strategy/exit_strategy.md` — financial exit scenarios (predates the three-layer vision; see §4 for the update)
- `docs/prd/agents/a9_business_optimization_agent_prd.md` — BO Agent (outer loop) full spec
- `docs/prd/agents/a9_innovation_driver_agent_prd.md` — Innovation Agent (discovery layer) full spec

> **Purpose.** The roadmap answers *what gets built next*. This document answers *where this is going and why* — the strategic logic that should outlive any single phase. Test major decisions against this document. When the roadmap and this document conflict, this document describes the intended destination; the roadmap describes the current path to it, and should be reconciled.

---

## 1. The Organizing Spine — Three Strategic Layers

Decision Studio is not a KPI monitoring tool with features bolted on. It is a three-layer strategic intelligence system, where each layer answers a different executive question and each layer's outputs feed the layer below while outcomes feed back upward as learning.

```
INNOVATION LAYER  (A9_Innovation_Driver_Agent)
    "What should we even consider doing?"
    Whitespace discovery · strategic options · innovation portfolio
        ↓ candidate objectives flow down
OUTER LOOP  (A9_Business_Optimization_Agent)
    "Are we executing our declared objectives?"
    Business Objectives · objective health · portfolio optimisation · sequencing
        ↓ objectives steer monitoring priority
INNER LOOP  (SA → DA → MA → SF → VA → PIB)
    "What's breaking and how do we fix it?"
    Detect · diagnose · recommend · measure · brief
        ↑ outcomes (VA attribution, control-group history) feed all layers as learning
```

| Mode | Layer | Executive question | Build status |
|---|---|---|---|
| **Run the business** | Inner Loop | What's breaking and how do we fix it? | Built and in production |
| **Change the business** | BO Agent (outer loop) | Are we executing declared objectives? | Phase A foundation = Phase 12C/12D; Phase B/C 2027–2028 |
| **Reimagine the business** | Innovation Agent | What should we consider doing? | Phase A 2029; Phase B/C 2030–2031 |

**Why this spine matters strategically:**

1. **It is additive, not a rewrite.** The inner loop is the engine. Each higher layer is a steering layer above it. No layer requires rebuilding the one below.
2. **No competitor offers all three.** EPM tools (Anaplan, Workday Adaptive) do "run" badly. Strategy consulting does "change" and "reimagine" manually and expensively. Innovation consulting does "reimagine" with no data foundation. The combined three-layer narrative is the category-defining position.
3. **Each layer expands the buyer and the market** (see §3).
4. **The trust curve gates the ascent** (see §5). You cannot sell or ship the upper layers until the layer below has earned trust.

---

## 2. The Two-Vision Strategic Bet

The single most important unresolved decision. Both are good outcomes; they are different companies requiring different capital, time horizon, and founder risk tolerance.

### Current Vision — Mid-Market FP&A Automation
- **Buyer:** CFO / VP FP&A of $50–500M companies
- **Motion:** Demo → trial → close; 6–12 week cycle; $50K–$150K ACV
- **Scale target:** 500–1,500 customers, $25–75M ARR
- **Competes with:** BI tools, junior FP&A analysts
- **Exit ceiling:** ~$500M
- **Capital to scale:** $5–15M; founder retains ~40%
- **The inner loop alone delivers this.**

### Extended Vision — Continuous Strategic Intelligence Platform
- **Buyer:** PE Operating Partner, CEO/COO, Transformation Officer, eventually Board
- **Motion:** Vision-led enterprise sale; 6–9 month cycle; $500K–$2M+ ACV; PE platform deals (one firm = 20 portfolio deployments under one contract)
- **Scale target:** 50–150 customers, $50–200M ARR
- **Competes with:** Strategy consulting engagements, innovation consulting
- **Exit ceiling:** $1B–$5B (three-layer platform could reach $10–15B)
- **Capital to scale:** $30–60M; founder retains ~15%
- **Requires all three layers.**

### The decision criteria
| Choose **Current** if… | Choose **Extended** if… |
|---|---|
| Exit in 4–5 years | Commit 7+ years |
| Retain 30%+ equity | Accept dilution to ~15% for larger absolute outcome |
| Capital-constrained | Can raise $30–60M |
| Value control and lifestyle | Can recruit/lead enterprise sales |
| Prefer 90% chance of $120M | Prefer 50% chance of $375M |
| Limited PE/enterprise access | Have warm access to a PE operating partner |

### The recommended posture (until the Month 12–18 decision point)
**Run both motions in parallel.** Mid-market revenue funds the team and produces the reference proof points; a top-down PE-targeted motion validates the extended vision. After 18 months, evaluate signal and commit. **Critically: architect today so the extended vision is never foreclosed** — clean protocol boundaries, the Business Objectives registry as a first-class entity, and cross-client data capture (see §7) cost little now and are expensive to retrofit.

> ⚠️ **Caution flagged in prior analysis.** The existing `exit_strategy.md` asserts "actions that maximize Scenario A also maximize B and C." That is true *within* mid-market positioning. It is **not** true when choosing between mid-market and platform positioning — those require genuinely different operational priorities. Do not let the older document's optimism mask a real fork.

---

## 3. Market and Buyer Expansion by Layer

| Layer | Market displaced | Approx. TAM | New buyers unlocked |
|---|---|---|---|
| Inner Loop | FP&A automation, BI tools | $5–10B | CFO, VP FP&A |
| BO Agent | Strategy consulting + EPM | $40B + $7B | CEO, COO, PE Operating Partner, Transformation Officer |
| Innovation Agent | Innovation consulting + corporate venture + ideation tools | $50B + $20B + $2B | CSO, Chief Innovation Officer, Corp Dev, Board |

**Combined coherent TAM: $100B+** under a single product narrative.

**The PE portfolio wedge** is the highest-leverage go-to-market for the extended vision: a PE firm runs the same value-creation playbook across 20 portfolio companies and hires the same consultants per company ($200K–$600K, 12 weeks each). One platform contract replaces ~$4M/year in assessment fees and yields 20 deployments. The PE firm becomes a channel, not just a customer.

---

## 4. Exit Strategy — Updated for the Three-Layer Vision

`exit_strategy.md` (v1.1) priced Decision Studio as AI-native vertical SaaS at $5–15M ARR. That framing is correct for the **current vision** and should be retained as Scenarios A–D. The three-layer vision adds two scenarios the older document cannot see:

### Scenario E — Strategic Enterprise Platform
- **ARR at exit:** $50–150M, NRR 160–180%
- **Multiple:** 15–25× (high NRR + platform positioning)
- **Valuation:** $1B–$5B
- **Acquirers:** Microsoft, Salesforce, ServiceNow, Palantir, large PE
- **Requires:** BO Agent live, ideally Innovation layer in market

### Scenario F — Consulting Firm Defensive Acquisition
- **Thesis:** The extended vision software-displaces strategy and innovation consulting. McKinsey / BCG / Bain / Accenture / Deloitte face structural AI pressure on billable-hour margins. A category-defining displacement platform becomes a **defensive acquisition** — productise the methodology or neutralise the threat.
- **Valuation:** $1B–$2B
- **Why this buyer does not exist for the current vision:** A consulting firm has no reason to acquire a mid-market FP&A tool. It has every reason to acquire the thing eating its discovery-and-diagnosis revenue.

**The NRR-cubed expansion vector** (extended vision): a client lands on the inner loop ($150K), adds the BO layer ($350K), adds the Innovation layer ($600K), then a PE parent rolls it platform-wide ($2M). Each layer is a new expansion vector — the compounding land-and-expand story single-product SaaS cannot tell. NRR is the dominant valuation multiplier; three layers structurally produce the highest NRR.

**Action:** ✅ Done (2026-06-01) — `exit_strategy.md` v1.2 appended Scenarios E and F and cross-references this document.

---

## 5. The Trust Curve — Why the Ascent Is Gated

Full autonomy is a trust and readiness constraint, not a technical one. A first-time AI buyer will not delegate "optimise my enterprise" or "consider entering this market" on day one. Trust is earned layer by layer.

| Window | Trust established | What the system does autonomously |
|---|---|---|
| Months 1–3 | Situation detection (SA) | Flags KPI breaches |
| Months 3–6 | Diagnosis (DA) | Explains root causes |
| Months 6–12 | Recommendation (SF) | Generates solutions; human approves |
| Months 12–18 | Outcome measurement (VA) | Confirms solutions worked |
| Months 18–30 | Objective pursuit (BO Agent) | Prioritises/sequences within declared objectives |
| Year 2–3+ | Strategic discovery (Innovation Agent) | Surfaces options; later, proactive generation |

**Consequences for sequencing:**
- The HITL gates are correct *for now* — they exist because trust is not yet earned, not because the architecture demands them. As trust accrues, autonomy extends; the gates are a dial, not a fixture.
- BO Agent Phase A (12C/12D) deliberately adds the objective layer *without* autonomous decision-making — visible value with zero trust required.
- Innovation autonomy is the longest-horizon deliverable precisely because "consider entering market Y" is a harder trust ask than "fix broken KPI X."

---

## 6. Organizational Preconditions & the Solo Founder's Path

> **Read this before believing any customer number in this document.** Every scenario above the smallest assumes an *organization that does not yet exist*. The ARR and customer figures in §2 and §4 are destinations conditional on building a company — not a plan you execute from the current configuration. This section makes the buried assumptions explicit so no future reader (including the author) mistakes a $3B *destination* for a *strategy*.

### Current reality (as of this writing)
Solopreneur, employed full-time elsewhere, ~100K lines built solo with AI assistance. That is a **product** achievement. Landing 50–150 enterprise accounts is an **organizational** achievement — the two share almost no DNA. Capital was stated in §2 ($5–15M current / $30–60M extended); capital is the *least* of what's missing. The missing thing is the org and the founder-role transition that capital pays for.

### The organization each scenario actually requires

| Scenario | ARR | Implied headcount* | Capital | Founder's job | Fits solo + day job? |
|---|---|---|---|---|---|
| **D: Downside** | $180–360K | 1 (you) | $0 | Builder + everything | Yes — barely |
| **A: Bootstrapped** | $600K–1.4M | 1–3 | $0 | Builder + seller + support | **Only if you go full-time** |
| **B: Funded growth** | $3–10M | 8–20 | $5–15M | CEO; first sales/CS hires | No — full-time + raise + team |
| **C: PE portfolio** | $5–15M | 10–25 | $0–10M | CEO + delivery org for portfolios | No — needs implementation/CS org |
| **E: Strategic platform** | $75–150M | **150–400** | $30–60M | CEO of a real company | No — multi-round, multi-year org |
| **F: Consulting defensive** | $40–120M | **120–350** | $30–60M | CEO + enterprise + delivery | No |

*\*~$250–400K ARR/employee at scale; early stage is far less efficient (~$75–100K/employee), making the early hiring need heavier per dollar of ARR.*

**The mechanics behind "50–150 enterprise customers":** an enterprise AE carries a ~$1–2M quota and closes a handful of $1M deals/year. Adding ~$30M net-new ARR/year (the steady-state growth E/F imply) needs ~20–30 quota-carrying reps **plus** sales engineers, **plus** the CS/implementation org to prevent churn, **plus** SOC 2 / security / legal to clear enterprise procurement. None of it happens on nights and weekends.

**The PE platform wedge is the most org-heavy, not the least.** "One PE firm = 20 portfolio deployments" multiplies *delivery* load even as it shortens *sales* cycles. It requires a delivery organization, full stop.

### The real fork comes long before the Month 12–18 "which vision" decision

The §2 decision point (commit to one vision) is not your first fork. Your first fork is earlier and more personal:

```
Fork 0 (now):  Stay solo + employed
                 → ceiling ≈ Scenario D, maybe a thin slice of A
                 → product can be excellent; revenue stays small by construction

Fork 1:        Go full-time (leave the gig)
                 → unlocks Scenario A and the OPTION on B/C
                 → requires runway + accepting the builder→operator shift

Fork 2:        Raise + hire (become a CEO)
                 → unlocks B/C and the OPTION on E/F
                 → this is where "50–150 customers" first becomes physically possible
```

Everything about the extended vision — the three-layer platform, the $1–5B exit, Scenarios E/F — **lives on the far side of Fork 2**, two decisions past where the founder stands today.

### Correction to the §2 "run both motions in parallel" advice
That advice silently assumed a team that can staff two go-to-market motions. **For a solo founder with a day job it is incoherent** — you cannot run two motions; while employed you can barely run one. Treat "run both motions in parallel" as advice that only becomes valid *after Fork 2*. Before then, the realistic motion count is zero-to-one.

### What a solopreneur-with-a-job actually optimizes for
A legitimate, good path that requires *none* of the headcount above:
- Reach a **small number of paying customers** — proof, not scale.
- Keep the **product sharp** and the **cross-client data structure captured** (§7 H2-1) — the asset that compounds regardless of org size.
- Build the **evidence** (VA outcome corpus, reference stories) that would justify Fork 1, or that makes an **acqui-hire / IP sale (Scenario D/A)** attractive *without ever building the org*.

Scenario D and a thin Scenario A are honest, reachable outcomes from the current configuration. Everything else is a decision to become a different kind of operator — worth wanting, but it must be *chosen*, not assumed.

---

## 7. Horizon Bets — Opportunities Beyond the Current Frame

These emerged from a deliberate examination of where founder experience (consulting: deliverable-based, finance-domain, analysis-of-historical-data) systematically does not look. They are **explorations to stage and protect optionality for**, not committed builds. Staged as Horizon 2 (bank now / document) and Horizon 3 (preserve optionality).

### H2-1 — Cross-Client Data Network Effect *(highest-regret-if-ignored)*
Every assessment generates calibrated monitoring profiles, IS/IS NOT segment archetypes, solution-success patterns, and VA outcomes. Today that intelligence is trapped per-tenant. **Aggregated and anonymized, it becomes a benchmark-and-playbook corpus no consultant can build** (confidentiality and structure prevent cross-client pooling). Year 1 it's a tool; year 5 it's an oracle a new entrant cannot replicate without the history.
- **Action now:** Begin *capturing* the cross-client dataset structure even before productising it. The data not collected now is the moat that cannot be built later. **This is the single most important architectural decision in this document.**
- **Strategic note:** This is the true network effect and the structural answer to "what stops Microsoft." Reconciles with the existing per-client "compounding moat" note by extending it across tenants.

### H2-2 — The Execution Gap (approve → execute)
The loop today is detect → diagnose → recommend → **approve → track**. It never *acts*. Closing approve→execute (ERP write-back, ticketing, workflow/RPA triggers, owned-task follow-through) turns "decision intelligence" into "autonomous operations" — a larger category, a COO buyer, and a system-of-action position that does not get ripped out.
- **Inherited blind spot:** Consultants stop at the recommendation deck; the architecture inherited the stop.
- **Action:** Document as the next category beyond decision intelligence; sequence after inner-loop trust and after the BO Agent. High build + trust cost — deliberate, not immediate.

### H2-3 — Simulation / Counterfactual Sandbox (digital twin)
DA analyses the past; VA projects committed solutions forward. The BO Agent builds a causal KPI map and trajectory forecasting. **Combine those and you have a what-if simulator you have not named as a product:** "what happens to my objective portfolio if I cut SG&A 10% and raise prices 3%?" — run before committing a dollar.
- **Why it's nearly free:** The ingredients (causal map + trajectory forecasting) are already on the BO Agent roadmap. Name the simulator as a deliverable so that work feeds it.
- **Demo value:** A wow no EPM tool can match. Likely the fastest path to a differentiated demo.

### H2-4 — Verifier & Red-Team Agents *(cheap, available now)*
Agentic patterns beyond the debate pattern already used in SF:
- **Verifier / grader agent** — LLM-as-judge scoring every SA/DA/SF output for quality before it reaches the human. A quality moat. (This is what the manual pre-mortem discipline already does — productise it.)
- **Adversarial / red-team agent** — argues *against* the recommended solution at the HITL gate. Directly serves the "cognitive dissonance is the valuable moment" philosophy — the gate was designed for dissonance but not staffed with an agent that creates it.

### H3-1 — Platform Inversion (be the substrate)
Deepest founder assumption: "we are the experts who design the analysis." The platform opportunity inverts it: Agent9 becomes the **substrate** (registry + A2A protocol + agent lifecycle + LLM routing + HITL framework) on which clients and partners build their own vertical agents. AWS-vs-application. The consulting partner builds industry-specific agents on the rails and keeps margin. **Dilutes focus if chased early; the difference between $500M and $5B if preserved.** Keep protocol boundaries clean now; do not build yet.

### H3-2 — Outward Agent Interoperability & Ambient Delivery
- **External A2A/MCP:** Internal A2A exists. The industry is standardizing inter-company agent protocols. Agent9 output consumed by *other* companies' agents (your supplier's agent ↔ your procurement agent). MCP was researched inbound (data) but not outbound (agent interop).
- **Ambient delivery:** The PIB assumes a human reading a briefing. The same intelligence could be an API others poll, a Teams/Slack presence, a voice agent, or embedded widgets at the point of decision. "Deliver the report to the executive" is the consulting frame; "put intelligence where the decision is made" is the product frame.

### H3-3 — Reflexive / Non-Business-KPI Applications
The detect→diagnose→solve→verify engine works on any metricized system: ops/infra monitoring, supply chain, and notably **monitoring the platform's own agents**. DevOps incident management is literally the same pattern. "Domain-agnostic" is understood; how far it reaches may be underexploited.

### Horizon-bet triage
| Bet | Stage | Why |
|---|---|---|
| H2-1 Cross-client data | **Bank now** — capture structure immediately | Highest regret if ignored; the real moat |
| H2-4 Verifier/red-team | **Bank now** — small builds | Cheap, immediate quality + demo + philosophy fit |
| H2-3 Simulation sandbox | **Document as vision** | Ingredients already on BO roadmap |
| H2-2 Execution gap | **Document as vision** | Next category; high build/trust cost |
| H3-1 Platform inversion | **Preserve optionality** | Huge but focus-diluting; protect architecture |
| H3-2 / H3-3 | **Preserve optionality** | Frontier-tracking; don't foreclose |

---

## 8. What This Means for Decisions Today

**The honest framing (per §6):** from the current solo + employed configuration, the reachable outcomes are Scenario D and a thin Scenario A. Everything else is gated on Fork 1 (go full-time) and Fork 2 (raise + build a team). The actions below are the ones that keep the larger options *open* at near-zero cost without requiring those forks yet — plus the one go-to-market caveat that only applies after Fork 2.

1. **Capture cross-client data structure now** (H2-1) — the one irreversible decision, and it requires no org. The asset compounds regardless of company size.
2. **Keep protocol boundaries clean** — preserves platform inversion (H3-1) and agent interop (H3-2) at near-zero cost.
3. **Ship the Business Objectives registry (12C/12D) as a first-class entity** — the data foundation for the entire outer loop and a prerequisite the simulation sandbox (H2-3) also needs.
4. **Build verifier/red-team agents opportunistically** (H2-4) — cheap quality wins that reinforce the HITL philosophy.
5. **Reach a small number of paying customers — proof, not scale.** This is the realistic solo objective and the evidence that would justify Fork 1. *"Run both go-to-market motions in parallel" applies only after Fork 2 (§6) — it is incoherent for a solo founder with a day job; before Fork 2 the realistic motion count is zero-to-one.*
6. **Treat the HITL gates as a dial, not a fixture** — design for progressive autonomy as trust accrues.

---

## 9. Reconciliation Backlog (documents that now conflict or lag)

| Document | Issue | Action |
|---|---|---|
| `docs/strategy/roadmap.md` | ⚠️ **Open.** BO Agent (lines 202–205) and Innovation Agent (207–210) still described in the *old* "process-improvement / innovation-pipeline" framing in the body | Pointer + conflict banner added at top of roadmap (2026-06-01). **Still to do:** rewrite the two Phase 3 agent body descriptions to match the rewritten PRDs |
| `docs/strategy/exit_strategy.md` | ✅ **Done (v1.2, 2026-06-01).** Scenarios E/F appended; positioning-fork caveat added; cross-references this doc | — |
| `docs/product/decision_studio_vision.md` | ✅ **Partly done (2026-06-01).** H1 retitled to its actual content (situation model + API contract); header banner redirects strategic-vision readers here; staleness flags added (Streamlit, YAML fallback, role lookup) | **Still to do (optional):** rename the file to `situation_model_api_contract.md` + grep inbound links |
| `memory/project_product_direction.md` | ✅ **Done (2026-06-01).** Resolved: single-principal is an inner-loop MVP constraint; BO/Innovation layers are multi-stakeholder as trust accrues. *(Pending founder confirmation — see open question below)* | — |

**Open question for founder alignment:** the `project_product_direction` resolution assumes the upper layers *should* be multi-stakeholder (Board/PE/CSO buyers, per the BO/Innovation PRDs). If the actual conviction is "never expose to a board, even long-term," the board/PE buyer personas must instead be **removed** from those PRDs and the §3 buyer expansion revised. This is the one reconciliation that changes product scope, not just documentation.

---

## 10. The One-Sentence North Star

> Decision Studio is building the continuous strategic intelligence platform that lets an enterprise run, change, and reimagine itself — autonomously detecting what's breaking, executing toward declared objectives, and discovering what to pursue next — grounded in the company's own data and compounding in value with every assessment it runs.

Everything in the roadmap should ladder up to that sentence. If a build does not advance one of the three layers, the cross-client moat, or the trust curve that unlocks autonomy, question whether it belongs.
