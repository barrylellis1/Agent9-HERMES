"""
A9 Orchestrator Agent

The Orchestrator Agent manages agent-to-agent communication and workflow orchestration.
It maintains a registry of available agents and handles agent lifecycle management.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable, Type, Union, Set
import inspect
from src.agents.shared.business_context_loader import try_load_business_context
from src.agents.shared.a9_debate_protocol_models import A9_ProblemStatement, A9_PS_BusinessContext
from src.agents.models.situation_awareness_models import SituationDetectionRequest
from src.agents.models.data_product_onboarding_models import (
    DataProductOnboardingWorkflowRequest,
    DataProductOnboardingWorkflowResponse,
    WorkflowStepSummary,
    DataProductSchemaInspectionRequest,
    DataProductContractGenerationRequest,
    DataProductRegistrationRequest,
    KPIRegistryUpdateRequest,
    BusinessProcessMappingRequest,
    PrincipalOwnershipRequest,
    DataProductQARequest,
)
from src.agents.models.deep_analysis_models import (
    DeepAnalysisRequest,
    DeepAnalysisResponse,
    DeepAnalysisPlan,
)
from src.agents.models.solution_finder_models import (
    SolutionFinderRequest,
    SolutionFinderResponse,
)

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Agent registry singleton that manages agent instances and provides access to them.
    """
    _instance = None
    _agents = {}
    _agent_factories = {}
    _agent_dependencies = {}
    _agent_initialization_status = {}
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super(AgentRegistry, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def register_agent(cls, agent_name: str, agent_instance: Any) -> None:
        """
        Register an agent instance with the registry.
        
        Args:
            agent_name: Name of the agent.
            agent_instance: Instance of the agent.
        """
        cls._agents[agent_name] = agent_instance
        logger.info(f"Agent {agent_name} registered with the registry")
    
    @classmethod
    def register_agent_factory(cls, agent_name: str, factory_func: Callable) -> None:
        """
        Register an agent factory function with the registry.
        
        Args:
            agent_name: Name of the agent.
            factory_func: Factory function to create the agent.
        """
        cls._agent_factories[agent_name] = factory_func
        logger.info(f"Agent factory for {agent_name} registered with the registry (total factories: {len(cls._agent_factories)})")
    
    @classmethod
    async def get_agent(cls, agent_name: str, config: Dict[str, Any] = None) -> Any:
        """
        Get an agent from the registry, creating it if necessary.
        
        Args:
            agent_name: Name of the agent to get.
            config: Configuration for agent creation if needed.
            
        Returns:
            Agent instance.
        """
        # Return existing instance if available
        if agent_name in cls._agents:
            logger.debug(f"Returning existing agent {agent_name} from registry")
            return cls._agents[agent_name]
        
        # Log available factories for diagnostics
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Available factories: {list(cls._agent_factories.keys())}")
        else:
            logger.info(f"Requesting agent '{agent_name}'. Registered factories: {list(cls._agent_factories.keys())}")
        
        # Create a new instance if we have a factory
        if agent_name in cls._agent_factories:
            logger.info(f"Creating new agent {agent_name} using registered factory with config keys: {list((config or {}).keys())}")
            factory = cls._agent_factories[agent_name]
            
            # Check if factory is async
            if inspect.iscoroutinefunction(factory):
                agent = await factory(config or {})
            else:
                agent = factory(config or {})
                
            cls._agents[agent_name] = agent
            logger.info(f"Agent {agent_name} created and registered successfully")
            return agent
        
        logger.error(f"Agent {agent_name} not found in registry and no factory available")
        return None
    
    @classmethod
    def list_agents(cls) -> List[str]:
        """
        List all registered agents.
        
        Returns:
            List of agent names.
        """
        return list(cls._agents.keys())
    
    @classmethod
    def register_agent_dependency(cls, agent_name: str, depends_on: List[str]) -> None:
        """
        Register dependencies for an agent.
        
        Args:
            agent_name: Name of the agent.
            depends_on: List of agent names that this agent depends on.
        """
        cls._agent_dependencies[agent_name] = depends_on
        logger.info(f"Dependencies for {agent_name} registered: {depends_on}")
    
    @classmethod
    def get_agent_dependencies(cls, agent_name: str) -> List[str]:
        """
        Get dependencies for an agent.
        
        Args:
            agent_name: Name of the agent.
            
        Returns:
            List of agent names that this agent depends on.
        """
        return cls._agent_dependencies.get(agent_name, [])
    
    @classmethod
    def set_agent_initialization_status(cls, agent_name: str, status: bool) -> None:
        """
        Set the initialization status for an agent.
        
        Args:
            agent_name: Name of the agent.
            status: Initialization status (True if initialized, False otherwise).
        """
        cls._agent_initialization_status[agent_name] = status
        logger.info(f"Agent {agent_name} initialization status set to {status}")
    
    @classmethod
    def get_agent_initialization_status(cls, agent_name: str) -> bool:
        """
        Get the initialization status for an agent.
        
        Args:
            agent_name: Name of the agent.
            
        Returns:
            Initialization status (True if initialized, False otherwise).
        """
        return cls._agent_initialization_status.get(agent_name, False)
    
    @classmethod
    def clear(cls) -> None:
        """
        Clear the registry (mainly for testing).
        """
        cls._agents = {}
        cls._agent_factories = {}
        cls._agent_dependencies = {}
        cls._agent_initialization_status = {}
        logger.info("Agent registry cleared")


class A9_Orchestrator_Agent:
    """
    Orchestrator Agent responsible for managing agent communication and workflow execution.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Orchestrator Agent.
        
        Args:
            config: Configuration dictionary.
        """
        self.config = config or {}
        self.name = "A9_Orchestrator_Agent"
        self.version = "0.1.0"
        self.registry = AgentRegistry()
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging for the agent."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initializing {self.__class__.__name__}")
    
    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> 'A9_Orchestrator_Agent':
        """
        Create a new instance of the Orchestrator Agent.
        
        Args:
            config: Configuration dictionary.
            
        Returns:
            Initialized Orchestrator Agent instance.
        """
        agent = cls(config)
        await agent.connect()
        return agent
    
    async def connect(self):
        """
        Connect to dependencies and initialize required resources.
        """
        self.logger.info(f"{self.name} connected to dependencies")
        return True
    
    async def disconnect(self):
        """
        Disconnect from dependencies and clean up resources.
        """
        self.logger.info(f"{self.name} disconnected from dependencies")
    
    def inject_business_context(self, problem_statement: Any, default_path: Optional[str] = None) -> Any:
        """
        Inject a stable Business Context into an A9_ProblemStatement if missing.

        - Accepts either a dict (serialized problem statement) or an A9_ProblemStatement instance.
        - Attempts to load context via env var A9_BUSINESS_CONTEXT_YAML, else uses default_path.
        - Returns the same type as provided (dict in, dict out; model in, model out).

        This is a minimal, opt-in helper that keeps existing patterns intact.
        """
        try:
            bc = try_load_business_context(default_path)
            if not bc:
                return problem_statement

            # Pydantic model path
            if isinstance(problem_statement, A9_ProblemStatement):
                if getattr(problem_statement, "business_context", None) is None:
                    problem_statement.business_context = bc
                return problem_statement

            # Dict path (serialized request)
            if isinstance(problem_statement, dict):
                if not problem_statement.get("business_context"):
                    try:
                        problem_statement["business_context"] = bc.serialize()
                    except Exception:
                        # Fallback to model_dump for safety
                        problem_statement["business_context"] = bc.model_dump()
                return problem_statement

            # Unknown type: no-op
            return problem_statement
        except Exception:
            # Non-intrusive: never raise from injector
            return problem_statement
    
    async def register_agent(self, agent_name: str, agent_instance: Any, dependencies: List[str] = None) -> None:
        """
        Register an agent with the registry.
        
        Args:
            agent_name: Name of the agent.
            agent_instance: Instance of the agent.
            dependencies: List of agent names that this agent depends on.
        """
        self.registry.register_agent(agent_name, agent_instance)
        
        # Register dependencies if provided
        if dependencies:
            self.registry.register_agent_dependency(agent_name, dependencies)
            self.logger.info(f"Registered agent {agent_name} with dependencies: {dependencies}")
    
    async def register_agent_factory(self, agent_name: str, factory_func: Callable, dependencies: List[str] = None) -> None:
        """
        Register an agent factory with the registry.
        
        Args:
            agent_name: Name of the agent.
            factory_func: Factory function to create the agent.
            dependencies: List of agent names that this agent depends on.
        """
        self.registry.register_agent_factory(agent_name, factory_func)
        
        # Register dependencies if provided
        if dependencies:
            self.registry.register_agent_dependency(agent_name, dependencies)
            self.logger.info(f"Registered agent factory {agent_name} with dependencies: {dependencies}")
            
    async def register_agent_dependency(self, agent_name: str, depends_on: List[str]) -> None:
        """
        Register dependencies for an agent.
        
        Args:
            agent_name: Name of the agent.
            depends_on: List of agent names that this agent depends on.
        """
        self.registry.register_agent_dependency(agent_name, depends_on)
        self.logger.info(f"Registered dependencies for {agent_name}: {depends_on}")
    
    async def get_agent(self, agent_name: str, config: Dict[str, Any] = None, resolve_dependencies: bool = True) -> Any:
        """
        Get an agent from the registry, resolving dependencies if needed.
        
        Args:
            agent_name: Name of the agent to get.
            config: Configuration for agent creation if needed.
            resolve_dependencies: Whether to resolve dependencies automatically.
            
        Returns:
            Agent instance.
        """
        # Check if we need to resolve dependencies
        if resolve_dependencies:
            await self._resolve_agent_dependencies(agent_name)
            
        return await self.registry.get_agent(agent_name, config)
    
    async def _resolve_agent_dependencies(self, agent_name: str, visited: Set[str] = None) -> None:
        """
        Resolve dependencies for an agent recursively.
        
        Args:
            agent_name: Name of the agent.
            visited: Set of already visited agents (to prevent cycles).
        """
        if visited is None:
            visited = set()
            
        # Prevent cycles
        if agent_name in visited:
            self.logger.warning(f"Dependency cycle detected for {agent_name}")
            return
            
        visited.add(agent_name)
        
        # Get dependencies for this agent
        dependencies = self.registry.get_agent_dependencies(agent_name)
        if not dependencies:
            self.logger.debug(f"No dependencies found for {agent_name}")
            return
            
        self.logger.info(f"Resolving dependencies for {agent_name}: {dependencies}")
        
        # Resolve each dependency recursively
        for dependency in dependencies:
            # First resolve dependencies of the dependency
            await self._resolve_agent_dependencies(dependency, visited)
            
            # Then ensure the dependency is created
            if dependency not in self.registry.list_agents():
                self.logger.info(f"Creating dependency {dependency} for {agent_name}")
                await self.registry.get_agent(dependency)
                
        self.logger.info(f"Dependencies resolved for {agent_name}")
        
    async def create_agent_with_dependencies(self, agent_name: str, config: Dict[str, Any] = None) -> Any:
        """
        Create an agent and ensure all its dependencies are created and initialized.
        
        Args:
            agent_name: Name of the agent to create.
            config: Configuration for agent creation.
            
        Returns:
            Created agent instance.
        """
        # First resolve all dependencies
        await self._resolve_agent_dependencies(agent_name)
        
        # Then create the agent
        agent = await self.registry.get_agent(agent_name, config)
        
        # Mark as initialized
        self.registry.set_agent_initialization_status(agent_name, True)
        
        return agent
    
    async def list_agents(self) -> List[str]:
        """
        List all registered agents.
        
        Returns:
            List of agent names.
        """
        return self.registry.list_agents()
    
    async def execute_agent_method(self, agent_name: str, method_name: str, params: Any) -> Any:
        """
        Execute a method on an agent and return the result.
        
        This is the core method for inter-agent communication via the orchestrator,
        enabling protocol-compliant message passing between agents.
        
        Args:
            agent_name: Name of the agent to execute the method on.
            method_name: Name of the method to execute.
            params: Parameters to pass to the method (can be dict, object, or primitive).
            
        Returns:
            Result of the method execution.
            
        Raises:
            ValueError: If the agent or method doesn't exist.
        """
        # Get the agent from the registry
        agent = await self.get_agent(agent_name)
        if not agent:
            error_msg = f"Agent '{agent_name}' not found in registry"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Check if the method exists on the agent
        if not hasattr(agent, method_name):
            error_msg = f"Method '{method_name}' not found on agent '{agent_name}'"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        method = getattr(agent, method_name)
        
        # Check if the method is callable
        if not callable(method):
            error_msg = f"'{method_name}' is not a callable method on agent '{agent_name}'"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        # Execute the method with the given parameters
        # Log parameter summary (non-sensitive)
        param_summary = ""
        try:
            if isinstance(params, dict):
                param_summary = f"keys={list(params.keys())[:6]}"
            else:
                param_summary = f"type={type(params).__name__}"
        except Exception:
            param_summary = "unavailable"
        self.logger.info(f"Executing {agent_name}.{method_name} ({param_summary})")
        try:
            _start_time = time.time()
            # Handle different parameter types
            if isinstance(params, dict):
                result = await method(**params) if inspect.iscoroutinefunction(method) else method(**params)
            else:
                result = await method(params) if inspect.iscoroutinefunction(method) else method(params)
                
            _elapsed_ms = int((time.time() - _start_time) * 1000)
            self.logger.info(f"Completed {agent_name}.{method_name} in {_elapsed_ms} ms")
            return result
        except Exception as e:
            error_msg = f"Error executing {agent_name}.{method_name}: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e

    async def _execute_workflow_step(
        self,
        agent_name: str,
        method_name: str,
        request_model,
        request_payload: Dict[str, Any],
        step_name: str,
        context: Dict[str, Any],
        suppress_errors: bool = False,
    ) -> WorkflowStepSummary:
        """Execute a workflow entrypoint and wrap the response into a summary."""

        try:
            if isinstance(request_model, type):
                request_instance = request_model(**request_payload)
            else:
                request_instance = request_model

            result = await self.execute_agent_method(
                agent_name,
                method_name,
                {"request": request_instance},
            )

            if hasattr(result, "model_dump"):
                result_dict = result.model_dump()
                status = result_dict.get("status", "success")
            else:
                result_dict = result if isinstance(result, dict) else {"result": result}
                status = result_dict.get("status", "success")

            context[step_name] = result_dict

            return WorkflowStepSummary(
                name=step_name,
                status=status,
                details=result_dict,
            )
        except Exception as exc:
            self.logger.error(f"Workflow step {step_name} failed: {exc}")
            if suppress_errors:
                return WorkflowStepSummary(
                    name=step_name,
                    status="error",
                    details={"error": str(exc)},
                )
            raise

    async def orchestrate_data_product_onboarding(
        self, request: DataProductOnboardingWorkflowRequest
    ) -> DataProductOnboardingWorkflowResponse:
        """Coordinate the full data product onboarding workflow across agents."""

        steps: List[WorkflowStepSummary] = []
        context: Dict[str, Any] = {}
        contract_paths: List[str] = []
        principal_owner: Dict[str, Any] = {}
        qa_report: Dict[str, Any] = {}
        activation_context: Dict[str, Any] = {}
        governance_status = "pending"

        def _build_response(status: str, error_message: Optional[str] = None) -> DataProductOnboardingWorkflowResponse:
            payload = {
                "steps": steps,
                "data_product_id": request.data_product_id,
                "contract_paths": contract_paths,
                "governance_status": governance_status,
                "principal_owner": principal_owner,
                "qa_report": qa_report,
                "activation_context": activation_context,
            }

            if status == "success":
                return DataProductOnboardingWorkflowResponse.success(
                    request_id=request.request_id,
                    **payload,
                )
            if status == "pending":
                return DataProductOnboardingWorkflowResponse.pending(
                    request_id=request.request_id,
                    **payload,
                )
            return DataProductOnboardingWorkflowResponse.error(
                request_id=request.request_id,
                error_message=error_message or "Data product onboarding failed",
                **payload,
            )

        async def _run_step(
            agent_name: str,
            method_name: str,
            model_cls,
            payload: Dict[str, Any],
            name: str,
            suppress_errors: bool = False,
        ) -> WorkflowStepSummary:
            summary = await self._execute_workflow_step(
                agent_name,
                method_name,
                model_cls,
                payload,
                name,
                context,
                suppress_errors=suppress_errors,
            )
            steps.append(summary)
            return summary

        try:
            try:
                await initialize_agent_registry()
            except Exception as init_err:  # pragma: no cover - defensive
                self.logger.warning(f"Agent registry initialization warning: {init_err}")

            for agent_name in [
                "A9_Data_Product_Agent",
                "A9_Data_Governance_Agent",
                "A9_Principal_Context_Agent",
            ]:
                try:
                    await self.get_agent(agent_name)
                except Exception as agent_err:  # pragma: no cover - defensive
                    self.logger.warning(f"Unable to pre-load {agent_name}: {agent_err}")

            # INGESTION LOGIC: If connection_overrides has file_path, load it into DuckDB
            if request.connection_overrides and request.connection_overrides.get('file_path') and request.source_system == 'duckdb':
                file_path = request.connection_overrides.get('file_path')
                table_name = request.connection_overrides.get('table_name', 'ingested_table')
                self.logger.info(f"Ingesting file {file_path} into table {table_name}")
                
                dp_agent = await self.get_agent("A9_Data_Product_Agent")
                # Use internal db_manager to execute raw SQL
                if hasattr(dp_agent, 'db_manager'):
                    ingest_sql = f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM '{file_path}'"
                    try:
                        # execute_query might be async
                        if hasattr(dp_agent.db_manager, 'execute_query'):
                            res = dp_agent.db_manager.execute_query(ingest_sql)
                            if hasattr(res, '__await__'):
                                await res
                        self.logger.info(f"Ingestion successful: {table_name}")
                    except Exception as ingest_err:
                        self.logger.error(f"Ingestion failed: {ingest_err}")
                        return _build_response("error", f"Data ingestion failed: {ingest_err}")

            inspection_payload = {
                "request_id": request.request_id,
                "principal_id": request.principal_id,
                "data_product_id": request.data_product_id,
                "source_system": request.source_system,
                "database": request.database,
                "schema": request.schema,
                "tables": request.tables,
                "inspection_depth": request.inspection_depth,
                "include_samples": request.include_samples,
                "environment": request.environment,
                "connection_overrides": request.connection_overrides,
            }
            inspection_step = await _run_step(
                "A9_Data_Product_Agent",
                "inspect_source_schema",
                DataProductSchemaInspectionRequest,
                inspection_payload,
                "inspect_source_schema",
            )
            if inspection_step.status == "error":
                return _build_response("error", "Schema inspection failed")

            inspection_details = context.get("inspect_source_schema", {})
            schema_summary = inspection_details.get("tables", [])
            inferred_kpis = inspection_details.get("inferred_kpis", [])

            # Save to staging area during onboarding; promote to production after governance approval
            target_contract_path = request.contract_output_path or f"src/registry_references/data_product_registry/staging/{request.data_product_id}.yaml"
            contract_payload = {
                "request_id": request.request_id,
                "principal_id": request.principal_id,
                "data_product_id": request.data_product_id,
                "schema_summary": schema_summary,
                "kpi_proposals": inferred_kpis,
                "target_contract_path": target_contract_path,
                "contract_overrides": request.contract_overrides or {},
            }
            contract_step = await _run_step(
                "A9_Data_Product_Agent",
                "generate_contract_yaml",
                DataProductContractGenerationRequest,
                contract_payload,
                "generate_contract_yaml",
            )
            if contract_step.status == "error":
                return _build_response("error", "Contract generation failed")

            contract_details = context.get("generate_contract_yaml", {})
            contract_path = contract_details.get("contract_path") or target_contract_path
            if contract_path and contract_path not in contract_paths:
                contract_paths.append(contract_path)

            registration_payload = {
                "request_id": request.request_id,
                "principal_id": request.principal_id,
                "data_product_id": request.data_product_id,
                "contract_path": contract_path,
                "display_name": request.data_product_name,
                "domain": request.data_product_domain,
                "description": request.data_product_description,
                "tags": request.data_product_tags or [],
                "owner_metadata": request.owner_metadata or {},
                "additional_metadata": request.additional_metadata or {},
            }
            registration_step = await _run_step(
                "A9_Data_Product_Agent",
                "register_data_product",
                DataProductRegistrationRequest,
                registration_payload,
                "register_data_product",
            )
            if registration_step.status == "error":
                return _build_response("error", "Registry registration failed")

            registration_details = context.get("register_data_product", {})
            if registration_details.get("registry_entry"):
                activation_context = {"registry_entry": registration_details.get("registry_entry")}

            if request.kpi_entries:
                kpi_payload = {
                    "request_id": request.request_id,
                    "principal_id": request.principal_id,
                    "data_product_id": request.data_product_id,
                    "kpis": request.kpi_entries,
                    "overwrite_existing": request.overwrite_existing_kpis,
                }
                kpi_step = await _run_step(
                    "A9_Data_Governance_Agent",
                    "register_kpi_metadata",
                    KPIRegistryUpdateRequest,
                    kpi_payload,
                    "register_kpi_metadata",
                )
                if kpi_step.status == "error":
                    governance_status = "error"
                    return _build_response("error", "KPI registry update failed")
                governance_status = "success"

            if request.business_process_mappings:
                mapping_payload = {
                    "request_id": request.request_id,
                    "principal_id": request.principal_id,
                    "data_product_id": request.data_product_id,
                    "mappings": request.business_process_mappings,
                    "overwrite_existing": request.overwrite_existing_mappings,
                }
                mapping_step = await _run_step(
                    "A9_Data_Governance_Agent",
                    "map_business_process",
                    BusinessProcessMappingRequest,
                    mapping_payload,
                    "map_business_processes",
                )
                if mapping_step.status == "error":
                    governance_status = "error"
                    return _build_response("error", "Business process mapping failed")
                if governance_status != "error":
                    governance_status = "success"

            if (
                request.candidate_owner_ids
                or request.fallback_roles
                or request.business_process_context
            ):
                ownership_payload = {
                    "request_id": request.request_id,
                    "principal_id": request.principal_id,
                    "data_product_id": request.data_product_id,
                    "candidate_owner_ids": request.candidate_owner_ids or [],
                    "fallback_roles": request.fallback_roles or [],
                    "business_process_context": request.business_process_context or [],
                    "environment": request.environment,
                }
                ownership_step = await _run_step(
                    "A9_Principal_Context_Agent",
                    "identify_data_product_owner",
                    PrincipalOwnershipRequest,
                    ownership_payload,
                    "identify_data_product_owner",
                )
                if ownership_step.status == "error":
                    return _build_response("error", "Principal ownership resolution failed")
                principal_owner = context.get("identify_data_product_owner", {})
                if principal_owner:
                    activation_context.setdefault("principal_ownership", principal_owner)

            if request.qa_enabled:
                qa_payload = {
                    "request_id": request.request_id,
                    "principal_id": request.principal_id,
                    "data_product_id": request.data_product_id,
                    "contract_path": contract_path,
                    "environment": request.environment,
                    "checks": request.qa_checks or [],
                    "additional_context": request.qa_additional_context or {},
                }
                qa_step = await _run_step(
                    "A9_Data_Product_Agent",
                    "validate_data_product_onboarding",
                    DataProductQARequest,
                    qa_payload,
                    "validate_data_product_onboarding",
                )
                qa_report = context.get("validate_data_product_onboarding", {})
                if qa_step.status == "error":
                    return _build_response("error", "QA validation failed")

            statuses = {step.status for step in steps}
            if "error" in statuses:
                return _build_response("error")
            if "pending" in statuses:
                return _build_response("pending")
            if governance_status == "pending" and not (
                request.kpi_entries or request.business_process_mappings
            ):
                governance_status = "success"
            return _build_response("success")

        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error(f"Unexpected onboarding failure: {exc}")
            return _build_response("error", str(exc))

    async def orchestrate_situation_detection(
        self, request: SituationDetectionRequest
    ) -> Dict[str, Any]:
        """
        Orchestrate the situation detection workflow.
        
        Args:
            request: The situation detection request.
            
        Returns:
            The detection results including surfaced situations and logs.
        """
        # Debugging: Print exactly what request is
        p_id = "unknown"
        try:
            if isinstance(request, dict):
                p_id = request.get('principal_context', {}).get('principal_id', 'unknown_dict')
            elif hasattr(request, 'principal_context'):
                if hasattr(request.principal_context, 'principal_id'):
                    p_id = request.principal_context.principal_id
                elif isinstance(request.principal_context, dict):
                    p_id = request.principal_context.get('principal_id', 'unknown_pc_dict')
            elif hasattr(request, 'principal_id'):
                p_id = request.principal_id
        except Exception as e:
            p_id = f"error_extracting_id_{str(e)}"

        self.logger.info(f"Orchestrating situation detection for principal {p_id}")
        
        try:
            # 1. Ensure SA Agent is initialized
            await self.get_agent("A9_Situation_Awareness_Agent")
            
            # 2. Execute detection
            result = await self.execute_agent_method(
                "A9_Situation_Awareness_Agent",
                "detect_situations",
                {"request": request}
            )
            
            # 3. Log success
            # Result is a SituationDetectionResponse object (Pydantic model)
            # We need to handle both object and dict return types from execute_agent_method
            if isinstance(result, dict):
                situations = result.get("situations", [])
                metadata = result.get("metadata", {})
                logs = result.get("logs", [])
            else:
                # Assume Pydantic model
                situations = getattr(result, "situations", [])
                metadata = getattr(result, "metadata", {}) if hasattr(result, "metadata") else {}
                logs = getattr(result, "logs", []) if hasattr(result, "logs") else []

            situation_count = len(situations)
            self.logger.info(f"Situation detection completed. Surfaced {situation_count} situations.")
            
            return {
                "status": "success",
                "situations": situations,
                "metadata": metadata,
                "logs": logs
            }
            
        except Exception as e:
            self.logger.error(f"Situation detection failed: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "situations": []
            }

    async def orchestrate_deep_analysis(
        self, request: DeepAnalysisRequest
    ) -> DeepAnalysisResponse:
        """
        Orchestrate the deep analysis workflow.
        
        Args:
            request: The deep analysis request.
            
        Returns:
            The analysis results including KT Analysis and Change Points.
        """
        self.logger.info(f"Orchestrating deep analysis for KPI: {request.kpi_name}")
        
        try:
            # 1. Ensure DA Agent is initialized
            await self.get_agent("A9_Deep_Analysis_Agent")
            
            # 2. Plan the analysis
            plan_response = await self.execute_agent_method(
                "A9_Deep_Analysis_Agent",
                "plan_deep_analysis",
                {"request": request}
            )
            
            # Handle potential dict response if not Pydantic model
            if isinstance(plan_response, dict):
                plan_data = plan_response.get("plan")
                if not plan_data:
                    return DeepAnalysisResponse.error(
                        request_id=request.request_id,
                        error_message="Planning failed: No plan returned"
                    )
                # Convert dict plan back to model if needed for execution
                if isinstance(plan_data, dict):
                    plan = DeepAnalysisPlan(**plan_data)
                else:
                    plan = plan_data
            else:
                if not plan_response.plan:
                    return DeepAnalysisResponse.error(
                        request_id=request.request_id,
                        error_message="Planning failed: No plan returned"
                    )
                plan = plan_response.plan

            self.logger.info(f"Analysis plan generated with {len(plan.steps)} steps")

            # 3. Execute the analysis
            execution_response = await self.execute_agent_method(
                "A9_Deep_Analysis_Agent",
                "execute_deep_analysis",
                {"plan": plan}
            )
            
            return execution_response
            
        except Exception as e:
            self.logger.error(f"Deep analysis orchestration failed: {str(e)}")
            return DeepAnalysisResponse.error(
                request_id=request.request_id,
                error_message=f"Deep analysis failed: {str(e)}"
            )

    async def orchestrate_solution_finding(
        self, request: SolutionFinderRequest
    ) -> SolutionFinderResponse:
        """
        Orchestrate the solution finding workflow.
        
        Args:
            request: The solution finder request.
            
        Returns:
            The solution finder response with ranked options and recommendations.
        """
        self.logger.info(f"Orchestrating solution finding for request: {request.request_id}")
        
        try:
            # 1. Ensure SF Agent is initialized
            await self.get_agent("A9_Solution_Finder_Agent")
            
            # 2. Execute recommendation
            response = await self.execute_agent_method(
                "A9_Solution_Finder_Agent",
                "recommend_actions",
                {"request": request}
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Solution finding orchestration failed: {str(e)}")
            # Return error response using model if possible, or construct one
            try:
                return SolutionFinderResponse(
                    request_id=request.request_id,
                    status="error",
                    message=f"Solution finding failed: {str(e)}",
                    options_ranked=[]
                )
            except Exception:
                # Fallback if validation fails
                raise RuntimeError(f"Solution finding failed and could not build error response: {e}")

    # ---- Headless orchestration helpers (for batch/background runs) ----
    async def prepare_environment(self, contract_path: str, view_name: str = "FI_Star_View", schema: str = "main") -> Dict[str, Any]:
        """
        Prepare the Data Product environment headlessly (no UI):
        - Register base CSV tables from the YAML contract (delegated to DP Agent)
        - Create the canonical view from the contract (delegated to DP Agent)

        Returns a dict with statuses so batch orchestration can proceed without UI.
        """
        results: Dict[str, Any] = {"status": "started", "contract_path": contract_path, "view_name": view_name}
        try:
            # Ensure DP agent is available per dependencies
            await self.get_agent("A9_Data_Product_Agent")
            
            # Register base tables (idempotent; DP will create/replace tables)
            reg = await self.execute_agent_method(
                "A9_Data_Product_Agent",
                "register_tables_from_contract",
                {"contract_path": contract_path, "schema": schema}
            )
            results["table_registration"] = reg
            
            # Create view from contract (DP will parse YAML and create/replace the view)
            try:
                created = await self.execute_agent_method(
                    "A9_Data_Product_Agent",
                    "create_view_from_contract",
                    {"contract_path": contract_path, "view_name": view_name}
                )
                results["view_creation"] = created
            except Exception as ve:
                results["view_creation"] = {"success": False, "error": str(ve)}
            
            results["status"] = "success"
        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
        return results

    async def onboard_data_product(
        self,
        data_product_id: Optional[str] = None,
        contract_path: Optional[str] = None,
        view_name: str = "FI_Star_View",
        schema: str = "main",
        timeframe: Optional[str] = "rolling_12_months",
        max_dimensions_per_kpi: int = 5,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Orchestrated data product onboarding (MVP):
        - Initialize agent registry factories
        - Register tables & create view via Data Product Agent
        - Validate registry integrity via Data Governance Agent
        - Compute & persist KPI top-dimension enrichment via Data Governance Agent

        Returns: { success, steps: [...], artifacts: { view_name, kpi_enrichment_path? } }
        """
        steps: List[Dict[str, Any]] = []
        artifacts: Dict[str, Any] = {}
        try:
            # Ensure factories are registered (orchestrator-driven)
            try:
                await initialize_agent_registry()
                steps.append({"name": "initialize_agent_registry", "status": "success"})
            except Exception as e:
                steps.append({"name": "initialize_agent_registry", "status": "error", "message": str(e)})
                if not self.config.get("continue_on_error", False):
                    return {"success": False, "steps": steps, "artifacts": artifacts}

            # Resolve default contract path from DPA where possible (avoid hardcoding)
            if not contract_path:
                try:
                    dp_agent = await self.get_agent("A9_Data_Product_Agent")
                    contract_path = dp_agent._contract_path()
                except Exception:
                    pass

            if not dry_run:
                # Prepare environment (tables + view)
                env = await self.prepare_environment(contract_path=contract_path, view_name=view_name, schema=schema)
                steps.append({
                    "name": "prepare_environment",
                    "status": env.get("status", "unknown"),
                    "message": env.get("message"),
                    "details": {
                        "table_registration": env.get("table_registration"),
                        "view_creation": env.get("view_creation"),
                    },
                })
                artifacts["view_name"] = view_name

                # Governance validation
                try:
                    gov = await self.execute_agent_method(
                        "A9_Data_Governance_Agent",
                        "validate_registry_integrity",
                        {"view_name": view_name},
                    )
                    steps.append({
                        "name": "validate_registry_integrity",
                        "status": "success" if bool(gov.get("success")) else "warning",
                        "details": gov,
                    })
                except Exception as e:
                    steps.append({"name": "validate_registry_integrity", "status": "error", "message": str(e)})
                    if not self.config.get("continue_on_error", False):
                        return {"success": False, "steps": steps, "artifacts": artifacts}

                # Compute KPI enrichment
                try:
                    dp_agent = await self.get_agent("A9_Data_Product_Agent")
                    enr = await self.execute_agent_method(
                        "A9_Data_Governance_Agent",
                        "compute_and_persist_top_dimensions",
                        {
                            "data_product_agent": dp_agent,
                            "timeframe": timeframe,
                            "max_dimensions_per_kpi": max_dimensions_per_kpi,
                        },
                    )
                    steps.append({
                        "name": "compute_and_persist_top_dimensions",
                        "status": "success" if bool(enr.get("success")) else "error",
                        "details": enr,
                    })
                    if enr.get("path"):
                        artifacts["kpi_enrichment_path"] = enr.get("path")
                except Exception as e:
                    steps.append({"name": "compute_and_persist_top_dimensions", "status": "error", "message": str(e)})
                    if not self.config.get("continue_on_error", False):
                        return {"success": False, "steps": steps, "artifacts": artifacts}
            else:
                steps.append({"name": "dry_run", "status": "skipped", "message": "No actions performed"})

            overall_success = all(s.get("status") in ("success", "warning", "skipped") for s in steps)
            return {"success": overall_success, "steps": steps, "artifacts": artifacts}
        except Exception as e:
            steps.append({"name": "onboard_data_product", "status": "error", "message": str(e)})
            return {"success": False, "steps": steps, "artifacts": artifacts}

    async def detect_situations_batch(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Headless/batch entrypoint to run situation detection via the SA Agent.
        Expects a request dict compatible with SituationDetectionRequest.
        """
        await self.get_agent("A9_Situation_Awareness_Agent")
        resp = await self.execute_agent_method(
            "A9_Situation_Awareness_Agent",
            "detect_situations",
            {"request": request}
        )
        return resp
    
    async def orchestrate_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate a workflow involving multiple agents.
        
        Args:
            workflow_config: Configuration for the workflow.
            
        Returns:
            Workflow result.
        """
        # This would be implemented with full workflow orchestration logic
        # For now, just a minimal placeholder
        self.logger.info(f"Orchestrating workflow: {workflow_config.get('name', 'Unnamed workflow')}")
        return {"status": "success", "message": "Workflow orchestrated"}


# Export singleton instance for global access
agent_registry = AgentRegistry()

# Initialize agent registry with common agent factories
async def initialize_agent_registry():
    """
    Initialize the agent registry with common agent factories.
    
    This function registers agent factories for commonly used agents
    so they can be created on-demand by the orchestrator.
    """
    # Initialize agent registry with common agent factories
    from src.agents.new.a9_principal_context_agent import A9_Principal_Context_Agent
    from src.agents.new.a9_situation_awareness_agent import A9_Situation_Awareness_Agent, create_situation_awareness_agent
    from src.agents.new.a9_data_product_agent import A9_Data_Product_Agent
    from src.agents.new.a9_data_governance_agent import A9_Data_Governance_Agent, create_data_governance_agent
    from src.agents.new.a9_nlp_interface_agent import A9_NLP_Interface_Agent
    from src.agents.a9_llm_service_agent import A9_LLM_Service_Agent
    from src.agents.new.a9_deep_analysis_agent import A9_Deep_Analysis_Agent, create_deep_analysis_agent
    from src.agents.new.a9_solution_finder_agent import A9_Solution_Finder_Agent, create_solution_finder_agent
    
    # Register agent factories
    agent_registry.register_agent_factory("A9_Principal_Context_Agent", A9_Principal_Context_Agent.create)
    agent_registry.register_agent_factory("A9_Situation_Awareness_Agent", create_situation_awareness_agent)
    agent_registry.register_agent_factory("A9_Data_Product_Agent", A9_Data_Product_Agent.create)
    agent_registry.register_agent_factory("A9_Data_Governance_Agent", A9_Data_Governance_Agent.create)
    agent_registry.register_agent_factory("A9_NLP_Interface_Agent", A9_NLP_Interface_Agent.create)
    agent_registry.register_agent_factory("A9_LLM_Service_Agent", A9_LLM_Service_Agent.create)
    agent_registry.register_agent_factory("A9_Deep_Analysis_Agent", create_deep_analysis_agent)
    agent_registry.register_agent_factory("A9_Solution_Finder_Agent", create_solution_finder_agent)
    
    # Register agent dependencies
    agent_registry.register_agent_dependency("A9_Data_Product_Agent", ["A9_Data_Governance_Agent"])
    agent_registry.register_agent_dependency("A9_Situation_Awareness_Agent", ["A9_Data_Product_Agent", "A9_Principal_Context_Agent"])
    agent_registry.register_agent_dependency("A9_Deep_Analysis_Agent", ["A9_Data_Product_Agent", "A9_Data_Governance_Agent", "A9_LLM_Service_Agent"])
    agent_registry.register_agent_dependency("A9_Solution_Finder_Agent", ["A9_Deep_Analysis_Agent", "A9_LLM_Service_Agent"])
    
    logger.info("Agent registry initialized with common agent factories and dependencies")


async def create_and_connect_agents(orchestrator: A9_Orchestrator_Agent, registry_factory=None):
    """
    Create and connect agents in the correct order based on dependencies.
    
    This function creates and connects agents in the following order:
    1. Data Governance Agent
    2. Principal Context Agent
    3. Data Product Agent
    4. Situation Awareness Agent
    
    Args:
        orchestrator: Orchestrator agent instance
        registry_factory: Optional registry factory to use
        
    Returns:
        Dictionary of created agents
    """
    logger.info("Creating and connecting agents in dependency order")
    
    # Initialize agent registry
    await initialize_agent_registry()
    
    # Create agents in dependency order
    agents = {}
    
    # 1. Data Governance Agent
    logger.info("Creating Data Governance Agent")
    dg_agent_config = {
        "orchestrator": orchestrator,
        "registry_factory": registry_factory
    }
    dg_agent = await orchestrator.create_agent_with_dependencies("A9_Data_Governance_Agent", dg_agent_config)
    agents["A9_Data_Governance_Agent"] = dg_agent
    
    # 2. Principal Context Agent
    logger.info("Creating Principal Context Agent")
    pc_agent_config = {
        "orchestrator": orchestrator,
        "registry_factory": registry_factory
    }
    pc_agent = await orchestrator.create_agent_with_dependencies("A9_Principal_Context_Agent", pc_agent_config)
    agents["A9_Principal_Context_Agent"] = pc_agent
    
    # 3. Data Product Agent
    logger.info("Creating Data Product Agent")
    dp_agent_config = {
        "orchestrator": orchestrator,
        "registry_factory": registry_factory,
        # Pass database config in the structure expected by A9_Data_Product_Agent
        "database": {"type": "duckdb", "path": "data/agent9-hermes-ui.duckdb"},
        "registry_path": "src/registry/data_product",
        "enable_llm_sql": True,
        "force_llm_sql": True
    }
    dp_agent = await orchestrator.create_agent_with_dependencies("A9_Data_Product_Agent", dp_agent_config)
    agents["A9_Data_Product_Agent"] = dp_agent
    
    # 4. Situation Awareness Agent
    logger.info("Creating Situation Awareness Agent")
    sa_agent_config = {
        "orchestrator": orchestrator,
        "registry_factory": registry_factory,
        "target_domains": ["Finance"]
    }
    sa_agent = await orchestrator.create_agent_with_dependencies("A9_Situation_Awareness_Agent", sa_agent_config)
    agents["A9_Situation_Awareness_Agent"] = sa_agent
    
    # 5. Deep Analysis Agent
    logger.info("Creating Deep Analysis Agent")
    da_agent_config = {
        "orchestrator": orchestrator,
        "registry_factory": registry_factory,
    }
    da_agent = await orchestrator.create_agent_with_dependencies("A9_Deep_Analysis_Agent", da_agent_config)
    agents["A9_Deep_Analysis_Agent"] = da_agent
    
    # 6. Solution Finder Agent
    logger.info("Creating Solution Finder Agent")
    sf_agent_config = {
        "orchestrator": orchestrator,
        "registry_factory": registry_factory,
    }
    sf_agent = await orchestrator.create_agent_with_dependencies("A9_Solution_Finder_Agent", sf_agent_config)
    agents["A9_Solution_Finder_Agent"] = sf_agent
    
    # Connect agents in the same order
    logger.info("Connecting agents in dependency order")
    
    # 1. Connect Data Governance Agent
    logger.info("Connecting Data Governance Agent")
    try:
        await dg_agent.connect(orchestrator)
    except TypeError:
        await dg_agent.connect()
    
    # 2. Connect Principal Context Agent
    logger.info("Connecting Principal Context Agent")
    try:
        await pc_agent.connect(orchestrator)
    except TypeError:
        await pc_agent.connect()
    
    # 3. Connect Data Product Agent
    logger.info("Connecting Data Product Agent")
    try:
        await dp_agent.connect(orchestrator)
    except TypeError:
        await dp_agent.connect()
    
    # 4. Connect Situation Awareness Agent
    logger.info("Connecting Situation Awareness Agent")
    try:
        await sa_agent.connect(orchestrator)
    except TypeError:
        await sa_agent.connect()
    
    # 5. Connect Deep Analysis Agent
    logger.info("Connecting Deep Analysis Agent")
    try:
        await da_agent.connect(orchestrator)
    except TypeError:
        await da_agent.connect()
    
    # 6. Connect Solution Finder Agent
    logger.info("Connecting Solution Finder Agent")
    try:
        await sf_agent.connect(orchestrator)
    except TypeError:
        await sf_agent.connect()
    
    logger.info("All agents created and connected successfully")
    return agents
