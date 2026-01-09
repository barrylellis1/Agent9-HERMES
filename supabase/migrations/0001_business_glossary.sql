-- Migration: Create business_glossary_terms table for pilot
-- Generated on 2026-01-08

create table if not exists public.business_glossary_terms (
    id text primary key,
    term text not null,
    definition text,
    aliases text[] default '{}',
    tags text[] default '{}',
    metadata jsonb default '{}',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists business_glossary_terms_term_idx
    on public.business_glossary_terms using gin (to_tsvector('english', term));

create index if not exists business_glossary_terms_aliases_idx
    on public.business_glossary_terms using gin (aliases);
