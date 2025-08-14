"""
Agent9 Base Classes

Provides base classes for Agent9 agents to ensure consistency and standards compliance.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class Agent9Base(ABC):
    """
    Base class for all Agent9 agents.
    
    All agents in Agent9 should inherit from this base class to ensure
    consistency in initialization, configuration, and protocol compliance.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the agent.
        
        Args:
            config: Configuration dictionary.
        """
        self.config = config or {}
        self.name = self.__class__.__name__
        self._setup_logging()
        
    def _setup_logging(self):
        """Set up logging for the agent."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initializing {self.__class__.__name__}")
    
    @classmethod
    @abstractmethod
    async def create(cls, config: Dict[str, Any] = None) -> 'Agent9Base':
        """
        Create a new instance of the agent.
        
        This is the standard factory method for all Agent9 agents.
        
        Args:
            config: Configuration dictionary.
            
        Returns:
            Initialized agent instance.
        """
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Connect to dependencies and initialize required resources.
        
        Returns:
            True if successful, False otherwise.
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from dependencies and clean up resources.
        
        Returns:
            True if successful, False otherwise.
        """
        pass
