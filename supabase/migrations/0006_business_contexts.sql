-- Migration: Business Contexts
-- Purpose: Store business context metadata for demos and customer deployments
-- Date: 2026-02-15

-- Create updated_at trigger function if not exists
create or replace function update_updated_at_column()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- Business Contexts table
create table if not exists business_contexts (
    id text primary key,
    name text not null,
    industry text not null,
    sub_sector text,
    description text,
    revenue text,
    employees text,
    ownership text,
    business_model jsonb default '{}',
    strategic_priorities text[] default '{}',
    competitors text[] default '{}',
    operational_context jsonb default '{}',
    consulting_spend text,
    consulting_firms_used jsonb default '{}',
    pain_points text[] default '{}',
    metadata jsonb default '{}',
    is_demo boolean default true,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

-- Indexes for performance
create index if not exists idx_business_contexts_industry on business_contexts(industry);
create index if not exists idx_business_contexts_is_demo on business_contexts(is_demo);
create index if not exists idx_business_contexts_name on business_contexts(name);

-- Updated_at trigger
drop trigger if exists set_updated_at_business_contexts on business_contexts;
create trigger set_updated_at_business_contexts
    before update on business_contexts
    for each row
    execute function update_updated_at_column();

-- Comments for documentation
comment on table business_contexts is 'Business context metadata for demos and customer deployments';
comment on column business_contexts.id is 'Unique identifier (e.g., demo_bicycle, demo_lubricants, customer_valvoline)';
comment on column business_contexts.is_demo is 'Flag to distinguish demo contexts from real customer contexts';
comment on column business_contexts.business_model is 'JSON structure containing revenue_streams, key_markets, etc.';
comment on column business_contexts.operational_context is 'JSON structure containing challenges, margin_pressures, etc.';
comment on column business_contexts.consulting_firms_used is 'JSON structure with firm names and spend amounts';
