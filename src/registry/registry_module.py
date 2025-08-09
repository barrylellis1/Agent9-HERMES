"""
Registry Module

Provides a simple interface to initialize and access all registry providers.
This module is the main entry point for using the registry system.
"""

import logging
from typing import Optional, Dict, Any

from src.registry.factory import RegistryFactory
from src.registry.providers.business_process_provider import BusinessProcessProvider
from src.registry.providers.kpi_provider import KPIProvider
from src.registry.providers.principal_provider import PrincipalProfileProvider
from src.registry.providers.data_product_provider import DataProductProvider
from src.registry.models.registry_config import RegistryConfig

logger = logging.getLogger(__name__)

# Global registry factory instance
_registry_factory: Optional[RegistryFactory] = None


async def initialize_registry(config: Optional[RegistryConfig] = None) -> None:
    """
    Initialize the registry system.
    
    This function creates and initializes all registry providers, making them
    available for use throughout the application.
    
    Args:
        config: Optional registry configuration. If not provided, the default
               configuration will be used.
    """
    global _registry_factory
    
    if _registry_factory is not None:
        logger.warning("Registry has already been initialized")
        return
    
    # Create the registry factory
    _registry_factory = RegistryFactory()
    
    # Use provided config or create default
    if config is None:
        config = RegistryConfig()
    
    # Register providers
    _register_providers(config)
    
    # Initialize all providers
    await _registry_factory.initialize()
    
    logger.info("Registry system initialized")


def _register_providers(config: RegistryConfig) -> None:
    """
    Register all providers with the registry factory.
    
    Args:
        config: Registry configuration
    """
    global _registry_factory
    
    if _registry_factory is None:
        raise RuntimeError("Registry factory not initialized")
    
    # Business Process Provider
    if "business_process" in config.providers:
        provider_config = config.providers["business_process"]
        if provider_config.enabled:
            provider = BusinessProcessProvider(
                source_path=provider_config.source_path,
                storage_format=provider_config.storage_format
            )
            _registry_factory.register_provider("business_process", provider)
    else:
        # Register with default settings
        provider = BusinessProcessProvider()
        _registry_factory.register_provider("business_process", provider)
    
    # KPI Provider
    if "kpi" in config.providers:
        provider_config = config.providers["kpi"]
        if provider_config.enabled:
            provider = KPIProvider(
                source_path=provider_config.source_path,
                storage_format=provider_config.storage_format
            )
            _registry_factory.register_provider("kpi", provider)
    else:
        # Register with default settings
        provider = KPIProvider()
        _registry_factory.register_provider("kpi", provider)
    
    # Data Product Provider
    if "data_product" in config.providers:
        provider_config = config.providers["data_product"]
        if provider_config.enabled:
            provider = DataProductProvider(
                source_path=provider_config.source_path,
                storage_format=provider_config.storage_format
            )
            _registry_factory.register_provider("data_product", provider)
    else:
        # Register with default settings
        provider = DataProductProvider()
        _registry_factory.register_provider("data_product", provider)
    
    # Principal Profile Provider
    if "principal_profile" in config.providers:
        provider_config = config.providers["principal_profile"]
        if provider_config.enabled:
            provider = PrincipalProfileProvider(
                source_path=provider_config.source_path,
                storage_format=provider_config.storage_format
            )
            _registry_factory.register_provider("principal_profile", provider)
    else:
        # Register with default settings
        provider = PrincipalProfileProvider()
        _registry_factory.register_provider("principal_profile", provider)


def get_registry() -> RegistryFactory:
    """
    Get the global registry factory.
    
    Returns:
        The registry factory instance
    
    Raises:
        RuntimeError: If the registry has not been initialized
    """
    global _registry_factory
    
    if _registry_factory is None:
        raise RuntimeError("Registry has not been initialized. Call initialize_registry first.")
    
    return _registry_factory


def is_initialized() -> bool:
    """
    Check if the registry has been initialized.
    
    Returns:
        True if the registry has been initialized, False otherwise
    """
    return _registry_factory is not None
