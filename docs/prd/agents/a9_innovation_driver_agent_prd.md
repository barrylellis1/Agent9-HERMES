# A9_Innovation_Driver_Agent PRD

<!-- 
CANONICAL PRD DOCUMENT
This is the official, canonical PRD document for this agent.
Last updated: 2026-06-01
Status: Multi-phase: Phase A 2029, Phase B 2030, Phase C 2031+
-->

## Overview

**Purpose:** Surface and evaluate evidence-based strategic innovation opportunities by analyzing operational data across the inner loop (SA→DA→SF→VA) and the Business Optimization Agent's objective portfolio. Generate a continuous stream of strategic options — candidates that principals can elevate into formal Business Objectives. At full realization, the agent displaces what innovation consulting firms (IDEO, frog, BCG Digital Ventures, McKinsey Digital) deliver in 12–18 week engagements.

**Agent Type:** Strategic Innovation & Option Generation Agent  
**Version:** 0.2 (Strategic Repositioning)

The Innovation Driver Agent operates at Layer 4 (Strategic Imagination) of Decision Studio's analytical intelligence framework. Whereas Situation Awareness (Layer 1) detects anomalies, Deep Analysis (Layer 2) provides diagnostic rigor, Business Optimization (Layer 3) pursues declared objectives, the Innovation Driver Agent discovers possibilities that no declared objective yet covers — whitespace, pattern transfers, market-grounded options that emerge from operational data rather than abstract brainstorming.

---

## Executive Summary

The Innovation Driver Agent is Decision Studio's strategic imagination layer. The existing SA→DA→SF→VA pipeline is the defensive inner loop — it fixes what's breaking. The Business Optimization Agent is the offensive outer loop — it pursues declared strategic objectives. The Innovation Driver Agent wraps both loops with continuous option generation — the discovery layer.

Decision Studio's three-mode architecture supports three fundamentally different strategic questions:

| Mode | Agent | Question | Outcome |
|---|---|---|---|
| **Run the business** | Inner Loop (SA→DA→SF→VA) | What's breaking and how do we fix it? | Defend KPI performance, maintain operations |
| **Change the business** | Business Optimization Agent | Are we executing declared objectives? | Pursue declared strategic goals with discipline |
| **Reimagine the business** | Innovation Driver Agent (this) | What should we even consider doing? | Discover new possibilities, enlarge strategic options |

At full realization, the system produces a continuous stream of strategic options — candidates that principals can elevate into formal Business Objectives to be pursued by the BO Agent. The Innovation Agent displaces the consultant's innovation engagement by grounding option generation in the client's own operational data rather than generic creative brainstorming, and by running continuously rather than as a one-time 12–18 week project.

**Why this matters:** CFOs currently hire innovation consultants ($500K–$3M per engagement) or run annual strategic planning off spreadsheets. The Innovation Driver Agent replaces the consultant's discovery phase with continuous, data-grounded option generation. Executives work with richer, more evidence-based strategic options. The system automatically surfaces new candidates when conditions change.

---

## Market Positioning

### Innovation Consulting Market Sizing

The addressable market is significantly larger than strategy consulting alone:

- **Innovation consulting:** ~$50B annually (IDEO, frog, BCG Digital Ventures, McKinsey Digital, Accenture Song)
- **Corporate venture and R&D advisory:** ~$20B
- **Innovation platform tools (Brightidea, IdeaScale):** ~$2B SaaS
- **Combined addressable market:** $70B+ — includes strategy consulting market as subset

### What the Innovation Driver Agent Displaces

| Competitor | What they do | Gap vs. Innovation Agent |
|---|---|---|
| IDEO / frog design | Workshop-driven creative brainstorming; design thinking process | One-time engagement ($500K–$3M), no data foundation, no sustainability, outcome dependent on consultant's network |
| BCG Digital Ventures / McKinsey Digital | Innovation strategy + build capabilities; structured discovery process | Bills $1M+/quarter; methodology lives in consultant's head; not continuous; expensive re-engagement for updates |
| Accenture Song | Productized design + innovation services | Generic engagement model; not grounded to client's operational data; high service labor cost |
| Brightidea / IdeaScale | Employee ideation portals; crowdsourcing tool | Collects raw ideas; no analysis; no portfolio management; no link to strategy or operational context |
| **No one** | Continuous, data-grounded, autonomous innovation discovery linked to KPI performance and strategic objectives | **This is the gap** |

### Why Now

LLMs are genuinely proficient at:
- Creative synthesis across distant domains
- Simulating multiple stakeholder perspectives (Stage 1 persona debates)
- Identifying pattern transfers from one context to another
- Generating ranked option sets with evidence trails

Innovation consulting has historically been high-margin precisely because it resists scale — outcomes depend on expensive human expertise and subjective judgment. AI changes this. Innovation consulting margins are now under the same pressure that strategy consulting margins already face.

### Key ICP Stakeholders

| Buyer | What they care about | When they engage |
|---|---|---|
| **Chief Strategy Officer** | Strategic option portfolio; what could we pursue that we haven't considered? | Phase A onwards |
| **Chief Innovation Officer / Head of Innovation** | Innovation pipeline visibility; kill-rate discipline; portfolio ROI tracking | Phase A onwards |
| **CEO** (growth-focused, mature companies) | New growth vectors; competitive positioning; adjacent market opportunities | Phase B onwards |
| **Chief Finance Officer** | Innovation ROI accountability; rigour around speculative spending; confidence in option sourcing | Phase B onwards |
| **Corp Dev / M&A** | Adjacent market opportunities; build vs. buy candidates; capability mapping | Phase B onwards |
| **PE Operating Partner** | Value creation playbook beyond cost reduction — top-line growth options; industry playbooks | Phase B onwards |

---

## Strategic Context

### Three-Layer Strategic Architecture

Decision Studio's intelligence flows through three levels of abstraction. Each layer answers a distinct executive question and produces outputs that feed both upward (as learning signals) and downward (as constraints and context).

```
LAYER 4 — INNOVATION DRIVER AGENT (Strategic Imagination)
    "What should we consider doing?"
    Whitespace discovery, strategic options, innovation portfolio
        ↓ candidates flow to BO Agent as new Objectives
        ↓ learning signals flow back from BO Agent outcomes
        
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
- **Layer 4 imagines.** Innovation Agent discovers what hasn't been declared yet — whitespace, pattern transfers, market signals — and surfaces them as candidates for elevation to formal objectives.

The inner loop (Layers 1–2) operates continuously on the status quo. The outer loop (Layer 3) constrains and prioritizes the inner loop. The imagination layer (Layer 4) challenges the outer loop with new possibilities.

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
  - High-confidence whitespace replication candidates can be auto-elevated to formal objectives (Phase B+)
  - Medium-confidence options surface for principal review

- **PIB "Strategic Options" section:**
  - Top 3–5 options from most recent assessment cycle
  - One-sentence hypothesis + evidence type + confidence level per option
  - Single-use token for quick elevation to BO Agent formal objective

- **HITL approval gates:**
  - Principal review and acceptance/rejection of surfaced options
  - Option prioritization and kill discipline

---

## Trust Curve and Phasing Rationale

Innovation Agent autonomy requires even more trust than BO Agent autonomy. Principals will accept "fix this broken KPI" more readily than "consider entering this adjacent market." Autonomy is earned through demonstrated accuracy and evidence quality. Phasing reflects the trust curve:

| Stage | Trust level | What the system does autonomously | Timeline |
|---|---|---|---|
| V1 | Discovery surfaced for human review | Innovation Agent generates option candidates; all require principal acknowledgement | Phase A (2029) |
| V2 | Pattern recognition trusted | Auto-elevation of high-confidence whitespace replication candidates to BO Agent objectives (still requires HITL approval before execution) | Phase B (2030) |
| V3 | Continuous innovation portfolio | Agent maintains full innovation portfolio; forces kill decisions; surfaces proactive options without request | Phase C (2031+) |

---

## Functional Requirements

### V1 Capabilities — Whitespace Discovery + Strategic Option Generation (Phase A — 2029)

#### 1. Whitespace Discovery from Internal Data

Systematic analysis of DA agent's IS NOT segments and persistent performance outliers to identify dimensional combinations that have repeatedly outperformed baseline:

- **Bright Spot Replication Candidates:** Read historical DA outputs across all recent assessments (12+ months). Identify dimensional combinations in IS NOT segments that persistently deliver above-baseline performance.
  - Example: "Customers aged 35–45 in Western region with product bundle X consistently show 3× higher margins than overall cohort — replicate this segment structure elsewhere?"
  
- **Cross-Segment Pattern Transfer:** When high-performance patterns emerge in one business process, project them onto adjacent processes.
  - Example: "Procurement cost reduction succeeded in Operations through vendor consolidation — can the same mechanism apply to Marketing vendor management?"

- **KPI Measurement Whitespace:** Compare client's KPI registry against industry benchmark library (Phase 12A feature). Surface "KPIs your peers measure that you don't" as indicators of unmeasured opportunity.
  - Example: "Peers measure Customer Lifetime Value; you don't — this gap suggests revenue growth opportunity you're not tracking."

- **Output:** Ranked whitespace discovery candidates with:
  - Evidence type (bright spot | pattern transfer | measurement gap)
  - Confidence score (0–1 based on data consistency)
  - Dimension specifications (what made it work in the source context?)
  - Replication difficulty estimate (easy to replicate vs. context-dependent)

#### 2. Cross-Domain Pattern Recognition from VA

Analyze Value Assurance Agent's solution success archive to identify archetypes and project them across domains:

- **Solution Archetype Extraction:** From VA's DiD attribution data, cluster successful solutions by mechanism type (cost reduction, revenue growth, capability building, quality improvement, etc.).

- **Pattern Transfer Analysis:** For each archetype, identify where it succeeded and where similar mechanisms could apply.
  - Example: "Service quality improvement (architecting mechanism: process standardization) delivered 15% success rate. Where else do unstandardized processes limit performance?"

- **Confidence Adjustment:** Cross-reference VA success patterns with DA dimensional analysis to estimate transfer confidence.
  - If the same dimension is a root cause in both source and target context, higher confidence
  - If dimensions differ, lower confidence but still worth exploring

- **Output:** Pattern transfer candidates with evidence basis, success archetype, replication requirements.

#### 3. Market Signal Integration

Integrate MA Agent's competitive and market intelligence into strategic option generation:

- **Competitive Positioning:** When MA detects peers moving into adjacent spaces, surface as "peer is exploring this — should we?" option.

- **Technology Emergence:** When MA signals new technology adoption in the market (e.g., AI-driven forecasting, automation tooling), correlate with client's KPI gaps to suggest "technology X could address performance gap Y."

- **Industry Trend Correlation:** Link emerging trends to the client's stated strategic priorities.

- **Output:** Market-signal-grounded options with external validity indicators.

#### 4. Strategic Option Generation (Multi-Persona Debate)

Generate ranked sets of strategic options using a multi-persona debate architecture similar to Solution Finder's 3×Stage1 + synthesis pattern:

- **Persona Set:** Three strategic personas (Conservative CFO, Aggressive CEO, Pragmatic COO) analyze the same option candidate and produce independent hypotheses about viability and value.

- **Debate:** Each persona provides a structured argument (why this could work, why it might fail, evidence threshold for confidence).

- **Synthesis:** LLM-synthesized resolution combines personas' perspectives into a single option card with explicit confidence rationale.

- **Ranking:** Options ranked by expected impact × confidence × strategic alignment.

#### 5. Innovation Option Cards (Pydantic Model)

Define `InnovationOption` model for storage and PIB surfacing:

```python
class InnovationOption(A9AgentBaseModel):
    option_id: str                                  # Unique within client
    client_id: str                                  # Mandatory tenant key
    title: str                                      # Option title
    hypothesis: str                                 # Clear hypothesis: "If we X, we could achieve Y"
    evidence_basis: Literal["whitespace", "pattern_transfer", "market_signal", "hybrid"]
    confidence: float                               # 0.0–1.0 (from multi-persona consensus)
    impact_estimate_lower: float                    # Conservative estimate
    impact_estimate_upper: float                    # Optimistic estimate
    impact_unit: str                                # "$M revenue", "% margin", "FTE savings", etc.
    required_capabilities_have: List[str]           # What we can leverage
    required_capabilities_need: List[str]           # What we'd need to build/acquire
    market_signal_alignment: Optional[str]          # Link to competitive/trend context
    originating_kpi_ids: List[str]                  # Which KPIs this addresses
    originating_segments: List[Dict[str, Any]]      # IS NOT segments or VA patterns
    originating_da_drivers: List[str]               # Root causes from DA analysis
    competitive_context: Optional[str]              # Peer behavior, industry trend
    persona_debate_summary: Optional[str]           # Multi-persona analysis rationale
    candidate_objective_template: Optional[Dict[str, Any]]  # Pre-populated BusinessObjective payload for elevation
    stage: Literal["discovered", "flagged", "incubating", "prototyped", "piloted", "scaling", "killed"] = "discovered"
    generated_at: str                               # ISO timestamp
    principal_reviewed_at: Optional[str] = None
    principal_decision: Optional[Literal["accept", "reject", "defer"]] = None
```

#### 6. PIB "Strategic Options" Section

Extend PIB template with new optional section:

- **Contents:** Top 3–5 highest-confidence options from the assessment cycle
- **Framing:** "These options surfaced from your operational data this period. None require immediate action. Flag any for deeper investigation."
- **Per-option display:**
  - Title + hypothesis (one sentence)
  - Evidence type + confidence level
  - Impact range
  - Single-use token to elevate option to BO Agent objective for formal pursuit
- **Tone:** Suggestive, not prescriptive. Options are hypotheses, not recommendations.

---

### V2 Capabilities — Innovation Portfolio Management (Phase B — 2030)

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

### V3 Capabilities — Cross-Loop Learning + Autonomous Generation (Phase C — 2031+)

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

| Phase | Scope | Timeline | Trust prerequisite |
|---|---|---|---|
| **V1 (Phase A)** | Whitespace Discovery, Pattern Transfer Analysis, Market Signal Integration, Strategic Option Generation via multi-persona debate, Innovation Option Cards, PIB Strategic Options section | 2029 | BO Agent Phase A established and validated with at least 2 reference customers |
| **V2 (Phase B)** | Innovation Pipeline stages, Kill Discipline (stale incubation rules), Portfolio Health metrics, Meta-Learning across sourcing methods | 2030 | V1 portfolio data accumulated (12+ months of options tracked to meaningful scale rates) |
| **V3 (Phase C)** | Cross-Loop Learning (successful innovations auto-suggest reapplication), Proactive Option Generation (trigger-based), Continuous Strategic Posture Reports | 2031+ | Multi-year customer maturity; demonstrated trust in autonomous BO Agent; 50%+ of innovation pilots validating hypotheses |

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
