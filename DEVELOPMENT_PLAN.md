# Agent9-HERMES Development Plan

**Created:** 2026-03-14
**Last updated:** 2026-04-08
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
```

**14 agents operational.** Core loop: detect → diagnose → prescribe → decide → track.

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
| PIB email delivery (Jinja2, SMTP, Gmail App Password) | Production-ready |
| Single-use briefing tokens (deep link, delegate, request_info, approve) | Production-ready |
| Delegation flow (DelegatePage, audit trail in situation_actions) | Production-ready |
| Follow-up NL questions with inline data results | Production-ready |
| Data Product Onboarding (8-step orchestrated workflow) | Production-ready |
| Decision Studio UI (React/Vite/Tailwind) | Production-ready |
| Supabase-backed registries (6 registries) | Production-ready |
| DuckDB + BigQuery + PostgreSQL data sources | Production-ready |
| Production deployment (Railway + Vercel + Supabase Cloud) | Live (deployed Mar 2026) |

### What's not built yet

| Capability | Planned phase |
|-----------|--------------|
| KPI accountability registry (dimensional ownership) | Phase 11A |
| LLM-assisted accountability import from HCM documents | Phase 11B |
| Swiss Style brand identity across UI | Phase 10 |
| PIB email — brand refresh | Phase 10 |
| DGA mandatory wiring (eliminate 16 governance fallback paths) | Phase 10B-DGA |
| Multi-tenant data connectivity (MCP-first, Snowflake/Databricks/HANA) | Phase 10C |
| KPI trend chart (monthly_values populated for all backends) | Phase 10C |
| Unified situation stream (merge problem + opportunity) | Phase 11C |
| Adaptive calibration loop (KPI Assistant → monitoring profiles) | Phase 11D |
| Audio briefings (TTS flash briefing) | Phase 11E |
| Business Optimization workflow (top-down strategic) | Phase 12 |
| KPI Assistant UI | Phase 12 |
| Slack notifications | Phase 12 |
| Authentication (Supabase Auth) | Infra B |
| Multi-tenant isolation | Infra B |

### Known tech debt (remaining)

| Item | Notes |
|------|-------|
| `situations` table partially redundant with `kpi_assessments` | Deprecation deferred — used by VA pipeline. Consolidate in Phase 11A. |
| `kpisScanned={14}` hardcoded in `DecisionStudio.tsx` | Wire real count from assessment API in Phase 11C |
| Separate `OpportunitySignal` / `Situation` models | Unify in Phase 11C |
| Client dropdown on SA Console | Move to login screen in Phase 10 |
| `run_enterprise_assessment.py` has no scheduler | CLI only — scheduler deferred |

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

## Forward Plan

### Phase 10: Brand Identity & UI Polish

**Goal:** Decision Studio looks and feels like a professional product. Current UI is functional but visually inconsistent with the Swiss Style brand guidelines.

**Priority:** High — needed before any external demo or outreach.

#### 10A: Decision Studio App UI

| Deliverable | Description |
|------------|-------------|
**Design principles (Quiet Expert / Swiss Style):**
- Monochrome dominance — deep slate backgrounds, semantic color used sparingly (1px left-border only on situation cards: red=variance, amber=watch, green=growth)
- No decorative animation — CouncilDebate uses monospace timestamp logs and clean progress bars, not theatric loading states
- Factual tone — "15 KPIs evaluated. 3 findings require attention." No exclamation points
- Transparency tier badges on chat responses — `[Organizational Knowledge Required]` etc. (quiet gray, builds trust by showing AI knows its limits)
- Aperture `BrandLogo` component built once, used across Login, DelegatePage, ActionHandler, ExecutiveBriefing, and landing page hero

| Deliverable | Description |
|------------|-------------|
| `BrandLogo` component | Implement Aperture logo mark (currently empty 1-line file). Shared across all surfaces. Drop into LandingPage hero as a free win once built. |
| Swiss Style design system | Satoshi font loaded globally (index.html). Semantic color tokens. Monochrome base. |
| KPI tile — visual refresh | Deep slate card, 1px left-border severity indicator only (no Christmas tree colors). Factual summary bar copy. |
| KPI tile — variance bar chart | Replace sparkline with variance/delta bars (actual − comparison). Red=below, green=above. No axes. Comparison type badge (vs Prior Year / vs Budget / vs Forecast) substitutes for axis label. Period window controlled by inline selector (see below). **Not yet rendered** — requires Phase 10C `get_kpi_monthly_series` to return `monthly_values`. Frontend component is spec'd and ready. |
| KPI tile — inline period selector | Small text links below the bar chart: `3M · 6M · 9M · 1Y`. Plain `font-mono text-[9px]` in slate-500, selected period in slate-300. Tapping re-fetches monthly series for that window via SA scan API with `num_months` param. Replaces the global Timeframe dropdown in the header entirely — timeframe control lives with the chart, not the header. Inspired by Yahoo Finance period selector pattern. Default: 9M. |
| KPI tile — top driver subtitle | When stored DA results exist for a KPI (assessment has already run), show Top 2 IS drivers as compact subtitle text (e.g. "North Region −$2.1M · Channel Indirect −$1.4M"). Condition: only when `kpi_assessments` data available — tiles without DA results unchanged. |
| KPI tile — wire real count | Replace hardcoded `kpisScanned={14}` with real `kpi_evaluated_count` from assessment API |
| Header — remove Timeframe dropdown | Timeframe control moves to KPI tile inline selector. Header contains: BrandLogo · Principal selector · Scan Now button only. Remove orphaned SC initials circle. |
| Deep Analysis — Is/Is Not exhibit | Backend (DA agent): hard cap at Top 5 IS / Top 3 IS NOT ranked by absolute delta. Frontend: items displayed with dimension as small label (not group header) — looks like a printed McKinsey exhibit at default state. Dimension summary row (net variance + item count per dimension) with expand-to-detail on click for audit trail. No pivot/filter controls on the chart itself — Refinement Chat handles deeper exploration. |
| Transparency tier badges | Chat responses (ProblemRefinementChat, ExecutiveBriefing Q&A) display quiet gray badges per tier: `[Context Recall]` `[Data Query]` `[Contextual Judgment]` `[Org Knowledge Required]` |
| ProblemRefinementChat | Sticky footer fix — suggested responses + input always visible |
| CouncilDebate | Terminal log aesthetic — monospace timestamps, clean progress bars. Remove any animated "thinking" theatrics. |
| Solution Proposal panel | Replace passive "Consensus Reached" card with a formal Solution Proposal. Three explicit actions: **Accept** (triggers HITL approval → Value Assurance), **Challenge** (principal states objection, LLM responds inline), **Reshape** (opens light shaping pass — see below). Swiss Style: slate card, no green backgrounds, left-border accent only. |
| Solution shaping (light pass) | After council debate, principal can type constraints ("assume we can't change procurement contracts", "make Option A more conservative on timeline"). LLM applies editorial adjustments to the existing solution options — no re-running the council. If still unsatisfied, principal returns to Deep Analysis problem refinement with different inputs. New `SolutionRefinementChat` component + lightweight backend endpoint. |
| ExecutiveBriefing — print CSS fix | **Critical:** Accordion `hidden` class uses `display:none !important` which defeats `print:block`. Fix with `@media print` override so all sections render in print output. Currently only 1 page prints instead of the full document. |
| ExecutiveBriefing page | Brand refresh. Section hierarchy: New Situations → Urgency → Solutions → Managed. Print CSS alignment. |
| Trajectory chart | Dark background. Dotted red line = Cost of Inaction. Solid slate = Expected. Crisp white/green = Actual. Pure Swiss geometry. |
| DelegatePage + ActionHandler | Aperture mark, visual consistency on token-action pages (email-linked flows) |
| Login | Remove "Agent9" from heading. Aperture mark. |
| Client selector → login screen | Remove client dropdown from SA Console header — already on Login |
| Remove debug artifacts | `console.log` statements, hardcoded counts, placeholder text |
| Dead code removal | Delete `VarianceDrawer.tsx`, `RidgelineScanner.tsx`, `SnowflakeScanner.tsx` — not imported anywhere |

#### 10B: PIB Email Template Refresh

| Deliverable | Description |
|------------|-------------|
| Swiss Style email | Monochrome base, Aperture logo mark, Satoshi or system font stack |
| Section hierarchy | Clear visual weight: New Situations → Urgency → Solutions → Managed |
| Top driver rows per situation | For each situation block, list Top 3 IS drivers as compact table rows: dimension · segment · delta. Always available (DA runs before PIB in assessment pipeline). Supplements prose SCQA summary — does not replace it. |
| CTA copy | Measured language throughout — "Request a Conversation", "View the Analysis". No exclamation points. |
| Mobile-safe layout | Tested on Gmail mobile + desktop |
| Executive Debrief print format | Full monochrome print document: Aperture mark + "Decision Studio" header, situation ID + date. Monochrome metadata strip (Financial Impact / Urgency / Confidence as slate labels, no red/amber/blue text). Recommended option as left-border callout not green box. Arguments For/Against in slate, not green/red text. Risk table clean. Footer: "This briefing was generated by Decision Studio using AI-assisted analysis." |
| Flash Briefing block | 3–5 sentence audio-ready summary at top of printed debrief. Structured for offline consumption and future TTS delivery (Phase 11E, on hold for MVP). Assembled from existing SCQA + recommendation fields — no new LLM call required. |

#### 10B-DGA: Data Governance Agent — Mandatory Wiring

**Goal:** Eliminate the 16 fallback paths that allow agents to bypass the DGA. The DGA methods for view resolution, KPI→data-product mapping, and business term translation are fully implemented but optional everywhere. This phase makes them the primary execution path — a required prerequisite before adding new data connectors in 10C.

**Why now (before 10C):** Every new connector (Snowflake, Databricks, SAP HANA) creates additional KPI→data-product resolution paths. Wiring the DGA first means new connectors inherit governance automatically rather than adding more fallback surface area.

**Three-phase delivery within 10B-DGA:**

| Sub-phase | Deliverables | Effort |
|-----------|-------------|--------|
| **DGA-A: Wire existing methods** | Make DGA calls mandatory in SA agent + DPA `connect()`. Replace all `if self.data_governance_agent:` guards with direct calls + proper error propagation. Wire `get_view_name_for_kpi()` as primary in DPA. Wire `map_kpis_to_data_products()` into `detect_situations` path. Remove contract-file view name fallbacks. | ~27–39h |
| **DGA-B: Real client/tenant access control** | Implement real policy logic in `validate_data_access()` (currently always-true stub). Replace manual `client_id` filtering in SA agent `_get_relevant_kpis()` with DGA access control call. Add client_id scoping to `map_kpis_to_data_products()`. Structurally prevents cross-client KPI contamination. | ~12–16h |
| **DGA-C: Registry hardening** | Fix Supabase initialization sequencing so the YAML contract file fallback never triggers in production. Supabase becomes the sole source of truth; contract file kept for local dev only. | ~20–30h |

**Current fallback inventory (16 paths across 3 files):**

| Tier | Paths | Files affected | DGA methods (already implemented) |
|------|-------|---------------|-----------------------------------|
| Tier 2 — Core mapping/view | 4 | SA agent, DA agent, DPA | `map_kpis_to_data_products()`, `get_view_name_for_kpi()` |
| Tier 3 — Translation | 5 | SA agent, DPA | `translate_business_terms()`, `get_view_name_for_kpi()` |
| Tier 1 — Client scoping | 2 | SA agent | `validate_data_access()` (needs real implementation) |
| Tier 4 — Structural/registry | 5 | SA agent, DPA | Registry init sequencing |

**Critical files:**
- `src/agents/new/a9_situation_awareness_agent.py` — 8 fallback paths
- `src/agents/new/a9_data_product_agent.py` — 5 fallback paths
- `src/agents/new/a9_deep_analysis_agent.py` — 1 fallback path
- `src/agents/new/a9_data_governance_agent.py` — DGA implementation (methods ready)
- `docs/architecture/data_governance_agent_connection.md` — documents known missing wiring

**Key insight:** DGA-A (wiring, ~27–39h) delivers 9 of 16 fallback eliminations using only code that already exists. DGA-B adds access control correctness. DGA-C is infrastructure hardening. Each sub-phase is independently deployable.

---

#### 10C: Multi-Tenant Data Connectivity (MCP-First Architecture)

**Goal:** Any enterprise client can connect their existing data warehouse to Decision Studio without custom integration work. MCP-first architecture means vendor-maintained servers handle connectivity; Decision Studio maintains only connection profiles and a thin SQL dialect layer.

**Why now:** The current implementation supports BigQuery and DuckDB only. The target ICP (mid-market enterprise, $200M–$2B) predominantly runs Snowflake, SAP HANA, or Databricks. Without this, the first non-BigQuery prospect stalls at "can you connect to our data?" Fixing this before the first pilot demo removes the objection permanently.

**Architecture decisions (non-negotiable):**
- MCP for external warehouses — vendor servers handle connection, auth, pooling. Decision Studio never holds raw credentials.
- Direct SDK for BigQuery — mature SDK, no MCP server needed yet
- Embedded DuckDB — local/demo data, no external connection
- `QueryDialect` layer (~50 lines per dialect) handles only SQL date/time function syntax differences — it is NOT a connector
- SA agent calls `data_product_agent.get_kpi_monthly_series()` — no backend knowledge in SA agent
- Connection profiles carry `connectivity_type` + `mcp_endpoint` + `source_system` — no `.env` changes per client

**Reference:** `docs/prd/agents/a9_data_product_agent_prd.md` — fully updated for this architecture

| Deliverable | Description |
|------------|-------------|
| `src/database/dialects/` module | `QueryDialect` base class + `BigQueryDialect`, `DuckDBDialect`, `SnowflakeDialect` (stub), `DatabricksDialect` (stub), `HanaDialect` (stub), `PostgresDialect`. Each dialect implements `monthly_series_sql(base_sql, date_col, num_months)` and `date_trunc_expr(col, period)`. |
| Connection profile schema update | Add `connectivity_type` (mcp/direct_bq/direct_duckdb), `mcp_endpoint`, `mcp_auth_type`, `mcp_api_key_env`, `source_system` fields. Existing profiles default to `direct_bq` or `direct_duckdb` — no breaking changes. |
| DPA execution router | `execute_sql()` routes: `mcp` → HTTP POST to `mcp_endpoint`; `direct_bq` → existing BigQuery SDK; `direct_duckdb` → existing DuckDB. Router reads `connectivity_type` from connection profile. |
| `get_kpi_monthly_series()` in DPA | Backend-agnostic public method. Resolves dialect from connection profile, builds SQL via dialect, executes via router, normalises to `[{period: YYYY-MM, value: float}]`. Replaces inline monthly series code in SA agent. |
| Remove `_bq_monthly_series_sql` from SA | Dead code once DPA method is live. SA agent calls `data_product_agent.get_kpi_monthly_series()` only. |
| KPI tile variance bars (frontend) | Unblocked by `get_kpi_monthly_series` — `monthly_values` now populated for all backends. 9-period delta bars render in KPI tiles. |
| MCP client utility | `src/database/mcp_client.py` — thin HTTP client for MCP execute-sql calls. Standard `requests`/`httpx` POST with auth header injection from env var. No vendor SDK dependency. |

**Connector rollout sequence:**
1. BigQuery + DuckDB — live in Phase 10C (already work via SDK; dialect wrappers added)
2. Snowflake — stub dialect in 10C; live when first Snowflake client onboards (activate Cortex MCP server on their instance)
3. Databricks — stub dialect in 10C; live when first Databricks client onboards
4. SAP HANA / Datasphere — stub dialect in 10C; live when first SAP client onboards (strong ICP fit given consulting background)
5. Postgres — stub dialect in 10C; useful for test environments and Supabase direct

#### 10D: Solution Finder Agent Performance Tuning

**Goal:** Reduce Solution Finder latency from 5+ minutes per debate to <2 minutes by optimizing API payload sizes and model routing.

**Current bottleneck:** Stage 2 (cross-review) and Stage 3 (synthesis) each take 174–250 seconds. Root cause: `prior_transcript` from Stage 1 containing full analysis context (12,034 tokens) is re-sent to Claude Sonnet for each subsequent stage, adding massive token overhead per call.

**Target:** 30–60 seconds per stage (4–5× speedup).

| Deliverable | Description | Expected impact |
|------------|-------------|-----------------|
| Trim prior_transcript for Stage 2/3 | Stage 1 collects full context; Stages 2–4 should send only summary of Stage 1 hypotheses (firm, conviction, key points) rather than full debate history. Estimated reduction: 12K → 3–4K tokens per stage. | 4–5× token reduction; target 30–60s per stage |
| Skip re-sending deep_analysis_payload | Stages 2–4 currently re-receive full DA Is/Is Not context. Pass only DA run ID + summary instead; DPA agent can fetch full context if needed. | 2–3K additional token savings |
| Evaluate Haiku for cross-review and synthesis | Profile Stage 2–3 with `claude-haiku-4-5-20251001` vs current Sonnet. If quality acceptable, potential 10–15s per stage gain. Stage 1 already uses Haiku; synthesis is the quality gate (humans see it). Preserve Sonnet for synthesis, use Haiku for Stage 2 only as experiment. | 10–15s per stage if acceptable; risk: reduced synthesis quality |
| Add SF performance instrumentation | Log elapsed time per stage + input/output token counts. Dashboard metric: median latency per stage. Baseline: Stage 1=26s, Stage 2=174s, Stage 3=250s. | Observable before/after comparison |
| Implement Option 1 first | Trim prior_transcript is lowest-risk, highest-impact. Deploy to production. Measure Stage 2/3 latency improvement. If <90s target met, defer Options 2–3. If >90s still, proceed to Option 2. | Empirical guidance on whether Options 2/3 needed |

**Implementation approach:**
1. (Week 1) Add logging instrumentation to SF agent; baseline current latencies
2. (Week 2) Implement Option 1 (trim prior_transcript) — modify `_run_solution_debate()` to pass summary instead of full history to synthesis API call
3. (Week 3) Test + deploy; measure improvement
4. (Week 4) If still slow, implement Option 2 (skip DA re-send) and profile Haiku vs Sonnet for Stage 2

**Files affected:**
- `src/agents/new/a9_solution_finder_agent.py` — transcript trimming logic in `_run_solution_debate()`
- `src/database/instrumentation.py` (new) or logging in SF agent — add timestamp + token tracking

---

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

---

## Infrastructure

### Infra A: Production Deployment ✅ COMPLETE (Mar 2026)

- Backend: Railway (Docker/FastAPI)
- Frontend: Vercel (Vite/React)
- Database: Supabase Cloud (Postgres)
- Analytics: BigQuery (GCP credentials via env var)
- GCP credentials materialized from `GCP_SERVICE_ACCOUNT_JSON` at startup
- Bicycle/FI DuckDB data not available in production — lubricants BigQuery works

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
