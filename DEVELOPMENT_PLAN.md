# Agent9-HERMES Development Plan

**Created:** 2026-03-14
**Last updated:** 2026-06-08
**Status:** Active

---

## Where We Are — June 2026

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
| KPI Accountability Registry — dimensional ownership, Supabase-backed, REST API, Registry Explorer tab, PIB filtering, SA filter | Production-ready (Phase 11A complete) |
| Unified situation stream — direction field replaces problem/opportunity binary; single grid | Production-ready (Phase 11C) |
| KPI Accountability Interview Agent (Phase 11B) — LLM-driven conversational interview; domain selection; live coverage tracker; Haiku per turn, Sonnet for coverage analysis; `ProposedAssignment` JSON output | Production-ready (Phase 11B complete) |
| DA market signal conflict detection (Phase 11F) — keyword scan of MA signals vs. DA `analysis_mode`; amber conflict badge + confidence % in Root Cause Analysis accordion | Production-ready (Phase 11F complete) |
| DA Mixed Analysis Mode (Phase 11G) — single IS/IS NOT view with problem (red) + opportunity (green) segments; mixed SCQA narrative; HITL resolution panel; SF `analysis_mode` propagation; 22 unit tests | Production-ready (Phase 11G complete) |
| DA Statistical Enrichment — partial (Phase 11H) — `effect_size_pct` (segment share of total gap), `is_outlier` flag (>mean+2σ), outlier segments forced to `control_group`; `replication_potential` now evidence-based; effect-size chips + Outlier badge in UI | Partial — effect size + outlier classification shipped; seasonal decomposition deferred |
| DA Segment Matrix (11I-A/B Addendum) — same-KPI cross-basis Is/Is-Not table (previous-period + plan-variance joined on shared dimensional rows); confirmed/basis_specific/secondary_only/healthy tier per segment; SF scoping prioritises confirmed tiers; replaces contradictory same-KPI problem+opportunity cards; 42 unit tests | Production-ready (Jul 2026) |
| Infra A4 — per-request registry refresh, client_id enforcement on all list endpoints, /admin/registry/reload, connection health dashboard | Production-ready |
| Infra B — connection profiles backend storage + credential encryption (AES-256 at rest) | Production-ready |
| Infra B — Supabase Auth dual-mode login (demo selector + email/password), backend JWT middleware | Production-ready |

### What's not built yet

| Capability | Planned phase |
|-----------|--------------|
| ~~DGA mandatory wiring — test suite (happy path, init failure, view resolution)~~ | ✅ Phase 10B-DGA tests — complete (5 tests, May 2026) |
| KPI trend chart (monthly_values populated for all backends) | Phase 10D |
| ~~KPI accountability registry~~| ✅ Phase 11A — complete (registry, API, PIB filter, SA filter, 5 unit tests) |
| ~~LLM-assisted accountability import from HCM documents~~ | ✅ Phase 11B — complete (Jun 2026) |
| ~~Unified situation stream (merge problem + opportunity)~~ | ✅ Phase 11C — complete |
| Adaptive calibration loop (KPI Assistant → monitoring profiles) | Phase 11D |
| Audio briefings (TTS flash briefing) | Phase 11E |
| ~~DA market signal conflict detection (outperforming / confirming / missing tailwinds)~~ | ✅ Phase 11F — complete (Jun 2026) |
| ~~DA Mixed Analysis Mode — single IS/IS NOT view with both problem segments (red) and opportunity segments (green); mixed SCQA narrative; DA determines framing from segment variance, not SA~~ | ✅ Phase 11G — complete (Jun 2026) |
| DA Statistical Enrichment — effect size relative to segment weight, seasonal decomposition (structural vs cyclical), confidence scoring on IS/IS NOT items; replaces heuristic replication_potential with evidence-based scores (Analytical Intelligence Layer 1) | ⚠️ Phase 11H — partial (Jun 2026): effect size + outlier classification shipped; seasonal decomposition deferred |
| **Advanced Alert Intelligence** — SA: budget/plan variance, projected breach, acceleration, concentration risk; DA: cross-KPI compound patterns (KPI relationship registry); VA: plan trajectory + covenant severity; PIB: alert-type-differentiated briefings | **Phase 11I** — 11I-A/B/C complete (Jul 2026); 11I-D (PIB) remaining |
| **Solution Validity Monitoring** — recurring health checks on active VA solutions: control group stability (V1), market condition drift + strategic alignment drift (V2); health score HEALTHY/WATCH/DEGRADED/INVALID; PIB "Solutions Requiring Attention" + "Pending Confirmations" sections; Portfolio health badge with action protocol | **Phase 11J** |
| **Meridian Flow Systems synthetic dataset** — 79,200-row SAP CO-PA BigQuery dataset; 21 dimensions (including `order_type` at rank #1); FY2024+2025+2026 all 12 months; 4 drift scenarios for 11K–11N unit tests; `scripts/clients/meridian.py` seed script | **Pre-11K** |
| **Data Product Observability** — DGA auto-classifies each data product's refresh cadence (`real_time \| micro_batch \| daily_batch \| weekly_batch \| monthly_close`); continuously confirms cadence; detects pipeline stalls; `pipeline_status` on data product contract | **Phase 11K** |
| **EDA Dimensional Importance Profiling** — DGA runs variance decomposition + concentration ratio + cardinality across all dimensions at onboarding; writes `dimension_importance_profile` JSONB to Supabase; replaces arbitrary 5-dimension cap in background DA; refreshed on schedule matching data product cadence | **Phase 11L** |
| **Change Detection Agent + DA Background Execution Mode** — lightweight statistical agent detects dimensional drift against EDA baseline; triggers background DA on drift or SA breach; DA gains `execution_context: interactive \| scheduled`; scheduled mode removes dimension cap, parallelises all dimensions via `asyncio.gather`; results persisted to `da_background_runs` Supabase table; DA response gains `summary_view` (top 5 dims × 3 rows) for SF and PIB consumption | **Phase 11M** |
| **Event-Driven PIB + SA Card DA State** — PIB fires on DA completion when results are materially different from last run (no cron schedule anywhere); situation cards gain `da_state: not_run \| running \| precomputed \| stale` badge; DeepFocusView gains accordion + importance badges for many-dimension results; on-demand DA always available from SA card regardless of pre-computed state | **Phase 11N** |
| **Business Objectives Registry** — first-class registry entity for declared strategic objectives; objective → KPI driver mapping with weights; `objective_id` on situation cards; SA severity weighting | **Phase 12C** |
| **Strategic Performance Summary** — objective health score (CRITICAL/AT_RISK/ON_TRACK/AHEAD) per assessment run; PIB "Strategic Objectives" section; Portfolio Objectives tab in UI | **Phase 12D** |
| KPI Causal Intelligence — KPI interdependency map in DGA; cross-KPI conflict detection before solution approval; strategic alignment scoring against declared corporate priorities (Analytical Intelligence Layer 2) | Phase 2 (2027) |
| Business Optimization Agent — Phase B: portfolio conflict detection, sequencing, strategic alignment scoring; Phase C: fully autonomous objective pursuit, KPI trajectory forecasting, living Business Plan generation (Analytical Intelligence Layer 3) | Phase 3 (2028) |
| ~~Company Intelligence KPI Template Generator (org-first onboarding with benchmarks)~~ | ✅ Phase 12A — complete (June 2026) |
| **Company Intelligence Principal Templates** — MA agent researches a company's leadership team; admin reviews + commits as `status='template'` principals; email optional at commit; no decision-style inference (admin chooses after seeing SF in action) | **Phase 12E** |
| Org-First Accountability Onboarding (process template → KPI requirements → assign) | Phase 12B |
| Business Optimization workflow (top-down strategic) | Phase 12 |
| KPI Assistant UI | Phase 12 |
| Slack notifications | Phase 12 |
| Executive Briefing Quality + Principal-Adaptive Output | Phase 13 |
| ~~**Uniform Time Dimension Layer**~~ — `TimeDimensionSpec` typed contract on every data product; single `TimeFilter` utility replaces 4 fragmented DPA mechanisms; 78 unit tests; all backends | ✅ Phase 10F — complete (May 2026). **Bug fix Jul 2026:** `*-to-date` previous-period comparisons (YTD/QTD/MTD) were comparing a partial current window against the *full* prior period instead of the same partial window one year back; DA's dimensional previous-query call sites were also double-applying the year shift (2 years back instead of 1). Both fixed in `_fyp_previous`/`_date_previous` and the 6 affected DA call sites — see 11I-A/B Addendum below. |
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
| **SOC 2 Controls Foundation** — audit event log, sign-in audit, principal archive lifecycle, briefing provenance footer, Sentry availability monitoring | **Infra C** (Q4 2026 — before first security review) |

### Known tech debt (remaining)

| Item | Notes |
|------|-------|
| `situations` table partially redundant with `kpi_assessments` | Deprecation deferred — used by VA pipeline. Consolidate in Phase 11A. (11A shipped; consolidation still pending.) |
| ~~`kpisScanned={14}` hardcoded in `DecisionStudio.tsx`~~ | ✅ Wired in Phase 11C |
| ~~Separate `OpportunitySignal` / `Situation` models~~ | ✅ Unified in Phase 11C |
| `run_enterprise_assessment.py` has no scheduler | CLI only — event-driven scheduling designed in Phases 11K–11N; replaces cron with data-change detection |
| ~~SA/PCA/DPA agents cache registry data at startup~~ | ✅ **Resolved May 2026 (Infra A4-a Approach A)** — per-request refresh added to `detect_situations`, `process_nl_query`, `get_kpi_definitions`, `get_principal_context_by_id`, `get_principal_context`, `get_data_product`, `generate_sql_for_kpi`. Regression test: `tests/unit/test_a9_registry_live_reload.py` (7 tests). Optional Approach B refactor (true per-request locals) deferred. |
| Settings tab bar horizontal density | After Phase 12A, the Settings header has 10 horizontal tabs (Company Profile, KPI Intelligence, KPIs, Principals, Data Products, Business Processes, Glossary, Connection Health, Accountability, Assign Ownership). Trigger for left-hand hierarchical nav refactor: section count > 7 (already crossed). Deferred as a standalone PR — owners decide when to schedule. Suggested 5-group taxonomy: Workspace / Data / Decision Registry / People / Governance. |

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

---

### Phase 10F: Uniform Time Dimension Layer ✅ COMPLETE (May 2026)

**Goal:** Replace four fragmented, incompatible time-filtering mechanisms in the DPA with a single typed `TimeFilter` utility. DA dimensional comparison (IS/IS NOT) works correctly for all data sources, including the dominant enterprise pattern of integer fiscal year + period columns.

**Why this was blocking:** DA comparison queries fail silently for any data product that does not use a standard DATE column. This includes every ERP-sourced financial data product (SAP: GJAHR + MONAT, Oracle: accounting periods, Workday: fiscal periods, BigQuery/Snowflake pre-aggregated fact tables). The `transaction_date` default in `_build_bq_dimensional_sql` is backwards — fiscal year + period is the rule for financial KPIs, not the exception.

**Root cause (diagnosed May 2026):** Four mechanisms each assume different things about time columns:

| Mechanism | File | Problem |
|---|---|---|
| `_get_timeframe_condition` | DPA | Generates `t.fiscal_year = {y}` — requires table alias `t`, not present in raw KPI SQL |
| `_build_bq_dimensional_sql._append_date` | DPA | Defaults `date_col = "transaction_date"` — column doesn't exist in ERP-sourced views |
| `_build_sf_dimensional_sql._append_date` | DPA | Same default |
| `_prev_timeframe` | DA | String map returns `None` for unknown timeframes (e.g. "yoy") → no comparison period |

**Design — `TimeDimensionSpec` (extend existing `time_dimensions` contract field):**

```python
# Type A: date — standard DATE/TIMESTAMP column (DuckDB bicycle, NetSuite, transactional tables)
{"type": "date", "column": "posting_date", "primary": True}

# Type B: fiscal_year_period — integer year + period (SAP, Oracle, Workday, BigQuery/Snowflake financial marts)
{"type": "fiscal_year_period", "year_column": "fiscal_year",
 "period_column": "fiscal_period", "period_type": "month", "primary": True}

# Type C: fiscal_year — annual granularity only (KPIs with no sub-year breakdown needed)
{"type": "fiscal_year", "year_column": "fiscal_year", "primary": True}
```

**Design — `TimeFilter` utility (`src/database/time_filter.py`):**

```python
class TimeFilter:
    @staticmethod
    def current_condition(spec: dict, timeframe: str, dialect: str = "bigquery") -> str:
        # Returns SQL WHERE fragment e.g. "fiscal_year = 2026 AND fiscal_period <= 5"
        ...
    @staticmethod
    def previous_condition(spec: dict, timeframe: str, dialect: str = "bigquery") -> str:
        # Returns prior-period equivalent e.g. "fiscal_year = 2025 AND fiscal_period <= 5"
        ...
```

Backend-agnostic for `fiscal_year_period` and `fiscal_year` types (integer comparison, no dialect-specific date arithmetic). Dialect-aware only for `date` type (BigQuery uses backtick quoting, Snowflake/DuckDB use standard quoting).

| Deliverable | Description |
|---|---|
| `TimeDimensionSpec` | Extend `time_dimensions` list in data product contracts with `type` field |
| `TimeFilter` utility | `src/database/time_filter.py` — pure logic, no I/O, backend-agnostic for fiscal types |
| DPA refactor | Replace `_get_timeframe_condition`, `_get_previous_timeframe_condition`, and both `_append_date` functions with `TimeFilter` calls |
| DA refactor | Replace `_prev_timeframe` string map with `TimeFilter.previous_condition` |
| Seed updates | Add `type` field to `time_dimensions` in `scripts/clients/lubricants.py`, `apex_lubricants.py`, `hess.py`, `bicycle.py` |
| Unit tests | `tests/unit/test_time_filter.py` — current/previous conditions for all 3 types × all timeframes × all dialects |

**Prerequisite:** None — independent of Phase 10D (MCP) and 10E (native AI).

**Impact when shipped:** DA IS/IS NOT dimensional comparison works for all clients. SG&A and all other lubricants financial KPIs get real YoY segment breakdowns, not zero-delta artifacts.

---

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

#### 11B: KPI Accountability Onboarding — LLM Interview ✅ COMPLETE (May 2026)

**Goal:** Solve the enterprise cold-start problem — LLM-driven conversational interview populates KPI ownership for a new client using process inheritance as the primary mechanism, with direct assignment as a fallback for KPIs that have no process or span multiple processes.

**Full spec:** `docs/architecture/phase_11b_accountability_onboarding.md`

**Design:** Assignments are always direct rows in `kpi_accountability` (Phase 11A — unchanged). Process ownership is onboarding scaffolding only — the interview uses it to batch-suggest KPIs, the admin confirms each one, and confirmed items write direct rows. No resolver, no inheritance chain, no new tables.

**Scales with revenue model:** No cap on principals. Deeper org coverage is handled via dimensional scoping on direct assignments. Process knowledge accelerates onboarding for large registries without adding runtime complexity.

**No schema migrations required** — `kpi_accountability` from Phase 11A is the only table needed.

| Deliverable | Description |
|------------|-------------|
| `A9_Accountability_Interview_Agent` | 3-phase conversational interview: process-guided suggestion → gap resolution → conflict review. Haiku for chat turns, Sonnet for coverage/conflict analysis. |
| API endpoints | `start`, `chat`, `confirm`, `coverage` (4 endpoints) |
| Admin UI panel | Two-column: chat left, live proposed assignments table right. Per-row confirm/modify/reject. Coverage %, conflict warnings. Bulk approve writes direct rows. |
| `principal_type` field on Principal model | `"individual" \| "team" \| "committee"` — principals can represent teams |
| Unit tests | 8 interview tests + 2 coverage tests — see spec |

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

#### 11I: Advanced Alert Intelligence

**Goal:** Enrich the SA→DA→VA→PIB pipeline with alert patterns that matter to enterprise FP&A but are missing today: budget/plan variance, projected threshold breach, rate-of-change acceleration, concentration risk, cross-KPI compound patterns, and compliance/covenant severity. These are the signals that distinguish a KPI monitoring tool from an early warning system.

**Why this matters:** The four alert types SA handles today (absolute threshold, period-over-period deviation, change-point trend disruption, positive outlier) are all reactive — they fire after the problem is visible. The gaps identified are either forward-looking (projected breach), structural (concentration risk), relational (compound patterns across KPIs), or contextual (actual vs. plan). Adding these shifts Decision Studio from "tells you what happened" to "tells you what is going to happen and what it means in context."

**Architecture principle:** These are additions to the SA detection layer, not rewrites. SA remains a sensor — each new pattern produces a situation card with a new `alert_type` field. DA, VA, and PIB consume that field to adjust framing, not to change pipeline mechanics.

---

##### 11I-A: SA Alert Enrichment — Four New Detection Patterns

**Prerequisites:** Phase 10F (TimeDimensionSpec — uniform time layer) ✅ complete.

###### Pattern 1: Budget / Plan Variance

SA today monitors actuals only. FP&A teams' primary trigger is "are we on plan?" — a distinct question from "are we below threshold?"

| Deliverable | Description |
|---|---|
| `plan_version_value` field on `KPI` registry model and `KPIDefinition` | Optional string — e.g. `"Budget"`, `"Plan"`, `"Forecast"`. When set, SA derives the plan SQL at runtime by substituting the version filter in the existing `sql_query` (`version = 'Actual'` → `version = 'Budget'`). When null, SA skips plan-variance detection for that KPI. No separate SQL field — the FI star schema carries plan data in the same view under a `Version` dimension; DPA already uses this pattern for DA budget vs. actuals comparisons. |
| Supabase migration | Add `plan_version_value TEXT` column to `kpis` table. No `plan_sql_query` column needed. |
| SA `_derive_plan_sql()` | Substitutes the version filter in `sql_query` using the data product schema's `column_aliases.version` and the KPI's `plan_version_value`. Reuses the DPA regex pattern already established at `a9_data_product_agent.py:3384`. |
| SA `_compute_plan_variance()` | When `plan_version_value` is present, derive plan SQL via `_derive_plan_sql()`, execute alongside actuals, compute `actual_vs_plan_pct = (actual - plan) / abs(plan)`. Apply KPI threshold bands. |
| New `alert_type = "plan_variance"` | Situation card carries `alert_type` distinguishing plan miss from threshold breach. `percent_change` = actual vs plan deviation. `plan_value` field on Situation stores the budget reference value. Narrative: "Gross Profit is 14% below plan for YTD 2026." |
| Seed pattern | `scripts/clients/apex_lubricants.py` — add `plan_version_value = "Budget"` to 2–3 representative KPIs (net_revenue, gross_profit, cogs). |
| Unit tests | 3 tests: plan variance fires when actual < plan × threshold; suppressed when plan_version_value is None; direction correctly inverted for cost KPIs (actual > plan = bad). |

###### Pattern 2: Projected Threshold Breach (Forward-Looking)

SA fires when a breach happens. The higher-value signal is "at current trajectory, you will breach in N periods." Shifts the response window from days to weeks.

| Deliverable | Description |
|---|---|
| `SA._project_trend()` | Linear regression over trailing `projection_lookback_periods` (default 6, configurable per KPI in `monitoring_profile`). Returns projected value at horizon `t+projection_horizon` (default 3 periods). |
| Threshold crossing detection | If trend projection crosses the critical or warning threshold within the horizon, fire a `projected_breach` situation. Uses the same threshold bands as the existing breach logic. |
| New `alert_type = "projected_breach"` | Situation card includes: `projected_breach_at_period` (the estimated period when breach occurs), `projection_confidence` (R² of the trend fit — low R² → "trajectory unstable"), `periods_until_breach`. `percent_change` = current gap between projected value and threshold. |
| Suppression rule | Do NOT fire projected_breach if an actual_breach situation already exists for the same KPI in the same assessment run. One or the other, not both. |
| Unit tests | 4 tests: projection fires when trend crosses threshold at t+2; suppressed when actual breach already present; suppressed when R² < 0.4 (noisy data); direction correct for cost KPIs. |

###### Pattern 3: Rate of Change Acceleration

SA's change-point detection identifies when a trend changed. Acceleration detection identifies when the deterioration is speeding up — a distinct and higher-urgency signal.

| Deliverable | Description |
|---|---|
| `SA._compute_acceleration()` | Using the trailing `monthly_values` time series: compute velocity (period-over-period delta) for the last N periods, then compute the change in velocity (second derivative). If the second derivative exceeds `acceleration_threshold` (configurable, default: 2× the rolling std dev of velocity), flag acceleration. |
| New `alert_type = "acceleration"` | Situation card signals that the rate of change is itself increasing. `acceleration_signal: float` = magnitude of second derivative relative to historical baseline. Narrative: "Gross Profit decline is accelerating — the monthly rate of deterioration doubled in the last 3 periods." |
| Prerequisite | `monthly_values` populated from the time-series query. Already required for TrajectoryChart and change-point detection. |
| Unit tests | 3 tests: acceleration fires when second derivative exceeds threshold; not fired on stable decline (first derivative constant); not fired on single-period spike. |

###### Pattern 4: Concentration Risk

Structural risk that builds slowly and never looks alarming in a single period. Boards and audit committees care about this; dashboards never surface it.

| Deliverable | Description |
|---|---|
| `kpi_type` field on `KPIDefinition` | New controlled vocabulary field: `"operational"` (default) \| `"concentration"` \| `"covenant"` \| `"regulatory"`. Concentration KPIs are derived metrics — e.g., "top 3 customer % of revenue" — that measure structural fragility rather than absolute performance. |
| Supabase migration | Add `kpi_type VARCHAR(32) DEFAULT 'operational'` to `kpis` table. |
| SA concentration handling | Concentration KPIs are monitored identically to operational KPIs — the `kpi_type` field drives framing and PIB routing only, not detection logic. Direction is typically `inverse_logic = True` (higher concentration = worse). |
| KPI Assistant pattern | New "Concentration KPI" template in KPI Assistant: suggests SQL pattern (`SUM(CASE WHEN ranked <= 3 THEN revenue END) / SUM(revenue)`) for common concentration metrics (customer, product, channel, region). Reduces cold-start friction for this pattern. |
| Seed examples | Add 1-2 concentration KPIs to Lubricants seed (e.g., customer concentration in B2B segment). |
| Unit tests | 2 tests: concentration KPI fires situation when threshold breached; `inverse_logic = True` is respected. |

---

##### 11I-B: DA Compound & Cross-KPI Patterns

SA monitors KPIs independently. The most actionable enterprise signals often live in the relationship between KPIs — revenue growing while margin declining is more important than either metric alone.

**Approach:** Lightweight KPI relationship registry. No full correlation engine. A declared relationship between two KPIs, with a defined "conflict direction." SA detects the compound pattern; DA deepens it.

| Deliverable | Description |
|---|---|
| `KPIRelationship` Pydantic model | `kpi_id`, `related_kpi_id`, `relationship_type` (`volume_margin` \| `receivables_revenue` \| `cost_revenue` \| `custom`), `conflict_direction` (`diverging` = opposite movements signal a problem; `converging` = same-direction movements signal a problem). |
| `kpi_relationships` Supabase table | Stores declared relationships. Composite PK: `(client_id, kpi_id, related_kpi_id)`. Max 1 relationship per pair per client. |
| `KPIRelationshipProvider` | Supabase-backed, strict `client_id` scoping. Methods: `get_relationships_for_kpi(kpi_id, client_id)`. |
| SA compound detection | After computing situation for `kpi_id`: look up `KPIRelationship`. If related KPI has a recent situation (or a current value in the same assessment run), evaluate whether the directions conflict. If conflict detected: set `compound_alert = True` on the situation card, add `related_kpi_id`, `compound_pattern` (human-readable: "Revenue UP / Margin DOWN — pricing or mix pressure"). |
| DA compound enrichment | DA receives `compound_alert = True` in the situation payload. In `_generate_scqa_summary()`: when compound_alert present, the Complication leads with the compound tension ("Despite revenue growing 8%, gross margin declined 3pp — the divergence suggests a mix shift or pricing compression, not a volume problem"). IS/IS NOT analysis runs for the primary KPI as normal; compound context surfaces in the narrative. |
| Seed patterns | Lubricants: `revenue ↔ gross_margin_pct` (volume_margin, diverging); `b2b_revenue ↔ accounts_receivable_days` (receivables_revenue, diverging). |
| REST API | `GET/POST/DELETE /api/v1/registry/kpi-relationships/` — 3 endpoints. |
| Unit tests | 5 tests: compound_alert fires when both KPIs in opposite directions; suppressed when only one KPI has a situation; DA narrative leads with compound tension when flag present; API returns relationships scoped to client_id; conflict_direction = converging fires when both move in same direction (for receivables + revenue). |

---

##### 11I-C: VA Plan/Budget Tracking + Compliance Severity

VA currently tracks three trajectories: inaction, expected, actual. With plan/budget data from 11I-A, a fourth trajectory becomes available. With `kpi_type` from 11I-A, compliance severity can be surfaced distinctly.

**Plan/Budget as Fourth Trajectory**

| Deliverable | Description |
|---|---|
| Capture `plan_value_at_approval` | When a solution is approved via HITL Gate 2, VA captures the plan/budget value for the target KPI (using `plan_sql_query` if available). Stored in `value_assurance_solutions.plan_value_at_approval`. |
| `plan` trajectory line | TrajectoryChart: optional 4th line (dashed amber) showing the budgeted baseline. Only rendered when `plan_value_at_approval` is present. Label: "Plan / Budget". |
| Verdict dimension: `vs_plan` | New verdict field: `"ahead_of_plan"` \| `"on_plan"` \| `"behind_plan"` \| `"no_plan_data"`. Computed as `(actual - plan) / abs(plan)` at measurement point. Shown as a secondary badge on the Portfolio table (e.g., "Validated · Ahead of Plan"). |
| PIB portfolio summary | Flash briefing: "3 solutions ahead of plan this month, 2 behind." Portfolio section of PIB email adds a plan-performance row. |
| Supabase migration | Add `plan_value_at_approval NUMERIC` to `value_assurance_solutions`. |
| Unit tests | 3 tests: plan trajectory captured at approval; vs_plan verdict computed correctly; portfolio summary counts by plan status. |

**Compliance / Covenant Severity Tier**

| Deliverable | Description |
|---|---|
| SA covenant handling | KPIs with `kpi_type = "covenant"` or `"regulatory"` fire situations at `severity = "critical"` regardless of threshold band — a covenant breach is always critical. Narrative framing changes: "Interest Coverage Ratio breached the debt covenant minimum of 3.0× (currently 2.8×)." |
| `kpi_type` passed to VA | Covenant KPIs are excluded from normal ROI/value-delivery tracking in VA. They're compliance obligations, not value opportunities. VA `register_solution()` rejects `kpi_type = "covenant"` with a clear error message. |
| Unit tests | 2 tests: covenant KPI fires severity=critical regardless of band; VA rejects covenant KPI registration. |

---

##### 11I-A/B Addendum: DA Segment Matrix ✅ COMPLETE (Jul 2026)

**Not originally scoped — emerged from a live production-shaped bug.** A KPI breaching on both the previous-period basis (`threshold_breach`) and the plan-variance basis (`plan_variance`) rendered as two separate, contradictory situation cards — e.g. EBITDA down 70% YoY shown alongside a green "ahead of plan" opportunity card that confusingly displayed the same −70% figure. The two bases are different perspectives on the same KPI and needed reconciling into one shared-frame view, not two rival cards.

| Deliverable | Description |
|---|---|
| SA `_merge_compound_kpi_situations` fold | A `plan_variance` situation for a KPI that already has a `problem` card folds into that card instead of rendering standalone — eliminates the contradictory-card display bug |
| DA segment matrix | When `merged_alert_types` contains both `threshold_breach` and `plan_variance` and budget data is available, DA re-runs the dimensional grouping for the secondary basis and joins `secondary_delta` + `basis_agreement` onto the primary Is/Is-Not table's rows — one shared-frame table, not a second KT pass or LLM narrative fusion |
| `_classify_basis_agreement` | Four-tier per-segment classification: `confirmed` (adverse on both bases — real problem), `basis_specific` (adverse on primary only — likely a comparison artifact), `secondary_only` (adverse on secondary only — missed by the primary diagnosis), `healthy` |
| Budget-SQL substitution fix | DPA's `generate_sql_for_kpi` silently drops its `filters` argument, so the matrix's secondary Budget pass was producing SQL identical to the Actual pass (delta=0 for every segment). Fixed via a `_budget_variant_kpi` proxy that pre-substitutes the version filter in the stored SQL (mirrors SA's `_derive_plan_sql`), applied at all 3 DA budget-comparison call sites (dimensional, total-summary, hierarchical) |
| SF tier-aware scoping | Solution Finder derives `confirmed_problem_segments` from the matrix tiers and prioritises them in the option-generation prompt; `basis_specific` segments are flagged as probable artifacts, not built around |
| Frontend | `IsIsNotExhibit` renders a second delta column (secondary basis) + tier chip per row; `—` shown for segments absent from the secondary grouping (was rendering as `$0`) |
| Unit tests | 42 tests in `test_da_alert_comparator.py` — comparator precedence, matrix eligibility, basis-agreement tiers (incl. inverse-logic cost KPIs), budget-SQL derivation across SQL Server / BigQuery / Snowflake dialects, response round-trips |

**Also fixed while verifying against live data** (see Phase 10F note above): the matrix's own verification was showing spurious 100%-adverse results until the underlying `TimeFilter` YoY window bug was found and fixed — worth noting since it would otherwise have looked like a matrix defect rather than a pre-existing timeframe defect.

---

##### 11I-D: PIB Alert-Type Differentiation

PIB email and flash briefing currently presents all situation cards with equivalent visual weight and narrative framing. With 6 distinct alert types, the briefing should prioritise, section, and frame them differently.

| Deliverable | Description |
|---|---|
| Alert-type priority ordering | PIB section order within a briefing: (1) Compliance/Covenant breaches, (2) Compound alerts (cross-KPI divergence), (3) Projected breaches, (4) Plan variance misses, (5) Threshold breaches, (6) Acceleration signals, (7) Opportunities. Same KPI appearing in multiple categories: rendered once at highest priority. |
| "Projected Risks" briefing section | New optional section between "New Situations" and "Urgency" for `projected_breach` alerts. Framing: "The following KPIs are not yet breached but are on trajectory to cross critical thresholds within 3 periods." |
| Compound alert framing | Compound alerts render with a two-KPI summary: "Revenue UP 8% / Gross Margin DOWN 3pp — divergence requires analysis." Both KPIs linked in the deep link. |
| Plan variance framing | Separate "Budget Performance" section in PIB: "Ahead of Plan (2): Net Revenue +6%, SG&A -4% vs budget. Behind Plan (3): Gross Profit -12%, COGS +8%, B2B Revenue -7% vs budget." |
| Flash briefing enrichment | Flash Briefing text structured for TTS: reads alert type naturally — "Three projected risks warrant attention before month close: …" vs "Two threshold breaches detected: …" |
| Jinja2 template updates | Update `pib_email_template.html` with conditional sections and alert-type-aware framing. |
| Unit tests | 4 tests: covenant breaches appear in section 1 regardless of card order; projected_breach cards appear in Projected Risks section; plan-variance cards render in Budget Performance section; compound alert renders both KPI names. |

---

**Phase 11I dependency graph:**

```
11I-A Pattern 1 (plan_version_value) ───────────────→ 11I-C (VA plan trajectory)
11I-A Pattern 2 (projected_breach) ──────────────────→ 11I-D (PIB Projected Risks section)
11I-A Pattern 3 (acceleration) ──────────────────────→ 11I-D (PIB priority ordering)
11I-A Pattern 4 (kpi_type=concentration/covenant) ───→ 11I-C (covenant severity) + 11I-D
11I-B (compound alert flag) ─────────────────────────→ DA SCQA enrichment + 11I-D
```

**Build order:** 11I-A (all 4 patterns) → 11I-B (compound) → 11I-C (VA) → 11I-D (PIB). Each sub-phase ships independently. 11I-D has the most value when 11I-A and 11I-B are complete, but can ship with partial alert type coverage.

**Prerequisite:** Phase 11A (KPI accountability — so plan_sql_query and kpi_type scope correctly per principal) ✅ complete.

---

### Phase 11J: Solution Validity Monitoring

**Goal:** Recurring automated health checks on active VA-tracked solutions — detecting when the diagnostic foundation, market context, or declared assumptions have shifted enough that the solution's basis is no longer valid. Gives the CFO confidence that ROI attribution is trustworthy months after approval, without requiring manual reassessment.

**ICP case:** Mid-market CFOs approving operational changes based on AI recommendations are making board-defensible bets with 6–18 month measurement horizons. A control group that recovers on its own, or a market shift that reverses the original diagnosis, produces false attribution that surfaces at the worst possible time. This feature turns "we approved it six months ago" into "the system confirmed last week that the diagnostic basis is still intact."

**Pre-mortem (2026-05-29):** Full pre-mortem conducted before implementation. Key findings:
- F1 (control group not persisted) and F2 (no VA→DA linkage) **retracted** — Phase 7C already stores `control_group_segments` in `AcceptedSolution` and persists to Supabase via `va_solutions_store.py`. No `da_run_id` needed; segments are copied by value at HITL Gate 2 approval.
- F3 (unstructured assumptions) **confirmed** — `key_assumptions: List[str]` has no typed structure or `validated_by` field. Must be fixed before building the feature.
- **Cross-session vulnerability** confirmed — `_workflow_store` is in-memory only. A Railway restart between the DA run and HITL approval produces a VA record with `control_group_segments=None`. Requires a guard (P2 below). Permanent fix deferred to Infra A5 (persist `_workflow_store` to Supabase).
- O1 (no action protocol on DEGRADED) **acknowledged** — resolved in 11J-C with "Re-run Analysis" CTA.

---

#### Prerequisites (build before 11J-A)

##### P1: Structured Assumption Model on SF Output

Replace `key_assumptions: List[str]` in `StrategySnapshot` with a typed model:

```python
class SolutionAssumption(BaseModel):
    assumption: str
    validated_by: Literal["sa_assessment", "ma_query", "human_confirmation"]
    validated_at: Optional[str] = None  # ISO datetime; None = not yet confirmed
    revalidation_days: Optional[int] = None  # for human_confirmation: days before re-confirmation needed
```

| Deliverable | Description |
|---|---|
| `SolutionAssumption` Pydantic model | New model in `value_assurance_models.py`. Strict validator: `validated_by` is required — rejects plain strings. |
| `StrategySnapshot.key_assumptions` | Change type from `List[str]` to `List[SolutionAssumption]`. |
| SF synthesis prompt update | Instruct LLM to classify each assumption: `sa_assessment` (verifiable from KPI data), `ma_query` (requires market intelligence), `human_confirmation` (requires a human decision). |
| Legacy coercion on read | On deserialisation from Supabase JSONB: if an element is a plain string, coerce to `SolutionAssumption(assumption=str, validated_by="human_confirmation")`. No destructive migration needed. |
| Unit tests | 3 — structured assumption round-trips through SF → VA; legacy string coerces correctly on read; validator rejects entry missing `validated_by`. |

##### P2: Cross-Session Guard at VA Registration

| Deliverable | Description |
|---|---|
| `validity_monitoring_available: bool` | New field on `AcceptedSolution` (default `False`). Set to `True` at registration only when `control_group_segments` is not `None`. |
| Registration warning | When `control_group_segments=None`, log `WARNING` with `solution_id` + `kpi_id`. Registration proceeds normally — this is not an error. |
| Supabase migration | `ADD COLUMN validity_monitoring_available BOOLEAN DEFAULT FALSE` on `value_assurance_solutions`. |
| Gate in 11J-A | `assess_solution_health()` skips solutions where `validity_monitoring_available=False` and records `health_score="UNKNOWN"` with reason `"control_group_not_captured"`. |
| Unit tests | 2 — `validity_monitoring_available=True` when segments present at registration; `validity_monitoring_available=False` + warning logged when segments absent. |

**Note:** When Infra A5 ships "Persist `_workflow_store` to Supabase," the cross-session gap is eliminated. At that point, remove the `validity_monitoring_available` gate and always populate segments from the durable workflow store.

---

#### 11J-A: VA `assess_solution_health()` — V1 Control Group Stability

**Trigger conditions:**
- Called by `run_enterprise_assessment.py` after the SA scan for each client
- Applies to all `AcceptedSolution` records where `validity_monitoring_available=True` AND `phase` IN (`APPROVED`, `IMPLEMENTING`, `LIVE`, `MEASURING`)
- **Implementation window guard:** skip solutions where `(now - approved_at).days < validity_check_delay_days` (default 60). Prevents false DEGRADED signals before the solution has had time to act. Configurable on `monitoring_profile`.

**V1 health checks:**

*Check 1 — Basis check:* Is the primary KPI still in an adverse state?
- Retrieve the KPI's most recent situation from the `situations` Supabase table (latest entry for `kpi_id` + `client_id`)
- If the KPI has recovered above its warning threshold while the solution is still in APPROVED or IMPLEMENTING phase (not yet LIVE), the recovery occurred without the solution's intervention — the basis for the solution may be self-resolving
- `basis_valid = True` if KPI is still below warning threshold (problem persists); `False` if it has recovered pre-LIVE

*Check 2 — Control group drift check:* Are the IS NOT segments still distinguishable from the IS segments?
- Read `control_group_segments` (stored `BenchmarkSegment` dicts) from `AcceptedSolution`
- For each stored control segment: re-query DPA to get the current value for that dimension combination (DPA `execute_sql` with appropriate WHERE clause for the segment's dimension + value)
- Compare `current_value` vs `segment_value_at_approval` (stored in the segment dict)
- Drift threshold: segment has "drifted" when `|current - baseline| / |baseline| > 0.20` (20%, configurable)
- `control_stable = True` if fewer than 50% of segments have drifted; `False` otherwise

**Health score matrix:**

| basis_valid | control_stable | health_score |
|---|---|---|
| True | True | HEALTHY |
| True | False | WATCH |
| False | True | WATCH |
| False | False | DEGRADED |
| DPA error / segments unavailable | — | UNKNOWN |

`INVALID` reserved for when the data product is no longer accessible or the solution is in a terminal state.

**Output and storage:**

```python
class SolutionHealthReport(BaseModel):
    solution_id: str
    kpi_id: str
    client_id: str
    assessed_at: str                    # ISO datetime
    health_score: Literal["HEALTHY", "WATCH", "DEGRADED", "INVALID", "UNKNOWN"]
    basis_check_valid: bool
    control_group_stable: bool
    segments_checked: int
    segments_drifted: int
    assumption_statuses: List[dict]     # per-assumption validated_by + validated_at
    narrative: str                      # 1-2 sentence plain-English summary
    recommended_action: Optional[str]   # "Re-run Analysis", "Confirm market assumptions", etc.
```

| Deliverable | Description |
|---|---|
| `solution_health_reports` Supabase table | Composite PK `(solution_id, assessed_at)`. Retain last 6 reports per solution (delete oldest on insert when count exceeds 6). |
| `latest_health_score` on `AcceptedSolution` | Denormalised field updated on every health report write — avoids JOIN on Portfolio list query. Supabase migration: `ADD COLUMN latest_health_score VARCHAR(16)`. |
| `VA.assess_solution_health(solution_id)` | New entrypoint. Returns `SolutionHealthReport`. |
| Unit tests | 6 — HEALTHY (both checks pass); WATCH (basis valid, control drifted); DEGRADED (both fail); UNKNOWN (DPA query error); skipped when `validity_monitoring_available=False`; skipped when inside `validity_check_delay_days` window. |

---

#### 11J-B: Assessment Pipeline Integration + PIB Surfacing

**`run_enterprise_assessment.py` integration:**

After completing the SA → DA → SF scan for a client, add a validity monitoring pass:

```python
active_solutions = await va.list_solutions(
    client_id=client_id,
    phase=["APPROVED", "IMPLEMENTING", "LIVE", "MEASURING"]
)
health_reports = []
for solution in active_solutions:
    if solution.validity_monitoring_available:
        report = await va.assess_solution_health(solution.solution_id)
        health_reports.append(report)
```

Health reports included in the `AssessmentResult` payload alongside situation cards.

**PIB sections added:**

| Section | Trigger | Content |
|---|---|---|
| **"Solutions Requiring Attention"** | At least one solution with `health_score` DEGRADED or WATCH | One row per solution: title, KPI, health score badge, `narrative` sentence, `recommended_action` link. Ordered: DEGRADED first, then WATCH. |
| **"Pending Confirmations"** | At least one `SolutionAssumption` with `validated_by="human_confirmation"` and `validated_at=None` or past `revalidation_days` | Bulleted list: assumption text + solution title + PIB single-use confirmation token. Framing: "The following assumptions on active solutions require your confirmation before the next assessment." |

- Jinja2 template: new conditional `solutions_requiring_attention` and `pending_confirmations` sections in `pib_email_template.html`.
- Unit tests: 3 — PIB includes DEGRADED solutions in attention section; section omitted when all HEALTHY; pending confirmations section renders with token links when unconfirmed assumptions exist.

---

#### 11J-C: VA Portfolio Health Badge + Action Protocol

| Deliverable | Description |
|---|---|
| Health score badge | Small pill on each Portfolio row: green HEALTHY, amber WATCH, red DEGRADED, grey UNKNOWN. Rendered alongside the existing verdict badge. |
| Tooltip | Hover: last assessed date + `narrative` from most recent report. |
| "Needs Attention" filter | Portfolio filter dropdown: "All" \| "Needs Attention" (WATCH + DEGRADED). Useful when 10+ solutions tracked. |
| Validity history tab | In solution detail drawer: new "Validity History" tab showing last 6 `SolutionHealthReport` entries as a timeline (date + health_score + narrative). |
| "Re-run Analysis" CTA | On DEGRADED solutions: CTA button that pre-fills the DA workflow with the original `situation_id` and `kpi_id`. Resolves pre-mortem O1 (no action protocol on DEGRADED). |
| Unit tests | 2 backend tests — `list_solutions` returns `latest_health_score`; detail endpoint returns last 6 health reports ordered by `assessed_at` desc. |

---

#### 11J-D: V2 Expansions (post-pilot validation only)

Do not build until V1 has run through at least one full pilot cycle and health score distribution is observable. Two checks held back because their thresholds require real calibration data.

| Check | What it validates | Data source | Notes |
|---|---|---|---|
| **Market Condition Drift** | Have MA signals that underpinned the solution shifted materially? | Re-query MA agent with original market query context; LLM compares response to `ma_market_signals` stored in `AcceptedSolution` at approval | Adds an MA agent call per solution — cost and latency implications |
| **Strategic Alignment Drift** | Has the principal's priority set changed since approval? | Compare `StrategySnapshot.principal_priorities` vs current `PrincipalContext.business_processes` from registry | `assess_strategy_alignment()` already implemented in VA — wire into `assess_solution_health()` as an additional verdict contributor |

---

**Phase 11J dependency graph:**

```
P1 (SolutionAssumption typed model) ───────────────→ 11J-A (assumption_statuses in health report)
                                                   → 11J-B (pending_confirmations PIB section)
P2 (validity_monitoring_available guard) ──────────→ 11J-A (skip gate for solutions without segments)
11I-B (kpi_relationships) ─────────────────────────→ optional: compound pattern in 11J-D
11J-A (assess_solution_health + Supabase tables) ──→ 11J-B (assessment pipeline integration)
                                                   → 11J-C (portfolio badge reads latest_health_score)
11J-B (PIB sections) ──────────────────────────────→ 11J-C (portfolio action triggers DA re-run)
Infra A5 (_workflow_store → Supabase) ─────────────→ removes P2 guard (permanent cross-session fix)
```

**Build order:** P1 → P2 → 11J-A → 11J-B → 11J-C → 11J-D (post-pilot only)

**Files to read before implementing:**
- `src/agents/models/value_assurance_models.py` — `StrategySnapshot`, `AcceptedSolution`, `RegisterSolutionRequest`
- `src/agents/new/a9_value_assurance_agent.py` — `register_solution()`, `assess_strategy_alignment()` (already implemented — wire into 11J-D)
- `src/database/va_solutions_store.py` — Supabase persistence layer for `AcceptedSolution`
- `src/agents/new/a9_solution_finder_agent.py:797` — synthesis prompt `key_assumptions` output (P1 prompt update target)
- `src/api/routes/workflows.py:715–757` — HITL Gate 2 approval block (P2 guard insertion point)

---

---

### Pre-11K: Meridian Synthetic Test Dataset

**Goal:** Build and seed the Meridian Flow Systems BigQuery dataset before implementing Phases 11K–11N. All four phases are designed around this dataset — cadence views, EDA profiles, drift signals, and pre-computed DA results are parameterised to its specific dimension structure. Unit tests for 11K–11N assert against its cardinalities and rankings.

**Why this must precede 11K:** The EDA ranking tests assert `order_type` at rank #1 with a 23pp CM I spread. The cadence sensing tests assert against the three BigQuery views (`copa_fresh`, `copa_nightly`, `copa_stale`). The change detection tests assert against `copa_baseline` and `copa_drifted` with four controlled perturbations. None of these can be unit-tested without the dataset.

**Spec:** `docs/testing/copa_synthetic_data_spec.md` — full schema, dimension profiles, row volume, scenario designs, seed script requirements, and validation queries.

**Client:** `meridian` — Meridian Flow Systems, industrial pump and flow control equipment manufacturer, $165M revenue, SAP S/4HANA CO-PA → BigQuery.

**Key design decisions:**
- `order_type` added as 21st analytical dimension — catalog standard / engineered-to-order / aftermarket parts / service contract
- `order_type` ranks #1 in EDA importance (23pp CM I spread: 32% catalog → 55% aftermarket parts)
- 79,200 rows: FY2024 + FY2025 + FY2026 all 12 months — full FY2026 ensures demo stability year-round
- FY2026 H1 story: ETO project slippage → catalog order mix shift drives CM I −2.6pp (three situation cards fire)
- FY2026 H2 story: ETO backlog converts, partial recovery — powers the VA trajectory chart
- Four drift scenarios in `copa_baseline`/`copa_drifted`: new_member (DIGITAL_NATIVE_OEM), distribution_shift (industry), volume_anomaly (P12 ×2.4), variance_spike (payment_terms CoV doubles)

| Deliverable | Description |
|---|---|
| `scripts/clients/meridian.py` | Seed script: creates BQ dataset, loads 79,200 rows with fixed `random.seed(42)`, creates cadence views and scenario tables, registers Supabase records (data product, 5 KPIs, 4 BPs, 2 principals) |
| BQ dataset `agent9-465818.meridian_copa` | Table `copa_line_items` (34 cols, 79,200 rows), views `copa_fresh/nightly/stale`, tables `copa_baseline/copa_drifted` |
| Supabase registry records | Data product `meridian_copa`, KPIs `net_revenue / cm_i_pct / cm_ii_pct / sales_deduction_rate / freight_cost_pct`, principals `meridian_cfo / meridian_coo` |
| `tests/fixtures/da_background_runs_seed.json` | Pre-computed DA result for Scenario D — Scenario D UI path tests (11N) depend on this |
| Validation queries | All pass: 79,200 row count, order_type=4 / customer_group=5 / industry=7 / customer_id≈820, CM waterfall consistency, concentration ratios |

**Test file scaffolding (create empty files for 11K–11N):**
```
tests/unit/test_phase_11k_cadence_sensing.py
tests/unit/test_phase_11l_eda_profiling.py
tests/unit/test_phase_11m_change_detection.py
tests/unit/test_phase_11n_da_state.py
```

**Scope:** M (seed script ~400 lines; schema is specified, no design work required)

---

### Phase 11K: DGA Data Product Observability

**Goal:** DGA automatically classifies each data product's refresh cadence and detects pipeline stalls — eliminating manual schedule configuration and enabling the change detection agent in Phase 11M.

**Why this matters:** The enterprise assessment pipeline cannot self-pace without knowing how often each data product refreshes. A daily_batch dataset sampled every 15 minutes wastes compute and produces false drift signals. A real-time feed sampled once daily misses intraday crises. Cadence must be learned from the data, not declared by configuration — and it must be continuously re-confirmed because ETL processes change.

| Deliverable | Description |
|---|---|
| `classify_refresh_cadence(data_product_id, client_id)` on DGA | Probes `MAX(time_col)` twice at a configurable interval via DPA execution; classifies pattern as `real_time \| micro_batch \| daily_batch \| weekly_batch \| monthly_close` from delta magnitude and time-of-day clustering. DGA generates the probe specification; DPA executes — boundary preserved. |
| `check_pipeline_health(data_product_id, client_id)` on DGA | Compares `NOW() - MAX(time_col)` against expected cadence interval × 1.5 tolerance. Returns `healthy \| stale \| unknown`. |
| `DataProductObservabilityRequest / Response` Pydantic models | New models in `src/agents/models/data_governance_models.py`. |
| Supabase migration | `20260610_data_product_observability.sql` — add `refresh_cadence`, `cadence_confirmed_at`, `last_refresh_detected_at`, `pipeline_status` to `data_products` table. |
| `DataProduct` model update | Add the four observability fields; all optional (null = not yet profiled). |
| `pipeline_failure` situation card | When `check_pipeline_health` returns `stale`, SA emits a structural alert card with `alert_type = "pipeline_failure"`. Highest priority in PIB section ordering (above covenant breaches). |
| `run_enterprise_assessment.py` integration | Call `DGA.check_pipeline_health()` per unique `data_product_id` before the KPI scan loop. Skip KPI assessment for stale data products and include the pipeline alert in the assessment results. |
| Manual override | `PATCH /api/v1/registry/data-products/{id}` accepts `refresh_cadence` field for explicit admin override. Overridden cadence is not auto-reclassified unless admin resets it. |
| Unit tests | 4 — health = stale when `NOW() - MAX > cadence × 1.5`; health = healthy within tolerance; pipeline_failure card emitted on stale; KPI assessment skipped when data product stale. |

**Key implementation decision — DGA boundary:** The DGA card prohibits DGA from querying data directly. `classify_refresh_cadence` and `check_pipeline_health` must generate a probe specification (table name, time column, threshold) and delegate execution to DPA via the orchestrator. DGA evaluates the result; DPA runs the SQL.

**Dependencies:** None — independent of other 11x phases. Produces `pipeline_status` and `refresh_cadence` consumed by Phase 11M.

**Scope:** M

---

### Phase 11L: EDA Dimensional Importance Profiling

**Goal:** During data product onboarding, DGA runs statistical EDA across all dimensions and writes a ranked `dimension_importance_profile` to Supabase — replacing the arbitrary 5-dimension config cap with data-driven dimension selection.

**Why this matters:** The current `max_dimensions = 5` config was set for interactive latency reasons, not analytical ones. A logistics data product may have 30+ meaningful dimensions; a financial model may have 6. The EDA profile lets DA process as many dimensions as carry signal — no more, no fewer — and does so in ranked order so background runs always lead with the strongest drivers.

**Note — critical filesystem bug fixed here:** The existing `compute_and_persist_top_dimensions()` on DGA writes to a local YAML file (`kpi_enrichment.yaml`). This file does not survive Railway redeploys. Phase 11L redirects all output to Supabase JSONB as the authoritative store.

```python
class DimensionImportanceEntry(BaseModel):
    dimension: str
    concentration_ratio: float   # top-3 group share / total
    cardinality: int             # unique member count
    variance_score: float        # coefficient of variation across groups
    importance_rank: int

class DimensionImportanceProfile(BaseModel):
    data_product_id: str
    client_id: str
    computed_at: str
    dimensions: List[DimensionImportanceEntry]
    total_variance_explained: float
```

| Deliverable | Description |
|---|---|
| `DimensionImportanceProfile` Pydantic model | New model in `src/agents/models/data_governance_models.py`. |
| `compute_and_persist_top_dimensions()` refactored | Extends existing method: adds `variance_score` (std dev of group KPI values / mean) and `cardinality` (`COUNT(DISTINCT dim_col)`) alongside existing concentration ratio. Writes `DimensionImportanceProfile` to Supabase `data_products.dimension_importance_profile` JSONB. Local YAML write retained as dev convenience only. |
| Supabase migration | `20260611_dimension_importance_profile.sql` — add `dimension_importance_profile JSONB` to `data_products` table; add `dimension_importance_profile JSONB` to `kpis` table (per-KPI override wins over data product default). |
| Onboarding step 9 | Data product onboarding 8-step workflow gains a step 9: "Compute EDA dimension profile." Triggered automatically after schema inspection completes. |
| `POST /api/v1/registry/data-products/{id}/compute-dimension-profile` | Triggers an async EDA run. Can be called manually to refresh a stale profile. |
| `GET /api/v1/registry/data-products/{id}/dimension-profile` | Returns the stored profile with `computed_at` timestamp. |
| DA `_dims_from_contract()` Priority 0 lookup | Before the existing contract YAML fallback chain, check for `dimension_importance_profile` on the data product registry record. When present, use its ranked `dimensions` list — no count cap applied in scheduled execution mode (see Phase 11M). In interactive mode, the `max_dimensions` config still caps the list. |
| Profile refresh schedule | `run_enterprise_assessment.py` calls `POST /compute-dimension-profile` for each data product whose profile is older than `refresh_cadence × 7` (weekly refresh for daily_batch, monthly for monthly_close). |
| Unit tests | 5 — profile written to Supabase not filesystem; DA Priority 0 lookup uses profile when present; DA falls back to contract YAML when profile absent; per-KPI profile overrides data product profile; onboarding step 9 fires after step 2. |

**Dependencies:** Phase 11K helpful (cadence drives profile refresh schedule) but not blocking. Phase 11L can ship independently.

**Scope:** M

---

### Phase 11M: Change Detection Agent + DA Background Execution Mode

**Goal:** A lightweight statistical agent detects significant dimensional drift against the EDA baseline and triggers background DA; DA gains uncapped parallel async execution in scheduled mode; the 5-dimension interactive cap is preserved; DA response gains a `summary_view` sized for SF and PIB consumption.

**Why this matters:** This is the core of the event-driven pipeline. The system stops polling on a fixed schedule and starts responding to actual data changes. DA stops being limited to 5 dimensions in background mode — it processes all dimensions in parallel, produces a full result, and a sized summary for downstream consumers. SF receives only the ranked diagnostic signal it needs, not the full dimensional table.

#### 11M-A: Dimensional Limit Removal

The `max_dimensions = 5` config is the interactive latency constraint. It is explicitly preserved for interactive mode and removed for scheduled mode:

| Mode | Dimension handling |
|---|---|
| `execution_context = "interactive"` | `max_dimensions` config applies (default 5). Current behaviour unchanged. |
| `execution_context = "scheduled"` | `max_dimensions` is overridden to `len(profile.dimensions)` from the EDA importance profile. If no profile exists, all dimensions from the contract schema are used with no cap. |

**Fallback when no EDA profile exists in scheduled mode:** Use `_dims_from_contract()` with no limit against the raw contract `dimension_semantics` list. Log a warning recommending onboarding step 9 be run. Do not silently fall back to the 5-dimension default — that would defeat the purpose of background mode.

#### 11M-B: DA `summary_view` — Tiered Output for Downstream Consumers

Each DA run produces two outputs. Both are stored in `da_background_runs.da_result`:

```python
class DeepAnalysisResponse(BaseModel):
    # ... existing fields ...
    summary_view: Optional[DASummaryView] = None   # NEW — always populated when execution_context="scheduled"

class DASummaryView(BaseModel):
    top_dimensions: List[str]           # top 5 by EDA importance rank
    is_items: List[dict]                # top 3 problem rows across all dimensions
    is_not_items: List[dict]            # top 3 healthy/benchmark rows
    mixed_framing: bool
    generated_at: str
```

**Consumer sizing:**

| Consumer | Receives | Why |
|---|---|---|
| SF Stage 1 + Synthesis | `summary_view` (top 5 dims × top 3 rows = ~15 cells) | LLM quality degrades with excess context; SF needs the strongest diagnostic signal, not the full table |
| PIB email | `summary_view.is_items[:3]` | Existing 10B spec: top 3 IS driver rows per situation block |
| Council Debate UI (pre-computed path) | Full `kt_is_is_not` | Interactive exploration — user chooses what to expand |
| SA card badge | `summary_view.top_dimensions[:2]` | KPI tile subtitle spec: top 2 dimension drivers |

**SF prompt update:** SF synthesis and Stage 1 prompts currently accept the full `deep_analysis_context`. When `summary_view` is present, pass `summary_view` as the DA context instead of the full `kt_is_is_not`. The existing `da_summary` field already provides a trimmed context for synthesis (Phase 10D) — `summary_view` replaces and formalises that pattern.

#### 11M-C: Change Detection Agent

**New agent:** `A9_Change_Detection_Agent` — a lightweight peer of SA, not embedded within it. Separate agent card required per protocol.

**Detection signals:**

| Signal | Detection method | Trigger threshold |
|---|---|---|
| New dimension members | `SET(current_members) - SET(baseline_members)` for top-N dimensions | Any new member in a top-5 dimension |
| Distribution shift | `\|concentration_ratio_current - concentration_ratio_baseline\| / baseline > 0.20` | 20% shift in top-3 group share |
| Volume anomaly | Total KPI value vs rolling mean | > 2σ from rolling 6-period mean |
| Variance spike | Any dimension's `variance_score` doubles from baseline | 2× baseline coefficient of variation |

```python
class ChangeSignal(BaseModel):
    dimension: str
    signal_type: Literal["new_member", "distribution_shift", "volume_anomaly", "variance_spike"]
    magnitude: float
    details: str

class ChangeDetectionResult(BaseModel):
    data_product_id: str
    client_id: str
    assessed_at: str
    signals: List[ChangeSignal]
    trigger_da: bool
    trigger_reason: Optional[str]
    affected_kpi_ids: List[str]
```

**Cadence matching:** CDA only runs for data products where `pipeline_status == "healthy"` (Phase 11K). Sampling frequency matches `refresh_cadence` — no point running CDA on a monthly_close dataset at daily cadence.

#### 11M-D: DA Async Parallel Execution

The sequential for-loop at line 1143 of `a9_deep_analysis_agent.py` processes dimensions one at a time. At 20 dimensions × ~200ms SQL round-trip = 8–16 seconds minimum in scheduled mode. This is not acceptable for a background pipeline that is supposed to run unnoticed.

**Fix:** Extract the per-dimension processing block into a `_process_dimension(dim)` coroutine. In scheduled mode, replace the sequential loop with `asyncio.gather(*[_process_dimension(dim) for dim in all_dims])`. Dimensions have no cross-dependencies — they are structurally independent GROUP BY queries.

#### 11M-E: `da_background_runs` Supabase Table

```sql
CREATE TABLE da_background_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kpi_id TEXT NOT NULL,
    client_id TEXT NOT NULL,
    trigger_type TEXT NOT NULL,  -- "change_detection" | "sa_breach" | "manual"
    trigger_signal JSONB,
    execution_context TEXT NOT NULL DEFAULT 'scheduled',
    status TEXT NOT NULL DEFAULT 'queued',  -- queued | running | complete | failed
    da_result JSONB,             -- full DeepAnalysisResponse
    queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT
);
```

Note: `da_background_runs` stores `(kpi_id, client_id)` as the primary coordination keys — not a foreign key to `kpi_assessments` — because background DA runs are triggered independently of assessment cycles.

| Additional deliverable | Description |
|---|---|
| `DeepAnalysisRequest` update | Add `execution_context: Literal["interactive", "scheduled"] = "interactive"` and `da_run_id: Optional[str]` |
| `run_enterprise_assessment.py` integration | After SA loop: invoke CDA per data product. If `trigger_da=True`, enqueue background DA to `da_background_runs` via `asyncio.create_task()`. |
| Unit tests | 8 — dim limit removed in scheduled mode; dim limit preserved in interactive mode; `asyncio.gather` used in scheduled mode (mock verify); summary_view top-5 × top-3 correct; SF receives summary_view not full kt; CDA triggers DA on distribution_shift signal; CDA suppresses trigger when `pipeline_status = stale`; no-profile fallback logs warning and uses full contract dimension list. |

**Dependencies:** Phase 11L (EDA profiles) must precede — CDA needs the baseline. Phase 11K (cadence) strongly recommended.

**Scope:** XL

---

### Phase 11N: Event-Driven PIB + SA Card DA State + UI Dimensional Accordion

**Goal:** PIB fires on DA completion events (not cron); situation cards show DA pre-computation state with an as-of timestamp; DeepFocusView renders many-dimension results with an accordion pattern; principals can always re-trigger on-demand DA from the SA card.

**Why this matters:** This phase closes the loop on the agentic pipeline. No fixed schedule exists anywhere. PIB only fires when analysis is materially new. The UI handles the full dimensional depth that scheduled DA now produces. The interactive path remains first-class — not as the default, but as the always-available override.

#### 11N-A: DA State on Situation Cards

```python
da_state: Literal["not_run", "running", "precomputed", "stale"] = "not_run"
# precomputed: background DA result available and fresh (within 1× cadence window)
# stale: result exists but older than 1× cadence window
# not_run: no background DA triggered for this situation
da_completed_at: Optional[str] = None
```

Supabase migration `20260612_da_state_on_assessments.sql`:
```sql
ALTER TABLE kpi_assessments
  ADD COLUMN IF NOT EXISTS da_state TEXT DEFAULT 'not_run'
      CHECK (da_state IN ('not_run', 'running', 'precomputed', 'stale')),
  ADD COLUMN IF NOT EXISTS da_completed_at TIMESTAMPTZ;
```

When a `da_background_runs` row transitions to `status = "complete"`, the assessment engine updates `kpi_assessments.da_state = "precomputed"` and `da_completed_at = NOW()` for the matching `(kpi_id, client_id)`.

#### 11N-B: Event-Driven PIB Trigger

PIB currently fires unconditionally after the SA loop in `run_enterprise_assessment.py`. Replace with a materiality-gated trigger:

```python
def _da_results_materially_differ(prev: dict, curr: dict) -> bool:
    # Compare top-3 (dimension, key) pairs in where_is
    # If 2+ have changed → material; trigger PIB
    prev_keys = {(e["dimension"], e["key"]) for e in
                 (prev.get("kt_is_is_not") or {}).get("where_is", [])[:3]}
    curr_keys = {(e["dimension"], e["key"]) for e in
                 (curr.get("kt_is_is_not") or {}).get("where_is", [])[:3]}
    return len(prev_keys.symmetric_difference(curr_keys)) >= 2
```

When a background DA run completes, `_maybe_trigger_pib(client_id, kpi_id)` is called. It compares the new `da_result` against the previous entry in `da_background_runs` for the same `(kpi_id, client_id)`. If materially different → PIB fires for all principals accountable for the KPI. If not → no briefing (avoids noise).

**PIB compose path for DA-completion events:** PIB's existing `_compose()` loads `get_latest_run()` from `assessment_runs`. A DA-completion-triggered PIB uses a new `trigger_type = "da_completion"` path that reads the DA result directly from `da_background_runs` rather than re-loading the full assessment run. All downstream PIB machinery (token generation, Jinja2 rendering, SMTP) is reused unchanged.

#### 11N-C: New API Endpoint — Pre-Computed DA Result

```
GET /api/v1/deep-analysis/background/{kpi_id}?client_id=X
```

Returns the latest `da_background_runs` entry for a KPI where `status = "complete"`. The frontend calls this endpoint when `da_state = "precomputed"` to load the Council Debate view without triggering a new DA run.

#### 11N-D: DeepFocusView — Accordion for Many-Dimension Results

The Council Debate Is/Is Not exhibit is designed around 5 dimensions. At 20–50 dimensions it becomes unworkable as a flat table.

| Deliverable | Description |
|---|---|
| Headline view | Top 3–5 dimensions by EDA importance rank always expanded. Dimension header shows importance rank badge (e.g., "#1 Driver") and variance contribution percentage. |
| Accordion — remaining dimensions | Dimensions ranked 6+ collapsed by default. "Show all N dimensions" expand control. |
| Importance rank badge | Small tag on each dimension header: `#1 · 34% variance` — sourced from `summary_view.top_dimensions` and the EDA profile. |
| Filter / search | Text input to filter visible dimensions by name — essential for logistics models with 30+ dimensions. |
| Pre-computed state loading | When `da_state = "precomputed"`, the "Run Analysis" button becomes "View Analysis". Clicking it calls `GET /deep-analysis/background/{kpi_id}` and populates the exhibit directly without triggering a new DA run. |
| Re-trigger CTA | "Refresh Analysis" always available regardless of `da_state`. Triggers on-demand interactive DA via existing `/deep-analysis/run` endpoint. Used when the principal suspects the pre-computed result is stale relative to recent events. |
| SA card badge | Situation card shows `da_state` badge: "Analysis ready · 2 hours ago" (precomputed), "Analysis running…" (running), "Analysis outdated · 14 hours" (stale), no badge (not_run). |

| Additional deliverables | Description |
|---|---|
| `GET /assessments/{run_id}/situations` update | Include `da_state` and `da_completed_at` per situation in response. |
| PIB email update | When composing from a DA-completion event: show `da_completed_at` timestamp in the briefing footer ("Analysis completed: 06:14 UTC"). Principals can see how fresh the analysis is relative to the situation timestamp. |
| Unit tests | 6 — `da_state = precomputed` after background DA completes; `da_state = stale` when `da_completed_at < NOW() - cadence`; PIB fires when DA results material; PIB suppressed when DA results unchanged; `GET /deep-analysis/background/{kpi_id}` returns latest complete run; PIB skips brief when `pipeline_status = stale`. |

**Phase 11N dependency graph:**
```
Phase 11M (da_background_runs + execution_context) ──→ 11N-A (da_state transitions)
                                                      → 11N-B (materiality check reads da_background_runs)
                                                      → 11N-C (new endpoint reads da_background_runs)
Phase 11K (pipeline_status) ─────────────────────────→ 11N-B (PIB suppressed when pipeline stale)
Phase 11L (EDA profile) ─────────────────────────────→ 11N-D (importance rank badges in accordion)
```

**Dependencies:** Phase 11M must precede. Phase 11K strongly recommended. Phase 11L needed for importance badges in the UI.

**Scope:** L

---

**Phase 11K–11N dependency chain:**

```
11K (cadence sensing + pipeline health)
  └── 11L (EDA profiling — can also ship independently)
        └── 11M (change detection + background DA + dimensional limit removal + summary_view)
              └── 11N (event-driven PIB + SA card state + accordion UI)
```

**Architectural decisions recorded:**
- Interactive DA always uses `max_dimensions` cap — latency constraint is real
- Scheduled DA has no dimension cap — EDA profile provides the ranked list; contract schema is the fallback when no profile
- SF receives `summary_view` (top 5 dims × top 3 rows), not full `kt_is_is_not`
- No fixed PIB cron schedule — PIB fires on DA completion events gated by materiality check
- Interactive DA path from SA card is first-class and always available — not a fallback
- Pipeline failure (`stale` data product) suppresses both DA and PIB — analysis on stale data is not delivered

**Sequencing decision (2026-07-02) — Harden before expanding:**

Pre-11K through 11N are deferred until the existing pipeline survives a complete end-to-end demo without breakage. The rationale:

1. The 5-dimension cap has not been raised as a prospect objection. Finance model ICPs (CFO-owned CO-PA data) naturally have 5–12 meaningful dimensions — the current cap is representative, not limiting, for the confirmed target audience.
2. Three higher-priority gaps exist that break the stated commercial moat (SA→DA→SF→VA) before dimensional depth becomes relevant:
   - **SF→VA wiring incomplete** — `kpi_id` and impact bounds are missing from the HITL approval payload in `workflows.py`. Solution handoff to VA does not work end-to-end.
   - **VA persistence is in-memory** — accepted solutions do not survive a Railway restart. VA trajectory chart cannot be demonstrated credibly.
   - **Phase 11I incomplete** — alert intelligence is the active phase; finish what is in flight before adding phases.
3. 11K–11N is 4 phases (XL/L/M/M scope) built on infrastructure that doesn't exist yet. The architectural boundaries it discovers (BQ parallel query limits, asyncio.gather under load, Supabase JSONB sizing) are only testable after the Meridian seed script exists.

**Revised build order before 11K–11N:**
1. Fix SF→VA HITL wiring (`workflows.py` — kpi_id + impact bounds in approval payload)
2. Persist VA solutions to Supabase (replace in-memory store)
3. Ship Phase 11I (Alert Intelligence) — complete the active phase
4. Build `scripts/clients/meridian.py` seed script as a standalone task — this is the only Pre-11K deliverable worth building now; it stress-tests BQ onboarding and provides a richer demo dataset regardless of whether 11K–11N ships
5. Implement 11K–11N when a prospect conversation confirms dimensional depth as a requirement, or when a specific SAP CO-PA / operational data model demo is scheduled

---

### Phase 11O: LLM Model Routing Modernization + Fable 5 A/B (Jul 2026)

**Goal:** Make the LLM service layer capability-aware so newer Claude models (Sonnet 5, Opus 4.8, Fable 5) can be adopted per-task via the existing routing table, then A/B the highest-value call sites against the current Sonnet 4.6 / Haiku 4.5 baseline.

**Why this matters:** The routing table pins Sonnet 4.6 (Feb 2026 generation) for synthesis/reasoning and the SF card documents repeated prompt-scaffolding fights against its reasoning limits (recovery_range 0.0 fallback, consistency-check paradox, boilerplate rationale). Sonnet 5 is the same sticker price with near-Opus quality ($2/$10 intro through Aug 2026); Fable 5 is a targeted experiment for the two call sites where analysis quality *is* the product — SF synthesis and the offline enterprise assessment (the stated commercial moat). Blocker today: `ClaudeService.generate()` unconditionally passes `temperature`, which returns 400 on Fable 5 / Opus 4.7+ and on Sonnet 5 for non-default values.

**Relationship to the 2026-07-02 "harden before expanding" decision:** 11O-A/B are hardening-compatible — small scope, no new agents, no new infrastructure, and they de-risk every future model migration. 11O-C is an experiment explicitly gated behind env overrides: zero production behavior change unless the A/B wins.

**Baseline (recorded 2026-07-12, commit 941a425):** unit suite 508 passed / 9 skipped / 2 pre-existing failures unrelated to LLM routing (`test_get_portfolio_summary_empty_store` — local VA store not empty; `test_generate_sql_ignores_all_tokens_in_filters` — column casing drift). All SA call sites route via `get_claude_model_for_task()`; only remaining deviation is Accountability Interview's hardcoded constants.

#### 11O-A: Capability-Aware Request Builder ✅ COMPLETE (Jul 2026)

Shipped as designed with two deviations: the effort env var is `A9_LLM_EFFORT` (not `CLAUDE_EFFORT` — that name is injected by the Claude Code harness into its shell sessions and would leak into local runs), and text extraction was additionally hardened to take the first `text` content block (Fable responses may lead with fallback/thinking blocks). SDK 0.84.0 → 0.116.0. 11 unit tests in `tests/unit/test_claude_service_capabilities.py`; full suite matches baseline (546 passed, same 2 pre-existing failures).

**E2E verified (2026-07-13):** live-API smoke across all five model families — Haiku 4.5 / Sonnet 4.6 with temperature preserved, Sonnet 5 / Opus 4.8 with temperature dropped (would 400 on old code), Fable 5 with server-side fallbacks beta accepted (org retention requirement confirmed). Full pipeline e2e: `run_enterprise_assessment.py --client lubricants --dry-run` — 15 KPIs, 13 escalated, 0 errors, SA card observations generated through the new builder.

| Deliverable | Description |
|---|---|
| Model capability map in `claude_service.py` | Per-model-family flags: `accepts_temperature`, `supports_thinking_config`, `supports_effort`, `max_output_tokens`. Keyed by model-ID prefix (e.g. `claude-sonnet-4-`, `claude-sonnet-5`, `claude-opus-4-8`, `claude-fable-5`). |
| Request builder | `generate()` / `analyze()` etc. consult the map: drop `temperature`/`top_p`/`top_k` for models that reject them; pass `output_config.effort` where supported (env-tunable per task, default `high`). |
| `stop_reason` handling | Check `stop_reason == "refusal"` before reading content; return `A9_LLM_Response(status="error", error_message=...)` with the refusal category in warnings. Required for Fable 5; harmless elsewhere. |
| Server-side fallbacks (Fable only) | When the resolved model is `claude-fable-5`, include `betas=["server-side-fallback-2026-06-01"]` + `fallbacks=[{"model": "claude-opus-4-8"}]` so classifier false-positives degrade to Opus instead of failing the request. |
| `anthropic` SDK bump | 0.84.0 → latest; verify `output_config` / `fallbacks` parameter support. |
| Unit tests | 4 — temperature dropped for Fable/Opus-4.8/Sonnet-5 IDs; temperature preserved for Sonnet 4.6/Haiku; refusal stop_reason → status="error"; capability map fallback for unknown model IDs (conservative: send no sampling params). |

**Scope:** S–M. No behavior change for current models — pure enablement.

#### 11O-B: Routing Table Refresh — Sonnet 5 ✅ COMPLETE (Jul 2026)

**A/B result (2026-07-13, three-way controlled test):** one frozen DA output (lubricants gross_margin_pct), one deterministic Stage 1, synthesis stage run per model. The frozen DA input happened to carry a data contradiction (quarterly avg +1.41pp vs intra-quarter −7.5pp slide, empty where_signals) — an unplanned reasoning stress test.

| | Sonnet 4.6 | Sonnet 5 | Fable 5 |
|---|---|---|---|
| Latency | 206.5s | 139.4s | 110.7s |
| Tokens in/out | 6,264/9,938 | 8,739/13,816 | 8,739/8,629 |
| Cost/call | ~$0.17 | ~$0.16 intro | ~$0.52 |
| Contradiction handling | buried in next steps | led with it, containment-first | flagged it AND made the call; sharpest inference ("quarterly average conceals the slide — next quarter opens from ~32% run-rate") |

**Decision: Sonnet 5 adopted** for REASONING / SOLUTION_FINDING / BRIEFING / SYNTHESIS / GENERAL. Haiku tasks unchanged. MA `synthesis_model` config default now follows the SYNTHESIS routing entry. KPI Assistant default → sonnet-5. Rollback = env override(s) to `claude-sonnet-4-6`. Accountability Interview's hardcoded constants intentionally not touched (documented deviation).

**11O-C evidence from the same run:** Fable won on quality AND latency at ~3× cost — promising but the input was degraded (empty where_signals), so the decision gate stays open pending one confirmatory round on a segment-rich DA output. Two anomalies logged from the run: (1) lubricants DA returned an empty Is/Is-Not table; (2) ~13 Snowflake SQL compilation errors fired at the end of the run despite lubricants being BigQuery-backed — possible cross-client routing leak. Both under investigation before the confirmatory round.

| Deliverable | Description |
|---|---|
| Routing table update | `REASONING` / `SYNTHESIS` / `GENERAL` (+ `SOLUTION_FINDING`, `BRIEFING`) → `claude-sonnet-5`. `STAGE1_PERSONA` / `NLP_PARSING` / `SQL_GENERATION` stay on Haiku 4.5. |
| Stage 1 determinism check | Sonnet 5 rejects non-default sampling; Stage 1 stays on Haiku 4.5 (temperature 0.0 preserved) — no change, but verify the capability map doesn't strip Haiku's temperature. |
| A/B validation | Run the Lubricants gross-margin scenario end-to-end (DA → SF full debate) on Sonnet 4.6 vs Sonnet 5 with identical inputs. Compare: synthesis rationale specificity, recovery_range plausibility, consistency-check pass rate, latency, token cost. |
| Regression gate | Unit suite matches the 941a425 baseline (508 pass; the 2 pre-existing failures tracked separately). |

**Scope:** S. Rollback = one env var (`CLAUDE_MODEL_SYNTHESIS=claude-sonnet-4-6`).

#### 11O-C: Fable 5 Gated Experiment — evidence collected, adoption deferred (Jul 2026)

**Three A/B rounds run (2026-07-13), all on lubricants gross_margin_pct with frozen DA + identical synthesis inputs per round:**

| Round | Input shape | Sonnet 5 | Fable 5 |
|---|---|---|---|
| 1 | Degraded DA (empty segments, data contradiction) | Epistemically careful but underpowered ("audit the data first"), 139s | Flagged the contradiction AND made the call; sharpest inference; 111s |
| 2 | Segment-rich DA, no Stage 1 (non-production shape) | Hit SF's 16384 max_tokens — truncated to 2 options | Complete 3-option briefing, 9.2K tokens, 115s |
| 3 | **Production-shaped** (41 segments + MBB Stage 1) | Complete, high quality: cost audit + pricing recalibration, 12–22pp anchored recovery, 114s, ~$0.14 | Complete, modestly sharper: used the internal benchmark (High Mileage Engine Oil +15pp) as replication anchor, explicit lever-risk causality, 111s, ~$0.60 |

**Verdict against the decision gate:** on clean production-shaped input, Fable is modestly better — not visibly 3× better. On degraded/contradictory input, Fable is clearly the strongest reasoner. Fable's natural home is therefore the **offline enterprise assessment** (messy data, latency-insensitive, quality-is-the-deliverable) — but that pipeline is SA-only today (DA/SF are HITL). **Decision: keep Sonnet 5 as the routing default; revisit Fable adoption when background DA/SF execution ships (Phase 11M/11N)** — at that point set `CLAUDE_MODEL_SYNTHESIS=claude-fable-5` on the scheduled path only. The capability layer (11O-A) makes that a config change.

**Watch item:** Sonnet 5 synthesis outputs run 11–16K tokens (vs Fable's ~9K) — round 3 used 11.2K of the 16384 cap. The cap only truncated on a non-production input shape, but headroom is thin; consider raising SF synthesis `max_tokens` to ~20000 defensively.

**Deferred (optional):** the loosened-scaffolding Fable variant (Phase 12 prompt constraints relaxed) — run if/when Fable adoption is activated.

Original deliverables table (for reference):

| Deliverable | Description |
|---|---|
| Org retention check | Confirm the Anthropic org meets Fable's 30-day data-retention requirement before any call (ZDR orgs 400 on every request). Also a client-facing consideration — document for enterprise conversations. |
| SF synthesis A/B | `CLAUDE_MODEL_SYNTHESIS=claude-fable-5` in dev only. Full-mode debate on the Lubricants scenario; per the Fable migration guidance, also test with Phase 12 prompt scaffolding (CONSISTENCY CHECK, recovery anchors) loosened — over-prescriptive prompts reduce Fable output quality. |
| Offline assessment A/B | `run_enterprise_assessment.py` run with Fable synthesis — latency-insensitive, quality-is-the-deliverable context. Evaluate Batch API (50% discount → Opus-standard pricing) if adopted. |
| Decision gate | Fable earns a routing-table place only if it visibly beats Sonnet 5 on synthesis quality at ~3.3× the price. Otherwise close the experiment and record findings here. |

**Scope:** S (experiment). **Dependencies:** 11O-A (blocker), 11O-B (comparison baseline).

---

### Phase 12: Platform Completeness + Business Objectives Foundation

**Goal:** Close remaining platform gaps (KPI Assistant UI, Slack, onboarding) and lay the data model foundation for the Business Optimization Agent outer loop. Sub-phases 12A–12E are the sequenced delivery plan.

| Sub-phase | Deliverable | Description |
|----------|------------|-------------|
| **12A** ✅ | Company Intelligence KPI Template Generator | Org-first onboarding: MA agent researches company → generates benchmark-anchored KPI templates (June 2026) |
| **12E** | Company Intelligence Principal Templates | MA agent researches a company's leadership team → admin commits as `status='template'` principals; email optional at commit; promotion to active gated on email entry |
| **12B** | Org-First Accountability Onboarding | Process template → principal suggestion → one-step accountability confirm |
| **12C** | Business Objectives Registry | `business_objectives` + `objective_kpi_drivers` tables; CRUD API + UI; `objective_id` on situation cards; SA severity enrichment |
| **12D** | Objective Health Score + Strategic Performance Summary | Composite objective health per assessment run; PIB "Strategic Objectives" section; Portfolio Objectives tab |
| — | KPI Assistant UI | React panel for the existing API-only KPI suggestion workflow |
| — | Slack notifications | PIB summary to Slack channel alongside email |

**Business Optimization Agent — full PRD:** `docs/prd/agents/a9_business_optimization_agent_prd.md`

**Phase B/C (2027–2028):** Portfolio conflict detection, strategic alignment scoring, sequencing, KPI trajectory forecasting, and fully autonomous objective pursuit are Phase B/C work — dependent on Phase A trust being established with pilot clients. See PRD for phasing rationale and trust curve.

**Reference:** `workflow_definitions/business_optimization.yaml`, `workflow_definitions/innovation_driver.yaml`

---

### Phase 12A: Company Intelligence-Driven KPI Template Generator ✅ COMPLETE (June 2026)

**Status:** Shipped 2026-06-02. Backend (MA extension + API routes + SA guard + migration), Admin Console UI, and unit tests all in place. Manual end-to-end validation pending with a real company name.

**Goal:** Given a company name, research its public footprint, generate a relevant KPI set with industry-calibrated benchmarks, and commit accepted KPIs to the registry ready for data connection. Org-first onboarding — the system tells clients what to measure before asking them to connect data.

**Positioning:** Replaces the blank-slate KPI entry experience. Admin enters company name; system returns industry-calibrated KPIs with benchmarks anchored to company-reported data where available. CFO can't dispute benchmarks that came from their own annual report.

**Pre-mortem mitigations (2026-05-30):**
- M1 (benchmark trust): every benchmark shows source badge (`📄 Company filing` / `🏭 Industry peer` / `🤖 Inferred`) and a confidence level — no unattributed numbers.
- M2 (dead KPI registry): introduce `status = template | active` on KPIs. SA evaluates only `active` KPIs. Template KPIs show as "Pending data connection" in Registry Explorer.
- M3 (two onboarding paths): Phase 12A is additive — data-first wizard still works for existing clients. Template generator is a new entry point, not a replacement.
- M4 (MA agent failure): graceful fallback to LLM-only with clear degradation notice; template still generated, all benchmarks marked `inferred`.
- M5 (industry taxonomy): two-level sector → sub-sector picker plus one-line business description for context — no forced taxonomy fit.
- M6 (legal/citation risk): cite source type only ("specialty chemicals analyst reports, 2024") — no specific competitor names or figures presented as fact.

**User flow:**
1. Admin enters company name + optional industry hint
2. MA agent runs 4 targeted Perplexity searches in parallel (filings, business segments, peer benchmarks, strategic KPI mentions)
3. LLM synthesises → structured `CompanyKPIProfile` grouped by domain
4. Admin reviews table: name, definition, benchmark range, source badge, accept/reject toggle
5. Commit → KPIs written to registry with `status = template`; link to "Connect your data sources"

| Deliverable | Description |
|------------|-------------|
| `POST /api/v1/templates/research-company` | Takes `company_name`, `client_id`, `industry_hint` → returns `CompanyKPIProfile` |
| `POST /api/v1/templates/commit` | Accepts KPIs with admin overrides → writes to KPI registry with `status=template` |
| MA agent `research_company_kpi_profile()` | 4 parallel Perplexity searches + 1 Sonnet synthesis → `CompanyKPIProfile` |
| `TemplateKPI` Pydantic model | `name, definition, unit, benchmark_low, benchmark_high, benchmark_source, confidence (filing/peer/inferred), domain, process_id` |
| `CompanyKPIProfile` Pydantic model | `company_name, industry_inferred, is_public, domains, template_kpis, research_sources, generated_at` |
| Supabase migration | Add `status TEXT DEFAULT 'active'`, `benchmark_range TEXT`, `benchmark_source TEXT` to `kpis` table |
| KPI Intelligence tab in Admin Console | 4-state UI: input → research progress → review table → commit confirmation |
| SA agent guard | Filter `status = 'active'` only; never evaluate `template` KPIs |
| Unit tests | MA search → synthesis round-trip; fallback to LLM-only when Perplexity unavailable; SA guard confirmed; commit writes correct status |

**Out of scope:** Accountability assignment during template review (Phase 12B). Automatic KPI → data source mapping. Template library persistence. Scheduled benchmark refresh.

**Success criteria:** Given a publicly traded company name, generates ≥10 relevant KPIs with benchmarks traceable to company-reported data. Admin completes flow in under 10 minutes. SA unaffected.

---

### Phase 12E: Company Intelligence-Driven Principal Templates

**Status:** Scoped 2026-06-04. Ready to build immediately after Phase 12A end-to-end validation passes. Estimated effort: ~9 hours focused work.

**Goal:** Given a company name, research its leadership team from public sources (10-K, proxy statements, investor relations, board pages) and generate template principal profiles ready for admin review. Admin confirms identities, enters emails (which are never inferred), and promotes individuals to active. Closes the "every principal is pre-loaded before first scan" gap in the registry-first onboarding flow — the sister phase to 12A.

**Positioning:** Replaces the blank-slate principal entry experience. Today, adding a CFO means typing their name, role, decision style, and assignments by hand for every client. Phase 12E pulls verifiable public information automatically and asks the admin to **confirm rather than create**. Stronger demo moment than KPI research alone because the demo audience IS the C-level exec — they see themselves in the system before they finish their coffee.

**Scope decisions adopted 2026-06-04:**
- **Decision 1 (no style inference):** MA agent does NOT infer `decision_style` or `communication_style`. Admin enters these fields manually after the principal has used Solution Finder and seen the different style outputs. Rationale: decision style hasn't been proven to meaningfully differentiate output for users; let them discover preference through SF rather than pre-commit based on LLM hypothesis.
- **Decision 2 (email optional at commit):** `email` column allows NULL on `principal_profiles`. PIB silently skips template principals or any principal with NULL email. Promotion to `status='active'` is gated on email entry.
- **Decision 3 (sequence):** Build immediately after Phase 12A end-to-end validation. Practice a complete 5-day onboarding run with a realistic company once 12E ships, to confirm the full registry-first onboarding flow is doable in 5 days.

**Pre-mortem mitigations (P1–P4):**

| ID | Risk | Mitigation |
|---|---|---|
| **P1** | Wrong CFO name presented to a prospect — embarrassing in front of named individuals | Per-principal source URL displayed in UI; confidence threshold ≥0.8 required for auto-accept (vs 0.6 for KPIs) |
| **P2** | Person left the company 6 months ago | "As of [source publication date]" stamp on every research record; admin can flag stale records for re-research |
| **P4** | GDPR/CCPA — even public info has consent dimensions | Store only public information; one-click delete from registry; never enrich beyond commercially-available sources; no photo/avatar enrichment |
| **P6** | Email pattern guessing — hard-blocked at every layer | `email` column allows NULL; UI does not offer guess buttons; PIB hard-skips NULL-email principals; LLM prompt explicitly forbids email generation |
| **P7** | Org chart inference from indirect signals | `reports_to` only populated when explicitly stated in a public source; otherwise NULL |

(P3 and P5 from initial draft removed — they covered decision-style inference risks, which Decision 1 eliminates.)

**User flow:**
1. Admin enters company name + role filter (default: CEO, CFO, COO, CTO, CHRO, CMO, CIO, CRO)
2. MA agent runs 4 targeted Perplexity searches in parallel:
   - Leadership listing — `{company} executive officers 10-K 2024 2025`
   - Proxy detail — `{company} DEF 14A proxy statement compensation`
   - IR / board page — `{company} board of directors investor relations leadership`
   - Strategic priorities by exec — `{company} CFO COO priorities investor day 2024 2025`
3. Sonnet synthesises into structured `CompanyPrincipalProfile` (name, role, tenure, source URLs, confidence — no inferred styles)
4. Admin reviews table:
   - Per row: accept/reject toggle
   - Email field is optional at commit; required at "Mark Active"
   - Decision style + communication style fields are NOT populated by research
5. Commit → writes to `principal_profiles` with `status='template'`
6. Promotion to `status='active'` requires explicit admin action AFTER email is entered

| Deliverable | Description |
|---|---|
| Supabase migration | Add `status TEXT DEFAULT 'active'`, `research_sources TEXT[]`, `confidence FLOAT`, and source URL column to `principal_profiles`; allow `email IS NULL` for templates |
| `TemplatePrincipal` Pydantic model | name, role, role_category, tenure_years, source_urls, confidence (no inferred style fields) |
| `CompanyPrincipalProfile` Pydantic model | company_name, template_principals, research_sources, generated_at, degraded |
| MA agent `research_company_principals()` | 4 parallel Perplexity searches + Sonnet synthesis → CompanyPrincipalProfile; mirrors 12A pattern |
| `POST /api/v1/templates/research-principals` | Takes `company_name`, `client_id`, optional `roles_filter` → returns `CompanyPrincipalProfile` |
| `POST /api/v1/templates/commit-principals` | Accepts principals with admin overrides → writes to `principal_profiles` with `status='template'` |
| `PATCH /api/v1/registry/principals/{id}/promote` | Promotes template to active after email is entered; rejects if email is NULL |
| Principal Intelligence tab in Admin Console | 4-state UI (input → researching → review → committed) mirroring KPI Intelligence; no style dropdowns; email field marked optional at commit, required at promote |
| PIB guard | Skip principals where `status='template' OR email IS NULL` — no briefings to non-active or contact-less principals |
| Login guard | Filter principal selector by `status='active' AND email IS NOT NULL`; templates only appear in Settings |
| SA / PCA guards | `get_principal_context` excludes `status='template'`; returns clean 404 if a template is referenced by id |
| Unit tests | MA round-trip; Perplexity-disabled degraded fallback; commit writes correct status; promote endpoint rejects on NULL email; PIB skips templates; login filter excludes templates |

**Out of scope:**
- HCM integration (Workday, BambooHR, ADP, etc.) — deferred to Phase 12F (concept)
- Email pattern guessing — NEVER, even with admin override
- Automatic `business_processes` assignment — Phase 12B's process templates feed this
- `kpi_line_preference` / `altitude` inference — admin sets manually based on principal preference
- Photo / avatar enrichment — privacy, out of scope
- Real-time leadership change monitoring — deferred to Phase 12J (concept)
- Decision style / communication style inference — explicitly rejected per Decision 1

**Success criteria:**
- Given a publicly traded company name, the system generates ≥4 C-level template principals with verified name, role, and tenure traceable to a public source URL.
- Admin completes the flow (review + commit) in under 5 minutes.
- PIB, login, and SA all correctly exclude template principals.
- Promotion to active is hard-gated on email entry (manually verified by attempting promote without email and confirming the 400 response).
- Multi-tenant isolation: client A's templates are never visible to client B.

**Prerequisite:** Phase 12A shipped (June 2026 — provides MA agent extension pattern, UI pattern, and `status='template'` precedent in code).

**Specific risks vs Phase 12A:**
- **Reputational** — Wrong CFO name in a demo damages trust more than a wrong KPI benchmark. The confidence threshold for auto-accept is tuned higher (0.8 vs 0.6).
- **Legal** — Public info ≠ unrestricted use. Consult counsel before shipping with paying customers; the M6-equivalent citation guardrail is stricter for individuals.
- **Currency** — Leadership changes faster than KPI definitions. The "as of date" stamp on every record is critical to manage user expectations.

---

### Phase 12B: Org-First Accountability Onboarding

**Goal:** Complement Phase 12A — when business process templates define KPI requirements, capture accountability during template selection rather than as a post-KPI interview step.

**Design:** Admin selects applicable business processes → templates show which principal is typically accountable for each → admin confirms or reassigns → accountability rows written to `kpi_accountability` directly. Phase 11B interview remains the tool for re-onboarding and gap resolution on existing registries.

| Deliverable | Description |
|------------|-------------|
| Process template → principal suggestion | During template review, each KPI shows a suggested accountable principal based on process ownership (COO → operations KPIs, CFO → finance KPIs) |
| One-step confirm | Admin confirms principal per KPI or reassigns; approved rows write directly to `kpi_accountability` |
| Integration with Phase 11B | Interview agent used for gap resolution only when template accountability is incomplete |

**Prerequisite:** Phase 12A (template KPIs in registry) + Phase 11A (kpi_accountability table).

---

### Phase 12C: Business Objectives Registry

**Goal:** Add Business Objectives as a first-class registry entity — the data foundation for the Business Optimization Agent's outer loop. Principals declare strategic objectives linked to KPI drivers. The system begins tracking progress without requiring any autonomous agent behaviour yet. This is the data model layer that all subsequent BO Agent phases depend on.

**Strategic context:** See `docs/prd/agents/a9_business_optimization_agent_prd.md` Phase A capabilities. This phase is the prerequisite for Phase 12D (objective health score) and the longer-term Phase B/C portfolio optimisation work. Without `business_objectives` as a first-class entity, the system has no way to steer the inner loop toward declared goals.

**Trust curve:** Phase 12C delivers visible value to principals immediately (objectives visible in the dashboard, situation cards annotated with which objective they affect) without requiring any autonomous AI decision-making.

##### Data Models

```python
class BusinessObjective(BaseModel):
    id: str                          # Natural semantic ID: "ebitda_margin_improvement"
    client_id: str                   # Strict tenant isolation
    name: str                        # "Improve EBITDA Margin to 15% by Q4 2026"
    description: Optional[str]
    target_value: float              # 15.0
    target_unit: str                 # "%" | "$M" | "days" etc.
    target_date: str                 # ISO date: "2026-12-31"
    owner_principal_id: str          # Who is accountable for this objective
    status: Literal["active", "paused", "achieved", "cancelled"] = "active"
    created_at: str

class ObjectiveKPIDriver(BaseModel):
    objective_id: str
    kpi_id: str
    client_id: str
    weight: float                    # 0.0–1.0; weights across all drivers for one objective must sum to 1.0
    contribution_direction: Literal["higher_is_better", "lower_is_better"]
```

| Deliverable | Description |
|---|---|
| `business_objectives` Supabase table | Composite PK `(client_id, id)`. Standard columns per model above. |
| `objective_kpi_drivers` Supabase table | Composite PK `(client_id, objective_id, kpi_id)`. FK to `business_objectives` and `kpis`. |
| `BusinessObjectivesProvider` | Supabase-backed, strict `client_id` scoping. Methods: `get_all(client_id)`, `get_by_id(objective_id, client_id)`, `get_drivers(objective_id, client_id)`, `upsert`, `delete`. |
| REST API — Objectives | `GET/POST/PUT/DELETE /api/v1/registry/business-objectives/` — standard CRUD with `client_id` query param. |
| REST API — Drivers | `GET/POST/DELETE /api/v1/registry/business-objectives/{id}/drivers/` — manage KPI driver mappings per objective. Driver weight validation: server-side check that `sum(weights) == 1.0` per objective before accepting. |
| Registry Explorer UI | New "Objectives" tab: list view with name, target, target date, owner, status, and driver count. Edit form with driver mapping table (KPI selector + weight slider + direction toggle). |
| `objective_id` on `SituationCard` | Add nullable `objective_id: Optional[str]` to `SituationCard`. SA assessment: after computing all situations, join each KPI against `objective_kpi_drivers` to populate `objective_id`. If a KPI drives multiple objectives, use the highest-weight objective. |
| SA severity enrichment | When `objective_id` is populated on a situation card, multiply the situation's computed severity score by `(1 + driver_weight)` — a KPI breach that is a high-weight driver of an active objective surfaces higher in the assessment results. Does not change threshold logic; only affects sort order and PIB priority. |
| Unit tests | 6 — CRUD round-trip; `client_id` isolation (Lubricants cannot see Hess objectives); driver weights rejected when sum ≠ 1.0; `objective_id` populated on situation card when KPI is a driver; `objective_id` is null when KPI has no declared objective; SA severity boost applied when `objective_id` present. |

**Prerequisite:** Phase 11A (`kpi_accountability` table already exists — same schema pattern). No dependency on Phase 12A or 12B.

---

### Phase 12D: Objective Health Score + Strategic Performance Summary

**Goal:** Compute a composite health score per objective at each enterprise assessment run, surface objective progress in the PIB, and add a Portfolio Objectives view to the dashboard. This completes the Phase A outer loop: principals can now see, in every briefing and in the main dashboard, whether the company is on track to hit its declared strategic goals — not just whether individual KPIs are breaching.

**Positioning:** This is the "Strategic Performance Summary" that differentiates Decision Studio from EPM tools (Anaplan, Workday Adaptive) which show plan vs. actuals but cannot autonomously diagnose why objectives are off-track or what to do about them. The objective health score connects individual KPI situations to strategic intent.

##### Objective Health Score Computation

| Concept | Detail |
|---|---|
| **Driver KPI status → score** | KPI in critical breach: `0.0`; warning breach: `0.5`; on-track: `1.0`; ahead of target: `1.25` (capped). Status read from SA assessment results for the current run. |
| **Composite score** | `composite = sum(driver.weight × kpi_score for driver in objective.drivers)`. Range: 0.0–1.25. |
| **Health thresholds** | CRITICAL (< 0.3), AT_RISK (0.3–0.6), ON_TRACK (0.6–0.9), AHEAD (≥ 0.9). |
| **Days to target** | For CRITICAL/AT_RISK: linear projection from current composite trend. If slope is positive: `days = (target_composite - current_composite) / slope`; if slope ≤ 0: `"Not on current trajectory"`. |
| **Trajectory direction** | Compare current composite to prior assessment: improving / stable / deteriorating. |
| **LLM narrative** | One-sentence Haiku-generated narrative per objective: "EBITDA Margin — primary driver (Gross Profit Margin) is in warning; two solutions active and on track." |

```python
class ObjectiveHealthScore(BaseModel):
    objective_id: str
    client_id: str
    assessed_at: str                      # ISO datetime
    health_score: Literal["CRITICAL", "AT_RISK", "ON_TRACK", "AHEAD"]
    composite_kpi_score: float            # 0.0–1.25
    driver_scores: Dict[str, float]       # kpi_id → individual score
    days_to_target: Optional[int]         # None when not on trajectory
    trajectory_direction: Literal["improving", "stable", "deteriorating"]
    active_solutions_count: int           # VA solutions contributing to this objective's KPIs
    narrative: str                        # LLM-generated 1-sentence summary
```

| Deliverable | Description |
|---|---|
| `VA.compute_objective_health(objective_id, client_id, assessment_results)` | New method. Takes the SA assessment results dict (already computed) + objective drivers from registry → returns `ObjectiveHealthScore`. No additional SQL queries — uses in-memory SA results. |
| `objective_health_scores` Supabase table | Persists one row per `(objective_id, assessed_at)`. Retain last 12 scores per objective for trend computation. |
| `latest_objective_health` on `business_objectives` | Denormalised `health_score VARCHAR(16)` updated on each assessment write — avoids JOIN on Portfolio Objectives list query. |
| `run_enterprise_assessment.py` integration | After SA scan and before PIB generation: compute `ObjectiveHealthScore` for all `status="active"` objectives of the client. Pass scores into PIB payload. |
| PIB — "Strategic Objectives" section | New optional PIB section. Trigger: at least one active objective exists. Content: card per objective showing name, target, health badge (CRITICAL/AT_RISK/ON_TRACK/AHEAD), composite score, days to target, active solutions count, narrative. Ordered: CRITICAL first, then AT_RISK, then ON_TRACK, then AHEAD. |
| Portfolio Objectives tab in UI | New tab in the main Decision Studio dashboard. Card grid: one card per active objective. Each card: name, owner, target + deadline, health badge, composite score sparkline (last 6 assessments), KPI driver pills (colour-coded by status), active solutions count. Click → objective detail drawer: full driver breakdown, health history, linked situations, linked VA solutions. |
| VA solution → objective contribution | `AcceptedSolution` gets optional `objective_ids: List[str]` — populated at registration when the solution's `kpi_id` is a driver of active objectives. Objective health score counts only solutions where `objective_ids` includes the objective being scored. |
| Unit tests | 7 — AHEAD when all drivers on-track; CRITICAL when primary driver in breach; composite weighted correctly across mixed driver statuses; days_to_target computed from positive trajectory; days_to_target returns null when trajectory is flat; PIB section renders when active objectives exist; PIB section omitted when no active objectives. |

**Phase 12D dependency graph:**

```
Phase 12C (business_objectives + objective_kpi_drivers) ──→ 12D (health score + PIB section)
Phase 11J (solution_health_reports) ───────────────────────→ 12D (active_solutions_count per objective)
SA assessment results (already computed per run) ──────────→ 12D (driver kpi scores — no extra queries)
```

**Build order:** Phase 12C must ship first. Phase 12D builds entirely on the objectives registry and the already-computed SA assessment results — no new data queries at health score time.

**Files to read before implementing:**
- `docs/prd/agents/a9_business_optimization_agent_prd.md` — full Phase A capability spec
- `src/agents/models/situation_awareness_models.py` — `SituationCard` model (add `objective_id`)
- `src/agents/new/a9_situation_awareness_agent.py` — `detect_situations()` return path (inject `objective_id`)
- `src/agents/new/a9_value_assurance_agent.py` — `register_solution()` (inject `objective_ids`)
- `scripts/run_enterprise_assessment.py` — insertion point for objective health computation

---

### Phase 13: Executive Briefing Quality + Principal-Adaptive Output

**Goal:** Elevate the Executive Briefing from "impressively close to MBB quality" to genuinely boardroom-ready: fix structural bugs, remove consultant jargon from display, restructure for a 2-minute CFO read, and adapt depth and tone by principal role.

**Pre-mortem mitigations (2026-05-30) — built in by design:**

- **M1 (multi-principal consistency):** All principals receive identical core facts and recommendation. Role adaptation controls entry point and depth only — never the conclusion. A full-view toggle is always available regardless of principal type. CFO and COO reading the same briefing independently must reach the same recommendation.
- **M2 (decision ask reliability):** `ImmediateAction` and `DecisionAsk` are defined as Pydantic fields in the SF synthesis response model before any UI is built. LLM compliance tested on ≥20 synthetic briefings. Decision ask capped at 25 words; hedge words (`consider`, `potentially`, `might`) rejected at schema validation. Do not build the UI component until schema compliance is confirmed.
- **M3 (firm name stripping):** Firm names (McKinsey, BCG, Bain) kept as internal reasoning anchors — they drive the debate structure. Stripped from top-level recommendation and options narrative only. Available in "View methodology" expand panel for transparency. Do not couple display fix to generation architecture.
- **M4 (CoI qualitative fallback):** Cost of Inaction is always shown — never blank. When `confidence = low` or calculation is unreliable, replace with: *"30-day projection: insufficient data for a reliable estimate — monitor [metric] weekly."* Never suppress; never show percentages above 1000%.
- **M5 (actions checklist schema first):** `ImmediateAction` Pydantic model (`action_text, owner, due_by, why_it_matters`) defined and schema-tested before the checklist UI component is written. If the LLM produces inconsistent action counts or missing owners, fix the prompt before touching the UI.
- **M6 (ROI range provenance):** Every ROI range links to a visible Assumptions panel showing key drivers (e.g., "Assumes 40–60% recovery of $132.7M DIY channel gap; excludes C&I Division"). A number without assumptions is not shown. This also resolves the CFO challenge scenario from the premortem.
- **M7 (data quality pressure):** Phase 13 is the forcing function for SA/DA data quality fixes. Better formatting makes weak underlying data more visible, not less. SA/DA fixes and Phase 13 UI changes should ship together.

#### Category 1 — Known bugs ✅ Complete (Jun 2026)

| Deliverable | File | Status |
|------------|------|--------|
| ~~Fix Cost of Inaction~~ | `ExecutiveBriefing.tsx` | ✅ `monthlyRate` capped at ±100%/yr; prevents astronomical projections from raw-dollar `percent_change` |
| ~~Fix duplicate recommendation~~ | `ExecutiveBriefing.tsx` | ✅ Duplicate rationale removed from Hero Card; shown once in Next Steps accordion |
| ~~Fix "Source: llm_knowledge"~~ | `ExecutiveBriefing.tsx` | ✅ `llm_knowledge` → "AI Knowledge Base"; `perplexity` → "Real-time Web Search" |

#### Category 2 — SF agent prompt rules

| Deliverable | File | Description |
|------------|------|-------------|
| Strip firm names from display narrative | `a9_solution_finder_agent.py` synthesis prompt | "BCG's Growth-Share Matrix" → "portfolio segmentation by volume and margin". Firm names retained as internal reasoning; available in "View methodology" panel |
| Cap ROI precision | SF synthesis prompt | Round ranges in output: "+$45M–$78M" not "+$45.0M to +$78.0M" |
| Cap paragraph length | SF synthesis prompt | Max 3 sentences per on-screen section; multi-clause sentences split |
| `DecisionAsk` structured output | `a9_solution_finder_agent.py` + `SFResponse` model | New field: `decision_ask: DecisionAsk` with `{decision_text (≤25 words), decision_owner, deadline, approval_type}`. Validated before display. |
| `ImmediateAction` structured output | `a9_solution_finder_agent.py` + `SFResponse` model | Replace prose action list with `List[ImmediateAction]`: `{action_text, owner, due_by_days, why_it_matters}`. Test LLM compliance on 20+ synthetic runs before building checklist UI. |
| Assumptions panel per ROI range | SF synthesis prompt + `SFResponse` model | Each option includes `List[str] key_assumptions` — 3–5 bullet drivers. Rendered as expandable panel in UI. |

#### Category 3 — Executive Briefing UI restructure

| Deliverable | File | Description |
|------------|------|-------------|
| Top block above the fold | `ExecutiveBriefingPage.tsx` | Always-visible: Situation (3 bullets max) + Decision ask (1 line from `DecisionAsk`) + Recommended path + Impact range. Above all detail. |
| CoI above recommendation | `ExecutiveBriefingPage.tsx` | Move Cost of Inaction block above the recommendation panel — it is the urgency anchor. "Doing nothing costs you $X by Q3." |
| Options tight table + drill-down | Strategic Options component | 5-column summary table (name, time, impact, risk, role in sequence). Full narrative (arguments for/against, stakeholder questions) in a side drawer on click — not all expanded inline. |
| Immediate Actions checklist | New `ImmediateActionsChecklist` component | Renders from `List[ImmediateAction]` schema. Owner chip + deadline badge + one-line "why it matters". Not built until schema compliance confirmed (M5). |
| Risk block: top 3 + expand | Risk section | Top 3 risks in main view with `stop/go` condition each. Remainder in "See all risks" expand. |
| Assumptions panel per option | New `AssumptionsPanel` component | Renders from `key_assumptions` field. Collapsed by default. Essential for CFO challenge scenario (M6). |
| Status Quo column in options table | Strategic Options table | Option 0 (Cost of Inaction baseline) with negative ROI, $0 cost, trajectory risk — gives a reference column. |
| Audit metadata footer | Briefing footer | `Model: Claude Sonnet 4.6 · Data: BigQuery YTD 2026 vs YTD 2025 · Council: McKinsey, Deloitte, Accenture, KPMG · Generated: [datetime] · Confidence: High` |

#### Category 4 — Principal-adaptive output

| Deliverable | File | Description |
|------------|------|-------------|
| Principal context in synthesis prompt | `a9_solution_finder_agent.py` synthesis prompt | Uses `principal_context.role`, `decision_authority`, `time_horizon` to vary evidence density and recommendation framing. C-level: decision-first, 5–8 bullets, business risk language. Director/manager: diagnostic depth, implementation tasks. |
| Role-adaptive depth in UI | `ExecutiveBriefingPage.tsx` | Detail sections collapsed by default for C-level (`principal_type = "individual"` + senior title); expanded for analyst/manager. Full-view toggle always accessible (M1). |
| Risk language by role | SF synthesis prompt | C-level: business risk + decision risk. Principal/manager: operational + analytical risk. Never hide uncertainty from any role. |

**Build order:** Category 1 bugs → Category 2 SF prompt + schema definitions → Category 2 schema compliance testing → Category 3 UI → Category 4 principal adaptation.

**Prerequisite:** `ImmediateAction` and `DecisionAsk` Pydantic models schema-tested before any Category 3 UI work begins.

---

### Phase 14+: Future (not scheduled)

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

---

### Infra C: SOC 2 Controls Foundation

**When:** Before first paying customer conversation that includes a security review (target Q4 2026). Not required for pilot demos — required before procurement, legal, or CISO review.

**Scope clarification:** This phase builds the *controls* that a SOC 2 Type II audit would assess — not the audit itself. The controls need to exist and be operational for several months before an audit firm can attest to them. Starting now means an audit is possible in H1 2027 if a customer requires it. Waiting until a customer asks means a 6-month delay at the worst possible moment in the sales cycle.

**What is NOT in scope here:** Infra B3 (database-level RLS isolation) and Infra B (Connection Profiles encryption + auth) are already planned as paying-customer blockers with their own sections. Those are the access-control and data-isolation controls. This phase covers the audit trail, availability, and operational visibility controls that are currently scattered or deferred with no target date.

---

#### C1: Audit Trail — Core Event Log

**Control category:** CC6 (Logical and Physical Access), CC7 (System Operations)

The `audit_events` table is already identified as an "enterprise compliance requirement" in Infra A5 Tier 3 but deferred to post-scale with no date. Moving it here gives it a delivery target before it's urgently needed.

| Deliverable | Description | Effort |
|------------|-------------|--------|
| `audit_events` Supabase table | Append-only. Columns: `id`, `client_id`, `principal_id` (nullable), `event_type`, `resource_type`, `resource_id`, `action`, `outcome` (success/failure), `ip_address` (nullable), `user_agent` (nullable), `metadata` (JSONB), `created_at`. No deletes — ever. | S |
| Event types (Phase 1) | `auth.login`, `auth.logout`, `auth.login_failed`, `solution.approved`, `solution.delegated`, `briefing.accessed`, `briefing.token_used`, `registry.record_created`, `registry.record_updated`, `registry.record_deleted` | S |
| `AuditService` utility | Single call site: `await AuditService.log(event_type, resource_type, resource_id, outcome, client_id, request)`. Fire-and-forget (non-blocking). One import replaces ad-hoc logging at each call site. | M |
| Wire into auth hooks | Auth login/logout/failure events → `audit_events` on every Supabase Auth callback | S |
| Wire into HITL approval | `solution.approved` → `audit_events` in `workflows.py` HITL Gate 2 block | S |
| Wire into registry CRUD | `registry.record_*` events on all `/api/v1/registry/` write endpoints | M |
| Wire into briefing token use | `briefing.token_used` + `briefing.accessed` in PIB token resolution | S |
| Admin Console — Audit Log panel | Table in Admin Console: filterable by `client_id`, `event_type`, date range. Read-only. Shows last 500 events. Paginated. | M |
| Retention policy | Supabase scheduled job: delete `audit_events` older than 2 years (SOC 2 standard retention). | S |
| Unit tests | 3 — `AuditService.log()` writes correct fields; auth hook fires on login failure; registry DELETE endpoint writes `registry.record_deleted` with correct `resource_id`. | M |

---

#### C2: Sign-In Audit (currently Login view item #11 — promoted here)

**Control category:** CC6.1 (Identification and Authentication)

This was tagged as S effort in the Login view UI Refinement Track but never prioritised. Moving it into this phase gives it a clear home.

| Deliverable | Description | Effort |
|------------|-------------|--------|
| Auth hook → `audit_events` | On every Supabase Auth `SIGNED_IN` / `SIGNED_OUT` / failed attempt callback: write `auth.login` / `auth.logout` / `auth.login_failed` to `audit_events`. Reuses `AuditService` from C1. | S |
| Failed-login rate alert | Backend: if `auth.login_failed` for the same `email` exceeds 5 in 10 minutes, log a `WARNING` and optionally notify platform admin. No lockout yet — warn only for first customers. | S |
| New device detection (future) | Flagged as Login view item #12. Deferred until MFA (below) is in place — they ship together. | — |

---

#### C3: Principal Lifecycle — Archive Instead of Delete

**Control category:** CC6.2 (User Provisioning and De-provisioning)

Currently identified in Settings → Principals tab item #7. Deleting a principal breaks the historical audit trail for every decision they approved or delegated. This is an SOC 2 control gap.

| Deliverable | Description | Effort |
|------------|-------------|--------|
| `status` field on `PrincipalProfile` | `"active"` \| `"inactive"` \| `"archived"`. Default `"active"`. Supabase migration: `ADD COLUMN status VARCHAR(16) DEFAULT 'active'`. | S |
| Archive instead of delete | `DELETE /api/v1/registry/principals/{id}` → sets `status = "archived"` instead of hard delete. Returns `200` with `{"archived": true}`. Hard delete removed from the API surface entirely. | S |
| Routing guard | SA agent `_get_relevant_kpis()` and PCA `get_principal_context*()` filter to `status = "active"` principals only. Archived principals cannot receive new briefings or decisions. | S |
| UI: collapsed Inactive section | Settings → Principals master table: active principals listed normally; `Inactive (N)` collapsed footer section showing archived records as read-only. | S |
| Historical attribution preserved | All `situation_actions`, `value_assurance_solutions`, and `audit_events` retain `principal_id` references. No cascade on archive. Historical decisions remain attributed. | (by design — no code change) |
| Unit tests | 2 — archived principal excluded from SA KPI scan; archived principal's historical `situation_actions` still queryable by `principal_id`. | S |

---

#### C4: Executive Briefing Audit Footer

**Control category:** CC4 (Monitoring Activities)

Currently Executive Briefing view item #16 in the UI Refinement Track. Promoted here because it's the CISO-facing artefact in a sales process — the briefing document that a CFO shows their security team needs provenance metadata.

| Deliverable | Description | Effort |
|------------|-------------|--------|
| Audit metadata on briefing footer | `Model: Claude Sonnet 4.6 · Data: BigQuery YTD 2026 vs YTD 2025 · Council: McKinsey, Deloitte, Accenture, KPMG · Generated: 2026-05-16 14:30 PM · Confidence: High` rendered in a monospace footer bar. Fields sourced from the `SituationAssessment` + `StrategySnapshot` models already in the briefing payload. | S |
| Same footer on printed PDF | CSS `@media print` ensures footer survives PDF export. | S |
| LLM prompt audit export (from Infra B2) | Export button on CouncilDebatePage: downloads full prompt/response log as JSON. Separate from briefing footer — for deep CISO review, not executive reading. Cross-reference with Infra B2. | M |

---

#### C5: Availability Monitoring

**Control category:** A1 (Availability)

**Decision (May 2026):** Sentry ($29/month) dropped in favour of free-tier tools that cover the same availability controls without a recurring cost. Revisit Sentry when a paying customer's SLA justifies it.

| Deliverable | Description | Effort |
|------------|-------------|--------|
| UptimeRobot monitor (config only) | Free account at uptimerobot.com. Add HTTP monitor pointing at `https://<railway-url>/health`. Check interval: 5 min. Alert channel: email to platform admin. No code required — the `/health` endpoint already exists. | S (config only) |
| Railway deployment alerts (config only) | Railway dashboard → Service → Settings → Notifications. Enable deployment failure + crash restart emails. Already available — just needs to be switched on. | S (config only) |
| Railway log viewer | All FastAPI unhandled exceptions already appear in Railway's built-in log viewer (searchable, filterable by severity). No code required at demo scale. | — (already available) |
| `workflow_errors` Supabase table | Structured error log for agent failures, LLM errors, and workflow exceptions. Already planned in Infra A5 Tier 1 (Error Log panel) — building it there avoids duplication. Cross-reference: Infra A5 Tier 1. | — (covered by A5) |

---

#### C6: MFA (Future — post-pilot)

**Control category:** CC6.1

Not required for first pilot but required for any enterprise customer running a formal procurement. Supabase Auth supports TOTP natively. Deferred until a prospect asks for it.

| Deliverable | Description | Effort |
|------------|-------------|--------|
| TOTP enrollment flow | Supabase Auth MFA API. Per-tenant `mfa_required` flag. Enrollment UI on first login after flag is set. | L |
| MFA enforcement middleware | Backend JWT middleware checks `amr` claim for MFA factor. Rejects requests without MFA factor when tenant has `mfa_required = true`. | M |
| Backup codes | Standard TOTP recovery codes. Stored hashed in Supabase. | M |

---

#### Sequencing and delivery

**Build order within Infra C:**

| Order | Item | Why this order |
|---|---|---|
| 1 | C1 (`AuditService` + `audit_events` table) | Everything else in this phase writes to it |
| 2 | C2 (sign-in audit hook) | Smallest addition once C1 exists; immediately SOC 2 relevant |
| 3 | C5 (Sentry + uptime) | Independent of C1; small effort; closes the availability gap now |
| 4 | C3 (principal archive) | Backend-only change; no UI dependency; closes the de-provisioning gap |
| 5 | C4 (briefing audit footer) | UI change; needs existing briefing payload fields confirmed |
| 6 | C6 (MFA) | Only when a prospect requires it |

**Relationship to other Infra phases:**

```
Infra B  (auth + JWT middleware)     ──→ C2 (auth hook fires on Supabase Auth events)
Infra B3 (RLS + provider isolation)  ──→ C1 (audit_events also scoped by client_id)
Infra A3 (usage_events table)        ──→ C1 (audit_events is a separate table — append-only immutable log vs. mutable usage counters)
Infra A5 (Admin Console)             ──→ C1 (Audit Log panel is Tier 1 in Admin Console once audit_events exists)
```

**Controls inventory for a future auditor:**

| SOC 2 Control Domain | Control | Delivered by |
|---|---|---|
| CC6.1 — Authentication | Email + password auth, JWT session | Infra B |
| CC6.1 — Authentication | Sign-in audit log | **Infra C2** |
| CC6.1 — MFA | TOTP per-tenant | **Infra C6** (future) |
| CC6.2 — User provisioning | Archive-not-delete principal lifecycle | **Infra C3** |
| CC6.3 — Access restrictions | RBAC (admin vs. non-admin) | Infra B (Connection Profiles role-gating) |
| CC6.6 — Data isolation | RLS on all registry tables | Infra B3 |
| CC6.6 — Credential encryption | AES-256 at rest for connection profiles | Infra B |
| CC7.2 — System monitoring | Railway log viewer + workflow_errors table (Infra A5) | **Infra C5 / A5** |
| CC4.1 — Monitoring activities | Briefing provenance metadata | **Infra C4** |
| A1.2 — Availability monitoring | UptimeRobot (free) + Railway deployment alerts | **Infra C5** |
| CC2.2 — Audit trail | Append-only event log | **Infra C1** |
| CC2.2 — Audit trail | LLM prompt export | Infra B2 |
