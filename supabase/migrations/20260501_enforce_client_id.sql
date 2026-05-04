-- Migration: 20260501_enforce_client_id
-- Purpose: Remove shared 'default' client rows; enforce explicit client_id ownership
--          on all registry tables. No row may exist without a real client_id.
--
-- Steps:
--   1. Copy business_processes and glossary from 'default' → each demo client
--   2. Delete 'default' rows
--   3. Drop DEFAULT values from client_id columns (every INSERT must be explicit)
--   4. Add CHECK constraints (empty string is also invalid)
--
-- Run locally:  .\supabase.exe db push --local
-- Run on prod:  .\supabase.exe db push

-- ============================================================
-- 1. Duplicate 'default' business_processes to each demo client
-- ============================================================

INSERT INTO public.business_processes
    (id, client_id, name, domain, description, display_name, owner_role,
     stakeholder_roles, tags, metadata)
SELECT
    id, 'bicycle', name, domain, description, display_name, owner_role,
    stakeholder_roles, tags, metadata
FROM public.business_processes
WHERE client_id = 'default'
ON CONFLICT (client_id, id) DO NOTHING;

INSERT INTO public.business_processes
    (id, client_id, name, domain, description, display_name, owner_role,
     stakeholder_roles, tags, metadata)
SELECT
    id, 'lubricants', name, domain, description, display_name, owner_role,
    stakeholder_roles, tags, metadata
FROM public.business_processes
WHERE client_id = 'default'
ON CONFLICT (client_id, id) DO NOTHING;

-- ============================================================
-- 2. Duplicate 'default' glossary terms to each demo client
--    (table may be empty — INSERT ... SELECT on 0 rows is a no-op)
-- ============================================================

INSERT INTO public.business_glossary_terms
    (id, client_id, term, definition, tags, metadata)
SELECT
    id, 'bicycle', term, definition, tags, metadata
FROM public.business_glossary_terms
WHERE client_id = 'default'
ON CONFLICT (client_id, id) DO NOTHING;

INSERT INTO public.business_glossary_terms
    (id, client_id, term, definition, tags, metadata)
SELECT
    id, 'lubricants', term, definition, tags, metadata
FROM public.business_glossary_terms
WHERE client_id = 'default'
ON CONFLICT (client_id, id) DO NOTHING;

-- ============================================================
-- 3. Delete 'default' rows — no shared state in production
-- ============================================================

DELETE FROM public.business_processes WHERE client_id = 'default';
DELETE FROM public.business_glossary_terms WHERE client_id = 'default';

-- Also delete any 'default' rows in other tables that snuck in
DELETE FROM public.kpis WHERE client_id = 'default';
DELETE FROM public.data_products WHERE client_id = 'default';
DELETE FROM public.principal_profiles WHERE client_id = 'default';

-- ============================================================
-- 4. Drop DEFAULT values — every INSERT must supply client_id
-- ============================================================

ALTER TABLE public.kpis
    ALTER COLUMN client_id DROP DEFAULT;

ALTER TABLE public.data_products
    ALTER COLUMN client_id DROP DEFAULT;

ALTER TABLE public.principal_profiles
    ALTER COLUMN client_id DROP DEFAULT;

ALTER TABLE public.business_processes
    ALTER COLUMN client_id DROP DEFAULT;

ALTER TABLE public.business_glossary_terms
    ALTER COLUMN client_id DROP DEFAULT;

-- ============================================================
-- 5. Add CHECK constraints — empty string is also invalid
-- ============================================================

ALTER TABLE public.kpis
    ADD CONSTRAINT kpis_client_id_nonempty
    CHECK (client_id <> '');

ALTER TABLE public.data_products
    ADD CONSTRAINT data_products_client_id_nonempty
    CHECK (client_id <> '');

ALTER TABLE public.principal_profiles
    ADD CONSTRAINT principal_profiles_client_id_nonempty
    CHECK (client_id <> '');

ALTER TABLE public.business_processes
    ADD CONSTRAINT business_processes_client_id_nonempty
    CHECK (client_id <> '');

ALTER TABLE public.business_glossary_terms
    ADD CONSTRAINT glossary_client_id_nonempty
    CHECK (client_id <> '');
