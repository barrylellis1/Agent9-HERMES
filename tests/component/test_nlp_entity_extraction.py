import os
import sys
import pytest

# Ensure project root is on sys.path to import 'src' package
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent, initialize_agent_registry
from src.agents.models.nlp_models import EntityExtractionInput


@pytest.mark.asyncio
async def test_entity_extraction_month_year_groupby():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    nlp_agent = await orchestrator.get_agent("A9_NLP_Interface_Agent")
    assert nlp_agent is not None

    text = "Show revenue by profit center for March 2024"
    req = EntityExtractionInput(text=text)
    res = await nlp_agent.entity_extraction(req, context={})

    assert res is not None
    assert res.human_action_required is False

    # Month present
    months = [e for e in res.entities if e.type == "month" and e.value.lower() == "march"]
    assert months, f"Expected month entity 'March'; got: {[ (e.type, e.value) for e in res.entities ]}"

    # Year present
    years = [e for e in res.entities if e.type == "year" and e.value == "2024"]
    assert years, f"Expected year entity '2024'"

    # Group-by present (first two tokens after 'by')
    groupbys = [e for e in res.entities if e.type == "groupby" and e.value.lower() == "profit center"]
    assert groupbys, f"Expected groupby 'profit center'"


@pytest.mark.asyncio
async def test_entity_extraction_groupby_region():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    nlp_agent = await orchestrator.get_agent("A9_NLP_Interface_Agent")
    assert nlp_agent is not None

    text = "Top 5 products by Region"
    req = EntityExtractionInput(text=text)
    res = await nlp_agent.entity_extraction(req, context={})

    assert res is not None
    assert res.human_action_required is False

    groupbys = [e for e in res.entities if e.type == "groupby" and e.value.lower() == "region"]
    assert groupbys, f"Expected groupby 'region'"


@pytest.mark.asyncio
async def test_entity_extraction_no_entities():
    orchestrator = await A9_Orchestrator_Agent.create({})
    await initialize_agent_registry()

    nlp_agent = await orchestrator.get_agent("A9_NLP_Interface_Agent")
    assert nlp_agent is not None

    text = "Hello world"
    req = EntityExtractionInput(text=text)
    res = await nlp_agent.entity_extraction(req, context={})

    assert res is not None
    assert res.human_action_required is False
    assert res.entities == [] or len(res.entities) == 0
