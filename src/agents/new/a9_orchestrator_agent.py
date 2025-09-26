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
    
    # Register agent factories
    agent_registry.register_agent_factory("A9_Principal_Context_Agent", A9_Principal_Context_Agent.create)
    agent_registry.register_agent_factory("A9_Situation_Awareness_Agent", create_situation_awareness_agent)
    agent_registry.register_agent_factory("A9_Data_Product_Agent", A9_Data_Product_Agent.create)
    agent_registry.register_agent_factory("A9_Data_Governance_Agent", A9_Data_Governance_Agent.create)
    agent_registry.register_agent_factory("A9_NLP_Interface_Agent", A9_NLP_Interface_Agent.create)
    agent_registry.register_agent_factory("A9_LLM_Service_Agent", A9_LLM_Service_Agent.create)
    
    # Register agent dependencies
    agent_registry.register_agent_dependency("A9_Data_Product_Agent", ["A9_Data_Governance_Agent"])
    agent_registry.register_agent_dependency("A9_Situation_Awareness_Agent", ["A9_Data_Product_Agent", "A9_Principal_Context_Agent"])
    
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
        "db_type": "duckdb",
        "db_path": "data/agent9-hermes.duckdb",
        "registry_path": "src/registry/data_product"
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
    
    logger.info("All agents created and connected successfully")
    return agents
