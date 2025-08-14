"""
Decision Studio Debug UI for Agent9 Situation Awareness

This Streamlit application provides a debug-enhanced user interface for 
interacting with the Situation Awareness Agent and visualizing KPI situations.
It follows Agent9 standards with orchestrator-driven workflow.

For MVP, focuses on Finance KPIs from the FI Star Schema.
"""

import os
import sys
import asyncio
import streamlit as st
import pandas as pd
import plotly.express as px
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# Add the project root to the Python path for imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Import our models
from src.agents.models.situation_awareness_models import (
    PrincipalContext, 
    PrincipalRole,
    BusinessProcess,
    TimeFrame, 
    ComparisonType,
    SituationSeverity,
    Situation,
    KPIValue,
    SituationDetectionRequest,
    SituationDetectionResponse,
    NLQueryRequest,
    NLQueryResponse,
    HITLRequest,
    HITLResponse,
    HITLDecision
)

# Import our orchestrator wrapper
from src.views.ui_orchestrator import UIOrchestrator

# Set page configuration
st.set_page_config(
    page_title="Agent9 Decision Studio Debug",
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
    .debug-panel {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
    }
    .metrics-card {
        background-color: #f7f7f7;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .stButton>button {
        width: 100%;
    }
    .sql-statement {
        font-family: monospace;
        white-space: pre-wrap;
        background-color: #f8f8f8;
        padding: 10px;
        border-radius: 5px;
        margin-top: 5px;
        margin-bottom: 5px;
        font-size: 0.9em;
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
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = None
    
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
        st.session_state.debug_mode = True  # Default to debug mode for this UI
    
    if "debug_metrics" not in st.session_state:
        st.session_state.debug_metrics = {}
    
    if "execution_time" not in st.session_state:
        st.session_state.execution_time = {}
    
    if "registry_loaded" not in st.session_state:
        st.session_state.registry_loaded = False

# Initialize the UI Orchestrator
async def initialize_orchestrator():
    """Initialize and connect to the UI Orchestrator."""
    if st.session_state.orchestrator is None:
        with st.spinner("Initializing Orchestrator..."):
            # Create orchestrator with contract path
            contract_path = os.path.join(
                os.path.abspath(os.path.dirname(__file__)), 
                "..", 
                "contracts",
                "fi_star_schema.yaml"
            )
            
            # Create the orchestrator with configuration
            orchestrator = UIOrchestrator({
                "contract_path": contract_path,
                "database_config": {
                    "type": "duckdb",
                    "path": ":memory:"  # Use in-memory database for demo
                },
                "orchestrator_config": {}
            })
            
            # Initialize the orchestrator
            start_time = time.time()
            await orchestrator.initialize()
            end_time = time.time()
            
            # Store execution time
            st.session_state.execution_time["orchestrator_init"] = round((end_time - start_time) * 1000, 2)  # ms
            
            # Store in session state
            st.session_state.orchestrator = orchestrator
            
            # Get debug metrics
            st.session_state.debug_metrics = orchestrator.get_debug_metrics()
            
            # Set registry loaded flag based on debug metrics
            if "registry_status" in st.session_state.debug_metrics:
                registry_status = st.session_state.debug_metrics["registry_status"]
                if registry_status and "kpi_registry" in registry_status:
                    st.session_state.registry_loaded = registry_status["kpi_registry"].get("loaded", False)
            
            # Get recommended questions for default principal
            try:
                principal_context = await orchestrator.get_principal_context(st.session_state.principal_role)
                questions = await orchestrator.get_recommended_questions(principal_context)
                st.session_state.recommended_questions = questions
            except Exception as e:
                st.error(f"Failed to get recommended questions: {str(e)}")
            
            return orchestrator
    
    return st.session_state.orchestrator

# Get principal context from the orchestrator
async def get_principal_context(principal_role: PrincipalRole):
    """Get principal context for the selected role."""
    orchestrator = st.session_state.orchestrator
    if orchestrator:
        try:
            start_time = time.time()
            context = await orchestrator.get_principal_context(principal_role)
            end_time = time.time()
            
            # Store execution time
            st.session_state.execution_time["get_principal_context"] = round((end_time - start_time) * 1000, 2)  # ms
            
            return context
        except Exception as e:
            st.error(f"Failed to get principal context: {str(e)}")
            return None
    return None

# Detect situations based on current filters
async def detect_situations():
    """Detect situations based on current filters and update the UI."""
    orchestrator = st.session_state.orchestrator
    if orchestrator:
        try:
            # Create request parameters
            principal_role = st.session_state.principal_role
            business_processes = st.session_state.business_processes
            timeframe = st.session_state.timeframe
            comparison_type = st.session_state.comparison_type
            filters = st.session_state.filters
            
            # Call the orchestrator to detect situations
            start_time = time.time()
            situations = await orchestrator.detect_situations(
                principal_role=principal_role,
                business_processes=business_processes,
                timeframe=timeframe,
                comparison_type=comparison_type,
                filters=filters
            )
            end_time = time.time()
            
            # Store execution time
            st.session_state.execution_time["detect_situations"] = round((end_time - start_time) * 1000, 2)  # ms
            
            # Update debug metrics
            st.session_state.debug_metrics = orchestrator.get_debug_metrics()
            
            # Store situations in session state
            st.session_state.situations = situations
            
            return situations
        except Exception as e:
            st.error(f"Failed to detect situations: {str(e)}")
            return []
    return []

# Process natural language query
async def process_query():
    """Process natural language query and update the UI."""
    orchestrator = st.session_state.orchestrator
    if orchestrator and st.session_state.nl_query:
        try:
            # Create request parameters
            principal_role = st.session_state.principal_role
            query = st.session_state.nl_query
            timeframe = st.session_state.timeframe
            
            # Call the orchestrator to process the query
            start_time = time.time()
            response = await orchestrator.process_nl_query(
                principal_role=principal_role,
                query=query,
                timeframe=timeframe
            )
            end_time = time.time()
            
            # Store execution time
            st.session_state.execution_time["process_query"] = round((end_time - start_time) * 1000, 2)  # ms
            
            # Update debug metrics
            st.session_state.debug_metrics = orchestrator.get_debug_metrics()
            
            # Store response in session state
            st.session_state.nl_response = response
            
            return response
        except Exception as e:
            st.error(f"Failed to process query: {str(e)}")
            return None
    return None

# Apply recommended question
def apply_question(question: str):
    """Apply a recommended question as the natural language query."""
    st.session_state.nl_query = question
    # Processing will be handled in the async section

# Display debug metrics
def display_debug_metrics():
    """Display debug metrics in the UI."""
    debug_metrics = st.session_state.debug_metrics
    execution_time = st.session_state.execution_time
    
    # Create tabs for different debug metrics
    debug_tab1, debug_tab2, debug_tab3, debug_tab4 = st.tabs([
        "🔍 Registry Status", 
        "⚙️ Agent Initialization", 
        "📊 KPI & Situation Metrics",
        "🔄 SQL Execution"
    ])
    
    with debug_tab1:
        st.subheader("Registry Status")
        registry_status = debug_metrics.get("registry_status", {})
        
        # Create a clean display of registry status
        if registry_status:
            # Create columns for different registry types
            cols = st.columns(len(registry_status))
            
            for i, (registry_name, status) in enumerate(registry_status.items()):
                with cols[i]:
                    st.metric(
                        label=registry_name.replace("_registry", "").title(),
                        value=status.get("count", 0),
                        delta="Loaded" if status.get("loaded", False) else "Not Loaded",
                        delta_color="normal" if status.get("loaded", False) else "off"
                    )
                    st.caption(f"Source: {status.get('source', 'Unknown')}")
        else:
            st.info("No registry status available yet")
    
    with debug_tab2:
        st.subheader("Agent Initialization Sequence")
        agent_inits = debug_metrics.get("agent_initializations", [])
        
        if agent_inits:
            # Convert to DataFrame for display
            df = pd.DataFrame(agent_inits)
            
            # Format timestamp
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df["time"] = df["timestamp"].dt.strftime("%H:%M:%S.%f").str[:-3]
            
            # Display as table
            st.dataframe(
                df[["agent", "status", "time"]],
                use_container_width=True
            )
            
            # Display execution time
            if "orchestrator_init" in execution_time:
                st.metric(
                    label="Total Initialization Time",
                    value=f"{execution_time['orchestrator_init']} ms"
                )
        else:
            st.info("No agent initialization data available yet")
    
    with debug_tab3:
        st.subheader("KPI & Situation Metrics")
        
        # Create columns for KPI and situation metrics
        col1, col2 = st.columns(2)
        
        with col1:
            # KPI metrics
            kpis_loaded = debug_metrics.get("kpis_loaded", 0)
            st.metric(
                label="KPIs Loaded",
                value=kpis_loaded
            )
            
            # Show time taken
            if "detect_situations" in execution_time:
                st.metric(
                    label="Situation Detection Time",
                    value=f"{execution_time.get('detect_situations', 0)} ms"
                )
        
        with col2:
            # Situation metrics
            situations_by_severity = debug_metrics.get("situations_by_severity", {})
            
            if situations_by_severity:
                # Convert to DataFrame for visualization
                severity_data = []
                for severity, count in situations_by_severity.items():
                    severity_data.append({
                        "Severity": severity,
                        "Count": count
                    })
                
                df = pd.DataFrame(severity_data)
                
                # Create bar chart
                fig = px.bar(
                    df, 
                    x="Severity", 
                    y="Count",
                    title="Situations by Severity",
                    color="Severity",
                    color_discrete_map={
                        "CRITICAL": "red",
                        "HIGH": "orange",
                        "MEDIUM": "yellow",
                        "LOW": "green",
                        "INFORMATION": "blue"
                    }
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No situations detected yet")
    
    with debug_tab4:
        st.subheader("SQL Execution")
        sql_statements = debug_metrics.get("sql_statements", [])
        
        if sql_statements:
            # Show SQL statements with execution time
            for i, statement in enumerate(sql_statements):
                with st.expander(f"SQL Statement {i+1} ({statement.get('execution_time_ms', 0):.2f} ms)"):
                    st.markdown(f"**Timestamp:** {statement.get('timestamp', '')}")
                    st.markdown("**SQL Query:**")
                    st.code(statement.get("query", ""), language="sql")
            
            # Show SQL execution time statistics
            sql_times = [s.get("execution_time_ms", 0) for s in sql_statements]
            if sql_times:
                st.metric(
                    label="Average SQL Execution Time",
                    value=f"{sum(sql_times) / len(sql_times):.2f} ms"
                )
                
                # Create histogram of execution times
                df = pd.DataFrame({
                    "Execution Time (ms)": sql_times
                })
                
                fig = px.histogram(
                    df, 
                    x="Execution Time (ms)",
                    title="SQL Execution Time Distribution",
                    nbins=10
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No SQL statements executed yet")

# Display protocol messages
def display_protocol_messages():
    """Display protocol messages in the UI."""
    debug_metrics = st.session_state.debug_metrics
    protocol_messages = debug_metrics.get("protocol_messages", [])
    
    with st.expander("Protocol Messages", expanded=False):
        if protocol_messages:
            # Convert to DataFrame for display
            df = pd.DataFrame(protocol_messages)
            
            # Format timestamp
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df["time"] = df["timestamp"].dt.strftime("%H:%M:%S.%f").str[:-3]
            
            # Display as table
            st.dataframe(
                df[["time", "direction", "method", "message"]],
                use_container_width=True
            )
        else:
            st.info("No protocol messages recorded yet")

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

# Main function to run the Streamlit app
def main():
    """Main function to run the Decision Studio Debug UI."""
    # Initialize session state
    init_session_state()
    
    # Title and description
    st.title("Agent9 Decision Studio Debug")
    st.markdown("*Visualize KPI situations with debugging capabilities*")
    
    # Create sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # Principal selection with specific IDs
        principal_options = [
            {"id": "cfo_001", "role": PrincipalRole.CFO, "display": "CFO (cfo_001)"},
            {"id": "finance_001", "role": PrincipalRole.FINANCE_MANAGER, "display": "Finance Manager (finance_001)"}
        ]
        
        # Get display names for the dropdown
        principal_display_options = [p["display"] for p in principal_options]
        
        # Default to CFO
        default_index = 0
        
        # Show principal selection dropdown
        selected_principal = st.selectbox(
            "Principal",
            options=principal_display_options,
            index=default_index
        )
        
        # Set the principal role based on selection
        selected_index = principal_display_options.index(selected_principal)
        st.session_state.principal_role = principal_options[selected_index]["role"]
        st.session_state.principal_id = principal_options[selected_index]["id"]
        
        # Show which principal was selected (role and ID)
        st.info(f"Selected: {principal_options[selected_index]['display']}")
        
        # Business process selection
        business_processes = st.multiselect(
            "Business Processes",
            options=[process.name for process in BusinessProcess],
            default=[BusinessProcess.PROFITABILITY_ANALYSIS.name],
            format_func=lambda x: x.replace("_", " ")
        )
        st.session_state.business_processes = [BusinessProcess[bp] for bp in business_processes]
        
        # Time frame selection
        timeframe = st.selectbox(
            "Time Frame",
            options=[tf.name for tf in TimeFrame],
            index=0,
            format_func=lambda x: x.replace("_", " ")
        )
        st.session_state.timeframe = TimeFrame[timeframe]
        
        # Comparison type selection
        comparison_type = st.selectbox(
            "Comparison Type",
            options=[ct.name for ct in ComparisonType],
            index=0,
            format_func=lambda x: x.replace("_", " ")
        )
        st.session_state.comparison_type = ComparisonType[comparison_type]
        
        # Add separator
        st.markdown("---")
        
        # Additional filters
        st.subheader("Additional Filters")
        
        # Profit Center filter
        profit_center = st.selectbox(
            "Profit Center",
            options=["All", "PC1000", "PC2000", "PC3000"],
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
    
    # Create tabs for situations and natural language query
    tab1, tab2 = st.tabs(["📊 Situations", "🔍 Natural Language Query"])
    
    with tab1:
        # Display situations
        if st.session_state.situations:
            st.subheader("Detected Situations")
            
            # Group situations by severity
            severity_order = {
                SituationSeverity.CRITICAL: 1,
                SituationSeverity.HIGH: 2,
                SituationSeverity.MEDIUM: 3,
                SituationSeverity.LOW: 4,
                SituationSeverity.INFORMATION: 5
            }
            
            # Sort situations by severity
            sorted_situations = sorted(
                st.session_state.situations,
                key=lambda s: severity_order.get(s.severity, 999)
            )
            
            # Display situations
            for situation in sorted_situations:
                severity_class = situation.severity.name.lower()
                display_situation(situation, severity_class)
        else:
            st.info("No situations detected yet. Click 'Refresh Situations' to detect situations.")
    
    with tab2:
        st.subheader("Natural Language Query")
        
        # Query input
        nl_query = st.text_area(
            "Enter your query",
            value=st.session_state.nl_query,
            height=100
        )
        st.session_state.nl_query = nl_query
        
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
            if hasattr(st.session_state.nl_response, 'kpi_values') and st.session_state.nl_response.kpi_values:
                st.subheader("KPI Values")
                for kpi_value in st.session_state.nl_response.kpi_values:
                    with st.expander(f"{kpi_value.kpi_name}"):
                        st.metric(
                            label=kpi_value.kpi_name,
                            value=f"{kpi_value.value:,.2f}",
                            delta=f"{(kpi_value.value - kpi_value.comparison_value):,.2f}" if kpi_value.comparison_value is not None else None
                        )
            
            # Display SQL query if available
            if hasattr(st.session_state.nl_response, 'sql_query') and st.session_state.nl_response.sql_query:
                with st.expander("SQL Query"):
                    st.code(st.session_state.nl_response.sql_query, language="sql")
    
    # Debug panels
    st.markdown("---")
    st.header("Debug Information")
    
    # Display debug metrics
    display_debug_metrics()
    
    # Display protocol messages
    display_protocol_messages()

# Run the async functions
async def run_async():
    """Run the async functions required for the app."""
    # Initialize orchestrator
    orchestrator = await initialize_orchestrator()
    
    # If we have an orchestrator and no situations, detect situations
    if orchestrator and not st.session_state.situations:
        await detect_situations()
    
    # Process natural language query if needed
    if orchestrator and st.session_state.nl_query and (
        not st.session_state.nl_response or 
        st.session_state.nl_response.request_id != st.session_state.nl_query
    ):
        await process_query()

# Streamlit doesn't natively support asyncio, so we need to handle it
if __name__ == "__main__":
    main()
    
    # Use this to run async functions
    asyncio.run(run_async())
