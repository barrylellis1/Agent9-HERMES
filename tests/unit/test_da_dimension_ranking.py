# arch-allow-direct-agent-construction
"""
Dimension ranking in Deep Analysis — declared order, not a hardcoded literal.

Regression guard for Stage I Part A (Aug 2026). `_dims_from_contract` used to
re-rank a contract's declared `dimension_semantics` against a static literal:

    preferred = ["profit_center_name", "customer_name", "product_name",
                 "product_line", "channel_name", "customer_segment", ...]

It was a hand-copy of two clients' field names, merged and frozen, applied to
every KPI, client and problem type — so each tenant was investigated in an order
nobody had chosen for them. For lubricants it forced profit-centre first against
a contract that declares products first, and with the cap at 5-of-16 that
ordering decided the entire investigation.

The parallel literal on the hierarchical drill path (`vector_order`) is covered
here too. It was inert only because no live contract happens to name a vector
"customer"/"product"/"profit_center" — a trap for the first one that does.

Registry-only as of Phase 16 step 5 (DEVELOPMENT_PLAN.md, 2026-08-30):
`_dims_from_contract` no longer has a YAML-contract fallback (deleted along with
the 8 legacy contract files once every real data product's
DataProduct.dimension_semantics was confirmed populated). Fixtures below feed
`_dims_from_registry` directly via mock rather than writing a YAML file to
tmp_path and patching a now-deleted `_contract_path_for_kpi` — the ban-filter/
dedup/ordering logic under test lives entirely in `_dims_from_contract` itself
and is unaffected by where `all_dims` came from.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent


# Mirrors the dimension_semantics list previously declared in
# src/registry_references/.../lubricants_star_schema.yaml (deleted, Phase 16
# step 5) — grouped Product -> Customer -> Organization -> Channel -> Account -> Time.
_LUBRICANTS_DIMS = [
    "product_name", "product_line", "product_category",
    "customer_name", "customer_segment", "customer_region",
    "profit_center_name", "business_unit",
    "channel_name", "channel_type",
    "account_name", "account_type", "account_category", "account_group",
    "fiscal_year", "fiscal_period", "transaction_date",
]

_BANNED_DIMS = [
    "product_line", "transaction_date", "customer_id", "is_active_flag",
    "account_hierarchy", "version", "Fiscal YTD", "customer_segment",
]

_DUPES_DIMS = ["product_line", "customer_segment", "product_line", "channel_name"]


def _agent(**config):
    return A9_Deep_Analysis_Agent(config or {})


def _with_registry_dims(agent, dims):
    """Feed _dims_from_contract via _dims_from_registry, its only source now."""
    return patch.object(agent, "_dims_from_registry", return_value=list(dims))


# ---------------------------------------------------------------------------
# Declared order is honoured
# ---------------------------------------------------------------------------


def test_contract_declared_order_is_preserved_verbatim():
    """The regression that pins the literal's deletion.

    Under the old `preferred` literal this returned profit_center_name first.
    The lubricants data product declares products first, and that is what
    must win.
    """
    agent = _agent()
    with _with_registry_dims(agent, _LUBRICANTS_DIMS):
        dims = agent._dims_from_contract(limit=15, kpi_name="gross_margin_pct", client_id="lubricants")

    assert dims[0] == "product_name", (
        "registry declares product dimensions first; a hardcoded preference list "
        "must not reorder it"
    )
    assert dims[:6] == [
        "product_name",
        "product_line",
        "product_category",
        "customer_name",
        "customer_segment",
        "customer_region",
    ]
    # The specific inversion the literal used to cause.
    assert dims.index("product_name") < dims.index("profit_center_name")


def test_top_ten_covers_product_customer_org_and_channel():
    """With max_dimensions=10 the analyzed set spans every business grouping.

    Documents what the cap actually buys on the live lubricants data product.
    """
    agent = _agent()
    with _with_registry_dims(agent, _LUBRICANTS_DIMS):
        dims = agent._dims_from_contract(limit=15, kpi_name="gross_margin_pct", client_id="lubricants")

    top10 = dims[:10]
    assert "product_name" in top10
    assert "customer_name" in top10
    assert "profit_center_name" in top10
    assert "channel_name" in top10


def test_limit_truncates_from_the_front():
    agent = _agent()
    with _with_registry_dims(agent, _LUBRICANTS_DIMS):
        five = agent._dims_from_contract(limit=5, kpi_name="k", client_id="lubricants")
        fifteen = agent._dims_from_contract(limit=15, kpi_name="k", client_id="lubricants")

    assert len(five) == 5
    assert five == fifteen[:5], "truncation must be a prefix, not a reshuffle"


# ---------------------------------------------------------------------------
# Filtering and hygiene are unchanged
# ---------------------------------------------------------------------------


def test_ban_filter_still_removes_non_dimensional_columns():
    agent = _agent()
    with _with_registry_dims(agent, _BANNED_DIMS):
        dims = agent._dims_from_contract(limit=15, kpi_name="k", client_id="c")

    assert dims == ["product_line", "customer_segment"]
    for banned in ("transaction_date", "customer_id", "is_active_flag",
                   "account_hierarchy", "version", "Fiscal YTD"):
        assert banned not in dims


def test_declared_duplicates_are_collapsed():
    agent = _agent()
    with _with_registry_dims(agent, _DUPES_DIMS):
        dims = agent._dims_from_contract(limit=15, kpi_name="k", client_id="c")

    assert dims == ["product_line", "customer_segment", "channel_name"]


# ---------------------------------------------------------------------------
# Phase 16 step 5 (DEVELOPMENT_PLAN.md) — registry-only, no YAML fallback
# ---------------------------------------------------------------------------


def test_registry_dims_pass_through_the_ban_filter():
    agent = _agent()
    with patch.object(agent, "_dims_from_registry",
                       return_value=["product_line", "transaction_date", "customer_id"]):
        dims = agent._dims_from_contract(limit=15, kpi_name="k", client_id="lubricants")

    assert dims == ["product_line"]


def test_empty_registry_yields_empty_no_yaml_fallback():
    """A data product with nothing declared in the registry yields [] — there
    is no legacy YAML contract left to fall back to (Phase 16 step 5 deleted
    it). This is the correct failure mode: a genuine gap surfaces as an empty
    dimension list, not a silently-guessed default from another tenant's
    contract."""
    agent = _agent()
    with patch.object(agent, "_dims_from_registry", return_value=[]):
        dims = agent._dims_from_contract(limit=15, kpi_name="gross_margin_pct", client_id="hess")

    assert dims == []


def test_dims_from_registry_returns_empty_when_kpi_unresolvable():
    agent = _agent()
    with patch.object(agent, "_lookup_kpi_scoped", return_value=None):
        assert agent._dims_from_registry(kpi_name="nonexistent", client_id="hess") == []


def test_dims_from_registry_returns_empty_when_data_product_provider_missing():
    agent = _agent()
    fake_kpi = SimpleNamespace(data_product_id="dp_x")
    with patch.object(agent, "_lookup_kpi_scoped", return_value=fake_kpi), \
         patch("src.registry.factory.RegistryFactory") as MockFactory:
        MockFactory.return_value.get_provider.return_value = None
        assert agent._dims_from_registry(kpi_name="k", client_id="c") == []


def test_dims_from_registry_never_raises_on_provider_exception():
    agent = _agent()
    fake_kpi = SimpleNamespace(data_product_id="dp_x")
    with patch.object(agent, "_lookup_kpi_scoped", return_value=fake_kpi), \
         patch("src.registry.factory.RegistryFactory") as MockFactory:
        MockFactory.return_value.get_provider.return_value.get.side_effect = RuntimeError("boom")
        assert agent._dims_from_registry(kpi_name="k", client_id="c") == []


# ---------------------------------------------------------------------------
# The hierarchical-path literal
# ---------------------------------------------------------------------------


def test_vector_order_follows_declared_hierarchy_order():
    """Fails before Stage I Part A.

    The old literal was `[k for k in ["customer","product","profit_center"]
    if k in hmap] or list(hmap.keys())`, so a contract naming its vectors
    customer/product/profit_center had its declared order silently rewritten.
    Only contracts that avoided those names escaped — which is why the defect
    stayed invisible.
    """
    import inspect

    src = inspect.getsource(A9_Deep_Analysis_Agent)
    # Assert on the assignment itself, not on prose — the explanatory comment
    # left at the site necessarily quotes the literal it replaced.
    assert "vector_order = list(hmap.keys())" in src
    assert "vector_order = [k for k" not in src

    # And the declared order is what a hierarchy map yields.
    hmap = {"product": ["product_line"], "customer": ["customer_name"], "profit_center": ["pc_name"]}
    assert list(hmap.keys()) == ["product", "customer", "profit_center"]


# ---------------------------------------------------------------------------
# Audit fields
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_plan_records_rank_source_and_considered_set():
    agent = _agent()
    from src.agents.models.deep_analysis_models import DeepAnalysisRequest

    req = DeepAnalysisRequest(
        request_id="r1",
        principal_id="cfo_001",
        kpi_name="gross_margin_pct",
        client_id="lubricants",
        timeframe="year_to_date",
    )
    with _with_registry_dims(agent, _LUBRICANTS_DIMS):
        resp = await agent.plan_deep_analysis(req)

    plan = resp.plan
    assert plan.dimension_rank_source == "contract_semantics"
    assert plan.dimensions_considered == plan.dimensions
    assert plan.dimensions_considered[0] == "product_name"


@pytest.mark.asyncio
async def test_rank_source_is_none_when_no_source_yields_dimensions():
    """'none' must be representable and distinct from a populated source.

    A run that investigated nothing should say so, not report a stale default.
    """
    from unittest.mock import AsyncMock

    agent = _agent()
    # DGA present but mapping-less: exercises the real "every source came back
    # empty" path rather than the missing-dependency RuntimeError.
    dga = MagicMock()
    dga.map_kpis_to_data_products = AsyncMock(return_value=SimpleNamespace(mappings=[]))
    agent.data_governance_agent = dga

    from src.agents.models.deep_analysis_models import DeepAnalysisRequest

    req = DeepAnalysisRequest(
        request_id="r2",
        principal_id="cfo_001",
        kpi_name="unmapped_kpi",
        client_id="lubricants",
        timeframe="year_to_date",
    )
    with patch.object(agent, "_dims_from_contract", return_value=[]), \
            patch.object(agent, "_lookup_kpi_scoped", return_value=None):
        resp = await agent.plan_deep_analysis(req)

    assert resp.plan.dimension_rank_source == "none"
    assert resp.plan.dimensions_considered == []


def test_response_carries_dimensions_analyzed_field():
    """dimensions_suggested and dimensions_analyzed are different questions.

    Before this field, a run reported N suggested, analyzed max_dimensions of
    them, and recorded nowhere which ones.
    """
    from src.agents.models.deep_analysis_models import DeepAnalysisResponse

    resp = DeepAnalysisResponse.success(
        request_id="r3",
        dimensions_suggested=["a", "b", "c", "d"],
        dimensions_analyzed=["a", "b"],
    )
    assert resp.dimensions_analyzed == ["a", "b"]
    assert resp.dimensions_suggested != resp.dimensions_analyzed


def test_max_dimensions_default_is_ten():
    """Search width, not report width — change_points is still cut to 5."""
    from src.agents.agent_config_models import A9_Deep_Analysis_Agent_Config

    assert A9_Deep_Analysis_Agent_Config().max_dimensions == 10
