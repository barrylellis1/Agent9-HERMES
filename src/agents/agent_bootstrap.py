"""
Agent Registry Bootstrap

Provides standardized initialization and discovery of Agent9 agents for orchestration.
Automatically discovers and registers agent factories with the agent registry.
"""

import os
import sys
import glob
import inspect
import importlib
import logging
from typing import Dict, Any, List, Type, Callable, Optional, Tuple

from src.agents.a9_orchestrator_agent import AgentRegistry
# No dependency on agent_base for now
from src.utils.config_utils import load_yaml

logger = logging.getLogger(__name__)

class AgentBootstrap:
    """
    Agent Bootstrap system that provides standardized agent registration
    and discovery according to Agent9 design standards.
    """
    _initialized = False
    _agent_classes = {}
    _agent_cards = {}
    
    @classmethod
    async def initialize(cls, config: Dict[str, Any] = None) -> bool:
        """
        Initialize the agent bootstrap system, discover available agents,
        and register agent factories with the agent registry.
        
        Args:
            config: Configuration dictionary (base_path, etc.)
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        if cls._initialized:
            logger.info("Agent bootstrap already initialized")
            return True
            
        try:
            config = config or {}
            base_path = config.get('base_path', os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            
            # Discover agent implementations
            discovered_agents = cls.discover_agent_implementations(base_path)
            if not discovered_agents:
                logger.warning("No agent implementations discovered")
                return False
                
            # Register discovered agent factories
            registry = AgentRegistry()
            for agent_name, agent_class in discovered_agents.items():
                factory_func = cls.create_agent_factory(agent_class)
                if factory_func:
                    registry.register_agent_factory(agent_name, factory_func)
                    cls._agent_classes[agent_name] = agent_class
                    logger.info(f"Registered agent factory for {agent_name}")
                    
            # Load agent cards for discovered agents
            cls._agent_cards = cls.load_agent_cards(base_path)
            
            cls._initialized = True
            logger.info(f"Agent bootstrap initialized with {len(discovered_agents)} agents")
            return True
            
        except Exception as e:
            logger.error(f"Error during agent bootstrap initialization: {str(e)}")
            return False
            
    @classmethod
    def discover_agent_implementations(cls, base_path: str) -> Dict[str, Type]:
        """
        Discover all agent implementations in the codebase.
        
        Args:
            base_path: Base path to start discovery from
            
        Returns:
            Dict of agent name to agent class
        """
        agents = {}
        
        # Discover both legacy and new agents
        agent_paths = [
            os.path.join(base_path, "agents", "*.py"),
            os.path.join(base_path, "agents", "new", "*.py")
        ]
        
        for path_pattern in agent_paths:
            for file_path in glob.glob(path_pattern):
                if os.path.basename(file_path).startswith('__'):
                    continue
                    
                try:
                    # Import the module
                    module_path = file_path.replace(os.path.commonprefix([base_path, file_path]), '')
                    module_path = module_path.replace(os.path.sep, '.').replace('.py', '')
                    if module_path.startswith('.'):
                        module_path = module_path[1:]
                        
                    # Handle different paths for src/ and non-src/ paths
                    if "src." not in module_path and os.path.basename(base_path) == "src":
                        module_path = f"src.{module_path}"
                    
                    module = importlib.import_module(module_path)
                    
                    # Find agent classes in the module
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            name.startswith('A9_') and 
                            name.endswith('_Agent')):
                            # Skip the base class itself
                            if name == 'Agent9Base':
                                continue
                                
                            # Check if the class has a create method
                            # For classmethods, we need to check differently than regular methods
                            has_create = False
                            
                            # Check if create exists as an attribute
                            if hasattr(obj, 'create'):
                                # Check if it's a classmethod by looking in the class dict
                                for cls_check in obj.__mro__:
                                    if 'create' in cls_check.__dict__:
                                        attr = cls_check.__dict__['create']
                                        if isinstance(attr, classmethod):
                                            has_create = True
                                            break
                                
                                # Also check if it's a regular method or function
                                if not has_create:
                                    create_attr = getattr(obj, 'create')
                                    has_create = inspect.isfunction(create_attr) or inspect.ismethod(create_attr)
                            
                            if has_create:
                                agents[name] = obj
                                logger.info(f"Discovered agent: {name} in {module_path}")
                            else:
                                logger.warning(f"Found agent class {name} but it lacks a create method")
                except Exception as e:
                    logger.warning(f"Error discovering agents in {file_path}: {str(e)}")
                    
        return agents
        
    @classmethod
    def create_agent_factory(cls, agent_class: Type) -> Optional[Callable]:
        """
        Create a factory function for an agent class.
        
        Args:
            agent_class: Agent class to create factory for
            
        Returns:
            Factory function or None if creation failed
        """
        if not hasattr(agent_class, 'create'):
            logger.warning(f"Agent class {agent_class.__name__} has no create method")
            return None
            
        # Get the create method
        create_method = getattr(agent_class, 'create')
        
        # For classmethods, the descriptor in the class.__dict__ is not the same as what you get with getattr
        # We need to check both approaches
        is_class_method = inspect.ismethod(create_method) and create_method.__self__ is agent_class
        
        # Check if create appears in the class dict as a classmethod
        for cls_check in agent_class.__mro__:
            if 'create' in cls_check.__dict__:
                attr = cls_check.__dict__['create']
                if isinstance(attr, classmethod):
                    is_class_method = True
                    break
        
        # Also check if it's a coroutine function (async def)
        is_coroutine = inspect.iscoroutinefunction(create_method) or (
            hasattr(create_method, '__func__') and inspect.iscoroutinefunction(create_method.__func__)
        )
        
        # For Agent9 standards, we require create to be both a classmethod and a coroutine
        if not is_class_method:
            logger.warning(f"Agent class {agent_class.__name__} create method must be a classmethod")
            return None
            
        if not is_coroutine:
            logger.warning(f"Agent class {agent_class.__name__} create method must be a coroutine (async def)")
            return None
            
        # Create a factory function that calls the create method
        async def factory_func(config: Dict[str, Any] = None):
            try:
                return await agent_class.create(config)
            except Exception as e:
                logger.error(f"Error creating agent {agent_class.__name__}: {str(e)}")
                return None
                
        return factory_func
        
    @classmethod
    def load_agent_cards(cls, base_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Load agent cards for all discovered agents.
        
        Args:
            base_path: Base path to start discovery from
            
        Returns:
            Dict of agent name to agent card
        """
        agent_cards = {}
        
        card_path = os.path.join(base_path, "agents", "new", "cards")
        if not os.path.exists(card_path):
            logger.warning(f"Agent card directory not found: {card_path}")
            return agent_cards
            
        for file_path in glob.glob(os.path.join(card_path, "*.yaml")):
            try:
                card_data = load_yaml(file_path)
                if card_data and 'agent_name' in card_data:
                    agent_name = card_data['agent_name']
                    agent_cards[agent_name] = card_data
                    logger.info(f"Loaded agent card for {agent_name}")
            except Exception as e:
                logger.warning(f"Error loading agent card from {file_path}: {str(e)}")
                
        return agent_cards
        
    @classmethod
    def get_agent_info(cls) -> List[Dict[str, Any]]:
        """
        Get information about all registered agents.
        
        Returns:
            List of agent information dictionaries
        """
        agent_info = []
        
        for agent_name, agent_class in cls._agent_classes.items():
            card_data = cls._agent_cards.get(agent_name, {})
            
            agent_info.append({
                'name': agent_name,
                'class': agent_class.__name__,
                'module': agent_class.__module__,
                'card': card_data
            })
            
        return agent_info
