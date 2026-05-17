-- Migration: 20260517_connection_profiles_backend
-- Purpose: Infra B — Move connection profiles from browser localStorage to Supabase.
--          Profiles are scoped by client_id (STRICT MATCH — same rule as all other tables).
--          Credentials are Fernet-encrypted server-side; never readable client-side.

CREATE TABLE IF NOT EXISTS public.connection_profiles (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       TEXT        NOT NULL,
    name            TEXT        NOT NULL,
    source_system   TEXT        NOT NULL,   -- bigquery | snowflake | duckdb | sqlserver | databricks
    host            TEXT,
    port            INTEGER,
    database_name   TEXT,
    schema_name     TEXT,
    credentials_encrypted TEXT,             -- Fernet-encrypted JSON blob; never returned to client
    is_default      BOOLEAN     NOT NULL DEFAULT FALSE,
    created_by      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at    TIMESTAMPTZ,
    last_used_by    TEXT,

    CONSTRAINT uq_connection_profiles_client_name UNIQUE (client_id, name)
);

CREATE INDEX IF NOT EXISTS idx_connection_profiles_client_id
    ON public.connection_profiles (client_id);

COMMENT ON TABLE public.connection_profiles IS
    'Per-client data source connection profiles. Credentials encrypted with Fernet. '
    'client_id is the tenant key — never mix records across tenants. '
    'Added Infra B (2026-05-17).';
