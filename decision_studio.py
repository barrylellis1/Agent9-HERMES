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
    if "selected_principal_id" in st.session_state and st.session_state.selected_principal_id:
        principal_profile_response = await get_principal_context(principal_id=st.session_state.selected_principal_id)
    else:
        st.info("Principal profiles not loaded yet. Please wait a moment and click 'Detect Situations' again.")
        return
    
    # Extract the PrincipalContext object from the response
    # Check if the response has a context field
    if hasattr(principal_profile_response, 'context') and principal_profile_response.context is not None:
        principal_context = principal_profile_response.context
    # Check if it has a profile field
    elif hasattr(principal_profile_response, 'profile') and principal_profile_response.profile is not None:
        # Get the profile data
        profile_data = principal_profile_response.profile
        
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
        st.session_state.last_detect_result = {"status": "success", "count": len(st.session_state.situations)}
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
        
        # Get principal profiles from registry
        if "principal_profiles" not in st.session_state:
            # Initialize with empty dict, will be populated in async section
            st.session_state.principal_profiles = {}
            st.session_state.principal_ids = []
            st.session_state.principal_id_to_role = {}
            st.session_state.principal_id_to_name = {}
        
        # If we have profiles, use them for the dropdown
        if st.session_state.principal_profiles:
            # Use principal IDs for the dropdown
            options = st.session_state.principal_ids
            default_id = st.session_state.get("selected_principal_id")
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
        else:
            # Fallback to a simple dropdown with default CFO ID if profiles aren't loaded yet
            st.warning("Principal profiles not loaded yet. Using default CFO profile.")
            st.session_state.selected_principal_id = "cfo_001"
        
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
        st.session_state.business_processes = selected_processes
        
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
        
        # Run situation detection (disabled until profiles are loaded)
        detect_disabled = not st.session_state.get("profiles_loaded", False)
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
        if detect_disabled:
            st.caption("Loading principal profiles... the button will enable automatically.")
    
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
                                    name = profile.get('name', role)
                                    principal_id_to_name[principal_id] = f"{name} ({role})"
                                    principal_profiles[principal_id] = profile
                            
                            # Update session state
                            st.session_state.principal_profiles = principal_profiles
                            st.session_state.principal_ids = principal_ids
                            st.session_state.principal_id_to_role = principal_id_to_role
                            st.session_state.principal_id_to_name = principal_id_to_name
                            st.session_state.profiles_loaded = True
                            
                            # Set default selected ID if not already set
                            if not st.session_state.principal_ids:
                                st.warning("No principal profiles found in registry")
                            elif "selected_principal_id" not in st.session_state:
                                # Find CFO profile if available
                                cfo_id = next((pid for pid, role in principal_id_to_role.items() 
                                              if isinstance(role, str) and role.lower() == 'chief financial officer' or role.lower() == 'cfo'), None)
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
                                # Mark rerun handled, but avoid explicit rerun to prevent refresh loops
                                st.session_state.profiles_rerun_done = True
                            
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
            except Exception as e:
                st.error(f"Error during query processing: {str(e)}")
        else:
            # Ensure we don't accidentally process NL queries when disabled
            st.session_state.trigger_query = False
        
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
        pass

# Streamlit doesn't natively support asyncio, so we need to handle it
if __name__ == "__main__":
    main()
    
    # Use this to run async functions
    asyncio.run(run_async())
