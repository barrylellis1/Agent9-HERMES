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
from src.registry.providers.kpi_provider import KPIProvider
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
                # Mark the principal provider as initialized in the factory's status dictionary
                cls._factory._provider_initialization_status['principal_profile'] = True
                profiles = principal_provider.get_all() or []
                logger.info(f"Initialized principal provider with {len(profiles)} profiles")
            else:
                logger.warning(f"Principal registry file not found at {principal_path}")
                # Create with default profiles
                principal_provider = PrincipalProfileProvider()
                principal_provider._load_default_profiles()
                cls._factory.register_provider('principal_profile', principal_provider)
                # Mark the principal provider as initialized in the factory's status dictionary
                cls._factory._provider_initialization_status['principal_profile'] = True
                logger.info("Using default principal profiles (registry file not found)")
            
            # Initialize and register business glossary provider
            from src.registry.providers.business_glossary_provider import BusinessGlossaryProvider
            
            # Check if business glossary provider is already registered
            existing_glossary_provider = cls._factory.get_provider('business_glossary')
            if existing_glossary_provider is None:
                logger.info("Initializing business glossary provider")
                glossary_path = os.path.join(registry_path, "data", "business_glossary.yaml")
                glossary_provider = BusinessGlossaryProvider(glossary_path=glossary_path)
                cls._factory.register_provider('business_glossary', glossary_provider)
                cls._factory._provider_initialization_status['business_glossary'] = True
                logger.info(f"Initialized business glossary provider with {len(glossary_provider.get_all())} terms")
            
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
            
            # Initialize and register KPI provider
            logger.info("Initializing KPI provider")
            
            # First check if a KPI provider is already registered
            existing_provider = cls._factory.get_provider('kpi')
            if existing_provider is not None:
                logger.info("KPI provider already registered, using existing instance")
                kpi_provider = existing_provider
            else:
                # Create a new KPI provider
                kpi_path = os.path.join(registry_path, "kpi", "kpi_registry.yaml")
                try:
                    # Always create a KPI provider, even if the file doesn't exist
                    # This ensures we have a provider registered that can return default KPIs
                    if os.path.exists(kpi_path):
                        logger.info(f"Creating KPI provider with file at {kpi_path}")
                        kpi_provider = KPIProvider(
                            source_path=kpi_path,
                            storage_format="yaml"
                        )
                    else:
                        logger.warning(f"KPI registry file not found at {kpi_path}, creating default provider")
                        kpi_provider = KPIProvider()  # Will use default KPIs
                    
                    # Register the provider
                    logger.info("Registering KPI provider with registry factory")
                    cls._factory.register_provider('kpi', kpi_provider)
                except Exception as e:
                    logger.error(f"Error creating KPI provider: {str(e)}")
                    # Create a basic provider with defaults as fallback
                    try:
                        logger.info("Creating fallback KPI provider")
                        kpi_provider = KPIProvider()
                        cls._factory.register_provider('kpi', kpi_provider)
                    except Exception as inner_e:
                        logger.error(f"Failed to create fallback KPI provider: {str(inner_e)}")
                        # Mark as not initialized but still create an empty provider
                        try:
                            empty_provider = KPIProvider()
                            cls._factory.register_provider('kpi', empty_provider)
                            cls._factory._provider_initialization_status['kpi'] = False
                            logger.warning("Created empty KPI provider as last resort")
                        except:
                            logger.error("Could not create empty KPI provider as last resort")
                            cls._factory._provider_initialization_status['kpi'] = False
                            return False
            
            # Load KPI data regardless of how the provider was obtained
            try:
                # Load the data
                logger.info("Loading KPI provider data")
                await kpi_provider.load()
                
                # Explicitly mark as initialized in the factory's status dictionary
                cls._factory._provider_initialization_status['kpi'] = True
                
                # Verify the provider is registered and accessible
                test_provider = cls._factory.get_provider('kpi')
                if test_provider is not None:
                    kpi_count = len(test_provider.get_all() or [])
                    logger.info(f"KPI provider successfully registered and initialized with {kpi_count} KPIs")
                    
                    # If no KPIs were loaded, try to load default KPIs
                    if kpi_count == 0:
                        logger.warning("No KPIs found in registry, loading default KPIs")
                        kpi_provider._load_default_kpis()
                        kpi_count = len(kpi_provider.get_all() or [])
                        logger.info(f"Loaded {kpi_count} default KPIs")
                else:
                    logger.error("KPI provider registration failed - provider not found after registration")
                    return False
            except Exception as e:
                logger.error(f"Error loading KPI provider data: {str(e)}")
                # Try to load default KPIs as fallback
                try:
                    logger.info("Loading default KPIs as fallback")
                    kpi_provider._load_default_kpis()
                    cls._factory._provider_initialization_status['kpi'] = True
                    logger.info(f"Loaded {len(kpi_provider.get_all() or [])} default KPIs")
                except Exception as inner_e:
                    logger.error(f"Failed to load default KPIs: {str(inner_e)}")
                    cls._factory._provider_initialization_status['kpi'] = False
            
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
