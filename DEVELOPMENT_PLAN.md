# Agent9-HERMES Development Plan

**Created:** 2026-03-14
**Status:** Active
**Supersedes:** `IMPLEMENTATION_PLAN.md` (Nov 2025), `HERMES_IMPLEMENTATION_PLAN.md` (original hackathon)

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
| Enterprise Assessment Pipeline (offline SA→DA batch) | Planned (Phase 9) — replaces `run_cfo_assessment.py` |
| Business Optimization (top-down strategic) | Workflow YAML exists, no agent code |
| Extended Solution Finding (Risk/Stakeholder agents) | Workflow YAML exists, agents not built |
| Innovation Driver | Workflow YAML exists, agents not built |
| Scheduled SA execution | Script exists, no scheduler |
| Email/Slack notifications | Data model ready, no sending code |
| KPI Assistant UI | API routes exist, no frontend |

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

### Phase 7C: Value Assurance UI Integration

**Status:** Planned. Components built, not wired.

**Context:** Phase 7 delivered 4 React components (ValueAssurancePanel, AttributionBreakdown, PortfolioDashboard, CostOfInactionBanner) and 7 VA API endpoints. None of the components are imported or used anywhere in the UI. No VA API calls exist in `client.ts`. The VA backend is fully operational — the gap is entirely in the frontend.

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

### Phase 9: Enterprise Assessment Pipeline

**Goal:** Replace the interactive dashboard-first model with offline, enterprise-wide analysis. Agent9 should not be perceived as "just another dashboard" — executives already have dashboards. The value is automated analysis, not KPI display.

**Why next:** This is the original product vision. The SA dashboard was a necessary stepping stone to demonstrate capabilities, but the core differentiator is pre-computed analysis: when an executive opens Agent9, they see findings, not raw numbers. This also enables the Briefing Agent (audio/mindmap output) and scheduled VA measurement.

**Design principles:**
- Assessment is **enterprise-level first** — all registered KPIs across all data products and business processes
- SA is a **sensor** — fetches values and computes severity from threshold distance. No problem/opportunity labeling.
- DA is the **analyst** — for each flagged KPI, runs Is/Is Not to produce both problem segments AND benchmark segments
- Principal-specific views are **layered on top** — the same assessment data, filtered by the principal's business processes
- SF and HITL remain **interactive** — pre-compute the analysis, keep humans in the decision loop

#### Phase 9A: Data Model + Persistence

| Deliverable | Description |
|------------|-------------|
| Supabase migration | `assessment_runs` (id, timestamp, status, kpi_count, config) |
| Supabase migration | `kpi_assessments` (id, run_id, kpi_id, kpi_value, severity, da_result JSONB, benchmark_segments JSONB) |
| Assessment models | Pydantic models: `AssessmentRun`, `KPIAssessment`, `AssessmentConfig` |

#### Phase 9B: Assessment Engine (replaces `run_cfo_assessment.py`)

| Deliverable | Description |
|------------|-------------|
| `run_enterprise_assessment.py` | New script: iterates ALL registered KPIs, runs SA measurement + DA analysis per KPI, persists to Supabase |
| Proper agent instantiation | Uses RegistryFactory + Orchestrator (not legacy `create_situation_awareness_agent`) |
| Configurable severity floor | Only run DA for KPIs above a configurable severity threshold |
| Idempotent runs | Assessment run ID prevents duplicate analysis for the same KPI in the same period |
| Progress logging | Per-KPI progress with timing, errors logged but non-fatal |

#### Phase 9C: API + UI

| Deliverable | Description |
|------------|-------------|
| `GET /assessments/latest` | Returns most recent assessment run with findings, filterable by principal/business_process |
| `GET /assessments/{run_id}` | Full assessment detail |
| `POST /assessments/run` | Trigger assessment on-demand (optional — may be CLI-only initially) |
| Landing page refactor | Dashboard reads from assessment API, shows pre-analyzed findings with headline summaries |
| KPI tile redesign | One tile per KPI showing DA headline (not just value + threshold), click drills into pre-loaded DeepFocusView |

#### Phase 9D: Principal-Specific Layering

| Deliverable | Description |
|------------|-------------|
| Assessment filtering | Filter assessment results by principal's business processes and KPI ownership |
| Personalized findings | "3 findings require your attention" — ranked by relevance to the principal |

#### Phase 9E: Briefing Agent — Audio Intelligence

**Goal:** Transform assessment results into consumable audio briefings. This is the "not a dashboard" differentiator — an executive gets a 60-second Flash Briefing during their commute instead of clicking through tiles.

**Prerequisite:** Phase 9B (assessment engine produces persisted results to summarize).

**PRD revision required:** The existing concept PRD (`docs/prd/agents/a9_briefing_agent_concept.md`) needs updating:
- Input model: `assessment_run_id` / `kpi_assessment_ids` instead of `source_uris`
- Personas: CFO, CEO, COO, Finance Manager (not Investor, Product Owner, Lead Engineer)
- Remove references to `A9_Implementation_Tracker_Agent` and `A9_Risk_Management_Agent` (don't exist)
- Mindmap capability deferred to Phase 10+ (requires graph visualization frontend)

| Deliverable | Description |
|------------|-------------|
| `a9_briefing_agent.py` | Agent with `generate_audio_briefing` entrypoint. LLM summarization → TTS API call |
| Briefing models | `BriefingRequest` (assessment_run_id, principal_id, workflow_stage), `BriefingResponse` (audio_url, transcript, bullet_points) |
| TTS integration | One provider to start (OpenAI TTS, ElevenLabs, or Google Cloud TTS) |
| Workflow-stage framing | SA → "Flash Briefing", DA → "Detective's Summary", SF → "Council Debate", VA → "ROI Post-Mortem" |
| Audio player UI | Inline audio player + transcript + bullet points in Decision Studio |
| API endpoint | `POST /api/v1/briefings/generate` — trigger on-demand or auto-generate after assessment |

**Deferred to Phase 10+:**
- Mindmap generation (graph visualization frontend, entity extraction)
- Multi-speaker podcast-style audio (conversational TTS — requires more complex TTS orchestration)

**Dependencies:** Phase 9B (assessment results in Supabase), LLM Service Agent (summarization), external TTS API key.

**Replaces:** `run_cfo_assessment.py` (outdated, SA-only, legacy agent instantiation, CFO-specific).

---

### Phase 10: Business Optimization Workflow

**Goal:** Top-down strategic entry point for board/executive-driven initiatives. Complements the bottom-up SA → DA pipeline with a strategy-first approach.

**Why after assessment:** Shows Agent9 handles proactive strategy, not just reactive KPI monitoring. Requires new agents but reuses SF and VA. The Enterprise Assessment Pipeline (Phase 9) provides the data foundation.

**Reference docs:**
- Workflow YAML: `workflow_definitions/business_optimization.yaml`

#### Phase 10A: New Agents Required

| Agent | Purpose | Complexity |
|-------|---------|-----------|
| `A9_Risk_Analysis_Agent` | Weighted risk scoring for proposed initiatives | Medium — PRD exists (dead code), needs rewrite |
| `A9_Stakeholder_Analysis_Agent` | Identify stakeholders, estimate support/resistance | Medium — new |
| `A9_Business_Optimization_Agent` | Assess operations, identify optimization signals | Medium — new |

#### Phase 10B: Workflow Integration

| Deliverable | Description |
|------------|-------------|
| Orchestrator method | `run_business_optimization()` |
| Board input capture | UI for executive-initiated strategic directives |
| MA integration | Market context for strategic initiatives |
| SF connection | Route optimization recommendations through existing SF pipeline |
| VA connection | Track whether strategic initiatives deliver expected value |

#### Phase 10C: UI

| Deliverable | Description |
|------------|-------------|
| Strategy initiative panel | New section in Decision Studio for top-down initiatives |
| Risk/stakeholder views | Visualize risk assessments and stakeholder maps |

---

### Phase 11: Extended Solution Finding

**Goal:** Heavyweight solution evaluation for strategic decisions. Adds Risk Analysis, Stakeholder Analysis, Solution Architect, and Implementation Planner to the SF pipeline.

**Why later:** The current SF (3×Stage1 + synthesis) handles routine KPI fixes well. Extended SF is for large-scale decisions where risk assessment and stakeholder buy-in matter more.

**Reference docs:**
- Workflow YAML: `workflow_definitions/solution_finding.yaml` (extended version)
- Workflow YAML: `workflow_definitions/solution_deployment.yaml`

#### New Agents Required

| Agent | Purpose | Notes |
|-------|---------|-------|
| `A9_Solution_Architect_Agent` | Technical/organizational solution design | New |
| `A9_Implementation_Planner_Agent` | High-level implementation planning | New — lightweight, not task tracking |
| `A9_Stakeholder_Engagement_Agent` | Manage stakeholder communication workflows | New |

**Note:** Solution Deployment workflow is intentionally NOT built as a full Agent9 workflow. Implementation tracking is handled by external PM tools (Jira, Monday, Asana). Agent9 captures `implementation_start` and `implementation_confirmed` timestamps for VA purposes only.

---

### Phase 12: Innovation Driver (Future)

**Goal:** LLM-powered brainstorming, idea incubation, and opportunity shaping.

**Why last:** Requires 4 new agents (Innovation, GenAI Expert, Solution Architect, Implementation Planner). Hard to demonstrate measurable value. Doesn't leverage the KT/IS NOT advantage.

**One interesting angle:** If VA shows that a certain type of solution consistently validates (e.g., supplier renegotiation), Innovation Driver could propose proactive application of that pattern to other KPIs before they breach. This creates a learning loop.

**Reference docs:**
- Workflow YAML: `workflow_definitions/innovation_driver.yaml`

**Status:** Not scoped in detail. Revisit after Phases 7-9 are solid.

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
| Enterprise Assessment Pipeline | Phase 9 | Replace `run_cfo_assessment.py` with enterprise-wide SA→DA batch, Supabase persistence |
| Scheduled assessment execution | Phase 9B+ | Trigger assessment runs on schedule (cron or timer) for automated VA measurement |
| Partner attribution + escalation routing | **Infra Phase C** | Lead tracking, handoff export, partner portal — enables Tier 1 partnerships |
| SOC 2 + SSO + data residency | **Infra Phase D** | Enterprise compliance — enables $100K+ ACV tier |
| Email/Slack notifications | Phase 7C or later | Notify principals when solutions are VALIDATED / FAILED |

### Testing Strategy

| Type | Coverage Target | Notes |
|------|----------------|-------|
| Unit tests | All attribution math, confidence scoring, verdict logic | Phase 7A |
| Integration tests | SF HITL → VA registration → measurement → evaluation | Phase 7B |
| Strategy drift scenarios | ALIGNED/DRIFTED/SUPERSEDED with portfolio impact | Phase 7A |
| Opportunity analysis tests | Positive anomaly detection, IS NOT as replication candidates | Phase 8B |
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

## Pre-Video: Decision Studio UI Polish

**Goal:** Fix UX issues that would look clunky on camera. These are not new features — they're refinements to existing screens that make the current pipeline presentable for recording.

**When:** After Phase 7 (VA) or in parallel. Must be complete before any video recording.

### Fix 1: ProblemRefinementChat — Sticky Footer (Priority: High)

**Problem:** User must scroll up to read the DA question, then scroll down to find suggested responses, then scroll further to the input field. Ping-pong scrolling breaks the conversation flow on camera.

**Fix:** Pin suggested responses and text input to the bottom of the component (sticky footer). Messages scroll independently above. The latest message auto-scrolls into view directly above the suggestions.

```
┌─────────────────────────────────────┐
│  Progress: ████░░░░░░ 2/5 topics    │
├─────────────────────────────────────┤
│                                     │
│  [Messages area — scrollable]       │
│  Agent: "What's the primary..."     │
│  You: "Supplier cost spike..."      │
│  Agent: "Which regions are..."      │  ← auto-scrolls to latest
│                                     │
├─────────────────────────────────────┤  ← sticky divider
│  Suggested: [Region East] [All]     │  ← always visible
│  ┌─────────────────────┐ [Send]     │
│  │ Type your response...│ [Skip]    │  ← always visible
│  └─────────────────────┘            │
└─────────────────────────────────────┘
```

**Effort:** Small (~1-2 hours)
**File:** `decision-studio-ui/src/components/ProblemRefinementChat.tsx`

### Fix 2: DeepFocusView — Accordion Collapse (Priority: High)

**Problem:** Left panel has 5-6 analysis sections all expanded inline. User scrolls through 2000+ pixels of content. Hard to find what you need. Looks overwhelming on camera.

**Fix:** Collapsible accordion sections with smart defaults and one-line summary previews:

```
▼ Executive Briefing              ← expanded by default (the headline)
▶ Root Cause Analysis             ← collapsed: "3 root causes identified"
▶ Variance Analysis (Is/Is Not)   ← collapsed: "4 dimensions analyzed"
▶ Market Intelligence             ← collapsed: "3 signals detected"
▶ Dimension Breakdown             ← collapsed: "Region × Product"
▶ Strategic Options               ← collapsed: "3 options generated"
```

Each section shows a compact summary line when collapsed. Click chevron to expand. Only one or two sections open at a time for clean screen recording.

Also: remove debug `console.log` on line 314 that spams every render.

**Effort:** Medium (~3-4 hours)
**File:** `decision-studio-ui/src/components/views/DeepFocusView.tsx`

### Fix 3: RegistryExplorer — Form-Based Editing (Priority: Medium)

**Problem:** 4 of 5 registries (KPIs, Data Products, Business Processes, Principals) use a raw JSON textarea for editing. Users must manually construct valid JSON. No field labels, no validation, no guidance. Not usable for a demo or customer-facing video.

**Fix:** Build dedicated form layouts per registry type with labeled fields, inline validation, and a brief instruction line. Keep raw JSON as a "View JSON" toggle for power users.

| Registry | Key Form Fields | Complexity |
|----------|----------------|-----------|
| **KPIs** | name, description, unit, upper/lower thresholds, data_product_id, business_process, metadata.lens_affinity | Medium — nested threshold object |
| **Data Products** | name, description, source_type, connection_profile, tables/views list | Medium — array of tables |
| **Business Processes** | name, domain, description, parent_process | Simple — flat fields |
| **Principals** | name, role, decision_style, priorities (tag array), business_processes (tag array) | Medium — array fields |

Each form includes:
- Labeled input fields with placeholder text
- Inline validation for required fields and numeric values
- Instruction line at top: *"Edit KPI thresholds and metadata. Changes are saved to the registry."*
- "View JSON" toggle to show raw payload (advanced mode)

**Effort:** Medium-Large (~1 day for all 4 registries)
**File:** `decision-studio-ui/src/pages/RegistryExplorer.tsx`

### Build Order

| Order | Fix | Effort | Video Impact |
|-------|-----|--------|-------------|
| 1 | ProblemRefinementChat sticky footer | ~1-2 hours | High — core demo flow |
| 2 | DeepFocusView accordion collapse | ~3-4 hours | High — analytical centerpiece |
| 3 | RegistryExplorer form layouts | ~1 day | Medium — admin screens, shown briefly |

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
| **Next** | 7C | Value Assurance UI | Wire VA components into Executive Briefing, Dashboard, portfolio view | Planned — components built, not wired |
| ~~Done~~ | 8 | Opportunity Deep Analysis | BenchmarkSegment, unified DA, Replication Targets UI | ✅ Complete (design revised) |
| ~~Done~~ | Pre-Video | UI Polish | Chat sticky footer, DA accordion, registry forms, persona passthrough | ✅ Complete |
| ~~Done~~ | Refinement | Dual-Framing + Interactive Decision Briefing | Steps 1-3 complete: benchmark-aware debate, two-panel briefing workspace, Q&A endpoint. Step 4 (multi-initiative approval) deferred. Step 5 (PRD updates) complete. | ✅ Steps 1-3 + 5 complete |
| **BLOCKER** | Infra A | Production Deployment | Cloud hosting, auth, monitoring, domain — gates all outreach | Planned (Apr-May 2026) |
| **Next** | 9A-D | Enterprise Assessment Pipeline | Offline SA→DA batch, Supabase persistence, pre-analyzed findings | Planned |
| **Next** | 9E | Briefing Agent — Audio Intelligence | Flash Briefings, persona-tailored TTS, workflow-stage framing | Planned (after 9B) |
| **BLOCKER** | Infra B | Customer Infrastructure | Multi-tenant isolation, CI/CD, provisioning — gates first pilot | Planned (May-Aug 2026) |
| **After** | 10 | Business Optimization | Top-down strategic entry, risk/stakeholder agents | Planned |
| **Year 2** | Infra C | Partner Infrastructure | Lead attribution, escalation routing, handoff export, partner portal | Planned (Mar-Dec 2027, triggered by 5+ customers) |
| **Later** | 11 | Extended Solution Finding | Heavyweight evaluation, solution architecture | Planned |
| **Future** | 12 | Innovation Driver | LLM brainstorming, idea incubation | Requires 4 new agents |
| **Year 3** | Infra D | Enterprise & Compliance | SOC 2, SSO, data residency, partner branding automation | Planned (H1 2028, triggered by Enterprise tier demand) |
| **Enterprise** | — | Enterprise Tier Roadmap | Decision Journal, Conditional Approval, Scenario Exploration, Stakeholder Pre-Briefing, VA Feedback Loop, Principal Learning Profile | Per-customer customization — not CaaS core |
