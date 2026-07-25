"""
Regression tests: DatabaseRegistryProvider.get() must not leak cross-tenant
records when two clients share the same generic record id.

Found live: a DELETE for brookshire_brothers's "cost_of_goods_sold" KPI
resolved to bicycle's KPI of the same name instead, because the provider's
bare-id fallback scan (for legacy/shared records) matched the first cached
item by id alone, with no client_id filtering at all. Every registry.py
call site that fetches-then-checks-ownership (single-item GET, PUT, PATCH,
DELETE, and the create-duplicate-check) had this same exposure.
"""

from unittest.mock import MagicMock

import pytest

from src.registry.models.kpi import KPI
from src.registry.providers.database_provider import DatabaseRegistryProvider


@pytest.fixture
def provider():
    p = DatabaseRegistryProvider(
        db_manager=MagicMock(), table_name="kpis", model_class=KPI, key_fields=["client_id", "id"]
    )
    # Two different clients, same generic KPI id — the exact collision found live.
    bicycle_kpi = KPI(id="cost_of_goods_sold", client_id="bicycle", name="COGS", domain="Finance", data_product_id="fi_star_schema")
    brookshire_kpi = KPI(id="cost_of_goods_sold", client_id="brookshire_brothers", name="COGS", domain="Finance", data_product_id="BR_FI_1")
    p._cache_item(bicycle_kpi)
    p._cache_item(brookshire_kpi)
    return p


def test_get_with_client_id_returns_the_correct_tenants_record(provider):
    result = provider.get("cost_of_goods_sold", client_id="brookshire_brothers")
    assert result is not None
    assert result.client_id == "brookshire_brothers"
    assert result.data_product_id == "BR_FI_1"


def test_get_with_different_client_id_returns_the_other_tenants_record(provider):
    result = provider.get("cost_of_goods_sold", client_id="bicycle")
    assert result is not None
    assert result.client_id == "bicycle"


def test_get_with_client_id_for_nonexistent_tenant_returns_none_not_wrong_tenant(provider):
    """The critical regression case: a client_id that has no matching record
    must return None — never silently fall through to a different tenant's
    record with the same id."""
    result = provider.get("cost_of_goods_sold", client_id="apex_lubricants")
    assert result is None


def test_get_without_client_id_preserves_legacy_bare_id_scan_behavior(provider):
    """Omitting client_id is the documented escape hatch for genuinely
    cross-client/shared lookups — must still work for backward compatibility,
    picking up whichever match the linear scan finds first."""
    result = provider.get("cost_of_goods_sold")
    assert result is not None
    assert result.id == "cost_of_goods_sold"
