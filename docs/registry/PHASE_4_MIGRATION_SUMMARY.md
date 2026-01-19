# Phase 4: Business Processes & Data Products Supabase Migration

**Date:** 2026-01-17  
**Status:** ✅ Implementation Complete | 🔄 Validation Pending

---

## What Was Built

### 1. Database Schemas

#### **Table: `public.business_processes`** (`0004_business_processes.sql`)

**Key Features:**
- Pydantic-compatible columns mapping to `BusinessProcess` model
- Normalized fields for domain, owner_role, stakeholder_roles
- Array columns for tags and stakeholder_roles
- JSONB for metadata extensions
- Full-text search on name + description
- 6 performance indexes (B-tree + GIN)
- Auto-updated timestamps

**Schema Highlights:**
```sql
create table public.business_processes (
    id text primary key,
    name text not null,
    domain text not null,
    description text,
    owner_role text,
    stakeholder_roles text[] default '{}',
    display_name text,
    tags text[] default '{}',
    metadata jsonb default '{}',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```

#### **Table: `public.data_products`** (`0005_data_products.sql`)

**Key Features:**
- Pydantic-compatible columns mapping to `DataProduct` model
- JSONB for tables and views definitions (complex nested objects)
- Array for related_business_processes (normalized IDs)
- Additional fields: yaml_contract_path, output_path, reviewed, language
- Full-text search on name + description + documentation
- 9 performance indexes (B-tree + GIN)
- Auto-updated timestamps

**Schema Highlights:**
```sql
create table public.data_products (
    id text primary key,
    name text not null,
    domain text not null,
    description text,
    owner text not null,
    version text default '1.0.0',
    related_business_processes text[] default '{}',
    tags text[] default '{}',
    metadata jsonb default '{}',
    tables jsonb default '{}',
    views jsonb default '{}',
    yaml_contract_path text,
    output_path text,
    last_updated date,
    reviewed boolean default false,
    language text default 'EN',
    documentation text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
```

---

### 2. Seeder Scripts

#### **Business Process Seeder** (`scripts/supabase_seed_business_processes.py`)

**Purpose:** Transform YAML business processes → Supabase rows

**Key Features:**
- Reads `business_process_registry.yaml`
- Direct transformation (no normalization needed)
- Idempotent upserts via `resolution=merge-duplicates`
- CLI flags: `--dry-run`, `--truncate-first`
- Environment variables: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_BUSINESS_PROCESS_TABLE`

**Usage:**
```bash
# Preview transformation
python scripts/supabase_seed_business_processes.py --dry-run

# Seed to Supabase
python scripts/supabase_seed_business_processes.py

# Fresh seed (delete + insert)
python scripts/supabase_seed_business_processes.py --truncate-first
```

#### **Data Product Seeder** (`scripts/supabase_seed_data_products.py`)

**Purpose:** Transform YAML data products → Supabase rows

**Key Features:**
- Reads `data_product_registry.yaml`
- Handles `product_id` → `id` mapping
- Parses `last_updated` date strings
- Preserves JSONB fields (tables, views, metadata)
- Idempotent upserts via `resolution=merge-duplicates`
- CLI flags: `--dry-run`, `--truncate-first`

**Usage:**
```bash
# Preview transformation
python scripts/supabase_seed_data_products.py --dry-run

# Seed to Supabase
python scripts/supabase_seed_data_products.py
```

---

### 3. Providers

#### **SupabaseBusinessProcessProvider** (`src/registry/providers/business_process_provider.py`)

**Class:** `SupabaseBusinessProcessProvider`

**Key Features:**
- Extends `BusinessProcessProvider` for compatibility
- Fetches business processes via Supabase REST API
- Converts Supabase rows → `BusinessProcess` Pydantic objects
- **Graceful fallback** - Falls back to YAML if Supabase fails
- Uses `json.loads(response.text)` to avoid Pydantic v1 API issues

**Initialization:**
```python
provider = SupabaseBusinessProcessProvider(
    supabase_url="http://localhost:54321",
    service_key="<service_role_key>",
    table="business_processes",
    schema="public",
    source_path="src/registry/business_process/business_process_registry.yaml",
)
await provider.load()
```

#### **SupabaseDataProductProvider** (`src/registry/providers/data_product_provider.py`)

**Class:** `SupabaseDataProductProvider`

**Key Features:**
- Extends `DataProductProvider` for compatibility
- Fetches data products via Supabase REST API
- Converts Supabase rows → `DataProduct` Pydantic objects
- **Graceful fallback** - Falls back to YAML if Supabase fails
- Handles complex JSONB fields (tables, views)

**Initialization:**
```python
provider = SupabaseDataProductProvider(
    supabase_url="http://localhost:54321",
    service_key="<service_role_key>",
    table="data_products",
    schema="public",
    source_path="src/registry/data_product/data_product_registry.yaml",
)
await provider.load()
```

---

### 4. Bootstrap Integration (`src/registry/bootstrap.py`)

**Environment Variables:**
- `BUSINESS_PROCESS_BACKEND` - Values: `yaml` (default) | `supabase`
- `DATA_PRODUCT_BACKEND` - Values: `yaml` (default) | `supabase`

**Logic:**
```python
backend_choice = os.getenv('BUSINESS_PROCESS_BACKEND', 'yaml').lower()

if backend_choice == 'supabase' and supabase_url and supabase_service_key:
    # Try Supabase
    bp_provider = SupabaseBusinessProcessProvider(...)
    await bp_provider.load()
else:
    # Use YAML
    bp_provider = BusinessProcessProvider(...)
    await bp_provider.load()
```

**Logging:**
- `"Initializing Supabase business process provider"`
- `"Supabase business process provider initialized successfully with N processes"`
- `"Falling back to YAML business process provider due to Supabase error: ..."`

---

## Files Created/Modified

### Created:
1. `supabase/migrations/0004_business_processes.sql` (52 lines)
2. `supabase/migrations/0005_data_products.sql` (72 lines)
3. `scripts/supabase_seed_business_processes.py` (114 lines)
4. `scripts/supabase_seed_data_products.py` (129 lines)
5. `docs/registry/PHASE_4_MIGRATION_SUMMARY.md` (this file)

### Modified:
1. `src/registry/providers/business_process_provider.py` (+80 lines)
   - Added `SupabaseBusinessProcessProvider` class
2. `src/registry/providers/data_product_provider.py` (+82 lines)
   - Added `SupabaseDataProductProvider` class
3. `src/registry/bootstrap.py` (+100 lines)
   - Added `BUSINESS_PROCESS_BACKEND` toggle logic
   - Added `DATA_PRODUCT_BACKEND` toggle logic
   - Imported both Supabase providers
4. `.env.example` (+2 lines)
   - Added `BUSINESS_PROCESS_BACKEND` and `DATA_PRODUCT_BACKEND` variables
   - Added table override variables
5. `docs/registry/supabase_migration_plan.md` (updated Phase 4 checklist)

---

## How to Use

### Step 1: Apply Migrations
```bash
supabase db reset
```

This applies all 5 migrations (0001-0005) to your local Supabase instance.

### Step 2: Seed Business Processes
```bash
# Set environment variables (if not in .env)
$env:SUPABASE_URL = "http://127.0.0.1:54321"
$env:SUPABASE_SERVICE_ROLE_KEY = "<your_service_key>"

# Dry run first
python scripts/supabase_seed_business_processes.py --dry-run

# Seed for real
python scripts/supabase_seed_business_processes.py
```

### Step 3: Seed Data Products
```bash
# Dry run first
python scripts/supabase_seed_data_products.py --dry-run

# Seed for real
python scripts/supabase_seed_data_products.py
```

### Step 4: Enable Supabase Backends
Add to your `.env` file:
```
BUSINESS_PROCESS_BACKEND=supabase
DATA_PRODUCT_BACKEND=supabase
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=<your_service_key>
```

### Step 5: Restart Agent9
```powershell
.\restart_decision_studio_ui.ps1
```

### Step 6: Verify
Check logs for:
```
INFO - Initializing Supabase business process provider
INFO - Supabase business process provider initialized successfully with 31 processes
INFO - Initializing Supabase data product provider
INFO - Supabase data product provider initialized successfully with 6 data products
```

---

## Validation Checklist

- [ ] Migrations applied successfully (`supabase db reset`)
- [ ] Business processes seeded successfully (~31 processes)
- [ ] Data products seeded successfully (~6 data products)
- [ ] `BUSINESS_PROCESS_BACKEND=supabase` set in `.env`
- [ ] `DATA_PRODUCT_BACKEND=supabase` set in `.env`
- [ ] Agent9 starts without errors
- [ ] Business process lookups work correctly
- [ ] Data product lookups work correctly
- [ ] Decision Studio shows correct data
- [ ] Fallback to YAML works if Supabase is down

---

## Design Decisions

### Why JSONB for Tables and Views?
**Problem:** DataProduct model has complex nested objects for table/view definitions  
**Solution:** Store as JSONB in Supabase  
**Benefit:** Direct Pydantic mapping, queryable with JSONB operators, flexible schema

### Why Array for related_business_processes?
**Problem:** Data products can be related to multiple business processes  
**Solution:** Use PostgreSQL array type with normalized IDs  
**Benefit:** Efficient queries, GIN indexing, consistent with other registries

### Why Keep yaml_contract_path?
**Problem:** Some data products reference external YAML contracts  
**Solution:** Store the path in Supabase for reference  
**Benefit:** Maintains compatibility with existing data product loading logic

---

## Migration Statistics

**Business Processes:**
- **Total in Registry:** ~31
- **Fields Migrated:** 8 (id, name, domain, description, owner_role, stakeholder_roles, display_name, tags, metadata)
- **Array Fields:** 2 (stakeholder_roles, tags)
- **JSONB Fields:** 1 (metadata)
- **Indexes Created:** 6

**Data Products:**
- **Total in Registry:** ~6
- **Fields Migrated:** 14 (id, name, domain, description, owner, version, related_business_processes, tags, metadata, tables, views, yaml_contract_path, output_path, last_updated, reviewed, language, documentation)
- **Array Fields:** 2 (related_business_processes, tags)
- **JSONB Fields:** 3 (metadata, tables, views)
- **Indexes Created:** 9

---

## Next Steps

### Immediate (Phase 4 Validation):
1. Run validation checklist above
2. Test business process lookups in agents
3. Test data product lookups in agents
4. Verify Decision Studio displays correct data
5. Test fallback by stopping Supabase

### Phase 5: Enterprise Hardening
- Implement RLS policies for multi-tenancy
- Add audit trail tables and triggers
- Add FK constraints: `data_products.related_business_processes` → `business_processes.id`
- HR system sync design
- Monitoring & alerting setup
- Backup/DR procedures

### Production Deployment
- Deploy to managed Supabase
- Configure production environment variables
- Set up CI/CD for migrations
- Implement automated seeding pipeline

---

**Status:** Ready for validation testing 🚀

**Phases Complete:** 1 (Business Glossary), 2 (Principal Profiles), 3 (KPI Registry), 4 (Business Processes & Data Products) ✅

**Total Registries Migrated:** 5 out of 5 core registries ✅
