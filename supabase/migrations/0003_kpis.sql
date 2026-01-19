-- Migration: Create kpis table
-- Generated on 2026-01-17
-- Purpose: Store KPI definitions with normalized business process relationships

-- KPIs table
-- Maps to KPI Pydantic model in src/registry/models/kpi.py
create table if not exists public.kpis (
    -- Core identity
    id text primary key,
    name text not null,
    domain text not null,
    description text,
    unit text,
    
    -- Data source
    data_product_id text not null,
    view_name text,
    
    -- Normalized business process relationships (IDs, not display names)
    business_process_ids text[] default '{}',
    
    -- SQL and calculation
    sql_query text,
    
    -- Filters (JSONB for flexibility)
    filters jsonb default '{}',
    
    -- Thresholds (array of threshold objects)
    -- Each threshold: {comparison_type, green_threshold, yellow_threshold, red_threshold, inverse_logic}
    thresholds jsonb default '[]',
    
    -- Dimensions (array of dimension objects)
    -- Each dimension: {name, field, values[], description}
    dimensions jsonb default '[]',
    
    -- Categorization
    tags text[] default '{}',
    synonyms text[] default '{}',
    
    -- Ownership
    owner_role text,
    stakeholder_roles text[] default '{}',
    
    -- Extension point for line/altitude and other metadata
    -- Includes: line, altitude, profit_driver_type, lens_affinity
    metadata jsonb default '{}',
    
    -- Audit fields
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Indexes for common queries
create index if not exists kpis_domain_idx
    on public.kpis (domain);

create index if not exists kpis_data_product_id_idx
    on public.kpis (data_product_id);

create index if not exists kpis_owner_role_idx
    on public.kpis (owner_role);

create index if not exists kpis_name_idx
    on public.kpis (name);

-- Full-text search on name and description
create index if not exists kpis_search_idx
    on public.kpis using gin (
        to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, ''))
    );

-- GIN index for business_process_ids array lookups
create index if not exists kpis_business_process_ids_idx
    on public.kpis using gin (business_process_ids);

-- GIN index for tags array lookups
create index if not exists kpis_tags_idx
    on public.kpis using gin (tags);

-- GIN index for metadata JSONB queries (e.g., line, altitude)
create index if not exists kpis_metadata_idx
    on public.kpis using gin (metadata);

-- Updated timestamp trigger (reuse function from principal_profiles)
create trigger update_kpis_updated_at
    before update on public.kpis
    for each row
    execute function public.update_updated_at_column();

-- Comments for documentation
comment on table public.kpis is 'KPI definitions for situation awareness and analysis. Maps to KPI Pydantic model.';
comment on column public.kpis.id is 'Unique KPI identifier (e.g., gross_revenue)';
comment on column public.kpis.business_process_ids is 'Normalized array of business process IDs (not display names)';
comment on column public.kpis.thresholds is 'Array of threshold objects for KPI evaluation (green/yellow/red)';
comment on column public.kpis.dimensions is 'Array of dimension objects for KPI analysis (e.g., profit center, region)';
comment on column public.kpis.metadata is 'Extension point including line, altitude, profit_driver_type, lens_affinity';
