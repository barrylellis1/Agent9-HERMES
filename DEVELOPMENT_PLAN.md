# Agent9-HERMES Development Plan

**Created:** 2026-03-14
**Last updated:** 2026-07-22
**Status:** Active

---

## Where We Are — July 2026

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
| Capability-aware LLM layer (Phase 11O) — per-model capability map (temperature/effort/fallbacks), Sonnet 5 routing default for reasoning/synthesis/briefing, refusal handling, product system prompt decoupled from dev-era Cascade guardrails | Production-ready (Jul 2026) |
| DA tenant-scoped KPI resolution — `_lookup_kpi_scoped` strict isolation at all 3 DA lookup sites (contract path, plan dims, execute); no cross-tenant same-id fallback; 5 regression tests | Production-ready (Jul 2026) |

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
| RACI Accountability Model (4-role R/A/C/I, KPI + Business-Process level, BP→KPI cascading; redefines the original 2-role/KPI-only design) | Phase 12B |
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
| ~~Database-level multi-tenant isolation~~ | ✅ Infra B3 — complete and verified live in production (RLS via `a9_tenant_scope` role on 12 tables, `tenant_scope()` transaction helper, provider `get_by_client()`, DGA gate in DPA `execute_sql`, composite-delete fix) |
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
- **Accountability is a routing/escalation axis, not a visibility gate** — RACI role (Responsible/Accountable/Consulted/Informed) determines *how* a KPI surfaces (actively, included, digest-only), never whether it's hidden outright; an unassigned KPI/business-process is visible to everyone by default (fail-open), never silently excluded
- **No snooze/hide preference layer** — correct signal routing eliminates noise at source
- **LLM-assisted accountability import** — HCM documents are the source of truth; LLM extracts, human confirms (same pattern as KPI Assistant)
- **Brand: "Decision Studio"** — Swiss Style, monochrome dominance, semantic color only, "Quiet Expert" voice
- **Domains:** decision-studios.com (brand) + trydecisionstudio.com (demo/trial)

Full accountability model: `docs/architecture/kpi_accountability_model.md` (original 2-role, KPI-only
design) and `docs/architecture/raci_accountability_model.md` (4-role RACI, KPI + Business-Process
level, redefines Phase 12B)

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

> ⚠️ **Number collision — there are TWO Phase 10D entries.** This one (complete, Apr 2026) and the
> open *MCP Abstraction Layer* below. Deliberately not renumbered: "Phase 10D" appears across ~15
> files referring to both, so a renumber would invalidate more cross-references than it fixes.
> References in `roadmap.md`, `realism_and_timeline.md` and `agent9_executive_summary.md` mean
> *this* one.

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

> ⚠️ **Number collision — see the completed *Solution Finder Performance Tuning* Phase 10D above.**
> The four `PHASE_10D_*.md` documents, `data_connectivity_strategy.md`, the Data Product and LLM
> Service PRDs, and the connectivity-tier strategy docs all mean *this* one.

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

> **Absorbed into Phase 15 Stage B (2026-07-21).** This typed assumption model is now the *canonical* SF assumption object, defined once as part of the unified `SFResponse` schema alongside `DecisionAsk`/`ImmediateAction` and extended with `grounded_vs_inferred` + `provenance` (Phase 15's "bets on" list and calibrated confidence are the same object — do not build a second one). Build it in Phase 15 Stage B, not separately here. Phase 11J retains only its monitoring/drift work (P2 onward), which *consumes* this schema. The model below stays as the reference spec.

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

### Phase 11O: LLM Model Routing Modernization + Fable 5 A/B ✅ COMPLETE (Jul 2026)

**Outcome:** 11O-A and 11O-B shipped; 11O-C experiment closed with adoption deferred — Sonnet 5 is the routing default for all interactive surfaces; Fable 5 is earmarked for the offline/background DA-SF path when Phase 11M/11N ships (config-only change thanks to 11O-A). Two side discoveries fixed along the way: DA cross-tenant KPI fallback (commit 5925de7) and the Cascade-guardrail system-prompt leak (commit 92619b0).

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

**11O-C evidence from the same run:** Fable won on quality AND latency at ~3× cost — promising but the input was degraded (empty where_signals), so the decision gate stayed open pending one confirmatory round on a segment-rich DA output. Two anomalies logged from the run: (1) lubricants DA returned an empty Is/Is-Not table; (2) ~13 Snowflake SQL compilation errors fired at the end of the run despite lubricants being BigQuery-backed. **Both resolved (2026-07-13, commit 5925de7) — shared root cause:** three clients share KPI id `gross_margin_pct`; DA's lookups matched display name only, always missed, and fell back to an unscoped `provider.get(id)` that returned another tenant's record → wrong `data_product_id` → Snowflake backend for a BigQuery client → every dimension query failed → empty table. A second leak defaulted `_contract_path_for_kpi` to the bicycle FI contract on a miss. Fixed with `_lookup_kpi_scoped(kpi_ref, client_id)` (id-or-name match, strict tenant isolation, scoped miss returns None) applied at all 3 lookup sites; verified 19/19 queries route to BigQuery, where_is 0 → 41 segments, zero Snowflake errors; 5 regression tests. This unblocked the segment-rich confirmatory round (11O-C round 3 below).

| Deliverable | Description |
|---|---|
| Routing table update | `REASONING` / `SYNTHESIS` / `GENERAL` (+ `SOLUTION_FINDING`, `BRIEFING`) → `claude-sonnet-5`. `STAGE1_PERSONA` / `NLP_PARSING` / `SQL_GENERATION` stay on Haiku 4.5. |
| Stage 1 determinism check | Sonnet 5 rejects non-default sampling; Stage 1 stays on Haiku 4.5 (temperature 0.0 preserved) — no change, but verify the capability map doesn't strip Haiku's temperature. |
| A/B validation | Run the Lubricants gross-margin scenario end-to-end (DA → SF full debate) on Sonnet 4.6 vs Sonnet 5 with identical inputs. Compare: synthesis rationale specificity, recovery_range plausibility, consistency-check pass rate, latency, token cost. |
| Regression gate | Unit suite matches the 941a425 baseline (508 pass; the 2 pre-existing failures tracked separately). |

**Scope:** S. Rollback = one env var (`CLAUDE_MODEL_SYNTHESIS=claude-sonnet-4-6`).

#### 11O-C: Fable 5 Gated Experiment ✅ CLOSED — adoption deferred to background DA/SF (Jul 2026)

**Three A/B rounds run (2026-07-13), all on lubricants gross_margin_pct with frozen DA + identical synthesis inputs per round:**

| Round | Input shape | Sonnet 5 | Fable 5 |
|---|---|---|---|
| 1 | Degraded DA (empty segments, data contradiction) | Epistemically careful but underpowered ("audit the data first"), 139s | Flagged the contradiction AND made the call; sharpest inference; 111s |
| 2 | Segment-rich DA, no Stage 1 (non-production shape) | Hit SF's 16384 max_tokens — truncated to 2 options | Complete 3-option briefing, 9.2K tokens, 115s |
| 3 | **Production-shaped** (41 segments + MBB Stage 1) | Complete, high quality: cost audit + pricing recalibration, 12–22pp anchored recovery, 114s, ~$0.14 | Complete, modestly sharper: used the internal benchmark (High Mileage Engine Oil +15pp) as replication anchor, explicit lever-risk causality, 111s, ~$0.60 |

**Verdict against the decision gate:** on clean production-shaped input, Fable is modestly better — not visibly 3× better. On degraded/contradictory input, Fable is clearly the strongest reasoner. Fable's natural home is therefore the **offline enterprise assessment** (messy data, latency-insensitive, quality-is-the-deliverable) — but that pipeline is SA-only today (DA/SF are HITL). **Decision: keep Sonnet 5 as the routing default; revisit Fable adoption when background DA/SF execution ships (Phase 11M/11N)** — at that point set `CLAUDE_MODEL_SYNTHESIS=claude-fable-5` on the scheduled path only. The capability layer (11O-A) makes that a config change.

**Watch item:** Sonnet 5 synthesis outputs run 11–16K tokens (vs Fable's ~9K) — round 3 used 11.2K of the 16384 cap. The cap only truncated on a non-production input shape, but headroom is thin; consider raising SF synthesis `max_tokens` to ~20000 defensively.

**Deferred (optional):** the loosened-scaffolding Fable variant (Phase 12 prompt constraints relaxed) — run if/when Fable adoption is activated.

**HITL conversational A/B addendum (2026-07-13):** dossier-driven simulated-CFO harness (frozen 6-turn refinement transcript + per-turn next-question replay; 3 hard tier-3 briefing Q&A probes). Results: Fable's questions modestly sharper (hypothesis-led, builds on captured facts instead of re-asking) but ~19s/turn vs Sonnet 5's ~10s/turn — a worse chat UX; Sonnet 5 won briefing Q&A outright (faster, format-compliant). **Fable also leaked `PLAN:/VERIFIED_ACTION:` scaffold into a customer-facing answer — root cause: the runtime was loading `docs/cascade_guardrails.yaml` (development coaching for the Windsurf/Cascade coding assistant, never a product prompt) as its default system prompt. Fixed by decoupling: product default now lives in code (`A9_DEFAULT_SYSTEM_PROMPT`, claude_service.py); the YAML is preserved untouched as a dev artifact the product never reads.** Conclusion reinforced: Sonnet 5 for all interactive surfaces; Fable's home is offline synthesis. Prompt-quality findings feed `docs/architecture/llm_prompt_redesign_da_sf.md` (Phase 13 Category 2/4 umbrella).

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

### Phase 12F: Business Process Template Generator ✅ COMPLETE (July 2026)

**Status:** Shipped 2026-07-22. Backend (MA extension + API routes + unit tests), embedded wizard panel (Day 3, before KPI Library), standalone Intelligence-nav page all in place.

**Goal:** Give every new client a governed business-process taxonomy at onboarding time, instead of onboarding with zero `business_processes` rows (discovered live-testing the onboarding wizard — Context Explorer showed 0 business processes for a practice client despite 19 active KPIs). This is a **prerequisite for Phase 12B**, not the other way around implied by earlier doc ordering — 12B's "templates show which principal is typically accountable for each process" assumes real process templates already exist.

**Design:** Unlike Phase 12A, no external research is needed. A canonical taxonomy of 39 business processes across 12 domains already existed (`src/registry/canonical/business_processes.py`, already used by `scripts/onboard_client.py` for scripted seeding) — this is genuinely the ~80% common ground across Agent9's Mid-Market ICP referenced in earlier product discussions. The LLM's job is pure selection: given the client's stored company profile (industry), select the relevant canonical subset and propose a small number of industry-specific extras. Canonical selections are always hydrated server-side from `BP_BY_ID`, never trusted verbatim from the LLM response, so the canonical taxonomy stays the actual single source of truth for their content.

| Deliverable | Description |
|------------|-------------|
| `POST /api/v1/templates/research-business-processes` | Resolves client_id server-side (never trusts the request body — a stricter pattern than 12A's `/commit`, see below); MA agent selects canonical + extra processes |
| `POST /api/v1/templates/commit-business-processes` | Writes accepted processes directly to `business_processes` — no template/active lifecycle, a committed process is immediately valid |
| MA agent `research_company_business_processes()` | 1 LLM call (no search) → `CompanyBusinessProcessProfile` |
| `BusinessProcessIntelligence.tsx` | Same 4-state flow as `KPIIntelligence.tsx`; embedded as the first of two panels sharing Day 3's route (`day3SubStep`), plus a standalone Intelligence-nav page |
| Unit tests | Canonical hydration verbatim from `BP_BY_ID` even with a mismatched LLM echo; extras colliding with canonical ids dropped; degraded fallback; commit idempotency; cache-mirroring |

**Real bug found and fixed during build:** the raw-SQL commit pattern this mirrors from 12A (`kpi_templates.py`) bypasses `DatabaseRegistryProvider`'s in-memory cache entirely — a newly committed row was invisible to every `registry.py` list endpoint (Context Explorer, the accountability interview) until the backend process restarted. Fixed here by mirroring new rows into the live provider's cache via `_cache_item()` on a genuine write, skipped on `skipped_duplicate` to avoid clobbering hand-edited existing rows. **12A likely has the same latent bug — flagged as a fast-follow, not fixed in this phase.**

**Deliberate divergence from the 12A precedent:** `kpi_templates.py`'s `/commit` trusts the request body's `client_id` outright (confirmed by reading the endpoint — no auth check, no query-param validation). Given this project's tenant-isolation rules, the new commit endpoint instead resolves the authoritative client_id server-side via `_resolve_create_client_id` (registry.py's existing helper) — an authenticated user's own client_id, or a validated `client_id` query param, never the body. **Backporting this to `kpi_templates.py` is a fast-follow, out of scope here.**

**Out of scope:** Process hierarchy (`docs/architecture/business_process_hierarchy_blueprint.md`'s `parent_id` model — separate, unimplemented future design). Retrofitting existing clients that onboarded before this shipped (no backfill script). Folding `business_processes_count` into the `kpi_library` progress-step's `complete` gate (informational field only — would retroactively mark already-onboarded clients incomplete).

**Prerequisite:** None — the canonical taxonomy and `business_processes` table/RLS already existed.

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

### Phase 12B: RACI Accountability Model

**Redefined 2026-07-25** — this phase's original design (single `accountable` role, KPI-only,
inferred purely from business-process template selection) is superseded. Live testing exposed why:
onboarding `brookshire_brothers`, a KPI-only strict-accountability model silently hid 5 real,
correctly-configured KPIs from every principal (see incident writeup in the new doc below), and a
follow-on design conversation concluded that ownership-gated visibility itself fights the theory
layer's cross-KPI correlation value proposition and the realistic ICP workflow (FP&A analyst
steward → VP → executive, not exec-navigates-everything).

**Full design:** `docs/architecture/raci_accountability_model.md` — 4-role RACI
(Responsible/Accountable/Consulted/Informed) applied at both KPI and Business-Process level, with
BP-level assignments cascading to KPIs by default; ownership becomes a routing/escalation axis, not
a hard visibility gate (graduated R/A/C/I visibility replaces binary include/exclude); generalizes
`kpi_accountability` to a `subject_type`/`subject_id` shape rather than duplicating it per subject
type. See that document for the full data model, governance rules, and phase deliverables table.

**Prerequisite:** Phase 12A (template KPIs in registry) + Phase 11A (kpi_accountability table) + **Phase 12F (business process templates — shipped July 2026; RACI's BP-level assignments assume real `business_processes` rows exist, which nothing created before 12F)**.

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

> **Status reconciled at Phase 15 close (2026-08-16).** Cat 2 shipped as Phase 15 Stages A–B and
> Cat 4 as Stage C. **Cat 3 — the briefing UI — is what returns here from Phase 15 Stage G**, which
> was always scoped as "Phase 13 Cat 3 + Cat 4 + Phase 15". Two entries were describing the same
> unbuilt UI from opposite directions; this is now the single owner.
>
> ✅ **Cat 3 BUILT 2026-08-16.** See the Cat 3 table and the build notes below it. Remaining in this
> phase: Cat 4's one UI item (role-adaptive collapse depth), deliberately deferred.
>
> ✅ **The M3 / Phase 18 conflict is settled — Phase 18's position wins, on the briefing surface.**
> M3 (May 2026) said keep firm names as internal reasoning anchors and strip them from display only;
> Phase 18 (Aug 2026) said firm identity should stop being a product feature at all. Decided in
> favour of Phase 18 for this page specifically, on the ground that the briefing is the artifact an
> executive exports to PDF and forwards — the worst place to carry a real firm's legal name over
> analysis that firm did not produce. M3's *substantive* point is kept: the persona id remains the
> reasoning anchor inside the prompt, and the display label now names the analytical tradition the
> persona encodes ("Portfolio & unit economics") rather than blanking it out. Generation is
> unchanged. Scope is the briefing only — the persona picker, council presets, `CouncilDebate.tsx`
> and `DeepFocusView.tsx` remain Phase 18 Category C.
>
> M1 below is also the invariant Phase 15 Stage J cites; it originates here.

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

> **Umbrella design (Jul 2026):** `docs/architecture/llm_prompt_redesign_da_sf.md` — structured outputs (API-guaranteed schemas replacing the hand-built JSON template + ~12 format MUST-rules), a principal/business context contract injected at BOTH SF stages with explicit consumption instructions, strict-tenancy business context (no generic fallback), refinement-interviewer value-of-information rules, and token-cap fixes (synthesis 16384→20000, QA 800→1200). The deliverables below are subsumed by / sequenced within that design. Evidence base: Phase 11O A/B rounds + HITL replay A/B.

> **Reconciliation (2026-07-21):** This category is **Stages A–C** of the unified SF build spine in **Phase 15**. Its structured-output migration and `SFResponse` schema are the single foundation that also carries Phase 11J P1's typed `SolutionAssumption` and Phase 15's "bets on" + calibrated-confidence fields — **one schema, one M2/M5 compliance gate**, not three rewrites. The `key_assumptions` field below becomes the typed `List[SolutionAssumption]` (see Phase 15 Stage B). Build order and gates: see Phase 15.

> 🔴 **CORRECTION (2026-08-16): the first deliverable below was NEVER BUILT, despite this category
> being recorded as shipped via Phase 15 Stages A–B.** Stages A–B were the structured-output schema;
> the firm-name prompt rule was not part of them and no equivalent instruction exists anywhere in
> `a9_solution_finder_agent.py`. Caught by a live e2e run, not by review: the briefing rendered
> *"This is **Bain's** Full Potential Transformation applied as a multi-year margin-architecture
> reset"* straight out of `options_ranked[2].description`, with `opt1.rationale` and the
> recommendation rationale both citing *"McKinsey's MECE cost-driver framing"* and `opt2.rationale`
> opening *"BCG's Growth-Share/Experience-Curve lens argues…"*.
>
> The prompt does not merely fail to forbid this — it **invites** it. Line ~1352 builds
> `framework_lines` from each persona's name plus the fallback text *"Apply signature frameworks and
> expertise"*, so the model is told to apply a named firm's signature method and then writes that
> sentence.
>
> **Consequence for Phase 18:** Category C is NOT closed by Cat 3's UI de-branding. Removing the
> chrome while the generated prose still names firms moves the exposure from a label the UI controls
> into free text nobody screens. A prior run of the same pipeline rendered clean, so this is
> intermittent — which makes it worse to rely on, not better.

| Deliverable | File | Description |
|------------|------|-------------|
| 🔴 **Strip firm names from display narrative — NOT BUILT** | `a9_solution_finder_agent.py` synthesis prompt | "BCG's Growth-Share Matrix" → "portfolio segmentation by volume and margin". Firm names retained as internal reasoning; available in "View methodology" panel. **Verified absent 2026-08-16 and observed leaking to a rendered briefing.** The `live-briefing-cat3*` specs' firm-name sweep is the regression test |
| Cap ROI precision | SF synthesis prompt | Round ranges in output: "+$45M–$78M" not "+$45.0M to +$78.0M" |
| Cap paragraph length | SF synthesis prompt | Max 3 sentences per on-screen section; multi-clause sentences split |
| `DecisionAsk` structured output | `a9_solution_finder_agent.py` + `SFResponse` model | New field: `decision_ask: DecisionAsk` with `{decision_text (≤25 words), decision_owner, deadline, approval_type}`. Validated before display. |
| `ImmediateAction` structured output | `a9_solution_finder_agent.py` + `SFResponse` model | Replace prose action list with `List[ImmediateAction]`: `{action_text, owner, due_by_days, why_it_matters}`. Test LLM compliance on 20+ synthetic runs before building checklist UI. |
| Assumptions panel per ROI range | SF synthesis prompt + `SFResponse` model | Each option includes `List[str] key_assumptions` — 3–5 bullet drivers. Rendered as expandable panel in UI. |

#### Category 3 — Executive Briefing UI restructure ✅ Built 2026-08-16

| Deliverable | File | Status |
|------------|------|--------|
| Top block above the fold | new `components/briefing/DecisionAskBlock.tsx` | ✅ Situation (≤3 bullets: problem + top 2 variance contributors with their dimension labels) + `DecisionAsk` + recommended path + impact range. Screen-only — print already opens with its own Flash Briefing |
| CoI above recommendation | `ExecutiveBriefing.tsx` | ✅ **was already satisfied** — the banner has sat above the hero card since Cat 1. No change needed |
| Options tight table + drill-down | new `components/briefing/OptionDetailDrawer.tsx` | ✅ Narrative (arguments for/against, stakeholder perspectives, prerequisites, triggers) moved behind "View full analysis" into a right-hand drawer; Esc + backdrop close. **Print keeps the narrative inline** — there is no drawer to open on paper |
| Immediate Actions checklist | new `components/briefing/ImmediateActionsChecklist.tsx` | ✅ Owner chip + deadline badge + "why it matters". A missing owner renders visibly as *unassigned* rather than being filled in — M5 puts that fix in the prompt, not the component |
| Risk block: top 3 + expand | `ExecutiveBriefing.tsx` | ✅ Top 3 + "See all N risks". **`stop/go` condition per risk NOT built — no field backs it** (see notes) |
| Assumptions panel per option | new `components/briefing/AssumptionsPanel.tsx` | ✅ grounded/inferred split, confidence, `validated_by`, provenance. Collapsed on screen, **always expanded in print** — M6 has to hold on the copy that gets forwarded and challenged |
| Status Quo column in options table | `ExecutiveBriefing.tsx` | ✅ Option 0 derived by `deriveStatusQuo()` from the same `kpiData` slice the CoI banner projects from. Leads the table as the reference column, and is **excluded from `axisDiscrimination`** (see notes) |
| Audit metadata footer | `ExecutiveBriefing.tsx` | ✅ KPI · Data (source system + resolved window + version, from `MeasurementContext`) · Council (de-branded) · Model · Confidence · Generated. **Every field read from the payload** — the spec's example line named a specific model version and data window; hardcoding either would make the audit strip assert something no run established |

**The finding that set the build order.** The schema fields were being *produced and then dropped one
`map()` short of the screen*, not missing from the backend. The synthesis JSON template already
requests `decision_ask` and `immediate_actions`
(`a9_solution_finder_agent.py:1638-1646`) and `_parse_decision_ask`/`_parse_immediate_actions` read
them back on the **shared** path — so none of this waited on the `use_structured_output` flip.
`workflows.py:380` `model_dump()`s the whole response. But `buildExecutiveBriefing` never carried
`decision_ask` or `immediate_actions`, and its per-option map dropped `key_assumptions` and
`flagged_side_effects`. That plumbing was step 0; every component was blocked on it.

**Evidence the fields are actually populated, not just typed:** `decision_quality.py`'s
`l6_commitment` passes only when `decision_ask.decision_text` **and** `decision_owner` **and** a
non-empty `immediate_actions` are all present — and Phase 15 closed at **13/13** on link 6. Stage E's
`flagged_side_effects` now render on the option card (count) and in the drawer (full list); they had
been parsed, typed and carried through the API without ever reaching a screen.

**Three spec deviations, each deliberate:**
1. **No `stop/go` condition per risk.** Nothing in the payload carries one. Risks are assembled from
   `blind_spots` and `unresolved_tensions`, whose mitigations are already keyword-derived in
   `briefingUtils`; generating a stop/go gate on top of that would be a fabricated control sitting in
   the section a reader trusts most. The recommended option's `implementation_triggers` are the real
   article and already render in the drawer.
2. **No "role in sequence" column.** Same reason — no per-option field expresses it. The table keeps
   Strategy / Est. ROI / Investment / Timeline / Reversibility / Risk, all payload-backed.
3. **Option 0 is excluded from the `axisDiscrimination` calculation.** Its values differ from every
   proposal almost by construction ($0 investment, a negative return), so folding it in would turn
   "all three proposals score the same here" into a cheerful "3 of 4 distinct" and suppress the exact
   finding that annotation was built (Aug 2026, off live briefings) to make.

**Also fixed in passing:** the hero card's duplicate recommendation title and owner/deadline row
(both now live in the block above it — the same duplication Cat 1 removed once already); the
hardcoded "Three strategic pathways" intro, which said three regardless of how many the run produced;
and a `print:`-variant trap — the Export button rasterises the live DOM through html2pdf and sees no
print media, so collapsed risk rows needed an explicit `.risk-overflow-row` rule in the
pdf-export-mode stylesheet or the PDF would have silently shipped a shorter risk list than the screen.

**Not built, and why:** Cat 4's role-adaptive collapse depth. It adds a principal-dependent render
path that cannot be confirmed in the same walkthrough as everything above, and Cat 4's substantive
half (prompt-side adaptation) already shipped in Stage C.

#### Category 4 — Principal-adaptive output

| Deliverable | File | Description |
|------------|------|-------------|
| Principal context in synthesis prompt | `a9_solution_finder_agent.py` synthesis prompt | Uses `principal_context.role`, `decision_authority`, `time_horizon` to vary evidence density and recommendation framing. C-level: decision-first, 5–8 bullets, business risk language. Director/manager: diagnostic depth, implementation tasks. |
| Role-adaptive depth in UI | `ExecutiveBriefingPage.tsx` | Detail sections collapsed by default for C-level (`principal_type = "individual"` + senior title); expanded for analyst/manager. Full-view toggle always accessible (M1). |
| Risk language by role | SF synthesis prompt | C-level: business risk + decision risk. Principal/manager: operational + analytical risk. Never hide uncertainty from any role. |

**Build order:** Category 1 bugs → Category 2 SF prompt + schema definitions → Category 2 schema compliance testing → Category 3 UI → Category 4 principal adaptation.

**Prerequisite:** `ImmediateAction` and `DecisionAsk` Pydantic models schema-tested before any Category 3 UI work begins.

**Remaining in Phase 13:** Cat 4's role-adaptive UI depth (collapse-by-default for C-level with an
always-available full-view toggle, M1). Everything else in the phase is closed.

**Verification state (2026-08-16).** `npm run build` passes; the 94-test mocked e2e suite
(`briefing-*`, `debate-moderator-render`) passes unchanged, so the DOM restructure broke no existing
assertion. Two LIVE runs were driven end to end against lubricants / `cfo_001` on BigQuery:

| | control (`live-briefing-cat3.spec.ts`) | refinement arm (`live-briefing-cat3-refined.spec.ts`) |
|---|---|---|
| refinement interview | skipped | conducted — 9 refine calls, 6 topics, 2 constraints captured |
| decision ask | present, 16 words | present, 16 words |
| immediate actions | 4 payload / 4 rendered | 4 / 4 |
| assumptions panels | 3 / 3 | 3 / 3 |
| critic side-effect chips | 3 / 3 | 3 / 3 |
| Option 0 column | present | present |
| firm names on page | none | 🔴 **"Bain" leaked** (see Cat 2 correction) |
| result | **passed** | **failed** on the firm-name sweep only |

Every payload-vs-DOM count matched in both arms — the four fields that were being dropped now reach
the screen, on real output. Stage E's critic findings rendered for the first time since they shipped
in July.

**Still not verified:** the two export paths (Print and html2pdf Export) against a collapsed risk
section, and an absent-`decision_ask` run (both live runs produced one, so the honest-absence path
has still never rendered). Neither is reachable from an automated run without fabricating input.

**Decision Quality (`scripts/score_dq_run.py`, new — wraps `decision_quality.score_run`):**

| link | control | refinement arm |
|---|---|---|
| L1 frame *(advisory screen)* | **FAIL** | **FAIL** — identical detail text |
| L2 alternatives | PASS (cost_audit, pricing_corridor) | PASS (pricing_corridor, volume_for_margin) |
| L3 information | PASS | PASS |
| L4 tradeoffs *(advisory screen)* | PASS | PASS |
| L5 reasoning | not-checked (no DA captured) | PASS |
| L6 commitment | PASS | PASS |
| chain | FAIL, capped by frame | FAIL, capped by frame |

**The refinement interview did not move link 1.** Both arms fail it with the same finding — *"every
option recovers the breached KPI within its existing structure"* — even though the interview ran
properly and fed two real constraints into Stage 1. This is evidence for, not against, Phase 15's
decision to hand frame to **Phase 19** rather than expect the existing refinement step to fix it: the
one framing intervention the product ships today does not widen the frame.

Read the 80% → 83% difference as instrumentation, not improvement: the control simply did not capture
a DA payload, so its L5 was not-checked. Caveats that matter: **n=1 per arm**, the interview was
answered by clicking the first suggested response each turn (a scripted respondent, not a person),
and L1/L4 are advisory term screens the rubric records at a 71% false-positive rate — they want human
adjudication, which is why the scorer prints their matched terms and does not gate on them.

---

### Phase 15: LLM Trust & Trustworthy Solution Generation

> **Numbering note:** Phase 14+ below is the reserved *unscheduled Future* bucket, so this scheduled body of work takes the next free number, 15.

**Goal:** Make Solution Finder produce recommendations an executive will act on — grounded in a verified cause, honest about what they bet on, and calibrated about what is known vs inferred. This is the "full pillar set" trust work, and it **folds the theory layer** (`docs/architecture/theory_layer_design.md`) into the numbered plan for the first time.

**Why this is one phase, not three (the reconciliation):** Phase 13 Cat 2/4, Phase 11J P1, and this phase all edit the *same two surfaces* — the `SFResponse` schema and the synthesis prompt in `a9_solution_finder_agent.py`. Built separately they rewrite that schema 3–4 times and re-pay the M2/M5 compliance gate each time. Instead they are sequenced as **one dependency-ordered build spine** with a single schema-compliance gate. **Key unification: Phase 11J P1's typed `SolutionAssumption` and this phase's "bets on" list are the same object** — one typed model carrying `{text, source_class, grounded_vs_inferred, confidence, provenance}`, defined once in Stage B. Phase 13 owns Stages A–C (the foundation); Phase 15 owns Stages D–F plus the confidence fields in B; Phase 11J P1 is absorbed into Stage B (11J keeps only its monitoring/drift work, which now *consumes* that schema).

**Unified build spine (dependency-ordered; each stage names its owning phase and whether it is buildable now or gated):**

| Stage | Work | Owner | Status |
|---|---|---|---|
| **A** | Forced tool-use structured output — `ClaudeService.generate_structured()` + `response_schema`/`tool_name` threaded through `A9_LLM_Request`/`A9_LLM_AnalysisRequest`/`A9_LLM_Service_Agent.generate()` | Phase 13 Cat 2 | ✅ **DONE (2026-07-23)** |
| **B** | Unified schema — `DecisionAsk` (word-count + hedge-word validators), `List[ImmediateAction]`, one typed `SolutionAssumption` (`assumption`/`validated_by`/`grounded`/`confidence`/`provenance` — field names match the already-written 11J P1 spec above, not the `text`/`source_class` shorthand used earlier in this doc's prose), typed `ImpactEstimate`/`RecoveryRange` replacing the untyped `impact_estimate` dict. `SFSynthesisSchema` added for tool-schema generation | Phase 13 Cat 2 + 11J P1 + Phase 15 | ✅ **DONE (2026-07-23)** |
| **C** | Principal/business-context contract at BOTH SF stages; strict tenancy (no generic fallback); principal-adaptive entry point/depth (never the conclusion — M1) | Phase 13 Cat 2 + Cat 4 | ✅ **DONE (2026-07-23)** |
| **D** | Grounding + constraint *input* contract — SF consumes verified causal chain + constraints + levers. Plumbing buildable now; constraint **content gated** on tenant-isolation tests + a pilot with real SF usage (theory §5.2 / §10 P2) | Phase 15 | ✅ **Plumbing DONE (2026-07-23)** — `enable_causal_grounding` defaults `False`; migration still not applied |
| **E** | Critic pass — `generate → critique-against-theory → synthesize`; traces each lever through the causal graph, flags side-effects / violated assumptions. Best model spent here | Phase 15 | ✅ **DONE (2026-07-26)** — `enable_critic_pass` defaults `False`, requires `enable_causal_grounding` too |
| **F** | "Bets on" assumptions → VA registration (`kpi_id` + impact bounds — verify SF→VA wiring); 11J market-condition drift re-query consumes the typed assumptions. Wiring can precede D/E (needs only Stage B) | Phase 15 + 11J P2 | ✅ **Core wiring DONE (2026-07-26)** — no flag needed (see notes); 11J drift-requery NOT built (separate follow-on) |
| **G** | Briefing UI built **once** against the unified schema — hero (`DecisionAsk`), Options table w/ Option-0 baseline, `ImmediateActionsChecklist`, the **single** `AssumptionsPanel` (grounded/inferred + provenance), Risk block surfacing Stage E side-effects; then Cat 4 role-adaptive depth. **Gated after Stage B (M5)** | Phase 13 Cat 3 + Cat 4 + Phase 15 | Gated after B — types.ts updated, no components built yet |
| **H** | Council redesign — collapse the simulated debate (frontend drops the dead `hypothesis` dispatch + unread `prior_transcript`); critic pass dual-duty (register check **+ propose candidate risks** for HITL accretion) with fully-audited findings; **theory-guided moderator** (grades options on constraint survival / causal-edge grounding / impact arithmetic / critic-finding response; forbidden to invent critiques; rubric parameterized judge-vs-integrator); `impact_estimate.scope` elicitation (unblocked — streaming removed the 20000 ceiling); per-stage token-ledger labels. Adversarial critique+rebuttal and collaborative/integrator protocol both **designed, evidence-gated** — see notes | Phase 15 (this session's audit) | ✅ **BUILT 2026-08-04** — `enable_theory_moderator` defaults `False` (PM-2 A/B arm; env `SF_ENABLE_THEORY_MODERATOR`); frontend collapsed to 2 dispatches, `VITE_DEBATE_MODE` retired; 10 new tests (`test_sf_stage_h_moderator.py`), 797 pass. Critic dual-duty (risk proposal) NOT yet added to the critic prompt — findings audit fixed, proposal duty is a follow-on. Live A/B still to run |

**Implementation notes (Stages A+B, 2026-07-23):**
- **Live production behavior is unchanged.** The synthesis call still uses the existing hand-tuned prompt path by default. A new `A9_Solution_Finder_Agent_Config.use_structured_output: bool = False` flag gates the forced-schema path — flip only after the live A/B compliance run (M2/M5) confirms quality parity or better vs the current prompt. This is deliberate: the schema+parsing/model work was safe to ship now (additive, defensively coerced, fully unit-tested with mocks); flipping the live call to an LLM-quality-dependent mechanism is not, until that run happens.
- **`expected_impact` (0–1 ranking heuristic used by `_rank_options`) was deliberately left untouched** — it is a different concept from `impact_estimate.recovery_range` (business-unit $/pp numbers, already consumed by `workflows.py`'s VA-registration impact-bounds conversion). Only `impact_estimate` became typed; this avoided breaking `_rank_options`, the UI ranking bars, and two of the four tests originally flagged as at-risk.
- Per-option `key_assumptions` (the "bets on" list) is a **new field on `SolutionOption`** — it did not exist before, so this was additive, not a rename.
- `StrategySnapshot.key_assumptions` (`value_assurance_models.py`) is retyped to `List[SolutionAssumption]` with a `mode="before"` validator that coerces legacy plain strings to `validated_by="human_confirmation"` — existing test fixtures using plain strings pass unchanged.
- New test file: `tests/unit/test_sf_structured_output.py` (33 tests) — schema validation, legacy coercion, SF's defensive per-option parsing helpers, and `generate_structured()`/routing plumbing, all against **mocked** Anthropic responses. No live API calls run from this suite — the 20+ synthetic-run compliance check and prompt-quality A/B remain a separate, manually-triggered step.
- UI: `types.ts` and `valueAssurance.ts` updated additively (`SolutionAssumption`, `DecisionAsk`, `ImmediateAction`, typed `impact_estimate`); no rendering components changed — `npm run build` passes.

**Implementation notes (Stage C, 2026-07-23):** Live production behavior changes here — this is a prompt-content change on the default path, not gated behind `use_structured_output`.
- `decision_maker` (previously 4 thin fields — name/role/decision_style/priorities — reaching only synthesis, unconsumed by any instruction) is now the fuller principal block and reaches **both** Stage 1 persona prompts (previously zero principal context, per the design doc's own finding) and synthesis, each paired with an explicit consumption instruction (exact wording per `llm_prompt_redesign_da_sf.md` §3.2).
- `time_frame` is wired for the first time — `PrincipalProfile.time_frame` was "framed but not wired" anywhere in the runtime (see `project_principal_lens_weighting` memory); it now reaches the prompt as the decision maker's planning horizon.
- `accountability_scope` is approximated from `business_processes`/`kpis` (the real existing fields) since no dedicated field exists on `PrincipalProfile`. `decision_authority` has no source field at all and is omitted rather than fabricated — consistent with design principle 3 (no invented defaults).
- Strict tenancy: the hardcoded generic `business_terms`/`profit_center` fallback dict is gone, replaced with an explicit "No business context available" disclaimer line. Note: the underlying *cross-tenant leak* (loading a different client's real context) was already fixed in a prior session (Jun 2026, SF card changelog) — this fix targets the *generic-fabrication* class the design doc's principle 3 warns about, not a security regression.
- Cat 4 principal-adaptive framing added at the synthesis touchpoint only (role → C-level decision-first vs diagnostic-depth framing), with the M1 invariant ("entry point and depth only, never the conclusion") stated explicitly in the prompt text itself rather than left implicit.
- Stage 1 persona calls only run in Hybrid Council mode (`enable_hybrid_council=True` or request-level persona/preset override) — confirmed via the existing `using_hybrid_council` gate; the default single-call path never reaches Stage 1, so `decision_maker`'s Stage-1 injection only fires there.
- New test file: `tests/unit/test_sf_stage_c_context_contract.py` (8 tests) — asserts on actual prompt text via a capturing stub orchestrator (same pattern as `test_solution_finder_llm_debate.py`), covering: decision_maker reaches both stages, detail-preference framing branches, the M1 invariant is stated, the disclaimer replaces the old fabricated text, and no-principal-context degrades safely.

**Pre-existing bug found + fixed while building Cat 4 (2026-07-23):** the initial Cat 4 implementation branched C-level vs non-C-level framing on a hardcoded role-title keyword list (`"cfo","ceo","coo","cxo","chief","president"`) — flagged as fragile and non-generalizing across tenants. Investigating a principled replacement (`PrincipalProfile.communication.detail_level`) surfaced a **much larger pre-existing bug in `A9_Principal_Context_Agent`** (both `get_principal_context()` and `get_principal_context_by_id()`, predates this session):
- `preferred_timeframes` was **hardcoded to `[CURRENT_QUARTER, YEAR_TO_DATE]` in every construction branch**, including when a real profile was found — `PrincipalProfile.time_frame` was never read at all. **Fixed** — now reads `time_frame.default_period` and maps it to the real enum.
- `communication_style` read a flat key (`profile_data.get('communication_style')`) that doesn't exist on `PrincipalProfile` (the real field is nested: `communication.detail_level`) — fell through to `"Concise"` for effectively every principal. **Fixed** — `communication.detail_level` is a declared field and survives `.model_dump()` through the real provider path.
- `decision_style` read from `persona_profile.decision_style` (one method) or a flat `decision_style` key (the other) — **neither exists on `PrincipalProfile`**, and `scripts/clients/*.py` seed data uses both of those exact (wrong) shapes inconsistently. `PrincipalProfileProvider.get()`/`.get_all()` return validated `PrincipalProfile` instances with no `extra="allow"`, so Pydantic silently drops these keys on load — **this one is only partially fixed**. `metadata.decision_style` (a real declared field) now works as a fallback, but nothing currently seeds `decision_style` into `metadata`, so it still resolves to `"Analytical"` for effectively every principal in production today. **Closing this fully requires a registry-schema decision** (add `decision_style` as a first-class `PrincipalProfile` field, or standardize seed scripts on `metadata.decision_style`) — not something a runtime fix alone can close. Flagged here rather than silently left as a residual gap.
- Consequence: the SF card's "Uses principal's `decision_style` from their profile to select appropriate consulting personas" (documented Dec 2024) has likely been selecting the same persona set for every principal via this path, independent of anything in this session's changes.
- New regression coverage: `tests/unit/test_principal_context_extraction.py` (14 tests) — pure extraction-helper tests plus an end-to-end test using **real `PrincipalProfile` instances** (not convenience dicts) proving `preferred_timeframes`/`communication_style` now genuinely vary per principal.
- Cat 4's framing branch now reads `decision_maker.communication_style` (registry-backed) instead of role-title keywords.

**Test sequence (one gate per stage):**
- **A:** structured-output smoke test; token-headroom check on production-shaped input.
- **B:** the **single** LLM compliance gate (M2/M5) on the complete schema — 20+ synthetic runs; decision-ask ≤25 words; hedge words rejected at validation; `source_class` + `grounded_vs_inferred` populated. **No SF UI starts until this passes.**
- **C:** cross-tenant business-context isolation regression; principal-adaptation consistency (same facts + same recommendation; only entry point/depth vary — M1).
- **D:** constraint-respecting test (SF does not re-propose a seeded impossible option); grounding test (each option cites the causal link it targets); **cross-tenant constraint-injection isolation test** before per-client prompt injection ships.
- **E:** critic-pass test — option with a known downstream side-effect flagged; known-good option passes clean.
- **F:** SF→VA round-trip (bets-on land with `kpi_id` + bounds; VA grades held/broke); drift re-query on a changed market assumption.
- **G:** no jest/vitest for `decision-studio-ui/` — `npm run build` for TS errors + manual walkthrough via `restart_decision_studio_ui.ps1`.

**Cross-cutting gates & pre-mortem constraints:**
- Schema defined and compliance-tested **before any SF UI** (M2/M5).
- **No "proved" language**; calibrated confidence capped at "consistent with" (theory §4).
- **Tenant-isolation tests pass before constraint injection ships** (theory §5.2; `feedback_sf_defects` — the SF contamination surface was hit once already).
- Constraint/grounding *content* gated on ≥1 pilot with real SF usage (accretion needs fuel; theory §10 kill-criteria apply).
- VA adjudication never pre-fills the flattering answer (theory §5.3) — relevant where F meets VA.

**Design references:** `docs/architecture/llm_prompt_redesign_da_sf.md` (Phase 13 umbrella, Stages A–C) and `docs/architecture/theory_layer_design.md` (Phase 15 pillars §5.2/§8/§10, Stages D–F). The Value Driver Tree / layered cross-section is a **separate, later, gated exhibit** (theory §7: static at P3 after 12C, interactive at P4 after observed pilot engagement) — not part of Stage G.

**Stage D research + schema design (2026-07-23):** Before writing Stage D's schema, researched how causal-graph modeling is actually done in practice, to avoid designing it from intuition alone.
- **Correlation ≠ causation must be two separate schema axes, not one.** Every source agrees causation implies correlation but not the reverse — a schema field trying to represent both "how sure are we" and "is this even a causal claim" produces misleading edges regardless of how carefully it's populated.
- **Pearl's ladder of causation** (association → intervention → counterfactual) maps directly onto Agent9's existing pipeline without any new machinery: SA/DA = association (rung 1), SF's proposed options = intervention hypotheses (rung 2, always untested at proposal time), VA's DiD attribution = counterfactual (rung 3, already in production). This became the `causal_rung` field on `kpi_relationships`, kept independent of `provenance` (the existing template/confirmed/hitl_proposed/va_validated ladder — *how captured*, not *which rung was established*).
- **On whether ML (regression/decision trees/neural nets) should quantify cause-effect:** no — those are associational models; using them to assert causation would be the exact overclaim this project's trust design exists to prevent. The one concretely useful technique identified: **Granger causality** on KPI time series, purpose-built for exactly what `lag_periods` needs (does KPI A's history predict KPI B's future, at what lag) — Agent9 already collects the monthly time series to run it on. DiD is already in production via VA. Causal discovery (DoWhy/PC algorithm) is real but any edge it proposes should land as `hitl_proposed` for review, same governance as everything else — never asserted directly.
- **Where a causal graph would actually sharpen SF, if built:** calibrating `time_to_value` from a measured lag instead of an LLM guess; blocking re-proposal of levers VA already found ineffective; targeting the causal mechanism instead of just the DA-located segment; and cross-KPI side-effect checking (Stage E's justification). The risk, stated plainly: an unguarded graph injection can make output *more confidently wrong*, not more precise, if template/correlational edges aren't visibly caveated to the LLM as less certain than va_validated ones.
- **Schema shipped from this discussion:** see §5.5 in `theory_layer_design.md` — `causal_rung`/`provenance` split, categorical `confidence`, and `assumptions` folding constraints in via a `record_type` discriminator rather than a separate table (same unification pattern as Stage B's `SolutionAssumption`). Migration + models designed, unit-tested, **not applied to any database** — held pending a producer or consumer, per explicit instruction to keep Phase 15 uncommitted until benefits are demonstrated.

**Stage D plumbing built (2026-07-23), consumption still gated by default:**
- `A9_Solution_Finder_Agent_Config.enable_causal_grounding: bool = False` — same gating pattern as `use_structured_output`. The read path is non-fatal by design (missing migration, empty tables, unresolvable KPI, or a cold registry pool all degrade to "no causal context injected," never a crash) — safe to ship with the flag off; flip only after the theory §10 P2 gate (tenant-isolation tests + a pilot) is satisfied.
- **Tenant-safe KPI resolution**: new `_lookup_kpi_scoped()` in `a9_solution_finder_agent.py` reuses `A9_Deep_Analysis_Agent`'s proven pattern (fix commit `5925de7`, 2026-07-13) verbatim — id-or-name match, strict client scoping, a same-id KPI from another tenant is never an acceptable fallback. Needed because `kpi_relationships`/`assumptions` are keyed by the registry `kpi_id`, while `da_summary` only ever carries `kpi_name` (a display string).
- **New `AssumptionProvider`** (`src/registry/providers/assumption_provider.py`), matching `KPIRelationshipProvider`'s pattern — `get_active_constraints(client_id, scope)`, `get_all`, `upsert`. No extraction/accretion pipeline calls `upsert` yet — that stays gated, this is standard CRUD plumbing for manual/admin-entered records today.
- **`KPIRelationshipProvider` updated** to map the 5 new causal-typing columns on both read and write — otherwise the provider would have silently dropped them, the exact bug class the PC agent audit found.
- **`_build_causal_context_section()`** formats the causal chain + active constraints into the synthesis prompt with provenance-aware caveating baked into the text itself: `template` edges get an explicit "UNCONFIRMED... do not assert as fact" caveat; `va_validated` edges get "consistent with... NEVER 'proved'" language. An empty graph produces an empty section — no fabricated content when there's nothing to say.
- **New test file**: `tests/unit/test_sf_stage_d_causal_grounding.py` (15 tests) — tenant-safe resolution (mirrors `test_da_kpi_scoped_lookup.py`), provenance-aware formatting, and end-to-end prompt injection via the Stage C stub-orchestrator pattern (flag off, KPI unresolvable, provider exception, the happy path, and Stage 1 receiving the same content).
- **Correction (2026-07-26): the causal-context fetch originally only reached synthesis, not Stage 1 — caught by the user, not by the tests.** `_run_stage1`'s `asyncio.gather` executes and completes before synthesis, but the fetch was coded right before `full_prompt` construction — so a persona formed its hypothesis with zero knowledge of an already-established mechanism/lag or an active constraint, and synthesis had to silently override or contradict it after the fact. Fixed by moving the fetch to right after `decision_maker` is resolved (same point Stage C already established reaches both stages), and:
  - The causal chain gets its own Stage 1 section (`causal_context_section_s1`), same provenance-aware caveating as synthesis.
  - Constraints merge into the **existing** `refinement_compact_s1["constraints"]` field — the one Stage 1's RULES text already instructs personas to respect ("Respect any do_not_propose items and constraints from PRINCIPAL CONSTRAINTS") — rather than inventing a second constraint mechanism a persona would have to separately learn to honor.
  - Fixing this surfaced two bugs of my own along the way, both now fixed: (1) an indentation mistake in the same edit that accidentally nested three pre-existing `refinement_result` checks inside the new constraint-merge block, breaking them whenever `refinement_result` was `None`; (2) the Stage D test file's e2e tests never actually exercised Stage 1 at all — missing `enable_hybrid_council: True` (the same gate found during Stage C) — so the original fetch-timing bug shipped with tests that looked green but never ran the code path they claimed to cover.
  - **Test-harness finding, fixed at the root this time**: the shared agent-registry singleton can return a cached `A9_Solution_Finder_Agent` instance across tests in the same process — this broke a config field varied test-to-test twice in one file. The fix isn't "set config after construction" (a workaround for one file); it's constructing the agent directly via `A9_Solution_Finder_Agent.create(config)`, which always does `cls(config)` with no caching, bypassing `orchestrator.create_agent_with_dependencies` entirely. Verified stable across repeated full-suite runs.
- **Epistemic guardrail added (2026-07-26): `causal_rung='intervention_tested'` now requires `provenance='va_validated'`, enforced at both the DB (CHECK constraint) and Pydantic (`model_validator`) layers.** Raised in discussion: does HITL confirmation of an MA-proposed causal edge risk confirming principal bias rather than establishing scientifically tested cause-and-effect? Yes — human agreement with a plausible narrative is not a statistical test, and it's the same cognitive failure mode (Sterman's finding on human causal reasoning) the theory layer exists to correct. Before this fix, nothing stopped a record from being `provenance='confirmed'` (a human said yes) *and* `causal_rung='intervention_tested'` (a scientific claim) simultaneously — the exact conflation `causal_rung`/`provenance` were split to prevent, just never enforced. Only VA actually running DiD/Granger causality on a specific edge may claim the tested rung now, at write time, regardless of what any human confirms. 5 new tests in `test_theory_layer_causal_schema.py` (16 total in that file); one pre-existing test asserted the now-forbidden combination and was corrected. This also reframes HITL's legitimate role for a proposed causal edge: supplying domain facts an algorithm can't know, and vetoing implausible claims (asymmetrically less bias-prone than confirming them) — never rendering a causal verdict.

**Stage E built (2026-07-26): the critic pass, `generate → critique-against-theory → synthesize`.**
- `A9_Solution_Finder_Agent_Config.enable_critic_pass: bool = False` — same gating pattern as the rest of Phase 15, and **additionally requires `enable_causal_grounding=True`**: a critic with no causal graph has nothing to critique against, so the dependency is explicit rather than silently inferred. Also skipped entirely when there's no actual graph/constraint data fetched (an empty graph produces no critic call, not an empty-handed one) and in `stage1_only` mode (no synthesis call exists to feed findings into).
- **Sequencing**: runs immediately after Stage 1's `asyncio.gather` completes and before the synthesis prompt is built — deliberately mirrors the Stage D fix earlier in this phase (catch it at the source, don't patch it after). The critic sees each persona's raw `proposed_option` (title, mechanism) plus the same causal chain + constraints Stage D already fetches, and is instructed to flag a concern **only when grounded in that data** — explicitly told not to invent generic risks.
- **New `CRITIC` task type** in `claude_service.py`, routed to `claude-sonnet-5` by default (same tier as `REASONING`/`SYNTHESIS`) — "best model spent here" respects Phase 11O-C's already-made decision that Fable 5 stays deferred to the offline/background path, not SF's interactive HITL path. Overridable via `CLAUDE_MODEL_CRITIC` if a stronger model is deliberately warranted later.
- **New `SolutionOption.flagged_side_effects: List[str]`** field (additive) — this is what Stage G's already-planned "Risk block surfacing Stage E side-effects" will render. Critic findings feed into the synthesis prompt as a `## CRITIC FINDINGS` section instructing synthesis to populate this field on the corresponding option and address the concern in its rationale/prerequisites, rather than silently dropping it.
- Findings are matched to their originating **persona**, not yet to a final `opt_N` id (synthesis assigns those) — synthesis is instructed to attribute by mechanism/persona correspondence when constructing the final options.
- Fully non-fatal: a critic-call failure degrades to no findings, never breaks solution generation — same discipline as every other Phase 15 stage.
- New test file: `tests/unit/test_sf_stage_e_critic_pass.py` (6 tests) — flag off, missing `enable_causal_grounding` dependency, empty graph (no data to critique), the happy path (findings reach both the critic prompt input and the synthesis prompt, and the final option carries `flagged_side_effects`), a critic finding nothing (no fabricated section), and critic-call failure degrading safely. Written directly against the lessons from Stage D/C's test-harness issues (`enable_hybrid_council` for Stage 1 to actually run, direct `A9_Solution_Finder_Agent.create()` construction to avoid the registry-caching pollution) — all 6 passed on the first run.

**Stage F built (2026-07-26): "bets on" assumptions → VA registration.**
- **Verified, not re-fixed**: the `kpi_id` + impact-bounds half of "SF→VA wiring" was already correct — `workflows.py`'s HITL-approve handler already resolves a real `kpi_id` (with a documented past-bug-fix comment about the old `kpi_id=""` regression) and computes `expected_impact_lower/upper` from `impact_estimate.recovery_range`. Nothing to build there.
- **The actual gap**: `StrategySnapshot.key_assumptions` — the field Stage B's "bets on" list is specifically meant to reach — was **always an empty stub**. `A9_Value_Assurance_Agent._build_strategy_snapshot()` declared `key_assumptions: List[str] = []` and never populated it, and `workflows.py` never passed a `strategy_snapshot` at all (so that fallback always ran), even though the approved option's real `key_assumptions` was sitting unused in `matched` (the already-resolved approved-option dict) the entire time.
- **This is a genuine bug fix, not new risk — no feature flag.** Unlike Stage D/E, nothing new is generated or called; existing data that was already computed during SF synthesis is simply threaded to where it always should have gone. New `RegisterSolutionRequest.bets_on_assumptions: Optional[List[dict]]` field; `workflows.py` passes `matched.get("key_assumptions")`; `register_solution()` reconstructs the snapshot via `StrategySnapshot(**{**snapshot.model_dump(), "key_assumptions": request.bets_on_assumptions})` when present — reusing the model's **existing** legacy-string-coercion validator rather than writing new coercion logic, and working identically whether the snapshot came from the caller or the agent's own fallback builder.
- **Explicitly NOT built**: the "11J market-condition drift re-query consumes the typed assumptions" half of this row — a separate, deeper 11J-scoped follow-on (re-querying MA for `validated_by="ma_query"` assumptions to check they still hold) that depends on assumptions actually flowing into VA, which this change now makes possible but does not itself implement.
- 5 new tests in `tests/unit/test_a9_value_assurance_agent_unit.py` (58 total in that file) — threading with typed dicts, legacy-string tolerance, no-regression when the field is absent (correctly asserts the *existing* snapshot assumptions pass through unchanged, not that they're empty — the fixture's default snapshot already carries one legacy-string assumption), and threading works identically via the fallback-builder path.

**Stage H designed (2026-08-04): debate-architecture audit + council redesign.** Full rationale and target architecture live in the PRD's 2026-08-04 block (`docs/prd/agents/a9_solution_finder_agent_prd.md`) — this entry records what was established and what the build is.
- **Audit finding (live e2e, unmocked, token ledger attached):** full mode's `hypothesis`/`cross_review`/`synthesis` are **three identical mega-prompt requests** — `debate_stage` only gates Stage 1 skipping; the UI's `prior_transcript` is read by **no backend code**; the cross-review/moderation is a single-call simulation (one author writes attack, defense, and verdict). Measured: 14.8s / 233.2s / 272.2s / 191.1s per stage, ~35k tokens per mega-call; the `hypothesis` stage's output is consumed by nothing. Full mode ≈ 3× fast-mode cost for materially the same epistemics.
- **Decision:** replace the debate-shaped middle with calls that either generate diversity or check against ground truth. Keep Stage 1 (3× independent personas — decorrelation is real at *generation*); critic pass gains dual duty (register check + propose candidate risks → HITL accretion feedstock); new **theory-guided moderator** grades options against the assumption register, causal edges, and impact arithmetic instead of simulating a jury; **HITL is the adversarial step** — the human is the rebuttal round, and their judgment is the one that accretes.
- **Evidence-gated, not built:** (1) staged adversarial critique + one schema-bounded rebuttal round (refute-with-citation / amend / accept-as-risk — no free text, so polite capitulation is structurally unavailable); gate = live A/B via the e2e harness, ≥5 runs each way, must change decisions or risk registers for the better. Rationale: RLHF convergence/sycophancy in iterated exchange; same-weights personas argue shallowly; debate-literature gains are mostly sampling + adjudication. (2) Collaborative/integrator protocol for cross-discipline problems (complements-not-substitutes; differentiated *context* per specialist; theory layer as interface contract; conflict-triggered reconciliation; DA routes judge-vs-integrator via an extension of `recommended_council_members`); build trigger = first genuinely cross-discipline pilot problem. Two accommodations land now: moderator rubric parameterized, persona context injection pluggable.
- **Also in scope for the build** (same surfaces, one pass): `impact_estimate.scope` elicitation — its deferral premise (synthesis at output ceiling) died when streaming lifted the SDK's 20000 non-streaming cap (`max_tokens` now 32000; measured 17,624-token output = 14,376 headroom); critic-findings audit fix (currently records `count` only); silent Stage 1 persona-drop defect (3 calls succeed, 2 hypotheses kept, no error).
- **Session infra shipped alongside (committed `7681114` + working tree):** `AsyncAnthropic` + `messages.stream()` in `claude_service.py` (Stage 1 calls now genuinely concurrent — dispatch within 4ms; previously 0/3 overlapped despite `gather`); per-run `token_usage` audit event on SF (per-call rows: `stage1_{persona}`/`critic_pass`/`synthesis`); client poll-budget fixes for the give-up-while-backend-succeeds bug class (SF 120s→900s — this, not a hang, was the "stall after hypothesis"; DA 45s→180s; SA 90s→600s); restart-script hardening (QuickEdit console wedge → file logging; `--reload-dir src`; `--strictPort`; stale-window cleanup).
- **Pre-mortem corrective actions (2026-08-04, PM-1..9 — these are Stage H build REQUIREMENTS, not suggestions):**
  - *Done now:* **PM-5** persona-drop root-caused and fixed — Stage 1 results were keyed by the LLM echoing `persona_id`; a successful call omitting that field was silently discarded (observed live: council of 2, no log). Now keyed positionally from `gather()` order, mismatched echoes logged, `dropped_personas` added to the `stage1_calls_complete` audit event. **PM-8** consumer inventory run — `cross_review`/`stage_1_hypotheses` consumers are exactly 6 UI files (`client.ts`, `types.ts`, `useDecisionStudio.ts`, `CouncilDebatePage.tsx`, `ExecutiveBriefing.tsx`, `briefingUtils.ts`); **no PIB template and no backend API surface renders them** — the collapse's blast radius is UI-only, plus stale localStorage briefings (defensive rendering required).
  - *Build requirements folded into Stage H:* **PM-1** moderator grades must display their denominator ("graded against N constraints / N edges + provenance mix") and degrade to an explicit "insufficient theory data to grade" on an empty register — never confident grades over nothing. **PM-3** SF logs active protocol + flag state (`enable_causal_grounding`/`enable_critic_pass`/`use_structured_output`) at run start; ledger call-labels double as the call-graph witness. **PM-6** harness asserts moderator output tokens <90% of budget; `heuristic_stub_fallback` stays armed. **PM-7** scope parser cross-checks `scope` against `basis` arithmetic — a segment change-point cited under an `enterprise` claim resets scope to `None` + audit event (elicited-but-wrong is worse than absent).
  - *Procedural:* **PM-2** fast mode survives ONLY as the A/B comparison arm with a kill decision at the A/B readout — not open-ended. **PM-4** one variable per live run: moderator rewrite ships on the hand-tuned prompt path first; `use_structured_output` flips in a separate, own-harness-run step. **PM-9** collaborative-mode accommodation is capped at two seams (rubric parameter + pluggable persona context); nothing else builds without a pilot problem.

**PM-2 A/B readout (2026-08-05/06): kill decision — moderator wins, adopt as default.** 10 runs (5/arm), identical fixed input (one DA result + one temperature-0 Stage 1 hypothesis set, reused across all 10 so the synthesis arm is the only variable), direct API driving via a scratchpad harness (`ab_debate.py`) to keep UI flake out of the comparison.
- **Scope elicitation: the decisive result.** Baseline 0/14 options stated scope across all 5 runs; moderator 12/12 (3/3 in every non-stub run). This is the defect the whole exercise was built to close, and it closed completely on one arm, not at all on the other.
- **Cost/latency:** moderator +15% output tokens (22,430 vs 19,526 avg), +13% duration (239s vs 212s) — the price of the grading duty.
- **Stub-fallback rate is arm-independent:** 1/5 on BOTH arms, same magnitude (~21-22k tokens, nowhere near budget) — this is a JSON-formatting failure, not truncation, and moderator adoption does nothing to fix it. `use_structured_output` (Stage A, already built and gated) is the designed fix — this A/B is the evidence that justifies flipping it, as its own separate PM-4-disciplined run.
- **Grades are stochastic, not deterministic:** `arithmetic_flags` on identical input went 0→3→0→1→(n/a, stub) across the 5 moderator runs. Grades are an advisory signal for the HITL reviewer, not a fixed verdict — this must be represented in how Stage G eventually renders them (confidence framing, not a checkbox).
- **Recommendation:** adopt `enable_theory_moderator=True` as the default. Keep the baseline prompt path alive for one more cycle as the control for the `use_structured_output` flip, then delete it (closes PM-2's "not open-ended" requirement).

**Diverse-council first exercise (2026-08-05): DA's Dynamic Diverse Council path run end-to-end for the first time.** DA's Problem Refinement chat (`_recommend_diverse_council`, keyword+role matching across MBB/Big4/Tech/Risk categories) was driven through 10 turns of realistic CFO answers to completion (`ready_for_solutions=True` requires either `MAX_TOTAL_TURNS=10` or full topic exhaustion — the interviewer never volunteers to stop early; the documented `"skip"` command is what actually advances a topic). Recommended council: `mckinsey, kpmg, accenture` (role=CFO, decision_style=analytical). Result (2 synthesis runs): each option is a legible descendant of one persona — McKinsey→negotiate (accelerate Chain A renewal), KPMG→govern (anchor-account renewal calendar + margin controls), Accenture→platformize (enterprise margin-intelligence platform). The govern/platformize archetypes never appeared in any of the 10 MBB-council runs. Quality held: 6/6 options scope-stated, 0 stubs, stable recommendation across both runs, critic findings graded per-option (one `standing` in run 2 — enterprise-wide indexing volume risk — vs the rest `answered`).
- **Confound flagged and partially resolved by a follow-up control run (MBB council + the diverse batch's own `refinement_result`, fresh Stage 1):** the diverse runs differed from the original MBB batch in TWO variables at once — council AND presence of refinement context (the MBB batch had none). The control isolates council as the only remaining variable.
  - **Refinement context alone measurably broadens MBB's framing** — one control option ("Structural Margin Governance & Best-Practice Replication Program") went `scope=enterprise` (26-47pp) and used governance vocabulary, which no refinement-free MBB run (0/10) ever did. So some of what looked like a council effect on first read is a refinement effect.
  - **The specific intervention ARCHETYPE still tracks persona, not refinement content.** All three control personas had the same refinement facts (ERP lag, manual rebate accruals, audit/governance requirements) available; only KPMG reached for a controls/audit-infrastructure fix (automate rebate accruals, centralize ERP data) and only Accenture reached for an actual technology-platform build. MBB's "governance" option, given the identical facts, stayed org/process (a cross-functional council enforcing discipline via change management, McKinsey's own 7S/MECE) — never systems, never a platform. So the diverse council's real contribution is narrower than first read (it doesn't cause "broader thinking" — refinement does that) but still real: it unlocks solution archetypes MBB does not reach for even with identical inputs.
  - **Sample size caveat applies fully:** n=1 control vs n=2 diverse, against a process already shown stochastic on identical input (the PM-2 readout above). Read as a signal worth a larger run, not as settled.
- **Bonus finding — a moderator rubric gap, caught while verifying the control's enterprise-scope claim before reporting it:** the control's `arithmetic_consistency=pass` grade on the enterprise-scope option was checked and found technically defensible but methodologically thin — it verifies the claimed range (26-47pp) falls inside a plausible fraction (35-63%) of the SUM of three segment-level change points (43.24+16.76+15.18≈75pp), but never checks whether summing UNWEIGHTED segment-level percentage-point deltas across segments with different revenue weights is a valid way to project enterprise-level recovery in the first place. This is the PM-1 pattern (confident grading over shaky ground) one layer deeper than PM-1 was written for — it only surfaced because this was the first run to produce a multi-segment "portfolio rollup" framing. **Follow-up for the moderator rubric:** add an explicit check/flag for cross-segment percentage-point summation used as an enterprise-impact proxy, distinct from the existing single-option internal-consistency check.
- **Harness extended:** `ab_debate.py` gained `capture_diverse`/`run_diverse` (drives Problem Refinement to completion, captures the recommended council + its Stage 1 hypotheses, runs fixed-council synthesis batches) — kept in the scratchpad, not yet promoted to a committed test.

**Deterministic measurement instruments built + Phase 0 validation (2026-08-06).** New `src/analysis/` package — mechanism fingerprinting, groundedness scoring, problem-type classification — all computed **without any LLM call**, because a model-based judge would wobble run-to-run and make process noise indistinguishable from measurement noise. Validated against the 13 SF payloads already on disk from the A/B and diverse runs, at zero API cost, before any new spend.

- 🔴 **CORRECTION — the "recommendations differ on every run" finding was measured wrongly.** The PM-2 A/B readout above reports 4 distinct recommendations across 4 successful runs per arm. That was **title-level string comparison**, and titles are verbose restatements of the same mechanism ("Contract Renewal-Timed Base Oil Cost-Indexing Clause" / "Trigger-Based Base Oil Indexation Clause" / "Structural Contract Reindexing: Base-Oil-Linked Price Adjustment Clause" are one recommendation, not three). Measured at the **mechanism** level with a deterministic fingerprint:

  | Arm | Selection stability (does the same lever family win?) | Option-set stability (is the candidate set the same?) |
  |---|---|---|
  | baseline | **50%** (indexation ×2, pricing_corridor ×2) | **100%** (same 3 families every run) |
  | moderator | **100%** (indexation ×4/4) | **50%** (set varies: cost_audit / pricing_corridor swap in) |
  | diverse | 100% (n=2) | 100% (n=2) |

  So the moderator arm looked **perfectly repeatable** on this batch, and merely verbose in how it says so.
  🔴 **RETRACTED 2026-08-09 — see the A/B closure entry below.** Four further runs on a clean build produced **50%** selection stability (indexation ×2, pricing_corridor ×2), *identical to baseline*. The 100% figure was a small-sample artifact at n=4; combined n=8 gives **75%**. The caveat was written directly beneath this claim at the time and then ignored in the headline — the same `feedback_one_observation_is_not_a_baseline` error repeated at n=4 instead of n=1. **The PM-2 kill decision rests on scope elicitation alone, not on stability.**
  **Caveats:** n=4 non-stub per arm; one situation only. "indexation" winning every moderator run may reflect a problem with one obvious answer rather than a stable process — a situation with two genuinely competitive levers is the real test. Within a single situation `scope_label` and `causal_edge` are constant, so the fingerprint reduces to lever family alone.

- **Taxonomy is data-derived, not invented.** An a-priori taxonomy (pricing / contract_terms / cost_structure / mix / governance / platform) did not survive the payloads; the real recurring families are `indexation`, `pricing_corridor`, `volume_for_margin`, `governance`, `platform`, `cost_audit`, `replication`. 100% of 39 options classified.
- **Phase 0 found and fixed a real classifier bug.** Matching title+description together and resolving by fixed priority produced three misclassifications, because long descriptions mention every lever in passing and outvoted each option's actual thesis ("Enterprise Margin Intelligence **Platform**…" → `indexation`; "**Systematize**…**Governance**…" → `platform`; a corridor option with no "index" in its title → `indexation`). Fix: match the **title**, earliest-mentioned lever wins — a title is a curated thesis and the model's choice of what to lead with is signal. This correctly separates compound options a fixed order would collapse. All three cases are now regression tests.
- **Groundedness scorer catches the moderator rubric gap deterministically.** The control run's enterprise claim scores `impact_ratio=28.14` and is flagged `cross_segment_summation` — 26–47pp against a **−1.67pp** enterprise move, consistent with summing unweighted segment deltas (43.24+16.76+15.18). The moderator had graded that option `arithmetic_consistency=pass`. Baseline options score 1–2/3 (all fail scope-stated); moderator/diverse score 4–5/5 with impact ratios 0.61–1.00; both stub runs score 0.
- **Design discipline: not-checked is never pass.** Every check returns True/False/**None**, where None means the input needed wasn't supplied (e.g. offline, no registry); None is excluded from both numerator and denominator. Conflating "not checked" with "passed" is the exact failure this package exists to catch.
- **G5 (constraints addressed) is deliberately weaker than G1–G4** and named accordingly — whether an option *violates* a constraint is a semantic judgement no regex makes honestly, so it checks only whether the option's text engages with the constraint's distinctive terms. Read as "addressed", never "complied".
- **Problem profile for the Lubricants case:** `mixed / concentrated / no-control / single` (dominance ratio 2.58). Notable: **the IS-NOT set is empty** — this problem has no contrast group, so "why here and not there" cannot be answered from the data at all. Worth knowing before comparing protocols that assume a control set exists.
- New tests: `tests/unit/test_sf_metrics.py` (43) — pure functions, no LLM/network/DB. Suite 840 pass.

**Data-accuracy hardening (2026-08-07/09).** A briefing review surfaced a cluster of number defects; every one traced to the same root — **prose or UI re-deriving what a typed model already carried correctly**. The A2A models held throughout; they were bypassed at three boundaries.
- **`MeasurementContext` on `KPIValue`** (`26dfa27`, `9d7c4da`) — provenance stamped on every reading: resolved window (not the `year_to_date` *token*), `comparison_basis`, `version`, filters, `source_system`, `sql_hash`. Fixed the "same KPI, two values" confusion (Actual 94.3M vs Budget 107.8M under one name, which cost real time to rule out). **`comparison_basis` was itself a correction:** the first cut asked SA's temporal window helper for a comparison window regardless of type, stamping `2025-12-01..2025-12-31` on `budget_vs_actual` / `target_vs_actual` / `benchmark` — three of six types got a confidently wrong window. Now `temporal` / `version` / `peer` / `projection` / `series`, with windows stamped only where meaningful. **Consequence for cross-agent assertions: window equality is only comparable *within* a basis.**
- **UI consumes rather than recomputes** (`781e0c3`) — the Cost of Inaction banner printed "Trend: Recovering" above worsening numbers. **Two** sign traps stacked: `delta/prev` cancels for a declining segment (both negative → positive ratio), and `current * (1 + rate)` moves a negative value *toward zero*. Fixing either alone leaves a wrong briefing — the interim state had the right label and wrong numbers, which is worse. `projectKpiTrend` extracted so the number an executive reads first is testable.
- **Narrative claim validation** (`3c5e5ed`, `94a7e85`) — the prose leading page one had **no check at all**. Two real errors: a segment's `-43.24` presented as "the headline KPI move" (true: 30.29%), and "140.4pp of combined drag" whose three cited components sum to 75.18. Both arithmetic, both checked without an LLM. Findings now render as a reader-facing caveat, not just an audit event — detection that reaches only an audit payload is a smoke alarm wired to a notepad. Tuning note: a bare `/headline/` cue gave 4 false positives out of 6; flags that cry wolf get ignored, so the cue requires an assertion verb and rejects subordinating prepositions.
- **SQL execution audit** — confirmed **all** data-product SQL runs through `DPA.execute_sql`; the DPA is the sole owner of every DB client (`BigQueryManager` / `SnowflakeManager` / `DuckDBManager` imported nowhere else outside `src/database/`). Execution is unified; **construction is not** — SA resolves windows with its own `_bq_get_period_dates` (0 uses of the shared `TimeFilter`, vs 38 in the DPA). They currently agree; nothing enforced that. `MeasurementContext` makes drift a testable assertion rather than an invisible risk, which is why it was done *before* the riskier SA→`TimeFilter` refactor.
**🏁 Stage H A/B CLOSED (2026-08-09) — moderator adopted, on one ground not two.**
Final tally: baseline n=4 non-stub, moderator n=8 non-stub (4 original + 4 on clean build `29a7313`), identical fixed input throughout.

| | scope stated | selection stability | avg output tokens |
|---|---|---|---|
| baseline | **0 / 12** | 50% (indexation ×2, pricing_corridor ×2) | 18,857 |
| moderator | **27 / 27** | **75%** (indexation ×6, pricing_corridor ×2) | 22,504 |

- **Decision: adopt the moderator arm** (`enable_theory_moderator=True`). The case rests on **scope elicitation**, which is structural and overwhelming — 27/27 vs 0/12, reproduced across two builds. That is the defect feeding segment-sized ranges into VA impact bounds.
- **Retraction:** the earlier "100% selection stability / second independent argument" claim did not survive replication. On the clean build the moderator matched baseline exactly at 50%; combined it is 75%. Suggestive, not decisive — **stability is not a differentiator between arms.**
- **Stub rate is not an arm property.** 0/4 on the clean build reflects the parser + `self.logger` fixes; baseline would benefit identically. Excluded from the comparison.
- **Cost of the rigour:** the extra batch surfaced a regression *I* had introduced (`self.logger` on the parse-failure path, `29a7313`), which had converted a recoverable parse failure into a hard error and a user-facing stub. Worth every minute — the "cheap close" would have shipped it.
- **Harness hardened before the final batch:** non-destructive run numbering (an earlier batch silently overwrote `ab_raw/moderator_1..2.json`; metrics survived in `ab_results.jsonl`, raw payloads did not), git-HEAD build stamping per run, and stub-vs-arm-mismatch disentangled — the old check reported a false `ARM MISMATCH` on every stub and buried the real cause.
- **Next per PM-2:** keep the baseline prompt path for one more cycle as the control for the `use_structured_output` flip, then delete it.

**🏁 Stage A `use_structured_output` A/B CLOSED (2026-08-09) — dead heat; adopt on failure-mode removal, not on measured gain.**

**The flag was never wired.** Before any run: the config field existed on `A9_Solution_Finder_Agent_Config` with two consuming call sites in the agent, but the orchestrator never populated it. It was pinned to its Pydantic default of `False`. **The experiment could not have run at all — both arms would have executed identical code**, and the result would have been a confident "no difference detected" from a test that never varied anything. Fixed (`347c87a`) plus `tests/unit/test_feature_flag_wiring.py`, which requires every flag `/healthz` reports to be read by the orchestrator and to default to `"false"`.

Design: 3 runs per arm, byte-identical input, server-side flag state verified via `/healthz` **before** spending on either arm.

| metric | control (prose) | structured (forced tool-use) |
|---|---|---|
| stub fallbacks | **0** | **0** |
| `impact_estimate.scope` | 9/9 | 9/9 |
| typed `recovery_range` | 9/9 | 9/9 |
| impact basis stated | 9/9 | 9/9 |
| reversibility | 9/9 | 9/9 |
| `key_assumptions` attached | 9/9 | 9/9 |
| `scope_label` | 5/9 | 6/9 |
| distinct recommendations | 3/3 | 3/3 |

**A dead heat.** The only difference — `scope_label` 5/9 vs 6/9 — is noise at n=3.

**Why that was foreseeable, and why the test still had value.** The control arm scored **perfectly** on every conformance measure, so structured output had no room to improve; the best available outcome was a tie. The result therefore does NOT say structured output is useless. It says that on this input, with a healthy model and a clean build, the prose path is already conformant. The case for structured output rests on conditions this test does not reproduce: unusually long or awkward payloads, truncation pressure, model drift, a future model version.

**DECISION DEFERRED (2026-08-10): revisit after Stage I closes.** The evidence here is a tie, so nothing is lost by waiting, and Stage I changes the shape of the synthesis call (per-persona constraint sets, a shared question queue) — which is exactly the kind of longer, more awkward payload where structured output would show a difference this test could not produce. Deciding now would fix the answer against the easy case.

**Recommendation when it is revisited: adopt — but the argument is failure-mode removal, not measured gain.** Same output quality at no observed cost, and the parse-failure path becomes structurally impossible rather than merely unobserved. That is materially weaker evidence than the moderator adoption (27/27 vs 0/12 on scope elicitation) and should not be described the same way. Per PM-2, if adopted, **delete the prose path** rather than carrying two.

**Unchanged by this:** recommendation instability. 3 distinct winners from 3 runs in BOTH arms — as expected, since structured output governs the FORMAT of an answer, not the choice of one.

**Method note:** the first comparison reported `assumptions attached: 0/9` in both arms, which read as a Stage B/F deliverable producing nothing. The field is `key_assumptions`; the script looked for `assumptions`. Checked before reporting — a measurement error dressed as a product gap would have sent real work in the wrong direction.

- **Parked behind this A/B (PM-4, one variable per live run):** (a) **token substitution** — the LLM references `{{kpi.current}}` rather than restating the figure, so misquoting becomes structurally impossible; vocabulary must be **basis-aware** (`{{kpi.prior}}` is meaningless for a plan variance, and would have resolved to *last December* had this been built before `comparison_basis`). (b) **KPI Semantic Contract** — `docs/architecture/kpi_semantic_contract.md`: DGA-declared `additive_across_dimensions`, `unit_class`, `sign_convention`, `scope_eligible`. Turns `groundedness`'s `cross_segment_summation` heuristic into a declared fact — **an LLM that sums three segment percentages *correctly* currently passes every check we have.** Both are the same idea (the registry states what a number means; consumers reference rather than re-derive) and should land together.

---

#### Stage I — Persona-differentiated problem framing (designed 2026-08-09, not built)

**The observation that started it.** Reading the Stage 1 hypotheses across 10 MBB runs: McKinsey, BCG and Bain produce *one analysis in three costumes*. Same causal claim (base-oil COGS pass-through colliding with a contractual price-lock at one customer), and two of three propose a near-verbatim identical intervention ("accelerate contract renewal negotiation"). Only Bain differs at all, and only in focus — the product line rather than the account.

This is **not** evidence that real MBB frameworks converge. It is evidence that our pipeline has removed every point at which they could diverge, *before* the personas are invoked. Two such points were found in code, and they are the two halves of this stage.

**Root cause 1 — the personas inherit an identical constraint set (the dominant one).**

```
ONE interviewer  →  FIXED five topics  →  ONE constraints list  →  top-5 truncation
                                       →  the identical copy handed to all three personas
```
`_generate_refinement_question` (`a9_deep_analysis_agent.py:2981`) runs a single interview. `STYLE_GUIDANCE` (`:105`) *already contains* McKinsey / BCG / Bain framings — but it is keyed on the **principal's** `decision_style`, not on a firm, and it steers **tone only**: `REFINEMENT_TOPIC_SEQUENCE` (`:88`) walks the same five topics regardless. The resulting `constraints` list is truncated to five and copied to every Stage 1 persona (`a9_solution_finder_agent.py:1667`).

Constraints bound the feasible answer set. Give three competent analysts the same bounds and they find the same move; the framework label can then only change how they *describe* the move they were always going to land on. **This is a better explanation of the convergence than any data-access theory** — and it matches how consulting actually differentiates: firms mostly share a data room, and diverge in the scoping conversation that decides what is fixed versus movable.

**Design — one conversation, three questioners.** Three separate interviews is a non-starter (today's flow already runs up to 10 turns; no CFO sits through 30). Instead:
- each persona contributes questions to a **shared** queue — the principal answers **once**, so human burden is unchanged;
- `_extract_refinements_from_response` runs **per persona** with persona-specific extraction instructions, so each reads *its own* constraints out of the shared transcript;
- each persona then solves under **its own** constraint set.

**The failure mode this buys, stated plainly.** Constraints are mostly *facts*, not opinions — "the union agreement runs through Q3" is true regardless of who asks. A persona that never asks about it does not get a differently-valid answer; it gets a **wrong** one, and its option looks *better* precisely because it never learned what would kill it. This is tolerable (it is how a real bake-off works — the client discounts the naive proposal), but it makes the moderator and HITL **load-bearing** in a way they are not today: every option must be checkable against the **union** of constraints, not only the subset its author discovered. Treat that as a build requirement, not a caveat.

**Root cause 2 — dimension selection is hardcoded, so the investigation is nobody's.**
`_dims_from_contract` (`a9_deep_analysis_agent.py:273`) ranks by a static literal:
```python
preferred = ["profit_center_name", "customer_name", "product_name",
             "product_line", "channel_name", "customer_segment", ...]
```
Same ordering for every KPI, client, and problem type. No framework, principal, or problem shape influences it. **Fix this regardless of the persona question** — choosing what to investigate based on the problem is an improvement with a single analyst and no council at all. Two steps, ascending cost:
1. **Route the interview topics and the dimension ranking off the problem profile.** `src/analysis/problem_profile.py` already classifies concentrated-vs-distributed, control-group presence, and cross-KPI conflict *deterministically* — and neither the interview nor the planner consults it. A concentrated single-customer problem and a diffuse enterprise one deserve different cuts and different questions. Cheap, no LLM, helps every path.
2. **Personas propose cuts** (only if step 1 leaves real headroom). The `plan_deep_analysis` → `DeepAnalysisPlan` → `execute_deep_analysis` split is already the injection point; `DeepAnalysisPlan.dimensions` is a plain list. Costs: 3× the fishing risk (each persona finds *something* in its preferred slice), more BigQuery spend and latency, and a moderator that must adjudicate claims resting on **different evidence bases** — which directly weakens G3, since arithmetic cannot be checked against data the moderator never saw.

**Cheap test before committing to either (~$0.50).** Have each persona *propose* which cuts it wants; run DA **once** on the union; compare the three proposals. If all three ask for customer × product, the frameworks do not diverge even on what to investigate and the expensive version is settled without building it. If McKinsey asks for profit-centre structure, BCG for channel and growth, Bain for customer cost-to-serve, the divergence is real and the build is justified.

**Sequencing.** Hold every live run until the `use_structured_output` flip lands (PM-4 — one variable per run). Then: problem-profile-driven topics + dimensions (deterministic, no experiment needed) → cheap proposal-comparison test → shared-interview build only if the test shows divergence. Measure the outcome with the Stage H instruments already built (mechanism fingerprint, groundedness, problem profile), comparing **within** problem type.

**🏁 Stage I B-3 GATE CLOSED (2026-08-12) — CONVERGE. B-4 (shared question queue) is NOT justified.**

The gate asked the question the whole persona-differentiation build rests on: *would the personas actually ask different questions?* Each persona proposed 6 refinement questions on one fixed DA result (lubricants `gross_margin_pct`), self-tagging each against the 9-topic interview vocabulary. Deterministic comparison, no LLM judge. Harness: `tools/ab_harness/b3_question_divergence.py`.

| council | personas | mean topic Jaccard | vs null |
|---|---|---|---|
| MBB | mckinsey, bcg, bain | **0.667** | **above the 95th pct — significantly MORE aligned than chance** |
| diverse (as `_recommend_diverse_council` selected) | mckinsey, pwc_strategy, accenture, kpmg | **0.604** | inside the null range — indistinguishable from random tagging |
| — | *random tagger, 6 picks of 9* | **0.512** (90% range 0.44–0.64) | — |

**The first verdict was wrong, and the error was mine.** The gate originally used a flat "mean Jaccard ≤ 0.70 ⇒ diverge" threshold and reported DIVERGE for both councils. But choosing 6 topics from a 9-item vocabulary produces overlap by arithmetic alone: a **random tagger scores ~0.51**. The threshold sat *below the null*, so it would have called chance divergence — and did, twice. Divergence requires scoring **below** the null; both councils scored **above** it. Corrected in the harness: the gate now simulates the null (fixed seed) and compares against it rather than a hand-picked number.

- **Even across disciplines, the questions converge.** All four diverse-council personas asked the same three things — what changed in period 2026-006, whether the erosion is segment-concentrated, and which external cost/competitive factors apply. What differed was **house vocabulary**, not substance: PwC framed it as *capabilities* (pricing governance, procurement), Accenture as *systems* (ERP/pricing-system constraints on granular margin instrumentation), KPMG as *governance* (escalation thresholds, controls). One analysis in four costumes — the original Stage I observation, reproduced at four personas spanning four disciplines rather than three strategy houses.
- **MBB collapses to two.** McKinsey and BCG produced **identical** topic sets (Jaccard 1.00); only Bain differed. A three-firm council is effectively two questioners.
- **Decision: close Stage I at B-2 for now.** Do not build the shared question queue or per-persona constraint sets *as designed*. The B-2 machinery (constraint provenance, the register-crowding truncation fix, the deterministic exposure report, the HITL "no adjudication pass ran" string) stands on its own merits and stays. **Superseded in part — see the extension below.**
- **Cost: ~$0.07 total** across both councils (6,265 in / 3,835 out tokens, `claude-sonnet-5`) against a $0.50 budget — the cheapest finding in Phase 15, and it prevented the most expensive build in it.

**🔬 B-3 EXTENSION (same day, 5 further arms, ~$1.15) — the convergence is the ROSTER, not the pipeline.**

Full record, methodology lessons and the proposed test series: **`docs/architecture/persona_council_experiments.md`**. Summary of what changed the conclusion:

- **Correction to the readout above.** The 20-mind arms tag 2 topics of 9, not 6, and that null (**0.157**) was not computed at the time. Against it, *every* council tested — including the 20 methods — sits **above** its null. Topic selection converges under every configuration; only the famous-four arm reached its null. The problem constrains which questions are worth asking. What differentiates is the **content within** topics, which topic-tag Jaccard cannot see and lexical Jaccard tracks (0.26 → 0.058 across the roster range).
- **Three clean single-variable comparisons.** Model only: MBB 0.667 → **0.810** (*more* convergent on the better model); 20 methods 0.405 → **0.311** (*more* divergent). Prompt only: 20 methods on Fable, authored profiles → **name only**, 0.311 → **0.261** (*more* divergent). One model change, two opposite directions, decided by who is in the council.
- **The differentiation is not authored.** Stripping the profiles entirely and prompting with the bare name *increased* divergence and surfaced concepts absent from any profile text — Ohno → *gemba*, Levitt → *electric*/*drivetrains*, Drucker → *abandonment*, Munger → *invert*. It lives in the model's knowledge of these people, which closes the circularity objection.
- **The consequential result.** Two of twenty methods (Carnegie, Deming) independently proposed the margin decline might be an **accounting artefact** — under-absorption from volume shortfall, or a costing-methodology change — before diagnosing any commercial cause. **Zero of the six consulting personas did.** The Aug 9 slice-validity incident was exactly that failure, and it passed SA, DA, three MBB personas and a briefing intact.
- **Revised recommendation:** the lever is **roster composition**, not the shared queue. Replace the consulting-firm roster with a method roster and keep the existing `_recommend_diverse_council` selection machinery — which also dissolves the roster defect below rather than patching it. B-4 should be re-asked against personas that actually differ.
- **NOT authorised, and the reason is explicit.** Every number measures *divergence*, which is a proxy. Nothing tests whether these questions elicit constraints that change the recommendation, and the load-bearing risk runs the other way — a council optimised for divergence could be a council optimised for mutual ignorance.

**🏁 PHASE 0 OUTCOME MEASURE RUN (2026-08-12, $0 — scored the saved payloads). The persona line CLOSES.**

Scored all seven arms on the only thing that matters: *does any persona challenge how cost was assigned before diagnosing a commercial cause* — the question that would have caught the Aug 9 artefact. `tools/ab_harness/b3_artefact_score.py`.

| council type | genuine hits |
|---|---|
| consulting + famous (arms 1–4) | **0 of 14 persona-slots** |
| 20 methods (arms 5–7) | **4 of 60 (~7%)** — Carnegie, Deming ×2, Ohno |

- **The roster thesis holds directionally and fails practically.** 0% vs ~7% is real, and it is the cost-accounting / SPC / shop-floor methods doing all of it. But selecting 4–6 from a 20-library is roughly a coin flip on including Carnegie or Deming. **A defect that produced a −457% margin and reached a briefing cannot be defended by a persona lottery.**
- **Decision: do not solve this with personas.** The artefact question must be asked deterministically on every run. `scripts/check_slice_validity.py` already computes it and is wired to nothing; the governed version is designed in `kpi_semantic_contract.md` §4 (sliceability). **Wiring that check now outranks any council change.** The stop rule written into the test design fired, and ~$0 of new spend closed a line that phases 1–3 would have refined at real cost.
- **Instrument caveat.** The term screen threw 14 candidates of which 4 survived adjudication — a **71% false-positive rate**, dominated by `absorb` in the commercial sense (*"we absorbed the cost increase"* ≠ absorption costing). Adjudication is recorded as data beside the screen rather than folded into a cleverer regex. The first version of that lookup had an off-by-one that turned every verdict into `unreviewed` and displayed as 0 genuine across all arms — a not-checked masquerading as a fail, caught only because a uniform zero looked wrong.
- **Limitation:** all arms saw the post-fix (clean) data, so this measures whether the method asks the question *as standard practice* — the property you actually want, since the check must fire before anyone suspects a problem.

**Also found by this gate, both recorded not fixed:**
- **The "four-firm" diverse council has two real choices and can seat one firm twice.** `technology` and `risk` have a single member each (Accenture, KPMG), so they are constants rather than selections; and KPMG sits in **both** `big4` and `risk`, so a risk-flavoured problem returns KPMG in two seats. Details on `A9_Deep_Analysis_Agent_card.md`.
- **`_build_kt_summary` formats percentage-point deltas as dollars.** The refinement prompt — production, not just the probe — renders `- Synthetic Blend Engine Oil: $-7 (0.0% of variance)` for a −7.1pp move, with a variance share that always rounds to zero. Same `KPIValue.unit` gap listed under Known Issues, surfacing in a new place. Identical for every persona, so it did not bias the gate.

#### A total LLM outage renders as a successful briefing (found 2026-08-09, NOT fixed)

A live Solution Finder run was attempted to refresh a test fixture. The Anthropic account had **zero credit**, so every LLM call failed:

```
credit balance is too low to access the Anthropic API
```

The workflow returned:

```
state: completed        error: None
options: "Tighten spend controls", "Optimize pricing"
```

The payload **does** carry `heuristic_stub_fallback` and the credit error in its audit trail — so the detection exists. It simply never reaches the reader. A user sees two plausible generic recommendations in a finished briefing with no signal that no analysis occurred.

This is the identical pattern already fixed once for narrative claim validation: *detection that reaches only an audit payload is a smoke alarm wired to a notepad.* The fix is the same shape — surface it as a reader-facing caveat, and consider whether a run in which **every** LLM call failed should report `state: completed` at all rather than `failed`.

Worse than a wrong number, because a wrong number can at least be argued with. This one is indistinguishable from a real recommendation, and its blandness ("tighten spend controls") is exactly what an executive would expect a weak AI tool to say — so it discredits the product precisely when it is not working.

**Also blocked by this:** refreshing the SF half of `tests/e2e/fixtures/live-briefing-payload.json`. The DA half is current (live, corrected data); the SF half predates the data fix, which is why the rendered ROI shows "534-825% of Chain A's decline". Needs one synthesis call once the account has credit.

#### RETRACTED: the `_rank_options` clustering concern (measured 2026-08-09)

**The claim, now withdrawn.** A live briefing showed two of three options with an identical Est. ROI and all three reading "Moderate Effort" / "Medium" risk, and this doc attributed that to `_rank_options` operating on LLM-assigned 0–1 scores that cluster — "the formula wraps that choice in the appearance of rigour". Measured against 18 captured SF payloads, **that is not what is happening.**

| field | observed across runs | verdict |
|---|---|---|
| `cost` | 0.25 / 0.30 / 0.50 — wide | spread; **display** bucketed it away |
| `risk` | 0.45 / 0.55 / 0.65 — wide | spread; collapsed to one label in **4 of 9** runs |
| `expected_impact` | mean spread **0.159**, range 0.06–0.30 | genuinely differentiated |

All three were **display** defects, not model behaviour. Three coarse bands (`≥0.7 / ≥0.4 / else`) destroyed differentiation the model had supplied. Fixed by widening to five bands and disclosing within-band order (`e9f7a39`). **No `_rank_options` change is warranted on this evidence.**

Method note: the same instinct that produced this wrong diagnosis produced the correct one about slice validity — the difference was that the second was checked against data before being acted on. Both should have been.

**What the measurement DID find, unremarked until now: a shared floor.**
```
baseline_1   18.5-31.2   18.5-26.3   18.5-28.0
baseline_3   18.5-31.2   18.5-26.3   18.5-28.0
moderator_5  18.5-31.2   18.5-28.0   18.5-26.3
```
The **low bound of `recovery_range` is identical across every option in 11 of 18 runs** — only the ceiling moves. So the ROI row looks differentiated while sharing a floor: every option is "18.5 to something". Not necessarily wrong (a floor could legitimately be the confirmed-recoverable amount, with options differing only in upside), but it is undocumented, nobody chose it, and it makes the apparent spread narrower than it reads. Worth a decision before the ranges are used for anything consequential — VA impact bounds in particular.

Genuine full duplicates are rarer than the briefing suggested: **2 of 14** non-stub runs. The other four "identical" rows are heuristic-stub fallbacks carrying no range at all.

#### Slice validity — found in production 2026-08-09, demo data FIXED, capability deliberately NOT built

**What happened.** The Lubricants demo dataset attributed **all** COGS to a single customer while revenue spanned twenty. Gross margin by customer therefore read **−457.71%** for that one account and **exactly 100.00%** for the other nineteen. Every layer above behaved correctly on top of it: SA raised a breach, DA found the "concentration", three MBB personas diagnosed a base-oil pass-through, and the briefing recommended renegotiating a contract to correct an ETL defect. The enterprise figure (33.25%) was right throughout — which is exactly why it survived. **The error only exists once you slice.**

Root cause was in the generator, not the warehouse: COGS rows were distributed across product and profit centre but pinned to `cust_id="C-RP-01"` / `ch_id="CH-DIY"`. The same defect sat on the Budget side and was arguably worse — a single pinned row *and* only the base-oil share of cost (`0.65 × 0.40`), implying a **74% budget margin against a 33% actual**, i.e. a fabricated ~41pp variance on every plan comparison in the system.

**Why every existing check missed it.** All Phase 15 instrumentation verifies arithmetic *inside* the pipeline — does the prose match the measured number (`narrative_claims`), does an impact claim match the observed delta (`groundedness` G3). **Nothing asked whether the slice itself was meaningful.** That is a different class of check, and no amount of downstream rigour substitutes for it.

**Fixed (2026-08-09).** COGS is now derived from the revenue lines at full dimensional grain, with per-product `cogs_ratio` and `base_oil_share` (`PRODUCT_ECONOMICS`) so margin genuinely varies by mix, plus `CUSTOMER_PRODUCT_BIAS` so accounts have realistically different mixes. Verified live: coverage symmetric on all six dimensions, margins 30.1–34.6%, enterprise 32.16%, plan variance −2.68pp.

**Consequence for the demo narrative — the protagonist changed.** The old story ("Chain A collapsed 43pp") was the artefact. The corrected data says: the base-oil shock is **distributed across customers** (−4.18 to −6.03pp, no concentration) and **concentrated in products** (Synthetic Blend −7.86pp, Conventional −7.33pp), *plus* a separate structural finding that Chain A is the weakest large account on level (30.53% vs Chain B's 34.56%) because of mix. This is a better exercise for the pipeline — DA now has a **non-empty IS-NOT set** ("not concentrated by customer, is concentrated by product"), which the old data could not support and which was noted above as a gap. **Any saved payload or screenshot citing −43.24pp is stale.** Deliberately *not* tuned further to manufacture a customer-level concentration; the flat spread is the truth of a raw-material shock.

**Built: an internal script, not a capability.** `scripts/check_slice_validity.py` profiles per-component dimensional coverage and reports which dimensions a ratio KPI can legitimately be cut by. Run **by hand** before building a demo on a new client dataset. Not wired to any agent, gates no workflow, has no UI. Enforcement in DA/SA/UI was designed and **explicitly rejected as scope creep** at demo stage. `"ok"` requires **full** coverage — 19 of 20 values means one slice is fabricated, and partial coverage is the case most likely to be believed. The pre-fix BigQuery profile is frozen at `tests/fixtures/lubricants_uneven_granularity_profile.json` so the case survives its own fix (`tests/unit/test_slice_validity.py`, 14 tests).

**Deferred to pilot: allocation provenance.** The coverage check measures **presence, not provenance** — a fully-allocated COGS column looks perfect to it. In a mature SAP CO-PA / S4 Margin Analysis landscape standard COGS *does* carry customer and product from the sales document, so the crude check often will not fire in the enterprise ICP; its value concentrates in mid-market and in warehouse layers that dropped characteristics, a segment not yet validated. The genuinely dangerous case is the one it cannot see: **cost that reached the customer by allocation rather than observation.** If a margin move is driven by allocated cost, the root cause may be an allocation-driver or basis change rather than the business — someone re-weights a driver and an account goes from profitable to catastrophic with nothing having happened commercially. Unlike 100%-margin rows, that is invisible to inspection. Cannot be built honestly against synthetic data; needs a real CO-PA/PaPM feed where the cycles exist. **Raise in pilot scoping conversations** ("we'd flag if your margin move came from an allocation change rather than the business" is strong to a controller) — never as a demo slide, where it invites a technical argument in a room that wants a business conversation.

**Open commercial question this raises.** If three MBB personas reliably yield one hypothesis, we are paying for three calls plus council machinery to obtain one idea — and presenting a "council" narrative that implies more independent scrutiny than occurred. That is a credibility exposure with a CFO who knows these firms. The earlier diverse-council run (McKinsey / KPMG / Accenture) *did* produce genuinely distinct archetypes — negotiate / govern / platformize — which appeared in none of the 10 MBB runs. Working hypothesis: **persona differentiation pays when the disciplines genuinely differ, and collapses when they do not.** Stage I tests whether framing-level differentiation can recover it within a single discipline; if it cannot, the honest options are one strategy persona plus genuinely different disciplines, or keeping three but no longer calling it a debate.

**🔬 EVIDENCE-SCOPE EXTENSION (2026-08-14/15, 11 further real SF runs) — the persona line stayed closed; two adjacent lines opened, ran, and closed too.**

Full record: **`docs/architecture/persona_council_experiments.md` §7b/§7c.** This work did not reopen B-4 — it followed a different architectural insight, that SF reasons over the dimensional decomposition of one KPI (WHERE it moved) and had two broken channels to WHY: causal-graph traversal was single-hop, and `market_signals` was never read by SF at all.

- **Two false zeros fixed first.** `_build_kt_summary` rendered percentage-point deltas as dollars (`$-7` for a −7.14pp move, collapsing distinct drivers onto identical values) and asserted `"(0.0% of variance)"` against every driver because the field is absent on the flat dimension path, not zero — this is the same defect the Aug-12 gate flagged at line 2022 above, now fixed via the KPI's registry unit. Separately, the SF `causal_context` audit event read `constraints` before fetching them, so every run reported `constraints: 0` regardless of what the register held — the register was correct throughout (one active lubricants constraint); only the audit was blind. Both pinned by regression tests. **27 of the 33 real-run options in this whole exploration were generated over the broken unit string** — a fact worth remembering before re-reading any option text quoted in this doc from before 2026-08-14.
- **Causal traversal (`max_hops` 1→2): no measurable effect, and the null is explained, not mysterious.** `get_causal_neighbourhood()` (BFS, hop-tracked) shipped and works — verified live. But on lubricants `gross_margin_pct`, the *direct* edge's mechanism prose already names base oil ("largest COGS input... passes through to COGS with a lag"), so the 2-hop node added precision, not the concept. **Graph depth and mechanism prose are substitutes** — the effect should reappear on a KPI whose near edges are still `mechanism: null` (three of six lubricants edges are). Not retested; not urgent.
- **Market-signal routing: one concrete, checkable win.** Without it, an indexed pricing clause benchmarked to **WTI crude** — wrong, since the crude-to-base-oil spread is exactly the risk being hedged. With signals routed in, it benchmarked to **Group I/II base oil spot**, the correct grade, traced to a specific MA signal. Kept.
- **Step 1 — task-statement permission to challenge the frame: null at n=2.** New flag `stage1_allow_frame_challenge` (default `False`, off-branch verified byte-identical to production text) gave Stage 1 explicit optional permission to propose a portfolio/exit move instead of a KPI recovery. **0 of 6 treatment options used it.** Closed — do not spend further on wording variants.
- **Step 2 — lens roster (Commercial/Operational/Structural, replacing McKinsey/BCG/Bain): null on the target, real value found along the way.** Building this surfaced that `to_prompt_context()` renders `## Consulting Advisor: McKinsey & Company` — the actual protected firm name — directly into production LLM prompts today, for all eight personas in `consulting_personas_registry.yaml`. The lens roster removes that exposure. On the actual question, **still 0/6 portfolio options**, even from a persona explicitly briefed for that lens (`typical_recommendations` names "portfolio reallocation" almost verbatim) — its frame-questioning transferred but pointed inward at an existing option's assumption, not outward at category participation. Kept as an available `council_preset` (`lens_council`) for the trademark fix alone; not presented as solving the portfolio gap.
- **Cumulative finding across both steps: 33 real options, zero structural, across two independently-tested variables (wording, roster) that both explicitly targeted the gap.** That is stronger evidence than either result alone that the missing ingredient isn't wording or who's asking — closed both lines rather than running a third variant.
- **Still open, not started:** whether the shared evidence base (DA output, refinement, market signals) contains what a portfolio-level call would need to be *grounded* rather than speculative. SF sees a KPI, not a category. Untested, and the natural next question if the portfolio gap is worth closing.

**Also found, not yet acted on:**
- `SF_ENABLE_CAUSAL_GROUNDING` defaults to `false` in code (`os.getenv(..., "false")`); it is only `true` in local `.env` for this exploration. Whether to enable it in production is an undecided, separate question from whether it works.
- Part A's own plan required a live lubricants DA run reporting `dimension_rank_source`, `dimensions_analyzed`, and measured latency **before Part B started.** Part B (B-1 through this extension) proceeded without it. Still owed.
- 36 files from Part A, B-1/B-2, this extension, and their tests are uncommitted as of this readout.

**🏁 `check_slice_validity` SHIPPED (2026-08-15).** Wired into onboarding Day 6 and Settings → Maintenance per the item above — `docs/architecture/kpi_semantic_contract.md` §4, advisory only, does not gate DA (confirmed by grep: zero references to `not_sliceable_by`/`slice_validity` anywhere in `a9_deep_analysis_agent.py`/`a9_solution_finder_agent.py`/`a9_situation_awareness_agent.py`). Four real bugs found and fixed via live verification against BigQuery and SQL Server, none catchable by a mocked unit test — cross-tenant KPI-id collision (`gross_margin_pct` exists for both `lubricants` and `brookshire_brothers`), BigQuery routing silently falling through to DuckDB because `KPI.view_name` is stored bare rather than fully-qualified, `GROUP BY component` (a SELECT alias) rejected by T-SQL, and a datetime-serialization bug that let a failed write report `status="success"`. Full detail in the commit series starting `efc8262`.

Then ran the check against every genuine multi-component KPI in lubricants and hess (9 of 26 KPIs — the rest are single-component sums with no grain-mismatch risk to check). Two findings worth keeping as **cleanup items with real demo value**, not just defects:

1. **Hess: `country` is `INVALID` across all four composite KPIs** (`gross_profit`, `ebitda`, `operating_income`, `return_on_capital` — consistent because they share the same underlying Revenue/COGS/SGA rows). The other four dimensions (`segment_name`, `basin_name`, `asset_name`, `business_unit`) are all `degraded`, not clean. This is exactly the "your COGS doesn't reach country grain" story `check_slice_validity.py`'s own docstring was written to catch — worth deciding whether to leave it as an authentic imperfection (a demo that shows the tool catching something real) or fix Hess's synthetic COGS/SGA generation the way lubricants' was fixed 2026-08-09.
2. **Lubricants: `channel` and `region` can't be checked at all** — BigQuery rejects them (`Unrecognized name: channel`; `Did you mean version?` for `region`). `KPI.dimensions` declares those two names on every lubricants KPI, but the actual view doesn't have columns by those names — the exact "allow-list decayed into stale declarations" failure `kpi_semantic_contract.md` §4.2 already names as the reason `KPI.dimensions` shouldn't be trusted as-is. Likely should be `channel_name`/`customer_region`, matching the naming convention every other lubricants dimension already uses. A real registry-data fix (via the `scripts/clients/lubricants.py` seed file, per the registry sync protocol), not touched here.

Excluded from the batch on purpose: `premium_mix_pct` (both lubricants and its `apex_lubricants` Snowflake twin) and `top3_customer_revenue_share` (apex only) — same reason: each splits one measure by an attribute, not two separately-recorded components, so the grain-mismatch check doesn't apply. `bicycle` (deprecated DuckDB backend, near-empty dataset) not run.

**apex_lubricants (Snowflake) — first live run against that backend, and it found a real bug on first contact.** Rows came back `{"COMPONENT": ..., "N": ...}` (Snowflake's default uppercase for unquoted identifiers), not the lowercase keys every other backend returned — a `KeyError` that sat outside the per-dimension error handling and killed the *entire* check, not just one dimension. Fixed case-insensitively (not a Snowflake special case) in the same commit that also made a row-shape surprise on one dimension degrade like an absent column, rather than aborting the whole run. See commit `b4133d9`.

Post-fix, 4 KPIs checked (`gross_margin_pct`, `gross_profit`, `operating_income`, `ebitda`), all four dimensions resolved correctly, and the finding is worth keeping for the same demo-depth reason as Hess's: **`customer_segment` and `channel_name` are `INVALID`, `product_line` and `profit_center_name` are `degraded`** — nothing on this dataset is cleanly sliceable, consistent across all four KPIs since they share the same underlying Revenue/COGS/SGA rows. Total populated at this point: 13 of 42 KPIs — **superseded below, same day.**

**🏁 SECOND CHECK ADDED (2026-08-16): completeness, not just cross-component coverage — a real gap a user caught directly.** Asked "why are so many of the simple KPIs excluded" and pushed back on the answer: *"we must measure every KPI, compound or not, to confirm it's fully additive for each dimension."* Correct, and the exclusion above was wrong, not just incomplete — cross-component coverage (do 2+ components reach the same dimension values) structurally cannot apply to a single-component KPI, but a single-component KPI can still be wrong when sliced: some rows might have no value for the dimension at all, silently dropping out of "revenue by customer" rather than corrupting one customer's number, and nothing checked for that.

New `check_completeness()` in `src/analysis/slice_validity.py` — `COUNT(dim)` vs `COUNT(*)`, filtered to the KPI's own components — answers that, and applies to EVERY KPI regardless of component count. `check_slice_validity()` now runs both per dimension (completeness always; cross-component only with 2+ components) and persists both; `not_sliceable_by` is the union of either landing on `INVALID`. New `extract_components()` auto-derives a KPI's components from its own `sql_query` via regex — required to run this against all 42 KPIs without specifying components by hand for each one.

**Auto-derivation found a second real bug on first full-registry run:** four KPIs (`product_sales_revenue`, `service_revenue`, `base_oil_cost`, `distribution_cost` — on both BigQuery and Snowflake) filter on `account_category`, not `account_type`, and have no `account_type` reference anywhere in their `sql_query`. `extract_components()` now tries `account_type` first, falls back to `account_category`. Fixed in the same pass; full commit history has both bugs.

**Result: 42/42 KPIs checked (up from 13) — every KPI in both registries, no exclusions.** `premium_mix_pct` and `top3_customer_revenue_share`, excluded in the first pass as "wrong shape for the tool" (they split one measure by an attribute, not two components), turned out not to need excluding at all — completeness applies to them too as ordinary single-component KPIs; only cross-component correctly stays empty for them. **217 total dimension-checks persisted** (164 completeness + 53 cross-component) across all three real backends: **170 ok, 25 degraded, 22 INVALID.** Lubricants remains the only fully clean client (matching its known post-Aug-9-fix state); Hess and Apex are uniformly imperfect within each client, for the reason recorded above — one root cause (COGS/SGA coverage vs Revenue's) surfacing identically across every downstream composite KPI, now additionally confirmed present in the single-component completeness numbers on the same clients.

**🏁 apex_lubricants `customer_rank` bug found and fixed (2026-08-15).** Re-running `scripts/validate_client_kpis.py` live (never trust a 5-day-old written record) turned up a new, previously undocumented error: `top3_customer_revenue_share`'s `sql_query` referenced `customer_rank` — not a stored column anywhere in `LubricantsStarSchemaView` (confirmed by reading the full `CREATE VIEW` in `scripts/load_lubricants_to_snowflake.py`), and never computed via `RANK()`/`ROW_NUMBER()` anywhere in the codebase. The KPI was authored assuming a pre-materialized ranking column that was never built — a genuine authoring bug, not a schema drift. Fixed in `scripts/clients/apex_lubricants.py` by rewriting the query as a two-CTE window-function computation (rank customers by summed revenue, then sum the top 3) — standard ANSI SQL, no schema change needed. Verified live: apex_lubricants now **16/16 clean** (was 15/16). Not yet synced to production Supabase — per the registry sync protocol, needs `onboard_client.py --client apex_lubricants --env production` after this commit lands.

**🏁 Three-client SA/DA live verification (2026-08-15/16), per the approved differentiated plan (clean data now, narrow gap fixed first, known-bug client held).**

- **lubricants (BigQuery) — clean baseline, confirms no regression.** SA: 12 real situation cards (Operating Income −19.4% YoY critical down to avg_transaction_value +1.6% high). DA on `gross_margin_pct`: `dimension_rank_source=contract_semantics`, same 10-dimension set and identical top-5 change points as the pre-session verification (Synthetic Blend Engine Oil −7.14, Conventional Engine Oil −6.61, Value −6.42, Compressor Oil −5.86, Engine Oils −5.8) — confirms the whole slice-validity/database_provider/runtime change set this session made introduced no regression to the live pipeline.
- **apex_lubricants (Snowflake) — clean after the `customer_rank` fix.** SA: 7 plausible situation cards (Gross Margin % −14.6% YoY critical, Gross Profit −9.8%, EBITDA −6.3%, Net Revenue +5.6%, Operating Income +1.3%) — no NULLs, no impossible percentages. DA on `gross_margin_pct`: ran successfully, 10 dimensions analyzed, 5 change points — **but the per-slice values themselves are implausible**: `customer_name="National Auto Parts Chain A"` shows a margin delta from −401.8% to −445.0%, `profit_center_name="Service Centers Division"`/`business_unit="Service Centers"` show −53.1% to −68.3%. These are not crashes or nulls — DA reports `status="success"` — they are silently wrong numbers.
- **This is the slice-validity check correctly predicting a real DA failure, on the second client, live.** `GET /admin/slice-validity?kpi_id=gross_margin_pct&client_id=apex_lubricants` shows `profit_center_name` at **degraded** cross-component coverage (COGS reaches only 3 of 4 Revenue-side profit centers) — the exact dimension that produced the −68% garbage value in DA's live change points. This is the second live confirmation of the class of bug the whole feature was built to catch (the first being the original Aug 9 lubricants incident), now caught *before* a demo rather than after one — because the check was populated (this session's earlier work) even though nothing yet gates on it (deliberately advisory-only, unchanged).
- **New cleanup finding, not yet acted on:** slice-validity's checked dimension set for apex KPIs comes from `KPI.dimensions` (`_DIMS` in the seed file — currently just `product_line`, `customer_segment`, `channel_name`, `profit_center_name`), but DA's live `dimensions_analyzed` pulls the full DPA schema, which also includes `customer_name`, `product_name`, `business_unit`, etc. `customer_name` — the dimension with the single worst DA value (−445%) — was never in slice-validity's checked set at all, so even a hypothetical future "auto-run on every KPI" would not have caught it. Worth widening `_DIMS` (or decoupling slice-validity's dimension source from `KPI.dimensions` toward DPA's actual schema) as a follow-up — noted here, not fixed.
- **hess (SQL Server) — held, not run, per the approved plan.** `validate_client_kpis.py` re-confirmed live: 7/16 problems unchanged from the 2026-08-10 record (`gross_margin_pct`=165.57% vs true 34.43%, `return_on_capital`=301.63%, 5 NULL KPIs). Running SA/DA here would not validate anything — SA finishing "successfully" is the exact silent-failure mode already diagnosed (sign-inverted COGS/SGA), and a clean-looking run would be false confidence, not evidence. Held pending the documented fix path: `measure_semantics` field on `DataProduct` contract + a negation validator (Phase 16 step 2), still unbuilt.

**🏁 Two live DA bugs found and fixed during this verification (2026-08-16), neither caught by the unit suite — the manual click-through the user did on Net Revenue's "Diagnose vs Budget/Plan" drill turned up both.**

**Bug A — only the first dimension ever populated the Variance Breakdown table.** [a9_deep_analysis_agent.py:1664](src/agents/new/a9_deep_analysis_agent.py#L1664) (pre-fix) gated the per-dimension fallback query on `if not kt.where_is:` — intended as "did *this* dimension's fast path fail to find anything," but `kt.where_is` is the list accumulated across *all* dimensions in the loop, not per-dimension state. The budget comparator forces every dimension through this fallback (the fast "TopN" path has no SQL shape for "vs budget" at all — it only knows how to rank by `delta_prev`, a period-over-period column; budget lives in a different `version` value of the same rows, not a second time window, so there's no single-query shortcut for it). Once dimension 1 (`product_name`) populated the list, the gate stayed permanently closed for dimensions 2–10 — they silently contributed nothing. Fixed by snapshotting `len(kt.where_is)` before each dimension's own pass and comparing after, so each dimension is judged on what *it* added, not on the loop's running total. Verified live: broken (14 items, all `product_name`) → fixed (70 items across all 10 dimensions), restart-and-reproduce both ways.

**Bug B — the "vs Budget/Plan" table was actually showing prior-period data, mislabeled.** Found while fixing Bug A: the same fallback block that Bug A was in, once reached for `comp_fb == "budget"`, ran an unconditional actual-vs-*prior-period* dual query (`comparison_period=True`) — never touching budget data at all. Confirmed by direct comparison: `product_name` deltas were byte-identical between a `comparator="previous"` run and a `comparator="budget"` run of the same KPI/timeframe. This codebase has a second, separate code path (`_maps_for_level`, used only when a client declares hierarchical dimension vectors) that *does* correctly build a real budget comparison via a version-substituted proxy KPI (`_budget_variant_kpi` — same helper already used correctly for the KPI-level headline number and the per-dimension rollup totals) — but the flat/legacy loop that most clients actually run through (lubricants included; no hierarchy declared) never called it. Fixed by branching the fallback on `comp_fb`: budget now runs the same real actual-vs-budget dual query as the correct path elsewhere in this file, previous still runs actual-vs-prior-period as before. Verified live: post-fix budget-comparator deltas now genuinely diverge from previous-comparator deltas for the same KPI (e.g. `product_name="Conventional Engine Oil"`: previous=+$918K, budget=−$2.19M) — proof the two bases are no longer the same query wearing a different label.

**Found while verifying Bug B, deliberately not fixed — a real budget/actual granularity mismatch, live in the seed data today.** Raised directly by the user before this fix shipped: FI budget data is commonly recorded at a coarser grain than actuals (e.g. by product category, not by product), and a naive actual-vs-budget-by-segment query will silently produce a confidently wrong number wherever that's true, rather than an error. Checked `generate_lubricants_demo_data.py` and found this is not hypothetical: **Revenue and COGS budget are correctly distributed across the full customer × product × profit-center × channel grain** (the generator's own comment records this was already fixed once, after an earlier bug where budget COGS was pinned to one customer) — **but budget SG&A is still a single row pinned to one customer/product** ([generate_lubricants_demo_data.py:526-531](scripts/generate_lubricants_demo_data.py#L526-L531)). Live-reproduced the consequence on `operating_income` (includes SG&A) sliced by `customer_name`, post-Bug-B-fix: `National Auto Parts Chain A` (= `C-RP-01`, the exact pinned customer) shows a −$11.59M delta — 6 to 20× larger than every other customer's −$400K to −$1.5M — purely an artifact of it silently absorbing 100% of budget SG&A while every other customer's budget SG&A defaults to $0. Decision (user, 2026-08-16): ship Bug A/B's fix now — strictly better than today's mislabeled-as-budget prior-period numbers even with this gap — and record the granularity mismatch as a follow-up rather than block on it. **Two remediation paths, not yet chosen between:** (1) fix the seed data — distribute budget SG&A across the same grain as actuals, mirroring the fix already done for revenue/COGS; (2) build a general coverage gate — before trusting a per-segment budget comparison for a given dimension, compare Budget's distinct-value count against Actual's for that dimension (same shape as this session's `check_completeness()`, applied to the version/comparator axis instead of the account-component axis) and suppress or flag segments where Budget doesn't reach comparable coverage. (2) is the one that protects against this on a *real* client with genuinely coarse budget data, which (1) alone does not.

**🏁 §4.5 SHIPPED (2026-08-16): `not_sliceable_by` now enforced in DA, not just displayed — the decision this whole feature deferred twice, reopened by the user and closed the same day.** Walking through the onboarding UI, the user asked directly why nothing in SA/DA reads `not_sliceable_by` — the answer ("advisory only, explicitly rejected as scope creep") held up until the user stated the field's actual original purpose: *"the reason we added the not sliceable by is to protect the DA from mis-calculating KPIs."* `docs/architecture/kpi_semantic_contract.md` §4.5 confirms that was always the design ("Exclude the dimension from `dims_to_process`... **But record every exclusion**") — what shipped earlier this session was a deliberate partial build (display only), not the full spec.

Before enforcing, checked §4.6's stated precondition first rather than assume it was satisfied: a deny list needs `reason_class` (`structural` = permanent fact about the client's business vs `pipeline_gap` = a completeness gap in the client's own source data/ETL) or it becomes, in the doc's words, "a place to hide bugs." Confirmed live: `reason_class` didn't exist anywhere in the implementation — every `not_sliceable_by` entry was a bare dimension name. User chose the full build (classify + enforce) over enforcing on top of the unclassified list. **Correction the same day:** `pipeline_gap` is not an Agent9 code defect — the user caught this directly: *"the fact that some dimensions in the data product are not sliceable will not be a bug for Agent9 to fix."* Right — Agent9 doesn't own the client's warehouse ETL; `pipeline_gap` is a data-completeness finding worth surfacing to whoever DOES own that pipeline (the client's data team, or Agent9's onboarding/implementation function for that account), not an internal engineering ticket. Reworded everywhere this was written as "bug/ticket" language — model docstrings, the DGA comment, and the UI banner text a client or onboarding staff would actually read.

**Built:**
- `NotSliceableByEntry {dimension, reason_class, note, source}` — both `src/registry/models/kpi.py` (registry layer) and `src/agents/models/data_governance_models.py` (agent I/O layer, deliberately duplicated rather than cross-imported, matching this codebase's existing layering). `reason_class` defaults to `pipeline_gap` — profiling alone can't distinguish a permanent fact from a bug, and §4.3's "prefer loud" principle means an unclassified gap defaults to actionable, not to assumed-permanent.
- Backward-compat `field_validator` on `KPI.not_sliceable_by` normalizing legacy bare-string entries (real persisted data from earlier in this session's batch run) into structured entries on load — no data migration needed, confirmed live (see below).
- `A9_Data_Governance_Agent.check_slice_validity()` now builds structured entries with a human-readable `note` quoting the actual coverage numbers, instead of a bare dimension name.
- `A9_Deep_Analysis_Agent.execute_deep_analysis()`: denied dimensions are excluded from `dims` **before** the `max_dimensions` cut (not after — a denied slot frees room for a valid dimension per §4.5's "useful interaction," rather than wasting a query slot on a cut already known meaningless), in both the flat/legacy loop (what every seeded client actually uses) and the hierarchical vector path (unused today, fixed for consistency anyway — "advisory only" claims should be true for every path, not just the tested one). New `DeepAnalysisResponse.dimensions_excluded: [{dimension, reason_class, source}]` — exclusion is never silent, matching §4.5's "one rule that must not be broken."
- UI: `SliceValidityPanel.tsx`'s deny-list banner now shows `reason_class` per dimension and states plainly that DA acts on this, not just displays it; `DeepFocusView.tsx`'s Analysis accordion shows a "Not sliced: X, Y — flagged by slice-validity" note whenever `dimensions_excluded` is non-empty, so "why isn't this dimension here" always has a visible answer in the product, not just in a log line.

**Live-verified end to end on `apex_lubricants`/`gross_margin_pct`**, reusing the exact persisted state left over from the earlier batch run — `channel_name` and `customer_segment` (flagged `INVALID` in that run, persisted in the *old* flat-string shape) came back correctly excluded: absent from `dimensions_analyzed` and `where_is`, present in `dimensions_excluded` with `reason_class: pipeline_gap`. The backward-compat normalizer upgraded the legacy data transparently — no migration script run, none needed. `dimensions_analyzed` also grew to reach two dimensions (`account_name`, `account_type`) it hadn't reached before, live confirmation of the "excluding known-invalid cuts frees slots" mechanic. `profit_center_name` (flagged `degraded`, not `INVALID`) correctly stayed in the analysis — the existing ok/degraded/INVALID threshold from earlier this session is unchanged; only `INVALID` lands in the deny list.

**Deliberately not built, recorded rather than silently skipped:** `validate_registry_integrity` does not yet surface `pipeline_gap` entries as a data-quality finding (§4.6's other requirement — the deny list should double as a running inventory of the client's own data-completeness gaps, worth flagging to whoever owns that client's pipeline, not just a static exclusion list nobody revisits). Every entry `check_slice_validity()` writes today defaults to `pipeline_gap`, so this inventory already exists in the data; it just isn't surfaced anywhere yet. Fast-follow, not required for DA's own correctness — DA excludes on `not_sliceable_by` regardless of whether anything downstream reads `reason_class`.

1175 unit tests pass (7 new — `tests/unit/test_kpi_not_sliceable_by_model.py`, covering the structured shape and the backward-compat normalizer; DA's own exclusion logic has no direct unit test, matching the pre-existing gap for the rest of `execute_deep_analysis`, which nothing in this codebase unit-tests end-to-end — live verification is the coverage for this method, same as Bug A/B above). Frontend `npm run build` passes clean.

**🏁 PUSHED TO PRODUCTION (2026-08-16).** All 20 commits from this branch (the full Stage I build, the slice-validity feature, and today's DA bug fixes + §4.5 enforcement) fast-forward merged to `master` and pushed. Sequenced deliberately to avoid a schema/code ordering hazard: (1) both pending Supabase migrations (`20260815_kpi_slice_validity_fields.sql`, `20260816_kpi_not_sliceable_by_enforcement.sql`) applied to production via `supabase db push --linked` *before* the code push, confirmed via `migration list --linked`; (2) code pushed, triggering Railway + Cloudflare Pages auto-deploy; (3) `onboard_client.py --client apex_lubricants --env production` run to sync the `customer_rank` fix, confirmed matching via `verify_prod_registry.py`. User confirmed the live site (decision-studios.com) working post-deploy.

**Full-pipeline production regression test (2026-08-16): SA → DA → SF on `lubricants`/`gross_margin_pct`, against the real deployed Railway backend, not local dev.** SA: 6 real situation cards, Gross Margin % critical −14.46% YoY. DA: 10 dimensions, 59 change points, zero exclusions (lubricants has no flagged `not_sliceable_by` dimensions — expected, matches its known-clean status). SF: full three-persona debate + synthesis, **no degraded/stub fallback** — three options each with real causal grounding (citing the actual `base_oil_cost → cogs → gross_margin_pct` mechanism, not a generic template), moderator grades (`constraint_survival: pass`, `arithmetic_consistency: pass` on all three), a correctly-scoped impact estimate (segment-level recovery range, explicitly not claimed enterprise-wide), and `human_action_required: True, type: "approval"` — correctly parked at HITL rather than auto-approved. Confirms the entire pipeline — including all of today's changes — works end-to-end against production, not just local dev. Evidence: `tools/ab_harness/prod_sa_lubricants_result.json`, `prod_da_gross_margin_result.json`, `prod_sf_gross_margin_result.json`.

---

#### 🏁 Decision Quality — the outcome measure Stage I said must come first (built 2026-08-15, $0)

**This is an instrument, not a stage.** It follows the Stage H precedent: `src/analysis/`'s mechanism
fingerprint, groundedness scorer and problem profiler were built *during* a stage and recorded as
implementation notes, not given their own letters. `decision_quality.py` is the fifth module in that
same package. What it produces, however, authorises real build work — recorded as Stage J below.

**Why it exists.** Stage I's B-3 record closed with an explicit blocker: *"Optimising a proxy is not
optimising the objective… until 'better' has a referent, every additional arm refines a number nobody
should act on."* Divergence, lever stability and citation hygiene are all proxies. This supplies the
referent — **Decision Quality** (Stanford SDG): six requirements scored as a chain where the weakest
link governs. Chosen over MAP / Vroom-Yetton / KT-DA / AHP because it is a **standard, not a
procedure** — it grades the artefact and asks nothing of how a customer runs its meetings, which is
what keeps this a software purchase rather than a change-management engagement. Full rationale,
corpus limits and the pre-registered prediction: **`docs/architecture/decision_quality_rubric.md`**.

**Built:** `src/analysis/decision_quality.py`, `tools/ab_harness/dq_score.py`, 19 tests
(`tests/unit/test_decision_quality.py`). All 11 saved `scope_arm_*.json` arms scored retrospectively —
**33 options, no new API spend.**

| link | passes (11 arms) | |
|---|---|---|
| 1 frame *(advisory)* | **2/11** | caps the chain ×9 |
| 2 creative alternatives | 10/11 | |
| 3 reliable information | **11/11** | |
| 4 clear values & tradeoffs *(advisory)* | **0/11** | caps the chain ×11 |
| 5 sound reasoning | 10/11 | |
| 6 commitment to action | **11/11** | |

**No run holds the chain.** Prediction scorecard: 2 of 4 correct, recorded plainly in the rubric doc
because the value of a pre-registered prediction is entirely in being allowed to lose it.

**Three findings:**
1. 🔴 **Link 4 fails 11/11 and is a product defect, not a measurement artefact.** Every run carries the
   identical vector `impact=0.5, cost=0.25, risk=0.25` — the agent config default, reached via
   `request.evaluation_criteria or [defaults]` where **nothing anywhere populates
   `evaluation_criteria`**. Every ranking the product has ever produced used a system constant. It
   escaped notice because a presence check passes: the matrix *looks* complete and fully weighted. → **Stage J.**
2. **The moderator is structurally blind to every failing link.** Union of `moderator_grades` keys
   across all 11 arms is `constraint_survival` / `causal_grounding` / `arithmetic_consistency` /
   `critic_findings_response` — links 3 and 5, the two already at 11/11 and 10/11. Zero rubric
   coverage of frame, alternatives or values. → **Stage H follow-on** (below), alongside the still-open
   critic dual-duty risk-proposal item.
3. 🔴 **`persona_council_experiments.md` §7c's `0 of 27` structural options is wrong as stated.** Arm D1
   opt_2 ("Immediate SKU Rationalization") genuinely proposes discontinuing and delisting SKUs, and D1
   is one of the six frame-challenge *treatment* options counted as `0/6`; E2 opt_3 is a second
   instance. The null was adjudicated at category/portfolio-exit granularity without that criterion
   ever being written down. Direction survives (2 of 33 is still near the floor); the number should
   not be quoted again without a stated criterion. Correction written into that doc.

**Two instrument defects found and fixed *before* any number above was reported** — both caught by
adjudicating screen hits rather than trusting them (§5's 71%-FPR lesson applied to this instrument):
`unclassified` was being counted as a lever family (turning arm E2 into a confident PASS on link 2),
and `volume_for_margin` auto-passed link 1 by matching `full-potential` on an ordinary recovery plan.
Both regression-tested. Adjudications recorded as data in `dq_score.py`, not folded into the regex.

**Also landed:** `mechanism.LEVER_PATTERNS` gained `mix_shift` and `hedging` — the two most common
unclassified levers, appearing across both MBB and lens rosters. All 43 existing mechanism tests pass
unchanged. `mechanism.py` is imported only by tests and the harness, never by an agent, so this
changes measurement and not generation.

**🔴 The lens-swap comparison is not yet readable.** With the taxonomy extended, 3-of-3 distinct lever
families turns out **not** to be a lens property — MBB reached it in 5 of 6 pre-fix runs (A/A0/A0C/B/C),
and the lens arms (E1, E2) match that ceiling rather than exceeding it. Worse, **C1 — the sole control
the lens swap is measured against — is the single worst run in the corpus at 1/3**, against post-fix
MBB arms D1/D2 at 2/3. Two treatment runs versus one outlier control draw is
`feedback_one_observation_is_not_a_baseline` again, on the control side.

A second pattern wants testing rather than asserting: **every post-fix MBB run scores below every
pre-fix MBB run but one.** The `_build_kt_summary` unit fix landed in between, replacing an
undifferentiated `$-7 (0.0% of variance)` smear with correctly ranked pp values. It is possible that a
*correctly specified problem invites a narrower answer* — an uncomfortable result, since that fix was
unambiguously right. Equally consistent with noise at these sample sizes.

**Next action, and a sequencing note that matters:** replicate the control to **n ≥ 3 on the current
post-push build** (~$0.20/run). Do not compare new runs against the existing C1 — it predates both the
Stage I build and today's DA work. The harness replays a **frozen** DA payload (`scope_da_input.json`,
stamped 2026-08-11), so today's budget-comparator and §4.5 fixes do **not** confound it; the SF agent
itself is what drifted, and that is enough to require a fresh control.

#### Stage J — Enterprise evaluation criteria ✅ BUILT 2026-08-16

| Stage | Work | Owner | Status |
|---|---|---|---|
| **J** | Populate `evaluation_criteria` from the **enterprise's** declared strategy so `_rank_options` stops using `A9_Solution_Finder_Agent_Config.weight_*`. Two fields on `A9_PS_BusinessContext`: `strategic_posture` (the justification) + `tradeoff_weights` (the operative numbers). Closes DQ link 4 | Phase 15 | ✅ **BUILT** — 27 tests (`test_sf_stage_j_tradeoff_weights.py`), 1202 suite pass. **No migration** — both fields ride the existing `business_contexts.metadata` JSONB |

**🔴 Naming corrected — `tradeoff_weights`, NOT `lens_weights`. The name was already taken.**
`principal_perspective_weighting_design.md` defines `perspective_weights` as
`{"plan": 1.0, "trend": 0.6, "peer": 0.3, "value_gap": 0.8, "bridge": 0.9}` — weights over the **five
comparison Perspectives** (L1 vs Plan · L2 vs Trend · L3 vs Peer · L4 vs Full potential · L5 Bridge), an
SA/DA concept governing how a KPI situation is *appraised and prioritised*. That is a different
feature, still unbuilt, and **the earlier claim in this entry that "the design already exists, only the
wiring is missing" was wrong.** Three things were called "lens" at once: those comparison lenses,
`PerspectiveAnalysis.lens` (`"Financial"`/`"Operational"`/`"Strategic"` argument sets on each option),
and this. Renamed to match what it actually feeds — `tradeoff_weights` → `TradeOffCriterion` →
`TradeOffMatrix`.

> ✅ **The other two were settled 2026-08-16 (owner decision), so all three now have distinct names:**
> the appraisal concept is a **Perspective** (`perspective_weights`, `PrincipalPerspectiveProfile`,
> doc renamed to `principal_perspective_weighting_design.md`), and the council concept keeps **lens**
> (`PerspectiveAnalysis` → `LensView`, `SolutionOption.perspectives` → `lens_views`, UI heading
> "Stakeholder Perspectives" → "Council Lenses"). Mnemonic: a **lens** is who is looking; a
> **Perspective** is what they compare against. Read paths accept the legacy `perspectives` key —
> briefing snapshots persisted to Supabase and localStorage predate the rename — via
> `AliasChoices` on the model and an explicit fallback in `briefingUtils`, `TradeOffAnalysis` and
> `decision_quality._option_blob` (that last one matters because the scorer is run against archived
> payloads, where dropping the old key would silently shrink the text blob for every historical run).
> This was cheap only because the Perspective half had no implementation — the collision was caught
> while one side was still paper. `organization_priorities` was considered and rejected: `A9_PS_BusinessContext`
already carries `strategic_priorities`, so it would have collided with a field on the same model, and
it overclaims — these three numbers break ties between options that all already address the problem,
which is a tiebreaker, not a priority.

**And the M1 argument below applies to option ranking ONLY, not to the comparison lenses.**
Lens weighting changes *which situations reach whom and how they are framed* — different questions,
which is correct and M1-compliant (a COO should not be paged about multi-year portfolio positioning).
Tradeoff weighting changes *which answer wins for the same question*. Per-principal is right for the
first and forbidden for the second. The original design was not wrong to be per-principal; it was
designing appraisal, and appraisal is personal.

**Pre-existing dead duplicate, found during the rename:** `A9_PS_Criterion` /
`A9_PS_DecisionCriteria` in `a9_debate_protocol_models.py` already model exactly this
(name/weight criteria over impact/cost/time_to_value/risk, plus `risk_tolerance`). **Zero references
anywhere outside their own definition** — CaaS debate-protocol scaffolding that was never wired. Left
in place, but note its `_validate_weights` requires weights to sum to 1.0 ±0.01, whereas
`_rank_options` does no normalisation at all. Two contradictory assumptions about the same concept
have been sitting in this codebase; **Stage J follows `_rank_options` (relative, unnormalised)** and
that is now stated in the model docstring. Retiring the dead pair is a cleanup candidate.

**🔴 Design corrected mid-build, on the user's challenge — weights are ENTERPRISE, not PRINCIPAL.**
The first cut followed `principal_perspective_weighting_design.md` and hung the field off
`PrincipalProfile`. The user pushed back before it went further: *a cash cow, an M&A mover and a
growth-stage business each have optimal weights that follow from corporate strategy and should impact
every decision the same.* Correct, and the codebase already said so — **the M1 invariant written into
the synthesis prompt** (`a9_solution_finder_agent.py`) states that *role adaptation controls entry
point and depth only; the conclusion is identical for every role.* Ranking weights change the
conclusion, so per-principal weights violate M1.

**Measured before deciding** (`_rank_options` replayed over the 11 saved arms under CEO/COO/CFO
profiles): **4 of 11 arms flip their recommended option.** But the flips land at margins of
**+0.0035 to +0.045**, and arm B0's default profile is an **exact 0.0000 tie** decided by list order.
Stable arms sit at +0.13. The scalars being weighted are LLM estimates in 0.05 increments on a process
already known stochastic on identical input — so weights only decide the outcome when the options were
near-equivalent anyway. Decision-analysis practice agrees with the user's instinct: corporate value
models are organizational, elicited once for the firm, not per executive.

**Built:**
- `TradeoffWeights` + `strategic_posture` on `A9_PS_BusinessContext` (`a9_debate_protocol_models.py`).
  `tradeoff_weights` is nullable with **no default_factory** — `None` means never configured and must stay
  visible; a default would manufacture consent, making "nobody chose this" indistinguishable from
  "this client chose the house numbers". Same reason the resolver returns `None` rather than the
  default vector.
- `strategic_posture` carries the *justification* — "margin defense", "growth capture",
  "cash preservation", "integration", "turnaround". Three bare numbers cannot be confirmed or argued
  with by a customer; a posture can. This makes link 4 *reasoned*, not merely explicit.
- Provider round-trip through `business_contexts.metadata` JSONB, both directions — **no migration
  needed**; the column and the explicit field-mapping pattern already exist.
- `_tradeoff_weights_to_criteria()` in the SF agent, resolving from the business context SF **already
  loads** for synthesis — no duplicate fetch, and it works for every caller rather than only the API
  route. An earlier cut put this in `workflows.py` with its own principal fetch; removed.
- **`tradeoff_weights` withheld from the LLM prompt** (`_business_context_for_prompt`) — the model
  writes each option's `expected_impact`/`cost`/`risk` scalars and `_rank_options` then weights exactly
  those three numbers. If the model can read the weighting it is about to be scored under, it can tilt
  the scalars toward it and the ranker applies the same weighting a second time to already-tilted
  input — invisible from outside, since nothing errors and the numbers merely lean.
  `strategic_posture` deliberately **stays** in the prompt: text drives generation, numbers drive
  selection, only the numbers are withheld. Per §7b's lesson all three channels carrying the value were
  enumerated before closing one — the `business_context` field on `A9_LLM_AnalysisRequest`/
  `A9_LLM_Request` never reaches prompt text (no provider in `src/llm_services/` reads it), and the
  `llm_debate_analysis_req` audit event keeps the full context on purpose, because that is provenance,
  not input.
- `TradeOffMatrix.criteria_source` (`request` / `business_context` / `config_default`) — provenance is
  now **recorded, not inferred**. The DQ link-4 check reads it and falls back to the old value
  comparison only for payloads predating the field, so the §8 baseline stays reproducible.

**Deliberately not done:** no weights seeded for any client. They are preferences, and inventing them
would reintroduce the exact defect this closes — a weighting nobody chose, now wearing the customer's
name. **Every client is `NULL` until someone sets one, so this is a no-op until configured.** There is
also no UI: Registry Explorer form editing is still on the pre-video polish list, so today the routes
are the seed file, the registry API, or SQL.

**🏁 LIVE VERIFICATION (2026-08-16) — Stage J confirmed working end to end; posture effect NOT
established, and the design cannot establish it.** Two arms, lubricants, frozen DA payload, arm-C
config, varying ONLY `business_contexts.metadata`. ~$0.45, 277s and 298s.

| arm | `criteria_source` | criteria | levers generated | winner |
|---|---|---|---|---|
| **P0** control (posture nulled) | `config_default` | 0.5 / 0.25 / 0.25 | mix_shift, pricing_corridor ×2 | SKU Rationalization (risk 0.30) |
| **P1** posture set | **`business_context`** | **0.4 / 0.2 / 0.4** | indexation ×2, pricing_corridor | Base-Oil Indexed Renewal (risk 0.30) |

**What is established:** the enterprise posture reaches `_rank_options` on the live path, provenance is
recorded correctly, no stub, `causal_context` confirms max_hops=2 / 6 edges / 1 constraint / 4 market
signals. **DQ link 4 would now pass for lubricants — the first time it has for any client.**

**What is NOT established, exactly as predicted before the runs:** whether `strategic_posture` in the
prompt changes *generation*. The lever families differ between arms — but arm C1 on an earlier build,
with **no posture**, produced `indexation ×3`, so "no posture" has already produced both outcomes. The
difference sits inside documented run-to-run variance (PM-2: `arithmetic_flags` 0→3→0→1 on identical
input), and both arms produced 2 distinct lever families and a winner at risk 0.30. **n=1 versus n=1
cannot separate a posture effect from stochastic variation**, and this was recorded as the prediction
before either arm ran.

**Structural finding — ranking weights are blind on most runs.** P1 produced a **dominated** option
set: opt_1 beat both alternatives on impact, cost *and* risk simultaneously, so no weighting could
change its winner. That matches the free replay across the 11 saved arms, where the lubricants posture
changed the recommendation in **1 of 11** — and only on arm B0, the exact 0.0000 tie. Weights act in a
narrow band: genuine close calls. Correct behaviour for a tiebreaker, and the reason the effect is
small rather than the chaos a per-principal design would have implied.

**🔴 Decision: do NOT run the `risk_posture` overlap arms (P2/P3).** A contradiction between
`risk_posture` text and a numeric risk weight can only surface in output if the posture text moves
generation — which is unestablished and would need n≥3 per arm minimum to test against this variance,
for a question that is answerable by design. **Settle it with a configuration-time consistency check
instead:** the two fields do genuinely different jobs (`risk_posture` is prose that shapes what gets
*proposed*; the risk weight is arithmetic that breaks ties among *proposals*), so collapsing them by
derivation would merge two different stages. Flag the contradiction where it is authored — warn when
`risk_posture: "high"` pairs with risk as the largest weight, or `"low"` with the smallest — and do
not block. This supersedes the earlier "derive — one authored source per concept" lean.

**Two pre-existing bugs found by actually running this, both fixed:** `onboard_client.py` opened
`.env` with the platform default encoding, so every run on Windows died with `UnicodeDecodeError`
before reaching Supabase; and `scope_arm.py` named output by arm letter alone, so two runs of one arm
varying only the database would silently overwrite each other — it now takes a label and refuses to
clobber an existing payload. **Also found, not fixed:** `_find_active_client_id` in
`company_profile.py` excludes `lubricants` and `bicycle` as demo clients, so the company-profile API
**cannot** set posture for them; the row had to be written directly. That surface works only for a
non-demo tenant.

**Method note — the check that saved the experiment.** Before restarting, `/api/v1/company-profile`
did not expose the new fields while a fresh Python process reading the same database did: the backend
was running stale code. Arms run at that moment would have exercised the old build and returned a
confident false negative. Verified per `feedback_verify_config_reaches_the_live_call_path` *before*
spending, not after.

**🔴 Separate defect found while measuring this, NOT fixed — `_rank_options` has no tie band.**
Arm B0's top two options score **identically to four decimal places** (0.035 vs 0.035) under the
default weighting, and the agent presents a confident `recommendation` anyway, chosen by list order.
This predates Stage J entirely and is independent of it. The honest output when the top-two margin is
below some threshold is "these are equivalent under this weighting", not a winner. Needs a threshold
nobody has an empirical basis for yet — so it is recorded rather than guessed at.

**Also still open:** the weighting is not surfaced anywhere a reader sees it. "Ranked for a
margin-defense posture: impact 0.4 / cost 0.3 / risk 0.3" turns a ranking into something checkable;
without it, three numbers decide the recommendation invisibly. Belongs with Stage G's briefing UI.

**Stage H follow-on (added 2026-08-15):** extend the moderator rubric to the links it currently cannot
see — frame and creative alternatives — **or** conclude they are not gradeable at synthesis time and
handle them upstream. Do not tune the four existing rubric items; they grade what already passes.
Joins the still-open critic dual-duty risk-proposal item on Stage H's follow-on list.

**🔴 Scope finding — framing is outside Phase 15 as this phase is defined.** Link 1 fails 9 of 11 and
is the chain's first link, but the frame is not set in Solution Finder at all: it is fixed upstream
when SA emits a situation card named after one breached KPI, and every persona downstream inherits
"recover this KPI" as an axiom. This is why **both** prior experiments returned nulls — the roster swap
varied who was in the council, the frame-challenge flag varied the task wording, and both varied things
*inside* a frame decided three stages earlier. Phase 15's stated goal is recommendations that are
grounded, honest about their bets, and calibrated on known-vs-inferred: all three concern the quality
of the answer to a given question, none concerns whether the right question was asked. **Phase 15 can
therefore complete successfully with link 1 still failing.** Needs its own phase or a home in whatever
owns situation-card semantics — flagged as the strongest candidate for what follows Phase 15, not as
work to squeeze into it.

**Still required before any frame conclusion is load-bearing:** a second problem shape. All 33 options
are one KPI on one DA result, so "frame fails 9 of 11" stays consistent with *this problem has one
right frame*.

---

## 🏁 PHASE 15 CLOSED (2026-08-16)

**Closed on an objective criterion rather than a judgment call.** Phase 15's goal was recommendations
an executive will act on — *grounded in a verified cause, honest about what they bet on, calibrated on
known vs inferred*. Measured against the Decision Quality chain across 13 runs / 39 options
(`decision_quality_rubric.md` §8–10):

| link | state at close |
|---|---|
| 2 creative alternatives | 12/13 |
| 3 reliable information | **13/13** |
| 4 clear values & tradeoffs | passes **whenever a client is configured** (Stage J) |
| 5 sound reasoning | 12/13 |
| 6 commitment to action | **13/13** |
| **1 appropriate frame** | 2/13 — **out of scope**, see below |

**Everything Phase 15 controls, passes.** Link 1 fails because the frame is authored in DA's SCQA
before any council runs — outside this phase by its own goal statement, which concerns the quality of
the answer to a given question and never whether the right question was asked. Holding Phase 15 open
for it would mean holding it open for work it structurally cannot do. → **Phase 19.**

### Final stage status

| Stage | State |
|---|---|
| A structured output | ✅ built; **flag still `false`** — see settlement 2 |
| B unified schema | ✅ |
| C context contract | ✅ |
| D grounding + constraints | ✅ live (`enable_causal_grounding=true`; migration **is** applied — the old "not applied" note was stale and is corrected below) |
| E critic pass | ✅ live |
| F bets → VA | ✅ core wiring |
| **G briefing UI** | ❌ at close: not built → returned to Phase 13 (settlement 1). **Subsequently built there, 2026-08-16** — see Phase 13 Cat 3 |
| H moderator | ✅ live, adopted on scope elicitation (27/27 vs 0/12) |
| I persona framing | closed at B-2; lens-swap comparison **unreadable** pending control replication |
| **J tradeoff weights** | ✅ built + live-verified; first link-4 pass on record |

### Three settlements

**1. Stage G returns to Phase 13, where it started.** Stage G was always *"Phase 13 Cat 3 + Cat 4 +
Phase 15"*. Cat 4 shipped inside Stage C; Cat 2 shipped inside Stages A–B. What remains of Stage G is
exactly **Phase 13 Cat 3 — the briefing UI**. Returning it removes a duplicate entry rather than
creating a new phase, and reconciles two entries that were describing the same unbuilt UI from
opposite directions.

**2. `use_structured_output`: decision recorded, flip handed off.** The call was deferred *"until
Stage I closes"*; Stage I has closed. The standing recommendation from the A/B stands — **adopt, on
failure-mode removal rather than measured gain** (the control arm scored perfectly on every
conformance measure, so a tie was the best available outcome), and **delete the prose path** per PM-2
rather than carrying two. The flag is deliberately **not flipped as part of a documentation close**:
it changes live LLM behaviour and deserves its own commit and verification run.

**3. Stage D's "migration still not applied" note was stale** — `20260723_theory_layer_causal_schema.sql`
exists, `enable_causal_grounding` is live, and arm P1 reported 6 edges / 1 constraint resolved from
the register. Corrected in the stage table above.

### Loose ends, handed off explicitly rather than carried

| item | goes to |
|---|---|
| Briefing UI (ex-Stage G) | **Phase 13 Cat 3** — ✅ built there 2026-08-16 |
| `use_structured_output` flip + prose-path deletion | follow-on commit, recommendation above |
| Critic dual-duty risk proposal | Stage H follow-on list |
| Moderator rubric coverage for links 1 + 2 | decide-or-drop; blocked on Phase 19 |
| `_rank_options` has no tie band | **plain bug** — a 0.0000 top-two tie is presented as a confident recommendation |
| `risk_posture` ↔ risk-weight consistency check | config-time warning, decided not built |
| No UI surfaces the tradeoff weighting to a reader | **Phase 18** (console work) |
| Control replication to n≥3 on the current build | unblocks the Stage I lens read |
| Frame | **Phase 19** |

### Bookkeeping defect found at close, NOT renumbered

🔴 **Two phases share the number 10D** — *Solution Finder Performance Tuning* (✅ Apr 2026) and *MCP
Abstraction Layer* (open). **Deliberately not renumbered:** "Phase 10D" appears across ~15 files
including four dedicated `PHASE_10D_*.md` documents, `data_connectivity_strategy.md`, three agent
PRDs and four strategy docs, referring to **both** phases. A renumber would silently invalidate more
cross-references than it fixes. Both headers now carry a disambiguation note instead.

---

### Phase 16: Data Product Contract Consolidation — finish the YAML → registry migration

> **Numbering note:** Phase 15 is the LLM-trust spine; Phase 14+ remains the reserved unscheduled Future bucket. This takes the next free number, 16.

**Goal:** one place where a data product's contract lives. Today it lives in two, with the same key name holding different shapes in each, and three agents reading whichever they happen to reach.

**Why this is a phase and not a chore.** Every number defect fixed in Phase 15 had the same root: a fact that existed in two places, or in none. The two-baseline briefing (FY-2025 headline vs YTD-2025 segments), the COGS attributed to one customer, the KPI whose sign was assumed rather than declared. A split contract store is that failure mode institutionalised — and it is *already* producing wrong output in a seeded client (see the Hess findings below).

---

#### The finding (audited 2026-08-10)

An attempt was made to move contract definitions into the Supabase registry and retire the YAML. **The migration is incomplete, so the YAML keeps resurfacing.** Six contract sections were never moved. Measured against `hess_financials.yaml`:

| section | Hess | lives in |
|---|---|---|
| `views[].llm_profile.dimension_semantics` | 10 entries | **YAML only** — and this is what Deep Analysis analyses by |
| `fallback_group_by_dimensions` | 3 | YAML only |
| `business_terms` | 7 | YAML only |
| `column_aliases` | 4 | YAML only |
| `supported_business_processes` | — | YAML only |
| `connection` | — | YAML only |

**`views` exists in BOTH stores under the same key with different shapes** — YAML holds `[{llm_profile, sql}]`, the registry record holds `{columns}`. Same name, different content. A naive merge is ambiguous, not merely incomplete, which is probably why the migration stalled here.

**12 contract YAML files remain on disk** at `src/registry_references/data_product_registry/data_products/`, including `hess_financials.yaml`, `lubricants_snowflake.yaml`, `lubricants_sqlserver.yaml`.

**Live reads, by agent:**

| agent | `yaml.safe_load` calls | status |
|---|---|---|
| `a9_deep_analysis_agent` | 3 | **LIVE** — `_dims_from_contract`; a real run logged `dims_from_contract=15` |
| `a9_data_product_agent` | 8 | 1 live, rest target absent files |
| `a9_data_governance_agent` | 3 | 1 live, rest target absent files |

This violates the standing rule in `CLAUDE.md` ("NEVER use `yaml.safe_load()` in agent files to load KPIs, principals, data products, or business processes"). The dead reads — `data_product_registry.yaml`, `consulting_personas_registry.yaml` — point at files that no longer exist; harmless, but they make the live ones harder to spot.

**Deleting the YAML today would break dimension selection for every client** and drop DA back to the bicycle `fi_star_schema.yaml` default — the cross-tenant contamination fixed in Jul 2026 (`_lookup_kpi_scoped`). The files cannot simply be removed; the content has to move first.

---

#### What triggered the audit: Hess KPI definitions are wrong (validated live 2026-08-10)

Manual validation of Apex (Snowflake) and Hess (SQL Server), one KPI each, executing generated SQL against the real databases.

**Apex — passes.** Connects via key-pair auth (password auth is blocked by account MFA). Generated SQL executes; equal-duration windows confirmed: `fiscal_year = 2026 AND fiscal_period <= 8` → **32.55%**, prior year → **37.03%**.

**Hess — SQL plumbing correct, KPI definitions wrong.** Time filtering, dialect quoting and the equal-duration comparison all behave. The seeded formulas do not:

| KPI | reported | actual |
|---|---|---|
| `gross_margin_pct` | 165.57% | **34.43%** |
| `gross_profit` | 6,236M | **1,297M** (4.8×) |
| `operating_income` | 6,816M | **717M** (9.5×) |
| `return_on_capital` | 301.63% | — |
| `lifting_cost`, `exploration_expense`, `capital_expenditure`, `operating_cash_flow`, `free_cash_flow` | **NULL** | reference `CapEx` / `OperatingCF`, which do not exist in the data |

COGS, SGA and Other are stored **negative** in `HessStarSchemaView` (as in BigQuery and Snowflake). Three KPIs negate them again (`WHEN 'COGS' THEN -[amount]`, `ELSE -[amount]`), which **adds** cost to revenue.

**The magnitude is not the worst property — the direction is.** Reported gross margin *rose* +2.66pp year-on-year while the true margin *fell* 2.66pp. Situation Awareness would see improvement and raise no alert on a declining business. A margin above 100% would eventually be spotted by eye; an inverted trend would not.

Roughly a third of Hess's KPI set is unusable: 3 wrong, 5 NULL, 1 impossible. **Not yet fixed** — deliberately, because the fix belongs in the contract, not in six hand-edited f-strings in `scripts/clients/hess.py`.

---

#### Design: `measure_semantics` on the data product

Sign convention is a **fact about the data**, so it is declared once on the data product record — a sibling of `time_dimensions`, which already works exactly this way:

```python
"measure_semantics": {
    "type_column": "account_type",
    "amount_column": "amount",
    "stored_sign": {"Revenue": "positive", "COGS": "negative",
                    "SGA": "negative", "Other": "negative"},
}
```

Properties this must have, and the reasons:
- **In the contract**, not embedded in each KPI's SQL string — otherwise every new KPI re-derives the convention and can get it wrong privately.
- **Not client-specific** — a field on the shared `DataProduct` model, so BigQuery, Snowflake and SQL Server all read one declaration.
- **Enforced, not documented** — a validator that fails any KPI whose SQL negates a measure the contract states is already negative. That is what would have caught Hess automatically instead of by hand, and it catches the next client without anyone remembering to look.

This is the same idea as the parked **KPI Semantic Contract** (`additive_across_dimensions`, `unit_class`, `sign_convention`, `scope_eligible`) — the registry states what a number means; consumers reference rather than re-derive. They should land together.

---

#### Onboarding scope: the wizard cannot express a working contract (audited 2026-08-10)

This is not only a migration. **The onboarding workflow does not collect the contract facts the analysis pipeline requires**, which is why every existing client was seeded through `scripts/clients/*.py` rather than through the wizard, and why the YAML keeps coming back.

**What `_build_contract_dict` emits** (`a9_data_product_agent.py`), the whole of it:

```
metadata {id, name, domain}
tables   [{name, columns[{name, data_type, semantic_tags}]}]
views    []            <-- always empty
kpis     [...]
```

**What it never emits, and what breaks without each:**

| missing | consequence |
|---|---|
| `time_dimensions` | DPA falls back to `{"type": "date", "column": "transaction_date"}`. **Three of four seeded clients use `fiscal_year_period`** — a wizard-onboarded fiscal dataset gets the wrong filter shape and silently returns wrong windows |
| `views[].llm_profile.dimension_semantics` | `_dims_from_contract` returns `[]`, so Deep Analysis has no dimensions to analyse and falls back to the KPI registry — or, historically, to the bicycle default contract |
| `measure_semantics` (proposed) | KPI SQL is hand-written per client with the sign convention assumed. This is exactly how Hess's three KPIs came to add cost to revenue |

Counts across the onboarding models and routes: `dimension_semantic` 0, `sign_convention` 0, `measure_semantic` 0, `account_type` 0, `fiscal` 0, `time_dimension` 1.

**The wizard's 5 steps** (Connection → Schema Discovery → Data Product Selection → Metadata Analysis → KPI Definition) collect schema and KPIs, and nothing about how time or measures behave. Those are not schema facts — no column type reveals that `amount` is negative for COGS, or that `fiscal_period` is a period rather than a date.

**Consequence to state plainly:** a data product onboarded through the current wizard produces contracts that are *structurally incomplete for the pipeline they feed*. It looks successful — the steps pass, the product registers — and the failure appears later as an empty Is/Is-Not, a wrong comparison window, or an inverted KPI. Every failure mode found this week, arriving by the front door.

**`contract_yaml` is a carrier, not a file.** `generate_contract_yaml` explicitly does not persist to disk ("Supabase is the canonical registry backend"), so the wizard is not writing the 12 files found on disk. But it serialises to YAML text and passes `contract_yaml: str` between steps, which keeps the YAML shape as the wizard's working model and makes the registry record a lossy projection of it.

##### Onboarding work implied by this phase

| # | Work | Note |
|---|---|---|
| **O1** | Emit `time_dimensions` from the wizard — detected where possible, confirmed by the user | Detection is a reasonable default (a `fiscal_year` + `fiscal_period` column pair is a strong signal), but it must be **confirmed**, not assumed; the cost of getting it wrong is silent wrong windows |
| **O2** | Collect `measure_semantics` — the sign of each measure/account type | Detectable by inspection: if every COGS row is negative, propose "negative" and ask. One question, once, replacing a per-KPI assumption |
| **O3** | Emit `dimension_semantics` / `fallback_group_by_dimensions` | The candidate analysis dimensions. Related to Phase 15 Stage I's problem-profile-driven selection — the wizard should propose, the profile should rank |
| **O4** | Replace `contract_yaml: str` with the typed contract object | Removes the last reason for the wizard to think in YAML at all |
| **O5** | Completeness gate before "register" | Refuse to register a data product missing time semantics or measure semantics. **The onboarding wizard is where a bad contract is cheapest to stop**; every other guard in this plan catches it downstream, after it has already produced a number |
| **O6** | Re-onboard one existing client through the fixed wizard | The only real proof. If lubricants cannot be reproduced through the UI, the wizard still cannot express a working contract |

**Ordering:** O1–O3 depend on the registry record gaining those fields (Phase 16 steps 1–2), so the wizard has somewhere to write them. O5 depends on O1–O3 existing to check. O6 is the acceptance test for the whole phase.

**Relationship to the existing Data Onboarding Refinement track** (below): that track is UI and workflow polish — chooser screen, wizard foundation, templates. This is a *content* gap in what the wizard produces, and it should be sequenced ahead of the polish. A better-looking wizard that still emits an incomplete contract is a faster way to a wrong briefing.

**Reframes the "1-day onboarding" claim.** The wizard completing is not the same as a usable data product. Until O5 exists, "onboarded" means the steps passed — not that the pipeline can analyse it correctly.

---

#### Sequence (order matters)

| # | Work | Why in this order |
|---|---|---|
| **1** | Move `dimension_semantics` + `fallback_group_by_dimensions` onto the registry record; repoint `_dims_from_contract` | The only live contract read. Also the fix for the **hardcoded dimension preference list** in Phase 15 Stage I — same change, two problems |
| **2** | Add `measure_semantics` + the negation validator | Sign convention and dimensions then come from one place |
| **3** | Correct the Hess KPIs against the declared convention; re-validate live | Fixes real wrong output, now expressed as data rather than code |
| **4** | Move `business_terms`, `column_aliases`, `supported_business_processes`, `connection` | The remaining sections; lower risk once the pattern exists |
| **5** | Resolve the `views` shape collision, delete the 12 YAML files and all `yaml.safe_load` calls in agent files | Only safe once nothing reads them |
| **6** | Architecture test: no `yaml.safe_load` in `src/agents/**` | Makes the rule in CLAUDE.md enforceable rather than aspirational |

**Onboarding (O1–O6 above) interleaves here:** O1–O3 land with steps 1–2, since the wizard needs somewhere to write those fields; O5's completeness gate lands with step 4; O6 — re-onboarding an existing client through the wizard — is the acceptance test for the phase.

**Do NOT do 2 before 1.** Adding `measure_semantics` to the registry while dimensions still come from disk leaves DA reading two halves of one contract from two stores — the exact shape that produced the two-baseline briefing.

**Verification for each step:** a live Deep Analysis per client per backend, checked against a direct query. Today gave three separate cases where code was correct and was not the code being executed; string tests do not close that.

---

#### Open questions

- **Hess is not a validated dataset** (established 2026-08-10). `HessStarSchemaView` is a *partially relabelled lubricants dataset*, living in the `agent9_lubricants` database alongside `LubricantsStarSchemaView`. Two dimensions were genuinely converted — `segment_name` (E&P, Midstream) and `basin_name` (Bakken, Gulf of Mexico, Guyana, Southeast Asia) are real Hess geography. The rest were not: `asset_name` holds **Automatic Transmission Fluid, Compressor Oil, Conventional Engine Oil**; `business_unit` holds **Retail Products, Service Centers**; `country` and `region` hold identical region values. An E&P asset is a field or a platform, not a motor oil.

  The five NULL KPIs — `lifting_cost`, `exploration_expense`, `capital_expenditure`, `operating_cash_flow`, `free_cash_flow` — are **correctly defined for an E&P company** and return nothing because the data is a lubricants P&L (`account_category` = Base Oil & Additives, Packaging, Distribution…). They are not the problem; they are the symptom.

  **The KPIs that DO return numbers are the greater risk.** `upstream_revenue` = 3,766,365,690 is simply `SUM(Revenue)` over lubricants data, presented under an oil & gas name. NULL is visibly broken; a plausible wrong number is not.

  **SCOPING DECISION (2026-08-10): data realism is explicitly NOT in scope for Apex or Hess.** They exist to demonstrate that Agent9 works technically against Snowflake and SQL Server, and for that purpose the underlying data does not need to be a faithful E&P or distributor P&L. Both remain useful as backend-connectivity proof. This closes the "generate real E&P data" option below unless the positioning changes.

  **What still matters under that framing, and why it is narrower than it looks:**
  - **The sign error is still worth fixing** — not for realism, but because it produces a *visibly impossible* number. A demo intended to prove "Agent9 runs on SQL Server" is undermined by a gross margin of 165.57%, and by a KPI whose direction is inverted. A technical proof still has to produce plausible output. It is also fixed *generically* by Phase 16 step 2 (`measure_semantics` + the negation validator), so it costs nothing extra once that lands.
  - **The five NULL KPIs can stay or go** — they weaken nothing technically. Removing them is tidier; leaving them is honest about the dataset being partial. Low priority either way.
  - **The relabelling does not matter** — `asset_name` holding motor oils is irrelevant to a connectivity demo.
  - **The one real constraint:** neither client should be presented as an industry case study, and no briefing from them should be shown as a customer example. `upstream_revenue` is lubricants revenue under an oil & gas name — fine as plumbing, misleading as a narrative.

  Options retained for the record, should positioning change:
  1. **Generate real Hess E&P data** — E&P account categories (lifting, exploration, capex, operating CF) and real assets. Makes all sixteen KPIs meaningful and gives a genuinely different second industry.
  2. **Accept Hess as a dimensional demo** — remove the KPIs the data cannot support, and rename the rest so they do not claim to be upstream figures.

  Doing neither leaves a seeded client whose working KPIs describe the wrong business.
- **Apex's remaining KPIs** — only `gross_margin_pct` was validated there. The same sign audit should run across its full set before anyone reads an Apex briefing.
- **Does any client legitimately store expenses positive?** The design assumes a per-data-product declaration precisely so the answer can differ; worth confirming none currently does, so the validator's default is the safe one.

---

### Phase 17: Theory Layer Visualization — the Value Driver Tree as a causal object

**The deliverable is one exhibit with four sections:**

| # | Section | Content |
|---|---|---|
| 1 | **Core Spine** | DuPont-style financial layout — the arithmetic skeleton |
| 2 | **External Ports** | Where outside forces enter: commodities, interest rates |
| 3 | **Causal Edges** | Cross-branch links *active in this situation* |
| 4 | **Assumptions** | Markers showing which theories are holding or breaking |

**Framing, from `theory_layer_design.md` §2.4:** *"Every driver tree bottoms out in accounting atoms; causality keeps going. This is the known limitation of the Value Driver Tree as an arithmetic skeleton — the theory layer is what annotates it into a causal object."* The spine is the skeleton; sections 2–4 are the annotation. That is the whole point of the exhibit, and it is why a spine-only version is not a partial delivery of it.

---

#### Readiness, audited 2026-08-10 — two of four are data models that do not exist

| Section | Needs | State |
|---|---|---|
| **Causal Edges** | `KPIRelationship` | **Mechanism READY.** Already carries `mechanism`, `lag_periods`, `conflict_direction`, `relationship_type`, and `causal_rung` — Pearl's ladder: `correlational` \| `intervention_hypothesized` \| `intervention_tested`. That field alone gives the confirmed-vs-assumed encoding. **Gated on content density, not build.** |
| **Assumptions** | a graded outcome per assumption | **HALF built.** `SolutionAssumption` carries `validated_by`, `grounded`, `confidence`, `provenance` — *what was assumed*. There is **no** graded/outcome/verdict field anywhere in `src/`. "Holding or breaking" is unrenderable today. |
| **Core Spine** | KPI arithmetic decomposition | **NOT built.** No `parent_kpi` / `contributes_to` / driver-tree model exists. `kpi_relationships` is peer-to-peer *causal* linkage, not arithmetic parentage — a DuPont spine needs Revenue → Gross Profit → Operating Income → ROIC as a tree. |
| **External Ports** | a structured port model | **NOT built.** Market signals exist as *prose* from the MA agent. `theory_layer_design.md` §2.3 enumerates the ports — input costs, demand volume, price realization, capital cost, talent supply, regulatory constraint — each with a characteristic **lag** and **buffer**. None of that is modelled. |

**So "when do we add the visualization" is mostly the wrong question.** Rendering is the last stretch; the spine and the ports are the work.

---

#### Dependency chain (shortest path first)

| # | Prerequisite | Why it must precede the exhibit |
|---|---|---|
| **T1** | **Phase 16 step 2** — `measure_semantics`, `additive_across_dimensions` | Without it the spine can silently mis-add. That is the −53pp header bug rendered as a tree, and **a wrong number in a diagram is harder to challenge than one in a table** — the picture carries authority the arithmetic has not earned. Hard prerequisite. |
| **T2** | **KPI decomposition model** — arithmetic parentage | New. Useful well beyond this exhibit: it is also what would let impact claims roll up correctly, and what a `scope_eligible` check would lean on. |
| **T3** | **Assumption grading (step 2)** — the write-back that marks an assumption held or broken | The holding/breaking marker *is* section 4. Without it that panel is a list, not a verdict. Already designed and gated on VA outcome data (see the assumption-grading notes). |
| **T4** | **Port model** — external drivers with lag and buffer | Conceptually the smallest of the four, but nothing exists. Turns MA prose into structured entries the exhibit can attach to a branch. |

**Density gate for section 3:** a causal map with one confirmed edge and three template priors does not demonstrate a theory layer — it advertises that there is not one yet. Suggested bar: **confirmed (`intervention_tested`) edges outnumber template/unconfirmed ones for that client.** Lubricants currently has ≈1 confirmed edge. Reach the bar through the accretion paths already designed (SA HITL comment mining, SF rejections, VA verdicts) rather than by building the viewer and hoping it fills.

---

#### Delivery rule

**Do not ship a partial four-panel layout.** Three empty panels beside one populated one reads as a product that does not work — worse than not showing the exhibit at all. Either all four sections carry content for the client being demonstrated, or the exhibit stays off.

This is a real risk with this particular feature: **it demos beautifully and gates poorly.** The pull to build the spine early — because a DuPont tree is easy and looks impressive — is exactly what would produce an empty causal map in front of someone.

---

#### Interim, available now and honest

**Provenance styling on the exhibits that already exist.** `causal_rung` and the confirmed/template distinction are already reaching briefings as text — a live production briefing carried *"causal: gross_margin_pct ↔ COGS (confirmed provenance, high confidence)"* alongside *"premium_mix_pct → gross_margin_pct (template provenance, moderate confidence)"*, and the risk register flagged that the unconfirmed template edge drove 30–50% of every option's projected recovery.

That distinction — **what we know versus what we assumed** — is the differentiating idea, and it needs neither the spine, the ports, nor the grading. Making it visual on the moderator verdicts and the assumptions panel is cheap, ships now, and does not promise a causal map that is not populated.

---

#### What a MATURE decomposition model does for Solution Finding

The decomposition model is filed under Phase 17 because the VDT needs it, but its larger value is to SF. A tree that accretes lags, elasticities and realisation rates from actual use changes what SF can do:

1. **Impact stops being asserted and becomes computed.** Today a `recovery_range` is a guess sized against the observed decline — the A/B measured the shape of it: **the LOW bound was identical (18.5) across every option in 11 of 18 runs**, i.e. the model anchors to a fraction of the loss rather than computing anything. With parentage, the LLM proposes the *operational* change ("3–5% list increase on ~35–45% of volume") and the system computes the KPI effect. Same move as the ROLLUP fix: the number requiring arithmetic is computed, not narrated. It also repairs the moderator's weakest check, which verifies an option against its own stated inputs rather than against the data.

2. **The option space becomes bounded by reachability.** The tree names which leaves feed the breached KPI. An option touching none of them is not a weak solution — it is structurally not a solution to *that* problem, and nothing checks this today.

3. **Accretion adds transfer functions.** The static tree says margin depends on base-oil cost. It cannot say **lag** (how long before the parent moves), **elasticity** (how much per unit), **realisation rate** ("we captured 60% of list the last two times"), or **controllability** ("we have never moved base-oil cost inside a quarter"). VA verdicts accrete exactly these, converting a decomposition into a **lever map with observed transfer functions** — what a long consulting relationship builds and a first engagement lacks.

4. **Scope translation comes free.** Parentage carries weight, so "+2.8pp on Engine Oils" becomes "+0.9pp enterprise at 32% revenue share" automatically, stated at both levels. This is the ambiguity the v3 production briefing had to flag in its own risk register.

5. **Structural option diversity — possibly a better mechanism than persona differentiation.** ⚠️ **Scope interaction with Stage I.** Stage I exists because three MBB personas converge on one hypothesis. But enumerating the leaves under a breached KPI and requiring options to span *different branches* (one cost-side, one price-side, one mix-side) produces diversity **by construction**, without depending on personas differing at all. On the evidence gathered so far — same-discipline personas converge, cross-discipline ones diverge — branch coverage may be the more reliable forcing function, and it is cheaper. **Evaluate this before Stage I is scoped**, not after: it could reduce Stage I's scope substantially, or replace part of it.

6. **VA can grade the MECHANISM, not only the outcome.** Today VA asks "did margin recover?". With decomposition it can ask "did COGS actually fall?" separately — distinguishing *the lever worked but was offset* from *the lever did not work*. Those are indistinguishable today, which makes every verdict noisy and the learning weak. This is what actually closes the accretion loop; without it VA returns roughly one bit per solution.

7. **It compounds, and does not transfer.** Each engagement adds observed elasticities and lags to that client's tree. It improves with use and cannot be copied by a competitor — the concrete mechanism behind "year two beats year one", which the pricing/NRR work assumes but does not currently supply.

**Three limits, stated so they are not discovered later:**
- **Arithmetic decomposition is not causal explanation.** `theory_layer_design.md` §2.4 is explicit: every driver tree bottoms out in accounting atoms and causality keeps going. `gross_profit = revenue + cogs` says nothing about *why* COGS rose.
- **Few observations make weak elasticities**, and the provenance ladder must apply here too. A *computed* impact carries more authority than a guessed one, so a badly-grounded elasticity is more dangerous than a badly-grounded guess.
- **Bounding the option space excludes the reframe.** Sometimes the right answer is not a leaf on the tree — it is that the tree is the wrong tree.

#### Acceptance demo: cold KPI vs matured KPI — does grounding produce more trustable proposals?

The demo that proves the thesis, and the missing demonstration behind the pricing/NRR claim that **year two beats year one**. Accretion is invisible by nature; this makes it visible.

**Run it as a real experiment BEFORE it is ever a demo.** If the matured arm is not better, that is the most valuable thing this could tell us and we want to know privately. The Stage A structured-output A/B is the precedent — a tie, honestly recorded, was a useful result.

##### Design

**Same KPI, two grounding states — NOT two KPIs.** Two different KPIs differ in data quality, decomposability and problem type, so any difference would be unattributable: we would be doing to ourselves exactly what the two-baseline briefing did to its reader. Run one KPI twice, with the theory layer suppressed and then live, so grounding is a **feature flag** rather than a change of subject. `problem_profile` is available if the result later needs generalising across problem types.

| arm | state |
|---|---|
| **cold** | no decomposition, no confirmed edges, no graded assumptions, no confirmed constraints |
| **matured** | arithmetic parentage available, causal edges at `intervention_tested`, assumptions graded against outcomes, constraints confirmed through HITL |

##### The trap: the cold arm will look fine

⚠️ **This is the most likely way the demo fails.** Ungrounded runs today already produce three well-formed options with scope stated, typed recovery ranges and plausible prose — measured conformance was **9/9 on every axis** in both arms of the Stage A A/B. A naive side-by-side shows two arms that read about equally well, and the exhibit falls flat.

**The difference is not how the recommendation READS. It is what can be CHECKED.**

| | cold | matured |
|---|---|---|
| impact | asserted; nobody can tell whether it is achievable | **computed** from the client's own arithmetic |
| causal claim | plausible mechanism, unverifiable | edge confirmed by DiD on their data |
| assumptions | listed | graded — this one held, that one broke |
| constraints | inferred from prose | confirmed by their team |

The exhibit must therefore make **verifiability** visible, not merely place two narratives side by side. Otherwise the demo undersells the thing it exists to prove.

##### Scoring — instruments, not eyeballs

"Trustable" is not eyeballable, and a demo scored by the demoer proves what the demoer wants. Score with the deterministic instruments already built: groundedness G1–G6, scope conformance, mechanism fingerprint, the narrative validator, and — once T2 lands — whether impact was **computed or asserted**.

**Pre-register the KPI and the claims before running.** Choosing the KPI where accretion happened to help most is cherry-picking with extra steps.

##### Lead time — start accreting now, not at demo time

The matured arm needs genuinely accreted content: confirmed edges, graded assumptions, observed elasticities. That does **not** arrive with the feature; it arrives with *use*, and with VA verdicts in particular.

So begin accreting on the Lubricants scenario from the moment the mechanisms exist — running the HITL loop for real and letting confirmations accumulate, so there is genuine theory to show when the time comes.

**The line that keeps it honest, and also what makes it persuasive:** a confirmed edge must be confirmed by **actual DiD**, never by someone typing it in. An `intervention_tested` badge means something precisely because it cannot be granted by hand. Hand-seeding the matured arm would produce a demo that wins the room and cannot survive a pilot.

---

#### Sequencing against the rest of the plan

After **Phase 16** (T1 is a hard prerequisite) and alongside or after **assumption grading step 2** (T3). T2 and T4 are new models that can be built in parallel once T1 lands. Section 3 can be prototyped against Lubricants at any point to prove the rendering, but must not ship until the density gate passes.

#### RESOLVED: derive the structure, author the presentation

The Core Spine's **graph** — what decomposes into what — is **derived** from the decomposition model. Its **layout** — which branches to show, collapse, emphasise, and in what order — is **authored**. Facts are derived; judgement is declared and labelled as judgement. Same separation as `comparison_basis`, `measure_semantics`, and confirmed-vs-template provenance.

**Why structure must be derived:**
- **The arithmetic already exists.** `gross_margin_pct` is `100 * SUM(rev + cogs) / SUM(rev)`; the decomposition is sitting in the KPI definition. Authoring restates a fact written down elsewhere, and a restated fact drifts — the failure mode Phase 16 exists to close.
- **A stale diagram is worse than a stale table.** Change a KPI formula and an authored tree goes quietly wrong. A picture carries more authority than a row of numbers: people argue with a table and believe a diagram.
- **Derived structure is testable.** Assert that children reconcile to their parent — if `gross_profit`'s children do not sum to `gross_profit`, either the tree or the KPI is wrong, and it surfaces at build time rather than in front of a CFO. An authored tree is an assertion with nothing to check it against.
- **It generalises.** A new client gets a tree from onboarding. Authoring adds a manual step, and Phase 16 established the wizard does not reliably collect the semantics it already needs.

**What authoring genuinely buys, and is therefore kept for presentation:** DuPont's canonical shape is what a CFO recognises; emphasis is editorial (collapse SG&A to one node, explode COGS into five); and not every KPI belongs on a spine.

**Storage consequence for T2** — this is the decision's practical output:
| layer | holds | required? |
|---|---|---|
| decomposition model | arithmetic parentage only: parent, children, operation | yes |
| presentation layer | collapse / emphasis / order / exclusions, per client | optional |

Absent a presentation layer you get a plain derived tree — **correct by default, pretty by choice.**

**The failure mode this design forbids: authoring the STRUCTURE.** A hand-drawn "gross margin comes from these three things" that disagrees with the KPI formula produces a diagram contradicting the numbers printed beside it — the two-baseline briefing in picture form, and harder to catch because nobody re-derives a tree by eye.

**The argument that settles it:** the decomposition model earns its keep beyond this exhibit. Arithmetic parentage is what tells you what a segment-level recovery claim does to the enterprise KPI — groundedness check **G3 done properly rather than heuristically** — and it is what `scope_eligible` would lean on. Derivation is not merely cheaper; **it unlocks checks authoring cannot provide.** Authoring buys appearance and nothing else, and that asymmetry decides it.

---

### Phase 18: Council Roster De-branding + Lens Council as a First-Class UI Citizen

> **Numbering note:** Phase 14+ below is the reserved unscheduled Future bucket; 15–17 are taken.
> This takes the next free number, 18.

**Goal:** retire consulting-firm identity as a *product feature*, and make the Lens Council
(`commercial` / `operational` / `structural`) render as well as MBB does instead of degrading to grey
fallbacks.

**Two independent drivers — either alone justifies the work.**
1. **The lens roster already exists and is second-class in the UI.** `lens_council` is in
   `consulting_personas_registry.yaml` with full framework/bias definitions, and E1/E2 ran on it. But
   every UI affordance is keyed to firm ids, so a lens run falls through to `{ id, label: id, color:
   'text-slate-400' }` — grey text, the generic `default` thought script, no specialty framing.
2. **Firm identity is currently a product feature, not a citation.** See the categories below.

#### Three categories of firm-name usage — only one is a problem

| # | Category | Sites | Disposition |
|---|---|---|---|
| **A** | **Attributed citation of published research** — McKinsey's 2025 *State of AI* survey, linked to mckinsey.com | `LandingPageAlternate.tsx:259-265`, `InsightsBIModernization.tsx:562-606` | ✅ **Keep.** Normal sourced citation, correctly attributed and linked |
| **B** | **Comparative marketing claims** — "the kind of structured analysis a McKinsey engagement delivers"; "on McKinsey, BCG, and Bain analytical traditions" | `LandingPage.tsx:270,635`, `HowItWorks.tsx:639,694` | ⚠️ **Judgment call, not engineering.** Positioning copy asserting equivalence to named competitors' services. Owner decision, listed for completeness |
| **C** | 🔴 **Firm identity used as product functionality** — a user *selects* "McKinsey" as an advisor and receives output attributed to "McKinsey & Company" | below | **This is the phase** |

**Category C inventory:**
- `uiConstants.ts:45-47` — persona picker entries `{ id: "mckinsey", label: "McKinsey", type: "firm" }`,
  each with an approximation of the real firm's brand colour (blue / green / red)
- `uiConstants.ts:37,39` — council presets described as "McKinsey, BCG, Bain" and "Accenture, Deloitte, BCG"
- `ExecutiveBriefing.tsx:457-460` — full legal names in the briefing itself — **CHROME cleared
  2026-08-16, CONTENT still leaking.** Phase 13 Cat 3 removed `FIRM_DISPLAY_NAMES`/`FIRM_STYLES`;
  names now come from `utils/personaLabels.ts` (the analytical tradition, not the firm), colours are
  assigned by position from a neutral palette, and the audit footer no longer title-cases raw ids
  onto the exported PDF as "Mckinsey · Bcg · Bain". **But the de-branding is incomplete, because the
  MODEL writes firm names into option prose and that prose renders verbatim** — see the Cat 2 gap
  below. An earlier revision of this line claimed the item was cleared outright; that was wrong.
- `CouncilDebatePage.tsx:11` — per-firm styling keyed by id
- `CouncilDebate.tsx` — **fabricated dialogue naming real firms**: *"Reviewing BCG proposal: does the
  experience curve logic hold at this volume?"*, *"Stress-testing Bain's implementation timeline…"*,
  *"McKinsey option: strong diagnosis, but who owns the execution?"* Severity qualifier: this block
  renders only pre-results (`!stageOneHypotheses || phase < 2`), so it is a **loading animation**, not
  fabricated analysis presented as output. Still invented quotes attributed to named real firms
- `ProblemRefinementChat.tsx:29` — maps a principal's `decision_style: "analytical"` to a badge
  reading **"McKinsey"**, so a person's decision style renders as a consulting firm

*Not a legal opinion — recorded as a commercial/diligence exposure that exists in shipped code today
and is independent of how the lens-vs-MBB analytical comparison resolves.*

#### 🔴 The functional blocker, found while inventorying

`DeepFocusView.tsx:968` and `:1072` hardcode `['mckinsey', 'bcg', 'bain']` as the fallback roster:

```ts
selectedPersonas: refinementResult?.recommended_council_members?.map(m => m.persona_id)
                  ?? ['mckinsey', 'bcg', 'bain'],
```

**Changing the backend default roster does not change what the UI requests.** Any roster swap that
does not touch these two lines will silently keep running MBB whenever the refinement result carries
no recommended council — which is exactly the arms-A0/B0 case where refinement never ran. This is a
functional defect, not styling, and it is the single highest-priority line item here.

#### Scope

| Item | Work | Size |
|---|---|---|
| **1** | Remove the hardcoded MBB fallback in `DeepFocusView.tsx` (×2) — default must come from the registry preset, not a literal | S |
| **2** | Make persona display data-driven — label, colour and description resolved from the persona registry rather than `uiConstants.ts` literals and `FIRM_NAMES` maps in two components | M |
| **3** | Per-lens thought scripts + colours so `commercial`/`operational`/`structural` do not render grey with generic text | M |
| **4** | Retire the fabricated firm dialogue in `CouncilDebate.tsx`; replace with lens-appropriate progress text that does not impersonate anyone | S |
| **5** | `ProblemRefinementChat.tsx:29` — `decision_style` badge shows the style ("Analytical"), not a firm | S — ✅ **DONE 2026-08-16** |
| **6** | `ExecutiveBriefing.tsx` — persona attribution and colours from the registry; no legal entity names in output | M — ⚠️ **CHROME DONE 2026-08-16, content not** |
| **7** | Decide the fate of the branded personas themselves: retire from the registry, or keep selectable and unadvertised | Decision |
| **8** | 🔴 **NEW** — `a9_deep_analysis_agent._recommend_diverse_council` hardcodes `PARTNER_RULES`: eight real firms with full legal names, keyword affinities and role mappings. This is a **backend** source of firm identity the original inventory missed | M |
| **9** | 🔴 **NEW** — Cat 2 prompt rule: stop the model writing firm names into option prose | S — ✅ **DONE 2026-08-16** |

#### Inventory correction (2026-08-16) — firm identity is FIVE layers, not one

The original inventory above is UI-only, which made the problem look like a labelling exercise. Found
by walking the live app during Phase 13 Cat 3:

| # | layer | site | state |
|---|---|---|---|
| 1 | **Council recommender** | `a9_deep_analysis_agent.py` `_recommend_diverse_council` → `PARTNER_RULES` | untouched — produces the *"AI Recommends — Boston Consulting Group · PwC Strategy& · Accenture · KPMG Advisory"* panel, with "Matched: market, competitive" rationales |
| 2 | **Persona registry** | `consulting_personas_registry.yaml` — 8 firm personas by legal name + the `mbb_council` / `big4_council` presets | untouched |
| 3 | **UI chrome** | briefing, refinement badge | ✅ done (items 5, 6-chrome) |
| 3b | **UI chrome** | persona picker, presets, `CouncilDebate.tsx` fabricated dialogue, `DeepFocusView` fallback roster | untouched (items 1–4) |
| 4 | **SF prompt** | council profiles name each firm and instruct "apply signature frameworks" | ✅ constrained by item 9 — names still reach the prompt as reasoning anchors, but output text is now forbidden to carry them |
| 5 | **Model output** | firm names written into `options_ranked[].description` / `.rationale` | ✅ addressed by item 9, **unverified** — see below |

**The lesson worth keeping: de-branding one layer makes the others more visible, not less.** Cat 3
cleaned the briefing chrome and the very next walkthrough surfaced a firm badge in the refinement
panel and a firm roster in the council picker. To a user there is no "scoped surface" — a partially
de-branded product reads as a bug, not as staged work. Either finish the sweep or leave it whole.

**Item 9 shipped without a verification run, deliberately and on the record.** The prompt constraint
is in place and 66 SF unit tests pass, but no live synthesis has been run against it. The leak is
intermittent (one clean run, one leaking, same pipeline), so a single green run would not have proved
anything anyway — absence of a run at least does not manufacture confidence. The firm-name sweep in
`live-briefing-cat3.spec.ts` / `live-briefing-cat3-refined.spec.ts` is the standing regression test;
the next live run either shows it holding or does not.

#### The substitute already exists

`consulting_personas_registry.yaml:350` — `lens_council`, *"Commercial / Operational / Structural —
method-defined, not firm-branded"*, with three fully-defined personas (`commercial`, `operational`,
`structural`) at lines 258 / 289 / 319. Item 7 is therefore not "design a replacement"; it is "decide
whether to make the existing replacement the default", and that decision is gated on the analytical
comparison being readable — see Not in scope, below, and `decision_quality_rubric.md` §9.

#### 🔴 The lens roster is DOMAIN-SCOPED and expected to grow (owner, 2026-08-16)

**There are three lenses because the launch domain is Finance KPIs.** Commercial / Operational /
Structural is a decomposition of *"margin fell"*, and the registry definitions say so outright —
Price-Volume-Mix, Customer Profitability, Cost-to-Serve, Overhead Absorption, Portfolio
Participation, Structural-Decline-vs-Cyclical-Dip. **Organizational and other lenses are expected
later, as the domains they serve are onboarded.** The set is a launch-domain roster, not a claim
about how many perspectives exist.

**This corrects how the coverage assessment below should be read.** Capital & liquidity, risk /
compliance / contractual, and competitive response are not holes in a roster that should have been
complete — they are lenses that arrive with their domains. The assessment's own conclusion ("coverage
is relative to the problem class, and there is no universal set") was right; what it lacked was the
consequence, which is that the roster is *designed* to be extended rather than merely *observed* to
be incomplete.

**Design consequence for item 7, and it is a real one.** The firm roster was universal by pretence —
any firm will advise on any problem, so a global default council was coherent even though it was
meaningless. A lens roster is honest by construction: a lens is *defined by the analytical territory
it covers*, so a global default is incoherent the moment a second domain exists. Swapping
`mbb_council` → `lens_council` is therefore **not a like-for-like substitution**. It needs a
selection mechanism keyed to the problem's domain — most naturally the KPI's data product or business
process, both already on the registry record. Item 7 should be re-scoped to include that resolver,
otherwise the first non-finance KPI gets a finance council and nothing in the system notices.

⚠️ **Naming collision to settle before Phase 18 writes more "lens" text.** "Lens" already means
something else here: `principal_perspective_weighting_design.md` §2 defines **five comparison lenses**
(Plan / Trend / Peer / Value-gap / Bridge) — *appraisal* lenses controlling which comparison a
principal's role weights. The council lenses are *analytical-territory* lenses. Two unrelated
concepts, one word, and the same document set. Pick distinct names now; renaming after both are
built across prompts, registry ids and UI copy costs far more.

#### Not in scope
- Category A citations (keep) and Category B marketing copy (owner call, not engineering).
- Whether the lens roster is analytically *better* than MBB. **Unresolved** — E1/E2 both hit 3/3
  distinct lever families, but so did five of six pre-fix MBB arms, and the control C1 is n=1 and the
  worst run in the corpus. See `decision_quality_rubric.md` §9.

#### Sequencing
**Item 1 is independent and should not wait** — it is a live defect regardless of which roster wins.
Items 2–6 are worth doing on the de-branding driver alone and do not depend on the analytical
comparison. **Item 7 does depend on it**, and on the control replication that makes §9 readable.

#### Do the three lenses cover the important perspectives? (assessed 2026-08-16)

**For a margin problem on a P&L data product, close to complete** — Commercial takes the revenue side,
Operational the cost side, Structural the participation question. That is a clean decomposition of
"margin fell."

**But coverage is relative to the problem class, and there is no universal set.** Asking whether three
lenses cover everything presumes a complete roster exists; it does not. What is absent, and when it
would bite:

| absent perspective | bites when |
|---|---|
| **Capital & liquidity** — working capital, cash conversion, capex | a cash problem, which is not a P&L problem — none of the three reach it |
| **Risk / compliance / contractual** | the register *records* the anchor price-lock; no lens *reasons* about what an action would breach |
| **Competitive response** | Commercial reaches for repricing without modelling what the competitor does next |
| **Organisational capability** | "can we actually execute this" — Bain's classic angle, dropped in the lens roster |

🔴 **A lens without data is theatre, and that is the binding constraint.** `dp_lubricants_financials`
is a pure general ledger: one signed `amount` column over five dimensions, entirely P&L. No balance
sheet, no volume, no headcount. A capital lens would have nothing to reason over and would produce
confident prose about working capital it cannot see — the same failure class as the −457% margin
incident. **Lens coverage is therefore gated on the operational data layers deferred 2026-08-16
(volume/units discussion), not on roster design.**

**The routing mechanism already exists.** Stage I B-1 routes *interview topics* by problem shape and
`_recommend_diverse_council` already does keyword/role matching for councils. The answerable question
is not "do three lenses cover everything" but **"does the routing pick the right lenses for this
problem"** — incremental, and requiring no universal roster.

🔴 **Design contradiction worth naming.** The Structural lens is built to question the frame — its
approach is literally *"questions the frame before optimizing inside it"* and its stated strength is
*"names when a KPI-recovery frame may be the wrong frame."* But DA **authors** the frame in SCQA
before any council runs (`problem_framing_design.md` §1b). The one lens designed to challenge the
frame is handed a frame already committed to prose and shipped downstream. **This is not a roster gap
— it is the framing work, and closing it would unlock a capability the roster already has.**

**What the evidence supports.** E1 and E2 each produced **3/3 distinct lever families**, so the three
lenses are non-redundant on this problem — the necessary condition, and precisely what MBB failed
(McKinsey/BCG topic Jaccard 1.00). E2's structural option proposed SKU exit/de-emphasis, the first
sign that lens does its job. n=2 against an unreadable control, so encouraging rather than established.

**Recommendation: do not add lenses now.** Revisit routing when a second problem shape gives something
to route *to*, and revisit capital/risk lenses when the data exists to support them. A fourth lens
today is a voice with nothing to read.

#### Open decisions
1. Are branded personas **removed** from the registry, or kept selectable but not surfaced? Removal is
   cleaner; keeping them preserves the A/B corpus's reproducibility.
2. Does the lens council become the **default preset**, before the comparison is settled? Defaulting to
   an unproven roster on de-branding grounds is defensible, but it should be a stated choice rather
   than a side effect of item 1.
3. Does the briefing name a lens at all? Attributing an option to "Commercial Lens" is honest; it may
   also be noise an executive does not need.

---

### Phase 19: Problem Framing — the frame is chosen, not inherited

> **Numbering note:** 15–18 are taken; Phase 14+ below is the reserved unscheduled Future bucket.
> This takes the next free number, 19.

**Full design:** `docs/architecture/problem_framing_design.md`. This entry records scope, sequencing
and dependencies only — the reasoning, the rejected alternatives and the open decisions live there.

**Goal:** the problem frame is **chosen by a human and recorded**, rather than authored by DA and
inherited by everything downstream.

**Why it is its own phase, not a stage of another:**
1. **It is the only systematic cap left on the Decision Quality chain.** Link 1 fails 11 of 13 scored
   runs. Links 2/3/5/6 pass consistently and link 4 passes whenever a client is configured
   (`decision_quality_rubric.md` §10).
2. **It is outside Phase 15 by that phase's own goal statement** — "grounded in a verified cause,
   honest about what they bet on, calibrated on known vs inferred" all concern the quality of the
   answer to a given question, never whether the right question was asked. **Phase 15 can complete
   successfully with link 1 still failing.**
3. **It is cross-cutting, not backend-only** — DA generation order, the DA console's render order, the
   assumption register, SF's synthesis task text, and a new gate. That is a phase, not a stage.

**Scope**

| # | Work | Notes |
|---|---|---|
| **1** | ~~Mandatory one-question framing gate, fires before SF **independently of the refinement interview**~~ 🔁 **superseded (2026-08-18) — mechanism B:** the framing question is the **mandatory first topic** (`problem_framing`) of the existing refinement interview instead, gating "Generate Solutions" until answered | `REFINEMENT_TOPIC_SEQUENCE` / `PROTECTED_TOPICS` / `MAX_TOPICS_IN_SEQUENCE` — practical guarantee unchanged (framing inserted after the cap runs), mechanism changed |
| **2** | Move `_generate_scqa_summary()` + DA's recommendation to **after** the gate | SCQA is the *output* of framing (decided 2026-08-16); executed by a full backend reorder behind `enable_framing_gate` |
| **3** | 🔴 `DeepFocusView.tsx` must not render `ScqaBlock` pre-gate | today it shows the answer first as "Recommendation" in `text-lg text-white` and the frame last in `text-slate-500 italic text-xs` — an anchored "yes" that still reports `frame_examined: true` |
| **4** | Frame decision written to the `Assumption` register with `falsification_criterion` + `expiry_event` | no new model; provenance ladder already exists; `expiry_event` (not calendar `expiry`) since the trigger is a VA verdict |
| **5** | Re-present a prior frame **with its reasoning and falsifier**, never as a pre-ticked default | the accretion-hardening risk; this is the whole mitigation |
| **6** | SF synthesis task text must be able to *express* a reframed objective | today it requires every option to name "the primary driver of THIS KPI situation" |
| **7** | DQ link 1 grades the **recorded decision**, retiring the term screen | also retires a screen with a known 71% FPR on this class — **carried forward, not built in the current plan** (see below) |
| **8** | Market Analysis repositioned as an input to DA's own framing/SCQA construction, not a sidecar between DA and SF | same MA call timing, no added latency/cost — Decision #12 of the implementation plan |

**Both prerequisites now closed (2026-08-17).** The build is unblocked for the first time this session.

✅ **Adjudicate the corpus before building — done.** All 13 `scope_arm_*.json` runs plus 4 fresh live
e2e runs (MBB control, MBB+refinement, first-ever live `lens_council` run) read verbatim, not just
scored. Verdict: **right call, essentially never examined — not a wrong call.** A real, specific
alternative (recover margin vs. reduce base-oil exposure — the confirmed root cause) sat unexamined in
every one of 17 runs. Sharpens the phase's own falsifier rather than triggering it: not "confirmed
unchanged," *never asked*. Full writeup: `problem_framing_design.md` §10.

✅ **Score a second problem shape — done.** Deliberately targeted Net Revenue's plan-variance card
(*"$20.2M / -16.2% below budget"*) over another year-over-year decline, specifically for its different
comparator mechanism (`plan_variance`/budget, not `threshold_breach`/prior-period) and unknown
concentration pattern. Confirmed genuinely different on two independent axes computed directly from
`kt_is_is_not`: 60 segments analyzed (vs. single digits), dominance ratio 1.76 — **below DA's own 2.0
"concentrated" threshold**, i.e. `distributed`, not `concentrated`. **The framing gap holds across
both shapes identically** — L1 fails on adjudication both times (5/6, capped by frame), the objective
is never offered as a choice either time, and each shape carries its own specific unexamined
alternative (base-oil exposure on shape 1; whether the shortfall is real or a budget-setting artifact
on shape 2). *"Frame fails N of 13"* no longer rests on testing one recurring situation. Full writeup:
`problem_framing_design.md` §11.

**One genuine difference worth carrying into the build, found on shape 2 and not shape 1:** the
frame's *reasoning quality* — not whether the objective was examined — was visibly sharper. Shape 2's
`COMPLICATION` explicitly separated confirmed problem segments from likely budget-artifact segments,
and its `key_assumptions` stated their own uncertainty rather than asserting the root cause as settled.
Different axis than L1 entirely, but worth the gate's design being aware sharper causal reasoning does
not substitute for the objective actually being asked about — the two can and did vary independently.

✅ **VA control-group side finding — investigated and CLOSED (2026-08-18), correcting the note below.**
The original observation (2/2 shapes showing `where_is_not` empty) was real, but the "shifting toward
a broader dataset property" conclusion was premature — checked and it does not generalize. Traced
`_benchmark_source` in `a9_deep_analysis_agent.py`: VA's actual signal is `benchmark_segments`, and
`problem` mode sources that from `where_is_not` while `opportunity`/`mixed` modes source it from
`where_is` instead (mixed mode deliberately empties `where_is_not`, retagging its content rather than
losing it). Both tested shapes happened to be `problem` mode. Dispatched DA directly (API only) on
`ecommerce_revenue` — a `mixed`-mode KPI unrelated to the shared base-oil shock — and got 17
`benchmark_segments`, **10 genuinely `control_group`-tagged** with real names and deltas (`National
Auto Parts Chain A`, `Chemicals & Additives`...), exactly what `workflows.py` would register onto a VA
solution. **No code change indicated.** The gap is real only for `problem`-mode KPIs downstream of the
base-oil shock (margin, revenue, and presumably the P&L rollups riding the same mechanism) — not the
client's data generally. Field-test plan takeaway: point it at an opportunity/mixed-mode situation, and
VA has a genuine counterfactual. Detail: `problem_framing_design.md` §12.

~~Adds to the "let VA's real outcome settle lens-vs-MBB" field-test plan's open gaps (alongside the
missing council-provenance field), and is its own worthwhile investigation — structural fact vs.
pipeline gap — independent of the framing gate build.~~ (superseded by the paragraph above — kept,
struck through, so the correction is visible rather than silently overwriting what was believed a day
earlier.) Second-shape detail remains at `problem_framing_design.md` §10–11; the VA correction is §12.

**Sequencing note.** Item 3 is a UI change and item 1 is a UX addition, so this phase overlaps Phase
18's console work. Worth landing them together rather than editing `DeepFocusView.tsx` twice.

✅ **Implementation plan approved, build started (2026-08-18).** 8-slice plan (register support →
framing prompt builder → SCQA deferral → wiring into the interview with server-side bypass guards →
frontend types + `FramingGateCard` → closing the three SF bypass paths + the pre-existing Cancel bug →
SF expressing the reframe), each independently committable behind `DA_ENABLE_FRAMING_GATE` (default
`false`). Plan: `C:\Users\Blell\.claude\plans\with-this-now-in-goofy-meteor.md`. Item 7 above (DQ link 1
grading the recorded decision) is explicitly carried forward, not part of this build — the plan ships
the decision record and the gate; re-pointing `decision_quality.py` at it is a follow-on.

✅ **Slices 1–6 shipped.** Both register migrations applied to production Supabase (with a real
migration-tooling gotcha found and fixed along the way — two same-day migrations collided on
Supabase's version key, since it tracks by leading numeric prefix only, not the full filename; fixed
by renaming one and re-verified against production via a read-only schema dump before AND after).

🔴 **A bigger pre-existing gap than the plan anticipated, found and fixed during Slice 6.**
`useDecisionStudio.ts`'s `handleStartDebate` — the function the plan assumed carries
`refinement_result` (and would carry `framing_decision`) to Solution Finder — has **zero callers
anywhere in the codebase**. It is dead code. The actual live SF dispatch path is
`DeepFocusView.tsx` navigating to `/debate/:id` with a `debateConfig` object that
`CouncilDebatePage.tsx` reads to build the request — and that object never carried refinement data
at all, only `selectedPersonas`/`councilType`/`selectedPreset`/`useHybridCouncil`/`resolvedAnalysisMode`.
**In production, Solution Finder has never received refinement's constraints, exclusions, or
hypotheses, independent of framing** — confirmed the receiving side was correct and simply unfed:
`a9_solution_finder_agent.py` already reads `preferences.get("refinement_result")` and its
sub-fields correctly (constraint exposure, market signal routing), it just never arrived. Fixed by
threading a `refinementResult` object (including `framing_decision`, sourced from
`refinementResult.framing_decision ?? framingDecision` since only the ONE turn that submits it
carries the field) through `debateConfig` → `CouncilDebatePage.tsx`'s `preferencesBase.refinement_result`
— the same wiring point both fixes needed, done together rather than split.

**Frame-required determination is DERIVED, not a hand-defaulted flag**: before any refinement turn
runs this session, `useDecisionStudio.ts` computes `framingRequired` from
`currentAnalysis.scqa_deferred && !currentAnalysis.scqa_summary` — DA's own response already says
whether the gate is genuinely active for this analysis, so the frontend never has to guess the
backend flag's value out of band (correctly `false` for every flag-off deployment, correctly `true`
only when the gate is real and unresolved). Once a live refinement turn reports a value, that takes
over as the authority for the rest of the session.

✅ **Slice 7 shipped — the 8-slice build is code-complete.** New `_build_chosen_frame_section()`
reuses `stage1_allow_frame_challenge`'s shape (permission, already tested insufficient) driven by a
recorded decision instead (never tested until now) — injected into both Stage 1 (per-persona) and
synthesis prompts, gated on data presence (`framing_decision` can only exist once the mandatory gate
was actually answered), not a separate flag. `tests/unit/` sits at **1295 passed, 3 skipped** (was
1205 at the plan's own stated baseline) with every slice landing its own tests plus real bugs found
and fixed along the way, none regressed.

✅ **Live-verified 2026-08-19** — two full live Playwright runs (`live-framing-gate.spec.ts`,
`live-framing-gate-ecommerce.spec.ts`) against the real running app, both passing, screenshots
inspected directly: `gross_margin_pct` (owner viewing own KPI, problem mode, 6 causal + 1 market-signal
alternative, reframe chosen and expressed by SF's Stage 1 personas) and `ecommerce_revenue`
(non-owner CEO viewer, mixed mode, zero causal-graph alternatives — confirms empty-graph never
fabricates). Two real bugs found and fixed live: owner-attribution role-abbreviation mismatch
(`_roles_match`), and local Supabase missing the Phase 19 migrations. A third, found by the user's own
manual testing right after: the pre-framing "Analysis" panel rendered completely empty because the
whole SCQA blob (not just Question/Answer) was deferred — fixed via `_build_situation_complication_facts()`
(facts-only, no LLM call). 🟡 **Still open**: the measurement Phase 19 exists for — re-scoring DQ link 1
on a post-gate live run against this session's own 17-run baseline.

**Stated falsifier** (from the design note, recorded before any build): if the frame is examined and
confirmed unchanged in nearly every run, this is an expensive way to write `frame_examined: true`, and
the honest conclusion is that the frame really is determined by the KPI that breached. **Not what
happened** — see the adjudication above; the frame was never asked, not confirmed unchanged.

---

### Phase 20: Causal-neighbourhood evidence + Market Analysis field wiring (in progress, 2026-08-19)

Live use of Phase 19 surfaced that `FramingAlternative` carries only relationship metadata for each
causal neighbour — never its own current value or trend — and that `FramingGateCard`'s narrow Action
Center column can't legibly host the richer evidence a framing decision actually needs. Full decision
record: `docs/architecture/problem_framing_design.md` §14 (9 decisions — neighbour evidence depth,
ranking criteria, the top-3 cap + disclosure, no new graph viz, MA field wiring scope, trend-chart
design, the evidence/decision panel split, evidence-before-prompt timing). Build sequence:

✅ **Backend**: `_fetch_neighbour_snapshot()` + `_fetch_neighbour_monthly_trend()` (BigQuery-only this
pass) + `_fetch_neighbour_evidence()` (DA) — one non-dimensional rollup query per neighbour, reusing
DA's own DPA-calling pattern (not a new SA RPC); concurrent across alternatives (bounded
`asyncio.Semaphore(6)`), non-fatal per neighbour (`return_exceptions=True`). Ranking (hop-tier first,
then `|percent_change|`) + top-5 list cap + `additional_causal_measures_count` disclosure wired into
`_build_framing_prompt`. New `NeighbourSnapshot` model; `FramingAlternative.neighbour_snapshot`,
`FramingPrompt.primary_snapshot`/`.additional_causal_measures_count`. 50 new/extended unit tests in
`test_da_framing_prompt.py` (ranking order, cap+disclosure, non-fatal degradation, market-signal
alternative never counted against the cap) — 1332 passing, no regressions.
✅ **Backend**: `workflows.py` MA field wiring — `synthesis`/`confidence`/`sources_queried` (already
computed by MA, previously dropped at the `market_signals`/`market_conflict` assembly point) now reach
`da_output.market_synthesis`. No new LLM/API call.
✅ **Frontend**: `CausalTrendChart.tsx` promoted from its throwaway prototype route (removed, along with
`ChartPrototype.tsx`) into the real component tree. New `CausalNeighbourhoodEvidence.tsx` (the LEFT-panel
evidence — chart + detailed per-alternative cards) rendered in a new "Causal Neighbourhood" accordion in
`DeepFocusView.tsx` that auto-expands the moment the framing gate activates (decision 9). `FramingGateCard.tsx`
slimmed to a compact color-dot + short-label list (decision 8) — mechanism/hop/confidence/provenance detail
moved to the evidence section. New `utils/causalColors.ts` (shared color/label assignment — the connective
tissue between the two panels) and `utils/causalTrendSeries.ts` (raw monthly_values → indexed % change,
each series baselined to its own first available point). `market_synthesis` surfaced in the Market
Intelligence accordion. `tsc --noEmit` and `npm run build` both clean.
🟡 **Live verification**: in progress (see this session's own live-verification discipline — code-complete
and unit-tested is not the same claim as "verified live").
Card update + commit: pending completion of live verification.

---

### Phase 14+: Future (not scheduled)

| Initiative | When |
|-----------|------|
| **Strategic causal graph** — `docs/architecture/strategic_causal_graph_design.md` (design note, not built). DQ link 1 (frame) failed 3/3 live runs 2026-08-19 because the causal graph is operational-only; a principal can never be offered a strategic/portfolio alternative at the framing gate. Highest-value consequence: converts L1 from a 71%-false-positive text screen into a real check. | After demo cycle — lock the open decisions in that doc first (node model, provenance vocabulary, per-client curation), ideally after confirming L1's failure rate beyond n=3 |
| **Per-KPI time dimension selection** — `docs/architecture/data_product_time_dimension_planning.md` (design note, not built; interim mitigation already shipped on `dp_lubricants_sales`). `_resolve_time_spec` picks one `primary` time dimension per data product with no per-KPI override; found live, 90.2% of Sales Order Items had `delivery_date` in a different fiscal month than their revenue's recognition period (5.5–8.9% swing on period-sliced KPIs). Narrow, additive fix (KPI-level `time_dimension_ref` + a `key` slug per time-dimension entry) — deliberately deferred because it touches the core DPA SQL-generation path. | Fast-follow, not pre-demo |
| **Causal edge magnitude** — `docs/architecture/causal_edge_direction_and_magnitude_design.md`. The **direction** half shipped 2026-08-20: `causal_direction` field + migration, lubricants' 6 edges backfilled, `_build_framing_prompt`'s hop-2+ path-validity filter (SA's undirected BFS untouched), 5 new regression tests — verified live, COGS/Premium Mix % no longer offered for Net Revenue, the 11F `base_oil_cost→cogs→gross_margin_pct` chain preserved. Hess/bicycle/apex_lubricants' edges still default to `causal_direction="unknown"` (safe, just unreviewed) — not yet backfilled. Remaining: `magnitude_category`/`magnitude_coefficient` (mirrors `confidence`'s categorical-not-a-float discipline; a real coefficient still requires `provenance="va_validated"`, same guardrail as `intervention_tested`) — blocked on a Granger implementation that doesn't exist. | Magnitude/curve: deferred. Other-clients' direction backfill: fast-follow |
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
| ~~Guided onboarding flow (4 steps)~~ | **Superseded (Jul 2026)** by a 6-step wizard shell (Workspace Setup / Principals / KPI Library / Assign Ownership / Connect Data / Validate & Launch) that embeds the real step components inline, computes completion from actual registry state (not click history), and adds a resume entry screen. Full design + implementation plan: `docs/architecture/onboarding_wizard_redesign.md`. |
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

#### Consulting Personas Registry — location gray area (noted, not scheduled)

`src/registry/consulting_personas/consulting_persona_provider.py` loads
`consulting_personas_registry.yaml` via `yaml.safe_load()`, process-lifetime singleton, no
`client_id` on any record. Two things worth resolving together, found 2026-08-15 while adding the
Commercial/Operational/Structural lens roster (`docs/architecture/persona_council_experiments.md` §7c
step 2):

- **Directory mismatch, not a rule violation.** The five enumerated registry types in
  [CLAUDE.md](CLAUDE.md) (KPIs, principals, data products, business processes, glossary) don't
  include consulting personas, and the content is genuinely non-tenant — shared methodology
  descriptions, not client data — closer in kind to `src/registry_references/` (explicitly carved out
  as "schema definitions, not registry data") than to anything Supabase-backed. But the file lives
  inside `src/registry/`, whose own structure comment says "Supabase-backed providers (no YAML)."
  Low-risk fix: relocate to `src/registry_references/consulting_personas/` so the exception is legible
  in the tree instead of silently contradicting the directory it sits in.
- **Same live-reload gap as the rest of this section.** The class-level singleton cache means an edit
  to the roster (including the lens personas just added) needs a full backend restart to take effect —
  discovered by testing, not by design. If Registry Live-Reload above is ever generalized to a
  provider-agnostic "reload on demand" mechanism, personas should be swept in rather than left as a
  restart-only exception.

**Not scheduled.** No client currently needs a private or customized roster — `principal_affinity` in
the same file is keyed by role name, not `client_id`, confirming the shared/global design is
intentional as-is. Revisit if that need appears; the seed-file protocol used elsewhere is the natural
pattern for a client-scoped variant if one is ever needed, not something to build speculatively now.

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

### Infra B3: Database-Level Multi-Tenant Isolation ← ✅ SHIPPED July 2026

**Status: complete and verified live in production (2026-07-14).** All three layers implemented, migration `supabase/migrations/20260713_rls_client_isolation.sql` applied to production via `supabase db push --linked`, and `scripts/verify_prod_registry.py --env production` confirms: `a9_tenant_scope` role present without BYPASSRLS, RLS + `client_isolation` policy live on all 12 tenant tables, and both fail-closed probes pass (no client context ⇒ 0 rows; scoped context ⇒ only that client's rows) against the real production database.

**Follow-on cleanup (2026-07-14):** while closing out verification, found and fixed two unrelated items surfaced along the way — `.env.production`'s `SUPABASE_DB_URL` was malformed (password missing, wrong pooler region) and had silently been pointing nowhere useful for direct-Postgres tooling; and production's `business_contexts`/`business_processes` tables carried stale non-production rows (`bicycle`, `hess` demo clients; 26 legacy canonical business-process rows on `lubricants` predating `BUSINESS_PROCESS_IDS`-scoped onboarding). Both cleaned up; `_FALLBACK_CLIENTS` in `registry.py` updated so `bicycle` can't reappear via the fallback path.

**Design deviations from the original sketch below (verified during implementation):**
- The app's asyncpg pool connects as `postgres`, which has **BYPASSRLS** in Supabase — plain `ENABLE ROW LEVEL SECURITY` + FastAPI middleware would have been silently bypassed. Instead: a dedicated `NOLOGIN` role `a9_tenant_scope` (no BYPASSRLS), switched to per-transaction via `SET LOCAL ROLE` + `set_config('app.client_id', …, true)` in `src/database/tenant_scope.py`. Policies are fail-closed (`client_id = current_setting('app.client_id', true)` — GUC unset ⇒ zero rows).
- Registry reads are served from an in-memory all-tenant cache loaded at bootstrap, so per-request middleware would gate nothing. RLS enforcement is applied at the DB-access layer on the paths that hit Postgres per request: `PostgresManager.fetch_records_scoped()`, `DatabaseRegistryProvider.load()` (when client-scoped), and the accountability + kpi_relationship providers.
- Layer 3 (DGA `validate_data_access`) was already implemented and tested but never called at runtime; the actual work was wiring it into DPA `execute_sql` as a fail-closed gate (scoped principal + no DGA ⇒ deny).
- Bonus fix: composite-key delete in `DatabaseRegistryProvider` deleted by bare `id`, which removed every tenant's same-id row. Now `delete_record_multi` matches all key fields.

**Residual gaps (tracked, not blockers):**
- `situations`, `kpi_assessments`, `situation_actions`, `value_assurance_evaluations`, `briefing_tokens` have no `client_id` column — isolation is indirect via parent records. Add columns + policies when those tables become tenant-sensitive.
- `list_principals` (registry.py) has a PostgREST/service-role fast path that bypasses RLS by design; it applies its own strict `client_id` filter server-side.
- SA agent still loads all tenants' KPIs into its dual-keyed in-memory registry and filters in `_get_relevant_kpis` (strict, tested) — moving SA to per-request scoped loads is future work.
- `RegisterSolutionRequest.client_id` (value_assurance.py `/register`) is accepted and correctly threaded into the persisted `AcceptedSolution`, but not required — a caller that omits it produces an orphaned row (`client_id=NULL` never matches any tenant's RLS session) rather than active misattribution. Lower severity than the writes below (data goes missing, not to the wrong tenant) but should eventually fail closed the same way.

**Follow-on audit (2026-07-21) — write-path completeness, not RLS:** Testing the rebuilt onboarding wizard (see Onboarding Wizard Redesign below) surfaced that RLS's read-isolation guarantee does not catch a different bug class: a write path that never resolves a `client_id` at all, so the persisted record silently gets the model's env-var default (`DataProduct`/`KPI` both default to `os.getenv("ACTIVE_CLIENT_ID", "lubricants")`) — a fully RLS-valid but *wrong* tenant, not a leak RLS is positioned to detect. Two directly wizard-reachable paths had this bug: `A9_Data_Product_Agent.register_data_product` (the data-product-onboarding workflow's registration step) and `A9_KPI_Assistant_Agent._trigger_registry_updates` (the "Register Data Product" button's KPI finalize call) — both fixed to fail loudly instead of defaulting, with `client_id` now threaded through the full request chain from the frontend. Widened into a full audit of every registry-mutating endpoint against CLAUDE.md's tenant-isolation rule (client_id mandatory on every KPI/Principal/DataProduct/BusinessProcess/GlossaryTerm record):
  - `business-processes` and `business_glossary_terms` create/update endpoints had **no ownership enforcement at all** (trusted whatever `client_id` was in the request body verbatim) — brought in line with kpis/principals/data-products via the same `_resolve_create_client_id`/`_enforce_write_ownership` helpers. Their models' `client_id` field previously defaulted to `"default"` with a docstring claiming shared/cross-tenant visibility; confirmed via the actual RLS policy (strict equality, no shared carve-out) and production data (zero rows anywhere use `"default"`) that this was vestigial from a pre-multi-tenant design, not a real feature — removed rather than preserved.
  - `connection_profiles`, `kpi_accountability`, `kpi_relationships`, `kpi_templates` `/commit` were already correctly enforcing this and needed no change.
  - Regression coverage: `tests/unit/test_registry_write_requires_client_id.py`.
  - **Product idea preserved, mechanism changed:** the original reasoning behind the shared `business_processes` scope was sound — most Mid-Market ICP clients share ~80% of common business processes, and a shared starting point would speed onboarding. Rather than a shared/ambiguously-owned registry row (which is exactly the ownership-ambiguity this audit closed), implement this the way KPI templates already do it: a canonical process library used as a *generation* source during onboarding, committed as a fully client-owned row the moment a client accepts it. Nothing is ever stored without a real owner. Candidate for Phase 12 (pairs naturally with Org-First Accountability Onboarding, Phase 12B).

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
