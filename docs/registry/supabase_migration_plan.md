# Supabase Migration Plan for Agent9 Registries

_Last updated: 2026-01-08_

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

## 7. Open Questions / Follow-Ups

1. Do we keep YAML files as source control backups or treat Supabase as the canonical source?
2. How do we seed test environments (CI) — ephemeral Supabase or Docker Postgres with migrations?
3. Strategy for RLS policies once we have multi-user admin editing.
4. How to version registry entries (e.g., KPI definition changes) — use audit/history tables?
5. Coordinate anomaly detection metadata tables with forthcoming design work.

## 8. Next Actions

- [ ] Finalize DDL & ensure all current registry fields are represented.
- [ ] Author YAML → SQL seed script.
- [ ] Prototype `SupabasePrincipalProfileProvider` using service key (dev only).
- [ ] Add setup instructions to developer onboarding docs once validated.

## 9. Pilot Migration Plan (Business Glossary)

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
