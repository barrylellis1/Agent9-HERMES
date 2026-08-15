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
"""

import textwrap
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent


# Mirrors src/registry_references/.../lubricants_star_schema.yaml, whose
# dimension_semantics block is grouped and commented Product -> Customer ->
# Organization -> Channel -> Account -> Time.
_LUBRICANTS_CONTRACT = textwrap.dedent(
    """
    metadata:
      id: dp_lubricants_financials
    views:
      - name: LubricantsStarSchemaView
        llm_profile:
          dimension_semantics:
            - "product_name"
            - "product_line"
            - "product_category"
            - "customer_name"
            - "customer_segment"
            - "customer_region"
            - "profit_center_name"
            - "business_unit"
            - "channel_name"
            - "channel_type"
            - "account_name"
            - "account_type"
            - "account_category"
            - "account_group"
            - "fiscal_year"
            - "fiscal_period"
            - "transaction_date"
    """
)

_BANNED_CONTRACT = textwrap.dedent(
    """
    metadata:
      id: dp_banned
    views:
      - name: V
        llm_profile:
          dimension_semantics:
            - "product_line"
            - "transaction_date"
            - "customer_id"
            - "is_active_flag"
            - "account_hierarchy"
            - "version"
            - "Fiscal YTD"
            - "customer_segment"
    """
)

_DUPES_CONTRACT = textwrap.dedent(
    """
    metadata:
      id: dp_dupes
    views:
      - name: V
        llm_profile:
          dimension_semantics:
            - "product_line"
            - "customer_segment"
            - "product_line"
            - "channel_name"
    """
)


def _agent(**config):
    return A9_Deep_Analysis_Agent(config or {})


def _with_contract(agent, yaml_text, tmp_path, name="contract.yaml"):
    """Point _dims_from_contract at a contract fixture on disk."""
    p = tmp_path / name
    p.write_text(yaml_text, encoding="utf-8")
    return patch.object(agent, "_contract_path_for_kpi", return_value=str(p))


# ---------------------------------------------------------------------------
# Declared order is honoured
# ---------------------------------------------------------------------------


def test_contract_declared_order_is_preserved_verbatim(tmp_path):
    """The regression that pins the literal's deletion.

    Under the old `preferred` literal this returned profit_center_name first.
    The lubricants contract declares products first, and that is what must win.
    """
    agent = _agent()
    with _with_contract(agent, _LUBRICANTS_CONTRACT, tmp_path):
        dims = agent._dims_from_contract(limit=15, kpi_name="gross_margin_pct", client_id="lubricants")

    assert dims[0] == "product_name", (
        "contract declares product dimensions first; a hardcoded preference list "
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


def test_top_ten_covers_product_customer_org_and_channel(tmp_path):
    """With max_dimensions=10 the analyzed set spans every business grouping.

    Documents what the cap actually buys on the live lubricants contract.
    """
    agent = _agent()
    with _with_contract(agent, _LUBRICANTS_CONTRACT, tmp_path):
        dims = agent._dims_from_contract(limit=15, kpi_name="gross_margin_pct", client_id="lubricants")

    top10 = dims[:10]
    assert "product_name" in top10
    assert "customer_name" in top10
    assert "profit_center_name" in top10
    assert "channel_name" in top10


def test_limit_truncates_from_the_front(tmp_path):
    agent = _agent()
    with _with_contract(agent, _LUBRICANTS_CONTRACT, tmp_path):
        five = agent._dims_from_contract(limit=5, kpi_name="k", client_id="lubricants")
        fifteen = agent._dims_from_contract(limit=15, kpi_name="k", client_id="lubricants")

    assert len(five) == 5
    assert five == fifteen[:5], "truncation must be a prefix, not a reshuffle"


# ---------------------------------------------------------------------------
# Filtering and hygiene are unchanged
# ---------------------------------------------------------------------------


def test_ban_filter_still_removes_non_dimensional_columns(tmp_path):
    agent = _agent()
    with _with_contract(agent, _BANNED_CONTRACT, tmp_path):
        dims = agent._dims_from_contract(limit=15, kpi_name="k", client_id="c")

    assert dims == ["product_line", "customer_segment"]
    for banned in ("transaction_date", "customer_id", "is_active_flag",
                   "account_hierarchy", "version", "Fiscal YTD"):
        assert banned not in dims


def test_declared_duplicates_are_collapsed(tmp_path):
    agent = _agent()
    with _with_contract(agent, _DUPES_CONTRACT, tmp_path):
        dims = agent._dims_from_contract(limit=15, kpi_name="k", client_id="c")

    assert dims == ["product_line", "customer_segment", "channel_name"]


def test_missing_contract_returns_empty_not_a_default(tmp_path):
    """A scoped miss must not fall back to another tenant's dimension names."""
    agent = _agent()
    with patch.object(agent, "_contract_path_for_kpi", return_value=""):
        assert agent._dims_from_contract(limit=15, kpi_name="k", client_id="c") == []


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
async def test_plan_records_rank_source_and_considered_set(tmp_path):
    agent = _agent()
    from src.agents.models.deep_analysis_models import DeepAnalysisRequest

    req = DeepAnalysisRequest(
        request_id="r1",
        principal_id="cfo_001",
        kpi_name="gross_margin_pct",
        client_id="lubricants",
        timeframe="year_to_date",
    )
    with _with_contract(agent, _LUBRICANTS_CONTRACT, tmp_path):
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
