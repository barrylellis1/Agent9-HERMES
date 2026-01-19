-- Migration: Business Processes Registry
-- Description: Create business_processes table for storing business process definitions
-- Date: 2026-01-17

-- Create business_processes table
create table if not exists public.business_processes (
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

-- Add comments for documentation
comment on table public.business_processes is 'Registry of business processes across all domains';
comment on column public.business_processes.id is 'Unique identifier (e.g., finance_profitability_analysis)';
comment on column public.business_processes.name is 'Human-readable name (e.g., Profitability Analysis)';
comment on column public.business_processes.domain is 'Business domain (e.g., Finance, HR, Sales)';
comment on column public.business_processes.description is 'Detailed description of the business process';
comment on column public.business_processes.owner_role is 'Primary role responsible for this process';
comment on column public.business_processes.stakeholder_roles is 'Array of roles with a stake in this process';
comment on column public.business_processes.display_name is 'Display name in format "Domain: Name"';
comment on column public.business_processes.tags is 'Array of tags for categorization';
comment on column public.business_processes.metadata is 'Additional metadata for extensions';

-- Create indexes for common query patterns
create index if not exists idx_business_processes_domain on public.business_processes(domain);
create index if not exists idx_business_processes_owner_role on public.business_processes(owner_role);
create index if not exists idx_business_processes_name on public.business_processes(name);

-- GIN indexes for array and JSONB columns
create index if not exists idx_business_processes_tags on public.business_processes using gin(tags);
create index if not exists idx_business_processes_stakeholder_roles on public.business_processes using gin(stakeholder_roles);
create index if not exists idx_business_processes_metadata on public.business_processes using gin(metadata);

-- Full-text search index
create index if not exists idx_business_processes_search on public.business_processes 
using gin(to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, '')));

-- Reuse the update_updated_at_column trigger from principal_profiles
create trigger update_business_processes_updated_at
    before update on public.business_processes
    for each row
    execute function public.update_updated_at_column();
