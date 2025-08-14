"""
Principal Context Agent

This agent manages principal context and relationships in business operations.
It handles registration, retrieval, and management of principal profiles as well
as mapping principals to business processes and KPIs.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

from src.registry.factory import RegistryFactory
from src.registry.providers.principal_provider import PrincipalProfileProvider

logger = logging.getLogger(__name__)


class A9_Principal_Context_Agent:
    """
    Principal Context Agent responsible for managing principal profiles and context.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Principal Context Agent.
        
        Args:
            config: Configuration dictionary.
        """
        self.config = config or {}
        self.principal_profiles = {}
        self._setup_logging()
        self._registry_factory = None
        self._principal_provider = None
        
    @classmethod
    async def create(cls, config: Dict[str, Any] = None) -> 'A9_Principal_Context_Agent':
        """
        Create a new instance of the Principal Context Agent.
        
        Args:
            config: Configuration dictionary.
            
        Returns:
            Initialized Principal Context Agent instance.
        """
        agent = cls(config)
        await agent.connect()
        return agent

    def _setup_logging(self):
        """Set up logging for the agent."""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info(f"Initializing {self.__class__.__name__}")
    
    async def connect(self):
        """
        Connect to dependencies and initialize required resources.
        """
        try:
            # Initialize registry factory
            self._registry_factory = RegistryFactory()
            
            # Get principal provider from registry factory
            self._principal_provider = self._registry_factory.get_principal_profile_provider()
            if not self._principal_provider:
                self.logger.warning("Could not get principal profile provider from registry factory")
                return
                
            # Load all principal profiles
            await self._load_principal_profiles()
            
            self.logger.info("Connected to dependencies")
        except Exception as e:
            self.logger.error(f"Error connecting to dependencies: {str(e)}")
    
    async def disconnect(self):
        """
        Disconnect from dependencies and clean up resources.
        """
        self.logger.info("Disconnected from dependencies")
    
    async def _load_principal_profiles(self):
        """
        Load principal profiles from the registry.
        """
        try:
            # Get all principal profiles
            profiles = self._principal_provider.get_all() or {}
            if not profiles:
                self.logger.warning("No principal profiles found in registry")
                return
                
            self.principal_profiles = profiles
            self.logger.info(f"Loaded {len(self.principal_profiles)} principal profiles from registry")
        except Exception as e:
            self.logger.error(f"Error loading principal profiles: {str(e)}")
            self.principal_profiles = {}
    
    async def set_principal_context(self, principal_id: str, context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Set principal context.
        
        Args:
            principal_id: Identifier of the principal.
            context_data: Additional context data.
            
        Returns:
            Principal context information.
        """
        try:
            # Get principal profile
            profile = await self.fetch_principal_profile(principal_id)
            if not profile:
                self.logger.warning(f"Principal profile not found: {principal_id}")
                return {}
                
            # Merge with context data
            if context_data:
                # Update profile with context data
                # This would be expanded in a full implementation
                pass
                
            return profile
        except Exception as e:
            self.logger.error(f"Error setting principal context: {str(e)}")
            return {}
    
    async def fetch_principal_profile(self, principal_id: str) -> Dict[str, Any]:
        """
        Fetch principal profile.
        
        Args:
            principal_id: Identifier of the principal.
            
        Returns:
            Principal profile information.
        """
        try:
            if not self._principal_provider:
                self.logger.warning("Principal profile provider not initialized")
                return {}
                
            # Convert principal_id to role name if it's a role
            if principal_id in self.principal_profiles:
                profile = self.principal_profiles[principal_id]
                return {
                    "name": profile.get("name", principal_id),
                    "business_processes": profile.get("business_processes", []),
                    "default_filters": profile.get("default_filters", {}),
                    "communication_style": profile.get("communication_style", "direct"),
                    "decision_timeframe": profile.get("decision_timeframe", "monthly")
                }
            else:
                self.logger.warning(f"Principal profile not found: {principal_id}")
                return {}
        except Exception as e:
            self.logger.error(f"Error fetching principal profile: {str(e)}")
            return {}
    
    async def get_context_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get context-based recommendations.
        
        Returns:
            List of recommendations.
        """
        # This would be implemented in a full version
        return []
    
    async def get_context_history(self) -> List[Dict[str, Any]]:
        """
        Get context history.
        
        Returns:
            List of context history items.
        """
        # This would be implemented in a full version
        return []
    
    async def clear_context(self) -> None:
        """
        Clear current context.
        """
        # This would be implemented in a full version
        pass
        
    async def get_principal_context(self, principal_role) -> Dict[str, Any]:
        """
        Get principal context for a given role.
        
        Args:
            principal_role: Role of the principal (PrincipalRole enum value)
            
        Returns:
            Principal context containing preferences and relevant business processes
        """
        from src.agents.models.situation_awareness_models import PrincipalContext, BusinessProcess, TimeFrame
        
        # Log the request
        self.logger.info(f"Getting principal context for role: {principal_role}")
        
        # First try to load from registry if not already loaded
        if not self.principal_profiles:
            await self._load_principal_profiles()
            
        # Try to find matching profile for the role
        profile_key = str(principal_role).lower()
        for key, profile in self.principal_profiles.items():
            if key.lower() == profile_key or (hasattr(profile, 'get') and profile.get('role', '').lower() == profile_key):
                # Create and return PrincipalContext
                business_processes = []
                
                # If profile is a dictionary and has business_processes
                if hasattr(profile, 'get') and profile.get('business_processes'):
                    for bp in profile.get('business_processes', []):
                        # Try to map to BusinessProcess enum
                        try:
                            business_processes.append(BusinessProcess(bp))
                        except ValueError:
                            self.logger.warning(f"Unknown business process: {bp} for principal {principal_role}")
                
                # Create context with defaults if values are missing
                principal_context = PrincipalContext(
                    role=principal_role,
                    business_processes=business_processes or list(BusinessProcess),
                    default_filters=profile.get('default_filters', {}) if hasattr(profile, 'get') else {},
                    decision_style=profile.get('decision_style', "Analytical") if hasattr(profile, 'get') else "Analytical",
                    communication_style=profile.get('communication_style', "Concise") if hasattr(profile, 'get') else "Concise",
                    preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
                )
                
                # Return as dictionary for JSON serialization
                return principal_context.model_dump()
        
        # If no matching profile is found, return a default context
        self.logger.warning(f"No principal profile found for role {principal_role}, using default")
        principal_context = PrincipalContext(
            role=principal_role,
            business_processes=list(BusinessProcess),
            default_filters={},
            decision_style="Analytical",
            communication_style="Concise",
            preferred_timeframes=[TimeFrame.CURRENT_QUARTER, TimeFrame.YEAR_TO_DATE]
        )
        
        return principal_context.model_dump()
