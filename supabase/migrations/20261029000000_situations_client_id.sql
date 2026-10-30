-- Situations carry their client (code review 2026-10-29, finding 1; owner go-ahead 2026-10-29).
--
-- The situations table had no client column, so a stored card could not be tied to its tenant,
-- and isolation was "indirect via parent records" (see 20260713_rls_client_isolation.sql, which
-- listed situations as a known gap). Card ids now name client and period (a hash), which stops
-- the overwriting; this column lets reads be limited to one client and puts the table inside
-- the RLS boundary.
--
-- Rows written before this migration keep client_id NULL: the old ids cannot be traced to one
-- client reliably (two clients wrote the same id). Under the fail-closed policy below, a NULL
-- row is visible to no tenant-scoped read.

ALTER TABLE situations ADD COLUMN IF NOT EXISTS client_id TEXT;

CREATE INDEX IF NOT EXISTS idx_situations_client_id ON situations(client_id);

-- Tenant isolation (Infra B3), as CLAUDE.md requires for every table with a client_id column.
GRANT SELECT ON situations TO a9_tenant_scope;
ALTER TABLE situations ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS client_isolation ON situations;
CREATE POLICY client_isolation ON situations FOR SELECT TO a9_tenant_scope
    USING (client_id = current_setting('app.client_id', true));
