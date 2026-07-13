# arch-allow-direct-agent-construction
"""
Tenant-scoped KPI resolution in Deep Analysis (`_lookup_kpi_scoped`).

Regression guard for the 2026-07-13 cross-tenant collision: three clients share
KPI id `gross_margin_pct` under the composite PK (client_id, id). DA's previous
unscoped `provider.get(id)` fallback resolved another tenant's record — wrong
data_product_id → wrong backend (Snowflake instead of BigQuery) → every
dimension query failed → empty Is/Is-Not.

These tests assert the STRICT behavior: when client_id is known, a same-id KPI
from another tenant is never returned — a scoped miss returns None.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent


def _kpi(kpi_id, client_id, name="Gross Margin %", data_product_id=None):
    return SimpleNamespace(
        id=kpi_id,
        client_id=client_id,
        name=name,
        data_product_id=data_product_id or f"dp_{client_id}",
    )


_REGISTRY = [
    _kpi("gross_margin_pct", "lubricants", data_product_id="dp_lubricants_financials"),
    _kpi("gross_margin_pct", "apex_lubricants", data_product_id="dp_lubricants_snowflake"),
    _kpi("gross_margin_pct", "hess", data_product_id="dp_hess_financials"),
    _kpi("net_revenue", "lubricants", name="Net Revenue"),
]


def _agent():
    return A9_Deep_Analysis_Agent({})


def _patched_provider():
    provider = MagicMock()
    provider.get_all.return_value = _REGISTRY
    factory = MagicMock()
    factory.get_provider.return_value = provider
    return patch(
        "src.registry.factory.RegistryFactory", return_value=factory
    )


def test_scoped_lookup_returns_requested_tenant_record():
    agent = _agent()
    with _patched_provider():
        k = agent._lookup_kpi_scoped("gross_margin_pct", "lubricants")
    assert k is not None
    assert k.client_id == "lubricants"
    assert k.data_product_id == "dp_lubricants_financials"


def test_scoped_lookup_matches_display_name_too():
    agent = _agent()
    with _patched_provider():
        k = agent._lookup_kpi_scoped("Gross Margin %", "hess")
    assert k is not None
    assert k.client_id == "hess"
    assert k.data_product_id == "dp_hess_financials"


def test_scoped_miss_never_falls_back_to_another_tenant():
    # bicycle has no gross_margin_pct — three other tenants do. Strict isolation:
    # the lookup must return None, not any same-id record from another client.
    agent = _agent()
    with _patched_provider():
        k = agent._lookup_kpi_scoped("gross_margin_pct", "bicycle")
    assert k is None


def test_unscoped_lookup_still_resolves_for_legacy_single_tenant_path():
    agent = _agent()
    with _patched_provider():
        k = agent._lookup_kpi_scoped("net_revenue", None)
    assert k is not None
    assert k.id == "net_revenue"


def test_contract_path_returns_empty_for_scoped_miss_not_fi_default():
    # A known-tenant KPI miss must NOT leak the bicycle FI contract (and its
    # dimension names) into another client's plan.
    agent = _agent()
    with _patched_provider():
        path = agent._contract_path_for_kpi("gross_margin_pct", client_id="bicycle")
    assert path == ""
