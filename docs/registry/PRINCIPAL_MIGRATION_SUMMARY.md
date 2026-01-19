# Principal Profiles Supabase Migration - Implementation Summary

**Date:** 2026-01-17  
**Status:** ✅ Implementation Complete | 🔄 Validation Pending

---

## What Was Built

### 1. Database Schema (`supabase/migrations/0002_principal_profiles.sql`)

**Table:** `public.principal_profiles`

**Key Features:**
- **Pydantic-compatible columns** - Direct mapping to `PrincipalProfile` model
- **Normalized relationships** - `business_process_ids text[]` stores BP IDs (not display names)
- **JSONB for nested objects** - `persona_profile`, `time_frame`, `communication`, `metadata`
- **Performance indexes:**
  - B-tree on `role`, `department`, `name`
  - Full-text search on `name` + `title`
  - GIN index on `business_process_ids` array
- **Auto-updated timestamps** - Trigger maintains `updated_at`

**Schema Highlights:**
```sql
create table public.principal_profiles (
    id text primary key,
    name text not null,
    title text,
    role text,
    department text,
    business_process_ids text[] default '{}',  -- Normalized!
    persona_profile jsonb default '{}',
    metadata jsonb default '{}',  -- Includes kpi_line_preference, kpi_altitude_preference
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```

---

### 2. Seeder Script (`scripts/supabase_seed_principal_profiles.py`)

**Purpose:** Transform YAML principals → Supabase rows with normalized BP IDs

**Key Features:**
- Reads `principal_registry.yaml` + `business_process_registry.yaml`
- Maps BP display names → IDs (e.g., `"Finance: Profitability Analysis"` → `"finance_profitability_analysis"`)
- Idempotent upserts via `resolution=merge-duplicates`
- CLI flags: `--dry-run`, `--truncate-first`
- Environment variables: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_PRINCIPAL_TABLE`

**Usage:**
```bash
# Preview transformation
python scripts/supabase_seed_principal_profiles.py --dry-run

# Seed to Supabase
python scripts/supabase_seed_principal_profiles.py

# Fresh seed (delete + insert)
python scripts/supabase_seed_principal_profiles.py --truncate-first
```

---

### 3. Provider (`src/registry/providers/principal_provider.py`)

**Class:** `SupabasePrincipalProfileProvider`

**Key Features:**
- Extends `PrincipalProfileProvider` for compatibility
- Fetches principals via Supabase REST API
- Converts Supabase rows → `PrincipalProfile` Pydantic objects
- **Graceful fallback** - Falls back to YAML if Supabase fails
- Uses `json.loads(response.text)` to avoid Pydantic v1 API lint issues
- Factory function: `create_supabase_principal_profile_provider(config)`

**Initialization:**
```python
provider = SupabasePrincipalProfileProvider(
    supabase_url="http://localhost:54321",
    service_key="<service_role_key>",
    table="principal_profiles",
    schema="public",
    source_path="src/registry/principal/principal_registry.yaml",  # Fallback
)
await provider.load()
```

---

### 4. Bootstrap Integration (`src/registry/bootstrap.py`)

**Environment Variable:** `PRINCIPAL_PROFILE_BACKEND`

**Values:**
- `yaml` (default) - Load from YAML files
- `supabase` - Load from Supabase, fallback to YAML on error

**Logic:**
```python
backend_choice = os.getenv('PRINCIPAL_PROFILE_BACKEND', 'yaml').lower()

if backend_choice == 'supabase' and supabase_url and supabase_service_key:
    # Try Supabase
    principal_provider = SupabasePrincipalProfileProvider(...)
    await principal_provider.load()
else:
    # Use YAML
    principal_provider = PrincipalProfileProvider(...)
    await principal_provider.load()
```

**Logging:**
- `"Initializing Supabase principal profile provider"`
- `"Supabase principal provider initialized successfully with N profiles"`
- `"Falling back to YAML principal provider due to Supabase error: ..."`

---

## Files Created/Modified

### Created:
1. `supabase/migrations/0002_principal_profiles.sql` (89 lines)
2. `scripts/supabase_seed_principal_profiles.py` (237 lines)
3. `docs/registry/PRINCIPAL_MIGRATION_SUMMARY.md` (this file)

### Modified:
1. `src/registry/providers/principal_provider.py` (+129 lines)
   - Added `SupabasePrincipalProfileProvider` class
   - Added `create_supabase_principal_profile_provider()` factory
2. `src/registry/bootstrap.py` (+33 lines, -19 lines)
   - Added `PRINCIPAL_PROFILE_BACKEND` toggle logic
   - Imported `SupabasePrincipalProfileProvider`
3. `docs/registry/supabase_migration_plan.md` (updated Phase 2 checklist)

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

This applies `0002_principal_profiles.sql` to your local Supabase instance.

### Step 3: Seed Principals
```bash
# Set environment variables (if not in .env)
$env:SUPABASE_URL = "http://localhost:54321"
$env:SUPABASE_SERVICE_ROLE_KEY = "<your_service_key>"

# Dry run first
python scripts/supabase_seed_principal_profiles.py --dry-run

# Seed for real
python scripts/supabase_seed_principal_profiles.py
```

### Step 4: Enable Supabase Backend
Add to your `.env` file:
```
PRINCIPAL_PROFILE_BACKEND=supabase
SUPABASE_URL=http://localhost:54321
SUPABASE_SERVICE_ROLE_KEY=<your_service_key>
```

### Step 5: Restart Agent9
```powershell
# Kill existing processes
Get-Process python | Where-Object {$_.Path -like "*Agent9*"} | Stop-Process -Force

# Restart Decision Studio
.\scripts\restart_decision_studio_ui.ps1
```

### Step 6: Verify
Check logs for:
```
INFO - Initializing Supabase principal profile provider
INFO - Supabase principal provider initialized successfully with 4 profiles
```

---

## Validation Checklist

- [ ] Migration applied successfully (`supabase db push`)
- [ ] Principals seeded successfully (4 profiles)
- [ ] `PRINCIPAL_PROFILE_BACKEND=supabase` set in `.env`
- [ ] Agent9 starts without errors
- [ ] Principal Context Agent returns correct profiles
- [ ] Situation Awareness respects principal KPI preferences
- [ ] Decision Studio shows principals correctly
- [ ] Fallback to YAML works if Supabase is down

---

## Next Steps

### Immediate (Phase 2 Validation):
1. Run validation checklist above
2. Test with different principals (CEO, CFO, COO, Finance Manager)
3. Verify KPI ordering respects `kpi_line_preference` / `kpi_altitude_preference`
4. Test fallback by stopping Supabase

### Phase 3: KPI Registry Migration
- Create `0003_kpis.sql` migration
- Implement `SupabaseKPIProvider`
- Create seed script for KPIs
- Wire `KPI_REGISTRY_BACKEND` toggle

### Phase 4: Business Processes & Data Products
- Migrate business processes
- Migrate data products
- Add FK constraints between tables

### Phase 5: Enterprise Hardening
- Implement RLS policies
- Add audit trail tables
- HR system sync design
- Monitoring & alerting
- Backup/DR procedures

---

## Design Decisions

### Why Normalize Business Process IDs?
**Problem:** YAML uses display names like `"Finance: Profitability Analysis"`  
**Solution:** Supabase stores IDs like `"finance_profitability_analysis"`  
**Benefit:** Stable references, easier FK constraints, no string matching issues

### Why JSONB for Nested Objects?
**Problem:** Pydantic models have nested dicts (`persona_profile`, `time_frame`, `communication`)  
**Solution:** Store as JSONB in Supabase  
**Benefit:** Flexible schema, direct Pydantic mapping, queryable with JSON operators

### Why Fallback to YAML?
**Problem:** Supabase might be down during development  
**Solution:** Provider falls back to YAML on error  
**Benefit:** Resilient development experience, gradual migration path

### Why Separate Seeder Script?
**Problem:** Need to populate Supabase from existing YAML  
**Solution:** Standalone Python script with CLI flags  
**Benefit:** Idempotent, testable, reusable for CI/CD

---

## Lessons Learned (from Business Glossary Pilot)

1. ✅ **Supabase REST API pattern works well** - Simple HTTP calls, no SDK required
2. ✅ **Env-based backend toggle** - Clean separation of dev/prod configs
3. ✅ **Idempotent seed scripts** - Use `resolution=merge-duplicates` for upserts
4. ✅ **Pre-commit hooks catch issues early** - Pydantic v1 API usage detected before merge
5. ✅ **Explicit JSON parsing** - Use `json.loads(response.text)` to avoid lint issues

---

## Questions for User

1. **FK Constraints:** Should we add FK constraints in Phase 2 or defer to Phase 4?
   - Pro: Enforces referential integrity early
   - Con: Requires business_processes table to exist first

2. **Which enterprise blocker to tackle first?**
   - RLS Policies (2-3 days)
   - Audit Logging (3-4 days)
   - HR System Sync (1-2 weeks)
   - Monitoring & Alerting (4-5 days)

3. **Testing strategy:** Unit tests now or after Phase 3 (KPI migration)?

---

**Status:** Ready for validation testing 🚀
