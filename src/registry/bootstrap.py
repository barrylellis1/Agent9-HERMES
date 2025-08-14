"""
Registry Bootstrap

This module is responsible for initializing and registering all registry providers
with the RegistryFactory, ensuring they are available to agents and services.

Provides standardized initialization of registry providers and agent factories.
"""

import os
import logging
from typing import Dict, Any, Optional

from src.registry.factory import RegistryFactory
from src.registry.providers.principal_provider import PrincipalProfileProvider
from src.agents.agent_bootstrap import AgentBootstrap
from src.registry.providers.data_product_provider import DataProductProvider
# Import other providers as needed

logger = logging.getLogger(__name__)

class RegistryBootstrap:
    """
    Bootstrap class for registry initialization.
    
    This class is responsible for properly initializing and registering
    all registry providers with the RegistryFactory, ensuring they are
    available to agents and services.
    """
    
    _initialized = False
    _factory = None
    
    @classmethod
    async def initialize(cls, config: Dict[str, Any] = None) -> bool:
        """
        Initialize the registry bootstrap system, register required providers,
        and initialize agent factories.
        
        Args:
            config: Configuration dictionary (base_path, registry_path, etc.)
            
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        if cls._initialized:
            logger.info("Registry bootstrap already initialized")
            return True
            
        try:
            config = config or {}
            base_path = config.get('base_path', os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            registry_path = config.get('registry_path', os.path.join(base_path, "registry"))
            
            # Initialize registry factory
            cls._factory = RegistryFactory()
            
            # Configure base paths
            # base_path = config.get("base_path", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            # registry_path = config.get("registry_path", os.path.join(base_path, "registry"))
            
            # Register principal provider
            principal_path = os.path.join(registry_path, "principal", "principal_registry.yaml")
            if os.path.exists(principal_path):
                principal_provider = PrincipalProfileProvider(
                    source_path=principal_path,
                    storage_format="yaml"
                )
                cls._factory.register_provider('principal_profile', principal_provider)
                await principal_provider.load()
                logger.info(f"Initialized principal provider with {len(principal_provider.get_all() or {})} profiles")
            else:
                logger.warning(f"Principal registry file not found at {principal_path}")
                # Create with default profiles
                principal_provider = PrincipalProfileProvider()
                principal_provider._load_default_profiles()
                cls._factory.register_provider('principal_profile', principal_provider)
                logger.info("Using default principal profiles (registry file not found)")
            
            # Initialize and register data product provider if needed
            data_product_path = os.path.join(registry_path, "data_product", "data_product_registry.yaml")
            if os.path.exists(data_product_path):
                data_provider = DataProductProvider(
                    source_path=data_product_path,
                    storage_format="yaml"
                )
                cls._factory.register_provider('data_product', data_provider)
                await data_provider.load()
                logger.info(f"Initialized data product provider with {len(data_provider.get_all() or {})} data products")
            else:
                logger.warning(f"Data product registry file not found at {data_product_path}")
            
            # Initialize agent factories using AgentBootstrap
            logger.info("Initializing agent bootstrap")
            agent_bootstrap_success = await AgentBootstrap.initialize({
                'base_path': base_path,
                'registry_factory': cls._factory
            })
            
            if agent_bootstrap_success:
                logger.info("Agent bootstrap initialization successful")
            else:
                logger.warning("Agent bootstrap initialization had issues, continuing with available agents")
            
            cls._initialized = True
            logger.info("Registry providers and agent factories initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize registry providers: {str(e)}")
            return False
    
    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the registry bootstrap has been initialized."""
        return cls._initialized
