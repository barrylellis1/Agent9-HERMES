# Supabase Migration & Enterprise Pilot Readiness Plan

_Last updated: 2026-01-17_

**Status:** Business Glossary pilot complete ✅ | Principal/KPI migration in design | Enterprise hardening planned

## Quick Links
- [Migration Progress Tracking](#migration-progress-tracking)
- [Enterprise Pilot Readiness Checklist](#enterprise-pilot-readiness-checklist)
- [Current Sprint Focus](#current-sprint-focus)

## 1. Objectives

- Stand up a local Supabase instance to host all registry-driven metadata currently stored in YAML/Python modules.
- Define portable schemas for principals, KPIs, consulting personas, data products, business processes, and future anomaly metadata.
- Document the migration path so the Agent9 runtime can swap providers without breaking dev/test environments.

## 2. Current Registry Artifacts (Source of Truth: Repository)

| Dataset | Current Location | Notes |
| --- | --- | --- |
| Principal profiles | `src/registry/principal/principal_registry.yaml` | Deep structure (preferences, filters, communication profile). |
| Business glossary | `src/registry/data/business_glossary.yaml` | Flat list of terms + metadata. |
| Business processes | `src/registry/data/business_processes.py` | Python list of dicts. |
| KPI registry | `src/registry/kpi/kpi_registry.yaml` | Includes thresholds, filters, metadata. |
| Data product contracts | `src/registry_references/data_product_registry/*` | Large YAML (tables, views, KPIs). |
| Consulting personas & presets | `src/registry/consulting_personas/*.yaml` | Personas + council presets. |
| Registry bootstrap defaults | `src/registry/bootstrap.py` | Fallback logic; needs Supabase-backed providers. |

## 3. Supabase Local Environment

1. **Prerequisites**
   - Docker Desktop running.
   - Node.js ≥ 18 (for Supabase CLI).

2. **Install CLI**
   ```bash
   npm install -g supabase
   ```

3. **Initialize Project**
   ```bash
   supabase init --project-name agent9-registry
   ```
   This creates `supabase/` with migrations & config. Commit schema SQL, never secrets.

4. **Start Local Stack**
   ```bash
   supabase start
   ```
   Capture connection string (Postgres + service/api keys) for local `.env`.

5. **Migrations**
   - Place DDL in `supabase/migrations/<timestamp>_registry_init.sql`.
   - Use `supabase db push` to apply locally.

6. **Seed Data**
   - Convert YAML to SQL inserts (`supabase/seed.sql`) or JSON load script.
   - Only seed non-sensitive sample data.

## 4. Proposed Schema (PostgreSQL via Supabase)

> All timestamp columns use `timestamptz` and default to `now()`. JSON-heavy structures stored in `jsonb` for flexibility.

### 4.1 Core Tables

```sql
-- Principal Profiles
create table principal_profiles (
    id text primary key,
    name text not null,
    title text not null,
    role text,
    department text,
    responsibilities text[],
    decision_style text,
    risk_tolerance text,
    communication_style text,
    preferences jsonb default '{}',
    default_filters jsonb default '{}',
    typical_timeframes text[],
    principal_groups text[],
    metadata jsonb default '{}',
    source text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- Business Processes
create table business_processes (
    id text primary key,
    name text not null,
    domain text not null,
    description text,
    owner text,
    tags text[],
    metadata jsonb default '{}'
);

-- KPI Definitions
create table kpis (
    id text primary key,
    name text not null,
    description text,
    domain text,
    unit text,
    business_process_ids text[],
    thresholds jsonb,
    filters jsonb,
    metadata jsonb,
    positive_trend_is_good boolean,
    default_timeframe text,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- KPI Threshold History (optional)
create table kpi_threshold_history (
    kpi_id text references kpis(id) on delete cascade,
    threshold_name text,
    value numeric,
    effective_at timestamptz default now(),
    primary key (kpi_id, threshold_name, effective_at)
);

-- Data Products
create table data_products (
    id text primary key,
    name text not null,
    description text,
    domain text,
    owner text,
    version text,
    tags text[],
    business_process_ids text[],
    metadata jsonb
);

-- Tables & Views for Data Products
create table data_product_tables (
    id uuid primary key default gen_random_uuid(),
    data_product_id text references data_products(id) on delete cascade,
    name text not null,
    schema jsonb,
    source text,
    metadata jsonb
);

create table data_product_views (
    id uuid primary key default gen_random_uuid(),
    data_product_id text references data_products(id) on delete cascade,
    name text not null,
    sql_definition text,
    metadata jsonb
);

-- Consulting Personas
create table consulting_personas (
    id text primary key,
    name text not null,
    label text,
    firm text,
    color text,
    tags text[],
    methodology_summary text,
    expertise jsonb,
    metadata jsonb
);

-- Council Presets
create table council_presets (
    id text primary key,
    name text not null,
    description text,
    tags text[],
    metadata jsonb
);

create table council_preset_members (
    preset_id text references council_presets(id) on delete cascade,
    persona_id text references consulting_personas(id) on delete cascade,
    position integer,
    primary key (preset_id, persona_id)
);

-- Business Glossary
create table business_glossary_terms (
    id text primary key,
    term text not null,
    definition text,
    aliases text[],
    tags text[],
    metadata jsonb
);
```

### 4.2 Future Tables

- `anomaly_detection_methods` – configuration for statistical/forecast/multivariate approaches.
- `anomaly_metadata` – links KPI/data product to detection config, thresholds, decay windows.
- `registry_audit_log` – who/when modifications occur (use Supabase row level security + triggers).

### 4.3 Supabase Policies (later)

- Restrict write access to service role.
- Provide read-only role for UI/admin console.
- In dev, disable RLS to simplify local evaluation.

## 5. Migration Strategy

1. **Data Export Scripts**
   - Write a Node/TypeScript script in `scripts/` that reads YAML files and outputs `INSERT` statements or uses Supabase Admin API.
   - Keep script idempotent (truncate + insert) for repeated local runs.

2. **Provider Refactor**
   - Implement Supabase-backed providers inheriting from existing abstract base classes.
   - Feature flag via config (e.g., `REGISTRY_BACKEND=supabase|yaml`).
   - Update `registry/bootstrap.py` to branch on config.

3. **Testing**
   - Provide fixtures for unit tests using an in-memory store or Supabase docker service in CI.
   - Migration acceptance criteria: registry-driven agents pass existing tests when backend switched to Supabase.

4. **Admin Console Integration**
   - Once Supabase holds registry data, Agent9 Admin Console can read/update via REST endpoints (Plan pending).

## 6. Configuration Changes

- Extend `src/config/registry_config.py` (or equivalent) to include:
  ```yaml
  registry_backend: supabase
  supabase:
    url: http://localhost:54321
    anon_key: <dev anon key>
    service_key: <dev service key>
  ```
- Update `.env.development` with Supabase credentials (never commit).
- Ensure `requirements.txt` / `package.json` capture any new client dependencies (`supabase-py` or `@supabase/supabase-js`).
- `BUSINESS_GLOSSARY_BACKEND=supabase` toggles the Supabase provider; fallback to YAML occurs automatically if the REST call fails.
- Environment variables respected: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, optional `SUPABASE_BUSINESS_GLOSSARY_TABLE` (defaults to `business_glossary_terms`).

## 7. Open Questions / Follow-Ups

1. Do we keep YAML files as source control backups or treat Supabase as the canonical source?
2. How do we seed test environments (CI) — ephemeral Supabase or Docker Postgres with migrations?
3. Strategy for RLS policies once we have multi-user admin editing.
4. How to version registry entries (e.g., KPI definition changes) — use audit/history tables?
5. Coordinate anomaly detection metadata tables with forthcoming design work.

## 8. Migration Progress Tracking

### Phase 1: Business Glossary (Pilot) ✅ COMPLETE

- [x] Define schema migration (`0001_business_glossary.sql`)
- [x] Implement `SupabaseBusinessGlossaryProvider`
- [x] Create seed script (`scripts/supabase_seed_business_glossary.py`)
- [x] Wire bootstrap with `BUSINESS_GLOSSARY_BACKEND` toggle
- [x] Add fallback to YAML on Supabase failure
- [x] Document in migration plan

**Lessons Learned:**
- Supabase REST API pattern works well for registry providers
- Env-based backend toggle provides clean dev/prod separation
- Seed scripts should be idempotent (upsert-based)
- Pre-commit hooks caught Pydantic v1 API usage early

### Phase 2: Principal Profiles ✅ IMPLEMENTATION COMPLETE

#### 2.1 Schema Design ✅
- [x] Map YAML fields to Supabase columns (Pydantic-compatible)
- [x] Design `business_process_ids` normalization (string → ID)
- [x] Create migration `0002_principal_profiles.sql`
- [x] Add indexes (id, role, department, business_process_ids GIN)
- [x] Add full-text search index
- [x] Add updated_at trigger
- [ ] Define RLS policies (deferred to Phase 5)

#### 2.2 Seeder Implementation ✅
- [x] Create `scripts/supabase_seed_principal_profiles.py`
- [x] Implement YAML → row transformation
- [x] Add BP display_name → id mapping logic
- [x] Support `--dry-run` and `--truncate-first` flags
- [x] Idempotent upserts via `resolution=merge-duplicates`

#### 2.3 Provider Implementation ✅
- [x] Implement `SupabasePrincipalProfileProvider`
- [x] Add async `load()` method (fetch via REST)
- [x] Implement `get()`, `get_all()`, `find_by_attribute()` (inherited)
- [x] Add error handling + YAML fallback
- [x] Factory function `create_supabase_principal_profile_provider()`
- [ ] Unit tests with mocked Supabase client (deferred)

#### 2.4 Bootstrap Integration ✅
- [x] Add `PRINCIPAL_PROFILE_BACKEND` env toggle
- [x] Wire provider selection in `registry/bootstrap.py`
- [x] Add logging for backend choice
- [x] Import `SupabasePrincipalProfileProvider` in bootstrap
- [x] Update `.env.example` with Supabase configuration

#### 2.5 Validation 🔄 IN PROGRESS
- [ ] Run migration on local Supabase: `supabase db push`
- [ ] Seed principals: `python scripts/supabase_seed_principal_profiles.py`
- [ ] Set `PRINCIPAL_PROFILE_BACKEND=supabase` in `.env`
- [ ] Principal Context Agent works with Supabase backend
- [ ] Situation Awareness respects principal preferences
- [ ] Decision Studio shows correct principals
- [ ] Integration test: YAML vs Supabase parity

### Phase 3: KPI Registry ✅ IMPLEMENTATION COMPLETE

- [x] Create migration `0003_kpis.sql`
- [x] Implement `SupabaseKPIProvider`
- [x] Create seed script `supabase_seed_kpis.py`
- [x] Wire `KPI_REGISTRY_BACKEND` toggle in bootstrap
- [x] Import `SupabaseKPIProvider` in bootstrap
- [ ] Validate SA agent KPI detection (pending)

### Phase 4: Business Processes & Data Products ✅ IMPLEMENTATION COMPLETE

- [x] Create migration `0004_business_processes.sql`
- [x] Create migration `0005_data_products.sql`
- [x] Implement `SupabaseBusinessProcessProvider`
- [x] Implement `SupabaseDataProductProvider`
- [x] Create seed script `supabase_seed_business_processes.py`
- [x] Create seed script `supabase_seed_data_products.py`
- [x] Wire `BUSINESS_PROCESS_BACKEND` toggle in bootstrap
- [x] Wire `DATA_PRODUCT_BACKEND` toggle in bootstrap
- [x] Import providers in bootstrap
- [ ] Add FK constraints between tables (deferred to Phase 5)
- [ ] Implement audit logging triggers (deferred to Phase 5)

### Phase 5: Enterprise Hardening 🔒 PLANNED

- [ ] Implement RLS policies
- [ ] Add audit trail tables
- [ ] HR system sync design
- [ ] Monitoring & alerting setup
- [ ] Backup/DR procedures

## 9. Enterprise Pilot Readiness Checklist

**Goal:** Identify and close gaps required for a real enterprise pilot with business users.

### Critical Blockers (Must Fix Before Pilot)

#### Security & Governance
- [ ] **RLS Policies** - Row-level security on all Supabase tables
  - Priority: **HIGH**
  - Owner: TBD
  - Estimate: 2-3 days
  - Dependencies: Principal/KPI migrations complete
- [ ] **Audit Logging** - Track who/what/when for all registry changes
  - Priority: **HIGH**
  - Owner: TBD
  - Estimate: 3-4 days
  - Tables: `registry_audit_log`, triggers on all registry tables
- [ ] **Secrets Management** - No hardcoded keys; use env vars + secret manager
  - Priority: **HIGH**
  - Owner: TBD
  - Estimate: 1 day
  - Action: Audit code for hardcoded credentials, document secret rotation

#### Data Quality & Reliability
- [ ] **FK Constraints** - Enforce referential integrity in Supabase
  - Priority: **HIGH**
  - Owner: TBD
  - Estimate: 2 days
  - Tables: `principal_profiles.business_process_ids` → `business_processes.id`
- [ ] **Monitoring & Alerting** - Health checks + alerts for registry/agent failures
  - Priority: **HIGH**
  - Owner: TBD
  - Estimate: 4-5 days
  - Tools: Supabase metrics, custom health endpoints, alert routing

#### Integration
- [ ] **HR System Sync** - Workday/SuccessFactors → Supabase principal profiles
  - Priority: **HIGH**
  - Owner: TBD
  - Estimate: 1-2 weeks
  - Scope: One-way sync, conflict resolution, scheduling

#### Operations
- [ ] **CI/CD for Migrations** - Automated migration runs on deploy
  - Priority: **HIGH**
  - Owner: TBD
  - Estimate: 2-3 days
  - Tools: GitHub Actions or equivalent
- [ ] **Backup & DR Plan** - Tested restore procedures
  - Priority: **HIGH**
  - Owner: TBD
  - Estimate: 2 days
  - Deliverable: Runbook + tested restore

### Important (Should Have for Pilot)

#### User Experience
- [ ] **Explainability** - Show why KPIs/situations are surfaced
  - Priority: **MEDIUM**
  - Owner: TBD
  - Estimate: 3-4 days
  - UI: Tooltips, "Why am I seeing this?" links
- [ ] **Graceful Degradation** - Fallback to YAML if Supabase fails
  - Priority: **MEDIUM**
  - Owner: TBD
  - Estimate: 1 day
  - Status: ⚠️ Partially done (glossary has fallback)

#### Integration
- [ ] **Data Product Onboarding** - Formalized process for adding new data products
  - Priority: **MEDIUM**
  - Owner: TBD
  - Estimate: 3-4 days
  - Deliverable: Runbook + validation checklist

#### Operations
- [ ] **Runbooks** - Operational procedures for common scenarios
  - Priority: **MEDIUM**
  - Owner: TBD
  - Estimate: 2-3 days
  - Scenarios: Supabase down, bad migration, add principal

### Nice to Have (Post-Pilot)

- [ ] **Multi-tenancy** - Tenant isolation in Supabase schema
- [ ] **Performance Benchmarks** - SA detection <5s, registry lookups <500ms
- [ ] **Advanced Caching** - Redis for registry lookups
- [ ] **Self-Service Profile Editing** - Principals can update their own preferences

---

## 10. Current Sprint Focus

**Sprint Goal:** ✅ **COMPLETE** - Phases 1-4 Migrated & Validated!

**Completed This Sprint:**
1. ✅ **Phase 1:** Business Glossary migration
2. ✅ **Phase 2:** Principal Profiles migration
3. ✅ **Phase 3:** KPI Registry migration
4. ✅ **Phase 4:** Business Processes & Data Products migration
5. ✅ **Phase 4 Validation:** All 5 registries tested and working
6. ✅ Documentation cleanup (`.env.template` → `.env.example`)

**Migration Statistics:**
- **5 migrations created:** `0001-0005` ✅ Applied
- **5 seeder scripts:** All working ✅ 73 items seeded
- **5 Supabase providers:** All loading from Supabase ✅ Validated
- **5 backend toggles:** Environment-based selection ✅ Working
- **Total items migrated:** 11 terms + 4 profiles + 20 KPIs + 31 processes + 7 products = **73 items**

**Validation Completed (January 18, 2026):**
- ✅ Database reset and all 5 migrations applied
- ✅ All 5 registries seeded successfully
- ✅ Supabase backends enabled in `.env`
- ✅ All providers verified loading from Supabase
- ✅ Decision Studio UI tested and functional
- ✅ Hybrid architecture (Supabase + YAML) validated

**Issues Resolved:**
- ✅ Added missing `httpx` import to `principal_provider.py`
- ✅ Fixed `SUPABASE_SERVICE_KEY` → `SUPABASE_SERVICE_ROLE_KEY` in bootstrap (5 locations)

**Documentation:**
- ✅ `PHASE_4_MIGRATION_SUMMARY.md` - Implementation details
- ✅ `PHASE_4_VALIDATION_SUMMARY.md` - Validation results and testing

**Next Options:**
1. **Phase 5** - Enterprise hardening (RLS, audit, FK constraints, HR sync, monitoring)
2. **Production Deployment** - Deploy to managed Supabase
3. **Feature Development** - Build on validated registry foundation

**Recommended Next Steps:**
- Review validation summary document
- Decide on Phase 5 enterprise features
- Plan production deployment timeline

---

## 11. Pilot Migration Plan (Business Glossary) ✅ COMPLETE

**Goal:** de-risk the broader Supabase rollout by migrating the business glossary first. This registry is read-mostly, has minimal write-paths, and is consumed by limited UX paths, making it a low-impact trial.

### Pilot Scope

- Source file: `src/registry/data/business_glossary.yaml` (currently ~50 terms).
- Consumer: registry bootstrap registers `BusinessGlossaryProvider`; primarily used by agents for term disambiguation.
- Output: Supabase table `business_glossary_terms` (see §4.1).

### Steps

1. **Define schema migration**
   - Create migration `supabase/migrations/<ts>_business_glossary.sql` with only the glossary table.
   - Columns: `id`, `term`, `definition`, `aliases[]`, `tags[]`, `metadata jsonb`, timestamps.

2. **Seed data**
   - Write a one-off script `scripts/seed_business_glossary.ts` that reads YAML and inserts rows via Supabase Admin API (using service key).
   - Mark script as dev-only; exclude credentials.

3. **Implement provider**
   - New class `SupabaseBusinessGlossaryProvider` implementing existing provider interface.
   - Reads glossary via Supabase REST (e.g., using `@supabase/supabase-js`).
   - Feature flag via config `REGISTRY_BUSINESS_GLOSSARY_BACKEND=supabase|yaml`.

4. **Wire bootstrap**
   - Update `RegistryBootstrap` to choose Supabase provider when flag enabled; fallback to YAML otherwise.
   - Log which backend loaded for traceability.

5. **Validation**
   - Unit tests verifying provider fetches data (mock Supabase client).
   - Manual regression: launch Decision Studio, ensure glossary-dependent features behave identically.

6. **Rollout Criteria**
   - All glossary reads succeed from Supabase.
   - Error handling: if Supabase unavailable, fallback to YAML read with warning.
   - Document setup in `Developer_Getting_Started.md`.

### Post-Pilot

- Review lessons learned (schema versioning, seed workflow, provider interface changes).
- Apply patterns to higher-impact registries (principal profiles, KPIs) once stable.
- [ ] Evaluate Supabase pricing/free tier for managed environments (future step).

### Seed Script Outline (Business Glossary)

Goal: Convert `business_glossary.yaml` into inserts for `business_glossary_terms` via Supabase Admin API.

1. **Script Shell**
   - Location: `scripts/supabase_seed_business_glossary.py` (Python CLI, included for pilot).
   - Dependencies: `httpx`, `pyyaml` (already in `requirements.txt`).

2. **High-Level Flow**
   ```python
   rows = transform_terms(load_glossary(Path('src/registry/data/business_glossary.yaml')))

   if args.dry_run:
       print(json.dumps(rows, indent=2))
       return

   headers = {
       "apikey": service_role,
       "Authorization": f"Bearer {service_role}",
       "Prefer": "resolution=merge-duplicates,return=representation",
       "Accept": "application/json",
       "Accept-Profile": schema,
   }

   if args.truncate_first:
       delete_existing_rows(client, endpoint, headers)

   upsert_rows(client, endpoint, headers, rows)
   ```

3. **Operational Notes**
   - CLI flags supported: `--dry-run`, `--truncate-first`.
   - Env vars required: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`; optional `SUPABASE_SCHEMA`, `SUPABASE_BUSINESS_GLOSSARY_TABLE`.
   - Idempotent via Supabase `on_conflict=id` upsert; dry-run prints payload only.
   - Intended for local/dev use; avoid wiring into CI until Supabase test infra decided.

### Provider Swap Plan

Objective: Allow `RegistryBootstrap` to load the business glossary from Supabase when configured, otherwise remain YAML-backed.

1. **Configuration Toggle**
   - Extend registry config model to include `business_glossary_backend` and Supabase credentials.
   - Sample config snippet:
     ```python
     registry_config = {
         "business_glossary_backend": os.getenv("BUSINESS_GLOSSARY_BACKEND", "yaml"),
         "supabase": {
             "url": os.getenv("SUPABASE_URL"),
             "service_key": os.getenv("SUPABASE_SERVICE_KEY"),
         }
     }
     ```

2. **New Provider**
   - Implement `SupabaseBusinessGlossaryProvider(RegistryProvider[BusinessGlossaryTerm])`.
   - Key methods: `load()` (fetch via Supabase REST/RPC), `get_all()`, `find_by_attribute()`.
   - Cache rows on load; revalidate by timestamp if needed.

3. **Bootstrap Logic**
   ```python
   backend = config.get("business_glossary_backend", "yaml")
   if backend == "supabase":
       glossary_provider = SupabaseBusinessGlossaryProvider(config["supabase"])
   else:
       glossary_provider = BusinessGlossaryProvider(glossary_path=glossary_path)

   cls._factory.register_provider('business_glossary', glossary_provider)
   await glossary_provider.load()
   cls._factory._provider_initialization_status['business_glossary'] = True
   ```

4. **Fallback Strategy**
   - Wrap Supabase load in try/except; on failure, log warning and instantiate YAML provider.
   - Track origin via provider property for observability.

5. **Testing**
   - Unit test Supabase provider with mocked client (e.g., responses library or supabase-js stub).
   - Integration test toggling config to ensure bootstrap selects correct provider.
