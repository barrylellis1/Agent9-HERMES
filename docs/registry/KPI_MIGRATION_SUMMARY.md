# KPI Registry Supabase Migration - Implementation Summary

**Date:** 2026-01-17  
**Status:** ✅ Implementation Complete | 🔄 Validation Pending

---

## What Was Built

### 1. Database Schema (`supabase/migrations/0003_kpis.sql`)

**Table:** `public.kpis`

**Key Features:**
- **Pydantic-compatible columns** - Direct mapping to `KPI` model
- **Normalized relationships** - `business_process_ids text[]` stores BP IDs (not display names)
- **JSONB for complex data** - `filters`, `thresholds`, `dimensions`, `metadata`
- **Performance indexes:**
  - B-tree on `domain`, `data_product_id`, `owner_role`, `name`
  - Full-text search on `name` + `description`
  - GIN indexes on `business_process_ids`, `tags`, `metadata`
- **Auto-updated timestamps** - Reuses trigger from principal_profiles

**Schema Highlights:**
```sql
create table public.kpis (
    id text primary key,
    name text not null,
    domain text not null,
    data_product_id text not null,
    business_process_ids text[] default '{}',  -- Normalized!
    filters jsonb default '{}',
    thresholds jsonb default '[]',  -- Array of threshold objects
    dimensions jsonb default '[]',  -- Array of dimension objects
    metadata jsonb default '{}',    -- Includes line, altitude, profit_driver_type, lens_affinity
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```

---

### 2. Seeder Script (`scripts/supabase_seed_kpis.py`)

**Purpose:** Transform YAML KPIs → Supabase rows with normalized BP IDs

**Key Features:**
- Reads `kpi_registry.yaml` + `business_process_registry.yaml`
- Maps BP display names/IDs → normalized IDs
- Handles complex JSONB fields (thresholds, dimensions, filters)
- Idempotent upserts via `resolution=merge-duplicates`
- CLI flags: `--dry-run`, `--truncate-first`
- Environment variables: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_KPI_TABLE`

**Usage:**
```bash
# Preview transformation
python scripts/supabase_seed_kpis.py --dry-run

# Seed to Supabase
python scripts/supabase_seed_kpis.py

# Fresh seed (delete + insert)
python scripts/supabase_seed_kpis.py --truncate-first
```

---

### 3. Provider (`src/registry/providers/kpi_provider.py`)

**Class:** `SupabaseKPIProvider`

**Key Features:**
- Extends `KPIProvider` for compatibility
- Fetches KPIs via Supabase REST API
- Converts Supabase rows → `KPI` Pydantic objects
- **Graceful fallback** - Falls back to YAML if Supabase fails
- Uses `json.loads(response.text)` to avoid Pydantic v1 API lint issues
- Factory function: `create_supabase_kpi_provider(config)`

**Initialization:**
```python
provider = SupabaseKPIProvider(
    supabase_url="http://localhost:54321",
    service_key="<service_role_key>",
    table="kpis",
    schema="public",
    source_path="src/registry/kpi/kpi_registry.yaml",  # Fallback
)
await provider.load()
```

---

### 4. Bootstrap Integration (`src/registry/bootstrap.py`)

**Environment Variable:** `KPI_REGISTRY_BACKEND`

**Values:**
- `yaml` (default) - Load from YAML files
- `supabase` - Load from Supabase, fallback to YAML on error

**Logic:**
```python
backend_choice = os.getenv('KPI_REGISTRY_BACKEND', 'yaml').lower()

if backend_choice == 'supabase' and supabase_url and supabase_service_key:
    # Try Supabase
    kpi_provider = SupabaseKPIProvider(...)
    await kpi_provider.load()
else:
    # Use YAML
    kpi_provider = KPIProvider(...)
    await kpi_provider.load()
```

**Logging:**
- `"Initializing Supabase KPI provider"`
- `"Supabase KPI provider initialized successfully with N KPIs"`
- `"Falling back to YAML KPI provider due to Supabase error: ..."`

---

## Files Created/Modified

### Created:
1. `supabase/migrations/0003_kpis.sql` (93 lines)
2. `scripts/supabase_seed_kpis.py` (252 lines)
3. `docs/registry/KPI_MIGRATION_SUMMARY.md` (this file)

### Modified:
1. `src/registry/providers/kpi_provider.py` (+135 lines)
   - Added `SupabaseKPIProvider` class
   - Added `create_supabase_kpi_provider()` factory
2. `src/registry/bootstrap.py` (+20 lines, -35 lines)
   - Added `KPI_REGISTRY_BACKEND` toggle logic
   - Imported `SupabaseKPIProvider`
   - Simplified KPI provider initialization
3. `docs/registry/supabase_migration_plan.md` (updated Phase 3 checklist)

---

## How to Use

### Step 1: Start Supabase (if not running)
```bash
cd c:\Users\barry\CascadeProjects\Agent9-HERMES
supabase start
```

### Step 2: Run Migration
```bash
supabase db push
```

This applies `0003_kpis.sql` to your local Supabase instance.

### Step 3: Seed KPIs
```bash
# Set environment variables (if not in .env)
$env:SUPABASE_URL = "http://localhost:54321"
$env:SUPABASE_SERVICE_ROLE_KEY = "<your_service_key>"

# Dry run first
python scripts/supabase_seed_kpis.py --dry-run

# Seed for real
python scripts/supabase_seed_kpis.py
```

### Step 4: Enable Supabase Backend
Add to your `.env` file:
```
KPI_REGISTRY_BACKEND=supabase
SUPABASE_URL=http://localhost:54321
SUPABASE_SERVICE_ROLE_KEY=<your_service_key>
```

### Step 5: Restart Agent9
```powershell
# Kill existing processes
Get-Process python | Where-Object {$_.Path -like "*Agent9*"} | Stop-Process -Force

# Restart Decision Studio
.\restart_decision_studio_ui.ps1
```

### Step 6: Verify
Check logs for:
```
INFO - Initializing Supabase KPI provider
INFO - Supabase KPI provider initialized successfully with 18 KPIs
```

---

## Validation Checklist

- [ ] Migration applied successfully (`supabase db push`)
- [ ] KPIs seeded successfully (~18 KPIs)
- [ ] `KPI_REGISTRY_BACKEND=supabase` set in `.env`
- [ ] Agent9 starts without errors
- [ ] Situation Awareness Agent detects situations using Supabase KPIs
- [ ] KPI metadata (line, altitude) respected in ordering
- [ ] Decision Studio shows KPIs correctly
- [ ] Fallback to YAML works if Supabase is down

---

## Design Decisions

### Why JSONB for Thresholds and Dimensions?
**Problem:** KPI model has complex nested arrays of objects  
**Solution:** Store as JSONB arrays in Supabase  
**Benefit:** Direct Pydantic mapping, queryable with JSONB operators, flexible schema

### Why Normalize Business Process IDs?
**Problem:** YAML uses display names like `"Finance: Profitability Analysis"`  
**Solution:** Supabase stores IDs like `"finance_profitability_analysis"`  
**Benefit:** Stable references, easier FK constraints, consistent with principal profiles

### Why Separate Seeder Script?
**Problem:** Need to populate Supabase from existing YAML  
**Solution:** Standalone Python script with CLI flags  
**Benefit:** Idempotent, testable, reusable for CI/CD, matches principal profiles pattern

---

## Migration Statistics

**Total KPIs in Registry:** ~18  
**Fields Migrated:** 15 (id, name, domain, description, unit, data_product_id, view_name, business_process_ids, sql_query, filters, thresholds, dimensions, tags, synonyms, owner_role, stakeholder_roles, metadata)  
**JSONB Fields:** 4 (filters, thresholds, dimensions, metadata)  
**Array Fields:** 4 (business_process_ids, tags, synonyms, stakeholder_roles)  
**Indexes Created:** 7 (domain, data_product_id, owner_role, name, search, business_process_ids GIN, tags GIN, metadata GIN)

---

## Next Steps

### Immediate (Phase 3 Validation):
1. Run validation checklist above
2. Test with Situation Awareness Agent
3. Verify KPI ordering respects metadata (line/altitude)
4. Test fallback by stopping Supabase

### Phase 4: Business Processes & Data Products
- Create migrations for business_processes and data_products tables
- Add FK constraints: `kpis.business_process_ids` → `business_processes.id`
- Implement providers and seeders

### Phase 5: Enterprise Hardening
- Implement RLS policies
- Add audit trail tables
- HR system sync design
- Monitoring & alerting
- Backup/DR procedures

---

**Status:** Ready for validation testing 🚀

**Phases Complete:** 1 (Business Glossary), 2 (Principal Profiles), 3 (KPI Registry) ✅
