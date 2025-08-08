# tests/manual/test_nlp_workflow.py
import asyncio
import json
import sys
import os

# Add the project root to the Python path to resolve module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.agents.agent_registry import registry

async def main():
    """
    Manual test script to run the full Situation Awareness workflow 
    and inspect the LLM-powered SQL generation process.
    """
    print("--- Initializing Agents ---")
    # Initialize all necessary agents from the registry
    orchestrator = await registry.get_agent("A9_Orchestrator_Agent")
    situation_agent = await registry.get_agent("A9_Situation_Awareness_Agent")
    # The V2 agent will be created by the orchestrator when needed.

    if not orchestrator or not situation_agent:
        print("Error: Could not initialize required agents.")
        return

    print("--- Agents Initialized ---")

    # Define the principal and filters for the test
    principal_id = "CEO"
    filters = {"Product Category": "Laptops"}
    
    print(f"\n--- Running Situational Picture for Principal: {principal_id} with Filters: {filters} ---")
    
    # The Situation Awareness agent needs the principal's profile
    principal_context_agent = await registry.get_agent("A9_Principal_Context_Agent")
    principal_profile = await principal_context_agent.fetch_principal_profile(principal_id)

    # Get the situational picture
    reports = await situation_agent.get_situational_picture(
        principal_id=principal_id,
        principal_profile=principal_profile,
        filters=filters
    )

    print(f"\n--- Test Complete. {len(reports)} Reports Generated. ---")

    if not reports:
        print("\nNo reports were generated. The workflow may have been interrupted.")
        return

    # Print the debug information for each report
    for i, report_data in enumerate(reports):
        print(f"\n--- Report {i+1}: KPI '{report_data.get('kpi_name')}' ---")
        
        meta = report_data.get("meta", {})
        debug_info = meta.get("debug_info", {})

        if not debug_info:
            print("  No debug info found in the report.")
            continue

        # Print the NLP request data
        nlp_request = debug_info.get("nlp_request_data", {})
        print("\n  [1] Data Sent to NLP Agent:")
        print(json.dumps(nlp_request, indent=4))

        # Print the final SQL query
        final_query = debug_info.get("final_sql_query", "Not available")
        print("\n  [2] Final LLM-Generated SQL Query:")
        print(final_query)
        
        # Print the final values
        print("\n  [3] Final Report Values:")
        print(f"    Current Value: {report_data.get('current_value')}")
        print(f"    Previous Value: {meta.get('previous_value')}")
        print(f"    Trend: {meta.get('trend')}")

if __name__ == "__main__":
    asyncio.run(main())
