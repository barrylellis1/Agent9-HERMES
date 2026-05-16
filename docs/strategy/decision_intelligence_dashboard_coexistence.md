# Decision Intelligence Strategy: Coexisting with Existing Dashboards

**Last updated:** May 2026
**Version:** 1.1 — SAP bridge moved to Phase 4 (H2 2028); Phase 10C connectivity context added; vendor semantic layer framing applied
**Status:** Strategic framework for Year 2+ partner conversations. SAP-specific bridge work (embedded SAC cards, Datasphere connector) is deferred to Phase 4 (H2 2028) per the roadmap. Decision Studio works alongside any BI tool today via the standalone Decision Studio UI + PIB email + white-paper report.

## 1. Objective
Deliver Decision Studio decision intelligence in environments where customers already have deeply adopted dashboards (e.g., SAP Analytics Cloud backed by Datasphere/Business Data Cloud; Tableau; Power BI; Looker) without requiring dashboard replacement. Decision Studio becomes the narrative, diagnostic, and orchestration layer sitting beside existing BI investments.

## 2. Positioning Narrative
1. **Dashboards show *what* happened; Agent9 explains *why* it matters and *what to do*.**  
2. **Agent9 layers registry intelligence** (principals, KPIs, processes, data products, glossary) on top of KPI tiles to create context-aware insights.  
3. **Agents orchestrate follow-up actions** (diagnostics, escalation, recommended playbooks) that dashboards cannot automate.  
4. **We integrate with — not replace — BI.** Insight cards embed directly inside SAC stories/analytic apps, maintaining user workflows.

## 3. Architecture Overview
```
Datasphere / SAP BTP (Shared Data Plane)
        ↓ (Live models)
SAP Analytics Cloud (Visualization Layer) ←→ Agent9 Insight Cards (Embedded)
        ↓                                    ↓
Decision Studio UI / Situation Awareness Agent / Data Product Agent
        ↓
Supabase Registry Metadata + YAML Contracts (Hybrid registry)
```
- Agent9 executes SQL against the same Datasphere views powering SAC to avoid drift.  
- Supabase registry tracks lineage, owners, refresh cadence for every data product referenced by SAC widgets.  
- Insight cards rendered in SAC reference the data product ID, version, and refresh timestamp for transparency.

## 4. Integration Patterns
### 4.1 Embedded Insight Cards
- **Delivery**: SAC Web Page widget or custom widget loads Agent9 card (React component).  
- **Context bridge**: SAC scripting API sends current story filter/KPI ID to Agent9 via query params or postMessage.  
- **Return payload**: Summary, anomaly explanation, confidence, recommended actions, escalation links.

### 4.2 Datasphere Alignment
- **Single source of truth**: Datasphere semantic layer (spaces/views) registered as Agent9 data products.  
- **Security**: Agent9 uses Datasphere service credentials mirroring SAC roles.  
- **Refresh orchestration**: Datasphere refresh → SAC live dataset → Agent9 cache invalidation event.

### 4.3 KPI / Metric Sync
- SAC widget value hash or timestamp passed into Agent9 request.  
- Agent9 recomputes value using same parameters; if mismatch > tolerance, card returns "Data out of sync" warning.

## 5. Guardrails & Governance
1. **Version tagging** – Every card displays `data_product_id`, version, last refreshed.  
2. **Cache SLA** – Agent9 caches invalidated immediately after Datasphere refresh signal.  
3. **Discrepancy detection** – Nightly job compares SAC exports vs Agent9 outputs; flags anomalies.  
4. **Audit trail** – Supabase logs which agent/card accessed which data product for traceability.  
5. **Fallback plan** – If Agent9 service unavailable, SAC card shows graceful message and link to Decision Studio.

## 6. GTM Messaging Pillars
1. **"Keep your dashboards, upgrade your decisions."**  
2. **"Agent9 is the executive copilot that watches KPIs for you."**  
3. **"Insight cards explain anomalies and recommend actions right where leaders already look."**  
4. **"Built on your Datasphere/SAC foundation, using your governance and security."**

## 7. Implementation Roadmap (Revised May 2026)

SAP-specific bridge work has been deferred to Phase 4 (H2 2028) per the product roadmap. The general "coexist with dashboards" capability is already delivered through three mechanisms today:

1. **PIB email delivery (Phase 10B, shipped Apr 2026)** — situations and recommendations land in the executive's inbox with single-use briefing tokens, delegation flow, and audit trail. No dashboard embedding required.
2. **White-paper report (Apr 2026)** — Gartner-style narrative document delivered as standalone HTML/PDF, can be shared via any channel.
3. **Decision Studio UI** — production-deployed; principals visit the URL directly when they want to investigate. No dashboard replacement, just an additional surface.

| Phase | Milestone | Timeline | Status |
|-------|-----------|----------|--------|
| **Phase 10C** | Direct SDK connectors (Tier 1) for DuckDB, BigQuery, Snowflake, Databricks, SQL Server | May 2026 | ✅ Complete — covers most "modern data stack" customers |
| **Phase 10D** | Vendor MCP routing (Tier 2) — Snowflake Cortex MCP, Databricks MCP, Postgres MCP | H2 2026 (vendor MCP maturity gated) | 📋 Pending |
| **Phase 11F** | Vendor AI Agent routing (Tier 3) — DGA routes ad-hoc NL follow-up to Cortex Analyst / Genie / SAP Joule | H2 2026–H1 2027 | 📋 Pending |
| **Phase 4 — SAP Bridge** | SAP Datasphere data product registration, SAC card embedding, KPI reconciliation automation | H2 2028 | 📋 Deferred — opens with SAP-native customer signed |
| **Phase 4 — SAC Custom Widget** | SAC SDK integration, theming, interaction callbacks | H2 2028 | 📋 Deferred — gated on SAP-native customer demand |

## 8. Strategic Context (May 2026)

The Apr 2026 strategic moat refresh shifts how this coexistence is framed:

- **Decision Studio does NOT need to embed in every dashboard.** The moat is the SA→DA→MA→SF→VA pipeline running above whatever data the customer has. Dashboards are display layers; Decision Studio is the analytical loop.
- **Vendor semantic layers handle "what happened" questions natively.** Snowflake Cortex Analyst, Databricks Genie, Microsoft Fabric Copilot — all production-ready. Customers ask these tools about their data. Decision Studio runs the decision pipeline on top.
- **SAP-specific embedding is a partner play, not a Year 1 product.** When a SAP-native pilot customer signs in 2027–2028, the SAC card embedding work becomes economically justified. Until then, Decision Studio's standalone UI + PIB email + white-paper report cover the coexistence need.

## 9. Next Actions (Active, May 2026)
1. **Outreach:** Lead with Decision Studio's standalone deployment proof point — production URL, real Lubricants data, live trajectory tracking. "We coexist with your BI" is true today; SAP-specific embedding is a Year 3 partner story.
2. **Architecture (deferred):** SAC bridge spec stays in Phase 4. Revisit when first SAP-native pilot is signed or partner conversation requires it.
3. **Sales Enablement:** Update slide appendix to say "Decision Studio coexists with any BI tool. Direct embedding (SAC, Tableau, Power BI) available as a Year 3 partner extension."
