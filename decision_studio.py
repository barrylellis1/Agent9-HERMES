"""
Standalone Decision Studio UI for Agent9 Situation Awareness

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
from enum import Enum

# Add the project root to the Python path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import required models and modules
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
# Import the correct situation awareness agent creator
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
    
    if "principal_role" not in st.session_state:
        st.session_state.principal_role = PrincipalRole.CFO
    
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
            try:
                # Create agent with contract path
                contract_path = os.path.join(
                    os.path.abspath(os.path.dirname(__file__)), 
                    "src", 
                    "contracts",
                    "fi_star_schema.yaml"
                )
                
                agent = create_situation_awareness_agent({
                    "contract_path": contract_path
                })
                
                # Connect to agent
                await agent.connect()
                
                st.session_state.agent = agent
                st.success("Agent initialized successfully!")
                
                return agent
            except Exception as e:
                st.error(f"Error initializing agent: {str(e)}")
                return None
    else:
        return st.session_state.agent

# Get principal context from the agent
async def get_principal_context(principal_role: PrincipalRole):
    """Get principal context for the selected role."""
    agent = st.session_state.agent
    if agent is None:
        return None
    
    # Get principal context from agent
    context = await agent.get_principal_context(principal_role)
    
    return context

# Detect situations based on current filters
async def detect_situations():
    """Detect situations based on current filters and update the UI."""
    agent = st.session_state.agent
    if agent is None:
        return
    
    # Prepare the situation detection request
    request = SituationDetectionRequest(
        request_id=str(uuid.uuid4()),
        principal_role=st.session_state.principal_role,
        business_processes=st.session_state.business_processes,
        timeframe=st.session_state.timeframe,
        comparison_type=st.session_state.comparison_type,
        filters=st.session_state.filters
    )
    
    with st.spinner("Detecting situations..."):
        try:
            # Call the agent
            response = await agent.detect_situations(request)
            
            # Update session state
            if response.status == "success":
                st.session_state.situations = response.situations
                st.success(f"Detected {len(response.situations)} situations")
            else:
                st.error(f"Error detecting situations: {response.message}")
        except Exception as e:
            st.error(f"Error detecting situations: {str(e)}")

# Process natural language query
async def process_query():
    """Process natural language query and update the UI."""
    agent = st.session_state.agent
    if agent is None:
        return
    
    # Prepare the NL query request
    request = NLQueryRequest(
        request_id=st.session_state.nl_query,
        query=st.session_state.nl_query,
        principal_role=st.session_state.principal_role,
        business_processes=st.session_state.business_processes,
        timeframe=st.session_state.timeframe,
        comparison_type=st.session_state.comparison_type,
        filters=st.session_state.filters
    )
    
    with st.spinner("Processing query..."):
        try:
            # Call the agent
            response = await agent.process_nl_query(request)
            
            # Update session state
            st.session_state.nl_response = response
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")

# Apply recommended question
def apply_question(question: str):
    """Apply a recommended question as the natural language query."""
    st.session_state.nl_query = question

# Main function to run the Streamlit app
def main():
    """Main function to run the Decision Studio UI."""
    # Initialize session state
    init_session_state()
    
    # Create the sidebar for filters
    with st.sidebar:
        st.title("Agent9 Decision Studio")
        
        # Principal role selector
        st.header("Principal Context")
        principal_role = st.selectbox(
            "Select Principal Role",
            options=[role.value for role in PrincipalRole],
            index=list(PrincipalRole).index(st.session_state.principal_role),
            format_func=lambda x: x.replace("_", " ").title(),
            key="principal_role_select"
        )
        st.session_state.principal_role = PrincipalRole(principal_role)
        
        # Business process selector
        st.header("Business Processes")
        all_processes = [process.value for process in BusinessProcess]
        selected_processes = st.multiselect(
            "Select Business Processes",
            options=all_processes,
            default=[process.value for process in st.session_state.business_processes],
            format_func=lambda x: x.replace("_", " ").title(),
            key="business_processes_select"
        )
        st.session_state.business_processes = [BusinessProcess(process) for process in selected_processes]
        
        # Timeframe selector
        st.header("Time Frame")
        timeframe = st.selectbox(
            "Select Time Frame",
            options=[tf.value for tf in TimeFrame],
            index=list(TimeFrame).index(st.session_state.timeframe),
            format_func=lambda x: x.replace("_", " ").title(),
            key="timeframe_select"
        )
        st.session_state.timeframe = TimeFrame(timeframe)
        
        # Comparison type selector
        comparison_type = st.selectbox(
            "Select Comparison",
            options=[ct.value for ct in ComparisonType],
            index=list(ComparisonType).index(st.session_state.comparison_type),
            format_func=lambda x: x.replace("_", " ").title(),
            key="comparison_type_select"
        )
        st.session_state.comparison_type = ComparisonType(comparison_type)
        
        # Additional filters
        st.header("Additional Filters")
        # For MVP, we'll include a simple text filter
        filter_key = st.text_input("Filter Key", key="filter_key")
        filter_value = st.text_input("Filter Value", key="filter_value")
        
        if st.button("Apply Filter"):
            if filter_key and filter_value:
                st.session_state.filters[filter_key] = filter_value
                st.success(f"Filter applied: {filter_key} = {filter_value}")
        
        # Clear filters
        if st.button("Clear Filters"):
            st.session_state.filters = {}
            st.success("Filters cleared")
        
        # Debug mode
        st.header("Debug Mode")
        debug_mode = st.checkbox("Enable Debug Mode", value=st.session_state.debug_mode)
        st.session_state.debug_mode = debug_mode
        
        # Run situation detection
        if st.button("Detect Situations"):
            # This will be handled in the async section
            pass
    
    # Main content area
    st.title("Finance KPI Situation Awareness")
    
    # Display information about the principal
    st.header(f"Principal: {st.session_state.principal_role.value.replace('_', ' ').title()}")
    
    # Display detected situations
    st.header("Detected Situations")
    
    if st.session_state.situations:
        # Group situations by severity
        severity_groups = {}
        for situation in st.session_state.situations:
            if situation.severity not in severity_groups:
                severity_groups[situation.severity] = []
            severity_groups[situation.severity].append(situation)
        
        # Display situations by severity
        for severity in [SituationSeverity.CRITICAL, SituationSeverity.HIGH, 
                         SituationSeverity.MEDIUM, SituationSeverity.LOW, 
                         SituationSeverity.INFORMATION]:
            if severity in severity_groups:
                st.subheader(f"{severity.value.capitalize()} Situations")
                
                for situation in severity_groups[severity]:
                    # Map severity to CSS class
                    severity_class = severity.value.lower()
                    display_situation(situation, severity_class)
    else:
        st.info("No situations detected yet. Click 'Detect Situations' to begin.")
    
    # Natural language query section
    st.header("Ask a Question")
    
    with st.container():
        st.session_state.nl_query = st.text_input(
            "Enter your question",
            value=st.session_state.nl_query
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
