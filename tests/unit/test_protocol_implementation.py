# arch-allow-direct-agent-construction
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.protocols.situation_awareness_protocol import SituationAwarenessProtocol
from src.agents.models.situation_awareness_models import (
    SituationDetectionRequest,
    PrincipalContext,
    BusinessProcess
)

@pytest.mark.asyncio
async def test_situation_awareness_agent_implements_protocol():
    """Test that the Situation Awareness Agent properly implements the SituationAwarenessProtocol."""
    # Create an instance of the agent
    agent = A9_Situation_Awareness_Agent({})
    
    # Check if it's an instance of the protocol
    assert isinstance(agent, SituationAwarenessProtocol), "Agent should implement SituationAwarenessProtocol"
    
    # Check that all required protocol methods are implemented
    assert hasattr(agent, "detect_situations"), "Agent should implement detect_situations"
    assert hasattr(agent, "process_nl_query"), "Agent should implement process_nl_query"
    assert hasattr(agent, "process_hitl_feedback"), "Agent should implement process_hitl_feedback"
    assert hasattr(agent, "get_recommended_questions"), "Agent should implement get_recommended_questions"
    assert hasattr(agent, "get_kpi_definitions"), "Agent should implement get_kpi_definitions"
    
    # Note: detect_situation, summarize_situation, aggregate_agent_outputs are not defined
    # in the agent card or PRD and have been removed from the compliance check.

@pytest.mark.asyncio
async def test_protocol_method_signatures():
    """Test that the method signatures match the protocol requirements."""
    agent = A9_Situation_Awareness_Agent({})
    
    # Check method signatures by inspecting their annotations
    detect_situations = agent.detect_situations.__annotations__
    assert 'request' in detect_situations, "detect_situations should accept a request parameter"
    assert detect_situations['return'].__name__ == 'SituationDetectionResponse', "detect_situations should return SituationDetectionResponse"
    
    process_nl_query = agent.process_nl_query.__annotations__
    assert 'request' in process_nl_query, "process_nl_query should accept a request parameter"
    assert process_nl_query['return'].__name__ == 'NLQueryResponse', "process_nl_query should return NLQueryResponse"
    
    process_hitl_feedback = agent.process_hitl_feedback.__annotations__
    assert 'request' in process_hitl_feedback, "process_hitl_feedback should accept a request parameter"
    assert process_hitl_feedback['return'].__name__ == 'HITLResponse', "process_hitl_feedback should return HITLResponse"
    
    get_recommended_questions = agent.get_recommended_questions.__annotations__
    assert 'principal_context' in get_recommended_questions, "get_recommended_questions should accept a principal_context parameter"
    assert get_recommended_questions['return'].__name__ == 'List', "get_recommended_questions should return List[str]"
    
    get_kpi_definitions = agent.get_kpi_definitions.__annotations__
    assert 'principal_context' in get_kpi_definitions, "get_kpi_definitions should accept a principal_context parameter"
    assert get_kpi_definitions['return'].__name__ == 'Dict', "get_kpi_definitions should return Dict[str, Any]"
