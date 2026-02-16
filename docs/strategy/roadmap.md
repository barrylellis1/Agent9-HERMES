# Agent9 Product Roadmap
**Last Updated:** February 2026
**Version:** 2.0 — Agent-sequenced, business-value-driven

---

## Guiding Principles

1. **Every agent built must map to a customer conversation.** If we can't explain why a CFO or FP&A team cares, it doesn't get prioritised.
2. **Multi-agent orchestration is infrastructure, not a differentiator.** All platform/technical work is in service of agent capability delivery.
3. **The consulting firm partner model shapes Phase 3 sequencing.** Agents that enable the delivery lifecycle (change management, stakeholder engagement) are prerequisites for partner conversations.
4. **5-day onboarding is a product capability, not just a process.** KPI Assistant Agent completion and template library expansion directly enable it.

---

## Current State (February 2026) — Built and Functional

### Core Agent Platform
- ✅ A9_Orchestrator_Agent — workflow coordination, agent lifecycle, dependency resolution
- ✅ A9_Situation_Awareness_Agent — continuous KPI monitoring, anomaly detection, severity scoring
- ✅ A9_Deep_Analysis_Agent — SCQA root cause analysis, KT Is/Is-Not decomposition, dimensional variance
- ✅ A9_Solution_Finder_Agent — multi-perspective debate, trade-off matrix, reversibility scoring
- ✅ A9_Principal_Context_Agent — role-based personalisation (CFO, CEO, COO, Finance Manager)
- ✅ A9_Data_Governance_Agent — data access policies, business term translation, audit logging
- ✅ A9_Data_Product_Agent — data product registry, SQL execution delegation, schema validation
- ✅ A9_LLM_Service_Agent — centralised LLM routing, model selection, prompt engineering
- ✅ A9_NLP_Interface_Agent — natural language query parsing, intent recognition
- ✅ A9_Data_Product_MCP_Service_Agent — SQL execution against DuckDB/Snowflake/BigQuery
- 🔄 A9_KPI_Assistant_Agent — partial build; LLM integration and SQL validation TODOs pending

### Platform Infrastructure
- ✅ Decision Studio UI (React, functional)
- ✅ Registry Explorer (KPIs, principals, business processes, data products, glossary)
- ✅ Database-agnostic backend (DuckDB, Supabase/Postgres, BigQuery)
- ✅ Audit trail and HITL checkpoints
- ✅ Principal-driven analysis (decision style → consulting persona framing)

### Known Issues to Resolve Before First Demo
- 🔴 Hardcoded `C:\Users\barry\` path in a9_solution_finder_agent.py:821
- 🔴 Business process field name mismatch (kpi_registry vs principal_registry)
- ⚠️ KPI Assistant Agent LLM integration incomplete (4 TODOs)
- ⚠️ McKinsey/BCG agent diagram removed from external-facing materials (done in exec summary)

---

## Phase 0 — Demo Ready (Now → April 2026)
*Goal: One compelling 5-minute demo. Zero new agent builds except Risk Analysis.*

### Product Work
- [ ] Fix hardcoded path in a9_solution_finder_agent.py:821
- [ ] Fix business process field name mismatch across registries
- [ ] Complete KPI Assistant Agent LLM integration (4 TODOs)
- [ ] Demo flow polish: Situation → Deep Analysis → Solution Finder → Audit Trail
- [ ] **A9_Risk_Analysis_Agent** — Build now (simple/MVP scope, 3 risk types, standalone)
  - *Why now:* Completes the core workflow loop; every solution recommendation currently has no risk score
  - *Spec:* Market risk, operational risk, financial risk; weighted scoring; plain-language summary
  - *Effort:* 1-2 sprints

### GTM Work
- [ ] Record 5-minute demo video
- [ ] Build landing page (agent9.ai)
- [ ] List 20 warm contacts (FP&A and CFO-level)
- [ ] Draft 2-slide pitch deck: FP&A entry pitch + CFO expansion pitch

---

## Phase 1 — Pilot Delivery (May 2026 → March 2027)
*Goal: 1-2 signed pilots, deliver successfully, build first case study. Build agents that make pilots stickier and more valuable.*

### Agent Builds

**A9_Market_Analysis_Agent** *(High priority — build during pilot delivery)*
- **Why now:** LLM problem-refinement questions already point to regulatory/market context gaps (observed in Decision Studio testing). Agent needed before second demo cycle.
- **What it does:** Continuously monitors market trends, competitor actions, regulatory signals; contextualises internal KPI situations with external intelligence
- **Customer value:** "Your margin decline isn't just internal — raw material costs rose 8% industry-wide this quarter"
- **Partner value:** Automates the 2-3 week research phase consulting firms charge premium rates to deliver
- **Dependency:** LLM Service Agent (for web research queries)
- **Effort:** 3-4 sprints

**A9_Stakeholder_Analysis_Agent** *(Medium priority — build in second half of Phase 1)*
- **Why Phase 1:** When pilots produce their first solution recommendations, the CFO's next question is "who do I need to get on board?" This agent answers that.
- **What it does:** Maps stakeholder landscape, assesses influence/impact, identifies domain owners, generates StakeholderAnalysisCompletedEvent
- **Customer value:** Makes recommendations actionable — not just "raise prices" but "here's who needs to approve it and who might resist"
- **Effort:** 2-3 sprints

**A9_Stakeholder_Engagement_Agent** *(Build paired with Stakeholder Analysis)*
- **What it does:** Measures engagement levels, generates targeted engagement recommendations by stakeholder, flags critical low-engagement alerts
- **Effort:** 2 sprints

### Platform Work (Phase 1)
- [ ] Lead attribution tracking — log every situation that converts to external consulting engagement
- [ ] 5-day onboarding Fast Start process (see Onboarding Moat document)
- [ ] SAP DataSphere onboarding template v1 (based on existing fi_star_schema.yaml work)
- [ ] Build pre-onboarding data readiness checklist

---

## Phase 2 — Post-Revenue Growth (April 2027 → December 2027)
*Goal: 5-8 customers, annual contract conversions, close the consulting delivery loop. This phase builds the agents that enable the consulting firm partner model.*

### Agent Builds

**A9_Change_Management_Agent** *(Highest strategic priority in Phase 2)*
- **Why:** This agent closes the value loop that no other tool closes. Agent9 currently recommends; Change Management tracks whether the recommendation delivered the promised value.
- **What it does:** Universal change lifecycle governance — impact/readiness assessment, communication strategy, value realisation tracking against declared KPIs, HITL approval workflows, compliance audit trail
- **Customer value:** "We recommended a pricing change. 6 months later, margin improved $1.8M vs $2M projected. Here's why it fell short and what to adjust."
- **Partner value:** Consulting firms can manage their delivery phase through Agent9, not just the diagnosis phase
- **Dependencies:** Stakeholder Engagement Agent, Implementation Tracker Agent, Data Product Agent, Risk Management Agent
- **Effort:** 5-6 sprints

**A9_Implementation_Tracker_Agent** *(Build alongside Change Management)*
- **What it does:** Task-level execution tracking, owner accountability, escalation to Change Management, real-time progress visibility
- **Customer value:** The "is the plan actually happening?" layer; creates daily habit loop that drives deep embedding
- **Effort:** 3 sprints

**A9_Risk_Management_Agent** *(Build for PE/compliance segment)*
- **What it does:** Takes Risk Analysis scores → implements mitigation strategies → monitors risk indicators → produces LP-reporting-grade audit trail with HITL enforcement on all actions
- **Customer value:** PE firms can show LPs documented evidence of how portfolio risks were identified, assessed, and mitigated
- **Dependencies:** Risk Analysis Agent
- **Effort:** 4 sprints

**A9_Opportunity_Analysis_Agent** *(Build for proactive value prop)*
- **What it does:** Scores opportunities across 5 dimensions (market, product, partnership, innovation, optimisation); produces ranked, quantified opportunity list
- **Customer value:** "Here's what could go right" counterpart to Situation Awareness "here's what's going wrong"
- **PE portfolio value:** Systematic value creation opportunity scanning across portfolio companies
- **Dependencies:** Market Analysis Agent
- **Effort:** 2-3 sprints

### Platform Work (Phase 2)
- [ ] Oracle NetSuite onboarding template
- [ ] Consulting partner portal v1 (lead attribution dashboard, agent usage tracking)
- [ ] Begin SOC 2 readiness assessment
- [ ] Hire #1: Sales/Customer Success (triggered by 2+ paying customers)

---

## Phase 3 — Scale (2028)
*Goal: 10-20 customers, first consulting firm partnerships, enterprise tier. Extend platform to operations buyer and build innovation pipeline.*

### Agent Builds

**A9_Performance_Optimization_Agent**
- **What it does:** Broader operational benchmarking beyond KPI root cause — resource allocation analysis, cross-metric trend analysis, process efficiency scoring
- **Customer value:** Extends Agent9 to COO buyer (second buyer in existing accounts); creates expansion revenue without new customer acquisition
- **Effort:** 4-5 sprints

**A9_Business_Optimization_Agent**
- **What it does:** Continuous process improvement engine — identifies workflow inefficiencies, recommends optimisations, tracks improvement outcomes over time
- **Customer value:** Long-term retention driver; every month of use generates new improvement recommendations
- **Effort:** 4-5 sprints

**A9_Innovation_Driver_Agent**
- **What it does:** Systematic innovation pipeline — identifies opportunities from Market Analysis + Solution Finder, evaluates feasibility/impact/strategic fit, coordinates implementation through Implementation Tracker
- **Partner value:** Enables consulting firms to offer structured innovation advisory through Agent9
- **Effort:** 4-5 sprints

### Platform Work (Phase 3)
- [ ] Snowflake + dbt onboarding template
- [ ] Enterprise tier launch ($100K+ ACV with SOC 2 Type II)
- [ ] First mid-tier consulting firm partner pilot (FTI, A&M, or Huron)
- [ ] Partner onboarding workflow — methodology encoding, branded agent configuration, revenue share tracking
- [ ] Hire #2: Platform Engineer; Hire #3: Product/Design

---

## Phase 4 — Partner Enablement (2028+)
*Goal: Consulting firm marketplace, branded agents, multi-party revenue model.*

### Agent Builds

**A9_Innovation_GenAI_Expert_Agent**
- AI/ML solution evaluation and architecture design
- Enables AI strategy advisory as a consulting firm offering
- Effort: Complex (5-6 sprints)

**A9_Solution_Architect_Agent**
- Architecture pattern management and technical validation
- Enables technology advisory engagements through Agent9
- Effort: Complex (5-6 sprints)

**A9_Quality_Assurance_Agent**
- Internal platform reliability and compliance testing
- Customer-facing value: compliance validation for regulated industries
- Effort: Medium (3 sprints)

### Platform Work (Phase 4)
- [ ] Branded agent marketplace — partner IP encoding, licensing, usage tracking, revenue share
- [ ] RAG integration — partner knowledge bases embedded in agent context
- [ ] BI Embed Adapter — situation cards surfaced in Tableau/Power BI
- [ ] Cloud Agent Bridge — map Agent9 protocols to Bedrock/Azure AI Agent Service

---

## Deprioritised / Not Building

**A9_UI_Design_Agent** — No customer-facing value. UI design generation is a developer productivity concern, not a business intelligence feature. If needed, use external LLM tooling.

---

## Agent Sequencing Summary

```
PHASE 0 (Now)
  Risk Analysis ─────────────────────────────── Completes core workflow loop

PHASE 1 (2026 pilots)
  Market Analysis ────────────────────────────── External intelligence layer
  Stakeholder Analysis + Engagement ──────────── Makes recommendations actionable

PHASE 2 (2027 growth)
  Change Management ──────────────────────────── Closes value loop; partner enablement
  Implementation Tracker ─────────────────────── Delivery visibility; habit loop
  Risk Management ────────────────────────────── PE/compliance segment
  Opportunity Analysis ───────────────────────── Proactive value prop; PE scanning

PHASE 3 (2028 scale)
  Performance Optimization ───────────────────── COO buyer; account expansion
  Business Optimization ──────────────────────── Long-term retention
  Innovation Driver ──────────────────────────── Partner-enabling; innovation advisory

PHASE 4 (2028+ marketplace)
  Innovation GenAI Expert ────────────────────── AI strategy advisory for partners
  Solution Architect ─────────────────────────── Technical advisory for partners
  Quality Assurance ──────────────────────────── Platform reliability; compliance
```

---

## Milestone Summary

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Risk Analysis Agent built | Mar 2026 | 📋 Pending |
| Hardcoded path + BP field name fixes | Mar 2026 | 📋 Pending |
| KPI Assistant Agent LLM integration complete | Mar 2026 | 📋 Pending |
| Demo video recorded | Apr 2026 | 🔄 In progress |
| Landing page live | Apr 2026 | 📋 Pending |
| Market Analysis Agent built | Jun 2026 | 📋 Pending |
| First pilot signed | Sep 2026 | 📋 Pending |
| Stakeholder Analysis + Engagement built | Oct 2026 | 📋 Pending |
| 5-day onboarding template v1 (SAP) | Oct 2026 | 📋 Pending |
| First case study documented | Jan 2027 | 📋 Pending |
| Change Management Agent built | Apr 2027 | 📋 Pending |
| Implementation Tracker + Risk Management built | Jun 2027 | 📋 Pending |
| Hire #1 (Sales/CS) | Jun 2027 | 📋 Pending |
| Opportunity Analysis Agent built | Aug 2027 | 📋 Pending |
| 5 customers / $300K-$480K ARR (base) | Dec 2027 | 📋 Pending |
| SOC 2 readiness | H1 2028 | 📋 Pending |
| First consulting firm partner pilot | H2 2028 | 📋 Pending |
| Performance + Business Optimization built | H2 2028 | 📋 Pending |
| 10+ customers / $800K+ ARR (base) | Jan 2029 | 📋 Pending |

---

*This roadmap supersedes the previous version (roadmap.md v1.0, Jun 2025). Previous version focused on technical infrastructure phases. This version sequences by business value delivery and consulting partner model enablement.*
