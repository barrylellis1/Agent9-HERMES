"""
Decision Studio UI for Agent9 Situation Awareness

This Streamlit application provides a user interface for interacting with
the Situation Awareness Agent and visualizing KPI situations.

For MVP, focuses on Finance KPIs from the FI Star Schema.
"""

import os
import sys
import asyncio
import streamlit as st
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

# Add the project root to the Python path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Now we can import our modules
from src.agents.models.situation_awareness_models import (
    PrincipalContext, 
    PrincipalRole,
    BusinessProcess,
    TimeFrame, 
    ComparisonType,
    SituationSeverity,
    SituationDetectionRequest,
    NLQueryRequest
)
from src.agents.new.a9_situation_awareness_agent import create_situation_awareness_agent

# Set page configuration
st.set_page_config(
    page_title="Agent9 Decision Studio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to improve the UI
st.markdown("""
<style>
    .situation-card {
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .critical {
        border-left: 5px solid #FF0000;
        background-color: rgba(255, 0, 0, 0.1);
    }
    .high {
        border-left: 5px solid #FFA500;
        background-color: rgba(255, 165, 0, 0.1);
    }
    .medium {
        border-left: 5px solid #FFFF00;
        background-color: rgba(255, 255, 0, 0.1);
    }
    .low {
        border-left: 5px solid #008000;
        background-color: rgba(0, 128, 0, 0.1);
    }
    .information {
        border-left: 5px solid #0000FF;
        background-color: rgba(0, 0, 255, 0.1);
    }
    .business-process {
        padding: 10px;
        border-radius: 5px;
        margin-right: 10px;
        cursor: pointer;
    }
    .business-process.selected {
        background-color: rgba(0, 0, 255, 0.2);
    }
    .stButton>button {
        width: 100%;
    }
    h1 {
        color: #1E3A8A;
    }
    h2 {
        color: #2563EB;
    }
    h3 {
        color: #3B82F6;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for our application
def init_session_state():
    """Initialize session state variables."""
    if "agent" not in st.session_state:
        st.session_state.agent = None
    
    if "ui_orchestrator" not in st.session_state:
        st.session_state.ui_orchestrator = None
    
    if "principal_role" not in st.session_state:
        st.session_state.principal_role = PrincipalRole.CFO
    
    if "principal_id" not in st.session_state:
        # Default principal ID for CFO role
        st.session_state.principal_id = "cfo_001"
    
    if "business_processes" not in st.session_state:
        st.session_state.business_processes = [BusinessProcess.PROFITABILITY_ANALYSIS]
    
    if "timeframe" not in st.session_state:
        st.session_state.timeframe = TimeFrame.CURRENT_QUARTER
    
    if "comparison_type" not in st.session_state:
        st.session_state.comparison_type = ComparisonType.QUARTER_OVER_QUARTER
    
    if "situations" not in st.session_state:
        st.session_state.situations = []
    
    if "nl_query" not in st.session_state:
        st.session_state.nl_query = ""
    
    if "nl_response" not in st.session_state:
        st.session_state.nl_response = None
    
    if "recommended_questions" not in st.session_state:
        st.session_state.recommended_questions = []
    
    if "filters" not in st.session_state:
        st.session_state.filters = {}
    
    if "debug_mode" not in st.session_state:
        st.session_state.debug_mode = False

# Initialize the Situation Awareness Agent
async def initialize_agent():
    """Initialize and connect to the Situation Awareness Agent."""
    if st.session_state.agent is None:
        with st.spinner("Initializing Situation Awareness Agent..."):
            # Create agent with contract path
            contract_path = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), 
                "..", 
                "contracts",
                "fi_star_schema.yaml"
            )
            
            agent = create_situation_awareness_agent({
                "contract_path": contract_path
            })
            
            # Connect the agent to its dependencies
            await agent.connect()
            
            # Store in session state
            st.session_state.agent = agent
            
            # Get recommended questions for default principal
            principal_context = agent.principal_profiles[st.session_state.principal_role]
            questions = await agent.get_recommended_questions(principal_context)
            st.session_state.recommended_questions = questions
            
            return agent
    
    return st.session_state.agent

# Get principal context from the agent
def get_principal_context(principal_role: PrincipalRole):
    """Get principal context for the selected role."""
    agent = st.session_state.agent
    if agent and principal_role in agent.principal_profiles:
        return agent.principal_profiles[principal_role]
    
    # Fallback to default
    return PrincipalContext(
        role=principal_role,
        business_processes=[BusinessProcess.PROFITABILITY_ANALYSIS],
        default_filters={},
        decision_style="analytical",
        communication_style="detailed",
        preferred_timeframes=[TimeFrame.CURRENT_QUARTER]
    )

# Detect situations based on current filters
async def detect_situations():
    """Detect situations based on current filters and update the UI."""
    # Use orchestrator instead of direct agent call
    from src.views.ui_orchestrator import UIOrchestrator
    
    if "ui_orchestrator" not in st.session_state or st.session_state.ui_orchestrator is None:
        with st.spinner("Initializing UI Orchestrator..."):
            # Create and initialize UIOrchestrator
            st.session_state.ui_orchestrator = UIOrchestrator()
            await st.session_state.ui_orchestrator.initialize()
    
    ui_orchestrator = st.session_state.ui_orchestrator
    if ui_orchestrator is None:
        st.error("UI Orchestrator not initialized")
        return
    
    # Call orchestrator to detect situations with principal_id if available
    with st.spinner("Detecting situations..."):
        try:
            situations = await ui_orchestrator.detect_situations(
                principal_role=st.session_state.principal_role,
                business_processes=st.session_state.business_processes,
                timeframe=st.session_state.timeframe,
                comparison_type=st.session_state.comparison_type,
                filters=st.session_state.filters,
                principal_id=st.session_state.principal_id if "principal_id" in st.session_state else None
            )
            
            st.session_state.situations = situations
            
            # Also get recommended questions if situations were found
            if situations:
                # Get principal context first (with principal_id if available)
                principal_context = await ui_orchestrator.get_principal_context(
                    st.session_state.principal_role,
                    st.session_state.principal_id if "principal_id" in st.session_state else None
                )
                
                # Get recommended questions using principal context
                questions = await ui_orchestrator.get_recommended_questions(principal_context)
                st.session_state.recommended_questions = questions
        except Exception as e:
            st.error(f"Error detecting situations: {str(e)}")

# Process natural language query
async def process_query():
    """Process natural language query and update the UI."""
    # Use orchestrator instead of direct agent call
    from src.views.ui_orchestrator import UIOrchestrator
    
    if not st.session_state.nl_query:
        return
    
    if "ui_orchestrator" not in st.session_state or st.session_state.ui_orchestrator is None:
        with st.spinner("Initializing UI Orchestrator..."):
            # Create and initialize UIOrchestrator
            st.session_state.ui_orchestrator = UIOrchestrator()
            await st.session_state.ui_orchestrator.initialize()
    
    ui_orchestrator = st.session_state.ui_orchestrator
    if ui_orchestrator is None:
        st.error("UI Orchestrator not initialized")
        return
    
    # Call orchestrator to process query with principal_id if available
    with st.spinner("Processing query..."):
        try:
            response = await ui_orchestrator.process_nl_query(
                principal_role=st.session_state.principal_role,
                query=st.session_state.nl_query,
                timeframe=st.session_state.timeframe,
                principal_id=st.session_state.principal_id if "principal_id" in st.session_state else None
            )
            
            st.session_state.nl_response = response
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
            st.session_state.nl_response = None

# Apply recommended question
def apply_question(question: str):
    """Apply a recommended question as the natural language query."""
    st.session_state.nl_query = question

# Main function to run the Streamlit app
def main():
    """Main function to run the Decision Studio UI."""
    # Initialize session state
    init_session_state()
    
    # Header
    st.title("Agent9 Decision Studio")
    st.subheader("Finance Situation Awareness")
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Filters & Controls")
        
        # Principal selector
        st.subheader("Principal")
        principal_role = st.selectbox(
            "Select Principal Role",
            options=[PrincipalRole.CFO, PrincipalRole.FINANCE_MANAGER],
            index=0,
            key="principal_role_select"
        )
        
        # Principal ID selector
        principal_id_options = {
            PrincipalRole.CFO: ["cfo_001"],
            PrincipalRole.FINANCE_MANAGER: ["ceo_001"]  # CEO also listed under Finance Manager for testing
        }
        
        principal_id = st.selectbox(
            "Select Specific Principal ID",
            options=principal_id_options.get(principal_role, [""]),
            index=0,
            key="principal_id_select"
        )
        
        if principal_role != st.session_state.principal_role:
            st.session_state.principal_role = principal_role
            # This will trigger a rerun with the new principal
        
        if "principal_id" not in st.session_state or principal_id != st.session_state.principal_id:
            st.session_state.principal_id = principal_id
            # This will trigger a rerun with the new principal ID
        
        # Business process selector
        st.subheader("Business Process")
        business_process = st.selectbox(
            "Select Business Process",
            options=[
                BusinessProcess.PROFITABILITY_ANALYSIS,
                BusinessProcess.REVENUE_GROWTH,
                BusinessProcess.EXPENSE_MANAGEMENT,
                BusinessProcess.CASH_FLOW,
                BusinessProcess.BUDGET_VS_ACTUALS
            ],
            index=0,
            key="business_process_select"
        )
        
        if [business_process] != st.session_state.business_processes:
            st.session_state.business_processes = [business_process]
            # This will trigger a rerun with the new business process
        
        # Timeframe selector
        st.subheader("Time Frame")
        timeframe = st.selectbox(
            "Select Time Frame",
            options=[
                TimeFrame.CURRENT_QUARTER,
                TimeFrame.CURRENT_MONTH,
                TimeFrame.YEAR_TO_DATE,
                TimeFrame.QUARTER_TO_DATE,
                TimeFrame.MONTH_TO_DATE
            ],
            index=0,
            key="timeframe_select"
        )
        
        if timeframe != st.session_state.timeframe:
            st.session_state.timeframe = timeframe
        
        # Comparison type selector
        st.subheader("Comparison")
        comparison_type = st.selectbox(
            "Select Comparison Type",
            options=[
                ComparisonType.QUARTER_OVER_QUARTER,
                ComparisonType.YEAR_OVER_YEAR,
                ComparisonType.MONTH_OVER_MONTH,
                ComparisonType.BUDGET_VS_ACTUAL
            ],
            index=0,
            key="comparison_type_select"
        )
        
        if comparison_type != st.session_state.comparison_type:
            st.session_state.comparison_type = comparison_type
        
        # Additional filters
        st.subheader("Additional Filters")
        
        # Profit Center filter
        profit_center = st.selectbox(
            "Profit Center",
            options=["All", "North America", "Europe", "Asia Pacific"],
            index=0
        )
        
        if profit_center != "All":
            st.session_state.filters["Profit Center ID"] = profit_center
        else:
            if "Profit Center ID" in st.session_state.filters:
                del st.session_state.filters["Profit Center ID"]
        
        # Customer Region filter
        customer_region = st.selectbox(
            "Customer Region",
            options=["All", "North", "South", "East", "West"],
            index=0
        )
        
        if customer_region != "All":
            st.session_state.filters["Customer ID"] = customer_region
        else:
            if "Customer ID" in st.session_state.filters:
                del st.session_state.filters["Customer ID"]
        
        # Refresh button
        if st.button("Refresh Situations"):
            # This will be handled in the async section
            st.experimental_rerun()
        
        # Debug mode toggle
        st.session_state.debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)

    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Situations section
        st.header(f"Situations for {st.session_state.principal_role}")
        
        if not st.session_state.situations:
            st.info("No situations detected yet. Click Refresh Situations to analyze the current data.")
        else:
            # Group situations by severity
            critical = [s for s in st.session_state.situations if s.severity == SituationSeverity.CRITICAL]
            high = [s for s in st.session_state.situations if s.severity == SituationSeverity.HIGH]
            medium = [s for s in st.session_state.situations if s.severity == SituationSeverity.MEDIUM]
            low = [s for s in st.session_state.situations if s.severity == SituationSeverity.LOW]
            info = [s for s in st.session_state.situations if s.severity == SituationSeverity.INFORMATION]
            
            # Display situations by severity
            if critical:
                st.subheader(f"Critical Situations ({len(critical)})")
                for situation in critical:
                    display_situation(situation, "critical")
            
            if high:
                st.subheader(f"High Priority Situations ({len(high)})")
                for situation in high:
                    display_situation(situation, "high")
            
            if medium:
                st.subheader(f"Medium Priority Situations ({len(medium)})")
                for situation in medium:
                    display_situation(situation, "medium")
            
            if low:
                st.subheader(f"Low Priority Situations ({len(low)})")
                for situation in low:
                    display_situation(situation, "low")
            
            if info:
                st.subheader(f"Informational ({len(info)})")
                for situation in info:
                    display_situation(situation, "information")
    
    with col2:
        # NL Query section
        st.header("Ask a Question")
        
        st.text_input(
            "Enter your question",
            key="nl_query",
            placeholder="E.g., What is the current Gross Margin?",
            help="Ask a question about your financial KPIs"
        )
        
        if st.button("Submit Question"):
            # This will be handled in the async section
            pass
        
        # Display recommended questions
        st.subheader("Recommended Questions")
        if st.session_state.recommended_questions:
            for question in st.session_state.recommended_questions:
                if st.button(question):
                    apply_question(question)
        else:
            st.info("No recommended questions available")
        
        # Display NL query response
        if st.session_state.nl_response:
            st.subheader("Answer")
            st.write(st.session_state.nl_response.answer)
            
            # Display KPI values if available
            if st.session_state.nl_response.kpi_values:
                st.subheader("KPI Values")
                for kpi_value in st.session_state.nl_response.kpi_values:
                    with st.expander(f"{kpi_value.kpi_name}"):
                        st.metric(
                            label=kpi_value.kpi_name,
                            value=f"{kpi_value.value:,.2f}",
                            delta=f"{(kpi_value.value - kpi_value.comparison_value):,.2f}" if kpi_value.comparison_value is not None else None
                        )
            
            # Display SQL query if debug mode is on
            if st.session_state.debug_mode and st.session_state.nl_response.sql_query:
                with st.expander("SQL Query"):
                    st.code(st.session_state.nl_response.sql_query, language="sql")

# Function to display a situation card
def display_situation(situation, severity_class):
    """Display a situation card in the UI."""
    with st.container():
        st.markdown(
            f"""
            <div class="situation-card {severity_class}">
                <h3>{situation.description}</h3>
                <p><strong>KPI:</strong> {situation.kpi_name}</p>
                <p><strong>Value:</strong> {situation.kpi_value.value:,.2f}</p>
            """,
            unsafe_allow_html=True
        )
        
        # Display comparison if available
        if situation.kpi_value.comparison_value is not None:
            percent_change = (situation.kpi_value.value - situation.kpi_value.comparison_value) / abs(situation.kpi_value.comparison_value) * 100
            st.markdown(
                f"""
                <p><strong>Change:</strong> {percent_change:,.1f}% from {situation.kpi_value.comparison_value:,.2f}</p>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        with st.expander("Details"):
            st.write(f"**Business Impact:** {situation.business_impact}")
            
            if situation.suggested_actions:
                st.subheader("Suggested Actions")
                for action in situation.suggested_actions:
                    st.write(f"- {action}")
            
            if situation.diagnostic_questions:
                st.subheader("Diagnostic Questions")
                for question in situation.diagnostic_questions:
                    if st.button(question, key=f"{situation.situation_id}_{question[:20]}"):
                        apply_question(question)

# Run the async functions
async def run_async():
    """Run the async functions required for the app."""
    # Initialize agent
    agent = await initialize_agent()
    
    # If we have an agent and no situations, detect situations
    if agent and not st.session_state.situations:
        await detect_situations()
    
    # Process natural language query if needed
    if st.session_state.nl_query and (
        not st.session_state.nl_response or 
        st.session_state.nl_response.request_id != st.session_state.nl_query
    ):
        await process_query()

# Streamlit doesn't natively support asyncio, so we need to handle it
if __name__ == "__main__":
    main()
    
    # Use this to run async functions
    asyncio.run(run_async())
