-- Migration 0007: Add client_id composite key to all registry tables
-- Date: 2026-02-20
-- Purpose: Multi-tenant isolation — each registry row is scoped to a client.
--          The business_contexts table is the client anchor (its id = client_id).
--          All other registry tables get client_id as part of the composite PK.
--
-- client_id defaults:
--   'lubricants'  -> principal_profiles, kpis, data_products  (existing seeded rows are Lubricants demo)
--   'default'     -> business_processes, business_glossary_terms  (shared/generic data)

-- ============================================================
-- 1. business_contexts — client anchor (already exists from 0006)
--    Add data_product_ids column if not present, then seed rows.
-- ============================================================
ALTER TABLE public.business_contexts
    ADD COLUMN IF NOT EXISTS data_product_ids text[] DEFAULT '{}';

-- Seed the two known demo clients (plus a shared 'default' client)
INSERT INTO public.business_contexts (id, name, industry, data_product_ids)
VALUES
  ('lubricants', 'Lubricants Business', 'Oil & Gas / Specialty Chemicals', ARRAY['dp_lubricants_financials']),
  ('bicycle',    'Global Bike Inc.',    'Retail & Manufacturing',           ARRAY['fi_star_schema']),
  ('default',    'Shared / Generic',   'All',                              ARRAY[]::text[])
ON CONFLICT (id) DO UPDATE SET
  data_product_ids = EXCLUDED.data_product_ids;

-- ============================================================
-- 2. principal_profiles — DEFAULT 'lubricants'
-- ============================================================
ALTER TABLE public.principal_profiles
    ADD COLUMN IF NOT EXISTS client_id text NOT NULL DEFAULT 'lubricants';

ALTER TABLE public.principal_profiles
    DROP CONSTRAINT IF EXISTS principal_profiles_pkey;

ALTER TABLE public.principal_profiles
    ADD PRIMARY KEY (client_id, id);

CREATE INDEX IF NOT EXISTS principal_profiles_client_id_idx
    ON public.principal_profiles (client_id);

-- ============================================================
-- 3. kpis — DEFAULT 'lubricants'
-- ============================================================
ALTER TABLE public.kpis
    ADD COLUMN IF NOT EXISTS client_id text NOT NULL DEFAULT 'lubricants';

ALTER TABLE public.kpis
    DROP CONSTRAINT IF EXISTS kpis_pkey;

ALTER TABLE public.kpis
    ADD PRIMARY KEY (client_id, id);

CREATE INDEX IF NOT EXISTS kpis_client_id_idx
    ON public.kpis (client_id);

-- ============================================================
-- 4. data_products — DEFAULT 'lubricants'
-- ============================================================
ALTER TABLE public.data_products
    ADD COLUMN IF NOT EXISTS client_id text NOT NULL DEFAULT 'lubricants';

ALTER TABLE public.data_products
    DROP CONSTRAINT IF EXISTS data_products_pkey;

ALTER TABLE public.data_products
    ADD PRIMARY KEY (client_id, id);

CREATE INDEX IF NOT EXISTS data_products_client_id_idx
    ON public.data_products (client_id);

-- ============================================================
-- 5. business_processes — DEFAULT 'default' (shared/generic)
-- ============================================================
ALTER TABLE public.business_processes
    ADD COLUMN IF NOT EXISTS client_id text NOT NULL DEFAULT 'default';

ALTER TABLE public.business_processes
    DROP CONSTRAINT IF EXISTS business_processes_pkey;

ALTER TABLE public.business_processes
    ADD PRIMARY KEY (client_id, id);

CREATE INDEX IF NOT EXISTS business_processes_client_id_idx
    ON public.business_processes (client_id);

-- ============================================================
-- 6. business_glossary_terms — DEFAULT 'default' (shared/generic)
-- ============================================================
ALTER TABLE public.business_glossary_terms
    ADD COLUMN IF NOT EXISTS client_id text NOT NULL DEFAULT 'default';

ALTER TABLE public.business_glossary_terms
    DROP CONSTRAINT IF EXISTS business_glossary_terms_pkey;

ALTER TABLE public.business_glossary_terms
    ADD PRIMARY KEY (client_id, id);

CREATE INDEX IF NOT EXISTS business_glossary_terms_client_id_idx
    ON public.business_glossary_terms (client_id);
