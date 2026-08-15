-- ---------------------------------------------------------------------------
-- KPI slice validity fields (docs/architecture/kpi_semantic_contract.md §4)
--
-- Wires A9_Data_Governance_Agent.check_slice_validity() to a real column set.
-- Advisory only -- nothing reads these to gate Deep Analysis's dimension
-- selection or block onboarding; that was designed and explicitly rejected
-- as scope creep at demo stage (DEVELOPMENT_PLAN.md -> Phase 15 -> Stage I).
--
-- Three fields on the KPI record, not a separate audit table. Safe because
-- data_product_id is a scalar column on kpis -- one KPI record, for one
-- client, always resolves to exactly one data product, so there is never an
-- ambiguity about which schema/grain not_sliceable_by refers to. A separate
-- table was the first draft of this design; dropped once that was confirmed,
-- because it would have needed the full 3-part RLS block (GRANT, ENABLE ROW
-- LEVEL SECURITY, CREATE POLICY) plus a new entry in
-- scripts/verify_prod_registry.py's _RLS_TABLES -- exactly the failure shape
-- this codebase has hit before, a new tenant table left outside isolation
-- because one of three required steps was skipped. New columns on `kpis`
-- need none of that: `kpis` is already in _RLS_TABLES and the existing
-- client_isolation policy covers every column on the table automatically.
-- ---------------------------------------------------------------------------

ALTER TABLE kpis
    ADD COLUMN IF NOT EXISTS not_sliceable_by JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS slice_validity_details JSONB,
    ADD COLUMN IF NOT EXISTS slice_validity_checked_at TIMESTAMPTZ;

COMMENT ON COLUMN kpis.not_sliceable_by IS
    'DENY list of dimensions this ratio KPI must not be sliced by -- defaults to empty (every dimension fine) until check_slice_validity finds otherwise. Deliberately a deny list, not an allow list: an allow list decays silently (a new column never analysed, nobody notices); a deny list fails loud. Populated only by A9_Data_Governance_Agent.check_slice_validity(), never authored by hand.';

COMMENT ON COLUMN kpis.slice_validity_details IS
    'Last check_slice_validity run''s raw per-dimension coverage -- {dimension: {counts, coverage, verdict}} -- so a human can see WHY a dimension is denied, not just that it is.';

COMMENT ON COLUMN kpis.slice_validity_checked_at IS
    'When check_slice_validity last ran for this KPI. Must be surfaced prominently wherever not_sliceable_by is displayed -- a stale green result trusted because it looks current is the primary failure mode this field exists to prevent.';
