# Agent9-HERMES Development Plan

**Created:** 2026-03-14
**Last updated:** 2026-04-23
**Status:** Active

---

## Where We Are — April 2026

### Pipeline status: fully operational end-to-end

```
run_enterprise_assessment.py
  → SA (detect KPI breaches, client-scoped)
  → DA (Is/Is Not root cause, benchmark segments)
  → kpi_assessments + assessment_runs (Supabase)
  → A9_PIB_Agent (compose + email)
  → Principal clicks email link
  → Decision Studio (Deep Analysis → Solution Finding → HITL → Value Assurance)
  → Portfolio (5-phase lifecycle tracking → verdict → ROI)
```

**14 agents operational.** Core loop: detect → diagnose → prescribe → decide → track → verify.

### What's working

| Capability | Status |
|-----------|--------|
| Enterprise KPI assessment (batch, client-scoped) | Production-ready |
| SA breach detection + opportunity signals | Production-ready |
| DA Is/Is Not root cause + change-point detection | Production-ready |
| DA benchmark segments (replication candidates) | Production-ready |
| Market context enrichment (Perplexity + Claude) | Production-ready |
| Multi-persona solution generation (3×Stage1 + synthesis) | Production-ready |
| HITL approval workflow | Production-ready |
| Value Assurance tracking (DiD attribution, verdict matrix) | Production-ready |
| VA 5-phase lifecycle (Approved→Implementing→Live→Measuring→Complete) | Production-ready |
| VA Portfolio dashboard (KPI-aware formatting, cost KPI sign flip) | Production-ready |
| White-paper report (Gartner-style cold-eyes document) | Production-ready |
| PIB email delivery (Jinja2, SMTP, Gmail App Password) | Production-ready |
| Single-use briefing tokens (deep link, delegate, request_info, approve) | Production-ready |
| Delegation flow (DelegatePage, audit trail in situation_actions) | Production-ready |
| Follow-up NL questions with inline data results | Production-ready |
| Data Product Onboarding (8-step orchestrated workflow) | Production-ready |
| Decision Studio UI (React/Vite/Tailwind, Swiss Style) | Production-ready |
| Supabase-backed registries (6 registries) | Production-ready |
| DuckDB + BigQuery + SQL Server + Snowflake + PostgreSQL data sources | Production-ready |
| Production deployment (Railway + Vercel + Supabase Cloud) | Live (deployed Mar 2026) |
| SF fast debate mode (2 calls dev / 4 calls production) | Production-ready |

### What's not built yet

| Capability | Planned phase |
|-----------|--------------|
| DGA mandatory wiring — test suite (happy path, init failure, view resolution) | Phase 10B-DGA tests |
| KPI trend chart (monthly_values populated for all backends) | Phase 10D |
| KPI accountability registry (dimensional ownership) | Phase 11A |
| LLM-assisted accountability import from HCM documents | Phase 11B |
| Unified situation stream (merge problem + opportunity) | Phase 11C |
| Adaptive calibration loop (KPI Assistant → monitoring profiles) | Phase 11D |
| Audio briefings (TTS flash briefing) | Phase 11E |
| DA market signal conflict detection (outperforming / confirming / missing tailwinds) | Phase 11F |
| Business Optimization workflow (top-down strategic) | Phase 12 |
| KPI Assistant UI | Phase 12 |
| Slack notifications | Phase 12 |
| Platform Admin & Client Onboarding (4-step guided flow) | Infra A2 |
| Usage monitoring (events, quotas, alerts) | Infra A3 |
| Authentication (Supabase Auth) | Infra B |
| Azure OpenAI provider + LLM audit export | Infra B2 |
| Multi-tenant isolation | Infra B |

### Known tech debt (remaining)

| Item | Notes |
|------|-------|
| `situations` table partially redundant with `kpi_assessments` | Deprecation deferred — used by VA pipeline. Consolidate in Phase 11A. |
| `kpisScanned={14}` hardcoded in `DecisionStudio.tsx` | Wire real count from assessment API in Phase 11C |
| Separate `OpportunitySignal` / `Situation` models | Unify in Phase 11C |
| `run_enterprise_assessment.py` has no scheduler | CLI only — scheduler deferred |
| SA/PCA/DPA agents cache registry data at startup | KPIs, principals, and data products loaded into memory at `connect()` — registry changes (new client, new KPI) require a service restart to take effect. Fix: live-query Supabase per request in `_get_relevant_kpis()`, `get_principal_context_by_id()`, and DPA data product lookup. |

---

## Architecture decisions (non-negotiable)

- **SA = sensor** — detects KPI movements, no problem/opportunity labeling
- **DA = analyst** — determines framing (problem vs opportunity) from IS/IS NOT
- **Assessment runs are client-scoped** — one enterprise scan per client, all principals read from it
- **KPI accountability is dimensional** — principals own KPIs at their scope of control (enterprise, region, LOB); same KPI can belong to multiple principals at different scopes
- **No snooze/hide preference layer** — correct signal routing eliminates noise at source
- **LLM-assisted accountability import** — HCM documents are the source of truth; LLM extracts, human confirms (same pattern as KPI Assistant)
- **Brand: "Decision Studio"** — Swiss Style, monochrome dominance, semantic color only, "Quiet Expert" voice
- **Domains:** decision-studios.com (brand) + trydecisionstudio.com (demo/trial)

Full accountability model: `docs/architecture/kpi_accountability_model.md`

---

## Completed Phases

### Phase 10A: Decision Studio App UI ✅ COMPLETE (Apr 2026)

Swiss Style brand identity across all UI surfaces:
- `BrandLogo` aperture component shared across Login, DelegatePage, ActionHandler, ExecutiveBriefing, Portfolio
- Satoshi font loaded globally; semantic color tokens; monochrome base
- KPI tile visual refresh — deep slate card, 1px left-border severity indicator, factual summary copy
- KPI tile variance/delta bar chart (DivergingBarChart component)
- Deep Analysis Is/Is Not exhibit — Top 5 IS / Top 3 IS NOT, dimension labels, McKinsey exhibit style
- ProblemRefinementChat sticky footer — suggested responses + input always visible
- CouncilDebate terminal log aesthetic — monospace timestamps, clean progress bars
- ExecutiveBriefing brand refresh + print CSS fix
- TrajectoryChart — dark background, dotted red inaction line, solid slate expected, crisp white actual
- DelegatePage + ActionHandler — aperture mark, visual consistency
- Login — "Decision Studio" heading, aperture mark
- Client dropdown removed from SA Console header (moved to Login)
- Dead code removal — VarianceDrawer.tsx, RidgelineScanner.tsx, SnowflakeScanner.tsx deleted
- Debug artifacts removed — console.log statements, hardcoded counts, placeholder text

### Phase 10B: PIB Email Template Refresh ✅ COMPLETE (Apr 2026)

- Swiss Style monochrome email template
- Section hierarchy: New Situations → Urgency → Solutions → Managed
- Top 3 IS driver rows per situation block
- Measured CTA copy — "Request a Conversation", "View the Analysis"
- Mobile-safe layout tested on Gmail
- Flash Briefing text block structured for future TTS delivery

### Phase 10C: Multi-Warehouse Direct SDK Connectors ✅ COMPLETE (May 2026)

All four backends operational and verified end-to-end via SA scan:

| Backend | Client | Situations detected | Notes |
|---------|--------|-------------------|-------|
| DuckDB | bicycle | 0 | No 2026 Actual data in dev dataset |
| BigQuery | lubricants | 8 | Production-ready |
| SQL Server | hess | 4 | Dev only — `pyodbc`/ODBC driver not in production Docker image |
| Snowflake | apex_lubricants | 3 | `AGENT9_DEMO.LUBRICANTS.LubricantsStarSchemaView` |

**Production gap — SQL Server:** `pyodbc` requires the Microsoft ODBC Driver 18 at the OS level. The current `python:3.11-slim` Docker image does not include it. SQL Server works in local dev but returns `Cannot connect: pyodbc/unixODBC not available` in Railway. Fix tracked in Infra A4: SQL Server Production Enablement below.

**What was built (prior to May 2026 — plan was stale):**
- `src/database/backends/sqlserver_manager.py` — pyodbc + asyncio.to_thread, MERGE upsert, INFORMATION_SCHEMA profiling
- `src/database/backends/snowflake_manager.py` — snowflake-connector-python, async wrapper
- `src/database/backends/databricks_manager.py` — Databricks SQL connector
- DPA `_ensure_sqlserver_connected()` / `_ensure_snowflake_connected()` — config from data product metadata → env vars → defaults
- DPA `_profile_table_sqlserver()` — full INFORMATION_SCHEMA profiling with FK extraction
- SA agent `_resolve_source_system()` — Tier 1 routing via `data_product_id` registry lookup
- SA agent `_get_kpi_value()` — `_is_ss_kpi` / `_is_sf_kpi` routing, T-SQL and Snowflake date injection, comparison SQL

**Connection config resolution (both backends):**
1. Data product `metadata` fields (e.g. `sqlserver_host`, `snowflake_account`)
2. Env vars (`SS_HOST`, `SS_PASSWORD` / `SF_ACCOUNT`, `SF_PASSWORD`)
3. Hard-coded dev defaults

---

### Phase 10D: Solution Finder Performance Tuning ✅ COMPLETE (Apr 2026)

**Result:** Dev latency reduced from ~9 min to ~3 min per debate (3× speedup).

| Deliverable | What was done |
|------------|---------------|
| Fast debate mode (`VITE_DEBATE_MODE`) | Dev: 2 API calls (stage1_only + synthesis). Production: 4 calls (all stages). Controlled via `.env.development` / `.env.production`. |
| DA context trimming | When Stage 1 hypotheses exist, skip full `deep_analysis_context` from synthesis payload (~8-12K token reduction). `da_summary` carries all key signals; personas already processed the full context in Stage 1. |
| Model routing preserved | Stage 1 → Haiku (parallel, ~5s). Synthesis → Sonnet (full power). No quality compromise in either mode. |

**Files changed:**
- `decision-studio-ui/src/hooks/useDecisionStudio.ts` — fast mode conditional stage skip
- `decision-studio-ui/src/pages/CouncilDebatePage.tsx` — fast mode conditional stage skip
- `src/agents/new/a9_solution_finder_agent.py` — conditional `deep_analysis_context` exclusion
- `decision-studio-ui/.env.development` — `VITE_DEBATE_MODE=fast`
- `decision-studio-ui/.env.production` — `VITE_DEBATE_MODE=full`

### VA 5-Phase Lifecycle ✅ COMPLETE (Apr 2026)

Expanded VA from single verdict status to independent lifecycle + evaluation dimensions:

| Component | What was built |
|-----------|---------------|
| `SolutionPhase` enum | APPROVED → IMPLEMENTING → LIVE → MEASURING → COMPLETE (forward-only transitions) |
| Backend agent method | `update_solution_phase()` — validates transition order, sets `go_live_at`/`completed_at`, resets `actual_trend` on Go Live |
| API endpoint | `PATCH /solutions/{id}/phase` — delegates to agent |
| Supabase migration | `phase`, `go_live_at`, `completed_at` columns + backfill |
| TrajectoryChart | Phase-aware rendering — CoI only during APPROVED/IMPLEMENTING, all lines at LIVE+ |
| Portfolio table | Redesigned: humanized KPI name, phase badge, verdict badge, KPI-aware impact formatting ($K/$M vs %), cost KPI sign flip (savings = positive) |
| Phase transition buttons | "Mark Implementing" (APPROVED→IMPLEMENTING), "Go Live" (IMPLEMENTING→LIVE) |
| Auto-complete | `evaluate_solution_impact()` auto-transitions to COMPLETE on verdict |
| Demo seed script | `scripts/seed_va_demo_data.py` — 7 solutions across all phases |

### White-Paper Report Page ✅ COMPLETE (Apr 2026)

- Standalone page at `/report/:situationId` — Gartner-style, white background, narrative arc
- Sections: Cover → Executive Summary → Situation → Root Causes → Market → Options → Recommendation → Roadmap → Risks → Appendix
- Draft/Approved badge from localStorage approval state
- Print and Download PDF buttons
- "Generate Report" link from Executive Briefing page

---

## Forward Plan

---

### Data Connectivity Tiers — The Three-Level Integration Model

**Status:** Strategic framework — governs all Phase 10C, 10D, and 11F decisions.

Agent9 connects to customer data warehouses at three progressive levels of integration depth. Each tier is independently deployable. Higher tiers are added on top of lower ones — they don't replace them.

```
┌───────────────────────────────────────────────────────────────────┐
│  Tier 3 — Vendor Agent                                            │
│  Customer has Cortex Analyst or Databricks Genie                  │
│  Agent9 sends a question → vendor AI handles NL-to-SQL, joins,   │
│  semantic resolution → Agent9 frames the result analytically      │
│  DGA routes: "which vendor semantic layer answers this question?"  │
├───────────────────────────────────────────────────────────────────┤
│  Tier 2 — Vendor MCP Server                                       │
│  Vendor hosts the MCP endpoint. Agent9 generates SQL from its     │
│  own data contracts, sends it via MCP EXECUTE_SQL, gets results.  │
│  Credentials never in Agent9 code — env var name only.            │
│  Snowflake Cortex MCP, Databricks MCP, SAP BDC MCP, Postgres MCP │
├───────────────────────────────────────────────────────────────────┤
│  Tier 1 — Native Plug-in                                          │
│  Agent9 owns the connection via direct SDK. SQL is generated by   │
│  DPA from Agent9 data contracts. Agent9 manages auth + execution. │
│  BigQuery (current), Snowflake SDK, Databricks SQL connector       │
└───────────────────────────────────────────────────────────────────┘
           ↓ Always present as fallback regardless of tier ↓
┌───────────────────────────────────────────────────────────────────┐
│  Tier 0 — Embedded (local/demo only)                              │
│  DuckDB in-process. No network. Used for dev and bicycle demo.    │
└───────────────────────────────────────────────────────────────────┘
```

#### When Each Tier Applies

| Tier | Customer Profile | Agent9 Role | SQL Owner |
|------|-----------------|-------------|-----------|
| **0 — Embedded** | Local dev / demo | Everything | Agent9 DPA |
| **1 — Native Plug-in** | Has warehouse, no MCP | Full control, direct SDK | Agent9 DPA |
| **2 — Vendor MCP** | Vendor has MCP server | Send SQL, get results | Agent9 DPA |
| **3 — Vendor Agent** | Has Cortex Analyst / Genie | Send question, frame result | Vendor AI |

#### Design Rules (Non-Negotiable)

- **SA and DA always use Tier 1 or 2** — deterministic, repeated KPI queries must not depend on vendor AI. Monitoring cannot be non-deterministic.
- **Tier 3 is for ad-hoc follow-up only** — complex NL questions from principals that exceed Agent9's regex NLP. Never for core pipeline queries.
- **DGA is the router** — determines which tier and which data product answers a given question. Vendors don't know which data product to query; the DGA does.
- **Tier 2 transport is neutral** — Agent9-generated SQL runs unchanged on any warehouse via MCP. No SQL translation.
- **Fallback chain:** Tier 3 unavailable → Tier 2 → Tier 1 → Tier 0. Each tier degrades gracefully.

#### Phase Mapping

| Phase | Tier | What Gets Built |
|-------|------|-----------------|
| **10C** ✅ | Tier 1 | SqlServerManager + SnowflakeManager + DatabricksManager direct SDK connectors — complete |
| **10D** | Tier 2 | MCP client + vendor MCP endpoint wiring; replaces direct SDK via decorator pattern |
| **11F** | Tier 3 | DGA routing to Cortex Analyst / Genie for complex NL follow-up |

**Reference:** `docs/architecture/data_connectivity_strategy.md`

---

### Phase 10B-DGA: Data Governance Agent — Mandatory Wiring ✅ COMPLETE (May 2026)

**Steps 1 & 2 complete.** All 16 optional `if self.data_governance_agent:` guards removed. Mandatory `RuntimeError` guards in place in all three agent files. DGA wired post-bootstrap via `runtime._wire_governance_dependencies()`.

**What was done:**
- SA agent (`process_nl_query`): 3 optional guards removed; mandatory `is None → raise RuntimeError` guard + 2 direct DGA calls
- DPA (`_get_view_name_from_kpi`, `_lookup_kpi_by_name`): 2 optional guards removed; mandatory `is None → raise RuntimeError` guard + 2 direct DGA calls
- DA agent (`plan_deep_analysis`): mandatory `is None → raise RuntimeError` guard added (May 2026, final fix closing the phase)

**DGA-B: DEFERRED** — `validate_data_access()` stays always-true stub. No real tenants → no cross-client risk. Revisit with Infra B (multi-tenant isolation, pre-Sep 2026).

**Remaining (Step 3 — tests):**
No DGA-specific test file exists. Three tests needed:
1. Mandatory DGA path happy path (SA `process_nl_query` with DGA wired → succeeds)
2. DGA init failure → clean `RuntimeError` (not `AttributeError`)
3. View name resolution through DGA in DPA `_get_view_name_from_kpi`

**Test file to create:** `tests/unit/test_a9_data_governance_wiring.py`

---


### Phase 10D: MCP Abstraction Layer

**Goal:** Transition from direct SDK to vendor-managed MCP servers when available. Decorator pattern allows swapping connection method without changing application code.

**Why separate from 10C:** Direct SDK works immediately with trial accounts (Phase 10C). Vendor MCP servers mature over time. Splitting phases allows Phase 10C to ship while infrastructure evolves.

| Deliverable | Description |
|------------|-------------|
| MCP client utility | HTTP client for MCP execute-sql calls with auth header injection |
| Manager MCP wrappers | Decorator pattern — same DatabaseManager interface, `connect()` routes to MCP endpoint |
| Connection profile schema | Add connectivity_type (direct_sdk/mcp_server), mcp_endpoint, mcp_auth_type fields |
| Factory MCP detection | DatabaseManagerFactory reads connectivity_type and instantiates correct wrapper |
| Migration guide | Document upgrade path from direct SDK to MCP (zero application code changes) |

**Prerequisite:** Vendor MCP servers released and stable (Snowflake Cortex MCP, Databricks SQL MCP). Phase 10D gates on vendor deliverables, not Agent9 development.

---

### Phase 10E: Native AI Capabilities (Snowflake Cortex, Databricks Mosaic)

**Goal:** Leverage platform-native LLM and AI features for enhanced analysis within customer data warehouses. Optional, deployed only when customers have platform upgrades.

**Why separate:** Non-critical enhancements. Require explicit platform upgrades (Cortex license, Mosaic subscription). Keep core connectivity (10C) and infrastructure (10D) clean.

**Capabilities to explore:**
- **Snowflake Cortex** — native SQL functions: `COMPLETE()` (LLM calls), `EXTRACT_ANSWER()`, vector embeddings, semantic search
- **Databricks Mosaic AI** — managed LLM service (Claude, GPT, Llama), fine-tuning, inference optimization

| Deliverable | Description |
|------------|-------------|
| Capability inventory | Document Cortex, Mosaic, UC AI maturity levels, licensing, performance |
| QueryDialect robustness | Ensure QueryDialect can parse customer views with Cortex functions without breaking |
| In-warehouse enrichment guide | Document patterns for customers to embed Cortex/Mosaic calls in curated views |
| Integration points (Phase 11+) | Document for future: in-SQL explanations, semantic drill-down, outcome prediction |
| Tests | Verify QueryDialect handles Cortex/Mosaic functions. Integration tests verify execution. |

**Design principle:** Customer-controlled enhancements. Customers enrich their curated views with Cortex/Mosaic calls at their discretion. Decision Studio executes enriched views without modification.

**Future (Phase 11+):** In-SQL explanation generation ("why is this KPI down?"), semantic drill-down suggestions, anomaly context discovery — all powered by Cortex/Mosaic, all staying within customer's warehouse.

### Phase 11: Platform Correctness

**Goal:** Complete the architectural model that makes signal routing correct by construction. Five independent sub-phases — build in any order.

#### 11A: KPI Accountability Registry ← NEXT

**Goal:** Principals own KPIs at the scope of their control. The registry expresses this dimensionally — routing is correct by construction, not patched with filters.

**Why now:** Phase 11A tech debt is already cleaned (assessment runs client-scoped, snooze removed, `get_latest_run` fixed). The next step is the accountability registry that makes per-principal PIB filtering accurate.

| Deliverable | Description |
|------------|-------------|
| `KPIAccountability` Pydantic model | `kpi_id`, `principal_id`, `scope_dimension` (optional), `scope_value` (optional), `role` (accountable/responsible) |
| Supabase migration | `kpi_accountability` table; max 1 accountable per KPI per scope |
| Seed lubricants data | Map 15 lubricants KPIs to 4 principals with correct enterprise/LOB scopes |
| PIB uses accountability registry | `_populate_situations` filters `kpi_assessments` by principal's accountability assignments rather than all situations |
| Admin UI — accountability view | Read-only list in Registry Explorer to start; editable later |

#### 11B: LLM-Assisted Accountability Import

**Goal:** Solve the enterprise cold-start problem — extract KPI accountability from HCM documents rather than requiring manual entry.

**Pattern:** Same as KPI Assistant — LLM suggests, human confirms, registry writes.

| Deliverable | Description |
|------------|-------------|
| `A9_Accountability_Import_Agent` | Accepts HCM document text (job descriptions, OKRs, RACI), extracts accountability statements, maps to KPI registry, returns proposals with confidence scores |
| Admin confirmation UI | Present extracted assignments; accept / adjust / reject before writing to registry |
| Conflict detection | Flag KPI assigned to >3 principals without dimensional scoping |

#### 11C: Unified Situation Stream

**Goal:** Remove the artificial problem/opportunity split. One stream, direction determines framing.

| Deliverable | Description |
|------------|-------------|
| Single situation grid | Remove separate opportunity section; one grid sorted by `abs(percent_change)` |
| Direction-agnostic SA | Unified `situations[]`; deprecate `OpportunitySignal` model |
| `card_type` → `direction` | Replace binary problem/opportunity with `up`/`down` direction field |
| Wire `kpi_evaluated_count` | Replace hardcoded `kpisScanned={14}` with real count from assessment API |

#### 11D: Adaptive Calibration Loop

**Goal:** KPI monitoring profiles improve automatically over time. Core compounding moat.

**Prerequisite:** Phase 9 (assessment engine with monitoring profiles) — already complete.

| Deliverable | Description |
|------------|-------------|
| Historical volatility analysis | KPI Assistant computes std dev, seasonal decomposition per KPI |
| Monitoring profile recommendation | LLM proposes `comparison_period`, `volatility_band`, etc. with rationale |
| Conversational refinement | Admin can challenge recommendations with domain knowledge |
| Recalibration trigger | After N cycles: what % of escalated situations led to action vs noise? |
| KPI Assistant UI | React panel for monitoring profile setup (currently API-only) |

**Moat:** After 12 months, switching means losing calibrated profiles for 50+ KPIs and validated noise/signal history.

#### 11F: DA Market Signal Conflict Detection

**Goal:** When internal KPI data moves in the opposite direction to the market intelligence signal, surface that conflict as the lead insight in the SCQA narrative — not as two separate sections sitting side by side.

**Why this matters:** Today the DA presents IS/IS NOT dimensional analysis and market intelligence independently. If a company's base oil costs fell 19.5% while market data shows industry-wide cost pressures of 15-25%, those two signals contradict each other — and the contradiction *is* the most valuable insight. The DA should detect, interpret, and frame it explicitly.

**Three conflict patterns to handle:**

| Pattern | Internal | Market | DA Framing |
|---------|----------|--------|------------|
| **Outperforming headwinds** | Costs ↓ 19% | Market costs ↑ 15-25% | "You are beating the market by ~35pp. What procurement strategy drove this? Is it structural or temporary?" |
| **Not capturing tailwinds** | Costs ↓ 5% | Market costs ↓ 20% | "Market conditions moved in your favour but you only captured 25% of available savings. Which contracts are locking you into above-market rates?" |
| **Confirming pressure** | Costs ↑ 19% | Market costs ↑ 15-25% | External validation. "Your experience aligns with market conditions. Focus shifts to which segments are most exposed." |

**Implementation:**

| Deliverable | Description |
|------------|-------------|
| Direction extraction | After MA agent returns, extract direction and magnitude of market signal (up/down/neutral, estimated %) |
| Conflict detection | Compare internal `percent_change` direction + magnitude against market signal direction |
| SCQA prompt update | Pass both signals into `_generate_scqa_summary()` with explicit instruction: "If directions conflict, lead with that conflict as the Complication. Interpret whether the company is outperforming or missing tailwinds." |
| Conflict badge in UI | Optional — small badge in DA view: "Outperforming market" / "Underperforming tailwind" / "Confirming market" |

**Prerequisite:** Phase 11C (unified situation stream) — direction is cleanly expressed as `percent_change` + `inverse_logic` by then, making conflict detection straightforward.

---

#### 11E: Audio Briefings ⏸ ON HOLD (post-MVP)

**Goal:** 60-second audio flash briefing — the "not a dashboard" differentiator for commuting executives.

**Status:** On hold for MVP. The Flash Briefing text block (Phase 10B) is structured for future TTS delivery — same content, different output channel. Revisit after first pilot signed.

| Deliverable | Description |
|------------|-------------|
| `A9_Audio_Briefing_Agent` | LLM summarization → TTS API (OpenAI TTS, ElevenLabs, or Google Cloud TTS) |
| Workflow-stage framing | SA → "Flash Briefing", DA → "Detective's Summary", SF → "Council Debate" |
| Audio player UI | Inline player + transcript in Decision Studio |

---

### Phase 12: Business Optimization + Platform Completeness

**Goal:** Top-down strategic workflow + close remaining gaps (KPI Assistant UI, Slack).

| Deliverable | Description |
|------------|-------------|
| Business Optimization workflow | Board/executive-initiated strategic directives flowing through SF and VA |
| `A9_Risk_Analysis_Agent` | Weighted risk scoring (PRD exists, dead code — rewrite) |
| `A9_Stakeholder_Analysis_Agent` | Identify stakeholders, estimate support/resistance |
| KPI Assistant UI | React panel for the existing API-only KPI suggestion workflow |
| Slack notifications | PIB summary to Slack channel alongside email |

**Reference:** `workflow_definitions/business_optimization.yaml`, `workflow_definitions/innovation_driver.yaml`

---

### Phase 13+: Future (not scheduled)

| Initiative | When |
|-----------|------|
| Extended Solution Finding (Risk, Stakeholder, Solution Architect agents) | After Phase 12 |
| Innovation Driver (proactive pattern application from VA history) | After multiple VA cycles |
| Decision Journal (institutional decision memory) | Enterprise tier only |
| Scenario Exploration (SF parameter adjustment) | Enterprise tier only |
| Principal Learning Profile | Enterprise tier only |
| KPI execution plan cache | Post first paying client — justified by usage data only. Keyed on `(kpi_id, timeframe, comparison_type, filters_hash)`, stores compiled SQL + result TTL in Supabase. Revisit when: >50 KPIs on daily cadence, or LLM costs >10% of infrastructure, or client requests it. |
| LLM-assisted NL→SQL for complex follow-up questions | Phase 11F or later — NLP Interface regex handles simple TopN queries today; LLM SQL generation needed for complex ad hoc P&L queries. MCP-connected warehouses (Snowflake Cortex, Databricks AI/BI) may handle this natively — evaluate before building. |
| **Decision Altitude classifier** | VA agent feature. Tags every approved decision as Operational or Strategic at approval time. Operational decisions → 90-day VA tracking with strict ROI measurement. Strategic decisions → long-horizon milestones, explicitly decoupled from short-term ROI scoring. Prevents Goodhart's Law: executives gaming the system by only approving safe, measurable tweaks to protect bonus metrics. |
| **Decoupling Event detection** | MA Agent enhancement. Detects when the current market regime differs materially from the regime under which historical Registry ROI data was generated. SF surfaces a confidence warning: "This playbook was built under a low-interest-rate / pre-tariff environment — confidence in replication is LOW." Circuit breaker for regime-shift errors. |
| **Systemic Shock mode** | SA Agent enhancement. When 80%+ of Tier 1 KPIs breach critical thresholds simultaneously, abandon dimensional Is/Is Not analysis (control group collapses) and enter Crisis Mode: cash preservation, liquidity exposure, and drawdown mapping replace normal situation cards. UI treatment changes to signal the shift. DiD attribution is suspended — VA cannot produce clean causal attribution during systemic shocks. |
| **Executive Autopsy view** | Registry / onboarding feature. When a new executive joins, surface a verified historical record of which prior initiatives moved KPIs and which did not (with DiD attribution). Framed as "objective autopsy, not legacy playbook" — caters to new executives' desire to establish their own baseline by showing them exactly what the old regime got wrong. Mitigates organ-rejection risk when leadership changes. |

---

### Thought Leadership Roadmap

Three content assets implied by the Kahneman / organizational RL product vision (May 2026).
These are external-facing pieces — white papers, keynotes, or long-form blog posts.
Not landing page copy (landing page handled separately in the positioning plan).

#### Asset 1: "The Organizational Learning Engine" (White Paper)

**Audience:** CTO, CDO, Chief Strategy Officer — not just CFO.
**Thesis:** Decision Studio is not an analytics tool. It is a calibration system for executive cognition. The full SA → DA → SF → VA pipeline maps directly to a reinforcement learning reward loop operating at the organizational level. Every verified VA outcome recalibrates executive System 1 intuition away from noise and toward ground truth. Over 12–18 months, executive decision quality compounds.

**Arc:**
1. Why organizational "instinct" is currently trained on false positives (confirmation bias, attribution without counterfactuals)
2. The Kahneman System 1 / System 2 gap — and why System 2 has historically been unavailable for most decisions
3. How each pipeline stage maps to the RL loop: SA (environment sensor) → DA (threat identification) → SF (action selection with multi-perspective debate) → VA (reward signal / causal attribution)
4. The Registry as durable institutional memory — decisions, rationale, and verified outcomes persist when executives leave
5. Compounding effect: organizations that run 20+ decisions through the VA loop build a proprietary playbook of what actually works at their scale, in their market

**Adversarial section (builds credibility):** Four ways this breaks — regime shift, black swans, executive departure, Goodhart's Law — and the specific mitigations built into the architecture.

---

#### Asset 2: "Why Smart Executives Make Bad Decisions (And It's Not Their Fault)" (Keynote / Blog)

**Audience:** Executive audience at a business/finance conference. Also works as a LinkedIn long-form post.
**Thesis:** When System 2 analysis costs $500K and twelve weeks, System 1 wins by default. This isn't irrationality — it's the only rational response to the options available. The problem isn't the executive; it's the economics of rigorous analysis.

**Hook:** A CFO sees a 15% margin drop. The evolutionary alarm fires. Without structured analysis available in the time window, they cut costs — the most available System 1 response. Six months later, the cut damaged a key supplier relationship. They never knew if the margin drop was even their fault. A competitor had a supply chain issue that quarter.

**Key points:**
- System 1 vs System 2: why enterprises run on instinct by necessity
- The "monitoring gap": why dashboards fail (staring at stable KPIs is cognitively exhausting)
- How peripheral vision works vs. how dashboards work
- The "78% make decisions first, justify with data after" stat (Hydrogen BI 2025)
- Decision Studio closes the economics gap: System 2 rigor at System 1 speed

---

#### Asset 3: "Four Ways AI Decision Tools Fail — And How We Built Around Them" (Sales / Positioning)

**Audience:** Skeptical CFO or CTO in a late-stage sales conversation. Also works as a "Quiet Expert" thought leadership piece.
**Thesis:** AI systems fail when they assume the future looks like the past. By naming our own failure modes — and showing the specific architectural mitigations — we establish credibility that no competitor who is still pitching "AI magic" can match.

**The four failure modes:**
1. **Regime shift** — historical ROI data becomes obsolete during macro disruption. Mitigation: MA Agent Decoupling Event flag
2. **Black swans** — control group collapses, DiD attribution impossible. Mitigation: Systemic Shock mode suspends attribution, switches to crisis framing
3. **Executive departure** — new leadership rejects inherited playbooks. Mitigation: Executive Autopsy view reframes history as objective evidence, not endorsement
4. **Goodhart's Law** — executives game measurable metrics, avoid bold bets. Mitigation: Decision Altitude classifier decouples strategic decisions from short-term VA scoring

**Closer:** "We point out these limits before you do because we've built around them. That's the difference between a demo that looks impressive and a system you can run your organization on."

---

**Production sequence:** Asset 2 first (shortest, sharpest, LinkedIn-native). Asset 3 second (arms the sales team). Asset 1 last (requires multiple VA cycles to have case study material).

---

## Infrastructure

### Infra A: Production Deployment ✅ COMPLETE (Mar 2026)

- Backend: Railway (Docker/FastAPI)
- Frontend: Vercel (Vite/React)
- Database: Supabase Cloud (Postgres)
- Analytics: BigQuery (GCP credentials via env var)
- GCP credentials materialized from `GCP_SERVICE_ACCOUNT_JSON` at startup
- Bicycle/FI DuckDB data not available in production — lubricants BigQuery works

### Infra A2: Platform Admin & Client Onboarding

**Goal:** Enable new enterprise clients to be registered and onboarded entirely through the UI, without running seed scripts. Sits above the per-client experience — a platform-level capability used by Decision Studio staff (not by clients themselves).

**Context:** The Login page already calls `listClients()` and shows all registered clients. Company Profile already creates a `BusinessContext` and locks a `client_id`. The Data Product Onboarding wizard already exists. What's missing is the entry point and sequencing that ties these together as a new-client flow.

**Current workaround:** Seed scripts (`demo_seed_lubricants.py`, `sync_yaml_to_supabase.py`, `update_principals_lubricants.py`) run manually from the command line. Not viable for self-service or partner delivery.

#### What to build

| Deliverable | Description |
|------------|-------------|
| Platform Admin login path | Separate credential or `role=platform_admin` flag at login. Admin sees all clients; per-client users see only their workspace. |
| Client Management screen | Table of all registered clients (id, name, industry, status, created date). "New Client" button initiates onboarding. |
| Guided onboarding flow (4 steps) | **Step 1 — Company Profile** (already built: `CompanyProfile.tsx` creates BusinessContext + locks `client_id`). **Step 2 — Data Product** (already built: Data Product Onboarding wizard). **Step 3 — Principals** (new: create initial principal profiles for the client). **Step 4 — Validation** (new: run a dry-run SA detect to confirm the pipeline is live). |
| Workspace badge (done ✅) | Persistent `client_id` indicator in Settings header so users always know which workspace they're managing. |
| `client_id` stamped server-side | API create endpoints (`/kpis`, `/principals`, `/data-products`, etc.) read `client_id` from session/token — never from form payload. Form templates omit `client_id`; backend injects it. |

#### Design decisions
- **No self-service registration** — client accounts are created by Decision Studio staff or partners, not by end users. The admin flow is an internal tool.
- **Onboarding = existing tools composed** — Company Profile + Data Product Onboarding + Principal setup are already built. The admin flow sequences them with a progress indicator, not net-new UI.
- **client_id is session-constant** — once logged in, `client_id` cannot be changed within a session. Registry forms never expose it as an editable field.

**Phase:** Infra B prerequisite — complete before first pilot customer.

---

### Infra A3: Usage Monitoring

**Goal:** Track decision volume per client to support pricing conversations, identify expansion opportunities, and detect churn risk — before building automated billing.

**Decision:** Yes to usage monitoring. No to in-app credit purchase yet. First pilot customers will be on negotiated contracts; self-serve purchase belongs after 3+ live clients reveal where limits are actually hit.

#### What to build

| Deliverable | Description |
|------------|-------------|
| `usage_events` table (Supabase) | `client_id`, `event_type` (assessment_run / solution_session / nl_query / kpi_scan), `kpi_id` (nullable), `principal_id` (nullable), `llm_tokens_used` (nullable), `timestamp`. Append-only — no deletes. |
| Usage hooks in orchestrator | Emit a `usage_event` row when: (1) SA assessment completes, (2) SF debate completes, (3) NL query returns a result. Single call to a `UsageService` utility — no agent changes required. |
| Monthly rollup view | Supabase view: `usage_summary_monthly` — assessments, solution_sessions, nl_queries, total_tokens grouped by `client_id` + month. |
| Quota config in client profile | Add `included_assessments` and `included_solution_sessions` fields to `BusinessContext` (or a separate `client_quotas` table). Platform admin sets these at onboarding. |
| Admin Console — Usage panel | Table: client name / assessments this month / solution sessions this month / NL queries / tokens. Color-coded: green (under 80%), amber (80–100%), red (over). |
| Client-facing usage widget | Small section in Settings or Dashboard: "Sessions used: 3 of 4 included this month. Need more? Contact us." CTA sends an email (no purchase flow yet). |
| 80% alert to platform admin | When a client hits 80% of included sessions, log a WARNING in the backend and optionally send an internal email. Platform admin reaches out proactively. |

#### What NOT to build yet
- Stripe integration or automated billing — not until 3+ paying customers
- Hard quota gates (block SF after limit) — warn only; first customers should not hit a wall
- Self-serve credit purchase — revisit when a client actually asks "can I just buy more right now?"

#### KPI-tier bundle pricing (future)
Once usage data from live customers calibrates breach rates:
- 10 KPIs → 2 solution sessions included (low-volatility)
- 25 KPIs → 6 sessions included (growth)
- 50+ KPIs → 15 sessions included (enterprise)

KPI count predicts decision volume — bundle sessions to KPI tiers to make pricing predictable for both sides.

**Phase:** Build alongside or immediately after Infra A2. Prerequisite for any pricing conversation with a pilot customer.

---

### Infra A4: Production Hardening

**Goal:** Make the production system resilient to registry changes, operational surprises, and growth in client count — without requiring service restarts or CLI access.

#### Registry Live-Reload (CRITICAL — fix before second pilot client)

**Problem:** SA, PCA, and DPA agents cache registry data (KPIs, principals, data products) in memory at `connect()` time. Any registry change — new client seeded, KPI added, SQL updated — is invisible to the running service until Railway restarts. Discovered when seeding the Hess client: hess KPIs were in Supabase but the SA agent returned 0 situations because its in-memory registry was stale.

**Fix:**

| Agent | Cached data | Fix |
|-------|------------|-----|
| `A9_Situation_Awareness_Agent` | `self.kpi_registry` (all KPIs) | `_get_relevant_kpis()` queries Supabase provider directly per request, filtered by `client_id` |
| `A9_Principal_Context_Agent` | Principal profiles | Already queries per request via provider — verify no startup cache |
| `A9_Data_Product_Agent` | Data product metadata | Look up data product from provider on each KPI execution, not from startup dict |

**Design rule:** Agents may cache registry data only within the scope of a single request (local variable). No instance-level registry dicts that persist across requests.

**Performance note:** SA scan already executes N SQL queries against external warehouses (BigQuery, Snowflake, SQL Server). One additional Supabase read per scan is negligible.

#### Admin-Triggered Registry Reload (stopgap until live-reload ships)

Add a `POST /api/v1/admin/registry/reload` endpoint that calls `connect()` on SA, PCA, and DPA agents to force a registry refresh without a full service restart. Protected by a platform-admin check. Useful as an immediate fix and as a diagnostic tool.

#### Connection Health Dashboard

Surface in the Admin Console: test each registered data product's connection profile, show last-successful query timestamp, warehouse status. Especially important for Snowflake (auto-suspend) and SQL Server (VPN/firewall dependencies).

#### Seed-from-UI (see Infra A2)

Running seed scripts with production credentials from a developer's machine is not a viable long-term workflow. Infra A2 (Platform Admin & Client Onboarding) replaces this entirely — seed operations become API calls that Railway executes server-side with its own env vars.

**Priority order:**
1. Registry live-reload in SA agent — unblocks Hess and any future client additions without restart
2. Admin reload endpoint — immediate operational relief
3. Connection health dashboard — visibility before adding a third pilot client
4. Seed-from-UI — required before handing onboarding to a non-engineer

#### SQL Server Production Enablement

**Problem:** Railway's `python:3.11-slim` container lacks the Microsoft ODBC Driver 18 and `unixODBC`, which `pyodbc` requires. The hess/SQL Server client is fully seeded and working in dev but returns `Cannot connect: pyodbc/unixODBC not available` in production.

**Recommended approach — Options 1 + 3 combined:**

1. **Add ODBC driver to Dockerfile** — install Microsoft ODBC Driver 18 + `unixodbc-dev` via the Microsoft apt repository. Adds ~200MB to the image, ~2 min to build time. One-time change. Makes ANY SQL Server (on-premise or cloud) work in production.

2. **Stand up Azure SQL Database for hess demo data** — Azure SQL Serverless tier (~$5–15/month at demo usage). Public endpoint accessible from Railway without VPN. Migrate the hess seed data into it. Update the hess connection profile in Supabase to point to the Azure SQL endpoint. Demo is then always-on and cloud-hosted — no local SQL Server dependency for prospect demos.

**Why not on-premise only:** On-premise SQL Server requires network accessibility from Railway (VPN tunnel or public IP). Azure SQL resolves this cleanly for the demo use case. Real customer SQL Servers are addressed in Infra B (customer infrastructure).

**Dockerfile change required:**
```dockerfile
# Microsoft ODBC Driver 18 for SQL Server
RUN apt-get update && apt-get install -y curl gnupg \
 && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft.gpg \
 && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev \
 && apt-get clean && rm -rf /var/lib/apt/lists/*
```

**Azure SQL setup steps:**
1. Create Azure SQL Database (serverless, General Purpose S0 or free tier)
2. Set firewall rule to allow Azure services (Railway's egress IPs or 0.0.0.0/0 for demo)
3. Run `seed_sqlserver_hess.py` against Azure SQL (update connection string)
4. Update hess data product connection profile in Supabase: `sqlserver_host`, `sqlserver_database`, `sqlserver_username`, `sqlserver_password`
5. Store credentials as Railway env vars: `HESS_SS_HOST`, `HESS_SS_PASSWORD`, etc.
6. Deploy updated Dockerfile → verify hess SA scan returns situations in production

**Priority:** After Infra A4 registry live-reload. Before first SQL Server pilot customer.

---

### Infra B: Customer Infrastructure ← BLOCKER for first pilot

**When:** Before first signed pilot (target Sep 2026)

| Deliverable | Priority | Notes |
|------------|----------|-------|
| Authentication | Critical | Supabase Auth — email + password; API keys for programmatic access |
| Multi-tenant isolation | Critical | Per-customer Supabase project; separate registries and KPI sets |
| Customer provisioning script | Critical | Create project → seed registries → configure contracts → send welcome |
| CI/CD pipeline | High | GitHub Actions: test → build → staging → manual promote to production |
| Error monitoring | High | Sentry free tier |
| Staging environment | High | Separate Railway instance |
| Automated backups | High | Nightly registry YAML export |
| Customer data export | Medium | Self-service export for enterprise procurement |

**Cost:** $200–$500/month base + $50–$100/month per customer on paid tiers.

### Infra B2: Enterprise LLM Deployment Options

**Goal:** Unblock regulated-industry prospects (banking, pharma, PE-backed) who cannot send financial data to third-party APIs. Azure OpenAI puts LLM processing inside the customer's own cloud tenant — same analytical capability, zero data residency risk.

**Context:** The `A9_LLM_Service_Agent` already routes to Claude (Anthropic) and has multi-provider architecture. Adding Azure OpenAI is a new provider implementation + config, not a rebuild. Anthropic API already has zero-data-retention by default — Azure OpenAI is for customers who need everything inside their own Azure subscription contractually.

| Deliverable | Description |
|------------|-------------|
| `AzureOpenAIService` provider | New `llm_services/azure_openai_service.py` implementing the same `generate()` interface as `ClaudeService`. Auth via `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_ENDPOINT` env vars. |
| `A9_LLM_Service_Agent` routing | Add `azure_openai` as a valid `LLM_PROVIDER` value. Model mapping: `gpt-4o` → synthesis, `gpt-4o-mini` → Stage 1 persona calls (equivalent to Haiku/Sonnet split). |
| Connection profile config | Document how to set `LLM_PROVIDER=azure_openai` in Railway env vars for a customer's dedicated deployment. |
| On-premise LLM stub (future) | Ollama provider stub — placeholder only. For customers with no cloud allowed. Quality trade-off vs. GPT-4o/Claude is significant; evaluate per-customer. |
| Enterprise security one-pager | `docs/strategy/enterprise_security_faq.md` — answers the five standard security questions buyers raise. Referenced from Data Onboarding page. |
| LLM prompt audit export | Export button in CouncilDebate UI — downloads the full prompt/response log for a session as JSON. GC/CISO review path before contract signing. |

**Trigger:** Build when a prospect is blocked specifically by data residency concerns. Do not build speculatively — Anthropic API covers 80% of enterprise buyers without this.

**Reference:** `docs/strategy/enterprise_security_faq.md`
