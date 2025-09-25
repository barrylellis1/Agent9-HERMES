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
import uuid
from enum import Enum
import logging

# Add the project root and 'src' directory to the Python path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Explicitly add the 'src' directory so 'src.agents...' imports resolve reliably
src_path = os.path.join(project_root, "src")
if os.path.isdir(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

# Import required models and modules
from src.agents.models.situation_awareness_models import (
    BusinessProcess,
    TimeFrame, 
    ComparisonType,
    SituationSeverity,
    SituationDetectionRequest,
    NLQueryRequest
)

# Import PrincipalContext from both models to ensure it's available
from src.agents.models.situation_awareness_models import PrincipalContext
from src.agents.models.principal_context_models import PrincipalProfileResponse
# Import Data Governance request models for debug mapping panel
from src.agents.models.data_governance_models import KPIDataProductMappingRequest, KPIViewNameRequest
# Import the agents from new implementation path
from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent
from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
from src.agents.new.a9_principal_context_agent import A9_Principal_Context_Agent

# Ensure root logger is configured; default to INFO to reduce console noise
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s"
    )
else:
    logging.getLogger().setLevel(logging.INFO)

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
    
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = None
        
    if "default_principal_id" not in st.session_state:
        st.session_state.default_principal_id = "cfo_001"
    
    if "business_processes" not in st.session_state:
        st.session_state.business_processes = ["Finance: Profitability Analysis"]  # Use specific business processes
    # Track previous selections to auto-trigger detection on change
    if "prev_business_processes" not in st.session_state:
        st.session_state.prev_business_processes = list(st.session_state.business_processes)
    
    if "timeframe" not in st.session_state:
        st.session_state.timeframe = TimeFrame.LAST_QUARTER
    if "prev_timeframe" not in st.session_state:
        st.session_state.prev_timeframe = st.session_state.timeframe
    
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
    # Seed minimal principal selector scaffolding so UI shows immediately
    if "principal_ids" not in st.session_state:
        st.session_state.principal_ids = [st.session_state.default_principal_id]
    if "principal_id_to_name" not in st.session_state:
        # Provide a friendly default display name
        st.session_state.principal_id_to_name = {st.session_state.default_principal_id: "Chief Financial Officer (CFO)"}
    if "selected_principal_id" not in st.session_state:
        st.session_state.selected_principal_id = st.session_state.default_principal_id
    # Ensure the principal selector widget state starts in sync with selected_principal_id
    if "principal_id_select" not in st.session_state:
        st.session_state.principal_id_select = st.session_state.selected_principal_id
    # Track previously selected principal to reset filters on change
    if "prev_selected_principal_id" not in st.session_state:
        st.session_state.prev_selected_principal_id = st.session_state.selected_principal_id
    # Flags to control one-time reruns/loading
    if "profiles_loaded" not in st.session_state:
        st.session_state.profiles_loaded = False
    if "profiles_rerun_done" not in st.session_state:
        st.session_state.profiles_rerun_done = False
    # Button trigger flags
    if "trigger_detect" not in st.session_state:
        st.session_state.trigger_detect = False
    if "trigger_query" not in st.session_state:
        st.session_state.trigger_query = False
    # One-time view ensure flag
    if "fi_star_view_checked" not in st.session_state:
        st.session_state.fi_star_view_checked = False
    # Feature flag to enable/disable NL Q&A UI
    if "enable_nl_ui" not in st.session_state:
        st.session_state.enable_nl_ui = False
    # Rolling debug trace for diagnostics
    if "debug_trace" not in st.session_state:
        st.session_state.debug_trace = []
    # Track if a detection is in progress (prevents duplicate spinners)
    if "detect_in_progress" not in st.session_state:
        st.session_state.detect_in_progress = False
    # Unified detection status: idle | queued | running | done | error
    if "detect_status" not in st.session_state:
        st.session_state.detect_status = "idle"
    # Per-KPI SQL debug flags/results
    if "show_per_kpi_sql" not in st.session_state:
        st.session_state.show_per_kpi_sql = False
    if "trigger_per_kpi_sql" not in st.session_state:
        st.session_state.trigger_per_kpi_sql = False
    if "per_kpi_sql_results" not in st.session_state:
        st.session_state.per_kpi_sql_results = []

# Initialize the Situation Awareness Agent using orchestrator-driven registration
async def initialize_agent():
    """Initialize and connect to the Situation Awareness Agent using orchestrator."""
    if st.session_state.agent is None:
        with st.spinner("Initializing Agent9 system..."):
            try:
                # Create agent with contract path
                contract_path = os.path.join(
                    os.path.abspath(os.path.dirname(__file__)), 
                    "src", 
                    "contracts",
                    "fi_star_schema.yaml"
                )
                
                # Initialize Registry Factory first
                from src.registry.factory import RegistryFactory
                from src.registry.providers.kpi_provider import KPIProvider
                from src.registry.providers.principal_provider import PrincipalProfileProvider
                from src.registry.providers.data_product_provider import DataProductProvider
                from src.registry.providers.business_glossary_provider import BusinessGlossaryProvider
                from src.registry.providers.business_process_provider import BusinessProcessProvider
                
                # Initialize registry factory
                registry_factory = RegistryFactory()
                
                # Register providers with explicit file paths
                registry_factory.register_provider('kpi', KPIProvider(
                    source_path="src/registry/kpi/kpi_registry.yaml",
                    storage_format="yaml"
                ))
                registry_factory.register_provider('principal_profile', PrincipalProfileProvider(
                    source_path="src/registry/principal/principal_registry.yaml",
                    storage_format="yaml"
                ))
                registry_factory.register_provider('data_product', DataProductProvider(
                    source_path="src/registry/data_product",
                    storage_format="yaml"
                ))
                registry_factory.register_provider('business_glossary', BusinessGlossaryProvider())
                registry_factory.register_provider('business_process', BusinessProcessProvider(
                    source_path="src/registry/business_process/business_process_registry.yaml",
                    storage_format="yaml"
                ))
                
                # Initialize registry factory
                await registry_factory.initialize()
                
                # First create and connect the orchestrator
                from src.agents.new.a9_orchestrator_agent import A9_Orchestrator_Agent, create_and_connect_agents
                
                with st.spinner("Creating and connecting orchestrator..."):
                    orchestrator_config = {}
                    orchestrator = await A9_Orchestrator_Agent.create(orchestrator_config)
                    await orchestrator.connect()
                    st.session_state.orchestrator = orchestrator
                
                # Use the orchestrator to create and connect all agents in the correct order
                with st.spinner("Creating and connecting agents in dependency order..."):
                    agents = await create_and_connect_agents(orchestrator, registry_factory)
                    
                    # Store agents in session state
                    st.session_state.agent = agents["A9_Situation_Awareness_Agent"]
                    st.success("Agent9 system initialized successfully!")
                
                # One-time ensure FI Star views/tables are created from contract
                try:
                    if not st.session_state.get("fi_star_view_checked", False):
                        with st.spinner("Preparing FI Star data product (tables and views)..."):
                            contract_path = os.path.join(
                                os.path.abspath(os.path.dirname(__file__)),
                                "src",
                                "contracts",
                                "fi_star_schema.yaml"
                            )
                            # Register base tables from contract (idempotent)
                            try:
                                await orchestrator.execute_agent_method(
                                    "A9_Data_Product_Agent",
                                    "register_tables_from_contract",
                                    {"contract_path": contract_path, "schema": "main"}
                                )
                            except Exception:
                                # Non-fatal; continue to view creation
                                pass
                            # Create or replace the FI_Star_View from the contract (idempotent)
                            await orchestrator.execute_agent_method(
                                "A9_Data_Product_Agent",
                                "create_view_from_contract",
                                {"contract_path": contract_path, "view_name": "FI_Star_View"}
                            )
                            st.session_state.fi_star_view_checked = True
                except Exception as e:
                    # Do not block UI on view prep issues; detection will surface errors if present
                    import logging as _logging
                    _logging.info(f"[DecisionStudio] FI Star prep skipped: {str(e)}")
                
                return st.session_state.agent
            except Exception as e:
                st.error(f"Error initializing agent system: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
    else:
        return st.session_state.agent

# Get situation awareness agent
async def get_situation_awareness_agent():
    """Get the situation awareness agent.
    
    Returns:
        The situation awareness agent instance
    """
    return await initialize_agent()

# Get principal context using the orchestrator
async def get_principal_context(principal_id=None):
    """Get principal context for the selected principal ID using the orchestrator.
    
    Args:
        principal_id: The principal ID to get context for
        
    Returns:
        The principal context for the selected principal
    """
    # Initialize agents if needed
    await initialize_agent()
    
    # Use the orchestrator to communicate with the Principal Context Agent
    if principal_id is None:
        # Default to CFO if no ID provided
        principal_id = "cfo_001"
    
    # Create the request message
    request = {
        "principal_id": principal_id
    }
    
    # Send the request through the orchestrator
    response = await st.session_state.orchestrator.execute_agent_method(
        "A9_Principal_Context_Agent",
        "get_principal_context_by_id",
        request
    )
    
    return response

def extract_principal_context(principal_profile_response):
    """Extract PrincipalContext from a response object.
    
    This handles both cases where the response is a PrincipalProfileResponse with a context field,
    or a PrincipalProfileResponse with only a profile field.
    """
    
    # Check if the response already has a context attribute
    if hasattr(principal_profile_response, 'context') and principal_profile_response.context is not None:
        return principal_profile_response.context
    
    # Check if it's a PrincipalProfileResponse with profile attribute
    elif hasattr(principal_profile_response, 'profile') and principal_profile_response.profile is not None:
        # Extract profile data
        profile = principal_profile_response.profile
        
        # Get role string
        role_str = profile.get('role', 'CFO')
        
        # Ensure we have a principal ID
        principal_id = profile.get('id', f"{role_str.lower()}_default")
        
        # Extract timeframes from profile
        timeframes = []
        for tf in profile.get('timeframes', ['Quarterly']):
            try:
                timeframes.append(TimeFrame(tf))
            except ValueError:
                # Default to current quarter
                timeframes.append(TimeFrame.CURRENT_QUARTER)
        
        # Ensure we have at least one timeframe
        if not timeframes:
            timeframes = [TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
        
        # Create principal context object with string-based business processes
        bp_list = profile.get('business_processes', ["Finance"]) or ["Finance"]
        return PrincipalContext(
            role=role_str,
            principal_id=principal_id,
            business_processes=[str(bp) for bp in bp_list],
            default_filters=profile.get('default_filters', {}),
            decision_style=profile.get('decision_style', 'Analytical'),
            communication_style=profile.get('communication_style', 'Concise'),
            preferred_timeframes=timeframes
        )
    
    # If it's already a PrincipalContext object
    elif hasattr(principal_profile_response, 'role') and hasattr(principal_profile_response, 'principal_id'):
        return principal_profile_response
    
    # Default case - should not happen but provides a fallback
    else:
        return PrincipalContext(
            role="CFO",
            principal_id="default_cfo",
            business_processes=["Finance"],
            default_filters={},
            decision_style="Analytical",
            communication_style="Concise",
            preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
        )

# Detect situations based on current filters
async def detect_situations():
    """Detect situations based on current filters and update the UI."""
    # Ensure agents are initialized
    await initialize_agent()
    
    if st.session_state.orchestrator is None:
        return
    
    # Ensure principal profiles are loaded before proceeding
    if not st.session_state.get("profiles_loaded", False):
        import asyncio as _asyncio
        # Wait briefly for profiles to load (run_async should set this soon)
        for _ in range(15):  # up to ~1.5s
            if st.session_state.get("profiles_loaded", False):
                break
            await _asyncio.sleep(0.1)
    # Start diagnostics
    try:
        st.session_state.debug_trace.append("detect_situations: start")
    except Exception:
        pass

    # Prepare the situation detection request
    # Require a selected principal once profiles are loaded to avoid accidental defaults
    # Log current selection vs widget for diagnostics
    try:
        logging.info(f"[DecisionStudio] detect_situations using selected_principal_id={st.session_state.get('selected_principal_id')}, widget_principal_id={st.session_state.get('principal_id_select')}")
    except Exception:
        pass
    if "selected_principal_id" in st.session_state and st.session_state.selected_principal_id:
        principal_profile_response = await get_principal_context(principal_id=st.session_state.selected_principal_id)
    else:
        st.info("Principal profiles not loaded yet. Please wait a moment and click 'Detect Situations' again.")
        return
    
    # Extract the PrincipalContext object from the response (robust to dicts)
    # If dict with 'context', use it directly
    if isinstance(principal_profile_response, dict) and principal_profile_response.get('context') is not None:
        principal_context = principal_profile_response.get('context')
    # If object with attribute 'context'
    elif hasattr(principal_profile_response, 'context') and principal_profile_response.context is not None:
        principal_context = principal_profile_response.context
    # Else if dict with 'profile', construct from profile
    elif isinstance(principal_profile_response, dict) and principal_profile_response.get('profile') is not None:
        # Get the profile data
        profile_data = principal_profile_response.get('profile')
        
        # Create a PrincipalContext object from the profile data
        from src.agents.models.situation_awareness_models import PrincipalContext, TimeFrame
        
        # Get business processes from the profile
        business_processes = []
        for bp in profile_data.get('business_processes', []):
            # Use BusinessProcess objects from registry instead of enum
            if st.session_state.orchestrator:
                # Get business process from registry
                bp_obj = await st.session_state.orchestrator.execute_agent_method(
                    "A9_Principal_Context_Agent",
                    "get_business_process_by_name",
                    {"name": bp}
                )
                if bp_obj:
                    business_processes.append(bp_obj)
        
        # Create the principal context
        principal_context = PrincipalContext(
            role=profile_data.get('role', 'CFO'),
            principal_id=profile_data.get('id', 'cfo_001'),
            business_processes=profile_data.get('business_processes', ['Finance']),  # Use string-based business processes
            default_filters=profile_data.get('default_filters', {}),
            decision_style=profile_data.get('decision_style', 'Analytical'),
            communication_style=profile_data.get('communication_style', 'Concise'),
            preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
        )
    else:
        # Default context if we can't extract from response
        from src.agents.models.situation_awareness_models import PrincipalContext, TimeFrame
        principal_context = PrincipalContext(
            role="CFO",
            principal_id="cfo_001",
            business_processes=["Finance"],  # Use domain-level business processes
            default_filters={},
            decision_style="Analytical",
            communication_style="Concise",
            preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
        )
    
    # Convert to dict if needed for Pydantic validation
    if hasattr(principal_context, 'model_dump'):
        principal_context_dict = principal_context.model_dump()
    else:
        principal_context_dict = principal_context

    # Log the principal context for debugging
    import logging
    logging.info(f"Using principal context: {principal_context_dict}")

    # If principal changed, reset UI filters to the principal's default filters to prevent stale overrides
    try:
        current_pid = st.session_state.get("selected_principal_id") or st.session_state.default_principal_id
        prev_pid = st.session_state.get("prev_selected_principal_id")
        if current_pid != prev_pid:
            defaults = {}
            # Try to extract defaults from the richer response we already fetched above
            if isinstance(principal_profile_response, dict):
                ctx = principal_profile_response.get('context')
                if isinstance(ctx, dict):
                    defaults = ctx.get('default_filters', {}) or {}
                if not defaults:
                    prof = principal_profile_response.get('profile') or {}
                    if isinstance(prof, dict):
                        defaults = prof.get('default_filters', {}) or {}
            else:
                # Object with attributes
                try:
                    ctx = getattr(principal_profile_response, 'context', None)
                    if ctx is not None:
                        defaults = getattr(ctx, 'default_filters', {}) or {}
                    if not defaults:
                        prof = getattr(principal_profile_response, 'profile', None)
                        if isinstance(prof, dict):
                            defaults = prof.get('default_filters', {}) or {}
                except Exception:
                    defaults = {}

            # Assign defaults (DPA will ignore sentinel values like 'Total'/'#'/'all')
            st.session_state.filters = defaults or {}
            st.session_state.prev_selected_principal_id = current_pid
            logging.info(f"[DecisionStudio] Principal changed to {current_pid}; filters reset to defaults: {st.session_state.filters}")
    except Exception:
        pass

    # If user hasn't explicitly selected business processes, default to those from the principal context
    try:
        if not st.session_state.business_processes:
            # Ensure list of strings
            pc_bps = []
            if isinstance(principal_context, dict):
                pc_bps = principal_context.get('business_processes', []) or []
            else:
                pc_bps = getattr(principal_context, 'business_processes', []) or []
            st.session_state.business_processes = [str(bp) for bp in pc_bps] if pc_bps else st.session_state.business_processes
    except Exception:
        pass

    # Create situation detection request
    request = SituationDetectionRequest(
        request_id=str(uuid.uuid4()),
        principal_context=principal_context_dict,
        business_processes=st.session_state.business_processes,  # Already string-based from our updates
        timeframe=st.session_state.timeframe,
        comparison_type=st.session_state.comparison_type,
        filters=st.session_state.filters
    )
    
    import asyncio as _asyncio
    st.session_state.detect_in_progress = True
    st.session_state.detect_status = "running"
    try:
        st.session_state.debug_trace.append("detect_situations: start")
    except Exception:
        pass
    try:
        with st.spinner("Detecting situations..."):
            # Check if data products are available first
            orchestrator = st.session_state.orchestrator
            # Use the orchestrator to check data products
            dp_response = await _asyncio.wait_for(
                orchestrator.execute_agent_method(
                    "A9_Data_Product_Agent",
                    "list_data_products",
                    {}
                ),
                timeout=12
            )
            # Call SA to detect situations
            response = await _asyncio.wait_for(
                st.session_state.orchestrator.execute_agent_method(
                    "A9_Situation_Awareness_Agent",
                    "detect_situations",
                    {"request": request.model_dump() if hasattr(request, 'model_dump') else request}
                ),
                timeout=20
            )
            try:
                st.session_state.debug_trace.append("detect_situations: orchestrator returned")
            except Exception:
                pass

        # Generate per-KPI SQL on demand
        try:
            if st.session_state.get("trigger_per_kpi_sql"):
                results = []
                situations = st.session_state.get("situations", []) or []
                if situations and st.session_state.orchestrator:
                    # Fetch KPI definitions once so we can request comparison SQL from Data Product Agent
                    kpi_defs_by_name = {}
                    try:
                        kpi_defs_resp = await st.session_state.orchestrator.execute_agent_method(
                            "A9_Situation_Awareness_Agent",
                            "get_kpi_definitions",
                            {"principal_context": principal_context_dict}
                        )
                        if isinstance(kpi_defs_resp, dict):
                            kpi_defs_by_name = kpi_defs_resp
                    except Exception:
                        kpi_defs_by_name = {}

                    for s in situations:
                        # Normalize KPI name from dict or model
                        try:
                            kpi_name = s.get('kpi_name') if isinstance(s, dict) else getattr(s, 'kpi_name', '')
                        except Exception:
                            kpi_name = ''
                        if not kpi_name:
                            continue
                        # Resolve KPI definition (from SA-provided defs) to avoid SA registry dependency
                        kpi_def = None
                        try:
                            if isinstance(kpi_defs_by_name, dict):
                                # exact match first
                                kpi_def = kpi_defs_by_name.get(kpi_name)
                                if not kpi_def:
                                    # case-insensitive fallback
                                    kn = (kpi_name or "").strip().lower()
                                    for n, kd in kpi_defs_by_name.items():
                                        try:
                                            if str(n).strip().lower() == kn:
                                                kpi_def = kd
                                                break
                                        except Exception:
                                            continue
                        except Exception:
                            kpi_def = None
                        base_sql_val = ""
                        comp_sql_val = ""
                        error_msg = None
                        try:
                            # Base SQL via SA delegator (keeps architecture clean)
                            try:
                                logging.info(f"[DecisionStudio] Requesting base SQL via SA for KPI='{kpi_name}', timeframe={st.session_state.get('timeframe')}")
                            except Exception:
                                pass
                            sql_text = await st.session_state.orchestrator.execute_agent_method(
                                "A9_Situation_Awareness_Agent",
                                "_get_sql_for_kpi",
                                {
                                    "kpi": (kpi_def or kpi_name),
                                    # Pass only explicit UI filters; SA will merge principal defaults
                                    "filters": st.session_state.get("filters", {}) or {},
                                    "principal_context": principal_context_dict,
                                    "timeframe": st.session_state.get("timeframe")
                                }
                            )
                            if isinstance(sql_text, dict) and 'sql' in sql_text:
                                base_sql_val = sql_text.get('sql') or ""
                            else:
                                base_sql_val = sql_text or ""
                            try:
                                logging.info(f"[DecisionStudio] Base SQL received for KPI='{kpi_name}', length={len(base_sql_val or '')}")
                            except Exception:
                                pass
                        except Exception as e:
                            error_msg = str(e)

                        # Comparison SQL via Situation Awareness Agent delegator (preferred)
                        try:
                            try:
                                logging.info(f"[DecisionStudio] Requesting comparison SQL via SA for KPI='{kpi_name}', comparison_type={st.session_state.get('comparison_type')}, timeframe={st.session_state.get('timeframe')}")
                            except Exception:
                                pass
                            comp_sql_resp = await st.session_state.orchestrator.execute_agent_method(
                                "A9_Situation_Awareness_Agent",
                                "_get_comparison_sql_for_kpi",
                                {
                                    "kpi": (kpi_def or kpi_name),
                                    "comparison_type": st.session_state.get("comparison_type"),
                                    # Pass only explicit UI filters; SA will merge principal defaults
                                    "filters": st.session_state.get("filters", {}) or {},
                                    "principal_context": principal_context_dict,
                                    "timeframe": st.session_state.get("timeframe")
                                }
                            )
                            if isinstance(comp_sql_resp, dict) and 'sql' in comp_sql_resp:
                                comp_sql_val = comp_sql_resp.get('sql') or ""
                            elif isinstance(comp_sql_resp, str):
                                comp_sql_val = comp_sql_resp or ""
                            try:
                                logging.info(f"[DecisionStudio] Comparison SQL via SA received for KPI='{kpi_name}', length={len(comp_sql_val or '')}")
                            except Exception:
                                pass
                        except Exception as e:
                            if not error_msg:
                                error_msg = str(e)

                        # No fallback: rely solely on SA path which caches the exact SQL used during execution

                        rec = {"kpi_name": kpi_name, "sql": base_sql_val}
                        if comp_sql_val:
                            rec["comparison_sql"] = comp_sql_val
                        if error_msg:
                            rec["error"] = error_msg
                        results.append(rec)
                st.session_state.per_kpi_sql_results = results
                st.session_state.trigger_per_kpi_sql = False
        except Exception:
            # Non-fatal; UI will show no SQL
            pass
            logging.info("[DecisionStudio] SA.detect_situations returned")

        # Normalize response across dict and Pydantic (v1/v2) objects
        if isinstance(response, dict):
            resp = response
        elif hasattr(response, 'model_dump'):
            # Pydantic v2
            resp = response.model_dump()
        elif hasattr(response, 'dict'):
            # Pydantic v1
            try:
                resp = response.dict()
            except Exception:
                # Best-effort fallback if dict() is restricted
                resp = {
                    'status': getattr(response, 'status', None),
                    'situations': getattr(response, 'situations', []),
                    'message': getattr(response, 'message', '')
                }
        else:
            # Generic object fallback
            resp = {
                'status': getattr(response, 'status', None),
                'situations': getattr(response, 'situations', []),
                'message': getattr(response, 'message', '')
            }

        # Update session state
        if resp.get('status') == "success":
            st.session_state.situations = resp.get('situations', [])
            st.success(f"Detected {len(st.session_state.situations)} situations")
            # Request a UI rerun so that the main panel reflects the new situations immediately
            try:
                st.session_state.post_detect_rerun = True
                st.session_state.detect_status = "done"
            except Exception:
                pass

            # DEBUG: Fetch Data Governance mappings for detected KPIs
            try:
                if st.session_state.debug_mode and st.session_state.situations:
                    # Collect KPI names
                    kpi_names = []
                    for s in st.session_state.situations:
                        try:
                            name = s.get('kpi_name') if isinstance(s, dict) else getattr(s, 'kpi_name', None)
                            if name:
                                kpi_names.append(name)
                        except Exception:
                            continue
                    kpi_names = list(sorted(set(kpi_names)))
                    if kpi_names:
                        # Build mapping request with context
                        pc_resp = await get_principal_context(
                            principal_id=st.session_state.selected_principal_id if st.session_state.get("selected_principal_id") else st.session_state.default_principal_id
                        )
                        principal_context_dbg = extract_principal_context(pc_resp)
                        mp_req = KPIDataProductMappingRequest(
                            kpi_names=kpi_names,
                            context={
                                "principal_id": principal_context_dbg.principal_id,
                                "business_processes": st.session_state.business_processes
                            }
                        )
                        mp_resp = await st.session_state.orchestrator.execute_agent_method(
                            "A9_Data_Governance_Agent",
                            "map_kpis_to_data_products",
                            {"request": mp_req}
                        )

                        # Normalize mappings
                        mappings = []
                        raw_mappings = []
                        if isinstance(mp_resp, dict) and 'mappings' in mp_resp:
                            raw_mappings = mp_resp['mappings']
                        elif hasattr(mp_resp, 'mappings'):
                            raw_mappings = mp_resp.mappings

                        # For each mapped KPI, also fetch view name
                        mapping_rows = []
                        for m in raw_mappings:
                            m_kpi = m.get('kpi_name') if isinstance(m, dict) else getattr(m, 'kpi_name', '')
                            m_dp = m.get('data_product_id') if isinstance(m, dict) else getattr(m, 'data_product_id', '')
                            # Ask DG for view name for the KPI
                            try:
                                v_req = KPIViewNameRequest(kpi_name=m_kpi)
                                v_resp = await st.session_state.orchestrator.execute_agent_method(
                                    "A9_Data_Governance_Agent",
                                    "get_view_name_for_kpi",
                                    {"request": v_req}
                                )
                                if isinstance(v_resp, dict):
                                    view_name = v_resp.get('view_name', '')
                                else:
                                    view_name = getattr(v_resp, 'view_name', '')
                            except Exception:
                                view_name = ''
                            mapping_rows.append({
                                "KPI": m_kpi,
                                "Data Product": m_dp,
                                "View": view_name
                            })
                        st.session_state.dg_kpi_mappings = mapping_rows
            except Exception as dbg_err:
                logging.info(f"[DecisionStudio] DG mapping debug skipped: {dbg_err}")
        # Persist last detection summary with optional KPI evaluated fields
        last_summary = {"status": "success", "count": len(st.session_state.situations)}
        try:
            if isinstance(resp, dict):
                if 'kpi_evaluated_count' in resp:
                    last_summary['kpi_evaluated_count'] = resp.get('kpi_evaluated_count')
                if 'kpis_evaluated' in resp:
                    last_summary['kpis_evaluated'] = resp.get('kpis_evaluated')
                if 'sql_query' in resp:
                    last_summary['sql_query'] = resp.get('sql_query')
        except Exception:
            pass
        st.session_state.last_detect_result = last_summary
    except _asyncio.TimeoutError:
        st.error("Timeout while detecting situations. Please try again.")
        try:
            st.session_state.debug_trace.append("detect_situations: timeout")
            st.session_state.last_detect_result = {"status": "timeout"}
            st.session_state.detect_status = "error"
        except Exception:
            pass
    except Exception as e:
        st.error(f"Error detecting situations: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        try:
            st.session_state.debug_trace.append(f"detect_situations: exception {str(e)}")
            st.session_state.last_detect_result = {"status": "exception", "error": str(e)}
            st.session_state.detect_status = "error"
        except Exception:
            pass
    finally:
        st.session_state.detect_in_progress = False
        if st.session_state.get("detect_status") == "running":
            st.session_state.detect_status = "done"

# Process natural language query
async def process_query():
    """Process the natural language query and update the UI."""
    agent = st.session_state.agent
    if agent is None or not st.session_state.nl_query:
        return
    
    # Get principal context
    if "selected_principal_id" in st.session_state and st.session_state.selected_principal_id:
        pc_resp = await get_principal_context(principal_id=st.session_state.selected_principal_id)
    else:
        pc_resp = await get_principal_context(principal_id="cfo_001")
    # Normalize into PrincipalContext model
    principal_context = extract_principal_context(pc_resp)
    
    # Create NL query request
    request = NLQueryRequest(
        request_id=st.session_state.nl_query,
        query=st.session_state.nl_query,
        principal_context=principal_context,
        # Extra fields are allowed and used downstream by the agent
        business_processes=st.session_state.business_processes,  # Already string-based from our updates
        timeframe=st.session_state.timeframe,
        comparison_type=st.session_state.comparison_type,
        filters=st.session_state.filters
    )
    
    with st.spinner("Processing query..."):
        try:
            # Check if data products are available first
            orchestrator = st.session_state.orchestrator
            
            # Use the orchestrator to check data products
            dp_response = await orchestrator.execute_agent_method(
                "A9_Data_Product_Agent",
                "list_data_products",
                {}
            )
            
            # Check if we have data products (normalize dict / Pydantic)
            if isinstance(dp_response, dict):
                data_products = dp_response.get('data_products', [])
            elif hasattr(dp_response, 'model_dump'):
                data_products = dp_response.model_dump().get('data_products', [])
            elif hasattr(dp_response, 'dict'):
                try:
                    data_products = dp_response.dict().get('data_products', [])
                except Exception:
                    data_products = getattr(dp_response, 'data_products', []) or []
            else:
                data_products = getattr(dp_response, 'data_products', []) or []
            if not data_products:
                st.warning("No data products found in the registry. Using demo data for query processing.")
                # Continue with query processing using demo data instead of returning early
                
            # Call the Situation Awareness Agent through the orchestrator
            request_data = request.model_dump() if hasattr(request, 'model_dump') else request
            response = await orchestrator.execute_agent_method(
                "A9_Situation_Awareness_Agent",
                "process_nl_query",
                {"request": request_data}
            )
            
            # Update session state
            from src.agents.models.situation_awareness_models import NLQueryResponse
            # Convert dict response to NLQueryResponse if needed
            if isinstance(response, dict):
                nl_response = NLQueryResponse(
                    request_id=response.get('request_id', request.request_id),
                    status=response.get('status', 'error'),
                    answer=response.get('answer', 'No response from agent'),
                    kpi_values=response.get('kpi_values', []),
                    sql_query=response.get('sql_query', ''),
                    recommended_questions=response.get('recommended_questions', [])
                )
                st.session_state.nl_response = nl_response
            else:
                st.session_state.nl_response = response

            # If this NL query was initiated from a follow-up within a situation, store a sid-scoped copy
            try:
                sid = st.session_state.get("current_followup_sid")
                if sid:
                    st.session_state[f"{sid}_nl_response"] = st.session_state.nl_response
                    # Clear the pointer so subsequent main NL queries don't get misattributed
                    st.session_state.current_followup_sid = None
                # Debug trace for diagnostics
                try:
                    _sql_len = len(getattr(st.session_state.nl_response, 'sql_query', '') or '')
                    st.session_state.debug_trace.append(f"process_query: response received (sql_len={_sql_len}, sid={sid})")
                except Exception:
                    pass
            except Exception:
                pass
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
            import traceback
            st.error(traceback.format_exc())

# Apply recommended question
def apply_question(question: str):
    """Apply a recommended question as the natural language query."""
    st.session_state.nl_query = question
    # Trigger processing on next async cycle
    st.session_state.trigger_query = True

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
        
        # Ensure principal profile containers exist without wiping any pre-seeded values
        if "principal_profiles" not in st.session_state:
            st.session_state.principal_profiles = {}
        if "principal_ids" not in st.session_state:
            st.session_state.principal_ids = [st.session_state.default_principal_id]
        if "principal_id_to_role" not in st.session_state:
            st.session_state.principal_id_to_role = {}
        if "principal_id_to_name" not in st.session_state:
            st.session_state.principal_id_to_name = {st.session_state.default_principal_id: "Chief Financial Officer (CFO)"}
        # Synchronous preload of principal profiles from YAML for immediate selector population
        try:
            if st.session_state.principal_ids == [st.session_state.default_principal_id]:
                import yaml as _yaml
                _ppath = os.path.join(project_root, "src", "registry", "principal", "principal_registry.yaml")
                if os.path.exists(_ppath):
                    with open(_ppath, "r", encoding="utf-8") as _f:
                        _pdata = _yaml.safe_load(_f) or {}
                    _plist = _pdata.get("principal_profiles") or _pdata.get("profiles") or []
                    p_ids = []
                    p_id_to_name = {}
                    p_id_to_role = {}
                    for p in _plist:
                        try:
                            if isinstance(p, dict):
                                pid = p.get("id") or p.get("principal_id")
                                name = p.get("name") or p.get("display_name") or pid
                                role = p.get("role") or p.get("title") or name
                                if pid:
                                    p_ids.append(pid)
                                    p_id_to_name[pid] = f"{name} ({role})" if name and role else (name or pid)
                                    p_id_to_role[pid] = role
                        except Exception:
                            continue
                    if p_ids:
                        st.session_state.principal_ids = p_ids
                        st.session_state.principal_id_to_name.update(p_id_to_name)
                        st.session_state.principal_id_to_role.update(p_id_to_role)
                        # Keep current selection if still valid, else choose CFO if available, else first
                        cur = st.session_state.get("selected_principal_id", st.session_state.default_principal_id)
                        if cur not in p_ids:
                            preferred = None
                            try:
                                if "cfo_001" in p_ids:
                                    preferred = "cfo_001"
                                else:
                                    # Try resolve by role name mapping
                                    preferred = next((pid for pid, role in p_id_to_role.items() if str(role).strip().lower() in ("cfo", "chief financial officer")), None)
                            except Exception:
                                preferred = None
                            chosen = preferred or p_ids[0]
                            st.session_state.selected_principal_id = chosen
                            logging.info(f"[DecisionStudio] Principal selection fallback: cur='{cur}' not in list; set to '{chosen}'")
        except Exception:
            pass
        
        # Show principal selector immediately; upgrade options once profiles load
        options = st.session_state.principal_ids if st.session_state.principal_ids else [st.session_state.default_principal_id]
        default_id = st.session_state.get("selected_principal_id", st.session_state.default_principal_id)
        safe_index = options.index(default_id) if (default_id in options) else 0
        principal_id = st.selectbox(
            "Select Principal",
            options=options,
            index=safe_index,
            format_func=lambda x: st.session_state.principal_id_to_name.get(x, x),
            key="principal_id_select"
        )
        # Store the selected ID
        st.session_state.selected_principal_id = principal_id
        
        # Business process selector
        st.header("Business Processes")
        
        # Get business processes from registry instead of enum
        if "business_process_options" not in st.session_state:
            st.session_state.business_process_options = [
                "Finance: Profitability Analysis",
                "Finance: Revenue Growth Analysis",
                "Finance: Expense Management",
                "Finance: Cash Flow Management",
                "Finance: Budget vs. Actuals",
                "Finance: Investor Relations Reporting",
                "Strategy: Market Share Analysis",
                "Strategy: EBITDA Growth Tracking",
                "Strategy: Capital Allocation Efficiency",
                "Operations: Order-to-Cash Cycle Optimization",
                "Operations: Inventory Turnover Analysis",
                "Operations: Production Cost Management",
                "Operations: Global Performance Oversight",
                "Supply Chain: Logistics Efficiency"
            ]
        
        # Try to get business processes from registry if orchestrator is available
        if st.session_state.orchestrator:
            try:
                # This will be populated in the async section
                pass
            except Exception as e:
                st.warning(f"Error loading business processes: {str(e)}")
        
        # Use specific business processes for selection
        selected_processes = st.multiselect(
            "Select Business Processes",
            options=st.session_state.business_process_options,
            default=st.session_state.business_processes if isinstance(st.session_state.business_processes[0], str) 
                   and any(":" in bp for bp in st.session_state.business_processes)
                   else ["Finance: Profitability Analysis"],
            key="business_processes_select"
        )
        # Normalize to sorted unique list for stable comparison
        new_bps = sorted(list(set(selected_processes)))
        old_bps = sorted(list(set(st.session_state.business_processes))) if isinstance(st.session_state.business_processes, list) else []
        st.session_state.business_processes = new_bps
        if new_bps != old_bps:
            # Auto-trigger detection on BP change
            st.session_state.trigger_detect = True
            st.session_state.detect_status = "queued"
            st.toast("Business Processes changed — detecting situations...", icon="🔄")
        
        # Timeframe selector
        st.header("Time Frame")
        timeframe = st.selectbox(
            "Select Time Frame",
            options=[tf.value for tf in TimeFrame],
            index=list(TimeFrame).index(st.session_state.timeframe),
            format_func=lambda x: x.replace("_", " ").title(),
            key="timeframe_select"
        )
        new_tf = TimeFrame(timeframe)
        old_tf = st.session_state.timeframe
        st.session_state.timeframe = new_tf
        if new_tf != old_tf:
            # Auto-trigger detection on timeframe change
            st.session_state.trigger_detect = True
            st.session_state.detect_status = "queued"
            st.session_state.prev_timeframe = new_tf
            st.toast("Timeframe changed — detecting situations...", icon="⏱️")
        
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
        if debug_mode:
            st.subheader("Registry & Profiles Debug")
            # Show what the UI currently sees
            profiles = st.session_state.get("principal_profiles", {})
            principal_ids = st.session_state.get("principal_ids", [])
            st.markdown(f"Profiles loaded (UI): **{len(profiles)}**")
            if principal_ids:
                preview_ids = principal_ids[:10]
                st.write({"ids_preview": preview_ids})
            debug_info = st.session_state.get("debug_info")
            if debug_info:
                st.json(debug_info)
            else:
                st.info("Debug info not populated yet. Click 'Detect Situations' or interact with the app to trigger loading.")
        
        # Run situation detection (always enabled; uses selected principal context at runtime)
        detect_disabled = False
        if st.button("Detect Situations", disabled=detect_disabled):
            # Set a flag to trigger detection in the async section
            st.session_state.trigger_detect = True
            logging.info("[DecisionStudio UI] Detect button clicked; trigger_detect=True")
            # Update unified status and flags immediately for consistent UI
            st.session_state.detect_status = "queued"
            st.session_state.detect_in_progress = True
            try:
                st.session_state.debug_trace.append("ui: detect requested")
            except Exception:
                pass
            st.info("Detection requested. Running in background...")
        # No extra caption; button is always available
    
    # Main content area
    st.title("Finance KPI Situation Awareness")
    
    # Display information about the principal
    if "selected_principal_id" in st.session_state and st.session_state.selected_principal_id:
        principal_name = st.session_state.principal_id_to_name.get(st.session_state.selected_principal_id, st.session_state.selected_principal_id)
        st.header(f"Principal: {principal_name}")
    else:
        st.header("Principal: CFO")
    
    # Display detected situations
    st.header("Detected Situations")
    
    if st.session_state.situations:
        # Optional summary from SA: number of KPIs evaluated and list
        if isinstance(st.session_state.get("last_detect_result"), dict):
            ldr = st.session_state.get("last_detect_result")
            evaluated_count = ldr.get("kpi_evaluated_count")
            evaluated_list = ldr.get("kpis_evaluated")
            if evaluated_count is not None:
                st.caption(f"KPIs evaluated: {evaluated_count}")
            if evaluated_list:
                with st.expander("Show evaluated KPIs"):
                    try:
                        st.write("\n".join(f"- {name}" for name in evaluated_list))
                    except Exception:
                        st.write(evaluated_list)
            # Show current timeframe and comparison context
            try:
                tf = st.session_state.timeframe
                ct = st.session_state.comparison_type
                tf_label = tf.value.replace('_', ' ').title() if hasattr(tf, 'value') else str(tf)
                ct_label = ct.value.replace('_', ' ').title() if hasattr(ct, 'value') else str(ct)
                st.caption(f"Timeframe: {tf_label} • Comparison: {ct_label}")
            except Exception:
                pass

        # Optional: Toggle to show SQL in KPI Details panel
        st.session_state.show_per_kpi_sql = st.checkbox("Show SQL in KPI Details (debug)", value=st.session_state.show_per_kpi_sql)
        # If enabled and no cached SQL results yet, trigger async generation
        try:
            # removed stray placeholder introduced during previous edit
            if st.session_state.show_per_kpi_sql:
                _has_results = bool(st.session_state.get("per_kpi_sql_results"))
                if not _has_results:
                    st.session_state.trigger_per_kpi_sql = True
                    st.toast("Generating per-KPI SQL for details...", icon="🧩")
        except Exception:
            pass
        # Group situations by severity (support both dict and Pydantic objects)
        severity_groups = {}
        for situation in st.session_state.situations:
            try:
                sev = situation.get('severity') if isinstance(situation, dict) else getattr(situation, 'severity', None)
                # Normalize severity to enum
                if isinstance(sev, str):
                    try:
                        sev_enum = SituationSeverity(sev)
                    except Exception:
                        sev_enum = SituationSeverity.INFORMATION
                else:
                    sev_enum = sev or SituationSeverity.INFORMATION
                if sev_enum not in severity_groups:
                    severity_groups[sev_enum] = []
                severity_groups[sev_enum].append(situation)
            except Exception:
                # Fallback bucket
                severity_groups.setdefault(SituationSeverity.INFORMATION, []).append(situation)
        
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

    # Debug panel: Data Governance KPI → Data Product / View mapping
    if st.session_state.get("debug_mode") and st.session_state.get("dg_kpi_mappings"):
        st.subheader("Data Governance Mappings (KPI → Data Product/View)")
        try:
            st.table(st.session_state.dg_kpi_mappings)
        except Exception:
            # Fallback simple rendering
            for row in st.session_state.dg_kpi_mappings:
                st.write(f"- {row.get('KPI')}: {row.get('Data Product')} / {row.get('View')}")
    
    # Debug panel: Diagnostics Trace
    if st.session_state.get("debug_mode"):
        st.subheader("Diagnostics Trace")
        trace = st.session_state.get("debug_trace", [])
        if trace:
            try:
                st.code("\n".join(trace), language="text")
            except Exception:
                st.write("\n".join(trace))
        else:
            st.caption("No trace entries yet.")
        # Last detection result snapshot
        last = st.session_state.get("last_detect_result")
        if last:
            st.subheader("Last Detection Result Snapshot")
            try:
                st.json(last)
            except Exception:
                st.write(last)
        # State HUD for flags
        st.subheader("State HUD")
        hud = {
            "profiles_loaded": st.session_state.get("profiles_loaded"),
            "trigger_detect": st.session_state.get("trigger_detect"),
            "detect_in_progress": st.session_state.get("detect_in_progress"),
            "fi_star_view_checked": st.session_state.get("fi_star_view_checked"),
            "selected_principal_id": st.session_state.get("selected_principal_id"),
        }
        try:
            st.json(hud)
        except Exception:
            st.write(hud)
        # Unified Detection Status panel
        st.subheader("Detection Status")
        ds = st.session_state.get("detect_status", "idle")
        dip = st.session_state.get("detect_in_progress", False)
        if ds == "queued":
            st.info("Detection requested. Waiting to start...")
        elif ds == "running" or dip:
            st.info("Detecting situations...")
        elif ds == "done":
            st.success("Detection completed.")
        elif ds == "error":
            st.error("Detection failed or timed out. See Diagnostics Trace for details.")
        else:
            st.caption("Idle")
    
    # Natural language query section (temporarily disabled by default)
    if st.session_state.get("enable_nl_ui", False):
        st.header("Ask a Question")
        with st.container():
            st.session_state.nl_query = st.text_input(
                "Enter your question",
                value=st.session_state.nl_query
            )
            if st.button("Submit Question"):
                # Set a flag to trigger NL query processing in the async section
                st.session_state.trigger_query = True
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
    """Display a situation card in the UI (supports dict or Pydantic model)."""
    def _get(obj, name, default=None):
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    # Top-level fields
    desc = _get(situation, 'description', 'Situation detected')
    kpi_name = _get(situation, 'kpi_name', '')
    kpi_value_obj = _get(situation, 'kpi_value', {})
    timestamp = _get(situation, 'timestamp', None)
    business_impact = _get(situation, 'business_impact', '')
    suggested_actions = _get(situation, 'suggested_actions', []) or []
    diagnostic_questions = _get(situation, 'diagnostic_questions', []) or []

    # Nested KPI value fields
    def _kv_get(name, default=None):
        if isinstance(kpi_value_obj, dict):
            return kpi_value_obj.get(name, default)
        return getattr(kpi_value_obj, name, default)

    val = _kv_get('value', None)
    comp_val = _kv_get('comparison_value', None)
    unit = _kv_get('unit', None)
    timeframe = _kv_get('timeframe', None)
    comp_type = _kv_get('comparison_type', None)

    with st.container():
        # Header block
        value_str = f"{val:,.2f}" if isinstance(val, (int, float)) else str(val)
        unit_str = f" {unit}" if unit else ""
        st.markdown(
            f"""
            <div class="situation-card {severity_class}">
                <h3>{desc}</h3>
                <p><strong>KPI:</strong> {kpi_name}</p>
                <p><strong>Value:</strong> {value_str}{unit_str}</p>
            """,
            unsafe_allow_html=True
        )

        # Comparison/variance line
        try:
            if comp_val is not None and isinstance(comp_val, (int, float)) and comp_val != 0:
                pct = (float(val) - float(comp_val)) / abs(float(comp_val)) * 100.0
                st.markdown(
                    f"""
                    <p><strong>Change:</strong> {pct:,.1f}% from {float(comp_val):,.2f}</p>
                    """,
                    unsafe_allow_html=True
                )
        except Exception:
            pass

        st.markdown("</div>", unsafe_allow_html=True)

        # Details panel with richer context
        with st.expander("Details"):
            if business_impact:
                st.write(f"**Business Impact:** {business_impact}")

            # Context attributes
            cols = st.columns(2)
            with cols[0]:
                if timeframe:
                    tf_label = timeframe.value if hasattr(timeframe, 'value') else str(timeframe)
                    st.write(f"**Timeframe:** {tf_label.replace('_', ' ').title()}")
                if comp_type:
                    ct_label = comp_type.value if hasattr(comp_type, 'value') else str(comp_type)
                    st.write(f"**Comparison:** {ct_label.replace('_', ' ').title()}")
            with cols[1]:
                if comp_val is not None:
                    try:
                        st.write(f"**Baseline:** {float(comp_val):,.2f}")
                    except Exception:
                        st.write(f"**Baseline:** {comp_val}")
                if timestamp:
                    st.write(f"**Detected:** {timestamp}")

            # Suggested actions
            if suggested_actions:
                st.subheader("Suggested Actions")
                for action in suggested_actions:
                    st.write(f"- {action}")

            # Diagnostic questions
            if diagnostic_questions:
                st.subheader("Diagnostic Questions")
                for question in diagnostic_questions:
                    # Ensure unique key even for dict situations
                    sid = _get(situation, 'situation_id', str(uuid.uuid4()))
                    if st.button(question, key=f"{sid}_{question[:20]}"):
                        apply_question(question)

            # Follow-up NL question (inline) – triggers SA.process_nl_query and shows generated SQL
            try:
                # Use a STABLE key so that reruns can find the stored results
                _sid = _get(situation, 'situation_id', None)
                if _sid:
                    local_sid = str(_sid)
                else:
                    # Derive from KPI name and description as a stable fallback
                    base_name = (kpi_name or '').strip().lower().replace(' ', '_')
                    desc_key = (desc or '').strip().lower().replace(' ', '_')[:50]
                    local_sid = f"sid_{base_name or 'kpi'}_{desc_key or 'desc'}"
                q_placeholder = f"Ask about {kpi_name} (e.g., Why did it change?)" if kpi_name else "Ask a follow-up question"
                followup_key = f"{local_sid}_followup_input"
                submit_key = f"{local_sid}_submit_followup"
                followup_text = st.text_input("Follow-up question", key=followup_key, placeholder=q_placeholder)
                if st.button("Ask", key=submit_key) and isinstance(followup_text, str) and followup_text.strip():
                    # Ensure NL UI processing is enabled and trigger query via existing handler
                    st.session_state.enable_nl_ui = True
                    # Remember which situation initiated this NL query so we can route the response
                    st.session_state.current_followup_sid = local_sid
                    st.session_state[f"{local_sid}_last_question"] = followup_text.strip()
                    apply_question(followup_text.strip())
                    st.toast("Processing your question...", icon="💬")

                # If we have a situation-scoped response, trust it and display directly; else fall back to request_id match
                sid_resp = st.session_state.get(f"{local_sid}_nl_response")
                nl_resp = sid_resp or st.session_state.get("nl_response")
                last_q = st.session_state.get(f"{local_sid}_last_question")
                matched = False
                if sid_resp and nl_resp:
                    matched = True
                    try:
                        st.session_state.debug_trace.append(f"display_situation: using sid-scoped NL response for {local_sid}")
                    except Exception:
                        pass
                else:
                    # Robust match: normalize whitespace/case for request_id vs last question
                    _rq = str(getattr(nl_resp, "request_id", "") or "").strip().lower() if nl_resp else ""
                    _lq = str(last_q or "").strip().lower() if last_q else ""
                    matched = bool(nl_resp and last_q and _rq == _lq)
                if matched and nl_resp:
                    st.subheader("Follow-up Answer")
                    try:
                        st.write(getattr(nl_resp, "answer", "") or "")
                    except Exception:
                        pass
                    sql_txt = getattr(nl_resp, "sql_query", "") or ""
                    if sql_txt:
                        st.markdown("**Generated SQL**")
                        try:
                            st.code(sql_txt, language='sql')
                        except Exception:
                            st.text(sql_txt)
                        # Allow user to execute the generated SQL and view results inline
                        run_key = f"{local_sid}_run_sql"
                        if st.button("Run SQL", key=run_key):
                            # Queue execution for async handler
                            st.session_state.nl_sql_to_run = {"sid": local_sid, "sql": sql_txt}
                            st.session_state.trigger_run_nl_sql = True
                            st.toast("Executing SQL...", icon="⏳")
                            try:
                                st.session_state.debug_trace.append(f"UI: queued NL SQL for {local_sid} (len={len(sql_txt)})")
                            except Exception:
                                pass
                            # Trigger a rerun so run_async picks up the queued execution immediately
                            try:
                                if hasattr(st, "rerun"):
                                    st.rerun()
                                elif hasattr(st, "experimental_rerun"):
                                    st.experimental_rerun()
                            except Exception:
                                pass
                        # If results are available for this situation, display them
                        res_key = f"{local_sid}_sql_result"
                        res_obj = st.session_state.get(res_key)
                        if isinstance(res_obj, dict):
                            rows = res_obj.get("rows", []) or []
                            cols = res_obj.get("columns", []) or []
                            success = res_obj.get("success", True)
                            msg = res_obj.get("message")
                            if rows:
                                st.markdown("**Results**")
                                try:
                                    # If rows are already list-of-dicts (records), display directly
                                    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                                        st.table(rows[:50])
                                    else:
                                        # Safely map row values to provided column names when available
                                        if cols:
                                            def _row_to_record(r):
                                                rec = {}
                                                for i, col in enumerate(cols):
                                                    if isinstance(r, (list, tuple)):
                                                        rec[str(col)] = r[i] if i < len(r) else None
                                                    elif isinstance(r, dict):
                                                        rec[str(col)] = r.get(col)
                                                    else:
                                                        # Fallback: single scalar or unknown structure
                                                        rec[str(col)] = r
                                                return rec
                                            formatted = [_row_to_record(r) for r in rows[:50]]
                                            st.table(formatted)
                                        else:
                                            st.table(rows[:50])
                                except Exception:
                                    st.write(rows[:50])
                            else:
                                # Show helpful status if no data
                                if success is False and msg:
                                    st.caption(f"SQL Error: {msg}")
                                elif msg:
                                    st.caption(msg)
            except Exception:
                pass

            # Optional: Show SQL for this KPI when enabled
            try:
                if st.session_state.get("show_per_kpi_sql"):
                    kname = kpi_name
                    sql_items = st.session_state.get("per_kpi_sql_results", []) or []
                    for item in sql_items:
                        if str(item.get("kpi_name")) == str(kname):
                            base_sql_text = item.get("sql")
                            comp_sql_text = item.get("comparison_sql")
                            err_text = item.get("error")
                            if base_sql_text or comp_sql_text or err_text:
                                st.subheader("SQL")
                            if base_sql_text:
                                st.markdown("**Base SQL**")
                                try:
                                    st.code(base_sql_text, language='sql')
                                except Exception:
                                    st.text(base_sql_text)
                            if comp_sql_text:
                                st.markdown("**Comparison SQL**")
                                try:
                                    st.code(comp_sql_text, language='sql')
                                except Exception:
                                    st.text(comp_sql_text)
                            if err_text and not (base_sql_text or comp_sql_text):
                                st.caption(f"SQL Error: {err_text}")
                            break
            except Exception:
                pass

# Run the async functions
async def run_async():
    """Run the async functions required for the app."""
    try:
        # Initialize agent
        agent = await initialize_agent()
        
        # Load principal profiles and business processes from registry
        if agent and st.session_state.orchestrator:
            try:
                # Get principal context agent
                pc_agent = await st.session_state.orchestrator.get_agent("A9_Principal_Context_Agent")
                if pc_agent:
                    # Get principal profiles and business processes from registry
                    # Use the canonical attribute name from the agent
                    registry_factory = getattr(pc_agent, "registry_factory", None)
                    if registry_factory:
                        # Get principal profiles
                        principal_provider = registry_factory.get_provider("principal_profile")
                        if principal_provider:
                            # Debug: log provider and profile count/types
                            try:
                                _profiles_dbg = principal_provider.get_all() or []
                                logging.info(f"[DecisionStudio] Principal provider available, count={len(_profiles_dbg)}")
                                if _profiles_dbg:
                                    first = _profiles_dbg[0]
                                    logging.info(f"[DecisionStudio] First profile type={type(first)}; repr={getattr(first,'id', getattr(first,'name', str(first)))})")
                            except Exception as _e:
                                logging.warning(f"[DecisionStudio] Error introspecting principal profiles: {_e}")
                            
                            # Also get business processes from registry
                            business_process_provider = registry_factory.get_provider("business_process")
                            if business_process_provider:
                                # Get all business processes
                                business_processes = business_process_provider.get_all()
                                
                                # Extract specific business processes
                                specific_processes = []
                                for bp in business_processes:
                                    if hasattr(bp, 'display_name') and bp.display_name:
                                        specific_processes.append(bp.display_name)
                                    elif hasattr(bp, 'id') and bp.id:
                                        specific_processes.append(bp.id)
                                
                                # Update business process options
                                if specific_processes:
                                    st.session_state.business_process_options = specific_processes
                            # Get all principal profiles
                            profiles = principal_provider.get_all()
                            logging.info(f"[DecisionStudio] Processing {len(profiles) if profiles else 0} principal profiles for selector")
                            
                            # Process profiles
                            principal_ids = []
                            principal_id_to_role = {}
                            principal_id_to_name = {}
                            principal_profiles = {}
                            
                            for profile in profiles:
                                # Support both model objects and dicts
                                if hasattr(profile, 'id') and hasattr(profile, 'name'):
                                    # PrincipalProfile model instance
                                    pid = getattr(profile, 'id')
                                    role = getattr(profile, 'title', None) or getattr(profile, 'name')
                                    name = getattr(profile, 'name')
                                    principal_ids.append(pid)
                                    principal_id_to_role[pid] = role
                                    principal_id_to_name[pid] = f"{name} ({role})"
                                    principal_profiles[pid] = profile.model_dump() if hasattr(profile, 'model_dump') else profile.__dict__
                                elif isinstance(profile, dict) and 'id' in profile:
                                    principal_id = profile['id']
                                    role = profile.get('role') or profile.get('title') or profile.get('name')
                                    principal_ids.append(principal_id)
                                    principal_id_to_role[principal_id] = role

                            # Persist loaded profiles and maps into session state for UI and gating
                            try:
                                if principal_ids:
                                    st.session_state.principal_ids = principal_ids
                                if principal_id_to_name:
                                    st.session_state.principal_id_to_name.update(principal_id_to_name)
                                if principal_id_to_role:
                                    st.session_state.principal_id_to_role.update(principal_id_to_role)
                                if principal_profiles:
                                    # Ensure container exists
                                    if "principal_profiles" not in st.session_state:
                                        st.session_state.principal_profiles = {}
                                    st.session_state.principal_profiles.update(principal_profiles)
                                # Signal that profiles are now available so detection can proceed
                                st.session_state.profiles_loaded = bool(principal_ids)
                            except Exception:
                                # Do not block on session updates
                                pass

                            # Set default principal selection if not already set
                            if "selected_principal_id" not in st.session_state and principal_ids:
                                # Find CFO profile if available
                                cfo_id = next((pid for pid, role in principal_id_to_role.items()
                                               if isinstance(role, str) and (role.lower() == 'chief financial officer' or role.lower() == 'cfo')), None)
                                if cfo_id:
                                    st.session_state.selected_principal_id = cfo_id
                                else:
                                    # Use first profile
                                    st.session_state.selected_principal_id = principal_ids[0]
                            # Prepare debug info for sidebar panel
                            try:
                                provider_status = registry_factory.provider_status() if hasattr(registry_factory, 'provider_status') else {}
                            except Exception:
                                provider_status = {}
                            st.session_state.debug_info = {
                                "provider_status": provider_status,
                                "profile_count": len(principal_ids),
                                "ids_preview": principal_ids[:10],
                                "names_preview": [st.session_state.principal_id_to_name.get(pid, pid) for pid in principal_ids[:5]]
                            }

                            # Force a rerun so the sidebar selector updates immediately (support old/new Streamlit)
                            # Only do this once to avoid infinite rerun loops
                            if not st.session_state.get("profiles_rerun_done", False):
                                # Mark rerun handled then trigger a one-time rerun to refresh selectors
                                st.session_state.profiles_rerun_done = True
                                try:
                                    import streamlit as _st
                                    if hasattr(_st, "rerun"):
                                        _st.rerun()
                                    elif hasattr(_st, "experimental_rerun"):
                                        _st.experimental_rerun()
                                except Exception:
                                    pass
                            
                            # Fetch recommended questions for the current principal
                            try:
                                import asyncio as _asyncio
                                # Get current principal context
                                pc_resp = await get_principal_context(
                                    principal_id=st.session_state.selected_principal_id
                                    if st.session_state.get("selected_principal_id") else st.session_state.default_principal_id
                                )
                                principal_context = extract_principal_context(pc_resp)
                                # Call SA agent for recommended questions
                                rq = await _asyncio.wait_for(
                                    st.session_state.orchestrator.execute_agent_method(
                                        "A9_Situation_Awareness_Agent",
                                        "get_recommended_questions",
                                        {"principal_context": principal_context}
                                    ),
                                    timeout=12
                                )
                                if isinstance(rq, dict) and rq.get("status") == "success" and "questions" in rq:
                                    st.session_state.recommended_questions = rq["questions"][:5]
                                elif isinstance(rq, list):
                                    st.session_state.recommended_questions = rq[:5]
                                else:
                                    # Keep whatever defaults we have
                                    pass
                            except Exception as rq_err:
                                logging.info(f"[DecisionStudio] Could not fetch recommended questions: {rq_err}")
            except Exception as e:
                st.error(f"Error loading principal profiles: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
        
        # Removed early detection trigger block to avoid pre-click spinners; detection is handled later with stricter gating
        
        # Handle NL query processing only when NL UI is enabled
        if st.session_state.get("enable_nl_ui", False):
            try:
                if st.session_state.get("trigger_query"):
                    st.session_state.trigger_query = False
                    await process_query()
                    # Mark NL ready to force a one-time rerun for inline display
                    try:
                        st.session_state._nl_ready = True
                    except Exception:
                        pass
            except Exception as e:
                st.error(f"Error during query processing: {str(e)}")
        else:
            # Ensure we don't accidentally process NL queries when disabled
            st.session_state.trigger_query = False
        
        # Execute any queued NL SQL (from Follow-up panels) and store results for inline display
        try:
            if st.session_state.get("trigger_run_nl_sql") and st.session_state.orchestrator:
                req = st.session_state.get("nl_sql_to_run")
                if isinstance(req, dict) and req.get("sql"):
                    raw_sql = req.get("sql")
                    # Sanitize: handle cases where LLM returned JSON with metadata
                    sql_to_run = raw_sql
                    try:
                        s = str(raw_sql or "").strip()
                        # Remove markdown fences if present
                        if s.startswith("```"):
                            # Strip the first fence line
                            s = s.split("\n", 1)[1] if "\n" in s else s.replace("```", "")
                        if s.endswith("```"):
                            s = s[: -3]
                        # Unescape common JSON-escaped sequences
                        s = s.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
                        s = s.replace("\\\"", '"')
                        s = s.replace("\\'", "'")
                        # Try JSON parse
                        if s.startswith("{") or s.startswith("["):
                            import json as _json
                            obj = _json.loads(s)
                            if isinstance(obj, dict):
                                sql_to_run = obj.get("sql_query") or obj.get("sql") or s
                            else:
                                sql_to_run = s
                        else:
                            # Truncate before known metadata markers if present
                            for marker in ['"confidence"', '"warnings"', '"explanation"', '\nconfidence', '\nwarnings', '\nexplanation']:
                                idx = s.find(marker)
                                if idx != -1:
                                    s = s[:idx]
                                    break
                            sql_to_run = s.strip()
                    except Exception:
                        sql_to_run = raw_sql

                    # Execute with a visible spinner and debug trace
                    try:
                        st.session_state.debug_trace.append("run_async: executing NL SQL via DP Agent")
                    except Exception:
                        pass
                    with st.spinner("Running SQL..."):
                        exec_resp = await st.session_state.orchestrator.execute_agent_method(
                            "A9_Data_Product_Agent",
                            "execute_sql",
                            {"sql_query": sql_to_run}
                        )
                    # Normalize exec_resp to a dict
                    if hasattr(exec_resp, "model_dump"):
                        exec_obj = exec_resp.model_dump()
                    elif isinstance(exec_resp, dict):
                        exec_obj = exec_resp
                    else:
                        exec_obj = {
                            "columns": getattr(exec_resp, "columns", []),
                            "rows": getattr(exec_resp, "rows", []),
                            "row_count": getattr(exec_resp, "row_count", 0)
                        }
                    sid = req.get("sid", "nl")
                    result_obj = {
                        "columns": exec_obj.get("columns", []),
                        "rows": exec_obj.get("rows", []),
                        "row_count": exec_obj.get("row_count", len(exec_obj.get("rows", []) or [])),
                        "success": exec_obj.get("success", True),
                        "message": exec_obj.get("message") or exec_obj.get("error")
                    }
                    st.session_state[f"{sid}_sql_result"] = result_obj
                    st.session_state.trigger_run_nl_sql = False
                    try:
                        st.session_state._nl_ready = True
                    except Exception:
                        pass
                    try:
                        import logging as _logging
                        _logging.info("[DecisionStudio] Executed NL SQL and updated session state with results")
                    except Exception:
                        pass
                    # User feedback toast
                    try:
                        rc = result_obj.get("row_count", 0)
                        if result_obj.get("success", True):
                            st.toast(f"SQL executed: {rc} rows", icon="✅")
                        else:
                            st.toast("SQL execution failed. See details below.", icon="⚠️")
                    except Exception:
                        pass
                    try:
                        st.session_state.debug_trace.append(f"run_async: NL SQL done (success={result_obj.get('success', True)}, rows={result_obj.get('row_count', 0)})")
                    except Exception:
                        pass
        except Exception as _nl_exec_err:
            try:
                import logging as _logging
                _logging.info(f"[DecisionStudio] NL SQL execution failed: {_nl_exec_err}")
            except Exception:
                pass
        
        # Ensure FI environment via Orchestrator (headless-compliant)
        try:
            if not st.session_state.fi_star_view_checked and st.session_state.orchestrator:
                import asyncio as _asyncio
                fi_contract_direct = os.path.join(project_root, "src", "contracts", "fi_star_schema.yaml")
                prep = await _asyncio.wait_for(
                    st.session_state.orchestrator.prepare_environment(
                        contract_path=fi_contract_direct,
                        view_name="FI_Star_View",
                        schema="main"
                    ),
                    timeout=45
                )
                logging.info(f"[DecisionStudio] Orchestrator.prepare_environment result: {prep}")
                st.session_state.fi_star_view_checked = True
        except Exception as _ensure_err:
            logging.info(f"[DecisionStudio] Skipped FI environment preparation: {_ensure_err}")
        
        # Fetch recommended questions only when NL UI is enabled
        if st.session_state.get("enable_nl_ui", False):
            try:
                if not st.session_state.recommended_questions and st.session_state.orchestrator:
                    import asyncio as _asyncio
                    pc_resp = await get_principal_context(
                        principal_id=st.session_state.selected_principal_id
                        if st.session_state.get("selected_principal_id") else st.session_state.default_principal_id
                    )
                    principal_context = extract_principal_context(pc_resp)
                    rq = await _asyncio.wait_for(
                        st.session_state.orchestrator.execute_agent_method(
                            "A9_Situation_Awareness_Agent",
                            "get_recommended_questions",
                            {"principal_context": principal_context}
                        ),
                        timeout=10
                    )
                    if isinstance(rq, dict) and rq.get("status") == "success" and "questions" in rq:
                        st.session_state.recommended_questions = rq["questions"][:5]
                    elif isinstance(rq, list):
                        st.session_state.recommended_questions = rq[:5]
            except Exception as _rq_err:
                logging.debug(f"[DecisionStudio] recommended questions not available yet: {_rq_err}")

        # Detect situations only when explicitly triggered (prevents auto-run loops)
        # Log gating state
        logging.info(
            f"[DecisionStudio] Gating state: agent_ready={bool(agent)}, profiles_loaded={st.session_state.get('profiles_loaded')}, trigger_detect={st.session_state.get('trigger_detect')}"
        )
        if agent and st.session_state.get("trigger_detect") and st.session_state.get("profiles_loaded", False):
            # reset the trigger before running to avoid re-entry loops
            st.session_state.trigger_detect = False
            try:
                st.session_state.debug_trace.append("run_async: invoking detect_situations")
            except Exception:
                pass
            await detect_situations()

        # Generate per-KPI SQL asynchronously when requested by UI
        if agent and st.session_state.get("trigger_per_kpi_sql") and st.session_state.get("profiles_loaded", False):
            # Reset trigger first to avoid re-entry
            st.session_state.trigger_per_kpi_sql = False
            try:
                st.session_state.debug_trace.append("run_async: generating per-kpi SQL")
            except Exception:
                pass
            try:
                # 1) Principal context
                pc_resp = await get_principal_context(
                    principal_id=st.session_state.selected_principal_id if st.session_state.get("selected_principal_id") else st.session_state.default_principal_id
                )
                principal_context = extract_principal_context(pc_resp)

                # 2) KPI definitions relevant to the principal
                kpi_defs_resp = await st.session_state.orchestrator.execute_agent_method(
                    "A9_Situation_Awareness_Agent",
                    "get_kpi_definitions",
                    {"principal_context": principal_context}
                )
                kpi_defs = {}
                if isinstance(kpi_defs_resp, dict):
                    kpi_defs = kpi_defs_resp
                elif hasattr(kpi_defs_resp, 'model_dump'):
                    kpi_defs = kpi_defs_resp.model_dump()

                # 3) Determine KPI names to generate SQL for
                eval_list = []
                ldr = st.session_state.get("last_detect_result")
                if isinstance(ldr, dict):
                    eval_list = ldr.get("kpis_evaluated") or []
                if not eval_list:
                    try:
                        eval_list = list({(s.get('kpi_name') if isinstance(s, dict) else getattr(s, 'kpi_name', None)) for s in st.session_state.get('situations', [])})
                    except Exception:
                        eval_list = []

                # 4) Merge filters (principal defaults + UI filters)
                merged_filters = {}
                try:
                    if hasattr(principal_context, 'default_filters') and isinstance(principal_context.default_filters, dict):
                        merged_filters.update(principal_context.default_filters)
                except Exception:
                    pass
                try:
                    if isinstance(st.session_state.get('filters'), dict):
                        merged_filters.update(st.session_state.filters)
                except Exception:
                    pass

                # 5) Generate per-KPI SQL via Data Product Agent (base + comparison)
                results = []
                for kpi_name in sorted([k for k in eval_list if k]):
                    kpi_def = None
                    if kpi_name in kpi_defs:
                        kpi_def = kpi_defs[kpi_name]
                    else:
                        try:
                            for v in (kpi_defs.values() if isinstance(kpi_defs, dict) else []):
                                try:
                                    name_v = v.get('name') if isinstance(v, dict) else getattr(v, 'name', None)
                                except Exception:
                                    name_v = None
                                if name_v == kpi_name:
                                    kpi_def = v
                                    break
                        except Exception:
                            pass
                    if not kpi_def:
                        results.append({"kpi_name": kpi_name, "sql": "", "error": "KPI definition not found"})
                        continue
                    try:
                        # Base SQL via Data Product Agent
                        resp_sql = await st.session_state.orchestrator.execute_agent_method(
                            "A9_Data_Product_Agent",
                            "generate_sql_for_kpi",
                            {
                                "kpi_definition": kpi_def,
                                "timeframe": st.session_state.timeframe,
                                "filters": merged_filters
                            }
                        )
                        base_sql = resp_sql.get('sql', '') if isinstance(resp_sql, dict) else ''

                        # Comparison SQL via Data Product Agent
                        comp_sql = ''
                        try:
                            comp_resp = await st.session_state.orchestrator.execute_agent_method(
                                "A9_Data_Product_Agent",
                                "generate_sql_for_kpi_comparison",
                                {
                                    "kpi_definition": kpi_def,
                                    "timeframe": st.session_state.timeframe,
                                    "comparison_type": st.session_state.get('comparison_type'),
                                    "filters": merged_filters
                                }
                            )
                            if isinstance(comp_resp, dict) and comp_resp.get('sql'):
                                comp_sql = comp_resp.get('sql') or ''
                        except Exception as _comp_err:
                            # Non-fatal for UI display
                            pass

                        # Assemble record for UI
                        if base_sql:
                            rec = {"kpi_name": kpi_name, "sql": base_sql}
                            if comp_sql:
                                rec["comparison_sql"] = comp_sql
                            results.append(rec)
                        else:
                            err_msg = resp_sql.get('message', 'Unknown error') if isinstance(resp_sql, dict) else 'Unknown error'
                            results.append({"kpi_name": kpi_name, "sql": "", "error": err_msg})
                    except Exception as gen_err:
                        results.append({"kpi_name": kpi_name, "sql": "", "error": str(gen_err)})

                st.session_state.per_kpi_sql_results = results
                st.toast("Per-KPI SQL ready.", icon="✅")
                # Mark ready so we can rerun once to display SQL without extra toggles
                try:
                    st.session_state._per_kpi_sql_ready = True
                except Exception:
                    pass
            except Exception as gen_all_err:
                st.session_state.per_kpi_sql_results = [{"kpi_name": "(all)", "sql": "", "error": str(gen_all_err)}]
                st.toast("Per-KPI SQL generation failed.", icon="⚠️")
        
        # Process natural language query if needed and enabled
        if st.session_state.get("enable_nl_ui", False):
            if st.session_state.nl_query and (
                not st.session_state.nl_response or 
                st.session_state.nl_response.request_id != st.session_state.nl_query
            ):
                await process_query()
    except Exception as e:
        st.error(f"Error in async operations: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Preserve orchestrator and agents across Streamlit reruns to keep
        # registry providers and principal profiles available for selectors.
        # Disconnection should be handled explicitly on app shutdown if needed.
        # If detection or per-KPI SQL just completed, trigger a one-time rerun
        try:
            import streamlit as _st
            if st.session_state.get("post_detect_rerun") or st.session_state.get("_per_kpi_sql_ready") or st.session_state.get("_nl_ready"):
                # reset flags before rerun to avoid loops
                st.session_state.post_detect_rerun = False
                st.session_state._per_kpi_sql_ready = False
                st.session_state._nl_ready = False
                if hasattr(_st, "rerun"):
                    _st.rerun()
                elif hasattr(_st, "experimental_rerun"):
                    _st.experimental_rerun()
        except Exception:
            pass

# Streamlit doesn't natively support asyncio, so we need to handle it
if __name__ == "__main__":
    main()
    
    # Use this to run async functions
    asyncio.run(run_async())
