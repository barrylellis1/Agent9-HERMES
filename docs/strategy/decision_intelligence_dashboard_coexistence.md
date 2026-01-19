# Decision Intelligence Strategy: Coexisting with Existing Dashboards

**Last updated:** January 19, 2026  
**Author:** Agent9 Architecture Team

## 1. Objective
Deliver Agent9 decision intelligence in environments where customers already have deeply adopted dashboards (e.g., SAP Analytics Cloud backed by Datasphere/Business Data Cloud) without requiring dashboard replacement. Agent9 becomes the narrative, diagnostic, and orchestration layer sitting beside existing BI investments.

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

## 7. Implementation Roadmap
| Phase | Milestone | Notes |
|-------|-----------|-------|
| P0 | Datasphere ↔ Agent9 connectivity | Register key views as data products, validate SQL access |
| P1 | SAC card embedding (web widget) | Stand up secure card endpoint, pass filters via script |
| P2 | KPI reconciliation automation | Implement nightly diff + alerting |
| P3 | Custom SAC widget / Analytic App | Full SDK integration, theming, interaction callbacks |
| P4 | GTM collateral | Customer demo script, architecture diagram, pricing positioning |

## 8. Next Actions
1. **Product**: Build insight card endpoint with SAC-compatible auth + theming.  
2. **Data**: Create Supabase entries mapping Datasphere views → SAC stories → KPIs.  
3. **Architecture**: Document cache invalidation + refresh orchestration runbook.  
4. **Sales Enablement**: Slide appendix highlighting “Decision Intelligence layer for existing dashboards.”  
5. **Pilot**: Identify a reference customer running SAC over Datasphere to showcase embedded cards.
