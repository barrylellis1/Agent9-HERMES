"""
Registry Factory

A factory class that provides access to all registry providers.
This is the main entry point for accessing registry data in Agent9.
"""

import logging
from typing import Dict, Optional, Type

from src.registry.providers.registry_provider import (
    BusinessProcessProvider,
    DataProductProvider,
    KPIProvider,
    PrincipalProfileProvider,
    RegistryProvider,
)
from src.registry.models.registry_config import RegistryConfig

logger = logging.getLogger(__name__)


class RegistryFactory:
    """
    Factory class for accessing registry providers.
    
    This class is responsible for creating and managing registry providers,
    ensuring that only one instance of each provider exists (singleton pattern).
    
    It serves as the primary entry point for all agents and services to access
    registry data, abstracting away the details of how and where data is stored.
    """
    
    _instance = None
    _providers: Dict[str, RegistryProvider] = {}
    
    def __new__(cls):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super(RegistryFactory, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the factory if not already initialized."""
        if not getattr(self, '_initialized', False):
            self._providers = {}
            self._config = RegistryConfig()
            self._initialized = True
            logger.info("Registry Factory initialized")
    
    async def initialize(self) -> None:
        """
        Initialize all registry providers.
        
        This method should be called at application startup to ensure
        all registry data is loaded and ready for use.
        """
        # Load all providers and their data
        for provider_name, provider in self._providers.items():
            logger.info(f"Loading registry data for {provider_name}")
            await provider.load()
        
        logger.info("All registry providers initialized and loaded")
    
    def register_provider(self, name: str, provider: RegistryProvider) -> None:
        """
        Register a new provider.
        
        Args:
            name: The name of the provider (e.g., 'business_process')
            provider: The provider instance to register
        """
        self._providers[name] = provider
        logger.info(f"Registered {name} provider")
    
    def get_provider(self, name: str) -> Optional[RegistryProvider]:
        """
        Get a registry provider by name.
        
        Args:
            name: The name of the provider to retrieve
            
        Returns:
            The provider if found, None otherwise
        """
        return self._providers.get(name)
    
    def get_business_process_provider(self) -> Optional[BusinessProcessProvider]:
        """Get the business process registry provider."""
        return self.get_provider('business_process')
    
    def get_kpi_provider(self) -> Optional[KPIProvider]:
        """Get the KPI registry provider."""
        return self.get_provider('kpi')
    
    def get_principal_profile_provider(self) -> Optional[PrincipalProfileProvider]:
        """Get the principal profile registry provider."""
        return self.get_provider('principal_profile')
    
    def get_data_product_provider(self) -> Optional[DataProductProvider]:
        """Get the data product registry provider."""
        return self.get_provider('data_product')
