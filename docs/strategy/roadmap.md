# Agent9 Product Roadmap
**Last Updated:** May 2026
**Version:** 2.3 — Phase 10A-10D shipped (Swiss Style UI, PIB email delivery, multi-warehouse direct SDK connectors, SF performance tuning, VA 5-phase lifecycle, white-paper report); production deployment live (Railway + Cloudflare Pages + Supabase Cloud since Apr 2026); strategic moat refresh — the SA→DA→SF→VA pipeline + Registry + VA outcome corpus is the moat; data connectivity is commodity (vendors like Snowflake Cortex Analyst and Databricks Genie commoditize it)

---

## Guiding Principles

1. **Every agent built must map to a customer conversation.** If we can't explain why a mid-market executive (CFO, COO, VP Ops, or FP&A team) cares, it doesn't get prioritised.
2. **Multi-agent orchestration AND data connectivity are infrastructure, not differentiators.** All platform/technical work is in service of agent capability delivery. Vendor semantic layers (Snowflake Cortex Analyst, Databricks Genie, SAP Datasphere) commoditize the connectivity layer; Agent9 adapts to them via the Tier 1/2/3 connectivity model. The moat is the SA→DA→MA→SF→VA pipeline + Registry + VA outcome corpus.
3. **The consulting firm partner model shapes Phase 3 sequencing.** Agents that enable the delivery lifecycle (change management, stakeholder engagement) are prerequisites for partner conversations.
4. **5-day onboarding is a product capability, not just a process.** KPI Assistant Agent completion and template library expansion directly enable it.

---

## Current State (May 2026) — Built and Functional

### Core Agent Platform (14 operational agents)
- ✅ A9_Orchestrator_Agent — workflow coordination, agent lifecycle, dependency resolution (7 workflow methods, singleton registry)
- ✅ A9_Situation_Awareness_Agent — client-scoped enterprise KPI monitoring, anomaly + opportunity detection, NL query, per-KPI monitoring profiles (Phase 9A), single-KPI assessment mode
- ✅ A9_Deep_Analysis_Agent — SCQA root cause analysis, KT Is/Is-Not decomposition, change-point detection, benchmark segments (replication candidates), BigQuery routing
- ✅ A9_Solution_Finder_Agent — multi-perspective debate (3×Stage1 parallel Haiku + Sonnet synthesis), trade-off matrix, fast/full debate modes, MA enrichment, HITL approval
- ✅ A9_Principal_Context_Agent — 8 principal profiles, dual lookup, business process mapping, role-based personalisation
- ✅ A9_Data_Governance_Agent — data access policies, business term translation, audit logging
- ✅ A9_Data_Product_Agent — schema inspection (DuckDB / BigQuery / Postgres / Snowflake / SQL Server), contract YAML, SQL execution
- ✅ A9_LLM_Service_Agent — centralised LLM routing (Anthropic Claude — Haiku for Stage 1, Sonnet for synthesis; GPT-4 deprecated Mar 2026), model selection, token tracking, guardrails
- ✅ A9_NLP_Interface_Agent — deterministic regex parsing (TopN, timeframe, grouping extraction); no LLM
- ✅ A9_Market_Analysis_Agent — real-time market intelligence via Perplexity + Claude synthesis (LLM-only fallback)
- ✅ A9_Value_Assurance_Agent — solution registration, 5-phase lifecycle (Approved → Implementing → Live → Measuring → Complete), three-trajectory tracking (inaction/expected/actual), DiD attribution, composite verdict, Supabase persistence
- ✅ A9_PIB_Agent — briefing composition, Jinja2 email rendering, SMTP delivery, single-use briefing tokens, delegation flow
- 🔄 A9_KPI_Assistant_Agent — API-only (4 endpoints under `/api/v1/data-product-onboarding/kpi-assistant/`); React UI panel pending
- ⛔ A9_Data_Product_MCP_Service_Agent — **DEPRECATED** (remove after 2025-11-30); direct SDK connectors replaced it
- ⛔ A9_Risk_Analysis_Agent — **DEAD CODE**, no tests, no registration; PRD exists; rewrite slated for Phase 12

### Platform Infrastructure (May 2026)
- ✅ Decision Studio UI (React/Vite/Tailwind, Swiss Style brand identity — Phase 10A)
- ✅ Registry Explorer (KPIs, principals, business processes, data products, glossary) — form-based editing
- ✅ **Multi-warehouse direct SDK connectors (Phase 10C)** — DuckDB (local), BigQuery, Snowflake, Databricks, SQL Server (dev only; production gated on Dockerfile ODBC driver). Tier 1 in the connectivity model.
- ✅ Supabase-backed registries (sole backend; no YAML fallbacks) — 6 registries with `client_id` multi-tenant isolation
- ✅ Audit trail and HITL checkpoints
- ✅ Principal-driven analysis (decision style → consulting persona framing)
- ✅ Value Assurance Portfolio Dashboard (phase-aware TrajectoryChart, KPI-aware Portfolio formatting, phase transition buttons)
- ✅ Cost of Inaction Banner in Executive Briefing
- ✅ Opportunity Detection (positive KPI, benchmark segments, replication targets, green KPI tiles)
- ✅ HITL Approve & Track workflow with VA solution registration
- ✅ **PIB email delivery (Phase 10B)** — Jinja2 templates, SMTP via Gmail App Password, Swiss Style monochrome design, single-use tokens, delegation flow with audit trail
- ✅ **White-paper report (Apr 2026)** — standalone Gartner-style document at `/report/:situationId`, print + PDF, Draft/Approved badges
- ✅ **Production deployment (Apr 2026)** — Railway backend, Cloudflare Pages frontend (replaced Vercel), Supabase Cloud database, GCP credentials for BigQuery materialized at startup; every push to `master` triggers auto-deploy
- ✅ Supabase persistence for situations, opportunities, VA solutions, VA evaluations, assessment runs

### Known Issues to Resolve Before First Pilot
- ⚠️ **Registry live-reload (Infra A4 — CRITICAL):** SA/PCA/DPA cache registry at startup; new client requires Railway restart. Fix slated May–Jun 2026.
- ⚠️ **SQL Server production enablement (Infra A4):** Railway `python:3.11-slim` lacks Microsoft ODBC Driver 18; works in dev only. Fix: add ODBC driver to Dockerfile + stand up Azure SQL for hess demo data.
- ⚠️ **Multi-tenant auth (Infra B — pre-pilot BLOCKER):** Supabase Auth + per-customer isolation required before first signed pilot (target Aug 2026).
- ⚠️ A9_KPI_Assistant_Agent UI — API exists; React panel pending (Phase 11D).
- 🟢 Resolved: hardcoded `C:\Users\barry\` paths, business process field name mismatch (fixed Apr–May 2026)

---

## Phase 0 — Demo Ready (Mar–Apr 2026) ✅ COMPLETE
*Original goal: Stable pipeline + external intelligence layer + opportunity detection. Achieved.*

### ✅ Shipped (Mar–Apr 2026)
- ✅ SA → DA → SF pipeline stable and production-quality
- ✅ Executive Decision Briefing: 19-page output with firm proposals, cross-review, options, roadmap, risk
- ✅ Multi-call SF architecture (stage1_only → hypothesis → cross_review → synthesis)
- ✅ MA Agent shipped (Pydantic models, Perplexity + Claude synthesis, wired into SF pipeline)
- ✅ Positive KPI opportunity detection in SA; green opportunity card in Decision Studio UI
- ✅ Value Assurance data model + full UI (AcceptedSolution model, Portfolio Dashboard, trajectory chart, CostOfInaction Banner)
- ✅ HITL Approve & Track workflow with VA solution registration

---

## Phase 10A–10D — Production Shipping (Apr–May 2026) ✅ COMPLETE
*Goal: Production-quality demo with brand identity, email delivery, multi-warehouse access, performance tuning. Achieved.*

### Phase 10A — Swiss Style Brand Refresh ✅ Apr 2026
- BrandLogo aperture component shared across Login, DelegatePage, ActionHandler, ExecutiveBriefing, Portfolio
- Satoshi font global; semantic color tokens; monochrome base
- KPI tile visual refresh (deep slate card, 1px severity border, factual summary copy)
- DivergingBarChart for variance/delta
- DA Is/Is Not McKinsey-exhibit treatment
- TrajectoryChart dark background; CouncilDebate terminal log aesthetic
- Dead code removed (VarianceDrawer, RidgelineScanner, SnowflakeScanner)

### Phase 10B — PIB Email Template Refresh ✅ Apr 2026
- Swiss Style monochrome email template
- Section hierarchy: New Situations → Urgency → Solutions → Managed
- Top 3 IS driver rows per situation block; measured CTA copy
- Mobile-safe layout tested on Gmail
- Flash Briefing text block structured for future TTS delivery

### Phase 10C — Multi-Warehouse Direct SDK Connectors ✅ May 2026
- DuckDB / BigQuery / Snowflake / Databricks / SQL Server (dev) operational
- SA scan verified end-to-end against all four production-target backends
- DPA + SA agent route via `_resolve_source_system()` (Tier 1 routing via `data_product_id` registry lookup)
- Connection config resolution: data product metadata → env vars → defaults
- Production gap (SQL Server): ODBC Driver 18 not in Railway `python:3.11-slim` Docker image — Infra A4 fix tracked

### Phase 10D — Solution Finder Performance Tuning ✅ Apr 2026
- Fast debate mode (`VITE_DEBATE_MODE`): dev 2 calls (stage1_only + synthesis), production 4 calls
- DA context trimming (~8–12K token reduction when Stage 1 hypotheses exist)
- Result: dev latency reduced from ~9 min to ~3 min per debate (3× speedup)
- Model routing preserved: Stage 1 → Haiku, Synthesis → Sonnet

### Additional shipped Apr 2026
- ✅ VA 5-phase lifecycle (Approved → Implementing → Live → Measuring → Complete) with phase-aware TrajectoryChart and KPI-aware Portfolio formatting
- ✅ White-paper report (Gartner-style cold-eyes document at `/report/:situationId`)
- ✅ Production deployment (Railway + Cloudflare Pages + Supabase Cloud)

---

## Phase 1 — Pre-Pilot Hardening + Outreach (May 2026 → Sep 2026)
*Goal: Production-grade multi-tenant deployment + first signed pilot. Tracked in DEVELOPMENT_PLAN.md as Infra A4 + Infra B.*

### Infrastructure (May–Aug 2026 — pre-pilot blockers)
- [ ] **Infra A4: Registry live-reload** — SA, PCA, DPA agents query Supabase per request (drop instance-level caches); admin reload endpoint as stopgap
- [ ] **Infra A4: SQL Server production enablement** — Microsoft ODBC Driver 18 in Dockerfile + Azure SQL for hess demo data
- [ ] **Infra A2: Platform Admin & Client Onboarding UI** — composes Company Profile + Data Product Onboarding wizards into guided 4-step flow; replaces seed-script dependency
- [ ] **Infra A3: Usage monitoring** — `usage_events` table, monthly rollup view, admin dashboard, client-facing widget
- [ ] **Infra B: Supabase Auth** — email + password, API keys
- [ ] **Infra B: Multi-tenant isolation** — per-customer Supabase project OR strict RLS with `client_id` enforcement
- [ ] **Phase 10B-DGA: DGA mandatory wiring** — eliminate 16 governance fallback paths; new connectors inherit governance automatically

### Outreach (May–Sep 2026)
- [ ] Record 5-minute demo video (lubricants end-to-end through VA Portfolio + white-paper report)
- [ ] Launch landing page (trydecisionstudio.com)
- [ ] Identify first 20 warm contacts (never-engaged mid-market CFOs, VP FP&A)
- [ ] Schedule first 10 discovery calls
- [ ] Send first pilot proposals at $18K–$30K (Fast Start tier)
- [ ] Close first pilot customer (target: Sep 2026)

### Agent Builds (deferred to Phase 2)

**A9_Stakeholder_Analysis_Agent** *(Medium priority — build in Phase 2)*
- **Why Phase 1:** When pilots produce their first solution recommendations, the executive's next question is "who do I need to get on board?" This agent answers that.
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
PHASE 0 (Mar–Apr 2026) ✅ COMPLETE
  Market Analysis ────────────────────────────── ✅ SHIPPED Mar 2026
  Positive KPI detection ─────────────────────── ✅ SHIPPED Mar 2026
  Value Assurance data model + full UI ──────── ✅ SHIPPED Mar 2026

PHASE 10A–10D (Apr–May 2026) ✅ COMPLETE
  Swiss Style brand identity ─────────────────── ✅ SHIPPED Apr 2026
  PIB email delivery + tokens + delegation ───── ✅ SHIPPED Apr 2026
  VA 5-phase lifecycle + white-paper report ──── ✅ SHIPPED Apr 2026
  Production deployment (Railway+CF+Supabase) ── ✅ SHIPPED Apr 2026
  Multi-warehouse SDK connectors (Tier 1) ────── ✅ SHIPPED May 2026 (Snowflake, Databricks, SQL Server dev)
  SF performance tuning (fast/full modes) ────── ✅ SHIPPED Apr 2026
  SA→DA→MA→SF→VA pipeline sequencing ─────────── ✅ SHIPPED (MA between DA and SF for framing + SF enrichment)

PHASE 1 (May–Sep 2026 — Pre-Pilot Hardening + Outreach)
  Phase 10B-DGA: Mandatory DGA wiring ─────────── 📋 Next
  Infra A4: Registry live-reload ──────────────── 📋 Next
  Infra A4: SQL Server production ─────────────── 📋 Pending
  Infra A2: Platform Admin Onboarding UI ──────── 📋 Pending
  Infra B: Auth + multi-tenant isolation ──────── 📋 BLOCKER for first pilot
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

## Milestone Summary (Rebased May 2026)

| Milestone | Target Date | Status |
|-----------|-------------|--------|
| Executive Decision Briefing stable (SA→DA→SF) | Mar 2026 | ✅ Complete |
| 5-pillar value proposition + updated strategy docs | Mar 2026 | ✅ Complete |
| MA Agent built + wired into SF pipeline | Mar 2026 | ✅ Complete |
| Positive KPI opportunity detection (SA+DA) | Mar 2026 | ✅ Complete |
| Value Assurance full UI (trajectory chart, portfolio, CostOfInaction) | Mar 2026 | ✅ Complete |
| Enterprise Assessment Pipeline (Phase 9A-C) | Apr 2026 | ✅ Complete |
| Phase 10A: Swiss Style brand identity | Apr 2026 | ✅ Complete |
| Phase 10B: PIB email delivery + single-use tokens + delegation flow | Apr 2026 | ✅ Complete |
| Phase 10D: SF performance tuning (3× speedup) | Apr 2026 | ✅ Complete |
| VA 5-phase lifecycle (Approved→Implementing→Live→Measuring→Complete) | Apr 2026 | ✅ Complete |
| White-paper report (Gartner-style) | Apr 2026 | ✅ Complete |
| Production deployment live (Railway + Cloudflare Pages + Supabase Cloud) | Apr 2026 | ✅ Complete |
| Phase 10C: Multi-warehouse direct SDK connectors (DuckDB, BigQuery, Snowflake, Databricks, SQL Server dev) | May 2026 | ✅ Complete |
| Demo video recorded (lubricants end-to-end) | Q2 2026 | 🔄 In progress |
| Landing page live (trydecisionstudio.com) | Q2 2026 | 🔄 In progress |
| BP field name fixes + KPI Assistant LLM complete | May 2026 | 🔄 Partial — KPI Assistant API done, UI pending |
| Phase 10B-DGA: Mandatory DGA wiring (eliminate 16 fallback paths) | Jun 2026 | 📋 Next |
| Infra A4: Registry live-reload (SA/PCA/DPA per-request Supabase reads) | Jun 2026 | 📋 Next |
| Infra A4: SQL Server production enablement (ODBC + Azure SQL) | Jul 2026 | 📋 Pending |
| Infra A2: Platform Admin + Client Onboarding UI | Jul 2026 | 📋 Pending |
| Infra A3: Usage monitoring (events, quotas, alerts) | Aug 2026 | 📋 Pending |
| Infra B: Supabase Auth + multi-tenant isolation (pre-pilot BLOCKER) | Aug 2026 | 📋 Pending |
| First 20 warm contacts identified | May–Jun 2026 | 📋 Pending |
| First 10 discovery calls | Jun–Jul 2026 | 📋 Pending |
| First pilot signed | Sep 2026 | 📋 Pending |
| Stakeholder Analysis + Engagement built | Oct 2026 | 📋 Pending |
| 5-day onboarding template v1 (SAP) | Oct 2026 | 📋 Pending |
| First case study documented | Jan 2027 | 📋 Pending |
| Change Management Agent built | Apr 2027 | 📋 Pending |
| Implementation Tracker + Risk Management built | Jun 2027 | 📋 Pending |
| Quit day job decision point (2+ paying customers + runway) | Apr 2027 | 📋 Pending |
| Hire #1 (Sales/CS) | Jun 2027 | 📋 Pending |
| Opportunity Analysis Agent built | Aug 2027 | 📋 Pending |
| 5 customers / $250K+ ARR | Dec 2027 | 📋 Pending |
| SOC 2 readiness | H1 2028 | 📋 Pending |
| First consulting firm partner pilot (mid-tier — FTI, A&M, Huron) | H2 2028 | 📋 Pending |
| Performance + Business Optimization built | H2 2028 | 📋 Pending |
| 10+ customers / $800K+ ARR | Jan 2029 | 📋 Pending |

---

*This roadmap supersedes the previous version (roadmap.md v1.0, Jun 2025). Previous version focused on technical infrastructure phases. This version sequences by business value delivery and consulting partner model enablement.*
