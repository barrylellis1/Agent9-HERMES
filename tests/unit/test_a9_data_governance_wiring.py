# arch-allow-direct-agent-construction
"""
Validates that Data Governance Agent wiring is mandatory across SA, DPA, and DA.

Three contracts under test:
1. SA process_nl_query — raises RuntimeError (not AttributeError) when DGA not wired
2. SA process_nl_query — calls DGA when wired
3. DPA _get_view_name_from_kpi — raises RuntimeError when DGA not wired
4. DPA _get_view_name_from_kpi — resolves view name through DGA when wired
5. DA plan_deep_analysis — raises RuntimeError when DGA not wired and contract yields no dimensions
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent
from src.agents.models.situation_awareness_models import NLQueryRequest, PrincipalContext
from src.agents.models.deep_analysis_models import DeepAnalysisRequest
from src.agents.models.data_governance_models import (
    BusinessTermTranslationResponse,
    KPIDataProductMappingResponse,
    KPIViewNameResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sa_agent(*, dga=None) -> A9_Situation_Awareness_Agent:
    agent = A9_Situation_Awareness_Agent(config={})
    agent.data_governance_agent = dga
    agent.kpi_registry = {}
    agent.data_product_agent = None
    return agent


def _dpa_agent(*, dga=None) -> A9_Data_Product_Agent:
    agent = A9_Data_Product_Agent(config={})
    agent.data_governance_agent = dga
    return agent


def _da_agent(*, dga=None) -> A9_Deep_Analysis_Agent:
    agent = A9_Deep_Analysis_Agent(config={})
    agent.data_governance_agent = dga
    agent.data_product_agent = None
    agent.llm_service_agent = None
    return agent


def _nl_request() -> NLQueryRequest:
    return NLQueryRequest(
        request_id="test-dga-001",
        query="What is gross margin this quarter?",
        principal_context=PrincipalContext(
            role="CFO",
            principal_id="cfo_001",
            client_id="lubricants",
            business_processes=["Finance"],
            default_filters={},
            decision_style="analytical",
            communication_style="direct",
            preferred_timeframes=[],
        ),
    )


def _da_request() -> DeepAnalysisRequest:
    return DeepAnalysisRequest(
        request_id="test-dga-da-001",
        principal_id="cfo_001",
        kpi_name="gross_margin",
    )


# ---------------------------------------------------------------------------
# 1. SA — DGA not wired → RuntimeError
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sa_nl_query_raises_runtime_error_when_dga_not_wired():
    """process_nl_query must raise RuntimeError, not AttributeError, when DGA is None."""
    agent = _sa_agent(dga=None)
    with pytest.raises(RuntimeError, match="Data Governance Agent not initialized"):
        await agent.process_nl_query(_nl_request())


# ---------------------------------------------------------------------------
# 2. SA — DGA wired → translate_business_terms is called
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sa_nl_query_calls_dga_translate_when_wired():
    """When DGA is wired, process_nl_query must call translate_business_terms."""
    mock_dga = AsyncMock()
    mock_dga.translate_business_terms = AsyncMock(
        return_value=BusinessTermTranslationResponse(
            resolved_terms={},
            unmapped_terms=[],
            human_action_required=False,
        )
    )
    mock_dga.map_kpis_to_data_products = AsyncMock(
        return_value=KPIDataProductMappingResponse(
            mappings=[],
            unmapped_kpis=[],
            human_action_required=False,
        )
    )

    agent = _sa_agent(dga=mock_dga)

    # Allow the call to proceed past DGA; downstream failures are acceptable here
    try:
        await agent.process_nl_query(_nl_request())
    except RuntimeError as exc:
        if "Data Governance Agent not initialized" in str(exc):
            pytest.fail(f"DGA guard fired unexpectedly: {exc}")
    except Exception:
        pass  # Downstream failures (data product, LLM) are out of scope for this test

    mock_dga.translate_business_terms.assert_called_once()


# ---------------------------------------------------------------------------
# 3. DPA — DGA not wired → RuntimeError
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dpa_get_view_name_raises_runtime_error_when_dga_not_wired():
    """_get_view_name_from_kpi must raise RuntimeError, not AttributeError, when DGA is None."""
    agent = _dpa_agent(dga=None)
    mock_kpi = MagicMock()
    mock_kpi.name = "gross_margin"
    with pytest.raises(RuntimeError, match="Data Governance Agent not initialized"):
        await agent._get_view_name_from_kpi(mock_kpi)


# ---------------------------------------------------------------------------
# 4. DPA — DGA wired → get_view_name_for_kpi called, result returned
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dpa_get_view_name_uses_dga_when_wired():
    """When DGA is wired, _get_view_name_from_kpi must use DGA's view name."""
    mock_dga = AsyncMock()
    mock_dga.get_view_name_for_kpi = AsyncMock(
        return_value=KPIViewNameResponse(
            kpi_name="gross_margin",
            view_name="lubricants_star_schema",
        )
    )

    agent = _dpa_agent(dga=mock_dga)
    mock_kpi = MagicMock()
    mock_kpi.name = "gross_margin"

    result = await agent._get_view_name_from_kpi(mock_kpi)

    mock_dga.get_view_name_for_kpi.assert_called_once()
    assert result == "lubricants_star_schema"


# ---------------------------------------------------------------------------
# 5. DA — DGA not wired and contract yields no dimensions → error response
#
# plan_deep_analysis wraps its body in try/except Exception, so RuntimeError is
# caught internally and returned as DeepAnalysisResponse(status="error"). The
# contract is: the error message must name the missing DGA, not produce an
# opaque AttributeError.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_da_plan_deep_analysis_surfaces_dga_error_when_not_wired():
    """When DGA is None and contract yields no dimensions, plan_deep_analysis must
    return an error response whose message identifies the missing DGA — not an
    opaque AttributeError."""
    agent = _da_agent(dga=None)
    # Force the DGA fallback branch: contract yields no dimensions
    agent._dims_from_contract = MagicMock(return_value=[])

    response = await agent.plan_deep_analysis(_da_request())

    assert response.status == "error"
    assert "Data Governance Agent not initialized" in (response.error_message or "")
