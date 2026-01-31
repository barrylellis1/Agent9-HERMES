-- Migration: Data Products Registry
-- Description: Create data_products table for storing data product definitions
-- Date: 2026-01-17

-- Create data_products table
create table if not exists public.data_products (
    id text primary key,
    name text not null,
    domain text not null,
    description text,
    owner text not null,
    version text default '1.0.0',
    source_system text default 'duckdb',
    related_business_processes text[] default '{}',
    tags text[] default '{}',
    metadata jsonb default '{}',
    tables jsonb default '{}',
    views jsonb default '{}',
    yaml_contract_path text,
    output_path text,
    last_updated date,
    reviewed boolean default false,
    staging boolean default false,
    language text default 'EN',
    documentation text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Add comments for documentation
comment on table public.data_products is 'Registry of data products across all domains';
comment on column public.data_products.id is 'Unique identifier (e.g., dp_fi_20250516_001)';
comment on column public.data_products.name is 'Human-readable name of the data product';
comment on column public.data_products.domain is 'Business domain (e.g., FI, SAP, HR)';
comment on column public.data_products.description is 'Description of the data product';
comment on column public.data_products.owner is 'Owner of the data product (team or role)';
comment on column public.data_products.version is 'Version of the data product';
comment on column public.data_products.related_business_processes is 'Array of business process IDs';
comment on column public.data_products.tags is 'Array of tags for categorization';
comment on column public.data_products.metadata is 'Additional metadata for extensions';
comment on column public.data_products.tables is 'JSONB object containing table definitions';
comment on column public.data_products.views is 'JSONB object containing view definitions';
comment on column public.data_products.yaml_contract_path is 'Path to YAML contract file';
comment on column public.data_products.output_path is 'Path to output data files';
comment on column public.data_products.last_updated is 'Date of last update';
comment on column public.data_products.reviewed is 'Whether the data product has been reviewed';
comment on column public.data_products.language is 'Language code (e.g., EN, DE)';
comment on column public.data_products.documentation is 'Documentation or notes';

-- Create indexes for common query patterns
create index if not exists idx_data_products_domain on public.data_products(domain);
create index if not exists idx_data_products_owner on public.data_products(owner);
create index if not exists idx_data_products_name on public.data_products(name);
create index if not exists idx_data_products_reviewed on public.data_products(reviewed);

-- GIN indexes for array and JSONB columns
create index if not exists idx_data_products_tags on public.data_products using gin(tags);
create index if not exists idx_data_products_related_bps on public.data_products using gin(related_business_processes);
create index if not exists idx_data_products_metadata on public.data_products using gin(metadata);
create index if not exists idx_data_products_tables on public.data_products using gin(tables);
create index if not exists idx_data_products_views on public.data_products using gin(views);

-- Full-text search index
create index if not exists idx_data_products_search on public.data_products 
using gin(to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, '') || ' ' || coalesce(documentation, '')));

-- Reuse the update_updated_at_column trigger
create trigger update_data_products_updated_at
    before update on public.data_products
    for each row
    execute function public.update_updated_at_column();

-- Optional: Add foreign key constraint to business_processes (can be added in Phase 5)
-- This is commented out for now to avoid circular dependencies during initial migration
-- alter table public.data_products
--     add constraint fk_data_products_business_processes
--     foreign key (related_business_processes) references public.business_processes(id);
