# Agent9-HERMES — Development History (shipped work)

**Generated:** 2026-09-17 — extracted verbatim from DEVELOPMENT_PLAN.md (5,734 lines) during the plan restructure.

Every phase here is **shipped and verified present in the tree**. Kept verbatim for the reasoning and post-mortems, which are often the valuable part. Nothing here is open work.

---
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

**🏁 apex_lubricants `customer_rank` bug found and fixed (2026-08-15).** Re-running `scripts/validate_client_kpis.py` live (never trust a 5-day-old written record) turned up a new, previously undocumented error: `top3_customer_revenue_share`'s `sql_query` referenced `customer_rank` — not a stored column anywhere in `LubricantsStarSchemaView` (confirmed by reading the full `CREATE VIEW` in `scripts/load_lubricants_to_snowflake.py`), and never computed via `RANK()`/`ROW_NUMBER()` anywhere in the codebase. The KPI was authored assuming a pre-materialized ranking column that was never built — a genuine authoring bug, not a schema drift. Fixed in `scripts/clients/apex_lubricants.py` by rewriting the query as a two-CTE window-function computation (rank customers by summed revenue, then sum the top 3) — standard ANSI SQL, no schema change needed. Verified live: apex_lubricants now **16/16 clean** (was 15/16). **Synced to production 2026-08-30** as part of the Phase 16 production sync's full `onboard_client.py --env production` pass for this client — confirmed by direct query against the production `kpis` table.

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

#### Status as of 2026-08-30 (end of day) — all 6 steps done; phase complete

Everything below that shipped in steps 1–4, plus O3 and the `discovery_only` fix, is **synced to
production** as of 2026-08-30: 4 migrations applied directly to the production `data_products`
table (`dimension_semantics`, `measure_semantics`, `column_aliases`, `dimension_hierarchies`
columns, confirmed present via direct query), all 11 commits merged to `master` (auto-deployed to
Railway + Cloudflare Pages, confirmed live — backend `/healthz` responds `200`, the deployed
frontend bundle contains the `discovery_only` fix), and registry data re-synced to production for
all 4 seeded clients (`onboard_client.py --env production`, confirmed via direct query: every
field lands where expected, Hess's 5 corrected KPIs read clean against the negation validator on
the production row itself, apex_lubricants' `customer_rank` fix and `top3_customer_revenue_share`
are both live).

**What this phase closes out, concretely:** steps 1–4 done and live; O3
(`dimension_semantics` from onboarding) done and live; the `temp_discovery` junk-row bug (found
during this phase's own O6 live-testing) root-caused, fixed, and deployed — checked production
directly, zero junk rows present. **O2 (`measure_semantics` detection + human confirmation) added
after this callout was first written** — both halves now done: detection live-verified against
hess's real SQL Server data (exact match to the manually-declared convention), and a required
confirmation card in the wizard UI, also live-verified end to end (screenshot captured). 21 new
unit tests across both pieces. **Still local Supabase only, not yet synced to production** — see
its own write-up below for the full detail.

**Update, later the same day (2026-08-30) — steps 5 and 6 also done.** The paragraph above was
accurate when first written; superseded within the same session. `exposed_columns` was migrated,
`dimension_semantics` was backfilled for apex_lubricants/bicycle (and hess, which turned out to
be missing it too), every confirmed-dead `yaml.safe_load` call site was deleted, DA's/DPA's
remaining YAML fallback branches were confirmed unreachable for every real client and deleted,
the 8 legacy contract YAML files were deleted from disk, and step 6's architecture test now bans
`yaml.safe_load(` in `src/agents/**` going forward. See the Step 5 subsection below for the full
detail — this phase's YAML → registry migration is complete. **Still open, not part of this
phase's scope:** O5's completeness gate (depends on O2 meaning something first — separate
Onboarding work, not blocked on anything closed here); `dp_lubricants_sales`'s empty registry
fields (pre-existing, unaffected by this cleanup — see the Step 5 subsection).

**Follow-up surfaced during this phase's production sync, unrelated to data product contracts —
tracked here rather than lost:** the backend has no real custom domain (`api.decision-studios.com`
doesn't resolve; the deployed app is only reachable at Railway's raw
`agent9-hermes-production.up.railway.app`). `trydecisionstudio.com`/`api.trydecisionstudio.com`
(what `.env.production` used to point at) turned out to be a dormant, unrelated Squarespace
placeholder — both `.env.production` files have been corrected to the real Railway URL in the
meantime. Setting up the actual custom domain is Railway dashboard + DNS work outside what can be
done from this environment — needs `decision-studios.com`'s DNS provider (Cloudflare, presumably,
given the frontend is already on Cloudflare Pages) plus a matching custom-domain entry in Railway.

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

#### Re-verified against the live registry, not the Hess fixture (2026-08-29)

A fair challenge surfaced that the finding above might be a Hess-specific test-onboarding artifact rather than a live production issue, since Hess is an explicitly-out-of-scope-for-realism connectivity proof (see the Open Questions section below). Checked directly against Supabase and the actual code path for the real production client, not just re-read the doc:

- **Confirmed NOT an artifact — `_dims_from_contract` (`a9_deep_analysis_agent.py:387`) has no Supabase fallback at all.** It calls `yaml.safe_load()` on a file path resolved by `_contract_path_for_kpi`, which does a tenant-scoped Supabase lookup only to find the KPI's `data_product_id`, then globs a local directory of YAML files on disk for a matching one. Supabase is never consulted for the contract *content*.
- **Confirmed the shape collision on the live client, not just Hess.** `GET /registry/data-products?client_id=lubricants` returns a real `views` field for `dp_lubricants_financials` — but it holds `{name, description, sql_definition, depends_on}`, structurally incapable of carrying `dimension_semantics` even if the code tried to read it from there. The split-store problem is confirmed live on the flagship client, not a Hess-only artifact.
- **New finding — `measure_semantics` has a head start nobody's cashed in.** The live `metadata` field on `dp_lubricants_financials` already carries `sign_convention: "signed"`, `negative_account_types: ["COGS", "SGA", "Other"]`, `positive_account_types: ["Revenue"]` — the same concept step 2 below proposes building from scratch, seeded by `scripts/clients/lubricants.py`. Checked consumption: **zero agent code in `src/` reads either field back.** Only the seed script writes it. So step 2's data model doesn't need to be invented from nothing for lubricants — the seeded convention already exists there; what's missing is the validator/enforcement side that would read and check against it, and a decision on whether to keep the existing `negative_account_types`/`positive_account_types` naming or move to the `stored_sign: {...}` shape proposed below. **Checked whether other clients carry the same fields — they don't:** `scripts/clients/apex_lubricants.py` and `scripts/clients/hess.py` have neither field. Lubricants is the only client with this convention seeded at all, which is consistent with Hess's KPI SQL having no declared convention to check against when its signs were hand-written wrong.

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

Roughly a third of Hess's KPI set is unusable: 3 wrong, 5 NULL, 1 impossible (`return_on_capital`,
which the negation validator built in step 2 subsequently attributed to the same sign bug — see
below). **Update (step 2, 2026-08-29):** the negation validator found 2 more mis-signed KPIs the
manual audit missed — `ebitda` and `return_on_capital` — bringing the real count to 5 wrong, 5
NULL. **Fixed (step 3, 2026-08-29 — see below):** all 5 mis-signed KPIs corrected and
re-validated live. The 5 NULL KPIs are untouched, deliberately — they reference `CapEx`/
`OperatingCF` account types that don't exist in this dataset at all, a different, lower-priority
problem the plan's Open Questions section already scoped as "can stay or go."

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
| `time_dimensions` | ~~DPA falls back to `{"type": "date", "column": "transaction_date"}`. **Three of four seeded clients use `fiscal_year_period`** — a wizard-onboarded fiscal dataset gets the wrong filter shape and silently returns wrong windows~~ **CORRECTED (2026-08-30, live-verified):** this claim was wrong. `register_data_product`'s `_synthesize_time_dimensions` genuinely infers the correct `fiscal_year_period` shape (`year_column=fiscal_year`, `period_column=fiscal_period`) from the live schema at onboarding time — confirmed by actually running the wizard against hess's real SQL Server database (`dp_hess_financials_test`, a throwaway registration, deleted after inspection) and reading back what Supabase stored. `time_dimensions` is NOT one of the wizard's gaps; O1 (below) can be marked resolved for the detection half of its scope |
| `views[].llm_profile.dimension_semantics` | `_dims_from_contract` returns `[]`, so Deep Analysis has no dimensions to analyse and falls back to the KPI registry — or, historically, to the bicycle default contract |
| `measure_semantics` (proposed) | KPI SQL is hand-written per client with the sign convention assumed. This is exactly how Hess's three KPIs came to add cost to revenue |

Counts across the onboarding models and routes: `dimension_semantic` 0, `sign_convention` 0, `measure_semantic` 0, `account_type` 0, `fiscal` 0, `time_dimension` 1.

**The wizard's 5 steps** (Connection → Schema Discovery → Data Product Selection → Metadata Analysis → KPI Definition) collect schema and KPIs, and nothing about how time or measures behave. Those are not schema facts — no column type reveals that `amount` is negative for COGS, or that `fiscal_period` is a period rather than a date.

**Consequence to state plainly:** a data product onboarded through the current wizard produces contracts that are *structurally incomplete for the pipeline they feed*. It looks successful — the steps pass, the product registers — and the failure appears later as an empty Is/Is-Not, a wrong comparison window, or an inverted KPI. Every failure mode found this week, arriving by the front door.

**`contract_yaml` is a carrier, not a file.** `generate_contract_yaml` explicitly does not persist to disk ("Supabase is the canonical registry backend"), so the wizard is not writing the 12 files found on disk. But it serialises to YAML text and passes `contract_yaml: str` between steps, which keeps the YAML shape as the wizard's working model and makes the registry record a lossy projection of it.

##### Onboarding work implied by this phase

| # | Work | Note |
|---|---|---|
| **O1** | 🟡 **Detection half DONE, live-verified 2026-08-30** — `register_data_product` already emits a correct `fiscal_year_period` shape without any wizard UI change. **Confirmation-by-the-user half NOT done** — the wizard never shows what it inferred or asks the admin to confirm it; a wrong inference (e.g. two similarly-named columns) would still ship silently | Detection is a reasonable default (a `fiscal_year` + `fiscal_period` column pair is a strong signal), but it must be **confirmed**, not assumed; the cost of getting it wrong is silent wrong windows |
| **O2** | ✅ **DONE, live-verified 2026-08-30** (local Supabase). Detection + a required human-confirmation UI card, both closed the same day — the admin sees the detected convention (editable per value) and must confirm before the wizard advances | Detectable by inspection: if every COGS row is negative, propose "negative" and ask. One question, once, replacing a per-KPI assumption |
| **O3** | ✅ **`dimension_semantics` half DONE, live-verified 2026-08-30** (local Supabase). `register_data_product` now writes `dimension_semantics` from already-profiled `semantic_tags`, mirroring `_synthesize_time_dimensions`'s structure. `fallback_group_by_dimensions` still NOT emitted by the wizard (unrelated field, seed-data-only per step 1) | The candidate analysis dimensions. Related to Phase 15 Stage I's problem-profile-driven selection — the wizard should propose, the profile should rank |
| **O4** | Replace `contract_yaml: str` with the typed contract object | Removes the last reason for the wizard to think in YAML at all |
| **O5** | Completeness gate before "register" | Refuse to register a data product missing time semantics or measure semantics. **The onboarding wizard is where a bad contract is cheapest to stop**; every other guard in this plan catches it downstream, after it has already produced a number |
| **O6** | Re-onboard one existing client through the fixed wizard | The only real proof. If lubricants cannot be reproduced through the UI, the wizard still cannot express a working contract |

**Ordering:** O1–O3 depend on the registry record gaining those fields (Phase 16 steps 1–2), so the wizard has somewhere to write them. O5 depends on O1–O3 existing to check. O6 is the acceptance test for the whole phase.

**O6 run in miniature, live-verified (2026-08-30).** Drove the real Admin Console wizard
(`DataProductOnboardingNew.tsx`, via Playwright — `decision-studio-ui/tests/e2e/
live-onboarding-hess-test.spec.ts`) against hess's actual SQL Server database, registering a
throwaway data product (`dp_hess_financials_test`, deleted after inspection) rather than
touching the real `dp_hess_financials` record. Confirms the O1–O3 gap empirically, not just by
reading `_build_contract_dict`/`register_data_product`'s code:

| Field | Wizard-registered | Real seeded record |
|---|---|---|
| `dimension_semantics` | `[]` | `None` (not yet migrated for hess either — Phase 16 step 1 scope, unrelated to the wizard) |
| `measure_semantics` | `None` | `{stored_sign, type_column, amount_column}` (step 2) |
| `column_aliases` | `None` | `{measure, date, version, default_version_value}` (step 4) |
| `dimension_hierarchies` | `{}` | `{geography, segment, financials}` (step 5) |
| `time_dimensions` | **correctly synthesized** — `fiscal_year_period`, right year/period columns | same shape, manually seeded |
| `views` | **real `CREATE VIEW` SQL introspected from SQL Server**, correctly capturing the segment/basin CASE-mapping logic | `{}` (not stored this way in the seed) |

Two results, not one: this reconfirms the O1–O3 gap (dimension_semantics/measure_semantics/
column_aliases/dimension_hierarchies stay permanently unwritable through the wizard, exactly as
`register_data_product`'s `DataProduct(...)` constructor — `a9_data_product_agent.py:857-874` —
predicts by never passing them), **and** it corrects a stale claim the original finding made
about `time_dimensions` (struck through above) — the wizard already gets that one right via
`_synthesize_time_dimensions`, discovered only by actually running it rather than trusting the
2026-08-10 audit's characterization. Neither result was assumed; both came from reading back what
Supabase actually stored after a real onboarding run.

**O3 (`dimension_semantics` half) closed the same day, synced to production 2026-08-30.** The raw material already
existed — schema profiling already tags every column `'dimension'`/`'measure'`/`'identifier'`/
`'time'` via `_infer_semantic_tags`, and the frontend already reads it back for
`KPIAssistantChat`'s `schemaMetadata.dimensions` — it just was never written to
`DataProduct.dimension_semantics` at registration. New `_synthesize_dimension_semantics(tables)`
mirrors `_synthesize_time_dimensions`'s exact structure (FACT-table-first precedence, profiled
order preserved, no re-ranking) and is now wired into `register_data_product`. Deliberately does
**not** duplicate `A9_Deep_Analysis_Agent._keep_contract_dim`'s ban-list (flags, `_id`, `version`,
`transaction_date`, ...) — that filter already runs uniformly at read time regardless of source,
so this only needs to hand it the raw candidate list. Re-ran the same live wizard test against
hess (`live-onboarding-hess-test.spec.ts`): `dimension_semantics` now populates with
`["version", "currency", "account_name", "account_type", "account_category", "segment_name",
"basin_name", "asset_name", "country", "region", "business_unit"]` — closely matching hess's own
manually-seeded list; `version` gets correctly stripped by DA's ban-list at read time,
`fiscal_year`/`fiscal_period` are correctly absent (tagged `'time'`, not `'dimension'`). 8 new/
extended unit tests in `tests/unit/test_data_product_agent_schema_generation.py`. 1449 unit tests
pass (1443 + 6 new — 2 of the 8 extend an existing test rather than add a new one).

**A separate, pre-existing bug found in the same investigation — FIXED same day (2026-08-30,
local Supabase).** Every "Schema Discovery" wizard step calls `orchestrate_data_product_onboarding`
unconditionally with `data_product_id='temp_discovery'`, which called `register_data_product`
unconditionally — meaning a junk `temp_discovery` data product got registered into Supabase for
whichever client was targeted, on every discovery run. Found two stray rows this way
(`brookshire_brothers` from 2026-07-24 — this had been happening in production-shaped local data
for over a month before anyone noticed; `hess` from this session's own live testing); both
deleted directly. **This is the same bug already named, unsolved, in the Settings → Data Products
UI audit** ("`temp_discovery` record is a discovery artifact leaking into production data" — see
the UI polish backlog below) — that entry recommended "root cause better" over a cosmetic filter,
which is what this fix does. New `discovery_only: bool` flag on
`DataProductOnboardingWorkflowRequest`, threaded from the wizard's `handleSchemaDiscovery` call;
`orchestrate_data_product_onboarding` skips `register_data_product` (and everything gated on it)
entirely when set, defaulting to `False` so every other caller keeps registering exactly as
before. Verified live: re-ran the same wizard test against hess after the fix — no `temp_discovery`
row appears, and the real registration at the "Metadata Analysis" step still succeeds and still
writes `dimension_semantics` correctly. 4 new unit tests in
`tests/unit/test_orchestrator_data_product_onboarding.py`. 1453 unit tests pass (1449 + 4 new).

**Not yet done (at the time this was written):** `fallback_group_by_dimensions` (O3's other
half — a different field, seed-data only, unrelated to this fix); O2 (`measure_semantics`) —
see below, closed the same day. The two production rows referenced in the UI backlog's items
3/10 turned out to already be gone when checked directly (see the phase-wide status note after
the Goal section) — no further cleanup needed there.

**O2 (`measure_semantics` detection) closed the same day, 2026-08-30 — the piece that actually
would have caught Hess's sign bug at onboarding time.** Unlike O1/O3, which are pure functions
over already-profiled column *metadata*, sign convention is a fact about the *data* — genuinely
needed a live query, not just a smarter read of what profiling already collected.

New `_pick_sign_detection_columns(profile)`: identifies an `(type_column, amount_column)` pair
to check, or `None`. Deliberately narrow — only fires when a column's name plausibly means
"account type" (`'accounttype'` as a substring once underscores/spaces are stripped); a generic
categorical column (`product_category`, `channel_type`) is **not** a safe guess, since sign
convention is a finance-domain concept specific to account classification. New
`_detect_measure_sign(...)`: runs `SELECT type_column, SUM(amount_column) GROUP BY type_column`
against the live source during profiling (one dialect branch per backend, same shape as the
existing `_sample_distinct_values`), deriving `"negative"`/`"positive"` per distinct value. **A
value whose total is exactly zero is dropped, never guessed** — genuine ambiguity must not
become a fabricated convention. Wired into the same profiling call site as the existing
categorical-sample-value population (`_profile_table`, where a live manager connection already
exists), and a new `_synthesize_measure_semantics(tables)` in `register_data_product` promotes
the detected result — mirroring `_synthesize_dimension_semantics`'s FACT-table-first precedence,
but returning a single dict or `None` (a data product has one sign convention, not several to
merge).

**Verified live against hess's real SQL Server database**, not assumed: re-ran
`live-onboarding-hess-test.spec.ts` (throwaway `dp_hess_financials_test` registration, deleted
after inspection) and got `{"Revenue": "positive", "COGS": "negative", "SGA": "negative",
"Other": "negative"}` — an **exact match** to the convention this session's earlier steps 2/3
declared by hand and used to fix Hess's actual KPI bugs. That match is strong, independent
confirmation the detection logic is correct, not merely plausible-looking. 17 new unit tests in
`tests/unit/test_data_product_agent_schema_generation.py`. 1468 unit tests pass (1453 + 15 net
new — 2 of the 17 extend existing tests rather than add new ones).

**Human confirmation closed the same day, 2026-08-30** — flagged as a real, higher-than-O1/O3
gap, and closed rather than left as an accepted risk once raised. For `time_dimensions`/
`dimension_semantics`, a wrong detection degrades *analysis quality* (dimensions ranked oddly, a
fiscal window slightly off). For `measure_semantics`, a wrong detection reproduces the Hess bug
class exactly — a KPI silently computing backwards, correctness rather than quality — so
"detection is conservative" wasn't treated as good enough on its own.

New `confirm_measure_semantics` agent method + `POST /data-product-onboarding/confirm-measure-
semantics` route: fetches the already-registered `DataProduct`, validates `client_id` ownership
(fail-loud, same pattern as `sync_related_business_processes`), overwrites `.measure_semantics`
with whatever the admin actually approved, upserts. Frontend: Metadata Analysis now extracts the
detected convention from the same workflow response that already carries the inspection result,
and — only when non-empty — renders a **required** confirmation card in place of advancing
straight to KPI Definition: each `stored_sign` value as an editable positive/negative dropdown,
a "Confirm Sign Convention & Continue" button that POSTs the (possibly corrected) value before
advancing. Nothing detected → no gate, wizard behaves exactly as before.

**Live-verified end to end**, not just unit-tested: re-ran `live-onboarding-hess-test.spec.ts`
against hess's real SQL Server database — the confirmation card rendered showing `COGS`/`SGA`/
`Other`=negative, `Revenue`=positive (screenshot captured), confirming as-detected persisted
that exact value through the new endpoint. 4 new unit tests (persists the confirmed value, an
admin's correction overrides the original detection — the actual point of the endpoint —
client_id-mismatch rejection, not-found returns an error rather than raising). No React/TSX test
suite exists in this codebase (no jest/vitest configured); the UI side is covered by the live
Playwright run, not a unit test. 1472 unit tests pass (1468 + 4 new).

This is also the concrete prerequisite O5's completeness gate ("refuse to register a data
product missing `measure_semantics`") needed to mean anything: gating on a value nobody has
looked at would not have been the protection O5 was designed to provide. O5 itself is still not
built.

**Not yet done:** O5's completeness gate itself; `fallback_group_by_dimensions`; synced to
production (local Supabase only as of this writing).

**Relationship to the existing Data Onboarding Refinement track** (below): that track is UI and workflow polish — chooser screen, wizard foundation, templates. This is a *content* gap in what the wizard produces, and it should be sequenced ahead of the polish. A better-looking wizard that still emits an incomplete contract is a faster way to a wrong briefing.

**Reframes the "1-day onboarding" claim.** The wizard completing is not the same as a usable data product. Until O5 exists, "onboarded" means the steps passed — not that the pipeline can analyse it correctly.

---

#### Sequence (order matters)

| # | Work | Why in this order |
|---|---|---|
| **1** | ✅ **DONE (2026-08-29, lubricants; synced to production 2026-08-30).** Moved `dimension_semantics` + `fallback_group_by_dimensions` onto the registry record; repointed `_dims_from_contract` | The only live contract read. Also the fix for the **hardcoded dimension preference list** in Phase 15 Stage I — that literal was already deleted (Aug 2026), so this step is now purely the store migration |
| **2** | ✅ **DONE (2026-08-29, all three financial data products; synced to production 2026-08-30).** Added `measure_semantics` + the negation validator | Sign convention and dimensions then come from one place |
| **3** | ✅ **DONE (2026-08-29, synced to production 2026-08-30).** Corrected all 5 Hess KPIs against the declared convention; re-validated live | Fixes real wrong output, now expressed as data rather than code |
| **4** | ✅ **DONE (2026-08-29, synced to production 2026-08-30) — scope revised on investigation, see Step 4 subsection below.** Of the four sections, only `column_aliases` needed a new registry field; `business_terms`/`supported_business_processes` had zero live readers and already-migrated equivalents (backfilled as data, not schema); `connection` is dead and insecure, recommended for deletion at step 5 | The remaining sections; lower risk once the pattern exists |
| **5** | ✅ **DONE 2026-08-30.** Full audit of every `yaml.safe_load` call site done; `views` shape collision resolved as a decision; `dimension_hierarchies`/`dimension_semantics`/`exposed_columns` migrated for every client that declares them; every dead call site deleted (not just marked dead); DA's/DPA's remaining YAML fallback branches confirmed unreachable for every real client and deleted; the 8 legacy contract YAML files deleted from disk | Only safe once nothing reads them — confirmed live, not assumed |
| **6** | ✅ **DONE 2026-08-30.** `yaml.safe_load(` banned in `src/agents/**` via `scripts/architecture_lint.py` (pre-commit) + `tests/architecture/test_architecture_compliance.py`, both enforcing the same pattern; 2 pre-existing, out-of-scope call sites allow-listed inline (`business_context_loader.py`, `a9_llm_service_agent.py`) | Makes the rule in CLAUDE.md enforceable rather than aspirational |

**Onboarding (O1–O6 above) interleaves here:** O1–O3 land with steps 1–2, since the wizard needs somewhere to write those fields; O5's completeness gate lands with step 4; O6 — re-onboarding an existing client through the wizard — is the acceptance test for the phase.

**Do NOT do 2 before 1.** Adding `measure_semantics` to the registry while dimensions still come from disk leaves DA reading two halves of one contract from two stores — the exact shape that produced the two-baseline briefing.

**Verification for each step:** a live Deep Analysis per client per backend, checked against a direct query. Today gave three separate cases where code was correct and was not the code being executed; string tests do not close that.

---

#### Step 1 — done for lubricants, synced to production 2026-08-30

`DataProduct` gained a real `dimension_semantics: List[str]` column (migration
`20260829120000_data_products_dimension_semantics.sql`) — `DatabaseRegistryProvider`'s serialize/
deserialize path is fully generic (`model_class(**data)` on read, `model_dump()` filtered against
a live `information_schema.columns` query on write), so no hand-maintained field list needed
updating on the provider side, unlike every other registry write path touched this session.
`_dims_from_contract` (`a9_deep_analysis_agent.py`) is now registry-first: a new
`_dims_from_registry()` resolves the KPI's `data_product_id` and reads `DataProduct
.dimension_semantics`; only when that's empty does it fall back to the original YAML scan,
byte-identical to before for every not-yet-migrated client. `fallback_group_by_dimensions`
needed no schema change at all — its one real consumer (`A9_Data_Product_Agent
._collect_group_by_items`, tier 4) already reads `DataProduct.metadata['fallback_group_by_dimensions']`
directly, so the fix there was purely seeding the value.

**A fourth instance of the explicit-allow-list trap, found and fixed in the same pass:**
`onboard_client.py`'s `_DP_COLS` — a hand-maintained set of columns the seeder is willing to
write — didn't know about the new column, so seeding lubricants with `dimension_semantics`
populated in `DATA_PRODUCT` silently wrote `NULL` to the real column on the first attempt. Same
shape as `causal_direction` (twice) and `AcceptedSolution.framing_snapshot`/`target_metric`
earlier this session — a fourth independent write path in this codebase carrying the identical
failure mode. Fixed; `dimension_semantics` now upserts correctly.

**Verified live, not assumed:** local Supabase re-seeded, confirmed via direct query that
lubricants' `dimension_semantics` populated correctly and every other client
(hess/apex_lubricants/bicycle/brookshire_brothers) still has it `NULL` — the fallback path is
genuinely still exercised for them, not just believed to be. `_dims_from_contract` and
`_dims_from_registry` called directly against a real `RegistryBootstrap`-initialized registry
(no mocks) for `gross_margin_pct`/lubricants — returned the registry-sourced order correctly. 6
new unit tests (`test_da_dimension_ranking.py`) pin registry-wins-over-YAML, ban-filter still
applies to registry-sourced dims, empty-registry-falls-back-unchanged, and non-fatal degradation
on a KPI-lookup or provider failure. 1410 unit tests pass.

**Synced to production 2026-08-30** via `onboard_client.py --client lubricants --env production`,
confirmed by direct query. **Not yet done:** steps 2–6 of the
sequence above; the same treatment for hess/apex_lubricants (their `dimension_semantics` stays
YAML-sourced until each is migrated in turn).

---

#### Step 2 — done, synced to production 2026-08-30

`DataProduct` gained `measure_semantics: Optional[Dict]` (migration
`20260829130000_data_products_measure_semantics.sql`) — same "one contract fact, one place" pattern
as step 1, same generic `DatabaseRegistryProvider` serialize path, no provider changes needed.
Shape: `{type_column: "account_type", amount_column: "amount", stored_sign: {"Revenue":
"positive", "COGS": "negative", ...}}`.

**Naming collision found and documented, not walked into silently:** `llm_profile
.measure_semantics` already exists inside the legacy `contract_yaml` text (read by
`a9_data_product_agent.py` and `a9_llm_service_agent.py` for the ad-hoc NL-to-SQL path) — a
different shape entirely (`{default_measure, default_aggregation}`) serving a different
purpose. Same key name, different shape, at a different attribute path (nested in YAML text
vs. this top-level column) — never colocated, so no runtime collision, but exactly the
anti-pattern this phase's own finding calls out for `views`. Flagged in both the model
docstring and the migration comment for whoever reads this next; not renamed, since the design
doc's own wording (and every cross-reference to it — the Phase 17 T1 dependency, the sequence
table) already commits to `measure_semantics` as the name.

**The negation validator** — `src/registry/validators/measure_semantics_validator.py`,
`check_sql_sign_convention(sql_query, measure_semantics) -> List[str]`. Static regex analysis
over `CASE...END` blocks (not a SQL parser): flags a `WHEN account_type='X' THEN -amount`
branch, or an `ELSE -amount` fallthrough, when `X` is already declared negative in
`stored_sign` — the exact shape of Hess's bug. Deliberately narrow: a standalone `SELECT
SUM(-amount) WHERE account_type='COGS'` (no CASE, no sibling branch to fight) is NOT flagged —
that's a legitimate "show this cost as a positive number" KPI (apex_lubricants' `cogs`/
`sga_expense`), not a sign bug. 17 new unit tests
(`tests/unit/test_measure_semantics_validator.py`) pinned against the REAL sql_query strings
from `scripts/clients/hess.py` (all 5 known-bad KPIs) and `scripts/clients/lubricants.py`/
`apex_lubricants.py` (must-not-false-positive), not synthetic fixtures — a validator that only
passes on invented SQL proves nothing about the bug it exists to catch.

**Seeded onto all three financial data products** (lubricants/apex_lubricants/hess — not just
the migrated-for-step-1 client, since the validator needs the fact declared to check anything):
same convention on all three per the Phase 16 finding ("COGS, SGA and Other are stored negative
in HessStarSchemaView, as in BigQuery and Snowflake"). `dp_lubricants_sales` correctly left
`None` — no P&L account-type convention applies there. **A 5th instance of the explicit-allow-
list trap** found and fixed in the same pass: `onboard_client.py`'s `_DP_COLS` didn't know
about the new column either (added proactively this time, before a silent-NULL re-seed, now
that the shape is recognised from steps 1 and the four prior instances this session).

**Verified live, not assumed — and it found more than the original manual audit did:**
`scripts/validate_client_kpis.py` now runs the static check alongside its existing live-value
check. Against Hess: flags all 3 originally-audited KPIs (`gross_profit`, `gross_margin_pct`,
`operating_income`) — **plus `ebitda` and `return_on_capital`, neither of which was in the
original 2026-08-10 manual audit's 3-KPI list.** Both have the identical `ELSE -amount`
fallthrough bug (confirmed live: `return_on_capital` reports 301.63%, already flagged
`IMPOSSIBLE for a percentage` by the pre-existing check — its wrongness was known, but not
previously attributed to this cause; `ebitda`'s wrongness was not previously known at all). This
is the validator doing exactly what it was built for — "catches the next client without anyone
remembering to look" also means it catches what a human audit missed the first time. Against
Apex's full 16-KPI set (closing the plan's own open question below, "only gross_margin_pct was
validated there"): zero violations, zero live-value problems. Against lubricants' full 20-KPI
set: zero violations, zero live-value problems. 1427 unit tests pass (1410 + 17 new).

**Not yet done:** Phase 16 step 3 (actually correcting Hess's 5 now-identified KPIs against the
declared convention — deliberately not done here; step 2 is "declare the fact and build the
check," step 3 is "act on it"); synced to production; steps 4–6.

---

#### Step 3 — done, synced to production 2026-08-30

Rewrote all 5 mis-signed KPIs in `scripts/clients/hess.py` to sum the already-signed `amount`
column directly instead of re-negating a measure the contract now declares negative — the same
idiom already live and validator-clean on lubricants (`gross_profit`/`gross_margin_pct`) and
apex_lubricants (`operating_income`, and `ebitda`'s D&A-addback branch, which Hess's `ebitda`
fix now mirrors exactly rather than inventing a new shape).

| KPI | before | after fix | original manual-audit "actual" |
|---|---|---|---|
| `gross_profit` | 6,236M | **1,297M** | 1,297M ✅ exact match |
| `gross_margin_pct` | 165.57% | **34.43%** | 34.43% ✅ exact match |
| `operating_income` | 6,816M | **717M** | 717M ✅ exact match |
| `ebitda` | 6,928M | **828M** | *(not independently computed in the original audit — new)* |
| `return_on_capital` | 301.63% (impossible) | **31.71%** | *(not independently computed — now merely plausible, not verified against an outside figure)* |

The first three land on the exact figures the 2026-08-10 manual SQL walkthrough computed
independently by hand — strong confirmation the fix (and the manual audit before it) are both
right, not just "different from before." `ebitda` and `return_on_capital` have no independent
hand-computed figure to match against (they weren't in the original 3-KPI manual audit at all —
step 2 found them); both are now merely *plausible* (no longer impossible/absurd), not
externally verified to a second figure the way the other three are.

**Re-validated live via `scripts/validate_client_kpis.py`:** all 5 sign-convention violations
cleared. `16 KPI(s) checked, 5 needing attention` — the remaining 5 are the pre-existing NULL
KPIs (`lifting_cost`, `exploration_expense`, `capital_expenditure`, `operating_cash_flow`,
`free_cash_flow`), untouched by design: they reference `CapEx`/`OperatingCF` account types that
don't exist in this dataset at all, a different and lower-priority problem this step was not
scoped to fix (see Open Questions below — "can stay or go... low priority either way").

**Not independently re-checked:** the YoY *direction* claim from the original finding ("reported
margin rose +2.66pp while true margin fell 2.66pp — Situation Awareness would see improvement
and raise no alert on a declining business") was about the trend across two periods, not the
single-period value corrected here. Re-validating that the alert direction itself now flips
correctly would need a live SA scan comparing two fiscal periods, not just the current-period
values checked in this pass — a natural follow-on if a full Hess situation-awareness
verification is wanted, not done here.

1427 unit tests pass, unchanged (this step edits seed SQL text, not the validator or its tests —
the validator's own tests intentionally keep the ORIGINAL buggy SQL strings as fixtures, since
they exist to prove the validator still catches that shape, independent of what hess.py now
contains).

**Synced to production 2026-08-30** — Hess's 5 corrected KPIs re-checked against the negation
validator directly on the production row, zero violations. **Not yet done:** steps 4–6.

---

#### Step 4 — done, synced to production 2026-08-30 — scope revised on investigation

The plan assumed all four remaining sections (`business_terms`, `column_aliases`,
`supported_business_processes`, `connection`) needed the same registry-column treatment as
`dimension_semantics`/`measure_semantics`. **Checked each for a live reader before migrating
any of them** (grepped all of `src/agents/**` for every key, not assumed from the section names)
— only one of the four actually needed a new field:

| section | live readers found | action taken |
|---|---|---|
| `column_aliases` | **1** — `A9_Data_Product_Agent._get_contract_column_aliases`, called from `_generate_sql_for_kpi`'s last-resort fallback (reached only when source_system routing can't resolve a backend — none of the seeded BigQuery/Snowflake/SQL Server clients ever hit it; exists for bicycle's DuckDB) | **Migrated** — new `DataProduct.column_aliases` field, same registry-first-with-YAML-fallback pattern as step 1 |
| `business_terms` | **0** | **Not migrated — backfilled as glossary data instead** (see below) |
| `supported_business_processes` | **0** | **Not migrated — already redundant** with `DataProduct.related_business_processes`, an existing field already populated per client |
| `connection` | **0** | **Not migrated — recommended for deletion at step 5**, see the security note below |

**`column_aliases`:** new field + migration (`20260829140000_data_products_column_aliases.sql`), same
`DatabaseRegistryProvider` generic serialize path, no provider changes. Fixed a real bug while
migrating it: `_get_contract_column_aliases(data_product_id)` took the parameter but its YAML
fallback called `self._contract_path()` with **no argument**, silently ignoring it and always
resolving to the bicycle default contract — the same cross-tenant-contamination shape already
fixed once for DA's `_dims_from_contract` (step 1), found here independently by reading the
method before migrating it, not assumed correct. Fixed as part of this change; `data_product_id`
now threaded through all 5 call sites inside `_generate_sql_for_kpi` (`getattr(kpi_definition,
'data_product_id', None)`). Seeded onto all 4 data products (lubricants/apex_lubricants/hess/
bicycle) — genuinely load-bearing only for bicycle (the one client whose `source_system=duckdb`
doesn't match any of the four explicit routing branches), and likely moot even there since all
20 of bicycle's KPIs already carry a literal `sql_query`. Seeded on the other three for
consistency and so the registry is a complete substitute for the YAML once step 5 deletes it. 9
new unit tests (`tests/unit/test_dpa_column_aliases_registry.py`) pin: registry wins when
populated, empty-dict registry value correctly treated as "not migrated" (falsy, not returned
as-is), `data_product_id` genuinely reaches `_contract_path` (the bug fix), and non-fatal
degradation on a missing registry factory, a provider exception, and a missing/malformed YAML
file. `onboard_client.py`'s `_DP_COLS` gained `column_aliases` proactively (6th instance of the
allow-list trap, added before a silent-NULL re-seed this time).

**`business_terms`:** zero live readers of the YAML key anywhere, but the DATA was a genuine
content gap, not dead weight — lubricants already has an equivalent (`EXTRA_GLOSSARY_TERMS` in
`scripts/clients/lubricants.py`, seeded independently of this phase, using the already-Supabase-
backed `business_glossary_terms` table), while apex_lubricants and hess had `EXTRA_GLOSSARY_TERMS
= []` — their YAML's domain-specific dimension vocabulary (Hess: segment/basin/asset/country/
business_unit/account_type/account_category; Apex: product_line/customer_segment/channel/
profit_center/account_type/account_category) was never carried over. Backfilled both from their
respective YAML `business_terms:` sections, in the same `{id, term, definition, domain, tags,
technical_mappings}` shape lubricants already uses. This is a seed-data completeness fix using
an existing mechanism, not a schema change — no migration needed. Confirmed no overlap with
`CORE_GLOSSARY_TERMS` (the canonical, cross-client set) before adding: that set covers KPI-name
terms (revenue, margin, ebitda, cogs, sga, yoy, qoq), not dimension-column terms.

**`supported_business_processes`:** zero live readers, and the data itself is redundant —
`DataProduct.related_business_processes` (an existing field) already carries the equivalent list
for every seeded client (confirmed: hess's `related_business_processes` already covers 4 of the
YAML's 6 entries; the other 2 are process names with no corresponding seeded business_process
record at all, a separate and smaller gap not chased down here). No action needed.

**`connection`:** zero live readers anywhere in `src/agents/**` (confirmed by grep, not assumed)
— superseded by the proper `connection_profiles` mechanism (`src/config/connection_profiles.py`,
`/api/v1/connection-profiles/`, an actual registry-backed table), which is what the live backend
actually uses to reach Snowflake/SQL Server/BigQuery (see `scripts/validate_client_kpis.py`'s
env-var-driven connection functions for the pattern actually in use). **Security note, not
urgent but worth naming plainly:** `hess_financials.yaml`'s `connection:` block carries a
plaintext password (`Agent9Test!2024` — the same local-Docker-default credential already visible
elsewhere in this repo, e.g. `validate_client_kpis.py`'s `SS_PASSWORD` default, so not a secret
being newly exposed here). Recommended action: **delete this block, don't migrate it**, when the
YAML files are removed in step 5 — migrating a dead, insecure field into a new JSONB column would
be a regression dressed up as progress.

**Verified live:** re-ran `scripts/validate_client_kpis.py` against hess/apex_lubricants/
lubricants after re-seeding — identical to step 3's results (5 needing attention on hess, all 5
being the pre-existing out-of-scope NULL KPIs; 0 on apex/lubricants). 1436 unit tests pass (1427
+ 9 new).

**Synced to production 2026-08-30.** **Not yet done:** steps 5–6. Step 5 now has a clearer scope than the plan
originally assumed: delete `connection` (recommended above, not carried forward) alongside the
YAML files themselves, rather than migrating it first.

---

#### Step 5 — partial (2026-08-29), schema/data synced to production 2026-08-30: audited every reader, migrated one more, files NOT yet safe to delete

Step 5's own precondition is "only safe once nothing reads them." Before touching any deletion,
**every `yaml.safe_load` call site in the three flagged agent files was read and classified** —
14 sites, not re-derived from the original finding's summary counts. This is the audit the phase
needed before step 5 could honestly be attempted at all.

| # | Site | Reads | Status |
|---|---|---|---|
| 1 | `a9_deep_analysis_agent.py` `_contract_path_for_kpi` | scans contracts dir for matching `metadata.id` | **LIVE** for apex_lubricants/hess/bicycle (step 1's fallback) |
| 2 | `a9_deep_analysis_agent.py` `_dims_from_contract` | `dimension_semantics` | **LIVE** for apex_lubricants/hess/bicycle; dead for lubricants (step 1) |
| 3 | `a9_deep_analysis_agent.py` `_hierarchies_from_contract` | `dimension_hierarchies` | Was LIVE for hess/bicycle — **migrated for hess this step** (see below) |
| 4 | `a9_data_product_agent.py` `_load_registry` | `data_product_registry.yaml` | **DEAD** — file confirmed absent at the real `registry_path` default |
| 5 | `a9_data_product_agent.py` `_load_registry` auto-hydrate | contract read nested inside #4's dead branch | **DEAD** — unreachable, guard never true |
| 6 | `a9_data_product_agent.py` onboarding QA lint | `contract_yaml` string param | LIVE — onboarding wizard, generic YAML-text parsing, not tied to the 12 files; blocked on Onboarding work item O4 |
| 7 | `a9_data_product_agent.py` `register_tables_from_contract` | arbitrary `contract_path` param | LIVE — onboarding wizard utility, generic |
| 8 | `a9_data_product_agent.py` `create_view_from_contract` | arbitrary `contract_path` param | LIVE — onboarding wizard utility, generic |
| 9 | `a9_data_product_agent.py` `generate_sql` (ad-hoc NL-to-SQL) | `yaml_contract_text` string | LIVE but deprioritized — `project_product_direction`: "don't build NL-to-SQL" |
| 10 | `a9_data_product_agent.py` `_get_contract_column_aliases` | `column_aliases` | Registry-first as of step 4; YAML fallback confirmed practically moot (confined to a fallback branch none of the 3 real clients ever reach) |
| 11 | `a9_data_product_agent.py` `_get_exposed_columns` | `exposed_columns` | LIVE per code, but its only call path (`_resolve_attribute_name` ← `_generate_sql_for_kpi`) is the SAME dead-for-3-real-clients fallback as #10 — **not migrated this step**, see below |
| 12 | `a9_data_governance_agent.py` `_load_exposed_columns` | `exposed_columns`, hardcoded to `FI_Star_View` (bicycle) | LIVE but narrow/bicycle-only; registered as an orchestrator workflow step (`validate_registry_integrity`) — not traced further this pass |
| 13 | `a9_data_governance_agent.py` `compute_and_persist_top_dimensions._contract_dims` | `dimension_semantics`, hardcoded to `FI_Star_View` (bicycle) | LIVE but narrow/bicycle-only offline enrichment tool; same orchestrator-registered pattern as #12 |
| 14 | `a9_data_governance_agent.py` (same method) | separate `kpi_enrichment.yaml` **cache** file | LIVE, unrelated to the 12 contract files — a different artifact entirely |

**`views` shape collision — resolved as a decision, not a migration.** Confirmed `DataProduct
.views` (the registry field, `Dict[str, ViewDefinition]`) has ZERO live readers anywhere:
`_backfill_fields` only touches `.name`; `DataProductProvider.find_by_view` (the one method that
queries it) has zero callers of its own. The registry's `views` was designed for a different
purpose (onboarding-authored view SQL/columns) than what the YAML's `views[].llm_profile`
actually carries (`dimension_semantics`, `dimension_hierarchies`, `exposed_columns` — three
distinct LLM-profile facts, now confirmed, not the one the original finding named). **Decision:**
the registry's `views` field keeps its original, still-unused-but-not-urgent purpose;
`dimension_hierarchies` and `exposed_columns`, when migrated, become sibling top-level
`DataProduct` fields — exactly the pattern `dimension_semantics`/`measure_semantics`/
`column_aliases` already established — never nested back under `views`. This is *why* the
collision won't recur: the registry side simply stops using that key for LLM-profile metadata,
so there is nothing left to collide.

**`dimension_hierarchies` migrated (hess).** New `DataProduct.dimension_hierarchies: Dict[str,
List[str]]` field (migration `20260829150000_data_products_dimension_hierarchies.sql`), a new
`_hierarchies_from_registry` method mirroring `_dims_from_registry` exactly, and the
`_hierarchies_from_contract` closure inside `execute_deep_analysis` tries the registry first.
**Genuinely live, unlike `column_aliases`**: `execute_deep_analysis` sets `used_hierarchical =
True` whenever this dict is non-empty, switching DA from flat dimension ranking to a
hierarchical-drill analysis path — a real behavioural fork this session's audit surfaced, not
previously in the Phase 16 finding table at all. Only `hess_financials.yaml` and `fi_star_schema
.yaml` (bicycle) declare this section among the seeded clients; `lubricants`/`apex_lubricants`
never did, so an empty result means two different things depending on the client ("not yet
migrated" for hess vs. "genuinely has none" for lubricants/apex) — both correctly fall through
to an equally-empty YAML scan either way. Verified live against the real bootstrapped registry
(no mocks): hess's `gross_margin_pct` returns the seeded `{geography, segment, financials}`
dict; lubricants' returns `{}` as expected. 7 new unit tests
(`tests/unit/test_da_dimension_hierarchies.py`). `onboard_client.py`'s `_DP_COLS` gained
`dimension_hierarchies` (7th instance of the explicit-allow-list trap this session, added
proactively).

**`exposed_columns` — migrated 2026-08-30, local Supabase only, not yet synced to production.**
This work is on branch `phase17-theory-layer`, not yet merged to `master` — per this document's
own Registry Data Sync Protocol, production sync happens after the push lands, not before. Named
in the prior pass as
"the clearest concrete next unit of step 5 work" and picked up here. `DataProduct
.exposed_columns: Dict[str, List[str]]` (migration `20260830_data_products_exposed_columns.sql`),
keyed by lowercased view name rather than a flat list — the pre-existing YAML-scan code already
looks up by view name with a fallback to `FI_Star_View`, and the registry shape stays faithful to
that rather than flattening it away. `_get_exposed_columns(view_name, data_product_id=None)`
gained the second parameter, tries the registry first, only scans YAML when the registry has
nothing for that view; its in-memory cache is now keyed by `(data_product_id, view_name_lower)`
so two data products can never collide on an identically-named view. **Found and fixed the same
cross-tenant bug shape a third time**: the YAML fallback called `self._contract_path()` with no
argument, always resolving to the bicycle default contract regardless of which data product was
actually asked about — same shape already fixed for `_dims_from_contract` (step 1) and
`_get_contract_column_aliases` (step 4). Fixed by threading `data_product_id` through the
method's one call site inside `_resolve_attribute_name` (already receives `kpi_definition`, so no
change was needed at that method's own 7 call sites inside `_generate_sql_for_kpi`). Seeded onto
all 4 data products (lubricants/apex_lubricants/hess/bicycle) — genuinely load-bearing only for
bicycle (`source_system=duckdb`, the one client with no explicit Tier-1 routing branch); seeded on
the other three for consistency and so the registry is a complete substitute for the YAML once
this step deletes it. 12 new unit tests (`tests/unit/test_dpa_exposed_columns_registry.py`).
Verified live against local Supabase: re-seeded all 4 clients, confirmed via direct query that
each data product's `exposed_columns` matches its source YAML's `views[].llm_profile
.exposed_columns` section exactly.

**`dimension_semantics` backfilled for hess and apex_lubricants — 2026-08-30, local Supabase
only, not yet synced to production** (same reason as `exposed_columns` above — not yet merged to
`master`). Step 1 (2026-08-29) only ever migrated this for lubricants; checked directly by
grepping `scripts/clients/*.py` before writing this pass rather than trusting this document's own
prior "hess is now the only non-lubricants client with either migrated" wording (which, read
carefully, was about `dimension_hierarchies`, not `dimension_semantics` — hess had neither field
until now). Ported verbatim from `hess_financials.yaml`/`lubricants_snowflake.yaml`'s
`views[].llm_profile.dimension_semantics:` sections. No code change needed — `_dims_from_registry`
(DA, built in step 1) already reads this generically per data product; this was purely a seed-data
gap. Verified live: direct query against local Supabase after re-seeding confirms both fields
populated correctly.

**Correction to this document, found while backfilling bicycle (2026-08-30):** the sentence above
("Only `hess_financials.yaml` and `fi_star_schema.yaml` (bicycle) declare this section
[`dimension_hierarchies`]") is **wrong for bicycle**, checked directly rather than carried
forward — `fi_star_schema.yaml` has only a comment ("dimension_hierarchies can be added later for
drill-down analysis"), no actual `dimension_hierarchies:` section. Nothing was migrated or seeded
for bicycle's `dimension_hierarchies` as a result — there is nothing to port. Bicycle's
`dimension_semantics` (above) and `exposed_columns` (above) were both real and have been
backfilled; `dimension_hierarchies` genuinely does not apply to this client, same as
lubricants/apex_lubricants.

**DGA's bicycle-only utilities (#12, #13) not traced further.** `validate_registry_integrity` and
`compute_and_persist_top_dimensions` are registered as orchestrator workflow steps; whether that
orchestrator workflow is ever actually invoked in a live path was not confirmed this pass —
flagged as audited-but-not-resolved rather than assumed dead.

**Why none of the 12 YAML files can be deleted yet, concretely:** every one of hess's, bicycle's,
and apex_lubricants'/lubricants' contract files still backs at least one confirmed-live read
(#1/#2 for apex/hess/bicycle's `dimension_semantics`; #11/#12 for `exposed_columns` across
multiple clients including lubricants; #13 for bicycle's enrichment tool). The onboarding-generic
sites (#6–#9) don't target these specific files but do count against step 6's "no `yaml.safe_load`
in `src/agents/**`" architecture test, and are gated on the separate Onboarding work item O4
("replace `contract_yaml: str` with the typed contract object") — a prerequisite the original
plan's ordering note didn't spell out this explicitly.

**Verified:** 1443 unit tests pass (1436 + 7 new). No YAML files touched or deleted this session.

**Update, same day (2026-08-30) — O4 turned out to be unnecessary; dead code deleted instead.**
Tracing sites #6–#9 to their *actual* live callers (not just their existence as methods) found
every one of them provably dead once followed all the way up, not "narrow/generic utilities"
as the original audit assumed:

- #6 (`validate_data_product_onboarding`'s file-based branch): its one live caller
  (`A9_Orchestrator_Agent`'s composite onboarding step) hardcodes `contract_path=None` with the
  comment "No YAML — Supabase is canonical"; the method's own early-return already skipped the
  file-based checks in that case.
- #7/#8 (`register_tables_from_contract`/`create_view_from_contract`): only reachable via
  `_load_registry`'s auto-hydrate branch (already confirmed dead by the original audit — site
  #4/#5), the orchestrator's `prepare_environment`/`onboard_data_product` (traced this pass —
  zero callers anywhere), or `decision_studio.py`, an unimported Streamlit prototype last
  touched Dec 2025.
- #9 (`generate_sql`'s ad-hoc NL-to-SQL YAML-profile extraction): has one live caller
  (`A9_Situation_Awareness_Agent._generate_sql_for_query`), but that caller never sets
  `contract_path` in its context, so the extraction branch itself was a permanent no-op.

**Deleted this pass, not just marked dead**, since step 6's architecture test greps for the
literal `yaml.safe_load` text rather than checking runtime reachability: `A9_Orchestrator_Agent
.prepare_environment`/`onboard_data_product`; `A9_Data_Product_Agent.register_tables_from_contract`/
`create_view_from_contract`; `A9_Data_Product_Agent._load_registry`'s auto-hydrate branch;
`validate_data_product_onboarding`'s file-based branch (now always returns its skip response);
`generate_sql`'s dead extraction block; `A9_Data_Governance_Agent.validate_registry_integrity`/
`compute_and_persist_top_dimensions`/`_load_exposed_columns` (sites #12/#13, confirmed dead via
the same orchestrator-caller trace). Two test files depended on deleted methods:
`tests/test_duckdb_views.py` deleted (tested only `create_view_from_contract`);
`tests/integration/test_cogs_validation.py`'s `prepare_environment` setup call replaced with a
skip-if-view-missing check. Cards updated: `A9_Orchestrator_Agent_card.md`,
`A9_Data_Product_Agent_card.md`, `A9_Data_Governance_Agent_card.md`. 1484 unit tests pass,
unchanged — none of the deleted code was exercised by the unit suite.

**Update, same day (2026-08-30) — the bigger decision was made and executed.** Verified live
(direct query, not assumed) that all 4 real data products
(`dp_lubricants_financials`/`dp_hess_financials`/`dp_lubricants_snowflake`/`fi_star_schema`) have
complete registry records for every field the YAML fallbacks would otherwise read. That made
`_get_contract_column_aliases`'s and `_get_exposed_columns`'s YAML fallback branches (DPA) and
`_dims_from_contract`/`_hierarchies_from_contract`'s YAML fallback branches (DA, including
`_contract_path_for_kpi`) provably unreachable for every real client, so they were deleted —
same pass as `_contract_path`/`_contract_path_for_kpi` (the resolvers only those branches used)
and the 8 legacy contract YAML files themselves (turned out to be 8 on disk, not the 12 the
original 2026-08-10 finding counted — 4 were already-orphaned fixtures never matched to any
live `data_product_id`: `dp_lubricants_sqlserver`, `SalesOrderStarSchemaView`,
`dp_sales_analytics_009`, `sales_star_schema`). `connection`'s deletion from the YAML files
(step 4's recommendation) went with them, since the whole files are gone.

**One data product's registry fields are still empty** — `dp_lubricants_sales` (the 5 Sales
KPIs). Checked before deleting anything: none of the 8 YAML files' `metadata.id` ever matched
it either, so its YAML fallback always returned nothing too. Deleting the fallback changes
nothing for this data product — same empty result, same underlying gap, not a new regression.
Backfilling it is a separate, pre-existing task, not part of this cleanup.

Step 6 (the architecture test) followed immediately: `yaml.safe_load(` is now banned in
`src/agents/**` via `scripts/architecture_lint.py` (already wired into the pre-commit hook) and
mirrored in `tests/architecture/test_architecture_compliance.py`. Two pre-existing call sites
outside this cleanup's scope — `business_context_loader.py` (SF debate-persona framing, not
registry data) and `a9_llm_service_agent.py` (dead ad-hoc-NL-to-SQL profile parsing, explicitly
deprioritized per `project_product_direction`) — are allow-listed inline with
`# arch-allow-yaml-fallback`, flagged in the lint script's own comment for whoever audits
CLAUDE.md rule 6 next.

Tests: 12 tests across `test_dpa_column_aliases_registry.py`/`test_dpa_exposed_columns_registry.py`
rewritten for registry-only behaviour (no more YAML-fixture-on-disk fixtures); `test_da_dimension_ranking.py`
rewritten to feed `_dims_from_registry` directly via mock instead of a temp YAML file +
`_contract_path_for_kpi` patch; `test_da_kpi_scoped_lookup.py`'s YAML-path test replaced with a
`_dims_from_registry` equivalent; `test_dpa_principal_filters.py`'s one fixture updated to
declare `base_column` explicitly (it had been passing only by accident, via the same YAML
fallback's always-defaults-to-bicycle behavior on a data_product_id that never matched anything).
1478 unit tests pass (1484 before this pass; net −6 from removing YAML-fallback tests with no
registry-only equivalent worth keeping).

**Local Supabase only, NOT yet synced to production** (this work is on `phase17-theory-layer`,
unmerged): `exposed_columns` column + all 4 clients' seed data, `dimension_semantics` for
hess/apex_lubricants — sync once this phase's remaining work lands on `master`, per this
document's own Registry Data Sync Protocol.

---

#### Open questions

- **Hess is not a validated dataset** (established 2026-08-10). `HessStarSchemaView` is a *partially relabelled lubricants dataset*, living in the `agent9_lubricants` database alongside `LubricantsStarSchemaView`. Two dimensions were genuinely converted — `segment_name` (E&P, Midstream) and `basin_name` (Bakken, Gulf of Mexico, Guyana, Southeast Asia) are real Hess geography. The rest were not: `asset_name` holds **Automatic Transmission Fluid, Compressor Oil, Conventional Engine Oil**; `business_unit` holds **Retail Products, Service Centers**; `country` and `region` hold identical region values. An E&P asset is a field or a platform, not a motor oil.

  The five NULL KPIs — `lifting_cost`, `exploration_expense`, `capital_expenditure`, `operating_cash_flow`, `free_cash_flow` — are **correctly defined for an E&P company** and return nothing because the data is a lubricants P&L (`account_category` = Base Oil & Additives, Packaging, Distribution…). They are not the problem; they are the symptom.

  **The KPIs that DO return numbers are the greater risk.** `upstream_revenue` = 3,766,365,690 is simply `SUM(Revenue)` over lubricants data, presented under an oil & gas name. NULL is visibly broken; a plausible wrong number is not.

  **SCOPING DECISION (2026-08-10): data realism is explicitly NOT in scope for Apex or Hess.** They exist to demonstrate that Agent9 works technically against Snowflake and SQL Server, and for that purpose the underlying data does not need to be a faithful E&P or distributor P&L. Both remain useful as backend-connectivity proof. This closes the "generate real E&P data" option below unless the positioning changes.

  **What still matters under that framing, and why it is narrower than it looks:**
  - ~~**The sign error is still worth fixing**~~ **FIXED (step 3, 2026-08-29, synced to production 2026-08-30):** gross margin now reports 34.43% — matching the manual audit's independently-computed figure exactly — instead of 165.57%. All 5 mis-signed KPIs corrected; see the Step 3 subsection above.
  - **The five NULL KPIs can stay or go** — they weaken nothing technically. Removing them is tidier; leaving them is honest about the dataset being partial. Low priority either way.
  - **The relabelling does not matter** — `asset_name` holding motor oils is irrelevant to a connectivity demo.
  - **The one real constraint:** neither client should be presented as an industry case study, and no briefing from them should be shown as a customer example. `upstream_revenue` is lubricants revenue under an oil & gas name — fine as plumbing, misleading as a narrative.

  Options retained for the record, should positioning change:
  1. **Generate real Hess E&P data** — E&P account categories (lifting, exploration, capex, operating CF) and real assets. Makes all sixteen KPIs meaningful and gives a genuinely different second industry.
  2. **Accept Hess as a dimensional demo** — remove the KPIs the data cannot support, and rename the rest so they do not claim to be upstream figures.

  Doing neither leaves a seeded client whose working KPIs describe the wrong business.
- ~~**Apex's remaining KPIs** — only `gross_margin_pct` was validated there. The same sign audit should run across its full set before anyone reads an Apex briefing.~~ **RESOLVED (step 2, 2026-08-29):** ran the negation validator + live-value check against all 16 Apex KPIs — zero sign-convention violations, zero live-value problems.
- **Does any client legitimately store expenses positive?** The design assumes a per-data-product declaration precisely so the answer can differ. **Partially confirmed (step 2, 2026-08-29):** all three financial-KPI clients checked (lubricants/apex_lubricants/hess) use the same convention (Revenue positive, COGS/SGA/Other negative) — none stores expenses positive. bicycle and brookshire_brothers not yet checked (no `measure_semantics` declared for them, and their KPI sets weren't audited this pass).

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

### Infra A: Production Deployment ✅ COMPLETE (Mar 2026)

- Backend: Railway (Docker/FastAPI)
- Frontend: Vercel (Vite/React)
- Database: Supabase Cloud (Postgres)
- Analytics: BigQuery (GCP credentials via env var)
- GCP credentials materialized from `GCP_SERVICE_ACCOUNT_JSON` at startup
- Bicycle/FI DuckDB data not available in production — lubricants BigQuery works

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

