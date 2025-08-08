# apps/a9_athyna_llm_sql_tester.py
import streamlit as st
import asyncio
import pandas as pd
import sys
import os

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.agent_registry import registry
from src.agents.a9_orchestrator_agent import A9_Orchestrator_Agent
from src.services.a9_data_product_mcp_service import A9_Data_Product_MCP_Service
from src.agents.utils.a9_shared_logger import a9_logger
from src.models.governance_models import KPIRequest
from src.models.nlp_models import NLPBusinessQueryInput

st.set_page_config(layout="wide", page_title="ATHENA LLM SQL Tester")

st.title("ATHENA LLM SQL Generation Tester")
st.write("An interactive tool to test the Natural Language to SQL generation capabilities of Agent9-ATHENA.")

async def initialize_agents():
    """Initializes and registers all necessary agents."""
    if 'agents_initialized' not in st.session_state:
        st.session_state.orchestrator = await A9_Orchestrator_Agent.create_from_registry()
        st.session_state.mcp_service = A9_Data_Product_MCP_Service()
        st.session_state.mcp_service.load_data_products()
        st.session_state.agents_initialized = True
        a9_logger.info("Agents and services initialized for Streamlit app.")

async def main():
    """Main function to run the Streamlit app."""
    await initialize_agents()

    st.sidebar.header("Controls")
    principal_id = st.sidebar.selectbox("Select Principal", ["CEO", "CFO", "CRO"])

    st.header(f"Query Interface for {principal_id}")

    natural_language_question = st.text_input(
        "Ask a business question:", 
        value="What is the total revenue for Laptops this year?"
    )

    if st.button("Generate SQL and Get Answer"):
        if not natural_language_question:
            st.warning("Please enter a business question.")
            return

        orchestrator = st.session_state.orchestrator
        mcp_service = st.session_state.mcp_service

        with st.spinner("Processing your request..."):
            try:
                # This workflow mimics the full agent orchestration for generating SQL.

                # 1. Get necessary context from other agents
                data_gov_agent = await registry.get_agent("A9_Data_Governance_Agent")
                principal_agent = await registry.get_agent("A9_Principal_Context_Agent")

                # 2. Fetch the principal's profile to get their business processes
                profile = await principal_agent.fetch_principal_profile(principal_id)
                # For this test, we'll use the first business process to find a relevant KPI.
                business_process = profile.business_processes[0] if profile.business_processes else "Financial Planning"
                kpi_request = KPIRequest(business_processes=[business_process])
                kpi_response = await data_gov_agent.get_kpis_for_business_processes(kpi_request)
                kpis = kpi_response.kpis
                kpi_name = kpis[0] if kpis else 'Gross Revenue'

                st.info(f"Using KPI: **{kpi_name}** for the base query.")

                # 3. Call the NLP agent to parse the question into structured intent and SQL
                nlp_agent = await registry.get_agent("A9_NLP_Interface_Agent")
                if not nlp_agent:
                    st.error("A9_NLP_Interface_Agent not found in registry.")
                    return

                nlp_request = NLPBusinessQueryInput(
                    question=natural_language_question,
                    user_id=principal_id,
                    principal_context=profile.model_dump() # Pass the full profile
                )

                nlp_result = await nlp_agent.parse_business_query(nlp_request)
                sql_query = nlp_result.raw_sql_query

                st.subheader("Generated SQL Query")
                if sql_query and not nlp_result.human_action_required:
                    st.code(sql_query, language='sql')

                    # 4. Execute the query using the MCP service
                    st.subheader("Query Result")
                    query_result = mcp_service.execute_query(sql_query)
                    
                    if isinstance(query_result, pd.DataFrame):
                        st.dataframe(query_result)
                    else:
                        st.warning("Query executed, but did not return a DataFrame.")
                        st.write(query_result)
                else:
                    st.error("Failed to generate SQL query.")
                    st.write(nlp_result.model_dump()) # Show the error response

            except Exception as e:
                st.error(f"An error occurred: {e}")
                a9_logger.error(f"Error in Streamlit app: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
