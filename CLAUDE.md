# Agent9-HERMES Project

## MANDATORY: Always Use restart_decision_studio_ui.ps1

- **NEVER** start backend or frontend independently (`uvicorn ...` or `npm run dev` directly)
- **ALWAYS** use `.\restart_decision_studio_ui.ps1` to start/restart the full stack (FastAPI + React)
- This script handles port cleanup, Docker/Supabase startup, and process sequencing
- **When running via Claude Code (bash tool)**, always use the execution policy bypass form:
  ```
  powershell.exe -ExecutionPolicy Bypass -File restart_decision_studio_ui.ps1
  ```
- Run from project root in PowerShell: `.\restart_decision_studio_ui.ps1`

---

## Production Deployment

**PUSH TO GITHUB = DEPLOY TO PRODUCTION**

- **Every push to `master` branch triggers automatic deployment:**
  - Frontend (React/Vite): Auto-deploys to **Vercel** within 2–3 minutes
  - Backend (FastAPI): Auto-deploys to **Railway** within 2–3 minutes
- **Do NOT deploy manually** — rely on GitHub automation
- **Verify both services live:**
  - Frontend: Vercel dashboard → deployments tab
  - Backend: Railway dashboard → deployment logs
- **Pre-push checklist:**
  - Run `npm run build` in `decision-studio-ui/` to catch TypeScript errors (Vercel will fail without these)
  - Run `.venv/Scripts/pytest tests/unit/ --timeout=15` to verify unit tests pass
  - Review `git diff HEAD` to confirm intended changes only

---

## Project Overview

Agent9-HERMES is a multi-agent automation system delivering automated business insights through
orchestrated AI workflows. ~100K lines of backend and UI code, 10 months of development.

**Status:** Production-capable demo system. Supabase-backed registries. BigQuery and DuckDB data sources.

---

## Current Capabilities

### Working End-to-End Pipelines

1. **Situation Awareness → Deep Analysis → Solution Finding**
   - SA Agent detects KPI threshold breaches → situation cards
   - DA Agent runs dimensional Is/Is Not analysis with change-point detection
   - SF Agent runs multi-call architecture: 3 parallel Stage 1 LLM calls (one per persona) + 1 synthesis call
   - Follow-up NL questions → NLP Interface → Data Product Agent SQL → inline results
   - HITL approval workflow for solution recommendations

2. **Data Product Onboarding (Admin Console)**
   - 8-step orchestrated workflow: inspect schema → contract YAML → register → KPI registration → BP mapping → principal ownership → QA
   - Supports DuckDB, BigQuery, PostgreSQL

3. **KPI Assistant (API Only — No UI)**
   - 4 endpoints at `/api/v1/data-product-onboarding/kpi-assistant/`

### Implemented Agents (14 Total)

| Agent | Key Capabilities | Status |
|---|---|---|
| **A9_Orchestrator_Agent** | Agent registry (singleton), dependency resolution, 7 workflow methods | Operational |
| **A9_Principal_Context_Agent** | 8 principal profiles, dual lookup, business process mapping | Operational |
| **A9_Situation_Awareness_Agent** | KPI monitoring, anomaly + opportunity detection, situation + opportunity cards, NL query, per-KPI monitoring profiles (Phase 9A), single-KPI assessment mode | Operational |
| **A9_Deep_Analysis_Agent** | Is/Is Not analysis, change-point detection, SCQA framing, BigQuery routing | Operational |
| **A9_Solution_Finder_Agent** | 3×Stage1 parallel LLM + synthesis, trade-off matrix, quantified impact, HITL, MA enrichment | Operational |
| **A9_Market_Analysis_Agent** | Perplexity web search + Claude synthesis → market signals, competitor context (LLM-only fallback) | Operational |
| **A9_Data_Product_Agent** | Schema inspection (DuckDB/BigQuery/Postgres), contract YAML, SQL execution | Operational |
| **A9_Data_Governance_Agent** | Business term translation, KPI mapping, registry validation; MVP allows all | Operational |
| **A9_NLP_Interface_Agent** | Deterministic regex parsing (no LLM), TopN/timeframe/grouping extraction | Operational |
| **A9_LLM_Service_Agent** | Multi-provider (Claude/Anthropic), model routing, token tracking, guardrails | Operational |
| **A9_KPI_Assistant_Agent** | LLM KPI suggestions, conversational refinement, contract updates | API-only (no UI) |
| **A9_PIB_Agent** | Briefing composition from assessment results, Jinja2 email rendering, SMTP delivery, delegation flow, briefing tokens | Operational |
| **A9_Data_Product_MCP_Service_Agent** | SQL execution via MCP | **DEPRECATED** (remove after 2025-11-30) |
| **A9_Risk_Analysis_Agent** | Weighted risk scoring | **Dead code** — no tests, no registration |

### What's NOT Built Yet

- KPI Assistant Streamlit/React UI — API routes exist, no frontend panel
- Remaining agents referenced in workflow YAMLs (Risk Management, Stakeholder, etc.)
- Registry Maintenance UI — placeholder in Admin Console
- Data Governance Admin UI — placeholder in Admin Console
- Scheduled/offline SA execution — `run_enterprise_assessment.py` operational (Phase 9A–9C shipped); landing page refactor pending
- Email/Slack notification to principals — PIB email delivery shipped (Phase 9C); Slack integration pending
- Value Assurance Supabase persistence — in-memory store only (MVP)
- Per-KPI monitoring profiles — registry model fields added (Phase 9A complete); SA runtime use pending Phase 9B

### API Surface (~70 endpoints)

- `/api/v1/workflows/` — situations, deep-analysis, solutions, data-product-onboarding
- `/api/v1/value-assurance/` — accepted solutions CRUD + ROI validation check (5 endpoints)
- `/api/v1/registry/` — full CRUD for KPIs, Principals, Data Products, Business Processes, Glossary
- `/api/v1/data-product-onboarding/kpi-assistant/` — suggest, chat, validate, finalize
- `/api/v1/connection-profiles/` — CRUD for database connection profiles
- `/api/v1/assessments/` — enterprise assessment runs + KPI assessment results (3 endpoints)
- `/api/v1/pib/` — briefing runs, token resolution, delegation, delegate suggestions (5 endpoints)

### Database Backends

| Backend | Status |
|---|---|
| DuckDB | Production-ready (local dev) |
| PostgreSQL / Supabase | Production-ready (cloud) |
| BigQuery | Production-ready (read-only analytics) |

---

## Technology Stack

- **Backend:** Python 3.11, FastAPI, async/await, Pydantic v2
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS (decision-studio-ui/)
- **Databases:** DuckDB (local), Supabase/PostgreSQL (cloud), BigQuery (analytics)
- **LLM:** A9_LLM_Service_Agent routes all calls — Claude (Anthropic) + GPT-4 (OpenAI)
- **Protocol:** A2A (Agent-to-Agent) with standardized Pydantic I/O models
- **Registries:** 6 YAML-backed registries with Supabase dual-persistence

---

## Critical Protocol Requirements (NON-NEGOTIABLE)

These apply when working anywhere in the codebase. See `src/agents/new/CLAUDE.md` for code examples.

1. **Agent Instantiation** 🔴
   - NEVER: `agent = AgentClass(config)`
   - ALWAYS: `await AgentRegistry.get_agent("name")` or `AgentClass.create_from_registry(config)`

2. **Pydantic Models Only** 🔴
   - ALL agent I/O must use Pydantic models — no raw dicts in agent-to-agent communication

3. **LLM Call Routing** 🔴
   - ALL LLM calls MUST go through A9_LLM_Service_Agent via Orchestrator
   - NO direct openai/anthropic imports in agent files (except a9_llm_service_agent.py)

4. **Logging Standard** 🔴
   - No `print()` statements; no direct `logging.getLogger()` in agents
   - Target: A9_SharedLogger (not yet implemented — interim: `logging.getLogger(__name__)`)

5. **Lifecycle Methods** 🔴
   - Implement `create()`, `connect()`, `disconnect()` — all async

---

## Project Structure

```
Agent9-HERMES/
├── src/
│   ├── agents/new/         # Core agent implementations (+ CLAUDE.md)
│   ├── api/                # FastAPI routes and runtime
│   ├── registry/           # Registry factory + 6 YAML-backed registries
│   ├── database/           # DuckDB / Postgres / BigQuery abstraction
│   ├── llm_services/       # LLM provider implementations
│   └── contracts/          # Data product contract YAML files
├── decision-studio-ui/     # React/Vite frontend (+ CLAUDE.md)
├── tests/                  # Test suites (+ CLAUDE.md)
├── docs/                   # Architecture docs + PRDs (+ CLAUDE.md)
├── scripts/                # Utility scripts (run_cfo_assessment.py, etc.)
├── workflow_definitions/   # Workflow YAML definitions
└── supabase/               # Supabase local dev config
```

## Run Commands

```bash
# Start full stack (MANDATORY — do not use alternatives):
.\restart_decision_studio_ui.ps1

# Unit tests:
.venv/Scripts/pytest tests/unit/ --timeout=15 --ignore=tests/unit/test_a9_data_product_mcp_service_agent_unit.py

# Enterprise assessment (replaces run_cfo_assessment.py):
.venv/Scripts/python run_enterprise_assessment.py [--principal <id>] [--kpi <kpi_id>] [--dry-run]
```

---

## Critical Areas (Handle with Care)

**Mission-critical — changes affect all workflows:**
- `src/agents/new/a9_orchestrator_agent.py` — central coordinator
- `src/agents/new/a9_principal_context_agent.py` — security and access control
- `src/agents/new/a9_data_governance_agent.py` — compliance critical
- `src/registry/factory.py` — registry initialization, affects system startup

**Do NOT modify without explicit permission:**
- Production database migration files (`supabase/migrations/`)
- Deployed agent cards in production registries
- Environment-specific configuration (`.env`)

---

## Known Issues & Technical Debt

1. **Business Process Provider Init** ⚠️ — Provider not found on startup; agent creates fallback. Expected, not breaking.
2. **Data Governance → Data Product connection** ⚠️ — DG agent not initialized in DP agent's `connect()`; falls back to local resolution.
3. **Principal ID vs Role-Based Lookup** 🔴 — PC Agent uses role names; should use IDs (`cfo_001`). Migration plan: `docs/architecture/principal_id_based_lookup_plan.md`.
4. **Business Process Format Inconsistencies** ⚠️ — Mixed formats across registries. Blueprint: `docs/architecture/business_process_hierarchy_blueprint.md`.
5. **Registry Provider Replacement Warnings** ℹ️ — Duplicate initialization; not breaking.
6. **Hardcoded File Paths** 🔴 — Some absolute paths remain; should use relative or env-var-based paths.
7. **Supabase DB URL Missing** ⚠️ — `.env` sets backend=supabase but `SUPABASE_DB_URL` not set → 5 registries fall back to YAML. Business Contexts registry works (uses REST API).

### Expected Warnings on Startup (Not Errors)

```
WARNING:src.registry.factory:Provider 'business_process' not found in registry factory
WARNING:src.agents.new.a9_principal_context_agent.A9_Principal_Context_Agent:Business process provider not found, creating default provider
WARNING:src.registry.factory:Provider 'business_process' exists but may not be properly initialized
WARNING:src.agents.new.a9_data_product_agent:Data Governance Agent not available for view name resolution
WARNING:src.registry.factory:Replacing existing kpi provider with new instance
WARNING:src.registry.factory:Replacing existing principal_profile provider with new instance
WARNING:src.registry.factory:Replacing existing data_product provider with new instance
WARNING:src.registry.factory:Replacing existing business_glossary provider with new instance
```

These indicate initialization sequence issues but fallback mechanisms are in place.

---

## Architecture Documentation

- Core docs: `docs/architecture/` — see `docs/CLAUDE.md` for file list
- Agent PRDs: `docs/prd/agents/` — one per implemented agent
- Work function guides: `src/agents/new/CLAUDE.md`, `tests/CLAUDE.md`, `decision-studio-ui/CLAUDE.md`
