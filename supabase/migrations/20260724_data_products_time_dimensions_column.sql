-- Migration: 20260724_data_products_time_dimensions_column
-- Purpose: data_products had no time_dimensions column at all — only
--          metadata/tables/views are real JSONB columns. DataProduct's
--          Pydantic model has always had a `time_dimensions` field, but
--          DatabaseRegistryProvider._serialize_item() filters every write
--          down to real DB columns (these tables are fully columnar, no
--          generic JSON blob), so the field was silently dropped on every
--          write — never an error, just gone. Discovered live: onboarding's
--          new time-dimension synthesis (Phase 12G) correctly computed a
--          fiscal_year_period spec, the API response showed it, but it never
--          reached Supabase.
--
--          The one place time_dimensions "worked" before this migration was
--          via a model_validator on DataProduct that backfills the top-level
--          field FROM metadata['time_dimensions'] on read (Apex Lubricants'
--          hand-authored seed script stashes it there specifically because no
--          dedicated column existed) — a documented workaround, not a real
--          persistence path. That validator is left in place as a read-side
--          compatibility shim for any existing rows using it; new writes go
--          through the real column added here.

ALTER TABLE public.data_products
    ADD COLUMN IF NOT EXISTS time_dimensions JSONB DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS idx_data_products_time_dimensions
    ON public.data_products USING gin(time_dimensions);

COMMENT ON COLUMN public.data_products.time_dimensions IS
    'List of TimeDimensionSpec dicts (type/column/year_column/period_column/... — see '
    'src/registry/models/data_product.py). The primary=true entry is used by SA/DA for '
    'QoQ/YoY/MoM temporal analysis via _resolve_time_spec.';
