# Agent9 Business Plan
**Last Updated:** May 2026
**Version:** 1.6 — Phase 10A–10D shipped (Swiss Style UI, PIB email delivery, multi-warehouse direct SDK connectors, SF performance tuning, VA 5-phase lifecycle, white-paper report); production deployment live on Railway + Cloudflare Pages + Supabase Cloud; strategic moat refresh — the SA→DA→SF→VA pipeline + Registry + VA outcome corpus is the moat; data connectivity is commodity

---

## Executive Summary

**Decision Studio** is an AI-powered decision intelligence platform that delivers continuous KPI monitoring, multi-perspective analysis, structured decision support, and post-implementation ROI validation for mid-market executives across any operational domain — finance, operations, sales, supply chain, and beyond. The platform combines registry-driven domain context, continuous monitoring, and external market intelligence to surface the right insight for the right executive — automatically, continuously, and with a complete audit trail.

Agent9 addresses five independent value propositions — each justifiable on its own, compounding together:
1. **Always-on monitoring** — proactive situation detection across KPIs before problems become crises
2. **Consulting-quality insight on demand** — structured root cause analysis, multi-perspective options debate, and board-ready narrative in hours not weeks
3. **Institutional memory and decision audit trail** — KPI definitions, decision rationale, and outcome tracking that survives executive turnover and satisfies compliance requirements
4. **Opportunity detection** — positive KPI outperformance detected, market context surfaced, capture options generated (not just problem response)
5. **Initiative tracking and proven ROI** — accepted solutions tracked post-implementation; actual KPI recovery attributed to the intervention vs. market tailwinds

**The primary market is not consulting displacement.** The largest addressable segment is the mid-market ($50M–$500M revenue) that never engaged MBB consulting because of cost. Agent9 is net-new capability for these companies — not a cheaper substitute.

**Current Stage:** Pre-revenue, platform built (~100K LOC), production deployment live (Railway + Cloudflare Pages + Supabase Cloud since Apr 2026), moonlighting development
**Go-to-Market Launch:** Q2–Q3 2026 (demo-ready, warm network outreach beginning May 2026)
**Primary Entry Buyer:** VP-level functional leaders (FP&A, Operations, Revenue) → C-suite champion for platform expansion
**Target:** $200K-$500K ARR within 18 months of first customer (raised from $150K-$350K — shipped MA/VA/Opportunity enable higher ACV and stronger renewal rates)
**Exit Strategy:** Strategic acquisition at $2M-$3M ARR for $15M-$30M (infrastructure/data platform framing)

---

## 1. Market Opportunity

### Market Size
- **Total Addressable Market (TAM):** $800B global consulting market
- **Serviceable Addressable Market (SAM):** $50B (mid-market + PE portfolio operations)
- **Serviceable Obtainable Market (SOM):** $5M-$10M (Year 3 target — 50-100 customers at $50K-$100K ACV)

*Note: SOM is deliberately conservative. As a bootstrapped solo founder, capturing even $5M of a $50B SAM represents meaningful traction and positions for acquisition or Series A.*

### Market Trends (Three Converging Forces)
1. **Consulting-quality analysis is now possible in hours, not weeks** — LLM-driven structured analysis (SCQA, multi-perspective debate, trade-off matrices) makes MBB-grade decision support accessible to mid-market companies that were previously priced out
2. **AI adoption is accelerating market change** — companies adopting AI are making decisions faster across pricing, product, and operations; the quarterly review cadence is already obsolete for companies competing against AI-enabled rivals
3. **"Data-driven" is unproven** — every company claims to be data-driven but no tool closes the loop between "we decided" and "it worked"; Decision Studio's trajectory tracking + DiD attribution is the first system that proves decision impact
4. Regulatory push for AI explainability and audit trails — Decision Studio's architecture *is* the audit trail

---

## 2. Product Vision

### Core Value Proposition
"AI-powered decision intelligence for mid-market executives — continuous monitoring, structured analysis, and actionable recommendations with a complete audit trail. Any domain where KPIs are measured."

### Five Value Pillars (Independent, Compounding)

**Pillar 1 — Always-On Monitoring (replaces absence of something)**
- 24/7 KPI surveillance across any operational domain (finance, operations, sales, supply chain) with multi-timeframe thresholds
- Proactive anomaly detection before any executive asks the question
- Situation lifecycle management (Open → Acknowledged → Assigned → Resolved)
- *Replaces:* Manual weekly dashboard reviews, reactive fire-fighting

**Pillar 2 — Consulting-Quality Insight on Demand (replaces expensive substitute OR net-new for never-engaged market)**
- Market Analysis Agent provides context and problem framing between DA and SF (Perplexity + Claude synthesis)
- Structured SCQA root cause analysis (Situation, Complication, Question, Answer)
- Multi-perspective solution debate with trade-off matrix (Financial, Operational, Strategic, Risk lenses)
- Role-personalised output: same KPI, different framing for CFO (analytical), COO (pragmatic), CEO (visionary)
- Market intelligence enriches Solution Finder with competitive signals and alignment validation
- *For consulting users:* replaces $500K-$2M engagements; delivers in hours not weeks
- *For never-engaged mid-market:* net-new structured analysis capability at a fraction of the cost ($44K-$100K ACV)

**Pillar 3 — Institutional Memory and Decision Audit Trail (fills gap nothing else addresses)**
- KPI definitions encoded with exact SQL logic, data lineage, and domain-specific mappings
- Decision provenance: every option considered, trade-off evaluated, outcome tracked
- Survives executive turnover — the definition of "Gross Margin" or "Cycle Time" or "Win Rate" never walks out the door again
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

### Platform Capabilities (As of May 2026)
- ✅ Multi-agent orchestration framework (A2A protocol-compliant) — 14 agents operational
- ✅ Market Analysis workflow (market context + problem framing before SA scan via Perplexity + Claude synthesis)
- ✅ Situation Awareness workflow (problem detection + positive KPI opportunity detection, context-aware, MA-informed, client-scoped enterprise assessment)
- ✅ Deep Analysis workflow (SCQA, Is/Is Not, change-point detection, benchmark segments, BigQuery routing)
- ✅ Solution Finder with multi-call LLM debate (Stage 1 parallel Haiku × 3 + Sonnet synthesis, MA enrichment); fast/full debate modes (~3 min dev, 4 calls production)
- ✅ Executive Decision Briefing (19-page structured output with McKinsey/BCG/Bain framing)
- ✅ Data product onboarding (8-step orchestrated workflow, YAML contract-driven)
- ✅ Audit trail and human-in-the-loop checkpoints
- ✅ Registry system (KPIs, principals, business processes, data products, glossary) — Supabase-backed, multi-tenant `client_id` isolation
- ✅ Decision Studio UI (React/Vite/Tailwind, Swiss Style brand identity, production-quality)
- ✅ Registry Explorer UI (browse/edit all registry entities)
- ✅ **Multi-warehouse direct SDK connectors (Phase 10C)** — DuckDB (local), BigQuery (operational), Snowflake (operational), SQL Server (operational in dev; production blocked on ODBC driver in Dockerfile); SAP Datasphere planned
- ✅ Market Analysis Agent — external intelligence layer via Perplexity + Claude synthesis (competitor signals, market context, trend validation)
- ✅ Value Assurance Agent — full 5-phase lifecycle (Approved → Implementing → Live → Measuring → Complete), three-trajectory tracking (inaction/expected/actual), DiD attribution, composite verdict matrix, Supabase persistence, phase-aware TrajectoryChart, KPI-aware Portfolio formatting
- ✅ Opportunity Detection — positive KPI outperformance detection, benchmark segment classification, replication target identification
- ✅ Portfolio Dashboard UI — trajectory chart, phase transition buttons (Mark Implementing, Go Live), measurement recording, portfolio-wide tracking
- ✅ Cost of Inaction Banner — pre-approval projection in Executive Briefing (slope-based 30d/90d forecast)
- ✅ HITL Approval Workflow — Approve & Track with VA solution registration, confirmation card, portfolio link
- ✅ **PIB email delivery (Phase 10B)** — Jinja2 templates, SMTP via Gmail App Password, Swiss Style monochrome design, single-use briefing tokens, delegation flow with audit trail
- ✅ **White-paper report (Apr 2026)** — standalone Gartner-style document at `/report/:situationId`, print + PDF support, Draft/Approved badges
- ✅ **Production deployment (Apr 2026)** — Railway backend (Docker/FastAPI), Cloudflare Pages frontend (replaced Vercel), Supabase Cloud database, GCP credentials for BigQuery materialized at startup
- 🔄 Demo video and landing page (in progress)
- 📋 Branded agent marketplace (post-first-revenue, Year 3+ roadmap)

---

## 3. Target Market & ICP

### Primary Segments (Priority Order)

#### Entry Buyer Pattern
VP-level functional leaders are the primary entry point across all domains — shorter sales cycles (4-6 weeks), budget authority for pilot pricing, and they create C-suite champions for platform expansion.

#### 1. Finance — VP FP&A / CFO ⭐⭐⭐ *(Launch Domain — Demo Ready)*
- **Size:** 10,000+ mid-market companies
- **ARPU:** $30K-$60K (VP entry), $60K-$120K (CFO expansion)
- **Pain:** 30% of every month spent explaining last month; reactive decision-making; no institutional memory for KPI definitions or decision rationale
- **Trigger Events:** New CFO hire demanding faster insights, board demanding better reporting, FP&A team under-resourced, cost reduction initiative
- **Why first:** Demo data ready (FI star schema), financial KPIs have clear thresholds, ROI is directly measurable (time saved on monthly close, faster anomaly detection)

#### 2. Operations — VP Operations / COO ⭐⭐⭐
- **Size:** 15,000+ mid-market manufacturing, logistics, and services companies
- **ARPU:** $40K-$80K (VP entry), $80K-$140K (COO expansion)
- **Pain:** Operational KPIs (cycle time, yield, fulfillment rate, capacity utilization) monitored in dashboards but not analyzed structurally; root cause investigation is manual and slow; decisions made without multi-perspective trade-off analysis
- **Trigger Events:** Supply chain disruption, quality incident, capacity expansion decision, new COO mandate, lean/continuous improvement initiative
- **Why strong fit:** Operational decisions are frequent, measurable, and high-volume — ideal for continuous monitoring. Dimensional Is/Is Not analysis maps naturally to production lines, facilities, shifts, SKUs.

#### 3. Sales & Revenue — VP Revenue / CRO ⭐⭐⭐
- **Size:** 10,000+ B2B mid-market companies
- **ARPU:** $30K-$60K (VP entry), $60K-$100K (CRO expansion)
- **Pain:** Pipeline metrics reviewed weekly but anomalies caught late; win rate changes not root-caused; pricing and discount decisions made without structured analysis; territory performance variance unexplained
- **Trigger Events:** Revenue miss, new CRO hire, GTM restructuring, pricing overhaul, churn spike
- **Why strong fit:** Revenue KPIs are well-defined and time-sensitive. Opportunity detection (positive outperformance in a segment) directly maps to replication strategies.

#### 4. Never-Engaged Mid-Market (Cross-Domain) ⭐⭐⭐ *(Primary TAM)*
- **Size:** 50,000+ companies ($50M-$500M revenue) — larger than the consulting-displacement segment
- **ARPU:** $44K-$80K (net-new capability, not a substitute comparison)
- **Pain:** Executives + spreadsheets + gut instinct across all domains; no structured analysis; no access to MBB-quality frameworks at their scale
- **Why they buy:** Not "cheaper consulting" — *capability they've never had*. First structured multi-perspective decision support. Easier sell: no competitive displacement, no incumbent to displace.
- **Trigger Events:** Margin squeeze, rapid growth, PE acquisition, new executive mandate
- **Sales note:** Shortest sales cycle. No "but we have McKinsey" objection. Pain is immediate and tangible. Best entry point for early pilots — reference customer proof unlocks higher-ACV deals.

#### 5. PE Portfolio Operations ⭐⭐⭐
- **Size:** 500 firms
- **ARPU:** $150K-$230K (platform fee + per-portfolio-company activation)
- **Pain:** Inconsistent KPI definitions across portfolio, manual value creation tracking, LP reporting overhead — across finance, ops, and revenue domains
- **Trigger Events:** Post-acquisition, value creation mandate, new GP joining portfolio ops team
- **Commercial structure:** Platform fee ($40K-$60K) + per-portfolio-company fee ($20K-$30K); expands automatically with new acquisitions
- **Cross-domain advantage:** PE firms need standardized decision intelligence across portfolio companies in different industries — Decision Studio's domain-agnostic architecture is a natural fit

#### 6. Corporate Strategy Teams ⭐⭐
- **Size:** 500 F500 companies
- **ARPU:** $300K+
- **Pain:** Strategic decisions need multiple perspectives across domains
- **Trigger Events:** Activist investor pressure, IPO prep, M&A due diligence
- **Note:** Deferred to Year 2+ — procurement complexity too high for solo founder Year 1

### Ideal Customer Profile

**Firmographics:**
- Mid-market or PE-backed company
- $50M-$5B revenue
- 200-5,000 employees

**Technographics:**
- Data platform: Snowflake, Databricks, BigQuery, SQL Server, SAP Datasphere, or structured CSV/Excel exports
- Source systems: ERP (SAP, Oracle, NetSuite), CRM (Salesforce, HubSpot), WMS/MES, or any system producing KPI-measurable data
- Existing BI tools (Tableau, Power BI, Looker) — indicates data maturity
- AI policy approved (or willingness to establish one for pilot)

**Psychographics:**
- Executives making recurring decisions without structured analysis frameworks
- Frustrated with consulting speed/cost OR never engaged consulting at all (net-new capability)
- Data exists but insight extraction is manual, slow, or siloed by department
- Innovation mandate from CEO/board, or operational pressure demanding faster decisions
- Willing to try new approaches

**Budget:**
- $50K-$200K decision support / analytics / consulting budget (or equivalent operational budget)
- Or: demonstrable cost-of-inaction exceeding $500K/year (Decision Studio can quantify this)

### Anti-Patterns (Avoid)

#### ❌ No Data Infrastructure
- Company lacks structured data systems (no ERP, CRM, WMS, or data warehouse)
- KPIs not defined or measured — data lives in ad hoc spreadsheets with no consistency
- **Why:** Would require months of data engineering before delivering value

#### ❌ "Innovation Theater" Culture
- Pilots get approved but never go to production
- Innovation budget exists but decisions blocked by committees
- **Why:** Waste time on pilots that never convert to revenue

#### ❌ Entrenched Advisory Relationships
- Long-standing strategic relationships with MBB or domain-specific consultancies
- External advisory firm embedded in the decision-making process
- **Why:** Political blockers — competing with trusted advisors who have budget lock-in

#### ❌ No AI Policy / No Executive Sponsor
- Company has no internal policy on AI tool usage and no champion willing to push one through
- Legal/compliance hasn't approved AI for operational data
- **Why:** Deal stuck in legal review for 6-12 months; no internal advocate to unblock

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

### Phase 0: Demo-Ready (Mar-Apr 2026) ✅ COMPLETE

**Status (May 2026):** All 5 value pillars have shipped product (SA + DA + SF + MA + VA + Opportunity). Production deployment is live (Railway + Cloudflare Pages + Supabase Cloud since Apr 2026). Swiss Style brand identity shipped across all UI surfaces. Multi-warehouse direct SDK connectors operational (DuckDB, BigQuery, Snowflake; SQL Server in dev). PIB email delivery with single-use tokens and delegation flow shipped. VA 5-phase lifecycle and white-paper report shipped.

**Completed:**
- ✅ Pre-video UI polish (sticky footer, accordion collapse, registry editing)
- ✅ Swiss Style brand refresh across Login, DelegatePage, ActionHandler, ExecutiveBriefing, Portfolio
- ✅ Production deployment (Railway + Cloudflare Pages + Supabase Cloud, GCP credentials for BigQuery)
- ✅ Multi-warehouse direct SDK connectors (Phase 10C)
- ✅ PIB email delivery + delegation flow (Phase 10B)
- ✅ VA 5-phase lifecycle + white-paper report

**Remaining (carries into Phase 1):**
- 🔄 Record demo video (Situation Awareness → Deep Analysis → Market Intelligence → Solution Finder → Approve & Track → VA Portfolio)
- 🔄 Build landing page
- 🔄 Prepare 3-slide pitch deck for discovery calls

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

**Production data backends (Updated May 2026):**

| Backend | Role | Status |
|---------|------|--------|
| **Supabase/PostgreSQL** | Platform state (registries, situations, VA solutions) + pilot extract storage | ✅ Operational |
| **BigQuery** | Customer analytics data (read-only) | ✅ Operational |
| **Snowflake** | Customer analytics data (read-only) — verified end-to-end via SA scan | ✅ Operational (Phase 10C) |
| **Databricks** | Customer analytics data (read-only, Unity Catalog / SQL warehouse) | ✅ Operational (Phase 10C) |
| **SQL Server** | Customer analytics data (read-only) — common in companies running SAP, Oracle ERP, or legacy on-prem stacks | ✅ Operational in dev; production gated on ODBC driver in Dockerfile + Azure SQL for cloud demo data |
| **SAP Datasphere** | Customer analytics data (read-only) — direct connection for SAP-native customers; eliminates CSV extract step | 📋 Planned |
| **DuckDB** | Local development only — used for early prototyping with SAP sample CSV data; not customer-facing | ✅ Dev only |

**Connector reality (May 2026):** Snowflake, BigQuery, and Databricks direct SDK connectors are operational and SA-scan verified. SQL Server works in local dev but the Railway production container lacks the Microsoft ODBC Driver 18 — fix is tracked as Infra A4 (add ODBC driver to Dockerfile + stand up Azure SQL for hess demo data). SAP Datasphere remains roadmap. Each connector reuses the Data Product Agent architecture — schema inspection, contract generation, and KPI mapping are backend-agnostic by design.

**Connectivity tier framework (Apr 2026 strategic refresh):** Agent9 connects to customer warehouses at three progressive levels — Tier 1 native SDK (where Agent9 owns the connection), Tier 2 vendor MCP server (vendor hosts the endpoint; Agent9-generated SQL flows through), and Tier 3 vendor AI agent (Cortex Analyst, Genie — handle complex NL follow-up). SA and DA always operate at Tier 1 or 2 for deterministic monitoring; Tier 3 is for ad-hoc questions only. The DGA routes across tiers. Phase 10C ships Tier 1 for the four backends above; Phase 10D wires Tier 2 via decorator pattern as vendor MCPs mature; Phase 11F adds Tier 3 routing for follow-up.

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

### Direct Competitors (Updated May 2026)

| Player | What They Do | Gap/Weakness |
|--------|--------------|---------------|
| **McKinsey/BCG/Bain** | Human consulting (+ internal AI tools like Lilli) | Slow (12-24 weeks), expensive ($500K-$2M), single perspective. Building AI internally but not productizing for mid-market. |
| **ChatGPT/Claude/Gemini** | Generic AI + agent frameworks | No domain expertise, no audit trail, no registry-driven context. Improving rapidly. |
| **Hebbia ($130M raised)** | AI analyst for PE/finance | Strong in document analysis; lacks multi-agent debate, registry depth, and consulting methodology framing. |
| **Numeric / Runway / Mosaic** | AI-powered FP&A and financial close | Narrow scope (financial operations only); no strategic advisory or multi-perspective analysis. |
| **Palantir AIP** | Data platform + AI agents | Enterprise-grade but complex, expensive, and technical — not strategic advisory. |
| **AWS Bedrock / Azure AI Agents** | Cloud-native agent orchestration | Infrastructure layer — no domain models, no consulting methodology, no vertical application. |
| **Tableau/Power BI + Copilot** | Dashboards + AI narration | Shows data and explains trends; doesn't advise, recommend, or debate options. |
| **Snowflake Cortex Analyst** | Vendor-native NL-to-SQL + semantic views over Snowflake data | Answers data questions; not a decision pipeline. No SA monitoring, no DA dimensional root cause, no SF multi-persona debate, no VA outcome tracking. Agent9 adapts to it (Tier 3 routing) rather than competes. |
| **Databricks Genie Spaces / AI/BI** | Vendor-native conversational analytics over Unity Catalog | Same gap as Cortex — strong on data access and NL questions; no automated KPI monitoring, root-cause analysis, or post-decision attribution. |

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

### Strategic Positioning (Updated May 2026)

The Apr 2026 strategic refresh draws a hard line between Agent9's moat and the commodity layer beneath it.

**Moat layer — never outsource:**
- The SA → DA → MA → SF → VA pipeline (market context → automated KPI monitoring → dimensional root-cause analysis → multi-persona solution debate → DiD outcome attribution)
- Registry-driven domain intelligence (KPIs, principals, business processes, data products, glossary — encoded per customer, deepens over time)
- VA outcome corpus (every approved decision creates a tracked trajectory; cross-customer pattern insights compound)
- Executive briefing composition, single-use tokens, delegation flow, HITL approval
- Calibrated monitoring profiles + validated signal/noise history (compounding moat — 12 months of calibration is hard to replicate)

**Commodity layer — Agent9 adapts to vendor semantic layers:**
- Database connectivity and query execution (Snowflake, Databricks, BigQuery vendors do this better)
- Schema discovery and metadata enrichment (Unity Catalog, Cortex semantic views)
- NL-to-SQL translation (Cortex Analyst, Genie commoditize this)
- Basic data governance (RBAC, row/column security)

**Architectural consequence:** The Data Product Agent and NLP Interface Agent become thin adapters over whatever semantic layer the customer has. The Data Governance Agent is the intelligent router that knows which data product answers each question and which vendor semantic layer to use. Agent9's data contracts remain the fallback for customers without vendor semantic layers, and the substrate for the onboarding workflow.

*Key competitive insight: Multi-agent orchestration AND data connectivity are both becoming commodity infrastructure. The durable differentiator is the analytical pipeline itself + the registry domain model + the VA outcome corpus — none of which any vendor is building. No competitor in any category offers post-decision ROI attribution with visual trajectory tracking.*

### Defensibility & Moat (Revised May 2026)

| Moat | Durability | How It Works |
|------|-----------|---------------|
| **SA→DA→MA→SF→VA Pipeline** | 🟢 Strong (the moat) | The full loop — market context + framing → automated KPI monitoring → dimensional root-cause analysis → multi-persona solution debate → DiD outcome attribution — is what no vendor is building. Cortex Analyst and Genie answer questions; they do not run this pipeline. This is the product. |
| **Registry-Driven Domain Intelligence** | 🟢 Strong | KPI definitions, principal profiles, business process mappings, data product contracts — deep enterprise context that takes months to build per customer. Hard to replicate without similar architecture. |
| **5-Day Onboarding Template Library** | 🟢 Strong (compounds with customers) | Pre-built data product contracts and KPI templates per ERP/data stack (SAP, Oracle, NetSuite, Snowflake). First customer takes 5 days; tenth customer in same stack takes 2. Competitors starting from scratch need months. *See Onboarding Moat document.* |
| **Decision Outcome Corpus** | 🟢 Strong (grows with customers) | Every debate, analysis, and recommendation builds a proprietary dataset of decision patterns. More customers = better recommendations. |
| **Operational Embedding** | 🟢 Strong (grows over time) | Once integrated into monthly close process, board pack preparation, and KPI monitoring rhythm, switching cost grows every month. By month 6, the registry IS their source of truth. |
| **Value Assurance Feedback Loop** | 🟢 Strong (grows with decisions) | Every approved decision creates a tracked trajectory — inaction projection, expected recovery, actual outcome. Over time, this builds a proprietary decision quality corpus: which types of recommendations work for this company, at this scale, in this industry. No competitor tracks post-decision KPI attribution. |
| **Calibrated Monitoring Profiles** | 🟢 Strong (compounding) | After 12 months, switching means losing calibrated noise/signal thresholds for 50+ KPIs and validated escalation history. Phase 11D adaptive calibration loop deepens this further. |
| **Audit Trail Standard** | 🟡 Medium | First to define "explainable AI decision intelligence" with full provenance. Defensible until cloud platforms add similar features (~18-24 months). |
| **Partner Network** | 🔴 Future (Year 3+) | Not a moat until partners exist. Mid-tier consulting firms (FTI, A&M, Huron) are the first targets. Lead generation + revenue assurance framing. *See Consulting Partner Strategy document.* |

**Multi-agent orchestration AND data connectivity are explicitly NOT listed as moats.** Both are commodity infrastructure — orchestration via AWS Bedrock / Azure AI Agents / LangGraph, connectivity via vendor MCP servers and semantic layers. The moat is the analytical pipeline itself, the registry domain model, the VA outcome corpus, and the calibrated monitoring profiles that compound with each customer-month.

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

### Milestones (Rebased to May 2026)

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| SA→DA→SF pipeline stable (19-page Executive Briefing) | Mar 2026 | ✅ Complete |
| 5-pillar value proposition + updated strategy docs | Mar 2026 | ✅ Complete |
| Market Analysis Agent PRD complete | Mar 2026 | ✅ Complete |
| Market Analysis Agent built + wired into SF pipeline | Apr 2026 | ✅ Complete |
| Positive KPI opportunity detection (SA) | Apr 2026 | ✅ Complete |
| Value Assurance data model + 5-phase lifecycle (Approved→Implementing→Live→Measuring→Complete) | Apr 2026 | ✅ Complete |
| Swiss Style brand refresh (Phase 10A) | Apr 2026 | ✅ Complete |
| PIB email delivery + single-use tokens + delegation flow (Phase 10B) | Apr 2026 | ✅ Complete |
| White-paper report (Gartner-style, /report/:situationId) | Apr 2026 | ✅ Complete |
| Production deployment live (Railway + Cloudflare Pages + Supabase Cloud) | Apr 2026 | ✅ Complete |
| Multi-warehouse direct SDK connectors (DuckDB, BigQuery, Snowflake, SQL Server dev) (Phase 10C) | May 2026 | ✅ Complete |
| Solution Finder performance tuning (fast/full debate modes, Phase 10D) | Apr 2026 | ✅ Complete |
| Demo video recorded (lubricants + bikes) | Q2 2026 | 🔄 In progress |
| Landing page live | Q2 2026 | 🔄 In progress |
| First 20 warm contacts identified (FP&A + never-engaged CFO) | May–Jun 2026 | 📋 Pending |
| First 10 discovery calls | Jun–Jul 2026 | 📋 Pending |
| Infra A4 registry live-reload + SQL Server production enablement | Jul–Aug 2026 | 📋 Pending |
| Infra B: Auth + multi-tenant isolation (pre-pilot blocker) | Aug 2026 | 📋 Pending |
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

**1. Commoditization Risk: Multi-agent orchestration AND data connectivity both become table stakes** *(Updated May 2026)*
- **Mitigation:** Shift differentiation from orchestration and connectivity to the SA→DA→MA→SF→VA pipeline + Registry domain model + VA outcome corpus. Vendor semantic layers (Snowflake Cortex Analyst, Databricks Genie) commoditize NL-to-SQL and data access; Agent9 adapts to them (Tier 2/3 routing) rather than competes. The DPA and NLP agents become thin adapters; the analytical pipeline above them is what no vendor is building.
- **Likelihood:** High (already happening — AWS Bedrock, Azure AI Agents, LangGraph for orchestration; Cortex Analyst, Genie Spaces, Unity Catalog for connectivity)
- **Impact:** High if Agent9 over-invests in orchestration/connectivity; Low if focus stays on the pipeline + registry + VA corpus

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

*The platform is deployed and live as of May 2026. Production hosting (Railway backend + Cloudflare Pages frontend + Supabase Cloud database + GCP credentials for BigQuery) is operational. Multi-tenant isolation, authentication, registry live-reload, and monitoring must be hardened before the first pilot customer.*

### Phase 0: Free-Tier / Self-Funded Launch ✅ COMPLETE (Apr 2026)

Backend deployed to Railway (Docker/FastAPI; on a paid tier for no-sleep reliability). Frontend on Cloudflare Pages (replaced Vercel Apr 2026). Database on Supabase Cloud (Postgres). BigQuery access via `GCP_SERVICE_ACCOUNT_JSON` env var materialized at startup. Domain registered, SSL via hosting providers. Every push to `master` triggers automatic deployment (2–3 min) to both Cloudflare Pages and Railway.

**Phase 0 hard cost: ~$50/year (domains) + Railway paid tier (~$20/month) + Supabase free tier.**

### Phase 1: Pre-Pilot Hardening (May–Aug 2026)

Items in flight or queued before first signed pilot. Tracked in `DEVELOPMENT_PLAN.md` as Infra A2, A3, A4.

| Item | Priority | Effort | Status / Notes |
|------|----------|--------|----------------|
| **Registry live-reload (Infra A4)** | 🔴 Critical | 1–2 weeks | SA, PCA, DPA cache registry at startup; new client requires Railway restart. Fix: per-request Supabase reads. Discovered when seeding the hess (SQL Server) client. |
| **Admin-triggered registry reload endpoint** | 🔴 Critical | 1–2 days | `POST /api/v1/admin/registry/reload` — operational stopgap until live-reload ships. |
| **SQL Server production enablement** | 🟠 High | 3–5 days | Add Microsoft ODBC Driver 18 + unixODBC to Dockerfile (~200MB, ~2 min build); stand up Azure SQL Database for hess demo data (~$5–15/month). Currently works in dev only. |
| **Platform Admin & Client Onboarding UI (Infra A2)** | 🟠 High | 2–3 weeks | Composes existing Company Profile + Data Product Onboarding wizards into a guided 4-step flow. Replaces seed-script dependency. Required before non-engineer can onboard a client. |
| **Usage monitoring (Infra A3)** | 🟡 Medium | 1 week | `usage_events` table, monthly rollup view, admin dashboard, client-facing usage widget. No automated billing yet — pricing conversations only. |
| **Connection health dashboard** | 🟡 Medium | 3–5 days | Per-data-product connection status (Snowflake auto-suspend, SQL Server VPN, BigQuery quota). Operational visibility before 3rd client. |

### Phase 2: Customer Infrastructure (Pre-First-Pilot, target Aug–Sep 2026)

Hard blockers for first signed pilot. Tracked as Infra B.

| Item | Priority | Effort | Notes |
|------|----------|--------|-------|
| **Authentication** | 🔴 Critical | 1–2 weeks | Supabase Auth (email + password) + API keys for programmatic access. Required before any production-grade pilot. |
| **Multi-tenant isolation** | 🔴 Critical | 2–3 weeks | Per-customer Supabase project OR Row-Level Security with strict `client_id` enforcement. Cannot run two customers simultaneously without this. |
| **Customer provisioning script** | 🔴 Critical | 1 week | Create project → seed registries → configure contracts → send welcome. Runs server-side from Platform Admin UI; no developer machine involvement. |
| **CI/CD pipeline (GitHub Actions)** | 🟠 High | 3–5 days | test → build → staging → manual promote to production. |
| **Error monitoring (Sentry)** | 🟠 High | 1 day | Free tier sufficient until 5K errors/month. |
| **Staging environment** | 🟠 High | 3–5 days | Separate Railway instance + Supabase project. Pre-production validation. |
| **Automated registry backups** | 🟠 High | 2–3 days | Nightly Supabase export to versioned storage. |
| **Customer data export** | 🟡 Medium | 1 week | Self-service export for enterprise procurement. |

**Phase 2 cost:** $200–$500/month base + $50–$100/month per customer on paid tiers.

### Phase 3: Enterprise Optional (post-first-pilot, as needed)

Tracked as Infra B2 — built only when a prospect is blocked specifically by data residency or LLM provider requirements.

| Item | Trigger |
|------|---------|
| **Azure OpenAI provider in A9_LLM_Service_Agent** | Regulated-industry prospect (banking, pharma, PE-backed) cannot send data to Anthropic API. |
| **LLM prompt audit export (JSON download)** | GC/CISO review path before contract signing. |
| **Enterprise security one-pager** | Standardized answers to the five security questions enterprise buyers raise. |
| **On-premise LLM stub (Ollama)** | Customer with no cloud allowed. Quality trade-off vs Claude/GPT-4o is significant; evaluate per-customer. |

**When to upgrade to paid tiers:**
- **First demo to a real prospect:** Upgrade backend hosting to eliminate cold-start delays (~$7-$20/month)
- **First paying customer:** Upgrade Supabase to Pro for daily backups and production SLA (~$25/month)
- **Estimated paid-tier cost when triggered:** ~$50-$75/month — still negligible vs. even a single pilot at $18K-$40K/year

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

| Phase | Timeline | One-Time (effort) | Monthly Recurring | Trigger |
|-------|----------|-------------------|-------------------|---------|
| Phase 0 (deploy) | Apr-May 2026 | ~1 week founder time | $0 (free tiers) → $50-$75 when first customer signs | Before first demo |
| Phase 1-2 (customers) | May 2026-Feb 2027 | $10K-$20K | $75-$200 base + $25-$50/customer | Before first pilot |
| Phase 2-3 (partners) | Mar-Dec 2027 | $15K-$30K | $500-$1K | When 5+ customers + Tier 1 partner conversations begin |
| Phase 3+ (enterprise) | 2028 | $50K-$100K | $2K-$5K | When pursuing $100K+ ACV deals |

**Phase 0 hard cost: $15-$50/year (domain only).** All hosting, database, auth, monitoring, and email run on free tiers through demos and early outreach. Paid tiers (~$50-$75/month) activate only when a paying customer requires production reliability.

**Total infrastructure investment through Year 3:** $75K-$150K (primarily effort, not vendor spend)
**As % of Year 3 base ARR ($1.13M-$2.23M):** 3.4-13% — well within SaaS infrastructure cost norms (typically 15-25% of revenue)

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

## 15. Next Steps (30/60/90 Days from May 2026)

### Next 30 Days (May–Jun 2026) — Pre-Outreach Polish + Pre-Pilot Hardening
- [ ] Record 5-minute demo video (lubricants end-to-end: SA → DA → MA → SF → Approve & Track → VA Portfolio + white-paper report)
- [ ] Launch landing page (trydecisionstudio.com) — static site with contact form
- [ ] Draft 2-slide pitch deck: FP&A entry pitch + CFO expansion pitch
- [ ] Start Infra A4: registry live-reload fix (SA/PCA/DPA agents per-request Supabase reads)
- [ ] Identify first 20 warm contacts (never-engaged mid-market CFOs, VP FP&A) — outreach list only, no commercial contact yet

### Next 60 Days (Jun–Jul 2026) — Outreach + Infra Hardening
- [ ] Begin warm network outreach — 20 contacts prioritising never-engaged mid-market CFOs and VP FP&A
- [ ] Schedule first 10 discovery calls (position as "AI Decision Intelligence", not "consulting marketplace")
- [ ] First discovery insight: are prospects more receptive as never-engaged (net-new) or consulting-augmentation buyers?
- [ ] Ship SQL Server production enablement (ODBC driver in Dockerfile + Azure SQL for hess demo data)
- [ ] Start Infra A2: Platform Admin + Client Onboarding UI

### Next 90 Days (Aug–Sep 2026) — First Pilot
- [ ] Ship Infra B: Supabase Auth + multi-tenant isolation (pre-pilot blocker)
- [ ] Identify 3–5 serious prospects; create tailored demos
- [ ] Send first pilot proposals at $18K–$30K (Fast Start Pilot tier)
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
- **Version:** 1.6
- **Last Updated:** May 2026
- **Next Review:** After first pilot signed (Sep 2026)
- **Owner:** Founder/CEO
