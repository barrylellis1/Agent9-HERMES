# Data Connectivity Strategy: Where Intelligence Lives

**Date:** 2026-04-14  
**Status:** Strategic direction — shapes all Phase 10D+ decisions  
**Context:** Vendor platforms (Snowflake Cortex Analyst, Databricks Genie) are commoditizing the semantic layer and NL-to-SQL capabilities that Agent9 originally built as enablers. This document defines where Agent9's investment should go.

---

## The Insight

When Agent9 began (mid-2025), the Data Product Agent and NLP Interface Agent were necessary enablers — the only way to bridge raw data warehouses and business intelligence. By 2026, every major vendor is shipping their own:

| Vendor Capability | Snowflake | Databricks |
|-------------------|-----------|------------|
| Semantic model (business terms, metrics, joins) | Cortex Analyst Semantic Views (YAML) | Genie Spaces (annotated tables + synonyms) |
| NL-to-SQL | Cortex Analyst | Genie |
| Schema discovery | INFORMATION_SCHEMA + MCP | Unity Catalog + MCP |
| Governed data access | RBAC + row/column security | Unity Catalog ACLs |
| Agentic orchestration | Cortex Agents | Managed MCP + AI Functions |

These vendors will do data connectivity better than Agent9 ever will — it's their core business.

---

## Agent9's Moat

What no vendor offers, and what no vendor is building:

```
SA: "Your revenue in North region dropped 12% — this is a breach of your 5% threshold"
DA: "The root cause is concentrated in Product Category X, starting Week 23, not present in South region"
SF: "Three strategic options: (1) pricing adjustment, (2) promotional campaign, (3) channel shift — 
     here are the trade-offs, quantified impact, and implementation timelines"
VA: "The pricing adjustment you approved 6 weeks ago has recovered 8% of the 12% gap, 
     with statistical confidence via Difference-in-Differences attribution"
PIB: "Here's your Monday morning briefing with the 3 situations that need your attention"
```

This is the product. The SA→DA→SF→VA pipeline is unique. Everything below it — connecting to databases, discovering schemas, translating natural language to SQL — is plumbing.

---

## Architectural Model

### Two Layers

```
┌─────────────────────────────────────────────────────┐
│  MOAT LAYER — Agent9 Analytical Pipeline            │
│                                                     │
│  SA → DA → SF → VA → PIB                           │
│  KPI monitoring, root-cause analysis, solutions,    │
│  value tracking, executive briefings                │
│                                                     │
│  Orchestrator, Principal Context, DGA (router)      │
├─────────────────────────────────────────────────────┤
│  ADAPTER LAYER — Data Connectivity                  │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Agent9 Data  │  │ Cortex       │  │ Databricks│ │
│  │ Contracts    │  │ Analyst      │  │ Genie     │ │
│  │ (fallback)   │  │ Semantic     │  │ Spaces    │ │
│  │              │  │ Views        │  │           │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘ │
│         │                 │                │        │
│         └────────┬────────┴────────────────┘        │
│                  │                                   │
│           DGA (intelligent router)                   │
│           "Which data product? Which semantic layer? │
│            Which principal has access?"               │
│                  │                                   │
│         MCP / Direct SDK                             │
│         (transport only)                             │
└─────────────────────────────────────────────────────┘
```

### The DGA's Role

The Data Governance Agent becomes the critical routing layer:

1. **Query routing:** User asks a follow-up question → DGA determines which data product holds the answer → routes to the appropriate vendor semantic layer (Cortex Analyst, Genie) or falls back to Agent9's own data contract + SQL generation

2. **Access control:** DGA knows which principal has access to which data products. Vendors handle row/column security within their platform, but DGA handles cross-platform, cross-data-product governance.

3. **Semantic translation:** DGA translates business terms to technical terms. When a customer has Cortex Analyst, DGA can delegate this to the vendor's semantic model. When they don't, DGA uses its own glossary.

**Key insight from the user:** Vendors don't know that *this* question should go to *this* data product and not *that* one. Agent9's DGA sits above individual platforms and makes that routing decision.

---

## What This Means for Each Agent

### Agents That Stay Exactly As They Are (Moat)

| Agent | Role | Investment Priority |
|-------|------|-------------------|
| **SA** | KPI monitoring, breach detection, opportunity signals | **HIGH** — deepen calibration, adaptive profiles |
| **DA** | Is/Is Not analysis, change-point detection, SCQA | **HIGH** — deepen analytical frameworks |
| **SF** | Multi-persona solution debate, trade-offs | **HIGH** — deepen quantified impact |
| **VA** | DiD attribution, verdict matrix, lifecycle | **HIGH** — deepen ROI validation |
| **PIB** | Briefing composition, delegation, tokens | **HIGH** — deepen decision workflow |
| **Orchestrator** | Pipeline coordination | **MEDIUM** — stable, extend as needed |
| **Principal Context** | Role-based accountability | **HIGH** — KPI accountability registry (Phase 11A) |
| **LLM Service** | Model routing, token tracking | **MEDIUM** — stable |

### Agents That Become Thin Adapters (Commodity)

| Agent | Current Role | Future Role | Investment Priority |
|-------|-------------|-------------|-------------------|
| **DPA** | Schema inspection, SQL generation, contract YAML, query execution | **Thin adapter:** delegates schema discovery to vendor MCP, delegates NL-to-SQL to vendor semantic layer, falls back to own contracts when vendor layer unavailable | **LOW** — maintain, don't expand |
| **NLP Interface** | Regex-based NL parsing (TopN, timeframe, grouping) | **Thin router:** simple queries → existing regex; complex queries → Cortex Analyst / Genie via DGA | **LOW** — don't build LLM NL-to-SQL (vendors will do this) |
| **KPI Assistant** | LLM-powered KPI suggestions | **Unchanged for now** — unique capability, vendor doesn't offer this yet | **MEDIUM** |

### Agent That Becomes More Important (Router)

| Agent | Current Role | Future Role | Investment Priority |
|-------|-------------|-------------|-------------------|
| **DGA** | Business term translation, KPI mapping, access validation (mostly stubs) | **Intelligent router:** determines which vendor semantic layer to use, which data product to query, enforces cross-platform access control. The layer that makes multi-platform work. | **HIGH** — was deprioritized, now critical |

---

## Roadmap Implications

### Phases That Increase in Priority

| Phase | Why More Important |
|-------|-------------------|
| **11A: KPI Accountability Registry** | Dimensional accountability is pure moat — vendors don't have this |
| **11D: Adaptive Calibration Loop** | Compounding moat — calibrated profiles get better with time |
| **DGA-A: Wire existing methods** | DGA is now the routing layer, not just a governance stub |
| **DGA-B: Real access control** | Multi-vendor routing requires real access control |

### Phases That Decrease in Priority

| Phase | Why Less Important |
|-------|-------------------|
| **10D-C: Admin Console data onboarding UI** | Simplify — if vendors have onboarding UIs, don't compete |
| **10E: Native AI Capabilities** | Reframe — don't build Cortex/Mosaic integration for analysis; instead consume their semantic layers as input |
| **Phase 13+ LLM NL-to-SQL** | Cancel — delegate to Cortex Analyst / Genie instead of building |

### Phases That Change Scope

| Phase | Original Scope | Revised Scope |
|-------|---------------|---------------|
| **10D: MCP Abstraction** | MCP + platform migration + Admin Console | MCP as data pipe only. `SYSTEM_EXECUTE_SQL` for SA/DA deterministic queries. Defer vendor semantic layer integration to Phase 11F. |
| **10E: Native AI** | "Leverage platform-native LLM features for enhanced analysis" | Reframe as "Consume vendor semantic layers as thin adapters for the analytical pipeline" |
| **11F (new): Vendor Semantic Integration** | Didn't exist | Wire Cortex Analyst + Genie as optional NL-to-SQL backends, routed by DGA. Replaces Phase 13+ NL-to-SQL item. |

---

## Connectivity Modes

### Mode 1: MCP as Data Pipe (Phase 10D — NOW)

```
SA/DA generate SQL (from data contracts) → MCP SYSTEM_EXECUTE_SQL → warehouse → results → Agent9 analyzes
```

**For:** Deterministic, repeated KPI monitoring queries. Stable, reliable, no vendor AI dependency.

### Mode 2: Vendor Semantic Layer for Ad-Hoc (Phase 11F — FUTURE)

```
User asks complex follow-up → NLP Interface → DGA routes to Cortex Analyst / Genie → vendor generates SQL → results → Agent9 frames analytically
```

**For:** Complex ad-hoc questions that exceed regex parsing. Vendor's semantic model handles the NL-to-SQL.

### Mode 3: Agent9 Own Contracts (Fallback — ALWAYS)

```
Customer has no vendor semantic layer → Agent9 data contracts → DPA generates SQL → MCP executes → results → Agent9 analyzes
```

**For:** Customers without Cortex Analyst / Genie. New onboarding before vendor setup. Local dev with DuckDB.

---

## Decision Record

| Decision | Rationale |
|----------|-----------|
| SA/DA queries use MCP as dumb pipe with Agent9-generated SQL | Deterministic queries need stability, not vendor AI |
| Complex ad-hoc NL queries delegate to vendor semantic layers | Vendors will always be better at NL-to-SQL on their own platform |
| DGA routes between vendor semantic layers and own contracts | Cross-platform governance is Agent9's unique position |
| Don't build LLM NL-to-SQL in Agent9 | Vendors commoditize this; invest in analytical pipeline instead |
| Data contracts remain as fallback, not primary | Customers without vendor semantic layers still need onboarding |
| Phase 10D scope narrowed to MCP data pipe only | Don't over-build the commodity layer |

---

## Summary

**Agent9's moat is making decisions from data, not connecting to data.**

The SA→DA→SF→VA pipeline is unique. Data connectivity is plumbing. Build thin adapters that work with whatever the customer already has. Invest in the analytical intelligence that no vendor replicates.
