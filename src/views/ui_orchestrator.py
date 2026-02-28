"""
UI Orchestrator Wrapper

This module provides a standards-compliant wrapper around the orchestrator
for the Decision Studio UI to use. It enforces proper orchestrator-driven
workflow and provides debugging capabilities.
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Import orchestrator
from src.agents.a9_orchestrator_agent import A9_Orchestrator_Agent, initialize_agent_registry

# Import models
from src.agents.models.situation_awareness_models import (
    PrincipalContext, 
    PrincipalRole,
    BusinessProcess,
    TimeFrame, 
    ComparisonType,
    SituationSeverity,
    SituationDetectionRequest,
    SituationDetectionResponse,
    NLQueryRequest,
    NLQueryResponse,
    HITLRequest,
    HITLResponse,
    Situation,
    KPIValue
)

# Import registry bootstrap
from src.registry.bootstrap import RegistryBootstrap

class UIOrchestrator:
    """
    Standards-compliant orchestrator wrapper for the Decision Studio UI.
    
    Handles all agent interactions through the orchestrator, enforcing
    Agent9 design standards and providing debug capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the UI orchestrator with configuration."""
        self.config = config
        self.orchestrator = None
        self.debug_metrics = {
            "kpis_loaded": 0,
            "sql_statements": [],
            "sql_execution_times_ms": [],
            "situations_by_severity": {},
            "registry_status": {},
            "agent_initializations": [],
            "protocol_messages": []
        }
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self) -> bool:
        """Initialize the orchestrator and required agents."""
        try:
            # First initialize the agent registry with common agent factories
            await RegistryBootstrap.initialize(self.config)
            
            # Create and initialize orchestrator
            orchestrator_config = self.config.get("orchestrator_config", {})
            self.orchestrator = await A9_Orchestrator_Agent.create(orchestrator_config)
            
            # Ensure default factories are registered for known agents
            # This provides a stable fallback when dynamic discovery misses create methods
            await initialize_agent_registry()
            
            # Log agent initialization
            self.debug_metrics["agent_initializations"].append({
                "agent": "orchestrator",
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            })
            
            # Register required agents via orchestrator
            await self._register_required_agents()
            
            # Get registry status
            self.debug_metrics["registry_status"] = await self._get_registry_status()
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize UI orchestrator: {str(e)}")
            return False
    
    async def _register_required_agents(self) -> None:
        """Initialize agent discovery through the orchestrator."""
        # Set up paths for contracts and data
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        contracts_path = os.path.join(base_path, "contracts")
        sap_data_path = self.config.get("sap_data_path", 
            "C:/Users/Blell/Documents/Agent9/SAP DataSphere Data/datasphere-content-1.7/datasphere-content-1.7/SAP_Sample_Content/CSV/FI")
        registry_path = os.path.join(base_path, "registry")
        
        # Set up configuration with all necessary paths
        config = {
            "base_path": base_path,
            "registry_path": registry_path,
            "contracts_path": contracts_path,
            "data_path": sap_data_path,
            "name": "A9_Orchestrator",
            "description": "Main Agent9 Orchestrator",
            "version": "1.0.0"
        }
        
        # Prefer explicit factory registration over dynamic discovery to avoid noisy logs
        # Factories are registered via initialize_agent_registry() during initialize()
        required_agents = [
            "A9_Situation_Awareness_Agent",
            "A9_Principal_Context_Agent",
            "A9_Data_Product_Agent"
        ]

        for agent_name in required_agents:
            try:
                # Attempt to instantiate the agent to validate availability
                agent = await self.orchestrator.get_agent(agent_name, config)
                if agent is not None:
                    self.logger.info(f"Instantiated {agent_name} via registered factory")
                    self.debug_metrics["agent_initializations"].append({
                        "agent": agent_name,
                        "timestamp": datetime.now().isoformat(),
                        "status": "validated"
                    })
                else:
                    self.logger.warning(f"{agent_name} not available (no factory registered)")
                    self.debug_metrics["agent_initializations"].append({
                        "agent": agent_name,
                        "timestamp": datetime.now().isoformat(),
                        "status": "unavailable"
                    })
            except Exception as e:
                self.logger.error(f"Error instantiating {agent_name}: {str(e)}")
                self.debug_metrics["agent_initializations"].append({
                    "agent": agent_name,
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "error": str(e)
                })
    
    async def _get_registry_status(self) -> Dict[str, Any]:
        """Get the current status of all registries."""
        status = {}
        
        # For the debug UI, we'll just report basic information
        # since we don't have direct provider access
        
        try:
            if self.orchestrator is None:
                self.logger.error("Orchestrator is None when trying to get registry status")
                return {"error": "Orchestrator not initialized"}
                
            # Get list of registered agents
            agents = await self.orchestrator.list_agents()
            
            # Set up basic registry information
            status["agent_registry"] = {
                "count": len(agents),
                "loaded": len(agents) > 0,
                "agents": agents
            }
            
            # Set placeholder values for other registries
            # In a full implementation, we would get this data from specific agents
            status["kpi_registry"] = {
                "count": 0,  # Will be populated during workflow execution
                "loaded": True,
                "source": "Registry access via agents"
            }
            
            status["business_process_registry"] = {
                "count": 0,  # Will be populated during workflow execution
                "loaded": True,
                "source": "Registry access via agents"
            }
            
            status["principal_registry"] = {
                "count": 0,  # Will be populated during workflow execution
                "loaded": True,
                "source": "Registry access via agents"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get registry status: {str(e)}")
            status["error"] = str(e)
        
        return status
    
    async def detect_situations(self, 
                                principal_role: PrincipalRole, 
                                business_processes: List[BusinessProcess],
                                timeframe: TimeFrame,
                                comparison_type: ComparisonType,
                                filters: Dict[str, Any] = None,
                                principal_id: str = None) -> List[Situation]:
        """
        Detect situations through the orchestrator.
        
        Args:
            principal_role: Role of the principal
            business_processes: List of business processes to analyze
            timeframe: Time frame for analysis
            comparison_type: Type of comparison to perform
            filters: Additional filters to apply
            principal_id: Specific ID of the principal (e.g., 'cfo_001')
            
        Returns:
            List of detected situations
        """
        start_time = time.time()
        
        # First, get the principal context for the given role and ID if provided
        principal_context = await self.get_principal_context(principal_role, principal_id)
        
        # Generate a unique request ID
        request_id = f"situation_{datetime.now().strftime('%Y%m%d%H%M%S')}_{principal_role.value}"
        
        # Create protocol-compliant request
        request = SituationDetectionRequest(
            request_id=request_id,
            principal_context=principal_context,
            business_processes=business_processes,
            timeframe=timeframe,
            comparison_type=comparison_type,
            filters=filters or {}
        )
        
        # Log protocol message
        self._log_protocol_message("request", "detect_situations", request)
        
        # Check if orchestrator is initialized
        if self.orchestrator is None:
            self.logger.error("Cannot detect situations: Orchestrator is not initialized")
            raise ValueError("Orchestrator is not initialized. Please ensure initialize() was called and completed successfully.")
            
        # Execute through orchestrator
        response = await self.orchestrator.execute_agent_method(
            "A9_Situation_Awareness_Agent",
            "detect_situations",
            request
        )
        
        # Update debug metrics
        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000
        
        # Count situations by severity
        situations_by_severity = {}
        for situation in response.situations:
            severity = situation.severity.name
            if severity not in situations_by_severity:
                situations_by_severity[severity] = 0
            situations_by_severity[severity] += 1
        
        self.debug_metrics["situations_by_severity"] = situations_by_severity
        
        # Log protocol message
        self._log_protocol_message("response", "detect_situations", response)
        
        return response.situations
    
    async def get_kpi_sqls(
        self,
        principal_role: PrincipalRole,
        business_processes: List[BusinessProcess],
        timeframe: TimeFrame,
        comparison_type: ComparisonType,
        filters: Dict[str, Any] = None,
        principal_id: str = None
    ) -> Dict[str, Dict[str, str]]:
        """
        Retrieve base and comparison SQL for relevant KPIs via the orchestrator.
        Returns a mapping: { kpi_name: { 'base_sql': str, 'comparison_sql': str } }
        """
        # Ensure orchestrator is initialized
        if self.orchestrator is None:
            raise ValueError("Orchestrator is not initialized. Call initialize() first.")

        # Resolve principal context
        principal_context = await self.get_principal_context(principal_role, principal_id)

        # Merge KPI definitions across requested business processes
        merged_kpis: Dict[str, Any] = {}
        for bp in (business_processes or []):
            try:
                resp = await self.orchestrator.execute_agent_method(
                    "A9_Situation_Awareness_Agent",
                    "get_kpi_definitions",
                    {"principal_context": principal_context, "business_process": bp}
                )
                if isinstance(resp, dict):
                    merged_kpis.update(resp)
            except Exception as e:
                self.logger.warning(f"get_kpi_sqls: unable to fetch KPI defs for {bp}: {e}")

        # If no BPs provided or empty result, attempt domain-level fallback using the role's default context
        if not merged_kpis:
            try:
                resp = await self.orchestrator.execute_agent_method(
                    "A9_Situation_Awareness_Agent",
                    "get_kpi_definitions",
                    {"principal_context": principal_context}
                )
                if isinstance(resp, dict):
                    merged_kpis.update(resp)
            except Exception as e:
                self.logger.warning(f"get_kpi_sqls: fallback fetch of KPI defs failed: {e}")

        results: Dict[str, Dict[str, str]] = {}
        # Fetch base and comparison SQL for each KPI
        for kpi_name, kpi_def in merged_kpis.items():
            try:
                base_resp = await self.orchestrator.execute_agent_method(
                    "A9_Data_Product_Agent",
                    "generate_sql_for_kpi",
                    {"kpi_definition": kpi_def, "timeframe": timeframe, "filters": (filters or {})}
                )
                base_sql = base_resp.get("sql", "") if isinstance(base_resp, dict) else ""

                comp_resp = await self.orchestrator.execute_agent_method(
                    "A9_Data_Product_Agent",
                    "generate_sql_for_kpi_comparison",
                    {
                        "kpi_definition": kpi_def,
                        "timeframe": timeframe,
                        "comparison_type": comparison_type,
                        "filters": (filters or {})
                    }
                )
                comp_sql = comp_resp.get("sql", "") if isinstance(comp_resp, dict) else ""

                results[kpi_name] = {"base_sql": base_sql, "comparison_sql": comp_sql}

                # Record for debug metrics panel
                if base_sql:
                    self.debug_metrics["sql_statements"].append({
                        "query": base_sql,
                        "execution_time_ms": 0.0,
                        "timestamp": datetime.now().isoformat(),
                        "note": f"base:{kpi_name}"
                    })
                if comp_sql:
                    self.debug_metrics["sql_statements"].append({
                        "query": comp_sql,
                        "execution_time_ms": 0.0,
                        "timestamp": datetime.now().isoformat(),
                        "note": f"comparison:{kpi_name}"
                    })
            except Exception as e:
                self.logger.warning(f"get_kpi_sqls: error fetching SQL for KPI {kpi_name}: {e}")

        return results
    
    async def process_nl_query(self, 
                               principal_role: PrincipalRole,
                               query: str,
                               timeframe: TimeFrame = TimeFrame.CURRENT_QUARTER,
                               principal_id: str = None) -> Dict[str, Any]:
        """
        Process a natural language query through the orchestrator.
        
        Args:
            principal_role: Role of the principal
            query: Natural language query
            timeframe: Time frame for analysis
            principal_id: Specific ID of the principal (e.g., 'cfo_001')
            
        Returns:
            Query response with answer and KPI values
        """
        start_time = time.time()
        
        # Get principal context if needed for enhanced requests
        principal_context = None
        if principal_id:
            # Get principal context with specific ID
            principal_context = await self.get_principal_context(principal_role, principal_id)
        
        # Create protocol-compliant request
        request = NLQueryRequest(
            principal_role=principal_role,
            query=query,
            timeframe=timeframe,
            principal_context=principal_context  # Use specific principal context if available
        )
        
        # Log protocol message
        self._log_protocol_message("request", "process_nl_query", request)
        
        # Check if orchestrator is initialized
        if self.orchestrator is None:
            self.logger.error("Cannot process NL query: Orchestrator is not initialized")
            raise ValueError("Orchestrator is not initialized. Please ensure initialize() was called and completed successfully.")
            
        # Execute through orchestrator
        response = await self.orchestrator.execute_agent_method(
            "A9_Situation_Awareness_Agent",
            "process_nl_query",
            request
        )
        
        # Update debug metrics
        end_time = time.time()
        execution_time_ms = (end_time - start_time) * 1000
        
        if hasattr(response, 'sql_query') and response.sql_query:
            self.debug_metrics["sql_statements"].append({
                "query": response.sql_query,
                "execution_time_ms": execution_time_ms,
                "timestamp": datetime.now().isoformat()
            })
            self.debug_metrics["sql_execution_times_ms"].append(execution_time_ms)
        
        # Log protocol message
        self._log_protocol_message("response", "process_nl_query", response)
        
        return response
    
    async def get_principal_context(self, principal_role: PrincipalRole, principal_id: str = None) -> PrincipalContext:
        """
        Get principal context through the orchestrator.
        
        Args:
            principal_role: Role of the principal
            principal_id: Specific ID of the principal (e.g., 'cfo_001')
            
        Returns:
            Principal context
        """
        # Log protocol message
        request_data = {"principal_role": principal_role}
        if principal_id:
            request_data["principal_id"] = principal_id
            
        self._log_protocol_message("request", "get_principal_context", request_data)
        
        # Check if orchestrator is initialized
        if self.orchestrator is None:
            self.logger.error("Cannot get principal context: Orchestrator is not initialized")
            raise ValueError("Orchestrator is not initialized. Please ensure initialize() was called and completed successfully.")
            
        # Execute through orchestrator - agent expects a single positional argument (principal_role)
        # Principal ID is not currently supported by the legacy method signature; we may extend later via a new method
        request_params = principal_role
            
        response = await self.orchestrator.execute_agent_method(
            "A9_Principal_Context_Agent",
            "get_principal_context",
            request_params
        )
        
        # Log protocol message
        self._log_protocol_message("response", "get_principal_context", response)
        
        return response
    
    async def get_recommended_questions(self, principal_context: PrincipalContext) -> List[str]:
        """
        Get recommended questions through the orchestrator.
        
        Args:
            principal_context: Principal context
            
        Returns:
            List of recommended questions
        """
        # Check if orchestrator is initialized
        if self.orchestrator is None:
            self.logger.error("Cannot get recommended questions: Orchestrator is not initialized")
            raise ValueError("Orchestrator is not initialized. Please ensure initialize() was called and completed successfully.")
            
        # Execute through orchestrator
        response = await self.orchestrator.execute_agent_method(
            "A9_Situation_Awareness_Agent",
            "get_recommended_questions",
            {"principal_context": principal_context}
        )
        
        return response
    
    def _log_protocol_message(self, direction: str, method: str, message: Any) -> None:
        """Log protocol messages for debugging."""
        self.debug_metrics["protocol_messages"].append({
            "timestamp": datetime.now().isoformat(),
            "direction": direction,
            "method": method,
            "message": str(message)
        })
    
    def get_debug_metrics(self) -> Dict[str, Any]:
        """Get debug metrics collected during operation."""
        return self.debug_metrics
    
    def reset_debug_metrics(self) -> None:
        """Reset debug metrics."""
        self.debug_metrics = {
            "kpis_loaded": 0,
            "sql_statements": [],
            "sql_execution_times_ms": [],
            "situations_by_severity": {},
            "registry_status": {},
            "agent_initializations": [],
            "protocol_messages": []
        }
