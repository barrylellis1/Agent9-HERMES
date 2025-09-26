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
    _provider_initialization_status: Dict[str, bool] = {}
    
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
        # Check if we have any providers to initialize
        if not self._providers:
            logger.warning("No providers registered for initialization")
            return
            
        # Load all providers and their data
        for provider_name, provider in self._providers.items():
            # Skip already initialized providers
            if self._provider_initialization_status.get(provider_name, False):
                logger.info(f"Provider '{provider_name}' already initialized, skipping")
                continue
                
            try:
                logger.info(f"Loading registry data for {provider_name}")
                await provider.load()
                self._provider_initialization_status[provider_name] = True
                logger.info(f"Successfully loaded data for {provider_name} provider")
            except Exception as e:
                logger.error(f"Failed to load data for {provider_name} provider: {str(e)}")
                self._provider_initialization_status[provider_name] = False
                
                # Try to load default data if available
                if hasattr(provider, '_load_default_data'):
                    try:
                        provider._load_default_data()
                        logger.info(f"Loaded default data for {provider_name} provider")
                        self._provider_initialization_status[provider_name] = True
                    except Exception as default_err:
                        logger.error(f"Failed to load default data for {provider_name}: {str(default_err)}")
        
        logger.info("All registry providers initialization attempt complete")
    
    def register_provider(self, name: str, provider: RegistryProvider) -> None:
        """
        Register a new provider.
        
        Args:
            name: The name of the provider (e.g., 'business_process')
            provider: The provider instance to register
        """
        # Check if provider is replacing an existing one
        if name in self._providers:
            # If it's the same instance, don't replace and keep initialization status
            if self._providers[name] is provider:
                logger.info(f"Provider '{name}' already registered with same instance, skipping")
                return
            # If the existing provider is already initialized, don't replace it
            elif self._provider_initialization_status.get(name, False):
                logger.info(f"Provider '{name}' already initialized, keeping existing instance")
                return
            else:
                logger.warning(f"Replacing existing {name} provider with new instance")
            
        self._providers[name] = provider
        self._provider_initialization_status[name] = False
        logger.info(f"Registered {name} provider")
    
    def get_provider(self, name: str) -> Optional[RegistryProvider]:
        """
        Get a registry provider by name.
        
        Args:
            name: The name of the provider to retrieve
            
        Returns:
            The provider if found, None otherwise
        """
        provider = self._providers.get(name)
        if provider is None:
            logger.warning(f"Provider '{name}' not found in registry factory")
        elif name in self._provider_initialization_status and not self._provider_initialization_status[name]:
            logger.warning(f"Provider '{name}' exists but may not be properly initialized")
        return provider
        
    @property
    def is_initialized(self) -> bool:
        """Check if the registry factory has been initialized with providers."""
        return bool(self._providers)
        
    def provider_status(self) -> Dict[str, bool]:
        """Get initialization status of all registered providers."""
        return self._provider_initialization_status.copy()
    
    def get_business_process_provider(self) -> Optional[BusinessProcessProvider]:
        """
        Get the business process provider. If it doesn't exist, create and register a default one.
        
        Returns:
            BusinessProcessProvider instance or None if creation fails
        """
        provider = self.get_provider("business_process")
        
        # If provider doesn't exist, create a default one
        if provider is None:
            try:
                from src.registry.providers.business_process_provider import BusinessProcessProvider
                logger.info("Creating default business process provider since none exists")
                provider = BusinessProcessProvider(
                    source_path="src/registry/business_process/business_process_registry.yaml",
                    storage_format="yaml"
                )
                self.register_provider("business_process", provider)
                # Mark as initialized
                self._provider_initialization_status["business_process"] = True
                logger.info("Default business process provider created and registered successfully")
            except Exception as e:
                logger.error(f"Failed to create default business process provider: {str(e)}")
                return None
                
        return provider
    
    def get_kpi_provider(self) -> Optional[KPIProvider]:
        """
        Get the KPI provider. If it doesn't exist, create and register a default one.
        
        Returns:
            KPIProvider instance or None if creation fails
        """
        provider = self.get_provider("kpi")
        
        # If provider doesn't exist, create a default one
        if provider is None:
            try:
                from src.registry.providers.kpi_provider import KPIProvider
                logger.info("Creating default KPI provider since none exists")
                # Load from YAML so that kpi_defaults and registry-driven semantics are applied
                provider = KPIProvider(
                    source_path="src/registry/kpi/kpi_registry.yaml",
                    storage_format="yaml"
                )
                self.register_provider("kpi", provider)
                # Mark as initialized
                self._provider_initialization_status["kpi"] = True
                logger.info("Default KPI provider created and registered successfully")
            except Exception as e:
                logger.error(f"Failed to create default KPI provider: {str(e)}")
                return None
                
        return provider
    
    def get_principal_profile_provider(self) -> Optional[PrincipalProfileProvider]:
        """Get the principal profile registry provider."""
        return self.get_provider('principal_profile')
    
    def get_data_product_provider(self) -> Optional[DataProductProvider]:
        """Get the data product registry provider."""
        return self.get_provider('data_product')
