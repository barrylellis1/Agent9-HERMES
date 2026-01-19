-- Migration: Create principal_profiles table
-- Generated on 2026-01-17
-- Purpose: Store principal profiles with normalized business process relationships

-- Principal Profiles table
-- Maps to PrincipalProfile Pydantic model in src/registry/models/principal.py
create table if not exists public.principal_profiles (
    -- Core identity
    id text primary key,
    name text not null,
    title text,
    
    -- HR-style attributes (from Workday/SuccessFactors)
    first_name text,
    last_name text,
    role text,
    department text,
    source text,
    description text,
    
    -- Context & responsibilities
    responsibilities text[] default '{}',
    
    -- Normalized business process relationships (IDs, not display names)
    business_process_ids text[] default '{}',
    
    -- Filters & preferences
    default_filters jsonb default '{}',
    typical_timeframes text[] default '{}',
    principal_groups text[] default '{}',
    
    -- Persona & behavior (decision_style, risk_tolerance, communication_style, values)
    persona_profile jsonb default '{}',
    
    -- UI & channel preferences
    preferences jsonb default '{}',
    
    -- Access control
    permissions text[] default '{}',
    
    -- Time frame preferences (default_period, historical_periods, forward_looking_periods)
    time_frame jsonb default '{}',
    
    -- Communication preferences (detail_level, format_preference, emphasis)
    communication jsonb default '{}',
    
    -- Extension point for KPI preferences and other metadata
    -- Includes: kpi_line_preference, kpi_altitude_preference
    metadata jsonb default '{}',
    
    -- Audit fields
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Indexes for common queries
create index if not exists principal_profiles_role_idx
    on public.principal_profiles (role);

create index if not exists principal_profiles_department_idx
    on public.principal_profiles (department);

create index if not exists principal_profiles_name_idx
    on public.principal_profiles (name);

-- Full-text search on name and title
create index if not exists principal_profiles_search_idx
    on public.principal_profiles using gin (
        to_tsvector('english', coalesce(name, '') || ' ' || coalesce(title, ''))
    );

-- GIN index for business_process_ids array lookups
create index if not exists principal_profiles_business_process_ids_idx
    on public.principal_profiles using gin (business_process_ids);

-- Updated timestamp trigger
create or replace function public.update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

create trigger update_principal_profiles_updated_at
    before update on public.principal_profiles
    for each row
    execute function public.update_updated_at_column();

-- Comments for documentation
comment on table public.principal_profiles is 'Principal profiles for context-aware agent behavior. Maps to PrincipalProfile Pydantic model.';
comment on column public.principal_profiles.id is 'Unique principal identifier (e.g., cfo_001)';
comment on column public.principal_profiles.business_process_ids is 'Normalized array of business process IDs (not display names)';
comment on column public.principal_profiles.persona_profile is 'Decision style, risk tolerance, communication style, values';
comment on column public.principal_profiles.metadata is 'Extension point including kpi_line_preference, kpi_altitude_preference';
