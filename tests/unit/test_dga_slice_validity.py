# arch-allow-direct-agent-construction
"""A9_Data_Governance_Agent.check_slice_validity() — docs/architecture/kpi_semantic_contract.md §4.

THINGS UNDER TEST
------------------
1. The DGA<->DPA wiring: non-fatal (returns status="error", never raises)
   when A9_Data_Product_Agent isn't wired, and a live-run regression that
   execute_sql is always called WITH data_product_id — the Tier-1 routing
   engagement.
2. Tenant isolation: a KPI record belonging to a different client must be
   treated as not-found, not silently used.
3. The persist-failure distinction: a write-back failure must report
   status="error" and checked_at=None, never status="success" with a
   timestamp that reverts to stale on the next read.
4. TWO INDEPENDENT CHECKS (added 2026-08-16, after "why are single-component
   KPIs excluded" turned out to be a real gap, not a design choice):
   completeness (does every row have a non-NULL value for this dimension —
   applies to EVERY KPI, one component or many) always runs; cross-component
   coverage (do 2+ components reach the same dimension values) only runs
   when there ARE 2+ components — nothing to compare with fewer. components
   auto-derive from the KPI's own sql_query when not given explicitly,
   required to run this against a plain single-component sum without a
   caller having to know and specify its components by hand.

Backend-quoting coverage: tests/unit/test_slice_validity_dialects.py.
check_completeness()/extract_components() unit coverage:
tests/unit/test_slice_validity_completeness.py,
tests/unit/test_slice_validity_extract_components.py.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.new.a9_data_governance_agent import A9_Data_Governance_Agent
from src.agents.models.data_governance_models import SliceValidityCheckRequest
from src.registry.models.kpi import KPI, KPIDimension

_MARGIN_SQL = (
    "SELECT ROUND(100.0 * SUM(CASE WHEN account_type IN ('Revenue', 'COGS') "
    "THEN amount ELSE 0 END), 2) AS value FROM `agent9-465818.LubricantsBusiness."
    "LubricantsStarSchemaView` WHERE version = 'Actual'"
)
_SINGLE_COMPONENT_SQL = (
    "SELECT SUM(amount) AS value FROM `agent9-465818.LubricantsBusiness."
    "LubricantsStarSchemaView` WHERE account_type = 'Revenue' AND version = 'Actual'"
)


def _kpi(**overrides) -> KPI:
    defaults = dict(
        id="gross_margin_pct",
        client_id="lubricants",
        name="Gross Margin %",
        domain="Finance",
        data_product_id="lubricants_financial_analytics",
        view_name="LubricantsStarSchemaView",
        sql_query=_MARGIN_SQL,
        dimensions=[
            KPIDimension(name="Customer", field="customer_name"),
            KPIDimension(name="Product", field="product_name"),
        ],
    )
    defaults.update(overrides)
    return KPI(**defaults)


def _dga(*, kpi=None, dpa=None, data_product=None) -> A9_Data_Governance_Agent:
    agent = A9_Data_Governance_Agent(config={})
    agent.kpi_provider = MagicMock()
    agent.kpi_provider.get.return_value = kpi
    agent.kpi_provider.upsert = AsyncMock()
    agent.data_product_provider = MagicMock()
    agent.data_product_provider.get.return_value = data_product
    agent.data_product_agent = dpa
    return agent


def _request(**overrides) -> SliceValidityCheckRequest:
    defaults = dict(kpi_id="gross_margin_pct", client_id="lubricants")
    defaults.update(overrides)
    return SliceValidityCheckRequest(**defaults)


def _fake_dpa(counts_by_dimension: dict, *, completeness_by_dimension: dict = None) -> MagicMock:
    """A DPA stand-in answering BOTH check shapes.

    `counts_by_dimension` = {dim: {component: count}} for the cross-component
    GROUP BY query. `completeness_by_dimension` = {dim: (total_rows,
    complete_rows)} for the completeness query — defaults to no fixture for
    any dimension, so (matching profile()'s existing "skip silently on an
    unrecognised query" behaviour) completeness is simply absent from the
    result for a dimension no test declared it for, rather than silently
    injecting an unrequested "ok"/"INVALID" verdict into not_sliceable_by.
    """
    dpa = MagicMock()
    completeness_by_dimension = completeness_by_dimension or {}

    async def _execute_sql(sql, data_product_id=None, **kw):
        if "COUNT(*) AS total_rows" in sql:
            for dim, (total, complete) in completeness_by_dimension.items():
                if f"COUNT({dim}) AS complete_rows" in sql:
                    return {"success": True, "rows": [{"total_rows": total, "complete_rows": complete}]}
            return {"success": False, "message": f"no completeness fixture for query: {sql}"}
        for dim, counts in counts_by_dimension.items():
            if f"COUNT(DISTINCT {dim})" in sql:
                rows = [{"component": c, "n": n} for c, n in counts.items()]
                return {"success": True, "rows": rows}
        return {"success": False, "message": f"no fixture for query: {sql}"}

    dpa.execute_sql = AsyncMock(side_effect=_execute_sql)
    return dpa


# ---------------------------------------------------------------------------
# Non-fatal wiring failures
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_returns_error_not_exception_when_dpa_not_wired():
    agent = _dga(kpi=_kpi(), dpa=None)

    resp = await agent.check_slice_validity(_request())

    assert resp.status == "error"
    assert "not wired" in resp.error_message.lower()


@pytest.mark.asyncio
async def test_cross_tenant_kpi_is_treated_as_not_found():
    """The KPI provider returns a record, but it belongs to a different client.

    CLAUDE.md: STRICT MATCH, never an `is not None` guard that lets an
    unscoped or wrong-tenant record leak through.
    """
    wrong_tenant_kpi = _kpi(client_id="hess")
    agent = _dga(kpi=wrong_tenant_kpi, dpa=_fake_dpa({}))

    resp = await agent.check_slice_validity(_request(client_id="lubricants"))

    assert resp.status == "error"
    assert "not found" in resp.error_message.lower()
    agent.data_product_agent.execute_sql.assert_not_called()


@pytest.mark.asyncio
async def test_client_id_is_passed_to_provider_get_not_a_bare_lookup():
    """Regression for a real bug found live (2026-08-15): two actual clients
    (lubricants, brookshire_brothers) both use the KPI id "gross_margin_pct".
    A bare provider.get(kpi_id) — no client_id — hit
    DatabaseRegistryProvider's documented fallback ("a bare-id linear scan...
    matches the first cached item with the given id regardless of tenant")
    and returned brookshire_brothers' record for a lubricants request. The
    prior test above uses a MagicMock, which accepts any call signature and
    can't catch this — it would pass whether or not client_id was actually
    forwarded. This test simulates the real provider shape: two KPIs sharing
    one id, disambiguated ONLY by which client_id argument reaches .get().
    """
    lubricants_kpi = _kpi(client_id="lubricants", name="Lubricants Margin")
    other_tenant_kpi = _kpi(client_id="brookshire_brothers", name="Brookshire Margin")

    def _tenant_aware_get(kpi_id, client_id=None):
        # Mirrors DatabaseRegistryProvider.get(): with client_id, honour it;
        # without it, fall through to "first match regardless of tenant" —
        # deliberately returning the WRONG one to prove the caller must pass
        # client_id, not rely on getting lucky with cache ordering.
        if client_id == "lubricants":
            return lubricants_kpi
        if client_id == "brookshire_brothers":
            return other_tenant_kpi
        return other_tenant_kpi  # bare-lookup fallback: "first match", wrong one on purpose

    agent = _dga(kpi=None, dpa=_fake_dpa({"customer_name": {"Revenue": 5, "COGS": 5}}))
    agent.kpi_provider.get = MagicMock(side_effect=_tenant_aware_get)

    resp = await agent.check_slice_validity(_request(
        kpi_id="gross_margin_pct", client_id="lubricants", dimensions=["customer_name"],
    ))

    assert resp.status == "success", (
        f"got status={resp.status!r} error={resp.error_message!r} — "
        "client_id was not forwarded to provider.get(), so the tenant-aware "
        "fake resolved the wrong client's KPI (the bare-lookup fallback branch)"
    )


@pytest.mark.asyncio
async def test_falls_back_to_bare_get_when_provider_rejects_client_id_kwarg():
    """The plain in-memory KPIProvider's .get(id_or_name) doesn't accept a
    client_id kwarg at all — must not crash the whole check on that provider
    shape, and the STRICT MATCH re-check must still apply to whatever it
    returns."""
    kpi = _kpi(client_id="lubricants")

    def _no_kwarg_get(kpi_id):
        return kpi

    agent = _dga(kpi=None, dpa=_fake_dpa({"customer_name": {"Revenue": 5, "COGS": 5}}))
    agent.kpi_provider.get = MagicMock(side_effect=_no_kwarg_get)

    resp = await agent.check_slice_validity(_request(dimensions=["customer_name"]))

    assert resp.status == "success"


@pytest.mark.asyncio
async def test_kpi_not_found_at_all_is_non_fatal():
    agent = _dga(kpi=None, dpa=_fake_dpa({}))

    resp = await agent.check_slice_validity(_request())

    assert resp.status == "error"


@pytest.mark.asyncio
async def test_no_dimensions_available_is_reported_not_raised():
    agent = _dga(kpi=_kpi(dimensions=[]), dpa=_fake_dpa({}))

    resp = await agent.check_slice_validity(_request(dimensions=None))

    assert resp.status == "error"
    assert "dimensions" in resp.error_message.lower()


@pytest.mark.asyncio
async def test_no_components_derivable_is_reported_not_raised():
    """New failure mode once components auto-derive: a sql_query that
    doesn't filter by account_type at all, and none given explicitly."""
    agent = _dga(kpi=_kpi(sql_query="SELECT 1"), dpa=_fake_dpa({}))

    resp = await agent.check_slice_validity(_request(dimensions=["customer_name"]))

    assert resp.status == "error"
    assert "components" in resp.error_message.lower()


@pytest.mark.asyncio
async def test_unresolvable_view_is_reported_not_raised():
    # No fully-qualified BQ reference here (unlike _SINGLE_COMPONENT_SQL) —
    # isolates "view genuinely can't be resolved" from the BigQuery-
    # reference-extraction fallback, which would otherwise recover a valid
    # view from sql_query even with view_name=None (see the test above).
    agent = _dga(
        kpi=_kpi(view_name=None, sql_query="SELECT SUM(amount) AS value WHERE account_type = 'Revenue'"),
        dpa=_fake_dpa({}),
    )

    resp = await agent.check_slice_validity(_request())

    assert resp.status == "error"
    assert "view" in resp.error_message.lower()


# ---------------------------------------------------------------------------
# Happy path — verdicts, persistence, and the Tier-1 routing regression
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verdicts_match_assess_and_populate_not_sliceable_by():
    """The Aug-9 shape: COGS reaches one customer, revenue reaches twenty."""
    dpa = _fake_dpa({
        "customer_name": {"Revenue": 20, "COGS": 1},   # INVALID — ratio 0.05
        "product_name": {"Revenue": 5, "COGS": 5},     # ok — full coverage
    })
    agent = _dga(kpi=_kpi(), dpa=dpa)

    resp = await agent.check_slice_validity(_request(
        dimensions=["customer_name", "product_name"],
    ))

    assert resp.status == "success"
    verdicts = {r.dimension: r.verdict for r in resp.cross_component_results}
    assert verdicts["customer_name"] == "INVALID"
    assert verdicts["product_name"] == "ok"
    assert [e.dimension for e in resp.not_sliceable_by] == ["customer_name"]
    assert resp.not_sliceable_by[0].reason_class == "pipeline_gap"
    assert resp.not_sliceable_by[0].source == "derived"
    assert resp.checked_at is not None
    assert resp.components_used == ["Revenue", "COGS"]


@pytest.mark.asyncio
async def test_execute_sql_is_always_called_with_data_product_id():
    """Regression for the Tier-1-routing gap found while designing this check.

    Every call, completeness and cross-component alike, must carry
    data_product_id — Snowflake/DuckDB queries are unquoted by convention
    (src/analysis/slice_validity.py's _quote_view), so execute_sql's Tier-2
    regex fallback (backtick -> BigQuery, bracket -> SQL Server) cannot
    recognise them.
    """
    dpa = _fake_dpa({"customer_name": {"Revenue": 5, "COGS": 5}})
    agent = _dga(kpi=_kpi(data_product_id="lubricants_financial_analytics"), dpa=dpa)

    await agent.check_slice_validity(_request(dimensions=["customer_name"]))

    assert dpa.execute_sql.await_count >= 1
    for call in dpa.execute_sql.call_args_list:
        assert call.kwargs.get("data_product_id") == "lubricants_financial_analytics"


@pytest.mark.asyncio
async def test_result_is_persisted_via_upsert_with_both_check_types():
    dpa = _fake_dpa(
        {"customer_name": {"Revenue": 20, "COGS": 1}},
        completeness_by_dimension={"customer_name": (100, 100)},
    )
    kpi = _kpi()
    agent = _dga(kpi=kpi, dpa=dpa)

    await agent.check_slice_validity(_request(dimensions=["customer_name"]))

    agent.kpi_provider.upsert.assert_awaited_once()
    (persisted,), _ = agent.kpi_provider.upsert.call_args
    assert [e.dimension for e in persisted.not_sliceable_by] == ["customer_name"]
    detail = persisted.slice_validity_details["customer_name"]
    assert detail["cross_component"]["verdict"] == "INVALID"
    assert detail["completeness"]["verdict"] == "ok"
    assert persisted.slice_validity_checked_at is not None
    # The rest of the KPI record must survive model_copy(update=...) untouched.
    assert persisted.id == kpi.id
    assert persisted.name == kpi.name


@pytest.mark.asyncio
async def test_persist_failure_reports_error_not_a_reverting_success():
    """A write-back failure must not read as success — see module docstring."""
    dpa = _fake_dpa({"customer_name": {"Revenue": 20, "COGS": 1}})
    agent = _dga(kpi=_kpi(), dpa=dpa)
    agent.kpi_provider.upsert = AsyncMock(side_effect=RuntimeError("db unavailable"))

    resp = await agent.check_slice_validity(_request(dimensions=["customer_name"]))

    assert resp.status == "error"
    assert resp.checked_at is None
    # But what the check actually found is still surfaced, not discarded.
    assert [e.dimension for e in resp.not_sliceable_by] == ["customer_name"]
    assert len(resp.cross_component_results) == 1


@pytest.mark.asyncio
async def test_persist_failure_is_caught_even_when_upsert_returns_false_silently():
    """Regression for a real bug found live (2026-08-15).
    DatabaseRegistryProvider.upsert()/register() logs a DB failure and
    returns False rather than raising — the prior test's
    AsyncMock(side_effect=RuntimeError(...)) exercises the exception path,
    but the ACTUAL live failure mode was a silent `False` return with no
    exception at all. That combination — success() plumbing reporting
    status="success" while the database write genuinely failed — is exactly
    the false-confidence shape this whole feature exists to prevent, and it
    slipped through in production for the very first live end-to-end run."""
    dpa = _fake_dpa({"customer_name": {"Revenue": 20, "COGS": 1}})
    agent = _dga(kpi=_kpi(), dpa=dpa)
    agent.kpi_provider.upsert = AsyncMock(return_value=False)

    resp = await agent.check_slice_validity(_request(dimensions=["customer_name"]))

    assert resp.status == "error"
    assert resp.checked_at is None
    assert [e.dimension for e in resp.not_sliceable_by] == ["customer_name"]


@pytest.mark.asyncio
async def test_defaults_to_the_kpis_own_declared_dimensions():
    dpa = _fake_dpa({
        "customer_name": {"Revenue": 5, "COGS": 5},
        "product_name": {"Revenue": 5, "COGS": 5},
    })
    kpi = _kpi(dimensions=[
        KPIDimension(name="Customer", field="customer_name"),
        KPIDimension(name="Product", field="product_name"),
    ])
    agent = _dga(kpi=kpi, dpa=dpa)

    resp = await agent.check_slice_validity(_request(dimensions=None))

    assert {r.dimension for r in resp.cross_component_results} == {"customer_name", "product_name"}


@pytest.mark.asyncio
async def test_source_system_resolved_from_data_product_when_available():
    dpa = _fake_dpa({"customer_name": {"Revenue": 5, "COGS": 5}})
    data_product = MagicMock(source_system="snowflake", client_id="lubricants")
    agent = _dga(kpi=_kpi(), dpa=dpa, data_product=data_product)

    await agent.check_slice_validity(_request(dimensions=["customer_name"]))

    for call in dpa.execute_sql.call_args_list:
        sql = call.args[0]
        # Snowflake convention is unquoted — no backticks or brackets in the FROM clause.
        assert "`" not in sql
        assert "[" not in sql


@pytest.mark.asyncio
async def test_data_product_from_a_different_tenant_is_not_trusted_for_source_system():
    """The same STRICT MATCH principle as the KPI lookup, applied to the
    data-product lookup too — a data product record belonging to a different
    client must not leak its source_system into this check."""
    dpa = _fake_dpa({"customer_name": {"Revenue": 5, "COGS": 5}})
    wrong_tenant_dp = MagicMock(source_system="snowflake", client_id="hess")
    agent = _dga(kpi=_kpi(), dpa=dpa, data_product=wrong_tenant_dp)

    await agent.check_slice_validity(_request(dimensions=["customer_name"]))

    # Falls back to the bigquery default rather than trusting hess's source_system.
    assert all("`" in call.args[0] for call in dpa.execute_sql.call_args_list)


# ---------------------------------------------------------------------------
# BigQuery: the fully-qualified reference, not the bare view_name
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bigquery_uses_the_fully_qualified_reference_from_sql_query():
    """Regression for a real bug found live (2026-08-15): KPI.view_name is
    stored bare ("LubricantsStarSchemaView"), not the fully-qualified
    `project.dataset.view` execute_sql's BigQuery routing actually needs.
    Backtick-wrapping the bare name produced a string execute_sql's regex
    doesn't recognise as BigQuery, so it silently fell through to the
    DuckDB manager, which raised "Parser Error: syntax error at or near
    backtick" on every dimension — each one silently skipped by profile()'s
    own per-dimension error handling, so the check "succeeded" with zero
    results and no visible error at all.
    """
    dpa = _fake_dpa({"customer_name": {"Revenue": 5, "COGS": 5}})
    data_product = MagicMock(source_system="bigquery", client_id="lubricants")
    kpi = _kpi(view_name="LubricantsStarSchemaView", sql_query=_MARGIN_SQL)
    agent = _dga(kpi=kpi, dpa=dpa, data_product=data_product)

    await agent.check_slice_validity(_request(dimensions=["customer_name"]))

    assert any(
        "FROM `agent9-465818.LubricantsBusiness.LubricantsStarSchemaView`" in call.args[0]
        for call in dpa.execute_sql.call_args_list
    )
    assert not any("FROM `LubricantsStarSchemaView`" in call.args[0] for call in dpa.execute_sql.call_args_list)


@pytest.mark.asyncio
async def test_bigquery_falls_back_to_bare_view_name_when_sql_query_has_no_reference():
    """Degrades to the old (buggy but not worse) behaviour rather than
    crashing when sql_query doesn't contain the expected fully-qualified
    pattern — still surfaces as a skipped-dimension result, not an
    exception. components explicit here so this test isolates the view-
    reference concern from the (separately tested) components-derivation
    concern — sql_query has no fully-qualified BQ reference AND no
    account_type filter, so components must be given explicitly.
    """
    dpa = _fake_dpa({})  # no fixture matches -> every dimension gets skipped, not raised
    data_product = MagicMock(source_system="bigquery", client_id="lubricants")
    kpi = _kpi(view_name="LubricantsStarSchemaView", sql_query="SELECT 1")
    agent = _dga(kpi=kpi, dpa=dpa, data_product=data_product)

    resp = await agent.check_slice_validity(_request(
        dimensions=["customer_name"], components=["Revenue", "COGS"],
    ))

    assert resp.status == "success"  # ran; just found nothing checkable
    assert resp.cross_component_results == []
    assert resp.completeness_results == []


# ---------------------------------------------------------------------------
# The two-check design itself
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_components_auto_derive_from_the_kpis_own_sql_query():
    """The point of this whole extension: a caller doesn't have to know or
    specify what a KPI is built from — it's already encoded in sql_query."""
    dpa = _fake_dpa({"customer_name": {"Revenue": 20, "COGS": 1}})
    kpi = _kpi(sql_query=_MARGIN_SQL)  # IN ('Revenue', 'COGS')
    agent = _dga(kpi=kpi, dpa=dpa)

    resp = await agent.check_slice_validity(_request(dimensions=["customer_name"]))

    assert resp.status == "success"
    assert resp.components_used == ["Revenue", "COGS"]


@pytest.mark.asyncio
async def test_measure_column_falls_back_to_account_category_end_to_end():
    """Regression for a real bug found live 2026-08-16: four real KPIs
    (product_sales_revenue, service_revenue, base_oil_cost,
    distribution_cost, on BOTH BigQuery and Snowflake) filter on
    account_category, not account_type, and every one of them failed with
    "could not determine components" before this fallback existed. This
    test exercises the fallback all the way through check_slice_validity,
    not just extract_components() in isolation — the DGA method must
    actually USE the auto-detected measure_column ("account_category" here),
    not silently keep querying with the wrong column.
    """
    dpa = _fake_dpa(
        {},  # single component — nothing to cross-compare
        completeness_by_dimension={"customer_name": (100, 100)},
    )
    kpi = _kpi(sql_query=(
        "SELECT SUM(amount) AS value FROM `x` WHERE account_category = 'Product Sales' "
        "AND version = 'Actual'"
    ))
    agent = _dga(kpi=kpi, dpa=dpa)

    resp = await agent.check_slice_validity(_request(dimensions=["customer_name"]))

    assert resp.status == "success"
    assert resp.components_used == ["Product Sales"]
    sql = dpa.execute_sql.call_args.args[0]
    assert "account_category IN ('Product Sales')" in sql


@pytest.mark.asyncio
async def test_explicit_components_override_auto_derivation():
    dpa = _fake_dpa({"customer_name": {"Revenue": 5, "SGA": 5}})
    agent = _dga(kpi=_kpi(sql_query=_MARGIN_SQL), dpa=dpa)  # would auto-derive Revenue/COGS

    resp = await agent.check_slice_validity(_request(
        dimensions=["customer_name"], components=["Revenue", "SGA"],
    ))

    assert resp.status == "success"
    assert resp.components_used == ["Revenue", "SGA"]


@pytest.mark.asyncio
async def test_completeness_runs_for_a_single_component_kpi_where_cross_component_cannot():
    """The actual gap this extension closes: a plain SUM(amount) KPI
    (net_revenue-shaped — 26 of 42 KPIs across the seeded clients) has
    exactly one component, so cross-component coverage has nothing to
    compare — but completeness is still fully meaningful."""
    dpa = _fake_dpa(
        {},  # no cross-component fixture — there's only one component, nothing to compare
        completeness_by_dimension={"customer_name": (100, 80)},  # 20% of rows have no customer_name
    )
    kpi = _kpi(sql_query=_SINGLE_COMPONENT_SQL)  # account_type = 'Revenue' only
    agent = _dga(kpi=kpi, dpa=dpa)

    resp = await agent.check_slice_validity(_request(dimensions=["customer_name"]))

    assert resp.status == "success"
    assert resp.components_used == ["Revenue"]
    assert resp.cross_component_results == []  # nothing to compare with 1 component
    assert len(resp.completeness_results) == 1
    assert resp.completeness_results[0].verdict == "degraded"  # 0.8 >= INVALID_BELOW (0.25) but < 1.0
    assert resp.not_sliceable_by == []  # degraded isn't INVALID — doesn't land in not_sliceable_by


@pytest.mark.asyncio
async def test_not_sliceable_by_is_the_union_of_both_checks():
    """A dimension can fail EITHER check and still land in not_sliceable_by
    — "don't trust a slice of this KPI by X" shouldn't depend on which of
    the two questions happened to be the one that caught it."""
    dpa = _fake_dpa(
        {
            "customer_name": {"Revenue": 5, "COGS": 5},   # cross-component: ok
            "product_name": {"Revenue": 5, "COGS": 5},    # cross-component: ok
        },
        completeness_by_dimension={
            "customer_name": (100, 100),   # completeness: ok
            "product_name": (100, 5),      # completeness: INVALID (5% coverage)
        },
    )
    agent = _dga(kpi=_kpi(), dpa=dpa)

    resp = await agent.check_slice_validity(_request(dimensions=["customer_name", "product_name"]))

    # product_name is fine by cross-component but fails completeness — still unsafe overall.
    assert [e.dimension for e in resp.not_sliceable_by] == ["product_name"]
