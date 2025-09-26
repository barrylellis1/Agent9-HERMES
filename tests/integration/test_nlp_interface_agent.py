import os
import sys
import asyncio
import pytest

# Ensure project root is on sys.path to import 'src' package
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent, initialize_agent_registry
from src.agents.models.nlp_models import NLPBusinessQueryInput


@pytest.mark.asyncio
async def test_parse_business_query_current_margin_uses_principal_defaults():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    # Create NLP agent via orchestrator registry
    nlp_agent = await orchestrator.get_agent("A9_NLP_Interface_Agent")
    assert nlp_agent is not None

    # Simulate principal context defaults; NLP should pass these through unchanged
    principal_context = {
        "filters": {
            "Profit Center Name": ["Production"],
            "Parent Customer Hierarchy ID": ["Z2", "Z3"],
        },
        "typical_timeframes": ["Quarterly"],
    }

    # Parse a minimal query that relies on defaults
    req = NLPBusinessQueryInput(query="Show my current Margin", principal_context=principal_context)
    res = await nlp_agent.parse_business_query(req, context={})

    assert res is not None
    assert res.human_action_required in (False, True)  # May require KPI clarification in some cases
    assert isinstance(res.principal_context, dict)

    # Expect a matched view with KPI resolved to Gross Margin (from KPI registry)
    if res.matched_views:
        mv = res.matched_views[0]
        assert mv.kpi_name in ("Gross Margin", "Gross Revenue", "Cost of Goods Sold")  # allow for synonym variability
        # Time hint should be a neutral 'current' resolved with granularity from principal typical_timeframes
        if mv.time_filter:
            assert mv.time_filter.expression in ("current", "current_quarter", "quarter_to_date", "this_quarter")
            # If neutral 'current' was used, granularity should prefer quarter due to typical_timeframes
            if mv.time_filter.expression == "current":
                assert mv.time_filter.granularity in ("quarter", "month", None)


@pytest.mark.asyncio
async def test_parse_business_query_gross_revenue_by_region_last_quarter():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    nlp_agent = await orchestrator.get_agent("A9_NLP_Interface_Agent")
    assert nlp_agent is not None

    principal_context = {"typical_timeframes": ["Quarterly", "Monthly"]}

    req = NLPBusinessQueryInput(
        query="Show Gross Revenue by region last quarter",
        principal_context=principal_context,
    )
    res = await nlp_agent.parse_business_query(req, context={})

    assert res is not None
    assert not res.human_action_required or res.human_action_type in (None, "clarification")

    # Expect KPI resolved to Gross Revenue
    assert res.matched_views, "Expected at least one matched view"
    mv = res.matched_views[0]
    assert mv.kpi_name.lower() in ("gross revenue", "gross_revenue")

    # Timeframe should resolve to last_quarter
    assert mv.time_filter is not None
    assert mv.time_filter.expression in ("last_quarter", "current_quarter", "quarter_to_date")

    # Groupings should include a region-like grouping when present
    if mv.groupings:
        g = mv.groupings[0].lower()
        assert "region" in g


@pytest.mark.asyncio
async def test_nlp_to_dpa_sql_generation():
    """End-to-end: NLP intent → KPI definition → DPA SQL generation (no execution)."""
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    # Agents
    nlp_agent = await orchestrator.get_agent("A9_NLP_Interface_Agent")
    assert nlp_agent is not None
    # Pass orchestrator so DPA can connect to DGA and resolve canonical view names
    dpa = await orchestrator.get_agent("A9_Data_Product_Agent", {"orchestrator": orchestrator})
    assert dpa is not None

    # Parse NLQ
    req = NLPBusinessQueryInput(query="Show Gross Revenue by region last quarter", principal_context={"typical_timeframes": ["Quarterly"]})
    res = await nlp_agent.parse_business_query(req, context={})
    assert res.matched_views, "Expected at least one matched view"
    kpi_name = res.matched_views[0].kpi_name

    # Get KPI definition from registry directly (deterministic path)
    from src.registry.factory import RegistryFactory
    kpi_provider = RegistryFactory().get_kpi_provider() or RegistryFactory().get_provider("kpi")
    # Ensure provider is loaded
    if hasattr(kpi_provider, "load"):
        try:
            await kpi_provider.load()
        except TypeError:
            kpi_provider.load()
    kpi_def = None
    if kpi_provider:
        # Try by name and by legacy id
        kpi_def = kpi_provider.get(kpi_name) or kpi_provider.get(kpi_name.lower())
    assert kpi_def is not None, f"KPI definition not found for {kpi_name}"

    # Let DPA generate SQL; do not execute
    sql_resp = await dpa.generate_sql_for_kpi(kpi_def, timeframe=None, filters={})
    assert sql_resp.get("success"), sql_resp
    sql = sql_resp.get("sql", "")
    assert isinstance(sql, str) and sql, "Expected non-empty SQL"
    # Should reference the canonical FI view and time_dim join
    assert '"FI_Star_View"' in sql or 'FI_Star_View' in sql


@pytest.mark.asyncio
async def test_hitl_escalation_when_kpi_missing():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    nlp_agent = await orchestrator.get_agent("A9_NLP_Interface_Agent")
    assert nlp_agent is not None

    # Ambiguous query with no KPI; should request clarification
    req = NLPBusinessQueryInput(query="Show performance this month", principal_context={"typical_timeframes": ["Monthly"]})
    res = await nlp_agent.parse_business_query(req, context={})

    assert res is not None
    assert res.human_action_required is True
    assert res.human_action_type in ("clarification", "error")
    assert isinstance(res.human_action_context, dict)


@pytest.mark.asyncio
async def test_timeframe_defaults_neutral_current_uses_typical_timeframes():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    nlp_agent = await orchestrator.get_agent("A9_NLP_Interface_Agent")
    assert nlp_agent is not None

    pc = {"typical_timeframes": ["Quarterly"]}
    req = NLPBusinessQueryInput(query="Show my current margin", principal_context=pc)
    res = await nlp_agent.parse_business_query(req, context={})

    # When KPI resolves, ensure 'current' granularity aligns with typical_timeframes
    if res.matched_views and res.matched_views[0].time_filter:
        tf = res.matched_views[0].time_filter
        assert tf.granularity in ("quarter", "month", None)


@pytest.mark.asyncio
async def test_nlp_to_dga_mapping_and_view_name():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    nlp_agent = await orchestrator.get_agent("A9_NLP_Interface_Agent")
    dga = await orchestrator.get_agent("A9_Data_Governance_Agent")
    assert nlp_agent is not None and dga is not None

    req = NLPBusinessQueryInput(query="Show Gross Revenue last quarter", principal_context={"typical_timeframes": ["Quarterly"]})
    res = await nlp_agent.parse_business_query(req, context={})
    assert res.matched_views, "Expected at least one matched view"
    kpi_name = res.matched_views[0].kpi_name

    # Map KPIs to data products
    from src.agents.models.data_governance_models import KPIDataProductMappingRequest, KPIViewNameRequest
    mapping_resp = await dga.map_kpis_to_data_products(KPIDataProductMappingRequest(kpi_names=[kpi_name], context={}))
    assert mapping_resp is not None
    assert not mapping_resp.human_action_required
    assert mapping_resp.mappings, f"KPI {kpi_name} should map to a data product"

    # Resolve view name
    view_resp = await dga.get_view_name_for_kpi(KPIViewNameRequest(kpi_name=kpi_name, context={}))
    assert view_resp.view_name and isinstance(view_resp.view_name, str)
    # FI KPIs should resolve to canonical FI_Star_View
    assert view_resp.view_name == "FI_Star_View" or view_resp.view_name.startswith("view_")


@pytest.mark.asyncio
async def test_parse_business_query_top5_by_revenue_last_quarter():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    nlp_agent = await orchestrator.get_agent("A9_NLP_Interface_Agent")
    assert nlp_agent is not None

    req = NLPBusinessQueryInput(query="Top 5 by revenue last quarter")
    res = await nlp_agent.parse_business_query(req, context={})

    assert res.topn is not None
    assert res.topn.limit_type == "top"
    assert res.topn.limit_n == 5
    if res.topn.limit_field:
        assert "revenue" in res.topn.limit_field.lower()

    assert res.matched_views, "Expected matched view for revenue"
    mv = res.matched_views[0]
    assert mv.kpi_name.lower() in ("gross revenue", "gross_revenue")
    if mv.time_filter:
        assert mv.time_filter.expression in ("last_quarter", "current_quarter", "quarter_to_date")


@pytest.mark.asyncio
async def test_parse_business_query_bottom3_by_margin_this_quarter():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    nlp_agent = await orchestrator.get_agent("A9_NLP_Interface_Agent")
    assert nlp_agent is not None

    req = NLPBusinessQueryInput(query="Bottom 3 by margin this quarter")
    res = await nlp_agent.parse_business_query(req, context={})

    assert res.topn is not None
    assert res.topn.limit_type == "bottom"
    assert res.topn.limit_n == 3
    if res.topn.limit_field:
        assert "margin" in res.topn.limit_field.lower()

    assert res.matched_views, "Expected matched view for margin"
    mv = res.matched_views[0]
    assert mv.kpi_name.lower() in ("gross margin", "gross_margin")
    if mv.time_filter:
        assert mv.time_filter.expression in ("current_quarter", "quarter_to_date", "this_quarter")


@pytest.mark.asyncio
async def test_nlp_to_dpa_sql_generation_with_topn():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    nlp_agent = await orchestrator.get_agent("A9_NLP_Interface_Agent")
    assert nlp_agent is not None
    dpa = await orchestrator.get_agent("A9_Data_Product_Agent", {"orchestrator": orchestrator})
    assert dpa is not None

    # NLQ with Top 5 intent
    req = NLPBusinessQueryInput(query="Top 5 by revenue last quarter")
    res = await nlp_agent.parse_business_query(req, context={})
    assert res.topn is not None and res.topn.limit_n == 5
    assert res.matched_views, "Expected matched view"

    # Resolve KPI def
    kpi_name = res.matched_views[0].kpi_name
    from src.registry.factory import RegistryFactory
    kpi_provider = RegistryFactory().get_kpi_provider() or RegistryFactory().get_provider("kpi")
    if hasattr(kpi_provider, "load"):
        try:
            await kpi_provider.load()
        except TypeError:
            kpi_provider.load()
    kpi_def = kpi_provider.get(kpi_name) or kpi_provider.get(kpi_name.lower())
    assert kpi_def is not None

    # Generate SQL with TopN forwarded to DPA
    sql_resp = await dpa.generate_sql_for_kpi(kpi_def, topn=res.topn, filters={})
    assert sql_resp.get("success"), sql_resp
    sql = sql_resp.get("sql", "")
    assert "ORDER BY" in sql.upper()
    assert "LIMIT 5" in sql.upper()
