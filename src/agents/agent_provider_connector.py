"""
Agent Provider Connector

This module provides a standardized way for agents to access registry providers,
with proper error handling and fallback mechanisms.
"""

import logging
from typing import Dict, Any, Optional, TypeVar, Generic

from pydantic import BaseModel
from src.registry.factory import RegistryFactory
from src.registry.providers.registry_provider import RegistryProvider

logger = logging.getLogger(__name__)
T = TypeVar('T', bound=BaseModel)

class AgentProviderConnector:
    """
    Connector for agents to access registry providers.
    
    This class provides a standardized way for agents to access registry
    providers, with proper error handling and fallback mechanisms.
    """
    
    def __init__(self, registry_factory: Optional[RegistryFactory] = None):
        """
        Initialize the agent provider connector.
        
        Args:
            registry_factory: Optional registry factory instance
        """
        self._registry_factory = registry_factory or RegistryFactory()
    
    def get_provider(self, provider_type: str) -> Optional[RegistryProvider]:
        """
        Get a provider by type with proper error handling.
        
        Args:
            provider_type: Type of provider to retrieve
            
        Returns:
            Provider if found and loaded, None otherwise
        """
        if not self._registry_factory:
            logger.error(f"Cannot get provider '{provider_type}': Registry factory not available")
            return None
            
        provider = self._registry_factory.get_provider(provider_type)
        
        # Check if provider exists but isn't loaded
        if provider and hasattr(provider, 'is_loaded') and not provider.is_loaded:
            logger.warning(f"Provider '{provider_type}' exists but not loaded")
        
        return provider
    
    async def ensure_provider(self, provider_type: str, config: Dict[str, Any] = None) -> Optional[RegistryProvider]:
        """
        Ensure a provider exists, creating and loading it if needed.
        
        Args:
            provider_type: Type of provider to ensure
            config: Optional configuration for provider creation
            
        Returns:
            Provider instance if available, None otherwise
        """
        provider = self.get_provider(provider_type)
        
        if not provider and config:
            # Attempt to create the provider if not found
            try:
                # Import providers dynamically based on type
                if provider_type == 'principal_profile':
                    from src.registry.providers.principal_provider import PrincipalProfileProvider
                    provider_class = PrincipalProfileProvider
                elif provider_type == 'data_product':
                    from src.registry.providers.data_product_provider import DataProductProvider
                    provider_class = DataProductProvider
                else:
                    logger.error(f"Unknown provider type: {provider_type}")
                    return None
                
                # Create and register provider
                provider = provider_class(**config)
                self._registry_factory.register_provider(provider_type, provider)
                logger.info(f"Created and registered missing provider: {provider_type}")
                
                # Load provider data
                if hasattr(provider, 'load'):
                    await provider.load()
            except Exception as e:
                logger.error(f"Failed to create provider '{provider_type}': {str(e)}")
        
        return provider
    
    def get_typed_provider(self, provider_type: str) -> Optional[RegistryProvider[T]]:
        """
        Get a provider with type hints for better IDE support.
        
        Args:
            provider_type: Type of provider to retrieve
            
        Returns:
            Typed provider if found, None otherwise
        """
        return self.get_provider(provider_type)
