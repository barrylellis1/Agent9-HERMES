# Agent9-HERMES Development Plan

**Created:** 2026-03-14
**Last updated:** 2026-04-06
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
| Swiss Style design system | Monochrome base, Satoshi font, semantic color only (red=variance, green=growth, blue=AI) |
| Dashboard visual refresh | KPI tiles, situation grid, header — align to brand guidelines |
| KPI tile improvements | Comparison period badge (YoY/QoQ/MoM), threshold reference line, wire real `kpi_evaluated_count` |
| Client selector → login screen | Remove client dropdown from SA Console header |
| Remove debug artifacts | `console.log` statements, hardcoded counts, placeholder text |

#### 10B: PIB Email Template Refresh

| Deliverable | Description |
|------------|-------------|
| Swiss Style email | Monochrome base, Aperture logo mark, Satoshi or system font stack |
| Section hierarchy | Clear visual weight: New Situations → Urgency → Solutions → Managed |
| Mobile-safe layout | Tested on Gmail mobile + desktop |

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

#### 11E: Audio Briefings

**Goal:** 60-second audio flash briefing — the "not a dashboard" differentiator for commuting executives.

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
