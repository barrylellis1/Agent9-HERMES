"""
Simple test script to verify protocol implementation.
"""
import asyncio
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.protocols.situation_awareness_protocol import SituationAwarenessProtocol

async def main():
    # Create an instance of the agent
    agent = A9_Situation_Awareness_Agent({})
    
    # Check if it's an instance of the protocol
    is_protocol = isinstance(agent, SituationAwarenessProtocol)
    print(f"Is agent an instance of SituationAwarenessProtocol? {is_protocol}")
    
    # Check that all required protocol methods are implemented
    print(f"Has detect_situations? {hasattr(agent, 'detect_situations')}")
    print(f"Has process_nl_query? {hasattr(agent, 'process_nl_query')}")
    print(f"Has process_hitl_feedback? {hasattr(agent, 'process_hitl_feedback')}")
    print(f"Has get_recommended_questions? {hasattr(agent, 'get_recommended_questions')}")
    print(f"Has get_kpi_definitions? {hasattr(agent, 'get_kpi_definitions')}")
    
    # Check that agent card entrypoints are implemented
    print(f"Has detect_situation? {hasattr(agent, 'detect_situation')}")
    print(f"Has summarize_situation? {hasattr(agent, 'summarize_situation')}")
    print(f"Has aggregate_agent_outputs? {hasattr(agent, 'aggregate_agent_outputs')}")

if __name__ == "__main__":
    asyncio.run(main())
