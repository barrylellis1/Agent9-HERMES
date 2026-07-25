-- Migration: 20260721_connection_profiles_add_snowflake_fields
-- Purpose: connection_profiles only had host/port/database_name/schema_name as
--          plain (non-secret) columns plus one encrypted credentials blob.
--          Snowflake needs three more non-secret fields (warehouse, username,
--          role) that don't fit any existing column without overloading its
--          meaning. Discovered live: getConnectionOverrides() was mapping
--          warehouse from schema_name (there was nowhere else to put it) and
--          silently dropping username/role/schema entirely on profile load.

ALTER TABLE public.connection_profiles
    ADD COLUMN IF NOT EXISTS warehouse TEXT,
    ADD COLUMN IF NOT EXISTS username   TEXT,
    ADD COLUMN IF NOT EXISTS role       TEXT;

COMMENT ON COLUMN public.connection_profiles.warehouse IS
    'Snowflake warehouse name. Not secret — stored in plain text like host/database_name/schema_name.';
COMMENT ON COLUMN public.connection_profiles.username IS
    'Connection username (snowflake, sqlserver). Not treated as secret; password remains in credentials_encrypted.';
COMMENT ON COLUMN public.connection_profiles.role IS
    'Optional Snowflake role.';
