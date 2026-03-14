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
| Value Assurance (outcome measurement) | PRD + workflow YAML done, no agent code |
| Opportunity Deep Analysis (positive anomalies) | Workflow YAML exists, no agent code |
| Business Optimization (top-down strategic) | Workflow YAML exists, no agent code |
| Extended Solution Finding (Risk/Stakeholder agents) | Workflow YAML exists, agents not built |
| Innovation Driver | Workflow YAML exists, agents not built |
| Scheduled SA execution | Script exists, no scheduler |
| Email/Slack notifications | Data model ready, no sending code |
| KPI Assistant UI | API routes exist, no frontend |

---

## Development Phases: Forward Plan

### Phase 7: Value Assurance Agent

**Goal:** Close the insight-to-outcome loop. Prove that HITL-approved solutions actually delivered KPI impact with honest, causal attribution.

**Why first:** This is Agent9's most defensible differentiator. It leverages DA's IS/IS NOT output as control groups for difference-in-differences attribution — the same analysis that diagnosed the problem proves the fix worked. No competing platform does this.

**Reference docs:**
- PRD: `docs/prd/agents/a9_value_assurance_agent_prd.md`
- Workflow YAML: `workflow_definitions/value_assurance.yaml`
- Methodology: `docs/architecture/analytical_methodology_positioning.md`

#### Phase 7A: Agent Core + Supabase Persistence

| Deliverable | Description |
|------------|-------------|
| `a9_value_assurance_agent.py` | Agent implementation with `create_from_registry`, async lifecycle |
| `A9ValueAssuranceAgentConfig` | Pydantic config model in `agent_config_models.py` |
| Agent card | `cards/a9_value_assurance_agent_card.md` |
| Pydantic models | `value_assurance_models.py` — rewrite existing models + add attribution types |
| Supabase migration | `value_assurance_solutions` + `value_assurance_evaluations` tables |
| `register_solution` entrypoint | Capture SF output + DA context + MA context + strategy snapshot |
| `evaluate_solution_impact` entrypoint | Counterfactual attribution (control group, market, seasonal, trend) |
| `check_strategy_alignment` entrypoint | Diff current registry state against approval-time snapshot |
| Confidence scoring | Factor-based confidence (control group quality, data volume, market data, confounders) |
| Unit tests | Attribution math, confidence scoring, verdict logic, strategy drift detection |

**Dependencies:** None — all upstream agents (SA, DA, MA, SF) already produce the required data.

#### Phase 7B: API Routes + Existing Endpoint Migration

| Deliverable | Description |
|------------|-------------|
| Refactor `value_assurance.py` routes | Delegate existing 5 endpoints to VA Agent (replace in-memory dict) |
| `GET /portfolio` | Aggregated portfolio dashboard data (strategy-aware) |
| `POST /solutions/{id}/narrative` | LLM-generated executive narrative |
| `GET /inaction-costs` | Projected cost of unaddressed situations |
| `POST /inaction-costs/{situation_id}` | Calculate specific inaction cost |
| Integration tests | End-to-end: SF HITL → VA registration → measurement → evaluation |

#### Phase 7C: Decision Studio UI

| Deliverable | Description |
|------------|-------------|
| Value Assurance panel | Post-HITL tracking view: expected impact, measurement countdown, interim trend |
| Attribution breakdown chart | Waterfall/stacked bar: attributable vs. market vs. seasonal vs. control |
| Verdict badge | VALIDATED / PARTIAL / FAILED with confidence indicator |
| Strategy alignment indicator | ALIGNED / DRIFTED / SUPERSEDED badges with drift explanation |
| Portfolio dashboard | Summary cards, solution table, cost of inaction, cumulative value chart |
| Cost of Inaction display | Show at HITL decision point alongside SF options |
| Narrative display | LLM-generated executive summary per solution |

#### Phase 7D: Orchestrator Integration

| Deliverable | Description |
|------------|-------------|
| Auto-registration trigger | Wire SF HITL approval event → VA `register_solution` |
| Orchestrator workflow method | `run_value_assurance()` on Orchestrator |
| Agent dependency graph update | VA depends on SA, DA, MA, SF, PC, DP |
| CLAUDE.md update | Add VA to Current Capabilities table |

---

### Phase 8: Opportunity Deep Analysis

**Goal:** Mirror the Problem DA pipeline for positive anomalies. Use the same KT Is/Is Not methodology to discover WHY something is working well and whether it can be replicated.

**Why second:** Same methodology, same data infrastructure, same UI patterns. High leverage — executives love hearing "here's what's working and why" as much as "here's what's broken." Feeds directly into VA for replication measurement.

**Reference docs:**
- Workflow YAML: `workflow_definitions/opportunity_deep_analysis.yaml`

#### Phase 8A: SA Opportunity Detection

| Deliverable | Description |
|------------|-------------|
| SA opportunity cards | Detect positive anomalies (KPI significantly ABOVE threshold or improving rapidly) |
| Opportunity card model | Extend `SituationCard` or create `OpportunityCard` with positive framing |
| UI opportunity cards | Green-themed cards in Decision Studio (vs. red/amber for problems) |

#### Phase 8B: Opportunity Analysis via DA

| Deliverable | Description |
|------------|-------------|
| DA opportunity mode | Is/Is Not analysis for positive anomalies — "WHERE is it working? WHERE is it NOT?" |
| Replication candidates | IS NOT column = dimensions where the opportunity hasn't spread yet |
| MA integration | "Is this a market tailwind we're riding, or did we do something unique?" |
| SCQA for opportunities | Situation/Complication/Question/Answer framed positively |

#### Phase 8C: Opportunity → Solution Finding → VA

| Deliverable | Description |
|------------|-------------|
| SF opportunity mode | Generate options for scaling/replicating the opportunity |
| VA opportunity tracking | Measure whether replication attempts succeed in IS NOT dimensions |

**Decision:** Implement as a mode on DA Agent (not a separate `A9_Opportunity_Analysis_Agent`). The methodology is identical — only the framing differs.

---

### Phase 9: Business Optimization Workflow

**Goal:** Top-down strategic entry point for board/executive-driven initiatives. Complements the bottom-up SA → DA pipeline with a strategy-first approach.

**Why third:** Shows Agent9 handles proactive strategy, not just reactive KPI monitoring. Requires new agents but reuses SF and VA.

**Reference docs:**
- Workflow YAML: `workflow_definitions/business_optimization.yaml`

#### Phase 9A: New Agents Required

| Agent | Purpose | Complexity |
|-------|---------|-----------|
| `A9_Risk_Analysis_Agent` | Weighted risk scoring for proposed initiatives | Medium — PRD exists (dead code), needs rewrite |
| `A9_Stakeholder_Analysis_Agent` | Identify stakeholders, estimate support/resistance | Medium — new |
| `A9_Business_Optimization_Agent` | Assess operations, identify optimization signals | Medium — new |

#### Phase 9B: Workflow Integration

| Deliverable | Description |
|------------|-------------|
| Orchestrator method | `run_business_optimization()` |
| Board input capture | UI for executive-initiated strategic directives |
| MA integration | Market context for strategic initiatives |
| SF connection | Route optimization recommendations through existing SF pipeline |
| VA connection | Track whether strategic initiatives deliver expected value |

#### Phase 9C: UI

| Deliverable | Description |
|------------|-------------|
| Strategy initiative panel | New section in Decision Studio for top-down initiatives |
| Risk/stakeholder views | Visualize risk assessments and stakeholder maps |

---

### Phase 10: Extended Solution Finding

**Goal:** Heavyweight solution evaluation for strategic decisions. Adds Risk Analysis, Stakeholder Analysis, Solution Architect, and Implementation Planner to the SF pipeline.

**Why fourth:** The current SF (3×Stage1 + synthesis) handles routine KPI fixes well. Extended SF is for large-scale decisions where risk assessment and stakeholder buy-in matter more.

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

### Phase 11: Innovation Driver (Future)

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
| Scheduled SA execution | Phase 7D or 8A | Trigger SA scans on schedule (cron or timer) for automated VA measurement |
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

| Priority | Phase | Scope | Key Deliverable | Video-Ready? |
|----------|-------|-------|-----------------|-------------|
| **Now** | 7 | Value Assurance | Counterfactual attribution, portfolio ROI, cost of inaction | Yes — closes the loop |
| **Pre-Video** | — | UI Polish | Chat sticky footer, DA accordion, registry forms | Required before recording |
| **Next** | 8 | Opportunity Deep Analysis | Positive anomaly Is/Is Not, replication candidates | Yes — "what's working" |
| **After** | 9 | Business Optimization | Top-down strategic entry, risk/stakeholder agents | Yes — strategy-driven |
| **Later** | 10 | Extended Solution Finding | Heavyweight evaluation, solution architecture | Incremental |
| **Future** | 11 | Innovation Driver | LLM brainstorming, idea incubation | Requires 4 new agents |
