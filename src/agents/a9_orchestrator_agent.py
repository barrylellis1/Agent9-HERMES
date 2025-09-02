"""
A9 Orchestrator Agent

The Orchestrator Agent manages agent-to-agent communication and workflow orchestration.
It maintains a registry of available agents and handles agent lifecycle management.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Type, Union
import inspect

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Agent registry singleton that manages agent instances and provides access to them.
    """
    _instance = None
    _agents = {}
    _agent_factories = {}
    
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
        logger.info(f"Agent factory for {agent_name} registered with the registry")
    
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
        
        # Create a new instance if we have a factory
        if agent_name in cls._agent_factories:
            logger.info(f"Creating new agent {agent_name} using registered factory")
            factory = cls._agent_factories[agent_name]
            
            # Check if factory is async
            if inspect.iscoroutinefunction(factory):
                agent = await factory(config or {})
            else:
                agent = factory(config or {})
                
            cls._agents[agent_name] = agent
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
    def clear(cls) -> None:
        """
        Clear the registry (mainly for testing).
        """
        cls._agents = {}
        cls._agent_factories = {}
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
    
    @classmethod
    async def create_from_registry(cls, config: Dict[str, Any] = None) -> 'A9_Orchestrator_Agent':
        """
        Alias for PRD-compliant factory naming. Delegates to create().
        """
        return await cls.create(config)
    
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
    
    async def register_agent(self, agent_name: str, agent_instance: Any) -> None:
        """
        Register an agent with the registry.
        
        Args:
            agent_name: Name of the agent.
            agent_instance: Instance of the agent.
        """
        self.registry.register_agent(agent_name, agent_instance)
    
    async def register_agent_factory(self, agent_name: str, factory_func: Callable) -> None:
        """
        Register an agent factory with the registry.
        
        Args:
            agent_name: Name of the agent.
            factory_func: Factory function to create the agent.
        """
        self.registry.register_agent_factory(agent_name, factory_func)
    
    async def get_agent(self, agent_name: str, config: Dict[str, Any] = None) -> Any:
        """
        Get an agent from the registry.
        
        Args:
            agent_name: Name of the agent to get.
            config: Configuration for agent creation if needed.
            
        Returns:
            Agent instance.
        """
        return await self.registry.get_agent(agent_name, config)
    
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
        self.logger.info(f"Executing {agent_name}.{method_name}")
        try:
            # Handle different parameter types
            if isinstance(params, dict):
                result = await method(**params) if inspect.iscoroutinefunction(method) else method(**params)
            else:
                result = await method(params) if inspect.iscoroutinefunction(method) else method(params)
                
            return result
        except Exception as e:
            error_msg = f"Error executing {agent_name}.{method_name}: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg) from e
    
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
        
    async def has_agent(self, agent_name: str) -> bool:
        """
        Check if an agent is available in the registry.
        
        Args:
            agent_name: Name of the agent to check.
            
        Returns:
            True if the agent is available, False otherwise.
        """
        # Check if the agent is already instantiated
        if agent_name in self.registry._agents:
            return True
            
        # Check if we have a factory for this agent
        if agent_name in self.registry._agent_factories:
            return True
            
        self.logger.warning(f"Agent {agent_name} not found in registry or factories")
        return False
        
    async def refresh_agent_registry(self, config: Dict[str, Any] = None) -> bool:
        """
        Refresh the agent registry by discovering and registering all available agents.
        
        This method uses the AgentBootstrap to discover agent implementations and 
        register their factories with the registry.
        
        Args:
            config: Configuration to pass to agent factories and bootstrap process.
            
        Returns:
            True if successful, False otherwise.
        """
        from src.agents.agent_bootstrap import AgentBootstrap
        
        try:
            # Set config for future use
            if config:
                self.config.update(config)
            
            # Get base path from config or default to current directory
            base_path = self.config.get("base_path", "src")
            
            # Discover agent implementations
            self.logger.info(f"Discovering agent implementations in {base_path}")
            agents = AgentBootstrap.discover_agent_implementations(base_path)
            
            # Register agent factories with the registry
            for agent_name, agent_class in agents.items():
                try:
                    self.logger.info(f"Registering factory for {agent_name}")
                    # Prefer class.create when available
                    factory = getattr(agent_class, 'create', None)
                    if callable(factory):
                        self.registry.register_agent_factory(agent_name, factory)
                        continue

                    # Fallback: support module-level factory functions following naming convention
                    # Example: A9_Situation_Awareness_Agent -> create_situation_awareness_agent
                    try:
                        module = __import__(agent_class.__module__, fromlist=['*'])
                        base = agent_name
                        if base.startswith('A9_'):
                            base = base[3:]
                        if base.endswith('_Agent'):
                            base = base[:-6]
                        factory_name = f"create_{base.lower()}"
                        module_level_factory = getattr(module, factory_name, None)
                        if callable(module_level_factory):
                            self.registry.register_agent_factory(agent_name, module_level_factory)
                            self.logger.info(f"Registered module-level factory {factory_name} for {agent_name}")
                        else:
                            self.logger.warning(f"No factory found for {agent_name} (no class.create and missing {factory_name})")
                    except Exception as inner_e:
                        self.logger.warning(f"Fallback factory resolution failed for {agent_name}: {str(inner_e)}")
                except Exception as e:
                    self.logger.warning(f"Failed to register factory for {agent_name}: {str(e)}")
            
            # Initialize registry providers if needed
            if "registry_path" in self.config:
                from src.registry.bootstrap import RegistryBootstrap
                registry_config = {
                    "base_path": self.config.get("base_path"),
                    "registry_path": self.config.get("registry_path")
                }
                
                await RegistryBootstrap.initialize(registry_config)
                self.logger.info("Registry providers initialized")
            
            return True
        except Exception as e:
            self.logger.error(f"Error refreshing agent registry: {str(e)}")
            return False


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
    from src.agents.a9_principal_context_agent import A9_Principal_Context_Agent
    from src.agents.a9_situation_awareness_agent import A9_Situation_Awareness_Agent
    from src.agents.a9_data_product_mcp_service_agent import A9_Data_Product_MCP_Service_Agent
    from src.agents.a9_data_governance_agent import A9_Data_Governance_Agent, create_data_governance_agent
    
    # Register agent factories
    agent_registry.register_agent_factory("A9_Orchestrator_Agent", A9_Orchestrator_Agent.create)
    agent_registry.register_agent_factory("A9_Principal_Context_Agent", A9_Principal_Context_Agent.create)
    # Use async class factory to ensure connect() is awaited
    agent_registry.register_agent_factory("A9_Situation_Awareness_Agent", A9_Situation_Awareness_Agent.create)
    agent_registry.register_agent_factory("A9_Data_Product_MCP_Service_Agent", A9_Data_Product_MCP_Service_Agent.create)
    agent_registry.register_agent_factory("A9_Data_Governance_Agent", A9_Data_Governance_Agent.create)
    
    logger.info("Agent registry initialized with common agent factories")
