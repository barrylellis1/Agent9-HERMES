"""KPI.not_sliceable_by structured shape — docs/architecture/kpi_semantic_contract.md §4.

Covers the 2026-08-16 change from a flat List[str] deny list to a list of
NotSliceableByEntry({dimension, reason_class, note, source}), and the
backward-compat validator that lets already-persisted flat-string records
(written before this change) still load without a migration.
"""
from src.registry.models.kpi import KPI, NotSliceableByEntry


def _kpi(**overrides):
    defaults = dict(
        id="gross_margin_pct",
        client_id="lubricants",
        name="Gross Margin %",
        domain="Finance",
        data_product_id="dp1",
    )
    defaults.update(overrides)
    return KPI(**defaults)


class TestDefaults:
    def test_empty_by_default(self):
        assert _kpi().not_sliceable_by == []


class TestStructuredEntries:
    def test_accepts_dict_entries(self):
        kpi = _kpi(not_sliceable_by=[
            {"dimension": "customer_name", "reason_class": "pipeline_gap", "source": "derived", "note": "5% coverage"},
        ])
        assert len(kpi.not_sliceable_by) == 1
        entry = kpi.not_sliceable_by[0]
        assert isinstance(entry, NotSliceableByEntry)
        assert entry.dimension == "customer_name"
        assert entry.reason_class == "pipeline_gap"
        assert entry.source == "derived"
        assert entry.note == "5% coverage"

    def test_reason_class_and_source_default(self):
        # A minimal entry (dimension only) still gets safe defaults, not a validation error —
        # §4.3's "prefer loud" principle: an unclassified gap defaults to actionable
        # (pipeline_gap), not silently assumed permanent (structural).
        kpi = _kpi(not_sliceable_by=[{"dimension": "region"}])
        entry = kpi.not_sliceable_by[0]
        assert entry.reason_class == "pipeline_gap"
        assert entry.source == "derived"

    def test_structural_override_accepted(self):
        kpi = _kpi(not_sliceable_by=[
            {"dimension": "customer_name", "reason_class": "structural", "source": "declared",
             "note": "COGS is booked at product level only — verified with client controller"},
        ])
        entry = kpi.not_sliceable_by[0]
        assert entry.reason_class == "structural"
        assert entry.source == "declared"


class TestLegacyFlatStringBackwardCompat:
    """Real KPI records were persisted with a bare list of dimension names
    before this field carried reason_class/source/note (2026-08-16) — these
    must still load, not fail validation, so already-checked KPIs don't
    become unreadable after this change ships."""

    def test_flat_string_list_normalizes(self):
        kpi = _kpi(not_sliceable_by=["customer_name", "channel_name"])
        dims = [e.dimension for e in kpi.not_sliceable_by]
        assert dims == ["customer_name", "channel_name"]
        for entry in kpi.not_sliceable_by:
            assert isinstance(entry, NotSliceableByEntry)
            # Prefer loud: an unclassified legacy entry defaults to pipeline_gap
            # (actionable), not structural (permanent, nothing to fix).
            assert entry.reason_class == "pipeline_gap"
            assert entry.source == "derived"
            assert entry.note is None

    def test_mixed_legacy_and_structured_entries(self):
        # Defensive: a record could plausibly be re-saved partway through a
        # migration with one entry in each shape. Both must survive.
        kpi = _kpi(not_sliceable_by=[
            "customer_name",
            {"dimension": "product_line", "reason_class": "structural", "source": "declared"},
        ])
        assert len(kpi.not_sliceable_by) == 2
        assert kpi.not_sliceable_by[0].dimension == "customer_name"
        assert kpi.not_sliceable_by[0].reason_class == "pipeline_gap"
        assert kpi.not_sliceable_by[1].dimension == "product_line"
        assert kpi.not_sliceable_by[1].reason_class == "structural"


class TestModelCopyPreservesShape:
    def test_model_copy_update_keeps_structured_entries_readable(self):
        # Mirrors what A9_Data_Governance_Agent.check_slice_validity() actually
        # does: kpi.model_copy(update={"not_sliceable_by": [...]}).
        kpi = _kpi()
        updated = kpi.model_copy(update={
            "not_sliceable_by": [
                NotSliceableByEntry(dimension="customer_name", reason_class="pipeline_gap", source="derived"),
            ]
        })
        assert updated.not_sliceable_by[0].dimension == "customer_name"
        # Untouched fields survive.
        assert updated.id == kpi.id
        assert updated.name == kpi.name
