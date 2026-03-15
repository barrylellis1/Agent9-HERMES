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
- "Approve & Track" button in DeepFocusView State F with loading/error/success states
- 42 unit tests passing

**Remaining (deferred):**
- VA UI components (ValueAssurancePanel, PortfolioDashboard) not yet wired into DeepFocusView post-approval — show after HITL approval or in briefing view
- Orchestrator `run_value_assurance()` method not added — VA is called directly from workflow route

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
| Future: Briefing Agent input | Assessment results become the input for audio Flash Briefings and mindmap generation |

**Dependencies:** Phases 7-8 complete (VA tracking, benchmark segments). Supabase operational.

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

## Cross-Cutting Concerns (All Phases)

### Infrastructure Improvements

| Item | When | Description |
|------|------|-------------|
| Supabase VA tables | Phase 7A | Migration script for `value_assurance_solutions` + `value_assurance_evaluations` |
| Value Assurance persistence | Phase 7A | Replace in-memory dict with Supabase |
| Enterprise Assessment Pipeline | Phase 9 | Replace `run_cfo_assessment.py` with enterprise-wide SA→DA batch, Supabase persistence |
| Scheduled assessment execution | Phase 9B+ | Trigger assessment runs on schedule (cron or timer) for automated VA measurement |
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

## Summary: Build Priority

| Priority | Phase | Scope | Key Deliverable | Status |
|----------|-------|-------|-----------------|--------|
| ~~Done~~ | 7 | Value Assurance | Counterfactual attribution, SF→VA approval handoff | ✅ Complete |
| ~~Done~~ | 8 | Opportunity Deep Analysis | BenchmarkSegment, unified DA, Replication Targets UI | ✅ Complete (design revised) |
| **Pre-Video** | — | UI Polish | Chat sticky footer, DA accordion, registry forms | Not started |
| **Next** | 9 | Enterprise Assessment Pipeline | Offline SA→DA batch for all KPIs, Supabase persistence, pre-analyzed findings | Planned |
| **After** | 10 | Business Optimization | Top-down strategic entry, risk/stakeholder agents | Planned |
| **Later** | 11 | Extended Solution Finding | Heavyweight evaluation, solution architecture | Planned |
| **Future** | 12 | Innovation Driver | LLM brainstorming, idea incubation | Requires 4 new agents |
