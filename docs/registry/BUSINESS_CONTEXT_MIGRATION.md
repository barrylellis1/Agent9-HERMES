# Business Context Migration to Supabase

**Date:** 2026-02-15  
**Status:** ✅ Implementation Complete - Ready for Testing

---

## Overview

This migration adds support for storing business context metadata in Supabase, enabling:
- **Multi-demo capability** - Switch between bicycle, lubricants, and other industry demos
- **Customer onboarding** - Store real customer contexts alongside demos
- **Dynamic switching** - Change contexts via environment variable or UI
- **Foundation for multi-tenancy** - Each context = potential tenant

---

## What Was Built

### 1. Database Schema (`0006_business_contexts.sql`)

Created `business_contexts` table with:
- **Core fields:** id, name, industry, sub_sector, description, revenue, employees, ownership
- **Business model:** JSONB for revenue_streams, key_markets
- **Strategic data:** strategic_priorities[], competitors[], pain_points[]
- **Operational context:** JSONB for challenges, margin pressures
- **Consulting data:** consulting_spend, consulting_firms_used (JSONB)
- **Demo flag:** is_demo boolean to distinguish demos from real customers
- **Timestamps:** created_at, updated_at with trigger

### 2. Provider (`business_context_provider.py`)

Implemented `SupabaseBusinessContextProvider` with:
- `get_context(context_id)` - Fetch by ID
- `list_contexts(is_demo=None)` - List all or filter by demo flag
- Converts Supabase rows to `A9_PS_BusinessContext` Pydantic models
- Error handling with logging

### 3. Seed Script (`supabase_seed_business_contexts.py`)

Features:
- Seeds bicycle demo context (from existing YAML)
- Seeds new lubricants demo context
- Supports `--dry-run` and `--truncate-first` flags
- Idempotent upserts via `resolution=merge-duplicates`

### 4. YAML Reference (`lubricants_context.yaml`)

Created reference YAML for lubricants demo with:
- Summit Lubricants & Specialty Products profile
- $3.2B revenue, 4,800 employees
- Automotive & industrial lubricants focus
- Realistic pain points for CFO/FP&A use cases
- Based on Valvoline/ExxonMobil industry knowledge

### 5. Loader Integration (`business_context_loader.py`)

Updated to support:
- `BUSINESS_CONTEXT_BACKEND=supabase` - Use Supabase provider
- `A9_BUSINESS_CONTEXT=demo_lubricants` - Select context by ID
- Fallback to YAML if Supabase fails
- Backward compatible with existing YAML paths

---

## Demo Contexts Available

### 1. Bicycle Retail (`demo_bicycle`)
- **Industry:** Retail & Manufacturing
- **Company:** Global Bike Inc.
- **Use Cases:** Inventory optimization, supply chain, e-bike expansion
- **Status:** Migrated from existing YAML

### 2. Lubricants & Specialty Products (`demo_lubricants`)
- **Industry:** Specialty Chemicals & Automotive Aftermarket
- **Company:** Summit Lubricants & Specialty Products
- **Revenue:** $3.2B, 4,800 employees
- **Use Cases:** Margin analysis, product mix optimization, plant utilization
- **Target:** Valvoline Sr. Director of Analytics (warm contact)
- **Status:** New, ready for demo

---

## How to Use

### Step 1: Apply Migration

```bash
# Reset database and apply all migrations (including 0006)
supabase db reset
```

### Step 2: Seed Data

```bash
# Dry run to preview data
python scripts/supabase_seed_business_contexts.py --dry-run

# Seed both demo contexts
python scripts/supabase_seed_business_contexts.py

# Or truncate first (clean slate)
python scripts/supabase_seed_business_contexts.py --truncate-first
```

### Step 3: Configure Environment

Add to `.env`:

```bash
# Enable Supabase backend for business contexts
BUSINESS_CONTEXT_BACKEND=supabase

# Select demo context (bicycle or lubricants)
A9_BUSINESS_CONTEXT=demo_lubricants

# Supabase connection (should already be set from Phase 1-4)
SUPABASE_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### Step 4: Test Demo Switching

```bash
# Switch to bicycle demo
export A9_BUSINESS_CONTEXT=demo_bicycle
# Restart Decision Studio
.\restart_app.ps1

# Switch to lubricants demo
export A9_BUSINESS_CONTEXT=demo_lubricants
# Restart Decision Studio
.\restart_app.ps1
```

### Step 5: Verify in Decision Studio

1. Start Decision Studio UI
2. Check that business context reflects selected demo
3. Verify agents use correct industry context
4. Test situation detection with demo-specific KPIs

---

## Environment Variables Reference

| Variable | Values | Default | Purpose |
|----------|--------|---------|---------|
| `BUSINESS_CONTEXT_BACKEND` | `yaml`, `supabase` | `yaml` | Choose backend provider |
| `A9_BUSINESS_CONTEXT` | `demo_bicycle`, `demo_lubricants`, etc. | None | Context ID for Supabase |
| `A9_BUSINESS_CONTEXT_YAML` | File path | None | Legacy YAML path (fallback) |
| `SUPABASE_URL` | URL | None | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Key | None | Service role key |
| `SUPABASE_BUSINESS_CONTEXTS_TABLE` | Table name | `business_contexts` | Override table name |

---

## Adding New Demo Contexts

### Option 1: Via Seed Script

1. Edit `scripts/supabase_seed_business_contexts.py`
2. Add new context to `get_all_contexts()`:
   ```python
   def create_energy_upstream_context() -> dict:
       return {
           "id": "demo_energy_upstream",
           "name": "Apex Energy Partners",
           "industry": "Energy",
           # ...
       }
   ```
3. Re-run seed script

### Option 2: Direct SQL Insert

```sql
INSERT INTO business_contexts (
    id, name, industry, sub_sector, description, is_demo
) VALUES (
    'demo_energy_upstream',
    'Apex Energy Partners',
    'Energy',
    'Upstream Oil & Gas (E&P)',
    'Independent E&P company...',
    true
);
```

### Option 3: Via Supabase Studio UI

1. Open http://127.0.0.1:54323
2. Navigate to Table Editor → business_contexts
3. Click "Insert row"
4. Fill in fields and save

---

## Architecture Benefits

### Multi-Tenancy Foundation
- Each context = potential tenant
- `is_demo=true` for demos, `is_demo=false` for real customers
- Easy to add `customer_id` FK for access control

### Rapid Customer Onboarding
- New customer = new context row
- No code changes needed
- Switch contexts via env var or UI

### Industry Templates
- Pre-built contexts for common industries
- Copy and customize for new customers
- Validate onboarding process with demos

### Scalability
- Contexts stored in database, not code
- UI can list available contexts dynamically
- Support hundreds of customers without code changes

---

## Next Steps

### Phase 1: Validation (This Sprint)
- [ ] Apply migration: `supabase db reset`
- [ ] Seed contexts: `python scripts/supabase_seed_business_contexts.py`
- [ ] Set `BUSINESS_CONTEXT_BACKEND=supabase` in `.env`
- [ ] Set `A9_BUSINESS_CONTEXT=demo_lubricants`
- [ ] Test Decision Studio with lubricants context
- [ ] Verify agents use lubricants-specific context
- [ ] Switch to bicycle demo and verify

### Phase 2: UI Demo Selector (After Valvoline Interest)
- [ ] Add demo selector to Login page or Admin Console
- [ ] Store selected context in session/localStorage
- [ ] Pass context_id to backend via API header
- [ ] Backend dynamically loads context from Supabase
- [ ] Live demo switching during presentations

### Phase 3: Customer Onboarding (Before First Pilot)
- [ ] Add customer context creation workflow
- [ ] Implement context cloning (copy demo → customize)
- [ ] Add context validation rules
- [ ] Build context management UI in Admin Console
- [ ] Document customer onboarding process

---

## Files Changed

### New Files
- `supabase/migrations/0006_business_contexts.sql`
- `src/registry/business_context/business_context_provider.py`
- `scripts/supabase_seed_business_contexts.py`
- `src/registry_references/business_context/lubricants_context.yaml`
- `docs/registry/BUSINESS_CONTEXT_MIGRATION.md`

### Modified Files
- `src/agents/shared/business_context_loader.py` - Added Supabase support

---

## Testing Checklist

- [ ] Migration applies without errors
- [ ] Seed script runs successfully
- [ ] Both demo contexts visible in Supabase Studio
- [ ] Provider fetches bicycle context correctly
- [ ] Provider fetches lubricants context correctly
- [ ] Loader uses Supabase when `BUSINESS_CONTEXT_BACKEND=supabase`
- [ ] Loader falls back to YAML on Supabase failure
- [ ] Decision Studio loads correct context
- [ ] Agents receive correct business context
- [ ] Switching contexts via env var works
- [ ] No errors in application logs

---

## Success Criteria

✅ **Migration Complete When:**
1. Both demo contexts seeded in Supabase
2. Can switch between demos via `A9_BUSINESS_CONTEXT` env var
3. Decision Studio reflects selected context
4. Agents use context-specific data
5. No breaking changes to existing YAML workflow

✅ **Ready for Valvoline Demo When:**
1. Lubricants context validated end-to-end
2. Demo shows lubricants-specific use cases
3. Can explain rapid industry adaptation capability
4. Bicycle demo still works (preserved)

---

## Support

For issues or questions:
1. Check Supabase Studio: http://127.0.0.1:54323
2. Review application logs for context loading
3. Verify environment variables are set correctly
4. Test with `--dry-run` flag first
5. Check YAML fallback is working
