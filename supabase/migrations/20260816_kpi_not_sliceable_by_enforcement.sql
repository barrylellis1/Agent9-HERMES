-- ---------------------------------------------------------------------------
-- not_sliceable_by is now ENFORCED by A9_Deep_Analysis_Agent, not just
-- displayed (docs/architecture/kpi_semantic_contract.md §4.5).
--
-- Corrects the comment written in 20260815_kpi_slice_validity_fields.sql,
-- which said "Advisory only -- nothing reads these to gate Deep Analysis's
-- dimension selection" -- true when that migration shipped, false as of
-- this one. DA now excludes every dimension in not_sliceable_by from
-- dims_to_process before the max_dimensions cut, and records each exclusion
-- on DeepAnalysisResponse.dimensions_excluded so it is never silent.
--
-- No column-level change: not_sliceable_by is JSONB and already accepted
-- arbitrary JSON. The shape stored in each array element changed at the
-- application layer (Pydantic) from a bare string to a structured object
-- {dimension, reason_class, note, source} -- src/registry/models/kpi.py's
-- NotSliceableByEntry, with a backward-compat validator that normalizes
-- already-persisted bare-string entries on read. No data backfill needed;
-- confirmed live against apex_lubricants' real persisted (pre-this-change)
-- deny list.
-- ---------------------------------------------------------------------------

COMMENT ON COLUMN kpis.not_sliceable_by IS
    'DENY list of dimensions this ratio KPI must not be sliced by -- one structured entry per dimension: {dimension, reason_class (structural|pipeline_gap), note, source (derived|declared)}. ENFORCED by A9_Deep_Analysis_Agent (docs/architecture/kpi_semantic_contract.md Sec4.5): excluded from analysis before the max_dimensions cut, recorded on DeepAnalysisResponse.dimensions_excluded. Defaults to empty (every dimension fine) until check_slice_validity finds otherwise. Deliberately a deny list, not an allow list: an allow list decays silently; a deny list fails loud. Populated only by A9_Data_Governance_Agent.check_slice_validity(), never authored by hand except a human override via source=declared.';
