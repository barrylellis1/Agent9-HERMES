# Agent9 HITL Decision Philosophy

**Last updated:** 2026-03-15
**Status:** Core architecture principle

---

## 1. Governing Principle

Agent9 is a decision **support** system, not a decision **making** system. Its role is to present the best information and advice for consideration, in the most natural and effective manner, to advance decision-making.

Cognitive dissonance between Agent9's data-driven insights and an executive's experience is **expected and productive**. When they disagree, either the data reveals something the executive's intuition missed, or the executive knows something the data cannot capture. Either way, the decision gets better. This tension is the most valuable moment in the entire workflow.

Agent9 does not need to be infallible. It needs to be useful.

---

## 2. HITL Gates in the Pipeline

The Agent9 pipeline has two primary HITL gates where the principal interacts with the system before a consequential decision advances:

### Gate 1: Problem Refinement (Post-DA, Pre-SF)

**Context:** The Deep Analysis Agent has produced an IS/IS NOT dimensional analysis with SCQA framing. Before the Solution Finder council convenes, the principal validates the problem diagnosis.

**What the principal does:**
- Reviews the IS/IS NOT table and root cause framing
- Asks clarifying questions about the data (NLP → DPA pipeline for data queries)
- Confirms or refines the problem statement
- Provides organizational context the data cannot reveal (e.g., "this is primarily market pass-through")

**Design:** Problem Refinement Chat — neutral Decision Studio voice, inline data query results, suggested questions from the analysis.

### Gate 2: Solution Decision (Post-SF, Pre-Approval)

**Context:** The Solution Finder has run its 3-stage council (independent proposals → cross-review → synthesis), Market Analysis has enriched with competitive context, and the Executive Briefing has been generated. This is the highest-stakes gate — the principal commits organizational resources.

**What the principal does:**
- Reviews the full Decision Briefing (interactive, not static)
- Interrogates the recommendations through Solution Q&A dialogue
- Challenges assumptions, probes blind spots, requests additional data
- Builds personal conviction before approving

**Design:** Solution Q&A Chat — same neutral voice as Problem Refinement, but with the full context stack (DA + SF Stage 1/2/3 + MA signals). Embedded in the Decision Briefing page, transforming it from a static document into an interactive decision workspace.

### Approval Gate: Post-Q&A

The "Approve & Track" action belongs **after** the principal has reviewed the full briefing and completed their Q&A due diligence. It should never appear before the briefing — presenting approval before review pressures the decision and undermines trust.

---

## 3. Interaction Design Principles

### Present, Don't Defend

When the principal challenges a recommendation, the system provides additional context and data. It does not argue. If the executive disagrees with the recommendation and overrides it, that is the system working correctly. The principal's judgment is the final authority.

### Consistent Voice

All HITL interactions use the same neutral Decision Studio voice — not the council personas (McKinsey/BCG/Bain). The council is an analytical device; the Q&A interface is a trusted advisor. Mixing voices creates confusion about who the principal is talking to.

### Transparent Boundaries

The system must clearly distinguish what it can and cannot answer:

| Tier | Description | Handling |
|---|---|---|
| **Context Recall** | Answerable from the analytical corpus (DA output, SF stages, MA signals) | High confidence — direct answer with source reference |
| **Data Query** | Requires SQL execution against the data warehouse | Verifiable — NLP → DPA pipeline, inline results |
| **Contextual Judgment** | Answerable by combining analytical corpus with principal/business/market context agents | Medium-high confidence — synthesize from multiple agent outputs, cite sources |
| **Organizational Knowledge** | Requires information Agent9 genuinely does not have (stakeholder politics, undocumented decisions, team dynamics) | Honest limitation — acknowledge the boundary, surface related context, suggest as a question to resolve with the relevant stakeholder |

#### Narrowing the gap: Context-aware agents

The boundary between what the system can and cannot answer is not fixed — it narrows as Agent9's context agents accumulate richer profiles. Three agents push questions that *appear* to require organizational judgment into answerable territory:

**Principal Context Agent** — knows the principal's decision style, priorities, risk tolerance, business process ownership, and reporting relationships. This turns questions like *"What would the CFO prioritize here?"* from unanswerable to answerable: the PC Agent knows the CFO's `decision_style: analytical` and `priorities: [cost_optimization, margin_defense]`, enabling the system to frame recommendations in terms the principal values.

**Business Context Registry** — captures business process hierarchies, domain definitions, strategic objectives, and organizational structure. Questions like *"Is this aligned with our strategic priorities?"* become answerable when the registry maps the affected KPI to a business process with documented strategic objectives.

**Market Analysis Agent** — provides real-time competitive intelligence via Perplexity web search + Claude synthesis. Questions like *"Have competitors already raised prices in this channel?"* don't require organizational knowledge — they require market research the MA Agent can perform on-demand during the Q&A, or may have already captured during the SF run.

The practical effect: many questions that seem like Tier 4 (organizational knowledge) are actually Tier 3 (contextual judgment) once the system consults its context agents. The Q&A should attempt this synthesis before falling back to "this requires organizational knowledge."

The system should still never hallucinate. When context agents don't have sufficient information to answer confidently, the system should transparently say what it *does* know from those agents and identify the specific gap. For example: *"The Business Context Registry shows Service Centers operates under the Revenue Growth strategic objective with a 40% channel margin. However, I don't have visibility into the specific franchise partner agreements that would determine whether a surcharge is contractually feasible — this requires legal review."*

### Earned Approval

The Q&A exists because the approval decision matters. The principal should feel they've done their due diligence — not that they're rubber-stamping an AI recommendation. Suggested questions (seeded from the briefing's Stakeholder Perspectives and Unresolved Tensions sections) guide the principal toward the most important issues to resolve.

---

## 4. Context Stack Architecture

Each HITL gate has access to an increasing context stack:

### Problem Refinement Context (Gate 1)

| Source | Content |
|---|---|
| SA Agent | KPI performance data, threshold breach, variance magnitude |
| DA Agent | IS/IS NOT dimensional breakdown, SCQA root cause framing, benchmark segments |
| KPI Registry | KPI definitions, thresholds, business process mappings |
| Principal Context Agent | Principal's decision style, priorities, risk tolerance, business process ownership |
| Business Context Registry | Business process hierarchy, domain definitions, strategic objectives |

### Solution Q&A Context (Gate 2)

*Everything from Gate 1, plus:*

| Source | Content |
|---|---|
| Problem Refinement | Principal's Q&A history — questions asked, answers received, organizational context provided |
| SF Stage 1 | 3 independent firm proposals (McKinsey, BCG, Bain) with evidence bases |
| SF Stage 2 | Cross-review critiques and endorsements with attribution |
| SF Synthesis | Ranked options, trade-off matrix, blind spots, unresolved tensions, stakeholder perspectives |
| MA Agent | Market intelligence signals — competitor moves, industry trends, supply chain dynamics |
| Business Context Registry | Strategic alignment — maps affected KPIs/business processes to organizational objectives |
| Principal Context Agent | Decision framing — the principal's stated priorities and decision style inform how the Q&A presents trade-offs |

This is the richest context stack in the entire pipeline. The combination of analytical output (DA, SF) with contextual agents (PC, Business Context, MA) means the system can answer most questions that arise during executive due diligence. The remaining gap — genuinely unknowable organizational knowledge — is transparently flagged, often with a partial answer from what the context agents *do* know.

---

## 5. Ripple Effects Across Agent PRDs

This philosophy has implications for existing agent PRDs:

### Principal Context Agent
- PC Agent profile data (decision style, priorities, risk tolerance, business process ownership) must be available to the Q&A context assembly — not just for access control but for **framing**
- Q&A responses should be tailored to the principal's decision style: an analytical CFO gets quantified trade-offs, an intuitive CEO gets strategic narrative

### Business Context Registry
- Business process hierarchy and strategic objectives must be queryable during Q&A — not just for filtering but for **alignment assessment**
- When a principal asks "Is this aligned with our strategy?", the system should map the affected KPI → business process → strategic objective and answer concretely
- Richer business context profiles (e.g., documented competitive positioning, channel strategies) directly narrow the Tier 4 gap

### Market Analysis Agent
- MA signals collected during the SF run should be persisted and available for Q&A retrieval (currently they are, via the briefing payload)
- The Q&A should be able to trigger **on-demand MA queries** for questions the original SF run didn't anticipate (e.g., "What are competitors doing about additive costs specifically?")
- This turns some apparent Tier 4 questions into Tier 2 (data query via web search rather than SQL)

### Solution Finder Agent
- The SF output must include structured fields that support Q&A retrieval: `blind_spots`, `unresolved_tensions`, stakeholder perspectives per option, and cross-review critique/endorsement pairs with attribution
- The recommendation should include suggested questions the principal should ask before approving

### NLP Interface Agent
- Must support being invoked in Solution Q&A context (not just Problem Refinement)
- Same deterministic regex parsing pipeline — the context changes, not the mechanism

### LLM Service Agent
- Solution Q&A prompts require the full SF context stack as system context
- Task routing: Q&A dialogue can use Haiku for simple context recall, Sonnet for complex synthesis

### Value Assurance Agent
- Approval payload should capture whether the principal completed Q&A before approving (engagement signal)

### Executive Briefing (UI)
- Must evolve from static document to interactive decision workspace
- Chat panel embedded in the briefing page
- Collapsible sections (not a flat 18-page wall)
- Approval button at bottom, after review and Q&A

---

## 6. What This Is Not

- **Not a chatbot.** The Q&A is scoped to a specific decision context (a single situation's analysis and recommendations). It is not a general-purpose conversational interface.
- **Not a board collaboration tool.** Single principal as decision maker. Executives will not expose Agent9 to a board.
- **Not a defense mechanism.** The system does not try to convince the principal that its recommendation is correct. It presents information for consideration.
- **Not a replacement for organizational judgment.** The system narrows the gap through context agents (Principal Context, Business Context, Market Analysis), but when a question requires knowledge that genuinely isn't in the system — undocumented decisions, stakeholder politics, team dynamics — it says so clearly while sharing what it *does* know.
