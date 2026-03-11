# A9_Market_Analysis_Agent PRD

**Version:** 1.0
**Status:** MVP — Not yet implemented
**Last Updated:** 2026-03-10
**Agent Type:** External Intelligence / Analysis Agent

---

## 1. Overview

The A9_Market_Analysis_Agent (MA Agent) is an external intelligence layer that monitors, analyzes, and surfacemarket signals—competitor moves, industry trends, regulatory changes, demand signals, pricing benchmarks, and supply chain disruptions—to enrich Agent9's decision workflows with market context.

**Core purpose:**
- Reactive mode: When SA detects a KPI breach (negative or positive), MA provides market context to help SF generate differentiated solutions (avoid commoditised responses, understand competitive constraints, identify tailwind opportunities).
- Proactive mode: Scheduled market scans across sectors/topics to surface emerging signals that may themselves trigger SA or inform principal strategy without a KPI event.
- Value assurance: Post-implementation, MA re-analyses the same KPI to attribute recovery to the intervention vs. market-wide tailwinds (honest ROI accounting).

**Market position:** MA is the agent enabling Agent9 to become the "never-engaged MBB partner"—providing decision intelligence grounded in current market reality, not just internal data. It positions Agent9 as a differentiated tier above rule-based analytics and BI.

---

## 2. Strategic Context

### Why This Agent Exists

The SA → DA → SF pipeline is internally grounded: it detects KPI anomalies, drills into root causes, and generates solutions. But without external market context, solutions risk being:
- **Commoditised:** Proposing actions competitors already execute (e.g., "reduce SKU complexity" when the entire industry is consolidating)
- **Naïve to constraints:** Missing regulatory/supply-chain headwinds that make an option infeasible
- **Blind to tailwinds:** Missing demand-side or technology tailwinds that amplify impact
- **Attributing to internal action what's driven by market winds:** Declaring a repricing success when the entire category recovered due to commodity pricing

### Value Unlock in the Pipeline

| Stage | Without MA | With MA |
|-------|----------|---------|
| **SA** | Detects KPI breach (fact) | Same, but context enriched by MA in next stage |
| **DA** | Root cause in internal dims (Is/Is Not analysis) | Same; market MA adds external validation |
| **SF** | Option generation grounded only in problem statement + KPIs | SF uses MA signals as constraints/tailwinds; generates differentiated, realistic options |
| **HITL** | Principal evaluates options without market validation | Principal sees options validated against competitor moves and market trends |
| **Post-implementation (Value Assurance)** | KPI recovery attributed 100% to solution; overestimates ROI | MA isolates intervention impact from market-wide tailwinds; honest ROI accounting |

### MBB Partnership Model

Agent9's competitive positioning hinges on delivering insights a CFO couldn't access via BI or Excel. MA feeds market-grounded decision logic that rivals MBB research quality:
- **Competitor move detection:** "Salesforce announced a 15% price drop on SMB tier → market is commoditising, adjust your segmentation strategy"
- **Trend synthesis:** "Three industry leaders adopted SKU consolidation in Q1 2026 → it's validation your cost-to-serve reduction is market-native"
- **Risk flagging:** "Supply bottleneck in semiconductor fabs projected Q3 2026 → your hardware redesign will face 60-day delays"

This positions Agent9 as the "always-on, market-aware" advisor—exactly the value MBB charges $500K+ to deliver quarterly.

---

## 3. Trigger Modes

### Mode 1: Reactive (Situation-Triggered)

**Trigger:** SA detects a KPI breach (positive or negative) → passes Situation object to MA.

**Flow:**

```
SA detects situation
    ↓
Situation card created
    ↓
MA.analyze_market_opportunity(situation)
    ↓
MA returns market context (signals, competitor actions, benchmarks)
    ↓
SF uses market context in synthesis LLM call
    ↓
SF options are differentiated + validated against market
```

**Input:** Serialised Situation object (kpi_name, kpi_value, severity, description, timestamp).
**Output:** `MarketAnalysisResponse` with:
- Top 3 market signals (competitor moves, industry trends, demand shifts)
- Competitor actions analysis
- Industry benchmarks relevant to the KPI
- Opportunity/threat scoring
- `sf_context` dict ready for SF's `market_analysis_input` field

**Timing:** Synchronous within SA → DA → SF workflow. Total latency budget: 10–15 seconds (Perplexity query + Sonnet synthesis).

---

### Mode 2: Proactive (Scheduled / On-Demand Scan)

**Trigger:** Principal or orchestrator requests a market scan on specified sectors/topics. No KPI event.

**Flow:**

```
Principal requests scan
    ↓
MA.scan_for_opportunities(sectors, topics, scan_depth)
    ↓
Perplexity queries per sector
    ↓
Sonnet synthesis + ranking
    ↓
Signals + surfaced opportunities returned
    ↓
Opportunities may trigger SA alerts or inform principal strategy directly
```

**Input:** `MarketScanRequest` with sector list, topics, scan_depth ("quick" | "standard" | "deep").
**Output:** `MarketScanResponse` with ranked signals, surfaced opportunities, threat flags, workflow recommendations.

**Timing:** Asynchronous, scheduled weekly or on-demand. Latency: 30–60 seconds for "standard" scan.

---

### Mode 3: Lightweight Competitive Context (Option Validation)

**Trigger:** During SF synthesis, when evaluating a proposed option, SF may query MA for quick competitive validation.

**Flow:**

```
SF considering option: "Reprice SKU 042 up 8%"
    ↓
SF.get_competitive_context(option, kpi_name, sector)
    ↓
MA returns quick assessment: competitor pricing moves, market validation
    ↓
SF includes in synthesis reasoning: "This is differentiated vs. competitor pricing, or it aligns with market moves"
```

**Input:** `CompetitiveContextRequest` with option title, KPI name, sector.
**Output:** `CompetitiveContextResponse` with differentiation assessment, competitor actions, market validation ("validated" | "commoditised" | "novel" | "risky").

**Timing:** Synchronous, lightweight. Latency: 5–10 seconds (cached competitor signals + quick classification).

---

## 4. Entrypoints

All entrypoints follow A2A protocol: Pydantic request → async method → Pydantic response.

### Entrypoint 1: `analyze_market_opportunity`

**Signature:**
```python
async def analyze_market_opportunity(request: MarketAnalysisRequest) -> MarketAnalysisResponse
```

**Purpose:** Reactive mode. Contextualise a KPI situation with market signals.

**Input Model:** `MarketAnalysisRequest`
- `situation` (optional): Serialised Situation object from SA
- `kpi_name` (optional): E.g., "Gross Margin (%)"
- `kpi_delta` (optional): % change from baseline
- `trigger_direction`: "problem" | "opportunity" | "proactive_scan"
- `sector` (optional): Company sector
- `company_name` (optional): Company identifier for competitor context
- `company_context` (optional): Dict with company size, geography, segment
- `principal_context` (optional): Principal role/department for filtering signals
- Standard base fields: `request_id`, `principal_id`, `timestamp`, `principal_context`

**Output Model:** `MarketAnalysisResponse`
- `signals`: List of `MarketSignal` objects (top 3 ranked by relevance + confidence)
- `competitor_signals`: List of `CompetitorSignal` objects (top 2)
- `industry_context`: `IndustryContext` with tailwinds/headwinds
- `opportunity_score`: Float 0–1 (null if problem mode)
- `threat_score`: Float 0–1 (null if opportunity mode)
- `key_questions`: List of strings for SF to address (e.g., "Is our pricing aligned with competitor moves?")
- `sf_context`: Dict ready for SF's `market_analysis_input` field
- `audit_log`: List of decisions/queries for compliance
- Standard base fields: `response_id`, `timestamp`, `status`

**Calling Agent(s):** SA Agent (during reactive workflow), SF Agent (optional enrichment).

**Trigger Condition:** SA workflow after situation card creation; optional in SF synthesis.

---

### Entrypoint 2: `scan_for_opportunities`

**Signature:**
```python
async def scan_for_opportunities(request: MarketScanRequest) -> MarketScanResponse
```

**Purpose:** Proactive mode. Scan sectors for emerging signals and opportunities.

**Input Model:** `MarketScanRequest`
- `sectors`: List of strings (e.g., ["Financial Services", "Healthcare"])
- `topics` (optional): List of specific topics (e.g., ["AI adoption", "regulatory", "M&A"])
- `principal_context` (optional): Dict for filtering (e.g., principal role, company segment)
- `scan_depth`: "quick" (cached signals only) | "standard" (fresh Perplexity query) | "deep" (multi-query synthesis)
- Standard base fields: `request_id`, `principal_id`, `timestamp`

**Output Model:** `MarketScanResponse`
- `signals`: List of all discovered `MarketSignal` objects, ranked by recency + confidence
- `surfaced_opportunities`: List of dicts with `title`, `description`, `opportunity_score`, `affected_kpis`, `recommended_workflow`
- `surfaced_threats`: List of dicts with `title`, `description`, `threat_score`, `affected_kpis`, `affected_sectors`
- `recommended_workflows`: List of workflow names to trigger (e.g., ["problem_deep_analysis", "innovation_driver"])
- `audit_log`: List of queries and synthesis steps
- Standard base fields: `response_id`, `timestamp`, `status`

**Calling Agent(s):** Orchestrator (scheduled task), Principal/UI (on-demand).

**Trigger Condition:** Scheduled (weekly), or manual principal request via API.

---

### Entrypoint 3: `get_competitive_context`

**Signature:**
```python
async def get_competitive_context(request: CompetitiveContextRequest) -> CompetitiveContextResponse
```

**Purpose:** Lightweight mode. Validate an option against competitive moves during SF synthesis.

**Input Model:** `CompetitiveContextRequest`
- `option_title`: Proposed option title (e.g., "Implement dynamic pricing for SKU 042")
- `option_description` (optional): Detailed description
- `kpi_name` (optional): KPI affected (e.g., "Gross Margin (%)")
- `sector` (optional): Market sector
- `company_context` (optional): Company identifiers
- Standard base fields: `request_id`, `principal_id`, `timestamp`

**Output Model:** `CompetitiveContextResponse`
- `differentiation_assessment`: Prose description (e.g., "Your pricing move is differentiated from Salesforce's recent $X cut; aligns with market consolidation trend.")
- `competitor_actions`: List of top `CompetitorSignal` objects relevant to the option
- `market_validation`: Enum: "validated" (others doing this) | "commoditised" (widespread) | "novel" (leading edge) | "risky" (few attempt, high failure rate)
- `confidence`: Float 0–1 in assessment
- `audit_log`: List of signals considered
- Standard base fields: `response_id`, `timestamp`, `status`

**Calling Agent(s):** SF Agent (during synthesis).

**Trigger Condition:** Optional, on-demand during SF option synthesis.

---

## 5. Pydantic Data Models

All models inherit from `A9AgentBaseModel`, `A9AgentBaseRequest`, or `A9AgentBaseResponse` (defined in `src/agents/shared/a9_agent_base_model.py`).

**File location:** `src/agents/models/market_analysis_models.py`

### Enums

```python
class MarketSignalType(str, Enum):
    """Types of market signals MA can surface."""
    COMPETITOR_MOVE = "competitor_move"           # Pricing, product, M&A, strategy shifts
    INDUSTRY_TREND = "industry_trend"             # Consolidation, technology adoption, practice shifts
    REGULATORY_CHANGE = "regulatory_change"       # Policy, compliance, reporting changes
    DEMAND_SIGNAL = "demand_signal"               # Customer demand shifts, market size, TAM
    PRICING_SIGNAL = "pricing_signal"             # Industry pricing benchmarks, cost inflation
    TECHNOLOGY_SHIFT = "technology_shift"         # New platforms, capabilities, disruption
    MACRO_ECONOMIC = "macro_economic"             # Interest rates, inflation, recession, forex
    SUPPLY_CHAIN = "supply_chain"                 # Disruptions, lead times, sourcing changes


class MarketSignalDirection(str, Enum):
    """Signal direction relative to company strategy."""
    POSITIVE = "positive"                         # Tailwind, opportunity, validation
    NEGATIVE = "negative"                         # Headwind, risk, constraint
    NEUTRAL = "neutral"                           # Informational, low impact
```

### Core Models

```python
class MarketSignal(A9AgentBaseModel):
    """Structured market signal from external sources."""
    signal_id: str = Field(..., description="Unique signal identifier (UUID format)")
    signal_type: MarketSignalType = Field(..., description="Type of signal")
    direction: MarketSignalDirection = Field(..., description="Positive/negative/neutral impact")
    title: str = Field(..., description="Short signal title (< 80 chars)")
    description: str = Field(..., description="Detailed description (< 500 chars)")
    source: str = Field(..., description="Source name: 'Perplexity', 'Claude', 'Financial Times', etc.")
    source_url: Optional[str] = Field(default=None, description="URL to original source if available")
    confidence: float = Field(..., ge=0, le=1, description="Confidence 0–1 (lower if LLM-derived)")
    recency_days: Optional[int] = Field(default=None, description="Days since signal occurred; null if LLM-derived")
    geographic_scope: Optional[str] = Field(default=None, description="'Global', 'EMEA', 'APAC', etc., or null for sector-wide")
    is_llm_derived: bool = Field(default=False, description="True if synthesised by Claude; false if cited from Perplexity")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="ISO format timestamp")


class CompetitorSignal(A9AgentBaseModel):
    """Specific competitor action or position."""
    competitor_name: str = Field(..., description="Competitor company name")
    action: str = Field(..., description="Action taken: pricing move, product launch, M&A, etc.")
    implications: List[str] = Field(default_factory=list, description="List of strategic implications for the customer")
    affected_kpis: List[str] = Field(default_factory=list, description="KPIs this action affects: ['Gross Margin (%)', 'Market Share']")
    source: str = Field(..., description="Source of intelligence")
    confidence: float = Field(default=0.7, ge=0, le=1, description="Confidence in accuracy of this signal")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="ISO format timestamp")


class IndustryContext(A9AgentBaseModel):
    """Industry-level benchmarks and trends."""
    sector: str = Field(..., description="Industry sector name (e.g., 'Financial Services')")
    subsector: Optional[str] = Field(default=None, description="Subsector if relevant (e.g., 'Insurance')")
    trend_summary: str = Field(..., description="One-paragraph summary of industry trends (< 300 chars)")
    tailwinds: List[str] = Field(default_factory=list, description="List of positive trends (e.g., 'AI adoption', 'M&A consolidation')")
    headwinds: List[str] = Field(default_factory=list, description="List of negative trends (e.g., 'margin compression', 'regulatory tightening')")
    benchmark_context: Optional[str] = Field(default=None, description="Quantified benchmarks (e.g., 'Industry gross margin: 35–45%'; 'Average R&D spend: 12–18% revenue')")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="ISO format timestamp")
```

### Request Models

```python
class MarketAnalysisRequest(A9AgentBaseRequest):
    """Request to analyze market context for a KPI situation."""
    situation: Optional[Dict[str, Any]] = Field(default=None, description="Serialised Situation object from SA")
    kpi_name: Optional[str] = Field(default=None, description="KPI name (e.g., 'Gross Margin (%)')")
    kpi_delta: Optional[float] = Field(default=None, description="% change in KPI (e.g., -3.5)")
    trigger_direction: str = Field(..., description="'problem' (negative KPI) | 'opportunity' (positive KPI) | 'proactive_scan'")
    sector: Optional[str] = Field(default=None, description="Company sector")
    company_name: Optional[str] = Field(default=None, description="Company identifier")
    company_context: Optional[Dict[str, Any]] = Field(default=None, description="Company metadata: size, geography, segment")
    principal_context: Optional[Dict[str, Any]] = Field(default=None, description="Principal metadata for filtering signals")


class MarketScanRequest(A9AgentBaseRequest):
    """Request to scan for emerging market opportunities/threats."""
    sectors: List[str] = Field(..., description="List of sectors to scan")
    topics: Optional[List[str]] = Field(default=None, description="Specific topics: ['AI adoption', 'regulatory', 'M&A']")
    principal_context: Optional[Dict[str, Any]] = Field(default=None, description="Principal metadata for filtering")
    scan_depth: str = Field(default="standard", description="'quick' (cached) | 'standard' (fresh query) | 'deep' (multi-query)")


class CompetitiveContextRequest(A9AgentBaseRequest):
    """Request lightweight competitive validation of an option."""
    option_title: str = Field(..., description="Option title (e.g., 'Implement dynamic pricing')")
    option_description: Optional[str] = Field(default=None, description="Detailed option description")
    kpi_name: Optional[str] = Field(default=None, description="KPI affected by option")
    sector: Optional[str] = Field(default=None, description="Sector context")
    company_context: Optional[Dict[str, Any]] = Field(default=None, description="Company metadata")
```

### Response Models

```python
class MarketAnalysisResponse(A9AgentBaseResponse):
    """Structured market analysis output."""
    signals: List[MarketSignal] = Field(default_factory=list, description="Top 3 relevant market signals")
    competitor_signals: List[CompetitorSignal] = Field(default_factory=list, description="Top 2 competitor actions")
    industry_context: Optional[IndustryContext] = Field(default=None, description="Industry-level context")
    opportunity_score: Optional[float] = Field(default=None, ge=0, le=1, description="Opportunity score (null if problem mode)")
    threat_score: Optional[float] = Field(default=None, ge=0, le=1, description="Threat score (null if opportunity mode)")
    key_questions: List[str] = Field(default_factory=list, description="Questions SF should address with options")
    sf_context: Dict[str, Any] = Field(default_factory=dict, description="Ready-to-use dict for SF's market_analysis_input field")
    audit_log: Optional[List[Dict[str, Any]]] = Field(default=None, description="Compliance audit trail: queries, API calls, synthesis steps")


class MarketScanResponse(A9AgentBaseResponse):
    """Output from proactive market scan."""
    signals: List[MarketSignal] = Field(default_factory=list, description="All discovered signals, ranked by recency + confidence")
    surfaced_opportunities: List[Dict[str, Any]] = Field(default_factory=list, description="Structured opportunities: title, description, opportunity_score, affected_kpis")
    surfaced_threats: List[Dict[str, Any]] = Field(default_factory=list, description="Structured threats: title, description, threat_score, affected_sectors")
    recommended_workflows: List[str] = Field(default_factory=list, description="Workflow names to trigger: ['problem_deep_analysis', 'innovation_driver']")
    audit_log: Optional[List[Dict[str, Any]]] = Field(default=None, description="Compliance audit trail")


class CompetitiveContextResponse(A9AgentBaseResponse):
    """Lightweight competitive validation output."""
    differentiation_assessment: str = Field(..., description="Prose assessment of option differentiation vs. competitors")
    competitor_actions: List[CompetitorSignal] = Field(default_factory=list, description="Relevant competitor signals")
    market_validation: str = Field(..., description="'validated' | 'commoditised' | 'novel' | 'risky'")
    confidence: float = Field(default=0.7, ge=0, le=1, description="Confidence in assessment")
    audit_log: Optional[List[Dict[str, Any]]] = Field(default=None, description="Compliance audit trail")
```

---

## 6. sf_context Integration Contract

The `sf_context` dict populated by MA and passed as `market_analysis_input` to SF is **critical**. SF's synthesis LLM prompt already includes `market_analysis_input` as structured context.

### Exact JSON Structure

```json
{
  "market_signals": [
    {
      "signal_id": "uuid",
      "signal_type": "competitor_move",
      "direction": "positive|negative|neutral",
      "title": "Salesforce announces 15% SMB tier price reduction",
      "description": "Salesforce cut pricing on SMB tier by 15% effective March 2026, signaling price competition intensifying in mid-market CRM",
      "source": "Perplexity",
      "confidence": 0.95,
      "recency_days": 3,
      "is_llm_derived": false
    }
  ],
  "competitor_context": [
    {
      "competitor_name": "Salesforce",
      "action": "15% price reduction on SMB tier",
      "implications": ["Market commoditising SMB tier", "Price-based competition intensifying", "Volume expected to shift upmarket"],
      "affected_kpis": ["Gross Margin (%)", "Market Share (%)"],
      "confidence": 0.95
    }
  ],
  "industry_benchmarks": "Financial Services gross margin benchmarks: 35–45% (industry average 40%); your 38% is slightly below peer average. Regulatory tailwind: Open Banking adoption rising; headwind: margin compression in deposit products.",
  "external_risk_factors": [
    "Supply chain shortage in semiconductor fabs projected Q3 2026 — hardware redesigns will face 60-day delays",
    "ECB interest rate cuts forecast Q2 2026 — margin compression expected in lending products"
  ],
  "opportunity_indicators": [
    "Three market leaders adopted SKU consolidation in Q1 2026 — validates feasibility of your cost-to-serve reduction",
    "AI-powered underwriting adoption rising in insurance — opportunity to leapfrog competitors with faster claims processing"
  ],
  "key_questions_for_sf": [
    "Is your repricing action aligned with or differentiated from competitor moves?",
    "What market-wide trends validate or constrain the proposed solution?",
    "Are there supply-chain headwinds that affect implementation timing?"
  ]
}
```

### How SF Uses It

SF's synthesis LLM prompt includes:
```
If market_analysis_input is provided, consider these external signals when evaluating options:
- Market signals: [context]
- Competitor moves: [context]
- Industry benchmarks: [context]
- Risk factors: [context]
- Opportunity tailwinds: [context]

Ensure recommendations are:
1. Differentiated from competitor moves (avoid commoditised responses)
2. Realistic given supply-chain/regulatory headwinds
3. Amplified by market tailwinds
```

**What MA must ensure:**
- `market_signals`: Top 3, ranked by relevance (confidence × recency weighting)
- `competitor_context`: Top 2, with clear implications for the customer
- `industry_benchmarks`: One paragraph, quantified
- `external_risk_factors` and `opportunity_indicators`: Both lists, each 2–3 items, actionable
- `key_questions_for_sf`: 3–5 questions, phrased as "Is X…?" or "Are there Y…?" to guide option synthesis

---

## 7. LLM Query Design

All LLM calls route through `A9_LLM_Service_Agent` via the Orchestrator. Provider: Anthropic Claude. Models vary by task.

### For `analyze_market_opportunity`

**Step 1: Fast KPI Classification (Haiku)**
- **Model:** `claude-haiku-4-5-20251001`
- **Purpose:** Classify the KPI situation into signal type buckets (classify cost-of-goods-sold decline → "cost/efficiency trend opportunity" → search "supply chain, manufacturing cost, labor efficiency trends").
- **Input:** KPI name, delta, trigger_direction
- **Output:** Structured JSON with signal_type, sector, search_focus
- **LLM call:** `A9_LLM_Service_Agent.generate(model=..., task="kpi_classification", ...)`

**Step 2: Web-Grounded Research (Perplexity API)**
- **Tool:** Perplexity API (separate from Claude stack; requires `PERPLEXITY_API_KEY` env var)
- **Query template:** `"[sector] [kpi_name] trends [signal_type] competitors [current year] market"`
  - Example: `"Financial Services gross margin trends competitors pricing benchmarks 2026 market"`
- **Output:** Cited, up-to-date sources with snippets
- **Fallback if Perplexity unavailable:** Use Claude's native knowledge, mark outputs `is_llm_derived: True`, cap confidence at 0.6, set `recency_days: null`

**Step 3: Synthesis (Sonnet)**
- **Model:** `claude-sonnet-4-6`
- **Purpose:** Synthesise Perplexity output + KPI context into structured `MarketAnalysisResponse`
- **Input:** KPI context + Perplexity citations
- **Output:** MarketSignal list, CompetitorSignal list, IndustryContext, opportunity/threat scores, sf_context dict
- **LLM call:** `A9_LLM_Service_Agent.generate(model="claude-sonnet-4-6", task="market_synthesis", ...)`

**Latency budget:** 10–15 seconds (Perplexity 5s + Sonnet 5s + overhead 5s).

---

### For `scan_for_opportunities`

**Quick Scan** (scan_depth="quick")
- Return cached signals from last 24 hours
- Haiku classification of top signals for relevance
- No fresh LLM queries
- Latency: < 2 seconds

**Standard Scan** (scan_depth="standard")
- One Perplexity query per sector: `"[sector] market trends opportunities risks 2026"`
- Sonnet synthesis across all sectors
- Rank by opportunity_score
- Latency: 30–45 seconds

**Deep Scan** (scan_depth="deep")
- Multi-query Perplexity per sector (one query per topic: AI adoption, regulatory, M&A, pricing, supply chain)
- Haiku pre-filtering of results
- Sonnet synthesis + cross-sector opportunity connection
- Generate recommended_workflows (e.g., "If AI adoption opportunity is high, recommend innovation_driver workflow")
- Latency: 60–90 seconds

---

### For `get_competitive_context`

**Lightweight Synthesis**
- Haiku classifies option into signal type
- Look up cached competitor signals matching signal type + sector
- Sonnet generates quick differentiation_assessment (100 words)
- Output market_validation enum based on frequency of competitor actions
- Latency: 5–10 seconds (mostly cache hits)

---

## 8. Data Sources

### Primary: Perplexity API

- **Coverage:** Real-time web search with cited sources
- **Advantage:** Current, up-to-date signals with attribution
- **Integration:** OpenAI-compatible endpoint; requires separate API key (`PERPLEXITY_API_KEY`)
- **Limitations:** Requires active internet; cost per query (~$0.01–0.05 per call)
- **Fallback:** If Perplexity unavailable, use Claude native knowledge (marked `is_llm_derived: True`, confidence capped at 0.6)

### Secondary: Claude Native Knowledge

- **Coverage:** Training data up to Feb 2025; includes competitor moves, industry trends through Feb 2025
- **Used when:** Perplexity unavailable or for lightweight validation queries
- **Limitation:** Not real-time; knowledge cutoff caveat required
- **Confidence handling:** Always mark `is_llm_derived: True`; cap confidence at 0.6–0.7; set `recency_days: null`

### Future Integrations (Post-MVP)

- Financial news APIs (Bloomberg, FactSet, Refinitiv)
- Regulatory change feeds (SEC EDGAR, EU CELEX)
- Industry analyst reports (Gartner, Forrester, McKinsey)
- Pricing intelligence databases (Competiscan, Wiser)
- Supply-chain monitoring (Everstream, Everline)

---

## 9. Workflow Integration

| Workflow | Step | MA Entrypoint | Input | Role | Status |
|----------|------|---------------|-------|------|--------|
| **Opportunity Deep Analysis** | After Data Product Agent queries | `analyze_market_opportunity` | Situation object | Assess market context for scaling/replicating opportunity | Optional |
| **Problem Deep Analysis** | After Deep Analysis Agent | `analyze_market_opportunity` | Situation object + DA insights | Provide market threat/constraint context for SF | Optional |
| **Solution Finding** | During SF synthesis (optional enrichment) | `get_competitive_context` | Each candidate option | Validate option differentiation vs. competitors | Optional |
| **Innovation Driver** | MA feeds opportunity signals | `scan_for_opportunities` | Sector list | Surface emerging opportunities to trigger innovation workflows | Optional |
| **Business Optimization** | Optional enrichment step | `analyze_market_opportunity` | KPI + company context | Contextualize optimization targets with market benchmarks | Optional |
| **Value Assurance** | 30/60/90-day post-implementation review | `analyze_market_opportunity` | Same KPI as original solution | Isolate intervention impact from market-wide tailwinds | Optional |

---

## 10. Value Assurance Hook

**Problem:** When a solution is implemented and the KPI recovers, how much of the improvement was driven by the intervention vs. market-wide tailwinds?

**Example:** A company implements a gross margin repricing action (reprices SKU 042 upward). Six months later, gross margin has recovered from 35% to 38%. Was this recovery due to the repricing action, or because the entire industry recovered from commodity price deflation?

**MA's Role:**

1. **Baseline (T0):** When SF proposes repricing, MA provides competitor pricing context + industry margin benchmarks. Result: Documented that benchmarks were 35–45% (industry avg 40%) at T0.

2. **Post-Implementation (T+30/60/90):** Value Assurance workflow triggers MA again with same KPI.
   - MA queries current competitor pricing, industry margins, and cost inflation
   - MA determines whether the industry recovered by 2% (market-wide tailwind) or stayed flat (intervention-driven)
   - MA outputs: "Industry margin benchmarks have risen from 40% avg to 41% avg (+1% tailwind). Your +3% recovery is 67% intervention-driven, 33% tailwind-driven. ROI attribution: intervention value $X, market value $Y."

3. **Honest Reporting:** Change Management Agent (in Value Assurance workflow) uses MA's attribution to separate intervention ROI from market effects. This prevents overestimating intervention impact.

**Implementation:** MA stores baseline signals at T0 (audit_log); `scan_for_opportunities` at T+30/60/90 compares current signals against baseline to isolate changes.

---

## 11. Technical Requirements

### A2A Protocol Compliance

- All entrypoints accept `A9AgentBaseRequest` subclasses; return `A9AgentBaseResponse` subclasses
- All I/O is Pydantic models (no raw dicts)
- Request/response IDs and timestamps mandatory
- Serialization via `.model_dump()` (Pydantic v2)
- No direct dict/JSON handling in agent code; models handle serialization

### LLM Routing

- **NO direct imports:** No `from anthropic import Anthropic` in agent code
- **ALWAYS route through:** `A9_LLM_Service_Agent` via Orchestrator
- **Model specification:** `A9_LLM_Service_Agent.generate(model="claude-sonnet-4-6", ...)` or use env var overrides (`CLAUDE_MODEL_MARKET_ANALYSIS`)
- **Token tracking:** Logged in audit_log (input_tokens, output_tokens per call)

### External API Integration (Perplexity)

- API key: `PERPLEXITY_API_KEY` env var (required for production; optional for MVP with fallback to Claude)
- Rate limiting: Implement backoff (exponential, max 3 retries)
- Timeout: 15 seconds per Perplexity call
- Fallback: If Perplexity unavailable, mark outputs `is_llm_derived: True`, cap confidence at 0.6

### HITL (Human-in-the-Loop)

- Not required for MA MVP (agent provides recommendations, SF/Value Assurance agents handle HITL)
- Future: MA may require principal approval for "risky" or "novel" signals before passing to SF
- Config-driven flag: `hitl_enabled` (future; not MVP)

### Async & Lifecycle

- All methods are async: `async def analyze_market_opportunity(...)`
- Implement lifecycle methods:
  - `async def create(config)` → Initialize Perplexity client, validate API key
  - `async def connect()` → Test Perplexity connectivity; fallback to Claude if unavailable
  - `async def disconnect()` → Cleanup (none needed for HTTP client, but required by protocol)
- Registry instantiation: `await AgentRegistry.get_agent("A9_Market_Analysis_Agent")`

### Pydantic Validation

- All models defined in `src/agents/models/market_analysis_models.py`
- Config: `ConfigDict(extra="allow", populate_by_name=True, validate_assignment=True)`
- Validation errors: Raise `AgentInputValidationError` (from `src.agents.exceptions`)
- No silent failures; all validation errors logged and raised

### Logging Standard

- **No print() statements**
- **Target:** A9_SharedLogger (not yet implemented; interim use `logging.getLogger(__name__)`)
- **Audit log fields:**
  - `timestamp`: ISO format
  - `action`: "kpi_classification", "perplexity_query", "sonnet_synthesis", "cache_hit"
  - `status`: "success", "fallback" (if Perplexity unavailable), "error"
  - `details`: Dict with query, response snippet, latency, token counts

### Error Handling

| Error Type | Handling |
|---|---|
| Perplexity API unavailable | Log warning; fallback to Claude; mark `is_llm_derived: True`; confidence capped 0.6 |
| LLM API error (rate limit, timeout) | Retry with exponential backoff (max 3); if all fail, return empty signals with error in audit_log |
| Invalid Pydantic input | Raise `AgentInputValidationError`; log validation errors |
| Network timeout | Return partial results (e.g., cached signals only) with "degraded" status |

---

## 12. Implementation Guidance

### File Structure

```
src/agents/
├── new/
│   └── a9_market_analysis_agent.py           # Main agent implementation
├── models/
│   └── market_analysis_models.py             # Pydantic models (defined in Section 5)
└── protocols/
    └── market_analysis_protocol.py           # (Optional) @runtime_checkable Protocol

tests/unit/
└── test_a9_market_analysis_agent_unit.py     # Unit tests (40–60% coverage target)

docs/prd/agents/
└── a9_market_analysis_agent_prd.md           # This document
```

### Implementation Order (Suggested)

1. **Models** (1–2 hours)
   - Define all Pydantic models in `market_analysis_models.py`
   - Test Pydantic validation with unit tests

2. **Agent skeleton** (2–3 hours)
   - Implement `A9_Market_Analysis_Agent` class
   - Implement lifecycle: `create()`, `connect()`, `disconnect()`
   - Stub all three entrypoints to return empty responses

3. **Perplexity integration** (3–4 hours)
   - Initialize Perplexity client (OpenAI-compatible endpoint)
   - Implement query builder (step 2 of `analyze_market_opportunity`)
   - Implement fallback to Claude if Perplexity unavailable
   - Test with mock Perplexity responses

4. **LLM synthesis (Haiku + Sonnet)** (4–5 hours)
   - Implement KPI classification (Haiku) in step 1
   - Implement response synthesis (Sonnet) in step 3
   - Route all LLM calls through `A9_LLM_Service_Agent` via Orchestrator
   - Test with mock LLM responses

5. **Entrypoint implementations** (5–6 hours)
   - `analyze_market_opportunity`: Full 3-step flow
   - `scan_for_opportunities`: Implement quick/standard/deep logic
   - `get_competitive_context`: Lightweight path with caching
   - Test end-to-end with live Perplexity + Claude

6. **Caching & performance** (2–3 hours)
   - Cache market signals in-memory (TTL: 24 hours for quick scans)
   - Implement latency budget checks (log warnings if > 15s)
   - Cache competitor signals by competitor_name + sector

7. **Testing & documentation** (3–4 hours)
   - Unit tests: 40–60% coverage (focus on entrypoints, Pydantic models)
   - Integration tests: test with Orchestrator
   - Agent card: `src/agents/new/cards/a9_market_analysis_agent_card.md`

**Total:** ~23–27 hours for MVP (Perplexity + Claude, no advanced caching, no HITL).

### Key Pitfalls to Avoid

1. **Direct Perplexity client in agent code** 🔴
   - **Wrong:** `from perplexity import Client; client = Client(...)`
   - **Right:** Wrap Perplexity in a service class; call it from the agent; handle failures gracefully

2. **Hardcoding LLM models** 🔴
   - **Wrong:** `claude_service.generate(model="claude-sonnet-4-6", ...)`
   - **Right:** Use `A9_LLM_Service_Agent` routing; allow model override via env vars (`CLAUDE_MODEL_MARKET_ANALYSIS`)

3. **No fallback when Perplexity is down** 🔴
   - **Wrong:** Fail the entire request if Perplexity unavailable
   - **Right:** Fallback to Claude with `is_llm_derived: True`, confidence capped, audit_log note

4. **Returning raw dicts instead of Pydantic models** 🔴
   - **Wrong:** `return {"signals": [...], "competitor_signals": [...]}`
   - **Right:** `return MarketAnalysisResponse(signals=..., competitor_signals=..., ...)`

5. **Not validating Pydantic input** 🔴
   - **Wrong:** Accept dict, convert to Pydantic silently
   - **Right:** Validate at entrypoint; raise `AgentInputValidationError` if invalid

6. **Missing audit_log** 🔴
   - **Audit_log must include:** LLM calls, Perplexity queries, fallbacks, latency, token counts
   - **Used for:** Compliance, debugging, understanding why signals were surfaced

### Key Integration Points

**Orchestrator:** MA is called via `await orchestrator.call_agent("A9_Market_Analysis_Agent", "analyze_market_opportunity", request)`

**A9_LLM_Service_Agent:** All LLM calls route through Orchestrator:
```python
# DO NOT do this:
# from src.llm_services.claude_service import ClaudeService
# response = ClaudeService().generate(...)

# DO do this:
llm_agent = await AgentRegistry.get_agent("A9_LLM_Service_Agent")
response = await llm_agent.generate(model="claude-haiku-4-5-20251001", task="kpi_classification", ...)
```

**Perplexity:** Separate API client (not through Orchestrator), but handle in a dedicated service class:
```python
# src/llm_services/perplexity_service.py
class PerplexityService:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")

    async def query(self, prompt: str, model: str = "sonar-pro") -> dict:
        # Query with retry logic and fallback
        ...
```

---

## 13. Success Metrics

### Functional Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| Entrypoint 1 latency (analyze_market_opportunity) | < 15s | Inline with SA→DA→SF workflow; must not block user experience |
| Entrypoint 2 latency (scan_for_opportunities, standard) | 30–60s | Asynchronous; acceptable for scheduled/on-demand scans |
| Entrypoint 3 latency (get_competitive_context) | < 10s | Used in SF synthesis; must be fast for inline validation |
| Signal relevance to KPI (user feedback) | > 70% | Signals must be actionable and relevant to the situation |
| Perplexity fallback success rate | > 95% | If Perplexity unavailable, Claude fallback must work reliably |

### Quality Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| Competitor signal confidence (avg) | > 0.75 | High-confidence intel; reflects Perplexity citation quality |
| Market signal recency (avg days) | < 14 | Signals must be recent; avoid stale data |
| sf_context completeness | 100% | All required fields populated (market_signals, competitor_context, benchmarks, risk/opportunity factors, key_questions) |
| Audit_log completeness | 100% | All LLM calls, Perplexity queries, and fallbacks logged for compliance |

### Integration Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| SF usage of market_analysis_input | TBD post-MVP | Measure % of SF calls that receive and use market context |
| Principal engagement with surfaced opportunities (scan mode) | TBD post-MVP | Track % of surfaced opportunities that trigger workflows or principal action |
| Value Assurance attribution accuracy | TBD post-MVP | Measure how well MA separates intervention ROI from market tailwinds (requires comparison against actual outcomes) |

### Cost Metrics (Post-MVP)

| Metric | Target | Notes |
|--------|--------|-------|
| Perplexity cost per analyze_market_opportunity call | < $0.05 | One query per call; optimize prompt to reduce tokens |
| Claude cost per synthesis call | < $0.10 | Sonnet synthesis; should be fast for inline latency |
| Total MA operational cost per month | < $500 | Assumes ~500 reactive calls/month + 50 proactive scans |

---

## 14. Out of Scope for MVP

- **Sentiment analysis & NLP on signals:** Classifying signal tone beyond simple positive/negative/neutral
- **Predictive analytics:** Forecasting future market moves (requires time-series models)
- **Deeper provider integrations:** Bloomberg, FactSet, Refinitiv, Everstream (post-MVP)
- **Real-time alerting:** Pushing alerts to principals on signal discovery (post-MVP; requires async message queue)
- **Collaborative analysis UI:** Frontend for principals to comment on/challenge signals (post-MVP)
- **Signal persistence:** Storing signals in database (MVP uses in-memory cache only)
- **HITL approval workflow:** Principal approval of signals before passing to SF (post-MVP; future config flag)
- **Multi-language support:** All signals in English only (post-MVP)
- **Supply-chain visualization:** Visual maps of supply-chain disruptions (post-MVP, requires external data)

---

## 15. Change Log

- **2026-03-10:** Created comprehensive MVP PRD. Defined three trigger modes (reactive, proactive, lightweight), all entrypoints with Pydantic models, sf_context integration contract, LLM query design (Haiku classification + Perplexity research + Sonnet synthesis), Perplexity API integration with Claude fallback, Value Assurance hook for honest ROI attribution, technical requirements (A2A protocol, async, logging, error handling), implementation guidance (27-hour estimate), and success metrics.
