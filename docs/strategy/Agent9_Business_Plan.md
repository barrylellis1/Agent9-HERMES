# Agent9 Business Plan
**Last Updated:** March 2026
**Version:** 1.5 — Pilot Data Onboarding ("bring your own extract") added to GTM Phase 1; production data backend roadmap (Snowflake, Databricks, SQL Server, SAP Datasphere); DuckDB deprecated as customer-facing backend

---

## Executive Summary

**Agent9** is an AI-powered decision intelligence platform that delivers continuous financial monitoring, multi-perspective analysis, structured decision support, and post-implementation ROI validation for mid-market CFOs and PE portfolio operations teams. The platform combines registry-driven domain context, continuous KPI monitoring, and external market intelligence to surface the right insight for the right executive — automatically, continuously, and with a complete audit trail.

Agent9 addresses five independent value propositions — each justifiable on its own, compounding together:
1. **Always-on monitoring** — proactive situation detection across KPIs before problems become crises
2. **Consulting-quality insight on demand** — structured root cause analysis, multi-perspective options debate, and board-ready narrative in hours not weeks
3. **Institutional memory and decision audit trail** — KPI definitions, decision rationale, and outcome tracking that survives executive turnover and satisfies compliance requirements
4. **Opportunity detection** — positive KPI outperformance detected, market context surfaced, capture options generated (not just problem response)
5. **Initiative tracking and proven ROI** — accepted solutions tracked post-implementation; actual KPI recovery attributed to the intervention vs. market tailwinds

**The primary market is not consulting displacement.** The largest addressable segment is the mid-market ($50M–$500M revenue) that never engaged MBB consulting because of cost. Agent9 is net-new capability for these companies — not a cheaper substitute.

**Current Stage:** Pre-revenue, platform built (~100K LOC), moonlighting development
**Go-to-Market Launch:** Q2 2026 (demo-ready, warm network outreach)
**Primary Entry Buyer:** VP FP&A / Head of Financial Planning (faster cycle) → CFO champion for expansion
**Target:** $200K-$500K ARR within 18 months of first customer (raised from $150K-$350K — shipped MA/VA/Opportunity enable higher ACV and stronger renewal rates)
**Exit Strategy:** Strategic acquisition at $2M-$3M ARR for $15M-$30M (infrastructure/data platform framing)

---

## 1. Market Opportunity

### Market Size
- **Total Addressable Market (TAM):** $800B global consulting market
- **Serviceable Addressable Market (SAM):** $50B (mid-market + PE portfolio operations)
- **Serviceable Obtainable Market (SOM):** $5M-$10M (Year 3 target — 50-100 customers at $50K-$100K ACV)

*Note: SOM is deliberately conservative. As a bootstrapped solo founder, capturing even $5M of a $50B SAM represents meaningful traction and positions for acquisition or Series A.*

### Market Trends
- Enterprise AI adoption accelerating
- Consulting firms under margin pressure
- Demand for speed and cost reduction
- Regulatory push for AI explainability and audit trails

---

## 2. Product Vision

### Core Value Proposition
"AI-powered decision intelligence for mid-market CFOs — continuous monitoring, structured analysis, and board-ready recommendations with a complete audit trail."

### Five Value Pillars (Independent, Compounding)

**Pillar 1 — Always-On Monitoring (replaces absence of something)**
- 24/7 KPI surveillance across Finance and Sales domains with multi-timeframe thresholds
- Proactive anomaly detection before the CFO asks the question
- Situation lifecycle management (Open → Acknowledged → Assigned → Resolved)
- *Replaces:* Manual weekly dashboard reviews, reactive fire-fighting

**Pillar 2 — Consulting-Quality Insight on Demand (replaces expensive substitute OR net-new for never-engaged market)**
- Structured SCQA root cause analysis (Situation, Complication, Question, Answer)
- Multi-perspective solution debate with trade-off matrix (Financial, Operational, Strategic, Risk lenses)
- Role-personalised output: same KPI, different framing for CFO (analytical), COO (pragmatic), CEO (visionary)
- External market intelligence via Market Analysis Agent (Perplexity + Claude synthesis)
- *For consulting users:* replaces $500K-$2M engagements; delivers in hours not weeks
- *For never-engaged mid-market:* net-new structured analysis capability at a fraction of the cost ($44K-$100K ACV)

**Pillar 3 — Institutional Memory and Decision Audit Trail (fills gap nothing else addresses)**
- KPI definitions encoded with exact SQL logic, data lineage, and GL account mappings
- Decision provenance: every option considered, trade-off evaluated, outcome tracked
- Survives executive turnover — the definition of "Gross Margin" never walks out the door again
- *Replaces:* Nothing currently — this capability does not exist in any comparable tool

**Pillar 4 — Opportunity Detection (proactive, not just reactive)**
- Positive KPI outperformance detected automatically alongside problem alerts
- Market Analysis Agent surfaces external market context for organic growth signals
- Opportunity framing in Solution Finder: "capitalise on" rather than "resolve"
- *Replaces:* Ad hoc awareness; systematic opportunity capture that previously required a dedicated strategy team

**Pillar 5 — Initiative Tracking and Proven ROI (self-validating feedback loop)**
- At HITL approval: KPI baseline captured, estimated ROI range recorded
- Post-implementation: KPI monitored against baseline; recovery attributed to intervention vs. market tailwind
- Creates a reinforced learning loop — Agent9 gets better as it accumulates decision outcomes
- *Replaces:* Nothing currently — ROI attribution from business intelligence decisions does not exist in any tool

### Key Differentiators
1. **Registry-driven domain intelligence** — KPIs, principals, business processes, data products encoded per customer; deep context no generic AI provides
2. **Always-on monitoring** — proactive, not reactive; runs 24/7 between consulting engagements
3. **Role-personalised framing** — same data, right narrative for each executive
4. **Decision audit trail** — complete provenance for compliance, board reporting, and investor scrutiny
5. **5-day onboarding** — first situation card in one week, not 8-12 weeks (see Onboarding Moat doc)
6. **Branded expertise** — partner consulting methodology encoded as agents (Year 3+)

### Platform Capabilities (As of March 2026)
- ✅ Multi-agent orchestration framework (A2A protocol-compliant)
- ✅ Situation Awareness workflow (problem detection + positive KPI opportunity detection)
- ✅ Deep Analysis workflow (SCQA, Is/Is Not, BigQuery routing)
- ✅ Solution Finder with multi-call LLM debate (Stage 1 parallel Haiku × 3 + Sonnet synthesis)
- ✅ Executive Decision Briefing (19-page structured output with McKinsey/BCG/Bain framing)
- ✅ Data product onboarding (YAML contract-driven)
- ✅ Audit trail and human-in-the-loop checkpoints
- ✅ Registry system (KPIs, principals, business processes, data products, glossary)
- ✅ Decision Studio UI (React, functional — production-quality)
- ✅ Registry Explorer UI (browse/edit all registry entities)
- ✅ Database-agnostic backend (BigQuery, Supabase/Postgres; Snowflake, Databricks, SQL Server, SAP Datasphere planned)
- ✅ Market Analysis Agent — external intelligence layer via Perplexity + Claude synthesis (competitor signals, market context, trend validation)
- ✅ Value Assurance Agent — full lifecycle: solution registration, three-trajectory tracking (inaction/expected/actual), DiD attribution, composite verdict matrix, Supabase persistence
- ✅ Opportunity Detection — positive KPI outperformance detection, benchmark segment classification, replication target identification
- ✅ Portfolio Dashboard UI — trajectory chart (inaction/expected/actual lines), measurement recording, portfolio-wide tracking
- ✅ Cost of Inaction Banner — pre-approval projection in Executive Briefing (slope-based 30d/90d forecast)
- ✅ HITL Approval Workflow — Approve & Track with VA solution registration, confirmation card, portfolio link
- 🔄 Demo video and landing page (in progress)
- 📋 Branded agent marketplace (post-first-revenue, Year 3+ roadmap)

---

## 3. Target Market & ICP

### Primary Segments (Priority Order)

#### 1. VP FP&A / Head of Financial Planning ⭐⭐⭐ *(NEW — Primary Entry Buyer)*
- **Size:** 10,000+ mid-market companies
- **ARPU:** $30K-$60K initial (entry point for CFO expansion)
- **Pain:** 30% of every month spent explaining last month; manual translation of data into three executive narratives
- **Trigger Events:** New CFO hire demanding faster insights, board demanding better reporting, FP&A team under-resourced
- **Why first:** Shorter sales cycle (4-6 weeks vs 4-6 months), clearer ROI (time saved on monthly close), budget authority for pilot pricing, creates internal CFO champion

#### 2. Mid-Market CFOs ⭐⭐⭐
- **Size:** 10,000+ companies
- **ARPU:** $60K-$120K (expanded from $80K-$100K with multi-pillar value)
- **Pain:** Reactive decision-making, consulting spend with no continuous coverage, no institutional memory
- **Trigger Events:** New CFO hire, cost reduction initiative, board demanding faster insights
- **Relationship to FP&A:** FP&A team entry → CFO becomes champion for expansion to full platform

#### 2a. Never-Engaged Mid-Market ⭐⭐⭐ *(New — Primary TAM)*
- **Size:** 50,000+ companies ($50M-$500M revenue) — larger than the consulting-displacement segment
- **ARPU:** $44K-$80K (net-new capability, not a substitute comparison)
- **Pain:** CFO + spreadsheet + gut instinct; no structured analysis; no access to MBB-quality frameworks at their scale
- **Why they buy:** Not "cheaper consulting" — *capability they've never had*. First structured multi-perspective decision support. Easier sell: no competitive displacement, no incumbent to displace.
- **Trigger Events:** Margin squeeze, rapid growth, PE acquisition, new CFO mandate
- **Sales note:** Shorter sales cycle than consulting-displacement customers. No "but we have McKinsey" objection. Pain is immediate and tangible.
- **Relationship to other segments:** Best entry point for early pilots. Reference customer proof unlocks higher-ACV CFO and PE deals.

#### 3. PE Portfolio Operations ⭐⭐⭐
- **Size:** 500 firms
- **ARPU:** $150K-$230K (platform fee + per-portfolio-company activation)
- **Pain:** Inconsistent KPI definitions across portfolio, manual value creation tracking, LP reporting overhead
- **Trigger Events:** Post-acquisition, value creation mandate, new GP joining portfolio ops team
- **Commercial structure:** Platform fee ($40K-$60K) + per-portfolio-company fee ($20K-$30K); expands automatically with new acquisitions

#### 4. Corporate Strategy Teams ⭐⭐
- **Size:** 500 F500 companies
- **ARPU:** $300K+
- **Pain:** Strategic decisions need multiple perspectives
- **Trigger Events:** Activist investor pressure, IPO prep
- **Note:** Deferred to Year 2+ — procurement complexity too high for solo founder Year 1

### Ideal Customer Profile

**Firmographics:**
- Mid-market or PE-backed company
- $500M-$5B revenue
- 500-5,000 employees

**Technographics:**
- Data platform: Snowflake, Databricks, BigQuery, SQL Server, or SAP Datasphere
- ERP system (SAP, Oracle, NetSuite) — or willing to export GL data as CSV for pilot
- BI tools (Tableau, Power BI, Looker)
- AI policy approved

**Psychographics:**
- Frustrated with consulting speed/cost
- Innovation mandate from CEO/board
- Data-driven decision culture
- Willing to try new approaches

**Budget:**
- $1M+ annual consulting spend
- $80K-$200K innovation budget

### Anti-Patterns (Avoid)

#### ❌ No Data Infrastructure
- Company lacks ERP, data warehouse, or BI tools
- Data in spreadsheets, siloed systems, or inaccessible
- **Why:** Would require months of data engineering before delivering value

#### ❌ "Innovation Theater" Culture
- Pilots get approved but never go to production
- Innovation budget exists but decisions blocked by committees
- **Why:** Waste time on pilots that never convert to revenue

#### ❌ Deep McKinsey/BCG Relationships
- Long-standing strategic relationships with Big 3 firms
- Consulting firm embedded in strategy process
- **Why:** Political blockers, competing with trusted advisors

#### ❌ No AI Policy Approved
- Company has no internal policy on AI tool usage
- Legal/compliance hasn't approved AI for sensitive data
- **Why:** Deal stuck in legal review for 6-12 months

---

## 4. Business Model

### Revenue Streams (Phased — Revised March 19, 2026)

**Year 1 — Direct Subscriptions Only**
- $18K-$40K pilot engagements (3-6 months) — includes full pipeline: SA + DA + SF + MA market intelligence + VA tracking
- Light implementation included in pilot price
- Goal: prove value via VA trajectory data, build case studies with measured ROI

**Year 2 — Subscriptions + Services**
- $75K-$140K annual contracts (post-pilot conversion — VA trajectory data from pilot carries forward as renewal evidence)
- $15K-$30K implementation/onboarding for new customers
- Usage-based pricing for high-volume debate sessions
- Expansion revenue: additional principals see trajectory chart → demand access → per-principal upsell

**Year 3+ — Platform + Partner Revenue**
- $90K-$150K annual platform subscriptions (Enterprise tier with SOC 2)
- Partner revenue share (15-30% of branded agent fees)
- Implementation and integration services
- Decision outcome corpus licensing (anonymized cross-customer pattern insights — Year 3+)

*Note: Partner/marketplace revenue is excluded from Year 1-2 projections. No consulting firm will encode IP in a pre-revenue startup platform. This becomes viable only after 10+ customers and proven ROI. Decision corpus licensing is a potential Year 3+ revenue stream once sufficient cross-customer data exists.*

### Pricing Architecture (Revised — Three-Layer Model)

The original single-tier pricing anchors Agent9 to consulting engagement analogies. The revised model reflects the operational infrastructure nature of the platform.

**Layer 1 — Platform (fixed annual, high switching cost)**
| Tier | Annual | Included |
|------|--------|----------|
| Starter | $25K-$35K | KPI registry, principal profiles, data product contracts, audit trail infrastructure |
| Professional | $40K-$55K | Above + extended KPI library, multi-domain business processes, Market Analysis intelligence |
| Enterprise | $70K-$100K | Above + SOC 2, SLA, dedicated onboarding, Portfolio Dashboard, priority support |

*Platform pricing raised $5K-$20K across tiers. Rationale: MA market intelligence, VA trajectory tracking, and Opportunity Detection are now shipped features that justify the premium — these are not roadmap items.*

**Layer 2 — Intelligence (per-principal/month, scales with adoption)**
- $750-$1,500 per principal per month (Situation Awareness, Deep Analysis, Solution Finder, Market Intelligence, Opportunity Detection)
- Value Assurance add-on: +$250/principal/month (Portfolio Dashboard, trajectory tracking, ROI attribution) — included in Professional+ tiers
- Example: 4 principals × $1,250/month × 12 = $60K/year

**Layer 3 — Onboarding (one-time Fast Start fee)**
- $10K-$15K flat for 5-day onboarding (data product contracts, KPI configuration, principal setup)
- Framed as speed and certainty, not consulting hours billed
- Pilot onboarding uses "bring your own extract" model — no source system connection required (see Pilot Data Onboarding below)
- *See Onboarding Moat document for full methodology*

**Year 1 Pilot Pricing (simplified for early customers)**
| Tier | Price | Duration | What They Get |
|------|-------|----------|---------------|
| **Fast Start Pilot** | $18K | 3 months | 5-day onboarding + 3 months monitoring + bi-weekly check-ins |
| **Full Pilot** | $30K-$40K | 6 months | Above + Deep Analysis + Solution Finder + Market Intelligence + VA tracking for 2 use cases |
| **Annual (post-pilot)** | $75K-$140K | 12 months | Full three-layer pricing; reflects operational embedding; VA trajectory data from pilot carries forward |

*Pilot pricing raised from $15K/$25K-$30K to $18K/$30K-$40K. Rationale: shipped MA + VA + Opportunity features make the pilot significantly more valuable — CFO sees market intelligence, trajectory tracking, and opportunity detection from day one, not just situation alerts. Enterprise tier ($120K+) deferred until 3+ reference customers and SOC 2 readiness.*

### Unit Economics (Revised March 19, 2026)

| Metric | Year 1 (Pilots) | Year 2 (Growth) | Change from Prior Revision |
|--------|-----------------|-----------------|----------------------|
| **CAC** | $5K-$10K | $15K-$25K | Unchanged — FP&A entry point may reduce |
| **ACV** | $18K-$40K | $75K-$140K | Raised — shipped MA/VA/Opportunity make demos more compelling; higher pilot pricing justified |
| **LTV** | $120K-$280K | $375K-$700K | Raised — VA trajectory evidence at renewal reduces churn + higher ACV base |
| **LTV:CAC** | 14-20x | 18-25x | Raised — VA evidence + operational embedding = strongest retention in category |
| **Logo Churn** | 8% | 2-4% (mature) | Lowered further — VA trajectory chart gives CFO monthly visible evidence of value; harder to cancel |
| **NRR** | 115% | 135-150% | Raised — opportunity detection creates new use cases within accounts; VA drives principal expansion |
| **Gross Margin** | 80-85% | 85-90% | Unchanged |
| **Payback Period** | 3-5 months | 3-6 months | Slightly improved — higher ACV with same CAC |

---

## 5. Go-to-Market Strategy

### Phase 0: Demo-Ready (Mar-Apr 2026) ✅ PLATFORM COMPLETE
**Goal:** Record demo video and prepare outreach materials

**Status (March 19, 2026):** Platform is demo-ready NOW. All 5 value pillars have shipped product (SA+DA+SF+MA+VA+Opportunity). Remaining work is UI polish and video recording, not feature development.

**Activities:**
- Pre-video UI polish (3 fixes: sticky footer, accordion collapse, registry editing)
- Record demo video (Situation Awareness → Deep Analysis → Market Intelligence → Solution Finder → Approve & Track → VA Portfolio)
- Build landing page
- Prepare 3-slide pitch deck for discovery calls

**Investment:** $2K-$3K (self-funded)
**Time Commitment:** 15 hours/week
**Key Deliverable:** Demo video showcasing full lifecycle including market intelligence and trajectory tracking

### Phase 1: Warm Network (May-Aug 2026)
**Goal:** 25 discovery calls, 8 demos, 2-3 pilot proposals

**Sales Motion:**
- Founder-led outreach to warm network only
- 30-minute "feedback" calls → live demos → pilot proposals
- Demo now shows: live KPI monitoring → root cause → market signals → multi-perspective debate → approve & track → trajectory chart
- Position as "AI Decision Intelligence for CFOs" (not "agentic consulting marketplace")
- $18K-$40K pilot pricing (3-6 months)

**Pilot Data Onboarding — "Bring Your Own Extract":**

Mid-market buyers are cautious about connecting AI tools to production ERP systems in week one. Agent9's pilot onboarding eliminates this objection entirely:

| Phase | Data Source | What the Customer Does | Customer Comfort Level |
|-------|-----------|----------------------|----------------------|
| **Pilot (Month 1-2)** | CSV/Excel extract → Supabase Postgres | Export GL/financial data from ERP, upload to Agent9 | High — "just export a spreadsheet" |
| **Pilot refresh** | Updated extract (monthly) | Re-export and upload during pilot period | High — same process, no new access |
| **Production (Month 3+)** | Direct BigQuery or Postgres read replica | Grant Agent9 read-only access to analytics layer | High — "read-only copy, no writes" |

**Why this works:**
- Removes the scariest pilot objection: *"You want access to our SAP/Oracle/NetSuite?"*
- First discovery call becomes: *"Send me a GL export and I'll have your first situation analysis back in 48 hours"*
- No throwaway infrastructure — extract loads into the same Supabase Postgres the customer will use in production
- Data Product Onboarding workflow handles the rest (schema inspection, contract generation, KPI mapping)
- When the customer is ready to go live, swap the extract-based connection profile for a direct database connection — same contract YAML, different data source

**Production data backends:**

| Backend | Role | Status |
|---------|------|--------|
| **Supabase/PostgreSQL** | Platform state (registries, situations, VA solutions) + pilot extract storage | ✅ Operational |
| **BigQuery** | Customer analytics data (read-only) | ✅ Operational |
| **Snowflake** | Customer analytics data (read-only) | 📋 Planned — high priority (dominant in mid-market data stacks) |
| **Databricks** | Customer analytics data (read-only, Unity Catalog / SQL warehouse) | 📋 Planned |
| **SQL Server** | Customer analytics data (read-only) — common in companies running SAP, Oracle ERP, or legacy on-prem stacks | 📋 Planned |
| **SAP Datasphere** | Customer analytics data (read-only) — direct connection for SAP-native customers; eliminates CSV extract step | 📋 Planned |
| **DuckDB** | Local development only — used for early prototyping with SAP sample CSV data; not customer-facing | ✅ Dev only |

**Connector priority** is driven by ICP overlap: Snowflake and Databricks cover the "modern data stack" segment (60%+ of target ICP). SQL Server covers legacy mid-market. SAP Datasphere covers SAP-native customers who want a direct connection rather than extracts. Each connector reuses the existing Data Product Agent architecture — schema inspection, contract generation, and KPI mapping are backend-agnostic by design.

**Investment:** $3K-$5K additional
**Time Commitment:** 15-20 hours/week
**Target:** 2-3 signed pilots by Aug 2026 (moved up from Sep — demo is stronger with MA/VA/Opportunity)
**Kill Criterion:** Zero pipeline after 30 conversations → reassess ICP

### Phase 2: First Revenue (Sep 2026-Feb 2027)
**Goal:** Deliver pilot(s) successfully, close 2-3 additional customers

**Activities:**
- Weekly check-ins with pilot customers
- VA trajectory data accumulates during pilot → concrete renewal evidence at 3-6 month mark
- Document ROI using actual VA trajectory data (not estimated — measured)
- Expand within pilot accounts (additional principals see trajectory chart → demand access)
- Begin outbound to similar profiles using case study with VA-measured outcomes

**Investment:** $5K additional
**Time Commitment:** 20 hours/week
**Target Revenue:** $30K-$100K (2-4 pilots)

### Phase 3: Prove & Decide (Mar-Dec 2027)
**Goal:** Convert pilots to annual contracts, reach 5-10 customers

**Decision Point (Month 12, ~Mar 2027):**
- ✅ If 2+ paying customers, pipeline of 3+ → Quit day job, go full-time
- ❌ If <2 customers, weak pipeline → Keep moonlighting, iterate or pivot

*Decision point moved up 1 month — earlier pilot starts = earlier data.*

**Full-Time Activities (if triggered):**
- Hire #1: Sales/Customer Success ($80K-$120K)
- Expand within existing accounts (VA trajectory + Opportunity Detection drive principal expansion)
- Outbound to similar profiles using VA-measured case studies
- Build 2-3 case studies with actual KPI recovery data (not hypothetical)
- Begin SOC 2 readiness for enterprise tier

**Target Revenue:** $150K-$500K ARR (4-10 customers at $30K-$75K ACV)

### Phase 4: Scale & Partner Exploration (2028)
**Goal:** Grow customer base, explore first partner relationships

**Partner Strategy (only if 10+ customers):**
- Target mid-tier consulting firms (FTI, A&M, Huron) — not BCG/McKinsey
- VA trajectory tracking becomes joint value prop: "our methodology + Agent9 tracking = proven ROI"
- Co-design 1 branded agent pilot with a willing partner
- Revenue share model (70-85% to partner)

**Target Revenue:** $500K-$1.5M ARR (10-20 customers)

*Note: Branded agent marketplace deferred to Year 3+. Direct customer value comes first.*

---

## 6. Competitive Landscape

### Direct Competitors (Updated February 2026)

| Player | What They Do | Gap/Weakness |
|--------|--------------|---------------|
| **McKinsey/BCG/Bain** | Human consulting (+ internal AI tools like Lilli) | Slow (12-24 weeks), expensive ($500K-$2M), single perspective. Building AI internally but not productizing for mid-market. |
| **ChatGPT/Claude/Gemini** | Generic AI + agent frameworks | No domain expertise, no audit trail, no registry-driven context. Improving rapidly. |
| **Hebbia ($130M raised)** | AI analyst for PE/finance | Strong in document analysis; lacks multi-agent debate, registry depth, and consulting methodology framing. |
| **Numeric / Runway / Mosaic** | AI-powered FP&A and financial close | Narrow scope (financial operations only); no strategic advisory or multi-perspective analysis. |
| **Palantir AIP** | Data platform + AI agents | Enterprise-grade but complex, expensive, and technical — not strategic advisory. |
| **AWS Bedrock / Azure AI Agents** | Cloud-native agent orchestration | Infrastructure layer — no domain models, no consulting methodology, no vertical application. |
| **Tableau/Power BI + Copilot** | Dashboards + AI narration | Shows data and explains trends; doesn't advise, recommend, or debate options. |

### Agent9 Unique Position

```
                HIGH DOMAIN INTELLIGENCE
                      │
     Traditional      │      Agent9
     Consulting       │      Decision Intelligence
                      │
LOW SCALE ────────────┼──────────── HIGH SCALE
                      │
     Generic AI       │      AI Finance Startups
     (ChatGPT)        │      (Hebbia, Numeric)
                      │
                LOW DOMAIN INTELLIGENCE
```

**Positioning (updated):** Agent9 is not an "agentic consulting marketplace" (Year 1). It is **AI-powered decision intelligence** that combines registry-driven domain context, multi-agent analysis, and full audit trails. The marketplace layer is a Year 3+ evolution.

*Key competitive insight: Multi-agent orchestration is becoming commodity infrastructure (AWS, Azure, open-source). The durable differentiator is the registry-driven domain model (KPIs, principals, business processes, data products, glossary) that gives agents enterprise context no generic platform provides.*

**New as of March 2026:** Agent9 now includes operational Market Analysis (real-time competitor and market intelligence via Perplexity), Value Assurance with three-trajectory tracking (inaction vs expected vs actual KPI recovery), and Opportunity Detection (positive outperformance surfaced alongside problems). No competitor in any category offers post-decision ROI attribution with visual trajectory tracking.

### Defensibility & Moat (Revised February 2026)

| Moat | Durability | How It Works |
|------|-----------|---------------|
| **Registry-Driven Domain Intelligence** | 🟢 Strong | KPI definitions, principal profiles, business process mappings, data product contracts — deep enterprise context that takes months to build per customer. Hard to replicate without similar architecture. |
| **5-Day Onboarding Template Library** | 🟢 Strong (compounds with customers) | Pre-built data product contracts and KPI templates per ERP/data stack (SAP, Oracle, NetSuite, Snowflake). First customer takes 5 days; tenth customer in same stack takes 2. Competitors starting from scratch need months. *See Onboarding Moat document.* |
| **Decision Outcome Corpus** | 🟢 Strong (grows with customers) | Every debate, analysis, and recommendation builds a proprietary dataset of decision patterns. More customers = better recommendations. |
| **Operational Embedding** | 🟢 Strong (grows over time) | Once integrated into monthly close process, board pack preparation, and KPI monitoring rhythm, switching cost grows every month. By month 6, the registry IS their source of truth. |
| **Value Assurance Feedback Loop** | 🟢 Strong (grows with decisions) | Every approved decision creates a tracked trajectory — inaction projection, expected recovery, actual outcome. Over time, this builds a proprietary decision quality corpus: which types of recommendations work for this company, at this scale, in this industry. No competitor tracks post-decision KPI attribution. |
| **Audit Trail Standard** | 🟡 Medium | First to define "explainable AI decision intelligence" with full provenance. Defensible until cloud platforms add similar features (~18-24 months). |
| **Partner Network** | 🔴 Future (Year 3+) | Not a moat until partners exist. Mid-tier consulting firms (FTI, A&M, Huron) are the first targets. Lead generation + revenue assurance framing. *See Consulting Partner Strategy document.* |

**Multi-agent orchestration is explicitly NOT listed as a moat.** It is commodity infrastructure by Q4 2027. The moat is everything listed above — the domain model, the templates, the embedded data, and the decision corpus.

---

## 7. Financial Projections (Revised March 19, 2026)

*Rebased post-Phase 7-8 completion. All five value pillars now have shipped product — MA Agent (market intelligence), VA Agent (three-trajectory ROI tracking with Portfolio Dashboard), and Opportunity Detection are operational. This changes the financial picture: demo-ready is NOW (not April), ACV justification is stronger (demonstrable features, not slides), and retention is more defensible (VA trajectory chart makes value visible to the CFO monthly).*

### 2-Year ARR Opportunity (March 2026 — March 2028)

**What changes with shipped MA + VA + Opportunity capabilities:**
- Higher ACV: demonstrable market intelligence and ROI tracking justify $10K-$15K uplift per account vs. prior projections
- Faster sales cycle: demo now shows live trajectory chart, market signals, and opportunity detection — not mockups
- Easier sales: never-engaged segment has no incumbent; net-new capability justification, not consulting displacement
- Stronger retention: Value Assurance trajectory chart shows the CFO monthly whether their decision is working — visible evidence, not a promise
- PE multiplier: one PE firm = multiple portfolio companies at $30K-$50K each; one deal can double total ARR
- Opportunity upsell: every KPI now generates two insight types (problem detection + opportunity capture) — doubles perceived value per principal

### Year 1: Moonlighting Phase (Mar 2026 - Feb 2027)

| Period | Activity | Revenue | Costs | Net |
|--------|----------|---------|-------|-----|
| Mar-Apr 2026 | UI polish, demo video, landing page *(platform already demo-ready)* | $0 | $2K | -$2K |
| May-Aug 2026 | Warm network outreach (FP&A + never-engaged CFO targets) | $0-$45K | $3K | -$3K to +$42K |
| Sep 2026-Feb 2027 | Pilot delivery, second customer, VA trajectory data accumulates | $20K-$75K | $5K | +$15K to +$70K |
| **Year 1 Total** | | **$20K-$120K** | **$10K** | **+$10K to +$110K** |

*Raised from prior $15K-$90K range. Rationale: (1) demo-ready NOW, not April — outreach starts 1 month earlier; (2) MA market intelligence + VA trajectory chart make demos significantly more compelling → higher meeting-to-pilot conversion; (3) Opportunity Detection doubles use case surface, making $25K-$30K pilot pricing easier to justify. Day job salary = no financial pressure.*

### Year 2: Growth Phase (Mar 2027 - Feb 2028)

| Scenario | Customers | Avg ACV | ARR | Costs | Net | Driver |
|----------|-----------|---------|-----|-------|-----|--------|
| **Downside** | 2-3 | $40K | $80K-$120K | $20K | +$60K-$100K | Slow sales; only never-engaged segment; no FP&A entry |
| **Base** | 5-8 | $75K-$95K | $375K-$760K | $65K | +$310K-$695K | 5-pillar value (all demonstrable) + FP&A entry + 1-2 PE portfolio wins |
| **Upside** | 10-18 | $90K-$120K | $900K-$2.16M | $140K | +$760K-$2.02M | 2 PE firms multi-portfolio + consulting-augmentation + VA-driven renewals |

**2-Year ARR Summary (end of Year 2, Feb 2028):**
| Scenario | ARR | Customers | ACV |
|----------|-----|-----------|-----|
| Downside | $80K-$120K | 2-3 | $40K (never-engaged only, but VA retention reduces churn) |
| Base | $375K-$760K | 5-8 | $75K-$95K (multi-pillar demonstrable value + VA trajectory evidence at renewal) |
| Upside | $900K-$2.16M | 10-18 | $90K-$120K (PE portfolio expansion + MA/VA differentiation closes larger deals) |

*Base ACV raised from $65K-$85K to $75K-$95K. Rationale: (1) VA trajectory chart is now a demonstrable feature — at renewal, CFO sees actual KPI recovery vs prediction, not just a promise; (2) MA market intelligence enriches every briefing with competitor signals — this is a feature no FP&A tool offers; (3) Opportunity Detection means each principal gets both problem alerts AND growth opportunity recommendations, justifying higher per-principal pricing. PE upside: 2 firms × 5 portfolio companies × $45K = $450K incremental ARR.*

### Year 3: Scale Phase (Mar 2028 - Feb 2029)

| Scenario | Customers | Avg ACV | Direct ARR | Partner Revenue | Total ARR | Team |
|----------|-----------|---------|-----------|----------------|-----------|------|
| **Downside** | 5-10 | $60K | $300K-$600K | $0 | $300K-$600K | 1-2 |
| **Base** | 12-22 | $90K | $1.08M-$1.98M | $50K-$250K | $1.13M-$2.23M | 3-5 |
| **Upside** | 22-35 | $110K | $2.42M-$3.85M | $300K-$1M | $2.72M-$4.85M | 6-8 |

*Year 3 raised across all scenarios. Drivers: (1) VA trajectory data has 12-18 months of actuals by Year 3 — renewal conversations show measured ROI, not projections; (2) Decision outcome corpus (Pillar 3 moat) starts generating cross-customer pattern insights; (3) Enterprise tier ($120K+ with SOC 2) launches H1 2028; (4) First mid-tier consulting firm partnership (FTI, A&M, or Huron) — partner sees VA tracking as joint value prop for their clients.*

### ARR Sensitivity: What Drives the Range

| Driver | Effect on ARR | Notes |
|--------|--------------|-------|
| 1 PE portfolio firm (5 companies) | +$150K-$200K in Year 2 | Single deal; single sales conversation |
| Never-engaged pilot converts to annual at $65K | +$65K ARR per customer | Year 1 pilot → Year 2 renewal |
| FP&A entry → CFO expansion | +$30K-$40K per account | 2nd budget pool; same account |
| Value Assurance creates renewal confidence | Churn reduced: 5% vs 15% | Pillar 5 creates measurable evidence |
| MA Agent enriches SF output (SHIPPED) | Live in pipeline — competitor signals, market context in every briefing | Operational feature complete |
| VA trajectory tracking proves ROI visually | +$10K-$15K ACV per renewal | Pillar 5 now has concrete UI — CFO sees recovery chart, not just a number |

---

## 8. Funding Strategy

### Bootstrap Path (Recommended)

**Phase 1: Self-Funded (Months 1-12)**
- $15K personal investment
- Moonlight while employed
- Get to first revenue

**Phase 2: Angel/Friends & Family (Month 13)**
- Raise $250K-$500K at $2M-$3M valuation
- 10-15% dilution
- Fund first hires + 12-month runway

**Phase 3: Seed Round (Month 24)**
- Raise $1M-$2M at $8M-$12M valuation
- 15-20% dilution
- Scale to $5M ARR

**Total Dilution by Year 3:** 25-35%  
**Founder Ownership:** 65-75%

### Alternative: Venture-Backed Path

**Seed Round (Month 6-12)**
- Raise $1M-$2M at $5M-$8M valuation
- 20-25% dilution
- Hire team immediately, scale faster

**Series A (Month 24)**
- Raise $5M-$10M at $20M-$40M valuation
- Additional 20-25% dilution
- Scale to $10M+ ARR

**Total Dilution by Year 3:** 40-50%  
**Founder Ownership:** 50-60%

**Trade-off:** Faster growth, higher dilution, investor pressure

---

## 9. Exit Strategy

### Potential Acquirers

#### Type 1: Data Platform Vendors (Highest Strategic Value)
**Who:** Snowflake, Databricks, Google Cloud, AWS  
**Why:** Add AI consulting layer, differentiate platform, upsell customers  
**Valuation:** 8-12x ARR  
**At $2M ARR:** $16M-$24M

#### Type 2: Consulting Firms
**Who:** Accenture, Deloitte, PwC, mid-tier firms  
**Why:** Automate delivery, scale without hiring, modernize offerings  
**Valuation:** 6-10x ARR  
**At $2M ARR:** $12M-$20M

#### Type 3: BI/Analytics Vendors
**Who:** Tableau, Power BI, Looker, Qlik  
**Why:** Move beyond dashboards, add "insights to action"  
**Valuation:** 7-10x ARR  
**At $2M ARR:** $14M-$20M

#### Type 4: AI/LLM Platforms (Highest Multiples)
**Who:** OpenAI, Anthropic, Cohere  
**Why:** Showcase enterprise use case, acquire distribution  
**Valuation:** 10-15x ARR  
**At $2M ARR:** $20M-$30M

### Exit Timing Recommendations

**Don't Sell at $500K ARR:**
- Valuation: $2M-$5M (4-10x)
- Net to founder (after tax): $1.2M-$3M
- Not life-changing after 2 years of work

**Optimal Exit at $2M-$3M ARR:**
- Valuation: $15M-$30M (10-15x)
- Net to founder (after tax): $9M-$18M
- 3-5x better outcome, worth 1-2 extra years

**Hold for $10M+ ARR if:**
- Strong competitive moat
- Path to $100M+ exit
- Enjoying the journey

---

## 10. Key Metrics & Milestones

### Product Metrics
- Demo completion rate: >80%
- Time to value: <30 days
- Platform uptime: >99%
- Bug count: <5 critical

### Sales Metrics
- Outreach → meeting: >20%
- Meeting → pilot: >30% (raised — MA/VA/Opportunity make live demo significantly more compelling)
- Pilot → annual customer: >60% (raised — VA trajectory data provides measurable renewal evidence)
- Average deal size (Year 1): $18K-$40K
- Average deal size (Year 2+): $75K-$140K

### Financial Metrics
- MRR growth: >10%/month (post first customer)
- CAC: <$10K (Year 1, founder-led); <$25K (Year 2, outbound)
- LTV: >$120K (Year 1); >$375K (Year 2+)
- LTV:CAC: >14x
- Gross margin: >80%
- Burn multiple: <2x

### Customer Success Metrics
- NPS: >50
- Logo retention: >92% (VA trajectory evidence reduces voluntary churn)
- Net revenue retention: >115% (Opportunity Detection + principal expansion drives upsell)
- Reference-ability: >80%

### Milestones (Rebased to March 2026)

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| SA→DA→SF pipeline stable (19-page Executive Briefing) | Mar 2026 | ✅ Complete |
| 5-pillar value proposition + updated strategy docs | Mar 2026 | ✅ Complete |
| Market Analysis Agent PRD complete | Mar 2026 | ✅ Complete |
| Market Analysis Agent built + wired into SF pipeline | Apr 2026 | 📋 Sprint |
| Positive KPI opportunity detection (SA) | Apr 2026 | 📋 Sprint |
| Value Assurance data model (AcceptedSolution) | Apr 2026 | 📋 Sprint |
| Demo video recorded (lubricants + bikes) | Apr 2026 | 📋 Pending |
| Landing page live | Apr 2026 | 📋 Pending |
| First 20 warm contacts identified (FP&A + never-engaged CFO) | May 2026 | 📋 Pending |
| First 10 discovery calls | Jun 2026 | 📋 Pending |
| First pilot signed | Sep 2026 | 📋 Pending |
| First case study documented | Jan 2027 | 📋 Pending |
| Second paying customer | Mar 2027 | 📋 Pending |
| Quit day job decision point | Apr 2027 | 📋 Pending |
| First hire Sales/CS (if full-time) | Jun 2027 | 📋 Pending |
| 5 customers / $250K+ ARR (base) | Dec 2027 | 📋 Pending |
| SOC 2 readiness | H1 2028 | 📋 Pending |
| First partner pilot (mid-tier consulting firm) | H2 2028 | 📋 Pending |
| 10+ customers / $800K+ ARR (base) | Jan 2029 | 📋 Pending |

**Kill Criteria:**
- Zero pipeline after 30 discovery calls (by Q3 2026) → Reassess ICP and positioning
- Zero paying customers by Q4 2026 → Major pivot or wind down
- First pilot churns / fails to renew → Stop selling, fix product

---

## 11. Risk Analysis & Mitigation

### Key Risks

**1. Commoditization Risk: Multi-agent orchestration becomes table stakes** *(NEW)*
- **Mitigation:** Shift differentiation from orchestration to registry-driven domain intelligence. The platform layer is commodity; the domain model (KPIs, principals, business processes, data products) is the moat.
- **Likelihood:** High (already happening — AWS Bedrock, Azure AI Agents, LangGraph)
- **Impact:** High

**2. Competitive Risk: Well-funded AI finance startups saturate ICP**
- **Mitigation:** Differentiate on multi-perspective analysis and audit trails vs. narrow FP&A tools. Target customers who need strategic advisory, not just financial automation.
- **Likelihood:** High (Hebbia $130M, Numeric $28M, Runway $60M+ already in market)
- **Impact:** High

**3. Sales Risk: Can't close customers as solo founder**
- **Mitigation:** Lower price point ($15K-$25K pilots) to reduce procurement friction. Founder-led warm network sales. Position as "feedback" conversations, not enterprise sales.
- **Likelihood:** Medium
- **Impact:** High

**4. Market Timing Risk: Enterprise AI budgets consolidate around platform vendors**
- **Mitigation:** Target companies <$1B revenue with shorter procurement cycles. Avoid F500 until reference customers exist. Consider embedding within existing platforms (SAP, Salesforce) rather than standalone.
- **Likelihood:** Medium-High
- **Impact:** Medium

**5. Product Risk: Platform not stable enough for enterprise**
- **Mitigation:** Over-invest in reliability. Start with forgiving early adopters. Pilot pricing sets appropriate expectations.
- **Likelihood:** Medium
- **Impact:** High

**6. Execution Risk: Burnout while moonlighting**
- **Mitigation:** Set boundaries, maintain work-life balance, quit day job only when 2+ paying customers and 6+ months runway saved.
- **Likelihood:** Medium
- **Impact:** Medium

**7. Partner Timing Risk: Marketplace vision is premature**
- **Mitigation:** Defer partner/marketplace strategy to Year 3+. Focus entirely on direct customer value for first 18 months. Do not spend time on BCG/McKinsey outreach until 10+ customers.
- **Likelihood:** High (no consulting firm will engage with pre-revenue startup)
- **Impact:** Low (if properly deferred; High if it becomes a distraction)

---

## 12. Team & Hiring Plan

*Revised March 2026 — accounts for accelerated partner timeline (Tier 0 now, Tier 1 at 5+ customers, Tier 2 at 10+). See `consulting_partner_strategy.md` for partner activation gates.*

### Current Team
- **Founder/CEO:** Solo (technical + business)

### Year 1 (Moonlighting) — No Hires

**Time allocation (15-25 hours/week):**

| Activity | Hours/Week | Notes |
|----------|-----------|-------|
| Product work (UI polish, Phase 9, bug fixes) | 6-8 | Reduces over time as platform stabilises |
| Customer outreach + demos | 4-6 | Primary revenue-generating activity |
| Tier 0 partner conversations (fractional CFOs) | 2-4 | These practitioners are also prospects — overlap is intentional |
| Content + demo video + landing page | 2-3 | Front-loaded in Apr-May 2026 |
| **Total** | **14-21** | Sustainable with day job at 15-20; stretches to 25 during sprint weeks |

**Contractor budget: $5K-$10K**
- Graphic designer: landing page, pitch deck, demo video editing ($2K-$3K)
- Legal: terms of service, privacy policy, pilot agreement template ($2K-$4K)
- Bookkeeping: monthly financials once revenue starts ($1K-$2K)

**Discipline required:** Tier 0 partner conversations must convert — either the practitioner becomes a customer or refers one within 90 days. If neither, deprioritise that relationship. Partner conversations that feel productive but generate no revenue are the highest-risk time sink during moonlighting phase.

### Year 2 (Full-Time) — 3 Hires

**Decision point (Month 12, ~Mar 2027):** Quit day job if 2+ paying customers + 6 months runway saved.

**Hire #1 (Month 13): Sales / Account Executive**
- $80K-$120K base + commission
- Owns new logo acquisition — outbound to never-engaged mid-market + FP&A entry buyers
- Founder shifts to product, partnerships, and strategic sales (PE, larger accounts)
- **Not responsible for partner management** — that stays with founder until Hire #1b

**Hire #1b (Month 15): Customer Success / Partner Operations**
- $70K-$100K
- Manages pilot customer onboarding, weekly check-ins, and renewal conversations
- Manages Tier 0 practitioners (fractional CFOs who are simultaneously customers and referral sources)
- Owns VA trajectory data review with customers — ensures measurements are recorded, trajectory charts are discussed at check-ins
- **Key insight:** Fractional CFOs are both customers and partners. The CS person managing their success IS managing the partner relationship. No separate partner team needed at this stage.

**Hire #2 (Month 18): Senior Engineer**
- $100K-$150K
- Platform stability, multi-tenant infrastructure, CI/CD pipeline
- Builds partner infrastructure: lead attribution tracking, escalation routing, diagnostic handoff export
- Frees founder from all production coding

**Hire #3 (Month 24): Product/Design**
- $90K-$130K
- UI/UX, customer feedback loop, roadmap prioritisation
- Partner portal design (basic dashboard for Tier 1 partners)
- Elevates product quality for enterprise tier readiness

**Year 2 fully-loaded team cost: $340K-$500K** (4 FTEs + founder)

### Year 3 (Growth) — Scale to 10-14 FTEs

| Function | Headcount | Roles | Cost Range |
|----------|-----------|-------|------------|
| Sales | 2-3 | 2 AEs (direct) + 1 Partner Manager (Tier 1-2 firm relationships) | $240K-$420K |
| Engineering | 3 | 1 senior (platform) + 1 mid (partner infra + integrations) + 1 mid (data/analytics) | $300K-$450K |
| Customer Success | 2 | 1 CSM (direct customers) + 1 CSM (partner-referred customers) | $140K-$200K |
| Marketing | 1-2 | 1 content/growth + 0.5 partner marketing (case studies, co-branded materials) | $90K-$180K |
| Operations | 1 | Finance/ops (SOC 2 compliance, vendor management, partner revenue share admin) | $80K-$120K |
| **Total** | **10-14** | | **$850K-$1.37M** |

**Partner Manager role (Year 3, new):**
- Owns Tier 1 boutique partner relationships (5-10 firms)
- Begins Tier 2 mid-tier firm conversations (FTI, A&M, Huron)
- Manages escalation routing: which situations go to which partner
- Tracks attribution data, prepares revenue share reports
- Works with Marketing on partner case studies using VA trajectory data
- **Hire profile:** Ex-consulting (Manager/Senior Manager level) who understands how firms buy and sell

---

## 12b. Infrastructure Roadmap

*The platform runs locally as of March 2026. Cloud deployment, multi-tenancy, authentication, and monitoring must be in place before the first pilot customer.*

### Phase 0: Pre-Outreach (April-May 2026) — $2K-$5K

| Item | Priority | Effort | Cost | Notes |
|------|----------|--------|------|-------|
| **Cloud deployment** | 🔴 Critical | 2-3 days | $50-$100/month | Railway or Render for FastAPI; Vercel for React frontend; Supabase Cloud for database |
| **Domain + SSL** | 🔴 Critical | 1 day | $50/year | agent9.ai — already planned |
| **Basic authentication** | 🔴 Critical | 2-3 days | $0-$25/month | Supabase Auth (email + password); API keys for programmatic access |
| **Error monitoring** | High | 1 day | $0/month (free tier) | Sentry for backend exceptions; captures errors before customers report them |
| **Transactional email** | Medium | 1 day | $0/month (free tier) | Resend or SendGrid — situation alerts, password reset, pilot welcome |
| **Landing page** | High | 1-2 days | $0/month | Static site on Vercel; simple: value prop, demo video embed, contact form |

**Total Phase 0 infra cost:** ~$100-$200/month recurring + $2K-$5K one-time setup effort

**Why this is the #1 blocker:** A prospect who sees a compelling demo will ask "when can we start?" The answer must be "next week" — not "let me figure out hosting." Cloud deployment must be complete before the first discovery call.

### Phase 1-2: Customer Infrastructure (May 2026-Feb 2027) — $10K-$20K

| Item | Priority | Effort | Cost | Notes |
|------|----------|--------|------|-------|
| **Multi-tenant isolation** | 🔴 Critical | 1-2 weeks | Included in Supabase | Per-customer Supabase project (simplest isolation model); separate registries, KPI sets, data products per tenant |
| **Customer provisioning script** | 🔴 Critical | 3-5 days | $0 | Automate: create Supabase project → seed registries → configure data product contracts → generate API keys → send welcome email |
| **Uptime monitoring** | High | 1 day | $0-$20/month | Better Uptime or UptimeRobot; customer-facing SLA requires monitoring |
| **Automated backups** | High | 1 day | Included in Supabase | Supabase handles Postgres backups; add nightly registry YAML export as belt-and-suspenders |
| **CI/CD pipeline** | High | 2-3 days | $0 (GitHub Actions) | On push to main: run unit tests → build → deploy to staging → manual promote to production |
| **Staging environment** | High | 1 day | $50-$100/month | Separate Railway/Render instance; test changes before they hit customer environments |
| **Log aggregation** | Medium | 1 day | $0-$50/month | Logtail or Papertrail; debug customer issues without SSH access |
| **Customer data export** | Medium | 2-3 days | $0 | Self-service data export (situations, analyses, VA trajectory data); required for enterprise procurement |

**Per-customer infrastructure cost:** ~$50-$100/month (Supabase project + proportional compute)
**At $18K-$40K pilot pricing:** Infrastructure is <1% of revenue per customer

### Phase 2-3: Partner Infrastructure (Mar 2027-Dec 2027) — $15K-$30K

| Item | Priority | Effort | Cost | Notes |
|------|----------|--------|------|-------|
| **Lead attribution tracking** | High | 2-3 weeks | $0 (built into platform) | New Supabase table: situation_id → escalation_type → partner_id → engagement_value → outcome. API endpoints for recording and querying. |
| **Escalation routing engine** | High | 1-2 weeks | $0 | Rule engine: situation type + severity + industry → partner assignment. Initially manual (founder routes); automated in Year 3. |
| **Diagnostic handoff export** | High | 1 week | $0 | PDF + structured JSON export of: situation card, DA analysis, MA market context, benchmark segments, impact estimates. Partner intake format. |
| **Partner portal (basic)** | Medium | 3-4 weeks | $0-$25/month | Dashboard: referred clients (anonymised), attributed engagements, revenue share earned, VA trajectory summaries for partner-delivered engagements. |
| **VA trajectory API (partner read-only)** | Medium | 1 week | $0 | Scoped API keys for partners to pull outcome data for their own case studies. Client consent required per situation. |
| **Revenue share tracking** | Medium | 1 week | $0 | Track: partner referral → customer subscription → revenue share owed. Manual payout initially; automate when 3+ partners active. |

### Phase 3+: Enterprise & Compliance Infrastructure (2028) — $50K-$100K

| Item | Priority | Effort | Cost | Notes |
|------|----------|--------|------|-------|
| **SOC 2 Type II** | 🔴 Required for Enterprise tier | 6-12 months | $30K-$50K | Required for $100K+ ACV deals. Start readiness assessment H1 2028. Covers: access controls, encryption, monitoring, incident response, vendor management. |
| **Data residency controls** | High | 2-4 weeks | Variable | EU customers may require EU-hosted data. Supabase supports regional projects. |
| **SSO / SAML integration** | High | 1-2 weeks | $0-$500/month | Enterprise customers require SSO (Okta, Azure AD). Supabase Auth supports SAML. |
| **Partner branding engine** | Medium | 4-6 weeks | $0 | White-label situation cards, partner logos in exports, branded email notifications. Only build when 3+ partners active. |
| **Revenue share automation** | Medium | 2-3 weeks | $500-$1K/month | Stripe Connect or similar for automated partner payouts. Only when partner volume justifies. |
| **Audit log export** | Medium | 1 week | $0 | SOC 2 requires exportable audit logs. Build on existing audit trail infrastructure. |

### Infrastructure Cost Summary

| Phase | Timeline | One-Time | Monthly Recurring | Trigger |
|-------|----------|----------|-------------------|---------|
| Phase 0 (deploy) | Apr-May 2026 | $2K-$5K | $100-$200 | Before first demo |
| Phase 1-2 (customers) | May 2026-Feb 2027 | $10K-$20K | $200-$500 + $50-$100/customer | Before first pilot |
| Phase 2-3 (partners) | Mar-Dec 2027 | $15K-$30K | $500-$1K | When 5+ customers + Tier 1 partner conversations begin |
| Phase 3+ (enterprise) | 2028 | $50K-$100K | $2K-$5K | When pursuing $100K+ ACV deals |

**Total infrastructure investment through Year 3:** $77K-$155K
**As % of Year 3 base ARR ($1.13M-$2.23M):** 3.5-14% — well within SaaS infrastructure cost norms (typically 15-25% of revenue)

---

## 13. Responsible Scaling Principles

### 1. Product-Led, Not Sales-Led
- ❌ Don't hire 10 salespeople before product is solid
- ✅ Perfect product with 5-10 customers first
- ✅ Let happy customers be best salespeople

### 2. Profitability-Focused
- ❌ Don't burn $500K/month for vanity metrics
- ✅ Target 50%+ gross margins
- ✅ CAC payback <12 months
- ✅ Path to profitability always clear

### 3. Partner-Enabled
- ❌ Don't build all integrations yourself
- ✅ Partner with consulting firms for delivery
- ✅ Partner with data platforms for distribution
- ✅ Focus on platform, let partners scale

### 4. Customer Success Before New Logos
- ❌ Don't chase 100 customers if 10 are churning
- ✅ 90%+ retention before scaling sales
- ✅ Net revenue retention >100%
- ✅ Reference customers in every segment

---

## 14. Moonlighting Execution Plan

### Time Management

**Weekly Rhythm:**
- **Monday-Thursday evenings (2 hours/night):** Product work, async customer support
- **Friday evening (3 hours):** Prep for customer check-ins
- **Saturday morning (4 hours):** Customer check-ins, demos for prospects
- **Sunday (4 hours):** Product refinement, content creation

**Total: 15-20 hours/week** (sustainable with day job)

### Boundaries to Set

**1. Time Boundaries**
- No Agent9 work during day job hours (except lunch)
- No customer calls during work hours
- Saturday mornings = customer time (block calendar)

**2. Energy Management**
- Sleep 7-8 hours (non-negotiable)
- Exercise 3x/week (maintain health)
- One full day off/week (Sunday afternoon = family time)

**3. Expectation Setting**
- Tell customers you're moonlighting (builds trust)
- Set response time expectations (24-48 hours)
- Schedule calls in advance (no ad-hoc)

### Red Flags to Quit Day Job

✅ **Safe to quit when:**
- 2+ paying customers ($50K+ ARR)
- 6+ months runway saved
- Customers happy and renewing
- Clear path to customer #3-5

❌ **Don't quit if:**
- Only 1 customer (too risky)
- Customers struggling to get value
- No pipeline for next customers
- Less than 6 months expenses saved

---

## 15. Next Steps (30/60/90 Days from March 2026)

### Next 30 Days (Mar-Apr 2026) — Development Sprint
*Full 7-day sprint plan: `docs/strategy/sprint_plan_march_2026.md`*
- [ ] Build Market Analysis Agent (Pydantic models, Perplexity service, Sonnet synthesis)
- [ ] Wire MA into SF pipeline → Market Intelligence badge in Executive Briefing
- [ ] Add positive KPI opportunity detection in SA → green opportunity card in Decision Studio
- [ ] Build Value Assurance data model (AcceptedSolution + Supabase persistence)
- [ ] End-to-end lubricants run with all changes; record 5-minute demo video
- [ ] Draft 2-slide pitch deck: FP&A entry pitch + CFO expansion pitch

### Next 60 Days (May-Jun 2026) — Outreach Begins
- [ ] Launch landing page (agent9.ai)
- [ ] Begin warm network outreach — 20 contacts prioritising never-engaged mid-market CFOs and VP FP&A
- [ ] Schedule first 10 discovery calls (position as "AI Decision Intelligence", not "consulting marketplace")
- [ ] First discovery insight: are prospects more receptive as never-engaged (net-new) or consulting-augmentation buyers?

### Next 90 Days (Jul-Sep 2026) — First Pilot
- [ ] Identify 3-5 serious prospects; create tailored demos
- [ ] Send first pilot proposals at $15K-$25K (Fast Start Pilot tier)
- [ ] Close first pilot customer (target: Sep 2026)
- [ ] Begin delivery — weekly check-ins, Value Assurance baseline capture
- [ ] Assess: Is ICP right? Is pricing right? Never-engaged vs FP&A vs PE — which converts fastest?

---

## Appendix A: Alternative Market - SMB/Restaurant Pivot

### Market Analysis
- **TAM:** 30M+ small businesses, 1M+ restaurants
- **ACV:** $50-$100/month (vs $100K+ for enterprise)
- **Sales Motion:** Self-serve, PLG (vs direct sales)
- **Customers Needed:** 1,000+ for $500K ARR (vs 5-10)

### Pros of SMB Pivot
- ✅ Faster to first revenue (self-serve)
- ✅ Simpler product (pre-built insights)
- ✅ Huge TAM (millions of businesses)
- ✅ Product-led growth potential

### Cons of SMB Pivot
- ❌ Lower ACV ($50 vs $100K)
- ❌ Higher churn (5%/month vs 1%/year)
- ❌ Need massive scale (1000s vs 10s)
- ❌ Competitive market (many "AI CFO" startups)
- ❌ Not feasible while moonlighting (need 40+ hours/week)

### Recommendation
**Stick with Enterprise CaaS for moonlighting phase**
- Better fit for limited time (1-2 customers manageable)
- Higher revenue per customer
- Warm network likely has enterprise contacts
- Can pivot to SMB later if desired (Year 2-3)

---

## Appendix B: Valuation Scenarios

### At $500K ARR

| Buyer Type | Multiple | Valuation | Notes |
|------------|----------|-----------|-------|
| Financial (PE) | 4-6x | $2M-$3M | No strategic premium |
| Strategic (Data Platform) | 8-10x | $4M-$5M | Moderate strategic value |
| Strategic (AI Platform) | 10-15x | $5M-$7.5M | High strategic value |

### At $2M ARR

| Buyer Type | Multiple | Valuation | Notes |
|------------|----------|-----------|-------|
| Financial (PE) | 6-8x | $12M-$16M | Standard SaaS metrics |
| Strategic (Data Platform) | 10-12x | $20M-$24M | Strong strategic fit |
| Strategic (AI Platform) | 12-15x | $24M-$30M | Competitive bidding |

### At $5M ARR

| Buyer Type | Multiple | Valuation | Notes |
|------------|----------|-----------|-------|
| Financial (PE) | 8-10x | $40M-$50M | Growth-stage SaaS |
| Strategic (Data Platform) | 12-15x | $60M-$75M | Category leader |
| Strategic (AI Platform) | 15-20x | $75M-$100M | Must-have acquisition |

### Factors That Increase Multiples

| Factor | Impact | Example |
|--------|--------|---------|
| **Growth Rate >100% YoY** | +2-4x | $500K → 8x = $4M |
| **Net Revenue Retention >120%** | +1-2x | $500K → 7x = $3.5M |
| **Profitability** | +1-2x | $500K → 7x = $3.5M |
| **Strategic Value** | +2-5x | Fills gap in acquirer portfolio |
| **Category Leader** | +1-3x | Clear market differentiation |

---

**Document Control:**
- **Version:** 1.5
- **Last Updated:** March 2026
- **Next Review:** After first pilot signed (Sep 2026)
- **Owner:** Founder/CEO
