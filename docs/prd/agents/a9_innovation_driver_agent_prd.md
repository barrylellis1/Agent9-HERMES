# A9_Innovation_Driver_Agent PRD

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2026-08-02
Status: Not scheduled. Phases gated on observable conditions, not dates — see "Phasing".
-->

## Overview

**Purpose:** Support executive and founder ideation sessions. When an idea surfaces in a brainstorming, innovation, or design-thinking session, the agent captures it, frames it quickly, and supplies the internal and external evidence needed to judge it while the conversation is still live. **The agent does not generate strategy. It makes the team's own thinking faster and better grounded.**

**Agent Type:** Ideation Session Support Agent
**Version:** 0.3 (Session Support Repositioning)

The Innovation Driver Agent operates at Layer 4 of Decision Studio's framework, but its role there is different in kind from the layers below it. Layers 1–3 are analytical: SA detects, DA diagnoses, BO pursues declared objectives. All three operate on the business as it exists. Layer 4 serves the human act of imagining what does not yet exist — and the imagination is the executives', not the agent's.

**What changed from v0.2, and why.** The previous version framed this agent as autonomous discovery: mining operational data for "whitespace," inferring strategic options, and surfacing them for approval. That was rejected for two reasons.

First, it mislocated the source of ideas. Genuine product and service innovation draws inspiration from anywhere — a customer complaint, a technology that just became affordable, something an executive saw in an unrelated industry twenty years ago, a competitor's abandoned attempt, a regulatory shift. That space cannot be enumerated, and an agent mining internal KPI data will never reach most of it.

Second, it inverted the trust problem. **An agent that proposes strategy fails by being wrong**, which is expensive and is precisely the fear that keeps such a tool out of the room. **An agent that supports a human's idea fails by being unhelpful** — someone ignores a suggestion and the session continues. Trust then accrues per useful contribution instead of having to be granted up front. That is the only version a leadership team is likely to admit to a strategy session, and admission to the room is the binding constraint on this product.

Building the causal model of business performance — the work v0.2 confused this with — belongs to onboarding and to the FP&A analysts and executives who continuously test and refine it. It is not this agent's job.

---

## Executive Summary

Ideation in real organisations happens in rooms — offsites, strategy days, design-thinking workshops, a whiteboard after a customer visit. Ideas arrive half-formed, get talked over, and most evaporate. The ones that survive do so because someone in the room could say, quickly and credibly, *"that's interesting, and here's why it might work here."*

That sentence is what this agent produces.

| Mode | Agent | Question | Who supplies the thinking |
|---|---|---|---|
| **Run the business** | Inner Loop (SA→DA→SF→VA) | What's breaking and how do we fix it? | The system |
| **Change the business** | Business Optimization Agent | Are we executing declared objectives? | The system, within declared goals |
| **Reimagine the business** | Innovation Driver Agent (this) | Is this idea worth pursuing, and what do we know about it? | **The executives. The agent supplies evidence.** |

The distinction in the last column is the product. The other two agents think and present conclusions. This one listens, frames, and equips.

**Why Agent9 specifically can do this.** In a live session, the valuable contribution is not a good idea — the people in the room already have those. It is instant, accurate recall of what the organisation already knows, joined to what is happening outside it. Agent9 holds both: a registry of KPIs, owners, channels, business processes and their actual performance, plus the Market Analysis agent's external signals. A consultant in the room does not have the internal half. A general-purpose LLM has neither.

**Worked example.** An executive says: *"What if we sold uptime to fleets instead of gallons?"* Within seconds the agent can put up: this client already tracks `service_revenue` with a named owner, so the idea is not greenfield; the Service Centers Division runs a positive margin delta; but `service_revenue` has no causal drivers mapped, so nothing in the model yet says what moves it; base oil is 50–60% of COGS with a confirmed one-month pass-through lag, so selling uptime rather than volume changes who carries that exposure; and externally, extended drain intervals are already compressing volume, which is what makes the idea timely rather than speculative. Then: what would have to be true, and what is the smallest test.

No consultant in the room has the first half of that. No general model has any of it.

---

## Market Positioning

### Positioning discipline — this agent does not displace innovation consulting

Earlier drafts of this PRD claimed displacement of IDEO, frog, BCG Digital Ventures and McKinsey Digital against a "$70B+ addressable market." **That claim is withdrawn.** It contradicts the positioning discipline established in `docs/architecture/theory_layer_design.md` §3.4 and §11, which is deliberate and applies here too:

> The competitor is Excel and the monthly variance meeting, **not MBB**. Never claim consulting takeover; MBB is the price anchor and a plausible acquirer or channel.

Those two stances imply opposite go-to-market motions — you cannot simultaneously court the large firms as channel partners and market yourself as their replacement. The theory-layer framing is the newer and more defensible one, and it governs.

The honest description of this agent is narrower and easier to defend: **a very well-briefed analyst in the room, with instant recall of the organisation's numbers and the outside market.** That is a real and currently unfilled role. It does not require anyone to believe an AI replaces a design-thinking practice.

### What this agent is and is not adjacent to

| Category | Example | Relationship to this agent |
|---|---|---|
| Innovation consultancies | IDEO, frog, BCG DV | **Not competing.** They run the session and bring method; this agent supports whoever runs it. A consultant-led workshop is a plausible deployment context, not a target to displace. |
| Ideation portals | Brightidea, IdeaScale | Adjacent. They collect ideas asynchronously at scale; this agent works a small number of ideas deeply, live, with evidence attached. |
| Meeting assistants | Otter, Fireflies, Copilot recall | Nearest functional neighbour, and the honest comparison. They transcribe and summarise. **None can say what your service revenue actually did last quarter or which channel carries your margin** — that requires the registry. |
| Strategy/BI dashboards | — | Answer questions you already knew to ask. This agent answers a question raised thirty seconds ago in conversation. |

### Why now

The enabling capability is not idea generation — the people in the room supply that. It is **fast, grounded synthesis on demand**: taking an unstructured spoken idea, working out which parts of a business registry are relevant, and returning a short evidence block in the time a conversation allows. LLMs became capable of that recently; the registry and market-signal plumbing that make the internal half possible are already built.

### Key ICP Stakeholders

Note the distinction v0.3 introduces between **who runs the session** and **who buys**. The person typing ideas into the panel in V1 is usually a facilitator or chief of staff, not the buyer.

| Stakeholder | Role | What they care about | From |
|---|---|---|---|
| **Facilitator / Chief of Staff** | Operator | Not slowing the room down; capturing what was said accurately | V1 |
| **CEO / Founder** | Participant | Their idea taken seriously and pressure-tested fast; not being led | V1 |
| **Chief Strategy Officer** | Buyer | Ideas surviving past the offsite; a record of what was considered and why it was parked | V1 |
| **Chief Innovation Officer** | Buyer | Pipeline visibility; kill discipline | V4 (needs portfolio memory) |
| **Chief Finance Officer** | Gatekeeper | Rigour around speculative spend; that an idea was evidenced before it consumed budget | V2 (needs the session artefact) |
| **Corp Dev / M&A** | Occasional | Build-vs-buy framing on ideas raised | V4 |
| **PE Operating Partner** | Occasional | Top-line growth options beyond cost reduction | V4 |

---

## Strategic Context

### Three-Layer Strategic Architecture

Decision Studio's intelligence flows through three levels of abstraction. Each layer answers a distinct executive question and produces outputs that feed both upward (as learning signals) and downward (as constraints and context).

```
LAYER 4 — INNOVATION DRIVER AGENT (Ideation Support)
    "Is this idea worth pursuing, and what do we already know about it?"
    The IDEA comes from the humans in the room. The agent captures,
    frames, and evidences it — internal (registry) + external (MA).
        ↓ ideas the room chooses to pursue can become BO Objectives
        ↓ registry + market context flow UP to ground each idea
        
LAYER 3 — BUSINESS OPTIMIZATION AGENT (Strategic Execution)
    "Are we executing declared objectives?"
    Objective-directed KPI monitoring, conflict detection, sequencing, portfolio optimization
        ↓ objectives flow to inner loop as monitoring priorities
        ↓ outcomes flow back from inner loop as performance signals
        
LAYER 2 — DEEP ANALYSIS AGENT (Diagnostic Rigor)
    "Why did the KPI move?"
    IS/IS NOT variance analysis, dimensional drivers, change-point detection
        ↓ diagnostic context flows to SF Agent, BO Agent, and Innovation Agent
        ↑ situation signals flow back from Layer 1
        
LAYER 1 — SITUATION AWARENESS AGENT (Anomaly Detection)
    "What's breaking and what's working?"
    KPI monitoring, anomaly detection, opportunity identification
        ↑ facts flow up to all upper layers
```

The three layers operate in concert:
- **Layer 1 detects.** SA identifies KPI breaches and opportunities without judgment.
- **Layer 2 diagnoses.** DA provides statistical rigor: which dimensions moved? with what confidence? what patterns persist?
- **Layer 3 pursues.** BO Agent steers the system toward declared objectives, managing portfolio conflicts and sequencing.
- **Layer 4 equips the people who imagine.** The Innovation Agent does not discover possibilities; executives raise them. The agent makes each one immediately arguable by attaching what the organisation already knows and what is happening outside it.

The inner loop (Layers 1–2) operates continuously on the status quo. The outer loop (Layer 3) constrains and prioritises the inner loop. Layer 4 is the only layer where the *input* originates with a human rather than with data — which is why it is a support agent rather than an analytical one.

---

## Architectural Role — Fourth Layer Wrapping Three Loops

The Innovation Driver Agent is positioned as a wrapper around all three lower layers, with read access to and write access to distinct outputs:

### Reads From (Input Signals)

- **DA Agent outputs:** 
  - IS NOT segments where bright spots persist across time (persistent outliers that suggest replication candidates)
  - Cross-dimensional pattern analysis (when one dimension moves, what else correlates?)
  - Change-point analysis (inflection moments that create discontinuities)

- **VA Agent solution success patterns:**
  - Which solution archetypes delivered impact?
  - What's the pattern of successful solutions? (cost reduction vs. revenue growth vs. capability building)
  - Can the same archetype apply to different business processes?

- **MA Agent market intelligence:**
  - Competitive signals (what are peers doing?)
  - Industry trend emergence
  - Regulatory or market structure shifts
  - Technology emergence in adjacent domains

- **BO Agent objective portfolio:**
  - Currently active objectives
  - Objective success/failure patterns (what types of objectives succeed?)
  - Objective abandonment reasons (why do some objectives get killed?)

- **Principal Context Agent:**
  - Decision style and risk appetite
  - Business process hierarchy and governance
  - Historical strategic priorities (to avoid re-proposing rejected ideas)
  - Stakeholder network and influencers

- **KPI Registry:**
  - Current measurement coverage (which operational areas are unmeasured?)
  - KPI definitions and business meaning
  - Peer benchmarks (when available — Phase 12A benchmark library integration)

### Writes To (Output Channels)

- **Innovation Pipeline Store** (new Supabase table):
  - Strategic option cards with stage, evidence, confidence, impact estimates
  - Tracked options with full decision history and rejection reasons

- **BO Agent as Business Objective candidates:**
  - An idea the room decides to pursue can be handed to BO as a candidate objective — **always by explicit human action, never auto-elevated.** Nothing this agent produces is a conclusion; auto-promotion would reintroduce exactly the "agent decides strategy" posture v0.3 removed.

- **PIB "Strategic Options" section:**
  - Top 3–5 options from most recent assessment cycle
  - One-sentence hypothesis + evidence type + confidence level per option
  - Single-use token for quick elevation to BO Agent formal objective

- **HITL approval gates:**
  - Principal review and acceptance/rejection of surfaced options
  - Option prioritization and kill discipline

---

## Phasing — gated on evidence, not dates

Earlier drafts assigned calendar dates (Phase A 2029, B 2030, C 2031+). Those are withdrawn. They were never schedule decisions; they were guesses about when enough usage would exist, expressed in time. Stating a date makes a dependency look like a plan and ages badly in either direction — if adoption is fast the roadmap looks sandbagged, if slow it looks like a slip.

Each phase is gated on an observable condition instead:

| Stage | What the agent does | Gate to begin |
|---|---|---|
| **V1 — Facilitator capture** | A human types ideas into a side panel during a session; agent returns an evidence block per idea | ≥1 client with a populated registry (KPIs, owners, business context) and a leadership team willing to pilot in a real session |
| **V2 — Session artefact** | Post-session summary: every idea raised, its evidence block, what the room concluded, what was parked | V1 used unprompted in ≥3 sessions by the same team — i.e. someone asked for it rather than being asked to try it |
| **V3 — Ambient capture** | Agent listens and extracts candidate ideas itself, with a human confirming what counts | V2 demonstrating that the *evidence* is the valued part, plus an explicit privacy/consent posture agreed with the client |
| **V4 — Portfolio memory** | Idea pipeline across sessions; resurfaces parked ideas when conditions change; kill discipline | A client with enough session history that "we discussed this eighteen months ago" is a real event |

**Why this ordering.** The hardest technical problem (deciding which utterances are ideas) and the hardest social problem (consent to record a strategy session) both sit in V3. The most valuable capability — grounded evidence on demand — sits in V1 and needs neither. Building V1 first tests the actual hypothesis, *is instant evidence on a raw idea useful in the room?*, at a fraction of the cost.

It also resolves an honest unknown. We do not know the social dynamics of a given leadership team, or how a team would receive a tool in a room where people are thinking out loud. **You cannot design an interaction model for a dynamic you have not observed.** V1 is cheap enough to be a way of finding out.

---

## Functional Requirements

### V1 Capabilities — Facilitator Capture + Evidence Block

The unit of work is **one idea, raised by a human, evidenced in the time a conversation allows.**

#### 1. Idea capture (human-driven)

A facilitator, chief of staff, or any participant types an idea into a side panel as it surfaces. Free text, one or two sentences, as spoken.

Deliberately **not** an AI extraction step in V1. Deciding which utterances in a brainstorm are ideas — as opposed to reactions, jokes, tangents, and half-sentences — is the hardest problem in the whole concept, and getting it wrong is worse than silence: a panel that keeps surfacing evidence for things nobody proposed will be closed within one session. A human in the room already solves this problem for free.

The capture field imposes no structure and no category. See §*Inspiration is not typed* below.

#### 2. The evidence block (the core output)

Per captured idea, within a few seconds, four parts:

**a. What we already know internally** — resolved against the registry, not generated:
- Do KPIs already exist for the area the idea touches? Are they owned, and by whom?
- What has their recent performance been?
- Are there causal relationships mapped that the idea would strengthen or contradict?
- Which business processes, channels, or data products are implicated?

The value here is *disconfirming as often as confirming*. "You already track this and it has been flat for six quarters" is more useful in a room than a supportive statistic.

**b. What is happening outside** — via the Market Analysis agent:
- Relevant market movement, competitive behaviour, regulatory or technology shifts
- Explicitly including whether this is already table stakes. **An idea three competitors already ship is catch-up, not innovation, and must be labelled as such.** Failing to say so is the fastest way to lose the room's trust.

**c. Framing** — turning a spoken fragment into something arguable:
- The idea restated as a claim that could be false
- What would have to be true for it to work (the preconditions)
- What would be the smallest test

**d. Honest gaps** — what the agent could not evidence, stated plainly. An evidence block that is confident about everything is not credible. "We have no data on service margin at fleet scale" is a legitimate and useful contribution.

#### 3. Inspiration is not typed

The v0.2 model carried `evidence_basis: Literal["whitespace", "pattern_transfer", "market_signal", "hybrid"]`. **That enum is removed.**

Elsewhere in Agent9, closed `Literal` sets are exactly right — `relationship_type`, `provenance`, `causal_rung` are all constrained deliberately, and this document endorses that discipline. Here the same instinct is actively harmful. Inspiration for a new product or service can come from anywhere: a customer complaint, a technology that just became affordable, a mechanism from an unrelated industry, a competitor's abandoned attempt, a regulatory change, a demographic shift, something someone noticed on holiday. Any enumeration will be incomplete, and an incomplete enumeration in a data model quietly becomes a ceiling on what the product can represent.

Provenance of an idea is captured as free text (`inspiration_note`) — where it came from, in the words of whoever raised it — because that context is useful later and cannot be reconstructed from a category.

#### 4. Stress-testing (multi-persona, retained from v0.2 with a changed subject)

The Conservative CFO / Aggressive CEO / Pragmatic COO persona debate is retained, but it now argues about **the executive's idea** rather than evaluating the agent's own proposal. This is a better fit for the mechanism than its original use: the personas are a device for surfacing objections a room might not voice, not a substitute for judgment.

Invoked on request, not automatically. Mid-session, it is usually an interruption.

#### 5. Session memory

Ideas persist with their evidence blocks, attributed to who raised them and when. This is the smallest useful unit of institutional memory for ideation, and it addresses the failure this product exists to fix: ideas raised in a room, never written down, gone by the next quarter.

No portfolio management, no stage gates, no kill discipline in V1 — those are V4 and require a client with enough history for them to mean anything.

#### 6. Data model

```python
class InnovationIdea(A9AgentBaseModel):
    idea_id: str
    client_id: str                                  # mandatory tenant key
    session_id: Optional[str]                       # groups ideas from one session
    raw_text: str                                   # as typed, unedited
    raised_by: Optional[str]                        # principal_id, when known
    inspiration_note: Optional[str]                 # free text — see §3, deliberately not an enum
    framed_claim: Optional[str]                     # agent's restatement as a falsifiable claim
    preconditions: List[str]                        # what would have to be true
    smallest_test: Optional[str]
    internal_evidence: List[Dict[str, Any]]         # registry-resolved, each with a source reference
    external_evidence: List[Dict[str, Any]]         # MA-sourced, each with a source reference
    already_table_stakes: Optional[bool]            # competitors already do this
    evidence_gaps: List[str]                        # what could not be evidenced — see §2d
    persona_debate_summary: Optional[str]           # populated only when stress-test requested
    status: Literal["captured", "parked", "pursuing", "discarded"] = "captured"
    created_at: str
```

Notes on the shape:

- `raw_text` is stored **unedited**. The agent's restatement lives separately in `framed_claim` so the original phrasing is never lost — an executive should be able to see their own words, not a paraphrase.
- Every entry in `internal_evidence` / `external_evidence` carries a source reference. Evidence a participant cannot trace back is not evidence.
- `status` is deliberately four flat values, not a stage pipeline. Pipelines imply a managed process this agent does not run in V1.
- No `confidence: float`. A number implies a calibration that does not exist for a two-sentence idea heard once, and would be false precision of exactly the kind this codebase avoids elsewhere.

### Later capabilities — portfolio management (maps to V4 — Portfolio Memory)

> **⚠ Written under v0.2 and not yet revised for v0.3.** The mechanics below (pipeline stages, kill discipline, portfolio health metrics) remain broadly sound as *portfolio memory* over ideas the room raised. But they were written assuming the agent generated the options itself, so any language implying agent-originated candidates, autonomous elevation, or confidence scoring of its own proposals is superseded by the Overview and V1 sections above. Revise when V4 is actually scheduled — not before, since the shape should follow what V1/V2 usage reveals.

#### 7. Innovation Pipeline Stages

Establish formal stage model for tracking option lifecycle:

- **Stages:**
  - `discovered` — Option identified by system, not yet reviewed by principal
  - `flagged` — Principal has reviewed and acknowledged; marked for potential pursuit
  - `incubating` — Assigned an owner; preliminary investigation underway
  - `prototyped` — Initial prototype or pilot plan exists
  - `piloted` — Limited-scope pilot executing
  - `scaling` — Pilot succeeded; scaling to full deployment
  - `killed` — Formally terminated with documented reason

- **Stage Transitions:** Each transition from one stage to the next requires HITL acknowledgement or explicit owner action.

- **Persistence:** Stage history tracked in `innovation_options` table; full audit trail maintained.

#### 8. Kill Discipline

Enforce decision discipline on incubating options:

- **Stale Incubation Rule:** If an option remains in `incubating` stage > 90 days without progression, system surfaces in PIB: "Option X has been incubating since [date] — require extension of decision or termination."

- **Kill Reason Taxonomy:** When options are killed, required to specify reason:
  - `insufficient_evidence` — Analysis suggested lower impact than required
  - `capability_gap_too_wide` — Build requirements prohibitive
  - `strategic_misalignment` — No longer fits declared objectives
  - `market_shift` — External conditions changed
  - `execution_failed` — Pilot did not validate hypothesis
  - `other` — With free-text explanation

- **Meta-Learning:** Aggregate kill reasons to surface patterns: "20% of internally-sourced innovations are killed due to strategic misalignment — consider filtering for strategy alignment earlier."

#### 9. Innovation Portfolio Health Metrics

Compute portfolio-level health indicators:

- **Pipeline Depth:** Count of options by stage. Example output: "5 discovered, 3 flagged, 1 incubating, 0 piloted, 0 scaling" — indicates strong upstream but weak downstream (consider acceleration).

- **Velocity:** Average time between stage transitions. Example: "Average time from flagged → incubating is 3 weeks; incubating → piloted is 8 weeks."

- **Kill Rate:** % of incubating options that reach kill decision (vs. stalling indefinitely). Healthy kill rate is 30–50% (discipline without excessive risk aversion).

- **Scale Rate:** % of piloted options that progress to scaling. Tracks actual validation success.

- **Innovation Portfolio ROI:** For options that reached `scaling`, use VA's DiD attribution methodology (adapted for innovation outcomes) to compute actual ROI realized.

- **Surface in PIB:** "Innovation portfolio health: 40 options in pipeline, 3 scaled this cycle, generating $2.1M incremental value; kill rate 35% (healthy discipline)."

#### 10. Meta-Learning Across Innovation Sources

Track which sourcing method produces the highest success rate:

- **Sourcing Attribution:** Each option tagged with primary source (whitespace | pattern_transfer | market_signal | hybrid).

- **Success Correlation:** For each source type, track:
  - % of options that reach `piloted` stage
  - % that progress to `scaling`
  - Average realized ROI (from VA data)
  - Kill rate by reason

- **Trend Surfacing:** "Pattern transfer innovations have 3× higher success rate (60% → scaling) vs. market signal innovations (20% → scaling). Consider doubling down on internal pattern extraction."

- **Sourcing Weight Adjustment:** Innovation Agent adjusts its own sourcing weights in subsequent cycles based on meta-learning results.

---

### Later capabilities — cross-loop learning and proactive surfacing

> **⚠ Written under v0.2 and not yet revised for v0.3 — treat with particular caution.** "Autonomous generation" and "proactive option generation" describe the agent proposing strategy unprompted, which is the exact posture v0.3 rejected on trust grounds (see Overview). If any of this is revived it must be reframed as *resurfacing ideas the room already raised* when conditions change — memory, not invention. Do not carry the autonomy framing forward unexamined.

#### 11. Cross-Loop Learning and Reapplication

Successful innovations that scaled become patterns for automatic reapplication in similar future contexts:

- **Success Pattern Extraction:** When an innovation reaches `scaling` and VA confirms positive DiD attribution, extract the underlying pattern:
  - What was the root cause it addressed?
  - What dimensions/segments did it target?
  - What were the prerequisites?

- **Automatic Reapplication Candidates:** When future SA assessments identify the same root cause in similar segments, surface: "We previously solved this with Innovation Option X — consider applying the same mechanism here."

- **Confidence Escalation:** Innovations with proven track record can auto-escalate from discovered → flagged without principal review (within trust policies).

- **Failed Innovation Learning:** When pilots are killed due to failed hypothesis, DA Agent performs root cause analysis on the failure:
  - Was the hypothesis wrong?
  - Did execution fail?
  - Did external conditions change?
  - Extract lessons for future option generation.

#### 12. Proactive Option Generation

Instead of surfacing options only in regular PIB cycles, trigger autonomous generation when conditions change:

- **Trigger Events:**
  - **Significant market shift detected by MA:** "Competitive intelligence suggests industry shift toward X — 3 options generated for your consideration."
  - **BO Agent objective marked DEGRADED:** "Your objective for EBITDA improvement is falling behind plan. 2 new options identified that could help accelerate it."
  - **Completion of any objective** (success or failure): "Your revenue growth objective completed ahead of plan. Here are 3 options to consider for next growth cycle."
  - **Emergence of persistent bright spots in DA:** "Financial Services division shows consistent 25% margin premium vs. baseline. 2 options to replicate this model elsewhere."

- **Output:** Proactive option sets surface without principal request, framed as "Given [trigger condition], here are options to consider."

- **No Default Action:** Options never auto-progress beyond `discovered` stage without explicit principal review.

#### 13. Continuous Strategic Posture Assessment

Generate quarterly "Strategic Posture Report" summarizing the system's complete strategic intelligence:

- **Contents:**
  - Objective portfolio health (Phase A BO Agent data)
  - Innovation pipeline status (V2 portfolio metrics)
  - KPI performance trends (Layer 1 SA data)
  - Root cause landscape (Layer 2 DA dimensional patterns)
  - Solution success patterns (Layer 2 VA data)
  - Market positioning (Layer 4 MA data)
  - Whitespace and opportunity summary
  - Recommended strategic focus for next quarter

- **Narrative:** LLM-synthesized report that reads like a strategy briefing from a consulting firm, but grounded entirely in the client's operational data.

- **Frequency:** Quarterly, automatically generated and surfaced to CEO/CFO/Strategy team.

- **This is the "Continuous Strategic Intelligence" artifact** that would typically require a $500K–$3M engagement to produce. Here it's generated autonomously.

---

## Input Requirements

```python
class InnovationDiscoveryInput(A9AgentBaseModel):
    """Innovation discovery and option generation request."""
    
    client_id: str                                  # Tenant identifier
    principal_id: str                               # Principal making request (optional for autonomous generation)
    discovery_scope: Literal["whitespace_only", "pattern_transfer_only", "market_signal_only", "comprehensive"] = "comprehensive"
    business_process_filter: Optional[List[str]] = None  # Constrain to certain processes (None = all)
    exclude_objective_ids: Optional[List[str]] = None    # Skip areas already covered by active objectives
    exclude_previously_rejected_ids: Optional[List[str]] = None  # Don't re-propose rejected options
    min_confidence: float = 0.5                    # Only surface options ≥ this confidence
    max_options_returned: int = 10                 # Cap number of options in response
    trigger_event: Optional[str] = None            # Proactive generation trigger (market_shift | objective_degradation | objective_completion | bright_spot_emergence)
    trigger_context: Optional[Dict[str, Any]] = None  # Context for the trigger event
```

---

## Output Specifications

```python
class InnovationDiscoveryResult(A9AgentBaseModel):
    """Strategic option generation and discovery results."""
    
    request_id: str                                 # Request correlation ID
    options: List[InnovationOption]                 # Generated strategic options
    discovery_summary: str                          # LLM-generated narrative explaining what was found and why
    methodology_notes: str                          # Audit trail of sources consulted
    confidence_justification: str                   # Why these confidence scores are appropriate
    
    # Portfolio state (V2+)
    portfolio_state: Optional[InnovationPortfolioSnapshot] = None
    # {total_options, by_stage: {discovered, flagged, incubating, ...}, pipeline_depth, velocity_metrics, kill_rate}
    
    # Meta-learning (V2+)
    sourcing_effectiveness: Optional[Dict[str, float]] = None
    # {whitespace: 0.65, pattern_transfer: 0.73, market_signal: 0.42} (success rates)
    
    # Proactive generation context (V3+)
    trigger_event_summary: Optional[str] = None
    
    # HITL
    human_action_required: bool = False
    human_action_type: Optional[str] = None         # "review" | "prioritization" | "kill_decision"
    human_action_context: Optional[Dict] = None
```

---

## Integration Points

- **Deep Analysis Agent:** IS NOT segments, dimensional drivers, change-point data for whitespace and pattern discovery
- **Value Assurance Agent:** Solution success patterns, realized ROI for meta-learning
- **Market Analysis Agent:** Competitive signals, industry trends, technology emergence
- **Business Optimization Agent:** Current objective portfolio, objective success/failure patterns
- **Principal Context Agent:** Decision style, business process hierarchy, historical strategic priorities
- **KPI Registry Provider:** Current measurement coverage, peer benchmarks (Phase 12A+)
- **Registry Providers:** Business Process definitions, Business Objectives, KPI definitions
- **Supabase:** Persistence layer for innovation options, pipeline stages, decision history

---

## Not in Scope (V1)

- Autonomous option execution (all options require HITL gating)
- Implementation planning (handed to Solution Finder or future Implementation Planner Agent)
- External innovation platform integration (Brightidea, IdeaScale connectors)
- Real-time competitive intelligence feed (uses MA Agent's existing cadence)
- Customer-facing ideation portals (this is an executive tool, not crowdsourcing platform)
- Venture capital or M&A financial modeling (beyond strategic option framing)

These may be prioritized in Phase C+.

---

## Phased Implementation Summary

See **Phasing — gated on evidence, not dates** above for the authoritative table. Restated here with scope:

| Phase | Scope | Gate to begin |
|---|---|---|
| **V1 — Facilitator capture** | Typed idea capture, evidence block (internal registry + external MA), framing, honest gaps, session memory, on-request persona stress-test | ≥1 client with a populated registry and a leadership team willing to pilot in a real session |
| **V2 — Session artefact** | Post-session summary: ideas raised, evidence, conclusions, parked items | V1 used unprompted in ≥3 sessions by the same team |
| **V3 — Ambient capture** | Agent extracts candidate ideas from the conversation; human confirms what counts | V2 showing the evidence is the valued part, plus an agreed privacy/consent posture |
| **V4 — Portfolio memory** | Cross-session idea pipeline, resurfacing on changed conditions, kill discipline | A client with enough session history for "we discussed this before" to be a real event |

**No dates.** Any date here would be a guess about adoption expressed as a schedule commitment. If Agent9 is adopted quickly, these gates open sooner; if slowly, later. The gates are the honest statement of dependency.

---

## Acceptance Criteria (Upon Implementation)

### V1 Acceptance Criteria

1. Agent successfully identifies whitespace discovery candidates from 12+ months of DA IS NOT segments with ≥3 examples per discovery scope category.
2. Cross-domain pattern recognition extracts solution archetypes from VA data and projects them to new contexts with documented transfer rationale.
3. Market signal integration correlates competitive/trend data from MA Agent to at least 2 strategic options per assessment.
4. Multi-persona debate generates ranked option sets with persona arguments, synthesis rationale, and confidence scores (all auditable).
5. InnovationOption Pydantic model successfully validates all generated options and persists to Supabase with strict client_id isolation.
6. PIB "Strategic Options" section displays top 3–5 options with hypothesis, evidence, confidence, and elevation token.
7. HITL approval gates require principal acknowledgement before options progress beyond `discovered` stage.
8. Full audit trail maintained for all option generation, analysis steps, and source data consulted.

### V2 Acceptance Criteria

1. Innovation Pipeline stage transitions tracked with HITL gates and full history persisted.
2. Stale incubation rule correctly surfaces options >90 days without progression.
3. Kill reason taxonomy enforced on all killed options; kill decision history accessible for meta-analysis.
4. Portfolio health metrics (pipeline depth, velocity, kill rate, scale rate) computed correctly and surfaced in PIB.
5. Meta-learning surfaces sourcing effectiveness (success rate by discovery method) with concrete impact on next-cycle sourcing weights.
6. Innovation Portfolio ROI computed using VA DiD attribution methodology for scaled options; results compared against projections.

### V3 Acceptance Criteria

1. Successful innovation patterns extracted from `scaling` options and stored for reapplication.
2. Failure analysis performed on killed piloted options; lessons captured for future generation.
3. Proactive option generation triggers correctly on market shifts, objective degradation, objective completion, and bright spot emergence.
4. Continuous Strategic Posture Report generated quarterly with complete narrative tying together portfolio, pipeline, KPI, and market data.
5. All outputs auditable with full methodology documentation and source attribution.
6. Agent complies with A2A protocol, A9 registry patterns, Pydantic model validation, and orchestrator-controlled instantiation.

---

## Change Log

- **2026-08-02 (v0.3 — Session Support Repositioning):** Core concept changed. v0.2 framed this as autonomous discovery — mining operational data for "whitespace" and surfacing inferred strategic options for approval. v0.3 makes it a **support agent for human ideation sessions**: executives raise the ideas, the agent captures, frames, and evidences them live.

  Two reasons for the change. **(1) Source of ideas.** Inspiration for a new product or service comes from anywhere — a customer complaint, a newly affordable technology, a mechanism seen in an unrelated industry, a competitor's abandoned attempt. That space is not enumerable and is not reachable by mining internal KPI data. Note the corollary in the data model: `evidence_basis` as a closed `Literal` is **removed**, replaced by free-text `inspiration_note`. Closed enums are right elsewhere in Agent9 (`relationship_type`, `provenance`, `causal_rung`) and wrong here, where an incomplete enumeration silently caps what the product can represent. **(2) Trust.** An agent that proposes strategy fails by being *wrong*; an agent that supports a human's idea fails by being *unhelpful*. Only the second is survivable in an executive strategy session, and admission to the room is the binding constraint on this product.

  Also: building the causal model of business performance is **not** this agent's job — that belongs to onboarding and to the FP&A analysts and executives who maintain it. v0.2 conflated the two.

  **Positioning corrected.** The "$70B+ addressable market / displaces IDEO, frog, BCG Digital Ventures" claim is **withdrawn** — it directly contradicted `theory_layer_design.md` §3.4/§11 ("competitor is Excel and the monthly variance meeting, not MBB; never claim consulting takeover; MBB is price anchor and plausible acquirer/channel"). The two imply opposite go-to-market motions. Replaced with the defensible version: a very well-briefed analyst in the room. Nearest real comparison is meeting assistants (Otter, Fireflies), which cannot reach the registry.

  **Phasing changed from dates to gates.** Phase A 2029 / B 2030 / C 2031+ withdrawn — those were adoption guesses expressed as schedule. New phases V1 facilitator capture → V2 session artefact → V3 ambient capture → V4 portfolio memory, each gated on an observable condition. Ordering is deliberate: the hardest technical problem (which utterances are ideas) and the hardest social problem (consent to record a strategy session) both sit in V3, while the most valuable capability (grounded evidence on demand) sits in V1 and needs neither.

  **Not revised in this pass:** the former V2/V3 capability sections, input/output models, integration points, and acceptance criteria still reflect v0.2 assumptions. The two capability sections carry explicit warning banners; the rest should be reworked when V1 is actually scheduled, so the shape follows what real session usage reveals rather than being invented now.

- **2026-06-01 (v0.2 — Strategic Repositioning):** Substantially rewritten from July 2025 v1.0 boilerplate. Original PRD positioned Innovation Agent as a workflow component for brainstorming ideation. New positioning treats it as the fourth strategic layer (Layer 4) wrapping the Business Optimization Agent outer loop and the SA→DA→SF→VA inner loop. Added: three-mode strategic architecture diagram (run/change/reimagine the business), market positioning ($70B+ innovation consulting market, software displacing consultant engagements), expanded buyer personas (CSO, Chief Innovation Officer, Corp Dev, CEO, CFO, PE Operating Partner), three-phase capability roadmap (V1 Whitespace Discovery → V2 Portfolio Management → V3 Cross-Loop Learning), input/output Pydantic models, detailed integration points with DA/VA/MA/BO/PC agents, trust curve rationale reflecting high autonomy bar, comprehensive acceptance criteria per phase. Original protocol compliance bullets retained and integrated into Acceptance Criteria. Status updated to multi-phase (2029–2031+). Removed: hackathon quick-start boilerplate, generic implementation guidance, test-harness references.

- **2025-07-17 (v1.0 — Initial Hackathon Template):** Created as generic agent template with MVP ideation, feasibility evaluation, prioritization, and project tracking. Positioned as workflow brainstorming component. Status: Planned for Phase 4. Protocol compliance documented but architecture not yet defined.

---

## Protocol Compliance

The Innovation Driver Agent must comply with all critical protocol requirements specified in the root CLAUDE.md:

- **Agent Instantiation:** Always instantiated via `await AgentRegistry.get_agent("innovation_driver")` or `A9_InnovationDriverAgent.create_from_registry(config)`. Direct instantiation forbidden.

- **Pydantic Models Only:** All agent-to-agent I/O uses Pydantic models. No raw dicts in A2A communication. InnovationOption, InnovationDiscoveryInput, InnovationDiscoveryResult models enforce type safety.

- **LLM Call Routing:** All LLM calls (option generation, multi-persona debate, synthesis) route through A9_LLM_Service_Agent via Orchestrator. No direct anthropic/openai imports in agent file.

- **Logging Standard:** No `print()` statements. Use `logging.getLogger(__name__)` (interim) or A9_SharedLogger (when available).

- **Lifecycle Methods:** Implement async `create()`, `connect()`, `disconnect()` following A9 agent patterns.

- **Registry Data Source:** Supabase is sole registry backend. No YAML fallbacks. If a provider returns empty/None, log error and return empty — do not silently load from files.

- **Multi-Tenant Isolation:** Every InnovationOption has mandatory `client_id`. API list endpoints accept `client_id` query parameter and enforce strict filtering. Cannot list or manipulate another client's options.

- **SQL Backend Routing:** Route analytics queries by looking up DataProduct.source_system in registry (bigquery, snowflake, sqlserver, duckdb) — not via regex detection.
