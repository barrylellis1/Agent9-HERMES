-- Migration: Fix business_glossary_terms schema to match Pydantic BusinessTerm model
-- Adds missing 'name' and 'client_id' columns, and aligns field names

-- 1. Add missing columns if they don't exist
ALTER TABLE IF EXISTS public.business_glossary_terms
  ADD COLUMN IF NOT EXISTS name text,
  ADD COLUMN IF NOT EXISTS client_id text DEFAULT 'default',
  ADD COLUMN IF NOT EXISTS synonyms text[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS technical_mappings jsonb DEFAULT '{}';

-- 2. Populate 'name' from 'term' if name is NULL
UPDATE public.business_glossary_terms
SET name = term
WHERE name IS NULL;

-- 3. Populate 'synonyms' from 'aliases' if aliases is not empty
UPDATE public.business_glossary_terms
SET synonyms = aliases
WHERE aliases != '{}' AND synonyms = '{}';

-- 4. Populate 'technical_mappings' from 'metadata' if metadata is not empty
UPDATE public.business_glossary_terms
SET technical_mappings = metadata
WHERE metadata != '{}'::jsonb AND technical_mappings = '{}'::jsonb;

-- 5. Make 'name' NOT NULL after populating
ALTER TABLE public.business_glossary_terms
  ALTER COLUMN name SET NOT NULL;

-- 6. Add index on name for faster lookups
CREATE INDEX IF NOT EXISTS business_glossary_terms_name_idx
  ON public.business_glossary_terms(name);

-- 7. Add composite index for client_id + name lookups
CREATE INDEX IF NOT EXISTS business_glossary_terms_client_name_idx
  ON public.business_glossary_terms(client_id, name);

-- Verify the migration
SELECT
  COUNT(*) as total_records,
  COUNT(name) as records_with_name,
  COUNT(CASE WHEN name IS NULL THEN 1 END) as null_name_count
FROM public.business_glossary_terms;
