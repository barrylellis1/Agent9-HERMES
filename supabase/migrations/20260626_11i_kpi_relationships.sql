-- Phase 11I-B: KPI Relationship Registry for compound alert detection

CREATE TABLE IF NOT EXISTS kpi_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id VARCHAR(64) NOT NULL,
    kpi_id VARCHAR(128) NOT NULL,
    related_kpi_id VARCHAR(128) NOT NULL,
    relationship_type VARCHAR(32) NOT NULL,
    conflict_direction VARCHAR(16) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT kpi_relationships_pk UNIQUE (client_id, kpi_id, related_kpi_id)
);

CREATE INDEX IF NOT EXISTS idx_kpi_relationships_client_kpi ON kpi_relationships (client_id, kpi_id);
CREATE INDEX IF NOT EXISTS idx_kpi_relationships_client_related ON kpi_relationships (client_id, related_kpi_id);

COMMENT ON TABLE kpi_relationships IS 'Declared relationships between KPI pairs for compound alert detection (11I-B).';
