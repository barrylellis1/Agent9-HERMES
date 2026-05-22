# Agent9-HERMES Development Plan

**Created:** 2026-03-14
**Last updated:** 2026-05-20
**Status:** Active

---

## Where We Are — May 2026

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
| Production deployment (Railway + Cloudflare Pages + Supabase Cloud) | Live (Cloudflare Pages since Apr 2026, replaces Vercel) |
| SF fast debate mode (2 calls dev / 4 calls production) | Production-ready |
| Opportunity framing — SF Council Debate + VA lifecycle (positive KPI) | Production-ready |
| KPI Accountability Registry — dimensional ownership, Supabase-backed, REST API, Registry Explorer tab | Partial (Phase 11A) — PIB filtering + unit tests not yet written |
| Unified situation stream — direction field replaces problem/opportunity binary; single grid | Production-ready (Phase 11C) |
| Infra A4 — per-request registry refresh, client_id enforcement on all list endpoints, /admin/registry/reload, connection health dashboard | Production-ready |
| Infra B — connection profiles backend storage + credential encryption (AES-256 at rest) | Production-ready |
| Infra B — Supabase Auth dual-mode login (demo selector + email/password), backend JWT middleware | Production-ready |

### What's not built yet

| Capability | Planned phase |
|-----------|--------------|
| ~~DGA mandatory wiring — test suite (happy path, init failure, view resolution)~~ | ✅ Phase 10B-DGA tests — complete (5 tests, May 2026) |
| KPI trend chart (monthly_values populated for all backends) | Phase 10D |
| ~~KPI accountability registry~~| ✅ Phase 11A — complete (registry, API, PIB filter, SA filter, 5 unit tests) |
| LLM-assisted accountability import from HCM documents | Phase 11B |
| ~~Unified situation stream (merge problem + opportunity)~~ | ✅ Phase 11C — complete |
| Adaptive calibration loop (KPI Assistant → monitoring profiles) | Phase 11D |
| Audio briefings (TTS flash briefing) | Phase 11E |
| DA market signal conflict detection (outperforming / confirming / missing tailwinds) | Phase 11F |
| DA Mixed Analysis Mode — single IS/IS NOT view with both problem segments (red) and opportunity segments (green); mixed SCQA narrative; DA determines framing from segment variance, not SA | Phase 11G |
| DA Statistical Enrichment — effect size relative to segment weight, seasonal decomposition (structural vs cyclical), confidence scoring on IS/IS NOT items; replaces heuristic replication_potential with evidence-based scores (Analytical Intelligence Layer 1) | Phase 11H |
| KPI Causal Intelligence — KPI interdependency map in DGA; cross-KPI conflict detection before solution approval; strategic alignment scoring against declared corporate priorities (Analytical Intelligence Layer 2) | Phase 2 (2027) |
| Business Optimization Agent — portfolio-level optimization across coupled KPIs; cross-intervention conflict detection; execution sequencing; strategic alignment (Analytical Intelligence Layer 3) | Phase 3 (2028) |
| Business Optimization workflow (top-down strategic) | Phase 12 |
| KPI Assistant UI | Phase 12 |
| Slack notifications | Phase 12 |
| **Time Dimension Mapping Wizard** — during onboarding schema inspection (step 2), auto-detect date columns and fragments (year, period, timestamp, etc.) per dialect; propose `display_expr` / `sort_expr` for `TimeDimensionSpec`; user confirms or edits; no developer seed changes required for new clients | Phase 12 |
| **Data Product Schema Sync / Drift Detection** — store `schema_snapshot` + `last_synced_at` on `DataProduct`; "Re-sync" button in Admin Console re-inspects live source, diffs against snapshot, flags affected KPIs, surfaces reconciliation UI; triggers: manual + pre-assessment auto-detect; impacted KPI SQL flagged before next assessment runs | Infra A5 |
| Platform Admin & Client Onboarding (4-step guided flow) | Infra A2 |
| Usage monitoring (events, quotas, alerts) | Infra A3 |
| Admin Console — Workflow history, error log, token cost, registry editor, LLM config | Infra A5 |
| ~~Registry client-isolation enforcement~~ | ✅ Infra A4 — complete (per-request refresh, strict client_id filter, reload endpoint, health dashboard) |
| ~~Connection Profiles backend storage + credential encryption~~ | ✅ Infra B — complete |
| ~~Authentication (Supabase Auth)~~ | ✅ Infra B — complete (dual-mode login + JWT middleware) |
| Azure OpenAI provider + LLM audit export | Infra B2 |
| **Database-level multi-tenant isolation** — Supabase RLS policies on all registry tables; `get_by_client(client_id)` on all providers; DGA `validate_data_access()` real enforcement (replaces always-true stub) | **Infra B3** (pre-first paying customer) |

### Known tech debt (remaining)

| Item | Notes |
|------|-------|
| `situations` table partially redundant with `kpi_assessments` | Deprecation deferred — used by VA pipeline. Consolidate in Phase 11A. (11A shipped; consolidation still pending.) |
| ~~`kpisScanned={14}` hardcoded in `DecisionStudio.tsx`~~ | ✅ Wired in Phase 11C |
| ~~Separate `OpportunitySignal` / `Situation` models~~ | ✅ Unified in Phase 11C |
| `run_enterprise_assessment.py` has no scheduler | CLI only — scheduler deferred |
| ~~SA/PCA/DPA agents cache registry data at startup~~ | ✅ **Resolved May 2026 (Infra A4-a Approach A)** — per-request refresh added to `detect_situations`, `process_nl_query`, `get_kpi_definitions`, `get_principal_context_by_id`, `get_principal_context`, `get_data_product`, `generate_sql_for_kpi`. Regression test: `tests/unit/test_a9_registry_live_reload.py` (7 tests). Optional Approach B refactor (true per-request locals) deferred. |

---

## Architecture decisions (non-negotiable)

- **SA = sensor** — detects KPI movements, no problem/opportunity labeling
- **DA = analyst + framer** — determines analysis_mode from segment variance structure, not SA. Mixed mode (both problem and opportunity segments present) is the normal enterprise state; pure problem / pure opportunity are edge cases.
- **Unit of decision is the segment, not the KPI headline** — DA's IS/IS NOT produces dimensional coordinates; SF targets solutions at those coordinates; VA validates recovery at segment level before aggregating to KPI
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

**Step 3 — tests: ✅ COMPLETE (May 2026)**
`tests/unit/test_a9_data_governance_wiring.py` — 5 tests, all passing:
1. SA `process_nl_query` raises `RuntimeError` (not `AttributeError`) when DGA not wired
2. SA `process_nl_query` calls `translate_business_terms` when DGA wired
3. DPA `_get_view_name_from_kpi` raises `RuntimeError` when DGA not wired
4. DPA `_get_view_name_from_kpi` resolves view name through DGA when wired
5. DA `plan_deep_analysis` returns `status="error"` with DGA message when not wired

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

#### 11A: KPI Accountability Registry ✅ COMPLETE (May 2026)

**Goal:** Principals own KPIs at the scope of their control. The registry expresses this dimensionally — routing is correct by construction, not patched with filters.

**Delivered:**
- `kpi_accountability` Supabase table + migration; singleton-accountable-per-scope constraint
- `KPIAccountability` Pydantic model + `AccountabilityRole` enum
- `KPIAccountabilityProvider`: asyncpg-backed, strict `client_id` scoping
- REST API: `GET/POST/DELETE /api/v1/accountability/` (list, by-principal, by-KPI)
- Seed data: 19 assignments mapping 15 lubricants KPIs to 4 principals
- `onboard_client.py` step 7 upserts ACCOUNTABILITY when module exports it
- Registry Explorer: read-only Accountability tab (scope badges, role badges)

| Deliverable | Description |
|------------|-------------|
| `KPIAccountability` Pydantic model | ✅ `kpi_id`, `principal_id`, `scope_dimension` (optional), `scope_value` (optional), `role` (accountable/responsible) |
| Supabase migration | ✅ `kpi_accountability` table; max 1 accountable per KPI per scope |
| Seed lubricants data | ✅ 19 assignments mapping 15 lubricants KPIs to 4 principals |
| PIB uses accountability registry | ✅ `_populate_situations` filters assessments to accountable KPIs; fallback to all when no assignments exist |
| SA uses accountability registry | ✅ `detect_situations` loads assignments; `_get_relevant_kpis` restricts KPI scan scope — fewer SQL queries + LLM calls per interactive scan |
| Admin UI — accountability view | ✅ Read-only Accountability tab in Registry Explorer (scope + role badges) |
| Unit tests | ✅ `tests/unit/test_kpi_accountability_wiring.py` — 5 tests (PIB filter, PIB fallback, PIB resilience, SA restrict, SA no-filter) |

#### 11A-ext: Opportunity Framing — SF + VA Agents ✅ COMPLETE (May 2026)

Complementary to Phase 11C unified stream. SF Council Debate and VA lifecycle now handle positive KPI direction (opportunity cards) with appropriate framing — debate personas frame options as "capture and replicate" rather than "fix and recover"; VA trajectory chart and phase lifecycle apply to opportunity solutions with inverted direction logic.

- DA POA: corrected IS/IS NOT framing and SCQA narrative for opportunity cards (positive KPI outperformance)
- SF: opportunity context propagated through council debate; option generation framed for capture/expansion
- VA: opportunity solutions register with baseline, projections, and trajectory tracking — same 5-phase lifecycle

#### 11B: LLM-Assisted Accountability Import ← NEXT

**Goal:** Solve the enterprise cold-start problem — extract KPI accountability from HCM documents rather than requiring manual entry.

**Pattern:** Same as KPI Assistant — LLM suggests, human confirms, registry writes.

| Deliverable | Description |
|------------|-------------|
| `A9_Accountability_Import_Agent` | Accepts HCM document text (job descriptions, OKRs, RACI), extracts accountability statements, maps to KPI registry, returns proposals with confidence scores |
| Admin confirmation UI | Present extracted assignments; accept / adjust / reject before writing to registry |
| Conflict detection | Flag KPI assigned to >3 principals without dimensional scoping |

#### 11C: Unified Situation Stream ✅ COMPLETE (May 2026)

**Goal:** Remove the artificial problem/opportunity split. One stream, direction determines framing.

| Deliverable | Description |
|------------|-------------|
| Single situation grid | ✅ Separate opportunity section removed; one grid sorted by `abs(percent_change)` |
| Direction-agnostic SA | ✅ Unified `situations[]`; `OpportunitySignal` model deprecated |
| `card_type` → `direction` | ✅ Binary problem/opportunity replaced with `up`/`down` direction field |
| Wire `kpi_evaluated_count` | ✅ Hardcoded `kpisScanned={14}` replaced with real count from assessment API |

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

#### 11G: DA Mixed Analysis Mode

**Goal:** Remove the artificial binary problem/opportunity framing. A single DA run surfaces both lagging segments (problem coordinates) and leading segments (opportunity coordinates) in one unified IS/IS NOT exhibit. SA's `direction` field is input signal only — DA determines framing from the segment variance structure it observes.

**Why this matters:** Mixed-signal KPIs — where the aggregate is slightly off-target but contains both outperforming and underperforming segments simultaneously — are the dominant enterprise case, not the edge case. The current binary model forces an artificial choice.

| Deliverable | Description |
|------------|-------------|
| DA `analysis_mode='mixed'` detection | After IS/IS NOT query: if both significant positive and negative segment deltas exist, auto-set `analysis_mode='mixed'`. Thresholds: ≥1 segment with delta > +threshold AND ≥1 segment with delta < -threshold. |
| Mixed IS/IS NOT response model | `KTIsIsNot` extended: `problem_segments` (red, negative delta), `opportunity_segments` (green, positive delta), `mixed_framing: bool` flag on `DeepAnalysisResponse` |
| Mixed SCQA prompt | Narrative frame: "Despite [KPI] being [X% off target], [leading segments] are outperforming — indicating a deployment gap rather than a market constraint. The question is how to replicate the proven mechanics while correcting the lagging segments." |
| `IsIsNotExhibit` mixed render | Single exhibit: problem segments rendered red (existing), opportunity segments rendered green (existing) — no mode switch needed. Header badge: "Mixed Signal — problem + opportunity detected" |
| SF mixed context | SF receives `mixed_framing=True` in DA output; debate personas frame options as "fix-and-replicate" combinations spanning the trade-off space |
| VA mixed tracking | Track aggregate KPI recovery; segment-level breakdown shows problem segment improvement AND opportunity segment maintenance in portfolio view |

**Reference design:** `docs/architecture/da_mixed_analysis_mode.md`

---

#### 11H: DA Statistical Enrichment (Analytical Intelligence Layer 1)

**Goal:** Ground IS/IS NOT findings in statistical evidence. Confidence scores on segment variance replace heuristic `replication_potential` scores. SA threshold breach is flagged as statistically significant or noise before DA runs.

**Why this matters:** A data scientist would ask: is National Auto Parts Chain A's +90bps variance statistically significant, or is it one contract distorting the mean? Is Service Centers' outperformance structural (12-month trend) or seasonal? DA currently reports what the numbers say; it should also say how much to trust them.

| Deliverable | Description |
|------------|-------------|
| Segment effect size | Compute each IS/IS NOT delta as % of total KPI variance (weight-adjusted), not raw delta — surfaces which segments actually drive the headline number |
| Seasonal decomposition | For segments with ≥12 periods of data: decompose into trend + seasonal + residual. Flag if current delta is seasonal (low replication confidence) vs structural (high confidence) |
| Variance significance scoring | Replace heuristic `replication_potential` (0–1) with evidence-based score: `effect_size_pct × trend_stability × data_completeness`. Display as confidence band in UI |
| Outlier detection | Flag segments where delta is >2σ from peer distribution — "This segment is a statistical outlier; interpret with caution" |
| DA context enrichment | Statistical scores injected into SF context: "Service Centers Division: structural trend, 0.92 replication confidence" vs "National Auto Parts Chain A: potential outlier, 0.41 confidence" |

**Prerequisite:** ≥12 months of segment-level data for decomposition. Short-history KPIs get effect size and significance only.

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

## UI Refinement Track (Parallel — no phase number)

**Status:** Active (May 2026)
**Framing:** Continuous, lower-urgency work alongside critical-path phases. Not a blocker for Sep 2026 first pilot. Investor-grade polish targeted for Q4 2026 / Q1 2027.
**Scope:** Full design system pass — semantic CSS variables, extracted shared components, documented tokens.
**Driven by:** Screenshot reviews. Each view gets a recommendations subsection seeded by a review session. Execute against named files and components.

**Constitutional reference:** `docs/architecture/ui_brand_guidelines.md` — Swiss Style monochrome, Satoshi typography, Aperture mark, "Quiet Expert" voice, "the chart is the receipt" UX philosophy. All refinements must respect these.

### Foundation work (do once, benefits every view)

| ID | Workstream | Files | Description |
|---|---|---|---|
| **F1** | Semantic severity tokens | `decision-studio-ui/tailwind.config.js`, `decision-studio-ui/src/index.css` | Replace hardcoded `red-400 / amber-400 / green-400 / emerald-400` with `--color-severity-critical / -warning / -info / -opportunity / -healthy`. KPITile, OpportunityCard, Portfolio, IS/IS NOT bars reuse them. |
| **F2** | Extract shared header | new `decision-studio-ui/src/components/shared/AppHeader.tsx` | Pulls inline header (BrandLogo + Principal selector + Refresh + Settings + status msg) out of `DashboardView.tsx` (lines ~50–95). Reused by Portfolio, CouncilDebate, ExecutiveBriefing, DeepFocusView. |
| **F3** | Extract summary strip | new `decision-studio-ui/src/components/shared/SummaryStrip.tsx` | Generalises `COVERAGE / FINDINGS / IMPACT LEVEL` inline section (`DashboardView.tsx` lines ~119–150) into `<SummaryStrip metrics={[…]} />`. Compresses to a single thin status strip per SA Console critique. |
| **F4** | Extract principal selector | new `decision-studio-ui/src/components/shared/PrincipalSelector.tsx` | Inline `<select>` from `DashboardView.tsx` lines ~70–88 becomes a component with persistent "Viewing as: COO" context cue. |
| **F5** | Extract solutions strip | new `decision-studio-ui/src/components/shared/SolutionsProgressBar.tsx` | Inline portfolio strip (`DashboardView.tsx` lines ~160–193) becomes a component. Visual weight to `failed_count`; segmented bar pattern instead of comma-list. |
| **F6** | Executive number formatter | new `decision-studio-ui/src/utils/formatExecutive.ts` | `-189051582 → -$189.1M`, `+150369071.62 → +$150.4M`. Applies everywhere raw integers currently render (IS/IS NOT bars, Replication Targets, KPI tile absolute values). |
| **F7** | Cost of Inaction component reuse | existing `CostOfInactionBanner` | Currently rendered only on Executive Briefing. Surface on DeepFocusView at top, next to/below Situation Summary. |
| **F8** | Document the design system | new `decision-studio-ui/DESIGN_SYSTEM.md` | One page: severity tokens, typography scale, spacing scale, component library index. Linked from `docs/architecture/ui_brand_guidelines.md`. |

### View-by-view recommendations

Format per view: priority-ordered table with file/component path and effort sizing (S = ≤2h, M = 2–6h, L = 6h+).

---

#### View: SA Console Dashboard
**Screenshot review:** 2026-05-16
**Primary files:** `decision-studio-ui/src/components/views/DashboardView.tsx`, `decision-studio-ui/src/components/dashboard/KPITile.tsx`

| # | Recommendation | File / component | Effort |
|---|---|---|---|
| 1 | Lead-finding hero treatment — top KPI renders at 2× width with "why it matters" framing; rest as denser secondary grid | `DashboardView.tsx` Priority Briefings + new `<HeroBriefing>` | L |
| 2 | Compress three-up summary to single status strip: `9 KPIs · 9 findings (6 critical, 3 info) · Lead: Net Revenue · Last scan: 2m ago` | `DashboardView.tsx` lines 119–150 → `<SummaryStrip>` (F3) | M |
| 3 | "What now?" action layer — every `KPITile` gets visible-on-hover actions (`Analyze`, `Send briefing`, `Delegate`); page-level CTA `Send PIB email to Rachel` | `KPITile.tsx`, `DashboardView.tsx` | M |
| 4 | Severity treatment is doubled (border-left + red value + badge) — keep border-left only | `KPITile.tsx` | S |
| 5 | "INFORMATION" yellow too prominent for benign findings — switch to green or drop badge when trend is favourable | `KPITile.tsx` severity color logic | S |
| 6 | Sparklines decorative at current size — either 2× larger with baseline reference, or remove | `KPITile.tsx` sparkline section | S |
| 7 | Add temporal grounding — replace `YEAR OVER YEAR` with `YTD 2026 vs YTD 2025` | `KPITile.tsx` comparison label | S |
| 8 | 3-column grid breaks at scale — group by business domain (Revenue / Cost / Profitability / Operations) with collapsible sections | `DashboardView.tsx` Priority Briefings | L |
| 9 | Healthy KPIs invisible — collapsed footer "X KPIs within normal range — expand to view" | `DashboardView.tsx` | S |
| 10 | Principal context not reinforced visually — persistent "Viewing as COO — operational lens" badge; KPI ordering by COO relevance | `PrincipalSelector.tsx` (F4), KPI sort logic | M |
| 11 | `Solutions in Progress` failed-count needs visual weight (red), not comma-list | `SolutionsProgressBar.tsx` (F5) | S |
| 12 | `Scan Now` paired with `Last scanned: X minutes ago` | `AppHeader.tsx` (F2) | S |
| 13 | Card vertical rhythm — stack KPI value / percentage tighter | `KPITile.tsx` | S |
| 14 | Unclear icon top-right (between Scan Complete and Settings) — needs tooltip or removal | `AppHeader.tsx` (F2) | S |

---

#### View: DeepFocusView (Deep Analysis)
**Screenshot review:** 2026-05-16
**Primary files:** `decision-studio-ui/src/components/views/DeepFocusView.tsx` and child components (Situation Summary, SCQA Root Cause, IS/IS NOT Analysis, Replication Targets, Market Intelligence, Action Center / Refinement Chat)

| # | Recommendation | File / component | Effort |
|---|---|---|---|
| 1 | Lead with the **Answer**, not the Situation. Render Answer (BLUF) at top of SCQA section in largest type; collapse Situation/Complication/Question behind `Show reasoning` | Root Cause Analysis component | M |
| 2 | Drop the "Question" panel (SCQA Question is analyst tool, not deliverable) — or fold into Complication italics | Root Cause Analysis component | S |
| 3 | Promote Replication Targets above-the-fold or pair side-by-side with IS/IS NOT (problem + closeable upside in one eye-scan) | `DeepFocusView.tsx` layout reorder | M |
| 4 | **"Source: llm_knowledge" is a CFO-trust killer.** Rewrite to `Source: Analyst synthesis (Claude Sonnet 4.6) · No live citation` when MA fell back to LLM-only mode. When Perplexity ran, show real citations with URLs and pull date. | `MarketIntelligence` card + `a9_market_analysis_agent.py` source attribution | M |
| 5 | Format all numbers via F6 executive formatter — `-189,051,582 → -$189.1M`, `+150,369,071.62 → +$150.4M` | IS/IS NOT bars, Replication Targets, Control Group (F6) | S |
| 6 | IS/IS NOT bars don't scale with values (B2B `-$79.4M` and DIFM `-$42.4M` look near-equal) — bar width proportional to absolute value | IS/IS NOT visualization component | M |
| 7 | DIY Retail green bar visually under-weighted — bolder green / dedicated treatment so the one positive finding pops | IS/IS NOT visualization | S |
| 8 | `Gross Profit decreased by 47.0% vs baseline (threshold=red)` — strip the `(threshold=red)` debug string; replace with `47.0% below baseline — critical threshold breached` | Situation Summary component | S |
| 9 | Yellow alert icon contradicts CRITICAL red badge — align severity icon color to badge | Situation Summary component | S |
| 10 | IS/IS NOT collapsed rows lack preview — show worst-row inline on header: `CUSTOMER_NAME -$186.9M (worst: Acme Corp -$45.2M) ▾` | IS/IS NOT category header | M |
| 11 | Action Center occupies ~30% of viewport always-visible — collapse to slim right-edge tab by default; expand on user action | `DeepFocusView.tsx` layout + Action Center wrapper | M |
| 12 | "ACTION CENTER" name + "1/6" + "Bain" badge all unexplained — rename to "Refinement Conversation"; show 6-step progress labels; label persona explicitly (`Persona: Bain — Hypothesis-Driven`) | Action Center header | S |
| 13 | Suggested response chips truncated mid-sentence — full text on hover, 2-line wrap, or truncation at less critical point | Refinement Chat suggested-responses component | S |
| 14 | Refinement Chat doesn't anchor to scroll position — highlight relevant section as chat advances through `_get_topic_sequence(da_output)` topics | Refinement Chat + scroll observer | L |
| 15 | Two-column layout above the fold: SCQA on left, IS/IS NOT on right; Replication Targets in a row with Situation Summary | `DeepFocusView.tsx` layout | L |
| 16 | `DETECTED 2:12:33 PM` missing date + data freshness (`data as of YTD 2026 vs YTD 2025`) | Header / metadata strip | S |
| 17 | No save / share / export affordance on the page — add action bar: `Send analysis`, `Export as PDF` (link to existing `/report/:situationId`), `Save as briefing draft` | `DeepFocusView.tsx` page-level toolbar | M |
| 18 | Cost of Inaction is missing — surface `CostOfInactionBanner` at top, next to/below Situation Summary | (F7) | S |
| 19 | `100% potential` badge undefined — tooltip: "This segment alone could close the gap" or "This segment is performing at 100% of its own target" | Replication Targets badge | S |
| 20 | Control Group nesting unclear — add intro sentence: `Control Group: segments performing at or near target — used to isolate factors driving the variance.` | Replication Targets section | S |
| 21 | Section title icons (microscope, chart) add no information — drop or replace with thin accent line per Swiss Style guidelines | All section headers | S |

---

---

#### View: Council Selection (Action Center → Assemble Council step)
**Screenshot review:** 2026-05-16
**Primary files:** Action Center container (in `DeepFocusView.tsx`), `AssembleCouncil` component or equivalent (see `decision-studio-ui/src/components/council/` if it exists), persona/firm registry

| # | Recommendation | File / component | Effort |
|---|---|---|---|
| 1 | AI RECOMMENDATION and Presets sections appear to compete — make relationship explicit: `AI recommends: MBB Strategy Council (4 firms below)` rather than two parallel choices | AssembleCouncil header logic | S |
| 2 | Two "GENERATE SOLUTIONS" buttons with identical labels — differentiate (`Use this recommendation` vs `Generate Solutions`) or remove the top pill | AssembleCouncil header + footer CTA | S |
| 3 | Councilors are firms not personas — add one-line value prop per councilor: `McKinsey & Company — Strategic / hypothesis-driven (MECE)`, etc. | Councilor card component | M |
| 4 | No explanation of WHY these four — add rationale string: `Recommended because Gross Profit Variance involves margin compression + e-commerce competitive dynamics + multi-segment underperformance — requires strategic, operational, technology, and risk lenses.` | AssembleCouncil + SF recommendation engine | M |
| 5 | "Source: llm_knowledge" persists on Market Intelligence cards (4 visible) — same fix as DeepFocusView rec #4 | `MarketIntelligence` source attribution | M (shared) |
| 6 | "Internal" label vs "Hybrid Council" button — confusing pairing. Refactor to proper segmented control with equal visual weight: `[ Internal \| Hybrid ]` | AssembleCouncil mode toggle | S |
| 7 | "Custom" tab undefined — add tooltip: `Custom: Pick individual firms and personas to build your own council.` | Custom tab | S |
| 8 | No cost or time preview before Generate Solutions — add: `MBB Strategy Council — 4 voices, ~3 min, ~$0.80 in compute` | AssembleCouncil footer CTA area | S |
| 9 | No diversity guardrail — AI recommended 4 large multinationals; should enforce perspective diversity (strategic / operational / industry / internal). Optional: `Diversity score: 7/10 — all external firms, consider adding internal CFO voice` | SF council recommendation logic | L |
| 10 | Generic person icons everywhere — distinctive marks per firm or per persona type (chess = strategy, shield = risk, circuit = tech) | Councilor card icon | S |
| 11 | No handoff messaging on Generate Solutions — add: `Generate Solutions will take ~3 minutes. You'll see the live debate in the Council Debate view.` | AssembleCouncil footer CTA | S |
| 12 | Right panel overflows (visible scrollbar) — expand panel temporarily during council selection OR move to modal / full-screen step | DeepFocusView Action Center container | M |
| 13 | Inconsistent purple usage — AI RECOMMENDATION purple ≠ Generate Solutions purple ≠ Bain green badge from Refinement step. Apply F1 semantic tokens (`--color-ai-action`, `--color-active-persona`) | AssembleCouncil + F1 | S |
| 14 | Missing "Why this council?" tooltip per councilor — click-to-expand: `McKinsey selected because the problem involves strategic margin compression with multi-segment dynamics — MECE framework and segmented analysis are well-suited.` | Councilor card hover state | M |

---

---

#### View: Council Debate (Stage 3 — Synthesis & Trade-Off Analysis)
**Screenshot review:** 2026-05-16
**URL:** `/debate/:situationId`
**Primary files:** `decision-studio-ui/src/pages/CouncilDebatePage.tsx`, solution card component, stage progress component

**⚠ Functional bug (not a UX item — flagged separately):** Stage 1 (Hypothesis) and Stage 2 (Cross-Review) narratives are not rendering. All three progress bars show complete with checkmarks, but only Stage 3 content displays. Either Stage 3 render is replacing prior stages (should be additive/scrollable), or Stage 1/2 content isn't being persisted to the page state, or fast debate mode is skipping the persisted Stage 1/2 narratives. Investigate `CouncilDebatePage.tsx` rendering logic. **The multi-perspective debate is the moat — losing the Stage 1/2 narratives loses the proof of reasoning.**

| # | Recommendation | File / component | Effort |
|---|---|---|---|
| 1 | No recommendation / ranking — three options shown as equals. Add `RECOMMENDED` badge on best impact-to-risk ratio card; or rank 1/2/3 with rationale | Solution card + SF synthesis output | M |
| 2 | Bar colors don't reflect value (Cost 5.5 and Cost 8.2 are both green) — apply F1 semantic thresholds at 3/6/8 → green/amber/red | Solution card bar component (F1) | S |
| 3 | Cards don't compare visually — eye ping-pongs between separate bars. Add comparison matrix view (one chart, three series per dimension) OR extend bars to common scale across cards | New `<ComparisonMatrix>` component or solution card layout refactor | L |
| 4 | No persona attribution — council vanishes after Stage 3. Add `Advocated by McKinsey` / `Advocated by Deloitte` badge per card. Closes the loop on the council selection investment | Solution card header + SF synthesis output | M |
| 5 | No "Doing nothing" baseline — add Option 0 (status quo) with CoI impact, zero cost, and trajectory risk | Solution grid + SF synthesis output | M |
| 6 | Card titles too long (Card 2 = 17 words) — short name (3-5 words) bold + one-line description pattern | Solution card title structure + SF prompt | M |
| 7 | No drill-down on cards — click → expand or navigate to solution detail (timeline, resources, quick wins) | Solution card click handler + new SolutionDetail view | L |
| 8 | No way to select preferred option on this page — `Select Solution 1` button per card (or radio); decision happens here, not on Executive Briefing | Solution card + state management | M |
| 9 | Scale unanchored — `Impact 7.8/10 — High (target: >6)` tooltip per bar; or threshold lines on bars | Solution card bar component | S |
| 10 | Stage progress bar shows completion only — click each stage to see what it produced (`Stage 1 generated 3 hypotheses in 47s`) | Stage progress component | M |
| 11 | Vast empty space below cards (~70% of viewport unused) — fill with persona contributions, Stage 1/2 narratives (once bug fixed), comparison matrix, council-replay affordance | `CouncilDebatePage.tsx` layout | M |
| 12 | "View Executive Briefing" is the only exit — add `Save for later`, `Regenerate with different council`, `Add custom option`, `Reject all` | Page-level toolbar | M |
| 13 | No timestamp / duration info — `Debate completed: 2 min 47 sec · 2026-05-16 14:30`. Reinforces speed proof point | Header/footer metadata | S |
| 14 | Browser tab title generic — set to `Council Debate — Gross Profit Variance` | `CouncilDebatePage.tsx` document.title or react-helmet | S |

---

---

#### View: Executive Briefing
**Screenshot review:** 2026-05-16
**URL:** `/briefing/:situationId`
**Primary files:** `decision-studio-ui/src/pages/ExecutiveBriefingPage.tsx` (or `Briefing.tsx`), Decision Workspace right panel, Strategic Options comparison table, Option detail cards, Implementation Roadmap component

**Strengths to preserve (so refinements don't regress them):** Recommended Path with full rationale + 4-metric strip + decision owner/deadline (textbook BLUF); Strategic Options comparison table; Arguments For/Against side-by-side; Immediate Actions Required with named owners and week-level deadlines; Implementation Roadmap with 3 phases; Decision Workspace (Ask/Select/Approve) panel; professional disclaimer footer. **This is the strongest page on the platform — critique is incremental, not structural.**

| # | Recommendation | File / component | Effort |
|---|---|---|---|
| 1 | Cost of Inaction is collapsed at the very bottom — should appear **above** the recommendation as the urgency anchor. "Doing nothing costs you $X by Q3 — here's our recommendation." | `ExecutiveBriefingPage.tsx` section order + CoI component | S |
| 2 | Recommended path rationale appears twice (top COUNCIL RECOMMENDATION + "Proceed with:" near Actions) — collapse the second to title + "see top" link, or differentiate (summary vs. detailed) | Briefing template + Proceed-with section | S |
| 3 | Strategic Options table has no Status Quo column — add Option 0 (CoI baseline) with negative ROI, $0 cost, trajectory risk | Strategic Options comparison table | M |
| 4 | Decision Workspace SELECT INITIATIVE is the most important decision on the page but rendered as the smallest control (tiny radio buttons + truncated titles) — expand to full-width initiative cards with full title, ROI band, click-to-select state | Decision Workspace SelectInitiative component | M |
| 5 | "Approve & Track" has no preview / confirmation — clicking permanently registers solution with VA. Add confirm modal: `Approve will register Option A with VA tracking. Baseline: $51.8M. Expected by Q3 2026: +$28.5M to +$45.6M. Decision owner: Finance Leadership. Continue?` | Approve & Track CTA + new confirm modal | M |
| 6 | Supporting Analysis collapsed by default — the whole brand promise is "show your work." Expand most-relevant section based on which initiative is highlighted; at minimum show section previews | Supporting Analysis accordion section | M |
| 7 | Stage 1 (Independent Firm Proposals) is hidden 80% down the page — surface one-line `Generated by: McKinsey + Deloitte + Accenture + KPMG` near top so council investment is reinforced | Briefing header / metadata strip | S |
| 8 | Arguments For/Against bullets are 50-word paragraphs — apply TL;DR pattern: bold lead-in (`Loyalty differential explains B2B contraction`) + supporting detail expands on click | Arguments component + SF prompt for bullet structure | M |
| 9 | REVERSIBILITY metric undefined — add tooltip: `How easily can this be unwound if it underperforms? High = pilot structure with exit clauses; Low = capital commitments or structural changes.` | Option metric strip | S |
| 10 | Implementation Roadmap phases use relative weeks ("Week 1-2") not actual dates — generate from `decision_owner_deadline + offset` to anchor to real action windows (`May 19 – May 30`) | Implementation Roadmap component + backend date computation | S |
| 11 | Phase 2 has a duplicate task ("Execute primary intervention…" one-liner + "Execute a 90-day operational pivot…" paragraph are the same task) — fix roadmap data model to one source-of-truth task with optional expansion | Roadmap data model + Phase rendering | M |
| 12 | Decision Workspace initiative titles truncated mid-word — wrap to 2 lines or use canonical short names (paired with Council Debate rec #6) | Decision Workspace SelectInitiative + SF prompt | S |
| 13 | Page header title truncated ("Decision Briefing: Year-to-date Gross Profit has...") — use canonical pattern `Gross Profit Variance — Executive Briefing` | Briefing header title | S |
| 14 | Risk & Considerations sections all use the same yellow warning icon — distinct icons: shield (Risk), lightbulb (Considerations), clock (Cost of Inaction) | Risk & Considerations section icons | S |
| 15 | Pre-populated Workspace questions ("What is the primary root cause?", "Which option has fastest time to impact?") — should answer in-context using briefing data, not route away (the briefing already knows the answers) | Decision Workspace question handler | M |
| 16 | Footer disclaimer should carry audit metadata: `Model: Claude Sonnet 4.6 · Data: BigQuery YTD 2026 vs YTD 2025 · Council: McKinsey, Deloitte, Accenture, KPMG · Generated: 2026-05-16 14:30 PM · Confidence: High`. Critical for CISO/compliance review | Briefing footer | S |
| 17 | No "regenerate" or "challenge" affordance — add `Refine this briefing` link near title for re-run with different council / different criteria | Briefing header toolbar | M |

---

---

#### View: Solutions Portfolio (list view)
**Screenshot review:** 2026-05-16
**Primary files:** `decision-studio-ui/src/components/PortfolioDashboard.tsx` (or equivalent), Portfolio table component, summary cards section

**Strengths to preserve:** Four-card summary header with semantic color (green Total ROI / green Validated / amber Partial / red Failed); Phase + Verdict double-badge pattern; info banner for pending measurements.

| # | Recommendation | File / component | Effort |
|---|---|---|---|
| 1 | KPI names show raw programmatic IDs title-cased (`Gross Margin Pct`, `Sga Expense`, `Cogs`, `B2b Revenue`) — map to KPI registry display names (`Gross Margin %`, `SG&A Expense`, `COGS`, `B2B Revenue`) | Portfolio table KPI column + KPI registry display name resolver | S |
| 2 | Three "13% of tracked solutions" strings are coincidental — add absolute counts: `1 of 8 solutions` | Summary card subtitle | S |
| 3 | "Lars Mikkelsen" subtitle lacks context — `Portfolio for: Lars Mikkelsen — CFO, Lubricants` | Header subtitle | S |
| 4 | Last row data inconsistency — solution title appears in KPI column instead of KPI name (likely missing display name on just-approved items) | Portfolio table data transform | M |
| 5 | `$-250K` format wrong — should be `-$250K` (sign before currency symbol). Apply F6 executive formatter | Impact column (F6) | S |
| 6 | No filtering or sorting controls — add filter by Phase / Verdict / KPI domain / date range; sortable columns | Portfolio table toolbar + table component | M |
| 7 | "PHASE" vs "VERDICT" column headers unexplained — add tooltips: `Phase = lifecycle stage (Approved → Implementing → Live → Measuring → Complete); Verdict = outcome assessment (Measuring / Validated / Partial / Failed)` | Column header tooltips | S |
| 8 | Eye icon on right is small and unlabeled — expand to `View` button or make row click-target with hover state | Portfolio table row action | S |
| 9 | Total count missing — `5 of 8 solutions in measurement window` rather than just `5` | Info banner | S |
| 10 | No portfolio-level grand totals — add bottom row: total realized impact (Live+Complete), % of expected captured, average attribution confidence | Portfolio table footer | M |
| 11 | Refresh button has no last-refreshed timestamp — pair with `Last refreshed: X minutes ago` (same as SA Console pattern) | Header refresh control | S |

---

#### View: Solution Detail (drill-down)
**Screenshot review:** 2026-05-16
**Primary files:** Solution Detail panel/page (likely in `PortfolioDashboard.tsx` or separate `SolutionDetail.tsx`), TrajectoryChart component, stat card row, RecordMeasurement form

**Strengths to preserve:** Three big stat cards (Realized Recovery / Avoided Loss / vs Plan) with semantic color; "View Original Decision Briefing" audit-trail link; three-line trajectory chart (Inaction / Expected / Actual) — DiD attribution made visible; preliminary-attribution warning is professional.

| # | Recommendation | File / component | Effort |
|---|---|---|---|
| 1 | EXPECTED IMPACT shows `+$280K to +$120K` — upper bound first. Fix to `+$120K to +$280K` (smaller bound first) | Solution Detail header metric row | S |
| 2 | Raw KPI ID `lub_sga_expense` exposed as subtitle — show display name or hide entirely | Solution Detail subtitle | S |
| 3 | Title is the full solution description (long) — pattern: short canonical name as H1, full description as supporting paragraph below | Solution Detail title | M |
| 4 | Y-axis labels raw integers (`4103000.0, 3944000.0`) — apply F6 formatter (`$4.1M, $3.9M`) | TrajectoryChart Y-axis tick formatter (F6) | S |
| 5 | X-axis labels `M0, M1, M2` lack real dates — use hybrid format `M2 (Mar 20)` or just real dates anchored to approval date | TrajectoryChart X-axis tick formatter | S |
| 6 | "eval" annotation at M2 vertical line is undefined — replace with labeled annotation: `Current evaluation checkpoint — Mar 20, 2026` | TrajectoryChart annotation | S |
| 7 | Both "Complete" and "Partial" badges at top-right confusing — composite badge `Complete · Partial (under target)` or stack with labels (`Phase:` / `Verdict:`) | Solution Detail header badges | S |
| 8 | Chart has no Y-axis title — add `SG&A Expense ($)` axis label | TrajectoryChart Y-axis title | S |
| 9 | Cost KPI direction counterintuitive — actual going DOWN is GOOD but visually reads as decline. Add `Lower is better (cost KPI)` annotation or invert chart for cost KPIs | TrajectoryChart cost-KPI rendering | M |
| 10 | RECORD KPI MEASUREMENT is single-field — for audit integrity add date picker (default today), source (auto/manual), notes field, confirmation before recording | RecordMeasurement form | M |
| 11 | "VS PLAN: $-190K · Behind expected ($3.5M target)" — relationship unclear. Expand: `Currently at $3.69M (M2), expected to be at $3.5M by M2 — $190K behind expected impact.` | VS PLAN stat card subtitle | S |
| 12 | "AVOIDED LOSS +$190K" needs DiD tooltip — `Without this solution, SG&A would have grown to $3.9M at M2 (inaction trajectory). By acting, we're at $3.7M — $190K of additional cost avoided.` | AVOIDED LOSS stat card tooltip | S |
| 13 | No "next checkpoint" indicator — `Next measurement: Apr 20, 2026 — owner: Finance Controller` | Solution Detail header / metadata strip | S |
| 14 | No actions on the page — add toolbar: `Mark Live`, `Update Expected Impact`, `Add Checkpoint`, `Escalate to Decision Owner` | Solution Detail action toolbar | M |
| 15 | No portfolio peer comparison — `$90K realized is below the portfolio median of $145K` | Solution Detail stat card subtitle or new comparison strip | M |
| 16 | Three trajectory lines (Inaction red-dotted / Expected gray / Actual white) lack visual differentiation — thicker lines, distinct stroke patterns, optional shaded confidence bands | TrajectoryChart line rendering | M |
| 17 | No milestone annotations on chart — when did implementation start, intermediate checkpoints, etc. Add vertical lines with labels | TrajectoryChart annotations | M |

---

---

#### View: Login
**Screenshot review:** 2026-05-16
**URL:** `decision-studios.com/login`
**Primary files:** `decision-studio-ui/src/pages/Login.tsx`, client selector, identity selector
**Cross-reference:** Infra B (Customer Infrastructure — Authentication) — the real auth work is already scoped there as a pre-Sep 2026 pilot blocker. This view section captures the UX evolution; Infra B captures the backend.

**Strengths to preserve (do NOT throw away the demo path):** Client + Identity selector is an excellent sales-demo and sandbox login flow. Circular avatars + role pattern reads enterprise-quality. Footer disclaimer is professional. Swiss Style execution is on-brand. Keep this design as the *demo mode* alongside production auth.

**Approach: additive evolution, not replacement.**
```
/login                  → Production login (email + password, SSO buttons)
/login?mode=demo        → Current identity-selector (sales demos + sandbox, gated by tenant demo_enabled flag)
/login?token=<JWT>      → Magic link path (PIB delegation flow — already partially implemented)
```

| # | Recommendation | File / component / scope | Effort |
|---|---|---|---|
| 1 | **Build real auth via Supabase Auth** (Infra B — pre-Sep 2026 blocker) — email + password as default for non-SSO customers | `Login.tsx` + Supabase Auth wiring + backend session middleware | L |
| 2 | Identity selection from a public list is an **information disclosure** in production — exposes org chart. Replace default with email field; demo path retained at `/login?mode=demo` | `Login.tsx` production mode | M |
| 3 | Client dropdown exposes the tenant list — replace with tenant inference from email domain (`sarah@apex.com` → Apex Lubricants) OR tenant-specific subdomain (`apex.decision-studios.com`) | `Login.tsx` + tenant resolver + Infra B | M |
| 4 | "Sign In via SSO" CTA is misleading (flow is just identity selection, not actual SSO) — rename to `Continue` or `Sign In` until SSO providers are wired | `Login.tsx` CTA copy | S |
| 5 | Add SSO providers — Microsoft + Google as first wave; Okta + SAML for Phase 11+ enterprise tier | `Login.tsx` SSO button row + Supabase Auth providers | L |
| 6 | Gate demo mode by tenant flag (`demo_enabled: true`) — production tenants can't be selected via `?mode=demo` | `Login.tsx` demo gate + registry tenant schema | S |
| 7 | Magic link flow for delegation (`?token=X`) — already used by PIB delegation pattern; formalize as official login mode with its own UX path | `Login.tsx` token mode + existing DelegatePage handler | M |
| 8 | Add Forgot password / Reset / Resend invite links — standard auth UI table stakes once real auth is in place | `Login.tsx` + password reset flow + email templates | M |
| 9 | MFA opt-in at tenant level — TOTP (Authy / Google Authenticator) first; SMS later if customer requested. Configurable per tenant in registry | MFA enrollment flow + tenant settings + Supabase Auth | L |
| 10 | Session management — device list, "sign out everywhere," last sign-in timestamp shown after login. For CFO-level financial access, this is expected | Account / Settings page + Supabase session API | M |
| 11 | Audit log for every sign-in attempt (success + failure) to `usage_events` table per Infra A3 — important for SOC 2 readiness | Backend auth hook + Infra A3 | S |
| 12 | New device detection — "We noticed a sign-in from a new device — confirm via email" pattern | Auth flow + email templates | M |
| 13 | When in demo mode, both paths visible in same panel — primary: email/password form; secondary: `Or try the demo` link revealing the identity selector | `Login.tsx` demo mode rendering | S |
| 14 | Tenant-specific subdomain support (later) — `apex.decision-studios.com` for white-labeled enterprise tier | DNS + tenant-aware routing + Phase 11+ scope | L |

---

---

#### View: Context Explorer (aka Registry Explorer)
**Screenshot review:** 2026-05-16
**URL:** `decision-studios.com/context`
**Primary files:** `decision-studio-ui/src/pages/ContextExplorer.tsx` (or `RegistryExplorer.tsx`), four-column registry layout, registry API endpoints under `/api/v1/registry/`

**🔴 CRITICAL BUG (tracked separately):** Client isolation is not enforced — Context Explorer leaks principals / data products / KPIs across tenants. **See Infra A4 → "Registry Client-Isolation Enforcement" section for the full bug spec, audit plan, and regression test.** This UI Refinement entry assumes that bug is fixed; the UX recommendations below presume tenant-scoped data.

**Strengths to preserve:** 4-column layout (Principals / Processes / KPIs / Data Products) is conceptually right for navigation. Counts at top of each column. Clean Swiss Style. Primary + subtitle text pattern.

| # | Recommendation | File / component / scope | Effort |
|---|---|---|---|
| 1 | "Navigate relationships" subtitle promises cross-column navigation but UI delivers 4 independent lists — clicking a Principal should highlight related Processes / KPIs / Data Products | ContextExplorer.tsx state + column rendering | L |
| 2 | Naming inconsistency: "Context Explorer" (URL + title) vs "Registry Explorer" (CLAUDE.md and rest of codebase) — pick one and apply everywhere, or document the distinction if they're meant to be different views | Page title + CLAUDE.md + breadcrumbs | S |
| 3 | Display name quality issues across Data Products (`Dp Fi 20250516 001`, `temp_discovery_ProfitCenters_view`, `dp_lubricants_sqlserver_LubricantsStarSchemaView_vi...`) — raw IDs and debug artifacts leaking through. Apply display name resolution from registry | Data Products column + display name resolver | M |
| 4 | KPI display name hygiene — `Employee Expense` and `Employee Expense Other` side-by-side; needs registry-side cleanup | KPI registry seed / data + display name resolver | M |
| 5 | Business Processes show duplicates (`Market Share Analysis` appears twice rows 9 & 13) — disambiguate by domain or deduplicate | Business Processes column + registry data | S |
| 6 | Multiple Principals with identical role labels (3× "Chief Financial Officer") — once client filtering fixed, still need scope disambiguation: `Sarah Chen — Chief Financial Officer · Lubricants Business` or `North America CFO` | Principal subtitle format | S |
| 7 | No filter or search — 106 processes and 65 KPIs cannot be scroll-navigated. Each column needs search by name + filter by category + sort | Per-column toolbar | M |
| 8 | No CRUD affordances visible — CLAUDE.md says Registry Explorer supports "form-based editing." Either add inline actions / right-click menu / click-to-edit, or clarify this is the navigation view distinct from edit views | Column row actions + per-entity edit modal/page | L |
| 9 | No relationship counts per item — Principal row should say `Rachel Kim — Chief Operating Officer · owns 12 KPIs · 8 processes · 2 data products` (the whole "navigate relationships" point) | Principal row + relationship count API | M |
| 10 | "Unknown" subtitle on records with incomplete metadata (`temp_discovery_ProfitCenters_view`, `dp_lubricants_sqlserver_...`) — backfill metadata, hide incomplete records, or render "Unknown" more discreetly | Subtitle rendering + registry data backfill | S |
| 11 | No grouping within columns — 106 processes scroll as flat list. Group by domain with collapsible section headers | Column rendering + group-by logic | M |
| 12 | No active / hover state on column items — click should select; selection drives the other 3 columns' filter state. Currently the columns are functionally inert | Column item interaction + cross-column state | M |
| 13 | No total scope summary at top — once filtering fixed, show: `For client: Lubricants Business — 4 principals · 39 processes · 15 KPIs · 2 data products` | Page header summary strip | S |
| 14 | Subtitles inconsistent across columns (role vs category vs source system) — standardize semantic or differentiate more clearly | Per-column subtitle pattern | S |
| 15 | KPI column subtitle shows "Finance" on every visible row — verify category field is being read and isn't always defaulting | KPI subtitle rendering + registry data | S |
| 16 | Truncated Data Product names cut mid-word — apply CSS `text-overflow: ellipsis` at word boundary or show full name on hover | Data Product row CSS | S |

---

---

#### View: Company Profile
**Screenshot review:** 2026-05-16
**Primary files:** `decision-studio-ui/src/pages/CompanyProfile.tsx`, Industry Benchmarks sidebar component, per-section card components

**Strengths to preserve:** Sectioned layout (Identity / Scale / Strategy / Governance). Locked Client ID with `stamps every KPI · principal · data product` explanation — brilliant transparency. Required-field markers + max limits (Regions 5, Strategic Priorities 3). Right sidebar reserved for Industry Benchmarks. Helpful placeholders.

| # | Recommendation | File / component / scope | Effort |
|---|---|---|---|
| 1 | Per-section Save buttons create state uncertainty — pick one pattern: single global Save + section "modified" indicators OR per-section Save with clear post-save state (`Saved 3s ago`) and disabled until next edit | CompanyProfile.tsx save state pattern | M |
| 2 | Industry Benchmarks sidebar is empty — populate live as Industry/Sub-industry fields are filled (`Specialty Chemicals → 12 reference companies, median revenue $450M, median GM 28%`); placeholder until then | Industry Benchmarks sidebar + benchmarks API | M |
| 3 | No completeness indicator — add progress bar (`Profile: 3 of 8 sections complete`) + per-section status chips (`Complete` / `Partial` / `Not started`) | Page header progress strip + per-section badges | S |
| 4 | No per-field "why this matters" tooltips — add `?` icon per field explaining downstream impact on KPI suggestions / SA thresholds / monitoring sensitivity / onboarding path | Per-field tooltip component | M |
| 5 | No examples or "Suggest with AI" affordance on Strategic Priorities — show 2-3 examples and offer AI suggestion based on Industry + Sub-industry context | Strategic Priorities input + KPI Assistant integration | M |
| 6 | All sections visible at once = long scroll — collapsible accordion (complete sections collapsed, incomplete expanded) OR step-by-step wizard | Page layout pattern | M |
| 7 | No "Save All" / "Submit Profile" terminal action — add page-level CTA that confirms profile complete and triggers KPI suggestion refresh + benchmark recompute | Page footer + downstream refresh hooks | M |
| 8 | No live preview of impact — as Industry selected, Benchmarks panel populates; as Revenue Range set, suggested SA thresholds appear; as Strategic Priorities added, related business processes light up in registry preview | Live-update sidebar + cross-component reactivity | L |
| 9 | Locked Client ID needs migration path note — add `Changing this requires support — contact your Decision Studio team` | Client ID locked helper text | S |
| 10 | Industry / Sub-industry fields unclear if list or free text — convert to typeahead dropdown from standard taxonomy (NAICS or industry-specific reference list) for benchmarking integrity | Industry/Sub-industry inputs + reference taxonomy data | M |
| 11 | Regions input is plain text with no validation — convert to tag input with autocomplete from standard region list (`North America`, `EMEA`, `APAC`, `LATAM`, `MEA`) to prevent inconsistent values breaking benchmarking joins | Regions input component | S |
| 12 | No "Last updated" / "Updated by" metadata — show per-section audit info (`Last updated by Lars Mikkelsen on 2026-05-10`) | Per-section footer metadata + audit fields | S |
| 13 | Right panel cramped if populated — widen when content present, OR push benchmarks inline next to relevant fields (revenue range shows industry median beside it) | Industry Benchmarks sidebar layout | M |
| 14 | Go-to-Market checkbox group needs `Select all that apply` helper text — combinations like B2B + Channel/Partner are common but not obvious | Go-to-Market section helper text | S |
| 15 | Operating Model dropdown — no preview of options. Pre-load dropdown so users can scan choices (`Centralized`, `Decentralized`, `Matrix`, `Holding Company`) before clicking | Operating Model select component | S |
| 16 | No skip / draft state for new users — add `Save as draft` / `Skip for now` per section so onboarding flow doesn't require completing every field upfront | Per-section action buttons + draft state | M |
| 17 | Visual rhythm — thick card padding, lots of empty space. Denser layout without losing readability | Card spacing tokens | S |
| 18 | Save button has no disabled state when no changes — desaturate until user has modified something in that section | Save button state logic | S |
| 19 | No keyboard shortcuts — Cmd+S saves current section | Page-level keyboard handler | S |

---

---

#### View: Settings → Business Process Registry (Master-Detail Editor)
**Screenshot review:** 2026-05-16
**Primary files:** `decision-studio-ui/src/pages/Settings.tsx` or `RegistryEditor.tsx`, Business Process master-detail components, tab navigation component
**Note:** Similar editor patterns likely exist for other registry tabs (Data Products / KPIs / Principals / Business Glossary). Recommendations below mostly generalize across all six tabs.

**Strengths to preserve:** Two-column master-detail layout (correct CRUD pattern). Tab navigation across all registry types. Workspace + Client badges in header (real improvement over Context Explorer's missing tenant indicator). Search box. View JSON affordance. Count visible (39). Metadata (JSON) field allows extensibility.

| # | Recommendation | File / component / scope | Effort |
|---|---|---|---|
| 1 | Table Name column truncated to 4-5 chars while ID column shows full text — invert priority: hide ID column (already in form on right), OR stack ID+Name vertically, OR resize columns to 60/40 in favor of Name | Master table column layout | S |
| 2 | "Workspace lubricants" + "Client lubricants" badges visually identical — clarify distinction in tooltips, or consolidate to single badge if always equal | Header badges | S |
| 3 | No domain grouping / filter — IDs already prefix by domain (`finance_`, `strategy_`, etc.). Add collapsible domain sections OR filter chips OR Domain column | Master table grouping/filter | M |
| 4 | No unsaved-changes guard — editing fields then clicking another row silently discards changes. Add `You have unsaved changes — Save / Discard?` modal | Master selection + dirty state tracking | M |
| 5 | Delete button has no confirmation AND no cascade impact warning — surface references: `This process is referenced by 3 KPIs and 2 principals. Proceed?` | Delete confirmation modal + relationship query | M |
| 6 | ID field editable on existing records — changing an ID after creation breaks references. Read-only when editing existing; editable only on new (with auto-suggest from Name) | ID field state logic | S |
| 7 | Owner Role is free text — convert to controlled dropdown sourced from Principal registry roles (prevents `CFO` vs `Chief Financial Officer` vs `cfo` drift) | Owner Role field + Principal registry integration | M |
| 8 | Domain is free text — convert to controlled dropdown with "Add new domain" affordance | Domain field + reference list | S |
| 9 | Tags as comma-separated string is brittle — convert to proper tag chip input with autocomplete from existing tags across registry, dedup, consistent casing | Tags field component | M |
| 10 | Metadata (JSON) field has no schema hint — add example placeholder (`// Optional: schedule_cadence, accountability_principals, custom_tags`) OR build structured editor for known optional fields | Metadata field UX | M |
| 11 | Domain may drift from ID prefix (`finance_x` with Domain `Operations` is inconsistent) — auto-derive Domain from ID prefix at create time, or lock them together | ID + Domain coupling logic | S |
| 12 | No "Used by" / Relationships panel — show which KPIs / Principals / Data Products reference this Business Process. Same value Context Explorer was trying to deliver but even more relevant on edit screen | Relationships panel below form + relationship query API | L |
| 13 | No "Last modified" / "Modified by" audit info — show `Last updated by Lars Mikkelsen on 2026-05-12 14:30` on every record (same as Company Profile #12) | Form footer metadata + audit fields | S |
| 14 | No "Duplicate" action — clone existing process as starting point for new one. Add `Duplicate` alongside Save / Delete | Form action buttons | S |
| 15 | Search box scope unclear — show what's being matched (`Search in: [Name] [ID] [Description] [Tags]`) | Search input + filter chips | S |
| 16 | No bulk operations — can't select multiple to delete or reassign. Not urgent at 39; painful at 200+ | Master table multi-select + bulk action toolbar | L |
| 17 | Tab navigation has no count badges — show `Business Processes (39)`, `Data Products (6)`, `KPIs (15)`, etc. for at-a-glance scope | Settings tab labels | S |
| 18 | Empty state missing when nothing selected — right pane should show `Select a business process to edit, or create a new one →` | Detail form empty state | S |
| 19 | Selected row highlight too subtle — stronger visual cue (left border, distinct background) | Master table row selected state | S |
| 20 | Truncated IDs in table need tooltip on hover (`operations_order_to_cash_cycle_opt...` → full text) | Master table cell tooltip | S |
| 21 | Save button has no disabled state when no changes — desaturate until user modifies something (same as Company Profile #18) | Save button state logic | S |
| 22 | No per-field tooltips explaining downstream impact (what does Domain do? What does Owner Role mean for routing?) | Per-field tooltip component | M |
| 23 | View JSON button competes visually with Save/Delete — move to separate visual group (top-right of form, or overflow menu) so it doesn't read as primary action | Form action layout | S |

**Cross-tab applicability:** Recommendations #1, #3, #4, #5, #6, #7, #8, #9, #10, #13, #14, #15, #16, #17, #19, #20, #21, #22 likely apply to all six Settings tabs (Company Profile / Business Processes / Data Products / KPIs / Principals / Business Glossary). When executing, build shared components (`RegistryMasterDetail`, `RegistryTagsInput`, `RegistryDeleteConfirm`, etc.) rather than per-tab implementations.

---

---

#### View: Settings → Data Products tab
**Screenshot review:** 2026-05-16
**Primary files:** Same Settings master-detail framework as Business Processes tab; Data Products specific components, `+ Onboard Data Product` wizard entry point

**Cross-reference:** Most recommendations from the Business Processes tab entry above apply identically here (truncation, unsaved-changes guard, delete cascade warning, audit metadata, tooltips, save button state, etc.). Shared components (`RegistryMasterDetail`, `RegistryTagsInput`, etc.) fix both tabs at once. This entry captures only what's **distinctive** to Data Products.

**Diagnostic finding (important for the Infra A4 bug investigation):**
Settings → Data Products shows **3 records** (all Lubricants-tagged) while Context Explorer shows **6 including Hess**. Same registry, different endpoints. **This narrows the bug location:**
- ✅ Supabase provider methods (`get_all_data_products`) ARE filtering by `client_id` correctly (Settings proves this)
- 🔴 The Context Explorer API endpoint is NOT passing `client_id` to the provider
- **Fix scope shrinks** — the bug is at the Context Explorer endpoint/route handler or UI fetch layer, not in the providers

| # | Recommendation | File / component / scope | Effort |
|---|---|---|---|
| 1 | `temp_discovery` record is a discovery artifact leaking into production data — investigate why discovery artifacts persist as Data Products. Either clean up Supabase data, or filter `temp_` prefix from production views (cosmetic fix; root cause better) | Data Product registry data + discovery workflow cleanup | M |
| 2 | `+ Onboard Data Product` CTA — wizard handoff undefined. Add effort signal (`Onboard Data Product (8 steps, ~10 min)`) or confirmation modal explaining what the wizard covers | Data Products tab CTA | S |
| 3 | No Connection Health column — Data Products' #1 diagnostic question is "is this connected?". Add per-row indicator (green/amber/red) based on last connection test + last successful query timestamp + source system badge | Master table column + connection probe API | M |
| 4 | No "Test Connection" action from list view — one-click connection test per row (fastest path to diagnose issues like the Snowflake MFA failure) | Master table row action + connection probe | S |
| 5 | No filter by source_system — at scale, filter chips for backend type (DuckDB / BigQuery / Snowflake / SQL Server / Postgres) | Master table filter toolbar | S |
| 6 | No "primary" / "default" indicator — if a tenant has multiple Data Products, which serves the principals' default analysis? Add `PRIMARY` badge or sort-first convention | Data Product schema + master table rendering | S |
| 7 | `dp_lubricants_sqlserver` shown as apparently working but known production-broken (Infra A4 SQL Server Dockerfile gap) — Settings should reflect deployment status: `Status: Dev only — production blocked` | Connection health rendering + deployment env detection | M |
| 8 | ID + Name redundancy more glaring than Business Processes (`dp_lubricants_sqlserver` ID = nearly identical Name) — drop Name column OR enforce human-readable display names (`Lubricants — SQL Server`) | Master table column logic + display name policy | S |
| 9 | Empty state ("Select an item or create new.") is well-handled here — **backport this pattern to the Business Processes tab** (recommendation #18 in that entry) | Cross-tab consistency | (covered by BP rec #18) |

---

---

#### View: Settings → KPIs tab
**Screenshot review:** 2026-05-16
**Primary files:** Same Settings master-detail framework, plus KPI-specific threshold editor, comparison-type dropdown, data product binding fields

**Cross-reference:** Most BP Registry recommendations apply (truncation, unsaved-changes guard, delete cascade, audit metadata, tooltips, save state, etc.). This entry captures KPI-specific issues — most importantly, the Threshold Editor redesign.

**Strengths to preserve:** Comparison dropdown with `+ Add Threshold` extensibility. Data Product ID + View Name binding (essential). Unit field captured. Metadata JSON has real semantic content (`line`, `altitude`). 15 KPIs visible = correctly tenant-filtered.

**HEADLINE RECOMMENDATION: Threshold Editor redesign — convert numeric inputs to semantic sliders (#1 below).** This single change is a Decision Studio differentiator — most BI tools don't have intuitive threshold UX. User explicitly requested it.

| # | Recommendation | File / component / scope | Effort |
|---|---|---|---|
| 1 | **Threshold Editor → semantic slider redesign** — replace bare 4-number inputs with horizontal slider per comparison type: color-coded segments (green/amber/red), 2-3 draggable handles with numeric labels, unit suffix from KPI Unit field (`5%` / `$5M`), direction indicator ("Higher is better" / "Lower is better"), optional current-value marker showing where SA last evaluated. Manual `[edit]` link reveals 4-input mode for power users. | New `<ThresholdSlider>` component + KPI editor integration | L |
| 2 | Threshold column labels missing — until slider redesign ships, at minimum add header labels (Green / Amber / Red / Critical) above the 4 numeric inputs | Threshold input layout | S |
| 3 | Unit field captured but not applied — Unit `$` should flow to Threshold display (`$5M` not `5`), Description, KPI tile rendering, briefing numbers. Overlaps with F6 executive formatter | Unit-aware formatting throughout KPI rendering | M |
| 4 | Inverse logic not visible — Net Revenue `+5` is good; SG&A Expense `+5` is bad. Add `inverse_logic` toggle in form OR auto-derive from Domain/KPI nature. Slider design (#1) makes this implicit through left/right green positioning | KPI schema + form + threshold rendering | M |
| 5 | Data Product ID + View Name are free text — convert to linked dropdowns: Data Product ID selects from Data Products registry; View Name selects from the chosen data product's discovered view list. Free text → typos → silent KPI failures | Data Product ID + View Name fields | M |
| 6 | No "Preview value" / "Test SQL" action — add `Test query` button that runs the base SQL and shows current value + position relative to thresholds. Single-click data quality check | Form action toolbar + KPI value endpoint | M |
| 7 | Comparison dropdown options unclear — `yoy`, `qoq` visible; pre-load dropdown with full set (`mtd`, `ytd`, `rolling_12m`, `prior_period`, `custom`) so users can scan | Comparison-type dropdown | S |
| 8 | Threshold rows can drop to zero with no warning — add empty state: `No thresholds defined — KPI will not generate situation cards. Add at least one threshold.` | Threshold section empty state | S |
| 9 | Metadata JSON has real semantic content (`line`, `altitude`) but no schema hint — document known fields with autocomplete | Metadata field UX + schema documentation | M |
| 10 | No "Used by" relationships panel — which Principals / Business Processes reference this KPI? Especially critical since KPIs are at the center of every analysis | Relationships panel + relationship query API | M |
| 11 | **Data hygiene issue — all Lubricants KPIs prefix with `lub_` (CLAUDE.md anti-pattern).** Per [CLAUDE.md](CLAUDE.md) Registry Record Identity 🔴 rule: `id` should be `net_revenue`, `client_id` should be `lubricants`. The composite PK `(client_id, id)` handles uniqueness. Tenant-prefixed IDs are explicitly called out as a sign client_id isn't being used as the tenant key. **Migration task: strip tenant prefixes from all KPI IDs across the registry.** Not pure UI work — needs a data migration script + cascade update of every reference. | KPI registry data migration + reference updates | L |

---

---

#### View: Settings → Principals tab
**Screenshot review:** 2026-05-16
**Primary files:** Same Settings master-detail framework, plus Principal-specific fields (Decision Style, Business Processes / KPIs / Responsibilities multi-value, Metadata preferences)

**Cross-reference:** Most BP Registry recommendations apply. This entry captures Principal-specific issues.

**Strengths to preserve:** 4 principals correctly tenant-filtered. **IDs follow CLAUDE.md convention** (`coo_001`, `cfo_001` — role-based, NOT tenant-prefixed — one of the few tabs that gets this right). Metadata JSON carries real semantic preferences (`kpi_line_preference`, `kpi_altitude_preference`) that affect briefing framing. Description gives rich operational context.

| # | Recommendation | File / component / scope | Effort |
|---|---|---|---|
| 1 | Four comma-separated fields (Business Processes / KPIs / Responsibilities / Decision Style) — most painful instance of this antipattern. Convert: BP + KPIs to multi-select picker from respective registries with chips showing human names; Decision Style to controlled-vocabulary multi-select; Responsibilities to chip-style free text | Principal form fields + shared registry-picker component | L |
| 2 | KPIs field empty for Rachel Kim despite SA generating 9 findings for her — registry doesn't reflect operational reality. Mapping happens through BP indirection or role-based hardcoding. Surfaces the **Phase 11A (KPI Accountability Registry)** gap. Until 11A ships, show a banner: `KPI ownership currently derived from Business Processes — explicit accountability mapping coming in Phase 11A.` | Principal form + KPI Accountability registry integration | L (covered by Phase 11A) |
| 3 | Decision Style undocumented but high-leverage (drives SF consulting persona framing per CLAUDE.md) — add tooltip: `Analytical → MECE/quantified; Visionary → strategic/long-horizon; Pragmatic → operational/quick-win.` Plus controlled vocabulary | Decision Style field + persona documentation | S |
| 4 | No avatar / visual identity in form header — Login page shows circular initials avatars (`RK`, `MW`, `SC`, `DT`); Settings page has none. Backport initials avatar to form header; optional photo upload | Principal form header + Avatar component | S |
| 5 | Description doesn't anchor to structured KPIs/processes — Rachel's description mentions operational areas that map to specific KPIs but KPIs field is empty. AI-suggest button: `Suggest KPIs and Processes from description` (single-click to apply) | Description field action + KPI Assistant integration | M |
| 6 | No team / org structure — who reports to whom is critical for PIB delegation (which already exists). Add `Reports to` field + derived `Direct reports`. Enables proper delegation suggestions | Principal schema + delegation suggestion logic | M |
| 7 | No active / inactive status — if a principal leaves, delete breaks historical audit trails. Add `status: active / inactive / archived` with handling: historical decisions remain attributed, new decisions can't route to inactive principals. UI: collapsed `Inactive (1)` section in master table | Principal schema + status field + master table grouping | M |
| 8 | Title is free text — `Chief Operating Officer` today, `COO` tomorrow. Controlled vocabulary (standard exec titles) with `Add custom title` affordance | Title field component | S |
| 9 | No scope / accountability indicator — Phase 11A territory. Currently no field expresses that Rachel owns enterprise-scope KPIs while Marcus owns LOB-scope. Critical for correct PIB routing | Phase 11A KPI Accountability Registry | (covered by Phase 11A) |
| 10 | Metadata JSON `kpi_line_preference` / `kpi_altitude_preference` are powerful but undocumented — same fix as KPI tab metadata: document known preference fields with autocomplete | Metadata field UX + preference schema docs | M |
| 11 | No "test as this principal" affordance — currently requires log out / log in to switch identity. Add `View dashboard as Rachel Kim` link with audit logging. Accelerates both demos and debugging | Principal form action + impersonation flow + audit log | M |

---

#### Data Product Onboarding — moved to dedicated section
**The Data Product Onboarding workflow chooser + 7-step wizard entries have been moved out of this UI Refinement Track** into a dedicated `## Data Onboarding Refinement (Post-MVP)` section below. Reason: the scope (cross-functional UI + backend + security + templates), the dependencies (Infra B Connection Profiles backend storage), and the timing (post-pilot) all exceed what fits a "single-view UI polish" track. The Data Onboarding section captures workstreams, prerequisites, and execution sequencing properly.

---

#### Future entries (placeholders — pending screenshots from user)

- **DelegatePage** — TBD
- **Business Glossary tab** — TBD (likely shares patterns with Business Processes tab above)

### Execution order

| Order | Item | Why this order |
|---|---|---|
| 1 | F1 (semantic tokens) + F6 (number formatter) | Every other refinement depends on tokens and formatted numbers |
| 2 | F2 + F3 + F4 + F5 (component extractions) | One pass through `DashboardView.tsx` — fewer merge conflicts than per-view edits |
| 3 | SA Console rec #1, #2, #3 (hero, summary strip, action layer) | Highest visible value; informs hero pattern for other views |
| 4 | DeepFocusView rec #1, #4, #11 (Answer-first, fix MA source attribution, collapse Action Center) | The three changes that most affect trust + readability |
| 5 | F8 (DESIGN_SYSTEM.md) | Written after extractions so it documents reality, not aspiration |
| 6 | SA Console hierarchy + scale items (#4–10) | Once hero pattern is set, the rest follows the same vocabulary |
| 7 | DeepFocusView hierarchy + layout items (#2, #3, #5–10, #15) | Same — apply consistent vocabulary across views |
| 8 | Other views as screenshots arrive | Each new screenshot review appends a subsection; work in priority order within that view |
| 9 | F7 (CoI on DeepFocusView) + all S-effort polish items, batched | Small visual nits |

### Tracking

When a recommendation ships, mark it ✅ in this table with the commit hash. When a recommendation is rejected after consideration, mark it ⊘ with a one-line reason. Do not delete rejected items — the rationale is the value.

---

## Data Onboarding Refinement (Post-MVP)

**Status:** Scoped May 2026 from screenshot reviews. **Deferred until after first pilot signed (target Sep 2026).**
**Scope:** Cross-functional refinement of the Data Product Onboarding wizard — spans UI, backend, security, templates, and post-pilot learnings.

**Why a separate section (not in UI Refinement Track):**
1. **Cross-functional** — recommendations span UI polish AND backend storage AND security architecture AND template library. UI Track is scoped to single-view polish.
2. **Critical dependencies** — blocks on Infra B (Connection Profiles backend storage with credential encryption + per-client tenancy). Cannot ship UI improvements that assume backend storage before the backend exists.
3. **Post-pilot timing** — wizard changes are destabilising. The current wizard works in demos and the seeded Lubricants/Hess flows. Refining before first pilot risks regressing the proof-of-concept. First-pilot feedback also reshapes priorities (which steps are friction in real onboarding vs. demo).
4. **Wizard-as-product** — onboarding is a multi-step product in its own right, not a screen. Separate section lets it have proper workstreams, prerequisites, and execution order.

---

### Prerequisites

| # | Prerequisite | Status | Why it blocks |
|---|---|---|---|
| 1 | **Infra B → Connection Profiles backend storage + encryption + per-client tenancy** | Not started | Wizard cannot store credentials securely until backend exists. Currently browser localStorage = 🔴 security gap. See Infra B sub-section. |
| 2 | First pilot signed and onboarded | Target Sep 2026 | Real-customer feedback reshapes which wizard steps are friction. Don't optimise for demo flows; optimise for real onboarding. |
| 3 | 2–3 onboarded data products across different industries | Post-pilot | Required to inform the Templates Library workstream — can't build templates from one example. |
| 4 | Wizard step count reconciliation | Quick fix | CLAUDE.md says 8 steps; UI shows 7. Reconcile docs before refinement. |

---

### Workstream 1: Workflow Chooser (entry screen)

**Screenshot review:** 2026-05-16
**Primary files:** `decision-studio-ui/src/pages/DataProductOnboarding.tsx`, workflow chooser component
**Strengths to preserve:** Two-card fork pattern. Meaningful iconography. Quick Tip pattern. Swiss Style layout.

| # | Recommendation | File / component / scope | Effort |
|---|---|---|---|
| 1 | No effort / scope signaling — add step count + time estimate to each card: `New Data Product · ~10 min · 7 steps` / `Extend Existing · ~3 min · 3 steps` | Workflow card subtitle | S |
| 2 | No visual map of wizard ahead — add `<WizardProgress>` strip below cards showing all 7 steps. Reduces dropout | New `<WizardProgress>` component (shared with Workstream 2) | M |
| 3 | Vast empty space above/below cards — fill with workflow preview, recent/in-progress onboardings (resume affordance), template chooser, backend selector | Page layout | M |
| 4 | Backend selection missing from this screen — add chip selector (`BigQuery / Snowflake / DuckDB / SQL Server / Postgres`) on `New Data Product` card | Workflow card form | M |
| 5 | No "Continue Last Onboarding" — detect Supabase draft state, offer `Resume: "Insurance Premium Analytics" (paused at step 4) →` | Draft state detection + resume banner | M (gated on Infra B draft storage) |
| 6 | Quick Tip generic — make data-aware (`You have 3 data products. Extending is usually faster than creating new.`) | Quick Tip + tenant context | S |
| 7 | "Data Product" abstract — add `What's a data product?` expandable with concrete example | Inline explainer | S |
| 8 | No explicit "Back to Settings" — pair back arrow with text `← Back to Data Products` | Page header back affordance | S |
| 9 | No permissions indication — add (if applicable): `Only platform admins can create new data products.` | Permission gate | S |
| 10 | Card backgrounds nearly identical — slight blue/green tint to help eye land | Workflow card background variants | S |
| 11 | CTA hover state — verify distinctive feedback for primary fork action | CTA styling | S |
| 12 | Keyboard navigation — add `Press 1 or 2 to select` hint | Keyboard handler + hint | S |
| 13 | "Quick Tip" header informal — Swiss Style suggests `When to extend` or `Recommended approach` | Quick Tip header copy | S |

---

### Workstream 2: Wizard Foundation (cross-cutting all 7 steps)

This workstream builds the shared scaffolding every step depends on. Doing it once benefits the whole wizard.

| # | Recommendation | File / component / scope | Effort |
|---|---|---|---|
| 1 | **Per-step validation framework** — every step validates before advancing (Step 1 = test connection, Step 2 = verify schema non-empty, Step 6 = run KPI SQL, Step 7 = dry-run registration) | New `<StepValidation>` framework + per-step probes | L |
| 2 | **Save Draft / Resume state** — backend-persisted wizard state (current step, partial inputs, last action timestamp). Every `Continue →` paired with quiet `Save & Exit` | Supabase `onboarding_drafts` table + draft state hook + per-step footer | L (gated on Infra B) |
| 3 | **Sidebar step time estimates** — `Connection Setup (~1 min)`, `Schema Discovery (~3 min)`, etc. Calibrate from telemetry once available | Wizard sidebar step metadata | S |
| 4 | **Sidebar step click behavior** — previous steps clickable (re-edit), current highlighted, future locked with cursor change | Sidebar click handler + visual state | S |
| 5 | **Keyboard navigation** — Cmd+Enter advance, Cmd+S save draft, Esc with confirm-discard | Wizard-level keyboard handler | M |
| 6 | **Cancel onboarding with confirm** — replace ambiguous back arrow with explicit `← Cancel onboarding` (`Discard progress? You can resume later from Settings → Data Products`) | Wizard header back affordance + confirm modal | S |
| 7 | **Workflow Log redesign** — currently stuck at bottom of sidebar, will grow with progress. Options: inline next to current step, slide-out panel, fixed bottom of viewport with timestamps + step duration | Workflow Log component | M |
| 8 | **`<WizardProgress>` component** (shared with Workstream 1) — single source of truth for step labels, status, and navigation | New shared component | M |

---

### Workstream 3: Wizard Step 1 — Connection Setup

**Screenshot review:** 2026-05-16
**Primary files:** Connection Setup step component, source-system adaptive form
**Strengths to preserve:** Adaptive form per backend. Pre-flight Company Profile banner. FK relationships warning. Honest browser-storage disclosure (until backend storage ships).

| # | Recommendation | File / component / scope | Effort |
|---|---|---|---|
| 1 | "Set up Company Profile first" banner is dismissible — convert to status-aware (`✓ Complete` or `⚠ 40% complete — KPI suggestions will be weaker`), not dismissible | Pre-flight banner + profile state hook | S |
| 2 | **"Profiles saved locally in browser" — real product gap.** Until Infra B Connection Profiles backend ships, upgrade warning from blue info to red callout AND disable Save Current button with security-rationale tooltip. After Infra B ships, remove warning entirely | Storage warning component + Save Current button | S (stopgap) |
| 3 | No "Test Connection" before Continue — add ✓/✗ validation gate (Workstream 2 #1 covers framework; this is the per-backend probe) | Test Connection button + per-backend connection probe | M |
| 4 | Source System dropdown hides backends — replace with chip/card selector showing all 5 with required-fields preview per chip | Source System selector | M |
| 5 | "FK relationships will be inferred" lacks context — tooltip explaining when it goes wrong and when to manually review in Schema Discovery | FK warning tooltip | S |
| 6 | "Save Current" button enabled before there's anything to save — disable until validated | Button state logic | S |
| 7 | No "Clone from existing data product" — `Clone connection from: [existing DP dropdown]` saves re-entering Snowflake creds | Connection profiles section | M (gated on Infra B) |
| 8 | "DuckDB (Local)" parenthesized convention inconsistent — apply uniformly across all backends | Source System dropdown labels | S |
| 9 | Schema label DuckDB-specific — adapt to backend (`Schema / Dataset` or fully dynamic) | Schema field label binding | S |
| 10 | Empty connection profiles state could offer import — `Import from .env` or `Paste credentials JSON` for power users | Connection profiles empty state | M (gated on Infra B) |

---

### Workstream 4–9: Wizard Steps 2–7 (TBD — pending screenshot reviews)

Placeholder workstreams for the remaining wizard steps. Each gets its own review session and recommendations table:

- **Workstream 4:** Step 2 — Schema Discovery (TBD)
- **Workstream 5:** Step 3 — Data Product Selection (TBD)
- **Workstream 6:** Step 4 — Metadata Analysis (TBD)
- **Workstream 7:** Step 5 — KPI Definition (TBD)
- **Workstream 8:** Step 6 — Query Validation (TBD)
- **Workstream 9:** Step 7 — Review & Register (TBD)

---

### Workstream 10: Templates Library

**Premise:** Common data product shapes recur across tenants (Lubricants Financials, SaaS Metrics, Insurance Underwriting, Manufacturing Operations). Templates pre-populate KPIs, BP mappings, ownership patterns — converting an 8-step manual flow into a 3-step template-driven flow for known industries. **Biggest lever for second-pilot-and-beyond onboarding velocity.**

**Why post-pilot:** Can't build templates from one example. Need 2–3 onboarded data products across different industries to extract the right abstractions.

| # | Deliverable | Effort |
|---|---|---|
| 1 | `data_product_templates` Supabase table schema (template_id, industry, name, description, schema_pattern, kpi_seed_list, bp_mapping_seed, principal_role_mapping) | M |
| 2 | Template authoring flow (admin tool: export a working data product as a reusable template) | M |
| 3 | Template chooser UI (added to Workflow Chooser entry screen as third option) | M |
| 4 | Template-driven wizard flow (skips Schema Discovery and Metadata Analysis when template pre-fills them; review-and-confirm pattern) | L |
| 5 | Initial template library — at minimum: Financial Analytics (current Lubricants pattern generalized), SaaS Metrics (post first SaaS pilot), Industry-specific patterns as customers onboard | L |
| 6 | Template versioning — when a template improves, existing data products built from it should be flaggable for re-sync | M |

---

### Workstream 11: Backend Hardening (cross-references)

Items already tracked elsewhere that this section depends on or feeds back into:

| Item | Tracked in | Dependency direction |
|---|---|---|
| Connection Profiles backend storage + encryption + per-client tenancy | Infra B (sub-section) | Prerequisite — blocks Workstreams 1 rec #5, 2 rec #2, 3 rec #2/#7/#10 |
| Registry client-isolation enforcement | Infra A4 | Adjacent — same family of multi-tenant correctness work |
| Registry live-reload | Infra A4 | Adjacent — newly onboarded data products should be immediately visible without service restart |
| FK inference accuracy improvements | Post-pilot learnings | Feeds back from real customer schemas |
| Schema discovery dialect handling | Post-pilot learnings | Feeds back from real customer data |
| Source system support matrix expansion (e.g., Databricks SQL, MotherDuck) | Phase 10D / future | Independent — each new backend adds a Source System chip option |

---

### Execution timing and order

**Do NOT pull this work into the pre-Sep 2026 pilot window.** The current wizard works for demos and seeded tenants; refining it pre-pilot risks regressing the proof-of-concept and delays harder pre-pilot work (Infra A4, Infra B auth, multi-tenant isolation).

**Recommended order (post-pilot):**

| Order | Workstream | Rationale |
|---|---|---|
| 1 | Workstream 11 prerequisites — confirm Infra B Connection Profiles backend is live | Everything else assumes secure backend storage |
| 2 | Workstream 2 — Wizard Foundation (shared scaffolding) | Built once, benefits all 7 steps + future steps |
| 3 | Workstream 1 — Workflow Chooser refinements | Entry screen, highest visibility, lowest risk |
| 4 | Workstream 3 — Connection Setup | First step users see; sets the bar for the rest |
| 5 | Workstreams 4–9 — Steps 2–7 | In priority order from post-pilot screenshot reviews |
| 6 | Workstream 10 — Templates Library | Biggest leverage, but requires 2–3 onboarded products as input data |

### Tracking

Same convention as UI Refinement Track. ✅ for shipped (with commit), ⊘ for rejected (with one-line reason). Rejected items stay in the doc — rationale is the value.

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

#### Registry Client-Isolation Enforcement (🔴 CRITICAL — fix before second pilot client)

**Problem:** Context Explorer (`/context`) and likely other registry list endpoints under `/api/v1/registry/*` return records across all tenants instead of strict-filtering by `client_id`. Discovered during 2026-05-16 UI Refinement Track screenshot review: an authenticated session at Lubricants Business shows 16 Principals (mix of Lubricants + Hess + demo), 6 Data Products spanning three tenants (`Lubricants Business Financial Analytics`, `Hess Corporation Financial Analytics`, `Lubricants Business Financial Analytics (Snowflake)`), and 65 KPIs (Lubricants alone seeds ~15).

**Why this is critical:** Violates the [CLAUDE.md](CLAUDE.md) Multi-Tenant Client Isolation 🔴 NON-NEGOTIABLE rule. A real Lubricants user seeing another tenant's principals or data products is a customer-facing data breach. Compounding: every additional pilot client onboarded onto a leaky registry multiplies the breach surface.

**Root cause hypotheses (audit to confirm):**
1. The Context Explorer endpoints may not be reading `client_id` from session/JWT
2. The UI may not be passing `client_id` as a query parameter
3. ~~The Supabase provider methods may use a permissive filter~~ → **RULED OUT by 2026-05-16 diagnostic.** Settings → Data Products tab shows 3 records (Lubricants only) while Context Explorer shows 6 (cross-tenant). Same underlying provider, different endpoint. Therefore the providers ARE filtering correctly — the bug is at the Context Explorer endpoint or UI fetch layer. Audit scope narrows to hypotheses 1 and 2 only.

**Fix plan:**

| Step | Deliverable | Effort |
|------|-------------|--------|
| 1. Audit endpoints | Read every `/api/v1/registry/*` route handler. Confirm each accepts `client_id` query param. Document any that don't. | ~2h |
| 2. Audit UI calls | Read `ContextExplorer.tsx` and any other registry-consuming page. Confirm `client_id` is read from session and passed on every fetch. | ~1h |
| 3. Audit Supabase providers | Read `get_all_*` methods in `src/registry/providers/supabase_*.py`. Confirm STRICT MATCH filter on `client_id` — replace any `is not None` or missing filters. | ~2h |
| 4. Add regression test | New `tests/integration/test_multi_tenant_isolation.py` that authenticates as Lubricants session and asserts every list endpoint returns ONLY Lubricants records. Should fail before fix, pass after. | ~3h |
| 5. Add the same test for delete/update | A Lubricants user must NOT be able to update or delete a Hess record by ID guess. Per CLAUDE.md DELETE endpoints rule. | ~2h |

**Verification:**
- Run regression test against local Supabase with Lubricants + Hess + demo seeded → all endpoints return only the authenticated tenant's records
- Manually log in as Lubricants, navigate to Context Explorer → counts drop to single-tenant scope (`16 → ~4 Principals`, `106 → ~12 Processes`, `65 → ~15 KPIs`, `6 → 2 Data Products`)
- Same check for SA Console, Portfolio, all registry-backed views

**Entry point for new conversation:** Read `decision-studio-ui/src/pages/ContextExplorer.tsx` first to see what API endpoints are called and what query params are passed. Then trace each endpoint to its route handler, then to its provider method. The bug is at one of those three layers.

**Coupling to other work:**
- Same root-cause family as Registry Live-Reload above — both are about registry methods not being correctly tenant-scoped at request time. Consider fixing in one combined pass.
- Blocks second pilot client onboarding (same blocker as Registry Live-Reload).
- Unblocks Context Explorer UI Refinement Track items #6, #9, #13 (which all assume tenant-scoped data).

---

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

### Infra A5: Admin Console — Operational Intelligence

**Goal:** Give a platform admin or IT admin visibility into what the system is doing, what it's costing, and where it's failing — without requiring Railway log access or running scripts. Sequenced after the UI Refinement Track; not a pilot blocker but needed before commercial scale.

**When:** Post-pilot (Q1 2027). Prerequisite: Infra A3 `usage_events` table must exist first.

**Implementation note:** All functions here are simple FastAPI routes + Supabase reads/writes. No agent protocol, no Pydantic A2A models. Data already exists in `_workflow_store`, LLM response `usage` dicts, and the DPA's SQL execution path — this phase is about surfacing it.

---

#### Tier 1 — Operational Confidence (build first)

| Deliverable | Data source | Description |
|------------|-------------|-------------|
| **Workflow Run History** | `_workflow_store` (in-memory, `workflows.py`) | Table of every SA/DA/SF/VA run: status, duration, principal, timestamp, situation ID. Filter by client, date range, workflow type. Click-through shows full result payload. Requires persisting `_workflow_store` to Supabase (currently in-memory only). |
| **Error Log** | `_workflow_store.error` + new `workflow_errors` Supabase table | Agent errors, LLM failures, workflow exceptions with context: which agent, which workflow, which KPI. Shows the last 100 errors; filter by severity. Currently visible only in Railway logs. |
| **Token Usage & Cost Monitor** | `A9_LLM_Response.usage` dict (already present on every LLM call) | Per-client, per-model, per-task-type token breakdown. Running cost estimate using published token pricing. Daily trend sparkline. Requires a fire-and-forget write to `llm_usage_log` Supabase table in `A9_LLM_Service_Agent.generate()` — one line change. Extends Infra A3 `usage_events`. |

#### Tier 2 — Configuration (reduces operational burden)

| Deliverable | Data source | Description |
|------------|-------------|-------------|
| **Registry Editor** | Existing `/api/v1/registry/` endpoints | Full CRUD UI for KPIs, data products, business processes, principals. Currently a placeholder "coming soon" in Admin Console. Routes exist; this is a UI-only build against existing API surface. |
| **LLM Configuration** | New `llm_config` Supabase table per client | Model selection per task type (Stage 1, Synthesis, Narrative); consistency slider mapped to temperature presets (Consistent 0.1 / Balanced 0.3 / Exploratory 0.7). BYOM API key entry field. Reads from `DEFAULT_CLAUDE_TASK_MODELS` and `create_claude_service_for_task()` in `src/llm_services/claude_service.py` — those per-task defaults already exist but are not wired to a UI or env-var override path. |
| **Client/Tenant Management** | Supabase `business_context` + all registry tables | Add/remove clients, view per-client KPI/principal/data product counts, trigger a dry-run SA scan to validate pipeline. Currently requires running seed scripts manually. Extends Infra A2 Platform Admin flow. |

#### Tier 3 — Diagnostic Tools (post-scale)

| Deliverable | Data source | Description |
|------------|-------------|-------------|
| **SQL Monitor** | New `sql_execution_log` Supabase table | Every `execute_sql()` call in DPA logged: data product, query (truncated), execution time, row count, error if any. Useful for debugging KPI data issues without BigQuery/DuckDB console access. |
| **Agent Health** | Orchestrator `list_agents()` + last-activity timestamps | Connected agents, dependency graph status, last successful call per agent. More useful for debugging than for customers; include in platform admin view only. |
| **Assessment Scheduler** | New `assessment_schedules` Supabase table | Configure automated SA runs (daily/weekly/threshold-triggered) per client. Currently only `run_enterprise_assessment.py` CLI. Scheduler calls the existing `/api/v1/assessments/` route on a cron. |
| **Audit Log** | New `audit_events` Supabase table | Who ran what, approved what solution, delegated what briefing, and when. Append-only. Enterprise compliance requirement; collect now, surface later. |

#### Implementation sequencing

1. **Persist `_workflow_store` to Supabase** — prerequisite for Workflow Run History. The in-memory store is lost on every Railway restart; this is the single biggest operational gap.
2. **Add `llm_usage_log` write in `generate()`** — one-line change; unlocks Token Usage Monitor.
3. **Build Registry Editor UI** — highest visible impact; the placeholder is prominent in the demo.
4. **Workflow Run History + Error Log panels** — operational confidence for the first paying customer.
5. **LLM Configuration screen** — needed once BYOM is a selling point.
6. **Tier 3 tools** — build as customer demand surfaces the need.

---

### Infra B: Customer Infrastructure ← BLOCKER for first pilot

**When:** Before first signed pilot (target Sep 2026)

| Deliverable | Priority | Notes |
|------------|----------|-------|
| Authentication | Critical | Supabase Auth — email + password; API keys for programmatic access |
| Multi-tenant isolation | Critical | Per-customer Supabase project; separate registries and KPI sets |
| **Connection Profiles backend storage + tenancy fix (🔴 SECURITY)** | **Critical** | **See dedicated sub-section below — currently browser-local with no tenancy enforcement; credentials in localStorage is a security incident waiting to happen** |
| Customer provisioning script | Critical | Create project → seed registries → configure contracts → send welcome |
| CI/CD pipeline | High | GitHub Actions: test → build → staging → manual promote to production |
| Error monitoring | High | Sentry free tier |
| Staging environment | High | Separate Railway instance |
| Automated backups | High | Nightly registry YAML export |
| Customer data export | Medium | Self-service export for enterprise procurement |

**Cost:** $200–$500/month base + $50–$100/month per customer on paid tiers.

#### Connection Profiles Backend Storage + Tenancy Fix (🔴 SECURITY)

**Problem:** Data Product Wizard's "Connection Profiles" feature currently stores connection configurations (host, port, database, credentials) in **browser localStorage**. Two compounding issues:

1. **Storage location wrong** — already acknowledged in the UI note ("backend storage will be added in a future update")
2. **Tenancy model wrong** — profiles are per-browser, not per-client. A user switching from Lubricants to Hess (same browser) would see the same profile list. There is no `client_id` scope on profiles at all.

**Plus:** credentials in browser localStorage are accessible to any XSS attack and persist in browser backups. For a CFO connecting to production SQL Server, this is a **security incident waiting to happen.**

**Correct model (per-client with admin role-gating):**
- Profiles stored in Supabase `connection_profiles` table
- Scoped to `client_id` (STRICT MATCH filter — same rule as Context Explorer fix)
- Encrypted at rest — passwords / service account JSON encrypted with tenant-specific key
- **Never readable client-side after creation** — connection tests run server-side; UI shows `••••` not the actual credential
- Audit-tracked: `created_by`, `created_at`, `last_used_at`, `last_used_by`
- Role-gated: only platform/client admins can create profiles with production credentials; non-admins can run connection tests against existing profiles but can't add new ones
- Team-shared within a client: colleague at Lubricants can reuse your Snowflake profile

**Fix plan:**

| Step | Deliverable | Effort |
|------|-------------|--------|
| 1. Schema | New Supabase table `connection_profiles` with `client_id`, `source_system`, `name`, `host`, `port`, `database`, `schema`, `credentials_encrypted`, `created_by`, `created_at`, `last_used_at`, `last_used_by`, `is_default` | ~3h |
| 2. Encryption | Per-client encryption key (derived from tenant secret) — credentials encrypted before insert; decryption only available to server-side connection probe | ~6h |
| 3. API endpoints | `POST/GET/DELETE /api/v1/connection-profiles` with `client_id` STRICT MATCH filter | ~4h |
| 4. UI migration | Replace browser localStorage logic in `ConnectionSetup` step with API calls. Connection Profiles section becomes tenant-scoped list. Credential fields render as `••••` on saved profiles. | ~6h |
| 5. Role-gating | Profile create/edit restricted to `role: admin`; non-admins see read-only list + Test Connection action | ~3h |
| 6. Regression test | `tests/integration/test_connection_profile_isolation.py` — Lubricants session cannot read/write Hess profiles | ~3h |
| 7. Migration | One-time script to alert any existing users that browser-stored profiles must be re-entered (cannot migrate ciphertext from localStorage) | ~1h |

**Coupling to other work:**
- Same family as Context Explorer multi-tenant bug (Infra A4 → Registry Client-Isolation Enforcement)
- Same family as KPI ID tenant-prefix anti-pattern (KPI tab rec #11)
- Same family as Auth (above in this Infra B table)
- All four are "missing `client_id` scoping on tenant-shared resources" — could batch into one multi-tenant correctness pass

**Until this ships:** the wizard's "browser local storage" disclosure note should be upgraded from blue info to red warning, and the "Save Current" button should be disabled with a tooltip explaining the risk.

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

---

### Infra B3: Database-Level Multi-Tenant Isolation ← BLOCKER for first paying customer

**When:** Before first signed paying customer. Not required for demos — required before a customer's financial data (KPI results, situation assessments, solution decisions) lives in production alongside another customer's data.

**Why this and not container-per-customer:** Decision Studio does not store customer business data — their EBITDA and revenue figures live in their own Snowflake/BigQuery. Agent9 stores only metadata: KPI definitions, principal profiles, situation cards, approved solutions. RLS on the Supabase registry tables is the correct isolation boundary for this data class. Container isolation is reserved for customers who contractually require on-premise or VPC deployment (Infra C, future).

**Current state:** Application-layer `client_id` filtering is applied per-call in agents and API routes (Infra A4). This is correct but fragile — a bug in any code path can bypass the filter and return another tenant's records. Several such bugs were found and fixed in May 2026. The fix must be architectural, not patch-by-patch.

**The three-layer fix:**

| Layer | What | Why |
|---|---|---|
| **1 — Database RLS** | Supabase Row-Level Security policies on all registry tables | A database bug cannot leak rows to the wrong tenant even if application code omits the filter |
| **2 — Provider isolation** | `get_by_client(client_id)` method on all registry providers | Callers get a single correct-by-construction method instead of `get_all()` + manual filter |
| **3 — DGA enforcement** | `validate_data_access()` real implementation (replaces always-true stub) | DGA becomes the authoritative cross-agent access-control checkpoint |

**Layer 1 — Supabase RLS (highest priority):**

```sql
-- Applied to: kpis, principal_profiles, data_products, business_processes,
--             situations, value_assurance_solutions, kpi_accountability
ALTER TABLE kpis ENABLE ROW LEVEL SECURITY;
CREATE POLICY "client_isolation" ON kpis
  USING (client_id = current_setting('app.client_id', true));
-- Repeat for each table
```

FastAPI middleware sets `app.client_id` at the start of every authenticated request:
```python
await conn.execute(f"SET LOCAL app.client_id = '{client_id}'")
```

This makes application-layer filter bugs non-exploitable — the database returns zero rows rather than another tenant's data.

**Layer 2 — Provider `get_by_client()` method:**

Add to each registry provider (`KPIProvider`, `PrincipalProfileProvider`, `DataProductProvider`, `BusinessProcessProvider`):
```python
def get_by_client(self, client_id: str) -> List[T]:
    return [item for item in self.get_all() if getattr(item, 'client_id', None) == client_id]
```

All agent code that currently does `provider.get_all()` + manual filter loop is migrated to `provider.get_by_client(client_id)`. Reduces per-call filter surface from N call sites to 1 provider method.

**Layer 3 — DGA `validate_data_access()` real enforcement:**

Replace the always-true stub with a real check:
```python
async def validate_data_access(self, principal_id: str, data_product_id: str, client_id: str) -> bool:
    dp = self.data_product_provider.get_by_client(client_id)
    return any(d.id == data_product_id for d in dp)
```

| Deliverable | Description | Effort |
|------------|-------------|--------|
| Supabase migration — RLS on 7 tables | SQL migration file; one policy per table; middleware to set `app.client_id` per request | M (1–2 days) |
| FastAPI middleware — `SET LOCAL app.client_id` | Inject at the start of every authenticated request; verify in integration test | S |
| Provider `get_by_client()` method | Add to 4 providers; update all call sites from `get_all()` + manual filter | M (1 day) |
| DGA `validate_data_access()` — real implementation | Replace always-true stub; wire into DPA before SQL execution | S |
| Regression test suite | `tests/unit/test_client_isolation.py` — verify that a request with `client_id=apex_lubricants` cannot read `client_id=lubricants` KPIs, situations, or data products | M |
| Security one-pager update | Update `docs/strategy/enterprise_security_faq.md` to reflect RLS enforcement as an architectural guarantee | S |

**Trigger:** Build before signing first paying customer. Demo system can run without it. Production system with two real customers cannot.

**Note — what this does NOT solve:** Separate data residency requirements (e.g., EU data must not leave EU) and on-premise deployment mandates. Those are addressed by separate Supabase projects per region (data residency) or a dedicated deployment model (on-premise). Both are future work, not required for the first customer cohort.
