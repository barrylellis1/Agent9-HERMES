# Agent9: 5-Day Onboarding as a Strategic Moat

**Last Updated:** February 2026
**Status:** Methodology designed; KPI Assistant Agent partially built (LLM integration pending)

---

## Why Onboarding Speed Is a Moat, Not Just a Process

Most AI analytics and BI tools promise fast deployment and deliver 8-12 weeks of professional services before a single insight lands. This gap between the promise and the delivery is where deals die, skepticism compounds, and the budget holder starts calling the competitor.

Agent9's **5-Day Fast Start** is designed to close that gap with a documented, repeatable, template-driven process that gets a customer to their first situation card in a week. The speed is not marketing — it is the product.

**Why this compounds over time:**

1. **Template library becomes IP.** Each new ERP onboarding generates a reusable template. The 10th SAP customer takes 3 days instead of 5. The library itself is a barrier competitors can't easily replicate without the same volume of deployments.
2. **Speed sets expectations.** A customer who has their first situation card in 5 days trusts the platform before they've had a chance to build doubt. The first success anchors the relationship.
3. **Operational embedding starts at Day 1.** The moment data flows into Agent9 registries, switching costs begin accumulating. Data product contracts, KPI calibrations, principal profiles — these take time to rebuild elsewhere.
4. **Partners want it too.** Consulting firms who eventually partner with Agent9 need to be able to tell their clients: "We'll have this running in your environment in a week." That capability is a precondition for the partner model.

---

## The 5-Day Process

### Prerequisites (Before Day 1)

**Pre-Onboarding Data Readiness Checklist** — sent to customer 1-2 weeks before start:

| Item | Required | Notes |
|------|----------|-------|
| Data source access credentials | ✅ Yes | Read-only service account sufficient |
| List of top 5-10 KPIs customer wants monitored | ✅ Yes | Names, definitions, calculation logic |
| Historical data range available | ✅ Yes | Minimum 12 months; 24 months preferred |
| ERP/warehouse schema documentation | ⚠️ Preferred | Agent9 can infer but docs speed Day 1 significantly |
| List of 3-5 principal users (with roles) | ✅ Yes | CFO, Finance Manager, etc. |
| Sample "bad month" situation to validate | 💡 Helpful | An anomaly the team already understands |
| IT point of contact for data access | ✅ Yes | For Day 1 connectivity |

**Internal Agent9 Gate:** If checklist is less than 80% complete, delay start date. Do not attempt onboarding without KPI definitions and data access confirmed.

---

### Day 1 — Connect and Map

**Goal:** Data flowing. Schema understood. KPI list confirmed.

| Task | Owner | Time |
|------|-------|------|
| Connect to data source (ERP, warehouse, flat file) | Agent9 engineer | 2 hrs |
| Run schema discovery against relevant tables | Agent9 (automated) | 30 min |
| Map customer KPI list to discovered fields | Agent9 engineer + customer FP&A | 2 hrs |
| Identify gaps (KPIs that can't be calculated from available data) | Joint | 1 hr |
| Confirm primary domain and business process scope | Agent9 | 30 min |
| **Day 1 output:** Data product contract draft v1 | | |

**Template library role:** ERP-specific schema maps (SAP CoA layouts, Oracle NetSuite table structures, Snowflake star schema patterns) pre-populated with common KPI field mappings. Day 1 is significantly faster when the template already knows where to find Gross Revenue in SAP.

---

### Day 2 — KPI Configuration

**Goal:** KPI registry populated. Thresholds calibrated. Principal profiles configured.

| Task | Owner | Time |
|------|-------|------|
| Populate KPI registry (definitions, formulas, thresholds) | Agent9 engineer | 3 hrs |
| KPI Assistant Agent draft review (where LLM integration is live) | Automated | 30 min |
| Customer review and approval of KPI definitions | Customer FP&A | 1 hr |
| Configure principal profiles (decision style, alert preferences) | Agent9 + customer | 1 hr |
| Set baseline values from historical data | Agent9 (automated) | 1 hr |
| **Day 2 output:** KPI registry v1 + principal profiles configured | | |

**KPI Assistant Agent role:** When fully integrated, the KPI Assistant Agent uses LLM to draft KPI definitions, strategic context, and threshold suggestions from minimal input. The customer approves rather than builds from scratch. This is the automation layer that makes Day 2 repeatable without a senior agent engineer on site.

---

### Day 3 — First Situation Card

**Goal:** Situation Awareness running. First real anomaly detected and presented.

| Task | Owner | Time |
|------|-------|------|
| Run Situation Awareness Agent against historical data | Agent9 (automated) | 2 hrs |
| Review initial situation cards generated | Agent9 engineer | 1 hr |
| Select 1-2 situations for customer walk-through | Agent9 | 30 min |
| Customer reviews first situation card with Agent9 | Joint | 1 hr |
| Calibrate severity scoring against customer's intuition | Joint | 1 hr |
| **Day 3 output:** First validated situation card in customer's hands | | |

**The "aha moment" is Day 3.** The moment a customer sees their own data surfaced as a structured situation — with severity, KPI context, and anomaly explanation — they shift from skeptical to engaged. This is when the budget conversation changes from "is this worth it" to "how do we expand this."

---

### Day 4 — Deep Analysis and Solution Finder Validation

**Goal:** Full workflow tested end-to-end. Customer understands the analysis depth.

| Task | Owner | Time |
|------|-------|------|
| Run Deep Analysis on Day 3 situation | Agent9 (automated) | 1 hr |
| Customer review of root cause analysis (SCQA framing) | Joint | 1 hr |
| Run Solution Finder | Agent9 (automated) | 1 hr |
| Customer review of solution options and trade-off matrix | Joint | 1 hr |
| Review audit trail and decision log | Customer FP&A | 30 min |
| Identify 1-2 additional situations for ongoing monitoring | Customer | 1 hr |
| **Day 4 output:** Full workflow demonstrated; customer approves 2-3 ongoing monitoring situations | | |

---

### Day 5 — Handover and Monitoring Start

**Goal:** Customer team operational. Monitoring running. Success criteria confirmed.

| Task | Owner | Time |
|------|-------|------|
| Customer training: how to review situation cards | Agent9 | 1 hr |
| Configure ongoing alert delivery (frequency, channel) | Joint | 30 min |
| Document known gaps and next data source additions | Joint | 1 hr |
| Confirm pilot success criteria with customer | Joint | 30 min |
| Handover package: registry exports, data product contracts, principal configs | Agent9 | 1 hr |
| **Day 5 output:** Customer self-sufficient for ongoing use; monitoring live | | |

---

## Template Library Strategy

### ERP-Specific Templates (Priority Order)

Each template covers: schema map, common KPI field mappings, known data quality issues, suggested threshold starting points, and example situation types.

| Template | Status | Priority |
|----------|--------|----------|
| **SAP S/4HANA / ECC** | In development (fi_star_schema.yaml work exists) | P0 — Build first |
| **Oracle NetSuite** | Not started | P1 — Phase 1 |
| **Snowflake + dbt** | Not started | P2 — Phase 2 |
| **Microsoft Dynamics 365** | Not started | P3 |
| **Sage Intacct** | Not started | P3 |
| **QuickBooks (mid-market)** | Not started | P3 |

### What Goes in a Template

```
templates/
└── sap_s4hana/
    ├── schema_map.yaml          # Table/field → Data product mapping
    ├── kpi_defaults.yaml        # Pre-built KPI definitions for common metrics
    ├── threshold_starters.yaml  # Statistical starting thresholds by KPI type
    ├── principal_defaults.yaml  # Typical CFO/FP&A profile configs for SAP customers
    ├── known_issues.md          # Common data quality issues in this ERP
    └── situation_examples.yaml  # Example situations this template has historically surfaced
```

### Template Compound Effect

| Customer Count | SAP Template Maturity | Day 1 Time Estimate |
|---------------|----------------------|---------------------|
| 1 (pilot) | Baseline | 4-5 hours |
| 3 | Schema map validated | 2-3 hours |
| 5 | KPI defaults validated | 1-2 hours |
| 10+ | Self-service with AI assist | < 1 hour |

After 10 SAP customers, the onboarding for that stack approaches full automation. The template library is the mechanism that turns 5-day Fast Start into 2-day Fast Start over time.

---

## KPI Assistant Agent: The Automation Layer

The KPI Assistant Agent is the internal tool that makes Fast Start repeatable without senior engineering involvement on every deal.

**Current state:** Partially built. LLM integration (4 TODOs) and SQL validation pending.

**What it does when complete:**

1. **KPI Definition Draft:** Given a KPI name and the data schema, generates a structured KPI definition including formula, description, strategic context, and threshold suggestions
2. **SQL Contract Generation:** Generates validated SQL for the data product contract against the connected schema
3. **Gap Analysis:** Flags KPIs where the data schema doesn't support calculation and suggests alternatives
4. **Registry Population:** Auto-populates kpi_registry.yaml entries for customer review and approval

**Fast Start without KPI Assistant Agent (current):** Requires 3 hours of engineer time on Day 2
**Fast Start with KPI Assistant Agent (target):** 45 minutes of customer review time; engineer supervises

**Priority:** KPI Assistant Agent LLM integration should be completed before the first paying pilot. It is a prerequisite for the Fast Start process to be deliverable without unsustainable engineer-hours per onboarding.

---

## Pricing Rationale

**Fast Start: $10,000–$15,000 (one-time)**

This pricing reflects:
- Speed and certainty of delivery (5 days, not 8 weeks)
- Template-based efficiency (not billed hourly)
- Strategic value of the first situation card (opens the relationship)
- Market comparison: competitors charge $50K–$150K for equivalent setup

The Fast Start is **not meant to be a profit center.** It should cover costs and signal professionalism. The value is in pulling forward the platform subscription and keeping the customer engaged before doubt accumulates.

**Additional data source: $5,000–$10,000 (per source)**
- Each additional ERP or warehouse beyond the initial onboarding
- Priced to be a straightforward expansion decision, not a renegotiation
- As template library matures, cost-to-serve drops while price stays stable

---

## Switching Cost Mechanics

The Fast Start process creates switching costs that compound over the life of the customer relationship:

| What Gets Built | What It Costs to Rebuild Elsewhere |
|-----------------|-----------------------------------|
| Data product contracts (per source) | 2-4 weeks per source + engineer time |
| KPI registry (calibrated to their data) | Full redefinition cycle |
| Principal profiles (decision style, alert preferences) | Cultural knowledge loss |
| Threshold calibrations (tuned over months) | Starts from scratch |
| Historical situation corpus (all prior anomalies) | Cannot be exported to competitor |
| Decision audit trail | Platform-specific, cannot migrate |

After 6 months of active use, the decision corpus and threshold calibrations are effectively irreplaceable. No competitor can offer to "import" them — the customer would need to restart from zero.

---

## Pre-Onboarding Data Readiness Assessment

Offered free to prospects who are close to signing. Serves two purposes:
1. Surfaces data quality issues before Day 1 (prevents failed onboardings)
2. Creates urgency — "your data is ready, here's exactly what we'd build in week one"

**Assessment covers:**
- Data source connectivity (can we connect?)
- Schema completeness (do the tables we need exist?)
- Data quality spot-check (are the key fields populated and consistent?)
- KPI calculability (can we calculate your top 5 KPIs from what's available?)
- Historical depth (how many months of data do we have to baseline from?)

**Delivery:** 2-3 hour automated scan + 1-page readiness report

**Sales motion:** Close assessment → confirm ready → book Fast Start date → contract

---

## Connection to Product Roadmap

| Phase | Onboarding Moat Action |
|-------|----------------------|
| Phase 0 (Now) | Complete KPI Assistant Agent LLM integration (4 TODOs); finalize SAP template v1 |
| Phase 1 (Pilot) | Validate Fast Start process with first 2 pilots; document lessons learned |
| Phase 1 (Growth) | Build Oracle NetSuite template; add pre-onboarding data readiness assessment tool |
| Phase 2 | Build Snowflake + dbt template; automate template selection based on data source type |
| Phase 3 | Self-service Fast Start portal — customers initiate and complete with minimal Agent9 involvement |

---

*"The moat is not the speed alone. The moat is that the template library gets better with every customer, and the switching costs accumulate from Day 1."*

---

*Confidential | February 2026*
