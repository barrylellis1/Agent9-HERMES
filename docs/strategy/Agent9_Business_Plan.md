# Agent9 Business Plan
**Last Updated:** February 12, 2026

---

## Executive Summary

**Agent9** is an AI-powered decision intelligence platform that delivers continuous financial monitoring, multi-perspective analysis, and structured decision support for mid-market CFOs and PE portfolio operations teams. The platform combines registry-driven domain context with multi-agent analysis to surface the right insight for the right executive — automatically, continuously, and with a complete audit trail.

Agent9 addresses three distinct value propositions, each independent of the others:
1. **Always-on monitoring** — proactive situation detection across KPIs before problems become crises
2. **Consulting-quality insight on demand** — structured root cause analysis, multi-perspective options debate, and board-ready narrative in hours not weeks
3. **Institutional memory and decision audit trail** — KPI definitions, decision rationale, and outcome tracking that survives executive turnover and satisfies compliance requirements

**Current Stage:** Pre-revenue, platform built (~100K LOC), moonlighting development
**Go-to-Market Launch:** Q2 2026 (demo-ready, warm network outreach)
**Primary Entry Buyer:** VP FP&A / Head of Financial Planning (faster cycle) → CFO champion for expansion
**Target:** $100K-$250K ARR within 18 months of first customer
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

### Three Value Pillars (Independent, Compounding)

**Pillar 1 — Always-On Monitoring (replaces absence of something)**
- 24/7 KPI surveillance across Finance and Sales domains with multi-timeframe thresholds
- Proactive anomaly detection before the CFO asks the question
- Situation lifecycle management (Open → Acknowledged → Assigned → Resolved)
- *Replaces:* Manual weekly dashboard reviews, reactive fire-fighting

**Pillar 2 — Consulting-Quality Insight on Demand (replaces expensive substitute)**
- Structured SCQA root cause analysis (Situation, Complication, Question, Answer)
- Multi-perspective solution debate with trade-off matrix (Financial, Operational, Strategic, Risk lenses)
- Role-personalised output: same KPI, different framing for CFO (analytical), COO (pragmatic), CEO (visionary)
- *Replaces:* $500K-$2M consulting engagements; delivers in hours not weeks

**Pillar 3 — Institutional Memory and Decision Audit Trail (fills gap nothing else addresses)**
- KPI definitions encoded with exact SQL logic, data lineage, and GL account mappings
- Decision provenance: every option considered, trade-off evaluated, outcome tracked
- Survives executive turnover — the definition of "Gross Margin" never walks out the door again
- *Replaces:* Nothing currently — this capability does not exist in any comparable tool

### Key Differentiators
1. **Registry-driven domain intelligence** — KPIs, principals, business processes, data products encoded per customer; deep context no generic AI provides
2. **Always-on monitoring** — proactive, not reactive; runs 24/7 between consulting engagements
3. **Role-personalised framing** — same data, right narrative for each executive
4. **Decision audit trail** — complete provenance for compliance, board reporting, and investor scrutiny
5. **5-day onboarding** — first situation card in one week, not 8-12 weeks (see Onboarding Moat doc)
6. **Branded expertise** — partner consulting methodology encoded as agents (Year 3+)

### Platform Capabilities (As of February 2026)
- ✅ Multi-agent orchestration framework (A2A protocol-compliant)
- ✅ Situation Awareness workflow
- ✅ Deep Analysis workflow
- ✅ Solution Finder with LLM debate
- ✅ Data product onboarding (YAML contract-driven)
- ✅ Audit trail and human-in-the-loop checkpoints
- ✅ Registry system (KPIs, principals, business processes, data products, glossary)
- ✅ Decision Studio UI (React, functional — final polish phase)
- ✅ Registry Explorer UI (browse/edit all registry entities)
- ✅ Database-agnostic backend (DuckDB, Supabase/Postgres, BigQuery)
- 🔄 Demo video and landing page (in progress)
- 📋 Branded agent marketplace (post-first-revenue roadmap)

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
- Modern data stack (Snowflake, Databricks, BigQuery)
- ERP system (SAP, Oracle, NetSuite)
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

### Revenue Streams (Phased)

**Year 1 — Direct Subscriptions Only**
- $15K-$30K pilot engagements (3-6 months)
- Light implementation included in pilot price
- Goal: prove value, build case studies

**Year 2 — Subscriptions + Services**
- $40K-$80K annual contracts (post-pilot conversion)
- $15K-$30K implementation/onboarding for new customers
- Usage-based pricing for high-volume debate sessions

**Year 3+ — Platform + Partner Revenue**
- $60K-$120K annual platform subscriptions
- Partner revenue share (15-30% of branded agent fees)
- Implementation and integration services

*Note: Partner/marketplace revenue is excluded from Year 1-2 projections. No consulting firm will encode IP in a pre-revenue startup platform. This becomes viable only after 10+ customers and proven ROI.*

### Pricing Architecture (Revised — Three-Layer Model)

The original single-tier pricing anchors Agent9 to consulting engagement analogies. The revised model reflects the operational infrastructure nature of the platform.

**Layer 1 — Platform (fixed annual, high switching cost)**
| Tier | Annual | Included |
|------|--------|----------|
| Starter | $20K-$30K | KPI registry, principal profiles, data product contracts, audit trail infrastructure |
| Professional | $35K-$50K | Above + extended KPI library, multi-domain business processes |
| Enterprise | $60K-$80K | Above + SOC 2, SLA, dedicated onboarding |

**Layer 2 — Intelligence (per-principal/month, scales with adoption)**
- $500-$1,500 per principal per month (Situation Awareness, Deep Analysis, Solution Finder access)
- Example: 4 principals × $1,000/month × 12 = $48K/year

**Layer 3 — Onboarding (one-time Fast Start fee)**
- $10K-$15K flat for 5-day onboarding (data product contracts, KPI configuration, principal setup)
- Framed as speed and certainty, not consulting hours billed
- *See Onboarding Moat document for full methodology*

**Year 1 Pilot Pricing (simplified for early customers)**
| Tier | Price | Duration | What They Get |
|------|-------|----------|---------------|
| **Fast Start Pilot** | $15K | 3 months | 5-day onboarding + 3 months monitoring + bi-weekly check-ins |
| **Full Pilot** | $25K-$30K | 6 months | Above + Deep Analysis + Solution Finder for 2 use cases |
| **Annual (post-pilot)** | $60K-$120K | 12 months | Full three-layer pricing; reflects operational embedding |

*Enterprise tier ($100K+) deferred until 3+ reference customers and SOC 2 readiness.*

### Unit Economics (Revised)

| Metric | Year 1 (Pilots) | Year 2 (Growth) | Change from Prior Plan |
|--------|-----------------|-----------------|----------------------|
| **CAC** | $5K-$10K | $15K-$25K | Unchanged — FP&A entry point may reduce |
| **ACV** | $15K-$30K | $60K-$120K | Raised — multi-budget expansion + PE structure |
| **LTV** | $90K-$180K | $240K-$480K | Raised — lower churn + higher NRR |
| **LTV:CAC** | 12-18x | 15-20x | Raised — operational embedding reduces churn |
| **Logo Churn** | 10% | 3-5% (mature) | Lowered — workflow embedding creates switching cost |
| **NRR** | 110% | 130-140% | Raised — multi-budget expansion + PE portfolio adds |
| **Gross Margin** | 80-85% | 85-90% | Raised — partner revenue (future) is near 100% margin |
| **Payback Period** | 3-6 months | 4-8 months | Unchanged |

---

## 5. Go-to-Market Strategy

### Phase 0: Demo-Ready (Feb-Apr 2026)
**Goal:** Ship a compelling 5-minute demo and begin outreach

**Activities:**
- Final Decision Studio UI polish
- Record demo video (Situation Awareness → Deep Analysis → Solution Finder → Audit Trail)
- Build landing page
- Prepare 3-slide pitch deck for discovery calls

**Investment:** $2K-$5K (self-funded)  
**Time Commitment:** 15 hours/week  
**Key Deliverable:** Demo video that sells the product without a live call

### Phase 1: Warm Network (May-Sep 2026)
**Goal:** 20 discovery calls, 5 demos, 1-2 pilot proposals

**Sales Motion:**
- Founder-led outreach to warm network only
- 30-minute "feedback" calls → live demos → pilot proposals
- Position as "AI Decision Intelligence for CFOs" (not "agentic consulting marketplace")
- $15K-$25K pilot pricing (3-6 months)

**Investment:** $3K-$5K additional  
**Time Commitment:** 15-20 hours/week  
**Target:** 1-2 signed pilots by Sep 2026  
**Kill Criterion:** Zero pipeline after 30 conversations → reassess ICP

### Phase 2: First Revenue (Oct 2026-Mar 2027)
**Goal:** Deliver pilot(s) successfully, close 1-2 additional customers

**Activities:**
- Weekly check-ins with pilot customers
- Document ROI and build first case study
- Expand within pilot accounts (additional use cases, users)
- Begin outbound to similar profiles using case study

**Investment:** $5K additional  
**Time Commitment:** 20 hours/week  
**Target Revenue:** $20K-$75K (1-3 pilots)

### Phase 3: Prove & Decide (Apr-Dec 2027)
**Goal:** Convert pilots to annual contracts, reach 5-8 customers

**Decision Point (Month 14, ~Apr 2027):**
- ✅ If 2+ paying customers, pipeline of 3+ → Quit day job, go full-time
- ❌ If <2 customers, weak pipeline → Keep moonlighting, iterate or pivot

**Full-Time Activities (if triggered):**
- Hire #1: Sales/Customer Success ($80K-$120K)
- Expand within existing accounts
- Outbound to similar profiles
- Build 2-3 case studies and references
- Begin SOC 2 readiness for enterprise tier

**Target Revenue:** $100K-$320K ARR (3-8 customers at $25K-$60K ACV)

### Phase 4: Scale & Partner Exploration (2028)
**Goal:** Grow customer base, explore first partner relationships

**Partner Strategy (only if 10+ customers):**
- Target mid-tier consulting firms (FTI, A&M, Huron) — not BCG/McKinsey
- Co-design 1 branded agent pilot with a willing partner
- Revenue share model (70-85% to partner)

**Target Revenue:** $300K-$900K ARR (8-15 customers)

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

### Defensibility & Moat (Revised February 2026)

| Moat | Durability | How It Works |
|------|-----------|---------------|
| **Registry-Driven Domain Intelligence** | 🟢 Strong | KPI definitions, principal profiles, business process mappings, data product contracts — deep enterprise context that takes months to build per customer. Hard to replicate without similar architecture. |
| **5-Day Onboarding Template Library** | 🟢 Strong (compounds with customers) | Pre-built data product contracts and KPI templates per ERP/data stack (SAP, Oracle, NetSuite, Snowflake). First customer takes 5 days; tenth customer in same stack takes 2. Competitors starting from scratch need months. *See Onboarding Moat document.* |
| **Decision Outcome Corpus** | 🟢 Strong (grows with customers) | Every debate, analysis, and recommendation builds a proprietary dataset of decision patterns. More customers = better recommendations. |
| **Operational Embedding** | 🟢 Strong (grows over time) | Once integrated into monthly close process, board pack preparation, and KPI monitoring rhythm, switching cost grows every month. By month 6, the registry IS their source of truth. |
| **Audit Trail Standard** | 🟡 Medium | First to define "explainable AI decision intelligence" with full provenance. Defensible until cloud platforms add similar features (~18-24 months). |
| **Partner Network** | 🔴 Future (Year 3+) | Not a moat until partners exist. Mid-tier consulting firms (FTI, A&M, Huron) are the first targets. Lead generation + revenue assurance framing. *See Consulting Partner Strategy document.* |

**Multi-agent orchestration is explicitly NOT listed as a moat.** It is commodity infrastructure by Q4 2027. The moat is everything listed above — the domain model, the templates, the embedded data, and the decision corpus.

---

## 7. Financial Projections (Stress-Tested February 2026)

*All projections rebased to Feb 2026 GTM launch. Three scenarios provided to bracket uncertainty.*

### Year 1: Moonlighting Phase (Feb 2026 - Jan 2027)

| Period | Activity | Revenue | Costs | Net |
|--------|----------|---------|-------|-----|
| Feb-Apr 2026 | Demo-ready, landing page | $0 | $5K | -$5K |
| May-Sep 2026 | Warm network outreach, first pilots | $0-$25K | $5K | -$5K to +$20K |
| Oct 2026-Jan 2027 | Pilot delivery, second customer | $15K-$50K | $5K | +$10K to +$45K |
| **Year 1 Total** | | **$15K-$75K** | **$15K** | **$0 to +$60K** |

*Plus day job salary = No financial stress. Year 1 goal is learning and validation, not revenue maximization.*

### Year 2: Growth Phase (Feb 2027 - Jan 2028)

| Scenario | Customers | Avg ACV | ARR | Costs | Net | Driver |
|----------|-----------|---------|-----|-------|-----|--------|
| **Downside** | 2-3 | $30K | $60K-$90K | $20K | +$40K-$70K | Slow sales cycle, no FP&A entry |
| **Base** | 5-8 | $60K-$80K | $300K-$480K | $60K | +$240K-$420K | Multi-pillar value + FP&A entry point |
| **Upside** | 10-15 | $80K-$100K | $800K-$1.2M | $120K | +$680K-$1.1M | One PE firm portfolio adoption |

*Base ACV raised from $40K to $60K-$80K reflecting multi-budget expansion (FP&A + CFO + compliance). Upside assumes one PE firm deploys across 3-5 portfolio companies at $150K-$200K total.*

### Year 3: Scale Phase (Feb 2028 - Jan 2029)

| Scenario | Customers | Avg ACV | Direct ARR | Partner Revenue | Total ARR | Team |
|----------|-----------|---------|-----------|----------------|-----------|------|
| **Downside** | 5-8 | $50K | $250K-$400K | $0 | $250K-$400K | 1-2 |
| **Base** | 10-20 | $80K | $800K-$1.6M | $50K-$200K | $850K-$1.8M | 3-5 |
| **Upside** | 20-30 | $100K | $2M-$3M | $300K-$800K | $2.3M-$3.8M | 6-8 |

*Year 3 partner revenue reflects first mid-tier consulting firm partnership (FTI, A&M, or Huron) generating lead referral fees and branded agent usage. Enterprise tier ($100K+ with SOC 2) launches H1 2028.*

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
- Meeting → pilot: >25%
- Pilot → annual customer: >50%
- Average deal size (Year 1): $15K-$30K
- Average deal size (Year 2+): $40K-$80K

### Financial Metrics
- MRR growth: >10%/month (post first customer)
- CAC: <$10K (Year 1, founder-led); <$25K (Year 2, outbound)
- LTV: >$60K (Year 1); >$120K (Year 2+)
- LTV:CAC: >6x
- Gross margin: >75%
- Burn multiple: <2x

### Customer Success Metrics
- NPS: >50
- Logo retention: >90%
- Net revenue retention: >110%
- Reference-ability: >80%

### Milestones (Rebased to February 2026)

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Demo video recorded | Apr 2026 | 🔄 In progress |
| Landing page live | Apr 2026 | 📋 Pending |
| First 10 discovery calls | Jun 2026 | 📋 Pending |
| First pilot signed | Sep 2026 | 📋 Pending |
| First case study documented | Jan 2027 | 📋 Pending |
| Second paying customer | Mar 2027 | 📋 Pending |
| Quit day job decision point | Apr 2027 | 📋 Pending |
| First hire (if full-time) | Jun 2027 | 📋 Pending |
| 5 customers / $200K ARR (base) | Dec 2027 | 📋 Pending |
| SOC 2 readiness | H1 2028 | 📋 Pending |
| First partner pilot (mid-tier firm) | H2 2028 | 📋 Pending |
| 10+ customers / $600K+ ARR (base) | Jan 2029 | 📋 Pending |

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

### Current Team
- **Founder/CEO:** Solo (technical + business)

### Year 1 (Moonlighting)
- No hires
- Leverage contractors for specific needs (design, legal)

### Year 2 (Full-Time)

**Hire #1 (Month 13): Sales/Customer Success**
- $80K-$120K base + commission
- Owns customer acquisition and retention
- Frees founder for product + partnerships

**Hire #2 (Month 18): Senior Engineer**
- $100K-$150K
- Platform stability, integrations, scalability
- Frees founder from all coding

**Hire #3 (Month 24): Product/Design**
- $90K-$130K
- UI/UX, customer feedback, roadmap
- Elevates product quality

### Year 3 (Growth)
- Sales team: 2-3 AEs
- Engineering: 2-3 engineers
- Customer Success: 1-2 CSMs
- Marketing: 1 content/growth marketer
- **Total: 8-12 FTEs**

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

## 15. Next Steps (30/60/90 Days from February 2026)

### Next 30 Days (Feb-Mar 2026)
- [ ] Final Decision Studio UI polish (demo-critical flows only)
- [ ] Record 5-minute demo video (Situation Awareness → Deep Analysis → Solution Finder → Audit Trail)
- [ ] Build simple landing page
- [ ] List 20 warm contacts (potential customers or referrers)
- [ ] Draft 3-slide pitch deck for discovery calls

### Next 60 Days (Apr-May 2026)
- [ ] Schedule and complete first 10 discovery calls
- [ ] Refine pitch and positioning based on feedback ("AI Decision Intelligence for CFOs" vs. "Agentic Consulting Marketplace")
- [ ] Identify 3-5 serious prospects from discovery calls
- [ ] Create tailored demos for top prospects

### Next 90 Days (Jun-Jul 2026)
- [ ] Send first pilot proposal(s) at $15K-$25K
- [ ] Close first pilot customer
- [ ] Begin pilot delivery (weekly check-ins)
- [ ] Start documenting learnings for case study
- [ ] Assess: Is the ICP right? Is the pricing right? Adjust if needed.

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
- **Version:** 1.0
- **Last Updated:** January 26, 2026
- **Next Review:** Monthly
- **Owner:** Founder/CEO
