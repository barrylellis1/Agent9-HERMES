# Agent9-HERMES Development Plan

**Created:** 2026-03-14
**Last updated:** 2026-04-06
**Status:** Active
**Supersedes:** `IMPLEMENTATION_PLAN.md` (Nov 2025), `HERMES_IMPLEMENTATION_PLAN.md` (original hackathon)

---

## Current Focus: Phase 10 — Brand Identity & UI Polish

**Status:** Phase 9 (Enterprise Assessment Pipeline) complete (2026-04-04). Full end-to-end pipeline operational: batch assessment → Supabase persistence → PIB email → deep link → delegation with audit trail.

**What to build next (in order):**

1. **Phase 10** — Brand Identity & UI Polish: Swiss Style design system, PIB email refinement, Decision Studio visual overhaul
2. **Phase 11** — Platform Refinement: unified situation stream, adaptive calibration loop, audio briefings
3. **Phase 12** — Business Optimization: top-down strategic workflows, new agents

**Key decisions already made:**
- SA = sensor (facts), DA = analyst (framing) — no separate opportunity agent
- Per-KPI monitoring profiles replace global timeframe dropdown
- Both positive and negative KPI movements flow through DA → SF → VA equally
- Bars for uncertainty (SA tiles), lines for trajectories (VA charts)
- Adaptive calibration loop is the core compounding moat
- Brand identity: "Swiss Style" AI — monochrome dominance, semantic color only, "Quiet Expert" voice
- Customer-facing brand: "Decision Studio" — domains: decision-studios.com + trydecisionstudio.com
- **No snooze/hide preference layer** — signal routing solves the noise problem at source
- **KPI accountability is dimensional** — principals own KPIs at the scope of their control (enterprise, region, LOB). Same KPI, different scope. See `docs/architecture/kpi_accountability_model.md`.
- **LLM-assisted accountability import** — HCM documents (job descriptions, OKRs, RACI) are the source of truth for accountability mapping; LLM extracts and proposes, human confirms
- **Assessment runs are client-scoped, not principal-scoped** — one enterprise scan per client, per-principal views filtered by accountability registry

**Known tech debt:**
- `kpisScanned={14}` hardcoded in `DecisionStudio.tsx:130` — wire real `kpi_evaluated_count` (Phase 11)
- Separate `OpportunitySignal` / `Situation` streams — unify (Phase 11)
- Client dropdown on SA Console — move to login screen
- `get_latest_run` filters by `principal_id` — should be client-scoped only (Phase 11A)
- Assessment runs tagged with `principal_id` — should be client-scoped (Phase 11A)

---

## Where We Are (Phases 1-6 Complete)

The core insight-to-action pipeline is built and operational:

```
SA (Detect) → DA (Diagnose) → MA (Context) → SF (Prescribe) → HITL (Decide)
```

### What's Working

| Capability | Agents | Status |
|-----------|--------|--------|
| KPI breach detection + situation cards | SA, PC, DG, DP | Production-ready |
| Is/Is Not root cause analysis + change-point detection | DA, DP (BigQuery) | Production-ready |
| Market context enrichment | MA (Perplexity + Claude) | Production-ready |
| Multi-persona solution generation (3×Stage1 + synthesis) | SF, LLM Service | Production-ready |
| Follow-up NL questions with inline data results | NLP Interface, DP | Production-ready |
| HITL approval workflow | SF → UI | Production-ready |
| Data Product Onboarding (8-step) | DP, DG, Orchestrator | Production-ready |
| KPI Assistant | KPI Assistant | API-only (no UI) |
| Decision Studio UI | React/Vite/Tailwind | Production-ready |
| Supabase-backed registries (6 registries) | Registry Factory | Production-ready |
| DuckDB + BigQuery + PostgreSQL data sources | DP, Database layer | Production-ready |

### What's Not Built

| Capability | Status |
|-----------|--------|
| Swiss Style brand identity across UI | Planned (Phase 10) — guidelines written, implementation pending |
| Unified situation stream (problem + opportunity merge) | Planned (Phase 11) — architectural refactor |
| Adaptive calibration loop | Planned (Phase 11) — KPI Assistant recommends monitoring profiles |
| Audio briefings (TTS) | Planned (Phase 11) — assessment results → audio summary |
| Business Optimization (top-down strategic) | Planned (Phase 12) — workflow YAML exists, no agent code |
| Extended Solution Finding (Risk/Stakeholder agents) | Planned (Phase 12) — workflow YAML exists, agents not built |
| Scheduled SA execution | Script exists, no scheduler |
| KPI Assistant UI | API routes exist, no frontend |
| Slack notifications | PIB email shipped; Slack integration pending |

---

## Development Phases: Forward Plan

### Phase 7: Value Assurance Agent ✅ COMPLETE

**Status:** Shipped (commit `a5a1e74`, Mar 2026). SF→VA approval handoff wired (commit `79a3f3b`).

**Delivered:**
- VA Agent: 6 entrypoints, DiD attribution, composite verdict matrix, confidence scoring
- 4 API endpoints + Supabase persistence (situations, solutions, evaluations tables)
- React components: ValueAssurancePanel, AttributionBreakdown, PortfolioDashboard, CostOfInactionBanner
- SF HITL approve → VA `register_solution` wired in `_record_solution_action()` — reconstructs RegisterSolutionRequest from workflow record (DA output, SF result, situation_id)
- "Approve & Track" button moved to Executive Briefing page (post-review, not pre-review) with post-approval confirmation card showing approved strategy, expected recovery, monitoring window, and next steps
- 42 unit tests passing

**Remaining (deferred):**
- VA UI components (ValueAssurancePanel, PortfolioDashboard) not yet wired into DeepFocusView post-approval — show after HITL approval or in briefing view
- Orchestrator `run_value_assurance()` method not added — VA is called directly from workflow route

---

### Phase 7C: Value Assurance UI Integration ✅ COMPLETE

**Status:** Shipped (Mar 2026). All VA components wired into the UI.

**Context:** Phase 7 delivered 4 React components and 7 VA API endpoints. Phase 7C wired everything together.

**Goal:** Surface outcome tracking to the principal so they can see whether approved decisions are delivering. This closes the Agent9 value loop visually: detect → diagnose → decide → **did it work?**

#### Deliverables

| Deliverable | Description |
|------------|-------------|
| VA API types + client functions | Add VA response types to `types.ts`; add `getPortfolio()`, `checkValueAssurance()`, `projectInactionCost()` to `client.ts` |
| Post-approval panel in ExecutiveBriefing | After "Approve & Track" succeeds, replace the confirmation card with `ValueAssurancePanel` showing the registered solution's monitoring window, expected recovery range, and current verdict |
| Portfolio view in Decision Studio | Add a "Value Assurance" tab or section to the main dashboard showing `PortfolioDashboard` — all approved solutions with their attribution verdicts (VALIDATED / PARTIALLY_VALIDATED / INSUFFICIENT_DATA / FAILED) |
| Cost of Inaction banner | Show `CostOfInactionBanner` on the SA dashboard for situations that have been open > N days without an approved solution |
| Attribution breakdown | `AttributionBreakdown` shown within `ValueAssurancePanel` — waterfall chart of intervention vs. market vs. seasonal attribution |

#### Where each component slots in

| Component | Location | Trigger |
|-----------|----------|---------|
| `ValueAssurancePanel` | `ExecutiveBriefing.tsx` | Shown after `approveState === 'approved'`; fetches via `checkValueAssurance(solutionId)` |
| `AttributionBreakdown` | Inside `ValueAssurancePanel` | Always rendered when panel is visible |
| `PortfolioDashboard` | New "Value Assurance" tab in `DecisionStudio.tsx` or standalone `/va` route | On-demand; fetches via `getPortfolio(principalId)` |
| `CostOfInactionBanner` | `DashboardView.tsx` / SA situation cards | When situation age > threshold and no solution registered |

**Files:** `decision-studio-ui/src/api/client.ts`, `decision-studio-ui/src/api/types.ts`, `ExecutiveBriefing.tsx`, `DecisionStudio.tsx`, `DashboardView.tsx`

**Effort:** Medium (~1 day). Components exist — this is wiring and layout work.

**Dependency:** None — VA API is fully operational.

---

### Phase 8: Opportunity Deep Analysis ✅ COMPLETE (with design revision)

**Status:** Shipped (commits `6869ed0`–`1b602b8`, Mar 2026).

**Delivered:**
- `BenchmarkSegment` Pydantic model — classifies DA IS NOT items as `internal_benchmark` (top quartile |delta|) or `control_group`
- `_classify_benchmark_segments()` function in DA agent
- `analysis_mode` field on `DeepAnalysisRequest` ("problem" | "opportunity") — controls SCQA framing
- Opportunity SCQA prompt variant: "the gap IS the strategy" McKinsey framing
- `Situation.from_opportunity_signal()` classmethod — converts OpportunitySignals to Situation cards
- Frontend: green KPI tiles, Replication Targets section in DeepFocusView
- `analysisMode` threaded from frontend through API to DA

**Design revision (Mar 2026):**
The initial design had SA pre-labeling situations as "problem" or "opportunity" via `card_type`. After review, we determined:
- **SA should be a sensor** — it reports KPI performance (facts only)
- **DA is the analyst** — it identifies both problems AND opportunities from the same Is/Is Not table
- One KPI should not produce duplicate cards (one problem, one opportunity)
- The `BenchmarkSegment` and Replication Targets UI work correctly regardless of `card_type`

The SA→opportunity labeling code (`from_opportunity_signal`, `card_type="opportunity"`) ships as-is but will be **revisited** when the Enterprise Assessment Pipeline (Phase 9) is built. The correct model: assessment runs enterprise-wide, DA always produces unified output, and findings surface as pre-analyzed results — not as separate problem/opportunity cards.

**Decision:** Unified DA — no separate Opportunity Analysis Agent. IS NOT outperformers = internal benchmarks = replication candidates.

---

### Phase 9: Enterprise Assessment Pipeline ✅ COMPLETE

**Status:** Shipped (2026-04-04). Full pipeline operational: batch assessment → Supabase persistence → PIB email → deep link → delegation with audit trail.

**Goal:** Replace the interactive dashboard-first model with offline, enterprise-wide analysis. Agent9 should not be perceived as "just another dashboard" — executives already have dashboards. The value is automated analysis, not KPI display.

**Design principles:**
- Assessment is **enterprise-level first** — all registered KPIs across all data products and business processes
- SA is a **sensor** — fetches values and computes severity from threshold distance. No problem/opportunity labeling.
- DA is the **analyst** — for each flagged KPI, runs Is/Is Not to produce both problem segments AND benchmark segments
- Principal-specific views are **layered on top** — the same assessment data, filtered by the principal's business processes
- SF and HITL remain **interactive** — pre-compute the analysis, keep humans in the decision loop
- **Noise filtering via KPI monitoring profiles** — each KPI defines its own comparison period, volatility band, breach duration threshold, and confidence floor. SA uses these to distinguish signal from noise before committing DA resources.

#### Phase 9A: Data Model + Persistence

| Deliverable | Description |
|------------|-------------|
| Supabase migration | `assessment_runs` (id, timestamp, status, kpi_count, config) |
| Supabase migration | `kpi_assessments` (id, run_id, kpi_id, kpi_value, severity, da_result JSONB, benchmark_segments JSONB) |
| Assessment models | Pydantic models: `AssessmentRun`, `KPIAssessment`, `AssessmentConfig` |
| KPI monitoring profile fields | New fields on KPI registry: `comparison_period`, `volatility_band`, `min_breach_duration`, `confidence_floor`, `urgency_window_days` |

#### Phase 9B: Assessment Engine (replaces `run_cfo_assessment.py`)

| Deliverable | Description | Status |
|------------|-------------|--------|
| `run_enterprise_assessment.py` | New script: iterates ALL registered KPIs, runs SA measurement + DA analysis per KPI, persists to Supabase | ✅ SHIPPED |
| Proper agent instantiation | Uses RegistryFactory + Orchestrator (not legacy `create_situation_awareness_agent`) | ✅ SHIPPED |
| KPI-specific comparison periods | SA uses each KPI's `comparison_period` instead of a global timeframe toggle | ✅ SHIPPED |
| Volatility-adjusted severity | Breach magnitude evaluated relative to the KPI's `volatility_band` — a 5% revenue dip may be noise while a 2% margin drop is a crisis | ✅ SHIPPED (basic implementation) |
| Confidence floor gating | Only escalate to DA when situation confidence exceeds the KPI's `confidence_floor`. Below that, flag as "monitoring" — visible but not consuming pipeline resources | ✅ SHIPPED |
| Configurable severity floor | Only run DA for KPIs above a configurable severity threshold | ✅ SHIPPED |
| Idempotent runs | Assessment run ID prevents duplicate analysis for the same KPI in the same period | ⚠️ PARTIAL (in-memory dedup; Supabase persistence TODO Phase 9C) |
| Progress logging | Per-KPI progress with timing, errors logged but non-fatal | ✅ SHIPPED |

#### Phase 9C: API + UI + PIB Email Delivery

| Deliverable | Description | Status |
|------------|-------------|--------|
| `GET /assessments/latest` | Returns most recent assessment run with findings, filterable by principal/business_process | ✅ SHIPPED (Supabase) |
| `GET /assessments/{run_id}` | Full assessment detail | ✅ SHIPPED (Supabase) |
| `POST /assessments/run` | Trigger assessment on-demand (optional — may be CLI-only initially) | ✅ SHIPPED |
| A9_PIB_Agent | Composes briefing content from assessment results, renders Jinja2 HTML email, sends via SMTP | ✅ SHIPPED (2026-04-04) |
| PIB API routes | `POST /pib/run`, `GET /pib/runs`, `GET /pib/token/{token}`, `POST /pib/delegate/{token}`, `GET /pib/delegates` | ✅ SHIPPED |
| Briefing token system | Single-use tokens with 7-day TTL for secure email deep links (Supabase `briefing_tokens` table) | ✅ SHIPPED |
| Email deep link → Dashboard | ActionHandler.tsx resolves token, navigates to DeepFocusView via kpi_name match | ✅ SHIPPED |
| Delegation flow | DelegatePage.tsx with KPI→BP→principal recommendations, audit trail in `situation_actions` table | ✅ SHIPPED |
| Gmail SMTP delivery | aiosmtplib integration, App Password auth, light-theme executive email template | ✅ SHIPPED |
| Supabase migrations | `assessment_runs`, `kpi_assessments`, `briefing_runs`, `briefing_tokens`, `situation_actions`, `email` on `principal_profiles` | ✅ SHIPPED |
| Enterprise assessment fixes | Client_id filter, YoY comparison_type default, client_id persisted on AssessmentRun | ✅ SHIPPED |
| Landing page refactor | Dashboard reads from assessment API, shows pre-analyzed findings. Swiss Style brand identity. | Moved to Phase 10A |
| KPI tile redesign | Comparison period badge, threshold reference line, wire `kpi_evaluated_count` | Moved to Phase 10B |

**KPI Tile Redesign Spec:**

~~The current KPI tile sparkline is **fake** (`Math.random()` in `KPITile.tsx` line 16). Replace with real data.~~ **Partially complete (Mar 2026).**

*Backend changes:*

| Deliverable | Description | Status |
|------------|-------------|--------|
| Monthly series query | SA queries 9 monthly aggregates per KPI via `_bq_monthly_series_sql()`. BigQuery only; DuckDB TODO | ✅ Done |
| `monthly_values` on data model | `KPIValue.monthly_values: Optional[List[Dict[str, Any]]]` — `{period, value}` | ✅ Done |
| Comparison period label | Include the KPI's `comparison_period` (from monitoring profile) on the Situation response | Pending (Phase 9A) |

*Frontend changes:*

| Deliverable | Description | Status |
|------------|-------------|--------|
| 9-month bar chart | Real bar chart from `monthly_values`. Latest bar in severity color, prior in muted slate | ✅ Done |
| Comparison period badge | Small label on tile: "QoQ" / "MoM" / "YoY" — sourced from monitoring profile | Pending (Phase 9A) |
| Threshold reference line | Horizontal dashed line at the KPI's threshold value | Pending |
| Remove `Math.random()` | Fake sparkline data generation deleted | ✅ Done |
| Wire `kpi_evaluated_count` | Replace hardcoded `kpisScanned={14}` in DecisionStudio.tsx with real count from API | Pending (Phase 9G) |

*Why 9 months:*
- Works regardless of comparison period (MoM sees recent trajectory, QoQ sees 3 full quarters, YoY sees 3/4 of the year)
- Shows seasonality visually — admin can see if a "breach" is just a seasonal dip
- Gives context: is this a sudden drop or a gradual decline?
- Consistent across all KPIs regardless of their individual comparison cadence

*Remaining sub-phases (9D principal layering, 9E audio briefings, 9F adaptive calibration, 9G unified stream) have been promoted to Phase 11 — see below. Phase 9D (principal-specific filtering) is effectively complete: the batch engine already filters KPIs by principal's business processes, and the PIB scopes content to the principal.*

---

### Phase 11: Platform Refinement

**Goal:** Four independent initiatives that strengthen the core platform. Each can be built in any order based on demo priorities.

#### 11A: KPI Accountability Model + Client-Scoped Assessment

**Goal:** Fix the fundamental architectural mismatch where assessment runs are principal-scoped. Introduce dimensional KPI accountability so the right principal gets the right signal by construction — no noise-filtering preference layer needed.

**Architecture doc:** `docs/architecture/kpi_accountability_model.md`

**The insight:** Principals own KPIs at the scope of their control. CFO owns Net Revenue enterprise-wide. Regional VP owns Net Revenue for EMEA. Same KPI, different scope. The accountability registry expresses this — SA uses it to route situations to exactly the right principals.

**Why this matters for the demo:** Currently Marcus Webb sees 0 situations in his PIB because `get_latest_run` filters by `principal_id: cfo_001`. The enterprise scan should be client-scoped; each principal gets a filtered view based on their accountability assignments.

| Deliverable | Description |
|------------|-------------|
| `kpi_accountability` registry model | New Pydantic model: `kpi_id`, `principal_id`, `scope_dimension` (optional), `scope_value` (optional), `role` (accountable/responsible) |
| Supabase migration | `kpi_accountability` table with governance constraints (max 1 accountable per KPI per scope) |
| `get_latest_run` refactor | Remove `principal_id` filter — query by `client_id` only. PIB filters `kpi_assessments` by principal's accountability assignments. |
| SA routing integration | SA passes `scope_dimension` + `scope_value` when generating situation items for a principal |
| Seed lubricants accountability | Map 15 lubricants KPIs to 4 principals with correct dimensional scopes |

#### 11B: LLM-Assisted Accountability Import

**Goal:** Solve the enterprise cold-start problem. Instead of manual KPI-to-principal mapping (which kills BI platform adoption), extract accountability from HCM documents using LLM.

**Source documents:** Job descriptions, org charts, performance review frameworks, OKRs, RACI matrices — accountability is already written down, just unstructured.

**Pattern:** Same as `A9_KPI_Assistant_Agent` — LLM suggests, human confirms, registry writes.

| Deliverable | Description |
|------------|-------------|
| `A9_Accountability_Import_Agent` | Accepts HCM document text, extracts accountability statements, maps to KPI registry, returns proposed assignments with confidence scores |
| Admin UI review flow | Present extracted assignments for human confirmation before writing to registry |
| Conflict detection | Flag cases where same KPI is assigned to >3 principals without dimensional scoping |

#### 11C: Unified Situation Stream (formerly 9G)

**Goal:** Eliminate the artificial split between "situations" (problems) and "opportunities" (positive signals). Every KPI movement that exceeds a confidence/magnitude threshold is a **situation** — direction determines framing, not whether it enters the pipeline.

| Deliverable | Description |
|------------|-------------|
| Single situation grid | Remove separate opportunity section. One grid sorted by `abs(percent_change)`. Green border = positive, red/amber = negative. |
| Direction-agnostic SA detection | Unified `situations[]` with `card_type` direction flag. Deprecate `OpportunitySignal` model. |
| Confidence-gated escalation | SA creates cards only when confidence > KPI's `confidence_floor`. Below threshold: "monitoring" status. |
| SF opportunity prompt variant | Stage 1 prompts shift from "fix" to "replicate/accelerate" for `analysis_mode="opportunity"`. |
| Wire `kpi_evaluated_count` | Replace hardcoded `kpisScanned={14}` with real count from assessment API. |

#### 11D: Adaptive Calibration Loop (formerly 9F)

**Goal:** Transform the KPI Assistant from a one-time onboarding helper into an ongoing tuning advisor. The system gets smarter per client over time — this is the core compounding moat.

**Prerequisite:** Phase 9 (assessment engine with monitoring profiles), existing KPI Assistant Agent.

| Deliverable | Description |
|------------|-------------|
| Historical volatility analysis | KPI Assistant queries production data, computes standard deviation, seasonal decomposition, data completeness metrics per KPI |
| Monitoring profile recommendation | LLM synthesizes stats into recommended `comparison_period`, `volatility_band`, etc. with rationale |
| Conversational refinement | Extend KPI Assistant chat — admin can challenge recommendations with domain knowledge |
| Recalibration trigger | After N cycles, review trigger accuracy: what % of escalated situations led to real action vs dismissed as noise |
| KPI Assistant UI | React panel for monitoring profile setup and recalibration (currently API-only) |

**Moat significance:** After 12 months, switching means losing calibrated profiles for 50+ KPIs, historical noise-vs-signal classification data, and validated decision outcomes.

#### 11E: Audio Briefings (formerly 9E)

**Goal:** Transform assessment results into consumable audio briefings. The "not a dashboard" differentiator — an executive gets a 60-second Flash Briefing during their commute.

| Deliverable | Description |
|------------|-------------|
| `a9_briefing_agent.py` | Agent with `generate_audio_briefing` entrypoint. LLM summarization → TTS API call |
| TTS integration | One provider to start (OpenAI TTS, ElevenLabs, or Google Cloud TTS) |
| Workflow-stage framing | SA → "Flash Briefing", DA → "Detective's Summary", SF → "Council Debate", VA → "ROI Post-Mortem" |
| Audio player UI | Inline audio player + transcript + bullet points in Decision Studio |

**Deferred:** Mindmap generation, multi-speaker podcast-style audio.

---

### Phase 12: Business Optimization Workflow

**Goal:** Top-down strategic entry point for board/executive-driven initiatives. Complements the bottom-up SA → DA pipeline with a strategy-first approach.

**Why later:** Shows Agent9 handles proactive strategy, not just reactive KPI monitoring. Requires new agents but reuses SF and VA.

**Reference docs:**
- Workflow YAML: `workflow_definitions/business_optimization.yaml`

#### New Agents Required

| Agent | Purpose | Complexity |
|-------|---------|-----------|
| `A9_Risk_Analysis_Agent` | Weighted risk scoring for proposed initiatives | Medium — PRD exists (dead code), needs rewrite |
| `A9_Stakeholder_Analysis_Agent` | Identify stakeholders, estimate support/resistance | Medium — new |
| `A9_Business_Optimization_Agent` | Assess operations, identify optimization signals | Medium — new |

#### Workflow Integration

| Deliverable | Description |
|------------|-------------|
| Orchestrator method | `run_business_optimization()` |
| Board input capture | UI for executive-initiated strategic directives |
| MA integration | Market context for strategic initiatives |
| SF connection | Route optimization recommendations through existing SF pipeline |
| VA connection | Track whether strategic initiatives deliver expected value |

---

### Phase 13: Extended Solution Finding (Future)

**Goal:** Heavyweight solution evaluation for strategic decisions. Adds Risk Analysis, Stakeholder Analysis, Solution Architect, and Implementation Planner to the SF pipeline.

**Why later:** The current SF (3×Stage1 + synthesis) handles routine KPI fixes well. Extended SF is for large-scale decisions.

#### New Agents Required

| Agent | Purpose | Notes |
|-------|---------|-------|
| `A9_Solution_Architect_Agent` | Technical/organizational solution design | New |
| `A9_Implementation_Planner_Agent` | High-level implementation planning | New — lightweight, not task tracking |
| `A9_Stakeholder_Engagement_Agent` | Manage stakeholder communication workflows | New |

---

### Phase 14: Innovation Driver (Future)

**Goal:** LLM-powered brainstorming, idea incubation, and opportunity shaping.

**Why last:** Requires 4 new agents. Hard to demonstrate measurable value. Doesn't leverage the KT/IS NOT advantage.

**One interesting angle:** If VA shows that a certain type of solution consistently validates (e.g., supplier renegotiation), Innovation Driver could propose proactive application of that pattern to other KPIs before they breach.

**Reference docs:** `workflow_definitions/innovation_driver.yaml`

---

### Future: Enterprise Tier Roadmap

These features go beyond CaaS core and into per-customer enterprise customization. They require significant data accumulation, organizational integration, or workflow complexity that only makes sense for dedicated enterprise deployments. Documented here as a roadmap — not planned for near-term development.

| Feature | Description | Why Enterprise-Only |
|---------|-------------|---------------------|
| **Decision Journal** | Capture principal's reasoning for approve/reject/defer decisions. Build institutional decision memory that informs future SF recommendations and VA evaluations | Requires months of decision data per customer; overlaps with existing board portals and decision-tracking tools |
| **Conditional Approval** | "Approve, but only if legal confirms by Week 2." Track prerequisites as blockers before implementation starts | This is project management — customers already have Jira, Monday, Asana for prerequisite tracking |
| **Scenario Exploration** | Let the principal adjust SF parameters ("What if we only pass through 50%?") and see re-estimated impact without re-running the full pipeline | Massive complexity for uncertain value; requires lightweight LLM re-estimation model |
| **Stakeholder Pre-Briefing Generator** | Generate scoped briefing extracts for specific stakeholders (VP Sales gets franchise impact, Legal gets contractual constraints) | Assumes deep organizational knowledge per customer; connects to Briefing Agent but requires per-role content filtering |
| **VA Feedback Loop** | When VA evaluates a past solution, surface historical results in future SF recommendations ("A similar intervention recovered 60% vs. the 85% estimate") | Requires multiple completed VA cycles to be meaningful; calibration data accumulates slowly |
| **Principal Learning Profile** | Track what the principal always asks vs. never questions; pre-surface relevant information, reduce emphasis on areas they consistently accept | Requires dozens of decision cycles per principal; risks perception of manipulative framing if not handled carefully |

---

## Infrastructure Phases (Interleaved with Feature Work)

*These phases are gated by business milestones, not feature dependencies. See `docs/strategy/Agent9_Business_Plan.md` Section 12b for full cost breakdown.*

### Infra Phase A: Production Deployment ← BLOCKER for outreach

**When:** April-May 2026 — must complete before first discovery call.
**Why:** Platform runs locally. A prospect who sees a demo will ask "when can we start?" and the answer must be "next week."

| Deliverable | Priority | Effort | Notes |
|------------|----------|--------|-------|
| **Cloud deployment** | 🔴 Critical | 2-3 days | Railway or Render (FastAPI backend); Vercel (React frontend); Supabase Cloud (database) |
| **Authentication** | 🔴 Critical | 2-3 days | Supabase Auth (email + password); API keys for programmatic access. No SSO yet. |
| **Error monitoring** | High | 1 day | Sentry free tier — capture backend exceptions before customers report them |
| **Domain + SSL** | 🔴 Critical | 1 day | decision-studios.com / trydecisionstudio.com — landing page + app subdomain |
| **Transactional email** | Medium | 1 day | Resend or SendGrid free tier — situation alerts, password reset, welcome email |
| **Environment parity** | High | 1 day | `.env.production` template; document deployment steps; ensure local dev matches cloud config |

**Cost:** $0/month on free tiers (Railway/Render, Vercel, Supabase Cloud, Sentry, Resend all have free tiers). Only hard cost is domain (~$15-$50/year). Upgrade to paid tiers (~$50-$75/month) when first paying customer requires production reliability. One-time effort: ~1 week.

**Dependency:** None — can run in parallel with Phase 9A.

---

### Infra Phase B: Customer Infrastructure ← BLOCKER for first pilot

**When:** May-August 2026 — must complete before first pilot customer starts.
**Trigger:** First signed pilot (target Sep 2026).

| Deliverable | Priority | Effort | Notes |
|------------|----------|--------|-------|
| **Multi-tenant isolation** | 🔴 Critical | 1-2 weeks | Per-customer Supabase project; separate registries, KPI sets, data products per tenant |
| **Customer provisioning script** | 🔴 Critical | 3-5 days | Automate: create Supabase project → seed registries → configure data product contracts → generate API keys → send welcome email |
| **CI/CD pipeline** | High | 2-3 days | GitHub Actions: run unit tests → build → deploy to staging → manual promote to production |
| **Staging environment** | High | 1 day | Separate Railway/Render instance; test changes before customer environments |
| **Automated backups** | High | 1 day | Supabase handles Postgres; add nightly registry YAML export as belt-and-suspenders |
| **Uptime monitoring** | High | 1 day | Better Uptime or UptimeRobot; customer-facing SLA requires monitoring |
| **Log aggregation** | Medium | 1 day | Logtail or Papertrail; debug customer issues without SSH access |
| **Customer data export** | Medium | 2-3 days | Self-service export (situations, analyses, VA trajectory); required for enterprise procurement |

**Cost:** $200-$500/month base + $50-$100/month per customer.

**Dependency:** Infra Phase A (cloud deployment must exist first).

---

### Infra Phase C: Partner Infrastructure ← Required for Tier 1 activation

**When:** March-December 2027 — builds when 5+ customers and Tier 1 partner conversations begin.
**Trigger:** 5+ paying customers + VA trajectory data from 1+ completed measurement windows.

| Deliverable | Priority | Effort | Notes |
|------------|----------|--------|-------|
| **Lead attribution tracking** | High | 2-3 weeks | New Supabase table: `partner_attributions` (situation_id, escalation_type, partner_id, engagement_value, outcome). API endpoints for recording and querying. |
| **Escalation routing engine** | High | 1-2 weeks | Rule engine: situation type + severity + industry → partner assignment. Initially manual (founder routes); automated in Year 3. |
| **Diagnostic handoff export** | High | 1 week | PDF + structured JSON export: situation card, DA analysis, MA market context, benchmark segments, impact estimates. Partner intake format. |
| **Partner portal (basic)** | Medium | 3-4 weeks | Dashboard: referred clients (anonymised), attributed engagements, revenue share earned, VA trajectory summaries for partner-delivered engagements. |
| **VA trajectory API (partner read-only)** | Medium | 1 week | Scoped API keys for partners to pull outcome data for case studies. Client consent required per situation. |
| **Revenue share tracking** | Medium | 1 week | Track: partner referral → customer subscription → revenue share owed. Manual payout initially. |

**Cost:** $15K-$30K development effort; minimal incremental hosting cost.

**Dependency:** Infra Phase B (customer infrastructure), Phase 9 (enterprise assessment for automated VA measurements).

---

### Infra Phase D: Enterprise & Compliance ← Required for Enterprise tier ($100K+ ACV)

**When:** H1 2028 — triggered by pursuit of enterprise-tier deals.
**Trigger:** 10+ customers, demand for Enterprise tier.

| Deliverable | Priority | Effort | Notes |
|------------|----------|--------|-------|
| **SOC 2 Type II** | 🔴 Required | 6-12 months | $30K-$50K. Access controls, encryption, monitoring, incident response, vendor management. |
| **SSO / SAML** | High | 1-2 weeks | Enterprise customers require SSO (Okta, Azure AD). Supabase Auth supports SAML. |
| **Data residency controls** | High | 2-4 weeks | EU customers may require EU-hosted data. Supabase supports regional projects. |
| **Audit log export** | Medium | 1 week | SOC 2 requires exportable audit logs. Build on existing audit trail infrastructure. |
| **Partner branding engine** | Medium | 4-6 weeks | White-label situation cards, partner logos, branded exports. Only when 3+ partners active. |
| **Revenue share automation** | Medium | 2-3 weeks | Stripe Connect or similar. Only when partner volume justifies. |

**Cost:** $50K-$100K. Largest single item is SOC 2 ($30K-$50K).

**Dependency:** Infra Phase C (partner infrastructure), stable customer base.

---

### HR Milestones (Mapped to Development Phases)

*See `docs/strategy/Agent9_Business_Plan.md` Section 12 for full role descriptions and compensation.*

| Milestone | Trigger | Role | Impact on Development |
|-----------|---------|------|----------------------|
| **Decision point** | Month 12 (~Mar 2027): 2+ customers + 6mo runway | Founder goes full-time | Doubles development velocity; enables Infra Phase C |
| **Hire #1** | Month 13 (~Apr 2027) | Sales / Account Executive | Founder shifts to product + partnerships; frees ~10 hrs/week for engineering |
| **Hire #1b** | Month 15 (~Jun 2027) | Customer Success / Partner Ops | Manages pilot customers + Tier 0 practitioners; enables founder to focus on Tier 1 partner conversations |
| **Hire #2** | Month 18 (~Sep 2027) | Senior Engineer | Takes over Infra Phase C (partner infra), platform stability, CI/CD ownership. Frees founder from production coding. |
| **Hire #3** | Month 24 (~Mar 2028) | Product/Design | Partner portal design, enterprise tier UX, product-led growth. Coincides with Infra Phase D. |
| **Year 3 scale** | 10+ customers / $800K+ ARR | +6-8 FTEs (Partner Manager, 2 engineers, 2 CSMs, marketing, ops) | Partner Manager owns Tier 1-2 firm relationships; dedicated engineer for partner infrastructure |

---

## Cross-Cutting Concerns (All Phases)

### Infrastructure Improvements

| Item | When | Description |
|------|------|-------------|
| Supabase VA tables | Phase 7A | Migration script for `value_assurance_solutions` + `value_assurance_evaluations` |
| Value Assurance persistence | Phase 7A | Replace in-memory dict with Supabase |
| Cloud deployment + auth + monitoring | **Infra Phase A** | Railway/Render + Supabase Cloud + Supabase Auth + Sentry — BLOCKER for outreach |
| Multi-tenant isolation | **Infra Phase B** | Per-customer Supabase project — BLOCKER for first pilot |
| CI/CD pipeline | **Infra Phase B** | GitHub Actions: test → build → deploy to staging |
| Enterprise Assessment Pipeline | Phase 9 | Replace `run_cfo_assessment.py` with enterprise-wide SA→DA batch, Supabase persistence | ✅ SHIPPED |
| PIB email delivery + delegation | Phase 9C | PIB agent, email templates, briefing tokens, delegate flow, situation_actions audit | ✅ SHIPPED |
| Swiss Style brand identity | Phase 10 | Aperture logo, Satoshi font, monochrome palette, PIB email alignment, "Quiet Expert" voice | Planned |
| Scheduled assessment execution | Phase 11+ | Trigger assessment runs on schedule (cron or timer) for automated VA measurement | Planned |
| Unified situation stream | Phase 11A | Merge OpportunitySignal into Situation. Direction-agnostic escalation, confidence gating. | Planned |
| Adaptive calibration loop | Phase 11B | KPI Assistant recommends monitoring profiles, recalibrates from VA outcomes. Core compounding moat. | Planned |
| Audio briefings | Phase 11C | TTS integration, Flash Briefings, workflow-stage framing | Planned |
| Email/Slack notifications | Phase 10+ | PIB email shipped (Phase 9C); Slack integration + VA-specific notifications pending | ⚠️ PARTIAL |
| Remove SA console dropdowns | Phase 10B | Client selector → login screen. Timeframe selector → remove (per-KPI monitoring profiles). | Planned |
| KPI monitoring profiles | Phase 9A | New fields on KPI registry: `comparison_period`, `volatility_band`, etc. | ✅ SHIPPED |
| Partner attribution + escalation routing | **Infra Phase C** | Lead tracking, handoff export, partner portal — enables Tier 1 partnerships | Planned |
| SOC 2 + SSO + data residency | **Infra Phase D** | Enterprise compliance — enables $100K+ ACV tier | Planned |

### Testing Strategy

| Type | Coverage Target | Notes |
|------|----------------|-------|
| Unit tests | All attribution math, confidence scoring, verdict logic | Phase 7A |
| Integration tests | SF HITL → VA registration → measurement → evaluation | Phase 7B |
| Strategy drift scenarios | ALIGNED/DRIFTED/SUPERSEDED with portfolio impact | Phase 7A |
| Opportunity analysis tests | Positive anomaly detection, IS NOT as replication candidates | Phase 8B |
| Unified stream tests | Direction-agnostic escalation, confidence gating, opportunity→SF pipeline | Phase 9G |
| End-to-end demo smoke tests | Full SA → DA → MA → SF → VA pipeline | Phase 7D |

### Documentation Updates Per Phase

- Agent PRD in `docs/prd/agents/`
- Agent row in root `CLAUDE.md` Current Capabilities table
- Agent entry in `src/agents/new/CLAUDE.md` file index
- Workflow YAML in `workflow_definitions/`
- API route documentation

---

## Deprecated Plans

The following plans are superseded by this document:

| File | Original Purpose | Status |
|------|-----------------|--------|
| `HERMES_IMPLEMENTATION_PLAN.md` | Original hackathon sprint plan (Sprint 0-3, day-based) | **DEPRECATED** — all items completed or overtaken |
| `IMPLEMENTATION_PLAN.md` | Nov 2025 refresh (Phase 1-6) | **DEPRECATED** — Phases 1-6 complete, this plan covers Phase 7+ |

These files are retained for historical reference but should not be used for planning.

---

### Phase 10: Brand Identity & UI Polish

**Goal:** Implement the Swiss Style design system across the entire product surface — app UI, landing page, PIB email, and admin screens. Must be complete before any demo recording or prospect-facing deployment.

**Design reference:** `docs/architecture/ui_brand_guidelines.md`

**Design principles:**
- "Swiss Style" AI — monochrome dominance, color only for semantic meaning (red = variance, green = opportunity, blue = AI action)
- "Quiet Expert" voice — BLUF, no alarmism, understated. No exclamation points or urgency language.
- Progressive disclosure — accordions, collapsible sections, never overwhelming
- Seamless marketing-to-product transition — same visual language across decision-studios.com and trydecisionstudio.com

#### 10A: Brand Identity Foundation

| Deliverable | Description | Effort |
|------------|-------------|--------|
| Aperture logo component | Geometric SVG logomark (`BrandLogo.tsx`). Strict, brutalist, no gradients | Small |
| Landing page rebrand | Rewrite hero text to "Quiet Expert" voice. Update color palette to Swiss Style monochrome | Medium |
| App header + navigation | Aperture logo, consistent "Decision Studio" branding across all pages | Small |
| Font stack | Satoshi (editorial sans-serif) with system font fallback | Small |

**Files:** `BrandLogo.tsx`, `LandingPage.tsx`, `Header.tsx`

#### 10B: App UI Polish

| Deliverable | Description | Effort |
|------------|-------------|--------|
| DeepFocusView accordion | Collapsible sections with one-line summary previews. Remove debug `console.log`. | ~3-4 hours |
| ProblemRefinementChat sticky footer | Pin suggested responses + input to bottom. Messages scroll above. | ~1-2 hours |
| RegistryExplorer form layouts | Dedicated form per registry type (KPIs, Data Products, BPs, Principals). "View JSON" toggle for power users. | ~1 day |
| Context Explorer rebrand | Rename to "Principal Dossier". Austere, high-contrast aesthetic. | Small |
| Registry Explorer rebrand | Rename to "Control Panel". Match Swiss Style. | Small |
| Delegated situation badge | "Delegated" badge on situation cards in SA dashboard for delegated KPIs | Small |
| Wire `kpi_evaluated_count` | Replace hardcoded `kpisScanned={14}` with real count from API | Small |

**Files:** `DeepFocusView.tsx`, `ProblemRefinementChat.tsx`, `RegistryExplorer.tsx`, `ContextExplorer.tsx`, `KPITile.tsx`

#### 10C: PIB Email Alignment

| Deliverable | Description | Effort |
|------------|-------------|--------|
| Aperture logo in email header | Inline SVG mark alongside "Principal Intelligence Briefing" | Small |
| Satoshi font stack | With `-apple-system, Helvetica, Arial` fallback for email clients | Small |
| Monochrome severity badges | Remove colored badge backgrounds (red/orange/yellow/blue). Neutral `#f3f4f6` badge, left-border carries severity color | Small |
| "Quiet Expert" copy | "Situations Detected (N)" not "Requiring Your Attention". "Open Situations — Awaiting Response" not "Overdue — No Action Taken" | Small |
| Semantic color only | Red = variance/problem, green = opportunity, blue = AI action (investigate button) | Small |
| Delegation completion | Show delegated-to-me situations in delegate's PIB. Resolve delegator/delegate names. Delegated badge in managed section. | Medium |

**Files:** `src/templates/pib_briefing.html`, `a9_pib_agent.py`

#### Build Order

| Order | Deliverable | Effort | Impact |
|-------|------------|--------|--------|
| 1 | Aperture logo + font stack (10A) | ~2-3 hours | Foundation for everything else |
| 2 | DeepFocusView accordion (10B) | ~3-4 hours | Core demo flow |
| 3 | ProblemRefinementChat sticky footer (10B) | ~1-2 hours | Core demo flow |
| 4 | Landing page rebrand (10A) | ~4-6 hours | First impression for prospects |
| 5 | PIB email alignment (10C) | ~3-4 hours | Executive-facing email |
| 6 | RegistryExplorer forms (10B) | ~1 day | Admin screens |
| 7 | Delegated badge + delegation PIB (10B/10C) | ~4 hours | Completes delegation flow |

---

### Refinement: Dual-Framing Pipeline + Interactive Decision Briefing

**Goal:** Complete the HITL pipeline by (1) surfacing both problem and opportunity framings through debate, (2) transforming the Executive Briefing from a static report into an interactive decision workspace with Solution Refinement, and (3) supporting multi-initiative approval.

**Why now:** The pipeline generates both problem segments and benchmark segments (Phase 8), but only the problem path flows through refinement and debate. The benchmark data (replication targets, internal outperformance) is displayed passively but never enters the HITL conversation. Meanwhile, the Executive Briefing is an 18-page static PDF — the principal can only approve or reject a single recommendation. Completing this makes the pipeline genuinely production-ready before building new capabilities (Phase 9+).

**Architecture reference:** `docs/architecture/hitl_decision_philosophy.md`

**Updated pipeline:**
```
SA → DA → Problem Refinement → Council Debate → Interactive Decision Briefing → VA Tracking
         (problem + opportunity)  (both framings)  (Solution Refinement + Q&A     (multi-initiative)
                                                    + Multi-Initiative Approval)
```

**Design principles:**
- **Always surface both framings** — when DA finds benchmark segments alongside problems, the debate and briefing must address both. Most KPI breaches (90%+) have dimensional variance, meaning both exist.
- **The Briefing IS the decision workspace.** Solution Refinement, Q&A, and approval all happen on the Interactive Decision Briefing page — not scattered across DeepFocusView and a separate briefing page.
- **Present, don't defend.** When the principal challenges a recommendation, provide context — don't argue.
- **Multi-initiative selection.** Real decisions are rarely "approve one option." Principals pursue portfolios: "Execute A immediately, begin B scoping in parallel, table C."

#### Step 1: Dual-Framing Through the Pipeline

**Problem:** SF agent's `_extract_deep_analysis_summary()` and `_trim_deep_analysis_context()` omit `benchmark_segments`. Stage 1 prompts and synthesis don't reference internal benchmarks. Problem Refinement only validates the problem, never asks about replication potential.

| Deliverable | Description |
|------------|-------------|
| SF context enrichment | Include `benchmark_segments` in the DA summary passed to Stage 1 and synthesis prompts. Internal benchmarks become evidence for solution feasibility |
| Problem Refinement expansion | Add a 6th topic: `replication_potential` — "Are the outperforming segments a valid template? What structural differences might prevent replication?" |
| Council recommendation awareness | Refinement LLM considers whether the KPI has strong benchmarks (favoring operational/replication personas) vs. no benchmarks (favoring creative/strategic personas) |
| Debate synthesis enrichment | Synthesis prompt explicitly asks: "How do the internal benchmarks validate or challenge each proposed option?" |

**Files:** `a9_solution_finder_agent.py`, `ProblemRefinementChat.tsx`, refinement API endpoint

#### Step 2: Interactive Decision Briefing (Briefing Page Transformation)

The Executive Briefing page becomes the venue for Solution Refinement — the principal's decision workspace.

**Layout:** Two-panel design (briefing content left, Solution Refinement chat right) — same pattern as DeepFocusView but on the briefing page.

| Deliverable | Description |
|------------|-------------|
| Collapsible sections | Briefing sections collapse/expand with smart defaults — executive summary expanded, Stage 1/2 details collapsed with one-line previews. Accordion pattern from DeepFocusView |
| Solution Refinement chat panel | Right-panel chat embedded in the briefing page. Same neutral voice as Problem Refinement. Activated when principal clicks "Refine & Decide" |
| Suggested questions | Seeded from the briefing's Stakeholder Perspectives and Unresolved Tensions sections — these are the questions the analysis itself identifies as unresolved |
| 4-tier transparency | Each answer tagged with confidence tier: Context Recall (high), Data Query (verifiable via NLP→DPA), Contextual Judgment (medium-high via PC/BC/MA), Organizational Knowledge (honest limitation) |

**What the principal does in Solution Refinement:**
1. **Questions recommendations** — "Why is Option A better given our Q3 cash position?" System responds with data-backed answers
2. **Surfaces opportunity angle** — "C&I's -$9.3M is evidence for Option A, but should replicating their hedging be a standalone initiative?"
3. **Combines or modifies options** — "I want Option A's speed with Option B's governance controls from Day 1"
4. **Selects initiative(s)** — Choose a portfolio: execute A, scope B, table C

**Files:** `ExecutiveBriefing.tsx` (two-panel layout, collapsible sections, chat integration), new `SolutionRefinementChat.tsx` component

#### Step 3: Solution Refinement Backend

| Deliverable | Description |
|------------|-------------|
| Q&A API endpoint | `POST /api/v1/workflows/solutions/{request_id}/qa` — accepts question, returns answer with confidence tier |
| Context assembly | Full context stack: DA SCQA + IS/IS NOT + benchmarks, SF Stage 1/2/3, MA signals, Problem Refinement history, blind spots, unresolved tensions |
| Tier classification | LLM classifies each question as context_recall / data_query / contextual_judgment / organizational_knowledge and responds accordingly |
| NLP → DPA integration | Tier 2 data queries route through existing NLP Interface → Data Product Agent pipeline |
| Topic sequence | 4 topics: `challenge_assumptions` → `explore_combinations` → `assess_risks` → `select_initiatives` |
| Pydantic models | `SolutionRefinementResult` — list of `SelectedInitiative` (option_id, modifications, conditions, priority, timeline_override) |

**Files:** New route in `src/api/routes/workflows.py`, context assembly logic, new models

#### Step 4: Multi-Initiative Approval + VA Tracking

**Problem:** Current approval is single-option ("Approve & Track" for one recommendation). Solution Refinement outputs a portfolio of initiatives.

| Deliverable | Description |
|------------|-------------|
| Initiative selection UI | Checkbox + priority selector per option on the briefing page. Principal marks which to approve, defer, or reject |
| Multi-initiative VA registration | Each approved initiative becomes a separate VA-tracked solution with its own ROI target and monitoring window |
| Briefing update | Post-approval, the briefing page shows all approved initiatives with the principal's modifications and combined expected impact |
| Approval confirmation | Confirmation card: approved initiatives, combined impact range, timeline, monitoring plan, "what happens next" |

**Files:** `ExecutiveBriefing.tsx` (initiative selection UI, approval confirmation), `workflows.py` (multi-initiative approval handler), `a9_value_assurance_agent.py` (batch registration)

#### Step 5: Agent PRD Updates (Ripple Effects)

| Agent PRD | Update Required |
|-----------|----------------|
| Solution Finder | Output must include `blind_spots`, `unresolved_tensions`, stakeholder perspectives per option, `benchmark_evidence` per option. Suggested pre-approval questions |
| Deep Analysis | Document that `benchmark_segments` are a required output consumed by SF and Solution Refinement (not just a UI artifact) |
| NLP Interface | Document support for Solution Refinement context (post-debate data queries) |
| LLM Service | Document Solution Refinement prompt requirements and task routing (Haiku for recall, Sonnet for synthesis) |
| Value Assurance | Support batch `register_solution` for multiple initiatives. Capture Solution Refinement engagement signal |
| HITL Decision Philosophy | Update Gate 2 to describe Interactive Decision Briefing as the primary decision venue with Solution Refinement embedded |

**Effort:** Medium-Large (~2 weeks total). Step 1 (dual-framing) ~2 days. Step 2-3 (Interactive Briefing + backend) ~1 week. Step 4 (multi-initiative) ~3 days. Step 5 (PRDs) ~1 day.

**Build order:** Step 1 → Step 2+3 (parallel frontend/backend) → Step 4 → Step 5

---

## Summary: Build Priority

| Priority | Phase | Scope | Key Deliverable | Status |
|----------|-------|-------|-----------------|--------|
| ~~Done~~ | 7 | Value Assurance | Counterfactual attribution, SF→VA approval handoff | ✅ Complete |
| ~~Done~~ | 7C | Value Assurance UI | ValueAssurancePanel, AttributionBreakdown, PortfolioDashboard, CostOfInactionBanner | ✅ Complete |
| ~~Done~~ | 8 | Opportunity Deep Analysis | BenchmarkSegment, unified DA, Replication Targets UI | ✅ Complete |
| ~~Done~~ | 9 | Enterprise Assessment Pipeline | Batch SA→Supabase, PIB email, deep links, delegation, audit trail | ✅ Complete (2026-04-04) |
| ~~Done~~ | Refinement | Dual-Framing + Interactive Decision Briefing | Benchmark-aware debate, two-panel briefing, Q&A endpoint | ✅ Steps 1-3 + 5 complete |
| ~~Done~~ | Infra A | Production Deployment | Railway + Vercel + Supabase Cloud + BigQuery | ✅ Complete (2026-03-24) |
| ~~Done~~ | Partner Deck | Business Premise & Challenge Presentation | Reveal.js deck, 13 slides | ✅ Complete |
| **WIP** | Demo Video | Remotion Conceptual Demo | 4:00 video, 10 scenes. Needs review pass + final render | In Progress |
| **Next** | 10 | Brand Identity & UI Polish | Swiss Style design system, Aperture logo, PIB email alignment, accordion/forms | Planned |
| **Next** | 11A | Unified Situation Stream | Merge problem/opportunity, direction-agnostic escalation, wire `kpi_evaluated_count` | Planned |
| **Next** | 11B | Adaptive Calibration Loop | KPI Assistant recommends monitoring profiles, recalibration from VA outcomes | Planned |
| **Next** | 11C | Audio Briefings | TTS integration, Flash Briefings, workflow-stage framing | Planned |
| **BLOCKER** | Infra B | Customer Infrastructure | Multi-tenant isolation, CI/CD, provisioning — gates first pilot | Planned (May-Aug 2026) |
| **After** | 12 | Business Optimization | Top-down strategic entry, risk/stakeholder agents | Planned |
| **Year 2** | Infra C | Partner Infrastructure | Lead attribution, escalation routing, partner portal | Planned (Mar-Dec 2027) |
| **Later** | 13 | Extended Solution Finding | Heavyweight evaluation, solution architecture | Planned |
| **Future** | 14 | Innovation Driver | LLM brainstorming, idea incubation | Requires 4 new agents |
| **Year 3** | Infra D | Enterprise & Compliance | SOC 2, SSO, data residency, partner branding | Planned (H1 2028) |
| **Enterprise** | — | Enterprise Tier Roadmap | Decision Journal, Conditional Approval, Scenario Exploration, VA Feedback Loop | Per-customer customization |
