# test_llm_workflow.py
import asyncio
import traceback

from src.agents.a9_orchestrator_agent import A9_Orchestrator_Agent
from src.agents.utils.a9_shared_logger import a9_logger

async def main():
    """
    Runs a full, end-to-end test of the agent workflow, including the new
    LLM-driven SQL generation.
    """
    a9_logger.info("--- Starting End-to-End Workflow Test ---")
    
    try:
        # The orchestrator will create and register all necessary agents, 
        # including the new A9_LLM_Service_Agent.
        orchestrator = await A9_Orchestrator_Agent.create_from_registry()
        
        # We run the workflow for the 'ceo' principal and automatically select
        # the first detected situation (hitl_choice=1) to test the full flow.
        solution_set = await orchestrator.run_workflow(principal_id="ceo_001", hitl_choice=1)
        
        if solution_set:
            a9_logger.info("--- Workflow Test Completed Successfully ---")
            a9_logger.info(f"Generated {len(solution_set.options)} solutions.")
            for i, option in enumerate(solution_set.options):
                a9_logger.info(f"  Solution {i+1}: {option.title} (Confidence: {option.confidence_score})")
                a9_logger.info(f"    - {option.summary}")
        else:
            a9_logger.error("--- Workflow Test Failed: No solution set was generated. ---")
    except Exception as e:
        a9_logger.error("--- An unexpected error occurred during the workflow test ---")
        a9_logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())
